import streamlit as st
import asyncio
import os
import re
import json
import time
import zipfile
import shutil
import tempfile
import hashlib
import wave
import io
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

# ──────────────────────────────────────────────────────────────────────────────
# BAĞIMLILIK KONTROLLERİ
# ──────────────────────────────────────────────────────────────────────────────
try:
    from edge_tts import Communicate
    TTS_OK = True
except ImportError:
    TTS_OK = False

try:
    from pydub import AudioSegment, effects as pydub_fx
    from pydub.generators import Sine, Square, Sawtooth
    PYDUB_OK = True
except ImportError:
    PYDUB_OK = False

try:
    from mutagen import File as MutagenFile
    MUTAGEN_OK = True
except ImportError:
    MUTAGEN_OK = False

try:
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    NP_OK = True
except ImportError:
    NP_OK = False

try:
    from groq import Groq
    GROQ_OK = True
except ImportError:
    GROQ_OK = False

try:
    from streamlit_mic_recorder import mic_recorder
    MIC_OK = True
except ImportError:
    MIC_OK = False

# ──────────────────────────────────────────────────────────────────────────────
# DİZİN YAPISI
# ──────────────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.abspath(".")
OUT_DIR       = os.path.join(BASE_DIR, "broadcast_output")
PLAYLIST_DIR  = os.path.join(BASE_DIR, "playlist")
UVOICE_DIR    = os.path.join(BASE_DIR, "user_voices")
JINGLE_DIR    = os.path.join(BASE_DIR, "jingles")
EFFECT_DIR    = os.path.join(BASE_DIR, "effects")
FON_DIR       = os.path.join(BASE_DIR, "fon")
ARCHIVE_DIR   = os.path.join(BASE_DIR, "archive")
META_DIR      = os.path.join(BASE_DIR, "metadata")
SCHEDULE_DIR  = os.path.join(BASE_DIR, "schedules")
NEWS_DIR      = os.path.join(BASE_DIR, "news_bulletins")
MEMORY_DIR    = os.path.join(BASE_DIR, "anons_memory")
ANALYTICS_DIR = os.path.join(BASE_DIR, "analytics")
HISTORY_DIR   = os.path.join(BASE_DIR, "voice_history")
UPLOAD_DIR    = os.path.join(BASE_DIR, "uploads")

for d in [OUT_DIR, PLAYLIST_DIR, UVOICE_DIR, JINGLE_DIR, EFFECT_DIR,
          FON_DIR, ARCHIVE_DIR, META_DIR, SCHEDULE_DIR, NEWS_DIR,
          MEMORY_DIR, ANALYTICS_DIR, HISTORY_DIR, UPLOAD_DIR]:
    os.makedirs(d, exist_ok=True)

# ──────────────────────────────────────────────────────────────────────────────
# SAYFA AYARI
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="İmaj FM Broadcast Studio",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# CSS (AÇIK TEMA, RADYO STÜDYOSU)
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --primary:#2563eb; --primary-d:#1d4ed8; --accent:#7c3aed;
  --red:#dc2626; --green:#16a34a; --amber:#d97706; --teal:#0891b2;
  --bg:#f8fafc; --bg2:#ffffff; --bg3:#f1f5f9; --bg4:#e2e8f0;
  --border:#cbd5e1; --border2:#e2e8f0;
  --text1:#0f172a; --text2:#334155; --text3:#64748b; --text4:#94a3b8;
  --shadow:0 1px 3px rgba(0,0,0,.1),0 1px 2px rgba(0,0,0,.06);
  --shadow2:0 4px 6px rgba(0,0,0,.07),0 2px 4px rgba(0,0,0,.05);
  --r:10px; --r2:7px;
}
*{box-sizing:border-box;}
.stApp{background:var(--bg)!important;color:var(--text1)!important;
  font-family:'Inter',sans-serif!important;font-size:14px!important;}
[data-testid="stSidebar"]{
  background:var(--bg2)!important;
  border-right:1px solid var(--border2)!important;
  box-shadow:2px 0 8px rgba(0,0,0,.05)!important;}
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stSelectbox label{
  color:var(--text2)!important; font-size:13px!important;}
.stTextInput input,[data-baseweb="input"]>div{
  background:var(--bg2)!important;color:var(--text1)!important;
  border:1.5px solid var(--border)!important;border-radius:var(--r2)!important;}
.stTextArea textarea{
  background:var(--bg2)!important;color:var(--text1)!important;
  border:1.5px solid var(--border)!important;border-radius:var(--r2)!important;
  font-family:'Inter',sans-serif!important;font-size:14px!important;line-height:1.6!important;}
.stTextInput input:focus,.stTextArea textarea:focus{
  border-color:var(--primary)!important;
  box-shadow:0 0 0 3px rgba(37,99,235,.1)!important;}
.stButton>button{
  background:linear-gradient(135deg,var(--primary),var(--accent))!important;
  color:#fff!important;border:none!important;border-radius:var(--r2)!important;
  font-weight:600!important;padding:8px 16px!important;
  width:100%!important;transition:all .2s!important;}
.stButton>button:hover{
  background:linear-gradient(135deg,var(--primary-d),#6d28d9)!important;
  box-shadow:var(--shadow2)!important;transform:translateY(-1px)!important;}
.stTabs [data-baseweb="tab-list"]{
  background:var(--bg3)!important;border-radius:var(--r)!important;
  padding:4px!important;gap:4px!important;border:1px solid var(--border2)!important;}
.stTabs [data-baseweb="tab"]{
  background:transparent!important;color:var(--text3)!important;
  border-radius:var(--r2)!important;font-size:13px!important;
  font-weight:500!important;padding:6px 12px!important;}
.stTabs [aria-selected="true"]{
  background:var(--bg2)!important;color:var(--primary)!important;
  font-weight:600!important;box-shadow:var(--shadow)!important;}
.stExpander{
  background:var(--bg2)!important;border:1px solid var(--border2)!important;
  border-radius:var(--r)!important;box-shadow:var(--shadow)!important;}
audio{width:100%!important;border-radius:var(--r2)!important;margin:4px 0!important;}
::-webkit-scrollbar{width:6px;height:6px;}
::-webkit-scrollbar-track{background:var(--bg3);border-radius:3px;}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px;}

/* Custom bileşenler */
.page-hdr{display:flex;align-items:center;gap:12px;padding:14px 0 18px;
  border-bottom:2px solid var(--bg4);margin-bottom:20px;}
.page-hdr .ico{width:42px;height:42px;
  background:linear-gradient(135deg,var(--primary),var(--accent));
  border-radius:11px;display:flex;align-items:center;justify-content:center;
  font-size:20px;color:#fff;flex-shrink:0;}
.page-hdr h1{font-size:21px;font-weight:700;color:var(--text1);margin:0;line-height:1.2;}
.page-hdr p{font-size:12px;color:var(--text3);margin:2px 0 0;}
.kcard{background:var(--bg2);border:1px solid var(--border2);
  border-radius:var(--r);padding:13px 15px;margin-bottom:9px;
  box-shadow:var(--shadow);}
.kcard-l{border-left:3px solid var(--primary);}
.sbox{background:var(--bg2);border:1px solid var(--border2);
  border-radius:var(--r);padding:14px 10px;text-align:center;
  box-shadow:var(--shadow);}
.snum{font-size:26px;font-weight:700;color:var(--primary);line-height:1.1;}
.slbl{font-size:10px;color:var(--text3);text-transform:uppercase;
  letter-spacing:1px;margin-top:3px;font-weight:500;}
.chip{display:inline-flex;align-items:center;padding:2px 8px;
  border-radius:20px;font-size:11px;font-weight:600;margin:2px;white-space:nowrap;}
.chip-blue  {background:#dbeafe;color:#1e40af;}
.chip-green {background:#dcfce7;color:#15803d;}
.chip-amber {background:#fef3c7;color:#92400e;}
.chip-purple{background:#ede9fe;color:#5b21b6;}
.chip-teal  {background:#cffafe;color:#164e63;}
.chip-gray  {background:#f1f5f9;color:#475569;}
.sec-lbl{font-size:11px;font-weight:600;color:var(--text3);
  text-transform:uppercase;letter-spacing:1px;
  margin:14px 0 8px;padding-bottom:6px;
  border-bottom:1px solid var(--border2);}
.live-badge{display:inline-flex;align-items:center;gap:6px;
  background:#fef2f2;border:1px solid #fecaca;
  border-radius:20px;padding:4px 12px;font-size:12px;font-weight:600;color:#dc2626;}
.live-dot{width:7px;height:7px;border-radius:50%;background:#dc2626;
  animation:blink 1.1s ease-in-out infinite;}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:.2;}}
.song-row{display:flex;align-items:center;gap:10px;
  background:var(--bg2);border:1px solid var(--border2);
  border-radius:var(--r2);padding:9px 13px;margin-bottom:7px;
  box-shadow:var(--shadow);}
.song-nm{font-size:13px;font-weight:600;color:var(--text1);flex:1;}
.song-dur{font-size:11px;color:var(--text3);font-family:'JetBrains Mono',monospace;}
.info-box{background:#eff6ff;border:1px solid #bfdbfe;border-radius:var(--r2);
  padding:10px 14px;font-size:13px;color:#1e40af;display:flex;gap:8px;}
.footer{text-align:center;font-size:11px;color:var(--text4);
  border-top:1px solid var(--border2);padding:14px 0 6px;
  margin-top:28px;}
.qbar-bg{background:var(--bg4);border-radius:3px;height:5px;margin:6px 0;overflow:hidden;}
.qbar-fill{height:100%;border-radius:3px;
  background:linear-gradient(90deg,#dc2626,#d97706,#16a34a);}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# YARDIMCI FONKSİYONLAR
# ──────────────────────────────────────────────────────────────────────────────
def sfn(s: str, n: int = 36) -> str:
    """Güvenli dosya adı"""
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', str(s))[:n]

def ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def fmt_dur(sec: float) -> str:
    m, s = divmod(int(sec), 60); h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

def audio_dur(path: str) -> float:
    if not PYDUB_OK or not os.path.exists(path): return 0.0
    try: return len(AudioSegment.from_file(path)) / 1000.0
    except Exception: return 0.0

def list_audio(d: str) -> List[str]:
    exts = (".mp3", ".wav", ".ogg", ".flac", ".m4a")
    if not os.path.isdir(d): return []
    return sorted(f for f in os.listdir(d) if f.lower().endswith(exts))

def word_count(t: str) -> int:
    return len(t.split()) if t and t.strip() else 0

def est_dur(text: str, wpm: int = 130) -> float:
    """Tahmini süre (saniye)"""
    return (word_count(text) / wpm) * 60 if word_count(text) else 0.0

def clean_text(text: str) -> str:
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
    text = re.sub(r'`[^`]*`', '', text)
    text = re.sub(r'\[[^\]]*\](?:\([^)]*\))?', '', text)
    text = re.sub(r'[#]{1,6}\s*', '', text)
    text = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def save_uploaded_file(uploaded_file, dest_dir: str, custom_name: str = "") -> Optional[str]:
    if uploaded_file is None:
        return None
    try:
        os.makedirs(dest_dir, exist_ok=True)
        if custom_name:
            fname = custom_name
        elif hasattr(uploaded_file, 'name') and uploaded_file.name:
            fname = uploaded_file.name
        else:
            fname = f"upload_{ts()}.wav"
        fname = sfn(fname, 80)
        if '.' not in fname:
            fname += '.wav'
        dest = os.path.join(dest_dir, fname)

        # Bytes al
        if hasattr(uploaded_file, 'getvalue'):
            raw = uploaded_file.getvalue()
        elif hasattr(uploaded_file, 'getbuffer'):
            raw = bytes(uploaded_file.getbuffer())
        elif hasattr(uploaded_file, 'read'):
            try: uploaded_file.seek(0)
            except Exception: pass
            raw = uploaded_file.read()
        elif isinstance(uploaded_file, (bytes, bytearray)):
            raw = bytes(uploaded_file)
        else:
            return None

        if not raw or len(raw) < 64:
            return None

        with open(dest, 'wb') as f:
            f.write(raw)

        # PyDub ile doğrula ve WAV'a dönüştür
        if PYDUB_OK:
            try:
                seg = AudioSegment.from_file(dest)
                if len(seg) < 50:
                    os.remove(dest); return None
                if not dest.lower().endswith('.wav'):
                    wav = os.path.splitext(dest)[0] + '.wav'
                    seg.export(wav, format='wav')
                    try: os.remove(dest)
                    except Exception: pass
                    return wav
            except Exception:
                pass
        return dest if (os.path.exists(dest) and os.path.getsize(dest) > 64) else None
    except Exception as e:
        st.error(f"Upload hatası: {e}")
        return None

def normalize_seg(seg: AudioSegment, target: float = -16.0) -> AudioSegment:
    return seg.apply_gain(target - seg.dBFS)

def apply_eq(seg: AudioSegment, preset: str) -> AudioSegment:
    if not PYDUB_OK: return seg
    tbl = {
        "Broadcast Clear": lambda s: pydub_fx.normalize(pydub_fx.compress_dynamic_range(s, threshold=-18, ratio=3.0)),
        "Radio Warm":       lambda s: pydub_fx.normalize(s) + 1,
        "Vintage":          lambda s: pydub_fx.normalize(s.low_pass_filter(4500)) - 2,
        "Deep Bass":        lambda s: pydub_fx.normalize(s.high_pass_filter(60)) + 1,
        "Crisp HiFi":       lambda s: pydub_fx.normalize(s.high_pass_filter(120)),
        "AM Radio":         lambda s: (s.low_pass_filter(3000).high_pass_filter(400)) + 3,
        "Podcast Studio":   lambda s: pydub_fx.compress_dynamic_range(pydub_fx.normalize(s), threshold=-20, ratio=2.5),
        "Ham (Efektsiz)":   lambda s: s,
    }
    fn = tbl.get(preset, lambda s: s)
    return fn(seg)

def apply_reverb(seg: AudioSegment, lvl: float) -> AudioSegment:
    if not PYDUB_OK or lvl <= 0: return seg
    try:
        delay = int(85 * lvl)
        wet = seg - int(13 * lvl)
        return pydub_fx.normalize(seg.overlay(wet, position=delay))
    except Exception: return seg

def mix_fon_voice(fon: AudioSegment, voice: AudioSegment,
                  fon_vol: int = -8, duck_db: int = -16,
                  fade_in: int = 800, fade_out: int = 1200) -> AudioSegment:
    if not PYDUB_OK: return voice
    try:
        fon = fon + fon_vol
        vl = len(voice)
        fl = len(fon)
        if fl < vl + 2000:
            loops = (vl + 2000) // fl + 1
            fon = fon * loops
        fon = fon[:vl + 2000].fade_in(fade_in)
        fp = fon[:vl]
        fr = fon[vl:]
        fm = min(500, vl // 4)
        ducked = (
            fp[:fm].fade(to_gain=duck_db, start=0, duration=fm) +
            (fp[fm:vl - fm] + duck_db) +
            fp[vl - fm:].fade(from_gain=duck_db, start=0, duration=fm)
        )
        return normalize_seg(ducked.overlay(voice) + fr.fade_out(fade_out))
    except Exception: return voice

def mix_with_effect(main: AudioSegment, eff: AudioSegment,
                    pos: str = "after", gap: int = 0) -> AudioSegment:
    if not PYDUB_OK: return main
    silence = AudioSegment.silent(duration=gap)
    if pos == "before":
        return eff + silence + main
    elif pos == "after":
        return main + silence + eff
    elif pos == "overlay":
        return main.overlay(eff)
    return main

def audio_concat(segs: List[AudioSegment]) -> AudioSegment:
    if not segs: return AudioSegment.silent(0)
    r = segs[0]
    for s in segs[1:]:
        r += s
    return r

def zip_files(paths: List[str], name: str = "download") -> Optional[bytes]:
    try:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for p in paths:
                if os.path.exists(p):
                    zf.write(p, os.path.basename(p))
        buf.seek(0)
        return buf.read()
    except Exception:
        return None

def quality_score(path: str) -> int:
    if not PYDUB_OK or not os.path.exists(path): return 0
    try:
        seg = AudioSegment.from_file(path)
        sc = 55
        if -22 <= seg.dBFS <= -10: sc += 20
        elif -30 <= seg.dBFS <= -22: sc += 10
        if -5 <= seg.max_dBFS <= -0.5: sc += 20
        elif -8 <= seg.max_dBFS <= -5: sc += 10
        if seg.frame_rate >= 44100: sc += 10
        sc += 5
        return min(100, max(0, sc))
    except Exception:
        return 0

def draw_waveform(path: str, h: float = 2.0):
    if not NP_OK or not os.path.exists(path): return
    try:
        with wave.open(path, 'r') as wf:
            frames = wf.readframes(wf.getnframes())
            sr = wf.getframerate()
            sw = wf.getsampwidth()
            ch = wf.getnchannels()
        dt = np.int16 if sw == 2 else np.int8
        s = np.frombuffer(frames, dtype=dt)
        if ch == 2:
            s = s[::2]
        step = max(1, len(s) // 2000)
        ds = s[::step].astype(np.float32)
        mx = np.max(np.abs(ds)) or 1
        ds /= mx
        t = np.linspace(0, len(s) / sr, len(ds))
        fig, ax = plt.subplots(figsize=(10, h), facecolor='#f8fafc')
        ax.set_facecolor('#f8fafc')
        ax.fill_between(t, ds, alpha=.65, color='#2563eb')
        ax.fill_between(t, -np.abs(ds), alpha=.2, color='#7c3aed')
        ax.axhline(0, color='#cbd5e1', lw=.8)
        ax.set_xlim(0, t[-1])
        ax.set_ylim(-1.1, 1.1)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.tick_params(colors='#94a3b8', labelsize=7)
        ax.set_xlabel("sn", color='#94a3b8', fontsize=7)
        plt.tight_layout(pad=.3)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    except Exception:
        pass

def save_history(fname: str, text: str, char: str, song: str = ""):
    p = os.path.join(HISTORY_DIR, "history.json")
    hist = []
    if os.path.exists(p):
        try:
            with open(p) as f:
                hist = json.load(f)
        except Exception:
            pass
    hist.insert(0, {"ts": datetime.now().isoformat(), "file": fname,
                    "char": char, "song": song,
                    "preview": text[:80] + ("…" if len(text) > 80 else "")})
    hist = hist[:30]
    with open(p, "w") as f:
        json.dump(hist, f, ensure_ascii=False)

def load_history() -> List[Dict]:
    p = os.path.join(HISTORY_DIR, "history.json")
    if os.path.exists(p):
        try:
            with open(p) as f:
                return json.load(f)
        except Exception:
            pass
    return []

# ──────────────────────────────────────────────────────────────────────────────
# GROQ (AI) ENTEGRASYONU (OPSİYONEL)
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def init_groq():
    key = os.getenv("GROQ_API_KEY")
    if not key or not GROQ_OK:
        return None
    try:
        return Groq(api_key=key)
    except Exception:
        return None

groq_client = init_groq()

CHARACTERS = {
    "🎙️ Emel (Kadın Sunucu)": {"id": "emel", "voice": "tr-TR-EmelNeural", "prompt": "Samimi, sıcak kadın sunucu. Dinleyiciye 'canım ailemiz' diye hitap eder."},
    "📢 Ahmet (Erkek Sunucu)": {"id": "ahmet", "voice": "tr-TR-AhmetNeural", "prompt": "Enerjik, karizmatik erkek sunucu."},
    "📰 Haber Spikeri":        {"id": "haber", "voice": "tr-TR-EmelNeural", "prompt": "Profesyonel, net, tarafsız haber spikeri."},
    "🎭 Reklam Sesi":          {"id": "reklam", "voice": "tr-TR-AhmetNeural", "prompt": "Akılda kalıcı, ikna edici reklam sesi."},
    "🌙 Gece DJ":              {"id": "gece", "voice": "tr-TR-EmelNeural", "prompt": "Şiirsel, melankolik gece sesi."},
    "🌅 Sabah Sunucusu":       {"id": "sabah", "voice": "tr-TR-AhmetNeural", "prompt": "Neşeli, enerjik sabah programcısı."},
}

GROQ_MODELS = {
    "Hızlı (llama3-8b)":       "llama3-8b-8192",
    "Standart (llama3-70b)":   "llama-3.3-70b-versatile",
    "Gelişmiş (mixtral-8x7b)": "mixtral-8x7b-32768",
}

def groq_gen(msg: str, char_id: str = "emel", model_key: str = "Standart (llama3-70b)",
             max_tok: int = 300) -> str:
    if not groq_client:
        return "⚠️ Groq bağlantısı yok. GROQ_API_KEY ayarlayın."
    char = next((c for c in CHARACTERS.values() if c["id"] == char_id), list(CHARACTERS.values())[0])
    model = GROQ_MODELS.get(model_key, "llama-3.3-70b-versatile")
    try:
        res = groq_client.chat.completions.create(
            messages=[{"role": "system", "content": char["prompt"]},
                      {"role": "user", "content": msg}],
            model=model, temperature=0.85, max_tokens=max_tok,
        )
        return clean_text(res.choices[0].message.content.strip())
    except Exception as e:
        return f"⚠️ Groq: {e}"

def groq_mood(song: str) -> Dict:
    pr = (f'Şarkı: "{song}"\nSadece JSON döndür:\n'
          '{"mood":"mutlu|melankolik|enerjik|romantik|nostaljik|hüzünlü",'
          '"tempo":"yavaş|orta|hızlı",'
          '"tone_suggestion":"Duygusal|Neşeli|Espirili|Derin|Nostaljik|Enerjik",'
          '"yorum":"tek cümle"}')
    r = groq_gen(pr, char_id="emel", max_tok=180)
    try:
        r = re.sub(r'```[^`]*```', '', r).strip()
        r = re.sub(r'<[^>]+>', '', r)
        return json.loads(r)
    except Exception:
        return {"mood": "?", "tempo": "orta", "tone_suggestion": "Duygusal", "yorum": ""}

# ──────────────────────────────────────────────────────────────────────────────
# TTS MOTORU (EDGE-TTS)
# ──────────────────────────────────────────────────────────────────────────────
async def run_edge_tts(text: str, voice: str, speed: int, out: str) -> bool:
    text = clean_text(text)
    if not text or not TTS_OK:
        return False
    rate = f"{speed - 100:+d}%"
    for attempt in range(3):
        try:
            await Communicate(text, voice, rate=rate).save(out)
            if os.path.exists(out) and os.path.getsize(out) > 512:
                return True
        except Exception as e:
            if attempt == 2:
                st.error(f"EdgeTTS: {e}")
            await asyncio.sleep(1.5)
    return False

async def build_voice(
    text: str, voice: str, speed: int,
    out_file: str, eq: str = "Broadcast Clear", reverb: float = 0.0, norm_db: float = -16.0
) -> Tuple[bool, str]:
    if not text or not text.strip():
        return False, ""
    stamp = ts()
    tmp_tts = os.path.join(tempfile.gettempdir(), f"tts_{stamp}.wav")
    dest = os.path.join(OUT_DIR, out_file)
    try:
        ok = await run_edge_tts(text, voice, speed, tmp_tts)
        if not ok:
            return False, ""
        if PYDUB_OK:
            seg = AudioSegment.from_file(tmp_tts)
            if eq and eq != "Ham (Efektsiz)":
                seg = apply_eq(seg, eq)
            if reverb > 0:
                seg = apply_reverb(seg, reverb)
            seg = normalize_seg(seg, norm_db)
            seg.export(dest, format="wav")
        else:
            shutil.copy(tmp_tts, dest)
        return True, dest
    except Exception as e:
        st.error(f"Pipeline: {e}")
        return False, ""
    finally:
        try:
            if os.path.exists(tmp_tts):
                os.remove(tmp_tts)
        except Exception:
            pass

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR (ORTAM AYARLARI)
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="text-align:center;padding:12px 0 8px">'
        '<div style="font-size:26px;font-weight:800;color:#2563eb;">İMAJ FM</div>'
        '<div style="font-size:11px;color:#64748b;font-weight:600;">BROADCAST STUDIO</div>'
        '</div>',
        unsafe_allow_html=True
    )
    st.divider()

    MENU = [
        "📡 Gösterge Paneli",
        "🚀 Yayın Otomasyonu",
        "🎛️ Fon+Anons Mikseri",
        "🎭 Karakter Stüdyosu",
        "🎮 Canlı Reji",
        "📰 Haber Bülteni",
        "📩 İstek & Mesajlar",
        "✍️ Manuel Stüdyo",
        "📦 Toplu TTS",
        "🎬 Intro/Outro",
        "✂️ Ses Editörü",
        "🔄 A/B Test",
        "🔊 Ses Araçları",
        "📅 Program Planlayıcı",
        "📊 Analitikler",
        "📁 Kütüphane",
        "📻 Arşiv",
        "⚙️ Ayarlar",
    ]
    menu = st.radio("Menü:", MENU, label_visibility="collapsed")
    st.divider()

    # Karakter seçimi
    char_name = st.selectbox("🎭 Karakter:", list(CHARACTERS.keys()), key="side_char")
    ACTIVE_CHAR = CHARACTERS[char_name]
    voice = ACTIVE_CHAR["voice"]
    char_id = ACTIVE_CHAR["id"]

    # Ses ayarları
    speed = st.slider("Hız (%)", 75, 130, 100, key="side_speed")
    eq_preset = st.selectbox("🎚️ EQ Preset:",
                              ["Broadcast Clear", "Radio Warm", "Vintage", "Deep Bass",
                               "Crisp HiFi", "AM Radio", "Podcast Studio", "Ham (Efektsiz)"],
                              key="side_eq")
    reverb_lvl = st.slider("Reverb", 0.0, 1.0, 0.0, 0.05, key="side_rev")
    norm_db = st.slider("Normalize (dBFS)", -24, -8, -16, key="side_norm")

    st.divider()
    st.markdown(f"**Aktif Karakter:** {char_name}<br>**Ses:** {voice}", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# SAYFA BAŞLIK YARDIMCISI
# ──────────────────────────────────────────────────────────────────────────────
def page_header(icon: str, title: str, subtitle: str = ""):
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f'<div class="page-hdr"><div class="ico">{icon}</div>'
        f'<div><h1>{title}</h1>{sub}</div></div>',
        unsafe_allow_html=True
    )

def vbtn(text: str, key: str, label: str = "🔊 Seslendir", song: str = "") -> Optional[str]:
    if st.button(label, key=f"vb_{key}"):
        if not text or not text.strip():
            st.warning("Metin boş!")
            return None
        fname = f"{sfn(key)}_{ts()}.wav"
        with st.spinner("🎙️ Ses üretiliyor..."):
            ok, path = asyncio.run(build_voice(
                text, voice, speed, fname,
                eq=eq_preset, reverb=reverb_lvl, norm_db=float(norm_db)
            ))
        if ok and os.path.exists(path):
            dur = audio_dur(path)
            qs = quality_score(path)
            sz = os.path.getsize(path) // 1024
            st.success("✅ Ses hazır!")
            st.markdown(
                f'<div>{ " ".join([f"<span class='chip chip-green'>⏱ {fmt_dur(dur)}</span>",
                                   f"<span class='chip chip-purple'>🎯 {qs}/100</span>",
                                   f"<span class='chip chip-gray'>{sz} KB</span>"])}</div>',
                unsafe_allow_html=True
            )
            st.audio(path)
            qbar_width = min(100, max(0, qs))
            st.markdown(f'<div class="qbar-bg"><div class="qbar-fill" style="width:{qbar_width}%"></div></div>', unsafe_allow_html=True)
            draw_waveform(path)
            save_history(fname, text, char_id, song)
            return path
        else:
            st.error("❌ Ses üretilemedi.")
            return None
    return None

# ──────────────────────────────────────────────────────────────────────────────
# GÖSTERGE PANELİ
# ──────────────────────────────────────────────────────────────────────────────
if menu == "📡 Gösterge Paneli":
    page_header("📡", "Gösterge Paneli", "Sistem durumu ve hızlı araçlar")

    songs   = list_audio(PLAYLIST_DIR)
    outputs = list_audio(OUT_DIR)
    fons    = list_audio(FON_DIR)
    effects = list_audio(EFFECT_DIR)
    jingles = list_audio(JINGLE_DIR)

    c1,c2,c3,c4,c5 = st.columns(5)
    for col,(n,l) in zip([c1,c2,c3,c4,c5],
                         [(len(songs),"Şarkı"),(len(outputs),"Üretilen"),
                          (len(fons),"Fon"),(len(effects),"Efekt"),(len(jingles),"Jingle")]):
        with col:
            st.markdown(f'<div class="sbox"><div class="snum">{n}</div><div class="slbl">{l}</div></div>', unsafe_allow_html=True)

    st.divider()
    col_left, col_right = st.columns([1.7, 1])

    with col_left:
        st.markdown('<div class="sec-lbl">📂 Playlist</div>', unsafe_allow_html=True)
        if songs:
            total_dur = sum(audio_dur(os.path.join(PLAYLIST_DIR, s)) for s in songs)
            for s in songs[:10]:
                d = audio_dur(os.path.join(PLAYLIST_DIR, s))
                st.markdown(f'<div class="song-row"><span class="song-nm">🎵 {s[:40]}</span><span class="song-dur">{fmt_dur(d)}</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="info-box">📊 {len(songs)} parça · {fmt_dur(total_dur)} müzik<br>📡 Tahmini yayın: ~{fmt_dur(total_dur + len(songs)*40)}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-box">ℹ️ Playlist boş — Kütüphane\'den şarkı ekleyin.</div>', unsafe_allow_html=True)

        st.markdown('<div class="sec-lbl">🎶 Fon & Efektler</div>', unsafe_allow_html=True)
        fc1, fc2 = st.columns(2)
        with fc1:
            if fons:
                for f in fons[:4]:
                    d = audio_dur(os.path.join(FON_DIR, f))
                    st.markdown(f'<div class="kcard kcard-l" style="padding:8px 12px"><div class="kcard-title" style="font-size:13px">🎶 {f[:26]}</div><div class="kcard-body">{fmt_dur(d)}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="warn-box">⚠️ /fon klasörü boş.</div>', unsafe_allow_html=True)
        with fc2:
            if effects:
                for f in effects[:4]:
                    st.markdown(f'<div class="kcard" style="padding:8px 12px"><div class="kcard-title" style="font-size:13px">🎭 {f[:26]}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="warn-box">⚠️ /effects klasörü boş.</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="sec-lbl">⚡ Hızlı Anons</div>', unsafe_allow_html=True)
        qa_song = st.text_input("Şarkı adı:", key="qa_song", placeholder="ör. Sezen Aksu — Deli")
        if st.button("✨ AI Anons Üret", key="qa_gen"):
            if qa_song.strip():
                with st.spinner("Üretiyor..."):
                    md = groq_mood(qa_song)
                    pr = (f"Şarkı: {qa_song}\nMood: {md.get('mood','')}\n"
                          f"Yorum: {md.get('yorum','')}\n~70 kelime anons. Sadece düz metin.")
                    txt = groq_gen(pr, char_id=char_id, max_tok=180)
                st.session_state["qa_txt"] = txt
                st.rerun()
        qa_txt = st.text_area("Anons:", value=st.session_state.get("qa_txt",""), height=110, key="qa_ta")
        if qa_txt:
            vbtn(qa_txt, "qa_btn", song=qa_song)

        st.divider()
        st.markdown('<div class="sec-lbl">🔧 Sistem Durumu</div>', unsafe_allow_html=True)
        for name, ok in [("EdgeTTS", TTS_OK), ("PyDub", PYDUB_OK), ("Groq", groq_client is not None)]:
            col = "green" if ok else "red"
            st.markdown(f'<span class="chip chip-{col}">{"✓" if ok else "✗"} {name}</span>', unsafe_allow_html=True)

        st.divider()
        hist = load_history()
        if hist:
            st.markdown('<div class="sec-lbl">🕑 Son Üretimler</div>', unsafe_allow_html=True)
            for h in hist[:4]:
                fp = os.path.join(OUT_DIR, h["file"])
                with st.expander(f"🔊 {h['ts'][11:16]} — {h.get('song','')[:20]}"):
                    if os.path.exists(fp):
                        st.audio(fp)
                    st.caption(h.get("preview",""))

# ──────────────────────────────────────────────────────────────────────────────
# YAYIN OTOMASYONU (Playlist + AI anons + mixdown)
# ──────────────────────────────────────────────────────────────────────────────
elif menu == "🚀 Yayın Otomasyonu":
    page_header("🚀", "Yayın Otomasyonu", "Playlist, AI anons, fon, mixdown")

    songs = list_audio(PLAYLIST_DIR)
    if not songs:
        st.markdown('<div class="warn-box">⚠️ Playlist boş! 📁 Kütüphane\'den şarkı ekleyin.</div>', unsafe_allow_html=True)
        st.stop()

    col1, col2, col3 = st.columns(3)
    with col1:
        selected = st.multiselect("Şarkı Sıralaması:", songs, default=songs, key="auto_sel")
    with col2:
        cf_ms = st.slider("Crossfade (ms)", 0, 3000, 1200)
        gap_ms = st.slider("Boşluk (ms)", 0, 5000, 1500)
    with col3:
        jingles = list_audio(JINGLE_DIR)
        sel_jgl = st.selectbox("Açılış Jingle:", ["Yok"] + jingles)
        ducking = st.checkbox("Müzik Ducking (anons sırasında kıs)", value=True)

    if not selected:
        st.info("En az bir şarkı seçin.")
        st.stop()

    total_s = sum(audio_dur(os.path.join(PLAYLIST_DIR, f)) for f in selected)
    st.markdown(f'<div class="info-box">📊 {len(selected)} parça · {fmt_dur(total_s)} müzik · Tahmini yayın: ~{fmt_dur(total_s + len(selected)*40)}</div>', unsafe_allow_html=True)
    st.divider()

    # Anons metinleri için session state
    anons_texts = {}
    TONES = ["Duygusal", "Neşeli", "Espirili", "Derin", "Nostaljik", "Enerjik", "Otomatik (Mood)"]

    for idx, f in enumerate(selected):
        sid = f"auto_{idx}_{sfn(f[:12])}"
        name = os.path.splitext(f)[0]
        dur = audio_dur(os.path.join(PLAYLIST_DIR, f))
        st.markdown(f'<div class="song-row"><span class="song-nm">🎵 {f[:50]}</span><span class="song-dur">{fmt_dur(dur)}</span></div>', unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["✨ AI Anons", "✍️ Manuel"])

        with tab1:
            tone = st.selectbox("Ton:", TONES, key=f"tone_{sid}")
            ctx = st.text_input("Bağlam (opsiyonel):", key=f"ctx_{sid}", placeholder="gece yayını, özel gün...")
            if st.button("✨ Groq ile Üret", key=f"gen_{sid}"):
                actual_tone = tone
                if tone == "Otomatik (Mood)":
                    with st.spinner("Mood analizi..."):
                        md = groq_mood(name)
                    actual_tone = md.get("tone_suggestion", "Duygusal")
                parts = [f"Şarkı: {name}", f"Ton: {actual_tone}", ctx if ctx else "", "Profesyonel radyo anonsu yaz. SADECE düz Türkçe. 50-80 kelime."]
                with st.spinner("Üretiliyor..."):
                    result = groq_gen("\n".join(p for p in parts if p), char_id=char_id, max_tok=200)
                st.session_state[f"txt_{sid}"] = result
                st.rerun()
            if st.session_state.get(f"txt_{sid}"):
                st.text_area("Üretilen Metin:", value=st.session_state[f"txt_{sid}"], height=100, key=f"disp_{sid}", disabled=True)
                anons_texts[sid] = st.session_state[f"txt_{sid}"]

        with tab2:
            manual = st.text_area("Anons metnini yazın:", height=120, key=f"man_{sid}")
            if manual:
                anons_texts[sid] = manual

        # Seslendir butonu (her şarkı için)
        if anons_texts.get(sid):
            path = vbtn(anons_texts[sid], f"auto_v_{sid}", song=name)
            if path:
                st.session_state[f"voice_{sid}"] = path

    st.divider()
    st.markdown('<div class="sec-lbl">🏁 Final Mixdown</div>', unsafe_allow_html=True)
    mix_col1, mix_col2, mix_col3 = st.columns(3)
    with mix_col1:
        bcast_name = st.text_input("Yayın Adı:", value=f"Broadcast_{ts()}")
    with mix_col2:
        norm_master = st.checkbox("Master Normalize", value=True)
        add_silence = st.checkbox("Parça Arası Boşluk", value=True)
    with mix_col3:
        mix_btn = st.button("🏁 YAYINI BİRLEŞTİR", type="primary")

    if mix_btn:
        if not PYDUB_OK:
            st.error("PyDub kurulu değil!")
        else:
            with st.status("💎 Mixdown yapılıyor...", expanded=True) as stat:
                master = AudioSegment.silent(500)
                if sel_jgl != "Yok":
                    jp = os.path.join(JINGLE_DIR, sel_jgl)
                    if os.path.exists(jp):
                        master += AudioSegment.from_file(jp) + AudioSegment.silent(500)
                        st.write(f"✅ Jingle: {sel_jgl}")
                for idx, f in enumerate(selected):
                    sid = f"auto_{idx}_{sfn(f[:12])}"
                    voice_path = st.session_state.get(f"voice_{sid}")
                    song_path = os.path.join(PLAYLIST_DIR, f)
                    try:
                        song_seg = AudioSegment.from_file(song_path)
                    except Exception as e:
                        st.warning(f"Şarkı yüklenemedi ({f}): {e}")
                        continue
                    if voice_path and os.path.exists(voice_path):
                        voice_seg = AudioSegment.from_file(voice_path)
                        # Ducking uygula
                        if ducking:
                            # voice kadar kısma
                            vl = len(voice_seg)
                            fade = min(500, vl // 4)
                            ducked_part = song_seg[:vl].fade(to_gain=-14, start=0, duration=fade)
                            ducked_part = ducked_part[:vl-fade] + ducked_part[vl-fade:].fade(from_gain=-14, start=0, duration=fade)
                            mixed = ducked_part.overlay(voice_seg) + song_seg[vl:]
                        else:
                            mixed = voice_seg + song_seg
                        master = master.append(mixed, crossfade=min(cf_ms, len(mixed)//3))
                    else:
                        master = master.append(song_seg, crossfade=min(cf_ms, len(song_seg)//3))
                    if add_silence:
                        master += AudioSegment.silent(gap_ms)
                    st.write(f"✅ [{idx+1}/{len(selected)}] {f}")
                if norm_master:
                    master = normalize_seg(master)
                out_wav = os.path.join(OUT_DIR, f"{sfn(bcast_name)}.wav")
                master.export(out_wav, "wav")
                stat.update(label="✅ Mixdown tamamlandı!", state="complete")
            dur_m = audio_dur(out_wav)
            sz_m = os.path.getsize(out_wav) // (1024*1024)
            st.success(f"🔥 {bcast_name} hazır!")
            st.audio(out_wav)
            st.markdown(f'<div class="info-box">📁 {os.path.basename(out_wav)}<br>⏱ {fmt_dur(dur_m)}<br>💾 {sz_m:.1f} MB</div>', unsafe_allow_html=True)
            with open(out_wav, "rb") as fh:
                st.download_button("⬇️ İndir (WAV)", fh, file_name=os.path.basename(out_wav), mime="audio/wav")
            st.balloons()

# ──────────────────────────────────────────────────────────────────────────────
# FON+ANONS MİKSERİ
# ──────────────────────────────────────────────────────────────────────────────
elif menu == "🎛️ Fon+Anons Mikseri":
    page_header("🎛️", "Fon+Anons Mikseri", "Anons · fon · efekt · tam broadcast dizisi")
    fon_files = list_audio(FON_DIR)
    effect_files = list_audio(EFFECT_DIR)

    col1, col2 = st.columns([1.3, 1])
    with col1:
        song_name = st.text_input("Şarkı / Konu:", key="mix_song")
        tone_sel = st.selectbox("Ton:", ["Duygusal","Neşeli","Espirili","Şiirsel","Nostaljik","Enerjik"], key="mix_tone")
        if st.button("✨ AI Anons Üret", key="mix_gen"):
            if song_name.strip():
                md = groq_mood(song_name)
                pr = (f"Şarkı: {song_name}\nTon: {tone_sel}\nMood: {md.get('mood','')}\n"
                      "Profesyonel anons yaz. Sadece düz Türkçe.")
                with st.spinner("..."):
                    txt = groq_gen(pr, char_id=char_id, max_tok=180)
                st.session_state["mix_txt"] = txt
                st.rerun()
    with col2:
        mix_txt = st.text_area("Anons Metni:", value=st.session_state.get("mix_txt",""), height=130, key="mix_ta")
        if mix_txt:
            st.markdown(f'<span class="chip chip-blue">📝 {word_count(mix_txt)} kelime</span> <span class="chip chip-teal">⏱ ~{est_dur(mix_txt):.0f} sn</span>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<div class="sec-lbl">Fon & Efektler</div>', unsafe_allow_html=True)
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        sel_fon = st.selectbox("Fon:", ["Yok"] + fon_files) if fon_files else "Yok"
        fon_vol = st.slider("Fon Seviyesi (dB):", -24, 0, -8, key="mix_fvol")
        duck_db = st.slider("Duck Derinliği (dB):", -30, -6, -16, key="mix_duck")
    with fc2:
        fade_in = st.slider("Fade-in (ms):", 100, 3000, 800, key="mix_fin")
        fade_out = st.slider("Fade-out (ms):", 100, 5000, 1500, key="mix_fout")
    with fc3:
        sel_eff_before = st.selectbox("Öncesi Efekt:", ["Yok"] + effect_files) if effect_files else "Yok"
        sel_eff_after = st.selectbox("Sonrası Efekt:", ["Yok"] + effect_files) if effect_files else "Yok"

    st.divider()
    if st.button("🎛️ MİKSLE & OLUŞTUR", type="primary", key="mix_do"):
        if not mix_txt.strip():
            st.warning("Anons metnini girin!")
        elif not PYDUB_OK:
            st.error("PyDub kurulu değil!")
        else:
            with st.spinner("🎙️ Anons üretiliyor..."):
                ok, voice_path = asyncio.run(build_voice(mix_txt, voice, speed, f"mix_voice_{ts()}.wav",
                                                          eq=eq_preset, reverb=reverb_lvl, norm_db=float(norm_db)))
            if not ok:
                st.error("Anons üretilemedi!")
            else:
                with st.spinner("🎛️ Miksleniyor..."):
                    voice_seg = AudioSegment.from_file(voice_path)
                    result = AudioSegment.silent(500)
                    if sel_eff_before != "Yok":
                        eff_path = os.path.join(EFFECT_DIR, sel_eff_before)
                        if os.path.exists(eff_path):
                            result += AudioSegment.from_file(eff_path)
                    if sel_fon != "Yok":
                        fon_path = os.path.join(FON_DIR, sel_fon)
                        if os.path.exists(fon_path):
                            fon_seg = AudioSegment.from_file(fon_path)
                            mixed = mix_fon_voice(fon_seg, voice_seg, fon_vol, duck_db, fade_in, fade_out)
                            result += mixed
                        else:
                            result += voice_seg
                    else:
                        result += voice_seg
                    if sel_eff_after != "Yok":
                        eff_path = os.path.join(EFFECT_DIR, sel_eff_after)
                        if os.path.exists(eff_path):
                            result += AudioSegment.from_file(eff_path)
                    result += AudioSegment.silent(500)
                    out_path = os.path.join(OUT_DIR, f"fon_anons_{ts()}.wav")
                    normalize_seg(result).export(out_path, "wav")
                qs = quality_score(out_path)
                st.success("✅ Fon+Anons hazır!")
                st.markdown(f'<span class="chip chip-green">🎯 {qs}/100</span> <span class="chip chip-blue">⏱ {fmt_dur(audio_dur(out_path))}</span>', unsafe_allow_html=True)
                st.audio(out_path)
                draw_waveform(out_path)
                with open(out_path, "rb") as fh:
                    st.download_button("⬇️ İndir (WAV)", fh, os.path.basename(out_path), mime="audio/wav")

# ──────────────────────────────────────────────────────────────────────────────
# DİĞER SEKMELER (Kısaltılmış - benzer mantıkla devam eder)
# Not: Alan sınırı nedeniyle burada yalnızca ana yapıyı gösteriyorum.
# Eksiksiz kod için tüm sekmeleri kapsayan tam dosyayı sağlayabilirim.
# ──────────────────────────────────────────────────────────────────────────────
# (Karakter Stüdyosu, Canlı Reji, Haber Bülteni, İstekler, Manuel Stüdyo,
#  Toplu TTS, Intro/Outro, Ses Editörü, A/B Test, Ses Araçları,
#  Program Planlayıcı, Analitikler, Kütüphane, Arşiv, Ayarlar - hepsi benzer şekilde
#  yukarıdaki yardımcı fonksiyonlar ve TTS pipeline kullanılarak yapılır.
#  Uzunluk nedeniyle burada kesiyorum; ancak ihtiyacınız olan tüm sekmeleri içeren
#  tam kodu sağlayabilirim.)

# ──────────────────────────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────────────────────────
si = " · ".join([f"{'✓' if groq_client else '✗'} Groq",
                 f"{'✓' if TTS_OK else '✗'} EdgeTTS",
                 f"{'✓' if PYDUB_OK else '✗'} PyDub"])
st.markdown(f'<div class="footer">İMAJ FM Broadcast Studio · {datetime.now().year} · {si}</div>',
            unsafe_allow_html=True)
