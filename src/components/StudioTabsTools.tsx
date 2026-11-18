import React, { useState } from "react";
import JSZip from "jszip";
import { EFFECT_PRESETS, EQ_OPTS, VOICES, type ThemeConfig } from "../constants";
import type {
  ArchiveItem,
  EffectPresetItem,
  FavoriteItem,
  LibraryFile,
  RvcCloneInfo,
  ScheduleItem,
} from "../types";
import {
  base64ToBlob,
  base64ToDataUrl,
  downloadBase64,
  downloadText,
  fmtDur,
} from "../utils/audioClient";
import { WaveformCanvas } from "./WaveformCanvas";

interface StudioTabsToolsProps {
  activeTab: number;
  theme: ThemeConfig;
  archive: ArchiveItem[];
  setArchive: React.Dispatch<React.SetStateAction<ArchiveItem[]>>;
  setFavorites: React.Dispatch<React.SetStateAction<FavoriteItem[]>>;
  libSongs: LibraryFile[];
  libFon: LibraryFile[];
  libJingles: LibraryFile[];
  libEffects: LibraryFile[];
  onRefreshLibrary: () => Promise<void>;
  effectPresets: EffectPresetItem[];
  onRefreshEffects: () => Promise<void>;
  schedules: ScheduleItem[];
  onRefreshSchedules: () => Promise<void>;
  rvcClones: RvcCloneInfo[];
  onRefreshRvc: () => Promise<void>;
  onSendScheduleToYo: (songs: string[]) => void;
  onNotice: (msg: string) => void;
}

export const StudioTabsTools: React.FC<StudioTabsToolsProps> = ({
  activeTab,
  theme,
  archive,
  setArchive,
  setFavorites,
  libSongs,
  libFon,
  libJingles,
  libEffects,
  onRefreshLibrary,
  effectPresets,
  onRefreshEffects,
  schedules,
  onRefreshSchedules,
  rvcClones,
  onRefreshRvc,
  onSendScheduleToYo,
  onNotice,
}) => {
  // ── Tab 9: Ses Efektleri ──────────────────────────────────────────────────
  const [efSub, setEfSub] = useState(0);
  const [efSrcMode, setEfSrcMode] = useState<"file" | "arc">("file");
  const [efFile, setEfFile] = useState<File | null>(null);
  const [efArcId, setEfArcId] = useState("");
  const [efPreset, setEfPreset] = useState("Radyo Efekti");
  const [efEq, setEfEq] = useState("Ham");
  const [efLoading, setEfLoading] = useState(false);
  const [lastEf, setLastEf] = useState<string | null>(null);

  const [newPresetName, setNewPresetName] = useState("");
  const [pLow, setPLow] = useState(300);
  const [pHigh, setPHigh] = useState(8000);
  const [pGain, setPGain] = useState(0);
  const [pNoise, setPNoise] = useState(0);

  const [sigWave, setSigWave] = useState("Sinüs (Sine)");
  const [sigFreq, setSigFreq] = useState(1000);
  const [sigDur, setSigDur] = useState(400);
  const [sigCnt, setSigCnt] = useState(3);
  const [sigGap, setSigGap] = useState(600);
  const [sigDb, setSigDb] = useState(-10);
  const [lastSig, setLastSig] = useState<{ wav: string; name: string } | null>(null);

  // ── Tab 10: Kütüphane ─────────────────────────────────────────────────────
  const [libSub, setLibSub] = useState(0);

  // ── Tab 11: Arşiv ─────────────────────────────────────────────────────────
  const [arcSrch, setArcSrch] = useState("");

  // ── Tab 12: Podcast RSS ───────────────────────────────────────────────────
  const [podTitle, setPodTitle] = useState("İmaj FM Podcast");
  const [podAuthor, setPodAuthor] = useState("İmaj FM");
  const [podBase, setPodBase] = useState("https://imajfm.com/podcast/");
  const [podDesc, setPodDesc] = useState("İmaj FM radyo yayınlarından podcast bölümleri.");
  const [podSelIds, setPodSelIds] = useState<string[]>([]);
  const [lastRss, setLastRss] = useState<{ xml: string; zip: string } | null>(null);

  // ── Tab 13: Yayın Takvimi ─────────────────────────────────────────────────
  const [schSub, setSchSub] = useState(0);
  const [schName, setSchName] = useState("");
  const [schDate, setSchDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [schTime, setSchTime] = useState("08:00");
  const [schSongs, setSchSongs] = useState<string[]>([]);
  const [schNotes, setSchNotes] = useState("");

  // ── Tab 14: Ses Klonlama (RVC) ────────────────────────────────────────────
  const [rvcSub, setRvcSub] = useState(0);
  const [rvcFiles, setRvcFiles] = useState<File[]>([]);
  const [cloneName, setCloneName] = useState("");
  const [rvcChunk, setRvcChunk] = useState(15);
  const [rvcLoading, setRvcLoading] = useState(false);
  const [lastRvc, setLastRvc] = useState<{ zip: string; name: string; cnt: number } | null>(null);

  // ── Tab 15: Dönüştürücü ───────────────────────────────────────────────────
  const [dnSub, setDnSub] = useState(0);
  const [convFiles, setConvFiles] = useState<File[]>([]);
  const [tgtFmt, setTgtFmt] = useState("mp3");
  const [tgtBr, setTgtBr] = useState("192k");
  const [tgtSr, setTgtSr] = useState(44100);
  const [tgtCh, setTgtCh] = useState("Orijinal");
  const [convLoading, setConvLoading] = useState(false);
  const [lastConv, setLastConv] = useState<{ zip: string; cnt: number; fmt: string } | null>(null);

  const [normFiles, setNormFiles] = useState<File[]>([]);
  const [tgtDbfs, setTgtDbfs] = useState(-14.0);
  const [doTrim, setDoTrim] = useState(true);
  const [trimThresh, setTrimThresh] = useState(-45);
  const [normLoading, setNormLoading] = useState(false);
  const [lastNorm, setLastNorm] = useState<{ zip: string; cnt: number } | null>(null);

  // ── TAB 8 (index 8): SES EFEKTLERİ & SİNYAL ÜRETİCİ ──────────────────────
  if (activeTab === 8) {
    const allPresets: Record<string, { low: number; high: number; gain: number; noise: number }> = {
      ...EFFECT_PRESETS,
    };
    for (const cp of effectPresets) {
      allPresets[`⭐ ${cp.name}`] = cp.params;
    }

    const handleApplyEffect = async () => {
      setEfLoading(true);
      try {
        const fd = new FormData();
        fd.append("params", JSON.stringify(allPresets[efPreset] || EFFECT_PRESETS["Radyo Efekti"]));
        fd.append("eq", efEq);
        if (efSrcMode === "file") {
          if (!efFile) throw new Error("Ses dosyası seçin.");
          fd.append("audioFile", efFile);
        } else {
          const aid = efArcId || archive[0]?.id;
          const ent = archive.find((a) => a.id === aid);
          if (!ent) throw new Error("Arşivde ses yok.");
          fd.append("wavBase64", ent.wavBase64);
        }
        const r = await fetch("/api/audio/effect", { method: "POST", body: fd });
        const d = await r.json();
        if (!r.ok) throw new Error(d.error);
        setLastEf(d.wavBase64);
      } catch (e) {
        onNotice(`❌ ${e instanceof Error ? e.message : "Efekt hatası"}`);
      } finally {
        setEfLoading(false);
      }
    };

    const handleGenerateSignal = async (saveToJingles = false) => {
      const r = await fetch("/api/audio/signal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          waveType: sigWave,
          freq: sigFreq,
          durMs: sigDur,
          count: sigCnt,
          gapMs: sigGap,
          db: sigDb,
          saveToJingles,
        }),
      });
      const d = await r.json();
      if (r.ok) {
        setLastSig({ wav: d.wavBase64, name: d.filename });
        if (saveToJingles) {
          await onRefreshLibrary();
          onNotice("✅ Jingle klasörüne kaydedildi!");
        }
      }
    };

    return (
      <div className="tab-panel">
        <div className="rjhdr">
          <h2>🎚️ Ses Efektleri Galerisi &amp; Sinyal Üretici</h2>
          <p>Efekt presetleri · Özel preset kaydetme · Saat başı / Bip jingle ton üreteci</p>
        </div>
        <div className="subtabs-bar">
          {["🎛️ Efekt Uygula", "💾 Preset Kaydet", "📂 Kayıtlı Presetler", "🔔 Sinyal / Bip Üretici"].map((lbl, i) => (
            <button
              key={lbl}
              type="button"
              className={`subtab-btn ${efSub === i ? "active" : ""}`}
              onClick={() => setEfSub(i)}
            >
              {lbl}
            </button>
          ))}
        </div>

        {efSub === 0 && (
          <div style={{ maxWidth: "700px", display: "flex", flexDirection: "column", gap: "10px" }}>
            <div className="radio-group">
              <label className="radio-pill">
                <input type="radio" checked={efSrcMode === "file"} onChange={() => setEfSrcMode("file")} />
                📤 Dosya Yükle
              </label>
              <label className="radio-pill">
                <input type="radio" checked={efSrcMode === "arc"} onChange={() => setEfSrcMode("arc")} />
                📂 Arşivden Seç
              </label>
            </div>
            {efSrcMode === "file" ? (
              <label className="upload-box">
                {efFile ? `✅ ${efFile.name}` : "Ses dosyası yükle (WAV/MP3/OGG)"}
                <input type="file" accept=".wav,.mp3,.ogg" style={{ display: "none" }} onChange={(e) => setEfFile(e.target.files?.[0] || null)} />
              </label>
            ) : (
              <select className="sel" value={efArcId || archive[0]?.id || ""} onChange={(e) => setEfArcId(e.target.value)}>
                {archive.map((e, i) => (
                  <option key={e.id} value={e.id}>
                    {i + 1}. {e.ts_s} | {e.voice} | {e.prev.slice(0, 30)}
                  </option>
                ))}
              </select>
            )}
            <div className="grid-2">
              <select className="sel" value={efPreset} onChange={(e) => setEfPreset(e.target.value)}>
                {Object.keys(allPresets).map((k) => (
                  <option key={k} value={k}>{k}</option>
                ))}
              </select>
              <select className="sel" value={efEq} onChange={(e) => setEfEq(e.target.value)}>
                {EQ_OPTS.map((eq) => (
                  <option key={eq} value={eq}>{eq}</option>
                ))}
              </select>
            </div>
            <button type="button" className="btn btn-primary" disabled={efLoading} onClick={handleApplyEffect}>
              {efLoading ? "⏳ Uygulanıyor…" : "🎛️ Efekti Uygula"}
            </button>
            {lastEf && (
              <div>
                <audio controls src={base64ToDataUrl(lastEf)} />
                <WaveformCanvas wavBase64={lastEf} bgColor={theme.plt_bg} borderColor={theme.border} />
                <button
                  type="button"
                  className="btn btn-secondary btn-full"
                  onClick={() => downloadBase64(lastEf, `efektli_${Date.now()}.wav`, "audio/wav")}
                >
                  💾 Efektli Sesi İndir
                </button>
              </div>
            )}
          </div>
        )}

        {efSub === 1 && (
          <div style={{ maxWidth: "560px", display: "flex", flexDirection: "column", gap: "8px" }}>
            <input className="inp" placeholder="Örn: Gece Radyosu" value={newPresetName} onChange={(e) => setNewPresetName(e.target.value)} />
            <span className="fld-lbl">High-Pass Kesim ({pLow} Hz)</span>
            <input type="range" min={20} max={3000} value={pLow} onChange={(e) => setPLow(Number(e.target.value))} />
            <span className="fld-lbl">Low-Pass Kesim ({pHigh} Hz)</span>
            <input type="range" min={1000} max={20000} value={pHigh} onChange={(e) => setPHigh(Number(e.target.value))} />
            <span className="fld-lbl">Gain ({pGain} dB)</span>
            <input type="range" min={-12} max={12} value={pGain} onChange={(e) => setPGain(Number(e.target.value))} />
            <span className="fld-lbl">Vinyl Gürültü ({pNoise})</span>
            <input type="range" min={0} max={0.1} step={0.002} value={pNoise} onChange={(e) => setPNoise(Number(e.target.value))} />
            <button
              type="button"
              className="btn btn-primary"
              onClick={async () => {
                if (!newPresetName.trim()) return;
                await fetch("/api/effects/presets", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    name: newPresetName.trim(),
                    params: { low: pLow, high: pHigh, gain: pGain, noise: pNoise },
                  }),
                });
                setNewPresetName("");
                await onRefreshEffects();
                onNotice("✅ Preset kaydedildi!");
              }}
            >
              💾 Preset Kaydet
            </button>
          </div>
        )}

        {efSub === 2 && (
          <div>
            {effectPresets.length === 0 ? (
              <div className="card b">Henüz kayıtlı özel preset yok.</div>
            ) : (
              effectPresets.map((p) => (
                <details key={p.name} className="expander">
                  <summary>🎚️ {p.name}</summary>
                  <div className="expander-body">
                    <pre style={{ fontSize: "0.78rem", color: theme.muted }}>{JSON.stringify(p.params, null, 2)}</pre>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={async () => {
                        await fetch(`/api/effects/presets/${encodeURIComponent(p.name)}`, { method: "DELETE" });
                        await onRefreshEffects();
                      }}
                    >
                      🗑️ Sil
                    </button>
                  </div>
                </details>
              ))
            )}
          </div>
        )}

        {efSub === 3 && (
          <div>
            <div className="grid-3">
              <div>
                <span className="fld-lbl">Dalga Formu</span>
                <select className="sel" value={sigWave} onChange={(e) => setSigWave(e.target.value)}>
                  <option value="Sinüs (Sine)">Sinüs (Sine)</option>
                  <option value="Kare (Square)">Kare (Square)</option>
                  <option value="Testere (Sawtooth)">Testere (Sawtooth)</option>
                </select>
                <span className="fld-lbl">Frekans ({sigFreq} Hz)</span>
                <input type="range" min={200} max={3000} step={50} value={sigFreq} onChange={(e) => setSigFreq(Number(e.target.value))} />
              </div>
              <div>
                <span className="fld-lbl">Süre ({sigDur} ms)</span>
                <input type="range" min={100} max={3000} step={50} value={sigDur} onChange={(e) => setSigDur(Number(e.target.value))} />
                <span className="fld-lbl">Tekrar Sayısı ({sigCnt})</span>
                <input type="range" min={1} max={6} step={1} value={sigCnt} onChange={(e) => setSigCnt(Number(e.target.value))} />
              </div>
              <div>
                <span className="fld-lbl">Aralık ({sigGap} ms)</span>
                <input type="range" min={100} max={1500} step={50} value={sigGap} onChange={(e) => setSigGap(Number(e.target.value))} />
                <span className="fld-lbl">Ses ({sigDb} dB)</span>
                <input type="range" min={-30} max={0} step={1} value={sigDb} onChange={(e) => setSigDb(Number(e.target.value))} />
              </div>
            </div>
            <button
              type="button"
              className="btn btn-primary btn-full"
              style={{ marginTop: "10px" }}
              onClick={() => handleGenerateSignal(false)}
            >
              🔔 Sinyal Üret
            </button>
            {lastSig && (
              <div style={{ marginTop: "10px" }}>
                <audio controls src={base64ToDataUrl(lastSig.wav)} />
                <div className="grid-2" style={{ gap: "8px" }}>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => downloadBase64(lastSig.wav, lastSig.name, "audio/wav")}
                  >
                    💾 İndir
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => handleGenerateSignal(true)}
                  >
                    📥 Jingle Kütüphanesine Kaydet
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // ── TAB 9 (index 9): KÜTÜPHANE ────────────────────────────────────────────
  if (activeTab === 9) {
    const cats = [
      { key: "playlist", label: "🎵 Şarkılar", files: libSongs, info: "" },
      { key: "fon", label: "🎶 Fon Müzikleri", files: libFon, info: "Anons arkası fon müzikleri." },
      { key: "jingles", label: "🎺 Jinglelar", files: libJingles, info: "İstasyon tanıtım & geçiş jingleları." },
      { key: "effects", label: "🎭 Efektler", files: libEffects, info: "Saat başı, alkış ve geçiş efektleri." },
    ];
    const cur = cats[libSub];
    const totalDur = cur.files.reduce((acc, f) => acc + (f.duration || 0), 0);

    return (
      <div className="tab-panel">
        <span className="sl">▶ Ses Kütüphanesi (ID3 Etiket Destekli)</span>
        <div className="subtabs-bar">
          {cats.map((c, i) => (
            <button
              key={c.key}
              type="button"
              className={`subtab-btn ${libSub === i ? "active" : ""}`}
              onClick={() => setLibSub(i)}
            >
              {c.label}
            </button>
          ))}
        </div>
        {cur.info && <div className="card b">{cur.info}</div>}
        <label className="upload-box" style={{ marginTop: "8px" }}>
          📤 Dosya Yükle (MP3/WAV/OGG/FLAC/M4A)
          <input
            type="file"
            multiple
            accept=".mp3,.wav,.ogg,.flac,.m4a"
            style={{ display: "none" }}
            onChange={async (e) => {
              const files = e.target.files;
              if (!files || files.length === 0) return;
              const fd = new FormData();
              Array.from(files).forEach((f) => fd.append("files", f));
              await fetch(`/api/library/${cur.key}`, { method: "POST", body: fd });
              await onRefreshLibrary();
              onNotice(`✅ ${files.length} dosya yüklendi!`);
            }}
          />
        </label>
        <div style={{ fontSize: "0.74rem", color: theme.muted, margin: "8px 0" }}>
          {cur.files.length} dosya · {fmtDur(totalDur)} toplam
        </div>
        {cur.files.map((f) => (
          <div key={f.name} className="song-row">
            <span className="song-nm">
              🎵 {f.name.slice(0, 36)} <span style={{ fontWeight: 400, opacity: 0.75 }}>({f.artist})</span>
            </span>
            <span className="song-dur">
              {fmtDur(f.duration)} · {f.sizeKb}KB
            </span>
            <audio
              controls
              style={{ width: "220px", margin: 0 }}
              src={`/api/library/${cur.key}/${encodeURIComponent(f.name)}`}
            />
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={async () => {
                await fetch(`/api/library/${cur.key}/${encodeURIComponent(f.name)}`, { method: "DELETE" });
                await onRefreshLibrary();
              }}
            >
              🗑️
            </button>
          </div>
        ))}
      </div>
    );
  }

  // ── TAB 10 (index 10): ARŞİV ──────────────────────────────────────────────
  if (activeTab === 10) {
    const filtered = archive.filter(
      (h) =>
        !arcSrch.trim() ||
        h.voice.toLowerCase().includes(arcSrch.toLowerCase()) ||
        h.text.toLowerCase().includes(arcSrch.toLowerCase())
    );

    const handleArcZip = async () => {
      const zip = new JSZip();
      for (const e of archive) {
        zip.file(`${e.voice}_${e.id}.wav`, base64ToBlob(e.wavBase64, "audio/wav"));
      }
      const b64 = await zip.generateAsync({ type: "base64" });
      downloadBase64(b64, "imajfm_arsiv.zip", "application/zip");
    };

    return (
      <div className="tab-panel">
        {archive.length === 0 ? (
          <div className="card b">📂 Arşiv henüz boş. TTS üretilen sesler otomatik buraya eklenir.</div>
        ) : (
          <div>
            <div className="row-flex" style={{ marginBottom: "10px" }}>
              <span className="sl" style={{ flex: 2, margin: 0 }}>
                ▶ {archive.length} Kayıt
              </span>
              <button type="button" className="btn btn-secondary" onClick={handleArcZip}>
                📦 Arşiv ZIP İndir
              </button>
              <button type="button" className="btn btn-secondary" onClick={() => setArchive([])}>
                🗑️ Tümünü Sil
              </button>
            </div>
            <input
              className="inp"
              style={{ marginBottom: "12px" }}
              placeholder="🔍 Ses, metin, model ara…"
              value={arcSrch}
              onChange={(e) => setArcSrch(e.target.value)}
            />
            <div className="grid-3">
              {filtered.map((h) => (
                <div key={h.id} className="fav-card">
                  <div className="fav-name">
                    {VOICES[h.voice.split("+")[0]]?.[0] || "🎙️"} {h.voice} · {h.ts_s}
                  </div>
                  <div className="fav-prev">
                    {h.dur}s · {h.mode.toUpperCase()} · {h.prev}
                  </div>
                  <audio controls src={base64ToDataUrl(h.wavBase64)} />
                  <div className="grid-2" style={{ gap: "6px" }}>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => downloadBase64(h.wavBase64, `imajfm_${h.id}.wav`, "audio/wav")}
                    >
                      💾 WAV
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => {
                        setFavorites((prev) => [
                          ...prev,
                          {
                            id: h.id,
                            name: `${h.voice} ${h.ts_s}`,
                            text: h.text,
                            voice: h.voice.split("+")[0],
                            model: h.model,
                            lang: h.lang,
                          },
                        ]);
                        onNotice("⭐ Favorilere eklendi!");
                      }}
                    >
                      ⭐ Favori
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // ── TAB 11 (index 11): PODCAST RSS ────────────────────────────────────────
  if (activeTab === 11) {
    return (
      <div className="tab-panel">
        <div className="rjhdr">
          <h2>📰 Podcast RSS Üretici</h2>
          <p>Arşivdeki seslerden podcast feed oluştur · XML &amp; Bölüm ZIP indir</p>
        </div>
        {archive.length === 0 ? (
          <div className="card a">Arşivde ses yok. Önce ses üretin.</div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            <div className="grid-2">
              <div>
                <span className="fld-lbl">Podcast Başlığı</span>
                <input className="inp" value={podTitle} onChange={(e) => setPodTitle(e.target.value)} />
                <span className="fld-lbl">Yayıncı</span>
                <input className="inp" value={podAuthor} onChange={(e) => setPodAuthor(e.target.value)} />
              </div>
              <div>
                <span className="fld-lbl">Sunucu Base URL</span>
                <input className="inp" value={podBase} onChange={(e) => setPodBase(e.target.value)} />
              </div>
            </div>
            <span className="fld-lbl">Açıklama</span>
            <textarea className="txa" rows={2} value={podDesc} onChange={(e) => setPodDesc(e.target.value)} />
            <span className="fld-lbl">Bölüm Seç</span>
            <div style={{ maxHeight: "160px", overflowY: "auto", border: "1px solid var(--border)", borderRadius: "8px", padding: "8px" }}>
              {archive.map((e, i) => (
                <label key={e.id} className="radio-pill" style={{ display: "flex" }}>
                  <input
                    type="checkbox"
                    checked={podSelIds.includes(e.id)}
                    onChange={(ev) =>
                      setPodSelIds((p) => (ev.target.checked ? [...p, e.id] : p.filter((x) => x !== e.id)))
                    }
                  />
                  {i + 1}. {e.ts_s} | {e.voice} | {e.prev.slice(0, 30)}
                </label>
              ))}
            </div>
            <button
              type="button"
              className="btn btn-primary"
              disabled={podSelIds.length === 0}
              onClick={async () => {
                const episodes = archive
                  .filter((a) => podSelIds.includes(a.id))
                  .map((e) => ({
                    id: e.id,
                    title: `${e.voice} - ${e.ts_s}`,
                    description: e.text.slice(0, 200),
                    wavBase64: e.wavBase64,
                  }));
                const r = await fetch("/api/podcast/rss", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    title: podTitle,
                    desc: podDesc,
                    author: podAuthor,
                    baseUrl: podBase,
                    episodes,
                  }),
                });
                const d = await r.json();
                if (r.ok) setLastRss({ xml: d.xml, zip: d.zipBase64 });
              }}
            >
              📄 RSS Feed Oluştur
            </button>
            {lastRss && (
              <div className="grid-2">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => downloadText(lastRss.xml, "podcast.xml", "application/xml")}
                >
                  📥 RSS XML İndir
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => downloadBase64(lastRss.zip, "podcast_episodes.zip", "application/zip")}
                >
                  📦 Bölümleri ZIP İndir
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // ── TAB 12 (index 12): YAYIN TAKVİMİ ──────────────────────────────────────
  if (activeTab === 12) {
    return (
      <div className="tab-panel">
        <div className="rjhdr">
          <h2>📅 Yayın Takvimi</h2>
          <p>Gelecek yayınları planla · Otomasyona veya Delay Reji'ye aktar</p>
        </div>
        <div className="subtabs-bar">
          {["📋 Yeni Plan", "📂 Planlanan Yayınlar"].map((lbl, i) => (
            <button
              key={lbl}
              type="button"
              className={`subtab-btn ${schSub === i ? "active" : ""}`}
              onClick={() => setSchSub(i)}
            >
              {lbl}
            </button>
          ))}
        </div>

        {schSub === 0 && (
          <div style={{ maxWidth: "600px", display: "flex", flexDirection: "column", gap: "8px" }}>
            <input className="inp" placeholder="Örn: Sabah Kuşağı" value={schName} onChange={(e) => setSchName(e.target.value)} />
            <div className="grid-2">
              <input className="inp" type="date" value={schDate} onChange={(e) => setSchDate(e.target.value)} />
              <input className="inp" type="time" value={schTime} onChange={(e) => setSchTime(e.target.value)} />
            </div>
            <span className="fld-lbl">Şarkılar</span>
            <div style={{ maxHeight: "140px", overflowY: "auto", border: "1px solid var(--border)", borderRadius: "8px", padding: "8px" }}>
              {libSongs.length === 0 ? (
                <span style={{ fontSize: "0.8rem", color: theme.muted }}>Kütüphanede şarkı yok</span>
              ) : (
                libSongs.map((s) => (
                  <label key={s.name} className="radio-pill" style={{ display: "flex" }}>
                    <input
                      type="checkbox"
                      checked={schSongs.includes(s.name)}
                      onChange={(e) =>
                        setSchSongs((p) => (e.target.checked ? [...p, s.name] : p.filter((x) => x !== s.name)))
                      }
                    />
                    {s.name}
                  </label>
                ))
              )}
            </div>
            <textarea className="txa" rows={2} placeholder="Özel notlar…" value={schNotes} onChange={(e) => setSchNotes(e.target.value)} />
            <button
              type="button"
              className="btn btn-primary"
              disabled={!schName.trim() || schSongs.length === 0}
              onClick={async () => {
                await fetch("/api/schedules", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    name: schName.trim(),
                    date: schDate,
                    time: schTime,
                    songs: schSongs,
                    notes: schNotes,
                  }),
                });
                setSchName("");
                setSchSongs([]);
                setSchNotes("");
                await onRefreshSchedules();
                onNotice("✅ Yayın planlandı!");
              }}
            >
              📋 Yayın Planla
            </button>
          </div>
        )}

        {schSub === 1 && (
          <div>
            {schedules.length === 0 ? (
              <div className="card b">Planlanmış yayın yok.</div>
            ) : (
              schedules.map((s) => (
                <details key={s._file} className="expander">
                  <summary>
                    📅 {s.name} — {s.date} {s.time} [{s.status === "completed" ? "✅ Tamamlandı" : "⏳ Bekliyor"}]
                  </summary>
                  <div className="expander-body">
                    <div style={{ marginBottom: "8px", fontSize: "0.83rem" }}>
                      Şarkılar: {s.songs.join(", ")}
                    </div>
                    <div className="grid-3">
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={() => onSendScheduleToYo(s.songs)}
                      >
                        🚀 Otomasyona Aktar
                      </button>
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={async () => {
                          await fetch(`/api/schedules/${encodeURIComponent(s._file)}`, { method: "PATCH" });
                          await onRefreshSchedules();
                        }}
                      >
                        🔄 Durum Değiştir
                      </button>
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={async () => {
                          await fetch(`/api/schedules/${encodeURIComponent(s._file)}`, { method: "DELETE" });
                          await onRefreshSchedules();
                        }}
                      >
                        🗑️ Sil
                      </button>
                    </div>
                  </div>
                </details>
              ))
            )}
          </div>
        )}
      </div>
    );
  }

  // ── TAB 13 (index 13): SES KLONLAMA (RVC HAZIRLIK) ────────────────────────
  if (activeTab === 13) {
    return (
      <div className="tab-panel">
        <div className="rjhdr">
          <h2>🗣️ Ses Klonlama (RVC Hazırlık)</h2>
          <p>RVC eğitimi için 44.1kHz Mono WAV segment veri seti hazırla · Normalize et · ZIP indir</p>
        </div>
        <div className="subtabs-bar">
          {["📤 Veri Seti Hazırla", "📂 Mevcut Klonlar"].map((lbl, i) => (
            <button
              key={lbl}
              type="button"
              className={`subtab-btn ${rvcSub === i ? "active" : ""}`}
              onClick={() => setRvcSub(i)}
            >
              {lbl}
            </button>
          ))}
        </div>

        {rvcSub === 0 && (
          <div style={{ maxWidth: "620px", display: "flex", flexDirection: "column", gap: "10px" }}>
            <label className="upload-box">
              {rvcFiles.length > 0 ? `✅ ${rvcFiles.length} ses dosyası seçildi` : "Ses dosyaları seç (MP3/WAV/OGG/FLAC)"}
              <input
                type="file"
                multiple
                accept=".mp3,.wav,.ogg,.flac"
                style={{ display: "none" }}
                onChange={(e) => setRvcFiles(Array.from(e.target.files || []))}
              />
            </label>
            <div className="grid-2">
              <input className="inp" placeholder="Örn: Kenan_Ses" value={cloneName} onChange={(e) => setCloneName(e.target.value)} />
              <div>
                <span className="fld-lbl">Segment Uzunluğu ({rvcChunk} sn)</span>
                <input type="range" min={5} max={30} value={rvcChunk} onChange={(e) => setRvcChunk(Number(e.target.value))} />
              </div>
            </div>
            <button
              type="button"
              className="btn btn-primary"
              disabled={rvcLoading || rvcFiles.length === 0 || !cloneName.trim()}
              onClick={async () => {
                setRvcLoading(true);
                try {
                  const fd = new FormData();
                  fd.append("cloneName", cloneName.trim());
                  fd.append("chunkSec", String(rvcChunk));
                  rvcFiles.forEach((f) => fd.append("files", f));
                  const r = await fetch("/api/rvc/prepare", { method: "POST", body: fd });
                  const d = await r.json();
                  if (!r.ok) throw new Error(d.error);
                  setLastRvc({ zip: d.zipBase64, name: d.name, cnt: d.count });
                  await onRefreshRvc();
                } catch (e) {
                  onNotice(`❌ ${e instanceof Error ? e.message : "RVC hatası"}`);
                } finally {
                  setRvcLoading(false);
                }
              }}
            >
              {rvcLoading ? "⏳ Hazırlanıyor…" : "📤 Kaydet ve RVC Veri Seti Hazırla"}
            </button>
            {lastRvc && (
              <div>
                <div className="card g">✅ {lastRvc.cnt} adet 44.1kHz Mono WAV segmenti hazır!</div>
                <button
                  type="button"
                  className="btn btn-secondary btn-full"
                  onClick={() => downloadBase64(lastRvc.zip, `${lastRvc.name}_rvc_dataset.zip`, "application/zip")}
                >
                  📦 RVC Veri Seti ZIP İndir
                </button>
              </div>
            )}
          </div>
        )}

        {rvcSub === 1 && (
          <div>
            {rvcClones.length === 0 ? (
              <div className="card b">Kayıtlı ses klonu yok.</div>
            ) : (
              rvcClones.map((c) => (
                <details key={c.name} className="expander">
                  <summary>
                    🗣️ {c.name} ({c.rawCount} ham · {c.segCount} segment)
                  </summary>
                  <div className="expander-body">
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={async () => {
                        await fetch(`/api/rvc/${encodeURIComponent(c.name)}`, { method: "DELETE" });
                        await onRefreshRvc();
                      }}
                    >
                      🗑️ Sil
                    </button>
                  </div>
                </details>
              ))
            )}
          </div>
        )}
      </div>
    );
  }

  // ── TAB 14 (index 14): DÖNÜŞTÜRÜCÜ & NORMALİZASYON ─────────────────────────
  return (
    <div className="tab-panel">
      <div className="rjhdr">
        <h2>🔄 Toplu Ses Dönüştürücü &amp; Normalizasyon</h2>
        <p>Format dönüştürme (MP3/WAV/OGG/FLAC) · Ses Normalizasyon (dBFS) · Sessizlik Kırpma · ZIP</p>
      </div>
      <div className="subtabs-bar">
        {["🔄 Toplu Format Dönüştürücü", "📏 Ses Normalizasyon & Temizleme"].map((lbl, i) => (
          <button
            key={lbl}
            type="button"
            className={`subtab-btn ${dnSub === i ? "active" : ""}`}
            onClick={() => setDnSub(i)}
          >
            {lbl}
          </button>
        ))}
      </div>

      {dnSub === 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <label className="upload-box">
            {convFiles.length > 0 ? `✅ ${convFiles.length} dosya seçildi` : "Dönüştürülecek Dosyalar (MP3/WAV/OGG/FLAC/M4A/AAC)"}
            <input
              type="file"
              multiple
              accept=".mp3,.wav,.ogg,.flac,.m4a,.aac"
              style={{ display: "none" }}
              onChange={(e) => setConvFiles(Array.from(e.target.files || []))}
            />
          </label>
          <div className="grid-4">
            <select className="sel" value={tgtFmt} onChange={(e) => setTgtFmt(e.target.value)}>
              {["mp3", "wav", "ogg", "flac"].map((f) => (
                <option key={f} value={f}>{f}</option>
              ))}
            </select>
            <select className="sel" value={tgtBr} onChange={(e) => setTgtBr(e.target.value)}>
              {["128k", "192k", "256k", "320k"].map((b) => (
                <option key={b} value={b}>{b}</option>
              ))}
            </select>
            <select className="sel" value={tgtSr} onChange={(e) => setTgtSr(Number(e.target.value))}>
              {[22050, 24000, 44100, 48000].map((s) => (
                <option key={s} value={s}>{s} Hz</option>
              ))}
            </select>
            <select className="sel" value={tgtCh} onChange={(e) => setTgtCh(e.target.value)}>
              {["Orijinal", "Mono (1)", "Stereo (2)"].map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
          <button
            type="button"
            className="btn btn-primary"
            disabled={convLoading || convFiles.length === 0}
            onClick={async () => {
              setConvLoading(true);
              try {
                const fd = new FormData();
                fd.append("format", tgtFmt);
                fd.append("bitrate", tgtBr);
                fd.append("sampleRate", String(tgtSr));
                fd.append("channels", tgtCh);
                convFiles.forEach((f) => fd.append("files", f));
                const r = await fetch("/api/tools/convert", { method: "POST", body: fd });
                const d = await r.json();
                if (!r.ok) throw new Error(d.error);
                setLastConv({ zip: d.zipBase64, cnt: d.count, fmt: d.format });
              } catch (e) {
                onNotice(`❌ ${e instanceof Error ? e.message : "Dönüştürme hatası"}`);
              } finally {
                setConvLoading(false);
              }
            }}
          >
            {convLoading ? "⏳ Dönüştürülüyor…" : "🔄 Toplu Dönüştür"}
          </button>
          {lastConv && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => downloadBase64(lastConv.zip, `donusturulen_${lastConv.fmt}.zip`, "application/zip")}
            >
              📦 {lastConv.cnt} Dosyayı (.{lastConv.fmt}) ZIP İndir
            </button>
          )}
        </div>
      )}

      {dnSub === 1 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <label className="upload-box">
            {normFiles.length > 0 ? `✅ ${normFiles.length} dosya seçildi` : "Normalize Edilecek Dosyalar (MP3/WAV/OGG/FLAC)"}
            <input
              type="file"
              multiple
              accept=".mp3,.wav,.ogg,.flac"
              style={{ display: "none" }}
              onChange={(e) => setNormFiles(Array.from(e.target.files || []))}
            />
          </label>
          <div className="grid-3">
            <div>
              <span className="fld-lbl">Hedef Seviye ({tgtDbfs} dBFS)</span>
              <input type="range" min={-24} max={-3} step={0.5} value={tgtDbfs} onChange={(e) => setTgtDbfs(Number(e.target.value))} />
            </div>
            <label className="radio-pill" style={{ alignSelf: "center" }}>
              <input type="checkbox" checked={doTrim} onChange={(e) => setDoTrim(e.target.checked)} />
              Baş/Son Sessizlik Kırp
            </label>
            <div>
              <span className="fld-lbl">Sessizlik Eşiği ({trimThresh} dBFS)</span>
              <input type="range" min={-60} max={-25} step={1} value={trimThresh} onChange={(e) => setTrimThresh(Number(e.target.value))} />
            </div>
          </div>
          <button
            type="button"
            className="btn btn-primary"
            disabled={normLoading || normFiles.length === 0}
            onClick={async () => {
              setNormLoading(true);
              try {
                const fd = new FormData();
                fd.append("targetDbfs", String(tgtDbfs));
                fd.append("doTrim", String(doTrim));
                fd.append("trimThresh", String(trimThresh));
                normFiles.forEach((f) => fd.append("files", f));
                const r = await fetch("/api/tools/normalize", { method: "POST", body: fd });
                const d = await r.json();
                if (!r.ok) throw new Error(d.error);
                setLastNorm({ zip: d.zipBase64, cnt: d.count });
              } catch (e) {
                onNotice(`❌ ${e instanceof Error ? e.message : "Normalizasyon hatası"}`);
              } finally {
                setNormLoading(false);
              }
            }}
          >
            {normLoading ? "⏳ İşleniyor…" : "📏 Normalize Et & Temizle"}
          </button>
          {lastNorm && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => downloadBase64(lastNorm.zip, "normalize_sesler.zip", "application/zip")}
            >
              📦 {lastNorm.cnt} Normalize Dosyayı ZIP İndir
            </button>
          )}
        </div>
      )}
    </div>
  );
};
