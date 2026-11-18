import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

export const BASE_DIR = path.resolve("imajfm_data");

export const DIRS = {
  playlist: path.join(BASE_DIR, "playlist"),
  fon: path.join(BASE_DIR, "fon"),
  jingles: path.join(BASE_DIR, "jingles"),
  effects: path.join(BASE_DIR, "effects"),
  output: path.join(BASE_DIR, "output"),
  archive: path.join(BASE_DIR, "archive"),
  uploads: path.join(BASE_DIR, "uploads"),
  anons: path.join(BASE_DIR, "anons"),
  effect_gallery: path.join(BASE_DIR, "effect_gallery"),
  podcast: path.join(BASE_DIR, "podcast"),
  schedules: path.join(BASE_DIR, "schedules"),
  rvc_workspace: path.join(BASE_DIR, "rvc_workspace"),
  voice_clones: path.join(BASE_DIR, "voice_clones"),
} as const;

export function ensureDirs(): void {
  for (const dir of Object.values(DIRS)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

export function safeFilename(s: string, maxLen = 40): string {
  const cleaned = String(s || "dosya")
    .replace(/[^a-zA-Z0-9_\-]/g, "_")
    .slice(0, maxLen);
  return cleaned || "dosya";
}

export function uid(len = 8): string {
  return crypto.randomBytes(Math.ceil(len / 2)).toString("hex").slice(0, len);
}

export function listAudioFiles(dir: string): string[] {
  const exts = new Set([".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"]);
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir)
    .filter((f) => exts.has(path.extname(f).toLowerCase()))
    .sort();
}

export function pcmToWav(
  rawData: Buffer,
  mimeType = "",
  defaultRate = 24000,
  defaultCh = 1,
  sw = 2
): Buffer {
  if (!rawData || rawData.length === 0) return Buffer.alloc(0);
  if (rawData.length > 44 && rawData.subarray(0, 4).toString("ascii") === "RIFF") {
    return rawData;
  }
  let rate = defaultRate;
  let ch = defaultCh;
  if (mimeType) {
    const mRate = mimeType.match(/rate=(\d+)/i);
    if (mRate) rate = parseInt(mRate[1], 10);
    const mCh = mimeType.match(/channels=(\d+)/i);
    if (mCh) ch = parseInt(mCh[1], 10);
  }
  const dataSize = rawData.length;
  const header = Buffer.alloc(44);
  header.write("RIFF", 0);
  header.writeUInt32LE(36 + dataSize, 4);
  header.write("WAVE", 8);
  header.write("fmt ", 12);
  header.writeUInt32LE(16, 16); // PCM chunk size
  header.writeUInt16LE(1, 20); // PCM format
  header.writeUInt16LE(ch, 22);
  header.writeUInt32LE(rate, 24);
  header.writeUInt32LE(rate * ch * sw, 28);
  header.writeUInt16LE(ch * sw, 32);
  header.writeUInt16LE(sw * 8, 34);
  header.write("data", 36);
  header.writeUInt32LE(dataSize, 40);
  return Buffer.concat([header, rawData]);
}

export async function runFfmpeg(args: string[]): Promise<{ stdout: string; stderr: string }> {
  return execFileAsync("ffmpeg", ["-y", "-hide_banner", "-loglevel", "error", ...args], {
    maxBuffer: 50 * 1024 * 1024,
  });
}

export interface AudioProbeResult {
  duration: number;
  sampleRate: number;
  channels: number;
  bitrate: string;
  title: string;
  artist: string;
}

export async function probeAudioFile(filePath: string): Promise<AudioProbeResult> {
  const fallbackTitle = path.basename(filePath, path.extname(filePath));
  const def: AudioProbeResult = {
    duration: 0,
    sampleRate: 44100,
    channels: 2,
    bitrate: "",
    title: fallbackTitle,
    artist: "Bilinmeyen",
  };
  if (!fs.existsSync(filePath)) return def;
  try {
    const { stdout } = await execFileAsync(
      "ffprobe",
      ["-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", filePath],
      { maxBuffer: 10 * 1024 * 1024 }
    );
    const parsed = JSON.parse(stdout);
    const fmt = parsed.format || {};
    const stream = Array.isArray(parsed.streams)
      ? parsed.streams.find((s: Record<string, unknown>) => s.codec_type === "audio") || parsed.streams[0]
      : {};
    const tags = fmt.tags || {};
    const title = tags.title || tags.TITLE || fallbackTitle;
    const artist = tags.artist || tags.ARTIST || tags.album_artist || "Bilinmeyen";
    const dur = parseFloat(fmt.duration || stream?.duration || "0") || 0;
    const sr = parseInt(stream?.sample_rate || "44100", 10) || 44100;
    const ch = parseInt(stream?.channels || "2", 10) || 2;
    const brRaw = parseInt(fmt.bit_rate || stream?.bit_rate || "0", 10) || 0;
    return {
      duration: dur,
      sampleRate: sr,
      channels: ch,
      bitrate: brRaw > 0 ? `${Math.round(brRaw / 1000)}kbps` : "",
      title: String(title),
      artist: String(artist),
    };
  } catch {
    return def;
  }
}

export async function withTempFile<T>(
  ext: string,
  buf: Buffer | null,
  fn: (tmpPath: string) => Promise<T>
): Promise<T> {
  const p = path.join(DIRS.uploads, `_tmp_${uid(10)}.${ext}`);
  try {
    if (buf) fs.writeFileSync(p, buf);
    return await fn(p);
  } finally {
    if (fs.existsSync(p)) {
      try {
        fs.unlinkSync(p);
      } catch {
        // ignore
      }
    }
  }
}

export interface AudioMetrics {
  dbfs: string;
  peak: string;
  clip: string;
  qs: number;
  duration: number;
}

export function wavDurationFromBuffer(wb: Buffer): number {
  if (!wb || wb.length < 44) return 0;
  try {
    if (wb.subarray(0, 4).toString("ascii") === "RIFF") {
      const byteRate = wb.readUInt32LE(28);
      if (byteRate > 0) {
        return Math.max(0, (wb.length - 44) / byteRate);
      }
    }
  } catch {
    // ignore
  }
  return Math.max(0, (wb.length - 44) / (24000 * 2));
}

export async function measureAudioMetrics(audioBuf: Buffer, ext = "wav"): Promise<AudioMetrics> {
  const fallbackDur = ext === "wav" ? wavDurationFromBuffer(audioBuf) : 0;
  if (!audioBuf || audioBuf.length === 0) {
    return { dbfs: "-", peak: "-", clip: "Bilgi Yok", qs: 70, duration: 0 };
  }
  return withTempFile(ext, audioBuf, async (tmpPath) => {
    const probe = await probeAudioFile(tmpPath);
    let meanVol = -18;
    let maxVol = -2;
    try {
      const { stderr } = await execFileAsync(
        "ffmpeg",
        ["-i", tmpPath, "-af", "volumedetect", "-f", "null", "-"],
        { maxBuffer: 10 * 1024 * 1024 }
      );
      const meanMatch = stderr.match(/mean_volume:\s*(-?[\d.]+)\s*dB/);
      const maxMatch = stderr.match(/max_volume:\s*(-?[\d.]+)\s*dB/);
      if (meanMatch) meanVol = parseFloat(meanMatch[1]);
      if (maxMatch) maxVol = parseFloat(maxMatch[1]);
    } catch {
      // fallback
    }

    let qs = 55;
    if (meanVol >= -22 && meanVol <= -10) qs += 20;
    else if (meanVol >= -30 && meanVol < -22) qs += 10;
    if (maxVol >= -5 && maxVol <= -0.5) qs += 20;
    else if (maxVol >= -8 && maxVol < -5) qs += 10;
    if (probe.sampleRate >= 22050) qs += 5;
    qs = Math.min(100, Math.max(0, qs));

    return {
      dbfs: Number.isFinite(meanVol) ? `${meanVol.toFixed(1)} dBFS` : "-∞",
      peak: Number.isFinite(maxVol) ? `${maxVol.toFixed(1)} dBFS` : "-∞",
      clip: maxVol >= -0.1 ? "⚠️ Klipping" : "✅ Temiz",
      qs,
      duration: probe.duration || fallbackDur,
    };
  });
}

export function getEqFilter(preset: string): string {
  switch (preset) {
    case "Broadcast":
      return "acompressor=threshold=-18dB:ratio=3:attack=5:release=80,loudnorm=I=-14:TP=-1:LRA=11";
    case "Warm":
      return "equalizer=f=220:t=q:w=1.2:g=2.5,volume=1dB,loudnorm=I=-14:TP=-1";
    case "AM":
      return "highpass=f=400,lowpass=f=3000,volume=3dB";
    case "Podcast":
      return "loudnorm=I=-16:TP=-1.5,acompressor=threshold=-20dB:ratio=2.5";
    case "Vinyl":
      return "lowpass=f=8000,volume=-2dB,loudnorm=I=-15:TP=-1";
    default:
      return "";
  }
}

export async function applyEqToBuffer(wavBuf: Buffer, eqPreset: string): Promise<Buffer> {
  const f = getEqFilter(eqPreset);
  if (!f) return wavBuf;
  return withTempFile("wav", wavBuf, async (inPath) => {
    return withTempFile("wav", null, async (outPath) => {
      await runFfmpeg(["-i", inPath, "-af", f, "-ar", "44100", "-ac", "2", outPath]);
      return fs.readFileSync(outPath);
    });
  });
}

export interface EffectParams {
  low?: number;
  high?: number;
  gain?: number;
  noise?: number;
}

export async function applyEffectToBuffer(
  audioBuf: Buffer,
  params: EffectParams,
  eqPreset = "Ham"
): Promise<Buffer> {
  const low = Math.max(20, Math.min(20000, Number(params.low ?? 100)));
  const high = Math.max(100, Math.min(20000, Number(params.high ?? 12000)));
  const gain = Number(params.gain ?? 0);
  const noise = Number(params.noise ?? 0);

  const filters: string[] = [];
  if (high < 20000) filters.push(`lowpass=f=${high}`);
  if (low > 20) filters.push(`highpass=f=${low}`);
  if (gain !== 0) filters.push(`volume=${gain}dB`);
  const eqf = getEqFilter(eqPreset);
  if (eqf) filters.push(eqf);
  filters.push("loudnorm=I=-14:TP=-1");

  return withTempFile("wav", audioBuf, async (inPath) => {
    return withTempFile("wav", null, async (outPath) => {
      if (noise > 0) {
        const amp = Math.min(noise, 0.25) * 0.4;
        const fc = `[0:a]${filters.join(",")}[main];anoisesrc=color=pink:amplitude=${amp}:r=44100[nz];[main][nz]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1[out]`;
        await runFfmpeg([
          "-i",
          inPath,
          "-filter_complex",
          fc,
          "-map",
          "[out]",
          "-ar",
          "44100",
          "-ac",
          "2",
          outPath,
        ]);
      } else {
        await runFfmpeg(["-i", inPath, "-af", filters.join(","), "-ar", "44100", "-ac", "2", outPath]);
      }
      return fs.readFileSync(outPath);
    });
  });
}

export function generateSignalWav(opts: {
  waveType: string;
  freq: number;
  durMs: number;
  count: number;
  gapMs: number;
  db: number;
}): Buffer {
  const sr = 44100;
  const amp = Math.pow(10, opts.db / 20) * 32767;
  const toneSamples = Math.max(1, Math.floor((opts.durMs / 1000) * sr));
  const gapSamples = Math.max(0, Math.floor((opts.gapMs / 1000) * sr));
  const fadeInSamples = Math.min(toneSamples / 2, Math.floor(0.015 * sr));
  const fadeOutSamples = Math.min(toneSamples / 2, Math.floor(0.025 * sr));

  const singleTone = Buffer.alloc(toneSamples * 2);
  for (let i = 0; i < toneSamples; i++) {
    const t = i / sr;
    const phase = (opts.freq * t) % 1;
    let s = 0;
    if (opts.waveType.includes("Kare")) {
      s = phase < 0.5 ? 1 : -1;
    } else if (opts.waveType.includes("Testere")) {
      s = 2 * phase - 1;
    } else {
      s = Math.sin(2 * Math.PI * opts.freq * t);
    }
    let env = 1;
    if (i < fadeInSamples) env = i / fadeInSamples;
    else if (i > toneSamples - fadeOutSamples) env = (toneSamples - i) / fadeOutSamples;
    const val = Math.max(-32767, Math.min(32767, Math.round(s * amp * env)));
    singleTone.writeInt16LE(val, i * 2);
  }

  const gapBuf = Buffer.alloc(gapSamples * 2);
  const parts: Buffer[] = [];
  for (let c = 0; c < opts.count; c++) {
    if (c > 0 && gapBuf.length > 0) parts.push(gapBuf);
    parts.push(singleTone);
  }
  return pcmToWav(Buffer.concat(parts), "", sr, 1, 2);
}

export async function convertToStandardWav(inputPath: string, outPath: string): Promise<void> {
  await runFfmpeg(["-i", inputPath, "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", outPath]);
}

export async function mixFonAndVoice(opts: {
  fonPath: string;
  voiceBuf: Buffer;
  fonVolDb: number;
  duckDb: number;
  fadeInMs?: number;
  fadeOutMs?: number;
}): Promise<Buffer> {
  const fadeInSec = (opts.fadeInMs ?? 600) / 1000;
  const fadeOutSec = (opts.fadeOutMs ?? 1200) / 1000;
  const leadSec = 0.5;
  const tailSec = 1.8;

  return withTempFile("wav", opts.voiceBuf, async (voicePath) => {
    const voiceProbe = await probeAudioFile(voicePath);
    const voiceLen = Math.max(0.5, voiceProbe.duration || 2.0);
    const totalLen = leadSec + voiceLen + tailSec;
    const duckStart = leadSec;
    const duckEnd = leadSec + voiceLen;
    const rampSec = Math.min(0.4, voiceLen / 4);
    const duckMult = Math.pow(10, opts.duckDb / 20);
    const fonMult = Math.pow(10, opts.fonVolDb / 20);

    // Smooth ducking envelope using ffmpeg volume expression
    const volExpr =
      `if(lt(t,${duckStart}),1,` +
      `if(lt(t,${(duckStart + rampSec).toFixed(3)}),1-(1-${duckMult.toFixed(4)})*(t-${duckStart})/${rampSec.toFixed(3)},` +
      `if(lt(t,${(duckEnd - rampSec).toFixed(3)}),${duckMult.toFixed(4)},` +
      `if(lt(t,${duckEnd}),${duckMult.toFixed(4)}+(1-${duckMult.toFixed(4)})*(t-${(duckEnd - rampSec).toFixed(3)})/${rampSec.toFixed(3)},1))))`;

    const fadeOutStart = Math.max(0, totalLen - fadeOutSec);
    const fc =
      `[0:a]aloop=loop=-1:size=2e+09,atrim=0:${totalLen.toFixed(3)},asetpts=PTS-STARTPTS,` +
      `aformat=sample_rates=44100:channel_layouts=stereo,` +
      `loudnorm=I=-14:TP=-1,volume=${fonMult.toFixed(4)},` +
      `afade=t=in:st=0:d=${fadeInSec.toFixed(3)},` +
      `volume='${volExpr}':eval=frame,` +
      `afade=t=out:st=${fadeOutStart.toFixed(3)}:d=${fadeOutSec.toFixed(3)}[fon];` +
      `[1:a]aformat=sample_rates=44100:channel_layouts=stereo,loudnorm=I=-13:TP=-1,` +
      `adelay=${Math.round(leadSec * 1000)}|${Math.round(leadSec * 1000)}[vox];` +
      `[fon][vox]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1[out]`;

    return withTempFile("wav", null, async (outPath) => {
      await runFfmpeg(["-i", opts.fonPath, "-i", voicePath, "-filter_complex", fc, "-map", "[out]", outPath]);
      return fs.readFileSync(outPath);
    });
  });
}

export async function duckAndOverlay(opts: {
  musicPath: string;
  voiceBuf: Buffer;
  posMs: number;
  duckDb: number;
  rampMs: number;
  voiceGainDb: number;
}): Promise<Buffer> {
  return withTempFile("wav", opts.voiceBuf, async (voicePath) => {
    const musicProbe = await probeAudioFile(opts.musicPath);
    const voiceProbe = await probeAudioFile(voicePath);
    const musicLen = Math.max(1, musicProbe.duration || 10);
    const voiceLen = Math.max(0.2, voiceProbe.duration || 2);
    const posSec = Math.max(0, opts.posMs / 1000);
    const rampSec = Math.max(0.05, opts.rampMs / 1000);
    const duckMult = Math.pow(10, opts.duckDb / 20);
    const voxMult = Math.pow(10, opts.voiceGainDb / 20);

    const startDuck = Math.max(0, posSec - rampSec / 2);
    const endDuck = posSec + voiceLen + rampSec / 2;
    const totalOut = Math.max(musicLen, endDuck + 0.2);

    const volExpr =
      `if(lt(t,${startDuck.toFixed(3)}),1,` +
      `if(lt(t,${(startDuck + rampSec).toFixed(3)}),1-(1-${duckMult.toFixed(4)})*(t-${startDuck.toFixed(3)})/${rampSec.toFixed(3)},` +
      `if(lt(t,${Math.max(startDuck + rampSec, endDuck - rampSec).toFixed(3)}),${duckMult.toFixed(4)},` +
      `if(lt(t,${endDuck.toFixed(3)}),${duckMult.toFixed(4)}+(1-${duckMult.toFixed(4)})*(t-${Math.max(startDuck + rampSec, endDuck - rampSec).toFixed(3)})/${rampSec.toFixed(3)},1))))`;

    const fc =
      `[0:a]aformat=sample_rates=44100:channel_layouts=stereo,apad,atrim=0:${totalOut.toFixed(3)},` +
      `loudnorm=I=-14:TP=-1,volume='${volExpr}':eval=frame[mus];` +
      `[1:a]aformat=sample_rates=44100:channel_layouts=stereo,loudnorm=I=-13.5:TP=-1,volume=${voxMult.toFixed(4)},` +
      `adelay=${Math.round(posSec * 1000)}|${Math.round(posSec * 1000)}[vox];` +
      `[mus][vox]amix=inputs=2:duration=first:normalize=0[out]`;

    return withTempFile("wav", null, async (outPath) => {
      await runFfmpeg(["-i", opts.musicPath, "-i", voicePath, "-filter_complex", fc, "-map", "[out]", outPath]);
      return fs.readFileSync(outPath);
    });
  });
}

export async function concatWavBuffers(buffers: Buffer[], crossfadeMs = 0): Promise<Buffer> {
  const valid = buffers.filter((b) => b && b.length > 44);
  if (valid.length === 0) return Buffer.alloc(0);
  if (valid.length === 1) return valid[0];

  const tempFiles: string[] = [];
  const outPath = path.join(DIRS.uploads, `_concat_out_${uid(10)}.wav`);
  try {
    for (let i = 0; i < valid.length; i++) {
      const p = path.join(DIRS.uploads, `_concat_in_${i}_${uid(8)}.wav`);
      fs.writeFileSync(p, valid[i]);
      tempFiles.push(p);
    }

    const args: string[] = [];
    for (const p of tempFiles) args.push("-i", p);

    const cfSec = Math.max(0, crossfadeMs / 1000);
    if (cfSec >= 0.05 && valid.length >= 2) {
      const probes = await Promise.all(tempFiles.map((p) => probeAudioFile(p)));
      const filters: string[] = [];
      for (let i = 0; i < tempFiles.length; i++) {
        filters.push(`[${i}:a]aformat=sample_rates=44100:channel_layouts=stereo[a${i}]`);
      }
      let prev = "a0";
      for (let i = 1; i < tempFiles.length; i++) {
        const minDur = Math.min(probes[i - 1].duration || 1, probes[i].duration || 1);
        const effCf = Math.min(cfSec, minDur / 3);
        const outTag = i === tempFiles.length - 1 ? "out" : `m${i}`;
        if (effCf >= 0.02) {
          filters.push(`[${prev}][a${i}]acrossfade=d=${effCf.toFixed(3)}:c1=tri:c2=tri[${outTag}]`);
        } else {
          filters.push(`[${prev}][a${i}]concat=n=2:v=0:a=1[${outTag}]`);
        }
        prev = outTag;
      }
      args.push("-filter_complex", filters.join(";"), "-map", "[out]", outPath);
    } else {
      const inputs = tempFiles.map((_, i) => `[${i}:a]aformat=sample_rates=44100:channel_layouts=stereo[a${i}]`).join(";");
      const concatTag = tempFiles.map((_, i) => `[a${i}]`).join("");
      args.push(
        "-filter_complex",
        `${inputs};${concatTag}concat=n=${tempFiles.length}:v=0:a=1[out]`,
        "-map",
        "[out]",
        outPath
      );
    }

    await runFfmpeg(args);
    return fs.readFileSync(outPath);
  } finally {
    for (const p of tempFiles) {
      if (fs.existsSync(p)) {
        try {
          fs.unlinkSync(p);
        } catch {
          // ignore
        }
      }
    }
    if (fs.existsSync(outPath)) {
      try {
        fs.unlinkSync(outPath);
      } catch {
        // ignore
      }
    }
  }
}

export async function generateSilenceWav(ms: number): Promise<Buffer> {
  const sr = 44100;
  const ch = 2;
  const sw = 2;
  const samples = Math.max(0, Math.floor((ms / 1000) * sr));
  return pcmToWav(Buffer.alloc(samples * ch * sw), "", sr, ch, sw);
}

export async function exportAudioBuffer(
  wavBuf: Buffer,
  fmt: "mp3" | "wav",
  bitrate = "192k",
  title = "İmaj FM Yayın"
): Promise<{ data: Buffer; ext: "mp3" | "wav" }> {
  if (fmt === "wav") {
    return { data: wavBuf, ext: "wav" };
  }
  return withTempFile("wav", wavBuf, async (inPath) => {
    return withTempFile("mp3", null, async (outPath) => {
      const dateStr = new Date().toLocaleDateString("tr-TR");
      await runFfmpeg([
        "-i",
        inPath,
        "-c:a",
        "libmp3lame",
        "-b:a",
        bitrate,
        "-metadata",
        `title=${title}`,
        "-metadata",
        "artist=İmaj FM Otomasyon",
        "-metadata",
        `album=İmaj FM Yayın (${dateStr})`,
        outPath,
      ]);
      return { data: fs.readFileSync(outPath), ext: "mp3" };
    });
  });
}

export interface AutomationTrackInput {
  id: string;
  songFilename: string;
  title: string;
  artist: string;
  anonsBase64?: string | null;
  anonsLibFile?: string | null;
  anonsPos: string;
  anonsOffsetSec: number;
  endAnonsEnabled?: boolean;
  endAnonsBase64?: string | null;
  fonBase64?: string | null;
  fonLibFile?: string | null;
  fonVolDb: number;
  jingleBase64?: string | null;
  jingleLibFile?: string | null;
  jinglePos: string;
  duckDb: number;
  anonsGainDb: number;
  rampMs: number;
}

async function resolveAudioToWavBuf(opts: {
  base64?: string | null;
  libDir?: string;
  libFile?: string | null;
}): Promise<Buffer | null> {
  if (opts.base64) {
    const raw = Buffer.from(opts.base64, "base64");
    return withTempFile("bin", raw, async (inP) => {
      return withTempFile("wav", null, async (outP) => {
        await convertToStandardWav(inP, outP);
        return fs.readFileSync(outP);
      });
    });
  }
  if (opts.libDir && opts.libFile) {
    const fp = path.join(opts.libDir, path.basename(opts.libFile));
    if (fs.existsSync(fp)) {
      return withTempFile("wav", null, async (outP) => {
        await convertToStandardWav(fp, outP);
        return fs.readFileSync(outP);
      });
    }
  }
  return null;
}

export async function buildTrackAudio(
  track: AutomationTrackInput,
  crossfadeMs = 1200
): Promise<{ wav: Buffer; notes: string[] }> {
  const songPath = path.join(DIRS.playlist, path.basename(track.songFilename));
  if (!fs.existsSync(songPath)) {
    throw new Error(`Şarkı dosyası bulunamadı: ${track.songFilename}`);
  }

  const notes: string[] = [];
  let songWav: Buffer = await withTempFile("wav", null, async (outP) => {
    await runFfmpeg(["-i", songPath, "-ar", "44100", "-ac", "2", "-af", "loudnorm=I=-14:TP=-1", outP]);
    return fs.readFileSync(outP);
  });

  const anonsWav = await resolveAudioToWavBuf({
    base64: track.anonsBase64,
    libDir: DIRS.anons,
    libFile: track.anonsLibFile,
  });
  const endAnonsWav = track.endAnonsEnabled
    ? await resolveAudioToWavBuf({ base64: track.endAnonsBase64 })
    : null;
  const fonWav = await resolveAudioToWavBuf({
    base64: track.fonBase64,
    libDir: DIRS.fon,
    libFile: track.fonLibFile,
  });
  const jingleWav = await resolveAudioToWavBuf({
    base64: track.jingleBase64,
    libDir: DIRS.jingles,
    libFile: track.jingleLibFile,
  });

  let preBlock: Uint8Array | null = null;
  let postBlock: Uint8Array | null = null;

  if (anonsWav) {
    if (track.anonsPos.startsWith("⏮️")) {
      let anonsBlk: Buffer = anonsWav;
      if (fonWav) {
        anonsBlk = await withTempFile("wav", fonWav, async (fp) =>
          mixFonAndVoice({ fonPath: fp, voiceBuf: anonsWav, fonVolDb: track.fonVolDb, duckDb: track.duckDb })
        );
      }
      if (jingleWav && track.jinglePos === "Anons Öncesi") {
        preBlock = await concatWavBuffers([jingleWav, anonsBlk], Math.min(400, crossfadeMs));
        notes.push("Jingle → Anons (Başı)");
      } else {
        preBlock = anonsBlk;
        notes.push("Anons (Başı)" + (fonWav ? " + Fon" : ""));
      }
    } else if (track.anonsPos.includes("Başlangıçtan")) {
      songWav = await withTempFile("wav", songWav, async (sp) =>
        duckAndOverlay({
          musicPath: sp,
          voiceBuf: anonsWav,
          posMs: Math.round(track.anonsOffsetSec * 1000),
          duckDb: track.duckDb,
          rampMs: track.rampMs,
          voiceGainDb: track.anonsGainDb,
        })
      );
      notes.push(`Talk-Over @${track.anonsOffsetSec.toFixed(1)}s (${track.duckDb.toFixed(0)}dB)`);
    } else if (track.anonsPos.includes("Bitişten")) {
      const songProbe = await withTempFile("wav", songWav, (sp) => probeAudioFile(sp));
      const posMs = Math.max(0, Math.round((songProbe.duration - track.anonsOffsetSec) * 1000));
      songWav = await withTempFile("wav", songWav, async (sp) =>
        duckAndOverlay({
          musicPath: sp,
          voiceBuf: anonsWav,
          posMs,
          duckDb: track.duckDb,
          rampMs: track.rampMs,
          voiceGainDb: track.anonsGainDb,
        })
      );
      notes.push(`Outro Üzeri -${track.anonsOffsetSec.toFixed(1)}s (${track.duckDb.toFixed(0)}dB)`);
    } else if (track.anonsPos.startsWith("⏭️")) {
      let anonsBlk: Buffer = anonsWav;
      if (fonWav) {
        anonsBlk = await withTempFile("wav", fonWav, async (fp) =>
          mixFonAndVoice({ fonPath: fp, voiceBuf: anonsWav, fonVolDb: track.fonVolDb, duckDb: track.duckDb })
        );
      }
      postBlock = anonsBlk;
      notes.push("Anons (Sonu)" + (fonWav ? " + Fon" : ""));
    }
  }

  if (endAnonsWav) {
    let endBlk: Buffer = endAnonsWav;
    if (fonWav) {
      endBlk = await withTempFile("wav", fonWav, async (fp) =>
        mixFonAndVoice({ fonPath: fp, voiceBuf: endAnonsWav, fonVolDb: track.fonVolDb, duckDb: track.duckDb })
      );
    }
    postBlock = postBlock ? await concatWavBuffers([postBlock as Buffer, endBlk], 300) : endBlk;
    notes.push("+ Ek Son Anons");
  }

  if (jingleWav) {
    if (track.jinglePos === "Şarkı Başı") {
      preBlock = preBlock ? await concatWavBuffers([preBlock as Buffer, jingleWav], 300) : jingleWav;
      notes.push("Jingle (Baş)");
    } else if (track.jinglePos === "Şarkı Sonu") {
      postBlock = postBlock ? await concatWavBuffers([jingleWav, postBlock as Buffer], 300) : jingleWav;
      notes.push("Jingle (Son)");
    }
  }

  const pieces: Buffer[] = [];
  if (preBlock) pieces.push(preBlock as Buffer);
  pieces.push(songWav);
  if (postBlock) pieces.push(postBlock as Buffer);

  const combined =
    pieces.length > 1 ? await concatWavBuffers(pieces, Math.min(crossfadeMs, 800)) : songWav;

  return { wav: combined, notes };
}
