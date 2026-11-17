"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  İMAJ FM · TTS STÜDYO  v7.1 — TAM ENTEGRE YAYIN SİSTEMİ                   ║
║  Gemini TTS · Delay Reji · Fon+Anons Mikseri · Yayın Otomasyonu            ║
║  Playlist · Toplu TTS · A/B Test · Kütüphane · Arşiv · ZIP                 ║
║  Ses Efektleri & Sinyal · Podcast RSS · Yayın Takvimi · RVC Hazırlık       ║
║  Canlı Metin Akışı · Ses Normalizasyon · Toplu Format Dönüştürücü         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

import streamlit as st
import wave, io, zipfile, re, time, datetime, hashlib, os, json, uuid
from xml.sax.saxutils import escape as xml_escape
from typing import Optional, Dict, List, Tuple

# ─── GOOGLE GEMINI TTS ──────────────────────────────────────────────────────
try:
    from google import genai
    from google.genai import types
    GEMINI_OK = True
except ImportError:
    GEMINI_OK = False

# ─── PYDUB ──────────────────────────────────────────────────────────────────
try:
    from pydub import AudioSegment, effects as pydub_fx
    from pydub.generators import Sine, Square, Sawtooth
    from pydub.silence import detect_leading_silence
    PYDUB_OK = True
except ImportError:
    PYDUB_OK = False

# ─── NUMPY & MATPLOTLIB ──────────────────────────────────────────────────────
try:
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    NP_OK = True
except ImportError:
    NP_OK = False

# ─── MUTAGEN (ID3) ────────────────────────────────────────────────────────────
try:
    from mutagen import File as MutagenFile
    MUTAGEN_OK = True
except ImportError:
    MUTAGEN_OK = False

# ─── DİZİNLER ──────────────────────────────────────────────────────────────────
BASE = os.path.abspath("imajfm_data")
DIRS = {
    "playlist": os.path.join(BASE, "playlist"),
    "fon": os.path.join(BASE, "fon"),
    "jingles": os.path.join(BASE, "jingles"),
    "effects": os.path.join(BASE, "effects"),
    "output": os.path.join(BASE, "output"),
    "archive": os.path.join(BASE, "archive"),
    "uploads": os.path.join(BASE, "uploads"),
    "anons": os.path.join(BASE, "anons"),
    "effect_gallery": os.path.join(BASE, "effect_gallery"),
    "podcast": os.path.join(BASE, "podcast"),
    "schedules": os.path.join(BASE, "schedules"),
    "rvc_workspace": os.path.join(BASE, "rvc_workspace"),
    "voice_clones": os.path.join(BASE, "voice_clones"),
}
for d in DIRS.values():
    os.makedirs(d, exist_ok=True)

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="İmaj FM TTS v7",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap');
*{box-sizing:border-box;}
html,body,[data-testid="stAppViewContainer"],[data-testid="stApp"],.main{
  background:#07090f!important;color:#dde2ee;font-family:'Inter',sans-serif;}
[data-testid="stSidebar"]{background:#05070c!important;border-right:1px solid #101828!important;}
[data-testid="stSidebarContent"]{padding:.6rem .7rem;}
.hdr{background:linear-gradient(135deg,#0c1a34,#09101e,#07090f);border:1px solid #172540;
  border-radius:14px;padding:20px 26px;margin-bottom:16px;position:relative;overflow:hidden;}
.hdr::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,#e02020,#f07800,#e02020);
  background-size:200%;animation:scan 3s linear infinite;}
@keyframes scan{0%{background-position:0%}100%{background-position:200%}}
.hdr h1{font-family:'Syne',sans-serif;font-size:1.65rem;font-weight:800;margin:0 0 3px;
  background:linear-gradient(90deg,#fff 25%,#ff6060);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.hdr p{margin:0;color:#6b7a8d;font-size:.8rem;}
.ldot{display:inline-block;width:7px;height:7px;background:#ff3a3a;border-radius:50%;
  margin-right:6px;animation:bl 1.2s infinite;}
@keyframes bl{0%,100%{opacity:1}50%{opacity:.1}}
.sl{font-family:'Syne',sans-serif;font-size:.61rem;font-weight:700;letter-spacing:.17em;
  color:#e05252;text-transform:uppercase;margin:14px 0 4px;display:block;}
.sl2{font-family:'Syne',sans-serif;font-size:.56rem;font-weight:700;letter-spacing:.14em;
  color:#3a7bd5;text-transform:uppercase;margin:9px 0 3px;display:block;}
.sl3{font-family:'Syne',sans-serif;font-size:.56rem;font-weight:700;letter-spacing:.14em;
  color:#10b981;text-transform:uppercase;margin:9px 0 3px;display:block;}
.mbox{background:#0b0f1a;border:1px solid #131c2e;border-radius:9px;padding:10px;text-align:center;}
.mbox .v{font-family:'Syne',sans-serif;font-size:1.25rem;font-weight:800;color:#e05252;}
.mbox .l{font-size:.58rem;letter-spacing:.11em;color:#2e3f55;text-transform:uppercase;margin-top:2px;}
.mbox.g .v{color:#22c55e;}.mbox.b .v{color:#3b82f6;}.mbox.a .v{color:#f59e0b;}
.mbox.p .v{color:#a78bfa;}.mbox.t .v{color:#10b981;}
.card{background:#0b0f1a;border:1px solid #131c2e;border-radius:8px;padding:10px 13px;margin:6px 0;font-size:.81rem;color:#6b7a8d;}
.card.b{border-left:3px solid #3a7bd5;}
.card.g{border-left:3px solid #22c55e;background:#021409;color:#4ade80;}
.card.a{border-left:3px solid #f59e0b;background:#100d00;color:#fbbf24;}
.card.r{border-left:3px solid #ef4444;background:#110404;color:#f87171;}
.card.p{border-left:3px solid #a78bfa;background:#090614;color:#c4b5fd;}
.card.t{border-left:3px solid #10b981;background:#011209;color:#34d399;}
[data-testid="stButton"]>button{font-family:'Syne',sans-serif;font-weight:700;border-radius:8px;transition:all .2s;}
[data-testid="stButton"]>button[kind="primary"]{background:linear-gradient(135deg,#b91c1c,#dc2626)!important;border:none!important;color:#fff!important;}
[data-testid="stButton"]>button[kind="primary"]:hover{background:linear-gradient(135deg,#dc2626,#ef4444)!important;transform:translateY(-1px);}
[data-testid="stButton"]>button[kind="secondary"]{background:#0f1420!important;border:1px solid #131c2e!important;color:#b0bac9!important;}
[data-testid="stTextArea"] textarea{background:#090d18!important;border:1px solid #131c2e!important;border-radius:9px!important;color:#dde2ee!important;font-family:'Inter',sans-serif!important;}
[data-testid="stSelectbox"]>div>div,[data-testid="stSelectbox"]>div>div>div{background:#090d18!important;border:1px solid #131c2e!important;border-radius:7px!important;color:#dde2ee!important;}
[data-testid="stTextInput"]>div>div>input{background:#090d18!important;border:1px solid #131c2e!important;border-radius:7px!important;color:#dde2ee!important;}
[data-testid="stAudio"]{background:#0b0f1a;border-radius:9px;padding:7px;}
[data-testid="stFileUploader"]{background:#090d18!important;border:2px dashed #1a2436!important;border-radius:9px!important;}
[data-testid="stSidebar"] details{background:#0b0f1a!important;border:1px solid #131c2e!important;border-radius:8px!important;margin-bottom:4px!important;}
[data-testid="stSidebar"] details summary{font-family:'Syne',sans-serif!important;font-size:.73rem!important;font-weight:700!important;color:#b0bac9!important;padding:7px 10px!important;}
[data-testid="stSidebar"] details summary:hover{color:#e05252!important;}
[data-testid="stSidebar"] details[open] summary{color:#e05252!important;}
[data-testid="stTabs"] [data-baseweb="tab-list"]{background:transparent!important;border-bottom:1px solid #131c2e;}
[data-testid="stTabs"] [data-baseweb="tab"]{background:transparent!important;color:#6b7a8d!important;font-family:'Syne',sans-serif!important;font-weight:700!important;font-size:.7rem!important;padding:8px 11px!important;border-bottom:2px solid transparent!important;}
[data-testid="stTabs"] [aria-selected="true"]{color:#e05252!important;border-bottom:2px solid #e05252!important;}
.qbar{background:#101828;border-radius:4px;height:5px;margin:3px 0;overflow:hidden;}
.qbar-f{height:100%;border-radius:4px;}
.song-row{display:flex;align-items:center;gap:9px;background:#0b0f1a;border:1px solid #131c2e;
  border-radius:7px;padding:8px 12px;margin-bottom:5px;transition:border-color .15s;}
.song-row:hover{border-color:#3a7bd5;}
.song-nm{font-family:'Syne',sans-serif;font-size:.8rem;font-weight:700;color:#dde2ee;flex:1;}
.song-dur{font-family:'JetBrains Mono',monospace;font-size:.66rem;color:#6b7a8d;}
.tl-block{background:#0b0f1a;border:1px solid #131c2e;border-radius:7px;padding:7px 11px;
  margin:3px 0;display:flex;align-items:center;gap:9px;}
.tl-time{font-family:'JetBrains Mono',monospace;font-size:.7rem;color:#10b981;min-width:46px;}
.tl-type{font-size:.6rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
  padding:2px 7px;border-radius:4px;min-width:58px;text-align:center;}
.ttype-song{background:#071a2e;color:#60a5fa;border:1px solid #1a3a5e;}
.ttype-anons{background:#1a0d00;color:#f59e0b;border:1px solid #5e3a00;}
.ttype-fon{background:#071a0f;color:#34d399;border:1px solid #0a3d1f;}
.tl-lbl{font-size:.76rem;color:#9aa7b8;flex:1;}
.tl-dur{font-family:'JetBrains Mono',monospace;font-size:.63rem;color:#6b7a8d;}
.rjhdr{background:linear-gradient(135deg,#071a0f,#07090f);border:1px solid #0d2e1a;
  border-radius:12px;padding:16px 20px;margin-bottom:14px;position:relative;overflow:hidden;}
.rjhdr::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,#10b981,#34d399,#10b981);background-size:200%;animation:scan 4s linear infinite;}
.rjhdr h2{font-family:'Syne',sans-serif;font-size:1.15rem;font-weight:800;margin:0 0 2px;
  background:linear-gradient(90deg,#fff 30%,#34d399);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.rjhdr p{margin:0;color:#528068;font-size:.73rem;}
.fav-card{background:#0b0f1a;border:1px solid #131c2e;border-radius:7px;padding:8px 11px;margin:4px 0;}
.fav-name{font-family:'Syne',sans-serif;font-size:.73rem;font-weight:700;color:#dde2ee;}
.fav-prev{font-size:.68rem;color:#6b7a8d;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
hr{border-color:#101828!important;margin:10px 0!important;}
::-webkit-scrollbar{width:4px;height:4px;}
::-webkit-scrollbar-track{background:#07090f;}
::-webkit-scrollbar-thumb{background:#1a2436;border-radius:2px;}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════ SABİTLER ═══════════════════════════
MAX_PER_KEY = 10
MAX_ARC = 60

VOICES = {
    "Zephyr":("♀","Parlak·Neşeli"),"Puck":("♂","Enerjik·Hareketli"),
    "Charon":("♂","Bilgilendirici"),"Kore":("♀","Sıcak·Güven"),
    "Fenrir":("♂","Heyecanlı·Dinamik"),"Aoede":("♀","Akıcı·Doğal"),
    "Leda":("♀","Genç·Enerjik"),"Orus":("♂","Kararlı·Güçlü"),
    "Achird":("♂","Dostane·Samimi"),"Algenib":("♂","Pürüzlü·Özgün"),
    "Algieba":("♂","Yumuşak·Hoş"),"Alnilam":("♂","Sağlam·Güçlü"),
    "Autonoe":("♀","Parlak·İyimser"),"Callirrhoe":("♀","Rahat·Akıcı"),
    "Despina":("♀","Pürüzsüz·Zarif"),"Enceladus":("♂","Yumuşak·Nefes"),
    "Erinome":("♀","Net·Hassas"),"Gacrux":("♂","Olgun·Deneyimli"),
    "Iapetus":("♂","Net·Anlaşılır"),"Laomedeia":("♀","Neşeli·Canlı"),
    "Pulcherrima":("♀","İfadeli·Çarpıcı"),"Rasalgethi":("♂","Profesyonel"),
    "Sadachbia":("♂","Canlı·Hareketli"),"Sadaltager":("♂","Bilgili·Otoriter"),
    "Schedar":("♂","Güçlü·Etkileyici"),"Sulafat":("♀","Sıcak·Davetkar"),
    "Umbriel":("♂","Derin·Gizemli"),"Vindemiatrix":("♀","Nazik·Kibar"),
    "Achernar":("♀","Yumuşak·Hassas"),"Zubenelgenubi":("♂","Rahat·Dengeli"),
}

MODELS = {
    "gemini-2.5-flash-tts": "🚀 2.5 Flash TTS (Stabil)",
    "gemini-2.5-pro-tts": "💎 2.5 Pro TTS (Kaliteli)",
    "gemini-2.5-flash-preview-tts": "⚡ 2.5 Flash Preview TTS",
    "gemini-2.5-flash-lite-preview-tts": "💡 2.5 Lite Preview TTS",
    "gemini-3.1-flash-tts-preview": "🔥 3.1 Flash TTS Preview",
}

LANGUAGES = {
    "otomatik":"🌐 Oto","tr-TR":"🇹🇷 Türkçe","en-US":"🇺🇸 EN-US",
    "en-GB":"🇬🇧 EN-UK","de-DE":"🇩🇪 Almanca","fr-FR":"🇫🇷 Fransızca",
    "ar-XA":"🇸🇦 Arapça","es-ES":"🇪🇸 İspanyolca",
}

STYLE_PRESETS = {
    "— Seçin —":"",
    "📻 Haber Sunucusu":"Profesyonel haber sunucusu gibi net, otoriter ve güven verici oku.",
    "🎉 Neşeli & Enerjik":"Çok neşeli ve coşkulu, müzik programı sunuyormuş gibi oku.",
    "🎭 Dramatik & Güçlü":"Dramatik ve etkileyici, büyük sahne duyurusu gibi oku.",
    "🌙 Sakin & Huzurlu":"Sakin, huzurlu ve rahatlatıcı, gece kuşağı tonu ile oku.",
    "🚨 Acil & Hızlı":"Acil haber tonu, hızlı ve yüksek enerjili oku.",
    "☕ Sıcak & Samimi":"Sıcak ve dostça, yakın arkadaşa anlatır gibi oku.",
    "📣 Reklam Sesi":"Profesyonel reklam seslendirmesi, çekici ve ikna edici oku.",
    "📖 Hikaye":"Büyüleyici hikaye anlatıcısı gibi ritmik ve ifadeli oku.",
}

TEMPLATES = {
    "🎙️ Sabah Açılış":"[excitedly] Günaydın! İmaj FM ile sabahın en güzel sesine uyanıyorsunuz!\n[seriously] Bugün haber bültenimizle başlıyoruz... [normal] hoş geldiniz!\n[excitedly] BU SABAH müzik, haber ve çok daha fazlası burada!",
    "🌙 Gece Kapanış":"[whispers] Ve gece yarısına yaklaşırken... İmaj FM sizinle.\n[sighs] Uzun bir günün ardından... kulaklarınıza iyi geceler.\n[whispers] Yarın yeniden buradayız. Tatlı rüyalar.",
    "📢 Özel Duyuru":"[excitedly] DUYURU DUYURU!\n[seriously] Değerli dinleyicilerimiz, önemli bir bildirimiz var.\n[excitedly] BU HAFTA sonu unutulmaz bir etkinlik sizi bekliyor!\n[shouting] KAÇIRMAYIN!",
    "🎵 Müzik Geçişi":"[normal] Ve müziğimiz devam ediyor...\n[whispers] Şimdi sizin için harika bir seçim var.\n[excitedly] İşte o şarkı!",
    "📰 Haber Girişi":"[seriously] İmaj FM Ana Haber Bülteni.\n[normal] Günün öne çıkan haberleriyle karşınızdayız.",
    "🎵 Şarkı Başı":"[excitedly] Ve şimdi sizi muhteşem bir şarkıyla baş başa bırakıyoruz!\n[normal] İşte bu dakikanın en özel sesi...",
    "🎵 Şarkı Sonu":"[normal] Dinlediğiniz şarkıydı... İmaj FM'de devam ediyoruz.\n[excitedly] Sıradaki sürpriz için kulaklarınız bizde kalsın!",
    "🎉 Yarışma":"[excitedly] BÜYÜK YARIŞMA BAŞLIYOR!\n[laughs] Hazır mısınız?\n[shouting] BU HAFTA kazanan sizin aranızdan çıkacak!\n[seriously] Hemen arayın... [excitedly] KAZANMA ŞANSI SİZİN!",
}

ETAGS = [
    ("🔥","Coşkulu","[excitedly] "),("🤫","Fısıltı","[whispers] "),
    ("😄","Gülen","[laughs] "),("📰","Ciddi","[seriously] "),
    ("📢","Bağırma","[shouting] "),("😮‍💨","Yorgun","[sighs] "),
    ("🎙️","Normal","[normal] "),
]

FON_TIPLERI = {
    "📻 Radyo Klasik":"Standart radyo fade-out, anons, fade-in.",
    "🎵 Yumuşak Giriş":"Müzik yavaşça yükseliyor, anons bitti, normale dönüyor.",
    "🌊 Dalgalı Geçiş":"Müzik dalgalanarak düşüyor, anons, tekrar yükseliyor.",
    "⚡ Enerji Geçişi":"Enerjik geçişle kesilip anons yapılıyor.",
}

EFFECT_PRESETS = {
    "Radyo Efekti": {"low": 300, "high": 3000, "gain": 3, "noise": 0.0},
    "Telefon Ses": {"low": 400, "high": 3400, "gain": 5, "noise": 0.0},
    "Ambians": {"low": 100, "high": 8000, "gain": -2, "noise": 0.0},
    "Dolby Atmos": {"low": 50, "high": 20000, "gain": 0, "noise": 0.0},
    "Vinyl": {"low": 120, "high": 7500, "gain": -1, "noise": 0.015},
}

EQ_OPTS = ["Ham", "Broadcast", "Warm", "AM", "Podcast", "Vinyl"]

# ═══════════════════════════ SESSION STATE ═══════════════════════
def _si(k, v):
    if k not in st.session_state:
        st.session_state[k] = v

DEFAULT_TEK = "[excitedly] İmaj FM'e hoş geldiniz! BU GECE unutulmaz bir program var...\n[whispers] Sürprizler için kulaklarınız bizde olsun.\n[seriously] Şimdi haberlere geçiyoruz."
DEFAULT_CIFT = "Sunucu: [excitedly] İmaj FM'e hoş geldiniz!\nMisafir: [laughs] Teşekkürler!\nSunucu: [seriously] Haberler... [normal] Müziğe dönüyoruz."

_si("_archive", [])
_si("_favorites", [])
_si("_api_pool", [{"key": "", "used": 0, "label": f"API {i+1}"} for i in range(10)])
_si("_active_idx", 0)
_si("_secrets_loaded", False)
_si("_api_stats", {"calls": 0, "chars": 0, "secs": 0.0})
_si("_giris", False)
_si("_t_tek", DEFAULT_TEK)
_si("ta1", DEFAULT_TEK)
_si("_t_cift", DEFAULT_CIFT)
_si("ta2", DEFAULT_CIFT)
_si("_t_bulk", "İmaj FM sabah yayını başlıyor.\nHaber bülteni için bekleyiniz.\nMüzik programımıza hoş geldiniz.")
_si("_t_ab1", "[excitedly] İmaj FM'e hoş geldiniz!")
_si("ab_a_ta", "[excitedly] İmaj FM'e hoş geldiniz!")
_si("_t_ab2", "[seriously] İmaj FM'e hoş geldiniz.")
_si("ab_b_ta", "[seriously] İmaj FM'e hoş geldiniz.")
_si("_playlist", [])
_si("_rj_voice", "Kore")
_si("_rj_model", "gemini-2.5-flash-tts")
_si("_rj_lang", "tr-TR")
_si("_rj_style", "")
_si("_rj_start", "06:00")
_si("_rj_plan", [])
_si("_rj_plan_ok", False)
_si("_processed_uploads", set())

# Kalıcı çıktı state'leri (Download butonlarının kaybolmaması için)
for _ok_key in [
    "_last_tek", "_last_cift", "_last_bulk_manual", "_last_bulk_file",
    "_last_ab_a", "_last_ab_b", "_last_mx", "_last_mx_bulk", "_last_mx_arc",
    "_last_yo", "_last_ch", "_last_cnt_arc", "_last_cnt_up",
    "_last_ef", "_last_sig", "_last_arc_zip", "_last_rss",
    "_last_rvc_zip", "_last_conv_zip", "_last_norm_zip"
]:
    _si(_ok_key, None)

# ═══════════════════════════ API HAVUZU ═════════════════════════
def load_secrets():
    if st.session_state._secrets_loaded:
        return
    st.session_state._secrets_loaded = True
    for i in range(10):
        try:
            v = st.secrets.get(f"GEMINI_API_KEY_{i+1}", "")
            if v and not st.session_state._api_pool[i]["key"]:
                st.session_state._api_pool[i]["key"] = str(v)
        except Exception:
            pass

load_secrets()

def get_key() -> Tuple[Optional[str], int]:
    pool = st.session_state._api_pool
    idx = st.session_state._active_idx
    for _ in range(10):
        s = pool[idx]
        if s["key"].strip() and s["used"] < MAX_PER_KEY:
            st.session_state._active_idx = idx
            return s["key"].strip(), idx
        idx = (idx + 1) % 10
    return None, -1

def consume(idx: int, chars: int = 0):
    if idx < 0:
        return
    st.session_state._api_pool[idx]["used"] += 1
    st.session_state._api_stats["calls"] += 1
    st.session_state._api_stats["chars"] += chars
    if st.session_state._api_pool[idx]["used"] >= MAX_PER_KEY:
        st.session_state._active_idx = (idx + 1) % 10

def mark_key_exhausted(idx: int):
    if idx >= 0:
        st.session_state._api_pool[idx]["used"] = MAX_PER_KEY
        st.session_state._active_idx = (idx + 1) % 10

def pool_stats() -> Tuple[int, int]:
    p = st.session_state._api_pool
    loaded = sum(1 for s in p if s["key"].strip())
    remain = sum(max(0, MAX_PER_KEY - s["used"]) for s in p if s["key"].strip())
    return loaded, remain

# ═══════════════════════════ YARDIMCI İŞLEVLER ══════════════════
def sfn(s: str, n: int = 36) -> str:
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', str(s))[:n] or "dosya"

def dur_bytes(wb: bytes) -> float:
    if not wb:
        return 0.0
    try:
        with wave.open(io.BytesIO(wb), "rb") as wf:
            fr = wf.getframerate()
            if fr > 0:
                return wf.getnframes() / float(fr)
    except Exception:
        pass
    if PYDUB_OK:
        try:
            return len(AudioSegment.from_file(io.BytesIO(wb))) / 1000.0
        except Exception:
            pass
    return max(0.0, (len(wb) - 44) / (24000 * 2))

def dur_file(path: str) -> float:
    if not path or not os.path.exists(path):
        return 0.0
    if PYDUB_OK:
        try:
            return len(AudioSegment.from_file(path)) / 1000.0
        except Exception:
            pass
    if MUTAGEN_OK:
        try:
            mf = MutagenFile(path)
            if mf and mf.info:
                return float(getattr(mf.info, "length", 0.0))
        except Exception:
            pass
    return 0.0

def read_id3_meta(path: str) -> Dict[str, str]:
    meta = {"title": os.path.splitext(os.path.basename(path))[0], "artist": "Bilinmeyen", "bitrate": ""}
    if not MUTAGEN_OK or not os.path.exists(path):
        return meta
    try:
        mf = MutagenFile(path, easy=True)
        if mf:
            if "title" in mf and mf["title"]:
                meta["title"] = str(mf["title"][0])
            if "artist" in mf and mf["artist"]:
                meta["artist"] = str(mf["artist"][0])
        mf_raw = MutagenFile(path)
        if mf_raw and getattr(mf_raw, "info", None):
            br = getattr(mf_raw.info, "bitrate", 0)
            if br:
                meta["bitrate"] = f"{int(br)//1000}kbps"
    except Exception:
        pass
    return meta

def fmt_dur(sec: float) -> str:
    if sec < 0:
        sec = 0
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

# ═══════════════════════════ ARŞİV ══════════════════════════════
def arc_add(voice: str, model: str, lang: str, style: str, text: str, wav: bytes, mode: str = "tek"):
    dur = dur_bytes(wav)
    uid = uuid.uuid4().hex[:10]
    st.session_state._archive.insert(0, {
        "id": uid,
        "ts": datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "ts_s": datetime.datetime.now().strftime("%d.%m %H:%M"),
        "voice": voice,
        "model": model,
        "model_s": model.replace("gemini-", "").replace("-preview", "").replace("-tts", ""),
        "lang": lang,
        "style": style[:40] if style else "",
        "text": text,
        "prev": text[:65].replace("\n", " ") + ("…" if len(text) > 65 else ""),
        "wav": wav,
        "dur": round(dur, 1),
        "size": len(wav),
        "mode": mode,
    })
    if len(st.session_state._archive) > MAX_ARC:
        st.session_state._archive = st.session_state._archive[:MAX_ARC]
    st.session_state._api_stats["secs"] = st.session_state._api_stats.get("secs", 0.0) + dur

# ═══════════════════════════ GEMINI TTS CORE ═════════════════════
def _extract_audio_from_response(resp) -> Tuple[bytes, str]:
    if not resp or not getattr(resp, "candidates", None):
        raise RuntimeError("API boş yanıt döndürdü.")
    cand = resp.candidates[0]
    if not getattr(cand, "content", None) or not getattr(cand.content, "parts", None):
        raise RuntimeError("API yanıtında ses içeriği bulunamadı (güvenlik filtresi veya boş içerik).")
    for part in cand.content.parts:
        inl = getattr(part, "inline_data", None)
        if inl and getattr(inl, "data", None):
            return inl.data, getattr(inl, "mime_type", "") or ""
    text_msgs = [getattr(p, "text", "") for p in cand.content.parts if getattr(p, "text", None)]
    raise RuntimeError(f"Ses üretilemedi. Model mesajı: {' '.join(text_msgs) or 'Yok'}")

def pcm2wav(raw_data: bytes, mime_type: str = "", rate: int = 24000, ch: int = 1, sw: int = 2) -> bytes:
    if not raw_data:
        return b""
    # Zaten WAV başlığı varsa tekrar sarmalama
    if raw_data[:4] == b"RIFF" and len(raw_data) > 44:
        return raw_data
    if mime_type:
        m_rate = re.search(r"rate=(\d+)", mime_type)
        if m_rate:
            rate = int(m_rate.group(1))
        m_ch = re.search(r"channels=(\d+)", mime_type)
        if m_ch:
            ch = int(m_ch.group(1))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(ch)
        wf.setsampwidth(sw)
        wf.setframerate(rate)
        wf.writeframes(raw_data)
    return buf.getvalue()

def _run_tts_with_rotation(fn_call, chars: int):
    if not GEMINI_OK:
        raise RuntimeError("`google-genai` paketi kurulu değil. `pip install google-genai` çalıştırın.")
    last_err = None
    for _ in range(10):
        ak, ai = get_key()
        if ak is None:
            break
        try:
            data, mime = fn_call(ak)
            consume(ai, chars)
            return data, mime, ai
        except Exception as e:
            err_s = str(e)
            last_err = e
            if any(x in err_s.upper() for x in ["429", "RESOURCE_EXHAUSTED", "QUOTA", "API_KEY_INVALID"]):
                mark_key_exhausted(ai)
                continue
            raise e
    raise RuntimeError(last_err or "Kullanılabilir API anahtarı kalmadı!")

def tts_single(model: str, text: str, voice: str, lang: str, style: str) -> Tuple[bytes, str, int]:
    full = f"{style}\n\n{text}" if style.strip() else text
    lc = lang if lang != "otomatik" else None

    def _call(api_key: str):
        c = genai.Client(api_key=api_key)
        sc_kwargs = {
            "voice_config": types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
            )
        }
        if lc:
            sc_kwargs["language_code"] = lc
        r = c.models.generate_content(
            model=model,
            contents=full,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(**sc_kwargs),
            ),
        )
        return _extract_audio_from_response(r)

    return _run_tts_with_rotation(_call, len(text))

def tts_multi(model: str, text: str, sp1: str, v1: str, sp2: str, v2: str, lang: str) -> Tuple[bytes, str, int]:
    lc = lang if lang != "otomatik" else None

    def _call(api_key: str):
        c = genai.Client(api_key=api_key)
        sc_kwargs = {
            "multi_speaker_voice_config": types.MultiSpeakerVoiceConfig(
                speaker_voice_configs=[
                    types.SpeakerVoiceConfig(
                        speaker=sp1,
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=v1)
                        ),
                    ),
                    types.SpeakerVoiceConfig(
                        speaker=sp2,
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=v2)
                        ),
                    ),
                ]
            )
        }
        if lc:
            sc_kwargs["language_code"] = lc
        r = c.models.generate_content(
            model=model,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(**sc_kwargs),
            ),
        )
        return _extract_audio_from_response(r)

    return _run_tts_with_rotation(_call, len(text))

# ═══════════════════════════ PYDUB YARDIMCI ══════════════════════
def norm_seg(seg, db: float = -16.0):
    if not PYDUB_OK or seg is None or len(seg) == 0:
        return seg
    try:
        if seg.dBFS == float("-inf"):
            return seg
        return seg.apply_gain(db - seg.dBFS)
    except Exception:
        return seg

def safe_append(seg1, seg2, crossfade_ms: int = 0):
    if not PYDUB_OK:
        return seg1
    if seg1 is None or len(seg1) == 0:
        return seg2
    if seg2 is None or len(seg2) == 0:
        return seg1
    cf = min(int(crossfade_ms), max(0, len(seg1) // 3), max(0, len(seg2) // 3))
    if cf >= 10:
        return seg1.append(seg2, crossfade=cf)
    return seg1 + seg2

def apply_eq(seg, preset: str):
    if not PYDUB_OK or seg is None or preset == "Ham":
        return seg
    try:
        if preset == "Broadcast":
            return pydub_fx.normalize(pydub_fx.compress_dynamic_range(seg, threshold=-18, ratio=3.0))
        elif preset == "Warm":
            return pydub_fx.normalize(seg) + 1
        elif preset == "AM":
            return (seg.low_pass_filter(3000).high_pass_filter(400)) + 3
        elif preset == "Podcast":
            return pydub_fx.compress_dynamic_range(pydub_fx.normalize(seg), threshold=-20, ratio=2.5)
        elif preset == "Vinyl":
            return pydub_fx.normalize(seg.low_pass_filter(8000)) - 2
    except Exception:
        pass
    return seg

def apply_effect(seg, params: Dict):
    if not PYDUB_OK or seg is None or not params:
        return seg
    try:
        low = int(params.get("low", 100))
        high = int(params.get("high", 12000))
        gain = float(params.get("gain", 0))
        noise_lvl = float(params.get("noise", 0.0))

        if high < 20000:
            seg = seg.low_pass_filter(high)
        if low > 20:
            seg = seg.high_pass_filter(low)
        if gain != 0:
            seg = seg + gain

        if noise_lvl > 0 and NP_OK and len(seg) > 0:
            sr = seg.frame_rate
            ch = seg.channels
            sw = seg.sample_width
            n_samples = int(len(seg) / 1000.0 * sr) * ch
            if n_samples > 0:
                amp = (2 ** (8 * sw - 1) - 1) * min(noise_lvl, 0.25)
                noise_arr = np.random.normal(0, amp, n_samples).clip(-32767, 32767).astype(np.int16)
                noise_seg = AudioSegment(
                    noise_arr.tobytes(),
                    frame_rate=sr,
                    sample_width=2,
                    channels=ch,
                )
                seg = seg.overlay(noise_seg)
        return norm_seg(seg)
    except Exception:
        return seg

def mix_fon_voice(fon_seg, voice_seg, fon_vol=-8, duck_db=-16, fi=800, fo=1200):
    if not PYDUB_OK:
        return voice_seg
    try:
        # Kanal ve örnekleme hızı eşitleme
        target_sr = max(fon_seg.frame_rate, voice_seg.frame_rate, 44100)
        target_ch = max(fon_seg.channels, voice_seg.channels)
        fon = fon_seg.set_frame_rate(target_sr).set_channels(target_ch) + fon_vol
        voice = voice_seg.set_frame_rate(target_sr).set_channels(target_ch)

        vl = len(voice)
        if vl == 0:
            return fon
        fl = len(fon)
        if fl == 0:
            return voice

        tail_ms = 2000
        if fl < vl + tail_ms:
            loops = (vl + tail_ms) // fl + 1
            fon = fon * loops
        fon = fon[:vl + tail_ms]
        if fi > 0 and len(fon) > fi:
            fon = fon.fade_in(fi)

        fp = fon[:vl]
        fr = fon[vl:]
        fm = min(500, vl // 4)
        if fm >= 15 and vl > 2 * fm:
            ducked = (
                fp[:fm].fade(to_gain=duck_db, start=0, duration=fm)
                + (fp[fm:vl - fm] + duck_db)
                + fp[vl - fm:].fade(from_gain=duck_db, start=0, duration=fm)
            )
        else:
            ducked = fp + duck_db

        if fo > 0 and len(fr) > 10:
            fr = fr.fade_out(min(fo, len(fr)))

        return norm_seg(ducked.overlay(voice) + fr)
    except Exception:
        return voice_seg

def seg_to_wav(seg) -> bytes:
    if not PYDUB_OK or seg is None:
        return b""
    try:
        buf = io.BytesIO()
        seg.export(buf, format="wav")
        return buf.getvalue()
    except Exception:
        return b""

def qs_bytes(wb: bytes) -> int:
    if not PYDUB_OK or not wb:
        return 70
    try:
        seg = AudioSegment.from_file(io.BytesIO(wb), format="wav")
        sc = 55
        if -22 <= seg.dBFS <= -10:
            sc += 20
        elif -30 <= seg.dBFS <= -22:
            sc += 10
        if -5 <= seg.max_dBFS <= -0.5:
            sc += 20
        elif -8 <= seg.max_dBFS <= -5:
            sc += 10
        if seg.frame_rate >= 22050:
            sc += 5
        return min(100, max(0, sc))
    except Exception:
        return 70

def draw_wf(wb: bytes, h: float = 2.0):
    if not NP_OK or not wb:
        return
    try:
        buf = io.BytesIO(wb)
        with wave.open(buf, 'rb') as wf:
            frames = wf.readframes(wf.getnframes())
            sr = wf.getframerate()
            sw_ = wf.getsampwidth()
            ch_ = wf.getnchannels()
        if not frames or sr <= 0:
            return
        if sw_ == 1:
            s = np.frombuffer(frames, dtype=np.uint8).astype(np.float32) - 128.0
        elif sw_ == 2:
            s = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
        elif sw_ == 4:
            s = np.frombuffer(frames, dtype=np.int32).astype(np.float32)
        elif sw_ == 3:
            raw_u8 = np.frombuffer(frames, dtype=np.uint8).reshape(-1, 3)
            s = ((raw_u8[:, 0].astype(np.int32)) | (raw_u8[:, 1].astype(np.int32) << 8) | (raw_u8[:, 2].astype(np.int32) << 16))
            s = np.where(s >= 0x800000, s - 0x1000000, s).astype(np.float32)
        else:
            return
        if ch_ > 1:
            s = s[::ch_]
        if len(s) == 0:
            return
        step = max(1, len(s) // 2000)
        ds = s[::step]
        mx = np.max(np.abs(ds)) or 1.0
        ds /= mx
        t = np.linspace(0, len(s) / sr, len(ds))
        fig, ax = plt.subplots(figsize=(10, h), facecolor='#07090f')
        ax.set_facecolor('#07090f')
        ax.fill_between(t, ds, alpha=.65, color='#3b82f6')
        ax.fill_between(t, -np.abs(ds), alpha=.2, color='#a78bfa')
        ax.axhline(0, color='#1a2436', lw=.8)
        ax.set_xlim(0, max(t[-1], 0.01))
        ax.set_ylim(-1.1, 1.1)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.tick_params(colors='#4b5c74', labelsize=7)
        plt.tight_layout(pad=.3)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    except Exception:
        pass

def list_audio(d: str) -> List[str]:
    exts = (".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac")
    if not os.path.isdir(d):
        return []
    return sorted(f for f in os.listdir(d) if f.lower().endswith(exts))

def save_upload(uf, dest_dir: str, custom_name: str = "", convert_to_wav: bool = True) -> Tuple[Optional[str], Optional[bytes]]:
    if uf is None:
        return None, None
    try:
        os.makedirs(dest_dir, exist_ok=True)
        fname = custom_name or getattr(uf, 'name', 'upload.wav')
        fname = re.sub(r'[^\w\-.]', '_', fname)
        if '.' not in fname:
            fname += '.wav'
        dest = os.path.join(dest_dir, fname)
        raw = uf.getvalue() if hasattr(uf, 'getvalue') else uf.read()
        if not raw or len(raw) < 64:
            return None, None
        with open(dest, 'wb') as f:
            f.write(raw)
        if PYDUB_OK and convert_to_wav:
            try:
                seg = AudioSegment.from_file(dest)
                wd = os.path.splitext(dest)[0] + '.wav'
                seg.export(wd, format='wav')
                if wd != dest and os.path.exists(dest):
                    os.remove(dest)  # Kütüphanede çift kayıt oluşmasını önle
                with open(wd, 'rb') as f:
                    return wd, f.read()
            except Exception:
                pass
        with open(dest, 'rb') as f:
            return dest, f.read()
    except Exception as e:
        st.error(f"Upload hatası: {e}")
        return None, None

def make_zip(items: List[Tuple[str, bytes]]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        used_names = set()
        for fn, data in items:
            safe = re.sub(r'[^\w\-.]', '_', fn)
            base, ext = os.path.splitext(safe)
            idx = 1
            while safe in used_names:
                safe = f"{base}_{idx}{ext}"
                idx += 1
            used_names.add(safe)
            zf.writestr(safe, data)
    return buf.getvalue()

# ═══════════════════════════ DELAY REJİ YARDIMCI ═════════════════
def song_uid() -> str:
    return uuid.uuid4().hex[:8]

def song_dur(s: Dict) -> int:
    return int(s.get("duration_min", 3)) * 60 + int(s.get("duration_sec", 30))

def add_time(base: str, secs: int) -> str:
    try:
        p = base.split(":")
        h, m = int(p[0]), int(p[1])
    except Exception:
        h, m = 6, 0
    t = h * 3600 + m * 60 + int(secs)
    hh = (t // 3600) % 24
    mm = (t % 3600) // 60
    ss = t % 60
    return f"{hh:02d}:{mm:02d}:{ss:02d}"

def auto_bas(s: Dict) -> str:
    return (f"[excitedly] Ve şimdi İmaj FM'de... {s.get('artist','?')}! "
            f"[normal] '{s.get('title','?')}' sizlerle. [whispers] Keyfini çıkarın...")

def auto_son(s: Dict) -> str:
    return (f"[normal] Dinlediğiniz {s.get('artist','?')} — '{s.get('title','?')}' idi. "
            f"[excitedly] İmaj FM'de devam ediyoruz!")

def build_plan(playlist: List[Dict], start: str) -> List[Dict]:
    plan = []
    cur = 0
    for song in playlist:
        sid = song["id"]
        sd = song_dur(song)
        if song.get("anons_bas"):
            txt = song.get("anons_bas_text") or auto_bas(song)
            ad = int(round(dur_bytes(song["anons_wav_bas"]))) if song.get("anons_wav_bas") else max(5, len(txt) // 15)
            plan.append({
                "time": add_time(start, cur), "off": cur, "type": "anons_bas", "song_id": sid,
                "label": f"🎙️ Baş → {song.get('title','?')}",
                "sub": txt[:55] + "…" if len(txt) > 55 else txt,
                "dur": ad, "wav": song.get("anons_wav_bas"), "text": txt
            })
            cur += ad
        if song.get("fon_aktif"):
            plan.append({
                "time": add_time(start, cur), "off": cur, "type": "fon", "song_id": sid,
                "label": f"🎶 Fon [{song.get('fon_tip','?')}] → {song.get('title','?')}",
                "sub": FON_TIPLERI.get(song.get("fon_tip", "📻 Radyo Klasik"), "")[:55],
                "dur": 4, "wav": None, "text": ""
            })
            cur += 4
        plan.append({
            "time": add_time(start, cur), "off": cur, "type": "song", "song_id": sid,
            "label": f"🎵 {song.get('artist','?')} — {song.get('title','?')}",
            "sub": fmt_dur(sd), "dur": sd, "wav": None, "text": ""
        })
        cur += sd
        if song.get("anons_son"):
            txt = song.get("anons_son_text") or auto_son(song)
            ad = int(round(dur_bytes(song["anons_wav_son"]))) if song.get("anons_wav_son") else max(4, len(txt) // 15)
            plan.append({
                "time": add_time(start, cur), "off": cur, "type": "anons_son", "song_id": sid,
                "label": f"🎙️ Son ← {song.get('title','?')}",
                "sub": txt[:55] + "…" if len(txt) > 55 else txt,
                "dur": ad, "wav": song.get("anons_wav_son"), "text": txt
            })
            cur += ad
    return plan

# ═══════════════════════════ YENİ MODÜL FONKSİYONLARI ════════════
def generate_podcast_rss(title: str, desc: str, author: str, base_url: str, episodes: List[Dict], output_path: str) -> Optional[str]:
    try:
        t_esc = xml_escape(title)
        d_esc = xml_escape(desc)
        a_esc = xml_escape(author)
        rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:itunes="http://www.itunes.com/dtd/podcast-1.0.dtd" version="2.0">
<channel>
    <title>{t_esc}</title>
    <description>{d_esc}</description>
    <language>tr</language>
    <itunes:author>{a_esc}</itunes:author>
    <itunes:explicit>no</itunes:explicit>
"""
        for ep in episodes:
            ep_title = xml_escape(ep.get("title", "Bölüm"))
            ep_desc = xml_escape(ep.get("description", ""))
            ep_url = xml_escape((base_url.rstrip("/") + "/" if base_url.strip() else "") + ep.get("url", ""))
            ep_guid = xml_escape(ep.get("guid", ep_url))
            pub_date = ep.get("pub_date", datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000"))
            rss += f"""    <item>
        <title>{ep_title}</title>
        <description>{ep_desc}</description>
        <enclosure url="{ep_url}" length="{ep.get('length', '0')}" type="audio/wav"/>
        <pubDate>{pub_date}</pubDate>
        <guid isPermaLink="false">{ep_guid}</guid>
    </item>
"""
        rss += "</channel>\n</rss>"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rss)
        return rss
    except Exception as e:
        st.error(f"RSS hatası: {e}")
        return None

def schedule_broadcast(name: str, date_str: str, broadcast_time: str, songs: List[str], notes: str = "") -> bool:
    try:
        uid = f"s_{int(time.time())}_{uuid.uuid4().hex[:4]}_{sfn(name)}.json"
        d = {
            "id": uid,
            "name": name,
            "date": date_str,
            "time": broadcast_time,
            "songs": songs,
            "notes": notes,
            "created": datetime.datetime.now().isoformat(),
            "status": "pending"
        }
        with open(os.path.join(DIRS["schedules"], uid), "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Takvim kayıt hatası: {e}")
        return False

def get_scheduled_broadcasts() -> List[Dict]:
    broadcasts = []
    if not os.path.isdir(DIRS["schedules"]):
        return broadcasts
    for fn in os.listdir(DIRS["schedules"]):
        if fn.endswith(".json"):
            fp = os.path.join(DIRS["schedules"], fn)
            try:
                with open(fp, encoding="utf-8") as f:
                    obj = json.load(f)
                    obj["_file"] = fn
                    broadcasts.append(obj)
            except Exception:
                pass
    return sorted(broadcasts, key=lambda x: (x.get("date", ""), x.get("time", "")))

def save_effect_preset(name: str, params: Dict) -> bool:
    try:
        path = os.path.join(DIRS["effect_gallery"], f"{sfn(name)}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"name": name, "params": params, "created": datetime.datetime.now().isoformat()}, f, ensure_ascii=False)
        return True
    except Exception:
        return False

def load_effect_presets() -> List[Dict]:
    presets = []
    if not os.path.isdir(DIRS["effect_gallery"]):
        return presets
    for fn in os.listdir(DIRS["effect_gallery"]):
        if fn.endswith(".json"):
            try:
                with open(os.path.join(DIRS["effect_gallery"], fn), encoding="utf-8") as f:
                    presets.append(json.load(f))
            except Exception:
                pass
    return presets

def prepare_rvc_dataset(audio_paths: List[str], output_dir: str, chunk_sec: int = 15, target_db: float = -16.0) -> int:
    if not PYDUB_OK:
        return 0
    try:
        os.makedirs(output_dir, exist_ok=True)
        seg_count = 0
        for i, path in enumerate(audio_paths):
            if os.path.exists(path):
                seg = AudioSegment.from_file(path)
                seg = norm_seg(seg, target_db)
                seg = seg.set_frame_rate(44100).set_channels(1)
                chunk_size = chunk_sec * 1000
                for j, start in enumerate(range(0, len(seg), chunk_size)):
                    chunk = seg[start:start + chunk_size]
                    if len(chunk) >= 1500:
                        chunk.export(os.path.join(output_dir, f"segment_{i+1:02d}_{j+1:02d}.wav"), format="wav")
                        seg_count += 1
        return seg_count
    except Exception as e:
        st.error(f"RVC hazırlık hatası: {e}")
        return 0

def live_text_flow(text: str, delay: float = 0.03):
    """Canlı metin akışı (Teleprompter)"""
    placeholder = st.empty()
    words = text.split(" ")
    acc = ""
    for w in words:
        acc += (w + " ")
        placeholder.markdown(
            f"<div style='background:#090d18;border:1px solid #1a2d4a;border-left:3px solid #e05252;"
            f"border-radius:8px;padding:14px 18px;font-size:1.15rem;line-height:1.6;color:#f1f5f9;'>"
            f"{acc} <span style='color:#e05252;'>▌</span></div>",
            unsafe_allow_html=True,
        )
        time.sleep(delay)
    placeholder.markdown(
        f"<div style='background:#090d18;border:1px solid #1a2d4a;border-left:3px solid #22c55e;"
        f"border-radius:8px;padding:14px 18px;font-size:1.15rem;line-height:1.6;color:#f1f5f9;'>"
        f"{text}</div>",
        unsafe_allow_html=True,
    )

# ═══════════════════════════ UI YARDIMCI ═════════════════════════
def txt_stats(text: str):
    cc = len(text)
    wc = len(text.split())
    sc = max(1, text.count(".") + text.count("!") + text.count("?"))
    est = max(1, cc / 17)
    st.markdown(f"<div style='font-size:.67rem;color:#6b7a8d;margin:3px 0 7px;'>📊 {cc} karakter · {wc} kelime · {sc} cümle · ~{est:.0f}s</div>", unsafe_allow_html=True)

def tag_btns(sk: str, widget_key: str, prefix: str):
    cols = st.columns(len(ETAGS))
    for i, (em, lbl, tag) in enumerate(ETAGS):
        with cols[i]:
            if st.button(em, key=f"{prefix}_et{i}", help=lbl, use_container_width=True):
                new_val = st.session_state.get(widget_key, st.session_state.get(sk, "")) + tag
                st.session_state[sk] = new_val
                st.session_state[widget_key] = new_val
                st.rerun()

def style_w(prefix: str) -> str:
    ps = st.selectbox("Preset", list(STYLE_PRESETS.keys()), label_visibility="collapsed", key=f"{prefix}_ps")
    pv = STYLE_PRESETS[ps]
    ca, cb = st.columns(2)
    with ca:
        st.markdown("<div style='font-size:.63rem;color:#3b82f6;margin-bottom:3px;'>🇹🇷 TR Stil</div>", unsafe_allow_html=True)
        tr_ = st.text_area("TR", value=pv, height=60, label_visibility="collapsed", key=f"{prefix}_str_{ps}")
    with cb:
        st.markdown("<div style='font-size:.63rem;color:#f59e0b;margin-bottom:3px;'>🇬🇧 EN Style</div>", unsafe_allow_html=True)
        en_ = st.text_area("EN", value="", height=60, label_visibility="collapsed", key=f"{prefix}_sen")
    return " / ".join(filter(None, [tr_.strip(), en_.strip()]))

def res_card(wav: bytes, voice: str, ai: int, dk: str, dn: str):
    dur = dur_bytes(wav)
    qs = qs_bytes(wav)
    bc = "#22c55e" if qs >= 70 else "#f59e0b" if qs >= 50 else "#ef4444"
    st.markdown(f"<div class='card g'>✅ {VOICES.get(voice, ('?',''))[0]} {voice} · API {ai+1} · {dur:.1f}s · {qs}/100</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='qbar'><div class='qbar-f' style='width:{qs}%;background:{bc};'></div></div>", unsafe_allow_html=True)
    st.audio(wav, format="audio/wav")
    draw_wf(wav)
    st.download_button("💾 WAV İndir", wav, file_name=dn, mime="audio/wav", use_container_width=True, key=dk)

# ═══════════════════════════ GİRİŞ ══════════════════════════════
def login_page():
    _, col, _ = st.columns([1, 1.05, 1])
    with col:
        st.markdown("""<div style='margin-top:60px;padding:32px 28px;background:#0b0f1a;border:1px solid #1a2d4a;border-radius:16px;box-shadow:0 20px 60px rgba(0,0,0,.8);'>
<h2 style='text-align:center;font-family:Syne,sans-serif;font-weight:800;font-size:1.45rem;margin:0 0 3px;background:linear-gradient(90deg,#fff 20%,#ff6060);-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>🎙️ İmaj FM</h2>
<p style='text-align:center;color:#6b7a8d;font-size:.68rem;letter-spacing:.15em;margin:0 0 22px;'>TTS STÜDYO v7 · GÜVENLİ GİRİŞ</p></div>""", unsafe_allow_html=True)
        u = st.text_input("u", "", placeholder="👤 kullanıcı adı", label_visibility="collapsed")
        p = st.text_input("p", "", type="password", placeholder="🔑 şifre", label_visibility="collapsed")
        try:
            exp_u = st.secrets.get("APP_USER", "kenan")
            exp_p = st.secrets.get("APP_PASS", "imajfm")
        except Exception:
            exp_u, exp_p = "kenan", "imajfm"
        if st.button("Stüdyoya Bağlan →", type="primary", use_container_width=True):
            if u == exp_u and p == exp_p:
                st.session_state._giris = True
                st.rerun()
            else:
                st.error("❌ Hatalı kullanıcı adı veya şifre.")

if not st.session_state._giris:
    login_page()
    st.stop()

# ═══════════════════════════ SIDEBAR ════════════════════════════
with st.sidebar:
    st.markdown("""<div style='text-align:center;padding:4px 0 10px;'>
<span style='font-family:Syne,sans-serif;font-size:.92rem;font-weight:800;background:linear-gradient(90deg,#fff,#ff6060);-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>🎙️ İmaj FM</span>
<span style='font-size:.6rem;color:#6b7a8d;letter-spacing:.1em;'> TTS v7.1</span></div>""", unsafe_allow_html=True)

    ak_sb, ai_sb = get_key()
    tk_sb, tr_sb = pool_stats()
    used_a = st.session_state._api_pool[ai_sb]["used"] if ai_sb >= 0 else 0
    rem_a = MAX_PER_KEY - used_a if ai_sb >= 0 else 0
    pct_a = used_a / MAX_PER_KEY if ai_sb >= 0 else 1
    bc_a = "#22c55e" if pct_a < .6 else "#f59e0b" if pct_a < .9 else "#ef4444"

    with st.expander(f"🗝️ API Havuzu · {tk_sb}/10 · {tr_sb} kalan", expanded=True):
        if ak_sb:
            lbl_a = st.session_state._api_pool[ai_sb].get("label", f"API {ai_sb+1}")
            st.markdown(f"""<div style='background:#07090f;border-radius:7px;padding:7px 9px;margin-bottom:6px;font-size:.71rem;'>
<div style='display:flex;justify-content:space-between;margin-bottom:3px;'>
<span style='color:#6b7a8d;'>Aktif: <b style='color:#22c55e;'>{lbl_a}</b></span>
<span style='color:#6b7a8d;'>Kalan: <b style='color:{"#22c55e" if rem_a>3 else "#f59e0b"};'>{rem_a}/{MAX_PER_KEY}</b></span>
<span style='color:#6b7a8d;'>Top: <b style='color:#3b82f6;'>{tr_sb}</b></span></div>
<div class='qbar'><div class='qbar-f' style='width:{pct_a*100:.0f}%;background:{bc_a};'></div></div>
<div style='font-size:.6rem;color:#6b7a8d;margin-top:2px;'>Otomatik rotasyon & 429 geçiş aktif</div></div>""", unsafe_allow_html=True)
        else:
            st.markdown("<div class='card r'>⛔ API yok!</div>", unsafe_allow_html=True)
        with st.expander("📋 Secrets Formatı", expanded=False):
            st.code('GEMINI_API_KEY_1 = "AIza..."', language="toml")
        for i in range(10):
            slot = st.session_state._api_pool[i]
            used_i = slot["used"]
            has = bool(slot["key"].strip())
            full = has and used_i >= MAX_PER_KEY
            warn = has and used_i >= int(MAX_PER_KEY * .6) and not full
            is_ac = (i == st.session_state._active_idx) and has and not full
            lbl_i = slot.get("label", f"API {i+1}")
            icon = "⬜" if not has else ("🔴" if full else ("🟡" if warn else "🟢"))
            badge = "boş" if not has else ("DOLU" if full else f"{used_i}/{MAX_PER_KEY}")
            with st.expander(f"{icon} {lbl_i}{' ◀' if is_ac else ''} · {badge}", expanded=False):
                nl = st.text_input(f"İ{i}", value=lbl_i, placeholder=f"API {i+1}", label_visibility="collapsed", key=f"lbl_{i}")
                if nl != lbl_i:
                    st.session_state._api_pool[i]["label"] = nl
                    st.rerun()
                nk = st.text_input(f"K{i}", value=slot["key"], type="password", placeholder="AIzaSy...", label_visibility="collapsed", key=f"key_{i}")
                if nk != slot["key"]:
                    st.session_state._api_pool[i]["key"] = nk
                    st.rerun()
                if has:
                    p2 = min(used_i / MAX_PER_KEY, 1)
                    b2 = "#22c55e" if p2 < .6 else "#f59e0b" if p2 < .9 else "#ef4444"
                    st.markdown(f"<div class='qbar'><div class='qbar-f' style='width:{p2*100:.0f}%;background:{b2};'></div></div>", unsafe_allow_html=True)
                k1, k2, k3 = st.columns(3)
                with k1:
                    if st.button("🔄", key=f"rst_{i}", use_container_width=True, help="Kotayı sıfırla"):
                        st.session_state._api_pool[i]["used"] = 0
                        st.rerun()
                with k2:
                    if st.button("▶", key=f"act_{i}", use_container_width=True, help="Aktif yap"):
                        st.session_state._active_idx = i
                        st.rerun()
                with k3:
                    if st.button("🗑️", key=f"del_{i}", use_container_width=True, help="Sil"):
                        st.session_state._api_pool[i] = {"key": "", "used": 0, "label": f"API {i+1}"}
                        st.rerun()

    pl_cnt = len(st.session_state._playlist)
    with st.expander(f"📻 Reji Playlist · {pl_cnt} şarkı", expanded=False):
        if not st.session_state._playlist:
            st.caption("Boş. Delay Reji sekmesinden ekleyin.")
        else:
            for i, s in enumerate(st.session_state._playlist[:8]):
                b = ""
                if s.get("anons_bas"):
                    b += "🎙️B "
                if s.get("anons_son"):
                    b += "🎙️S "
                if s.get("fon_aktif"):
                    b += "🎶 "
                st.markdown(f"<div style='font-size:.68rem;color:#6b7a8d;padding:2px 0;border-bottom:1px solid #0d1420;'>{i+1}. <b style='color:#60a5fa;'>{s.get('title','?')[:18]}</b> {b}</div>", unsafe_allow_html=True)

    pl_songs = list_audio(DIRS["playlist"])
    fon_files = list_audio(DIRS["fon"])
    with st.expander(f"📂 Kütüphane · {len(pl_songs)} şarkı · {len(fon_files)} fon", expanded=False):
        arc_cnt = len(st.session_state._archive)
        st.caption(f"Arşiv: {arc_cnt} ses · Çıktı: {len(list_audio(DIRS['output']))}")

    if st.button("🚪 Çıkış Yap", use_container_width=True, key="logout_btn"):
        st.session_state._giris = False
        st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;color:#4b5c74;font-size:.61rem;'>İmaj FM v7.1 · 2026</div>", unsafe_allow_html=True)

# ═══════════════════════════ HEADER ═════════════════════════════
stat_g = st.session_state._api_stats
tk_m, tr_m = pool_stats()
ak_chk, ai_m = get_key()
rem_m = MAX_PER_KEY - st.session_state._api_pool[ai_m]["used"] if ai_m >= 0 else 0
arc_m = len(st.session_state._archive)
pl_m = len(st.session_state._playlist)

st.markdown("""<div class='hdr'><h1>🎙️ İmaj FM · Seslendirme Stüdyosu</h1>
<p><span class='ldot'></span>Gemini TTS v7.1 · Delay Reji · Yayın Otomasyonu · Fon+Anons · Ses Efektleri · RVC · Dönüştürücü</p></div>""", unsafe_allow_html=True)

c8 = st.columns(8)
defs = [("30", "Ses"), (f"{tk_m}/10", "API", "g"), (f"{tr_m}", "Kalan", "a"),
        (f"{arc_m}", "Arşiv", "b"), (f"{stat_g.get('calls', 0)}", "İstek"),
        (f"{stat_g.get('secs', 0):.0f}s", "Ses", "p"), (f"{pl_m}", "Playlist", "t"),
        (f"{len(pl_songs)}", "Şarkı")]
for col, (val, lbl, *cls) in zip(c8, defs):
    c = cls[0] if cls else ""
    with col:
        st.markdown(f'<div class="mbox {c}"><div class="v">{val}</div><div class="l">{lbl}</div></div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

if not GEMINI_OK:
    st.error("⚠️ `google-genai` kütüphanesi kurulu değil! `pip install google-genai` ile kurun (TTS dışındaki araçlar çalışmaya devam eder).")
elif ak_chk is None:
    st.warning("⛔ Kullanılabilir API anahtarı yok! TTS üretimi için sol panelden anahtar ekleyin veya kotayı sıfırlayın.")
elif rem_m <= 2:
    st.warning(f"⚠️ API {ai_m+1} limitine yakın ({rem_m} kaldı).")

# ═══════════════════════════ SEKMELER ════════════════════════════
tabs = st.tabs([
    "🎤 Tek", "🎭 Çift", "📦 Toplu", "🔬 A/B Test",
    "⭐ Favoriler", "📻 Delay Reji", "🎛️ Fon+Anons",
    "🚀 Yayın Otomasyon", "🎚️ Ses Efektleri", "📁 Kütüphane",
    "📂 Arşiv", "📰 Podcast RSS", "📅 Yayın Takvimi",
    "🗣️ Ses Klonlama", "🔄 Dönüştürücü"
])
t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15 = tabs

# ════════════════ T1 — TEK KONUŞMACI ════════════════════════════
with t1:
    cL, cR = st.columns([1.05, 1], gap="large")
    with cL:
        st.markdown("<span class='sl'>▶ Şablon</span>", unsafe_allow_html=True)
        tmpl1 = st.selectbox("Ş1", ["— Yok —"] + list(TEMPLATES.keys()), label_visibility="collapsed", key="tmpl1")
        if tmpl1 != "— Yok —" and st.button("📥 Yükle", key="ltmpl1"):
            st.session_state._t_tek = TEMPLATES[tmpl1]
            st.session_state.ta1 = TEMPLATES[tmpl1]
            st.rerun()
        st.markdown("<span class='sl'>▶ Model</span>", unsafe_allow_html=True)
        m1l = st.selectbox("M1", list(MODELS.values()), label_visibility="collapsed", key="m1")
        mdl1 = [k for k, v in MODELS.items() if v == m1l][0]
        st.markdown("<span class='sl'>▶ Dil</span>", unsafe_allow_html=True)
        l1l = st.selectbox("L1", list(LANGUAGES.values()), label_visibility="collapsed", index=1, key="l1")
        lng1 = [k for k, v in LANGUAGES.items() if v == l1l][0]
        st.markdown("<span class='sl'>▶ Ses</span>", unsafe_allow_html=True)
        cn1 = st.radio("CN1", ["Tümü", "♀ Kadın", "♂ Erkek"], horizontal=True, label_visibility="collapsed", key="cn1")
        f1 = {k: v for k, v in VOICES.items() if cn1 == "Tümü" or (cn1 == "♀ Kadın" and v[0] == "♀") or (cn1 == "♂ Erkek" and v[0] == "♂")}
        vc1 = st.selectbox("V1", list(f1.keys()), format_func=lambda x: f"{VOICES[x][0]} {x} — {VOICES[x][1]}", label_visibility="collapsed", key="v1")
        eq1 = st.selectbox("EQ", EQ_OPTS, label_visibility="collapsed", key="eq1")
        st.markdown("<span class='sl'>▶ Stil</span>", unsafe_allow_html=True)
        sty1 = style_w("t1")
        ak1, ai1 = get_key()
        r1 = MAX_PER_KEY - st.session_state._api_pool[ai1]["used"] if ai1 >= 0 else 0
        st.markdown(f"<div class='card b'><b>{VOICES[vc1][0]} {vc1}</b> — {VOICES[vc1][1]}<br><span style='color:#3a7bd5;'>{m1l[:22]}</span> · <span style='color:#22c55e;'>API {ai1+1 if ai1>=0 else '-'}</span> · {r1} kalan</div>", unsafe_allow_html=True)
        st.markdown("<span class='sl'>▶ Favorilere Ekle</span>", unsafe_allow_html=True)
        fa, fb = st.columns([2, 1])
        with fa:
            fname1 = st.text_input("FN", "", placeholder="Favori ismi…", label_visibility="collapsed", key="fname1")
        with fb:
            if st.button("⭐ Ekle", key="fadd1", use_container_width=True):
                cur_t = st.session_state.get("ta1", st.session_state._t_tek)
                if fname1.strip() and cur_t.strip():
                    st.session_state._favorites.append({
                        "id": uuid.uuid4().hex[:8],
                        "name": fname1.strip(),
                        "text": cur_t,
                        "voice": vc1,
                        "model": mdl1,
                        "lang": lng1
                    })
                    st.success("⭐ Eklendi!")
                    time.sleep(0.3)
                    st.rerun()
    with cR:
        st.markdown("<span class='sl'>▶ Anons Metni</span>", unsafe_allow_html=True)
        tag_btns("_t_tek", "ta1", "t1")
        txt1 = st.text_area("TT1", height=220, label_visibility="collapsed", key="ta1", placeholder="Metni buraya yazın…")
        st.session_state._t_tek = txt1
        txt_stats(txt1)

        b_gen, b_prom = st.columns([2, 1])
        with b_gen:
            gen_clicked = st.button(f"🔴 {vc1} ile Seslendir", type="primary", use_container_width=True, key="btn1")
        with b_prom:
            prom_clicked = st.button("📺 Canlı Prompter", use_container_width=True, key="btn_prompter")

        if prom_clicked:
            if txt1.strip():
                live_text_flow(txt1, delay=0.08)
            else:
                st.warning("⚠️ Prompter için metin boş.")

        if gen_clicked:
            if not txt1.strip():
                st.warning("⚠️ Metin boş.")
            else:
                with st.spinner(f"🎙️ {vc1} seslendiriyor…"):
                    try:
                        raw, mime, used_ai = tts_single(mdl1, txt1, vc1, lng1, sty1)
                        wav = pcm2wav(raw, mime)
                        if PYDUB_OK and eq1 != "Ham":
                            seg = apply_eq(AudioSegment.from_file(io.BytesIO(wav), format="wav"), eq1)
                            wav = seg_to_wav(norm_seg(seg))
                        arc_add(vc1, mdl1, lng1, sty1, txt1, wav, "tek")
                        st.session_state._last_tek = {
                            "wav": wav, "voice": vc1, "ai": used_ai,
                            "dn": f"imajfm_{vc1.lower()}_{lng1}.wav"
                        }
                    except Exception as e:
                        st.error(f"❌ {e}")

        if st.session_state._last_tek:
            lt = st.session_state._last_tek
            res_card(lt["wav"], lt["voice"], lt["ai"], "dl1", lt["dn"])

# ════════════════ T2 — ÇİFT KONUŞMACI ══════════════════════════
with t2:
    st.markdown("<div class='card b'>🎭 İki konuşmacı — Multi-speaker Gemini TTS · Tek WAV çıktı</div>", unsafe_allow_html=True)
    cL2, cR2 = st.columns([1.05, 1], gap="large")
    with cL2:
        tmpl2 = st.selectbox("Ş2", ["— Yok —"] + list(TEMPLATES.keys()), label_visibility="collapsed", key="tmpl2")
        if tmpl2 != "— Yok —" and st.button("📥 Yükle", key="ltmpl2"):
            st.session_state._t_cift = TEMPLATES[tmpl2]
            st.session_state.ta2 = TEMPLATES[tmpl2]
            st.rerun()
        m2l = st.selectbox("M2", list(MODELS.values()), label_visibility="collapsed", key="m2")
        mdl2 = [k for k, v in MODELS.items() if v == m2l][0]
        l2l = st.selectbox("L2", list(LANGUAGES.values()), label_visibility="collapsed", index=1, key="l2")
        lng2 = [k for k, v in LANGUAGES.items() if v == l2l][0]
        st.markdown("<span class='sl'>▶ Konuşmacı 1</span>", unsafe_allow_html=True)
        ca, cb = st.columns([1, 2])
        with ca:
            sp1n = st.text_input("S1N", "Sunucu", label_visibility="collapsed", key="sp1n")
        with cb:
            sp1v = st.selectbox("S1V", list(VOICES.keys()), format_func=lambda x: f"{VOICES[x][0]} {x}", label_visibility="collapsed", index=list(VOICES.keys()).index("Kore"), key="sp1v")
        st.markdown("<span class='sl'>▶ Konuşmacı 2</span>", unsafe_allow_html=True)
        cc, cd = st.columns([1, 2])
        with cc:
            sp2n = st.text_input("S2N", "Misafir", label_visibility="collapsed", key="sp2n")
        with cd:
            sp2v = st.selectbox("S2V", list(VOICES.keys()), format_func=lambda x: f"{VOICES[x][0]} {x}", label_visibility="collapsed", index=list(VOICES.keys()).index("Fenrir"), key="sp2v")
        eq2 = st.selectbox("EQ2", EQ_OPTS, label_visibility="collapsed", key="eq2")
        ak2, ai2 = get_key()
        r2 = MAX_PER_KEY - st.session_state._api_pool[ai2]["used"] if ai2 >= 0 else 0
        st.markdown(f"<div class='card b'><code style='color:#60a5fa;'>{sp1n}</code>→<b>{sp1v}</b> · <code style='color:#f87171;'>{sp2n}</code>→<b>{sp2v}</b><br>API {ai2+1 if ai2>=0 else '-'} · {r2} kalan</div>", unsafe_allow_html=True)
    with cR2:
        st.markdown("<span class='sl'>▶ Diyalog</span>", unsafe_allow_html=True)
        tag_btns("_t_cift", "ta2", "t2")
        txt2 = st.text_area("TT2", height=220, label_visibility="collapsed", key="ta2")
        st.session_state._t_cift = txt2
        txt_stats(txt2)
        if st.button(f"🔴 {sp1n}&{sp2n} Diyalog", type="primary", use_container_width=True, key="btn2"):
            if not txt2.strip():
                st.warning("⚠️ Metin boş.")
            else:
                with st.spinner("🎭 Diyalog üretiliyor…"):
                    try:
                        raw2, mime2, used_ai2 = tts_multi(mdl2, txt2, sp1n, sp1v, sp2n, sp2v, lng2)
                        wav2 = pcm2wav(raw2, mime2)
                        if PYDUB_OK and eq2 != "Ham":
                            s2 = apply_eq(AudioSegment.from_file(io.BytesIO(wav2), format="wav"), eq2)
                            wav2 = seg_to_wav(norm_seg(s2))
                        arc_add(f"{sp1v}+{sp2v}", mdl2, lng2, "", txt2, wav2, "cift")
                        st.session_state._last_cift = {
                            "wav": wav2, "voice": sp1v, "ai": used_ai2,
                            "dn": f"imajfm_diyalog_{sp1v.lower()}.wav"
                        }
                    except Exception as e:
                        st.error(f"❌ {e}")

        if st.session_state._last_cift:
            lc2 = st.session_state._last_cift
            res_card(lc2["wav"], lc2["voice"], lc2["ai"], "dl2", lc2["dn"])

# ════════════════ T3 — TOPLU TTS ════════════════════════════════
with t3:
    st.markdown("<div class='card b'>📦 Her satır ayrı WAV — TXT/CSV yükle veya manuel yaz — ZIP indir</div>", unsafe_allow_html=True)
    btab1, btab2 = st.tabs(["✏️ Manuel Liste", "📄 TXT/CSV Yükle"])
    with btab1:
        cL3, cR3 = st.columns([1, 1.2], gap="large")
        with cL3:
            m3l = st.selectbox("M3", list(MODELS.values()), label_visibility="collapsed", key="m3")
            mdl3 = [k for k, v in MODELS.items() if v == m3l][0]
            l3l = st.selectbox("L3", list(LANGUAGES.values()), label_visibility="collapsed", index=1, key="l3")
            lng3 = [k for k, v in LANGUAGES.items() if v == l3l][0]
            cn3 = st.radio("CN3", ["Tümü", "♀ Kadın", "♂ Erkek"], horizontal=True, label_visibility="collapsed", key="cn3")
            f3 = {k: v for k, v in VOICES.items() if cn3 == "Tümü" or (cn3 == "♀ Kadın" and v[0] == "♀") or (cn3 == "♂ Erkek" and v[0] == "♂")}
            vc3 = st.selectbox("V3", list(f3.keys()), format_func=lambda x: f"{VOICES[x][0]} {x}", label_visibility="collapsed", key="v3")
            eq3 = st.selectbox("EQ3", EQ_OPTS, label_visibility="collapsed", key="eq3")
            sty3 = st.text_area("STY3", "", height=50, label_visibility="collapsed", placeholder="Stil (opsiyonel)", key="sty3")
            rpm_delay = st.slider("İstekler arası bekleme (sn — Free Tier 429 koruması)", 0, 21, 0, key="rpm_delay3")
            _, tr3 = pool_stats()
            lines3p = [l.strip() for l in st.session_state._t_bulk.splitlines() if l.strip()]
            st.markdown(f"<div class='card {'a' if len(lines3p)>tr3 else 'b'}'>{len(lines3p)} satır · {tr3} kalan</div>", unsafe_allow_html=True)
        with cR3:
            txt3 = st.text_area("TT3", value=st.session_state._t_bulk, height=220, label_visibility="collapsed", key="ta3", placeholder="Her satır bir ses…")
            st.session_state._t_bulk = txt3
            lines3 = [l.strip() for l in txt3.splitlines() if l.strip()]
            st.markdown(f"<div style='font-size:.67rem;color:#6b7a8d;'>{len(lines3)} satır</div>", unsafe_allow_html=True)
            if st.button(f"🔴 {len(lines3)} Satırı Üret", type="primary", use_container_width=True, key="btn3"):
                if not lines3:
                    st.warning("⚠️ Satır yok.")
                else:
                    res3, err3 = [], []
                    prog3 = st.progress(0)
                    sts3 = st.empty()
                    for idx3, line3 in enumerate(lines3):
                        sts3.markdown(f"<div style='font-size:.73rem;color:#6b7a8d;'>🎙️ {idx3+1}/{len(lines3)}: {line3[:40]}</div>", unsafe_allow_html=True)
                        try:
                            raw3, mime3, _ = tts_single(mdl3, line3, vc3, lng3, sty3)
                            wav3 = pcm2wav(raw3, mime3)
                            if PYDUB_OK and eq3 != "Ham":
                                s3 = apply_eq(AudioSegment.from_file(io.BytesIO(wav3), format="wav"), eq3)
                                wav3 = seg_to_wav(norm_seg(s3))
                            arc_add(vc3, mdl3, lng3, sty3, line3, wav3, "bulk")
                            fn3 = f"{idx3+1:02d}_{vc3.lower()}_{re.sub(r'[^\w]', '_', line3[:12])}.wav"
                            res3.append((fn3, wav3, line3))
                        except Exception as e:
                            err3.append(f"Satır {idx3+1}: {e}")
                        prog3.progress((idx3 + 1) / len(lines3))
                        if rpm_delay > 0 and idx3 < len(lines3) - 1:
                            time.sleep(rpm_delay)
                    prog3.empty()
                    sts3.empty()
                    st.session_state._last_bulk_manual = {"res": res3, "err": err3, "zip": make_zip([(fn, wb) for fn, wb, _ in res3]) if res3 else None, "vc": vc3}

            if st.session_state._last_bulk_manual:
                bm = st.session_state._last_bulk_manual
                if bm["res"]:
                    st.markdown(f"<div class='card g'>✅ {len(bm['res'])} ses üretildi</div>", unsafe_allow_html=True)
                    st.download_button("📦 ZIP İndir", bm["zip"], file_name=f"bulk_{bm['vc'].lower()}.zip", mime="application/zip", use_container_width=True, key="dl3zip")
                    for fi_b, (fn, wb, ln) in enumerate(bm["res"]):
                        with st.expander(f"🔊 {fn[:45]}", expanded=False):
                            st.audio(wb, format="audio/wav")
                            st.download_button("💾 İndir", wb, file_name=fn, mime="audio/wav", key=f"dl3_{fi_b}_{fn}")
                for e in bm["err"]:
                    st.markdown(f"<div class='card r'>❌ {e}</div>", unsafe_allow_html=True)

    with btab2:
        up_f = st.file_uploader("TXT veya CSV Yükle", type=["txt", "csv"], key="bulk_up")
        if up_f:
            content = up_f.getvalue().decode("utf-8", "ignore")
            lines_u = [l.strip() for l in content.splitlines() if l.strip()]
            if up_f.name.endswith(".csv"):
                lines_u = [l.split(",")[0].strip().strip('"') for l in lines_u if l.split(",")[0].strip()]
            st.success(f"✅ {len(lines_u)} satır okundu")
            st.session_state["bulk_up_lines"] = lines_u
            for i, l in enumerate(lines_u[:5]):
                st.markdown(f"<div style='font-size:.73rem;color:#6b7a8d;'>{i+1}. {l[:70]}</div>", unsafe_allow_html=True)
        if st.session_state.get("bulk_up_lines"):
            mu_ml = st.selectbox("Model", list(MODELS.values()), label_visibility="collapsed", key="mu_m")
            mu_mdl = [k for k, v in MODELS.items() if v == mu_ml][0]
            mu_ll = st.selectbox("Dil", list(LANGUAGES.values()), label_visibility="collapsed", index=1, key="mu_l")
            mu_lng = [k for k, v in LANGUAGES.items() if v == mu_ll][0]
            mu_vc = st.selectbox("Ses", list(VOICES.keys()), format_func=lambda x: f"{VOICES[x][0]} {x}", label_visibility="collapsed", key="mu_v")
            if st.button("🚀 Dosyadan Toplu Üret", type="primary", use_container_width=True, key="mu_btn"):
                lu = st.session_state["bulk_up_lines"]
                res_u = []
                prog_u = st.progress(0)
                for i, ln in enumerate(lu):
                    try:
                        rw, mm, _ = tts_single(mu_mdl, ln, mu_vc, mu_lng, "")
                        wv = pcm2wav(rw, mm)
                        arc_add(mu_vc, mu_mdl, mu_lng, "", ln, wv, "bulk-file")
                        res_u.append((f"{i+1:03d}_{mu_vc.lower()}.wav", wv))
                    except Exception as e:
                        st.warning(f"Satır {i+1}: {e}")
                    prog_u.progress((i + 1) / len(lu))
                if res_u:
                    st.session_state._last_bulk_file = {"zip": make_zip(res_u), "count": len(res_u)}
            if st.session_state._last_bulk_file:
                bf = st.session_state._last_bulk_file
                st.success(f"✅ {bf['count']} ses üretildi!")
                st.download_button("📦 ZIP İndir", bf["zip"], "bulk_dosya.zip", "application/zip", key="mu_zip")

# ════════════════ T4 — A/B TEST ══════════════════════════════════
with t4:
    st.markdown("<div class='card p'>🔬 Aynı metni iki farklı ses/model/stil ile karşılaştır</div>", unsafe_allow_html=True)
    ab_c1, ab_c2 = st.columns(2, gap="large")

    def ab_col(col, label, prefix, txt_key, ta_key, store_key, model_key, lang_key, voice_key, eq_key, style_key, dl_key, btn_key, arc_mode):
        with col:
            st.markdown(f"<div style='font-family:Syne,sans-serif;font-size:.7rem;font-weight:800;letter-spacing:.14em;color:{'#a78bfa' if 'A' in label else '#fb923c'};text-transform:uppercase;margin-bottom:7px;'>{label}</div>", unsafe_allow_html=True)
            ml = st.selectbox("M", list(MODELS.values()), label_visibility="collapsed", key=model_key)
            mdl = [k for k, v in MODELS.items() if v == ml][0]
            ll = st.selectbox("L", list(LANGUAGES.values()), label_visibility="collapsed", index=1, key=lang_key)
            lng = [k for k, v in LANGUAGES.items() if v == ll][0]
            cn = st.radio("CN", ["Tümü", "♀", "♂"], horizontal=True, label_visibility="collapsed", key=f"{prefix}_cn")
            fv = {k: v for k, v in VOICES.items() if cn == "Tümü" or (cn == "♀" and v[0] == "♀") or (cn == "♂" and v[0] == "♂")}
            vc = st.selectbox("V", list(fv.keys()), format_func=lambda x: f"{VOICES[x][0]} {x}", label_visibility="collapsed", key=voice_key)
            eq = st.selectbox("EQ", EQ_OPTS, label_visibility="collapsed", key=eq_key)
            ps = st.selectbox("PS", list(STYLE_PRESETS.keys()), label_visibility="collapsed", key=f"{prefix}_ps")
            sty = st.text_area("STY", value=STYLE_PRESETS[ps], height=50, label_visibility="collapsed", key=f"{style_key}_{ps}")
            tag_btns(txt_key, ta_key, prefix)
            txt = st.text_area("TXT", height=120, label_visibility="collapsed", key=ta_key)
            st.session_state[txt_key] = txt
            if st.button(f"🔴 {label} Üret", use_container_width=True, key=btn_key):
                if not txt.strip():
                    st.warning("Metin boş")
                else:
                    with st.spinner(f"{vc} üretiyor…"):
                        try:
                            rw, mm, _ = tts_single(mdl, txt, vc, lng, sty)
                            wv = pcm2wav(rw, mm)
                            if PYDUB_OK and eq != "Ham":
                                s = apply_eq(AudioSegment.from_file(io.BytesIO(wv), format="wav"), eq)
                                wv = seg_to_wav(norm_seg(s))
                            arc_add(vc, mdl, lng, sty, txt, wv, arc_mode)
                            st.session_state[store_key] = {"wav": wv, "vc": vc, "qs": qs_bytes(wv), "dur": dur_bytes(wv)}
                        except Exception as e:
                            st.error(f"❌ {e}")
            if st.session_state.get(store_key):
                ab_d = st.session_state[store_key]
                st.markdown(f"<div class='card {'p' if 'A' in label else 'a'}'>{ab_d['vc']} · {ab_d['dur']:.1f}s · {ab_d['qs']}/100</div>", unsafe_allow_html=True)
                st.audio(ab_d["wav"], format="audio/wav")
                draw_wf(ab_d["wav"])
                st.download_button(f"💾 {label}", ab_d["wav"], file_name=f"{prefix}_{ab_d['vc'].lower()}.wav", mime="audio/wav", key=dl_key)

    ab_col(ab_c1, "🅐 VERSİYON A", "ab_a", "_t_ab1", "ab_a_ta", "_last_ab_a", "masel", "lasel", "vasel", "eqasel", "styasel", "dlab", "btnab1", "ab-A")
    ab_col(ab_c2, "🅑 VERSİYON B", "ab_b", "_t_ab2", "ab_b_ta", "_last_ab_b", "mbsel", "lbsel", "vbsel", "eqbsel", "stybsel", "dlbb", "btnab2", "ab-B")

# ════════════════ T5 — FAVORİLER ════════════════════════════════
with t5:
    favs = st.session_state._favorites
    if not favs:
        st.markdown("<div style='text-align:center;padding:45px;color:#6b7a8d;'><div style='font-size:2rem;'>⭐</div><div style='font-family:Syne,sans-serif;margin-top:7px;'>Favori metin yok</div><div style='font-size:.78rem;margin-top:4px;'>Tek sekmesinden ⭐ Ekle butonunu kullanın.</div></div>", unsafe_allow_html=True)
    else:
        hf1, hf2 = st.columns([3, 1])
        with hf1:
            st.markdown(f"<span class='sl'>▶ {len(favs)} Favori</span>", unsafe_allow_html=True)
        with hf2:
            if st.button("🗑️ Tümünü Sil", use_container_width=True, key="fav_clr"):
                st.session_state._favorites = []
                st.rerun()
        for fi, fv in enumerate(favs):
            fc1, fc2, fc3, fc4 = st.columns([2, .8, .8, .5])
            with fc1:
                st.markdown(f"<div class='fav-card'><div class='fav-name'>⭐ {fv['name']}</div><div class='fav-prev'>{fv.get('voice','—')} · {fv.get('lang','—')}</div><div class='fav-prev'>{fv['text'][:55]}</div></div>", unsafe_allow_html=True)
            with fc2:
                if st.button("📋", key=f"fcp_{fv['id']}", use_container_width=True, help="Tek sekmesine yükle"):
                    st.session_state._t_tek = fv["text"]
                    st.session_state.ta1 = fv["text"]
                    st.success("✅ Tek sekmesine yüklendi!")
            with fc3:
                if st.button("🔴", key=f"fsp_{fv['id']}", use_container_width=True, help="Seslendir"):
                    with st.spinner("🎙️ Üretiyor…"):
                        try:
                            rwf, mmf, _ = tts_single(fv.get("model", "gemini-2.5-flash-tts"), fv["text"], fv.get("voice", "Kore"), fv.get("lang", "tr-TR"), "")
                            wvf = pcm2wav(rwf, mmf)
                            arc_add(fv.get("voice", "Kore"), fv.get("model", ""), fv.get("lang", ""), "", fv["text"], wvf, "fav")
                            st.session_state[f"_fw_{fv['id']}"] = wvf
                        except Exception as e:
                            st.error(f"❌ {e}")
            with fc4:
                if st.button("🗑️", key=f"fdel_{fv['id']}", use_container_width=True):
                    st.session_state._favorites.pop(fi)
                    st.rerun()
            if f"_fw_{fv['id']}" in st.session_state:
                fw = st.session_state[f"_fw_{fv['id']}"]
                st.audio(fw, format="audio/wav")
                st.download_button("💾 İndir", fw, file_name=f"fav_{sfn(fv['name'], 12)}.wav", mime="audio/wav", key=f"fdl_{fv['id']}")

# ════════════════ T6 — DELAY REJİ ═══════════════════════════════
with t6:
    st.markdown("<div class='rjhdr'><h2>📻 Delay Reji — Yayın Otomasyonu</h2><p>Playlist · İnteraktif Sıralama · Şarkı başı/sonu anons · Fon müzik geçişleri · Yayın planı · ZIP</p></div>", unsafe_allow_html=True)
    rj1, rj2, rj3, rj4 = st.tabs(["🎵 Playlist", "⚙️ Ayarlar", "📋 Yayın Planı", "🎬 Üretim & ZIP"])

    with rj1:
        pl = st.session_state._playlist
        st.markdown("<span class='sl'>▶ Yeni Şarkı Ekle</span>", unsafe_allow_html=True)
        nc1, nc2, nc3, nc4 = st.columns([2, 1.5, .5, .5])
        with nc1:
            nt = st.text_input("Şarkı", "", placeholder="Şarkı adı…", label_visibility="collapsed", key="nt")
        with nc2:
            na = st.text_input("Sanatçı", "", placeholder="Sanatçı…", label_visibility="collapsed", key="na")
        with nc3:
            ndm = st.number_input("Dk", 0, 30, 3, label_visibility="collapsed", key="ndm")
        with nc4:
            nds = st.number_input("Sn", 0, 59, 30, label_visibility="collapsed", key="nds")
        ba, bb = st.columns(2)
        with ba:
            if st.button("➕ Ekle", use_container_width=True, key="add_song"):
                if nt.strip():
                    st.session_state._playlist.append({
                        "id": song_uid(),
                        "title": nt.strip(),
                        "artist": na.strip() or "Bilinmeyen",
                        "duration_min": int(ndm),
                        "duration_sec": int(nds),
                        "anons_bas": False,
                        "anons_son": False,
                        "anons_bas_text": "",
                        "anons_son_text": "",
                        "fon_aktif": False,
                        "fon_tip": "📻 Radyo Klasik",
                        "anons_wav_bas": None,
                        "anons_wav_son": None
                    })
                    st.session_state._rj_plan_ok = False
                    st.rerun()
                else:
                    st.warning("Şarkı adı boş olamaz.")
        with bb:
            if st.button("🎲 Demo Playlist", use_container_width=True, key="demo_pl"):
                demos = [
                    ("Gece Yarısı", "Sezen Aksu", 3, 45),
                    ("Yüksek Yüksek Tepelere", "Barış Manço", 4, 12),
                    ("Oy Benim Sarı Turnam", "Neşet Ertaş", 3, 55),
                    ("Hayatımın Anlamı", "MFÖ", 3, 28),
                    ("Leylim Ley", "Zülfü Livaneli", 4, 5),
                    ("Mavi Bisiklet", "Sıla", 3, 48),
                    ("Seni Bana Verecekler", "Tarkan", 4, 20)
                ]
                st.session_state._playlist = [{
                    "id": song_uid(), "title": t, "artist": ar, "duration_min": dm, "duration_sec": ds,
                    "anons_bas": False, "anons_son": False, "anons_bas_text": "", "anons_son_text": "",
                    "fon_aktif": False, "fon_tip": "📻 Radyo Klasik",
                    "anons_wav_bas": None, "anons_wav_son": None
                } for t, ar, dm, ds in demos]
                st.session_state._rj_plan_ok = False
                st.rerun()

        st.markdown("<span class='sl'>▶ Şarkı Dosyası Yükle (MP3/WAV — ID3 Otomatik Okuma)</span>", unsafe_allow_html=True)
        pl_up = st.file_uploader("Şarkı dosyaları", type=["mp3", "wav", "ogg", "flac", "m4a"], accept_multiple_files=True, key="pl_up")
        if pl_up:
            added = 0
            for uf in pl_up:
                uid_up = f"pl_{uf.name}_{uf.size}"
                if uid_up in st.session_state._processed_uploads:
                    continue
                dp, _ = save_upload(uf, DIRS["playlist"], uf.name, convert_to_wav=False)
                if dp:
                    st.session_state._processed_uploads.add(uid_up)
                    d = dur_file(dp)
                    mn, sc = divmod(int(d), 60)
                    meta = read_id3_meta(dp)
                    added += 1
                    st.session_state._playlist.append({
                        "id": song_uid(),
                        "title": meta["title"],
                        "artist": meta["artist"],
                        "duration_min": mn,
                        "duration_sec": sc,
                        "anons_bas": False, "anons_son": False,
                        "anons_bas_text": "", "anons_son_text": "",
                        "fon_aktif": False, "fon_tip": "📻 Radyo Klasik",
                        "anons_wav_bas": None, "anons_wav_son": None,
                        "local_file": dp
                    })
            if added:
                st.success(f"✅ {added} şarkı ID3 bilgileriyle eklendi!")
                st.session_state._rj_plan_ok = False
                st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)
        if not pl:
            st.markdown("<div style='text-align:center;padding:28px;color:#6b7a8d;'>🎵 Playlist boş</div>", unsafe_allow_html=True)
        else:
            ts2 = sum(song_dur(s) for s in pl)
            bc = sum(1 for s in pl if s.get("anons_bas"))
            sc2 = sum(1 for s in pl if s.get("anons_son"))
            fc = sum(1 for s in pl if s.get("fon_aktif"))
            pm1, pm2, pm3, pm4, pm5 = st.columns(5)
            with pm1:
                st.markdown(f'<div class="mbox t"><div class="v">{len(pl)}</div><div class="l">Şarkı</div></div>', unsafe_allow_html=True)
            with pm2:
                st.markdown(f'<div class="mbox b"><div class="v">{fmt_dur(ts2)}</div><div class="l">Süre</div></div>', unsafe_allow_html=True)
            with pm3:
                st.markdown(f'<div class="mbox a"><div class="v">{bc}</div><div class="l">Baş Anons</div></div>', unsafe_allow_html=True)
            with pm4:
                st.markdown(f'<div class="mbox a"><div class="v">{sc2}</div><div class="l">Son Anons</div></div>', unsafe_allow_html=True)
            with pm5:
                st.markdown(f'<div class="mbox g"><div class="v">{fc}</div><div class="l">Fon</div></div>', unsafe_allow_html=True)

            # İnteraktif Sıra Düzenleyici
            with st.expander("🔀 Hızlı Sıra & Anons Düzenleyici (Tablo)", expanded=False):
                rows = [
                    {
                        "Sıra": i + 1,
                        "Şarkı": s["title"],
                        "Sanatçı": s["artist"],
                        "Baş Anons": bool(s.get("anons_bas", False)),
                        "Son Anons": bool(s.get("anons_son", False)),
                        "Fon": bool(s.get("fon_aktif", False)),
                        "_idx": i,
                    }
                    for i, s in enumerate(pl)
                ]
                edited = st.data_editor(
                    rows,
                    column_config={
                        "Sıra": st.column_config.NumberColumn(min_value=1, max_value=len(pl), step=1),
                        "_idx": None,
                    },
                    disabled=["Şarkı", "Sanatçı"],
                    hide_index=True,
                    use_container_width=True,
                    key="pl_editor"
                )
                if st.button("✅ Sıralamayı ve İşaretleri Uygula", use_container_width=True, key="apply_pl_order"):
                    sorted_rows = sorted(edited, key=lambda r: r["Sıra"])
                    new_pl = []
                    for r in sorted_rows:
                        item = pl[r["_idx"]]
                        item["anons_bas"] = r["Baş Anons"]
                        item["anons_son"] = r["Son Anons"]
                        item["fon_aktif"] = r["Fon"]
                        if item["anons_bas"] and not item.get("anons_bas_text"):
                            item["anons_bas_text"] = auto_bas(item)
                        if item["anons_son"] and not item.get("anons_son_text"):
                            item["anons_son_text"] = auto_son(item)
                        new_pl.append(item)
                    st.session_state._playlist = new_pl
                    st.session_state._rj_plan_ok = False
                    st.rerun()

            st.markdown("<br><span class='sl'>▶ Şarkı Listesi</span>", unsafe_allow_html=True)
            for si, song in enumerate(pl):
                sid = song["id"]
                ds = song_dur(song)
                hb = song.get("anons_bas", False)
                hs = song.get("anons_son", False)
                hf = song.get("fon_aktif", False)
                with st.expander(f"🎵 {si+1:02d}. {song.get('artist','?')} — {song.get('title','?')}  [{fmt_dur(ds)}]", expanded=False):
                    e1, e2, e3, e4 = st.columns([2, 1.5, .5, .5])
                    with e1:
                        nt2 = st.text_input("Başlık", value=song["title"], label_visibility="collapsed", key=f"et_{sid}")
                        if nt2 != song["title"]:
                            st.session_state._playlist[si]["title"] = nt2
                            st.session_state._rj_plan_ok = False
                            st.rerun()
                    with e2:
                        na2 = st.text_input("Sanatçı", value=song["artist"], label_visibility="collapsed", key=f"ea_{sid}")
                        if na2 != song["artist"]:
                            st.session_state._playlist[si]["artist"] = na2
                            st.session_state._rj_plan_ok = False
                            st.rerun()
                    with e3:
                        ndm2 = st.number_input("Dk", 0, 30, int(song["duration_min"]), label_visibility="collapsed", key=f"edm_{sid}")
                        if ndm2 != song["duration_min"]:
                            st.session_state._playlist[si]["duration_min"] = int(ndm2)
                            st.session_state._rj_plan_ok = False
                            st.rerun()
                    with e4:
                        nds2 = st.number_input("Sn", 0, 59, int(song["duration_sec"]), label_visibility="collapsed", key=f"eds_{sid}")
                        if nds2 != song["duration_sec"]:
                            st.session_state._playlist[si]["duration_sec"] = int(nds2)
                            st.session_state._rj_plan_ok = False
                            st.rerun()
                    st.markdown("<hr>", unsafe_allow_html=True)
                    tg1, tg2, tg3 = st.columns(3)
                    with tg1:
                        nb = st.checkbox("🎙️ Şarkı Başı Anonsu", value=hb, key=f"cb_{sid}")
                        if nb != hb:
                            st.session_state._playlist[si]["anons_bas"] = nb
                            if nb and not song.get("anons_bas_text"):
                                st.session_state._playlist[si]["anons_bas_text"] = auto_bas(song)
                            st.session_state._rj_plan_ok = False
                            st.rerun()
                    with tg2:
                        ns2 = st.checkbox("🎙️ Şarkı Sonu Anonsu", value=hs, key=f"cs_{sid}")
                        if ns2 != hs:
                            st.session_state._playlist[si]["anons_son"] = ns2
                            if ns2 and not song.get("anons_son_text"):
                                st.session_state._playlist[si]["anons_son_text"] = auto_son(song)
                            st.session_state._rj_plan_ok = False
                            st.rerun()
                    with tg3:
                        nf2 = st.checkbox("🎶 Fon Müzik Geçişi", value=hf, key=f"cf_{sid}")
                        if nf2 != hf:
                            st.session_state._playlist[si]["fon_aktif"] = nf2
                            st.session_state._rj_plan_ok = False
                            st.rerun()
                    if song.get("fon_aktif"):
                        fo = list(FON_TIPLERI.keys())
                        cf = song.get("fon_tip", "📻 Radyo Klasik")
                        ci = fo.index(cf) if cf in fo else 0
                        nft = st.selectbox("Fon Tipi", fo, index=ci, label_visibility="collapsed", key=f"ft_{sid}")
                        if nft != cf:
                            st.session_state._playlist[si]["fon_tip"] = nft
                            st.session_state._rj_plan_ok = False
                            st.rerun()
                        st.markdown(f"<div style='font-size:.67rem;color:#10b981;'>ℹ️ {FON_TIPLERI[nft]}</div>", unsafe_allow_html=True)
                    if song.get("anons_bas"):
                        st.markdown("<span class='sl3'>▸ Baş Anons Metni</span>", unsafe_allow_html=True)
                        bd = song.get("anons_bas_text") or auto_bas(song)
                        nbt = st.text_area("BT", value=bd, height=78, label_visibility="collapsed", key=f"bat_{sid}")
                        if nbt != song.get("anons_bas_text", ""):
                            st.session_state._playlist[si]["anons_bas_text"] = nbt
                            st.session_state._playlist[si]["anons_wav_bas"] = None
                        if song.get("anons_wav_bas"):
                            st.markdown("<div class='card g' style='font-size:.71rem;'>✅ Ses üretildi</div>", unsafe_allow_html=True)
                            st.audio(song["anons_wav_bas"], format="audio/wav")
                        else:
                            st.markdown("<div class='card a' style='font-size:.71rem;'>⏳ Henüz ses yok — Üretim sekmesinden üretin</div>", unsafe_allow_html=True)
                    if song.get("anons_son"):
                        st.markdown("<span class='sl3'>▸ Son Anons Metni</span>", unsafe_allow_html=True)
                        sd_t = song.get("anons_son_text") or auto_son(song)
                        nst = st.text_area("ST", value=sd_t, height=78, label_visibility="collapsed", key=f"sot_{sid}")
                        if nst != song.get("anons_son_text", ""):
                            st.session_state._playlist[si]["anons_son_text"] = nst
                            st.session_state._playlist[si]["anons_wav_son"] = None
                        if song.get("anons_wav_son"):
                            st.markdown("<div class='card g' style='font-size:.71rem;'>✅ Ses üretildi</div>", unsafe_allow_html=True)
                            st.audio(song["anons_wav_son"], format="audio/wav")
                        else:
                            st.markdown("<div class='card a' style='font-size:.71rem;'>⏳ Henüz ses yok</div>", unsafe_allow_html=True)
                    st.markdown("<hr>", unsafe_allow_html=True)
                    or1, or2, or3, or4 = st.columns(4)
                    with or1:
                        if si > 0 and st.button("⬆️", key=f"up_{sid}", use_container_width=True):
                            p2 = st.session_state._playlist
                            p2[si-1], p2[si] = p2[si], p2[si-1]
                            st.session_state._rj_plan_ok = False
                            st.rerun()
                    with or2:
                        if si < len(pl) - 1 and st.button("⬇️", key=f"dn_{sid}", use_container_width=True):
                            p2 = st.session_state._playlist
                            p2[si+1], p2[si] = p2[si], p2[si+1]
                            st.session_state._rj_plan_ok = False
                            st.rerun()
                    with or3:
                        if st.button("🔝", key=f"top_{sid}", use_container_width=True):
                            p2 = st.session_state._playlist
                            p2.insert(0, p2.pop(si))
                            st.session_state._rj_plan_ok = False
                            st.rerun()
                    with or4:
                        if st.button("🗑️", key=f"dsong_{sid}", use_container_width=True):
                            st.session_state._playlist.pop(si)
                            st.session_state._rj_plan_ok = False
                            st.rerun()
            if st.button("🗑️ Playlist'i Temizle", use_container_width=True, key="clr_pl"):
                st.session_state._playlist = []
                st.session_state._rj_plan_ok = False
                st.rerun()

    with rj2:
        st.markdown("<div class='card b'>Bu ayarlar tüm Delay Reji anonslarına uygulanır.</div>", unsafe_allow_html=True)
        ra1, ra2 = st.columns(2)
        with ra1:
            rjml = st.selectbox("Model", list(MODELS.values()), label_visibility="collapsed", key="rj_msel")
            rjmk = [k for k, v in MODELS.items() if v == rjml][0]
            st.session_state._rj_model = rjmk
            rjll = st.selectbox("Dil", list(LANGUAGES.values()), index=1, label_visibility="collapsed", key="rj_lsel")
            rjlk = [k for k, v in LANGUAGES.items() if v == rjll][0]
            st.session_state._rj_lang = rjlk
            rj_st = st.text_input("Başlangıç Saati", value=st.session_state._rj_start, placeholder="HH:MM", label_visibility="collapsed", key="rj_start_inp")
            if rj_st != st.session_state._rj_start:
                st.session_state._rj_start = rj_st
                st.session_state._rj_plan_ok = False
        with ra2:
            rjcn = st.radio("Cinsiyet", ["Tümü", "♀ Kadın", "♂ Erkek"], horizontal=True, label_visibility="collapsed", key="rj_cn")
            rjvf = {k: v for k, v in VOICES.items() if rjcn == "Tümü" or (rjcn == "♀ Kadın" and v[0] == "♀") or (rjcn == "♂ Erkek" and v[0] == "♂")}
            rjvc = st.selectbox("Ses", list(rjvf.keys()), format_func=lambda x: f"{VOICES[x][0]} {x}", label_visibility="collapsed", key="rj_vsel")
            st.session_state._rj_voice = rjvc
        st.markdown("<span class='sl'>▶ Reji Stil Talimatı</span>", unsafe_allow_html=True)
        rjps = st.selectbox("Stil Preset", list(STYLE_PRESETS.keys()), label_visibility="collapsed", key="rj_ps")
        rjsty = st.text_area("Stil", value=STYLE_PRESETS[rjps], height=72, label_visibility="collapsed", key=f"rj_sty_{rjps}")
        st.session_state._rj_style = rjsty
        st.markdown(f"<div class='card t'>🎙️ <b>{st.session_state._rj_voice}</b> · 🤖 <b>{st.session_state._rj_model.replace('gemini-','').replace('-tts','')}</b> · 🌐 <b>{st.session_state._rj_lang}</b> · 🕐 <b>{st.session_state._rj_start}</b></div>", unsafe_allow_html=True)
        if st.button("🔄 Tüm Anons Metinlerini Otomatik Yenile", use_container_width=True, key="regen_all"):
            for i, s in enumerate(st.session_state._playlist):
                if s.get("anons_bas"):
                    st.session_state._playlist[i]["anons_bas_text"] = auto_bas(s)
                    st.session_state._playlist[i]["anons_wav_bas"] = None
                if s.get("anons_son"):
                    st.session_state._playlist[i]["anons_son_text"] = auto_son(s)
                    st.session_state._playlist[i]["anons_wav_son"] = None
            st.success("✅ Metinler yenilendi!")
            st.session_state._rj_plan_ok = False

    with rj3:
        pl3 = st.session_state._playlist
        if not pl3:
            st.markdown("<div class='card r'>⚠️ Playlist boş.</div>", unsafe_allow_html=True)
        else:
            gc1, _ = st.columns([1, 2])
            with gc1:
                if st.button("📋 Yayın Planını Oluştur", type="primary", use_container_width=True, key="gen_plan"):
                    st.session_state._rj_plan = build_plan(pl3, st.session_state._rj_start)
                    st.session_state._rj_plan_ok = True
                    st.rerun()
            if not st.session_state._rj_plan_ok:
                st.markdown("<div class='card a'>ℹ️ Plan henüz oluşturulmadı.</div>", unsafe_allow_html=True)
            else:
                plan = st.session_state._rj_plan
                tp = sum(p["dur"] for p in plan)
                sb = [p for p in plan if p["type"] == "song"]
                ab = [p for p in plan if p["type"] in ("anons_bas", "anons_son")]
                fb = [p for p in plan if p["type"] == "fon"]
                et = add_time(st.session_state._rj_start, int(tp))
                pc1, pc2, pc3, pc4 = st.columns(4)
                with pc1:
                    st.markdown(f'<div class="mbox t"><div class="v">{len(sb)}</div><div class="l">Şarkı</div></div>', unsafe_allow_html=True)
                with pc2:
                    st.markdown(f'<div class="mbox a"><div class="v">{len(ab)}</div><div class="l">Anons</div></div>', unsafe_allow_html=True)
                with pc3:
                    st.markdown(f'<div class="mbox g"><div class="v">{len(fb)}</div><div class="l">Fon</div></div>', unsafe_allow_html=True)
                with pc4:
                    st.markdown(f'<div class="mbox b"><div class="v">{fmt_dur(tp)}</div><div class="l">Toplam</div></div>', unsafe_allow_html=True)
                st.markdown(f"<div style='background:#021409;border:2px solid #10b981;border-radius:10px;padding:12px 16px;margin:9px 0;'><div style='font-family:Syne,sans-serif;font-weight:800;color:#34d399;'>📡 {st.session_state._rj_start} → {et[:5]}</div><div style='font-size:.74rem;color:#528068;margin-top:3px;'>{len(plan)} blok · {len(sb)} şarkı · {len(ab)} anons · {len(fb)} fon</div></div>", unsafe_allow_html=True)
                tmap = {"song": ("ttype-song", "🎵 ŞARKI"), "anons_bas": ("ttype-anons", "🎙️ BAŞ"), "anons_son": ("ttype-anons", "🎙️ SON"), "fon": ("ttype-fon", "🎶 FON")}
                for blk in plan:
                    tcls, tlbl = tmap.get(blk["type"], ("ttype-song", "?"))
                    wi = "✅ " if blk.get("wav") else ("⏳ " if blk["type"] in ("anons_bas", "anons_son") else "")
                    st.markdown(f"<div class='tl-block'><span class='tl-time'>{blk['time'][:5]}</span><span class='tl-type {tcls}'>{tlbl}</span><span class='tl-lbl'>{wi}{blk['label']}</span><span class='tl-dur'>{fmt_dur(blk['dur'])}</span></div>", unsafe_allow_html=True)

    with rj4:
        pl4 = st.session_state._playlist
        if not pl4:
            st.markdown("<div class='card r'>⚠️ Playlist boş.</div>", unsafe_allow_html=True)
        else:
            needed = [(i, s, "bas") for i, s in enumerate(pl4) if s.get("anons_bas") and not s.get("anons_wav_bas")] + [(i, s, "son") for i, s in enumerate(pl4) if s.get("anons_son") and not s.get("anons_wav_son")]
            done = [(i, s, "bas") for i, s in enumerate(pl4) if s.get("anons_bas") and s.get("anons_wav_bas")] + [(i, s, "son") for i, s in enumerate(pl4) if s.get("anons_son") and s.get("anons_wav_son")]
            _, trj = pool_stats()
            st.markdown(f"<div class='card {'t' if not needed else 'a'}'>✅ {len(done)} üretildi · ⏳ {len(needed)} bekliyor · Ses: <b>{st.session_state._rj_voice}</b> · {trj} kalan</div>", unsafe_allow_html=True)
            st.markdown("<span class='sl'>▶ Şarkı Bazlı Üretim</span>", unsafe_allow_html=True)
            for si, song in enumerate(pl4):
                sid = song["id"]
                if not song.get("anons_bas") and not song.get("anons_son"):
                    continue
                with st.expander(f"🎵 {si+1:02d}. {song.get('title','?')}", expanded=False):
                    ub1, ub2 = st.columns(2)
                    if song.get("anons_bas"):
                        with ub1:
                            st.markdown("<div style='font-size:.71rem;color:#f59e0b;font-weight:700;margin-bottom:3px;'>🎙️ BAŞ ANONSU</div>", unsafe_allow_html=True)
                            bt = song.get("anons_bas_text") or auto_bas(song)
                            st.text_area("bt2", value=bt, height=68, label_visibility="collapsed", key=f"pb_{sid}", disabled=True)
                            if song.get("anons_wav_bas"):
                                st.audio(song["anons_wav_bas"], format="audio/wav")
                                st.download_button("💾 BAŞ", song["anons_wav_bas"], file_name=f"bas_{si+1:02d}.wav", mime="audio/wav", key=f"dlb_{sid}")
                            if st.button("🔴 Üret", key=f"gb_{sid}", use_container_width=True):
                                with st.spinner("🎙️ Baş anons üretiliyor…"):
                                    try:
                                        rw, mm, _ = tts_single(st.session_state._rj_model, bt, st.session_state._rj_voice, st.session_state._rj_lang, st.session_state._rj_style)
                                        wv = pcm2wav(rw, mm)
                                        st.session_state._playlist[si]["anons_wav_bas"] = wv
                                        arc_add(st.session_state._rj_voice, st.session_state._rj_model, st.session_state._rj_lang, st.session_state._rj_style, bt, wv, "reji")
                                        st.session_state._rj_plan_ok = False
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ {e}")
                    if song.get("anons_son"):
                        with ub2:
                            st.markdown("<div style='font-size:.71rem;color:#60a5fa;font-weight:700;margin-bottom:3px;'>🎙️ SON ANONSU</div>", unsafe_allow_html=True)
                            st2 = song.get("anons_son_text") or auto_son(song)
                            st.text_area("st3", value=st2, height=68, label_visibility="collapsed", key=f"ps_{sid}", disabled=True)
                            if song.get("anons_wav_son"):
                                st.audio(song["anons_wav_son"], format="audio/wav")
                                st.download_button("💾 SON", song["anons_wav_son"], file_name=f"son_{si+1:02d}.wav", mime="audio/wav", key=f"dls_{sid}")
                            if st.button("🔴 Üret", key=f"gs_{sid}", use_container_width=True):
                                with st.spinner("🎙️ Son anons üretiliyor…"):
                                    try:
                                        rw2, mm2, _ = tts_single(st.session_state._rj_model, st2, st.session_state._rj_voice, st.session_state._rj_lang, st.session_state._rj_style)
                                        wv2 = pcm2wav(rw2, mm2)
                                        st.session_state._playlist[si]["anons_wav_son"] = wv2
                                        arc_add(st.session_state._rj_voice, st.session_state._rj_model, st.session_state._rj_lang, st.session_state._rj_style, st2, wv2, "reji")
                                        st.session_state._rj_plan_ok = False
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ {e}")

            st.markdown("<hr><span class='sl'>▶ Toplu Üretim</span>", unsafe_allow_html=True)
            if needed:
                st.markdown(f"<div class='card {'a' if len(needed)>trj else 'b'}'>{len(needed)} anons üretilecek · {trj} kalan</div>", unsafe_allow_html=True)
                if st.button(f"🔴 {len(needed)} Anonsu Toplu Üret", type="primary", use_container_width=True, key="bulk_rj"):
                    prg = st.progress(0)
                    sts_r = st.empty()
                    errs_r = []
                    for ni, (nsi, nsong, ntype) in enumerate(needed):
                        ntxt = (nsong.get("anons_bas_text") or auto_bas(nsong)) if ntype == "bas" else (nsong.get("anons_son_text") or auto_son(nsong))
                        sts_r.markdown(f"<div style='font-size:.73rem;color:#6b7a8d;'>🎙️ {ni+1}/{len(needed)}: {nsong['title']} [{ntype}]</div>", unsafe_allow_html=True)
                        try:
                            rw_b, mm_b, _ = tts_single(st.session_state._rj_model, ntxt, st.session_state._rj_voice, st.session_state._rj_lang, st.session_state._rj_style)
                            wv_b = pcm2wav(rw_b, mm_b)
                            if ntype == "bas":
                                st.session_state._playlist[nsi]["anons_wav_bas"] = wv_b
                            else:
                                st.session_state._playlist[nsi]["anons_wav_son"] = wv_b
                            arc_add(st.session_state._rj_voice, st.session_state._rj_model, st.session_state._rj_lang, st.session_state._rj_style, ntxt, wv_b, "reji")
                        except Exception as e:
                            errs_r.append(f"{nsong['title']} ({ntype}): {e}")
                        prg.progress((ni + 1) / len(needed))
                    sts_r.empty()
                    st.session_state._rj_plan_ok = False
                    if errs_r:
                        for er in errs_r:
                            st.markdown(f"<div class='card r'>❌ {er}</div>", unsafe_allow_html=True)
                    else:
                        st.success(f"✅ {len(needed)} anons üretildi!")
                        st.rerun()
            else:
                st.markdown("<div class='card g'>✅ Tüm seçili anonslar üretildi!</div>", unsafe_allow_html=True)

            st.markdown("<hr><span class='sl'>▶ ZIP İndir</span>", unsafe_allow_html=True)
            zip_rj = []
            for si2, s2 in enumerate(pl4):
                if s2.get("anons_wav_bas"):
                    zip_rj.append((f"{si2+1:02d}_BAS_{sfn(s2.get('title','?'), 12)}.wav", s2["anons_wav_bas"]))
                if s2.get("anons_wav_son"):
                    zip_rj.append((f"{si2+1:02d}_SON_{sfn(s2.get('title','?'), 12)}.wav", s2["anons_wav_son"]))
            if zip_rj:
                st.markdown(f"<div class='card t'>{len(zip_rj)} anons ZIP'e hazır</div>", unsafe_allow_html=True)
                st.download_button(f"📦 {len(zip_rj)} Anonsu ZIP İndir", make_zip(zip_rj), file_name=f"reji_{st.session_state._rj_start.replace(':','-')}.zip", mime="application/zip", use_container_width=True, key="dl_rj_zip")
            else:
                st.markdown("<div class='card a'>⏳ Üretilmiş anons yok.</div>", unsafe_allow_html=True)

# ════════════════ T7 — FON+ANONS MİKSERİ ════════════════════════
with t7:
    st.markdown("<div class='rjhdr' style='border-color:#1a1a3e;'><h2 style='background:linear-gradient(90deg,#fff 30%,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>🎛️ Fon+Anons Mikseri</h2><p style='color:#6b7a8d;'>Anons TTS + Fon müziği · Duck efekti · Fade-in/out · Arşivden miksleme · ZIP</p></div>", unsafe_allow_html=True)
    if not PYDUB_OK:
        st.markdown("<div class='card r'>⚠️ <b>PyDub kurulu değil.</b> <code>requirements.txt</code> içinde <code>pydub</code> (ve Python 3.13+ için <code>audioop-lts</code>), <code>packages.txt</code> içinde <code>ffmpeg</code> olmalıdır.</div>", unsafe_allow_html=True)
    else:
        fon_mx = list_audio(DIRS["fon"])
        if not fon_mx:
            st.markdown("<div class='card a'>📁 Fon klasörü boş. Kütüphane sekmesinden fon müziği yükleyebilirsiniz.</div>", unsafe_allow_html=True)
        mx1, mx2, mx3 = st.tabs(["🎛️ Tek Miksleme", "📦 Toplu Fon", "🗄️ Arşivden"])

        with mx1:
            cLm, cRm = st.columns([1.1, 1], gap="large")
            with cLm:
                st.markdown("<span class='sl'>▶ Anons TTS Ayarları</span>", unsafe_allow_html=True)
                mx_ml = st.selectbox("MX Model", list(MODELS.values()), label_visibility="collapsed", key="mx_m")
                mx_mdl = [k for k, v in MODELS.items() if v == mx_ml][0]
                mx_ll = st.selectbox("MX Dil", list(LANGUAGES.values()), label_visibility="collapsed", index=1, key="mx_l")
                mx_lng = [k for k, v in LANGUAGES.items() if v == mx_ll][0]
                mx_cn = st.radio("MX Cins", ["Tümü", "♀ Kadın", "♂ Erkek"], horizontal=True, label_visibility="collapsed", key="mx_cn")
                mx_vf = {k: v for k, v in VOICES.items() if mx_cn == "Tümü" or (mx_cn == "♀ Kadın" and v[0] == "♀") or (mx_cn == "♂ Erkek" and v[0] == "♂")}
                mx_vc = st.selectbox("MX Ses", list(mx_vf.keys()), format_func=lambda x: f"{VOICES[x][0]} {x}", label_visibility="collapsed", key="mx_v")
                mx_ps = st.selectbox("MX Stil", list(STYLE_PRESETS.keys()), label_visibility="collapsed", key="mx_ps")
                mx_sty = st.text_area("MX Stil T", value=STYLE_PRESETS[mx_ps], height=58, label_visibility="collapsed", key=f"mx_sty_{mx_ps}")
                st.markdown("<span class='sl'>▶ Hazır Anons WAV/MP3 Yükle</span>", unsafe_allow_html=True)
                mx_up = st.file_uploader("Hazır anons", type=["wav", "mp3", "ogg"], key="mx_up")
                mx_uwav = None
                if mx_up:
                    _, mx_uwav = save_upload(mx_up, DIRS["anons"], f"up_{mx_up.name}")
                    if mx_uwav:
                        st.audio(mx_uwav, format="audio/wav")
                        st.markdown(f"<div class='card g' style='font-size:.71rem;'>✅ Yüklendi — {dur_bytes(mx_uwav):.1f}s</div>", unsafe_allow_html=True)
            with cRm:
                st.markdown("<span class='sl'>▶ Anons Metni</span>", unsafe_allow_html=True)
                mx_txt = st.text_area("MX TXT", "", height=95, label_visibility="collapsed", key="mx_txt", placeholder="Anons metni yaz veya sol taraftan ses yükle…")
                if mx_txt:
                    txt_stats(mx_txt)
                st.markdown("<span class='sl'>▶ Fon Müziği</span>", unsafe_allow_html=True)
                fon_src = st.radio("Fon Kaynak", ["📁 Kütüphaneden", "📤 Yükle"], horizontal=True, key="fon_src")
                fon_path = None
                if fon_src == "📁 Kütüphaneden":
                    if fon_mx:
                        sel_fon = st.selectbox("Fon", fon_mx, label_visibility="collapsed", key="sel_fon")
                        fon_path = os.path.join(DIRS["fon"], sel_fon)
                        st.markdown(f"<div style='font-size:.67rem;color:#6b7a8d;'>{sel_fon} · {fmt_dur(dur_file(fon_path))}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div class='card a'>Kütüphanede fon yok</div>", unsafe_allow_html=True)
                else:
                    fon_up2 = st.file_uploader("Fon Müziği", type=["mp3", "wav", "ogg"], key="fon_up2")
                    if fon_up2:
                        dp2, _ = save_upload(fon_up2, DIRS["fon"], fon_up2.name, convert_to_wav=False)
                        if dp2:
                            fon_path = dp2
                            st.success("✅ Fon kütüphaneye eklendi")
                st.markdown("<span class='sl'>▶ Parametreler</span>", unsafe_allow_html=True)
                mx_p1, mx_p2 = st.columns(2)
                with mx_p1:
                    fvol = st.slider("Fon Ses (dB)", -24, 0, -8, key="mx_fvol")
                    duck = st.slider("Duck dB", -30, -6, -16, key="mx_duck")
                with mx_p2:
                    fi = st.slider("Fade-In ms", 100, 3000, 800, key="mx_fi")
                    fo = st.slider("Fade-Out ms", 100, 5000, 1500, key="mx_fo")
                mx_eq = st.selectbox("EQ", EQ_OPTS, label_visibility="collapsed", key="mx_eq")

                if st.button("🎛️ MİKSLE & OLUŞTUR", type="primary", use_container_width=True, key="mx_btn"):
                    anons_wav = mx_uwav
                    if not anons_wav and mx_txt.strip():
                        with st.spinner(f"🎙️ {mx_vc} seslendiriyor…"):
                            try:
                                rw, mm, _ = tts_single(mx_mdl, mx_txt, mx_vc, mx_lng, mx_sty)
                                anons_wav = pcm2wav(rw, mm)
                                arc_add(mx_vc, mx_mdl, mx_lng, mx_sty, mx_txt, anons_wav, "tek")
                            except Exception as e:
                                st.error(f"❌ TTS: {e}")
                    if anons_wav and fon_path and os.path.exists(fon_path):
                        with st.spinner("🎛️ Miksliyor…"):
                            try:
                                vs = AudioSegment.from_file(io.BytesIO(anons_wav))
                                fs = AudioSegment.from_file(fon_path)
                                mx_out = mix_fon_voice(fs, vs, fvol, duck, fi, fo)
                                if mx_eq != "Ham":
                                    mx_out = apply_eq(mx_out, mx_eq)
                                mxw = seg_to_wav(norm_seg(mx_out))
                                st.session_state._last_mx = {"wav": mxw, "dur": len(mx_out) / 1000.0, "qs": qs_bytes(mxw), "fn": f"fon_anons_{int(time.time())}.wav"}
                            except Exception as e:
                                st.error(f"❌ Miksleme: {e}")
                    elif anons_wav:
                        st.session_state._last_mx = {"wav": anons_wav, "dur": dur_bytes(anons_wav), "qs": qs_bytes(anons_wav), "fn": "anons_fonsuz.wav"}
                    elif not (mx_txt.strip() or mx_uwav):
                        st.warning("⚠️ Metin girin veya WAV yükleyin.")

                if st.session_state._last_mx:
                    lmx = st.session_state._last_mx
                    st.markdown(f"<div class='card t'>✅ Miks Hazır · {fmt_dur(lmx['dur'])} · {lmx['qs']}/100</div>", unsafe_allow_html=True)
                    st.audio(lmx["wav"], format="audio/wav")
                    draw_wf(lmx["wav"])
                    st.download_button("📦 Fon+Anons WAV İndir", lmx["wav"], file_name=lmx["fn"], mime="audio/wav", use_container_width=True, key="dl_mx")

        with mx2:
            st.markdown("<div class='card b'>Arşivdeki TTS seslerine toplu fon uygula</div>", unsafe_allow_html=True)
            arc_mx = [e for e in st.session_state._archive if e.get("wav")]
            if not arc_mx or not fon_mx:
                st.info("Arşivde ses veya kütüphanede fon yok.")
            else:
                sf_bulk = st.selectbox("Fon", fon_mx, key="sfb")
                fv_b = st.slider("Fon Ses", -24, 0, -8, key="fvb")
                dd_b = st.slider("Duck", -30, -6, -16, key="ddb")
                opts_ab = [f"{i+1}. {e['ts_s']} · {e['voice']} · {e['prev'][:28]}" for i, e in enumerate(arc_mx)]
                sel_ab = st.multiselect("Arşivden Seç", opts_ab, key="sel_ab")
                if sel_ab and st.button("📦 Toplu Uygula", use_container_width=True, key="bulk_fon"):
                    idxs = [opts_ab.index(s) for s in sel_ab]
                    fs2 = AudioSegment.from_file(os.path.join(DIRS["fon"], sf_bulk))
                    res_b = []
                    prg_b = st.progress(0)
                    for ni, idx_b in enumerate(idxs):
                        try:
                            vs2 = AudioSegment.from_file(io.BytesIO(arc_mx[idx_b]["wav"]))
                            ms = mix_fon_voice(fs2, vs2, fv_b, dd_b)
                            mw = seg_to_wav(ms)
                            res_b.append((f"fon_{arc_mx[idx_b]['voice']}_{arc_mx[idx_b]['id']}.wav", mw))
                        except Exception as e:
                            st.warning(f"Hata: {e}")
                        prg_b.progress((ni + 1) / len(idxs))
                    if res_b:
                        st.session_state._last_mx_bulk = {"zip": make_zip(res_b), "count": len(res_b)}
                if st.session_state._last_mx_bulk:
                    mb = st.session_state._last_mx_bulk
                    st.success(f"✅ {mb['count']} ses mikslendi!")
                    st.download_button("📦 ZIP İndir", mb["zip"], "fon_toplu.zip", "application/zip", key="dl_toplu_fon")

        with mx3:
            arc_mx3 = [e for e in st.session_state._archive if e.get("wav")]
            if not arc_mx3:
                st.info("Arşiv boş.")
            else:
                opts_a3 = [f"{i+1}. {e['ts_s']} | {e['voice']} | {e['prev'][:38]}" for i, e in enumerate(arc_mx3)]
                sel_a3 = st.selectbox("Arşivden", opts_a3, key="sel_a3")
                idx_a3 = opts_a3.index(sel_a3)
                ent = arc_mx3[idx_a3]
                st.audio(ent["wav"], format="audio/wav")
                draw_wf(ent["wav"])
                if fon_mx:
                    sf3 = st.selectbox("Fon", fon_mx, key="sf3")
                    fv3 = st.slider("Fon", -24, 0, -8, key="fv3")
                    if st.button("🎛️ Uygula", use_container_width=True, key="arc_mix3"):
                        try:
                            vs3 = AudioSegment.from_file(io.BytesIO(ent["wav"]))
                            fs3 = AudioSegment.from_file(os.path.join(DIRS["fon"], sf3))
                            m3 = mix_fon_voice(fs3, vs3, fv3)
                            mw3 = seg_to_wav(norm_seg(m3))
                            st.session_state._last_mx_arc = {"wav": mw3, "fn": f"arc_fon_{ent['id']}.wav"}
                        except Exception as e:
                            st.error(f"❌ {e}")
                    if st.session_state._last_mx_arc:
                        ma = st.session_state._last_mx_arc
                        st.audio(ma["wav"], format="audio/wav")
                        st.download_button("💾 WAV İndir", ma["wav"], ma["fn"], "audio/wav", key="dl_arc3")

# ════════════════ T8 — YAYIN OTOMASYONU ══════════════════════════
with t8:
    st.markdown("<div class='rjhdr' style='border-color:#0d2e0a;'><h2 style='background:linear-gradient(90deg,#fff 30%,#22c55e);-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>🚀 Yayın Otomasyonu</h2><p style='color:#528068;'>Şarkı + Anons + Fon → Tam yayın akışı · Zincir · Ses Birleştir · WAV</p></div>", unsafe_allow_html=True)
    if not PYDUB_OK:
        st.markdown("<div class='card r'>⚠️ <b>PyDub kurulu değil.</b></div>", unsafe_allow_html=True)
    else:
        yo1, yo2, yo3 = st.tabs(["📋 Yayın Planla", "🔗 Zincir Yayın", "✂️ Ses Birleştir"])

        with yo1:
            pl_songs_yo = list_audio(DIRS["playlist"])
            if not pl_songs_yo:
                st.markdown("<div class='card a'>📁 Kütüphanede şarkı yok. Kütüphane sekmesinden ekleyin.</div>", unsafe_allow_html=True)
            else:
                yc1, yc2 = st.columns([1.2, 1])
                with yc1:
                    yo_sel = st.multiselect("Şarkı Sıralaması", pl_songs_yo, default=pl_songs_yo[:min(3, len(pl_songs_yo))], key="yo_sel")
                    yo_cf = st.slider("Crossfade ms", 0, 3000, 1200, key="yo_cf")
                    yo_gap = st.slider("Boşluk ms", 0, 5000, 1500, key="yo_gap")
                    fon_yo = list_audio(DIRS["fon"])
                    yo_fon = st.selectbox("Fon", ["Yok"] + fon_yo, key="yo_fon")
                    yo_fvol = st.slider("Fon Ses", -24, 0, -8, key="yo_fvol") if yo_fon != "Yok" else -8
                    yo_duck = st.slider("Duck", -30, -6, -16, key="yo_duck") if yo_fon != "Yok" else -16
                    yo_name = st.text_input("Yayın Adı", value=f"Yayin_{datetime.datetime.now().strftime('%H%M')}", key="yo_name")
                with yc2:
                    st.markdown("<span class='sl'>▶ Anons Ekle</span>", unsafe_allow_html=True)
                    arc_yo = [e for e in st.session_state._archive if e.get("wav")]
                    st.markdown(f"<div style='font-size:.67rem;color:#6b7a8d;'>Arşivde {len(arc_yo)} ses · Sırayla şarkı başına atanır</div>", unsafe_allow_html=True)
                    yo_arc = st.checkbox("Arşiv seslerini şarkı başına ekle", key="yo_arc")
                    yo_up = st.file_uploader("Veya Anons WAV Yükle", type=["wav", "mp3"], accept_multiple_files=True, key="yo_up")
                    up_anons = []
                    if yo_up:
                        for uf in yo_up:
                            _, wv = save_upload(uf, DIRS["anons"], uf.name)
                            if wv:
                                up_anons.append(wv)
                        if up_anons:
                            st.success(f"✅ {len(up_anons)} anons hazır")
                if yo_sel and st.button("🚀 YAYIN OLUŞTUR", type="primary", use_container_width=True, key="yo_btn"):
                    with st.status("🎙️ Yayın oluşturuluyor…", expanded=True) as yo_st:
                        master = AudioSegment.silent(500)
                        fon_yo_seg = AudioSegment.from_file(os.path.join(DIRS["fon"], yo_fon)) if yo_fon != "Yok" else None
                        for idx_y, fn_y in enumerate(yo_sel):
                            sp_y = os.path.join(DIRS["playlist"], fn_y)
                            if not os.path.exists(sp_y):
                                st.write(f"⚠️ {fn_y} bulunamadı")
                                continue
                            st.write(f"🎵 [{idx_y+1}/{len(yo_sel)}] {fn_y}")
                            try:
                                sseg = AudioSegment.from_file(sp_y)
                            except Exception as e:
                                st.write(f"❌ {e}")
                                continue
                            an_wav = None
                            if yo_arc and idx_y < len(arc_yo):
                                an_wav = arc_yo[idx_y]["wav"]
                            elif idx_y < len(up_anons):
                                an_wav = up_anons[idx_y]
                            if an_wav:
                                aseg = AudioSegment.from_file(io.BytesIO(an_wav))
                                if fon_yo_seg:
                                    blk = safe_append(mix_fon_voice(fon_yo_seg, aseg, yo_fvol, yo_duck), sseg, yo_cf)
                                else:
                                    blk = aseg + sseg
                            else:
                                blk = sseg
                            master = safe_append(master, blk, yo_cf)
                            if yo_gap > 0:
                                master += AudioSegment.silent(yo_gap)
                            st.write(f"✅ [{idx_y+1}] Tamamlandı")
                        master = norm_seg(master)
                        out_yo = seg_to_wav(master)
                        out_path = os.path.join(DIRS["output"], f"{sfn(yo_name)}.wav")
                        with open(out_path, "wb") as f_out:
                            f_out.write(out_yo)
                        yo_st.update(label="✅ Hazır!", state="complete")
                        st.session_state._last_yo = {"wav": out_yo, "dur": len(master)/1000.0, "name": yo_name, "cnt": len(yo_sel)}
                        st.balloons()
                if st.session_state._last_yo:
                    lyo = st.session_state._last_yo
                    st.markdown(f"<div class='card g'>✅ {lyo['name']} · {fmt_dur(lyo['dur'])} · {lyo['cnt']} şarkı</div>", unsafe_allow_html=True)
                    st.audio(lyo["wav"], format="audio/wav")
                    st.download_button(f"📦 {lyo['name']} İndir", lyo["wav"], file_name=f"{sfn(lyo['name'])}.wav", mime="audio/wav", use_container_width=True, key="dl_yo")

        with yo2:
            st.markdown("<div class='card b'>Delay Reji anonsları + Kütüphane şarkıları → Zincir yayın</div>", unsafe_allow_html=True)
            pl_songs_ch = list_audio(DIRS["playlist"])
            fon_ch_list = list_audio(DIRS["fon"])
            rj_pl = st.session_state._playlist
            if not pl_songs_ch or not fon_ch_list:
                st.markdown("<div class='card a'>Kütüphanede şarkı ve fon müziği gerekli.</div>", unsafe_allow_html=True)
            elif not rj_pl:
                st.markdown("<div class='card a'>Delay Reji playlist boş.</div>", unsafe_allow_html=True)
            else:
                ch_fon = st.selectbox("Fon", fon_ch_list, key="ch_fon")
                ch_cf = st.slider("Crossfade", 0, 2000, 1000, key="ch_cf")
                ch_name = st.text_input("Yayın Adı", value=f"Zincir_{datetime.datetime.now().strftime('%H%M')}", key="ch_name")
                anr = [s for s in rj_pl if s.get("anons_wav_bas") or s.get("anons_wav_son")]
                st.markdown(f"<div class='card t'>{len(anr)}/{len(rj_pl)} şarkı için anons hazır</div>", unsafe_allow_html=True)
                if st.button("🔗 ZİNCİR YAYIN", type="primary", use_container_width=True, key="ch_btn"):
                    with st.status("🔗 Zincir yayın birleştiriliyor…", expanded=True) as ch_st:
                        mch = AudioSegment.silent(500)
                        fch = AudioSegment.from_file(os.path.join(DIRS["fon"], ch_fon))
                        for i, song in enumerate(rj_pl):
                            st.write(f"🎵 [{i+1}/{len(rj_pl)}] {song.get('title','?')}")
                            aw_bas = song.get("anons_wav_bas")
                            aw_son = song.get("anons_wav_son")
                            lf = song.get("local_file")
                            pf = next((f for f in pl_songs_ch if song.get("title", "").lower() in f.lower()), None)
                            sp = lf if lf and os.path.exists(lf) else (os.path.join(DIRS["playlist"], pf) if pf else None)

                            blk = AudioSegment.empty()
                            if aw_bas:
                                ag_b = AudioSegment.from_file(io.BytesIO(aw_bas))
                                blk = safe_append(blk, mix_fon_voice(fch, ag_b), ch_cf)
                            if sp and os.path.exists(sp):
                                try:
                                    sg = AudioSegment.from_file(sp)
                                    blk = safe_append(blk, sg, ch_cf)
                                except Exception as e:
                                    st.write(f"❌ {e}")
                            if aw_son:
                                ag_s = AudioSegment.from_file(io.BytesIO(aw_son))
                                blk = safe_append(blk, mix_fon_voice(fch, ag_s), ch_cf)
                            if len(blk) > 0:
                                mch = safe_append(mch, blk, ch_cf)
                                st.write(f"✅ [{i+1}] eklendi")
                        mch = norm_seg(mch)
                        chw = seg_to_wav(mch)
                        out_ch_path = os.path.join(DIRS["output"], f"{sfn(ch_name)}.wav")
                        with open(out_ch_path, "wb") as f_ch:
                            f_ch.write(chw)
                        ch_st.update(label="✅ Hazır!", state="complete")
                        st.session_state._last_ch = {"wav": chw, "dur": len(mch)/1000.0, "name": ch_name}
                        st.balloons()
                if st.session_state._last_ch:
                    lch = st.session_state._last_ch
                    st.markdown(f"<div class='card g'>✅ {lch['name']} · {fmt_dur(lch['dur'])}</div>", unsafe_allow_html=True)
                    st.audio(lch["wav"], format="audio/wav")
                    st.download_button(f"📦 {lch['name']} İndir", lch["wav"], f"{sfn(lch['name'])}.wav", "audio/wav", use_container_width=True, key="dl_ch")

        with yo3:
            st.markdown("<div class='card b'>Birden fazla sesi sıralı birleştir → tek WAV</div>", unsafe_allow_html=True)
            cnt1, cnt2 = st.tabs(["📂 Arşivden", "📤 Dosya Yükle"])
            with cnt1:
                arc_cnt = [e for e in st.session_state._archive if e.get("wav")]
                if not arc_cnt:
                    st.info("Arşiv boş.")
                else:
                    opts_cnt = [f"{i+1}. {e['ts_s']} | {e['voice']} | {e['prev'][:30]}" for i, e in enumerate(arc_cnt)]
                    sel_cnt = st.multiselect("Sesler (seçim sırası)", opts_cnt, key="sel_cnt")
                    cg = st.slider("Boşluk ms", 0, 3000, 500, key="cg")
                    cf2 = st.slider("Crossfade ms", 0, 2000, 200, key="cf2")
                    if sel_cnt and st.button("🔗 Birleştir", use_container_width=True, key="cnt_arc"):
                        idxs = [opts_cnt.index(s) for s in sel_cnt]
                        segs = [AudioSegment.from_file(io.BytesIO(arc_cnt[i]["wav"])) for i in idxs]
                        if segs:
                            rc = segs[0]
                            for sc3 in segs[1:]:
                                if cg > 0:
                                    rc += AudioSegment.silent(cg)
                                rc = safe_append(rc, sc3, cf2)
                            cw = seg_to_wav(norm_seg(rc))
                            st.session_state._last_cnt_arc = {"wav": cw, "n": len(segs), "dur": len(rc)/1000.0}
                    if st.session_state._last_cnt_arc:
                        lca = st.session_state._last_cnt_arc
                        st.success(f"✅ {lca['n']} ses · {fmt_dur(lca['dur'])}")
                        st.audio(lca["wav"], format="audio/wav")
                        st.download_button("📦 WAV İndir", lca["wav"], "birlesik.wav", "audio/wav", key="dl_cnt_arc")

            with cnt2:
                cnt_ups = st.file_uploader("Ses Dosyaları", type=["wav", "mp3", "ogg", "flac"], accept_multiple_files=True, key="cnt_up2")
                if cnt_ups:
                    gu = st.slider("Boşluk", 0, 3000, 500, key="gu")
                    cu = st.slider("Crossfade", 0, 2000, 200, key="cu")
                    if st.button("🔗 Birleştir", use_container_width=True, key="cnt_up_btn"):
                        su = []
                        for uf in cnt_ups:
                            try:
                                su.append(AudioSegment.from_file(io.BytesIO(uf.getvalue())))
                            except Exception as e:
                                st.warning(f"{uf.name}: {e}")
                        if su:
                            ru = su[0]
                            for s in su[1:]:
                                if gu > 0:
                                    ru += AudioSegment.silent(gu)
                                ru = safe_append(ru, s, cu)
                            uw = seg_to_wav(norm_seg(ru))
                            st.session_state._last_cnt_up = {"wav": uw, "n": len(su), "dur": len(ru)/1000.0}
                    if st.session_state._last_cnt_up:
                        lcu = st.session_state._last_cnt_up
                        st.success(f"✅ {lcu['n']} dosya · {fmt_dur(lcu['dur'])}")
                        st.audio(lcu["wav"], format="audio/wav")
                        st.download_button("📦 WAV İndir", lcu["wav"], "upload_birlesik.wav", "audio/wav", key="dl_cnt_up")

# ════════════════ T9 — SES EFEKTLERİ & SİNYAL ÜRETİCİ ════════════
with t9:
    st.markdown("<div class='rjhdr' style='border-color:#3a1a2e;'><h2 style='background:linear-gradient(90deg,#fff 30%,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>🎚️ Ses Efektleri Galerisi & Sinyal Üretici</h2><p style='color:#6b7a8d;'>Efekt presetleri · Özel preset kaydetme · Saat başı / Bip jingle ton üreteci</p></div>", unsafe_allow_html=True)
    if not PYDUB_OK:
        st.markdown("<div class='card r'>⚠️ PyDub kurulu değil.</div>", unsafe_allow_html=True)
    else:
        ef1, ef2, ef3, ef4 = st.tabs(["🎛️ Efekt Uygula", "💾 Preset Kaydet", "📂 Kayıtlı Presetler", "🔔 Sinyal / Bip Üretici"])

        with ef1:
            st.markdown("<span class='sl'>▶ Kaynak Ses Seç (Yükle veya Arşivden)</span>", unsafe_allow_html=True)
            ef_src_mode = st.radio("Kaynak", ["📤 Dosya Yükle", "📂 Arşivden Seç"], horizontal=True, key="ef_src_mode")
            ef_wav = None
            if ef_src_mode == "📤 Dosya Yükle":
                ef_up = st.file_uploader("Ses dosyası", type=["wav", "mp3", "ogg"], key="ef_up")
                if ef_up:
                    _, ef_wav = save_upload(ef_up, DIRS["uploads"], f"ef_{ef_up.name}")
            else:
                arc_ef = [e for e in st.session_state._archive if e.get("wav")]
                if arc_ef:
                    opts_ef = [f"{i+1}. {e['ts_s']} | {e['voice']} | {e['prev'][:30]}" for i, e in enumerate(arc_ef)]
                    sel_aef = st.selectbox("Arşiv Ses", opts_ef, key="sel_aef")
                    ef_wav = arc_ef[opts_ef.index(sel_aef)]["wav"]
                else:
                    st.info("Arşiv boş.")

            if ef_wav:
                st.audio(ef_wav, format="audio/wav")
                all_presets = dict(EFFECT_PRESETS)
                for cp in load_effect_presets():
                    all_presets[f"⭐ {cp['name']}"] = cp["params"]

                ef_preset = st.selectbox("Efekt Preseti", list(all_presets.keys()), key="ef_preset")
                ef_eq = st.selectbox("EQ", EQ_OPTS, key="ef_eq")

                if st.button("🎛️ Efekti Uygula", type="primary", use_container_width=True, key="ef_apply"):
                    with st.spinner("Efekt uygulanıyor…"):
                        try:
                            seg = AudioSegment.from_file(io.BytesIO(ef_wav))
                            seg = apply_effect(seg, all_presets[ef_preset])
                            seg = apply_eq(seg, ef_eq)
                            seg = norm_seg(seg)
                            ef_out = seg_to_wav(seg)
                            st.session_state._last_ef = {"wav": ef_out, "preset": ef_preset}
                        except Exception as e:
                            st.error(f"❌ {e}")
            if st.session_state._last_ef:
                lef = st.session_state._last_ef
                st.success(f"✅ {lef['preset']} uygulandı!")
                st.audio(lef["wav"], format="audio/wav")
                draw_wf(lef["wav"])
                st.download_button("💾 Efektli Sesi İndir", lef["wav"], f"efektli_{int(time.time())}.wav", "audio/wav", use_container_width=True, key="dl_ef")

        with ef2:
            st.markdown("<span class='sl'>▶ Yeni Preset Kaydet</span>", unsafe_allow_html=True)
            preset_name = st.text_input("Preset Adı", placeholder="Örn: Gece Radyosu", key="preset_name")
            ep1, ep2 = st.columns(2)
            with ep1:
                low = st.slider("High-Pass Kesim (Alt Frekans Hz)", 20, 3000, 300)
                high = st.slider("Low-Pass Kesim (Üst Frekans Hz)", 1000, 20000, 8000)
            with ep2:
                gain = st.slider("Gain (dB)", -12, 12, 0)
                noise = st.slider("Vinyl / Analog Gürültü", 0.0, 0.1, 0.0, 0.002)

            if st.button("💾 Preset Kaydet", use_container_width=True, key="save_preset"):
                if preset_name.strip():
                    params = {"low": low, "high": high, "gain": gain, "noise": noise}
                    if save_effect_preset(preset_name, params):
                        st.success(f"✅ '{preset_name}' kaydedildi! Artık Efekt Uygula sekmesinde seçilebilir.")
                else:
                    st.warning("⚠️ Preset adı girin.")

        with ef3:
            presets = load_effect_presets()
            if not presets:
                st.markdown("<div class='card a'>Kayıtlı özel preset yok.</div>", unsafe_allow_html=True)
            else:
                for p in presets:
                    with st.expander(f"🎚️ {p['name']}"):
                        st.json(p["params"])
                        if st.button("🗑️ Sil", key=f"del_preset_{p['name']}", use_container_width=True):
                            fp_p = os.path.join(DIRS["effect_gallery"], f"{sfn(p['name'])}.json")
                            if os.path.exists(fp_p):
                                os.remove(fp_p)
                            st.rerun()

        with ef4:
            st.markdown("<div class='card b'>🔔 Saat başı sinyali, sansür bipi veya intro tonu üretin (Sinüs / Kare / Testere dalgası)</div>", unsafe_allow_html=True)
            sg1, sg2, sg3 = st.columns(3)
            with sg1:
                wave_type = st.selectbox("Dalga Formu", ["Sinüs (Sine)", "Kare (Square)", "Testere (Sawtooth)"], key="sig_wave")
                sig_freq = st.slider("Frekans (Hz)", 200, 3000, 1000, 50, key="sig_freq")
            with sg2:
                sig_dur = st.slider("Süre (ms)", 100, 3000, 400, 50, key="sig_dur")
                sig_cnt = st.slider("Tekrar Sayısı (Saat Başı Bip)", 1, 6, 3, key="sig_cnt")
            with sg3:
                sig_gap = st.slider("Bip Arası Boşluk (ms)", 100, 1500, 600, 50, key="sig_gap")
                sig_db = st.slider("Ses Seviyesi (dB)", -30, 0, -10, key="sig_db")

            if st.button("🔔 Sinyal Üret", type="primary", use_container_width=True, key="sig_gen_btn"):
                gen_cls = Sine if "Sinüs" in wave_type else (Square if "Kare" in wave_type else Sawtooth)
                tone = gen_cls(sig_freq).to_audio_segment(duration=sig_dur).apply_gain(sig_db).fade_in(15).fade_out(25)
                out_sig = tone
                for _ in range(sig_cnt - 1):
                    out_sig = out_sig + AudioSegment.silent(sig_gap) + tone
                sig_wav = seg_to_wav(out_sig)
                st.session_state._last_sig = {"wav": sig_wav, "name": f"sinyal_{sig_freq}hz.wav"}

            if st.session_state._last_sig:
                lsig = st.session_state._last_sig
                st.audio(lsig["wav"], format="audio/wav")
                draw_wf(lsig["wav"])
                sc_a, sc_b = st.columns(2)
                with sc_a:
                    st.download_button("💾 Sinyali İndir", lsig["wav"], lsig["name"], "audio/wav", use_container_width=True, key="dl_sig")
                with sc_b:
                    if st.button("📥 Efekt Kütüphanesine Kaydet", use_container_width=True, key="save_sig_lib"):
                        dest_s = os.path.join(DIRS["effects"], lsig["name"])
                        with open(dest_s, "wb") as fs_out:
                            fs_out.write(lsig["wav"])
                        st.success(f"✅ {lsig['name']} Efektler klasörüne kaydedildi!")

# ════════════════ T10 — KÜTÜPHANE ════════════════════════════════
with t10:
    st.markdown("<span class='sl'>▶ Ses Kütüphanesi (ID3 Etiket Destekli)</span>", unsafe_allow_html=True)
    lib1, lib2, lib3, lib4 = st.tabs(["🎵 Şarkılar", "🎶 Fon Müzikleri", "🎺 Jinglelar", "🎭 Efektler"])

    def lib_panel(dir_p: str, tab, tk: str, info: str = ""):
        with tab:
            if info:
                st.markdown(f"<div class='card b' style='font-size:.77rem;'>{info}</div>", unsafe_allow_html=True)
            ups = st.file_uploader("Dosya Yükle", type=["mp3", "wav", "ogg", "flac", "m4a"], accept_multiple_files=True, key=f"lib_{tk}")
            if ups:
                cnt_l = 0
                for u in ups:
                    uid_l = f"lib_{tk}_{u.name}_{u.size}"
                    if uid_l in st.session_state._processed_uploads:
                        continue
                    sp_l, _ = save_upload(u, dir_p, u.name, convert_to_wav=False)
                    if sp_l:
                        st.session_state._processed_uploads.add(uid_l)
                        cnt_l += 1
                    else:
                        st.warning(f"⚠️ {u.name} kaydedilemedi.")
                if cnt_l > 0:
                    st.success(f"✅ {cnt_l} dosya eklendi!")
                    st.rerun()
            files_l = list_audio(dir_p)
            tot_l = sum(dur_file(os.path.join(dir_p, f)) for f in files_l)
            st.markdown(f"<div style='font-size:.67rem;color:#6b7a8d;margin:3px 0 9px;'>{len(files_l)} dosya · {fmt_dur(tot_l)} toplam</div>", unsafe_allow_html=True)
            for f in files_l:
                fp_l = os.path.join(dir_p, f)
                d_l = dur_file(fp_l)
                sz_l = os.path.getsize(fp_l) // 1024
                meta_l = read_id3_meta(fp_l)
                br_txt = f" · {meta_l['bitrate']}" if meta_l.get("bitrate") else ""
                cc_l = st.columns([3, 1.3, .5])
                with cc_l[0]:
                    st.markdown(f'<div class="song-row"><span class="song-nm">🎵 {f[:36]} <span style="font-weight:400;color:#6b7a8d;font-size:.7rem;">({meta_l["artist"]})</span></span><span class="song-dur">{fmt_dur(d_l)} · {sz_l}KB{br_txt}</span></div>', unsafe_allow_html=True)
                with cc_l[1]:
                    st.audio(fp_l)
                with cc_l[2]:
                    if st.button("🗑️", key=f"ldel_{tk}_{f}", help="Sil", use_container_width=True):
                        if os.path.exists(fp_l):
                            os.remove(fp_l)
                        st.rerun()

    lib_panel(DIRS["playlist"], lib1, "songs")
    lib_panel(DIRS["fon"], lib2, "fon", "Enstrümental arka plan. Anons sırasında duck efekti ile otomatik alçalır.")
    lib_panel(DIRS["jingles"], lib3, "jingles")
    lib_panel(DIRS["effects"], lib4, "effects", "Alkış, geçiş, saat başı ve ambians efektleri.")

# ════════════════ T11 — ARŞİV ════════════════════════════════════
with t11:
    arc = st.session_state._archive
    stat_a = st.session_state._api_stats
    st.markdown("<span class='sl'>▶ Oturum İstatistikleri</span>", unsafe_allow_html=True)
    sa1, sa2, sa3, sa4, sa5 = st.columns(5)
    with sa1:
        st.markdown(f'<div class="mbox b"><div class="v">{len(arc)}</div><div class="l">Kayıt</div></div>', unsafe_allow_html=True)
    with sa2:
        st.markdown(f'<div class="mbox g"><div class="v">{stat_a.get("calls", 0)}</div><div class="l">API Çağrısı</div></div>', unsafe_allow_html=True)
    with sa3:
        st.markdown(f'<div class="mbox a"><div class="v">{stat_a.get("secs", 0):.0f}s</div><div class="l">Üretilen Ses</div></div>', unsafe_allow_html=True)
    with sa4:
        st.markdown(f'<div class="mbox p"><div class="v">{stat_a.get("chars", 0):,}</div><div class="l">Karakter</div></div>', unsafe_allow_html=True)
    with sa5:
        tmb = sum(e["size"] for e in arc) / (1024 * 1024)
        st.markdown(f'<div class="mbox"><div class="v">{tmb:.1f}MB</div><div class="l">Boyut</div></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if not arc:
        st.markdown("<div style='text-align:center;padding:45px;color:#6b7a8d;'><div style='font-size:2rem;'>📂</div><div style='font-family:Syne,sans-serif;margin-top:7px;'>Arşiv Boş</div></div>", unsafe_allow_html=True)
    else:
        ah1, ah2, ah3 = st.columns([2, 1, 1])
        with ah1:
            st.markdown(f"<span class='sl'>▶ {len(arc)} Kayıt</span>", unsafe_allow_html=True)
        with ah2:
            if st.button("📦 ZIP Hazırla", use_container_width=True, key="arc_zip"):
                st.session_state._last_arc_zip = make_zip([
                    (f"{e['ts_s'].replace(':','-').replace(' ','_')}_{e['voice']}_{e['id']}.wav", e["wav"])
                    for e in arc
                ])
        with ah3:
            if st.button("🗑️ Tümünü Sil", use_container_width=True, key="arc_clr"):
                st.session_state._archive = []
                st.session_state._last_arc_zip = None
                st.session_state._api_stats = {"calls": 0, "chars": 0, "secs": 0.0}
                st.rerun()

        if st.session_state._last_arc_zip:
            st.download_button("💾 Hazırlanan Arşiv ZIP'ini İndir", st.session_state._last_arc_zip, "imajfm_arsiv.zip", "application/zip", use_container_width=True, key="arc_zip_dl")

        af1, af2 = st.columns([2, 1])
        with af1:
            arc_srch = st.text_input("Ara", "", placeholder="🔍 Ses, metin, model…", label_visibility="collapsed", key="arc_srch")
        with af2:
            arc_mode = st.selectbox("Mod", ["Tümü", "tek", "cift", "bulk", "bulk-file", "ab-A", "ab-B", "fav", "reji"], label_visibility="collapsed", key="arc_mode")
        farce = arc
        if arc_srch.strip():
            q = arc_srch.lower()
            farce = [h for h in farce if q in h["voice"].lower() or q in h["text"].lower() or q in h["model_s"].lower()]
        if arc_mode != "Tümü":
            farce = [h for h in farce if h.get("mode", "") == arc_mode]
        st.markdown(f"<div style='font-size:.67rem;color:#6b7a8d;margin:3px 0 9px;'>{len(farce)} kayıt</div>", unsafe_allow_html=True)
        mc = {"tek": "#3b82f6", "cift": "#a78bfa", "bulk": "#22c55e", "bulk-file": "#10b981", "ab-A": "#a78bfa", "ab-B": "#fb923c", "fav": "#fbbf24", "reji": "#10b981"}
        gcols = st.columns(3)
        for gi, h in enumerate(farce):
            with gcols[gi % 3]:
                col = mc.get(h.get("mode", "tek"), "#3b82f6")
                st.markdown(f"""<div style='background:#0b0f1a;border:1px solid #131c2e;border-radius:8px;padding:10px 12px;margin-bottom:7px;'>
<div style='display:flex;justify-content:space-between;margin-bottom:4px;'>
<span style='font-family:Syne,sans-serif;font-size:.77rem;font-weight:700;color:#60a5fa;'>{VOICES.get(h['voice'].split('+')[0], ('?',''))[0]} {h['voice'][:11]}</span>
<span style='font-size:.63rem;color:#6b7a8d;font-family:JetBrains Mono,monospace;'>{h['ts_s']}</span></div>
<div style='font-size:.66rem;color:#6b7a8d;margin-bottom:4px;'>
<span style='color:{col};background:{col}18;border-radius:3px;padding:1px 5px;font-size:.6rem;font-weight:700;'>{h.get('mode','tek').upper()}</span>
 {h['model_s']} · {h['dur']}s · {h['size']//1024}KB</div>
<div style='font-size:.76rem;color:#9aa7b8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>{h['prev']}</div></div>""", unsafe_allow_html=True)
                st.audio(h["wav"], format="audio/wav")
                dc1, dc2 = st.columns(2)
                with dc1:
                    st.download_button("💾 WAV", h["wav"], file_name=f"imajfm_{h['voice'].lower().replace('+','_')}_{h['id']}.wav", mime="audio/wav", use_container_width=True, key=f"adl_{h['id']}")
                with dc2:
                    if st.button("⭐", key=f"afav_{h['id']}", use_container_width=True, help="Favoriye ekle"):
                        st.session_state._favorites.append({
                            "id": h["id"],
                            "name": h["voice"] + " " + h["ts_s"],
                            "text": h["text"],
                            "voice": h["voice"].split("+")[0],
                            "model": h["model"],
                            "lang": h["lang"]
                        })
                        st.success("⭐ Favoriye eklendi!")

# ════════════════ T12 — PODCAST RSS ══════════════════════════════
with t12:
    st.markdown("<div class='rjhdr' style='border-color:#1a2a3e;'><h2 style='background:linear-gradient(90deg,#fff 30%,#3b82f6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>📰 Podcast RSS Üretici</h2><p style='color:#6b7a8d;'>Arşivdeki seslerden podcast feed oluştur · XML & Bölüm ZIP indir</p></div>", unsafe_allow_html=True)
    arc_pod = [e for e in st.session_state._archive if e.get("wav")]
    if not arc_pod:
        st.markdown("<div class='card a'>Arşivde ses yok. Önce ses üretin.</div>", unsafe_allow_html=True)
    else:
        pc_a, pc_b = st.columns(2)
        with pc_a:
            pod_title = st.text_input("Podcast Başlığı", value="İmaj FM Podcast", key="pod_title")
            pod_author = st.text_input("Yayıncı / Yazar", value="İmaj FM", key="pod_author")
        with pc_b:
            pod_base = st.text_input("Sunucu Base URL (opsiyonel)", value="https://imajfm.com/podcast/", key="pod_base")
        pod_desc = st.text_area("Açıklama", value="İmaj FM radyo yayınlarından podcast bölümleri.", key="pod_desc")

        opts_pod = [f"{i+1}. {e['ts_s']} | {e['voice']} | {e['prev'][:30]}" for i, e in enumerate(arc_pod)]
        selected_ep = st.multiselect("Bölüm Seç", opts_pod, key="pod_sel")

        if st.button("📄 RSS Feed Oluştur", type="primary", use_container_width=True, key="pod_btn"):
            if selected_ep:
                episodes, zip_items = [], []
                for sel in selected_ep:
                    e = arc_pod[opts_pod.index(sel)]
                    fn_ep = f"episode_{e['id']}.wav"
                    episodes.append({
                        "title": f"{e['voice']} - {e['ts_s']}",
                        "description": e["text"][:200],
                        "url": fn_ep,
                        "length": str(len(e["wav"])),
                        "pub_date": datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000"),
                        "guid": e["id"]
                    })
                    zip_items.append((fn_ep, e["wav"]))
                rss_path = os.path.join(DIRS["podcast"], f"podcast_{int(time.time())}.xml")
                rss_xml = generate_podcast_rss(pod_title, pod_desc, pod_author, pod_base, episodes, rss_path)
                if rss_xml:
                    st.session_state._last_rss = {"xml": rss_xml, "zip": make_zip(zip_items)}
            else:
                st.warning("⚠️ En az 1 bölüm seçin.")

        if st.session_state._last_rss:
            lrss = st.session_state._last_rss
            st.success("✅ RSS feed ve bölüm paketi oluşturuldu!")
            rc1, rc2 = st.columns(2)
            with rc1:
                st.download_button("📥 RSS XML İndir", lrss["xml"], "podcast.xml", "application/xml", use_container_width=True, key="dl_rss")
            with rc2:
                st.download_button("📦 Bölümleri ZIP İndir", lrss["zip"], "podcast_episodes.zip", "application/zip", use_container_width=True, key="dl_pod_zip")

# ════════════════ T13 — YAYIN TAKVİMİ ══════════════════════════
with t13:
    st.markdown("<div class='rjhdr' style='border-color:#2e1a0a;'><h2 style='background:linear-gradient(90deg,#fff 30%,#f59e0b);-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>📅 Yayın Takvimi</h2><p style='color:#6b7a8d;'>Gelecek yayınları planla · Durum güncelle · Delay Reji'ye aktar</p></div>", unsafe_allow_html=True)
    sc1, sc2 = st.tabs(["📋 Yeni Plan", "📂 Planlanan Yayınlar"])

    with sc1:
        sch_name = st.text_input("Yayın Adı", placeholder="Örn: Sabah Kuşağı", key="sch_name")
        sd_c1, sd_c2 = st.columns(2)
        with sd_c1:
            sch_date = st.date_input("Tarih", key="sch_date")
        with sd_c2:
            sch_time = st.time_input("Saat", key="sch_time")
        sch_songs = st.multiselect("Kütüphane Şarkıları", list_audio(DIRS["playlist"]), key="sch_songs")
        sch_notes = st.text_area("Notlar", placeholder="Özel notlar…", key="sch_notes")

        if st.button("📋 Yayın Planla", type="primary", use_container_width=True, key="sch_btn"):
            if sch_name.strip() and sch_songs:
                if schedule_broadcast(sch_name.strip(), str(sch_date), sch_time.strftime("%H:%M"), sch_songs, sch_notes):
                    st.success("✅ Yayın planlandı!")
                    st.rerun()
            else:
                st.warning("⚠️ Yayın adı ve en az 1 şarkı gerekli.")

    with sc2:
        schedules = get_scheduled_broadcasts()
        if not schedules:
            st.markdown("<div class='card a'>Planlanmış yayın yok.</div>", unsafe_allow_html=True)
        else:
            for idx_s, s in enumerate(schedules[:30]):
                st_badge = "✅ Tamamlandı" if s.get("status") == "completed" else "⏳ Bekliyor"
                with st.expander(f"📅 {s.get('name')} — {s.get('date')} {s.get('time')} [{st_badge}]"):
                    st.markdown(f"<div class='card b'>🎵 {len(s.get('songs', []))} şarkı · Not: {s.get('notes') or 'Yok'}</div>", unsafe_allow_html=True)
                    st.write("Şarkılar:", ", ".join(s.get("songs", [])))
                    b_s1, b_s2, b_s3 = st.columns(3)
                    with b_s1:
                        if st.button("📻 Reji Playlist'e Aktar", key=f"sch_load_{idx_s}", use_container_width=True):
                            loaded_pl = []
                            for fn_s in s.get("songs", []):
                                fp_s = os.path.join(DIRS["playlist"], fn_s)
                                d_s = dur_file(fp_s)
                                mn_s, sc_s = divmod(int(d_s or 210), 60)
                                meta_s = read_id3_meta(fp_s) if os.path.exists(fp_s) else {"title": fn_s, "artist": "Takvim"}
                                loaded_pl.append({
                                    "id": song_uid(), "title": meta_s["title"], "artist": meta_s["artist"],
                                    "duration_min": mn_s, "duration_sec": sc_s,
                                    "anons_bas": True, "anons_son": False,
                                    "anons_bas_text": "", "anons_son_text": "",
                                    "fon_aktif": False, "fon_tip": "📻 Radyo Klasik",
                                    "anons_wav_bas": None, "anons_wav_son": None,
                                    "local_file": fp_s if os.path.exists(fp_s) else None
                                })
                            st.session_state._playlist = loaded_pl
                            st.session_state._rj_start = s.get("time", "06:00")[:5]
                            st.session_state._rj_plan_ok = False
                            st.success("✅ Delay Reji sekmesine aktarıldı!")
                    with b_s2:
                        next_st = "completed" if s.get("status") != "completed" else "pending"
                        if st.button("🔄 Durum Değiştir", key=f"sch_tog_{idx_s}", use_container_width=True):
                            fp_sch = os.path.join(DIRS["schedules"], s["_file"])
                            s_copy = {k: v for k, v in s.items() if k != "_file"}
                            s_copy["status"] = next_st
                            with open(fp_sch, "w", encoding="utf-8") as fw_s:
                                json.dump(s_copy, fw_s, ensure_ascii=False, indent=2)
                            st.rerun()
                    with b_s3:
                        if st.button("🗑️ Sil", key=f"sch_del_{idx_s}", use_container_width=True):
                            fp_sch = os.path.join(DIRS["schedules"], s["_file"])
                            if os.path.exists(fp_sch):
                                os.remove(fp_sch)
                            st.rerun()

# ════════════════ T14 — SES KLONLAMA (RVC HAZIRLIK) ═════════════
with t14:
    st.markdown("<div class='rjhdr' style='border-color:#2a1a3e;'><h2 style='background:linear-gradient(90deg,#fff 30%,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>🗣️ Ses Klonlama (RVC Hazırlık)</h2><p style='color:#6b7a8d;'>RVC eğitimi için 44.1kHz Mono segment veri seti hazırla · Normalize et · ZIP indir</p></div>", unsafe_allow_html=True)
    if not PYDUB_OK:
        st.markdown("<div class='card r'>⚠️ PyDub kurulu değil.</div>", unsafe_allow_html=True)
    else:
        rvc1, rvc2 = st.tabs(["📤 Ses Yükle & Veri Seti Hazırla", "📂 Mevcut Ses Klonları"])

        with rvc1:
            st.markdown("<span class='sl'>▶ Kaynak Ses Dosyaları Yükle</span>", unsafe_allow_html=True)
            rvc_ups = st.file_uploader("Ses dosyaları (MP3/WAV/OGG)", type=["mp3", "wav", "ogg", "flac"], accept_multiple_files=True, key="rvc_ups")
            rc_a, rc_b = st.columns(2)
            with rc_a:
                clone_name = st.text_input("Ses / Model Adı", placeholder="Örn: Kenan_Ses", key="clone_name")
            with rc_b:
                rvc_chunk = st.slider("Segment Uzunluğu (sn)", 5, 30, 15, key="rvc_chunk")

            if rvc_ups and clone_name.strip() and st.button("📤 Kaydet ve RVC Veri Seti Hazırla", type="primary", use_container_width=True, key="rvc_save"):
                clone_dir = os.path.join(DIRS["voice_clones"], sfn(clone_name))
                os.makedirs(clone_dir, exist_ok=True)
                saved_paths = []
                for uf in rvc_ups:
                    dp, _ = save_upload(uf, clone_dir, uf.name)
                    if dp:
                        saved_paths.append(dp)
                if saved_paths:
                    rvc_dir = os.path.join(DIRS["rvc_workspace"], sfn(clone_name))
                    seg_cnt = prepare_rvc_dataset(saved_paths, rvc_dir, chunk_sec=rvc_chunk)
                    if seg_cnt > 0:
                        zip_items = []
                        for f in sorted(os.listdir(rvc_dir)):
                            fp = os.path.join(rvc_dir, f)
                            if os.path.isfile(fp):
                                with open(fp, "rb") as fh:
                                    zip_items.append((f, fh.read()))
                        st.session_state._last_rvc_zip = {
                            "zip": make_zip(zip_items),
                            "name": sfn(clone_name),
                            "cnt": seg_cnt,
                            "dir": rvc_dir
                        }
            if st.session_state._last_rvc_zip:
                lrvc = st.session_state._last_rvc_zip
                st.markdown(f"<div class='card g'>✅ Veri seti hazır: <b>{lrvc['cnt']}</b> adet 44.1kHz Mono WAV segmenti<br>📁 {lrvc['dir']}</div>", unsafe_allow_html=True)
                st.download_button("📦 RVC Veri Seti ZIP İndir", lrvc["zip"], f"{lrvc['name']}_rvc_dataset.zip", "application/zip", use_container_width=True, key="dl_rvc_zip")

        with rvc2:
            st.markdown("<span class='sl'>▶ Mevcut Ses Klonları</span>", unsafe_allow_html=True)
            clones = [d for d in os.listdir(DIRS["voice_clones"]) if os.path.isdir(os.path.join(DIRS["voice_clones"], d))]
            if not clones:
                st.markdown("<div class='card a'>Henüz kayıtlı ses klonu yok.</div>", unsafe_allow_html=True)
            else:
                for c in clones:
                    c_dir = os.path.join(DIRS["voice_clones"], c)
                    r_dir = os.path.join(DIRS["rvc_workspace"], c)
                    c_files = list_audio(c_dir)
                    r_files = list_audio(r_dir) if os.path.isdir(r_dir) else []
                    with st.expander(f"🗣️ {c} ({len(c_files)} ham dosya · {len(r_files)} RVC segment)"):
                        for f in c_files[:5]:
                            st.audio(os.path.join(c_dir, f))
                        if len(c_files) > 5:
                            st.caption(f"+ {len(c_files) - 5} dosya daha")
                        if st.button("🗑️ Klonu Sil", key=f"del_clone_{c}"):
                            import shutil
                            shutil.rmtree(c_dir, ignore_errors=True)
                            shutil.rmtree(r_dir, ignore_errors=True)
                            st.rerun()

# ════════════════ T15 — DÖNÜŞTÜRÜCÜ & NORMALİZASYON ══════════════
with t15:
    st.markdown("<div class='rjhdr' style='border-color:#0f2e3a;'><h2 style='background:linear-gradient(90deg,#fff 30%,#38bdf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>🔄 Toplu Ses Dönüştürücü & Normalizasyon</h2><p style='color:#6b7a8d;'>Format dönüştürme (MP3/WAV/OGG/FLAC) · Ses Normalizasyon (dBFS) · Sessizlik Kırpma · ZIP</p></div>", unsafe_allow_html=True)
    if not PYDUB_OK:
        st.markdown("<div class='card r'>⚠️ PyDub ve FFmpeg kurulu olmalıdır.</div>", unsafe_allow_html=True)
    else:
        dn1, dn2 = st.tabs(["🔄 Toplu Format Dönüştürücü", "📏 Ses Normalizasyon & Temizleme"])

        with dn1:
            conv_ups = st.file_uploader("Dönüştürülecek Ses Dosyaları", type=["mp3", "wav", "ogg", "flac", "m4a", "aac"], accept_multiple_files=True, key="conv_ups")
            cv1, cv2, cv3, cv4 = st.columns(4)
            with cv1:
                tgt_fmt = st.selectbox("Hedef Format", ["mp3", "wav", "ogg", "flac"], key="tgt_fmt")
            with cv2:
                tgt_br = st.selectbox("Bitrate (MP3/OGG)", ["128k", "192k", "256k", "320k"], index=1, key="tgt_br")
            with cv3:
                tgt_sr = st.selectbox("Örnekleme Hızı (Hz)", [22050, 24000, 44100, 48000], index=2, key="tgt_sr")
            with cv4:
                tgt_ch = st.selectbox("Kanal", ["Orijinal", "Mono (1)", "Stereo (2)"], key="tgt_ch")

            if conv_ups and st.button("🔄 Toplu Dönüştür", type="primary", use_container_width=True, key="conv_btn"):
                res_conv = []
                prg_c = st.progress(0)
                for idx_c, uf in enumerate(conv_ups):
                    try:
                        seg = AudioSegment.from_file(io.BytesIO(uf.getvalue()))
                        seg = seg.set_frame_rate(int(tgt_sr))
                        if tgt_ch == "Mono (1)":
                            seg = seg.set_channels(1)
                        elif tgt_ch == "Stereo (2)":
                            seg = seg.set_channels(2)
                        out_buf = io.BytesIO()
                        exp_kw = {"format": tgt_fmt}
                        if tgt_fmt in ("mp3", "ogg"):
                            exp_kw["bitrate"] = tgt_br
                        seg.export(out_buf, **exp_kw)
                        base_n = os.path.splitext(uf.name)[0]
                        res_conv.append((f"{sfn(base_n)}.{tgt_fmt}", out_buf.getvalue()))
                    except Exception as e:
                        st.warning(f"{uf.name} dönüştürülemedi: {e}")
                    prg_c.progress((idx_c + 1) / len(conv_ups))
                if res_conv:
                    st.session_state._last_conv_zip = {"zip": make_zip(res_conv), "cnt": len(res_conv), "fmt": tgt_fmt}

            if st.session_state._last_conv_zip:
                lcz = st.session_state._last_conv_zip
                st.success(f"✅ {lcz['cnt']} dosya .{lcz['fmt']} formatına dönüştürüldü!")
                st.download_button("📦 Dönüştürülenleri ZIP İndir", lcz["zip"], f"donusturulen_{lcz['fmt']}.zip", "application/zip", use_container_width=True, key="dl_conv_zip")

        with dn2:
            norm_ups = st.file_uploader("Normalize Edilecek Dosyalar", type=["mp3", "wav", "ogg", "flac"], accept_multiple_files=True, key="norm_ups")
            nm1, nm2, nm3 = st.columns(3)
            with nm1:
                tgt_dbfs = st.slider("Hedef Ses Seviyesi (dBFS)", -24.0, -3.0, -14.0, 0.5, key="tgt_dbfs")
            with nm2:
                do_trim = st.checkbox("Baş/Son Sessizlikleri Kırp", value=True, key="do_trim")
            with nm3:
                trim_thresh = st.slider("Sessizlik Eşiği (dBFS)", -60, -25, -45, key="trim_thresh")

            if norm_ups and st.button("📏 Normalize Et & Temizle", type="primary", use_container_width=True, key="norm_btn"):
                res_norm = []
                prg_n = st.progress(0)
                for idx_n, uf in enumerate(norm_ups):
                    try:
                        seg = AudioSegment.from_file(io.BytesIO(uf.getvalue()))
                        if do_trim and len(seg) > 200:
                            lead = detect_leading_silence(seg, silence_threshold=trim_thresh, chunk_size=10)
                            trail = detect_leading_silence(seg.reverse(), silence_threshold=trim_thresh, chunk_size=10)
                            if lead + trail < len(seg) - 100:
                                seg = seg[lead:len(seg) - trail]
                        seg = pydub_fx.normalize(seg)
                        seg = norm_seg(seg, tgt_dbfs)
                        base_n = os.path.splitext(uf.name)[0]
                        res_norm.append((f"{sfn(base_n)}_norm.wav", seg_to_wav(seg)))
                    except Exception as e:
                        st.warning(f"{uf.name} işlenemedi: {e}")
                    prg_n.progress((idx_n + 1) / len(norm_ups))
                if res_norm:
                    st.session_state._last_norm_zip = {"zip": make_zip(res_norm), "cnt": len(res_norm)}

            if st.session_state._last_norm_zip:
                lnz = st.session_state._last_norm_zip
                st.success(f"✅ {lnz['cnt']} dosya {tgt_dbfs} dBFS seviyesine normalize edildi!")
                st.download_button("📦 Normalize Dosyaları ZIP İndir", lnz["zip"], "normalize_sesler.zip", "application/zip", use_container_width=True, key="dl_norm_zip")

# ════════════════ FOOTER ═════════════════════════════════════════
st.markdown("<hr>", unsafe_allow_html=True)
gms = "✅ Gemini" if GEMINI_OK else "❌ Gemini"
pds = "✅ PyDub" if PYDUB_OK else "❌ PyDub"
nps = "✅ NumPy/Matplotlib" if NP_OK else "❌ NumPy"
mts = "✅ Mutagen" if MUTAGEN_OK else "❌ Mutagen"
tk_f, tr_f = pool_stats()
st.markdown(
    f"<div style='text-align:center;color:#4b5c74;font-size:.65rem;letter-spacing:.08em;padding:4px 0 10px;'>"
    f"İMAJ FM TTS STÜDYO v7.1 · {gms} · {pds} · {nps} · {mts} · API: {tk_f}/10 yüklü · {tr_f} kalan · 2026</div>",
    unsafe_allow_html=True,
)
