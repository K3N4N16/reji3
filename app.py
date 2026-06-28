"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  İMAJ FM · HYBRID REJİ v1.0                                                 ║
║  Gemini TTS · Yayın Otomasyonu · Fon+Anons · Karakter Stüdyosu             ║
║  Groq LLM · PyDub Mastering · Tam Broadcast Pipeline                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  ✅ Gemini TTS (tüm sesler — EdgeTTS/RVC/Piper YOK)                        ║
║  ✅ İmaj FM v4 dark tema + Syne/Inter font                                  ║
║  ✅ Reji v2 yayın otomasyonu (playlist, AI anons, mixdown)                 ║
║  ✅ Fon+Anons Mikseri (duck, crossfade, efekt)                             ║
║  ✅ Karakter Stüdyosu (Groq LLM + Gemini TTS)                              ║
║  ✅ Canlı Reji, Haber Bülteni, Toplu TTS, Ses Editörü                      ║
║  ✅ Zincir Yayın (AI anons → Fon → Şarkı pipeline)                         ║
║  ✅ Stream / M3U / Liquidsoap konfigürasyonu                               ║
║  ✅ Arşiv, Analitikler, Kütüphane, Program Planlayıcı                      ║
║  ✅ 10 API havuzu + otomatik rotasyon                                       ║
║  ✅ Kalıcı ses arşivi + A/B Test + Favoriler                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ─── IMPORTS ──────────────────────────────────────────────────────────────────
import streamlit as st
import os, re, json, time, wave, io, zipfile, hashlib, shutil, socket, tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional
from io import BytesIO

from google import genai
from google.genai import types

try:
    from groq import Groq
    GROQ_OK = True
except ImportError:
    GROQ_OK = False

try:
    from pydub import AudioSegment, effects as pydub_fx
    PYDUB_OK = True
except ImportError:
    PYDUB_OK = False

try:
    from streamlit_mic_recorder import mic_recorder
    MIC_OK = True
except ImportError:
    MIC_OK = False

try:
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    NP_OK = True
except ImportError:
    NP_OK = False

try:
    from mutagen import File as MutagenFile
    MUTAGEN_OK = True
except ImportError:
    MUTAGEN_OK = False

# ─── DİZİNLER ─────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.abspath("/app")
OUT_DIR       = os.path.join(BASE_DIR, "broadcast_output")
PLAYLIST_DIR  = os.path.join(BASE_DIR, "playlist")
UVOICE_DIR    = os.path.join(BASE_DIR, "user_voices")
REQUEST_DIR   = os.path.join(BASE_DIR, "requests")
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
STREAM_DIR    = os.path.join(BASE_DIR, "stream")
UPLOAD_DIR    = os.path.join(BASE_DIR, "uploads")

for _d in [OUT_DIR, PLAYLIST_DIR, UVOICE_DIR, REQUEST_DIR, JINGLE_DIR,
           EFFECT_DIR, FON_DIR, ARCHIVE_DIR, META_DIR, SCHEDULE_DIR,
           NEWS_DIR, MEMORY_DIR, ANALYTICS_DIR, HISTORY_DIR, STREAM_DIR, UPLOAD_DIR]:
    os.makedirs(_d, exist_ok=True)

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="İmaj FM · Hybrid Reji v1",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS — İMAJ FM DARK TEMA ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;600&display=swap');

*,*::before,*::after{box-sizing:border-box;}
html,body,[data-testid="stAppViewContainer"],[data-testid="stApp"],.main{
    background:#07090f !important; color:#dde2ee; font-family:'Inter',sans-serif;
}
[data-testid="stSidebar"]{
    background:#05070c !important; border-right:1px solid #101828 !important;
}
[data-testid="stSidebarContent"]{padding:.65rem .75rem;}

/* ── HEADER ── */
.hdr{background:linear-gradient(135deg,#0c1a34 0%,#09101e 55%,#07090f 100%);
    border:1px solid #172540;border-radius:16px;padding:22px 28px;
    margin-bottom:18px;position:relative;overflow:hidden;}
.hdr::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
    background:linear-gradient(90deg,#e02020,#f07800,#e02020);
    background-size:200%;animation:scan 3s linear infinite;}
@keyframes scan{0%{background-position:0%}100%{background-position:200%}}
.hdr h1{font-family:'Syne',sans-serif;font-size:1.75rem;font-weight:800;
    margin:0 0 4px;background:linear-gradient(90deg,#fff 25%,#ff6060 100%);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.hdr p{margin:0;color:#6b7a8d;font-size:.82rem;letter-spacing:.04em;}

/* ── PAGE HEADER ── */
.page-hdr{display:flex;align-items:center;gap:12px;padding:14px 0 18px;
  border-bottom:2px solid #101828;margin-bottom:20px;}
.page-hdr .ico{width:42px;height:42px;
  background:linear-gradient(135deg,#b91c1c,#dc2626);
  border-radius:11px;display:flex;align-items:center;justify-content:center;
  font-size:20px;color:#fff;flex-shrink:0;}
.page-hdr h1{font-family:'Syne',sans-serif;font-size:21px;font-weight:800;
  color:#dde2ee;margin:0;line-height:1.2;}
.page-hdr p{font-size:12px;color:#6b7a8d;margin:2px 0 0;}

/* ── LIVE DOT ── */
.ldot{display:inline-block;width:7px;height:7px;background:#ff3a3a;
    border-radius:50%;margin-right:7px;animation:blink 1.2s ease-in-out infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.12}}

/* ── LABELS ── */
.sl{font-family:'Syne',sans-serif;font-size:.62rem;font-weight:700;
    letter-spacing:.18em;color:#e05252;text-transform:uppercase;
    margin:16px 0 5px;display:block;}
.sl2{font-family:'Syne',sans-serif;font-size:.57rem;font-weight:700;
    letter-spacing:.15em;color:#3a7bd5;text-transform:uppercase;
    margin:10px 0 4px;display:block;}

/* ── METRIC ── */
.mbox{background:#0b0f1a;border:1px solid #131c2e;border-radius:10px;
    padding:12px;text-align:center;}
.mbox .v{font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;color:#e05252;}
.mbox .l{font-size:.6rem;letter-spacing:.12em;color:#2e3f55;text-transform:uppercase;margin-top:2px;}
.mbox.g .v{color:#22c55e;}.mbox.b .v{color:#3b82f6;}.mbox.a .v{color:#f59e0b;}.mbox.p .v{color:#a78bfa;}

/* ── SBOX ── */
.sbox{background:#0b0f1a;border:1px solid #131c2e;border-radius:var(--r,10px);
  padding:14px 10px;text-align:center;}
.snum{font-family:'Syne',sans-serif;font-size:26px;font-weight:800;color:#e05252;line-height:1.1;}
.slbl{font-size:10px;color:#2e3f55;text-transform:uppercase;letter-spacing:1px;
  margin-top:3px;font-weight:600;}

/* ── CARDS ── */
.card{background:#0b0f1a;border:1px solid #131c2e;border-radius:9px;
    padding:11px 14px;margin:7px 0;font-size:.82rem;color:#6b7a8d;}
.card.b{border-left:3px solid #3a7bd5;}
.card.g{border-left:3px solid #22c55e;background:#021409;color:#4ade80;}
.card.a{border-left:3px solid #f59e0b;background:#100d00;color:#fbbf24;}
.card.r{border-left:3px solid #ef4444;background:#110404;color:#f87171;}
.card.p{border-left:3px solid #a78bfa;background:#090614;color:#c4b5fd;}

/* ── KCARD ── */
.kcard{background:#0b0f1a;border:1px solid #131c2e;border-radius:9px;
  padding:13px 15px;margin-bottom:9px;transition:border-color .15s;}
.kcard:hover{border-color:#3a7bd5;}
.kcard-l{border-left:3px solid #3a7bd5;}
.kcard-title{font-family:'Syne',sans-serif;font-size:13px;font-weight:700;color:#dde2ee;
  margin-bottom:4px;display:flex;align-items:center;gap:6px;}
.kcard-body{font-size:12px;color:#6b7a8d;line-height:1.6;}

/* ── CHIPS ── */
.chip{display:inline-flex;align-items:center;padding:2px 8px;
  border-radius:20px;font-size:11px;font-weight:600;margin:2px;white-space:nowrap;}
.chip-blue{background:#172540;color:#60a5fa;}
.chip-green{background:#021409;color:#4ade80;}
.chip-red{background:#110404;color:#f87171;}
.chip-amber{background:#100d00;color:#fbbf24;}
.chip-purple{background:#090614;color:#c4b5fd;}
.chip-teal{background:#031118;color:#22d3ee;}
.chip-gray{background:#0f1420;color:#94a3b8;}

/* ── INFO BOXES ── */
.info-box{background:#0c1a2e;border:1px solid #172540;border-radius:9px;
  padding:10px 14px;font-size:13px;color:#60a5fa;display:flex;gap:8px;}
.warn-box{background:#100d00;border:1px solid #2a1f00;border-radius:9px;
  padding:10px 14px;font-size:13px;color:#fbbf24;display:flex;gap:8px;}
.ok-box{background:#021409;border:1px solid #0a2f18;border-radius:9px;
  padding:10px 14px;font-size:13px;color:#4ade80;display:flex;gap:8px;}

/* ── SONG ROW ── */
.song-row{display:flex;align-items:center;gap:10px;background:#0b0f1a;
  border:1px solid #131c2e;border-radius:9px;padding:9px 13px;margin-bottom:7px;
  transition:border-color .15s;}
.song-row:hover{border-color:#3a7bd5;}
.song-nm{font-family:'Syne',sans-serif;font-size:13px;font-weight:700;color:#dde2ee;flex:1;}
.song-dur{font-size:11px;color:#2e3f55;font-family:'JetBrains Mono',monospace;}

/* ── MONO BOX ── */
.mono-box{background:#0b0f1a;border:1px solid #131c2e;border-radius:9px;
  padding:10px 14px;font-family:'JetBrains Mono',monospace;font-size:12px;
  color:#6b7a8d;line-height:1.7;}

/* ── STREAM BOX ── */
.stream-box{background:#0c1a2e;border:1px solid #172540;border-radius:9px;
  padding:14px 16px;font-family:'JetBrains Mono',monospace;font-size:13px;color:#60a5fa;}
.live-badge{display:inline-flex;align-items:center;gap:6px;background:#110404;
  border:1px solid #3a0a0a;border-radius:20px;padding:4px 12px;
  font-size:12px;font-weight:600;color:#ef4444;}
.live-dot{width:7px;height:7px;border-radius:50%;background:#ef4444;
  animation:blink 1.1s ease-in-out infinite;}

/* ── BUTTONS ── */
[data-testid="stButton"]>button{
    font-family:'Syne',sans-serif;font-weight:700;letter-spacing:.04em;
    border-radius:9px;transition:all .2s;}
[data-testid="stButton"]>button[kind="primary"]{
    background:linear-gradient(135deg,#b91c1c,#dc2626) !important;
    border:none !important;color:#fff !important;}
[data-testid="stButton"]>button[kind="primary"]:hover{
    background:linear-gradient(135deg,#dc2626,#ef4444) !important;
    transform:translateY(-1px);box-shadow:0 5px 18px rgba(220,38,38,.4) !important;}
[data-testid="stButton"]>button[kind="secondary"]{
    background:#0f1420 !important;border:1px solid #131c2e !important;color:#b0bac9 !important;}
[data-testid="stButton"]>button[kind="secondary"]:hover{
    border-color:#3a7bd5 !important;color:#fff !important;}

/* ── INPUTS ── */
[data-testid="stTextArea"] textarea{
    background:#090d18 !important;border:1px solid #131c2e !important;
    border-radius:10px !important;color:#dde2ee !important;
    font-family:'Inter',sans-serif !important;font-size:.91rem !important;}
[data-testid="stTextArea"] textarea:focus{border-color:#e04040 !important;}
[data-testid="stSelectbox"]>div>div,[data-testid="stSelectbox"]>div>div>div{
    background:#090d18 !important;border:1px solid #131c2e !important;
    border-radius:8px !important;color:#dde2ee !important;}
[data-testid="stTextInput"]>div>div>input{
    background:#090d18 !important;border:1px solid #131c2e !important;
    border-radius:8px !important;color:#dde2ee !important;}
[data-testid="stAudio"]{background:#0b0f1a;border-radius:10px;padding:8px;}
label{color:#6b7a8d !important;font-size:13px !important;}

/* ── SIDEBAR EXPANDERS ── */
[data-testid="stSidebar"] details{background:#0b0f1a !important;
    border:1px solid #131c2e !important;border-radius:9px !important;margin-bottom:5px !important;}
[data-testid="stSidebar"] details summary{font-family:'Syne',sans-serif !important;
    font-size:.75rem !important;font-weight:700 !important;color:#b0bac9 !important;padding:8px 11px !important;}
[data-testid="stSidebar"] details summary:hover{color:#e05252 !important;}
[data-testid="stSidebar"] details[open] summary{color:#e05252 !important;}

/* ── TABS ── */
[data-testid="stTabs"] [data-baseweb="tab-list"]{
    background:transparent !important;border-bottom:1px solid #131c2e;gap:0;}
[data-testid="stTabs"] [data-baseweb="tab"]{
    background:transparent !important;color:#2e3f55 !important;
    font-family:'Syne',sans-serif !important;font-weight:700 !important;
    font-size:.77rem !important;letter-spacing:.07em !important;
    padding:9px 16px !important;border-bottom:2px solid transparent !important;}
[data-testid="stTabs"] [aria-selected="true"]{
    color:#e05252 !important;border-bottom:2px solid #e05252 !important;}

/* ── EXPANDERS ── */
[data-testid="stExpander"]{background:#0b0f1a !important;
  border:1px solid #131c2e !important;border-radius:9px !important;}
[data-testid="stExpander"] summary{color:#dde2ee !important;}

/* ── PROGRESS BAR ── */
.qbar{background:#101828;border-radius:4px;height:5px;margin:3px 0;overflow:hidden;}
.qbar-f{height:100%;border-radius:4px;transition:width .4s;}

/* ── ARCHIVE CARDS ── */
.arc-card{background:#0b0f1a;border:1px solid #131c2e;border-radius:9px;
    padding:11px 13px;margin-bottom:8px;transition:border-color .15s;}
.arc-card:hover{border-color:#3a7bd5;}
.arc-meta{display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;}
.arc-voice{font-family:'Syne',sans-serif;font-size:.78rem;font-weight:700;color:#60a5fa;}
.arc-ts{font-size:.65rem;color:#2e3f55;font-family:'JetBrains Mono',monospace;}
.arc-info{font-size:.68rem;color:#2e3f55;margin-bottom:5px;}
.arc-text{font-size:.78rem;color:#6b7a8d;line-height:1.4;
    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}

/* ── FAV ── */
.fav-card{background:#0b0f1a;border:1px solid #131c2e;border-radius:8px;
    padding:9px 12px;margin:5px 0;transition:all .15s;}
.fav-card:hover{border-color:#e05252;}
.fav-name{font-family:'Syne',sans-serif;font-size:.75rem;font-weight:700;color:#dde2ee;}
.fav-prev{font-size:.7rem;color:#3d4f68;margin-top:2px;
    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}

/* ── SECTION LABEL ── */
.sec-lbl{font-size:11px;font-weight:700;color:#e05252;text-transform:uppercase;
  letter-spacing:2px;margin:14px 0 8px;padding-bottom:6px;border-bottom:1px solid #131c2e;
  font-family:'Syne',sans-serif;}

/* ── MISC ── */
hr{border-color:#101828 !important;margin:11px 0 !important;}
::-webkit-scrollbar{width:4px;height:4px;}
::-webkit-scrollbar-track{background:#07090f;}
::-webkit-scrollbar-thumb{background:#1a2436;border-radius:2px;}
::-webkit-scrollbar-thumb:hover{background:#3a7bd5;}
.footer{text-align:center;font-size:11px;color:#101828;border-top:1px solid #0d1420;
  padding:14px 0 6px;margin-top:28px;letter-spacing:.5px;}
audio{width:100%!important;border-radius:9px!important;margin:4px 0!important;}
.stSuccess{background:#021409!important;border:1px solid #0a2f18!important;color:#4ade80!important;border-radius:9px!important;}
.stWarning{background:#100d00!important;border:1px solid #2a1f00!important;color:#fbbf24!important;border-radius:9px!important;}
.stError{background:#110404!important;border:1px solid #3a0a0a!important;color:#f87171!important;border-radius:9px!important;}
.stInfo{background:#0c1a2e!important;border:1px solid #172540!important;color:#60a5fa!important;border-radius:9px!important;}
</style>
""", unsafe_allow_html=True)

# ─── SABİTLER ─────────────────────────────────────────────────────────────────
MAX_PER_KEY = 10
MAX_ARCHIVE = 60

VOICES = {
    "Zephyr":("♀","Parlak · Neşeli"),         "Puck":("♂","Enerjik · Hareketli"),
    "Charon":("♂","Bilgilendirici · Açık"),    "Kore":("♀","Sıcak · Güven Veren"),
    "Fenrir":("♂","Heyecanlı · Dinamik"),      "Aoede":("♀","Akıcı · Doğal"),
    "Leda":("♀","Genç · Enerjik"),             "Orus":("♂","Kararlı · Güçlü"),
    "Achird":("♂","Dostane · Samimi"),         "Algenib":("♂","Pürüzlü · Özgün"),
    "Algieba":("♂","Yumuşak · Hoş"),           "Alnilam":("♂","Sağlam · Güçlü"),
    "Autonoe":("♀","Parlak · İyimser"),        "Callirrhoe":("♀","Rahat · Akıcı"),
    "Despina":("♀","Pürüzsüz · Zarif"),        "Enceladus":("♂","Yumuşak · Nefes"),
    "Erinome":("♀","Net · Hassas"),            "Gacrux":("♂","Olgun · Deneyimli"),
    "Iapetus":("♂","Net · Anlaşılır"),         "Laomedeia":("♀","Neşeli · Canlı"),
    "Pulcherrima":("♀","İfadeli · Çarpıcı"),   "Rasalgethi":("♂","Profesyonel"),
    "Sadachbia":("♂","Canlı · Hareketli"),     "Sadaltager":("♂","Bilgili · Otoriter"),
    "Schedar":("♂","Güçlü · Etkileyici"),      "Sulafat":("♀","Sıcak · Davetkar"),
    "Umbriel":("♂","Derin · Gizemli"),         "Vindemiatrix":("♀","Nazik · Kibar"),
    "Achernar":("♀","Yumuşak · Hassas"),       "Zubenelgenubi":("♂","Rahat · Dengeli"),
}

MODELS = {
    "gemini-2.5-flash-tts":              "🚀 2.5 Flash  (Stabil)",
    "gemini-2.5-pro-tts":                "💎 2.5 Pro    (En Kaliteli)",
    "gemini-2.5-flash-lite-preview-tts": "💡 2.5 Lite   (Ekonomik)",
}

LANGUAGES = {
    "otomatik":"🌐 Oto","tr-TR":"🇹🇷 Türkçe","en-US":"🇺🇸 EN-US",
    "en-GB":"🇬🇧 EN-UK","de-DE":"🇩🇪 Almanca","fr-FR":"🇫🇷 Fransızca",
    "es-ES":"🇪🇸 İspanyolca","it-IT":"🇮🇹 İtalyanca","pt-BR":"🇧🇷 PT-BR",
}

STYLE_PRESETS = {
    "— Seçin —":"",
    "📻 Haber Sunucu":   "Profesyonel haber sunucusu gibi net, otoriter ve güven verici bir tonla oku.",
    "🎉 Neşeli & Enerjik":"Çok neşeli ve coşkulu, müzik programı sunuyormuş gibi oku.",
    "🎭 Dramatik & Güçlü":"Dramatik ve etkileyici, büyük sahne duyurusu gibi oku.",
    "🌙 Sakin & Huzurlu": "Sakin, huzurlu ve rahatlatıcı, gece kuşağı tonu ile oku.",
    "🚨 Acil & Hızlı":    "Acil haber tonu, hızlı ve yüksek enerjili sesle oku.",
    "☕ Sıcak & Samimi":  "Sıcak ve dostça, yakın arkadaşa anlatır gibi oku.",
    "📣 Reklam Sesi":     "Profesyonel reklam seslendirmesi, çekici ve ikna edici oku.",
    "📖 Hikaye Anlatıcı": "Büyüleyici hikaye anlatıcısı gibi ritmik ve ifadeli oku.",
    "⚽ Spor Yorumcusu":  "Heyecanlı spor yorumcusu gibi yüksek tempo ile oku.",
    "🎬 Belgesel Sesi":   "Derin belgesel anlatıcısı, ağır ve anlamlı tonla oku.",
}

ETAGS = [
    ("🔥","Coşkulu",   "[excitedly] ","#ff6b35"),
    ("🤫","Fısıltı",   "[whispers] ", "#a78bfa"),
    ("😄","Gülümseyen","[laughs] ",   "#34d399"),
    ("📰","Ciddi",     "[seriously] ","#60a5fa"),
    ("📢","Bağırma",   "[shouting] ", "#f59e0b"),
    ("😮‍💨","Yorgun",  "[sighs] ",    "#94a3b8"),
    ("🎙️","Normal",   "[normal] ",   "#cbd5e1"),
]

TEMPLATES = {
    "🎙️ Sabah Açılış":
        "[excitedly] Günaydın! İmaj FM ile sabahın en güzel sesine uyanıyorsunuz!\n"
        "[seriously] Bugün haber bültenimizle başlıyoruz... [normal] hoş geldiniz!\n"
        "[excitedly] BU SABAH müzik, haber ve çok daha fazlası burada!",
    "🌙 Gece Kapanış":
        "[whispers] Ve gece yarısına yaklaşırken... İmaj FM sizinle.\n"
        "[sighs] Uzun bir günün ardından... kulaklarınıza iyi geceler.\n"
        "[whispers] Yarın yeniden buradayız. Tatlı rüyalar.",
    "📢 Özel Duyuru":
        "[excitedly] DUYURU DUYURU!\n"
        "[seriously] Değerli dinleyicilerimiz, önemli bir bildirimiz var.\n"
        "[excitedly] BU HAFTA sonu unutulmaz bir etkinlik sizi bekliyor!\n"
        "[shouting] KAÇIRMAYIN!",
    "🎵 Müzik Geçişi":
        "[normal] Ve müziğimiz devam ediyor...\n"
        "[whispers] Şimdi sizin için harika bir seçim var.\n"
        "[excitedly] İşte o şarkı!",
    "📰 Haber Girişi":
        "[seriously] İmaj FM Ana Haber Bülteni.\n"
        "[normal] Günün öne çıkan haberleriyle karşınızdayız.\n"
        "[seriously] Şimdi tüm ayrıntılarıyla...",
    "🎉 Yarışma":
        "[excitedly] BÜYÜK YARIŞMA BAŞLIYOR!\n"
        "[laughs] Hazır mısınız?\n"
        "[shouting] BU HAFTA kazanan sizin aranızdan çıkacak!\n"
        "[seriously] Hemen arayın... [excitedly] KAZANMA ŞANSI SIZIN!",
}

CHARS = {
    "🎙️ Dilay — Kadın Sunucu": {
        "id": "dilay", "voice": "Kore",
        "prompt": (
            "Sen İmaj FM'in efsanevi kadın sunucusu Dilay'sın. "
            "Türk kültürü ve müzikte derin bilgilisin. Dinleyiciye 'canım ailemiz' diye hitap edersin. "
            "28-45 saniye (~80-120 kelime). KESİNLİKLE sadece düz Türkçe metin. "
            "XML/HTML/SSML/Markdown/yıldız/parantez KULLANMA."
        ),
    },
    "📢 Kenan — Erkek Sunucu": {
        "id": "kenan", "voice": "Orus",
        "prompt": "Karizmatik güçlü sesli erkek sunucu. Enerjik, samimi. 30-40 sn. SADECE düz Türkçe.",
    },
    "📰 Haber Spikeri": {
        "id": "haber", "voice": "Iapetus",
        "prompt": "Profesyonel radyo haber spikeri. Net, tarafsız. SADECE düz Türkçe.",
    },
    "🎭 Reklam Sesi": {
        "id": "reklam", "voice": "Schedar",
        "prompt": "Akılda kalıcı 15-30 sn radyo reklamı. SADECE düz Türkçe.",
    },
    "🌙 Gece DJsi": {
        "id": "gece", "voice": "Umbriel",
        "prompt": "Gece yayını şiirsel DJ. Melankolik, büyüleyici. 40-50 sn. SADECE düz Türkçe.",
    },
    "🌅 Sabah Sunucusu": {
        "id": "sabah", "voice": "Puck",
        "prompt": "Enerjik neşeli sabah sunucusu. 25-35 sn. SADECE düz Türkçe.",
    },
}

GROQ_MODELS = {
    "Hızlı (llama3-8b)":       "llama3-8b-8192",
    "Standart (llama3-70b)":   "llama-3.3-70b-versatile",
    "Gelişmiş (mixtral-8x7b)": "mixtral-8x7b-32768",
}

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def sfn(s: str, n: int = 36) -> str:
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', str(s))[:n]

def ts_str() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def ts_short() -> str:
    return datetime.now().strftime("%d.%m %H:%M")

def fmt_dur(sec: float) -> str:
    m, s = divmod(int(sec), 60); h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

def word_count(t: str) -> int:
    return len(t.split()) if t and t.strip() else 0

def est_dur(text: str) -> float:
    return max(1, len(text) / 17)

def clean_text(text: str) -> str:
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
    text = re.sub(r'\[[^\]]*\](?:\([^)]*\))?', '', text)
    text = re.sub(r'[#]{1,6}\s*', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def list_audio(d: str) -> list:
    exts = (".mp3", ".wav", ".ogg", ".flac", ".m4a")
    if not os.path.isdir(d): return []
    return sorted(f for f in os.listdir(d) if f.lower().endswith(exts))

def audio_dur(path: str) -> float:
    if not PYDUB_OK or not os.path.exists(path): return 0.0
    try: return len(AudioSegment.from_file(path)) / 1000.0
    except Exception: return 0.0

def get_id3(path: str) -> dict:
    if not MUTAGEN_OK or not os.path.exists(path): return {}
    try:
        a = MutagenFile(path, easy=True)
        if a is None: return {}
        return {"title": str(a.get("title", [""])[0]), "artist": str(a.get("artist", [""])[0])}
    except Exception: return {}

def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close(); return ip
    except Exception: return "localhost"

def zip_files(paths: list, name: str = "download") -> Optional[bytes]:
    try:
        buf = BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for p in paths:
                if os.path.exists(p): zf.write(p, os.path.basename(p))
        buf.seek(0); return buf.read()
    except Exception: return None

def save_uploaded_file(uploaded_file, dest_dir: str, custom_name: str = "") -> Optional[str]:
    if uploaded_file is None: return None
    try:
        os.makedirs(dest_dir, exist_ok=True)
        fname = custom_name if custom_name else (uploaded_file.name if hasattr(uploaded_file, 'name') else f"upload_{ts_str()}.wav")
        fname = sfn(fname, 80)
        if '.' not in fname: fname += '.wav'
        dest = os.path.join(dest_dir, fname)
        if hasattr(uploaded_file, 'getvalue'): raw = uploaded_file.getvalue()
        elif hasattr(uploaded_file, 'read'): raw = uploaded_file.read()
        else: return None
        if not raw or len(raw) < 64: return None
        with open(dest, 'wb') as f: f.write(raw)
        return dest
    except Exception: return None

def save_meta(key: str, data: dict):
    p = os.path.join(META_DIR, f"{sfn(key)}.json"); ex = {}
    if os.path.exists(p):
        try:
            with open(p) as f: ex = json.load(f)
        except Exception: pass
    ex.update(data); ex["updated"] = datetime.now().isoformat()
    with open(p, "w", encoding="utf-8") as f: json.dump(ex, f, ensure_ascii=False, indent=2)

def load_meta(key: str) -> dict:
    p = os.path.join(META_DIR, f"{sfn(key)}.json")
    if os.path.exists(p):
        try:
            with open(p) as f: return json.load(f)
        except Exception: pass
    return {}

def save_memory(song: str, text: str, tone: str):
    h = hashlib.md5(song.encode()).hexdigest()[:10]
    p = os.path.join(MEMORY_DIR, f"{h}.json"); prev = {}
    if os.path.exists(p):
        try:
            with open(p) as f: prev = json.load(f)
        except Exception: pass
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"song": song, "text": text, "tone": tone,
                   "count": prev.get("count", 0) + 1,
                   "last": datetime.now().isoformat()}, f, ensure_ascii=False)

def check_memory(song: str) -> Optional[dict]:
    h = hashlib.md5(song.encode()).hexdigest()[:10]
    p = os.path.join(MEMORY_DIR, f"{h}.json")
    if os.path.exists(p):
        try:
            with open(p) as f: return json.load(f)
        except Exception: pass
    return None

def save_history(fname: str, text: str, char: str, song: str = ""):
    p = os.path.join(HISTORY_DIR, "history.json"); hist = []
    if os.path.exists(p):
        try:
            with open(p) as f: hist = json.load(f)
        except Exception: pass
    hist.insert(0, {"ts": datetime.now().isoformat(), "file": fname, "char": char,
                    "song": song, "preview": text[:80] + ("…" if len(text) > 80 else "")})
    hist = hist[:30]
    with open(p, "w") as f: json.dump(hist, f, ensure_ascii=False)

def load_history() -> list:
    p = os.path.join(HISTORY_DIR, "history.json")
    if os.path.exists(p):
        try:
            with open(p) as f: return json.load(f)
        except Exception: pass
    return []

def log_event(event: str, data: dict):
    p = os.path.join(ANALYTICS_DIR, f"log_{datetime.now().strftime('%Y%m%d')}.json"); logs = []
    if os.path.exists(p):
        try:
            with open(p) as f: logs = json.load(f)
        except Exception: pass
    logs.append({"ts": datetime.now().isoformat(), "event": event, **data})
    with open(p, "w") as f: json.dump(logs, f, ensure_ascii=False)

# ─── PYDUB AUDIO TOOLS ────────────────────────────────────────────────────────
def normalize_seg(seg: "AudioSegment", target: float = -16.0) -> "AudioSegment":
    if not PYDUB_OK: return seg
    return seg.apply_gain(target - seg.dBFS)

def apply_eq(seg: "AudioSegment", preset: str) -> "AudioSegment":
    if not PYDUB_OK: return seg
    tbl = {
        "Broadcast Clear": lambda s: pydub_fx.normalize(pydub_fx.compress_dynamic_range(s, threshold=-18, ratio=3.0)),
        "Radio Warm":       lambda s: pydub_fx.normalize(s) + 1,
        "Vintage":          lambda s: pydub_fx.normalize(s.low_pass_filter(4500)) - 2,
        "Deep Bass":        lambda s: pydub_fx.normalize(s.high_pass_filter(60)) + 1,
        "Crisp HiFi":       lambda s: pydub_fx.normalize(s.high_pass_filter(120)),
        "AM Radio":         lambda s: (s.low_pass_filter(3000).high_pass_filter(400)) + 3,
        "Podcast Studio":   lambda s: pydub_fx.compress_dynamic_range(pydub_fx.normalize(s), threshold=-20, ratio=2.5),
    }
    fn = tbl.get(preset); return fn(seg) if fn else seg

def apply_reverb(seg: "AudioSegment", lvl: float) -> "AudioSegment":
    if not PYDUB_OK or lvl <= 0: return seg
    try:
        delay = int(85 * lvl); wet = seg - int(13 * lvl)
        return pydub_fx.normalize(seg.overlay(wet, position=delay))
    except Exception: return seg

def apply_ducking(music: "AudioSegment", voice: "AudioSegment",
                  duck_db: int = -14, fade_ms: int = 500) -> "AudioSegment":
    if not PYDUB_OK: return music
    try:
        vl = len(voice); fm = min(fade_ms, max(50, vl // 4))
        part = music[:vl]; rest = music[vl:]
        ducked = (
            part[:fm].fade(to_gain=duck_db, start=0, duration=fm) +
            (part[fm:vl - fm] + duck_db) +
            part[vl - fm:].fade(from_gain=duck_db, start=0, duration=fm)
        )
        return ducked.overlay(voice) + rest
    except Exception: return music.overlay(voice)

def mix_fon_voice(fon: "AudioSegment", voice: "AudioSegment",
                  fon_vol: int = -8, duck_db: int = -16,
                  fade_in: int = 800, fade_out: int = 1200) -> "AudioSegment":
    if not PYDUB_OK: return voice
    try:
        fon = fon + fon_vol; vl = len(voice); fl = len(fon)
        if fl < vl + 2000:
            loops = (vl + 2000) // fl + 1; fon = fon * loops
        fon = fon[:vl + 2000].fade_in(fade_in)
        fp = fon[:vl]; fr = fon[vl:]; fm = min(500, vl // 4)
        ducked = (
            fp[:fm].fade(to_gain=duck_db, start=0, duration=fm) +
            (fp[fm:vl - fm] + duck_db) +
            fp[vl - fm:].fade(from_gain=duck_db, start=0, duration=fm)
        )
        return normalize_seg(ducked.overlay(voice) + fr.fade_out(fade_out))
    except Exception: return voice

def mix_with_effect(main: "AudioSegment", eff: "AudioSegment",
                    pos: str = "after", gap: int = 0) -> "AudioSegment":
    if not PYDUB_OK: return main
    silence = AudioSegment.silent(duration=gap)
    if pos == "before": return eff + silence + main
    elif pos == "after": return main + silence + eff
    elif pos == "overlay": return main.overlay(eff)
    return main

def do_export(src: str, fmt: str, out_dir: str = OUT_DIR) -> str:
    if not PYDUB_OK or fmt == "wav" or not os.path.exists(src): return src
    try:
        seg = AudioSegment.from_file(src)
        base = os.path.splitext(os.path.basename(src))[0]
        out = os.path.join(out_dir, f"{base}.{fmt}")
        kw = {"bitrate": "320k"} if fmt == "mp3" else {}
        seg.export(out, format=fmt, **kw); return out
    except Exception as e:
        st.error(f"Export: {e}"); return src

def audio_concat(segs: list) -> "AudioSegment":
    if not segs: return AudioSegment.silent(0)
    r = segs[0]
    for s in segs[1:]: r += s
    return r

def generate_jingle(freq: int = 440, dur_ms: int = 2000, style: str = "sine") -> Optional["AudioSegment"]:
    if not PYDUB_OK or not NP_OK: return None
    try:
        from pydub.generators import Sine, Square, Sawtooth
        gmap = {"sine": Sine, "square": Square, "sawtooth": Sawtooth}
        g = gmap.get(style, Sine)
        seg = (g(freq).to_audio_segment(duration=dur_ms // 3) +
               g(int(freq * 1.25)).to_audio_segment(duration=dur_ms // 3) +
               g(int(freq * 1.5)).to_audio_segment(duration=dur_ms // 3))
        return seg.fade_in(80).fade_out(180) - 10
    except Exception: return None

def quality_score(path: str) -> int:
    if not PYDUB_OK or not os.path.exists(path): return 50
    try:
        seg = AudioSegment.from_file(path)
        dbfs = abs(seg.dBFS); dur = len(seg)/1000
        sc = 100
        if dbfs > 30: sc -= 20
        elif dbfs < 8: sc -= 10
        if dur < 1: sc -= 15
        if seg.channels == 1: sc -= 5
        return max(0, min(100, sc))
    except Exception: return 50

def draw_waveform(path: str, h: float = 1.5):
    if not NP_OK or not os.path.exists(path): return
    try:
        with wave.open(path, 'rb') as wf:
            sr = wf.getframerate(); ch = wf.getnchannels(); sw = wf.getsampwidth()
            frames = wf.readframes(wf.getnframes())
        dt = np.int16 if sw == 2 else np.int8
        s = np.frombuffer(frames, dtype=dt)
        if ch == 2: s = s[::2]
        step = max(1, len(s) // 2000); ds = s[::step].astype(np.float32)
        mx = np.max(np.abs(ds)) or 1; ds /= mx
        t = np.linspace(0, len(s) / sr, len(ds))
        fig, ax = plt.subplots(figsize=(10, h), facecolor='#07090f')
        ax.set_facecolor('#07090f')
        ax.fill_between(t, ds, alpha=.65, color='#e05252')
        ax.fill_between(t, -np.abs(ds), alpha=.2, color='#3a7bd5')
        ax.axhline(0, color='#131c2e', lw=.8)
        ax.set_xlim(0, t[-1]); ax.set_ylim(-1.1, 1.1)
        for sp in ax.spines.values(): sp.set_visible(False)
        ax.tick_params(colors='#2e3f55', labelsize=7)
        ax.set_xlabel("sn", color='#2e3f55', fontsize=7)
        plt.tight_layout(pad=.3)
        st.pyplot(fig, use_container_width=True); plt.close(fig)
    except Exception: pass

# ─── GEMINI TTS ───────────────────────────────────────────────────────────────
def pcm2wav(pcm: bytes, rate=24000, ch=1, sw=2) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(ch); wf.setsampwidth(sw); wf.setframerate(rate)
        wf.writeframes(pcm)
    return buf.getvalue()

def tts_single(api_key: str, model: str, text: str, voice: str, lang: str, style: str) -> bytes:
    full = f"{style}\n\n{text}" if style.strip() else text
    lc = lang if lang != "otomatik" else None
    c = genai.Client(api_key=api_key)
    r = c.models.generate_content(
        model=model, contents=full,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                language_code=lc,
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                )
            )
        )
    )
    return r.candidates[0].content.parts[0].inline_data.data

def tts_multi(api_key: str, model: str, text: str, sp1: str, v1: str, sp2: str, v2: str, lang: str) -> bytes:
    lc = lang if lang != "otomatik" else None
    c = genai.Client(api_key=api_key)
    r = c.models.generate_content(
        model=model, contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                language_code=lc,
                multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                    speaker_voice_configs=[
                        types.SpeakerVoiceConfig(speaker=sp1,
                            voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=v1))),
                        types.SpeakerVoiceConfig(speaker=sp2,
                            voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=v2))),
                    ]
                )
            )
        )
    )
    return r.candidates[0].content.parts[0].inline_data.data

def gemini_tts_to_file(api_key: str, model: str, text: str, voice: str, lang: str, style: str,
                       eq_preset: str = "Broadcast Clear", reverb: float = 0.0, norm_db: float = -16.0,
                       out_path: str = "") -> tuple:
    """Gemini TTS → WAV bytes + disk. Returns (wav_bytes, file_path)"""
    try:
        raw = tts_single(api_key, model, text, voice, lang, style)
        wav = pcm2wav(raw)
        # PyDub mastering
        if PYDUB_OK:
            seg = AudioSegment(raw, frame_rate=24000, sample_width=2, channels=1)
            if eq_preset and eq_preset != "Ham (Efektsiz)": seg = apply_eq(seg, eq_preset)
            if reverb > 0: seg = apply_reverb(seg, reverb)
            seg = normalize_seg(seg, norm_db)
            buf = BytesIO(); seg.export(buf, format="wav"); wav = buf.getvalue()
        if out_path:
            os.makedirs(os.path.dirname(out_path) if os.path.dirname(out_path) else OUT_DIR, exist_ok=True)
            with open(out_path, "wb") as f: f.write(wav)
        return wav, out_path
    except Exception as e:
        raise RuntimeError(f"Gemini TTS: {e}")

# ─── GROQ ─────────────────────────────────────────────────────────────────────
@st.cache_resource
def init_groq():
    key = os.getenv("GROQ_API_KEY")
    if not key or not GROQ_OK: return None
    try: return Groq(api_key=key)
    except Exception: return None

groq_client = init_groq()

def groq_gen(msg: str, char_id: str = "dilay", model_key: str = "Standart (llama3-70b)",
             temp: float = 0.87, max_tok: int = 450) -> str:
    if not groq_client: return "⚠️ Groq bağlantısı yok. GROQ_API_KEY ayarlayın."
    char = next((c for c in CHARS.values() if c["id"] == char_id), list(CHARS.values())[0])
    model = GROQ_MODELS.get(model_key, "llama-3.3-70b-versatile")
    try:
        res = groq_client.chat.completions.create(
            messages=[{"role": "system", "content": char["prompt"]},
                      {"role": "user",   "content": msg}],
            model=model, temperature=temp, max_tokens=max_tok,
        )
        return clean_text(res.choices[0].message.content.strip())
    except Exception as e: return f"⚠️ Groq: {e}"

def groq_stt(audio_bytes: bytes, lang: str = "tr") -> str:
    if not groq_client: return "⚠️ Groq bağlantısı yok."
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
            tf.write(audio_bytes); p = tf.name
        with open(p, "rb") as f:
            res = groq_client.audio.transcriptions.create(
                file=("audio.wav", f), model="whisper-large-v3", language=lang)
        os.remove(p); return res.text.strip()
    except Exception as e: return f"⚠️ STT: {e}"

def groq_mood(song: str) -> dict:
    pr = (f'Şarkı: "{song}"\nSadece JSON döndür:\n'
          '{"mood":"mutlu|melankolik|enerjik|romantik|nostaljik|hüzünlü",'
          '"tone_suggestion":"Duygusal|Neşeli & İşveli|Espirili|Derin & Şiirsel|Nostaljik|Enerjik",'
          '"yorum":"tek cümle"}')
    r = groq_gen(pr, char_id="dilay", temp=0.2, max_tok=120)
    try:
        c = re.sub(r'```[^`]*```', '', r).strip()
        return json.loads(c)
    except Exception:
        return {"mood": "?", "tone_suggestion": "Duygusal", "yorum": ""}

# ─── SESSION STATE ─────────────────────────────────────────────────────────────
def _safe_init(key, val):
    if key not in st.session_state:
        st.session_state[key] = val

_safe_init("_archive", [])
_safe_init("_favorites", [])
_safe_init("_api_pool", [{"key": "", "used": 0, "label": f"API {i+1}"} for i in range(10)])
_safe_init("_active_idx", 0)
_safe_init("_secrets_loaded", False)
_safe_init("_api_stats", {"total_calls": 0, "total_chars": 0, "total_secs": 0.0})
_safe_init("_giris", False)
_safe_init("_t_tek", "[excitedly] İmaj FM'e hoş geldiniz! BU GECE unutulmaz bir program var...\n[whispers] Sürprizler için kulaklarınız bizde olsun.\n[seriously] Şimdi haberlere geçiyoruz.")
_safe_init("_t_bulk", "İmaj FM sabah yayını başlıyor.\nHaber bülteni için bekleyiniz.\nMüzik programımıza hoş geldiniz.")
_safe_init("qa_txt", "")

def load_secrets_once():
    if st.session_state._secrets_loaded: return
    st.session_state._secrets_loaded = True
    for i in range(10):
        try:
            v = st.secrets.get(f"GEMINI_API_KEY_{i+1}", "")
            if v and not st.session_state._api_pool[i]["key"]:
                st.session_state._api_pool[i]["key"] = v
        except Exception: pass

load_secrets_once()

def get_active_key():
    pool = st.session_state._api_pool; idx = st.session_state._active_idx
    for _ in range(10):
        s = pool[idx]
        if s["key"].strip() and s["used"] < MAX_PER_KEY:
            st.session_state._active_idx = idx
            return s["key"].strip(), idx
        idx = (idx + 1) % 10
    return None, -1

def consume(idx, chars=0):
    st.session_state._api_pool[idx]["used"] += 1
    st.session_state._api_stats["total_calls"] += 1
    st.session_state._api_stats["total_chars"] += chars
    if st.session_state._api_pool[idx]["used"] >= MAX_PER_KEY:
        st.session_state._active_idx = (idx + 1) % 10

def pool_stats():
    p = st.session_state._api_pool
    loaded = sum(1 for s in p if s["key"].strip())
    used_t = sum(s["used"] for s in p if s["key"].strip())
    remain = sum(max(0, MAX_PER_KEY - s["used"]) for s in p if s["key"].strip())
    return loaded, used_t, remain

def archive_add(voice, model, lang, style, text, wav_bytes, mode="tek"):
    dur = len(wav_bytes) / (24000 * 2)
    uid = hashlib.md5((text + voice + str(time.time())).encode()).hexdigest()[:10]
    entry = {
        "id": uid, "ts": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "ts_short": ts_short(), "voice": voice, "model": model,
        "model_short": model.replace("gemini-", "").replace("-preview", "").replace("-tts", ""),
        "lang": lang, "style": style[:40] if style else "",
        "text": text, "preview": text[:70].replace("\n", " ") + ("…" if len(text) > 70 else ""),
        "wav": wav_bytes, "dur": round(dur, 1), "size": len(wav_bytes), "mode": mode,
    }
    st.session_state._archive.insert(0, entry)
    if len(st.session_state._archive) > MAX_ARCHIVE:
        st.session_state._archive = st.session_state._archive[:MAX_ARCHIVE]
    st.session_state._api_stats["total_secs"] += dur

# ─── UI HELPERS ───────────────────────────────────────────────────────────────
def chip_html(label: str, color: str = "blue") -> str:
    return f'<span class="chip chip-{color}">{label}</span>'

def section(label: str):
    st.markdown(f'<div class="sec-lbl">{label}</div>', unsafe_allow_html=True)

def page_header(icon: str, title: str, sub: str = ""):
    st.markdown(
        f'<div class="page-hdr"><div class="ico">{icon}</div>'
        f'<div><h1>{title}</h1><p>{sub}</p></div></div>',
        unsafe_allow_html=True
    )

def qbar(score: int):
    bc = "#22c55e" if score >= 70 else ("#f59e0b" if score >= 40 else "#ef4444")
    st.markdown(
        f'<div class="qbar"><div class="qbar-f" style="width:{score}%;background:{bc};"></div></div>',
        unsafe_allow_html=True
    )

def text_stats_bar(text: str):
    cc = len(text); wc = len(text.split())
    sc = max(1, text.count(".") + text.count("!") + text.count("?"))
    est = max(1, cc / 17)
    st.markdown(
        f"<div style='font-size:.68rem;color:#2e3f55;margin:3px 0 8px;'>"
        f"📊 {cc} karakter · {wc} kelime · {sc} cümle · ~{est:.0f}s tahmini süre</div>",
        unsafe_allow_html=True)

def tag_buttons(state_key: str, prefix: str):
    cols = st.columns(len(ETAGS))
    for i, (em, lbl, tag, col) in enumerate(ETAGS):
        with cols[i]:
            if st.button(em, key=f"{prefix}_et_{i}", help=f"{lbl}: {tag.strip()}",
                         use_container_width=True):
                st.session_state[state_key] = st.session_state.get(state_key, "") + tag
                st.rerun()

# ─── YARDIMCI: Gemini TTS ile seslendir ve arşivle ───────────────────────────
def do_tts_and_save(text: str, voice: str, model: str, lang: str, style: str,
                    eq_preset: str, reverb: float, norm_db: float,
                    mode: str = "tek", save_to_file: bool = False,
                    file_prefix: str = "imajfm") -> Optional[bytes]:
    ak, ai = get_active_key()
    if ak is None:
        st.error("❌ Aktif API anahtarı yok! Sidebar'dan ekleyin.")
        return None
    try:
        wav, _ = gemini_tts_to_file(
            ak, model, text, voice, lang, style, eq_preset, reverb, norm_db,
            out_path=os.path.join(OUT_DIR, f"{sfn(file_prefix)}_{ts_str()}.wav") if save_to_file else ""
        )
        consume(ai, len(text))
        archive_add(voice, model, lang, style, text, wav, mode)
        if save_to_file:
            save_history(f"{sfn(file_prefix)}_{ts_str()}.wav", text, voice)
        log_event("tts_generated", {"voice": voice, "model": model, "chars": len(text), "mode": mode})
        return wav
    except Exception as e:
        st.error(f"❌ {e}"); return None

def vbtn_gemini(text: str, key: str, voice: str, model: str, lang: str, style: str,
                eq_preset: str, reverb: float, norm_db: float, label: str = "🔴 Seslendir",
                mode: str = "tek", save_to_file: bool = True, song: str = "") -> Optional[bytes]:
    if st.button(label, key=f"vb_{key}", type="primary", use_container_width=True):
        if not text or not text.strip():
            st.warning("Metin boş!"); return None
        with st.spinner("🎙️ Gemini TTS üretiyor..."):
            wav = do_tts_and_save(text, voice, model, lang, style, eq_preset, reverb, norm_db,
                                  mode=mode, save_to_file=save_to_file, file_prefix=key)
        if wav:
            dur = len(wav) / (24000 * 2)
            st.markdown(
                chip_html(f"✅ {voice}", "green") + " " +
                chip_html(f"⏱ {dur:.1f}s", "blue") + " " +
                chip_html(f"🎯 {quality_score_bytes(wav)}/100", "purple"),
                unsafe_allow_html=True
            )
            st.audio(wav, format="audio/wav")
            st.download_button("💾 WAV", wav, file_name=f"imajfm_{key}_{ts_str()}.wav",
                               mime="audio/wav", key=f"dl_{key}_{ts_str()}")
            if save_to_file:
                save_history(f"{key}.wav", text, voice, song)
        return wav
    return None

def quality_score_bytes(wav: bytes) -> int:
    if not PYDUB_OK: return 75
    try:
        seg = AudioSegment(wav[44:], frame_rate=24000, sample_width=2, channels=1)
        dbfs = abs(seg.dBFS); sc = 100
        if dbfs > 30: sc -= 20
        elif dbfs < 8: sc -= 10
        return max(0, min(100, sc))
    except Exception: return 75

# ─── GİRİŞ ────────────────────────────────────────────────────────────────────
def login():
    _, col, _ = st.columns([1, 1.05, 1])
    with col:
        st.markdown("""
        <div style='margin-top:65px;padding:34px 30px;background:#0b0f1a;
                    border:1px solid #1a2d4a;border-radius:18px;
                    box-shadow:0 24px 64px rgba(0,0,0,.8);'>
            <h2 style='text-align:center;font-family:Syne,sans-serif;font-weight:800;
                       font-size:1.5rem;margin:0 0 3px;
                       background:linear-gradient(90deg,#fff 20%,#ff6060);
                       -webkit-background-clip:text;-webkit-text-fill-color:transparent;'>
                🎙️ İmaj FM
            </h2>
            <p style='text-align:center;color:#2e3f55;font-size:.7rem;
                      letter-spacing:.15em;margin:0 0 24px;'>
                HYBRİD REJİ v1 · GEMİNİ TTS · GÜVENLİ GİRİŞ
            </p>
        </div>""", unsafe_allow_html=True)
        u = st.text_input("u", "", placeholder="👤  kullanıcı adı", label_visibility="collapsed")
        p = st.text_input("p", "", type="password", placeholder="🔑  şifre", label_visibility="collapsed")
        if st.button("Stüdyoya Bağlan →", type="primary", use_container_width=True):
            if u == "kenan" and p == "imajfm":
                st.session_state._giris = True; st.rerun()
            else: st.error("❌ Hatalı giriş.")

if not st.session_state._giris:
    login(); st.stop()

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:5px 0 11px;'>
        <span style='font-family:Syne,sans-serif;font-size:.95rem;font-weight:800;
            background:linear-gradient(90deg,#fff,#ff6060);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;'>
            🎙️ İmaj FM
        </span>
        <span style='font-size:.62rem;color:#2e3f55;letter-spacing:.1em;'>  HYBRİD REJİ v1</span>
    </div>
    """, unsafe_allow_html=True)

    # ── API HAVUZU ────────────────────────────────────────────────
    ak_sb, ai_sb = get_active_key()
    tk_sb, tu_sb, tr_sb = pool_stats()

    if ak_sb:
        used_act = st.session_state._api_pool[ai_sb]["used"]
        rem_act  = MAX_PER_KEY - used_act
        pct_act  = used_act / MAX_PER_KEY
        bc_act   = "#22c55e" if pct_act < .6 else ("#f59e0b" if pct_act < .9 else "#ef4444")
    else:
        rem_act = 0; pct_act = 1; bc_act = "#ef4444"

    with st.expander(f"🗝️  API Havuzu  ·  {tk_sb}/10  ·  {tr_sb} kalan", expanded=True):
        if ak_sb:
            st.markdown(f"""
            <div style='background:#07090f;border-radius:8px;padding:8px 10px;margin-bottom:7px;font-size:.73rem;'>
                <div style='display:flex;justify-content:space-between;margin-bottom:4px;'>
                    <span style='color:#6b7a8d;'>Aktif: <b style='color:#22c55e;'>
                        {st.session_state._api_pool[ai_sb].get("label",f"API {ai_sb+1}")}</b></span>
                    <span style='color:#6b7a8d;'>Kalan: <b style='color:{"#22c55e" if rem_act>3 else "#f59e0b"};'>{rem_act}/{MAX_PER_KEY}</b></span>
                    <span style='color:#6b7a8d;'>Toplam: <b style='color:#3b82f6;'>{tr_sb}</b></span>
                </div>
                <div class='qbar'><div class='qbar-f' style='width:{pct_act*100:.0f}%;background:{bc_act};'></div></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("<div class='card r'>⛔ API yok! Aşağıdan ekleyin.</div>", unsafe_allow_html=True)

        with st.expander("📋 Secrets.toml Formatı", expanded=False):
            st.code("GEMINI_API_KEY_1 = \"AIza...\"\nGEMINI_API_KEY_2 = \"AIza...\"\n...", language="toml")

        st.markdown("<span class='sl2'>▸ 10 API SLOTU</span>", unsafe_allow_html=True)
        for i in range(10):
            slot = st.session_state._api_pool[i]
            used = slot["used"]; has = bool(slot["key"].strip())
            full = has and used >= MAX_PER_KEY
            warn = has and used >= int(MAX_PER_KEY * .6) and not full
            is_ac = (i == st.session_state._active_idx) and has and not full
            lbl = slot.get("label", f"API {i+1}")
            if not has: icon = "⬜"; badge = "boş"
            elif full:  icon = "🔴"; badge = "DOLU"
            elif warn:  icon = "🟡"; badge = f"{used}/{MAX_PER_KEY}"
            else:       icon = "🟢"; badge = f"{used}/{MAX_PER_KEY}"
            act_m = " ◀" if is_ac else ""
            with st.expander(f"{icon} {lbl}{act_m}  ·  {badge}", expanded=False):
                nl = st.text_input(f"İsim{i}", value=lbl, placeholder=f"API {i+1}",
                                   label_visibility="collapsed", key=f"lbl_{i}")
                if nl != lbl: st.session_state._api_pool[i]["label"] = nl; st.rerun()
                nk = st.text_input(f"Key{i}", value=slot["key"], type="password",
                                   placeholder="AIzaSy...", label_visibility="collapsed", key=f"key_{i}")
                if nk != slot["key"]: st.session_state._api_pool[i]["key"] = nk; st.rerun()
                if has:
                    p2 = min(used / MAX_PER_KEY, 1)
                    b2 = "#22c55e" if p2 < .6 else ("#f59e0b" if p2 < .9 else "#ef4444")
                    st.markdown(f"<div class='qbar'><div class='qbar-f' style='width:{p2*100:.0f}%;background:{b2};'></div></div><div style='font-size:.62rem;color:#2e3f55;'>{used}/{MAX_PER_KEY} · {MAX_PER_KEY-used} kalan</div>", unsafe_allow_html=True)
                k1, k2, k3 = st.columns(3)
                with k1:
                    if st.button("🔄", key=f"rst_{i}", help="Sıfırla", use_container_width=True):
                        st.session_state._api_pool[i]["used"] = 0; st.rerun()
                with k2:
                    if st.button("▶", key=f"act_{i}", help="Aktif yap", use_container_width=True):
                        st.session_state._active_idx = i; st.rerun()
                with k3:
                    if st.button("🗑️", key=f"del_{i}", help="Sil", use_container_width=True):
                        st.session_state._api_pool[i] = {"key": "", "used": 0, "label": f"API {i+1}"}; st.rerun()

    # ── Karakter + TTS Ayarları ─────────────────────────────────
    st.markdown("<span class='sl'>▸ KARAKTER</span>", unsafe_allow_html=True)
    char_name = st.selectbox("Karakter:", list(CHARS.keys()), label_visibility="collapsed", key="sb_char")
    AC = CHARS[char_name]
    st.markdown(chip_html(AC["id"].upper(), "blue") + " " + chip_html(AC["voice"], "gray"), unsafe_allow_html=True)

    st.markdown("<span class='sl'>▸ GEMİNİ TTS</span>", unsafe_allow_html=True)
    sel_model = st.selectbox("Model:", list(MODELS.keys()), format_func=lambda x: MODELS[x],
                              label_visibility="collapsed", key="sb_model")
    sel_voice = st.selectbox("Ses:", list(VOICES.keys()),
                              format_func=lambda x: f"{VOICES[x][0]} {x} — {VOICES[x][1]}",
                              label_visibility="collapsed", key="sb_voice", index=list(VOICES.keys()).index(AC["voice"]))
    sel_lang  = st.selectbox("Dil:", list(LANGUAGES.keys()), format_func=lambda x: LANGUAGES[x],
                              label_visibility="collapsed", key="sb_lang", index=1)

    st.markdown("<span class='sl'>▸ MASTERİNG</span>", unsafe_allow_html=True)
    eq_sb     = st.selectbox("EQ:", ["Broadcast Clear", "Radio Warm", "Vintage", "Deep Bass",
                                      "Crisp HiFi", "AM Radio", "Podcast Studio", "Ham (Efektsiz)"],
                              label_visibility="collapsed", key="sb_eq")
    reverb_sb = st.slider("Reverb", 0.0, 1.0, 0.0, step=0.05, key="sb_rev")
    norm_sb   = st.slider("Normalize (dBFS)", -24, -8, -16, key="sb_norm")

    st.markdown("<span class='sl'>▸ GROQ</span>", unsafe_allow_html=True)
    groq_mkey = st.selectbox("Groq Model:", list(GROQ_MODELS.keys()), label_visibility="collapsed", index=1, key="sb_groq")
    exp_fmt   = st.selectbox("Export:", ["wav", "mp3", "ogg", "flac"], label_visibility="collapsed", key="sb_fmt")
    stt_lang  = st.selectbox("STT Dili:", ["tr", "en", "de", "fr", "ar"], label_visibility="collapsed", key="sb_stt")

    # ── Arşiv Mini ────────────────────────────────────────────────
    arc_count  = len(st.session_state._archive)
    total_secs = st.session_state._api_stats["total_secs"]
    with st.expander(f"📂  Arşiv  ·  {arc_count} kayıt  ·  {total_secs:.0f}s", expanded=False):
        if not st.session_state._archive:
            st.caption("Henüz kayıt yok.")
        else:
            for h in st.session_state._archive[:5]:
                st.markdown(f"<div style='font-size:.7rem;color:#3d4f68;padding:3px 0;border-bottom:1px solid #0d1420;'>{h['ts_short']} · <b style='color:#60a5fa;'>{h['voice']}</b> · {h['dur']}s</div>", unsafe_allow_html=True)
            if arc_count > 5:
                st.caption(f"+{arc_count-5} daha")

    with st.expander("🎭  Duygu Etiketleri", expanded=False):
        st.markdown("""
        <div style='font-size:.7rem;color:#6b7a8d;line-height:2;'>
        <span style='color:#60a5fa;font-family:monospace;'>[excitedly]</span> Coşkulu<br>
        <span style='color:#60a5fa;font-family:monospace;'>[whispers]</span> Fısıltı<br>
        <span style='color:#60a5fa;font-family:monospace;'>[seriously]</span> Ciddi · Haber<br>
        <span style='color:#60a5fa;font-family:monospace;'>[laughs]</span> Gülümseyen<br>
        <span style='color:#60a5fa;font-family:monospace;'>[shouting]</span> Bağırma<br>
        <span style='color:#60a5fa;font-family:monospace;'>[sighs]</span> Yorgun<br>
        <span style='color:#60a5fa;font-family:monospace;'>[normal]</span> Standart
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;color:#101828;font-size:.62rem;'>İmaj FM Hybrid Reji v1 · 2026</div>", unsafe_allow_html=True)

# Aktif karakter sesi
A_VOICE = sel_voice
A_CHAR  = AC["id"]

# ─── ANA SAYFA HEADER ─────────────────────────────────────────────────────────
st.markdown("""
<div class='hdr'>
    <h1>🎙️ İmaj FM · Hybrid Reji Stüdyosu</h1>
    <p><span class='ldot'></span>Gemini TTS &nbsp;·&nbsp; Yayın Otomasyonu &nbsp;·&nbsp; Fon+Anons Mikseri &nbsp;·&nbsp; Karakter Stüdyosu &nbsp;·&nbsp; A/B Test &nbsp;·&nbsp; Toplu TTS &nbsp;·&nbsp; Zincir Yayın</p>
</div>
""", unsafe_allow_html=True)

# Metrik satırı
tk_m, tu_m, tr_m = pool_stats()
arc_m  = len(st.session_state._archive)
stat_m = st.session_state._api_stats
mc1, mc2, mc3, mc4, mc5 = st.columns(5)
with mc1: st.markdown(f'<div class="mbox b"><div class="v">{tk_m}/10</div><div class="l">API Anahtarı</div></div>', unsafe_allow_html=True)
with mc2: st.markdown(f'<div class="mbox g"><div class="v">{tr_m}</div><div class="l">Kalan Kota</div></div>', unsafe_allow_html=True)
with mc3: st.markdown(f'<div class="mbox a"><div class="v">{stat_m["total_calls"]}</div><div class="l">API Çağrısı</div></div>', unsafe_allow_html=True)
with mc4: st.markdown(f'<div class="mbox p"><div class="v">{arc_m}</div><div class="l">Arşiv Kayıt</div></div>', unsafe_allow_html=True)
with mc5: st.markdown(f'<div class="mbox"><div class="v">{stat_m["total_secs"]:.0f}s</div><div class="l">Üretilen Ses</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── MENÜ ─────────────────────────────────────────────────────────────────────
MENU = [
    "📡 Gösterge Paneli",
    "🚀 Yayın Otomasyonu",
    "🎛️ Fon+Anons Mikseri",
    "🎭 Karakter Stüdyosu",
    "🎤 Tek Konuşmacı",
    "👥 Çift Konuşmacı",
    "📰 Haber Bülteni",
    "📩 İstek & Mesajlar",
    "✍️ Manuel Stüdyo",
    "📦 Toplu TTS",
    "🎬 Intro/Outro",
    "✂️ Ses Editörü",
    "🔄 A/B Test",
    "📡 Stream Yayın",
    "📅 Program Planlayıcı",
    "📊 Analitikler",
    "📁 Kütüphane",
    "📻 Arşiv & İstatistik",
    "⚙️ Ayarlar",
]

menu = st.radio("Menü:", MENU, label_visibility="collapsed", horizontal=False,
                key="main_menu", index=0)
st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# M0 — GÖSTERGE PANELİ
# ══════════════════════════════════════════════════════════════════════════════
if menu == "📡 Gösterge Paneli":
    page_header("📡", "Gösterge Paneli", "Yayın sistemi durumu ve hızlı araçlar")

    songs   = list_audio(PLAYLIST_DIR)
    outputs = list_audio(OUT_DIR)
    fons    = list_audio(FON_DIR)
    effects = list_audio(EFFECT_DIR)
    reqs    = [f for f in os.listdir(REQUEST_DIR) if f.endswith(".json")]
    jingles = list_audio(JINGLE_DIR)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    for col, (n, l) in zip([c1, c2, c3, c4, c5, c6],
        [(len(songs), "Şarkı"), (len(outputs), "Üretilen"), (len(fons), "Fon"),
         (len(effects), "Efekt"), (len(reqs), "İstek"), (len(jingles), "Jingle")]):
        with col:
            st.markdown(f'<div class="sbox"><div class="snum">{n}</div><div class="slbl">{l}</div></div>', unsafe_allow_html=True)

    st.divider()
    cl, cr = st.columns([1.7, 1])

    with cl:
        section("📂 Playlist")
        if songs:
            total = sum(audio_dur(os.path.join(PLAYLIST_DIR, s)) for s in songs)
            for s in songs[:10]:
                d = audio_dur(os.path.join(PLAYLIST_DIR, s))
                tags = get_id3(os.path.join(PLAYLIST_DIR, s))
                art = (f' {chip_html(tags["artist"][:16],"purple")}' if tags.get("artist") else "")
                st.markdown(
                    f'<div class="song-row"><span class="song-nm">🎵 {s[:40]}</span>'
                    f'{art}<span class="song-dur">{fmt_dur(d)}</span></div>',
                    unsafe_allow_html=True)
            st.markdown(f'<div class="mono-box">📊 {len(songs)} parça · {fmt_dur(total)} müzik<br>📡 Tahmini yayın: ~{fmt_dur(total + len(songs)*40)}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-box">ℹ️ Playlist boş — 📁 Kütüphane\'den şarkı ekle.</div>', unsafe_allow_html=True)

        section("🎶 Fon & Efektler")
        fc1, fc2 = st.columns(2)
        with fc1:
            if fons:
                for f in fons[:4]:
                    d = audio_dur(os.path.join(FON_DIR, f))
                    st.markdown(f'<div class="kcard kcard-l" style="padding:8px 12px"><div class="kcard-title">🎶 {f[:26]}</div><div class="kcard-body">{fmt_dur(d)}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="warn-box">⚠️ /fon klasörü boş.</div>', unsafe_allow_html=True)
        with fc2:
            if effects:
                for f in effects[:4]:
                    st.markdown(f'<div class="kcard" style="padding:8px 12px"><div class="kcard-title">🎭 {f[:26]}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="warn-box">⚠️ /effects klasörü boş.</div>', unsafe_allow_html=True)

    with cr:
        section("⚡ Hızlı Anons")
        qa = st.text_input("Şarkı adı:", key="qa_in", placeholder="ör. Nilüfer — Deli")
        if st.button("✨ AI Anons Üret", key="qa_gen"):
            if qa.strip():
                with st.spinner("Üretiyor..."):
                    md  = groq_mood(qa)
                    pr  = f"Şarkı: {qa}\nMood: {md.get('mood','')}\n~60 kelime anons. SADECE düz Türkçe."
                    txt = groq_gen(pr, char_id=A_CHAR, model_key=groq_mkey, max_tok=150)
                st.session_state["qa_txt"] = txt; st.rerun()
        if st.session_state.get("qa_txt"):
            ed = st.text_area("Anons:", value=st.session_state["qa_txt"], height=110, key="qa_ta")
            st.session_state["qa_txt"] = ed
            if ed.strip():
                vbtn_gemini(ed, "qa_main", sel_voice, sel_model, sel_lang, "",
                            eq_sb, reverb_sb, float(norm_sb), label="🔴 Seslendir", song=qa)

        st.divider()
        section("🔧 Sistem Durumu")
        for nm, ok in [("Groq LLM", groq_client is not None), ("Gemini TTS", bool(get_active_key()[0])),
                       ("PyDub", PYDUB_OK), ("Waveform", NP_OK), ("Mikrofon", MIC_OK)]:
            st.markdown(chip_html(f"{'✓' if ok else '✗'} {nm}", "green" if ok else "red"), unsafe_allow_html=True)

        st.divider()
        hist = load_history()
        if hist:
            section("🕑 Son Üretimler")
            for h in hist[:4]:
                st.markdown(f"<div style='font-size:.7rem;color:#3d4f68;padding:3px 0;border-bottom:1px solid #0d1420;'>{h['ts'][11:16]} — {h.get('song','')[:20]}<br><span style='color:#60a5fa;'>{h.get('preview','')[:40]}</span></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# M1 — YAYIN OTOMASYONU
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "🚀 Yayın Otomasyonu":
    page_header("🚀", "Yayın Otomasyonu", "Playlist · AI anons · Gemini TTS · Mixdown")
    songs = list_audio(PLAYLIST_DIR)
    if not songs:
        st.markdown('<div class="warn-box">⚠️ Playlist boş! 📁 Kütüphane\'den şarkı ekle.</div>', unsafe_allow_html=True)
        st.stop()

    co1, co2, co3 = st.columns(3)
    with co1:
        selected = st.multiselect("Şarkı Sıralaması:", songs, default=songs, key="aut_sel")
    with co2:
        cf_ms  = st.slider("Crossfade (ms)", 0, 3000, 1200)
        gap_ms = st.slider("Boşluk (ms)", 0, 5000, 1500)
    with co3:
        jfiles  = list_audio(JINGLE_DIR)
        sel_jgl = st.selectbox("Açılış Jingle:", ["Yok"] + jfiles)
        ducking = st.checkbox("Müzik Ducking", value=True)
        fon_files = list_audio(FON_DIR)
        auto_fon  = st.checkbox("Otomatik Fon", value=False)
        sel_fon_auto = "Yok"
        if auto_fon and fon_files:
            sel_fon_auto = st.selectbox("Fon:", fon_files)

    if not selected:
        st.info("En az bir şarkı seç."); st.stop()

    total_s = sum(audio_dur(os.path.join(PLAYLIST_DIR, f)) for f in selected)
    st.markdown(f'<div class="mono-box">📊 {len(selected)} parça · {fmt_dur(total_s)} müzik · Tahmini yayın: ~{fmt_dur(total_s + len(selected)*40)}</div>', unsafe_allow_html=True)
    st.divider()

    TONES = ["Duygusal", "Neşeli & İşveli", "Espirili", "Derin & Şiirsel", "Nostaljik", "Enerjik", "Otomatik (Mood)"]
    eff_files = list_audio(EFFECT_DIR)

    for idx, f in enumerate(selected):
        sid  = f"au{idx}_{sfn(f[:12])}"
        name = os.path.splitext(f)[0]
        tags = get_id3(os.path.join(PLAYLIST_DIR, f))
        dur  = audio_dur(os.path.join(PLAYLIST_DIR, f))
        mem  = check_memory(name)

        art_html = (f' {chip_html(tags["artist"][:16],"purple")}' if tags.get("artist") else "")
        mem_html = (f""" {chip_html(f'♻ {mem["count"]}x', "amber")}""" if mem else "")
        st.markdown(
            f'<div class="song-row"><span class="song-nm">🎵 {f[:40]}</span>'
            f'{art_html}{mem_html}<span class="song-dur">{fmt_dur(dur)}</span></div>',
            unsafe_allow_html=True)

        t1, t2, t3, t4 = st.tabs(["✨ AI Anons", "🎤 Mikrofon", "📂 Dosya Yükle", "👁 Önizleme"])

        with t1:
            ca, cb = st.columns([1, 2])
            with ca:
                tone_s  = st.selectbox("Ton:", TONES, key=f"tone_{sid}")
                ctx_s   = st.text_input("Bağlam:", key=f"ctx_{sid}", placeholder="gece yayını...")
                gen_btn = st.button("✨ Groq ile Üret", key=f"gen_{sid}")
                reg_btn = st.button("🔄 Yeniden Üret",  key=f"reg_{sid}")

            if gen_btn or reg_btn:
                md_data = {}; actual_tone = tone_s
                if tone_s == "Otomatik (Mood)":
                    with st.spinner("Mood analizi..."):
                        md_data = groq_mood(name)
                    actual_tone = md_data.get("tone_suggestion", "Duygusal")
                parts = [
                    f"Şarkı: {name}",
                    f"Sanatçı: {tags['artist']}" if tags.get("artist") else "",
                    f"Ton: {actual_tone}",
                    f"Mood: {md_data.get('mood','')}" if md_data else "",
                    f"Bağlam: {ctx_s}" if ctx_s else "",
                    "",
                    "Bu şarkı için profesyonel radyo anonsu yaz.",
                    "SADECE düz Türkçe — XML/SSML/Markdown KULLANMA.",
                ]
                with st.spinner("Yazıyor..."):
                    result = groq_gen("\n".join(p for p in parts if p), char_id=A_CHAR, model_key=groq_mkey)
                st.session_state[f"txt_{sid}"] = result
                save_memory(name, result, actual_tone); st.rerun()

            with cb:
                cur = st.session_state.get(f"txt_{sid}", "")
                new = st.text_area("Anons Metni:", value=cur, height=170, key=f"ta_{sid}",
                                   placeholder="Groq ile üret veya yaz...")
                if new != cur: st.session_state[f"txt_{sid}"] = new
                wc = word_count(new)
                if wc:
                    st.markdown(chip_html(f"📝 {wc} kelime", "blue") + " " +
                                chip_html(f"⏱ ~{est_dur(new):.0f}sn", "teal"), unsafe_allow_html=True)

                if new.strip():
                    use_fon  = st.checkbox("Fon müziği ekle", key=f"fon_chk_{sid}")
                    fon_here = "Yok"
                    if use_fon and fon_files:
                        fon_here = st.selectbox("Fon:", fon_files, key=f"fon_sel_{sid}")
                    use_eff  = st.checkbox("Efekt ekle", key=f"eff_chk_{sid}")
                    eff_here = "Yok"; eff_pos = "after"
                    if use_eff and eff_files:
                        eff_here = st.selectbox("Efekt:", eff_files, key=f"eff_sel_{sid}")
                        eff_pos  = st.radio("Konum:", ["before", "after"], horizontal=True, key=f"ep_{sid}")

                    if st.button("🔊 Anonsu Seslendir", key=f"v_{sid}", type="primary"):
                        with st.spinner("🎙️ Gemini TTS..."):
                            wav = do_tts_and_save(new, sel_voice, sel_model, sel_lang, "",
                                                  eq_sb, reverb_sb, float(norm_sb),
                                                  mode="yayin", save_to_file=True, file_prefix=sid)
                        if wav:
                            final_wav = wav
                            # Fon miksaj
                            if use_fon and fon_here != "Yok" and PYDUB_OK:
                                fp2 = os.path.join(FON_DIR, fon_here)
                                if os.path.exists(fp2):
                                    try:
                                        vseg = AudioSegment(wav[44:], frame_rate=24000, sample_width=2, channels=1)
                                        fonseg = AudioSegment.from_file(fp2)
                                        mixed  = mix_fon_voice(fonseg, vseg)
                                        if use_eff and eff_here != "Yok":
                                            ep2 = os.path.join(EFFECT_DIR, eff_here)
                                            if os.path.exists(ep2):
                                                mixed = mix_with_effect(mixed, AudioSegment.from_file(ep2), eff_pos, 200)
                                        final_p = os.path.join(OUT_DIR, f"final_{sfn(sid)}_{ts_str()}.wav")
                                        normalize_seg(mixed).export(final_p, "wav")
                                        with open(final_p, "rb") as fh: final_wav = fh.read()
                                    except Exception as e: st.warning(f"Fon: {e}")
                            st.success("✅ Hazır!")
                            st.markdown(chip_html("FON+ANONS", "teal") if (use_fon and fon_here != "Yok") else "", unsafe_allow_html=True)
                            st.audio(final_wav, format="audio/wav")
                            st.session_state[f"fp_{sid}"] = final_wav
                            save_meta(sid, {"song": f, "text": new, "char": A_CHAR, "voice": sel_voice})
                            save_history(f"{sid}.wav", new, A_CHAR, name)

        with t2:
            if MIC_OK:
                rec = mic_recorder("🔴 Kayıt Başlat", "⬛ Durdur", key=f"mic_{sid}")
                if rec:
                    st.session_state[f"fp_{sid}"] = rec["bytes"]
                    st.success("✅ Kaydedildi"); st.audio(rec["bytes"])
                    if st.button("🗣️ STT", key=f"stt_{sid}"):
                        with st.spinner("..."): sr = groq_stt(rec["bytes"], stt_lang)
                        st.session_state[f"stt_{sid}"] = sr; st.rerun()
                if st.session_state.get(f"stt_{sid}"):
                    sv = st.text_area("Transkript:", value=st.session_state[f"stt_{sid}"],
                                      height=80, key=f"stt_ta_{sid}")
                    st.session_state[f"stt_{sid}"] = sv
            else:
                st.info("streamlit-mic-recorder kurulu değil.")

        with t3:
            up = st.file_uploader("Hazır ses:", type=["mp3", "wav", "ogg", "flac"], key=f"up_{sid}")
            if up is not None:
                saved = save_uploaded_file(up, UVOICE_DIR, f"UP_{sid}_{ts_str()}.wav")
                if saved:
                    with open(saved, "rb") as fh: st.session_state[f"fp_{sid}"] = fh.read()
                    st.success(f"✅ {os.path.basename(saved)}")
                    st.audio(saved)

        with t4:
            meta = load_meta(sid)
            if meta: st.json(meta)
            fp_data = st.session_state.get(f"fp_{sid}")
            if fp_data:
                st.markdown("**Kaydedilen Anons:**")
                st.audio(fp_data, format="audio/wav")
            else:
                st.info("Henüz anons yok.")

    st.divider()
    section("🏁 Final Mixdown")
    mx1, mx2, mx3 = st.columns(3)
    with mx1: bcast_name = st.text_input("Yayın Adı:", value=f"Broadcast_{ts_str()}")
    with mx2:
        norm_mast = st.checkbox("Master Normalize", value=True)
        add_sil   = st.checkbox("Parça Arası Boşluk", value=True)
    with mx3:
        mix_btn = st.button("🏁 YAYINI BİRLEŞTİR", type="primary", use_container_width=True)

    if mix_btn:
        if not PYDUB_OK:
            st.error("PyDub kurulu değil!")
        else:
            with st.status("💎 Mixdown yapılıyor...", expanded=True) as stat:
                master = AudioSegment.silent(duration=gap_ms)
                if sel_jgl != "Yok":
                    jp = os.path.join(JINGLE_DIR, sel_jgl)
                    if os.path.exists(jp):
                        master += AudioSegment.from_file(jp) + AudioSegment.silent(500)
                        st.write(f"✅ Jingle: {sel_jgl}")
                for idx2, f in enumerate(selected):
                    sid2 = f"au{idx2}_{sfn(f[:12])}"
                    fp_data2 = st.session_state.get(f"fp_{sid2}")
                    sp = os.path.join(PLAYLIST_DIR, f)
                    try: sseg = AudioSegment.from_file(sp)
                    except Exception as e: st.warning(f"Yüklenemedi ({f}): {e}"); continue
                    if fp_data2:
                        try:
                            aseg = AudioSegment(fp_data2[44:] if len(fp_data2) > 44 else fp_data2,
                                                frame_rate=24000, sample_width=2, channels=1)
                        except Exception:
                            buf2 = BytesIO(fp_data2)
                            aseg = AudioSegment.from_file(buf2)
                        try: mixed = apply_ducking(sseg, aseg) if ducking else aseg + sseg
                        except Exception: mixed = aseg + sseg
                        master = master.append(mixed, crossfade=min(cf_ms, len(sseg) // 3))
                    else:
                        master = master.append(sseg, crossfade=min(cf_ms, len(sseg) // 3))
                    if add_sil: master += AudioSegment.silent(gap_ms)
                    st.write(f"✅ [{idx2+1}/{len(selected)}] {f}")
                if norm_mast: master = normalize_seg(master)
                out_wav = os.path.join(OUT_DIR, f"{sfn(bcast_name)}.wav")
                master.export(out_wav, "wav")
                final = do_export(out_wav, exp_fmt) if exp_fmt != "wav" else out_wav
                shutil.copy2(final, os.path.join(ARCHIVE_DIR, os.path.basename(final)))
                stat.update(label="✅ Mixdown tamamlandı!", state="complete")
            dur_m = audio_dur(final); sz_m = os.path.getsize(final) // (1024 * 1024)
            st.success(f"🔥 {bcast_name} hazır!")
            st.audio(final)
            st.markdown(f'<div class="mono-box">📁 {os.path.basename(final)}<br>⏱ {fmt_dur(dur_m)}<br>💾 {sz_m:.1f} MB</div>', unsafe_allow_html=True)
            with open(final, "rb") as fh:
                st.download_button(f"⬇️ İndir (.{exp_fmt})", fh, file_name=os.path.basename(final), mime=f"audio/{exp_fmt}")
            log_event("broadcast", {"name": bcast_name, "dur": dur_m, "tracks": len(selected)})
            st.balloons()


# ══════════════════════════════════════════════════════════════════════════════
# M2 — FON+ANONS MİKSERİ
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "🎛️ Fon+Anons Mikseri":
    page_header("🎛️", "Fon+Anons Mikseri", "Fon · anons · efekt · tam broadcast dizisi")
    fon_files  = list_audio(FON_DIR)
    eff_files  = list_audio(EFFECT_DIR)
    song_files = list_audio(PLAYLIST_DIR)

    tab_comp, tab_quick, tab_batch, tab_chain = st.tabs([
        "🎛️ Kompozisyon", "⚡ Hızlı", "📦 Toplu Fon", "🔗 Zincir Yayın"
    ])

    with tab_comp:
        c1, c2 = st.columns([1.3, 1])
        with c1:
            fa_song = st.text_input("Şarkı/Konu:", key="fa_song")
            fa_tone = st.selectbox("Ton:", ["Duygusal", "Neşeli", "Espirili", "Şiirsel", "Nostaljik", "Enerjik"])
            if st.button("✨ AI Anons Üret", key="fa_gen"):
                if fa_song.strip():
                    md = groq_mood(fa_song)
                    pr = (f"Şarkı: {fa_song}\nTon: {fa_tone}\nMood: {md.get('mood','')}\n"
                          "Profesyonel anons yaz. SADECE düz Türkçe.")
                    with st.spinner("..."): txt = groq_gen(pr, char_id=A_CHAR, model_key=groq_mkey)
                    st.session_state["fa_txt"] = txt; st.rerun()
        with c2:
            fa_txt = st.text_area("Anons:", value=st.session_state.get("fa_txt", ""),
                                   height=130, key="fa_ta", placeholder="Metin yaz veya üret...")
            if fa_txt != st.session_state.get("fa_txt", ""): st.session_state["fa_txt"] = fa_txt
            wc = word_count(fa_txt)
            if wc:
                st.markdown(chip_html(f"📝 {wc} kelime", "blue") + " " +
                            chip_html(f"⏱ ~{est_dur(fa_txt):.0f}sn", "teal"), unsafe_allow_html=True)

        st.divider(); section("Fon & Efektler")
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            sel_fon_c = st.selectbox("Fon:", ["Yok"] + fon_files, key="fa_fon") if fon_files else "Yok"
            fon_vol   = st.slider("Fon Seviyesi (dB):", -24, 0, -8, key="fa_fvol")
            fon_duck  = st.slider("Duck Derinliği:", -30, -6, -16, key="fa_duck")
        with fc2:
            sel_eff_b = st.selectbox("Öncesi Efekt:", ["Yok"] + eff_files, key="fa_eb") if eff_files else "Yok"
            sel_eff_a = st.selectbox("Sonrası Efekt:", ["Yok"] + eff_files, key="fa_ea") if eff_files else "Yok"
        with fc3:
            fade_in_fa  = st.slider("Fade-in (ms):",  100, 3000, 800,  key="fa_fin")
            fade_out_fa = st.slider("Fade-out (ms):", 100, 5000, 1500, key="fa_fout")
            gap_b = st.slider("Başlangıç Boşluk:", 0, 3000, 500)
            gap_a = st.slider("Bitiş Boşluk:", 0, 3000, 1000)

        section("Şarkı (Opsiyonel)")
        sc1, sc2 = st.columns(2)
        with sc1:
            add_song = st.checkbox("Şarkı ekle", key="fa_addsong")
            sel_song_fa = st.selectbox("Şarkı:", song_files, key="fa_song_sel") if (add_song and song_files) else None
        with sc2:
            song_pos = st.radio("Konum:", ["Anons Sonrası", "Anons Öncesi"], horizontal=True, key="fa_spos") if add_song else "Anons Sonrası"
            song_cf  = st.slider("Crossfade:", 0, 2000, 800, key="fa_scf") if add_song else 800

        st.divider()
        if st.button("🎛️ MİKSLE & OLUŞTUR", type="primary", key="fa_mix_btn", use_container_width=True):
            fa_cur = st.session_state.get("fa_txt", "")
            if not fa_cur.strip(): st.warning("Önce anons metnini gir!")
            elif not PYDUB_OK: st.error("PyDub kurulu değil!")
            else:
                with st.spinner("🎙️ Gemini TTS..."):
                    wav = do_tts_and_save(fa_cur, sel_voice, sel_model, sel_lang, "",
                                         eq_sb, reverb_sb, float(norm_sb),
                                         mode="fon_anons", save_to_file=True, file_prefix="fa_raw")
                if not wav: st.error("Ses üretilemedi.")
                else:
                    with st.spinner("🎛️ Miksliyor..."):
                        vseg   = AudioSegment(wav[44:], frame_rate=24000, sample_width=2, channels=1)
                        result = AudioSegment.silent(gap_b)
                        if isinstance(sel_eff_b, str) and sel_eff_b != "Yok":
                            ep = os.path.join(EFFECT_DIR, sel_eff_b)
                            if os.path.exists(ep): result += AudioSegment.from_file(ep)
                        if isinstance(sel_fon_c, str) and sel_fon_c != "Yok":
                            fp2 = os.path.join(FON_DIR, sel_fon_c)
                            if os.path.exists(fp2):
                                result += mix_fon_voice(AudioSegment.from_file(fp2), vseg,
                                                        fon_vol=fon_vol, duck_db=fon_duck,
                                                        fade_in=fade_in_fa, fade_out=fade_out_fa)
                            else: result += vseg
                        else: result += vseg
                        if isinstance(sel_eff_a, str) and sel_eff_a != "Yok":
                            ep = os.path.join(EFFECT_DIR, sel_eff_a)
                            if os.path.exists(ep): result += AudioSegment.from_file(ep)
                        result += AudioSegment.silent(gap_a)
                        if add_song and sel_song_fa:
                            sp2 = os.path.join(PLAYLIST_DIR, sel_song_fa)
                            if os.path.exists(sp2):
                                sseg = AudioSegment.from_file(sp2)
                                result = (result.append(sseg, crossfade=song_cf)
                                          if song_pos == "Anons Sonrası"
                                          else sseg.append(result, crossfade=song_cf))
                        out_p = os.path.join(OUT_DIR, f"fon_anons_{ts_str()}.wav")
                        normalize_seg(result).export(out_p, "wav")
                    qs = quality_score(out_p)
                    st.success("✅ Fon+Anons hazır!")
                    st.markdown(chip_html(f"🎯 {qs}/100", "green") + " " +
                                chip_html(f"⏱ {fmt_dur(audio_dur(out_p))}", "blue") + " " +
                                chip_html("FON+ANONS", "teal"), unsafe_allow_html=True)
                    st.audio(out_p); qbar(qs); draw_waveform(out_p)
                    with open(out_p, "rb") as fh:
                        st.download_button("⬇️ İndir", fh, os.path.basename(out_p), key="fa_dl")

    with tab_quick:
        qf1, qf2 = st.columns(2)
        with qf1:
            qf_text = st.text_area("Anons:", height=110, key="qf_txt")
            qf_fon  = st.selectbox("Fon:", fon_files, key="qf_fon") if fon_files else None
        with qf2:
            qf_eff = st.selectbox("Efekt:", ["Yok"] + eff_files, key="qf_eff") if eff_files else "Yok"
            qf_vol = st.slider("Fon Ses:", -24, 0, -10, key="qf_vol")
        if st.button("⚡ HIZLI OLUŞTUR", key="qf_btn", type="primary"):
            if qf_text.strip() and qf_fon and PYDUB_OK:
                with st.spinner("..."):
                    wav = do_tts_and_save(qf_text, sel_voice, sel_model, sel_lang, "",
                                         eq_sb, reverb_sb, float(norm_sb),
                                         mode="hizli", save_to_file=True, file_prefix="qfon")
                if wav:
                    fonseg = AudioSegment.from_file(os.path.join(FON_DIR, qf_fon))
                    vseg   = AudioSegment(wav[44:], frame_rate=24000, sample_width=2, channels=1)
                    mixed  = mix_fon_voice(fonseg, vseg, fon_vol=qf_vol)
                    if isinstance(qf_eff, str) and qf_eff != "Yok":
                        ep = os.path.join(EFFECT_DIR, qf_eff)
                        if os.path.exists(ep): mixed += AudioSegment.from_file(ep)
                    op = os.path.join(OUT_DIR, f"qfon_{ts_str()}.wav")
                    normalize_seg(mixed).export(op, "wav")
                    st.success("✅"); st.audio(op); draw_waveform(op)
            else: st.warning("Metin, fon ve PyDub gerekli.")

    with tab_batch:
        if fon_files and PYDUB_OK:
            bf_fon = st.selectbox("Fon:", fon_files, key="bf_fon")
            bf_vol = st.slider("Fon Ses:", -24, 0, -10, key="bf_vol")
            bf_sel = st.multiselect("İşlenecek Dosyalar:", list_audio(OUT_DIR), key="bf_sel")
            if st.button("📦 Toplu Uygula", key="bf_btn") and bf_sel:
                prog = st.progress(0)
                for i, f_bf in enumerate(bf_sel):
                    fonseg = AudioSegment.from_file(os.path.join(FON_DIR, bf_fon))
                    vseg   = AudioSegment.from_file(os.path.join(OUT_DIR, f_bf))
                    normalize_seg(mix_fon_voice(fonseg, vseg, fon_vol=bf_vol))\
                        .export(os.path.join(OUT_DIR, f"fon_{f_bf}"), "wav")
                    prog.progress((i + 1) / len(bf_sel))
                st.success(f"✅ {len(bf_sel)} dosyaya fon uygulandı!")
        else:
            st.markdown('<div class="info-box">ℹ️ /fon klasörüne müzik ekle ve PyDub kur.</div>', unsafe_allow_html=True)

    with tab_chain:
        st.markdown('<div class="info-box">ℹ️ Her şarkı için: AI Anons (Gemini TTS) → Fon Duck → Şarkı pipeline.</div>', unsafe_allow_html=True)
        if song_files and fon_files and PYDUB_OK:
            ch_songs  = st.multiselect("Şarkılar:", song_files, default=song_files[:2], key="ch_songs")
            ch_fon    = st.selectbox("Fon:", fon_files, key="ch_fon")
            ch_char   = st.selectbox("Anons Karakteri:", list(CHARS.keys()), key="ch_char")
            ch_voice  = CHARS[ch_char]["voice"]
            ch_name   = st.text_input("Yayın Adı:", value=f"Chain_{ts_str()}", key="ch_name")
            if st.button("🔗 ZİNCİR YAYIN OLUŞTUR", type="primary", key="ch_btn") and ch_songs:
                ak_ch, ai_ch = get_active_key()
                if not ak_ch: st.error("API yok!"); st.stop()
                with st.status("Zincir yayın oluşturuluyor...", expanded=True) as stat_ch:
                    master_ch = AudioSegment.silent(1000)
                    for i, sg in enumerate(ch_songs):
                        sn = os.path.splitext(sg)[0]
                        st.write(f"🎵 [{i+1}/{len(ch_songs)}] {sg} işleniyor...")
                        md_ch = groq_mood(sn)
                        anons_txt = groq_gen(
                            f"Şarkı: {sn}\nMood: {md_ch.get('mood','')}\nKısa anons. SADECE düz Türkçe.",
                            char_id=CHARS[ch_char]["id"], model_key=groq_mkey, max_tok=200
                        )
                        try:
                            wav_ch, _ = gemini_tts_to_file(ak_ch, sel_model, anons_txt, ch_voice, "tr-TR", "",
                                                            eq_preset=eq_sb, reverb=reverb_sb, norm_db=float(norm_sb))
                            consume(ai_ch, len(anons_txt))
                            vseg_ch  = AudioSegment(wav_ch[44:], frame_rate=24000, sample_width=2, channels=1)
                            fonseg_ch = AudioSegment.from_file(os.path.join(FON_DIR, ch_fon))
                            block = mix_fon_voice(fonseg_ch, vseg_ch).append(
                                AudioSegment.from_file(os.path.join(PLAYLIST_DIR, sg)), crossfade=1200)
                            master_ch = master_ch.append(block, crossfade=800)
                        except Exception as e: st.warning(f"{sg}: {e}")
                    out_ch = os.path.join(OUT_DIR, f"{sfn(ch_name)}.wav")
                    normalize_seg(master_ch).export(out_ch, "wav")
                    shutil.copy2(out_ch, os.path.join(ARCHIVE_DIR, os.path.basename(out_ch)))
                    stat_ch.update(label="✅ Zincir yayın hazır!", state="complete")
                st.success(f"🎉 {ch_name} hazır!"); st.audio(out_ch)
                st.markdown(f'<div class="mono-box">⏱ {fmt_dur(audio_dur(out_ch))} · {len(ch_songs)} parça</div>', unsafe_allow_html=True)
                with open(out_ch, "rb") as fh:
                    st.download_button("⬇️ İndir", fh, os.path.basename(out_ch), key="ch_dl")
        else:
            st.markdown('<div class="warn-box">⚠️ Playlist, Fon ve PyDub gerekli.</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# M3 — KARAKTER STÜDYOSU (Groq LLM + Gemini TTS)
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "🎭 Karakter Stüdyosu":
    page_header("🎭", "Karakter Stüdyosu", "Groq LLM ile AI anons üret + Gemini TTS ile seslendir")
    c1, c2 = st.columns([1.3, 1])
    with c1:
        kar_sel  = st.selectbox("Karakter:", list(CHARS.keys()), key="kar_sel")
        kar_char = CHARS[kar_sel]
        kar_voice = st.selectbox("Gemini Sesi:", list(VOICES.keys()),
                                  format_func=lambda x: f"{VOICES[x][0]} {x} — {VOICES[x][1]}",
                                  index=list(VOICES.keys()).index(kar_char["voice"]), key="kar_voice")
        kar_tone  = st.selectbox("Ton:", ["Duygusal", "Neşeli", "Espirili", "Şiirsel", "Nostaljik", "Enerjik"])
        kar_topic = st.text_area("Konu / Şarkı / Talimat:", height=90, key="kar_topic",
                                  placeholder="Şarkı adı, haber konusu, program tanıtımı...")
        kar_wt    = st.slider("Hedef kelime:", 30, 250, 90, key="kar_wt")
        if st.button("🚀 Groq ile Üret", key="kar_gen"):
            if kar_topic.strip():
                pr = f"Konu: {kar_topic}\nTon: {kar_tone}\nHedef: ~{kar_wt} kelime\nSADECE düz Türkçe."
                with st.spinner("Groq yazıyor..."):
                    res = groq_gen(pr, char_id=kar_char["id"], model_key=groq_mkey, max_tok=kar_wt * 6)
                st.session_state["kar_txt"] = res; st.rerun()

    with c2:
        kar_txt = st.text_area("Üretilen Metin:", value=st.session_state.get("kar_txt", ""),
                                height=250, key="kar_ta")
        if kar_txt != st.session_state.get("kar_txt", ""): st.session_state["kar_txt"] = kar_txt
        wc = word_count(kar_txt)
        if wc:
            st.markdown(chip_html(f"📝 {wc} kelime", "blue") + " " +
                        chip_html(f"⏱ ~{est_dur(kar_txt):.0f}sn", "teal"), unsafe_allow_html=True)
        if kar_txt.strip():
            kar_style = st.text_area("Stil talimatı (opsiyonel):", height=60, key="kar_style")
            bc1, bc2 = st.columns(2)
            with bc1:
                vbtn_gemini(kar_txt, "kar_main", kar_voice, sel_model, "tr-TR",
                            kar_style, eq_sb, reverb_sb, float(norm_sb), label="🔴 Seslendir", mode="karakter")
            with bc2:
                st.download_button("⬇️ TXT", kar_txt.encode("utf-8"),
                                   f"karakter_{ts_str()}.txt", "text/plain", key="kar_dl")
            st.markdown(chip_html(kar_char["id"].upper(), "blue") + " " + chip_html(kar_voice, "green"), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# M4 — TEK KONUŞMACI (İmaj FM v4 style)
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "🎤 Tek Konuşmacı":
    page_header("🎤", "Tek Konuşmacı", "Gemini TTS · Radyo şablonları · Duygu etiketleri")

    # Şablon yükle
    with st.expander("📋 Radyo Şablonları", expanded=False):
        tpl_cols = st.columns(4)
        for ti2, (tpl_name, tpl_text) in enumerate(TEMPLATES.items()):
            with tpl_cols[ti2 % 4]:
                if st.button(tpl_name, key=f"tpl_{ti2}", use_container_width=True):
                    st.session_state["_t_tek"] = tpl_text; st.rerun()

    # Metin alanı
    st.markdown("<span class='sl'>▸ METIN & DUYGU ETİKETLERİ</span>", unsafe_allow_html=True)
    tag_buttons("_t_tek", "tek")
    tek_txt = st.text_area("Metin:", value=st.session_state.get("_t_tek", ""),
                            height=180, key="tek_ta",
                            placeholder="[excitedly] Günaydın İmaj FM!\n[whispers] Bugün harika bir program...")
    if tek_txt != st.session_state.get("_t_tek", ""):
        st.session_state["_t_tek"] = tek_txt
    if tek_txt: text_stats_bar(tek_txt)

    # Stil
    st.markdown("<span class='sl2'>▸ STİL TALİMATI</span>", unsafe_allow_html=True)
    ps_tek = st.selectbox("Preset:", list(STYLE_PRESETS.keys()), label_visibility="collapsed", key="tek_ps")
    tek_style = st.text_area("Stil:", value=STYLE_PRESETS[ps_tek], height=55,
                              label_visibility="collapsed", key="tek_style")

    # Ses seçici + seslendirme
    vc1, vc2, vc3 = st.columns([2, 1, 1])
    with vc1:
        tek_voice = st.selectbox("Ses:", list(VOICES.keys()),
                                  format_func=lambda x: f"{VOICES[x][0]} {x} — {VOICES[x][1]}",
                                  key="tek_voice")
    with vc2:
        tek_model = st.selectbox("Model:", list(MODELS.keys()), format_func=lambda x: MODELS[x],
                                  key="tek_model")
    with vc3:
        tek_lang  = st.selectbox("Dil:", list(LANGUAGES.keys()), format_func=lambda x: LANGUAGES[x],
                                  key="tek_lang", index=1)

    bb1, bb2, bb3, bb4 = st.columns(4)
    with bb1:
        if st.button("🔴 Seslendir", key="tek_go", type="primary", use_container_width=True):
            if tek_txt.strip():
                ak2, ai2 = get_active_key()
                if ak2 is None: st.error("❌ API yok!")
                else:
                    with st.spinner("🎙️ Gemini TTS..."):
                        try:
                            raw2 = tts_single(ak2, tek_model, tek_txt, tek_voice, tek_lang, tek_style)
                            wav2 = pcm2wav(raw2)
                            if PYDUB_OK:
                                seg2 = AudioSegment(raw2, frame_rate=24000, sample_width=2, channels=1)
                                if eq_sb != "Ham (Efektsiz)": seg2 = apply_eq(seg2, eq_sb)
                                if reverb_sb > 0: seg2 = apply_reverb(seg2, reverb_sb)
                                seg2 = normalize_seg(seg2, float(norm_sb))
                                buf2 = BytesIO(); seg2.export(buf2, format="wav"); wav2 = buf2.getvalue()
                            consume(ai2, len(tek_txt))
                            archive_add(tek_voice, tek_model, tek_lang, tek_style, tek_txt, wav2, "tek")
                            st.session_state["_tek_wav"] = wav2
                            save_history(f"tek_{ts_str()}.wav", tek_txt, tek_voice)
                            st.rerun()
                        except Exception as e: st.error(f"❌ {e}")
    with bb2:
        if st.session_state.get("_tek_wav"):
            st.download_button("💾 WAV", st.session_state["_tek_wav"],
                               f"imajfm_tek_{ts_str()}.wav", "audio/wav", key="tek_dl")
    with bb3:
        if st.button("⭐ Favoriye", key="tek_fav", use_container_width=True):
            fname2 = st.text_input("Favori adı:", key="tek_fav_name", placeholder="Açılış anonsu")
            if fname2:
                st.session_state._favorites.append({
                    "id": hashlib.md5(tek_txt.encode()).hexdigest()[:8],
                    "name": fname2, "text": tek_txt,
                    "voice": tek_voice, "model": tek_model, "lang": tek_lang,
                }); st.rerun()
    with bb4:
        if st.button("🗑️ Temizle", key="tek_clr", use_container_width=True):
            st.session_state["_t_tek"] = ""; st.session_state.pop("_tek_wav", None); st.rerun()

    if st.session_state.get("_tek_wav"):
        dur2 = len(st.session_state["_tek_wav"]) / (24000 * 2)
        qs2  = quality_score_bytes(st.session_state["_tek_wav"])
        st.markdown(f'<div class="card g">✅ {VOICES[tek_voice][0]} {tek_voice} · {dur2:.1f}s · {len(st.session_state["_tek_wav"]):,} byte</div>', unsafe_allow_html=True)
        st.audio(st.session_state["_tek_wav"], format="audio/wav")
        qbar(qs2); draw_waveform_bytes(st.session_state.get("_tek_wav"))


# ══════════════════════════════════════════════════════════════════════════════
# M5 — ÇİFT KONUŞMACI
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "👥 Çift Konuşmacı":
    page_header("👥", "Çift Konuşmacı", "Gemini Multi-Speaker TTS")
    st.info("Format: `İsim: [excitedly] Metin` — Her satır ayrı konuşmacı.")

    cift_txt = st.text_area("Diyalog:", value=st.session_state.get("_t_cift",
        "Sunucu: [excitedly] İmaj FM'e hoş geldiniz!\nMisafir: [laughs] Teşekkürler, burada olmak harika!\nSunucu: [seriously] Haberler... [normal] Müziğe dönüyoruz."),
        height=180, key="cift_ta")
    _safe_init("_t_cift", cift_txt)

    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        sp1_name  = st.text_input("1. Konuşmacı adı:", value="Sunucu", key="sp1_name")
        sp1_voice = st.selectbox("1. Ses:", list(VOICES.keys()),
                                  format_func=lambda x: f"{VOICES[x][0]} {x}",
                                  key="sp1_voice", index=list(VOICES.keys()).index("Kore"))
    with cc2:
        sp2_name  = st.text_input("2. Konuşmacı adı:", value="Misafir", key="sp2_name")
        sp2_voice = st.selectbox("2. Ses:", list(VOICES.keys()),
                                  format_func=lambda x: f"{VOICES[x][0]} {x}",
                                  key="sp2_voice", index=list(VOICES.keys()).index("Puck"))
    with cc3:
        cift_model = st.selectbox("Model:", list(MODELS.keys()), format_func=lambda x: MODELS[x], key="cift_model")
        cift_lang  = st.selectbox("Dil:", list(LANGUAGES.keys()), format_func=lambda x: LANGUAGES[x], key="cift_lang", index=1)

    if st.button("🔴 Çift Konuşmacı Seslendir", key="cift_go", type="primary"):
        if not cift_txt.strip(): st.warning("Metin boş!")
        else:
            ak3, ai3 = get_active_key()
            if ak3 is None: st.error("❌ API yok!")
            else:
                with st.spinner("🎙️ Multi-Speaker Gemini TTS..."):
                    try:
                        raw3 = tts_multi(ak3, cift_model, cift_txt, sp1_name, sp1_voice, sp2_name, sp2_voice, cift_lang)
                        wav3 = pcm2wav(raw3)
                        if PYDUB_OK:
                            seg3 = AudioSegment(raw3, frame_rate=24000, sample_width=2, channels=1)
                            seg3 = normalize_seg(seg3, float(norm_sb))
                            buf3 = BytesIO(); seg3.export(buf3, format="wav"); wav3 = buf3.getvalue()
                        consume(ai3, len(cift_txt))
                        archive_add(f"{sp1_voice}+{sp2_voice}", cift_model, cift_lang, "", cift_txt, wav3, "cift")
                        st.session_state["_cift_wav"] = wav3; st.rerun()
                    except Exception as e: st.error(f"❌ {e}")

    if st.session_state.get("_cift_wav"):
        dur3 = len(st.session_state["_cift_wav"]) / (24000 * 2)
        st.markdown(f'<div class="card g">✅ {sp1_voice} + {sp2_voice} · {dur3:.1f}s</div>', unsafe_allow_html=True)
        st.audio(st.session_state["_cift_wav"], format="audio/wav")
        st.download_button("💾 WAV", st.session_state["_cift_wav"],
                           f"imajfm_cift_{ts_str()}.wav", "audio/wav", key="cift_dl")


# ══════════════════════════════════════════════════════════════════════════════
# M6 — HABER BÜLTENİ
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "📰 Haber Bülteni":
    page_header("📰", "Haber Bülteni", "AI ile haber metni üret ve seslendir")
    nb1, nb2 = st.columns([1.3, 1])
    with nb1:
        nb_date   = st.text_input("Tarih/Saat:", value=datetime.now().strftime("%d %B %Y, %H:%M"), key="nb_date")
        nb_items  = st.text_area("Haber Başlıkları (her satır ayrı):", height=150, key="nb_items",
                                  placeholder="Hükümet yeni ekonomi paketini açıkladı\nAvrupa'da sıcaklık rekoru kırıldı\nSüper Lig'de haftanın sonuçları")
        nb_style  = st.selectbox("Ton:", ["Resmi · Tarafsız", "Kısa · Özet", "Geniş Haber"])
        if st.button("✨ Haber Metni Üret", key="nb_gen"):
            if nb_items.strip():
                pr = (f"Tarih: {nb_date}\nHaber başlıkları:\n{nb_items}\n\n"
                      f"Stil: {nb_style}\n"
                      "Profesyonel radyo haber bülteni yaz. SADECE düz Türkçe.")
                with st.spinner("Groq yazıyor..."):
                    res = groq_gen(pr, char_id="haber", model_key=groq_mkey, max_tok=500)
                st.session_state["nb_txt"] = res; st.rerun()
    with nb2:
        nb_txt = st.text_area("Haber Metni:", value=st.session_state.get("nb_txt", ""),
                               height=320, key="nb_ta")
        if nb_txt != st.session_state.get("nb_txt", ""): st.session_state["nb_txt"] = nb_txt
        if nb_txt.strip():
            wc_nb = word_count(nb_txt)
            st.markdown(chip_html(f"📝 {wc_nb} kelime", "blue") + " " +
                        chip_html(f"⏱ ~{est_dur(nb_txt):.0f}sn", "teal"), unsafe_allow_html=True)
            nb_voice = st.selectbox("Haber Sesi:", list(VOICES.keys()),
                                     format_func=lambda x: f"{VOICES[x][0]} {x}",
                                     index=list(VOICES.keys()).index("Iapetus"), key="nb_voice")
            vbtn_gemini(nb_txt, "nb_main", nb_voice, sel_model, "tr-TR", "",
                        eq_sb, reverb_sb, float(norm_sb), label="🔴 Haberi Seslendir", mode="haber")
            # Dosyaya kaydet
            if st.button("💾 Bülteni Kaydet", key="nb_save"):
                nb_file = os.path.join(NEWS_DIR, f"bulten_{ts_str()}.txt")
                with open(nb_file, "w", encoding="utf-8") as f: f.write(nb_txt)
                st.success(f"✅ Kaydedildi: {os.path.basename(nb_file)}")


# ══════════════════════════════════════════════════════════════════════════════
# M7 — İSTEK & MESAJLAR
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "📩 İstek & Mesajlar":
    page_header("📩", "İstek & Mesajlar", "Dinleyici istekleri ve anons üretimi")
    rq1, rq2 = st.tabs(["📥 Yeni İstek", "📋 İstekler"])
    with rq1:
        ra1, ra2 = st.columns(2)
        with ra1:
            rq_name = st.text_input("Dinleyici Adı:", key="rq_name")
            rq_song = st.text_input("Şarkı İsteği:", key="rq_song")
        with ra2:
            rq_msg  = st.text_area("Mesaj:", height=100, key="rq_msg")
        if st.button("📩 İstek Kaydet", key="rq_save"):
            if rq_name and rq_song:
                rq_data = {"name": rq_name, "song": rq_song, "message": rq_msg,
                           "timestamp": datetime.now().isoformat(), "status": "bekliyor"}
                rq_file = os.path.join(REQUEST_DIR, f"req_{ts_str()}.json")
                with open(rq_file, "w", encoding="utf-8") as f: json.dump(rq_data, f, ensure_ascii=False)
                st.success("✅ İstek kaydedildi!"); st.rerun()

    with rq2:
        rfiles = sorted([f for f in os.listdir(REQUEST_DIR) if f.endswith(".json")], reverse=True)
        if not rfiles: st.info("Henüz istek yok.")
        for rf in rfiles[:25]:
            try:
                with open(os.path.join(REQUEST_DIR, rf)) as fh: rd = json.load(fh)
                sc_rq = "green" if rd.get("status") == "broadcast" else "amber"
                with st.expander(f"🎵 {rd.get('song','?')} — {rd.get('name','?')}"):
                    st.markdown(chip_html(rd.get("status", "?").upper(), sc_rq) + " " +
                                chip_html(rd.get("name", "?"), "blue"), unsafe_allow_html=True)
                    st.caption(f"Mesaj: {rd.get('message','—')} | {rd.get('timestamp','')[:16]}")
                    bc1_rq, bc2_rq = st.columns(2)
                    with bc1_rq:
                        if st.button("📻 Anons Üret", key=f"ri_{rf}"):
                            pr_rq = (f"Dinleyici: {rd.get('name')}\nŞarkı: {rd.get('song')}\n"
                                     f"Mesaj: {rd.get('message')}\nSADECE düz Türkçe anons.")
                            with st.spinner("..."):
                                txt_rq = groq_gen(pr_rq, char_id=A_CHAR, model_key=groq_mkey, max_tok=250)
                            st.session_state[f"ri_txt_{rf}"] = txt_rq; st.rerun()
                        if st.session_state.get(f"ri_txt_{rf}"):
                            t_rq = st.text_area("Anons:", value=st.session_state[f"ri_txt_{rf}"],
                                                height=90, key=f"ri_ta_{rf}")
                            st.session_state[f"ri_txt_{rf}"] = t_rq
                            vbtn_gemini(t_rq, f"ri_v_{rf}", sel_voice, sel_model, "tr-TR", "",
                                        eq_sb, reverb_sb, float(norm_sb), label="🔴 Seslendir")
                    with bc2_rq:
                        if st.button("✅ Yayına Alındı", key=f"rd_{rf}"):
                            rd["status"] = "broadcast"
                            with open(os.path.join(REQUEST_DIR, rf), "w") as fh:
                                json.dump(rd, fh, ensure_ascii=False)
                            st.rerun()
            except Exception: pass


# ══════════════════════════════════════════════════════════════════════════════
# M8 — MANUEL STÜDYO
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "✍️ Manuel Stüdyo":
    page_header("✍️", "Manuel Stüdyo", "Serbest metin yazma ve seslendirme")
    c1, c2 = st.columns([1.3, 1])
    STYLE_MAP = {"Radyo Sunucu": "dilay", "Haber Spikeri": "haber",
                 "Reklam Sesi": "reklam", "Gece DJsi": "gece", "Sabah Sunucusu": "sabah"}
    with c1:
        m_tone  = st.selectbox("Ton:", ["Duygusal", "Neşeli", "Espirili", "Şiirsel", "Nostaljik", "Enerjik", "Genel"])
        m_style = st.selectbox("Stil:", list(STYLE_MAP.keys()))
        m_wt    = st.slider("Hedef kelime:", 30, 250, 90)
        m_cust  = st.text_area("Konu/talimat:", height=75, key="m_cust")
        if st.button("🚀 Groq ile Üret", key="m_gen"):
            pr_m = f"Ton: {m_tone}\nStil: {m_style}\nHedef: ~{m_wt} kelime\n{m_cust}\nSADECE düz Türkçe — XML/SSML YOK."
            with st.spinner("..."):
                res_m = groq_gen(pr_m, char_id=STYLE_MAP.get(m_style, "dilay"),
                                 model_key=groq_mkey, max_tok=m_wt * 6)
            st.session_state["m_txt"] = res_m; st.rerun()
    with c2:
        m_txt = st.text_area("Son Metin:", value=st.session_state.get("m_txt", ""),
                              height=295, key="m_ta")
        if m_txt != st.session_state.get("m_txt", ""): st.session_state["m_txt"] = m_txt
        wc_m = word_count(m_txt)
        if wc_m:
            st.markdown(chip_html(f"📝 {wc_m} kelime", "blue") + " " +
                        chip_html(f"⏱ ~{est_dur(m_txt):.0f}sn", "teal"), unsafe_allow_html=True)
        if m_txt.strip():
            bc1_m, bc2_m, bc3_m = st.columns(3)
            with bc1_m:
                vbtn_gemini(m_txt, "m_v", sel_voice, sel_model, sel_lang, "",
                            eq_sb, reverb_sb, float(norm_sb), label="🔴 Seslendir", mode="manuel")
            with bc2_m:
                st.download_button("⬇️ TXT", m_txt.encode("utf-8"), f"anons_{ts_str()}.txt",
                                   "text/plain", key="m_dl")
            with bc3_m:
                if st.button("🔄 Sıfırla", key="m_rst"):
                    st.session_state["m_txt"] = ""; st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# M9 — TOPLU TTS
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "📦 Toplu TTS":
    page_header("📦", "Toplu TTS", "CSV / TXT / Manuel liste — Gemini TTS ile seri üretim")
    tab_txt, tab_csv, tab_list = st.tabs(["📄 TXT", "📊 CSV", "✏️ Manuel Liste"])

    with tab_txt:
        st.info("Her satır ayrı bir ses dosyası olarak üretilir.")
        txt_up = st.file_uploader("TXT dosyası:", type=["txt"], key="bulk_txt_up")
        if txt_up:
            saved_txt = save_uploaded_file(txt_up, UPLOAD_DIR, f"bulk_{ts_str()}.txt")
            if saved_txt:
                with open(saved_txt, "r", encoding="utf-8", errors="ignore") as f:
                    lines_txt = [l.strip() for l in f.readlines() if l.strip()]
                st.success(f"✅ {len(lines_txt)} satır")
                st.session_state["bulk_lines"] = lines_txt
        if st.session_state.get("bulk_lines"):
            lines = st.session_state["bulk_lines"]
            st.markdown(f'<div class="mono-box">{len(lines)} satır · İlk 3: {" | ".join(lines[:3])[:100]}</div>', unsafe_allow_html=True)
            bulk_prefix = st.text_input("Dosya ön eki:", value="satir", key="bulk_prefix")
            bulk_voice  = st.selectbox("Ses:", list(VOICES.keys()), format_func=lambda x: f"{VOICES[x][0]} {x}", key="bulk_voice")
            if st.button("🚀 Toplu Üret", key="bulk_txt_btn", type="primary"):
                ak_b, ai_b = get_active_key()
                if not ak_b: st.error("API yok!")
                else:
                    prog = st.progress(0); results = []
                    for i, line in enumerate(lines):
                        try:
                            raw_b = tts_single(ak_b, sel_model, line, bulk_voice, "tr-TR", "")
                            wav_b = pcm2wav(raw_b)
                            consume(ai_b, len(line))
                            fname_b = os.path.join(OUT_DIR, f"{bulk_prefix}_{i+1:03d}_{ts_str()}.wav")
                            with open(fname_b, "wb") as f: f.write(wav_b)
                            archive_add(bulk_voice, sel_model, "tr-TR", "", line, wav_b, "bulk")
                            results.append(fname_b)
                        except Exception as e: st.warning(f"[{i+1}]: {e}")
                        prog.progress((i + 1) / len(lines))
                    st.success(f"✅ {len(results)}/{len(lines)} ses üretildi!")
                    for r_b in results[:3]: st.audio(r_b)
                    if results:
                        zdata = zip_files(results, "toplu_tts")
                        if zdata:
                            st.download_button("⬇️ ZIP İndir", zdata, "toplu_tts.zip", "application/zip")

    with tab_csv:
        csv_up = st.file_uploader("CSV dosyası:", type=["csv"], key="bulk_csv_up")
        if csv_up:
            try:
                import csv as _csv, io as _io
                content_csv = csv_up.read().decode("utf-8", "ignore")
                reader_csv  = _csv.DictReader(_io.StringIO(content_csv))
                rows_csv    = list(reader_csv)
                if rows_csv:
                    headers_csv = list(rows_csv[0].keys())
                    st.success(f"✅ {len(rows_csv)} satır | Sütunlar: {', '.join(headers_csv)}")
                    text_col = st.selectbox("Metin Sütunu:", headers_csv, key="csv_col")
                    csv_voice = st.selectbox("Ses:", list(VOICES.keys()), format_func=lambda x: f"{VOICES[x][0]} {x}", key="csv_voice")
                    if st.button("🚀 CSV'den Üret", key="csv_btn", type="primary"):
                        ak_csv, ai_csv = get_active_key()
                        if not ak_csv: st.error("API yok!")
                        else:
                            prog_csv = st.progress(0); cnt_csv = 0
                            for i, row in enumerate(rows_csv):
                                txt_csv = row.get(text_col, "").strip()
                                if txt_csv:
                                    try:
                                        raw_csv = tts_single(ak_csv, sel_model, txt_csv, csv_voice, "tr-TR", "")
                                        wav_csv = pcm2wav(raw_csv)
                                        consume(ai_csv, len(txt_csv))
                                        fname_csv = os.path.join(OUT_DIR, f"csv_{i+1:03d}_{ts_str()}.wav")
                                        with open(fname_csv, "wb") as f: f.write(wav_csv)
                                        archive_add(csv_voice, sel_model, "tr-TR", "", txt_csv, wav_csv, "bulk")
                                        cnt_csv += 1
                                    except Exception: pass
                                prog_csv.progress((i + 1) / len(rows_csv))
                            st.success(f"✅ {cnt_csv} ses üretildi!")
            except Exception as e: st.error(f"CSV hatası: {e}")

    with tab_list:
        ml_txt = st.text_area("Her satır ayrı ses:", height=200, key="ml_txt",
                               placeholder="Günaydın canım ailemiz!\nHava bugün çok güzel.\nVe şimdi müzikle baş başa bırakıyoruz.")
        ml_prefix = st.text_input("Ön ek:", value="anons", key="ml_prefix")
        ml_voice  = st.selectbox("Ses:", list(VOICES.keys()), format_func=lambda x: f"{VOICES[x][0]} {x}", key="ml_voice")
        if st.button("🚀 Hepsini Üret", key="ml_btn", type="primary") and ml_txt.strip():
            lines_ml = [l.strip() for l in ml_txt.split("\n") if l.strip()]
            ak_ml, ai_ml = get_active_key()
            if not ak_ml: st.error("API yok!")
            else:
                prog_ml = st.progress(0); results_ml = []
                for i, line in enumerate(lines_ml):
                    try:
                        raw_ml = tts_single(ak_ml, sel_model, line, ml_voice, "tr-TR", "")
                        wav_ml = pcm2wav(raw_ml)
                        consume(ai_ml, len(line))
                        fname_ml = os.path.join(OUT_DIR, f"{ml_prefix}_{i+1:03d}_{ts_str()}.wav")
                        with open(fname_ml, "wb") as f: f.write(wav_ml)
                        archive_add(ml_voice, sel_model, "tr-TR", "", line, wav_ml, "bulk")
                        results_ml.append(fname_ml)
                    except Exception as e: st.warning(f"[{i+1}]: {e}")
                    prog_ml.progress((i + 1) / len(lines_ml))
                st.success(f"✅ {len(results_ml)}/{len(lines_ml)} üretildi!")
                if results_ml and PYDUB_OK:
                    if st.button("🔗 Birleştir", key="ml_merge"):
                        master_ml = audio_concat([AudioSegment.from_file(p) for p in results_ml])
                        out_p_ml  = os.path.join(OUT_DIR, f"merged_{ts_str()}.wav")
                        normalize_seg(master_ml).export(out_p_ml, "wav"); st.audio(out_p_ml)
                        with open(out_p_ml, "rb") as fh:
                            st.download_button("⬇️ Birleştirilmiş", fh, os.path.basename(out_p_ml), key="ml_dl")
                if results_ml:
                    zdata_ml = zip_files(results_ml, "liste_tts")
                    if zdata_ml:
                        st.download_button("⬇️ ZIP İndir", zdata_ml, "liste_tts.zip", "application/zip")


# ══════════════════════════════════════════════════════════════════════════════
# M10 — INTRO / OUTRO
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "🎬 Intro/Outro":
    page_header("🎬", "Intro/Outro Builder", "Program girişi ve kapanış seslendirme")
    ti_tab, to_tab = st.tabs(["🎬 Program Girişi", "🎤 Program Kapanışı"])

    def io_tab_fn(tab_io, title_io, sys_pr_io, kp_io):
        with tab_io:
            prog_name_io = st.text_input("Program Adı:", key=f"{kp_io}_prog")
            dstr_io      = st.text_input("Tarih/Saat:", value=datetime.now().strftime("%d %B %Y, %H:%M"), key=f"{kp_io}_date")
            ext_io       = st.text_area("Ek bilgi:", height=60, key=f"{kp_io}_ext")
            if st.button(f"✨ {title_io} Üret", key=f"{kp_io}_gen"):
                pr_io = (f"{sys_pr_io}\nProgram: {prog_name_io}\nTarih: {dstr_io}\n"
                         f"{'Ek: '+ext_io if ext_io else ''}\nSADECE düz Türkçe.")
                with st.spinner("..."):
                    txt_io = groq_gen(pr_io, char_id=A_CHAR, model_key=groq_mkey, max_tok=200)
                st.session_state[f"{kp_io}_txt"] = txt_io; st.rerun()
            txt_io2 = st.text_area("Metin:", value=st.session_state.get(f"{kp_io}_txt", ""),
                                   height=145, key=f"{kp_io}_ta")
            if txt_io2 != st.session_state.get(f"{kp_io}_txt", ""): st.session_state[f"{kp_io}_txt"] = txt_io2
            if txt_io2.strip():
                ff_io = list_audio(FON_DIR); jf_io = list_audio(JINGLE_DIR)
                wj_io = st.checkbox("Jingle ile", key=f"{kp_io}_wj")
                wf_io = st.checkbox("Fon ile", key=f"{kp_io}_wf")
                js_io = st.selectbox("Jingle:", jf_io, key=f"{kp_io}_js") if (wj_io and jf_io) else None
                fs_io = st.selectbox("Fon:", ff_io, key=f"{kp_io}_fs") if (wf_io and ff_io) else None
                io_voice_sel = st.selectbox("Ses:", list(VOICES.keys()),
                                             format_func=lambda x: f"{VOICES[x][0]} {x}", key=f"{kp_io}_voice")
                if st.button(f"🔊 {title_io} Seslendir", key=f"{kp_io}_vb", type="primary"):
                    ak_io, ai_io = get_active_key()
                    if not ak_io: st.error("API yok!")
                    else:
                        with st.spinner("🎙️ Gemini TTS..."):
                            try:
                                raw_io = tts_single(ak_io, sel_model, txt_io2, io_voice_sel, "tr-TR", "")
                                wav_io = pcm2wav(raw_io)
                                consume(ai_io, len(txt_io2))
                                archive_add(io_voice_sel, sel_model, "tr-TR", "", txt_io2, wav_io, kp_io)
                                final_io = wav_io
                                if wf_io and fs_io and PYDUB_OK:
                                    vseg_io = AudioSegment(raw_io, frame_rate=24000, sample_width=2, channels=1)
                                    fonseg_io = AudioSegment.from_file(os.path.join(FON_DIR, fs_io))
                                    mixed_io = mix_fon_voice(fonseg_io, vseg_io)
                                    out_io = os.path.join(OUT_DIR, f"{kp_io}_fon_{ts_str()}.wav")
                                    normalize_seg(mixed_io).export(out_io, "wav")
                                    with open(out_io, "rb") as f: final_io = f.read()
                                elif wj_io and js_io and PYDUB_OK:
                                    vseg_io = AudioSegment(raw_io, frame_rate=24000, sample_width=2, channels=1)
                                    jgl_io  = AudioSegment.from_file(os.path.join(JINGLE_DIR, js_io))
                                    mixed_io = apply_ducking(jgl_io, vseg_io)
                                    out_io = os.path.join(OUT_DIR, f"{kp_io}_jgl_{ts_str()}.wav")
                                    normalize_seg(mixed_io).export(out_io, "wav")
                                    with open(out_io, "rb") as f: final_io = f.read()
                                st.success("✅"); st.audio(final_io, format="audio/wav")
                                st.session_state[f"{kp_io}_path"] = final_io
                            except Exception as e: st.error(f"❌ {e}")
                if st.session_state.get(f"{kp_io}_path"):
                    st.download_button("💾 WAV", st.session_state[f"{kp_io}_path"],
                                       f"{kp_io}_{ts_str()}.wav", "audio/wav", key=f"{kp_io}_dl")

    io_tab_fn(ti_tab, "Giriş",   "Enerjik çekici program açılış (~30 sn).", "intro")
    io_tab_fn(to_tab, "Kapanış", "Sıcak nostaljik program kapanış (~25 sn).", "outro")


# ══════════════════════════════════════════════════════════════════════════════
# M11 — SES EDİTÖRÜ
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "✂️ Ses Editörü":
    page_header("✂️", "Ses Editörü", "Kırp · Birleştir · Jingle Üret")
    tab_trim, tab_concat, tab_jingle = st.tabs(["✂️ Kırp", "🔗 Birleştir", "🎵 Jingle Üret"])

    with tab_trim:
        trim_up = st.file_uploader("Kırpılacak ses:", type=["mp3", "wav", "ogg", "flac"], key="trim_up")
        if trim_up and PYDUB_OK:
            saved_trim = save_uploaded_file(trim_up, UPLOAD_DIR, f"trim_{ts_str()}.wav")
            if saved_trim:
                seg_trim = AudioSegment.from_file(saved_trim); dur_trim = len(seg_trim) / 1000
                st.audio(saved_trim)
                st.markdown(f'<div class="mono-box">⏱ {fmt_dur(dur_trim)} | {seg_trim.dBFS:.1f}dBFS</div>', unsafe_allow_html=True)
                draw_waveform(saved_trim, 1.8)
                tc1, tc2 = st.columns(2)
                with tc1: start_s = st.slider("Başlangıç (sn):", 0.0, dur_trim, 0.0, 0.1, key="trim_start")
                with tc2: end_s   = st.slider("Bitiş (sn):", 0.0, dur_trim, dur_trim, 0.1, key="trim_end")
                if st.button("✂️ Kırp", key="trim_btn", type="primary"):
                    if start_s < end_s:
                        trimmed = seg_trim[int(start_s * 1000):int(end_s * 1000)]
                        out_trim = os.path.join(OUT_DIR, f"trimmed_{ts_str()}.wav")
                        trimmed.export(out_trim, "wav")
                        st.success(f"✅ {fmt_dur(end_s - start_s)}")
                        st.audio(out_trim)
                        with open(out_trim, "rb") as fh:
                            st.download_button("⬇️ İndir", fh, os.path.basename(out_trim), key="trim_dl")

    with tab_concat:
        concat_sel = st.multiselect("Birleştirilecek dosyalar:", list_audio(OUT_DIR), key="concat_sel")
        concat_gap = st.slider("Aralarındaki boşluk (ms):", 0, 3000, 500)
        if concat_sel and PYDUB_OK and st.button("🔗 Birleştir", key="concat_btn", type="primary"):
            segs = []
            for f_c in concat_sel:
                try: segs.append(AudioSegment.from_file(os.path.join(OUT_DIR, f_c)))
                except Exception: pass
            if segs:
                result_c = segs[0]
                for s in segs[1:]: result_c = result_c + AudioSegment.silent(concat_gap) + s
                out_c = os.path.join(OUT_DIR, f"concat_{ts_str()}.wav")
                normalize_seg(result_c).export(out_c, "wav")
                st.success("✅"); st.audio(out_c); draw_waveform(out_c)
                with open(out_c, "rb") as fh:
                    st.download_button("⬇️ WAV", fh, os.path.basename(out_c), key="concat_dl")

    with tab_jingle:
        jg1, jg2 = st.columns(2)
        with jg1:
            jgl_freq  = st.slider("Frekans (Hz):", 200, 1200, 440, key="jgl_freq")
            jgl_dur   = st.slider("Süre (ms):", 500, 5000, 2000, key="jgl_dur")
        with jg2:
            jgl_style = st.selectbox("Stil:", ["sine", "square", "sawtooth"], key="jgl_style")
            jgl_name  = st.text_input("İsim:", value=f"jingle_{ts_str()}", key="jgl_name")
        if st.button("🎵 Jingle Üret", key="jgl_btn", type="primary") and PYDUB_OK:
            jgl = generate_jingle(jgl_freq, jgl_dur, jgl_style)
            if jgl:
                out_jgl = os.path.join(JINGLE_DIR, f"{sfn(jgl_name)}.wav")
                jgl.export(out_jgl, "wav")
                st.success("✅"); st.audio(out_jgl)
                with open(out_jgl, "rb") as fh:
                    st.download_button("⬇️ WAV", fh, os.path.basename(out_jgl), key="jgl_dl")


# ══════════════════════════════════════════════════════════════════════════════
# M12 — A/B TEST
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "🔄 A/B Test":
    page_header("🔄", "A/B Test", "İki farklı ses/stil karşılaştırma")
    ab_txt_shared = st.text_area("Ortak Metin:", value=st.session_state.get("_t_ab1", "[excitedly] İmaj FM'e hoş geldiniz!"),
                                  height=100, key="ab_shared")
    ab1, ab2 = st.columns(2)
    with ab1:
        st.markdown("<span class='sl'>▸ VERSİYON A</span>", unsafe_allow_html=True)
        ab_v_a   = st.selectbox("Ses A:", list(VOICES.keys()), format_func=lambda x: f"{VOICES[x][0]} {x}", key="ab_va")
        ab_s_a   = st.text_area("Stil A:", height=55, key="ab_sa", placeholder="Coşkulu oku...")
        ab_m_a   = st.selectbox("Model A:", list(MODELS.keys()), format_func=lambda x: MODELS[x], key="ab_ma")
        if st.button("🔴 A Seslendir", key="ab_go_a", type="primary", use_container_width=True):
            ak_a, ai_a = get_active_key()
            if ak_a:
                with st.spinner("A..."):
                    try:
                        raw_a = tts_single(ak_a, ab_m_a, ab_txt_shared, ab_v_a, "tr-TR", ab_s_a)
                        wav_a = pcm2wav(raw_a)
                        consume(ai_a, len(ab_txt_shared))
                        archive_add(ab_v_a, ab_m_a, "tr-TR", ab_s_a, ab_txt_shared, wav_a, "ab-A")
                        st.session_state["_ab_wav_a"] = wav_a; st.rerun()
                    except Exception as e: st.error(f"❌ {e}")
        if st.session_state.get("_ab_wav_a"):
            st.audio(st.session_state["_ab_wav_a"], format="audio/wav")
            st.download_button("💾 A", st.session_state["_ab_wav_a"], f"ab_A_{ts_str()}.wav", "audio/wav", key="ab_dl_a")

    with ab2:
        st.markdown("<span class='sl'>▸ VERSİYON B</span>", unsafe_allow_html=True)
        ab_v_b   = st.selectbox("Ses B:", list(VOICES.keys()), format_func=lambda x: f"{VOICES[x][0]} {x}", key="ab_vb", index=1)
        ab_s_b   = st.text_area("Stil B:", height=55, key="ab_sb", placeholder="Ciddi oku...")
        ab_m_b   = st.selectbox("Model B:", list(MODELS.keys()), format_func=lambda x: MODELS[x], key="ab_mb")
        if st.button("🔴 B Seslendir", key="ab_go_b", type="primary", use_container_width=True):
            ak_b2, ai_b2 = get_active_key()
            if ak_b2:
                with st.spinner("B..."):
                    try:
                        raw_b = tts_single(ak_b2, ab_m_b, ab_txt_shared, ab_v_b, "tr-TR", ab_s_b)
                        wav_b = pcm2wav(raw_b)
                        consume(ai_b2, len(ab_txt_shared))
                        archive_add(ab_v_b, ab_m_b, "tr-TR", ab_s_b, ab_txt_shared, wav_b, "ab-B")
                        st.session_state["_ab_wav_b"] = wav_b; st.rerun()
                    except Exception as e: st.error(f"❌ {e}")
        if st.session_state.get("_ab_wav_b"):
            st.audio(st.session_state["_ab_wav_b"], format="audio/wav")
            st.download_button("💾 B", st.session_state["_ab_wav_b"], f"ab_B_{ts_str()}.wav", "audio/wav", key="ab_dl_b")


# ══════════════════════════════════════════════════════════════════════════════
# M13 — STREAM YAYIN
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "📡 Stream Yayın":
    page_header("📡", "Stream Yayın", "M3U · HTML Player · Liquidsoap")
    tab_s1, tab_s2, tab_s3 = st.tabs(["📡 Stream Link", "📻 Yayın Akışı", "🔗 Icecast"])

    with tab_s1:
        out_files_s = list_audio(OUT_DIR); arc_files_s = list_audio(ARCHIVE_DIR)
        all_s = out_files_s + [f"[ARŞİV] {f}" for f in arc_files_s]
        sf_path_s = None
        if all_s:
            sel_s = st.selectbox("Dosya:", all_s, key="st_sel")
            real_nm_s = sel_s.replace("[ARŞİV] ", "")
            real_dir_s = ARCHIVE_DIR if sel_s.startswith("[ARŞİV]") else OUT_DIR
            sf_path_s = os.path.join(real_dir_s, real_nm_s)
            if os.path.exists(sf_path_s):
                st.audio(sf_path_s)
                st.markdown(f'<div class="mono-box">📁 {real_nm_s} | ⏱ {fmt_dur(audio_dur(sf_path_s))} | 💾 {os.path.getsize(sf_path_s)//1024}KB</div>', unsafe_allow_html=True)
        sc1_s, sc2_s = st.columns(2)
        with sc1_s:
            stream_port  = int(st.number_input("Port:", 1024, 65535, 8765, key="st_port"))
            stream_title = st.text_input("Yayın Adı:", value="İmaj FM Hybrid Reji", key="st_title")
        if st.button("📡 Stream Link Üret", key="st_start"):
            local_ip_s  = get_local_ip()
            stream_url  = f"http://{local_ip_s}:{stream_port}/stream"
            html_p_s = os.path.join(STREAM_DIR, "player.html")
            with open(html_p_s, "w", encoding="utf-8") as f:
                f.write(f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{stream_title}</title>
<style>body{{background:#07090f;font-family:Inter,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}}
.p{{background:#0b0f1a;border:1px solid #131c2e;border-radius:14px;padding:36px;text-align:center;max-width:380px}}
h1{{background:linear-gradient(90deg,#fff,#ff6060);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:1.3em;margin-bottom:14px}}
audio{{width:100%;margin:14px 0;border-radius:9px}}
.dot{{display:inline-block;width:7px;height:7px;border-radius:50%;background:#dc2626;margin-right:5px;animation:b 1.1s infinite}}
@keyframes b{{0%,100%{{opacity:1}}50%{{opacity:.2}}}}</style></head><body>
<div class="p"><h1>🎙️ {stream_title}</h1><div style="font-size:13px;color:#6b7a8d"><span class="dot"></span>İmaj FM Hybrid Reji</div>
<audio controls autoplay loop><source src="{stream_url}" type="audio/mpeg"><source src="{stream_url}" type="audio/wav"></audio>
<p style="font-size:11px;color:#2e3f55">{datetime.now().strftime("%H:%M")}</p></div></body></html>""")
            m3u_p_s = os.path.join(STREAM_DIR, "stream.m3u")
            with open(m3u_p_s, "w") as f: f.write(f"#EXTM3U\n#EXTINF:-1,{stream_title}\n{stream_url}\n")
            st.session_state.update({"stream_url": stream_url, "stream_active": True, "stream_file": sf_path_s})
            st.rerun()

        if st.session_state.get("stream_active") and st.session_state.get("stream_url"):
            url_s = st.session_state["stream_url"]
            st.markdown(f'<div class="stream-box"><div class="live-badge" style="margin-bottom:10px"><span class="live-dot"></span>YAYIN AKTİF</div><br>🔗 <b>URL:</b><br>{url_s}</div>', unsafe_allow_html=True)
            cc1_s, cc2_s, cc3_s = st.columns(3)
            with cc1_s:
                m3u_p2 = os.path.join(STREAM_DIR, "stream.m3u")
                if os.path.exists(m3u_p2):
                    with open(m3u_p2) as f: m_s = f.read()
                    st.download_button("⬇️ .m3u", m_s.encode(), "stream.m3u", "audio/x-mpegurl", key="dl_m3u")
            with cc2_s:
                html_p2 = os.path.join(STREAM_DIR, "player.html")
                if os.path.exists(html_p2):
                    with open(html_p2, encoding="utf-8") as f: h_s = f.read()
                    st.download_button("⬇️ HTML Player", h_s.encode(), "player.html", "text/html", key="dl_html")
            with cc3_s:
                if st.button("⏹ Durdur", key="st_stop"):
                    st.session_state.update({"stream_active": False, "stream_url": None}); st.rerun()
            sf2_s = st.session_state.get("stream_file")
            if sf2_s and os.path.exists(sf2_s):
                section("🎧 Sayfa İçi Oynatıcı"); st.audio(sf2_s, autoplay=True)

    with tab_s2:
        songs_ps = list_audio(PLAYLIST_DIR)
        if songs_ps and PYDUB_OK:
            ps_sel  = st.multiselect("Şarkılar:", songs_ps, default=songs_ps[:3], key="ps_sel")
            ps_name = st.text_input("Ad:", value=f"Stream_{ts_str()}", key="ps_name")
            ps_jgl  = st.selectbox("Jingle:", ["Yok"] + list_audio(JINGLE_DIR), key="ps_jgl")
            ps_fon  = st.selectbox("Fon:", ["Yok"] + list_audio(FON_DIR), key="ps_fon")
            if st.button("📻 Yayın Akışı Oluştur", key="ps_build", type="primary") and ps_sel:
                with st.status("Oluşturuluyor...", expanded=True) as stat_ps:
                    master_ps = AudioSegment.silent(1000)
                    if ps_jgl != "Yok":
                        jp_ps = os.path.join(JINGLE_DIR, ps_jgl)
                        if os.path.exists(jp_ps): master_ps += AudioSegment.from_file(jp_ps)
                    for i, f_ps in enumerate(ps_sel):
                        sp_ps = os.path.join(PLAYLIST_DIR, f_ps)
                        try:
                            sseg_ps = AudioSegment.from_file(sp_ps)
                            if ps_fon != "Yok":
                                fp2_ps = os.path.join(FON_DIR, ps_fon)
                                if os.path.exists(fp2_ps):
                                    fon2_ps = AudioSegment.from_file(fp2_ps)
                                    bridge_ps = fon2_ps[:5000].fade_in(400).fade_out(400) if len(fon2_ps) >= 5000 else fon2_ps
                                    master_ps = master_ps.append(bridge_ps, crossfade=400)
                            master_ps = master_ps.append(sseg_ps, crossfade=1200)
                            st.write(f"✅ [{i+1}] {f_ps}")
                        except Exception as e: st.warning(f"{f_ps}: {e}")
                    master_ps = normalize_seg(master_ps)
                    out_p_ps  = os.path.join(OUT_DIR, f"{sfn(ps_name)}.wav")
                    master_ps.export(out_p_ps, "wav")
                    final_ps  = do_export(out_p_ps, exp_fmt) if exp_fmt != "wav" else out_p_ps
                    shutil.copy2(final_ps, os.path.join(ARCHIVE_DIR, os.path.basename(final_ps)))
                    stat_ps.update(label="✅ Hazır!", state="complete")
                st.success(f"🎉 {ps_name}"); st.audio(final_ps)
                with open(final_ps, "rb") as fh:
                    st.download_button(f"⬇️ (.{exp_fmt})", fh, os.path.basename(final_ps), mime=f"audio/{exp_fmt}")

    with tab_s3:
        section("🔗 Icecast / Liquidsoap")
        ic1_s, ic2_s = st.columns(2)
        with ic1_s:
            ic_host  = st.text_input("Host:", value="localhost", key="ic_host")
            ic_port  = st.number_input("Port:", value=8000, key="ic_port")
            ic_mount = st.text_input("Mount:", value="/stream", key="ic_mount")
        with ic2_s:
            ic_pass = st.text_input("Şifre:", type="password", key="ic_pass")
            ic_name = st.text_input("Yayın Adı:", value="İmaj FM Hybrid", key="ic_name")
        if st.button("📋 Liquidsoap Script", key="ic_gen"):
            ls_script = (f"#!/usr/bin/liquidsoap\n# İmaj FM Hybrid Reji · {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
                         f"set(\"log.level\",3)\n"
                         f"playlist = playlist(reload=1,mode=\"randomize\",\"{PLAYLIST_DIR}\")\n"
                         f"output.icecast(%mp3(bitrate=192),host=\"{ic_host}\",port={int(ic_port)},\n"
                         f"  password=\"{ic_pass}\",mount=\"{ic_mount}\",name=\"{ic_name}\",playlist)")
            st.code(ls_script, language="bash")
            st.download_button("⬇️ stream.liq", ls_script.encode(), "stream.liq", "text/plain", key="dl_liq")


# ══════════════════════════════════════════════════════════════════════════════
# M14 — PROGRAM PLANLAYICI
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "📅 Program Planlayıcı":
    page_header("📅", "Program Planlayıcı", "Haftalık yayın takvimi ve program şablonları")
    pp1, pp2 = st.columns([1.5, 1])
    with pp1:
        section("📅 Haftalık Program")
        DAYS = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        SLOTS = ["06:00-09:00 Sabah", "09:00-12:00 Öğle Öncesi", "12:00-14:00 Öğle",
                 "14:00-17:00 İkindi", "17:00-20:00 Akşam", "20:00-23:00 Gece", "23:00-02:00 Gece Yarısı"]
        sched_day  = st.selectbox("Gün:", DAYS, key="sched_day")
        sched_slot = st.selectbox("Kuşak:", SLOTS, key="sched_slot")
        sched_prog = st.text_input("Program Adı:", key="sched_prog")
        sched_host = st.text_input("Sunucu:", key="sched_host")
        sched_note = st.text_area("Not:", height=60, key="sched_note")
        if st.button("💾 Programa Ekle", key="sched_save"):
            sched_file = os.path.join(SCHEDULE_DIR, f"{sfn(sched_day)}.json")
            sched = {}
            if os.path.exists(sched_file):
                try:
                    with open(sched_file) as f: sched = json.load(f)
                except Exception: pass
            sched[sched_slot] = {"program": sched_prog, "host": sched_host,
                                  "note": sched_note, "updated": datetime.now().isoformat()}
            with open(sched_file, "w", encoding="utf-8") as f: json.dump(sched, f, ensure_ascii=False, indent=2)
            st.success(f"✅ {sched_day} — {sched_slot} kaydedildi!")

    with pp2:
        section("📋 Mevcut Program")
        sched_view = st.selectbox("Gün:", DAYS, key="sched_view")
        sched_file_v = os.path.join(SCHEDULE_DIR, f"{sfn(sched_view)}.json")
        if os.path.exists(sched_file_v):
            try:
                with open(sched_file_v) as f: sched_v = json.load(f)
                for slot_v, info_v in sched_v.items():
                    st.markdown(
                        f'<div class="kcard kcard-l"><div class="kcard-title">⏰ {slot_v}</div>'
                        f'<div class="kcard-body">{info_v.get("program","—")} · {info_v.get("host","—")}<br>'
                        f'{info_v.get("note","")}</div></div>',
                        unsafe_allow_html=True)
            except Exception: st.info("Program dosyası okunamadı.")
        else:
            st.info("Bu gün için program girilmemiş.")


# ══════════════════════════════════════════════════════════════════════════════
# M15 — ANALİTİKLER
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "📊 Analitikler":
    page_header("📊", "Analitikler", "Oturum ve yayın istatistikleri")
    stat_a = st.session_state._api_stats
    arc_a  = st.session_state._archive

    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    with sc1: st.markdown(f'<div class="mbox b"><div class="v">{len(arc_a)}</div><div class="l">Toplam Kayıt</div></div>', unsafe_allow_html=True)
    with sc2: st.markdown(f'<div class="mbox g"><div class="v">{stat_a["total_calls"]}</div><div class="l">API Çağrısı</div></div>', unsafe_allow_html=True)
    with sc3: st.markdown(f'<div class="mbox a"><div class="v">{stat_a["total_secs"]:.0f}s</div><div class="l">Üretilen Ses</div></div>', unsafe_allow_html=True)
    with sc4: st.markdown(f'<div class="mbox p"><div class="v">{stat_a["total_chars"]:,}</div><div class="l">İşlenen Karakter</div></div>', unsafe_allow_html=True)
    with sc5:
        total_mb_a = sum(e["size"] for e in arc_a) / (1024 * 1024)
        st.markdown(f'<div class="mbox"><div class="v">{total_mb_a:.1f}MB</div><div class="l">Arşiv Boyutu</div></div>', unsafe_allow_html=True)

    st.divider()
    if arc_a and NP_OK:
        voices_used = {}
        for e in arc_a:
            voices_used[e["voice"]] = voices_used.get(e["voice"], 0) + 1
        section("🎙️ En Çok Kullanılan Sesler")
        for v_name, v_cnt in sorted(voices_used.items(), key=lambda x: -x[1])[:8]:
            pct = v_cnt / len(arc_a)
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0;">'
                f'<span style="width:100px;font-size:.75rem;color:#dde2ee;">{VOICES.get(v_name,("",""))[0]} {v_name}</span>'
                f'<div class="qbar" style="flex:1;"><div class="qbar-f" style="width:{pct*100:.0f}%;background:#e05252;"></div></div>'
                f'<span style="width:30px;text-align:right;font-size:.7rem;color:#6b7a8d;">{v_cnt}</span>'
                f'</div>', unsafe_allow_html=True)

    st.divider()
    # Analitik log dosyaları
    log_files = [f for f in os.listdir(ANALYTICS_DIR) if f.startswith("log_") and f.endswith(".json")]
    if log_files:
        section("📋 Olay Logları")
        latest_log = sorted(log_files)[-1]
        with open(os.path.join(ANALYTICS_DIR, latest_log)) as f:
            logs_data = json.load(f)
        for log_entry in logs_data[-10:]:
            st.markdown(f"<div style='font-size:.7rem;color:#3d4f68;padding:2px 0;border-bottom:1px solid #0d1420;'>{log_entry['ts'][11:16]} · <b style='color:#60a5fa;'>{log_entry['event']}</b> · {str(log_entry)[:60]}</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# M16 — KÜTÜPHANE
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "📁 Kütüphane":
    page_header("📁", "Kütüphane", "Şarkı · Fon · Jingle · Efekt yönetimi")
    lt1, lt2, lt3, lt4 = st.tabs(["🎵 Playlist", "🎶 Fon", "🎵 Jingle", "🎭 Efektler"])

    def lib_panel_fn(dir_p, tab_lib, kp_lib, desc=""):
        with tab_lib:
            if desc: st.markdown(f'<div class="info-box">ℹ️ {desc}</div>', unsafe_allow_html=True)
            up_lib = st.file_uploader("Dosya yükle:", type=["mp3", "wav", "ogg", "flac", "m4a"],
                                       accept_multiple_files=True, key=f"up_{kp_lib}")
            if up_lib:
                cnt_lib = 0
                for uf_lib in up_lib:
                    sv_lib = save_uploaded_file(uf_lib, dir_p, uf_lib.name)
                    if sv_lib: cnt_lib += 1
                if cnt_lib: st.success(f"✅ {cnt_lib} dosya yüklendi!"); st.rerun()
            files_lib = list_audio(dir_p)
            st.markdown(chip_html(f"{len(files_lib)} dosya", "blue"), unsafe_allow_html=True)
            for f_lib in files_lib:
                fp_lib = os.path.join(dir_p, f_lib)
                dur_lib = audio_dur(fp_lib)
                tags_lib = get_id3(fp_lib)
                art_lib = (f' {chip_html(tags_lib["artist"][:16],"purple")}' if tags_lib.get("artist") else "")
                cc_lib = st.columns([3, 1, 1])
                with cc_lib[0]:
                    st.markdown(
                        f'<div class="song-row"><span class="song-nm">🎵 {f_lib[:38]}</span>'
                        f'{art_lib}<span class="song-dur">{fmt_dur(dur_lib)}</span></div>',
                        unsafe_allow_html=True)
                with cc_lib[1]: st.audio(fp_lib)
                with cc_lib[2]:
                    if st.button("🗑️", key=f"dl_{kp_lib}_{f_lib}", help="Sil"):
                        os.remove(fp_lib); st.rerun()

    lib_panel_fn(PLAYLIST_DIR, lt1, "songs")
    lib_panel_fn(FON_DIR, lt2, "fon", "Enstrümental background müzikler. Anons sırasında otomatik alçalır.")
    lib_panel_fn(JINGLE_DIR, lt3, "jingles")
    lib_panel_fn(EFFECT_DIR, lt4, "effects", "Alkış, gülme, kapı, ambians efektleri.")


# ══════════════════════════════════════════════════════════════════════════════
# M17 — ARŞİV & İSTATİSTİK
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "📻 Arşiv & İstatistik":
    page_header("📻", "Arşiv & İstatistik", "Oturum ses arşivi + Üretilen dosyalar")
    at1, at2, at3 = st.tabs(["🎙️ Oturum Arşivi", "📂 Üretilen Dosyalar", "⭐ Favoriler"])

    with at1:
        arc = st.session_state._archive
        stat_arc = st.session_state._api_stats
        si1, si2, si3, si4, si5 = st.columns(5)
        with si1: st.markdown(f'<div class="mbox b"><div class="v">{len(arc)}</div><div class="l">Toplam Kayıt</div></div>', unsafe_allow_html=True)
        with si2: st.markdown(f'<div class="mbox g"><div class="v">{stat_arc["total_calls"]}</div><div class="l">API Çağrısı</div></div>', unsafe_allow_html=True)
        with si3: st.markdown(f'<div class="mbox a"><div class="v">{stat_arc["total_secs"]:.0f}s</div><div class="l">Üretilen Ses</div></div>', unsafe_allow_html=True)
        with si4: st.markdown(f'<div class="mbox p"><div class="v">{stat_arc["total_chars"]:,}</div><div class="l">Karakter</div></div>', unsafe_allow_html=True)
        with si5:
            total_mb_arc = sum(e["size"] for e in arc) / (1024 * 1024)
            st.markdown(f'<div class="mbox"><div class="v">{total_mb_arc:.1f}MB</div><div class="l">Arşiv</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if not arc:
            st.markdown("<div style='text-align:center;padding:50px;color:#2e3f55;'><div style='font-size:2rem;'>📂</div><div style='font-family:Syne,sans-serif;font-size:.95rem;font-weight:700;margin-top:8px;'>Arşiv Boş</div></div>", unsafe_allow_html=True)
        else:
            ah1, ah2, ah3 = st.columns([2, 1, 1])
            with ah1: st.markdown(f"<span class='sl'>▶ {len(arc)} Kayıt</span>", unsafe_allow_html=True)
            with ah2:
                if st.button("📦 Tümünü ZIP", use_container_width=True, key="arc_zip"):
                    zba = io.BytesIO()
                    with zipfile.ZipFile(zba, "w", zipfile.ZIP_DEFLATED) as za:
                        for h_arc in arc:
                            fn_arc = f"{h_arc['ts_short'].replace(':','-').replace(' ','_')}_{h_arc['voice']}_{h_arc['id']}.wav"
                            za.writestr(fn_arc, h_arc["wav"])
                    st.download_button("💾 ZIP İndir", zba.getvalue(), "imajfm_arsiv.zip", "application/zip", key="arc_zip_dl")
            with ah3:
                if st.button("🗑️ Tümünü Sil", use_container_width=True, key="arc_clr"):
                    st.session_state._archive = []
                    st.session_state._api_stats = {"total_calls": 0, "total_chars": 0, "total_secs": 0.0}
                    st.rerun()

            # Filtre
            af1, af2 = st.columns([2, 1])
            with af1:
                arc_search = st.text_input("Ara", "", placeholder="🔍 Ses, metin veya model ara…", label_visibility="collapsed", key="arc_search")
            with af2:
                arc_mode = st.selectbox("Mod", ["Tümü", "tek", "cift", "fon_anons", "yayin", "bulk", "karakter", "haber", "manuel", "ab-A", "ab-B"],
                                         label_visibility="collapsed", key="arc_mode")
            filtered_arc = arc
            if arc_search.strip():
                q_arc = arc_search.lower()
                filtered_arc = [h for h in filtered_arc if q_arc in h["voice"].lower() or q_arc in h["text"].lower() or q_arc in h["model"].lower()]
            if arc_mode != "Tümü":
                filtered_arc = [h for h in filtered_arc if h.get("mode", "") == arc_mode]

            st.markdown(f"<div style='font-size:.68rem;color:#2e3f55;margin:4px 0 10px;'>{len(filtered_arc)} kayıt gösteriliyor</div>", unsafe_allow_html=True)
            gcols = st.columns(3)
            for gi, h_arc2 in enumerate(filtered_arc):
                with gcols[gi % 3]:
                    mode_bc = {"tek": "#3b82f6", "cift": "#a78bfa", "fon_anons": "#22d3ee",
                               "yayin": "#f59e0b", "bulk": "#22c55e", "ab-A": "#a78bfa",
                               "ab-B": "#fb923c", "karakter": "#e05252"}.get(h_arc2.get("mode", "tek"), "#3b82f6")
                    st.markdown(f"""
                    <div class='arc-card'>
                        <div class='arc-meta'>
                            <span class='arc-voice'>{VOICES.get(h_arc2["voice"],("?",""))[0]} {h_arc2["voice"]}</span>
                            <span class='arc-ts'>{h_arc2["ts_short"]}</span>
                        </div>
                        <div class='arc-info'>
                            <span style='color:{mode_bc};background:{mode_bc}18;border-radius:4px;padding:1px 6px;font-size:.62rem;font-weight:700;'>{h_arc2.get("mode","tek").upper()}</span>
                            &nbsp;{h_arc2["model_short"]} · {h_arc2["lang"]} · {h_arc2["dur"]}s · {h_arc2["size"]//1024}KB
                        </div>
                        <div class='arc-text'>{h_arc2["preview"]}</div>
                    </div>""", unsafe_allow_html=True)
                    st.audio(h_arc2["wav"], format="audio/wav")
                    dca, dcb = st.columns(2)
                    with dca:
                        st.download_button("💾 WAV", h_arc2["wav"],
                                           file_name=f"imajfm_{h_arc2['voice'].lower()}_{h_arc2['id']}.wav",
                                           mime="audio/wav", use_container_width=True, key=f"arc_dl_{h_arc2['id']}")
                    with dcb:
                        if st.button("⭐", key=f"arc_fav_{h_arc2['id']}", help="Favorilere ekle", use_container_width=True):
                            st.session_state._favorites.append({
                                "id": h_arc2["id"], "name": h_arc2["voice"] + " " + h_arc2["ts_short"],
                                "text": h_arc2["text"], "voice": h_arc2["voice"],
                                "model": h_arc2["model"], "lang": h_arc2["lang"],
                            }); st.rerun()

    with at2:
        files_out = sorted(list_audio(OUT_DIR), reverse=True)
        files_arc2 = sorted(list_audio(ARCHIVE_DIR), reverse=True)
        srch_out = st.text_input("🔍 Ara:", key="out_srch")
        filtered_out = [f for f in files_out if srch_out.lower() in f.lower()] if srch_out else files_out
        st.markdown(chip_html(f"{len(filtered_out)} dosya", "blue"), unsafe_allow_html=True)
        if filtered_out and st.button("⬇️ Hepsini ZIP", key="out_zip"):
            all_out_paths = [os.path.join(OUT_DIR, f) for f in filtered_out[:30]]
            zdata_out = zip_files(all_out_paths, "broadcast_output")
            if zdata_out:
                st.download_button("⬇️ ZIP", zdata_out, "broadcast_output.zip", "application/zip", key="out_zip_dl")
        for f_out in filtered_out[:40]:
            fp_out = os.path.join(OUT_DIR, f_out); dur_out = audio_dur(fp_out); sz_out = os.path.getsize(fp_out) // 1024
            with st.expander(f"🔊 {f_out[:46]} | {fmt_dur(dur_out)} | {sz_out}KB"):
                st.audio(fp_out); draw_waveform(fp_out, 1.4)
                ac1, ac2, ac3, ac4 = st.columns(4)
                with ac1:
                    with open(fp_out, "rb") as fh:
                        st.download_button("⬇️ WAV", fh, f_out, "audio/wav", key=f"dw_out_{f_out}")
                with ac2:
                    if PYDUB_OK and st.button("→ MP3", key=f"2mp3_out_{f_out}"):
                        mp3_out = do_export(fp_out, "mp3")
                        with open(mp3_out, "rb") as fh:
                            st.download_button("⬇️ MP3", fh, os.path.basename(mp3_out), key=f"dm_out_{f_out}")
                with ac3:
                    if st.button("🗄️ Arşivle", key=f"arc_out_{f_out}"):
                        shutil.copy2(fp_out, os.path.join(ARCHIVE_DIR, f_out)); st.success("✅")
                with ac4:
                    if st.button("🗑️ Sil", key=f"del_out_{f_out}"):
                        os.remove(fp_out); st.rerun()

    with at3:
        favs = st.session_state._favorites
        if not favs:
            st.markdown("<div style='text-align:center;padding:40px;color:#2e3f55;'>⭐ Henüz favori yok.</div>", unsafe_allow_html=True)
        else:
            for fi, fv in enumerate(favs):
                fc1, fc2, fc3, fc4 = st.columns([3, 1, 1, 0.5])
                with fc1:
                    st.markdown(f"""
                    <div class='fav-card'>
                        <div class='fav-name'>⭐ {fv['name']}</div>
                        <div class='fav-prev'>{fv.get('voice','—')} · {fv.get('lang','—')}</div>
                        <div class='fav-prev' style='margin-top:3px;'>{fv['text'][:70]}</div>
                    </div>""", unsafe_allow_html=True)
                with fc2:
                    if st.button("📋 Kopyala", key=f"fcp_{fi}", use_container_width=True):
                        st.session_state["_t_tek"] = fv["text"]; st.rerun()
                with fc3:
                    if st.button("🔴 Seslendir", key=f"fsp_{fi}", use_container_width=True):
                        ak_fav, ai_fav = get_active_key()
                        if ak_fav:
                            with st.spinner("..."):
                                try:
                                    raw_fav = tts_single(ak_fav, fv.get("model", sel_model), fv["text"],
                                                          fv.get("voice", "Kore"), fv.get("lang", "tr-TR"), "")
                                    wav_fav = pcm2wav(raw_fav)
                                    consume(ai_fav, len(fv["text"]))
                                    archive_add(fv.get("voice", "Kore"), fv.get("model", ""), fv.get("lang", ""), "", fv["text"], wav_fav, "fav")
                                    st.session_state[f"_fwav_{fi}"] = wav_fav; st.rerun()
                                except Exception as e: st.error(f"❌ {e}")
                with fc4:
                    if st.button("🗑️", key=f"fdel_{fi}", use_container_width=True):
                        st.session_state._favorites.pop(fi); st.rerun()
                if f"_fwav_{fi}" in st.session_state:
                    st.audio(st.session_state[f"_fwav_{fi}"], format="audio/wav")
                    st.download_button("💾", st.session_state[f"_fwav_{fi}"],
                                       file_name=f"fav_{fv['name'].replace(' ','_')}.wav",
                                       mime="audio/wav", key=f"fdl_{fi}")


# ══════════════════════════════════════════════════════════════════════════════
# M18 — AYARLAR
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "⚙️ Ayarlar":
    page_header("⚙️", "Ayarlar", "API bağlantıları · aktif ayarlar · temizlik")
    s1, s2, s3 = st.tabs(["🔑 API & Bağlantı", "📋 Aktif Ayarlar", "🧹 Temizlik"])

    with s1:
        st.markdown(
            '<div class="mono-box"><b>GEMINI_API_KEY_1..10</b> — Google Gemini TTS (ZORUNLU)<br>'
            '<b>GROQ_API_KEY</b>     — Groq LLM + Whisper STT (opsiyonel)<br><br>'
            'secrets.toml formatı:<br>GEMINI_API_KEY_1 = "AIzaSy..."<br>GROQ_API_KEY = "gsk_..."</div>',
            unsafe_allow_html=True)
        st.divider()
        if st.button("🧪 Gemini TTS Test"):
            ak_t, ai_t = get_active_key()
            if not ak_t: st.error("API anahtarı yok!")
            else:
                with st.spinner("Test ediliyor..."):
                    try:
                        raw_t = tts_single(ak_t, "gemini-2.5-flash-tts", "Merhaba! İmaj FM Hybrid Reji test.", "Kore", "tr-TR", "")
                        wav_t = pcm2wav(raw_t)
                        consume(ai_t, 40)
                        st.success("✅ Gemini TTS çalışıyor!")
                        st.audio(wav_t, format="audio/wav")
                    except Exception as e: st.error(f"❌ {e}")
        if st.button("🧪 Groq LLM Test"):
            if not groq_client: st.error("GROQ_API_KEY yok!")
            else:
                with st.spinner("..."):
                    r_t = groq_gen("Merhaba, kısa test.", max_tok=30)
                if not r_t.startswith("⚠️"): st.success(f"✅ {r_t[:60]}")
                else: st.error(r_t)

    with s2:
        st.json({
            "character": A_CHAR,
            "voice": sel_voice,
            "model": sel_model,
            "language": sel_lang,
            "eq": eq_sb,
            "reverb": reverb_sb,
            "normalize_db": norm_sb,
            "groq_model": groq_mkey,
            "export_format": exp_fmt,
            "stt_language": stt_lang,
            "api_pool_loaded": pool_stats()[0],
            "api_pool_remaining": pool_stats()[2],
            "archive_count": len(st.session_state._archive),
        })

    with s3:
        dirs_s3 = [("Üretilen", OUT_DIR), ("Kullanıcı Sesi", UVOICE_DIR),
                   ("Uploads", UPLOAD_DIR), ("Hafıza", MEMORY_DIR),
                   ("Analitik", ANALYTICS_DIR), ("Geçmiş", HISTORY_DIR)]
        cols_s3 = st.columns(len(dirs_s3))
        for col_s3, (lbl_s3, d_s3) in zip(cols_s3, dirs_s3):
            with col_s3:
                cnt_s3 = len(os.listdir(d_s3)) if os.path.isdir(d_s3) else 0
                st.markdown(f'<div class="sbox"><div class="snum">{cnt_s3}</div><div class="slbl">{lbl_s3}</div></div>', unsafe_allow_html=True)
                if st.button("🗑️", key=f"cl_{sfn(d_s3)}"):
                    for f_s3 in os.listdir(d_s3):
                        fp_s3 = os.path.join(d_s3, f_s3)
                        if os.path.isfile(fp_s3):
                            try: os.remove(fp_s3)
                            except Exception: pass
                    st.success("✅"); st.rerun()


# ─── FOOTER ───────────────────────────────────────────────────────────────────
si_footer = " · ".join([
    f"{'✓' if groq_client else '✗'} Groq",
    f"{'✓' if bool(get_active_key()[0]) else '✗'} Gemini TTS",
    f"{'✓' if PYDUB_OK else '✗'} PyDub",
    f"{'✓' if NP_OK else '✗'} Waveform",
    f"{'✓' if MIC_OK else '✗'} Mikrofon",
])
st.markdown(f"""
<div class='footer'>
    İMAJ FM · HYBRID REJİ v1.0 &nbsp;·&nbsp; Google Gemini TTS &nbsp;·&nbsp; 2026<br>
    <span style='font-size:.6rem;'>{si_footer}</span>
</div>
""", unsafe_allow_html=True)


# ─── YARDIMCI: WAV bytes'tan waveform çiz ─────────────────────────────────────
def draw_waveform_bytes(wav_bytes: bytes, h: float = 1.5):
    if not wav_bytes or not NP_OK: return
    try:
        buf_wf = io.BytesIO(wav_bytes)
        with wave.open(buf_wf, 'rb') as wf:
            sr_wf = wf.getframerate(); ch_wf = wf.getnchannels(); sw_wf = wf.getsampwidth()
            frames_wf = wf.readframes(wf.getnframes())
        dt_wf = np.int16 if sw_wf == 2 else np.int8
        s_wf  = np.frombuffer(frames_wf, dtype=dt_wf)
        if ch_wf == 2: s_wf = s_wf[::2]
        step_wf = max(1, len(s_wf) // 2000); ds_wf = s_wf[::step_wf].astype(np.float32)
        mx_wf = np.max(np.abs(ds_wf)) or 1; ds_wf /= mx_wf
        t_wf  = np.linspace(0, len(s_wf) / sr_wf, len(ds_wf))
        fig_wf, ax_wf = plt.subplots(figsize=(10, h), facecolor='#07090f')
        ax_wf.set_facecolor('#07090f')
        ax_wf.fill_between(t_wf, ds_wf, alpha=.65, color='#e05252')
        ax_wf.fill_between(t_wf, -np.abs(ds_wf), alpha=.2, color='#3a7bd5')
        ax_wf.axhline(0, color='#131c2e', lw=.8); ax_wf.set_xlim(0, t_wf[-1]); ax_wf.set_ylim(-1.1, 1.1)
        for sp_wf in ax_wf.spines.values(): sp_wf.set_visible(False)
        ax_wf.tick_params(colors='#2e3f55', labelsize=7)
        plt.tight_layout(pad=.3)
        st.pyplot(fig_wf, use_container_width=True); plt.close(fig_wf)
    except Exception: pass
ENDOFFILE
# Dosyanın satır sayısını Python ile hesaplayıp yazdırma
try:
    with open("/mnt/user-data/outputs/app.py", "r", encoding="utf-8") as f:
        satir_sayisi = len(f.readlines())
    print(f"Done: {satir_sayisi} /mnt/user-data/outputs/app.py lines")
except FileNotFoundError:
    print("Dosya bulunamadı.")
Output

