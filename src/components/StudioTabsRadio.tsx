import React, { useState } from "react";
import JSZip from "jszip";
import {
  ANONS_POSITIONS,
  FON_TIPLERI,
  JINGLE_POSITIONS,
  LANGUAGES,
  MODELS,
  STYLE_PRESETS,
  VOICES,
} from "../constants";
import type {
  ArchiveItem,
  AudioMetrics,
  AutomationTrack,
  LibraryFile,
  RejiPlanBlock,
  RejiSong,
} from "../types";
import {
  addTime,
  autoBas,
  autoSon,
  base64ToBlob,
  base64ToDataUrl,
  buildRejiPlan,
  downloadBase64,
  downloadText,
  fileToBase64,
  fmtDur,
  songDur,
} from "../utils/audioClient";

interface StudioTabsRadioProps {
  activeTab: number;
  archive: ArchiveItem[];
  playlist: RejiSong[];
  setPlaylist: React.Dispatch<React.SetStateAction<RejiSong[]>>;
  yoTracks: AutomationTrack[];
  setYoTracks: React.Dispatch<React.SetStateAction<AutomationTrack[]>>;
  libSongs: LibraryFile[];
  libFon: LibraryFile[];
  libJingles: LibraryFile[];
  libAnons: LibraryFile[];
  onRefreshLibrary: () => Promise<void>;
  onArchiveAdd: (item: Omit<ArchiveItem, "id" | "ts" | "ts_s" | "model_s" | "prev">) => void;
  onNotice: (msg: string) => void;
}

export const StudioTabsRadio: React.FC<StudioTabsRadioProps> = ({
  activeTab,
  archive,
  playlist,
  setPlaylist,
  yoTracks,
  setYoTracks,
  libSongs,
  libFon,
  libJingles,
  libAnons,
  onRefreshLibrary,
  onArchiveAdd,
  onNotice,
}) => {
  // ── Tab 6: Delay Reji ─────────────────────────────────────────────────────
  const [rjSub, setRjSub] = useState(0);
  const [nt, setNt] = useState("");
  const [na, setNa] = useState("");
  const [ndm, setNdm] = useState(3);
  const [nds, setNds] = useState(30);
  const [rjModel, setRjModel] = useState("gemini-3.8-flash-lite-tts");
  const [rjLang, setRjLang] = useState("tr-TR");
  const [rjVoice, setRjVoice] = useState("Kore");
  const [rjStart, setRjStart] = useState("06:00");
  const [rjPs, setRjPs] = useState("— Seçin —");
  const [rjStyle, setRjStyle] = useState("");
  const [rjPlan, setRjPlan] = useState<RejiPlanBlock[]>([]);
  const [rjBulkLoading, setRjBulkLoading] = useState(false);

  // ── Tab 7: Fon+Anons ──────────────────────────────────────────────────────
  const [mxSub, setMxSub] = useState(0);
  const [mxMdl, setMxMdl] = useState("gemini-3.8-flash-lite-tts");
  const [mxVc, setMxVc] = useState("Kore");
  const [mxFile, setMxFile] = useState<File | null>(null);
  const [mxTxt, setMxTxt] = useState("");
  const [selFon, setSelFon] = useState("");
  const [fvol, setFvol] = useState(-8);
  const [duck, setDuck] = useState(-16);
  const [mxLoading, setMxLoading] = useState(false);
  const [lastMx, setLastMx] = useState<{ wav: string; fn: string } | null>(null);

  const [bulkFonSel, setBulkFonSel] = useState("");
  const [bulkArcIds, setBulkArcIds] = useState<string[]>([]);
  const [bulkFonLoading, setBulkFonLoading] = useState(false);
  const [lastMxBulk, setLastMxBulk] = useState<{ zip: string; count: number } | null>(null);

  const [arc3Id, setArc3Id] = useState("");
  const [sf3, setSf3] = useState("");
  const [mx3Loading, setMx3Loading] = useState(false);
  const [lastMxArc, setLastMxArc] = useState<{ wav: string; fn: string } | null>(null);

  // ── Tab 8: Yayın Otomasyon ────────────────────────────────────────────────
  const [yoSub, setYoSub] = useState(0);
  const [pickLib, setPickLib] = useState<string[]>([]);
  const [gDuck, setGDuck] = useState(-16);
  const [gRamp, setGRamp] = useState(450);
  const [gAnonsGain, setGAnonsGain] = useState(1.5);
  const [gFonVol, setGFonVol] = useState(-8);
  const [gCf, setGCf] = useState(1500);
  const [gGap, setGGap] = useState(0);
  const [gComp, setGComp] = useState(true);
  const [gNorm, setGNorm] = useState(true);
  const [gStartTime, setGStartTime] = useState("08:00");
  const [openJingle, setOpenJingle] = useState("Yok");
  const [closeJingle, setCloseJingle] = useState("Yok");
  const [autoJEvery, setAutoJEvery] = useState(0);
  const [autoJFile, setAutoJFile] = useState("Yok");
  const [yoOutName, setYoOutName] = useState(() => {
    const d = new Date();
    return `ImajFM_Yayin_${String(d.getDate()).padStart(2, "0")}${String(d.getMonth() + 1).padStart(2, "0")}_${String(d.getHours()).padStart(2, "0")}${String(d.getMinutes()).padStart(2, "0")}`;
  });
  const [yoOutFmt, setYoOutFmt] = useState<"mp3" | "wav">("mp3");
  const [yoMp3Br, setYoMp3Br] = useState("192k");
  const [yoRendering, setYoRendering] = useState(false);
  const [yoLogs, setYoLogs] = useState<string[]>([]);
  const [lastYo, setLastYo] = useState<{
    data: string;
    ext: string;
    name: string;
    cnt: number;
    sizeMb: number;
    metrics: AudioMetrics;
    cueText: string;
  } | null>(null);

  // Quick TTS per track state
  const [qTexts, setQTexts] = useState<Record<string, string>>({});
  const [qVoices, setQVoices] = useState<Record<string, string>>({});
  const [qBusy, setQBusy] = useState<Record<string, boolean>>({});

  // Yo2: Chain Render
  const [chFon, setChFon] = useState("");
  const [chCf, setChCf] = useState(1000);
  const [chFmt, setChFmt] = useState<"mp3" | "wav">("mp3");
  const [chName, setChName] = useState("Zincir_Yayin");
  const [chLoading, setChLoading] = useState(false);
  const [lastCh, setLastCh] = useState<{
    data: string;
    ext: string;
    filename: string;
    metrics: AudioMetrics;
  } | null>(null);

  // Yo3: Quick Concat
  const [cntArcIds, setCntArcIds] = useState<string[]>([]);
  const [lastCntArc, setLastCntArc] = useState<string | null>(null);
  const [cntFiles, setCntFiles] = useState<File[]>([]);
  const [lastCntUp, setLastCntUp] = useState<{ data: string; ext: string } | null>(null);

  const makeYoTrackFromLib = (file: LibraryFile, title?: string, artist?: string): AutomationTrack => ({
    id: Math.random().toString(36).slice(2, 10),
    songFilename: file.name,
    title: title || file.title || file.name,
    artist: artist || file.artist || "Bilinmeyen",
    dur: file.duration || 180,
    anonsSrc: "Yok",
    anonsArcId: null,
    anonsLibFile: null,
    anonsBase64: null,
    anonsName: "",
    anonsPos: ANONS_POSITIONS[1],
    anonsOffsetSec: 6.0,
    endAnonsEnabled: false,
    endAnonsSrc: "📂 Arşiv",
    endAnonsArcId: null,
    endAnonsBase64: null,
    fonSrc: "Yok",
    fonLibFile: null,
    fonBase64: null,
    fonVolDb: gFonVol,
    jingleSrc: "Yok",
    jingleLibFile: null,
    jingleBase64: null,
    jinglePos: "Şarkı Başı",
    duckDb: gDuck,
    anonsGainDb: gAnonsGain,
    rampMs: gRamp,
  });

  // ── TAB 5 (index 5): DELAY REJİ ───────────────────────────────────────────
  if (activeTab === 5) {
    const needed = [
      ...playlist
        .map((s, i) => ({ i, s, type: "bas" as const }))
        .filter((x) => x.s.anons_bas && !x.s.anons_wav_bas),
      ...playlist
        .map((s, i) => ({ i, s, type: "son" as const }))
        .filter((x) => x.s.anons_son && !x.s.anons_wav_son),
    ];
    const generatedAnons = [
      ...playlist
        .map((s, i) =>
          s.anons_wav_bas
            ? { name: `${String(i + 1).padStart(2, "0")}_BAS_${s.title.slice(0, 10)}.wav`, b64: s.anons_wav_bas }
            : null
        )
        .filter(Boolean),
      ...playlist
        .map((s, i) =>
          s.anons_wav_son
            ? { name: `${String(i + 1).padStart(2, "0")}_SON_${s.title.slice(0, 10)}.wav`, b64: s.anons_wav_son }
            : null
        )
        .filter(Boolean),
    ] as Array<{ name: string; b64: string }>;

    const handleRejiUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (!files || files.length === 0) return;
      const fd = new FormData();
      Array.from(files).forEach((f) => fd.append("files", f));
      const r = await fetch("/api/library/playlist", { method: "POST", body: fd });
      const data = await r.json();
      await onRefreshLibrary();
      const addedSongs: RejiSong[] = (data.added || []).map((a: { name: string; duration: number; title: string; artist: string }) => {
        const mn = Math.floor((a.duration || 180) / 60);
        const sc = Math.floor((a.duration || 180) % 60);
        return {
          id: Math.random().toString(36).slice(2, 10),
          title: a.title,
          artist: a.artist,
          duration_min: mn,
          duration_sec: sc,
          anons_bas: false,
          anons_son: false,
          anons_bas_text: "",
          anons_son_text: "",
          fon_aktif: false,
          fon_tip: "📻 Radyo Klasik",
          local_file: a.name,
        };
      });
      setPlaylist((p) => [...p, ...addedSongs]);
    };

    const handleBulkReji = async () => {
      if (needed.length === 0) return;
      setRjBulkLoading(true);
      const updated = [...playlist];
      for (const item of needed) {
        const txt =
          item.type === "bas"
            ? item.s.anons_bas_text || autoBas(item.s.artist, item.s.title)
            : item.s.anons_son_text || autoSon(item.s.artist, item.s.title);
        try {
          const r = await fetch("/api/tts/single", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              model: rjModel,
              text: txt,
              voice: rjVoice,
              lang: rjLang,
              style: rjStyle,
            }),
          });
          const data = await r.json();
          if (r.ok && data.wavBase64) {
            if (item.type === "bas") updated[item.i].anons_wav_bas = data.wavBase64;
            else updated[item.i].anons_wav_son = data.wavBase64;
            onArchiveAdd({
              voice: rjVoice,
              model: rjModel,
              lang: rjLang,
              style: rjStyle,
              text: txt,
              wavBase64: data.wavBase64,
              dur: Number(data.metrics.duration.toFixed(1)),
              mode: "reji",
            });
          }
        } catch (err) {
          onNotice(`❌ ${item.s.title}: ${err instanceof Error ? err.message : "Hata"}`);
        }
      }
      setPlaylist(updated);
      setRjBulkLoading(false);
    };

    const handleZipReji = async () => {
      const zip = new JSZip();
      for (const g of generatedAnons) {
        zip.file(g.name, base64ToBlob(g.b64, "audio/wav"));
      }
      const b64 = await zip.generateAsync({ type: "base64" });
      downloadBase64(b64, "reji_anonslar.zip", "application/zip");
    };

    return (
      <div className="tab-panel">
        <div className="rjhdr">
          <h2>📻 Delay Reji — Yayın Otomasyonu</h2>
          <p>Playlist · İnteraktif Sıralama · Şarkı başı/sonu anons · Fon geçişleri · Yayın planı · ZIP</p>
        </div>
        <div className="subtabs-bar">
          {["🎵 Playlist", "⚙️ Ayarlar", "📋 Yayın Planı", "🎬 Üretim & ZIP"].map((lbl, idx) => (
            <button
              key={lbl}
              type="button"
              className={`subtab-btn ${rjSub === idx ? "active" : ""}`}
              onClick={() => setRjSub(idx)}
            >
              {lbl}
            </button>
          ))}
        </div>

        {rjSub === 0 && (
          <div>
            <div className="grid-4" style={{ marginBottom: "8px" }}>
              <input className="inp" placeholder="Şarkı adı…" value={nt} onChange={(e) => setNt(e.target.value)} />
              <input className="inp" placeholder="Sanatçı…" value={na} onChange={(e) => setNa(e.target.value)} />
              <input className="inp" type="number" min={0} max={30} value={ndm} onChange={(e) => setNdm(Number(e.target.value))} />
              <input className="inp" type="number" min={0} max={59} value={nds} onChange={(e) => setNds(Number(e.target.value))} />
            </div>
            <div className="grid-2" style={{ marginBottom: "10px" }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => {
                  if (!nt.trim()) return;
                  setPlaylist((p) => [
                    ...p,
                    {
                      id: Math.random().toString(36).slice(2, 10),
                      title: nt.trim(),
                      artist: na.trim() || "Bilinmeyen",
                      duration_min: ndm,
                      duration_sec: nds,
                      anons_bas: false,
                      anons_son: false,
                      anons_bas_text: "",
                      anons_son_text: "",
                      fon_aktif: false,
                      fon_tip: "📻 Radyo Klasik",
                    },
                  ]);
                  setNt("");
                  setNa("");
                }}
              >
                ➕ Ekle
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => {
                  const demos: Array<[string, string, number, number]> = [
                    ["Gece Yarısı", "Sezen Aksu", 3, 45],
                    ["Yüksek Yüksek Tepelere", "Barış Manço", 4, 12],
                    ["Oy Benim Sarı Turnam", "Neşet Ertaş", 3, 55],
                    ["Hayatımın Anlamı", "MFÖ", 3, 28],
                  ];
                  setPlaylist(
                    demos.map(([t, ar, dm, ds]) => ({
                      id: Math.random().toString(36).slice(2, 10),
                      title: t,
                      artist: ar,
                      duration_min: dm,
                      duration_sec: ds,
                      anons_bas: true,
                      anons_son: false,
                      anons_bas_text: "",
                      anons_son_text: "",
                      fon_aktif: false,
                      fon_tip: "📻 Radyo Klasik",
                    }))
                  );
                }}
              >
                🎲 Demo Playlist
              </button>
            </div>
            <label className="upload-box" style={{ marginBottom: "10px" }}>
              📤 Şarkı dosyaları yükle (MP3/WAV/OGG/FLAC/M4A)
              <input
                type="file"
                multiple
                accept=".mp3,.wav,.ogg,.flac,.m4a"
                style={{ display: "none" }}
                onChange={handleRejiUpload}
              />
            </label>
            {playlist.map((song, si) => (
              <details key={song.id} className="expander">
                <summary>
                  <span>
                    🎵 {String(si + 1).padStart(2, "0")}. {song.artist} — {song.title} [{fmtDur(songDur(song))}]
                  </span>
                </summary>
                <div className="expander-body">
                  <div className="grid-3" style={{ marginBottom: "8px" }}>
                    <label className="radio-pill">
                      <input
                        type="checkbox"
                        checked={song.anons_bas}
                        onChange={(e) => {
                          const checked = e.target.checked;
                          setPlaylist((p) =>
                            p.map((x) =>
                              x.id === song.id
                                ? {
                                    ...x,
                                    anons_bas: checked,
                                    anons_bas_text: x.anons_bas_text || autoBas(x.artist, x.title),
                                  }
                                : x
                            )
                          );
                        }}
                      />
                      🎙️ Baş Anonsu
                    </label>
                    <label className="radio-pill">
                      <input
                        type="checkbox"
                        checked={song.anons_son}
                        onChange={(e) => {
                          const checked = e.target.checked;
                          setPlaylist((p) =>
                            p.map((x) =>
                              x.id === song.id
                                ? {
                                    ...x,
                                    anons_son: checked,
                                    anons_son_text: x.anons_son_text || autoSon(x.artist, x.title),
                                  }
                                : x
                            )
                          );
                        }}
                      />
                      🎙️ Son Anonsu
                    </label>
                    <label className="radio-pill">
                      <input
                        type="checkbox"
                        checked={song.fon_aktif}
                        onChange={(e) =>
                          setPlaylist((p) =>
                            p.map((x) => (x.id === song.id ? { ...x, fon_aktif: e.target.checked } : x))
                          )
                        }
                      />
                      🎶 Fon Geçişi
                    </label>
                  </div>
                  {song.fon_aktif && (
                    <select
                      className="sel"
                      style={{ marginBottom: "6px" }}
                      value={song.fon_tip}
                      onChange={(e) =>
                        setPlaylist((p) =>
                          p.map((x) => (x.id === song.id ? { ...x, fon_tip: e.target.value } : x))
                        )
                      }
                    >
                      {Object.keys(FON_TIPLERI).map((ft) => (
                        <option key={ft} value={ft}>
                          {ft}
                        </option>
                      ))}
                    </select>
                  )}
                  {song.anons_bas && (
                    <div>
                      <span className="fld-lbl">Baş Anons Metni</span>
                      <textarea
                        className="txa"
                        rows={2}
                        value={song.anons_bas_text || autoBas(song.artist, song.title)}
                        onChange={(e) =>
                          setPlaylist((p) =>
                            p.map((x) => (x.id === song.id ? { ...x, anons_bas_text: e.target.value } : x))
                          )
                        }
                      />
                    </div>
                  )}
                  {song.anons_son && (
                    <div>
                      <span className="fld-lbl">Son Anons Metni</span>
                      <textarea
                        className="txa"
                        rows={2}
                        value={song.anons_son_text || autoSon(song.artist, song.title)}
                        onChange={(e) =>
                          setPlaylist((p) =>
                            p.map((x) => (x.id === song.id ? { ...x, anons_son_text: e.target.value } : x))
                          )
                        }
                      />
                    </div>
                  )}
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    style={{ marginTop: "8px" }}
                    onClick={() => setPlaylist((p) => p.filter((x) => x.id !== song.id))}
                  >
                    🗑️ Kaldır
                  </button>
                </div>
              </details>
            ))}
            {playlist.length > 0 && (
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setPlaylist([])}
              >
                🗑️ Playlist'i Temizle
              </button>
            )}
          </div>
        )}

        {rjSub === 1 && (
          <div style={{ display: "flex", flexDirection: "column", gap: "8px", maxWidth: "560px" }}>
            <select className="sel" value={rjModel} onChange={(e) => setRjModel(e.target.value)}>
              {Object.entries(MODELS).map(([k, lbl]) => (
                <option key={k} value={k}>
                  {lbl}
                </option>
              ))}
            </select>
            <select className="sel" value={rjLang} onChange={(e) => setRjLang(e.target.value)}>
              {Object.entries(LANGUAGES).map(([k, lbl]) => (
                <option key={k} value={k}>
                  {lbl}
                </option>
              ))}
            </select>
            <select className="sel" value={rjVoice} onChange={(e) => setRjVoice(e.target.value)}>
              {Object.entries(VOICES).map(([k, [g]]) => (
                <option key={k} value={k}>
                  {g} {k}
                </option>
              ))}
            </select>
            <span className="fld-lbl">Başlangıç Saati</span>
            <input className="inp" value={rjStart} onChange={(e) => setRjStart(e.target.value)} />
            <select
              className="sel"
              value={rjPs}
              onChange={(e) => {
                setRjPs(e.target.value);
                setRjStyle(STYLE_PRESETS[e.target.value] || "");
              }}
            >
              {Object.keys(STYLE_PRESETS).map((k) => (
                <option key={k} value={k}>
                  {k}
                </option>
              ))}
            </select>
            <textarea className="txa" rows={3} value={rjStyle} onChange={(e) => setRjStyle(e.target.value)} />
          </div>
        )}

        {rjSub === 2 && (
          <div>
            <button
              type="button"
              className="btn btn-primary"
              disabled={playlist.length === 0}
              onClick={() => setRjPlan(buildRejiPlan(playlist, rjStart))}
            >
              📋 Yayın Planını Oluştur
            </button>
            <div style={{ marginTop: "10px" }}>
              {rjPlan.map((blk, i) => (
                <div key={i} className="tl-block">
                  <span className="tl-time">{blk.time.slice(0, 5)}</span>
                  <span
                    className={`tl-type ${
                      blk.type === "song" ? "ttype-song" : blk.type === "fon" ? "ttype-fon" : "ttype-anons"
                    }`}
                  >
                    {blk.type.toUpperCase()}
                  </span>
                  <span className="tl-lbl">{blk.label}</span>
                  <span className="tl-dur">{fmtDur(blk.dur)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {rjSub === 3 && (
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {needed.length > 0 && (
              <button
                type="button"
                className="btn btn-primary btn-full"
                disabled={rjBulkLoading}
                onClick={handleBulkReji}
              >
                {rjBulkLoading ? "⏳ Üretiliyor…" : `🔴 ${needed.length} Anonsu Toplu Üret`}
              </button>
            )}
            {generatedAnons.length > 0 ? (
              <button
                type="button"
                className="btn btn-secondary btn-full"
                onClick={handleZipReji}
              >
                📦 {generatedAnons.length} Anonsu ZIP İndir
              </button>
            ) : (
              <div className="card b">Anons üretmek için şarkılara Baş/Son anonsu ekleyin ve üretin.</div>
            )}
          </div>
        )}
      </div>
    );
  }

  // ── TAB 6 (index 6): FON + ANONS MİKSERİ ──────────────────────────────────
  if (activeTab === 6) {
    const fonNames = libFon.map((f) => f.name);
    const activeFon = selFon || fonNames[0] || "";
    const activeBulkFon = bulkFonSel || fonNames[0] || "";
    const activeSf3 = sf3 || fonNames[0] || "";
    const activeArc3 = arc3Id || archive[0]?.id || "";

    const handleMixSingle = async () => {
      if (!activeFon) {
        onNotice("⚠️ Önce Kütüphane sekmesinden Fon müziği yükleyin.");
        return;
      }
      setMxLoading(true);
      try {
        let voiceBase64 = "";
        if (!mxFile && mxTxt.trim()) {
          const rt = await fetch("/api/tts/single", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ model: mxMdl, text: mxTxt, voice: mxVc, lang: "tr-TR", style: "" }),
          });
          const dt = await rt.json();
          if (!rt.ok) throw new Error(dt.error);
          voiceBase64 = dt.wavBase64;
          onArchiveAdd({
            voice: mxVc,
            model: mxMdl,
            lang: "tr-TR",
            style: "",
            text: mxTxt,
            wavBase64: voiceBase64,
            dur: Number(dt.metrics.duration.toFixed(1)),
            mode: "tek",
          });
        }
        const fd = new FormData();
        fd.append("fonFile", activeFon);
        fd.append("fonVolDb", String(fvol));
        fd.append("duckDb", String(duck));
        if (mxFile) fd.append("voiceFile", mxFile);
        else if (voiceBase64) fd.append("voiceBase64", voiceBase64);
        else throw new Error("Anons metni yazın veya dosya yükleyin.");

        const rm = await fetch("/api/audio/fon-mix", { method: "POST", body: fd });
        const dm = await rm.json();
        if (!rm.ok) throw new Error(dm.error);
        setLastMx({ wav: dm.wavBase64, fn: `fon_anons_${Date.now()}.wav` });
      } catch (e) {
        onNotice(`❌ ${e instanceof Error ? e.message : "Miks hatası"}`);
      } finally {
        setMxLoading(false);
      }
    };

    const handleBulkFon = async () => {
      if (!activeBulkFon || bulkArcIds.length === 0) return;
      setBulkFonLoading(true);
      try {
        const items = archive
          .filter((a) => bulkArcIds.includes(a.id))
          .map((a) => ({ id: a.id, wavBase64: a.wavBase64 }));
        const r = await fetch("/api/audio/fon-mix-bulk", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ fonFile: activeBulkFon, items }),
        });
        const d = await r.json();
        if (!r.ok) throw new Error(d.error);
        setLastMxBulk({ zip: d.zipBase64, count: d.count });
      } catch (e) {
        onNotice(`❌ ${e instanceof Error ? e.message : "Hata"}`);
      } finally {
        setBulkFonLoading(false);
      }
    };

    const handleMixArchive3 = async () => {
      const ent = archive.find((a) => a.id === activeArc3);
      if (!ent || !activeSf3) return;
      setMx3Loading(true);
      try {
        const fd = new FormData();
        fd.append("fonFile", activeSf3);
        fd.append("voiceBase64", ent.wavBase64);
        const r = await fetch("/api/audio/fon-mix", { method: "POST", body: fd });
        const d = await r.json();
        if (!r.ok) throw new Error(d.error);
        setLastMxArc({ wav: d.wavBase64, fn: `arc_fon_${ent.id}.wav` });
      } catch (e) {
        onNotice(`❌ ${e instanceof Error ? e.message : "Hata"}`);
      } finally {
        setMx3Loading(false);
      }
    };

    return (
      <div className="tab-panel">
        <div className="rjhdr">
          <h2>🎛️ Fon + Anons Mikseri</h2>
          <p>Anons TTS + Fon müziği · Duck efekti · Fade-in/out · Arşivden miksleme · ZIP</p>
        </div>
        <div className="subtabs-bar">
          {["🎛️ Tek Miksleme", "📦 Toplu Fon", "🗄️ Arşivden"].map((lbl, i) => (
            <button
              key={lbl}
              type="button"
              className={`subtab-btn ${mxSub === i ? "active" : ""}`}
              onClick={() => setMxSub(i)}
            >
              {lbl}
            </button>
          ))}
        </div>

        {mxSub === 0 && (
          <div className="grid-2-asym">
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <select className="sel" value={mxMdl} onChange={(e) => setMxMdl(e.target.value)}>
                {Object.entries(MODELS).map(([k, lbl]) => (
                  <option key={k} value={k}>
                    {lbl}
                  </option>
                ))}
              </select>
              <select className="sel" value={mxVc} onChange={(e) => setMxVc(e.target.value)}>
                {Object.entries(VOICES).map(([k, [g]]) => (
                  <option key={k} value={k}>
                    {g} {k}
                  </option>
                ))}
              </select>
              <label className="upload-box">
                {mxFile ? `✅ ${mxFile.name}` : "📤 Veya Hazır Anons WAV/MP3 Yükle"}
                <input
                  type="file"
                  accept=".wav,.mp3,.ogg"
                  style={{ display: "none" }}
                  onChange={(e) => setMxFile(e.target.files?.[0] || null)}
                />
              </label>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <textarea
                className="txa"
                rows={4}
                placeholder="Anons metni yaz veya soldan ses yükle…"
                value={mxTxt}
                onChange={(e) => setMxTxt(e.target.value)}
              />
              <span className="fld-lbl">Fon Müziği</span>
              <select className="sel" value={activeFon} onChange={(e) => setSelFon(e.target.value)}>
                {fonNames.length === 0 ? (
                  <option value="">Kütüphanede fon yok</option>
                ) : (
                  fonNames.map((fn) => (
                    <option key={fn} value={fn}>
                      {fn}
                    </option>
                  ))
                )}
              </select>
              <span className="fld-lbl">Fon Ses ({fvol} dB)</span>
              <input type="range" min={-24} max={0} value={fvol} onChange={(e) => setFvol(Number(e.target.value))} />
              <span className="fld-lbl">Duck ({duck} dB)</span>
              <input type="range" min={-30} max={-6} value={duck} onChange={(e) => setDuck(Number(e.target.value))} />
              <button
                type="button"
                className="btn btn-primary btn-full"
                disabled={mxLoading}
                onClick={handleMixSingle}
              >
                {mxLoading ? "⏳ Miksleniyor…" : "🎛️ MİKSLE & OLUŞTUR"}
              </button>
              {lastMx && (
                <div>
                  <audio controls src={base64ToDataUrl(lastMx.wav)} />
                  <button
                    type="button"
                    className="btn btn-secondary btn-full"
                    onClick={() => downloadBase64(lastMx.wav, lastMx.fn, "audio/wav")}
                  >
                    📦 WAV İndir
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {mxSub === 1 && (
          <div>
            {archive.length > 0 && fonNames.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", maxWidth: "600px" }}>
                <select className="sel" value={activeBulkFon} onChange={(e) => setBulkFonSel(e.target.value)}>
                  {fonNames.map((fn) => (
                    <option key={fn} value={fn}>
                      {fn}
                    </option>
                  ))}
                </select>
                <span className="fld-lbl">Arşivden Seç</span>
                <div style={{ maxHeight: "200px", overflowY: "auto", border: "1px solid var(--border)", borderRadius: "8px", padding: "8px" }}>
                  {archive.map((e, i) => (
                    <label key={e.id} className="radio-pill" style={{ display: "flex", marginBottom: "4px" }}>
                      <input
                        type="checkbox"
                        checked={bulkArcIds.includes(e.id)}
                        onChange={(ev) =>
                          setBulkArcIds((prev) =>
                            ev.target.checked ? [...prev, e.id] : prev.filter((x) => x !== e.id)
                          )
                        }
                      />
                      {i + 1}. {e.ts_s} · {e.voice} · {e.prev.slice(0, 28)}
                    </label>
                  ))}
                </div>
                <button
                  type="button"
                  className="btn btn-primary"
                  disabled={bulkFonLoading || bulkArcIds.length === 0}
                  onClick={handleBulkFon}
                >
                  {bulkFonLoading ? "⏳ Uygulanıyor…" : "📦 Toplu Uygula"}
                </button>
                {lastMxBulk && (
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => downloadBase64(lastMxBulk.zip, "fon_toplu.zip", "application/zip")}
                  >
                    📦 ZIP İndir ({lastMxBulk.count} dosya)
                  </button>
                )}
              </div>
            ) : (
              <div className="card b">Arşivde ses veya kütüphanede fon yok.</div>
            )}
          </div>
        )}

        {mxSub === 2 && (
          <div>
            {archive.length > 0 && fonNames.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", maxWidth: "600px" }}>
                <select className="sel" value={activeArc3} onChange={(e) => setArc3Id(e.target.value)}>
                  {archive.map((e, i) => (
                    <option key={e.id} value={e.id}>
                      {i + 1}. {e.ts_s} | {e.voice} | {e.prev.slice(0, 32)}
                    </option>
                  ))}
                </select>
                <select className="sel" value={activeSf3} onChange={(e) => setSf3(e.target.value)}>
                  {fonNames.map((fn) => (
                    <option key={fn} value={fn}>
                      {fn}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  className="btn btn-primary"
                  disabled={mx3Loading}
                  onClick={handleMixArchive3}
                >
                  {mx3Loading ? "⏳ Miksleniyor…" : "🎛️ Uygula"}
                </button>
                {lastMxArc && (
                  <div>
                    <audio controls src={base64ToDataUrl(lastMxArc.wav)} />
                    <button
                      type="button"
                      className="btn btn-secondary btn-full"
                      onClick={() => downloadBase64(lastMxArc.wav, lastMxArc.fn, "audio/wav")}
                    >
                      💾 WAV
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="card b">Arşiv veya fon klasörü boş.</div>
            )}
          </div>
        )}
      </div>
    );
  }

  // ── TAB 7 (index 7): GELİŞMİŞ YAYIN OTOMASYONU ────────────────────────────
  const fonList = libFon.map((f) => f.name);
  const jingleList = libJingles.map((f) => f.name);
  const anonsLibList = libAnons.map((f) => f.name);

  const handleYoUploadSongs = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    const fd = new FormData();
    Array.from(files).forEach((f) => fd.append("files", f));
    const r = await fetch("/api/library/playlist", { method: "POST", body: fd });
    const data = await r.json();
    await onRefreshLibrary();
    const added = (data.added || []).map((a: LibraryFile) => makeYoTrackFromLib(a));
    setYoTracks((p) => [...p, ...added]);
  };

  const handleQuickTtsTrack = async (trk: AutomationTrack) => {
    const tid = trk.id;
    const qTxt = qTexts[tid] ?? autoBas(trk.artist, trk.title);
    const qVc = qVoices[tid] ?? "Kore";
    setQBusy((p) => ({ ...p, [tid]: true }));
    try {
      const r = await fetch("/api/tts/single", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model: "gemini-3.8-flash-lite-tts", text: qTxt, voice: qVc, lang: "tr-TR", style: "" }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.error);
      onArchiveAdd({
        voice: qVc,
        model: d.usedModel || "gemini-3.8-flash-lite-tts",
        lang: "tr-TR",
        style: "",
        text: qTxt,
        wavBase64: d.wavBase64,
        dur: Number(d.metrics.duration.toFixed(1)),
        mode: "otomasyon",
      });
      setYoTracks((prev) =>
        prev.map((x) => (x.id === tid ? { ...x, anonsBase64: d.wavBase64, anonsName: `TTS_${qVc}` } : x))
      );
      onNotice(`✅ Üretildi ve atandı (${d.metrics.duration.toFixed(1)}s)!`);
    } catch (e) {
      onNotice(`❌ ${e instanceof Error ? e.message : "Hata"}`);
    } finally {
      setQBusy((p) => ({ ...p, [tid]: false }));
    }
  };

  const handleQuickAiTrack = async (trk: AutomationTrack) => {
    const tid = trk.id;
    setQBusy((p) => ({ ...p, [tid]: true }));
    try {
      const r = await fetch("/api/ai/write-anons", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: `${trk.artist} - ${trk.title}` }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.error);
      setQTexts((p) => ({ ...p, [tid]: d.text }));
    } catch (e) {
      onNotice(`❌ ${e instanceof Error ? e.message : "AI hatası"}`);
    } finally {
      setQBusy((p) => ({ ...p, [tid]: false }));
    }
  };

  const resolveAnonsBase64 = (trk: AutomationTrack) => {
    if (trk.anonsSrc === "📂 Arşivden Seç" && trk.anonsArcId) {
      return archive.find((a) => a.id === trk.anonsArcId)?.wavBase64 || null;
    }
    return trk.anonsBase64;
  };

  const resolveEndAnonsBase64 = (trk: AutomationTrack) => {
    if (!trk.endAnonsEnabled) return null;
    if (trk.endAnonsSrc === "📂 Arşiv" && trk.endAnonsArcId) {
      return archive.find((a) => a.id === trk.endAnonsArcId)?.wavBase64 || null;
    }
    return trk.endAnonsBase64;
  };

  const handlePreviewTrack = async (trk: AutomationTrack) => {
    try {
      const r = await fetch("/api/automation/preview-track", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          crossfadeMs: gCf,
          track: {
            ...trk,
            anonsBase64: resolveAnonsBase64(trk),
            endAnonsBase64: resolveEndAnonsBase64(trk),
          },
        }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.error);
      setYoTracks((prev) => prev.map((x) => (x.id === trk.id ? { ...x, previewBase64: d.wavBase64 } : x)));
    } catch (e) {
      onNotice(`❌ ${e instanceof Error ? e.message : "Önizleme hatası"}`);
    }
  };

  const handleRenderMaster = async (cueLines: string[]) => {
    if (yoTracks.length === 0) return;
    setYoRendering(true);
    setYoLogs([]);
    try {
      const payloadTracks = yoTracks.map((trk) => ({
        ...trk,
        anonsBase64: resolveAnonsBase64(trk),
        endAnonsBase64: resolveEndAnonsBase64(trk),
      }));
      const r = await fetch("/api/automation/render-master", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tracks: payloadTracks,
          openJingle,
          closeJingle,
          autoJEvery,
          autoJFile,
          crossfadeMs: gCf,
          gapMs: gGap,
          compressor: gComp,
          normalize: gNorm,
          format: yoOutFmt,
          bitrate: yoMp3Br,
          outName: yoOutName,
        }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.error);
      setYoLogs(d.logs || []);
      setLastYo({
        data: d.dataBase64,
        ext: d.ext,
        name: yoOutName,
        cnt: yoTracks.length,
        sizeMb: d.sizeMb,
        metrics: d.metrics,
        cueText: `İMAJ FM YAYIN AKIŞI (${yoOutName})\n${"=".repeat(60)}\n${cueLines.join("\n")}`,
      });
      onNotice(`✅ Tam Yayın Hazır (${String(d.ext).toUpperCase()})!`);
    } catch (e) {
      onNotice(`❌ ${e instanceof Error ? e.message : "Render hatası"}`);
    } finally {
      setYoRendering(false);
    }
  };

  let curSecT = 0;
  const cueRows = yoTracks.map((trk, ci) => {
    const stHhmm = addTime(gStartTime, curSecT);
    curSecT += Math.round(trk.dur || 180);
    const hasA = Boolean(trk.anonsBase64 || trk.anonsLibFile || trk.anonsArcId);
    const hasJ = Boolean(trk.jingleBase64 || trk.jingleLibFile);
    const aInfo = (hasA ? trk.anonsPos.split("(")[0].trim() : "Anons Yok") + (trk.endAnonsEnabled ? " + Ek Son" : "");
    const jInfo = hasJ ? `🎺 ${trk.jinglePos}` : "—";
    const line = `${stHhmm} | #${String(ci + 1).padStart(2, "0")} | ${trk.artist} - ${trk.title} (${fmtDur(trk.dur)}) | ${aInfo} | ${jInfo} | Duck: ${trk.duckDb.toFixed(0)}dB`;
    return { stHhmm, aInfo, jInfo, line, trk, ci };
  });

  return (
    <div className="tab-panel">
      <div className="rjhdr">
        <h2>🚀 Akıllı Yayın Otomasyonu — Tam MP3 Yayın Stüdyosu</h2>
        <p>
          Şarkı Yükle &amp; Seç · Her Şarkıya Özel Anons (Başı / İçi Talk-Over / Sonu), Fon &amp; Jingle · Anında Hızlı TTS · Müzik Kısma · MP3 Çıktısı
        </p>
      </div>
      <div className="subtabs-bar">
        {["🎛️ Playlist & Tam Yayın (MP3)", "🔗 Reji Zincir Yayın", "✂️ Hızlı Ses Birleştir"].map((lbl, i) => (
          <button
            key={lbl}
            type="button"
            className={`subtab-btn ${yoSub === i ? "active" : ""}`}
            onClick={() => setYoSub(i)}
          >
            {lbl}
          </button>
        ))}
      </div>

      {yoSub === 0 && (
        <div>
          <span className="sl">1️⃣ Adım: Yayına Şarkı Ekle</span>
          <div className="grid-2">
            <div>
              <label className="upload-box">
                📤 Bilgisayardan Şarkı Yükle (MP3/WAV/OGG/FLAC)
                <input
                  type="file"
                  multiple
                  accept=".mp3,.wav,.ogg,.flac,.m4a"
                  style={{ display: "none" }}
                  onChange={handleYoUploadSongs}
                />
              </label>
            </div>
            <div>
              <span className="fld-lbl">📚 Kütüphanedeki Şarkılardan Seç</span>
              <div style={{ maxHeight: "100px", overflowY: "auto", border: "1px solid var(--border)", borderRadius: "8px", padding: "6px", marginBottom: "6px" }}>
                {libSongs.length === 0 ? (
                  <span style={{ fontSize: "0.78rem", color: "var(--muted)" }}>Kütüphane boş</span>
                ) : (
                  libSongs.map((s) => (
                    <label key={s.name} className="radio-pill" style={{ display: "flex" }}>
                      <input
                        type="checkbox"
                        checked={pickLib.includes(s.name)}
                        onChange={(e) =>
                          setPickLib((p) =>
                            e.target.checked ? [...p, s.name] : p.filter((x) => x !== s.name)
                          )
                        }
                      />
                      {s.name} ({fmtDur(s.duration)})
                    </label>
                  ))
                )}
              </div>
              <div className="grid-2" style={{ gap: "8px" }}>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  disabled={pickLib.length === 0}
                  onClick={() => {
                    const matched = libSongs.filter((s) => pickLib.includes(s.name));
                    setYoTracks((p) => [...p, ...matched.map((m) => makeYoTrackFromLib(m))]);
                    setPickLib([]);
                  }}
                >
                  ➕ Seçilenleri Ekle
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => {
                    let imp = 0;
                    const added: AutomationTrack[] = [];
                    for (const rs of playlist) {
                      const match =
                        libSongs.find((f) => f.name === rs.local_file) ||
                        libSongs.find((f) => f.name.toLowerCase().includes(rs.title.toLowerCase()));
                      if (match) {
                        const trk = makeYoTrackFromLib(match, rs.title, rs.artist);
                        if (rs.anons_wav_bas) {
                          trk.anonsSrc = "📤 Dosyadan Yükle";
                          trk.anonsBase64 = rs.anons_wav_bas;
                          trk.anonsName = "Reji Baş";
                          trk.anonsPos = ANONS_POSITIONS[0];
                        }
                        if (rs.anons_wav_son) {
                          trk.endAnonsEnabled = true;
                          trk.endAnonsBase64 = rs.anons_wav_son;
                        }
                        added.push(trk);
                        imp++;
                      }
                    }
                    if (imp > 0) setYoTracks((p) => [...p, ...added]);
                    else onNotice("⚠️ Reji'de yerel dosyayla eşleşen şarkı yok.");
                  }}
                >
                  📻 Delay Reji'den Aktar
                </button>
              </div>
            </div>
          </div>

          <hr />

          {yoTracks.length === 0 ? (
            <div className="card a">
              🎵 Yayın listeniz boş. Yukarıdan şarkı yükleyin veya kütüphaneden ekleyin.
            </div>
          ) : (
            <div>
              <span className="sl">2️⃣ Adım: Global Müzik Kısma &amp; Yayın Kuralları</span>
              <details className="expander" open>
                <summary>⚙️ Global Ses Kısma (Ducking), Crossfade &amp; Otomatik Jingle Ayarları</summary>
                <div className="expander-body">
                  <div className="grid-4">
                    <div>
                      <span className="fld-lbl">📉 Müzik Kısılma ({gDuck} dB)</span>
                      <input type="range" min={-30} max={-3} step={1} value={gDuck} onChange={(e) => setGDuck(Number(e.target.value))} />
                      <span className="fld-lbl">🎚️ Kısılma Yumuşaklığı ({gRamp} ms)</span>
                      <input type="range" min={150} max={1500} step={50} value={gRamp} onChange={(e) => setGRamp(Number(e.target.value))} />
                    </div>
                    <div>
                      <span className="fld-lbl">🎙️ Anons Kazancı ({gAnonsGain} dB)</span>
                      <input type="range" min={-6} max={9} step={0.5} value={gAnonsGain} onChange={(e) => setGAnonsGain(Number(e.target.value))} />
                      <span className="fld-lbl">🎶 Fon Seviyesi ({gFonVol} dB)</span>
                      <input type="range" min={-24} max={0} step={1} value={gFonVol} onChange={(e) => setGFonVol(Number(e.target.value))} />
                    </div>
                    <div>
                      <span className="fld-lbl">🔀 Crossfade ({gCf} ms)</span>
                      <input type="range" min={0} max={4000} step={100} value={gCf} onChange={(e) => setGCf(Number(e.target.value))} />
                      <span className="fld-lbl">⏸️ Şarkı Arası Boşluk ({gGap} ms)</span>
                      <input type="range" min={0} max={3000} step={100} value={gGap} onChange={(e) => setGGap(Number(e.target.value))} />
                    </div>
                    <div>
                      <label className="radio-pill" style={{ marginTop: "8px" }}>
                        <input type="checkbox" checked={gComp} onChange={(e) => setGComp(e.target.checked)} />
                        📻 Radyo Kompresör
                      </label>
                      <label className="radio-pill" style={{ marginTop: "6px" }}>
                        <input type="checkbox" checked={gNorm} onChange={(e) => setGNorm(e.target.checked)} />
                        📏 Master Normalize (-14 dBFS)
                      </label>
                      <span className="fld-lbl">🕐 Yayın Başlangıç Saati</span>
                      <input className="inp" value={gStartTime} onChange={(e) => setGStartTime(e.target.value)} />
                    </div>
                  </div>
                  <div className="grid-3" style={{ marginTop: "8px" }}>
                    <div>
                      <span className="fld-lbl">🎺 Açılış Jingle</span>
                      <select className="sel" value={openJingle} onChange={(e) => setOpenJingle(e.target.value)}>
                        <option value="Yok">Yok</option>
                        {jingleList.map((j) => (
                          <option key={j} value={j}>{j}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <span className="fld-lbl">🎺 Kapanış Jingle</span>
                      <select className="sel" value={closeJingle} onChange={(e) => setCloseJingle(e.target.value)}>
                        <option value="Yok">Yok</option>
                        {jingleList.map((j) => (
                          <option key={j} value={j}>{j}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <span className="fld-lbl">🔄 Her X Şarkıda Otomatik Jingle</span>
                      <select className="sel" value={autoJEvery} onChange={(e) => setAutoJEvery(Number(e.target.value))}>
                        {[0, 2, 3, 4, 5].map((n) => (
                          <option key={n} value={n}>
                            {n === 0 ? "Kapalı" : `Her ${n} şarkıda bir`}
                          </option>
                        ))}
                      </select>
                      {autoJEvery > 0 && (
                        <select className="sel" style={{ marginTop: "4px" }} value={autoJFile} onChange={(e) => setAutoJFile(e.target.value)}>
                          <option value="Yok">Yok</option>
                          {jingleList.map((j) => (
                            <option key={j} value={j}>{j}</option>
                          ))}
                        </select>
                      )}
                    </div>
                  </div>
                  <button
                    type="button"
                    className="btn btn-secondary btn-full"
                    style={{ marginTop: "10px" }}
                    onClick={() => {
                      setYoTracks((prev) =>
                        prev.map((t) => ({
                          ...t,
                          duckDb: gDuck,
                          anonsGainDb: gAnonsGain,
                          rampMs: gRamp,
                          fonVolDb: gFonVol,
                        }))
                      );
                      onNotice("✅ Tüm şarkılara uygulandı!");
                    }}
                  >
                    ⚡ Bu Müzik Kısma / Ses Değerlerini Tüm Şarkılara Uygula
                  </button>
                </div>
              </details>

              <span className="sl">3️⃣ Adım: Şarkı Bazlı Anons, Fon, Jingle &amp; Konum ({yoTracks.length} Şarkı)</span>
              {yoTracks.map((trk, ti) => {
                const tid = trk.id;
                const updateTrk = (patch: Partial<AutomationTrack>) =>
                  setYoTracks((prev) => prev.map((x) => (x.id === tid ? { ...x, ...patch } : x)));
                const maxSec = Math.max(10, Math.floor((trk.dur || 180) - 2));

                return (
                  <details key={tid} className="expander" open={ti === 0}>
                    <summary>
                      <span>
                        🎵 {String(ti + 1).padStart(2, "0")}. {trk.artist} — {trk.title} [{fmtDur(trk.dur)}] · 📉 {trk.duckDb.toFixed(0)}dB
                      </span>
                    </summary>
                    <div className="expander-body">
                      <div className="row-flex" style={{ marginBottom: "10px" }}>
                        {ti > 0 && (
                          <button
                            type="button"
                            className="btn btn-secondary btn-sm"
                            onClick={() =>
                              setYoTracks((p) => {
                                const arr = [...p];
                                [arr[ti - 1], arr[ti]] = [arr[ti], arr[ti - 1]];
                                return arr;
                              })
                            }
                          >
                            ⬆️ Yukarı
                          </button>
                        )}
                        {ti < yoTracks.length - 1 && (
                          <button
                            type="button"
                            className="btn btn-secondary btn-sm"
                            onClick={() =>
                              setYoTracks((p) => {
                                const arr = [...p];
                                [arr[ti + 1], arr[ti]] = [arr[ti], arr[ti + 1]];
                                return arr;
                              })
                            }
                          >
                            ⬇️ Aşağı
                          </button>
                        )}
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={() => setYoTracks((p) => p.filter((x) => x.id !== tid))}
                        >
                          🗑️ Kaldır
                        </button>
                      </div>

                      <div className="grid-2-asym">
                        <div>
                          <span className="sl2">▸ Ana Anons Seçimi &amp; Konumu</span>
                          <div className="radio-group">
                            {["Yok", "📂 Arşivden Seç", "📚 Kütüphaneden Seç", "📤 Dosyadan Yükle", "🎙️ Anında Hızlı TTS"].map((opt) => (
                              <label key={opt} className="radio-pill">
                                <input
                                  type="radio"
                                  name={`asrc_${tid}`}
                                  checked={trk.anonsSrc === opt}
                                  onChange={() => updateTrk({ anonsSrc: opt })}
                                />
                                {opt}
                              </label>
                            ))}
                          </div>

                          {trk.anonsSrc === "📂 Arşivden Seç" && (
                            <select
                              className="sel"
                              value={trk.anonsArcId || archive[0]?.id || ""}
                              onChange={(e) => updateTrk({ anonsArcId: e.target.value })}
                            >
                              {archive.length === 0 ? (
                                <option value="">Arşivde ses yok</option>
                              ) : (
                                archive.map((a) => (
                                  <option key={a.id} value={a.id}>
                                    {a.ts_s} · {a.voice} · {a.prev.slice(0, 26)}
                                  </option>
                                ))
                              )}
                            </select>
                          )}

                          {trk.anonsSrc === "📚 Kütüphaneden Seç" && (
                            <select
                              className="sel"
                              value={trk.anonsLibFile || anonsLibList[0] || ""}
                              onChange={(e) => updateTrk({ anonsLibFile: e.target.value })}
                            >
                              {anonsLibList.length === 0 ? (
                                <option value="">Anons klasörü boş</option>
                              ) : (
                                anonsLibList.map((f) => (
                                  <option key={f} value={f}>{f}</option>
                                ))
                              )}
                            </select>
                          )}

                          {trk.anonsSrc === "📤 Dosyadan Yükle" && (
                            <label className="upload-box">
                              {trk.anonsName ? `✅ ${trk.anonsName}` : "Anons Dosyası (WAV/MP3/OGG)"}
                              <input
                                type="file"
                                accept=".wav,.mp3,.ogg"
                                style={{ display: "none" }}
                                onChange={async (e) => {
                                  const f = e.target.files?.[0];
                                  if (!f) return;
                                  const b64 = await fileToBase64(f);
                                  updateTrk({ anonsBase64: b64, anonsName: f.name });
                                }}
                              />
                            </label>
                          )}

                          {trk.anonsSrc === "🎙️ Anında Hızlı TTS" && (
                            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                              <div className="row-flex">
                                <select
                                  className="sel"
                                  value={qVoices[tid] ?? "Kore"}
                                  onChange={(e) => setQVoices((p) => ({ ...p, [tid]: e.target.value }))}
                                >
                                  {Object.keys(VOICES).map((v) => (
                                    <option key={v} value={v}>{v}</option>
                                  ))}
                                </select>
                                <button
                                  type="button"
                                  className="btn btn-secondary btn-sm"
                                  style={{ whiteSpace: "nowrap" }}
                                  disabled={qBusy[tid]}
                                  onClick={() => handleQuickAiTrack(trk)}
                                >
                                  ✨ AI Metin
                                </button>
                              </div>
                              <textarea
                                className="txa"
                                rows={3}
                                value={qTexts[tid] ?? autoBas(trk.artist, trk.title)}
                                onChange={(e) => setQTexts((p) => ({ ...p, [tid]: e.target.value }))}
                              />
                              <button
                                type="button"
                                className="btn btn-secondary btn-full"
                                disabled={qBusy[tid]}
                                onClick={() => handleQuickTtsTrack(trk)}
                              >
                                {qBusy[tid] ? "⏳ Üretiliyor…" : "🔴 Anında Seslendir & Ata"}
                              </button>
                            </div>
                          )}

                          {trk.anonsSrc !== "Yok" && (
                            <div style={{ marginTop: "8px" }}>
                              <span className="fld-lbl">📍 Anons Konumu</span>
                              <select
                                className="sel"
                                value={trk.anonsPos}
                                onChange={(e) => updateTrk({ anonsPos: e.target.value })}
                              >
                                {ANONS_POSITIONS.map((pos) => (
                                  <option key={pos} value={pos}>{pos}</option>
                                ))}
                              </select>
                              {(trk.anonsPos.includes("Başlangıçtan") || trk.anonsPos.includes("Bitişten")) && (
                                <div>
                                  <span className="fld-lbl">
                                    ⏱️ {trk.anonsPos.includes("Başlangıçtan") ? "Başlangıçtan Kaç sn Sonra?" : "Bitişten Kaç sn Önce?"} ({trk.anonsOffsetSec}s)
                                  </span>
                                  <input
                                    type="range"
                                    min={trk.anonsPos.includes("Bitişten") ? 3 : 0}
                                    max={Math.min(60, maxSec)}
                                    step={0.5}
                                    value={trk.anonsOffsetSec}
                                    onChange={(e) => updateTrk({ anonsOffsetSec: Number(e.target.value) })}
                                  />
                                </div>
                              )}
                            </div>
                          )}

                          <label className="radio-pill" style={{ marginTop: "8px" }}>
                            <input
                              type="checkbox"
                              checked={trk.endAnonsEnabled}
                              onChange={(e) => updateTrk({ endAnonsEnabled: e.target.checked })}
                            />
                            ➕ Ayrıca Şarkı Sonuna da Ek Anons Ekle
                          </label>
                          {trk.endAnonsEnabled && (
                            <div style={{ marginTop: "4px" }}>
                              <div className="radio-group">
                                {["📂 Arşiv", "📤 Dosya"].map((es) => (
                                  <label key={es} className="radio-pill">
                                    <input
                                      type="radio"
                                      name={`esrc_${tid}`}
                                      checked={trk.endAnonsSrc === es}
                                      onChange={() => updateTrk({ endAnonsSrc: es })}
                                    />
                                    {es}
                                  </label>
                                ))}
                              </div>
                              {trk.endAnonsSrc === "📂 Arşiv" ? (
                                <select
                                  className="sel"
                                  value={trk.endAnonsArcId || archive[0]?.id || ""}
                                  onChange={(e) => updateTrk({ endAnonsArcId: e.target.value })}
                                >
                                  {archive.map((a) => (
                                    <option key={a.id} value={a.id}>
                                      {a.ts_s} · {a.voice} · {a.prev.slice(0, 24)}
                                    </option>
                                  ))}
                                </select>
                              ) : (
                                <label className="upload-box">
                                  Son Anons Dosyası
                                  <input
                                    type="file"
                                    accept=".wav,.mp3,.ogg"
                                    style={{ display: "none" }}
                                    onChange={async (e) => {
                                      const f = e.target.files?.[0];
                                      if (!f) return;
                                      const b64 = await fileToBase64(f);
                                      updateTrk({ endAnonsBase64: b64 });
                                    }}
                                  />
                                </label>
                              )}
                            </div>
                          )}
                        </div>

                        <div>
                          <span className="sl3">▸ Fon Müziği (Şarkı Başı/Sonu Anons Altı)</span>
                          <div className="radio-group">
                            {["Yok", "📚 Fon Kütüphanesi", "📤 Dosyadan Yükle"].map((opt) => (
                              <label key={opt} className="radio-pill">
                                <input
                                  type="radio"
                                  name={`fsrc_${tid}`}
                                  checked={trk.fonSrc === opt}
                                  onChange={() => updateTrk({ fonSrc: opt })}
                                />
                                {opt}
                              </label>
                            ))}
                          </div>
                          {trk.fonSrc === "📚 Fon Kütüphanesi" && (
                            <select
                              className="sel"
                              value={trk.fonLibFile || fonList[0] || ""}
                              onChange={(e) => updateTrk({ fonLibFile: e.target.value })}
                            >
                              {fonList.map((f) => (
                                <option key={f} value={f}>{f}</option>
                              ))}
                            </select>
                          )}
                          {trk.fonSrc === "📤 Dosyadan Yükle" && (
                            <label className="upload-box">
                              Fon Müziği Yükle
                              <input
                                type="file"
                                accept=".mp3,.wav,.ogg"
                                style={{ display: "none" }}
                                onChange={async (e) => {
                                  const f = e.target.files?.[0];
                                  if (!f) return;
                                  updateTrk({ fonBase64: await fileToBase64(f) });
                                }}
                              />
                            </label>
                          )}

                          <span className="sl3">▸ Jingle / Sweeper</span>
                          <div className="radio-group">
                            {["Yok", "📚 Jingle Kütüphanesi", "📤 Dosyadan Yükle"].map((opt) => (
                              <label key={opt} className="radio-pill">
                                <input
                                  type="radio"
                                  name={`jsrc_${tid}`}
                                  checked={trk.jingleSrc === opt}
                                  onChange={() => updateTrk({ jingleSrc: opt })}
                                />
                                {opt}
                              </label>
                            ))}
                          </div>
                          {trk.jingleSrc === "📚 Jingle Kütüphanesi" && (
                            <select
                              className="sel"
                              value={trk.jingleLibFile || jingleList[0] || ""}
                              onChange={(e) => updateTrk({ jingleLibFile: e.target.value })}
                            >
                              {jingleList.map((j) => (
                                <option key={j} value={j}>{j}</option>
                              ))}
                            </select>
                          )}
                          {trk.jingleSrc === "📤 Dosyadan Yükle" && (
                            <label className="upload-box">
                              Jingle Yükle
                              <input
                                type="file"
                                accept=".mp3,.wav,.ogg"
                                style={{ display: "none" }}
                                onChange={async (e) => {
                                  const f = e.target.files?.[0];
                                  if (!f) return;
                                  updateTrk({ jingleBase64: await fileToBase64(f) });
                                }}
                              />
                            </label>
                          )}
                          {trk.jingleSrc !== "Yok" && (
                            <select
                              className="sel"
                              style={{ marginTop: "6px" }}
                              value={trk.jinglePos}
                              onChange={(e) => updateTrk({ jinglePos: e.target.value })}
                            >
                              {JINGLE_POSITIONS.map((jp) => (
                                <option key={jp} value={jp}>{jp}</option>
                              ))}
                            </select>
                          )}

                          <span className="sl3">▸ Müzik Kısma (Ducking) &amp; Ses Dengesi</span>
                          <div className="grid-2" style={{ gap: "8px" }}>
                            <div>
                              <span className="fld-lbl">📉 Kısılma ({trk.duckDb} dB)</span>
                              <input type="range" min={-30} max={-3} step={1} value={trk.duckDb} onChange={(e) => updateTrk({ duckDb: Number(e.target.value) })} />
                              <span className="fld-lbl">🎚️ Geçiş ({trk.rampMs} ms)</span>
                              <input type="range" min={150} max={1500} step={50} value={trk.rampMs} onChange={(e) => updateTrk({ rampMs: Number(e.target.value) })} />
                            </div>
                            <div>
                              <span className="fld-lbl">🎙️ Anons ({trk.anonsGainDb} dB)</span>
                              <input type="range" min={-6} max={9} step={0.5} value={trk.anonsGainDb} onChange={(e) => updateTrk({ anonsGainDb: Number(e.target.value) })} />
                              {trk.fonSrc !== "Yok" && (
                                <>
                                  <span className="fld-lbl">🎶 Fon ({trk.fonVolDb} dB)</span>
                                  <input type="range" min={-24} max={0} step={1} value={trk.fonVolDb} onChange={(e) => updateTrk({ fonVolDb: Number(e.target.value) })} />
                                </>
                              )}
                            </div>
                          </div>

                          <button
                            type="button"
                            className="btn btn-secondary btn-full"
                            style={{ marginTop: "8px" }}
                            onClick={() => handlePreviewTrack(trk)}
                          >
                            🎧 Bu Şarkıyı Önizle
                          </button>
                          {trk.previewBase64 && <audio controls src={base64ToDataUrl(trk.previewBase64)} />}
                        </div>
                      </div>
                    </div>
                  </details>
                );
              })}

              <hr />
              <span className="sl">4️⃣ Adım: Yayın Akışı (Cue Sheet) &amp; Tam MP3 Çıktısı</span>
              {cueRows.map((row) => (
                <div key={row.trk.id} className="tl-block">
                  <span className="tl-time">{row.stHhmm}</span>
                  <span className="tl-type ttype-song">#{String(row.ci + 1).padStart(2, "0")}</span>
                  <span className="tl-lbl">
                    <b>{row.trk.artist} — {row.trk.title}</b> · {row.aInfo} · {row.jInfo} · 📉 {row.trk.duckDb.toFixed(0)}dB
                  </span>
                  <span className="tl-dur">{fmtDur(row.trk.dur)}</span>
                </div>
              ))}

              <div className="grid-4" style={{ marginTop: "12px" }}>
                <input className="inp" value={yoOutName} onChange={(e) => setYoOutName(e.target.value)} />
                <select className="sel" value={yoOutFmt} onChange={(e) => setYoOutFmt(e.target.value as "mp3" | "wav")}>
                  <option value="mp3">MP3</option>
                  <option value="wav">WAV</option>
                </select>
                <select className="sel" value={yoMp3Br} disabled={yoOutFmt !== "mp3"} onChange={(e) => setYoMp3Br(e.target.value)}>
                  {["128k", "192k", "256k", "320k"].map((b) => (
                    <option key={b} value={b}>{b}</option>
                  ))}
                </select>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => {
                    setYoTracks([]);
                    setLastYo(null);
                  }}
                >
                  🗑️ Listeyi Temizle
                </button>
              </div>

              <button
                type="button"
                className="btn btn-primary btn-full"
                style={{ marginTop: "10px" }}
                disabled={yoRendering}
                onClick={() => handleRenderMaster(cueRows.map((r) => r.line))}
              >
                {yoRendering ? "🎙️ Tam yayın kurgulanıyor ve miksleniyor…" : `🚀 TAM YAYINI OLUŞTUR (${yoOutFmt.toUpperCase()})`}
              </button>

              {yoLogs.length > 0 && (
                <div className="card b" style={{ marginTop: "8px" }}>
                  {yoLogs.map((l, i) => (
                    <div key={i}>{l}</div>
                  ))}
                </div>
              )}

              {lastYo && (
                <div style={{ marginTop: "10px" }}>
                  <div className="card g">
                    ✅ <b>{lastYo.name}.{lastYo.ext}</b> · {fmtDur(lastYo.metrics.duration)} · {lastYo.cnt} şarkı · {lastYo.sizeMb} MB · Seviye: {lastYo.metrics.dbfs} ({lastYo.metrics.clip})
                  </div>
                  <audio
                    controls
                    src={base64ToDataUrl(lastYo.data, lastYo.ext === "mp3" ? "audio/mpeg" : "audio/wav")}
                  />
                  <div className="grid-2" style={{ gap: "8px" }}>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() =>
                        downloadBase64(
                          lastYo.data,
                          `${lastYo.name}.${lastYo.ext}`,
                          lastYo.ext === "mp3" ? "audio/mpeg" : "audio/wav"
                        )
                      }
                    >
                      📦 Tam Yayını İndir (.{lastYo.ext.toUpperCase()})
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => downloadText(lastYo.cueText, `${lastYo.name}_cuesheet.txt`)}
                    >
                      📄 Cue Sheet (.TXT)
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {yoSub === 1 && (
        <div>
          <div className="card b">Delay Reji anonsları + Kütüphane şarkıları → Zincir yayın</div>
          {libSongs.length > 0 && fonList.length > 0 && playlist.length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px", maxWidth: "600px", marginTop: "10px" }}>
              <select className="sel" value={chFon || fonList[0]} onChange={(e) => setChFon(e.target.value)}>
                {fonList.map((f) => (
                  <option key={f} value={f}>{f}</option>
                ))}
              </select>
              <span className="fld-lbl">Crossfade ({chCf} ms)</span>
              <input type="range" min={0} max={2000} value={chCf} onChange={(e) => setChCf(Number(e.target.value))} />
              <select className="sel" value={chFmt} onChange={(e) => setChFmt(e.target.value as "mp3" | "wav")}>
                <option value="mp3">mp3</option>
                <option value="wav">wav</option>
              </select>
              <input className="inp" value={chName} onChange={(e) => setChName(e.target.value)} />
              <button
                type="button"
                className="btn btn-primary"
                disabled={chLoading}
                onClick={async () => {
                  setChLoading(true);
                  try {
                    const items = playlist.map((s) => {
                      const match =
                        libSongs.find((f) => f.name === s.local_file) ||
                        libSongs.find((f) => f.name.toLowerCase().includes(s.title.toLowerCase()));
                      return {
                        anonsBasBase64: s.anons_wav_bas || null,
                        anonsSonBase64: s.anons_wav_son || null,
                        songFilename: match?.name || null,
                      };
                    });
                    const r = await fetch("/api/automation/chain-render", {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({
                        items,
                        fonFile: chFon || fonList[0],
                        crossfadeMs: chCf,
                        format: chFmt,
                        outName: chName,
                      }),
                    });
                    const d = await r.json();
                    if (!r.ok) throw new Error(d.error);
                    setLastCh({
                      data: d.dataBase64,
                      ext: d.ext,
                      filename: d.filename,
                      metrics: d.metrics,
                    });
                  } catch (e) {
                    onNotice(`❌ ${e instanceof Error ? e.message : "Hata"}`);
                  } finally {
                    setChLoading(false);
                  }
                }}
              >
                {chLoading ? "⏳ Oluşturuluyor…" : "🔗 ZİNCİR YAYIN"}
              </button>
              {lastCh && (
                <div>
                  <audio
                    controls
                    src={base64ToDataUrl(lastCh.data, lastCh.ext === "mp3" ? "audio/mpeg" : "audio/wav")}
                  />
                  <button
                    type="button"
                    className="btn btn-secondary btn-full"
                    onClick={() =>
                      downloadBase64(
                        lastCh.data,
                        lastCh.filename,
                        lastCh.ext === "mp3" ? "audio/mpeg" : "audio/wav"
                      )
                    }
                  >
                    📦 İndir (.{lastCh.ext.toUpperCase()})
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="card a" style={{ marginTop: "8px" }}>
              Delay Reji playlist'i, şarkılar ve fon müziği gerekli.
            </div>
          )}
        </div>
      )}

      {yoSub === 2 && (
        <div className="grid-2">
          <div>
            <span className="sl">📂 Arşivden Birleştir</span>
            {archive.length === 0 ? (
              <div className="card b">Arşiv boş.</div>
            ) : (
              <div>
                <div style={{ maxHeight: "180px", overflowY: "auto", border: "1px solid var(--border)", borderRadius: "8px", padding: "8px", marginBottom: "8px" }}>
                  {archive.map((e, i) => (
                    <label key={e.id} className="radio-pill" style={{ display: "flex" }}>
                      <input
                        type="checkbox"
                        checked={cntArcIds.includes(e.id)}
                        onChange={(ev) =>
                          setCntArcIds((p) => (ev.target.checked ? [...p, e.id] : p.filter((x) => x !== e.id)))
                        }
                      />
                      {i + 1}. {e.ts_s} | {e.voice} | {e.prev.slice(0, 28)}
                    </label>
                  ))}
                </div>
                <button
                  type="button"
                  className="btn btn-primary btn-full"
                  disabled={cntArcIds.length === 0}
                  onClick={async () => {
                    const wavsBase64 = archive.filter((a) => cntArcIds.includes(a.id)).map((a) => a.wavBase64);
                    const r = await fetch("/api/automation/concat", {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ wavsBase64, format: "wav" }),
                    });
                    const d = await r.json();
                    if (r.ok) setLastCntArc(d.dataBase64);
                  }}
                >
                  🔗 Birleştir
                </button>
                {lastCntArc && (
                  <div>
                    <audio controls src={base64ToDataUrl(lastCntArc)} />
                    <button
                      type="button"
                      className="btn btn-secondary btn-full"
                      onClick={() => downloadBase64(lastCntArc, "birlesik.wav", "audio/wav")}
                    >
                      📦 WAV İndir
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
          <div>
            <span className="sl">📤 Dosya Yükle &amp; MP3 Birleştir</span>
            <label className="upload-box">
              {cntFiles.length > 0 ? `✅ ${cntFiles.length} dosya seçildi` : "Ses Dosyaları Seç"}
              <input
                type="file"
                multiple
                accept=".wav,.mp3,.ogg,.flac"
                style={{ display: "none" }}
                onChange={(e) => setCntFiles(Array.from(e.target.files || []))}
              />
            </label>
            <button
              type="button"
              className="btn btn-primary btn-full"
              style={{ marginTop: "8px" }}
              disabled={cntFiles.length === 0}
              onClick={async () => {
                const fd = new FormData();
                fd.append("format", "mp3");
                cntFiles.forEach((f) => fd.append("files", f));
                const r = await fetch("/api/automation/concat", { method: "POST", body: fd });
                const d = await r.json();
                if (r.ok) setLastCntUp({ data: d.dataBase64, ext: d.ext });
              }}
            >
              🔗 MP3 Olarak Birleştir
            </button>
            {lastCntUp && (
              <div>
                <audio controls src={base64ToDataUrl(lastCntUp.data, "audio/mpeg")} />
                <button
                  type="button"
                  className="btn btn-secondary btn-full"
                  onClick={() => downloadBase64(lastCntUp.data, `birlesik.${lastCntUp.ext}`, "audio/mpeg")}
                >
                  📦 İndir
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
