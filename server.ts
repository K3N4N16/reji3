import express from "express";
import fs from "node:fs";
import path from "node:path";
import multer from "multer";
import JSZip from "jszip";
import {
  DIRS,
  ensureDirs,
  safeFilename,
  uid,
  listAudioFiles,
  probeAudioFile,
  measureAudioMetrics,
  applyEqToBuffer,
  applyEffectToBuffer,
  generateSignalWav,
  mixFonAndVoice,
  concatWavBuffers,
  exportAudioBuffer,
  buildTrackAudio,
  runFfmpeg,
  withTempFile,
  convertToStandardWav,
  type AutomationTrackInput,
} from "./server/audio.ts";
import { aiWriteAnons, ttsSingle, ttsMulti } from "./server/gemini.ts";

ensureDirs();

const app = express();
app.use(express.json({ limit: "100mb" }));
app.use(express.urlencoded({ extended: true, limit: "100mb" }));

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 150 * 1024 * 1024 },
});

function xmlEscape(str: string): string {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

function getCategoryDir(cat: string): string | null {
  if (cat === "playlist") return DIRS.playlist;
  if (cat === "fon") return DIRS.fon;
  if (cat === "jingles") return DIRS.jingles;
  if (cat === "effects") return DIRS.effects;
  if (cat === "anons") return DIRS.anons;
  return null;
}

// ─── HEALTH & AUTH ────────────────────────────────────────────────────────────
app.get("/api/health", (_req, res) => {
  res.json({
    ok: true,
    geminiConfigured: Boolean(process.env.GEMINI_API_KEY),
    ffmpeg: true,
  });
});

app.post("/api/login", (req, res) => {
  const { username, password } = req.body || {};
  const expUser = process.env.APP_USER || "kenan";
  const expPass = process.env.APP_PASS || "imajfm";
  if (username === expUser && password === expPass) {
    return res.json({ ok: true, user: expUser });
  }
  return res.status(401).json({ ok: false, error: "Hatalı kullanıcı adı veya şifre." });
});

// ─── AI ANONS YAZARI & GEMINI TTS ─────────────────────────────────────────────
app.post("/api/ai/write-anons", async (req, res) => {
  try {
    const { topic, tone } = req.body || {};
    if (!topic || !String(topic).trim()) {
      return res.status(400).json({ error: "Konu boş olamaz." });
    }
    const text = await aiWriteAnons(String(topic).trim(), tone);
    res.json({ text });
  } catch (err) {
    res.status(500).json({ error: err instanceof Error ? err.message : "AI yazım hatası" });
  }
});

app.post("/api/tts/single", async (req, res) => {
  try {
    const { model, text, voice, lang, style, eq } = req.body || {};
    if (!text || !String(text).trim()) {
      return res.status(400).json({ error: "Metin boş olamaz." });
    }
    const out = await ttsSingle({
      model: model || "gemini-3.8-flash-lite-tts",
      text: String(text),
      voice: voice || "Kore",
      lang: lang || "tr-TR",
      style: style || "",
    });
    let wav = out.wav;
    if (eq && eq !== "Ham") {
      wav = await applyEqToBuffer(wav, eq);
    }
    const metrics = await measureAudioMetrics(wav, "wav");
    res.json({
      wavBase64: wav.toString("base64"),
      usedModel: out.usedModel,
      metrics,
    });
  } catch (err) {
    res.status(500).json({ error: err instanceof Error ? err.message : "TTS hatası" });
  }
});

app.post("/api/tts/multi", async (req, res) => {
  try {
    const { model, text, sp1, v1, sp2, v2, lang, eq } = req.body || {};
    if (!text || !String(text).trim()) {
      return res.status(400).json({ error: "Diyalog metni boş olamaz." });
    }
    const out = await ttsMulti({
      model: model || "gemini-3.8-flash-tts",
      text: String(text),
      sp1: sp1 || "Sunucu",
      v1: v1 || "Kore",
      sp2: sp2 || "Misafir",
      v2: v2 || "Fenrir",
      lang: lang || "tr-TR",
    });
    let wav = out.wav;
    if (eq && eq !== "Ham") {
      wav = await applyEqToBuffer(wav, eq);
    }
    const metrics = await measureAudioMetrics(wav, "wav");
    res.json({
      wavBase64: wav.toString("base64"),
      usedModel: out.usedModel,
      metrics,
    });
  } catch (err) {
    res.status(500).json({ error: err instanceof Error ? err.message : "Multi-TTS hatası" });
  }
});

app.post("/api/tts/bulk", async (req, res) => {
  try {
    const { lines, model, voice, lang, style, eq } = req.body || {};
    if (!Array.isArray(lines) || lines.length === 0) {
      return res.status(400).json({ error: "Satır listesi boş." });
    }
    const zip = new JSZip();
    const items: Array<{ filename: string; text: string; wavBase64: string; duration: number }> = [];
    const errors: string[] = [];

    for (let i = 0; i < lines.length; i++) {
      const line = String(lines[i]).trim();
      if (!line) continue;
      try {
        const out = await ttsSingle({
          model: model || "gemini-3.8-flash-lite-tts",
          text: line,
          voice: voice || "Kore",
          lang: lang || "tr-TR",
          style: style || "",
        });
        let wav = out.wav;
        if (eq && eq !== "Ham") {
          wav = await applyEqToBuffer(wav, eq);
        }
        const metrics = await measureAudioMetrics(wav, "wav");
        const fn = `${String(i + 1).padStart(2, "0")}_${(voice || "kore").toLowerCase()}_${safeFilename(line, 12)}.wav`;
        zip.file(fn, wav);
        items.push({
          filename: fn,
          text: line,
          wavBase64: wav.toString("base64"),
          duration: metrics.duration,
        });
      } catch (e) {
        errors.push(`Satır ${i + 1}: ${e instanceof Error ? e.message : String(e)}`);
      }
    }

    const zipBuf = items.length > 0 ? await zip.generateAsync({ type: "nodebuffer" }) : null;
    res.json({
      items,
      errors,
      zipBase64: zipBuf ? zipBuf.toString("base64") : null,
    });
  } catch (err) {
    res.status(500).json({ error: err instanceof Error ? err.message : "Toplu TTS hatası" });
  }
});

// ─── KÜTÜPHANE (LIBRARY) ─────────────────────────────────────────────────────
app.get("/api/library/:category", async (req, res) => {
  const dir = getCategoryDir(String(req.params.category));
  if (!dir) return res.status(400).json({ error: "Geçersiz kategori" });
  const files = listAudioFiles(dir);
  const detailed = await Promise.all(
    files.map(async (name) => {
      const fp = path.join(dir, name);
      const stat = fs.statSync(fp);
      const probe = await probeAudioFile(fp);
      return {
        name,
        sizeKb: Math.round(stat.size / 1024),
        duration: probe.duration,
        title: probe.title,
        artist: probe.artist,
        bitrate: probe.bitrate,
      };
    })
  );
  res.json({ files: detailed });
});

app.post("/api/library/:category", upload.array("files"), async (req, res) => {
  const dir = getCategoryDir(String(req.params.category));
  if (!dir) return res.status(400).json({ error: "Geçersiz kategori" });
  const uploaded = (req.files as Express.Multer.File[]) || [];
  const added: Array<{ name: string; duration: number; title: string; artist: string; sizeKb: number }> = [];

  for (const f of uploaded) {
    const ext = path.extname(f.originalname) || ".wav";
    const base = safeFilename(path.basename(f.originalname, ext), 60);
    const fname = `${base}${ext.toLowerCase()}`;
    const dest = path.join(dir, fname);
    fs.writeFileSync(dest, f.buffer);
    const probe = await probeAudioFile(dest);
    added.push({
      name: fname,
      duration: probe.duration,
      title: probe.title,
      artist: probe.artist,
      sizeKb: Math.round(f.size / 1024),
    });
  }
  res.json({ added });
});

app.get("/api/library/:category/:filename", (req, res) => {
  const dir = getCategoryDir(String(req.params.category));
  if (!dir) return res.status(400).json({ error: "Geçersiz kategori" });
  const safe = path.basename(String(req.params.filename));
  const fp = path.join(dir, safe);
  if (!fs.existsSync(fp)) return res.status(404).json({ error: "Dosya bulunamadı" });
  res.sendFile(fp);
});

app.delete("/api/library/:category/:filename", (req, res) => {
  const dir = getCategoryDir(String(req.params.category));
  if (!dir) return res.status(400).json({ error: "Geçersiz kategori" });
  const safe = path.basename(String(req.params.filename));
  const fp = path.join(dir, safe);
  if (fs.existsSync(fp)) fs.unlinkSync(fp);
  res.json({ ok: true });
});

// ─── FON + ANONS MİKSERİ ─────────────────────────────────────────────────────
app.post("/api/audio/fon-mix", upload.single("voiceFile"), async (req, res) => {
  try {
    const { fonFile, voiceBase64, fonVolDb, duckDb } = req.body || {};
    if (!fonFile) return res.status(400).json({ error: "Fon müziği seçin." });
    const fonPath = path.join(DIRS.fon, path.basename(fonFile));
    if (!fs.existsSync(fonPath)) return res.status(404).json({ error: "Fon dosyası bulunamadı." });

    let voiceBuf: Buffer | null = null;
    if (req.file) {
      voiceBuf = await withTempFile("bin", req.file.buffer, async (inP) =>
        withTempFile("wav", null, async (outP) => {
          await convertToStandardWav(inP, outP);
          return fs.readFileSync(outP);
        })
      );
    } else if (voiceBase64) {
      voiceBuf = Buffer.from(voiceBase64, "base64");
    }
    if (!voiceBuf) return res.status(400).json({ error: "Anons sesi bulunamadı." });

    const out = await mixFonAndVoice({
      fonPath,
      voiceBuf,
      fonVolDb: Number(fonVolDb ?? -8),
      duckDb: Number(duckDb ?? -16),
    });
    const metrics = await measureAudioMetrics(out, "wav");
    res.json({ wavBase64: out.toString("base64"), metrics });
  } catch (err) {
    res.status(500).json({ error: err instanceof Error ? err.message : "Miks hatası" });
  }
});

app.post("/api/audio/fon-mix-bulk", async (req, res) => {
  try {
    const { fonFile, items } = req.body || {};
    if (!fonFile || !Array.isArray(items) || items.length === 0) {
      return res.status(400).json({ error: "Fon ve sesler gerekli." });
    }
    const fonPath = path.join(DIRS.fon, path.basename(fonFile));
    if (!fs.existsSync(fonPath)) return res.status(404).json({ error: "Fon dosyası bulunamadı." });

    const zip = new JSZip();
    for (const item of items) {
      const vBuf = Buffer.from(item.wavBase64, "base64");
      const mixed = await mixFonAndVoice({
        fonPath,
        voiceBuf: vBuf,
        fonVolDb: -8,
        duckDb: -16,
      });
      zip.file(`fon_${safeFilename(item.id, 12)}.wav`, mixed);
    }
    const zipBuf = await zip.generateAsync({ type: "nodebuffer" });
    res.json({ zipBase64: zipBuf.toString("base64"), count: items.length });
  } catch (err) {
    res.status(500).json({ error: err instanceof Error ? err.message : "Toplu fon miks hatası" });
  }
});

// ─── SES EFEKTLERİ & SİNYAL ÜRETİCİ ─────────────────────────────────────────
app.post("/api/audio/effect", upload.single("audioFile"), async (req, res) => {
  try {
    let params = req.body?.params;
    if (typeof params === "string") params = JSON.parse(params);
    const eq = req.body?.eq || "Ham";

    let rawWav: Buffer | null = null;
    if (req.file) {
      rawWav = await withTempFile("bin", req.file.buffer, async (inP) =>
        withTempFile("wav", null, async (outP) => {
          await convertToStandardWav(inP, outP);
          return fs.readFileSync(outP);
        })
      );
    } else if (req.body?.wavBase64) {
      rawWav = Buffer.from(req.body.wavBase64, "base64");
    }
    if (!rawWav) return res.status(400).json({ error: "Ses dosyası gerekli." });

    const out = await applyEffectToBuffer(rawWav, params || {}, eq);
    const metrics = await measureAudioMetrics(out, "wav");
    res.json({ wavBase64: out.toString("base64"), metrics });
  } catch (err) {
    res.status(500).json({ error: err instanceof Error ? err.message : "Efekt hatası" });
  }
});

app.get("/api/effects/presets", (_req, res) => {
  const files = fs.readdirSync(DIRS.effect_gallery).filter((f) => f.endsWith(".json"));
  const presets = files
    .map((fn) => {
      try {
        return JSON.parse(fs.readFileSync(path.join(DIRS.effect_gallery, fn), "utf-8"));
      } catch {
        return null;
      }
    })
    .filter(Boolean);
  res.json({ presets });
});

app.post("/api/effects/presets", (req, res) => {
  const { name, params } = req.body || {};
  if (!name || !String(name).trim()) return res.status(400).json({ error: "Preset adı gerekli." });
  const fp = path.join(DIRS.effect_gallery, `${safeFilename(name)}.json`);
  fs.writeFileSync(fp, JSON.stringify({ name: String(name).trim(), params, created: new Date().toISOString() }, null, 2));
  res.json({ ok: true });
});

app.delete("/api/effects/presets/:name", (req, res) => {
  const fp = path.join(DIRS.effect_gallery, `${safeFilename(String(req.params.name))}.json`);
  if (fs.existsSync(fp)) fs.unlinkSync(fp);
  res.json({ ok: true });
});

app.post("/api/audio/signal", (req, res) => {
  try {
    const { waveType, freq, durMs, count, gapMs, db, saveToJingles } = req.body || {};
    const wav = generateSignalWav({
      waveType: waveType || "Sinüs (Sine)",
      freq: Number(freq ?? 1000),
      durMs: Number(durMs ?? 400),
      count: Number(count ?? 3),
      gapMs: Number(gapMs ?? 600),
      db: Number(db ?? -10),
    });
    const filename = `sinyal_${Number(freq ?? 1000)}hz.wav`;
    if (saveToJingles) {
      fs.writeFileSync(path.join(DIRS.jingles, filename), wav);
    }
    res.json({ wavBase64: wav.toString("base64"), filename });
  } catch (err) {
    res.status(500).json({ error: err instanceof Error ? err.message : "Sinyal hatası" });
  }
});

// ─── YAYIN OTOMASYONU ────────────────────────────────────────────────────────
app.post("/api/automation/preview-track", async (req, res) => {
  try {
    const { track, crossfadeMs } = req.body as { track: AutomationTrackInput; crossfadeMs?: number };
    const { wav, notes } = await buildTrackAudio(track, crossfadeMs ?? 1200);
    res.json({ wavBase64: wav.toString("base64"), notes });
  } catch (err) {
    res.status(500).json({ error: err instanceof Error ? err.message : "Önizleme hatası" });
  }
});

app.post("/api/automation/render-master", async (req, res) => {
  try {
    const {
      tracks,
      openJingle,
      closeJingle,
      autoJEvery,
      autoJFile,
      crossfadeMs,
      gapMs,
      compressor,
      normalize,
      format,
      bitrate,
      outName,
    } = req.body || {};

    if (!Array.isArray(tracks) || tracks.length === 0) {
      return res.status(400).json({ error: "Yayın listesi boş." });
    }

    const segments: Buffer[] = [];
    const logs: string[] = [];

    if (openJingle && openJingle !== "Yok") {
      const p = path.join(DIRS.jingles, path.basename(openJingle));
      if (fs.existsSync(p)) {
        const w = await withTempFile("wav", null, async (outP) => {
          await runFfmpeg(["-i", p, "-ar", "44100", "-ac", "2", "-af", "loudnorm=I=-14:TP=-1", outP]);
          return fs.readFileSync(outP);
        });
        segments.push(w);
        logs.push(`🎺 Açılış Jingle: ${openJingle}`);
      }
    }

    const { generateSilenceWav } = await import("./server/audio.ts");
    const gapWav = Number(gapMs) > 0 ? await generateSilenceWav(Number(gapMs)) : null;

    for (let i = 0; i < tracks.length; i++) {
      const trk = tracks[i] as AutomationTrackInput;
      const { wav, notes } = await buildTrackAudio(trk, Number(crossfadeMs ?? 1500));
      segments.push(wav);
      logs.push(`🎵 [${i + 1}/${tracks.length}] ${trk.artist} — ${trk.title}${notes.length ? ` (${notes.join(" · ")})` : ""}`);

      if (
        Number(autoJEvery) > 0 &&
        autoJFile &&
        autoJFile !== "Yok" &&
        (i + 1) % Number(autoJEvery) === 0 &&
        i < tracks.length - 1
      ) {
        const ajp = path.join(DIRS.jingles, path.basename(autoJFile));
        if (fs.existsSync(ajp)) {
          const w = await withTempFile("wav", null, async (outP) => {
            await runFfmpeg(["-i", ajp, "-ar", "44100", "-ac", "2", "-af", "loudnorm=I=-14:TP=-1", outP]);
            return fs.readFileSync(outP);
          });
          segments.push(w);
          logs.push(`🔄 Ara Jingle: ${autoJFile}`);
        }
      }

      if (gapWav && i < tracks.length - 1) {
        segments.push(gapWav);
      }
    }

    if (closeJingle && closeJingle !== "Yok") {
      const p = path.join(DIRS.jingles, path.basename(closeJingle));
      if (fs.existsSync(p)) {
        const w = await withTempFile("wav", null, async (outP) => {
          await runFfmpeg(["-i", p, "-ar", "44100", "-ac", "2", "-af", "loudnorm=I=-14:TP=-1", outP]);
          return fs.readFileSync(outP);
        });
        segments.push(w);
        logs.push(`🎺 Kapanış Jingle: ${closeJingle}`);
      }
    }

    let masterWav = await concatWavBuffers(segments, Number(crossfadeMs ?? 1500));

    const postFilters: string[] = [];
    if (compressor) {
      postFilters.push("acompressor=threshold=-18dB:ratio=2.8:attack=5:release=80");
    }
    if (normalize) {
      postFilters.push("loudnorm=I=-14:TP=-1");
    }
    if (postFilters.length > 0) {
      masterWav = await withTempFile("wav", masterWav, async (inP) =>
        withTempFile("wav", null, async (outP) => {
          await runFfmpeg(["-i", inP, "-af", postFilters.join(","), outP]);
          return fs.readFileSync(outP);
        })
      );
    }

    const fmt = format === "wav" ? "wav" : "mp3";
    const exported = await exportAudioBuffer(masterWav, fmt, bitrate || "192k", outName || "İmaj FM Yayın");
    const outFile = `${safeFilename(outName || "ImajFM_Yayin")}.${exported.ext}`;
    fs.writeFileSync(path.join(DIRS.output, outFile), exported.data);

    const metrics = await measureAudioMetrics(exported.data, exported.ext);
    res.json({
      dataBase64: exported.data.toString("base64"),
      ext: exported.ext,
      filename: outFile,
      sizeMb: Number((exported.data.length / (1024 * 1024)).toFixed(2)),
      metrics,
      logs,
    });
  } catch (err) {
    res.status(500).json({ error: err instanceof Error ? err.message : "Master render hatası" });
  }
});

app.post("/api/automation/chain-render", async (req, res) => {
  try {
    const { items, fonFile, crossfadeMs, format, outName } = req.body || {};
    const fonPath = fonFile ? path.join(DIRS.fon, path.basename(fonFile)) : null;
    const segments: Buffer[] = [];

    for (const item of items || []) {
      if (item.anonsBasBase64 && fonPath && fs.existsSync(fonPath)) {
        segments.push(
          await mixFonAndVoice({
            fonPath,
            voiceBuf: Buffer.from(item.anonsBasBase64, "base64"),
            fonVolDb: -8,
            duckDb: -16,
          })
        );
      }
      if (item.songFilename) {
        const sp = path.join(DIRS.playlist, path.basename(item.songFilename));
        if (fs.existsSync(sp)) {
          segments.push(
            await withTempFile("wav", null, async (outP) => {
              await runFfmpeg(["-i", sp, "-ar", "44100", "-ac", "2", "-af", "loudnorm=I=-14:TP=-1", outP]);
              return fs.readFileSync(outP);
            })
          );
        }
      }
      if (item.anonsSonBase64 && fonPath && fs.existsSync(fonPath)) {
        segments.push(
          await mixFonAndVoice({
            fonPath,
            voiceBuf: Buffer.from(item.anonsSonBase64, "base64"),
            fonVolDb: -8,
            duckDb: -16,
          })
        );
      }
    }

    if (segments.length === 0) {
      return res.status(400).json({ error: "Zincir yayın için birleştirilecek ses bulunamadı." });
    }
    const master = await concatWavBuffers(segments, Number(crossfadeMs ?? 1000));
    const fmt = format === "wav" ? "wav" : "mp3";
    const exported = await exportAudioBuffer(master, fmt, "192k", outName || "Zincir Yayın");
    const metrics = await measureAudioMetrics(exported.data, exported.ext);
    res.json({
      dataBase64: exported.data.toString("base64"),
      ext: exported.ext,
      filename: `${safeFilename(outName || "Zincir")}.${exported.ext}`,
      metrics,
    });
  } catch (err) {
    res.status(500).json({ error: err instanceof Error ? err.message : "Zincir yayın hatası" });
  }
});

app.post("/api/automation/concat", upload.array("files"), async (req, res) => {
  try {
    const format = req.body?.format === "mp3" ? "mp3" : "wav";
    const buffers: Buffer[] = [];
    const files = (req.files as Express.Multer.File[]) || [];
    for (const f of files) {
      const w = await withTempFile("bin", f.buffer, async (inP) =>
        withTempFile("wav", null, async (outP) => {
          await convertToStandardWav(inP, outP);
          return fs.readFileSync(outP);
        })
      );
      buffers.push(w);
    }
    if (req.body?.wavsBase64) {
      const arr = typeof req.body.wavsBase64 === "string" ? JSON.parse(req.body.wavsBase64) : req.body.wavsBase64;
      for (const b64 of arr) {
        buffers.push(Buffer.from(b64, "base64"));
      }
    }
    if (buffers.length === 0) return res.status(400).json({ error: "Birleştirilecek ses yok." });
    const merged = await concatWavBuffers(buffers, 250);
    const exported = await exportAudioBuffer(merged, format, "192k", "Birlesik_Yayin");
    res.json({
      dataBase64: exported.data.toString("base64"),
      ext: exported.ext,
    });
  } catch (err) {
    res.status(500).json({ error: err instanceof Error ? err.message : "Birleştirme hatası" });
  }
});

// ─── PODCAST RSS ──────────────────────────────────────────────────────────────
app.post("/api/podcast/rss", async (req, res) => {
  try {
    const { title, desc, author, baseUrl, episodes } = req.body || {};
    if (!Array.isArray(episodes) || episodes.length === 0) {
      return res.status(400).json({ error: "En az bir bölüm seçin." });
    }
    const zip = new JSZip();
    let rss = `<?xml version="1.0" encoding="UTF-8"?>\n<rss xmlns:itunes="http://www.itunes.com/dtd/podcast-1.0.dtd" version="2.0">\n<channel>\n`;
    rss += `    <title>${xmlEscape(title || "İmaj FM Podcast")}</title>\n`;
    rss += `    <description>${xmlEscape(desc || "")}</description>\n`;
    rss += `    <language>tr</language>\n`;
    rss += `    <itunes:author>${xmlEscape(author || "İmaj FM")}</itunes:author>\n`;
    rss += `    <itunes:explicit>no</itunes:explicit>\n`;

    const prefix = baseUrl && String(baseUrl).trim() ? `${String(baseUrl).replace(/\/+$/, "")}/` : "";
    for (const ep of episodes) {
      const buf = Buffer.from(ep.wavBase64, "base64");
      const fn = `episode_${safeFilename(ep.id, 12)}.wav`;
      zip.file(fn, buf);
      const epUrl = xmlEscape(`${prefix}${fn}`);
      rss += `    <item>\n`;
      rss += `        <title>${xmlEscape(ep.title || "Bölüm")}</title>\n`;
      rss += `        <description>${xmlEscape(ep.description || "")}</description>\n`;
      rss += `        <enclosure url="${epUrl}" length="${buf.length}" type="audio/wav"/>\n`;
      rss += `        <pubDate>${new Date().toUTCString()}</pubDate>\n`;
      rss += `        <guid isPermaLink="false">${xmlEscape(ep.id || fn)}</guid>\n`;
      rss += `    </item>\n`;
    }
    rss += `</channel>\n</rss>`;

    fs.writeFileSync(path.join(DIRS.podcast, `podcast_${Date.now()}.xml`), rss, "utf-8");
    const zipBuf = await zip.generateAsync({ type: "nodebuffer" });
    res.json({ xml: rss, zipBase64: zipBuf.toString("base64") });
  } catch (err) {
    res.status(500).json({ error: err instanceof Error ? err.message : "RSS hatası" });
  }
});

// ─── YAYIN TAKVİMİ (SCHEDULES) ───────────────────────────────────────────────
app.get("/api/schedules", (_req, res) => {
  const files = fs.readdirSync(DIRS.schedules).filter((f) => f.endsWith(".json"));
  const list = files
    .map((fn) => {
      try {
        const obj = JSON.parse(fs.readFileSync(path.join(DIRS.schedules, fn), "utf-8"));
        obj._file = fn;
        return obj;
      } catch {
        return null;
      }
    })
    .filter(Boolean)
    .sort((a, b) => `${a.date}${a.time}`.localeCompare(`${b.date}${b.time}`));
  res.json({ schedules: list });
});

app.post("/api/schedules", (req, res) => {
  const { name, date, time, songs, notes } = req.body || {};
  if (!name || !Array.isArray(songs) || songs.length === 0) {
    return res.status(400).json({ error: "Yayın adı ve şarkılar gerekli." });
  }
  const file = `s_${Date.now()}_${uid(4)}_${safeFilename(name)}.json`;
  const obj = {
    id: file,
    name: String(name).trim(),
    date: String(date || ""),
    time: String(time || ""),
    songs,
    notes: String(notes || ""),
    created: new Date().toISOString(),
    status: "pending",
  };
  fs.writeFileSync(path.join(DIRS.schedules, file), JSON.stringify(obj, null, 2));
  res.json({ ok: true, schedule: { ...obj, _file: file } });
});

app.patch("/api/schedules/:file", (req, res) => {
  const fp = path.join(DIRS.schedules, path.basename(String(req.params.file)));
  if (!fs.existsSync(fp)) return res.status(404).json({ error: "Bulunamadı" });
  const obj = JSON.parse(fs.readFileSync(fp, "utf-8"));
  obj.status = obj.status === "completed" ? "pending" : "completed";
  fs.writeFileSync(fp, JSON.stringify(obj, null, 2));
  res.json({ ok: true, status: obj.status });
});

app.delete("/api/schedules/:file", (req, res) => {
  const fp = path.join(DIRS.schedules, path.basename(String(req.params.file)));
  if (fs.existsSync(fp)) fs.unlinkSync(fp);
  res.json({ ok: true });
});

// ─── SES KLONLAMA (RVC VERİ SETİ HAZIRLIK) ──────────────────────────────────
app.get("/api/rvc", (_req, res) => {
  if (!fs.existsSync(DIRS.voice_clones)) return res.json({ clones: [] });
  const dirs = fs
    .readdirSync(DIRS.voice_clones)
    .filter((d) => fs.statSync(path.join(DIRS.voice_clones, d)).isDirectory());
  const clones = dirs.map((c) => {
    const cDir = path.join(DIRS.voice_clones, c);
    const rDir = path.join(DIRS.rvc_workspace, c);
    return {
      name: c,
      rawCount: listAudioFiles(cDir).length,
      segCount: fs.existsSync(rDir) ? listAudioFiles(rDir).length : 0,
    };
  });
  res.json({ clones });
});

app.post("/api/rvc/prepare", upload.array("files"), async (req, res) => {
  try {
    const cloneName = safeFilename(req.body?.cloneName || "Klon", 32);
    const chunkSec = Math.max(5, Math.min(30, Number(req.body?.chunkSec ?? 15)));
    const files = (req.files as Express.Multer.File[]) || [];
    if (files.length === 0) return res.status(400).json({ error: "Ses dosyası yükleyin." });

    const cloneDir = path.join(DIRS.voice_clones, cloneName);
    const rvcDir = path.join(DIRS.rvc_workspace, cloneName);
    fs.mkdirSync(cloneDir, { recursive: true });
    fs.mkdirSync(rvcDir, { recursive: true });

    const zip = new JSZip();
    let totalSegs = 0;

    for (let i = 0; i < files.length; i++) {
      const f = files[i];
      const rawPath = path.join(cloneDir, `${i + 1}_${safeFilename(f.originalname, 30)}.wav`);
      await withTempFile("bin", f.buffer, async (tmpIn) => {
        await runFfmpeg([
          "-i",
          tmpIn,
          "-ar",
          "44100",
          "-ac",
          "1",
          "-af",
          "loudnorm=I=-16:TP=-1",
          rawPath,
        ]);
      });
      const segPattern = path.join(rvcDir, `segment_${String(i + 1).padStart(2, "0")}_%02d.wav`);
      await runFfmpeg([
        "-i",
        rawPath,
        "-f",
        "segment",
        "-segment_time",
        String(chunkSec),
        "-c",
        "copy",
        segPattern,
      ]);
    }

    const segFiles = fs.readdirSync(rvcDir).filter((f) => f.endsWith(".wav")).sort();
    for (const sf of segFiles) {
      const fp = path.join(rvcDir, sf);
      const probe = await probeAudioFile(fp);
      if (probe.duration >= 1.5) {
        zip.file(sf, fs.readFileSync(fp));
        totalSegs++;
      }
    }

    const zipBuf = await zip.generateAsync({ type: "nodebuffer" });
    res.json({
      name: cloneName,
      count: totalSegs,
      zipBase64: zipBuf.toString("base64"),
    });
  } catch (err) {
    res.status(500).json({ error: err instanceof Error ? err.message : "RVC hazırlık hatası" });
  }
});

app.delete("/api/rvc/:name", (req, res) => {
  const name = safeFilename(String(req.params.name), 32);
  fs.rmSync(path.join(DIRS.voice_clones, name), { recursive: true, force: true });
  fs.rmSync(path.join(DIRS.rvc_workspace, name), { recursive: true, force: true });
  res.json({ ok: true });
});

// ─── DÖNÜŞTÜRÜCÜ & NORMALİZASYON ────────────────────────────────────────────
app.post("/api/tools/convert", upload.array("files"), async (req, res) => {
  try {
    const files = (req.files as Express.Multer.File[]) || [];
    if (files.length === 0) return res.status(400).json({ error: "Dosya yükleyin." });
    const fmt = ["mp3", "wav", "ogg", "flac"].includes(req.body?.format) ? req.body.format : "mp3";
    const bitrate = req.body?.bitrate || "192k";
    const sr = Number(req.body?.sampleRate || 44100);
    const ch = req.body?.channels === "Mono (1)" ? "1" : req.body?.channels === "Stereo (2)" ? "2" : null;

    const zip = new JSZip();
    for (const f of files) {
      const base = safeFilename(path.basename(f.originalname, path.extname(f.originalname)), 40);
      const outBytes = await withTempFile("bin", f.buffer, async (inP) =>
        withTempFile(fmt, null, async (outP) => {
          const args = ["-i", inP, "-ar", String(sr)];
          if (ch) args.push("-ac", ch);
          if (fmt === "mp3") args.push("-c:a", "libmp3lame", "-b:a", bitrate);
          if (fmt === "ogg") args.push("-c:a", "libvorbis", "-b:a", bitrate);
          args.push(outP);
          await runFfmpeg(args);
          return fs.readFileSync(outP);
        })
      );
      zip.file(`${base}.${fmt}`, outBytes);
    }
    const zipBuf = await zip.generateAsync({ type: "nodebuffer" });
    res.json({ zipBase64: zipBuf.toString("base64"), count: files.length, format: fmt });
  } catch (err) {
    res.status(500).json({ error: err instanceof Error ? err.message : "Dönüştürme hatası" });
  }
});

app.post("/api/tools/normalize", upload.array("files"), async (req, res) => {
  try {
    const files = (req.files as Express.Multer.File[]) || [];
    if (files.length === 0) return res.status(400).json({ error: "Dosya yükleyin." });
    const targetDbfs = Number(req.body?.targetDbfs ?? -14);
    const doTrim = req.body?.doTrim === "true" || req.body?.doTrim === true;
    const trimThresh = Number(req.body?.trimThresh ?? -45);

    const zip = new JSZip();
    for (const f of files) {
      const base = safeFilename(path.basename(f.originalname, path.extname(f.originalname)), 40);
      const outBytes = await withTempFile("bin", f.buffer, async (inP) =>
        withTempFile("wav", null, async (outP) => {
          const filters: string[] = [];
          if (doTrim) {
            filters.push(
              `silenceremove=start_periods=1:start_duration=0.05:start_threshold=${trimThresh}dB,areverse,silenceremove=start_periods=1:start_duration=0.05:start_threshold=${trimThresh}dB,areverse`
            );
          }
          filters.push(`loudnorm=I=${targetDbfs}:TP=-1`);
          await runFfmpeg(["-i", inP, "-af", filters.join(","), "-ar", "44100", "-ac", "2", outP]);
          return fs.readFileSync(outP);
        })
      );
      zip.file(`${base}_norm.wav`, outBytes);
    }
    const zipBuf = await zip.generateAsync({ type: "nodebuffer" });
    res.json({ zipBase64: zipBuf.toString("base64"), count: files.length });
  } catch (err) {
    res.status(500).json({ error: err instanceof Error ? err.message : "Normalizasyon hatası" });
  }
});

// ─── VITE / STATIC SERVING ON PORT 3000 ──────────────────────────────────────
const PORT = 3000;

async function startServer() {
  if (process.env.NODE_ENV !== "production") {
    const { createServer: createViteServer } = await import("vite");
    const vite = await createViteServer({
      server: { middlewareMode: true, hmr: false },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distDir = path.resolve("dist");
    app.use(express.static(distDir));
    app.get("*", (_req, res) => {
      res.sendFile(path.join(distDir, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`🎙️ İmaj FM TTS Stüdyo listening on http://0.0.0.0:${PORT}`);
  });
}

startServer();
