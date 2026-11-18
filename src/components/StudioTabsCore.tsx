import React, { useState } from "react";
import {
  DEFAULT_CIFT,
  DEFAULT_TEK,
  EQ_OPTS,
  ETAGS,
  LANGUAGES,
  MODELS,
  STYLE_PRESETS,
  TEMPLATES,
  VOICES,
  type ThemeConfig,
} from "../constants";
import type { ArchiveItem, AudioMetrics, FavoriteItem } from "../types";
import {
  base64ToDataUrl,
  downloadBase64,
  txtStats,
} from "../utils/audioClient";
import { ResultCard } from "./ResultCard";
import { WaveformCanvas } from "./WaveformCanvas";

interface StudioTabsCoreProps {
  activeTab: number;
  theme: ThemeConfig;
  favorites: FavoriteItem[];
  setFavorites: React.Dispatch<React.SetStateAction<FavoriteItem[]>>;
  onArchiveAdd: (item: Omit<ArchiveItem, "id" | "ts" | "ts_s" | "model_s" | "prev">) => void;
  tekText: string;
  setTekText: React.Dispatch<React.SetStateAction<string>>;
  onNotice: (msg: string) => void;
}

export const StudioTabsCore: React.FC<StudioTabsCoreProps> = ({
  activeTab,
  theme,
  favorites,
  setFavorites,
  onArchiveAdd,
  tekText,
  setTekText,
  onNotice,
}) => {
  // ── Tab 1: Tek Konuşmacı ──────────────────────────────────────────────────
  const [tmpl1, setTmpl1] = useState("— Yok —");
  const [aiTopic1, setAiTopic1] = useState("");
  const [aiWriting, setAiWriting] = useState(false);
  const [mdl1, setMdl1] = useState("gemini-3.8-flash-lite-tts");
  const [customMdl1, setCustomMdl1] = useState("gemini-3.8-flash-tts");
  const [lng1, setLng1] = useState("tr-TR");
  const [gender1, setGender1] = useState("Tümü");
  const [vc1, setVc1] = useState("Kore");
  const [eq1, setEq1] = useState("Ham");
  const [ps1, setPs1] = useState("— Seçin —");
  const [styTr1, setStyTr1] = useState("");
  const [styEn1, setStyEn1] = useState("");
  const [favName1, setFavName1] = useState("");
  const [loading1, setLoading1] = useState(false);
  const [err1, setErr1] = useState("");
  const [prompterText, setPrompterText] = useState("");
  const [prompterDone, setPrompterDone] = useState(false);
  const [lastTek, setLastTek] = useState<{
    wav: string;
    voice: string;
    usedModel: string;
    metrics: AudioMetrics;
    dn: string;
  } | null>(null);

  // ── Tab 2: Çift Konuşmacı ─────────────────────────────────────────────────
  const [tmpl2, setTmpl2] = useState("— Yok —");
  const [mdl2, setMdl2] = useState("gemini-3.8-flash-tts");
  const [lng2, setLng2] = useState("tr-TR");
  const [sp1n, setSp1n] = useState("Sunucu");
  const [sp1v, setSp1v] = useState("Kore");
  const [sp2n, setSp2n] = useState("Misafir");
  const [sp2v, setSp2v] = useState("Fenrir");
  const [eq2, setEq2] = useState("Ham");
  const [txt2, setTxt2] = useState(DEFAULT_CIFT);
  const [loading2, setLoading2] = useState(false);
  const [err2, setErr2] = useState("");
  const [lastCift, setLastCift] = useState<{
    wav: string;
    voice: string;
    usedModel: string;
    metrics: AudioMetrics;
    dn: string;
  } | null>(null);

  // ── Tab 3: Toplu TTS ──────────────────────────────────────────────────────
  const [bulkSubTab, setBulkSubTab] = useState<"manual" | "file">("manual");
  const [mdl3, setMdl3] = useState("gemini-3.8-flash-lite-tts");
  const [lng3, setLng3] = useState("tr-TR");
  const [vc3, setVc3] = useState("Kore");
  const [eq3, setEq3] = useState("Ham");
  const [sty3, setSty3] = useState("");
  const [txt3, setTxt3] = useState(
    "İmaj FM sabah yayını başlıyor.\nHaber bülteni için bekleyiniz.\nMüzik programımıza hoş geldiniz."
  );
  const [loading3, setLoading3] = useState(false);
  const [bulkRes, setBulkRes] = useState<{
    items: Array<{ filename: string; text: string; wavBase64: string; duration: number }>;
    errors: string[];
    zipBase64: string | null;
    vc: string;
  } | null>(null);

  const [fileLines, setFileLines] = useState<string[]>([]);
  const [muMdl, setMuMdl] = useState("gemini-3.8-flash-lite-tts");
  const [muVc, setMuVc] = useState("Kore");
  const [loadingMu, setLoadingMu] = useState(false);
  const [bulkFileRes, setBulkFileRes] = useState<{
    zipBase64: string;
    count: number;
  } | null>(null);

  // ── Tab 4: A/B Test ───────────────────────────────────────────────────────
  const [abA, setAbA] = useState({
    model: "gemini-3.8-flash-lite-tts",
    lang: "tr-TR",
    voice: "Kore",
    eq: "Ham",
    ps: "— Seçin —",
    style: "",
    text: "[excitedly] İmaj FM'e hoş geldiniz!",
    loading: false,
    err: "",
    res: null as null | { wav: string; voice: string; metrics: AudioMetrics },
  });
  const [abB, setAbB] = useState({
    model: "gemini-3.8-flash-tts",
    lang: "tr-TR",
    voice: "Fenrir",
    eq: "Ham",
    ps: "— Seçin —",
    style: "",
    text: "[seriously] İmaj FM'e hoş geldiniz.",
    loading: false,
    err: "",
    res: null as null | { wav: string; voice: string; metrics: AudioMetrics },
  });

  // ── Helpers ───────────────────────────────────────────────────────────────
  const filteredVoices1 = Object.entries(VOICES).filter(([, [g]]) => {
    if (gender1 === "♀ Kadın") return g === "♀";
    if (gender1 === "♂ Erkek") return g === "♂";
    return true;
  });

  const handleAiWrite = async () => {
    if (!aiTopic1.trim()) return;
    setAiWriting(true);
    setErr1("");
    try {
      const r = await fetch("/api/ai/write-anons", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: aiTopic1.trim() }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || "AI yazım hatası");
      setTekText(data.text);
    } catch (e) {
      setErr1(e instanceof Error ? e.message : "AI hatası");
    } finally {
      setAiWriting(false);
    }
  };

  const handleLivePrompter = () => {
    if (!tekText.trim()) return;
    const words = tekText.split(" ");
    setPrompterDone(false);
    setPrompterText("");
    let i = 0;
    const timer = setInterval(() => {
      i++;
      setPrompterText(words.slice(0, i).join(" "));
      if (i >= words.length) {
        clearInterval(timer);
        setPrompterDone(true);
      }
    }, 65);
  };

  const handleGenTek = async () => {
    if (!tekText.trim()) {
      setErr1("⚠️ Metin boş.");
      return;
    }
    setLoading1(true);
    setErr1("");
    const activeModel = mdl1 === "__custom__" ? customMdl1 : mdl1;
    const combinedStyle = [styTr1.trim(), styEn1.trim()].filter(Boolean).join(" / ");
    try {
      const r = await fetch("/api/tts/single", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: activeModel,
          text: tekText,
          voice: vc1,
          lang: lng1,
          style: combinedStyle,
          eq: eq1,
        }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || "TTS hatası");
      onArchiveAdd({
        voice: vc1,
        model: data.usedModel || activeModel,
        lang: lng1,
        style: combinedStyle,
        text: tekText,
        wavBase64: data.wavBase64,
        dur: Number(data.metrics.duration.toFixed(1)),
        mode: "tek",
        metrics: data.metrics,
      });
      setLastTek({
        wav: data.wavBase64,
        voice: vc1,
        usedModel: data.usedModel,
        metrics: data.metrics,
        dn: `imajfm_${vc1.toLowerCase()}_${lng1}.wav`,
      });
    } catch (e) {
      setErr1(e instanceof Error ? e.message : "TTS hatası");
    } finally {
      setLoading1(false);
    }
  };

  const handleGenMulti = async () => {
    if (!txt2.trim()) return;
    setLoading2(true);
    setErr2("");
    try {
      const r = await fetch("/api/tts/multi", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: mdl2,
          text: txt2,
          sp1: sp1n,
          v1: sp1v,
          sp2: sp2n,
          v2: sp2v,
          lang: lng2,
          eq: eq2,
        }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || "Multi-TTS hatası");
      onArchiveAdd({
        voice: `${sp1v}+${sp2v}`,
        model: data.usedModel || mdl2,
        lang: lng2,
        style: "",
        text: txt2,
        wavBase64: data.wavBase64,
        dur: Number(data.metrics.duration.toFixed(1)),
        mode: "cift",
        metrics: data.metrics,
      });
      setLastCift({
        wav: data.wavBase64,
        voice: sp1v,
        usedModel: data.usedModel,
        metrics: data.metrics,
        dn: `imajfm_diyalog_${sp1v.toLowerCase()}.wav`,
      });
    } catch (e) {
      setErr2(e instanceof Error ? e.message : "Multi-TTS hatası");
    } finally {
      setLoading2(false);
    }
  };

  const handleBulkManual = async () => {
    const lines = txt3
      .split(/\r?\n/)
      .map((l) => l.trim())
      .filter(Boolean);
    if (lines.length === 0) return;
    setLoading3(true);
    try {
      const r = await fetch("/api/tts/bulk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lines,
          model: mdl3,
          voice: vc3,
          lang: lng3,
          style: sty3,
          eq: eq3,
        }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || "Toplu TTS hatası");
      for (const item of data.items || []) {
        onArchiveAdd({
          voice: vc3,
          model: mdl3,
          lang: lng3,
          style: sty3,
          text: item.text,
          wavBase64: item.wavBase64,
          dur: Number((item.duration || 0).toFixed(1)),
          mode: "bulk",
        });
      }
      setBulkRes({
        items: data.items || [],
        errors: data.errors || [],
        zipBase64: data.zipBase64,
        vc: vc3,
      });
    } catch (e) {
      onNotice(`❌ ${e instanceof Error ? e.message : "Toplu hata"}`);
    } finally {
      setLoading3(false);
    }
  };

  const handleBulkFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    const raw = await f.text();
    let lines = raw
      .split(/\r?\n/)
      .map((l) => l.trim())
      .filter(Boolean);
    if (f.name.toLowerCase().endsWith(".csv")) {
      lines = lines
        .map((l) => l.split(",")[0].trim().replace(/^"|"$/g, ""))
        .filter(Boolean);
    }
    setFileLines(lines);
  };

  const handleBulkFileRun = async () => {
    if (fileLines.length === 0) return;
    setLoadingMu(true);
    try {
      const r = await fetch("/api/tts/bulk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lines: fileLines,
          model: muMdl,
          voice: muVc,
          lang: "tr-TR",
          style: "",
          eq: "Ham",
        }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || "Toplu dosya hatası");
      for (const item of data.items || []) {
        onArchiveAdd({
          voice: muVc,
          model: muMdl,
          lang: "tr-TR",
          style: "",
          text: item.text,
          wavBase64: item.wavBase64,
          dur: Number((item.duration || 0).toFixed(1)),
          mode: "bulk-file",
        });
      }
      if (data.zipBase64) {
        setBulkFileRes({ zipBase64: data.zipBase64, count: data.items.length });
      }
    } catch (e) {
      onNotice(`❌ ${e instanceof Error ? e.message : "Hata"}`);
    } finally {
      setLoadingMu(false);
    }
  };

  const runAb = async (which: "A" | "B") => {
    const st = which === "A" ? abA : abB;
    const setSt = which === "A" ? setAbA : setAbB;
    if (!st.text.trim()) return;
    setSt((prev) => ({ ...prev, loading: true, err: "" }));
    try {
      const r = await fetch("/api/tts/single", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: st.model,
          text: st.text,
          voice: st.voice,
          lang: st.lang,
          style: st.style,
          eq: st.eq,
        }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || "A/B TTS hatası");
      onArchiveAdd({
        voice: st.voice,
        model: st.model,
        lang: st.lang,
        style: st.style,
        text: st.text,
        wavBase64: data.wavBase64,
        dur: Number(data.metrics.duration.toFixed(1)),
        mode: `ab-${which}`,
        metrics: data.metrics,
      });
      setSt((prev) => ({
        ...prev,
        loading: false,
        res: { wav: data.wavBase64, voice: st.voice, metrics: data.metrics },
      }));
    } catch (e) {
      setSt((prev) => ({
        ...prev,
        loading: false,
        err: e instanceof Error ? e.message : "Hata",
      }));
    }
  };

  const handlePlayFavorite = async (fv: FavoriteItem) => {
    try {
      const r = await fetch("/api/tts/single", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: fv.model || "gemini-3.8-flash-lite-tts",
          text: fv.text,
          voice: fv.voice || "Kore",
          lang: fv.lang || "tr-TR",
          style: "",
        }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error);
      onArchiveAdd({
        voice: fv.voice || "Kore",
        model: fv.model || "gemini-3.8-flash-lite-tts",
        lang: fv.lang || "tr-TR",
        style: "",
        text: fv.text,
        wavBase64: data.wavBase64,
        dur: Number(data.metrics.duration.toFixed(1)),
        mode: "fav",
        metrics: data.metrics,
      });
      setFavorites((prev) =>
        prev.map((x) => (x.id === fv.id ? { ...x, wavBase64: data.wavBase64 } : x))
      );
    } catch (e) {
      onNotice(`❌ ${e instanceof Error ? e.message : "Hata"}`);
    }
  };

  // ── TAB 0: TEK KONUŞMACI ──────────────────────────────────────────────────
  if (activeTab === 0) {
    const st1 = txtStats(tekText);
    return (
      <div className="tab-panel grid-2-asym">
        <div>
          <span className="sl">▶ Şablon & AI Anons Yazarı</span>
          <div className="row-flex">
            <select
              className="sel"
              value={tmpl1}
              onChange={(e) => setTmpl1(e.target.value)}
            >
              <option value="— Yok —">— Yok —</option>
              {Object.keys(TEMPLATES).map((k) => (
                <option key={k} value={k}>
                  {k}
                </option>
              ))}
            </select>
            {tmpl1 !== "— Yok —" && (
              <button
                type="button"
                className="btn btn-secondary"
                style={{ whiteSpace: "nowrap" }}
                onClick={() => setTekText(TEMPLATES[tmpl1])}
              >
                📥 Şablonu Yükle
              </button>
            )}
          </div>

          <div className="row-flex" style={{ marginTop: "8px" }}>
            <input
              className="inp"
              placeholder="✨ AI Konu yaz (örn: Akşam trafiği & Sezen Aksu)..."
              value={aiTopic1}
              onChange={(e) => setAiTopic1(e.target.value)}
            />
            <button
              type="button"
              className="btn btn-secondary"
              style={{ whiteSpace: "nowrap" }}
              disabled={aiWriting}
              onClick={handleAiWrite}
            >
              {aiWriting ? "⏳ Yazıyor…" : "✨ AI Metin Yaz"}
            </button>
          </div>

          <span className="sl">▶ Model & Dil</span>
          <div className="grid-2" style={{ gap: "8px" }}>
            <select
              className="sel"
              value={mdl1}
              onChange={(e) => setMdl1(e.target.value)}
            >
              {Object.entries(MODELS).map(([k, lbl]) => (
                <option key={k} value={k}>
                  {lbl}
                </option>
              ))}
              <option value="__custom__">✍️ Özel Model ID Gir</option>
            </select>
            <select
              className="sel"
              value={lng1}
              onChange={(e) => setLng1(e.target.value)}
            >
              {Object.entries(LANGUAGES).map(([k, lbl]) => (
                <option key={k} value={k}>
                  {lbl}
                </option>
              ))}
            </select>
          </div>
          {mdl1 === "__custom__" && (
            <input
              className="inp"
              style={{ marginTop: "6px" }}
              value={customMdl1}
              onChange={(e) => setCustomMdl1(e.target.value)}
              placeholder="Özel Model ID"
            />
          )}

          <span className="sl">▶ Ses & EQ</span>
          <div className="radio-group">
            {["Tümü", "♀ Kadın", "♂ Erkek"].map((g) => (
              <label key={g} className="radio-pill">
                <input
                  type="radio"
                  name="gender1"
                  checked={gender1 === g}
                  onChange={() => {
                    setGender1(g);
                    const first = Object.entries(VOICES).find(([, [vg]]) =>
                      g === "Tümü" ? true : g.startsWith("♀") ? vg === "♀" : vg === "♂"
                    );
                    if (first) setVc1(first[0]);
                  }}
                />
                {g}
              </label>
            ))}
          </div>
          <div className="grid-2" style={{ gap: "8px" }}>
            <select
              className="sel"
              value={vc1}
              onChange={(e) => setVc1(e.target.value)}
            >
              {filteredVoices1.map(([k, [g, desc]]) => (
                <option key={k} value={k}>
                  {g} {k} — {desc}
                </option>
              ))}
            </select>
            <select
              className="sel"
              value={eq1}
              onChange={(e) => setEq1(e.target.value)}
            >
              {EQ_OPTS.map((eq) => (
                <option key={eq} value={eq}>
                  {eq}
                </option>
              ))}
            </select>
          </div>

          <span className="sl">▶ Stil</span>
          <select
            className="sel"
            value={ps1}
            onChange={(e) => {
              setPs1(e.target.value);
              setStyTr1(STYLE_PRESETS[e.target.value] || "");
            }}
          >
            {Object.keys(STYLE_PRESETS).map((k) => (
              <option key={k} value={k}>
                {k}
              </option>
            ))}
          </select>
          <div className="grid-2" style={{ gap: "8px", marginTop: "6px" }}>
            <div>
              <div style={{ fontSize: "0.7rem", fontWeight: 700, color: theme.accent2, marginBottom: "3px" }}>
                🇹🇷 TR Stil
              </div>
              <textarea
                className="txa"
                rows={2}
                value={styTr1}
                onChange={(e) => setStyTr1(e.target.value)}
              />
            </div>
            <div>
              <div style={{ fontSize: "0.7rem", fontWeight: 700, color: "#d97706", marginBottom: "3px" }}>
                🇬🇧 EN Style
              </div>
              <textarea
                className="txa"
                rows={2}
                value={styEn1}
                onChange={(e) => setStyEn1(e.target.value)}
              />
            </div>
          </div>

          <div className="row-flex" style={{ marginTop: "10px" }}>
            <input
              className="inp"
              placeholder="⭐ Favori ismi…"
              value={favName1}
              onChange={(e) => setFavName1(e.target.value)}
            />
            <button
              type="button"
              className="btn btn-secondary"
              style={{ whiteSpace: "nowrap" }}
              onClick={() => {
                if (favName1.trim() && tekText.trim()) {
                  setFavorites((prev) => [
                    ...prev,
                    {
                      id: Math.random().toString(36).slice(2, 10),
                      name: favName1.trim(),
                      text: tekText,
                      voice: vc1,
                      model: mdl1 === "__custom__" ? customMdl1 : mdl1,
                      lang: lng1,
                    },
                  ]);
                  setFavName1("");
                  onNotice("⭐ Favorilere eklendi!");
                }
              }}
            >
              ⭐ Favoriye Ekle
            </button>
          </div>
        </div>

        <div>
          <span className="sl">▶ Anons Metni</span>
          <div className="etag-grid">
            {ETAGS.map(([em, lbl, tag]) => (
              <button
                key={lbl}
                type="button"
                className="btn btn-secondary btn-sm"
                title={lbl}
                onClick={() => setTekText((t) => t + tag)}
              >
                {em}
              </button>
            ))}
          </div>
          <textarea
            className="txa"
            rows={10}
            value={tekText}
            onChange={(e) => setTekText(e.target.value)}
            placeholder="Metni buraya yazın…"
          />
          <div style={{ fontSize: "0.73rem", color: theme.muted, margin: "4px 0 8px" }}>
            📊 {st1.chars} karakter · {st1.words} kelime · {st1.sentences} cümle · ~{st1.estSec}s
          </div>

          <div className="row-flex">
            <button
              type="button"
              className="btn btn-primary"
              style={{ flex: 2 }}
              disabled={loading1}
              onClick={handleGenTek}
            >
              {loading1 ? `🎙️ ${vc1} seslendiriyor…` : `🔴 ${vc1} ile Seslendir`}
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              style={{ flex: 1 }}
              onClick={handleLivePrompter}
            >
              📺 Canlı Prompter
            </button>
          </div>

          {prompterText && (
            <div
              className={`card ${prompterDone ? "g" : "b"}`}
              style={{ fontSize: "1.06rem", lineHeight: 1.6, marginTop: "10px" }}
            >
              {prompterText}
              {!prompterDone && <span style={{ color: theme.accent }}>▌</span>}
            </div>
          )}

          {err1 && <div className="card r">❌ {err1}</div>}

          {lastTek && (
            <ResultCard
              wavBase64={lastTek.wav}
              voice={lastTek.voice}
              usedModel={lastTek.usedModel}
              metrics={lastTek.metrics}
              downloadName={lastTek.dn}
              theme={theme}
            />
          )}
        </div>
      </div>
    );
  }

  // ── TAB 1: ÇİFT KONUŞMACI ─────────────────────────────────────────────────
  if (activeTab === 1) {
    const st2 = txtStats(txt2);
    return (
      <div className="tab-panel">
        <div className="card b">
          🎭 İki konuşmacı — Multi-speaker Gemini TTS (Oto 3 katmanlı yedek aktif) · Tek WAV çıktı
        </div>
        <div className="grid-2-asym" style={{ marginTop: "12px" }}>
          <div>
            <div className="row-flex">
              <select
                className="sel"
                value={tmpl2}
                onChange={(e) => setTmpl2(e.target.value)}
              >
                <option value="— Yok —">— Yok —</option>
                {Object.keys(TEMPLATES).map((k) => (
                  <option key={k} value={k}>
                    {k}
                  </option>
                ))}
              </select>
              {tmpl2 !== "— Yok —" && (
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setTxt2(TEMPLATES[tmpl2])}
                >
                  📥 Yükle
                </button>
              )}
            </div>
            <div className="grid-2" style={{ gap: "8px", marginTop: "8px" }}>
              <select className="sel" value={mdl2} onChange={(e) => setMdl2(e.target.value)}>
                {Object.entries(MODELS).map(([k, lbl]) => (
                  <option key={k} value={k}>
                    {lbl}
                  </option>
                ))}
              </select>
              <select className="sel" value={lng2} onChange={(e) => setLng2(e.target.value)}>
                {Object.entries(LANGUAGES).map(([k, lbl]) => (
                  <option key={k} value={k}>
                    {lbl}
                  </option>
                ))}
              </select>
            </div>
            <span className="sl">▶ Konuşmacı 1 & 2</span>
            <div className="row-flex" style={{ marginBottom: "8px" }}>
              <input
                className="inp"
                style={{ flex: 1 }}
                value={sp1n}
                onChange={(e) => setSp1n(e.target.value)}
              />
              <select
                className="sel"
                style={{ flex: 2 }}
                value={sp1v}
                onChange={(e) => setSp1v(e.target.value)}
              >
                {Object.entries(VOICES).map(([k, [g]]) => (
                  <option key={k} value={k}>
                    {g} {k}
                  </option>
                ))}
              </select>
            </div>
            <div className="row-flex" style={{ marginBottom: "8px" }}>
              <input
                className="inp"
                style={{ flex: 1 }}
                value={sp2n}
                onChange={(e) => setSp2n(e.target.value)}
              />
              <select
                className="sel"
                style={{ flex: 2 }}
                value={sp2v}
                onChange={(e) => setSp2v(e.target.value)}
              >
                {Object.entries(VOICES).map(([k, [g]]) => (
                  <option key={k} value={k}>
                    {g} {k}
                  </option>
                ))}
              </select>
            </div>
            <select className="sel" value={eq2} onChange={(e) => setEq2(e.target.value)}>
              {EQ_OPTS.map((eq) => (
                <option key={eq} value={eq}>
                  {eq}
                </option>
              ))}
            </select>
          </div>
          <div>
            <span className="sl">▶ Diyalog Metni</span>
            <div className="etag-grid">
              {ETAGS.map(([em, lbl, tag]) => (
                <button
                  key={lbl}
                  type="button"
                  className="btn btn-secondary btn-sm"
                  title={lbl}
                  onClick={() => setTxt2((t) => t + tag)}
                >
                  {em}
                </button>
              ))}
            </div>
            <textarea
              className="txa"
              rows={9}
              value={txt2}
              onChange={(e) => setTxt2(e.target.value)}
            />
            <div style={{ fontSize: "0.73rem", color: theme.muted, margin: "4px 0 8px" }}>
              📊 {st2.chars} karakter · {st2.words} kelime · ~{st2.estSec}s
            </div>
            <button
              type="button"
              className="btn btn-primary btn-full"
              disabled={loading2}
              onClick={handleGenMulti}
            >
              {loading2 ? "🎭 Diyalog üretiliyor…" : `🔴 ${sp1n} & ${sp2n} Diyalog Üret`}
            </button>
            {err2 && <div className="card r">❌ {err2}</div>}
            {lastCift && (
              <ResultCard
                wavBase64={lastCift.wav}
                voice={lastCift.voice}
                usedModel={lastCift.usedModel}
                metrics={lastCift.metrics}
                downloadName={lastCift.dn}
                theme={theme}
              />
            )}
          </div>
        </div>
      </div>
    );
  }

  // ── TAB 2: TOPLU TTS ──────────────────────────────────────────────────────
  if (activeTab === 2) {
    const lines3 = txt3
      .split(/\r?\n/)
      .map((l) => l.trim())
      .filter(Boolean);
    return (
      <div className="tab-panel">
        <div className="card b">
          📦 Her satır ayrı WAV — TXT/CSV yükle veya manuel yaz — ZIP indir
        </div>
        <div className="subtabs-bar">
          <button
            type="button"
            className={`subtab-btn ${bulkSubTab === "manual" ? "active" : ""}`}
            onClick={() => setBulkSubTab("manual")}
          >
            ✏️ Manuel Liste
          </button>
          <button
            type="button"
            className={`subtab-btn ${bulkSubTab === "file" ? "active" : ""}`}
            onClick={() => setBulkSubTab("file")}
          >
            📄 TXT/CSV Yükle
          </button>
        </div>

        {bulkSubTab === "manual" ? (
          <div className="grid-2-asym">
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <select className="sel" value={mdl3} onChange={(e) => setMdl3(e.target.value)}>
                {Object.entries(MODELS).map(([k, lbl]) => (
                  <option key={k} value={k}>
                    {lbl}
                  </option>
                ))}
              </select>
              <select className="sel" value={lng3} onChange={(e) => setLng3(e.target.value)}>
                {Object.entries(LANGUAGES).map(([k, lbl]) => (
                  <option key={k} value={k}>
                    {lbl}
                  </option>
                ))}
              </select>
              <select className="sel" value={vc3} onChange={(e) => setVc3(e.target.value)}>
                {Object.entries(VOICES).map(([k, [g]]) => (
                  <option key={k} value={k}>
                    {g} {k}
                  </option>
                ))}
              </select>
              <select className="sel" value={eq3} onChange={(e) => setEq3(e.target.value)}>
                {EQ_OPTS.map((eq) => (
                  <option key={eq} value={eq}>
                    {eq}
                  </option>
                ))}
              </select>
              <textarea
                className="txa"
                rows={2}
                placeholder="Stil (opsiyonel)"
                value={sty3}
                onChange={(e) => setSty3(e.target.value)}
              />
            </div>
            <div>
              <textarea
                className="txa"
                rows={9}
                value={txt3}
                onChange={(e) => setTxt3(e.target.value)}
              />
              <button
                type="button"
                className="btn btn-primary btn-full"
                style={{ marginTop: "8px" }}
                disabled={loading3 || lines3.length === 0}
                onClick={handleBulkManual}
              >
                {loading3 ? "⏳ Üretiliyor…" : `🔴 ${lines3.length} Satırı Üret`}
              </button>
              {bulkRes && (
                <div style={{ marginTop: "10px" }}>
                  {bulkRes.items.length > 0 && (
                    <div className="card g">✅ {bulkRes.items.length} ses üretildi</div>
                  )}
                  {bulkRes.zipBase64 && (
                    <button
                      type="button"
                      className="btn btn-secondary btn-full"
                      onClick={() =>
                        downloadBase64(
                          bulkRes.zipBase64!,
                          `bulk_${bulkRes.vc.toLowerCase()}.zip`,
                          "application/zip"
                        )
                      }
                    >
                      📦 ZIP İndir
                    </button>
                  )}
                  {bulkRes.errors.map((err, i) => (
                    <div key={i} className="card r">
                      ❌ {err}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div>
            <label className="upload-box">
              📄 TXT veya CSV Dosyası Seç
              <input
                type="file"
                accept=".txt,.csv"
                style={{ display: "none" }}
                onChange={handleBulkFileUpload}
              />
            </label>
            {fileLines.length > 0 && (
              <div style={{ marginTop: "10px" }}>
                <div className="card g">✅ {fileLines.length} satır okundu</div>
                <div className="grid-2" style={{ marginTop: "8px" }}>
                  <select className="sel" value={muMdl} onChange={(e) => setMuMdl(e.target.value)}>
                    {Object.entries(MODELS).map(([k, lbl]) => (
                      <option key={k} value={k}>
                        {lbl}
                      </option>
                    ))}
                  </select>
                  <select className="sel" value={muVc} onChange={(e) => setMuVc(e.target.value)}>
                    {Object.entries(VOICES).map(([k, [g]]) => (
                      <option key={k} value={k}>
                        {g} {k}
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  type="button"
                  className="btn btn-primary btn-full"
                  style={{ marginTop: "10px" }}
                  disabled={loadingMu}
                  onClick={handleBulkFileRun}
                >
                  {loadingMu ? "⏳ Üretiliyor…" : "🚀 Dosyadan Toplu Üret"}
                </button>
                {bulkFileRes && (
                  <button
                    type="button"
                    className="btn btn-secondary btn-full"
                    style={{ marginTop: "8px" }}
                    onClick={() =>
                      downloadBase64(bulkFileRes.zipBase64, "bulk_dosya.zip", "application/zip")
                    }
                  >
                    📦 {bulkFileRes.count} Sesi ZIP İndir
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // ── TAB 3: A/B TEST ───────────────────────────────────────────────────────
  if (activeTab === 3) {
    const renderAbCol = (
      label: string,
      which: "A" | "B",
      state: typeof abA,
      setState: React.Dispatch<React.SetStateAction<typeof abA>>
    ) => (
      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
        <span className="sl">{label}</span>
        <select
          className="sel"
          value={state.model}
          onChange={(e) => setState((p) => ({ ...p, model: e.target.value }))}
        >
          {Object.entries(MODELS).map(([k, lbl]) => (
            <option key={k} value={k}>
              {lbl}
            </option>
          ))}
        </select>
        <select
          className="sel"
          value={state.lang}
          onChange={(e) => setState((p) => ({ ...p, lang: e.target.value }))}
        >
          {Object.entries(LANGUAGES).map(([k, lbl]) => (
            <option key={k} value={k}>
              {lbl}
            </option>
          ))}
        </select>
        <select
          className="sel"
          value={state.voice}
          onChange={(e) => setState((p) => ({ ...p, voice: e.target.value }))}
        >
          {Object.entries(VOICES).map(([k, [g]]) => (
            <option key={k} value={k}>
              {g} {k}
            </option>
          ))}
        </select>
        <select
          className="sel"
          value={state.eq}
          onChange={(e) => setState((p) => ({ ...p, eq: e.target.value }))}
        >
          {EQ_OPTS.map((eq) => (
            <option key={eq} value={eq}>
              {eq}
            </option>
          ))}
        </select>
        <select
          className="sel"
          value={state.ps}
          onChange={(e) =>
            setState((p) => ({ ...p, ps: e.target.value, style: STYLE_PRESETS[e.target.value] || "" }))
          }
        >
          {Object.keys(STYLE_PRESETS).map((k) => (
            <option key={k} value={k}>
              {k}
            </option>
          ))}
        </select>
        <textarea
          className="txa"
          rows={2}
          value={state.style}
          onChange={(e) => setState((p) => ({ ...p, style: e.target.value }))}
          placeholder="Stil"
        />
        <div className="etag-grid">
          {ETAGS.map(([em, lbl, tag]) => (
            <button
              key={lbl}
              type="button"
              className="btn btn-secondary btn-sm"
              title={lbl}
              onClick={() => setState((p) => ({ ...p, text: p.text + tag }))}
            >
              {em}
            </button>
          ))}
        </div>
        <textarea
          className="txa"
          rows={4}
          value={state.text}
          onChange={(e) => setState((p) => ({ ...p, text: e.target.value }))}
        />
        <button
          type="button"
          className="btn btn-primary btn-full"
          disabled={state.loading}
          onClick={() => runAb(which)}
        >
          {state.loading ? `${state.voice} üretiyor…` : `🔴 ${label} Üret`}
        </button>
        {state.err && <div className="card r">❌ {state.err}</div>}
        {state.res && (
          <div>
            <div className="card b">
              {state.res.voice} · {state.res.metrics.duration.toFixed(1)}s · {state.res.metrics.qs}/100
            </div>
            <audio controls src={base64ToDataUrl(state.res.wav)} />
            <WaveformCanvas
              wavBase64={state.res.wav}
              bgColor={theme.plt_bg}
              borderColor={theme.border}
            />
            <button
              type="button"
              className="btn btn-secondary btn-full"
              onClick={() =>
                downloadBase64(
                  state.res!.wav,
                  `ab_${which.toLowerCase()}_${state.res!.voice.toLowerCase()}.wav`,
                  "audio/wav"
                )
              }
            >
              💾 {label}
            </button>
          </div>
        )}
      </div>
    );

    return (
      <div className="tab-panel">
        <div className="card p">
          🔬 Aynı metni iki farklı ses/model/stil ile karşılaştır
        </div>
        <div className="grid-2" style={{ marginTop: "10px" }}>
          {renderAbCol("🅐 VERSİYON A", "A", abA, setAbA)}
          {renderAbCol("🅑 VERSİYON B", "B", abB, setAbB)}
        </div>
      </div>
    );
  }

  // ── TAB 4: FAVORİLER ──────────────────────────────────────────────────────
  return (
    <div className="tab-panel">
      {favorites.length === 0 ? (
        <div className="card b">
          ⭐ Henüz favori metin yok. Tek sekmesinden ekleyebilirsiniz.
        </div>
      ) : (
        <div>
          <button
            type="button"
            className="btn btn-secondary"
            style={{ marginBottom: "10px" }}
            onClick={() => setFavorites([])}
          >
            🗑️ Tümünü Sil
          </button>
          {favorites.map((fv) => (
            <div key={fv.id} style={{ marginBottom: "10px" }}>
              <div className="row-flex">
                <div className="fav-card" style={{ flex: 2 }}>
                  <div className="fav-name">⭐ {fv.name}</div>
                  <div className="fav-prev">
                    {fv.voice || "—"} · {fv.text.slice(0, 65)}
                  </div>
                </div>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => {
                    setTekText(fv.text || DEFAULT_TEK);
                    onNotice("📋 Tek sekmesine yüklendi!");
                  }}
                >
                  📋 Yükle
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => handlePlayFavorite(fv)}
                >
                  🔴 Oku
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() =>
                    setFavorites((prev) => prev.filter((x) => x.id !== fv.id))
                  }
                >
                  🗑️
                </button>
              </div>
              {fv.wavBase64 && (
                <audio controls src={base64ToDataUrl(fv.wavBase64)} />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
