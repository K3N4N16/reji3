import React, { useCallback, useEffect, useState } from "react";
import { ANONS_POSITIONS, DEFAULT_TEK, THEMES, VOICES } from "./constants";
import type {
  ArchiveItem,
  AutomationTrack,
  EffectPresetItem,
  FavoriteItem,
  LibraryFile,
  RejiSong,
  RvcCloneInfo,
  ScheduleItem,
} from "./types";
import { fmtDur } from "./utils/audioClient";
import { StudioTabsCore } from "./components/StudioTabsCore";
import { StudioTabsRadio } from "./components/StudioTabsRadio";
import { StudioTabsTools } from "./components/StudioTabsTools";

const TAB_LABELS = [
  "🎤 Tek",
  "🎭 Çift",
  "📦 Toplu",
  "🔬 A/B Test",
  "⭐ Favoriler",
  "📻 Delay Reji",
  "🎛️ Fon+Anons",
  "🚀 Yayın Otomasyon",
  "🎚️ Ses Efektleri",
  "📁 Kütüphane",
  "📂 Arşiv",
  "📰 Podcast RSS",
  "📅 Yayın Takvimi",
  "🗣️ Ses Klonlama",
  "🔄 Dönüştürücü",
];

export const App: React.FC = () => {
  const [loggedIn, setLoggedIn] = useState(false);
  const [loginUser, setLoginUser] = useState("");
  const [loginPass, setLoginPass] = useState("");
  const [loginErr, setLoginErr] = useState("");

  const [themeName, setThemeName] = useState<string>("🌙 Yüksek Kontrast Koyu");
  const theme = THEMES[themeName] || THEMES["🌙 Yüksek Kontrast Koyu"];

  const [activeTab, setActiveTab] = useState(0);
  const [notice, setNotice] = useState("");
  const [geminiReady, setGeminiReady] = useState(true);

  const [tekText, setTekText] = useState(DEFAULT_TEK);
  const [archive, setArchive] = useState<ArchiveItem[]>([]);
  const [favorites, setFavorites] = useState<FavoriteItem[]>([]);
  const [playlist, setPlaylist] = useState<RejiSong[]>([]);
  const [yoTracks, setYoTracks] = useState<AutomationTrack[]>([]);
  const [callsCount, setCallsCount] = useState(0);
  const [totalSecs, setTotalSecs] = useState(0);

  const [libSongs, setLibSongs] = useState<LibraryFile[]>([]);
  const [libFon, setLibFon] = useState<LibraryFile[]>([]);
  const [libJingles, setLibJingles] = useState<LibraryFile[]>([]);
  const [libEffects, setLibEffects] = useState<LibraryFile[]>([]);
  const [libAnons, setLibAnons] = useState<LibraryFile[]>([]);

  const [effectPresets, setEffectPresets] = useState<EffectPresetItem[]>([]);
  const [schedules, setSchedules] = useState<ScheduleItem[]>([]);
  const [rvcClones, setRvcClones] = useState<RvcCloneInfo[]>([]);

  // Apply CSS theme variables
  useEffect(() => {
    const r = document.documentElement.style;
    r.setProperty("--bg", theme.bg);
    r.setProperty("--sb", theme.sb);
    r.setProperty("--card", theme.card);
    r.setProperty("--inp", theme.inp);
    r.setProperty("--border", theme.border);
    r.setProperty("--text", theme.text);
    r.setProperty("--muted", theme.muted);
    r.setProperty("--dim", theme.dim);
    r.setProperty("--accent", theme.accent);
    r.setProperty("--accent2", theme.accent2);
    r.setProperty("--sec-btn", theme.sec_btn);
    r.setProperty("--hdr-bg", theme.hdr_bg);
    r.setProperty("--plt-bg", theme.plt_bg);
    if (theme.isLight) {
      r.setProperty("--card-g", "#ecfdf5");
      r.setProperty("--card-g-txt", "#065f46");
      r.setProperty("--card-a", "#fffbeb");
      r.setProperty("--card-a-txt", "#92400e");
      r.setProperty("--card-r", "#fef2f2");
      r.setProperty("--card-r-txt", "#991b1b");
      r.setProperty("--card-p", "#f5f3ff");
      r.setProperty("--card-p-txt", "#5b21b6");
      r.setProperty("--hdr-title", "linear-gradient(90deg,#0f172a 25%,#dc2626)");
    } else {
      r.setProperty("--card-g", "#052e16");
      r.setProperty("--card-g-txt", "#86efac");
      r.setProperty("--card-a", "#291802");
      r.setProperty("--card-a-txt", "#fde68a");
      r.setProperty("--card-r", "#2d0606");
      r.setProperty("--card-r-txt", "#fca5a5");
      r.setProperty("--card-p", "#1b1035");
      r.setProperty("--card-p-txt", "#ddd6fe");
      r.setProperty("--hdr-title", "linear-gradient(90deg,#ffffff 25%,#ff6b6b)");
    }
  }, [theme]);

  const showNotice = useCallback((msg: string) => {
    setNotice(msg);
    setTimeout(() => {
      setNotice((cur) => (cur === msg ? "" : cur));
    }, 4500);
  }, []);

  const refreshLibrary = useCallback(async () => {
    try {
      const [s, f, j, ef, an] = await Promise.all([
        fetch("/api/library/playlist").then((r) => r.json()),
        fetch("/api/library/fon").then((r) => r.json()),
        fetch("/api/library/jingles").then((r) => r.json()),
        fetch("/api/library/effects").then((r) => r.json()),
        fetch("/api/library/anons").then((r) => r.json()),
      ]);
      setLibSongs(s.files || []);
      setLibFon(f.files || []);
      setLibJingles(j.files || []);
      setLibEffects(ef.files || []);
      setLibAnons(an.files || []);
    } catch {
      // ignore
    }
  }, []);

  const refreshEffects = useCallback(async () => {
    try {
      const r = await fetch("/api/effects/presets");
      const d = await r.json();
      setEffectPresets(d.presets || []);
    } catch {
      // ignore
    }
  }, []);

  const refreshSchedules = useCallback(async () => {
    try {
      const r = await fetch("/api/schedules");
      const d = await r.json();
      setSchedules(d.schedules || []);
    } catch {
      // ignore
    }
  }, []);

  const refreshRvc = useCallback(async () => {
    try {
      const r = await fetch("/api/rvc");
      const d = await r.json();
      setRvcClones(d.clones || []);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((d) => setGeminiReady(Boolean(d.geminiConfigured)))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (loggedIn) {
      refreshLibrary();
      refreshEffects();
      refreshSchedules();
      refreshRvc();
    }
  }, [loggedIn, refreshLibrary, refreshEffects, refreshSchedules, refreshRvc]);

  const handleArchiveAdd = useCallback(
    (item: Omit<ArchiveItem, "id" | "ts" | "ts_s" | "model_s" | "prev">) => {
      const now = new Date();
      const ts = now.toLocaleString("tr-TR");
      const ts_s = `${String(now.getDate()).padStart(2, "0")}.${String(now.getMonth() + 1).padStart(2, "0")} ${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
      const newItem: ArchiveItem = {
        ...item,
        id: Math.random().toString(36).slice(2, 12),
        ts,
        ts_s,
        model_s: item.model.replace("gemini-", "").replace("-preview", "").replace("-tts", ""),
        prev: item.text.slice(0, 65).replace(/\n/g, " ") + (item.text.length > 65 ? "…" : ""),
      };
      setArchive((prev) => [newItem, ...prev].slice(0, 60));
      setCallsCount((c) => c + 1);
      setTotalSecs((s) => s + (item.dur || 0));
    },
    []
  );

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginErr("");
    try {
      const r = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: loginUser, password: loginPass }),
      });
      const d = await r.json();
      if (r.ok && d.ok) {
        setLoggedIn(true);
      } else {
        setLoginErr(d.error || "Hatalı kullanıcı adı veya şifre.");
      }
    } catch {
      setLoginErr("Sunucuya bağlanılamadı.");
    }
  };

  if (!loggedIn) {
    return (
      <div className="login-wrap">
        <form className="login-card" onSubmit={handleLogin}>
          <div>
            <h2
              style={{
                textAlign: "center",
                fontFamily: "Syne, sans-serif",
                fontWeight: 800,
                fontSize: "1.5rem",
                margin: "0 0 4px",
              }}
            >
              🎙️ İmaj FM Stüdyo
            </h2>
            <p
              style={{
                textAlign: "center",
                color: theme.muted,
                fontSize: "0.75rem",
                letterSpacing: "0.12em",
                margin: "0 0 12px",
              }}
            >
              TTS &amp; OTOMASYON v7.5 · GÜVENLİ GİRİŞ
            </p>
          </div>
          <input
            className="inp"
            placeholder="👤 kullanıcı adı"
            value={loginUser}
            onChange={(e) => setLoginUser(e.target.value)}
          />
          <input
            className="inp"
            type="password"
            placeholder="🔑 şifre"
            value={loginPass}
            onChange={(e) => setLoginPass(e.target.value)}
          />
          <button type="submit" className="btn btn-primary btn-full">
            Stüdyoya Bağlan →
          </button>
          {loginErr && <div className="card r">❌ {loginErr}</div>}
        </form>
      </div>
    );
  }

  return (
    <div className="studio-shell">
      {/* SIDEBAR */}
      <aside className="studio-sidebar">
        <div
          style={{
            textAlign: "center",
            padding: "4px 0 6px",
            fontFamily: "Syne, sans-serif",
            fontSize: "1rem",
            fontWeight: 800,
          }}
        >
          🎙️ İmaj FM <span style={{ color: theme.accent, fontSize: "0.72rem" }}>v7.5</span>
        </div>

        <div>
          <span className="fld-lbl">🎨 Tema</span>
          <select
            className="sel"
            value={themeName}
            onChange={(e) => setThemeName(e.target.value)}
          >
            {Object.keys(THEMES).map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>

        <details className="expander">
          <summary>🚀 Otomasyon Akışı · {yoTracks.length} şarkı</summary>
          <div className="expander-body">
            {yoTracks.length === 0 ? (
              <div style={{ fontSize: "0.75rem", color: theme.muted }}>
                Boş. Yayın Otomasyon sekmesinden ekleyin.
              </div>
            ) : (
              yoTracks.slice(0, 8).map((yt, i) => (
                <div key={yt.id} style={{ fontSize: "0.73rem", padding: "2px 0" }}>
                  {i + 1}. <b>{yt.title.slice(0, 20)}</b> ({fmtDur(yt.dur)})
                </div>
              ))
            )}
          </div>
        </details>

        <details className="expander">
          <summary>
            📂 Kütüphane · {libSongs.length} şarkı · {libFon.length} fon
          </summary>
          <div className="expander-body" style={{ fontSize: "0.75rem", color: theme.muted }}>
            Arşiv: {archive.length} · Jingle: {libJingles.length}
          </div>
        </details>

        <button
          type="button"
          className="btn btn-secondary btn-full"
          style={{ marginTop: "auto" }}
          onClick={() => setLoggedIn(false)}
        >
          🚪 Çıkış Yap
        </button>
      </aside>

      {/* MAIN */}
      <main className="studio-main">
        <div className="hdr">
          <h1>🎙️ İmaj FM · Seslendirme &amp; Yayın Otomasyon Stüdyosu</h1>
          <p>
            <span className="ldot" />
            Gemini Flash TTS (2.5 / 3.8) · AI Anons Yazarı · Şarkı İçi/Başı/Sonu Talk-Over · MP3 Yayın Çıktısı · Yüksek Kontrast
          </p>
        </div>

        <div className="kpi-grid">
          <div className="mbox">
            <div className="v">{Object.keys(VOICES).length}</div>
            <div className="l">Ses</div>
          </div>
          <div className="mbox g">
            <div className="v">{geminiReady ? "Hazır" : "Eksik"}</div>
            <div className="l">Gemini</div>
          </div>
          <div className="mbox a">
            <div className="v">{favorites.length}</div>
            <div className="l">Favori</div>
          </div>
          <div className="mbox b">
            <div className="v">{archive.length}</div>
            <div className="l">Arşiv</div>
          </div>
          <div className="mbox">
            <div className="v">{callsCount}</div>
            <div className="l">İstek</div>
          </div>
          <div className="mbox p">
            <div className="v">{totalSecs.toFixed(0)}s</div>
            <div className="l">Ses</div>
          </div>
          <div className="mbox t">
            <div className="v">{yoTracks.length}</div>
            <div className="l">Otomasyon</div>
          </div>
          <div className="mbox">
            <div className="v">{libSongs.length}</div>
            <div className="l">Şarkı</div>
          </div>
        </div>

        {!geminiReady && (
          <div className="card a">
            ⚠️ GEMINI_API_KEY sunucu ortamında tanımlı değil. Seslendirme/AI özellikleri için Settings &gt; Secrets panelinden ekleyin (Otomasyon ve ses araçları anahtarsız da çalışır).
          </div>
        )}

        {notice && <div className="card g">{notice}</div>}

        {/* TABS */}
        <div className="tabs-bar">
          {TAB_LABELS.map((lbl, idx) => (
            <button
              key={lbl}
              type="button"
              className={`tab-btn ${activeTab === idx ? "active" : ""}`}
              onClick={() => setActiveTab(idx)}
            >
              {lbl}
            </button>
          ))}
        </div>

        {activeTab <= 4 && (
          <StudioTabsCore
            activeTab={activeTab}
            theme={theme}
            favorites={favorites}
            setFavorites={setFavorites}
            onArchiveAdd={handleArchiveAdd}
            tekText={tekText}
            setTekText={setTekText}
            onNotice={showNotice}
          />
        )}

        {activeTab >= 5 && activeTab <= 7 && (
          <StudioTabsRadio
            activeTab={activeTab}
            archive={archive}
            playlist={playlist}
            setPlaylist={setPlaylist}
            yoTracks={yoTracks}
            setYoTracks={setYoTracks}
            libSongs={libSongs}
            libFon={libFon}
            libJingles={libJingles}
            libAnons={libAnons}
            onRefreshLibrary={refreshLibrary}
            onArchiveAdd={handleArchiveAdd}
            onNotice={showNotice}
          />
        )}

        {activeTab >= 8 && (
          <StudioTabsTools
            activeTab={activeTab}
            theme={theme}
            archive={archive}
            setArchive={setArchive}
            setFavorites={setFavorites}
            libSongs={libSongs}
            libFon={libFon}
            libJingles={libJingles}
            libEffects={libEffects}
            onRefreshLibrary={refreshLibrary}
            effectPresets={effectPresets}
            onRefreshEffects={refreshEffects}
            schedules={schedules}
            onRefreshSchedules={refreshSchedules}
            rvcClones={rvcClones}
            onRefreshRvc={refreshRvc}
            onSendScheduleToYo={(songs) => {
              const matched = libSongs.filter((ls) => songs.includes(ls.name));
              setYoTracks(
                matched.map((m) => ({
                  id: Math.random().toString(36).slice(2, 10),
                  songFilename: m.name,
                  title: m.title || m.name,
                  artist: m.artist || "Bilinmeyen",
                  dur: m.duration || 180,
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
                  fonVolDb: -8,
                  jingleSrc: "Yok",
                  jingleLibFile: null,
                  jingleBase64: null,
                  jinglePos: "Şarkı Başı",
                  duckDb: -16,
                  anonsGainDb: 1.5,
                  rampMs: 450,
                }))
              );
              setActiveTab(7);
              showNotice("✅ Yayın Otomasyonu sekmesine aktarıldı!");
            }}
            onNotice={showNotice}
          />
        )}

        <hr />
        <div
          style={{
            textAlign: "center",
            color: theme.muted,
            fontSize: "0.72rem",
            letterSpacing: "0.06em",
            padding: "6px 0 12px",
          }}
        >
          <b>İMAJ FM TTS STÜDYO v7.5</b> · {geminiReady ? "✅ Gemini" : "⚠️ Gemini"} · ✅ FFmpeg DSP · 2026
        </div>
      </main>
    </div>
  );
};

export default App;
