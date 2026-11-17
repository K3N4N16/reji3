"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  İMAJ FM · TTS STÜDYO  v7.5 — TAM ENTEGRE YAYIN SİSTEMİ                   ║
║  Yüksek Kontrast Koyu & Aydınlık Tema · Gemini Flash 2.5 / 3.1 / 3.8 TTS    ║
║  3 Katmanlı Multi-Speaker Düzeltmesi · AI Anons Yazarı · Anında Hızlı TTS   ║
║  Gelişmiş Yayın Otomasyonu (Başı/İçi Talk-Over/Sonu · Ducking · MP3/ID3)   ║
║  Delay Reji · Fon+Anons · Ses Efektleri & Sinyal · Podcast RSS · Takvim     ║
║  RVC Veri Seti · Ses Normalizasyon · Toplu Dönüştürücü                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

import streamlit as st
import wave, io, zipfile, re, time, datetime, os, json, uuid, shutil
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
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, ID3NoHeaderError
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
    page_title="İmaj FM TTS v7.5",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════ TEMALAR ════════════════════════════
THEMES = {
    "🌙 Yüksek Kontrast Koyu": {
        "bg": "#090d16", "sb": "#060911", "card": "#111827", "inp": "#0f172a",
        "border": "#334155", "text": "#f8fafc", "muted": "#cbd5e1", "dim": "#94a3b8",
        "accent": "#ef4444", "accent2": "#60a5fa", "sec_btn": "#1e293b",
        "hdr_bg": "linear-gradient(135deg,#13223d,#0d1526)", "plt_bg": "#090d16",
    },
    "☀️ Aydınlık Stüdyo": {
        "bg": "#f1f5f9", "sb": "#e2e8f0", "card": "#ffffff", "inp": "#ffffff",
        "border": "#94a3b8", "text": "#0f172a", "muted": "#1e293b", "dim": "#334155",
        "accent": "#dc2626", "accent2": "#2563eb", "sec_btn": "#e2e8f0",
        "hdr_bg": "linear-gradient(135deg,#ffffff,#e2e8f0)", "plt_bg": "#f8fafc",
    },
    "🌊 Stüdyo Lacivert": {
        "bg": "#0b132b", "sb": "#070d1f", "card": "#1c2541", "inp": "#141d38",
        "border": "#3a506b", "text": "#ffffff", "muted": "#e0e7ff", "dim": "#a5b4fc",
        "accent": "#f97316", "accent2": "#38bdf8", "sec_btn": "#243154",
        "hdr_bg": "linear-gradient(135deg,#1c2541,#0b132b)", "plt_bg": "#0b132b",
    },
}

if "_theme_name" not in st.session_state:
    st.session_state["_theme_name"] = "🌙 Yüksek Kontrast Koyu"

def apply_theme_css(t: Dict[str, str]):
    is_light = t["bg"].startswith("#f")
    card_g, card_g_txt = ("#ecfdf5", "#065f46") if is_light else ("#052e16", "#86efac")
    card_a, card_a_txt = ("#fffbeb", "#92400e") if is_light else ("#291802", "#fde68a")
    card_r, card_r_txt = ("#fef2f2", "#991b1b") if is_light else ("#2d0606", "#fca5a5")
    card_p, card_p_txt = ("#f5f3ff", "#5b21b6") if is_light else ("#1b1035", "#ddd6fe")
    hdr_title = "linear-gradient(90deg,#0f172a 25%,#dc2626)" if is_light else "linear-gradient(90deg,#ffffff 25%,#ff6b6b)"

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
*{{box-sizing:border-box;}}
html,body,[data-testid="stAppViewContainer"],[data-testid="stApp"],.main{{
  background:{t['bg']}!important;color:{t['text']}!important;font-family:'Inter',sans-serif;}}
[data-testid="stHeader"]{{background:transparent!important;}}
[data-testid="stSidebar"]{{background:{t['sb']}!important;border-right:1px solid {t['border']}!important;}}
[data-testid="stSidebarContent"]{{padding:.6rem .75rem;color:{t['text']}!important;}}
[data-testid="stSidebar"] *, [data-testid="stAppViewContainer"] p,
[data-testid="stWidgetLabel"] p, label, .stMarkdown, span{{color:{t['text']};}}
.hdr{{background:{t['hdr_bg']};border:1px solid {t['border']};
  border-radius:14px;padding:18px 24px;margin-bottom:14px;position:relative;overflow:hidden;}}
.hdr::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,{t['accent']},#f59e0b,{t['accent']});background-size:200%;animation:scan 3s linear infinite;}}
@keyframes scan{{0%{{background-position:0%}}100%{{background-position:200%}}}}
.hdr h1{{font-family:'Syne',sans-serif;font-size:1.6rem;font-weight:800;margin:0 0 4px;
  background:{hdr_title};-webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
.hdr p{{margin:0;color:{t['muted']}!important;font-size:.84rem;font-weight:500;}}
.ldot{{display:inline-block;width:8px;height:8px;background:#ef4444;border-radius:50%;margin-right:7px;animation:bl 1.2s infinite;}}
@keyframes bl{{0%,100%{{opacity:1}}50%{{opacity:.15}}}}
.sl{{font-family:'Syne',sans-serif;font-size:.7rem;font-weight:800;letter-spacing:.14em;
  color:{t['accent']}!important;text-transform:uppercase;margin:12px 0 5px;display:block;}}
.sl2{{font-family:'Syne',sans-serif;font-size:.66rem;font-weight:800;letter-spacing:.12em;
  color:{t['accent2']}!important;text-transform:uppercase;margin:8px 0 4px;display:block;}}
.sl3{{font-family:'Syne',sans-serif;font-size:.66rem;font-weight:800;letter-spacing:.12em;
  color:#10b981!important;text-transform:uppercase;margin:8px 0 4px;display:block;}}
.mbox{{background:{t['card']};border:1px solid {t['border']};border-radius:10px;padding:10px;text-align:center;}}
.mbox .v{{font-family:'Syne',sans-serif;font-size:1.25rem;font-weight:800;color:{t['accent']};}}
.mbox .l{{font-size:.63rem;font-weight:700;letter-spacing:.09em;color:{t['muted']};text-transform:uppercase;margin-top:2px;}}
.mbox.g .v{{color:#16a34a;}}.mbox.b .v{{color:{t['accent2']};}}.mbox.a .v{{color:#d97706;}}
.mbox.p .v{{color:#8b5cf6;}}.mbox.t .v{{color:#059669;}}
.card{{background:{t['card']};border:1px solid {t['border']};border-radius:8px;padding:10px 14px;margin:6px 0;font-size:.84rem;color:{t['text']};font-weight:500;}}
.card.b{{border-left:4px solid {t['accent2']};}}
.card.g,.card.t{{border-left:4px solid #16a34a;background:{card_g};color:{card_g_txt};}}
.card.a{{border-left:4px solid #d97706;background:{card_a};color:{card_a_txt};}}
.card.r{{border-left:4px solid #dc2626;background:{card_r};color:{card_r_txt};}}
.card.p{{border-left:4px solid #7c3aed;background:{card_p};color:{card_p_txt};}}
[data-testid="stButton"]>button{{font-family:'Syne',sans-serif;font-weight:700;border-radius:8px;transition:all .15s;}}
[data-testid="stButton"]>button[kind="primary"]{{background:linear-gradient(135deg,#b91c1c,#dc2626)!important;border:none!important;color:#ffffff!important;}}
[data-testid="stButton"]>button[kind="primary"] *{{color:#ffffff!important;}}
[data-testid="stButton"]>button[kind="secondary"]{{background:{t['sec_btn']}!important;border:1px solid {t['border']}!important;color:{t['text']}!important;}}
[data-testid="stDownloadButton"]>button{{background:{t['sec_btn']}!important;border:1px solid {t['border']}!important;color:{t['text']}!important;font-weight:700!important;}}
[data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input{{
  background:{t['inp']}!important;border:1px solid {t['border']}!important;border-radius:8px!important;
  color:{t['text']}!important;font-weight:500!important;}}
[data-testid="stSelectbox"] div[data-baseweb="select"]>div,
[data-testid="stMultiSelect"] div[data-baseweb="select"]>div{{
  background:{t['inp']}!important;border:1px solid {t['border']}!important;border-radius:8px!important;color:{t['text']}!important;}}
[data-testid="stSelectbox"] span, [data-testid="stMultiSelect"] span{{color:{t['text']}!important;}}
div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"]{{
  background:{t['card']}!important;border:1px solid {t['border']}!important;}}
li[role="option"]{{color:{t['text']}!important;background:{t['card']}!important;}}
li[role="option"]:hover, li[aria-selected="true"]{{background:{t['sec_btn']}!important;color:{t['accent']}!important;font-weight:700!important;}}
[data-testid="stExpander"] details{{background:{t['card']}!important;border:1px solid {t['border']}!important;border-radius:9px!important;margin-bottom:6px!important;}}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary p{{color:{t['text']}!important;font-weight:700!important;}}
[data-testid="stFileUploader"] section{{background:{t['inp']}!important;border:2px dashed {t['border']}!important;border-radius:9px!important;color:{t['text']}!important;}}
[data-testid="stTabs"] [data-baseweb="tab-list"]{{background:{t['card']}!important;border-bottom:2px solid {t['border']};padding:4px 8px 0;border-radius:10px 10px 0 0;gap:4px;flex-wrap:wrap;}}
[data-testid="stTabs"] [data-baseweb="tab"]{{background:transparent!important;color:{t['dim']}!important;font-family:'Syne',sans-serif!important;font-weight:700!important;font-size:.76rem!important;padding:8px 12px!important;border-bottom:3px solid transparent!important;}}
[data-testid="stTabs"] [aria-selected="true"]{{color:{t['accent']}!important;border-bottom:3px solid {t['accent']}!important;background:{t['sec_btn']}!important;border-radius:6px 6px 0 0;}}
.qbar{{background:{t['border']};border-radius:4px;height:6px;margin:4px 0;overflow:hidden;}}
.qbar-f{{height:100%;border-radius:4px;}}
.song-row{{display:flex;align-items:center;gap:9px;background:{t['card']};border:1px solid {t['border']};border-radius:8px;padding:8px 12px;margin-bottom:5px;}}
.song-nm{{font-family:'Syne',sans-serif;font-size:.84rem;font-weight:700;color:{t['text']};flex:1;}}
.song-dur{{font-family:'JetBrains Mono',monospace;font-size:.72rem;color:{t['muted']};}}
.tl-block{{background:{t['card']};border:1px solid {t['border']};border-radius:8px;padding:8px 12px;margin:4px 0;display:flex;align-items:center;gap:10px;}}
.tl-time{{font-family:'JetBrains Mono',monospace;font-size:.76rem;font-weight:700;color:#10b981;min-width:60px;}}
.tl-type{{font-size:.64rem;font-weight:800;letter-spacing:.06em;text-transform:uppercase;padding:3px 8px;border-radius:5px;min-width:62px;text-align:center;}}
.ttype-song{{background:{t['sec_btn']};color:{t['accent2']};border:1px solid {t['accent2']};}}
.ttype-anons{{background:{card_a};color:{card_a_txt};border:1px solid #d97706;}}
.ttype-fon{{background:{card_g};color:{card_g_txt};border:1px solid #16a34a;}}
.tl-lbl{{font-size:.82rem;color:{t['text']};flex:1;}}
.tl-dur{{font-family:'JetBrains Mono',monospace;font-size:.72rem;color:{t['muted']};}}
.rjhdr{{background:{t['card']};border:1px solid {t['border']};border-radius:12px;padding:15px 20px;margin-bottom:14px;border-left:4px solid #10b981;}}
.rjhdr h2{{font-family:'Syne',sans-serif;font-size:1.18rem;font-weight:800;margin:0 0 3px;color:{t['text']};}}
.rjhdr p{{margin:0;color:{t['muted']};font-size:.8rem;}}
.fav-card{{background:{t['card']};border:1px solid {t['border']};border-radius:8px;padding:9px 12px;margin:4px 0;}}
.fav-name{{font-family:'Syne',sans-serif;font-size:.82rem;font-weight:700;color:{t['text']};}}
.fav-prev{{font-size:.74rem;color:{t['muted']};margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
hr{{border-color:{t['border']}!important;margin:12px 0!important;}}
</style>
""", unsafe_allow_html=True)

CURRENT_THEME = THEMES.get(st.session_state["_theme_name"], THEMES["🌙 Yüksek Kontrast Koyu"])
apply_theme_css(CURRENT_THEME)

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
    "gemini-3.1-flash-tts-preview": "🔥 3.1 Flash TTS Preview (En Güncel)",
    "gemini-3.8-flash-tts": "✨ 3.8 Flash TTS (Oto-Fallback Aktif)",
    "gemini-2.5-flash-tts": "🚀 2.5 Flash TTS (Stabil)",
    "gemini-2.5-pro-tts": "💎 2.5 Pro TTS (Yüksek Kalite)",
    "gemini-2.5-flash-preview-tts": "⚡ 2.5 Flash Preview TTS",
    "gemini-2.5-flash-lite-preview-tts": "💡 2.5 Lite Preview TTS",
}
FALLBACK_TTS_CHAIN = ["gemini-3.1-flash-tts-preview", "gemini-2.5-flash-tts", "gemini-2.5-flash-preview-tts"]

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

ANONS_POSITIONS = [
    "⏮️ Şarkı Başı (Önce Anons, Sonra Şarkı)",
    "🎚️ Şarkı İçi (Başlangıçtan X sn Sonra · Talk-Over)",
    "🎙️ Şarkı İçi (Bitişten X sn Önce · Outro Üzeri)",
    "⏭️ Şarkı Sonu (Şarkı Biter, Sonra Anons)",
]

JINGLE_POSITIONS = ["Şarkı Başı", "Şarkı Sonu", "Anons Öncesi"]

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
_si("_pending_t_tek", None)
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
_si("_yo_tracks", [])
_si("_rj_voice", "Kore")
_si("_rj_model", "gemini-3.1-flash-tts-preview")
_si("_rj_lang", "tr-TR")
_si("_rj_style", "")
_si("_rj_start", "06:00")
_si("_rj_plan", [])
_si("_rj_plan_ok", False)
_si("_processed_uploads", set())

for _ok_key in [
    "_last_tek", "_last_cift", "_last_bulk_manual", "_last_bulk_file",
    "_last_ab_a", "_last_ab_b", "_last_mx", "_last_mx_bulk", "_last_mx_arc",
    "_last_yo", "_last_yo_cue", "_last_ch", "_last_cnt_arc", "_last_cnt_up",
    "_last_ef", "_last_sig", "_last_arc_zip", "_last_rss",
    "_last_rvc_zip", "_last_conv_zip", "_last_norm_zip"
]:
    _si(_ok_key, None)

if st.session_state._pending_t_tek is not None:
    st.session_state._t_tek = st.session_state._pending_t_tek
    st.session_state.ta1 = st.session_state._pending_t_tek
    st.session_state._pending_t_tek = None

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
    if MUTAGEN_OK:
        try:
            mf = MutagenFile(path)
            if mf and mf.info and getattr(mf.info, "length", 0.0) > 0:
                return float(mf.info.length)
        except Exception:
            pass
    if PYDUB_OK:
        try:
            return len(AudioSegment.from_file(path)) / 1000.0
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

def audio_metrics(wb: bytes) -> Dict[str, str]:
    if not PYDUB_OK or not wb:
        return {"dbfs": "-", "peak": "-", "clip": "Bilgi Yok"}
    try:
        seg = AudioSegment.from_file(io.BytesIO(wb))
        dbfs = f"{seg.dBFS:.1f} dBFS" if seg.dBFS != float("-inf") else "-∞"
        peak = f"{seg.max_dBFS:.1f} dBFS" if seg.max_dBFS != float("-inf") else "-∞"
        clip = "⚠️ Klipping" if seg.max_dBFS >= -0.1 else "✅ Temiz"
        return {"dbfs": dbfs, "peak": peak, "clip": clip}
    except Exception:
        return {"dbfs": "-", "peak": "-", "clip": "-"}

# ═══════════════════════════ ARŞİV ══════════════════════════════
def arc_add(voice: str, model: str, lang: str, style: str, text: str, wav: bytes, mode: str = "tek"):
    dur = dur_bytes(wav)
    uid = uuid.uuid4().hex[:10]
    st.session_state._archive.insert(0, {
        "id": uid,
        "ts": datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "ts_s": datetime.datetime.now().strftime("%d.%m %H:%M"),
        "voice": voice, "model": model,
        "model_s": model.replace("gemini-", "").replace("-preview", "").replace("-tts", ""),
        "lang": lang, "style": style[:40] if style else "", "text": text,
        "prev": text[:65].replace("\n", " ") + ("…" if len(text) > 65 else ""),
        "wav": wav, "dur": round(dur, 1), "size": len(wav), "mode": mode,
    })
    if len(st.session_state._archive) > MAX_ARC:
        st.session_state._archive = st.session_state._archive[:MAX_ARC]
    st.session_state._api_stats["secs"] = st.session_state._api_stats.get("secs", 0.0) + dur

# ═══════════════════════════ GEMINI TTS + AI YAZAR ═══════════════
def _extract_audio_from_response(resp) -> Tuple[bytes, str]:
    if not resp or not getattr(resp, "candidates", None):
        raise RuntimeError("API boş yanıt döndürdü.")
    cand = resp.candidates[0]
    if not getattr(cand, "content", None) or not getattr(cand.content, "parts", None):
        raise RuntimeError("API yanıtında ses içeriği bulunamadı.")
    for part in cand.content.parts:
        inl = getattr(part, "inline_data", None)
        if inl and getattr(inl, "data", None):
            return inl.data, getattr(inl, "mime_type", "") or ""
    text_msgs = [getattr(p, "text", "") for p in cand.content.parts if getattr(p, "text", None)]
    raise RuntimeError(f"Ses üretilemedi: {' '.join(text_msgs) or 'Boş yanıt'}")

def pcm2wav(raw_data: bytes, mime_type: str = "", rate: int = 24000, ch: int = 1, sw: int = 2) -> bytes:
    if not raw_data:
        return b""
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

def _run_tts_with_rotation(model: str, fn_call, chars: int):
    if not GEMINI_OK:
        raise RuntimeError("`google-genai` paketi kurulu değil. `pip install google-genai` çalıştırın.")
    models_to_try = [model] + [m for m in FALLBACK_TTS_CHAIN if m != model]
    last_err = None
    for mdl in models_to_try:
        for _ in range(10):
            ak, ai = get_key()
            if ak is None:
                break
            try:
                data, mime = fn_call(ak, mdl)
                consume(ai, chars)
                if mdl != model:
                    st.toast(f"ℹ️ '{model}' yerine otomatik '{mdl}' kullanıldı.", icon="🔄")
                return data, mime, ai
            except Exception as e:
                err_s = str(e).upper()
                last_err = e
                if any(x in err_s for x in ["429", "RESOURCE_EXHAUSTED", "QUOTA", "API_KEY_INVALID"]):
                    mark_key_exhausted(ai)
                    continue
                if any(x in err_s for x in ["404", "NOT_FOUND", "IS NOT FOUND", "NOT SUPPORTED"]):
                    break
                raise e
    raise RuntimeError(last_err or "Kullanılabilir API anahtarı veya aktif model kalmadı!")

def tts_single(model: str, text: str, voice: str, lang: str, style: str) -> Tuple[bytes, str, int]:
    full = f"{style}\n\n{text}" if style.strip() else text
    lc = lang if lang != "otomatik" else None

    def _call(api_key: str, mdl: str):
        c = genai.Client(api_key=api_key)
        sc_kwargs = {
            "voice_config": types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
            )
        }
        if lc:
            sc_kwargs["language_code"] = lc
        r = c.models.generate_content(
            model=mdl,
            contents=full,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(**sc_kwargs),
            ),
        )
        return _extract_audio_from_response(r)

    return _run_tts_with_rotation(model, _call, len(text))

def _parse_dialogue_turns(text: str, sp1: str, sp2: str) -> List[Tuple[str, str]]:
    turns: List[Tuple[str, str]] = []
    cur_sp = sp1
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.lower().startswith(f"{sp1.lower()}:"):
            cur_sp = sp1
            utt = line[len(sp1) + 1:].strip()
        elif line.lower().startswith(f"{sp2.lower()}:"):
            cur_sp = sp2
            utt = line[len(sp2) + 1:].strip()
        else:
            utt = line
        if utt:
            turns.append((cur_sp, utt))
    return turns or [(sp1, text.strip())]

def tts_multi(model: str, text: str, sp1: str, v1: str, sp2: str, v2: str, lang: str) -> Tuple[bytes, str, int]:
    lc = lang if lang != "otomatik" else None
    turns = _parse_dialogue_turns(text, sp1, sp2)

    part_fields = getattr(types.Part, "model_fields", {}) if GEMINI_OK else {}
    has_speech_meta = "speech_metadata" in part_fields

    if has_speech_meta:
        sm_cls = getattr(types, "SpeechMetadata", None)
        parts = [
            types.Part(text=utt, speech_metadata=sm_cls(speaker=sp))
            if sm_cls is not None
            else types.Part(text=utt, speech_metadata={"speaker": sp})
            for sp, utt in turns
        ]
        structured_contents = [types.Content(role="user", parts=parts)]
    else:
        structured_contents = None

    plain_contents = (
        f"TTS the following conversation between {sp1} and {sp2}:\n"
        + "\n".join(f"{sp}: {utt}" for sp, utt in turns)
    )

    def _make_call(contents_payload):
        def _call(api_key: str, mdl: str):
            c = genai.Client(api_key=api_key)
            sc_kwargs = {
                "multi_speaker_voice_config": types.MultiSpeakerVoiceConfig(
                    speaker_voice_configs=[
                        types.SpeakerVoiceConfig(speaker=sp1, voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=v1))),
                        types.SpeakerVoiceConfig(speaker=sp2, voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=v2))),
                    ]
                )
            }
            if lc:
                sc_kwargs["language_code"] = lc
            r = c.models.generate_content(
                model=mdl,
                contents=contents_payload,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(**sc_kwargs),
                ),
            )
            return _extract_audio_from_response(r)
        return _call

    # 1) SDK speech_metadata destekliyorsa doğrudan gönder
    if structured_contents is not None:
        try:
            return _run_tts_with_rotation(model, _make_call(structured_contents), len(text))
        except Exception as e:
            if "400" not in str(e) and "INVALID_ARGUMENT" not in str(e).upper():
                raise

    # 2) Klasik düz metin formatını dene
    try:
        target_mdl = "gemini-2.5-flash-preview-tts" if model.startswith("gemini-3") else model
        return _run_tts_with_rotation(target_mdl, _make_call(plain_contents), len(text))
    except Exception as e:
        err_u = str(e).upper()
        if not any(x in err_u for x in ["400", "INVALID_ARGUMENT", "SPEECH_METADATA", "MULTI-SPEAKER"]):
            raise

    # 3) Kesin Yedek: Konuşmacıları sırayla tts_single ile üretip birleştir
    st.toast("ℹ️ Çoklu konuşmacı sıralı sentez modunda birleştiriliyor…", icon="🎭")
    last_ai = 0
    if PYDUB_OK:
        merged = AudioSegment.empty()
        for sp, utt in turns:
            v_sel = v1 if sp == sp1 else v2
            rw, mm, last_ai = tts_single(model, utt, v_sel, lang, "")
            wv = pcm2wav(rw, mm)
            seg = AudioSegment.from_file(io.BytesIO(wv), format="wav")
            if len(merged) > 0:
                merged += AudioSegment.silent(150, frame_rate=seg.frame_rate)
            merged += seg
        return seg_to_wav(merged), "audio/wav", last_ai
    else:
        pcm_chunks = []
        for idx_t, (sp, utt) in enumerate(turns):
            v_sel = v1 if sp == sp1 else v2
            rw, mm, last_ai = tts_single(model, utt, v_sel, lang, "")
            if rw[:4] == b"RIFF" and len(rw) > 44:
                rw = rw[44:]
            if idx_t > 0:
                pcm_chunks.append(b"\x00" * (24000 * 2 * 150 // 1000))
            pcm_chunks.append(rw)
        return b"".join(pcm_chunks), "audio/L16;rate=24000", last_ai

def ai_write_anons(topic: str, tone: str = "Enerjik radyo sunucusu") -> str:
    if not GEMINI_OK:
        return f"[excitedly] Şimdi İmaj FM'de {topic} sizlerle! [normal] Keyifli dinlemeler!"
    ak, ai = get_key()
    if not ak:
        raise RuntimeError("AI metin yazarı için kullanılabilir API anahtarı yok.")
    prompt = (
        f"İmaj FM radyosu için kısa, akıcı ve profesyonel bir Türkçe radyo anonsu yaz (maksimum 2-3 cümle). "
        f"Konu / Şarkı: '{topic}'. Ton: {tone}. "
        f"Cümle başlarına uygun yerlere sadece şu duygu etiketlerinden koy: [excitedly], [normal], [whispers], [seriously]. "
        f"Sadece okunacak anons metnini döndür, açıklama yazma."
    )
    c = genai.Client(api_key=ak)
    r = c.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    consume(ai, len(prompt))
    return (r.text or "").strip()

# ═══════════════════════════ PYDUB & YAYIN DSP MOTORU ════════════
def unify_seg(seg, sr: int = 44100, ch: int = 2, sw: int = 2):
    if not PYDUB_OK or seg is None:
        return seg
    return seg.set_frame_rate(sr).set_channels(ch).set_sample_width(sw)

def norm_seg(seg, db: float = -14.0):
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
    seg1, seg2 = unify_seg(seg1), unify_seg(seg2)
    cf = min(int(crossfade_ms), max(0, len(seg1) // 3), max(0, len(seg2) // 3))
    return seg1.append(seg2, crossfade=cf) if cf >= 10 else (seg1 + seg2)

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
        low, high = int(params.get("low", 100)), int(params.get("high", 12000))
        gain, noise_lvl = float(params.get("gain", 0)), float(params.get("noise", 0.0))
        if high < 20000:
            seg = seg.low_pass_filter(high)
        if low > 20:
            seg = seg.high_pass_filter(low)
        if gain != 0:
            seg = seg + gain
        if noise_lvl > 0 and NP_OK and len(seg) > 0:
            sr, ch, sw = seg.frame_rate, seg.channels, seg.sample_width
            n_samples = int(len(seg) / 1000.0 * sr) * ch
            if n_samples > 0:
                amp = (2 ** (8 * sw - 1) - 1) * min(noise_lvl, 0.25)
                noise_arr = np.random.normal(0, amp, n_samples).clip(-32767, 32767).astype(np.int16)
                noise_seg = AudioSegment(noise_arr.tobytes(), frame_rate=sr, sample_width=2, channels=ch)
                seg = seg.overlay(noise_seg)
        return norm_seg(seg)
    except Exception:
        return seg

def mix_fon_voice(fon_seg, voice_seg, fon_vol=-8, duck_db=-16, fi=600, fo=1200):
    if not PYDUB_OK:
        return voice_seg
    try:
        fon = norm_seg(unify_seg(fon_seg), -14.0) + fon_vol
        voice = norm_seg(unify_seg(voice_seg), -13.0)
        vl, fl = len(voice), len(fon)
        if vl == 0:
            return fon
        if fl == 0:
            return voice
        lead_ms, tail_ms = 500, 1800
        total_need = lead_ms + vl + tail_ms
        if fl < total_need:
            fon = fon * (total_need // fl + 1)
        fon = fon[:total_need]
        if fi > 0 and len(fon) > fi:
            fon = fon.fade_in(fi)
        f_pre, f_mid, f_post = fon[:lead_ms], fon[lead_ms:lead_ms + vl], fon[lead_ms + vl:]
        fm = min(400, vl // 4)
        if fm >= 15 and vl > 2 * fm:
            ducked_mid = (
                f_mid[:fm].fade(to_gain=duck_db, start=0, duration=fm)
                + (f_mid[fm:vl - fm] + duck_db)
                + f_mid[vl - fm:].fade(from_gain=duck_db, start=0, duration=fm)
            )
        else:
            ducked_mid = f_mid + duck_db
        if fo > 0 and len(f_post) > 10:
            f_post = f_post.fade_out(min(fo, len(f_post)))
        return norm_seg((f_pre + ducked_mid + f_post).overlay(voice, position=lead_ms), -14.0)
    except Exception:
        return voice_seg

def duck_and_overlay(music_seg, voice_seg, pos_ms: int, duck_db: float = -16.0, ramp_ms: int = 450, voice_gain_db: float = 1.5):
    if not PYDUB_OK:
        return music_seg
    music = norm_seg(unify_seg(music_seg), -14.0)
    voice = norm_seg(unify_seg(voice_seg), -13.5 + voice_gain_db)
    if len(voice) == 0:
        return music
    pos_ms = max(0, int(pos_ms))
    needed_len = pos_ms + len(voice) + 200
    if len(music) < needed_len:
        music = music + AudioSegment.silent(duration=needed_len - len(music), frame_rate=44100).set_channels(2).set_sample_width(2)
    half_r = ramp_ms // 2
    start_duck = max(0, pos_ms - half_r)
    end_duck = min(len(music), pos_ms + len(voice) + half_r)
    seg_pre, seg_mid, seg_post = music[:start_duck], music[start_duck:end_duck], music[end_duck:]
    r = min(ramp_ms, len(seg_mid) // 3)
    if r >= 15 and len(seg_mid) > 2 * r:
        mid_ducked = (
            seg_mid[:r].fade(to_gain=duck_db, start=0, duration=r)
            + (seg_mid[r:len(seg_mid) - r] + duck_db)
            + seg_mid[len(seg_mid) - r:].fade(from_gain=duck_db, start=0, duration=r)
        )
    else:
        mid_ducked = seg_mid + duck_db
    return (seg_pre + mid_ducked + seg_post).overlay(voice, position=pos_ms)

def build_track_audio(track: Dict, crossfade_ms: int = 1200) -> Tuple[Optional[object], List[str]]:
    notes = []
    song_path = track.get("path")
    if not song_path or not os.path.exists(song_path):
        return None, ["Şarkı dosyası bulunamadı"]
    song_seg = norm_seg(unify_seg(AudioSegment.from_file(song_path)), -14.0)
    duck_db = float(track.get("duck_db", -16.0))
    anons_gain = float(track.get("anons_gain_db", 1.5))
    ramp_ms = int(track.get("ramp_ms", 450))
    fon_vol = float(track.get("fon_vol_db", -8.0))

    fon_seg = None
    if track.get("fon_bytes"):
        fon_seg = AudioSegment.from_file(io.BytesIO(track["fon_bytes"]))
    elif track.get("fon_file") and os.path.exists(os.path.join(DIRS["fon"], track["fon_file"])):
        fon_seg = AudioSegment.from_file(os.path.join(DIRS["fon"], track["fon_file"]))

    jingle_seg = None
    if track.get("jingle_bytes"):
        jingle_seg = norm_seg(unify_seg(AudioSegment.from_file(io.BytesIO(track["jingle_bytes"]))), -14.0)
    elif track.get("jingle_file") and os.path.exists(os.path.join(DIRS["jingles"], track["jingle_file"])):
        jingle_seg = norm_seg(unify_seg(AudioSegment.from_file(os.path.join(DIRS["jingles"], track["jingle_file"]))), -14.0)
    jingle_pos = track.get("jingle_pos", "Şarkı Başı")

    anons_seg = None
    if track.get("anons_bytes"):
        anons_seg = AudioSegment.from_file(io.BytesIO(track["anons_bytes"]))
    elif track.get("anons_file") and os.path.exists(os.path.join(DIRS["anons"], track["anons_file"])):
        anons_seg = AudioSegment.from_file(os.path.join(DIRS["anons"], track["anons_file"]))
    elif track.get("anons_arc_id"):
        ent = next((e for e in st.session_state._archive if e["id"] == track["anons_arc_id"]), None)
        if ent and ent.get("wav"):
            anons_seg = AudioSegment.from_file(io.BytesIO(ent["wav"]))

    end_anons_seg = None
    if track.get("end_anons_enabled"):
        if track.get("end_anons_bytes"):
            end_anons_seg = AudioSegment.from_file(io.BytesIO(track["end_anons_bytes"]))
        elif track.get("end_anons_arc_id"):
            ent2 = next((e for e in st.session_state._archive if e["id"] == track["end_anons_arc_id"]), None)
            if ent2 and ent2.get("wav"):
                end_anons_seg = AudioSegment.from_file(io.BytesIO(ent2["wav"]))

    pre_block, post_block = AudioSegment.empty(), AudioSegment.empty()
    pos_mode = track.get("anons_pos", ANONS_POSITIONS[0])
    offset_sec = float(track.get("anons_offset_sec", 6.0))

    if anons_seg is not None:
        anons_u = norm_seg(unify_seg(anons_seg), -13.5 + anons_gain)
        if pos_mode.startswith("⏮️"):
            anons_blk = mix_fon_voice(fon_seg, anons_u, fon_vol, duck_db) if fon_seg is not None else anons_u
            if jingle_seg is not None and jingle_pos == "Anons Öncesi":
                pre_block = safe_append(jingle_seg, anons_blk, min(400, crossfade_ms))
                notes.append("Jingle → Anons (Başı)")
            else:
                pre_block = anons_blk
                notes.append("Anons (Başı)" + (" + Fon" if fon_seg is not None else ""))
        elif "Başlangıçtan" in pos_mode:
            song_seg = duck_and_overlay(song_seg, anons_u, int(offset_sec * 1000), duck_db, ramp_ms, anons_gain)
            notes.append(f"Talk-Over @{offset_sec:.1f}s ({duck_db:.0f}dB)")
        elif "Bitişten" in pos_mode:
            pos_ms = max(0, len(song_seg) - int(offset_sec * 1000))
            song_seg = duck_and_overlay(song_seg, anons_u, pos_ms, duck_db, ramp_ms, anons_gain)
            notes.append(f"Outro Üzeri -{offset_sec:.1f}s ({duck_db:.0f}dB)")
        elif pos_mode.startswith("⏭️"):
            post_block = mix_fon_voice(fon_seg, anons_u, fon_vol, duck_db) if fon_seg is not None else anons_u
            notes.append("Anons (Sonu)" + (" + Fon" if fon_seg is not None else ""))

    if end_anons_seg is not None:
        end_u = norm_seg(unify_seg(end_anons_seg), -13.5 + anons_gain)
        end_blk = mix_fon_voice(fon_seg, end_u, fon_vol, duck_db) if fon_seg is not None else end_u
        post_block = safe_append(post_block, end_blk, 300) if len(post_block) > 0 else end_blk
        notes.append("+ Ek Son Anons")

    if jingle_seg is not None:
        if jingle_pos == "Şarkı Başı":
            pre_block = safe_append(pre_block, jingle_seg, 300) if len(pre_block) > 0 else jingle_seg
            notes.append("Jingle (Baş)")
        elif jingle_pos == "Şarkı Sonu":
            post_block = safe_append(jingle_seg, post_block, 300) if len(post_block) > 0 else jingle_seg
            notes.append("Jingle (Son)")

    combined = song_seg
    if len(pre_block) > 0:
        combined = safe_append(pre_block, combined, min(crossfade_ms, 800))
    if len(post_block) > 0:
        combined = safe_append(combined, post_block, min(crossfade_ms, 800))
    return combined, notes

def export_audio_bytes(seg, fmt: str = "mp3", bitrate: str = "192k", title: str = "İmaj FM Yayın") -> Tuple[bytes, str]:
    buf = io.BytesIO()
    if fmt.lower() == "mp3":
        try:
            tmp_mp3 = os.path.join(DIRS["output"], f"_tmp_{uuid.uuid4().hex[:8]}.mp3")
            seg.export(tmp_mp3, format="mp3", bitrate=bitrate)
            if MUTAGEN_OK:
                try:
                    try:
                        tags = ID3(tmp_mp3)
                    except ID3NoHeaderError:
                        tags = ID3()
                    tags.add(TIT2(encoding=3, text=title))
                    tags.add(TPE1(encoding=3, text="İmaj FM Otomasyon"))
                    tags.add(TALB(encoding=3, text=f"İmaj FM Yayın ({datetime.date.today().strftime('%d.%m.%Y')})"))
                    tags.save(tmp_mp3)
                except Exception:
                    pass
            with open(tmp_mp3, "rb") as f:
                data = f.read()
            if os.path.exists(tmp_mp3):
                os.remove(tmp_mp3)
            return data, "mp3"
        except Exception as e:
            st.warning(f"⚠️ MP3 kodlama hatası ({e}), WAV formatına geçildi.")
    seg.export(buf, format="wav")
    return buf.getvalue(), "wav"

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

def draw_wf(wb: bytes, h: float = 1.9):
    if not NP_OK or not wb:
        return
    try:
        with wave.open(io.BytesIO(wb), 'rb') as wf:
            frames, sr, sw_, ch_ = wf.readframes(wf.getnframes()), wf.getframerate(), wf.getsampwidth(), wf.getnchannels()
        if not frames or sr <= 0:
            return
        if sw_ == 1:
            s = np.frombuffer(frames, dtype=np.uint8).astype(np.float32) - 128.0
        elif sw_ == 2:
            s = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
        elif sw_ == 4:
            s = np.frombuffer(frames, dtype=np.int32).astype(np.float32)
        else:
            return
        if ch_ > 1:
            s = s[::ch_]
        if len(s) == 0:
            return
        ds = s[::max(1, len(s) // 2000)]
        ds /= (np.max(np.abs(ds)) or 1.0)
        t = np.linspace(0, len(s) / sr, len(ds))
        bg_c = CURRENT_THEME["plt_bg"]
        fig, ax = plt.subplots(figsize=(10, h), facecolor=bg_c)
        ax.set_facecolor(bg_c)
        ax.fill_between(t, ds, alpha=.7, color='#3b82f6')
        ax.fill_between(t, -np.abs(ds), alpha=.25, color='#8b5cf6')
        ax.axhline(0, color=CURRENT_THEME["border"], lw=.8)
        ax.set_xlim(0, max(t[-1], 0.01))
        ax.set_ylim(-1.1, 1.1)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.tick_params(colors=CURRENT_THEME["dim"], labelsize=7)
        plt.tight_layout(pad=.3)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    except Exception:
        pass

def list_audio(d: str) -> List[str]:
    exts = (".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac")
    return sorted(f for f in os.listdir(d) if f.lower().endswith(exts)) if os.path.isdir(d) else []

def save_upload(uf, dest_dir: str, custom_name: str = "", convert_to_wav: bool = True) -> Tuple[Optional[str], Optional[bytes]]:
    if uf is None:
        return None, None
    try:
        os.makedirs(dest_dir, exist_ok=True)
        fname = re.sub(r'[^\w\-.]', '_', custom_name or getattr(uf, 'name', 'upload.wav'))
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
                    os.remove(dest)
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

# ═══════════════════════════ DELAY REJİ & YENİ MODÜLLER ══════════
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
    return f"{(t // 3600) % 24:02d}:{(t % 3600) // 60:02d}:{t % 60:02d}"

def auto_bas(s: Dict) -> str:
    return f"[excitedly] Ve şimdi İmaj FM'de... {s.get('artist','?')}! [normal] '{s.get('title','?')}' sizlerle. [whispers] Keyfini çıkarın..."

def auto_son(s: Dict) -> str:
    return f"[normal] Dinlediğiniz {s.get('artist','?')} — '{s.get('title','?')}' idi. [excitedly] İmaj FM'de devam ediyoruz!"

def build_plan(playlist: List[Dict], start: str) -> List[Dict]:
    plan, cur = [], 0
    for song in playlist:
        sid, sd = song["id"], song_dur(song)
        if song.get("anons_bas"):
            txt = song.get("anons_bas_text") or auto_bas(song)
            ad = int(round(dur_bytes(song["anons_wav_bas"]))) if song.get("anons_wav_bas") else max(5, len(txt) // 15)
            plan.append({"time": add_time(start, cur), "off": cur, "type": "anons_bas", "song_id": sid, "label": f"🎙️ Baş → {song.get('title','?')}", "dur": ad, "wav": song.get("anons_wav_bas"), "text": txt})
            cur += ad
        if song.get("fon_aktif"):
            plan.append({"time": add_time(start, cur), "off": cur, "type": "fon", "song_id": sid, "label": f"🎶 Fon [{song.get('fon_tip','?')}] → {song.get('title','?')}", "dur": 4, "wav": None, "text": ""})
            cur += 4
        plan.append({"time": add_time(start, cur), "off": cur, "type": "song", "song_id": sid, "label": f"🎵 {song.get('artist','?')} — {song.get('title','?')}", "dur": sd, "wav": None, "text": ""})
        cur += sd
        if song.get("anons_son"):
            txt = song.get("anons_son_text") or auto_son(song)
            ad = int(round(dur_bytes(song["anons_wav_son"]))) if song.get("anons_wav_son") else max(4, len(txt) // 15)
            plan.append({"time": add_time(start, cur), "off": cur, "type": "anons_son", "song_id": sid, "label": f"🎙️ Son ← {song.get('title','?')}", "dur": ad, "wav": song.get("anons_wav_son"), "text": txt})
            cur += ad
    return plan

def make_yo_track(path: str, title: str = "", artist: str = "") -> Dict:
    meta = read_id3_meta(path)
    return {
        "id": song_uid(), "path": path, "title": title or meta["title"], "artist": artist or meta["artist"],
        "dur": dur_file(path), "anons_src": "Yok", "anons_arc_id": None, "anons_file": None,
        "anons_bytes": None, "anons_name": "", "anons_pos": ANONS_POSITIONS[1], "anons_offset_sec": 6.0,
        "end_anons_enabled": False, "end_anons_arc_id": None, "end_anons_bytes": None,
        "fon_src": "Yok", "fon_file": None, "fon_bytes": None, "fon_vol_db": -8.0,
        "jingle_src": "Yok", "jingle_file": None, "jingle_bytes": None, "jingle_pos": "Şarkı Başı",
        "duck_db": -16.0, "anons_gain_db": 1.5, "ramp_ms": 450,
    }

def generate_podcast_rss(title: str, desc: str, author: str, base_url: str, episodes: List[Dict], output_path: str) -> Optional[str]:
    try:
        rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:itunes="http://www.itunes.com/dtd/podcast-1.0.dtd" version="2.0">
<channel>
    <title>{xml_escape(title)}</title>
    <description>{xml_escape(desc)}</description>
    <language>tr</language>
    <itunes:author>{xml_escape(author)}</itunes:author>
    <itunes:explicit>no</itunes:explicit>
"""
        for ep in episodes:
            ep_url = xml_escape((base_url.rstrip("/") + "/" if base_url.strip() else "") + ep.get("url", ""))
            pub_date = ep.get("pub_date", datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000"))
            rss += f"""    <item>
        <title>{xml_escape(ep.get('title','Bölüm'))}</title>
        <description>{xml_escape(ep.get('description',''))}</description>
        <enclosure url="{ep_url}" length="{ep.get('length','0')}" type="audio/wav"/>
        <pubDate>{pub_date}</pubDate>
        <guid isPermaLink="false">{xml_escape(ep.get('guid', ep_url))}</guid>
    </item>\n"""
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
        d = {"id": uid, "name": name, "date": date_str, "time": broadcast_time, "songs": songs, "notes": notes, "created": datetime.datetime.now().isoformat(), "status": "pending"}
        with open(os.path.join(DIRS["schedules"], uid), "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Takvim hatası: {e}")
        return False

def get_scheduled_broadcasts() -> List[Dict]:
    res = []
    for fn in os.listdir(DIRS["schedules"]):
        if fn.endswith(".json"):
            try:
                with open(os.path.join(DIRS["schedules"], fn), encoding="utf-8") as f:
                    obj = json.load(f)
                    obj["_file"] = fn
                    res.append(obj)
            except Exception:
                pass
    return sorted(res, key=lambda x: (x.get("date", ""), x.get("time", "")))

def save_effect_preset(name: str, params: Dict) -> bool:
    try:
        with open(os.path.join(DIRS["effect_gallery"], f"{sfn(name)}.json"), "w", encoding="utf-8") as f:
            json.dump({"name": name, "params": params, "created": datetime.datetime.now().isoformat()}, f, ensure_ascii=False)
        return True
    except Exception:
        return False

def load_effect_presets() -> List[Dict]:
    res = []
    for fn in os.listdir(DIRS["effect_gallery"]):
        if fn.endswith(".json"):
            try:
                with open(os.path.join(DIRS["effect_gallery"], fn), encoding="utf-8") as f:
                    res.append(json.load(f))
            except Exception:
                pass
    return res

def prepare_rvc_dataset(audio_paths: List[str], output_dir: str, chunk_sec: int = 15, target_db: float = -16.0) -> int:
    if not PYDUB_OK:
        return 0
    try:
        os.makedirs(output_dir, exist_ok=True)
        cnt = 0
        for i, path in enumerate(audio_paths):
            if os.path.exists(path):
                seg = norm_seg(AudioSegment.from_file(path), target_db).set_frame_rate(44100).set_channels(1)
                for j, start in enumerate(range(0, len(seg), chunk_sec * 1000)):
                    ch = seg[start:start + chunk_sec * 1000]
                    if len(ch) >= 1500:
                        ch.export(os.path.join(output_dir, f"segment_{i+1:02d}_{j+1:02d}.wav"), format="wav")
                        cnt += 1
        return cnt
    except Exception as e:
        st.error(f"RVC hatası: {e}")
        return 0

def live_text_flow(text: str, delay: float = 0.04):
    ph = st.empty()
    acc = ""
    for w in text.split(" "):
        acc += w + " "
        ph.markdown(
            f"<div class='card b' style='font-size:1.12rem;line-height:1.6;'>{acc}<span style='color:{CURRENT_THEME['accent']};'>▌</span></div>",
            unsafe_allow_html=True,
        )
        time.sleep(delay)
    ph.markdown(f"<div class='card g' style='font-size:1.12rem;line-height:1.6;'>{text}</div>", unsafe_allow_html=True)

# ═══════════════════════════ UI YARDIMCI ═════════════════════════
def txt_stats(text: str):
    cc, wc = len(text), len(text.split())
    sc = max(1, text.count(".") + text.count("!") + text.count("?"))
    st.markdown(f"<div style='font-size:.73rem;color:{CURRENT_THEME['muted']};margin:3px 0 7px;'>📊 {cc} karakter · {wc} kelime · {sc} cümle · ~{max(1, cc/17):.0f}s</div>", unsafe_allow_html=True)

def tag_btns(sk: str, widget_key: str, prefix: str):
    cols = st.columns(len(ETAGS))
    for i, (em, lbl, tag) in enumerate(ETAGS):
        with cols[i]:
            if st.button(em, key=f"{prefix}_et{i}", help=lbl, use_container_width=True):
                nv = st.session_state.get(widget_key, st.session_state.get(sk, "")) + tag
                st.session_state[sk] = nv
                st.session_state[widget_key] = nv
                st.rerun()

def style_w(prefix: str) -> str:
    ps = st.selectbox("Preset", list(STYLE_PRESETS.keys()), label_visibility="collapsed", key=f"{prefix}_ps")
    ca, cb = st.columns(2)
    with ca:
        st.markdown(f"<div style='font-size:.7rem;font-weight:700;color:{CURRENT_THEME['accent2']};margin-bottom:3px;'>🇹🇷 TR Stil</div>", unsafe_allow_html=True)
        tr_ = st.text_area("TR", value=STYLE_PRESETS[ps], height=60, label_visibility="collapsed", key=f"{prefix}_str_{ps}")
    with cb:
        st.markdown("<div style='font-size:.7rem;font-weight:700;color:#d97706;margin-bottom:3px;'>🇬🇧 EN Style</div>", unsafe_allow_html=True)
        en_ = st.text_area("EN", value="", height=60, label_visibility="collapsed", key=f"{prefix}_sen")
    return " / ".join(filter(None, [tr_.strip(), en_.strip()]))

def res_card(wav: bytes, voice: str, ai: int, dk: str, dn: str):
    dur, qs = dur_bytes(wav), qs_bytes(wav)
    mt = audio_metrics(wav)
    bc = "#16a34a" if qs >= 70 else "#d97706" if qs >= 50 else "#dc2626"
    st.markdown(f"<div class='card g'>✅ {VOICES.get(voice, ('?',''))[0]} <b>{voice}</b> · API {ai+1} · {dur:.1f}s · Kalite: {qs}/100 · Seviye: {mt['dbfs']} · {mt['clip']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='qbar'><div class='qbar-f' style='width:{qs}%;background:{bc};'></div></div>", unsafe_allow_html=True)
    st.audio(wav, format="audio/wav")
    draw_wf(wav)
    st.download_button("💾 WAV İndir", wav, file_name=dn, mime="audio/wav", use_container_width=True, key=dk)

def model_selector(key_prefix: str) -> str:
    mkeys = list(MODELS.keys()) + ["__custom__"]
    sel = st.selectbox(
        "Model",
        mkeys,
        format_func=lambda k: MODELS[k] if k in MODELS else "✍️ Özel Model ID Gir",
        label_visibility="collapsed",
        key=f"{key_prefix}_msel",
    )
    if sel == "__custom__":
        return st.text_input("Özel Model ID", value="gemini-3.8-flash-tts", key=f"{key_prefix}_mcustom").strip() or "gemini-2.5-flash-tts"
    return sel

def lang_selector(key_prefix: str) -> str:
    lkeys = list(LANGUAGES.keys())
    return st.selectbox(
        "Dil",
        lkeys,
        index=1,
        format_func=lambda k: LANGUAGES[k],
        label_visibility="collapsed",
        key=f"{key_prefix}_lsel",
    )

# ═══════════════════════════ GİRİŞ ══════════════════════════════
def login_page():
    _, col, _ = st.columns([1, 1.05, 1])
    with col:
        st.markdown(f"""<div style='margin-top:60px;padding:32px 28px;background:{CURRENT_THEME['card']};border:1px solid {CURRENT_THEME['border']};border-radius:16px;'>
<h2 style='text-align:center;font-family:Syne,sans-serif;font-weight:800;font-size:1.5rem;margin:0 0 4px;color:{CURRENT_THEME['text']};'>🎙️ İmaj FM Stüdyo</h2>
<p style='text-align:center;color:{CURRENT_THEME['muted']};font-size:.75rem;letter-spacing:.12em;margin:0 0 18px;'>TTS & OTOMASYON v7.5 · GÜVENLİ GİRİŞ</p></div>""", unsafe_allow_html=True)
        u = st.text_input("Kullanıcı Adı", "", placeholder="👤 kullanıcı adı", label_visibility="collapsed")
        p = st.text_input("Şifre", "", type="password", placeholder="🔑 şifre", label_visibility="collapsed")
        try:
            exp_u, exp_p = st.secrets.get("APP_USER", "kenan"), st.secrets.get("APP_PASS", "imajfm")
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
    st.markdown(f"<div style='text-align:center;padding:4px 0 6px;font-family:Syne,sans-serif;font-size:1rem;font-weight:800;color:{CURRENT_THEME['text']};'>🎙️ İmaj FM <span style='color:{CURRENT_THEME['accent']};font-size:.72rem;'>v7.5</span></div>", unsafe_allow_html=True)

    sel_theme = st.selectbox("🎨 Tema", list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state["_theme_name"]), key="_theme_picker")
    if sel_theme != st.session_state["_theme_name"]:
        st.session_state["_theme_name"] = sel_theme
        st.rerun()

    ak_sb, ai_sb = get_key()
    tk_sb, tr_sb = pool_stats()
    used_a = st.session_state._api_pool[ai_sb]["used"] if ai_sb >= 0 else 0
    rem_a = MAX_PER_KEY - used_a if ai_sb >= 0 else 0
    pct_a = used_a / MAX_PER_KEY if ai_sb >= 0 else 1
    bc_a = "#16a34a" if pct_a < .6 else "#d97706" if pct_a < .9 else "#dc2626"

    with st.expander(f"🗝️ API Havuzu · {tk_sb}/10 · {tr_sb} kalan", expanded=True):
        if ak_sb:
            lbl_a = st.session_state._api_pool[ai_sb].get("label", f"API {ai_sb+1}")
            st.markdown(f"""<div class='card b' style='padding:8px 10px;font-size:.76rem;'>
Aktif: <b>{lbl_a}</b> · Kalan: <b>{rem_a}/{MAX_PER_KEY}</b> · Toplam: <b>{tr_sb}</b>
<div class='qbar'><div class='qbar-f' style='width:{pct_a*100:.0f}%;background:{bc_a};'></div></div>
<div style='font-size:.66rem;color:{CURRENT_THEME['muted']};'>Oto-rotasyon & 429/Model Fallback aktif</div></div>""", unsafe_allow_html=True)
        else:
            st.markdown("<div class='card r'>⛔ API anahtarı yok!</div>", unsafe_allow_html=True)
        for i in range(10):
            slot = st.session_state._api_pool[i]
            used_i, has = slot["used"], bool(slot["key"].strip())
            full, warn = (has and used_i >= MAX_PER_KEY), (has and used_i >= int(MAX_PER_KEY * .6) and used_i < MAX_PER_KEY)
            is_ac = (i == st.session_state._active_idx) and has and not full
            lbl_i = slot.get("label", f"API {i+1}")
            icon = "⬜" if not has else ("🔴" if full else ("🟡" if warn else "🟢"))
            badge = "boş" if not has else ("DOLU" if full else f"{used_i}/{MAX_PER_KEY}")
            with st.expander(f"{icon} {lbl_i}{' ◀' if is_ac else ''} · {badge}", expanded=False):
                nl = st.text_input(f"İ{i}", value=lbl_i, label_visibility="collapsed", key=f"lbl_{i}")
                if nl != lbl_i:
                    st.session_state._api_pool[i]["label"] = nl
                    st.rerun()
                nk = st.text_input(f"K{i}", value=slot["key"], type="password", placeholder="AIzaSy...", label_visibility="collapsed", key=f"key_{i}")
                if nk != slot["key"]:
                    st.session_state._api_pool[i]["key"] = nk
                    st.rerun()
                k1, k2, k3 = st.columns(3)
                with k1:
                    if st.button("🔄", key=f"rst_{i}", use_container_width=True, help="Sıfırla"):
                        st.session_state._api_pool[i]["used"] = 0
                        st.rerun()
                with k2:
                    if st.button("▶", key=f"act_{i}", use_container_width=True, help="Aktif"):
                        st.session_state._active_idx = i
                        st.rerun()
                with k3:
                    if st.button("🗑️", key=f"del_{i}", use_container_width=True, help="Sil"):
                        st.session_state._api_pool[i] = {"key": "", "used": 0, "label": f"API {i+1}"}
                        st.rerun()

    with st.expander(f"🚀 Otomasyon Akışı · {len(st.session_state._yo_tracks)} şarkı", expanded=False):
        if not st.session_state._yo_tracks:
            st.caption("Boş. Yayın Otomasyon sekmesinden ekleyin.")
        else:
            for i, yt in enumerate(st.session_state._yo_tracks[:8]):
                st.markdown(f"<div style='font-size:.73rem;padding:2px 0;'>{i+1}. <b>{yt['title'][:20]}</b> ({fmt_dur(yt['dur'])})</div>", unsafe_allow_html=True)

    pl_songs = list_audio(DIRS["playlist"])
    fon_files = list_audio(DIRS["fon"])
    with st.expander(f"📂 Kütüphane · {len(pl_songs)} şarkı · {len(fon_files)} fon", expanded=False):
        st.caption(f"Arşiv: {len(st.session_state._archive)} · Jingle: {len(list_audio(DIRS['jingles']))}")

    if st.button("🚪 Çıkış Yap", use_container_width=True, key="logout_btn"):
        st.session_state._giris = False
        st.rerun()

# ═══════════════════════════ HEADER ═════════════════════════════
stat_g = st.session_state._api_stats
tk_m, tr_m = pool_stats()
ak_chk, ai_m = get_key()

st.markdown("""<div class='hdr'><h1>🎙️ İmaj FM · Seslendirme & Yayın Otomasyon Stüdyosu</h1>
<p><span class='ldot'></span>Gemini Flash TTS (2.5 / 3.1 / 3.8) · AI Anons Yazarı · Şarkı İçi/Başı/Sonu Talk-Over · MP3 Yayın Çıktısı · Yüksek Kontrast</p></div>""", unsafe_allow_html=True)

c8 = st.columns(8)
defs = [("30", "Ses"), (f"{tk_m}/10", "API", "g"), (f"{tr_m}", "Kalan", "a"),
        (f"{len(st.session_state._archive)}", "Arşiv", "b"), (f"{stat_g.get('calls', 0)}", "İstek"),
        (f"{stat_g.get('secs', 0):.0f}s", "Ses", "p"), (f"{len(st.session_state._yo_tracks)}", "Otomasyon", "t"),
        (f"{len(pl_songs)}", "Şarkı")]
for col, (val, lbl, *cls) in zip(c8, defs):
    with col:
        st.markdown(f'<div class="mbox {cls[0] if cls else ""}"><div class="v">{val}</div><div class="l">{lbl}</div></div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

if not GEMINI_OK:
    st.error("⚠️ `google-genai` kurulu değil! `pip install google-genai` çalıştırın.")
elif ak_chk is None:
    st.warning("⛔ API anahtarı yok! Sol panelden ekleyin (Otomasyon ve ses araçları anahtarsız da çalışır).")

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
        st.markdown("<span class='sl'>▶ Şablon & AI Anons Yazarı</span>", unsafe_allow_html=True)
        tmpl1 = st.selectbox("Ş1", ["— Yok —"] + list(TEMPLATES.keys()), label_visibility="collapsed", key="tmpl1")
        if tmpl1 != "— Yok —" and st.button("📥 Şablonu Yükle", key="ltmpl1"):
            st.session_state._t_tek = st.session_state.ta1 = TEMPLATES[tmpl1]
            st.rerun()

        ai_c1, ai_c2 = st.columns([2, 1])
        with ai_c1:
            ai_topic1 = st.text_input("AI Konu", "", placeholder="✨ AI Konu yaz (örn: Akşam trafiği & Sezen Aksu)...", label_visibility="collapsed", key="ai_topic1")
        with ai_c2:
            if st.button("✨ AI Metin Yaz", use_container_width=True, key="ai_write_t1"):
                if ai_topic1.strip():
                    try:
                        gen_t = ai_write_anons(ai_topic1.strip())
                        st.session_state._t_tek = st.session_state.ta1 = gen_t
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ {e}")

        st.markdown("<span class='sl'>▶ Model & Dil</span>", unsafe_allow_html=True)
        mdl1 = model_selector("t1")
        lng1 = lang_selector("t1")

        st.markdown("<span class='sl'>▶ Ses & EQ</span>", unsafe_allow_html=True)
        cn1 = st.radio("CN1", ["Tümü", "♀ Kadın", "♂ Erkek"], horizontal=True, label_visibility="collapsed", key="cn1")
        f1 = {k: v for k, v in VOICES.items() if cn1 == "Tümü" or (cn1 == "♀ Kadın" and v[0] == "♀") or (cn1 == "♂ Erkek" and v[0] == "♂")}
        vc1 = st.selectbox("V1", list(f1.keys()), format_func=lambda x: f"{VOICES[x][0]} {x} — {VOICES[x][1]}", label_visibility="collapsed", key="v1")
        eq1 = st.selectbox("EQ", EQ_OPTS, label_visibility="collapsed", key="eq1")

        st.markdown("<span class='sl'>▶ Stil</span>", unsafe_allow_html=True)
        sty1 = style_w("t1")

        fa, fb = st.columns([2, 1])
        with fa:
            fname1 = st.text_input("FN", "", placeholder="⭐ Favori ismi…", label_visibility="collapsed", key="fname1")
        with fb:
            if st.button("⭐ Favoriye Ekle", key="fadd1", use_container_width=True):
                cur_t = st.session_state.get("ta1", st.session_state._t_tek)
                if fname1.strip() and cur_t.strip():
                    st.session_state._favorites.append({"id": uuid.uuid4().hex[:8], "name": fname1.strip(), "text": cur_t, "voice": vc1, "model": mdl1, "lang": lng1})
                    st.success("⭐ Eklendi!")
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
            if st.button("📺 Canlı Prompter", use_container_width=True, key="btn_prompter"):
                if txt1.strip():
                    live_text_flow(txt1, delay=0.07)

        if gen_clicked:
            if not txt1.strip():
                st.warning("⚠️ Metin boş.")
            else:
                with st.spinner(f"🎙️ {vc1} seslendiriyor…"):
                    try:
                        raw, mime, used_ai = tts_single(mdl1, txt1, vc1, lng1, sty1)
                        wav = pcm2wav(raw, mime)
                        if PYDUB_OK and eq1 != "Ham":
                            wav = seg_to_wav(norm_seg(apply_eq(AudioSegment.from_file(io.BytesIO(wav), format="wav"), eq1)))
                        arc_add(vc1, mdl1, lng1, sty1, txt1, wav, "tek")
                        st.session_state._last_tek = {"wav": wav, "voice": vc1, "ai": used_ai, "dn": f"imajfm_{vc1.lower()}_{lng1}.wav"}
                    except Exception as e:
                        st.error(f"❌ {e}")

        if st.session_state._last_tek:
            lt = st.session_state._last_tek
            res_card(lt["wav"], lt["voice"], lt["ai"], "dl1", lt["dn"])

# ════════════════ T2 — ÇİFT KONUŞMACI ══════════════════════════
with t2:
    st.markdown("<div class='card b'>🎭 İki konuşmacı — Multi-speaker Gemini TTS (Oto 3 katmanlı yedek aktif) · Tek WAV çıktı</div>", unsafe_allow_html=True)
    cL2, cR2 = st.columns([1.05, 1], gap="large")
    with cL2:
        tmpl2 = st.selectbox("Ş2", ["— Yok —"] + list(TEMPLATES.keys()), label_visibility="collapsed", key="tmpl2")
        if tmpl2 != "— Yok —" and st.button("📥 Yükle", key="ltmpl2"):
            st.session_state._t_cift = st.session_state.ta2 = TEMPLATES[tmpl2]
            st.rerun()
        mdl2 = model_selector("t2")
        lng2 = lang_selector("t2")
        st.markdown("<span class='sl'>▶ Konuşmacı 1 & 2</span>", unsafe_allow_html=True)
        ca, cb = st.columns([1, 2])
        with ca: sp1n = st.text_input("S1N", "Sunucu", label_visibility="collapsed", key="sp1n")
        with cb: sp1v = st.selectbox("S1V", list(VOICES.keys()), format_func=lambda x: f"{VOICES[x][0]} {x}", label_visibility="collapsed", index=list(VOICES.keys()).index("Kore"), key="sp1v")
        cc, cd = st.columns([1, 2])
        with cc: sp2n = st.text_input("S2N", "Misafir", label_visibility="collapsed", key="sp2n")
        with cd: sp2v = st.selectbox("S2V", list(VOICES.keys()), format_func=lambda x: f"{VOICES[x][0]} {x}", label_visibility="collapsed", index=list(VOICES.keys()).index("Fenrir"), key="sp2v")
        eq2 = st.selectbox("EQ2", EQ_OPTS, label_visibility="collapsed", key="eq2")
    with cR2:
        st.markdown("<span class='sl'>▶ Diyalog Metni</span>", unsafe_allow_html=True)
        tag_btns("_t_cift", "ta2", "t2")
        txt2 = st.text_area("TT2", height=220, label_visibility="collapsed", key="ta2")
        st.session_state._t_cift = txt2
        txt_stats(txt2)
        if st.button(f"🔴 {sp1n} & {sp2n} Diyalog Üret", type="primary", use_container_width=True, key="btn2"):
            if txt2.strip():
                with st.spinner("🎭 Diyalog üretiliyor…"):
                    try:
                        raw2, mime2, used_ai2 = tts_multi(mdl2, txt2, sp1n, sp1v, sp2n, sp2v, lng2)
                        wav2 = pcm2wav(raw2, mime2)
                        if PYDUB_OK and eq2 != "Ham":
                            wav2 = seg_to_wav(norm_seg(apply_eq(AudioSegment.from_file(io.BytesIO(wav2), format="wav"), eq2)))
                        arc_add(f"{sp1v}+{sp2v}", mdl2, lng2, "", txt2, wav2, "cift")
                        st.session_state._last_cift = {"wav": wav2, "voice": sp1v, "ai": used_ai2, "dn": f"imajfm_diyalog_{sp1v.lower()}.wav"}
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
            mdl3 = model_selector("t3")
            lng3 = lang_selector("t3")
            vc3 = st.selectbox("V3", list(VOICES.keys()), format_func=lambda x: f"{VOICES[x][0]} {x}", label_visibility="collapsed", key="v3")
            eq3 = st.selectbox("EQ3", EQ_OPTS, label_visibility="collapsed", key="eq3")
            sty3 = st.text_area("STY3", "", height=50, label_visibility="collapsed", placeholder="Stil (opsiyonel)", key="sty3")
            rpm_delay = st.slider("İstekler arası bekleme (sn)", 0, 21, 0, key="rpm_delay3")
        with cR3:
            txt3 = st.text_area("TT3", value=st.session_state._t_bulk, height=210, label_visibility="collapsed", key="ta3")
            st.session_state._t_bulk = txt3
            lines3 = [l.strip() for l in txt3.splitlines() if l.strip()]
            if st.button(f"🔴 {len(lines3)} Satırı Üret", type="primary", use_container_width=True, key="btn3") and lines3:
                res3, err3 = [], []
                prog3 = st.progress(0)
                for idx3, line3 in enumerate(lines3):
                    try:
                        raw3, mime3, _ = tts_single(mdl3, line3, vc3, lng3, sty3)
                        wav3 = pcm2wav(raw3, mime3)
                        if PYDUB_OK and eq3 != "Ham":
                            wav3 = seg_to_wav(norm_seg(apply_eq(AudioSegment.from_file(io.BytesIO(wav3), format="wav"), eq3)))
                        arc_add(vc3, mdl3, lng3, sty3, line3, wav3, "bulk")
                        res3.append((f"{idx3+1:02d}_{vc3.lower()}_{sfn(line3, 12)}.wav", wav3, line3))
                    except Exception as e:
                        err3.append(f"Satır {idx3+1}: {e}")
                    prog3.progress((idx3 + 1) / len(lines3))
                    if rpm_delay > 0 and idx3 < len(lines3) - 1:
                        time.sleep(rpm_delay)
                st.session_state._last_bulk_manual = {"res": res3, "err": err3, "zip": make_zip([(fn, wb) for fn, wb, _ in res3]) if res3 else None, "vc": vc3}
            if st.session_state._last_bulk_manual:
                bm = st.session_state._last_bulk_manual
                if bm["res"]:
                    st.success(f"✅ {len(bm['res'])} ses üretildi")
                    st.download_button("📦 ZIP İndir", bm["zip"], f"bulk_{bm['vc'].lower()}.zip", "application/zip", use_container_width=True, key="dl3zip")
                for e in bm["err"]:
                    st.markdown(f"<div class='card r'>❌ {e}</div>", unsafe_allow_html=True)
    with btab2:
        up_f = st.file_uploader("TXT veya CSV Yükle", type=["txt", "csv"], key="bulk_up")
        if up_f:
            lines_u = [l.strip() for l in up_f.getvalue().decode("utf-8", "ignore").splitlines() if l.strip()]
            if up_f.name.endswith(".csv"):
                lines_u = [l.split(",")[0].strip().strip('"') for l in lines_u if l.split(",")[0].strip()]
            st.session_state["bulk_up_lines"] = lines_u
            st.success(f"✅ {len(lines_u)} satır okundu")
        if st.session_state.get("bulk_up_lines"):
            mu_mdl = model_selector("mu_m")
            mu_vc = st.selectbox("Ses", list(VOICES.keys()), format_func=lambda x: f"{VOICES[x][0]} {x}", key="mu_v")
            if st.button("🚀 Dosyadan Toplu Üret", type="primary", use_container_width=True, key="mu_btn"):
                lu, res_u = st.session_state["bulk_up_lines"], []
                prog_u = st.progress(0)
                for i, ln in enumerate(lu):
                    try:
                        rw, mm, _ = tts_single(mu_mdl, ln, mu_vc, "tr-TR", "")
                        wv = pcm2wav(rw, mm)
                        arc_add(mu_vc, mu_mdl, "tr-TR", "", ln, wv, "bulk-file")
                        res_u.append((f"{i+1:03d}_{mu_vc.lower()}.wav", wv))
                    except Exception as e:
                        st.warning(f"Satır {i+1}: {e}")
                    prog_u.progress((i + 1) / len(lu))
                if res_u:
                    st.session_state._last_bulk_file = {"zip": make_zip(res_u), "count": len(res_u)}
            if st.session_state._last_bulk_file:
                bf = st.session_state._last_bulk_file
                st.download_button(f"📦 {bf['count']} Sesi ZIP İndir", bf["zip"], "bulk_dosya.zip", "application/zip", key="mu_zip")

# ════════════════ T4 — A/B TEST ══════════════════════════════════
with t4:
    st.markdown("<div class='card p'>🔬 Aynı metni iki farklı ses/model/stil ile karşılaştır</div>", unsafe_allow_html=True)
    ab_c1, ab_c2 = st.columns(2, gap="large")

    def ab_col(col, label, prefix, txt_key, ta_key, store_key, btn_key, dl_key, arc_mode):
        with col:
            st.markdown(f"<span class='sl'>{label}</span>", unsafe_allow_html=True)
            mdl = model_selector(prefix)
            lng = lang_selector(prefix)
            vc = st.selectbox("V", list(VOICES.keys()), format_func=lambda x: f"{VOICES[x][0]} {x}", label_visibility="collapsed", key=f"{prefix}_v")
            eq = st.selectbox("EQ", EQ_OPTS, label_visibility="collapsed", key=f"{prefix}_eq")
            ps = st.selectbox("PS", list(STYLE_PRESETS.keys()), label_visibility="collapsed", key=f"{prefix}_ps")
            sty = st.text_area("STY", value=STYLE_PRESETS[ps], height=50, label_visibility="collapsed", key=f"{prefix}_sty_{ps}")
            tag_btns(txt_key, ta_key, prefix)
            txt = st.text_area("TXT", height=110, label_visibility="collapsed", key=ta_key)
            st.session_state[txt_key] = txt
            if st.button(f"🔴 {label} Üret", use_container_width=True, key=btn_key) and txt.strip():
                with st.spinner(f"{vc} üretiyor…"):
                    try:
                        rw, mm, _ = tts_single(mdl, txt, vc, lng, sty)
                        wv = pcm2wav(rw, mm)
                        if PYDUB_OK and eq != "Ham":
                            wv = seg_to_wav(norm_seg(apply_eq(AudioSegment.from_file(io.BytesIO(wv), format="wav"), eq)))
                        arc_add(vc, mdl, lng, sty, txt, wv, arc_mode)
                        st.session_state[store_key] = {"wav": wv, "vc": vc, "qs": qs_bytes(wv), "dur": dur_bytes(wv)}
                    except Exception as e:
                        st.error(f"❌ {e}")
            if st.session_state.get(store_key):
                d = st.session_state[store_key]
                st.markdown(f"<div class='card b'>{d['vc']} · {d['dur']:.1f}s · {d['qs']}/100</div>", unsafe_allow_html=True)
                st.audio(d["wav"], format="audio/wav")
                draw_wf(d["wav"])
                st.download_button(f"💾 {label}", d["wav"], f"{prefix}_{d['vc'].lower()}.wav", "audio/wav", key=dl_key)

    ab_col(ab_c1, "🅐 VERSİYON A", "ab_a", "_t_ab1", "ab_a_ta", "_last_ab_a", "btnab1", "dlab", "ab-A")
    ab_col(ab_c2, "🅑 VERSİYON B", "ab_b", "_t_ab2", "ab_b_ta", "_last_ab_b", "btnab2", "dlbb", "ab-B")

# ════════════════ T5 — FAVORİLER ════════════════════════════════
with t5:
    favs = st.session_state._favorites
    if not favs:
        st.markdown("<div class='card b'>⭐ Henüz favori metin yok. Tek sekmesinden ekleyebilirsiniz.</div>", unsafe_allow_html=True)
    else:
        if st.button("🗑️ Tümünü Sil", key="fav_clr"):
            st.session_state._favorites = []
            st.rerun()
        for fi, fv in enumerate(favs):
            fc1, fc2, fc3, fc4 = st.columns([2, .7, .7, .5])
            with fc1:
                st.markdown(f"<div class='fav-card'><div class='fav-name'>⭐ {fv['name']}</div><div class='fav-prev'>{fv.get('voice','—')} · {fv['text'][:55]}</div></div>", unsafe_allow_html=True)
            with fc2:
                if st.button("📋 Yükle", key=f"fcp_{fv['id']}", use_container_width=True):
                    st.session_state._pending_t_tek = fv["text"]
                    st.rerun()
            with fc3:
                if st.button("🔴 Oku", key=f"fsp_{fv['id']}", use_container_width=True):
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
                st.audio(st.session_state[f"_fw_{fv['id']}"], format="audio/wav")

# ════════════════ T6 — DELAY REJİ ═══════════════════════════════
with t6:
    st.markdown("<div class='rjhdr'><h2>📻 Delay Reji — Yayın Otomasyonu</h2><p>Playlist · İnteraktif Sıralama · Şarkı başı/sonu anons · Fon geçişleri · Yayın planı · ZIP</p></div>", unsafe_allow_html=True)
    rj1, rj2, rj3, rj4 = st.tabs(["🎵 Playlist", "⚙️ Ayarlar", "📋 Yayın Planı", "🎬 Üretim & ZIP"])
    with rj1:
        pl = st.session_state._playlist
        nc1, nc2, nc3, nc4 = st.columns([2, 1.5, .5, .5])
        with nc1: nt = st.text_input("Şarkı", "", placeholder="Şarkı adı…", label_visibility="collapsed", key="nt")
        with nc2: na = st.text_input("Sanatçı", "", placeholder="Sanatçı…", label_visibility="collapsed", key="na")
        with nc3: ndm = st.number_input("Dk", 0, 30, 3, label_visibility="collapsed", key="ndm")
        with nc4: nds = st.number_input("Sn", 0, 59, 30, label_visibility="collapsed", key="nds")
        ba, bb = st.columns(2)
        with ba:
            if st.button("➕ Ekle", use_container_width=True, key="add_song") and nt.strip():
                st.session_state._playlist.append({"id": song_uid(), "title": nt.strip(), "artist": na.strip() or "Bilinmeyen", "duration_min": int(ndm), "duration_sec": int(nds), "anons_bas": False, "anons_son": False, "anons_bas_text": "", "anons_son_text": "", "fon_aktif": False, "fon_tip": "📻 Radyo Klasik", "anons_wav_bas": None, "anons_wav_son": None})
                st.session_state._rj_plan_ok = False
                st.rerun()
        with bb:
            if st.button("🎲 Demo Playlist", use_container_width=True, key="demo_pl"):
                demos = [("Gece Yarısı", "Sezen Aksu", 3, 45), ("Yüksek Yüksek Tepelere", "Barış Manço", 4, 12), ("Oy Benim Sarı Turnam", "Neşet Ertaş", 3, 55), ("Hayatımın Anlamı", "MFÖ", 3, 28)]
                st.session_state._playlist = [{"id": song_uid(), "title": t, "artist": ar, "duration_min": dm, "duration_sec": ds, "anons_bas": True, "anons_son": False, "anons_bas_text": "", "anons_son_text": "", "fon_aktif": False, "fon_tip": "📻 Radyo Klasik", "anons_wav_bas": None, "anons_wav_son": None} for t, ar, dm, ds in demos]
                st.session_state._rj_plan_ok = False
                st.rerun()
        pl_up = st.file_uploader("Şarkı dosyaları (MP3/WAV)", type=["mp3", "wav", "ogg", "flac", "m4a"], accept_multiple_files=True, key="pl_up")
        if pl_up:
            added = 0
            for uf in pl_up:
                uid_up = f"pl_{uf.name}_{uf.size}"
                if uid_up in st.session_state._processed_uploads:
                    continue
                dp, _ = save_upload(uf, DIRS["playlist"], uf.name, convert_to_wav=False)
                if dp:
                    st.session_state._processed_uploads.add(uid_up)
                    mn, sc = divmod(int(dur_file(dp)), 60)
                    meta = read_id3_meta(dp)
                    st.session_state._playlist.append({"id": song_uid(), "title": meta["title"], "artist": meta["artist"], "duration_min": mn, "duration_sec": sc, "anons_bas": False, "anons_son": False, "anons_bas_text": "", "anons_son_text": "", "fon_aktif": False, "fon_tip": "📻 Radyo Klasik", "anons_wav_bas": None, "anons_wav_son": None, "local_file": dp})
                    added += 1
            if added:
                st.rerun()
        if pl:
            for si, song in enumerate(pl):
                sid = song["id"]
                with st.expander(f"🎵 {si+1:02d}. {song['artist']} — {song['title']} [{fmt_dur(song_dur(song))}]", expanded=False):
                    tg1, tg2, tg3 = st.columns(3)
                    with tg1:
                        nb = st.checkbox("🎙️ Baş Anonsu", value=song.get("anons_bas", False), key=f"cb_{sid}")
                        if nb != song.get("anons_bas", False):
                            song["anons_bas"] = nb
                            if nb and not song.get("anons_bas_text"):
                                song["anons_bas_text"] = auto_bas(song)
                            st.rerun()
                    with tg2:
                        ns2 = st.checkbox("🎙️ Son Anonsu", value=song.get("anons_son", False), key=f"cs_{sid}")
                        if ns2 != song.get("anons_son", False):
                            song["anons_son"] = ns2
                            if ns2 and not song.get("anons_son_text"):
                                song["anons_son_text"] = auto_son(song)
                            st.rerun()
                    with tg3:
                        song["fon_aktif"] = st.checkbox("🎶 Fon Geçişi", value=song.get("fon_aktif", False), key=f"cf_{sid}")
                    if song.get("anons_bas"):
                        song["anons_bas_text"] = st.text_area("Baş Anons Metni", value=song.get("anons_bas_text") or auto_bas(song), height=65, key=f"bat_{sid}")
                    if song.get("anons_son"):
                        song["anons_son_text"] = st.text_area("Son Anons Metni", value=song.get("anons_son_text") or auto_son(song), height=65, key=f"sot_{sid}")
                    if st.button("🗑️ Kaldır", key=f"dsong_{sid}"):
                        pl.pop(si)
                        st.rerun()
            if st.button("🗑️ Playlist'i Temizle", key="clr_pl"):
                st.session_state._playlist = []
                st.rerun()
    with rj2:
        st.session_state._rj_model = model_selector("rj")
        st.session_state._rj_lang = lang_selector("rj")
        st.session_state._rj_voice = st.selectbox("Ses", list(VOICES.keys()), format_func=lambda x: f"{VOICES[x][0]} {x}", key="rj_vsel")
        st.session_state._rj_start = st.text_input("Başlangıç Saati", value=st.session_state._rj_start, key="rj_start_inp")
        rjps = st.selectbox("Stil", list(STYLE_PRESETS.keys()), key="rj_ps")
        st.session_state._rj_style = st.text_area("Stil Metni", value=STYLE_PRESETS[rjps], height=65, key=f"rj_sty_{rjps}")
    with rj3:
        if st.button("📋 Yayın Planını Oluştur", type="primary", key="gen_plan") and st.session_state._playlist:
            st.session_state._rj_plan = build_plan(st.session_state._playlist, st.session_state._rj_start)
            st.session_state._rj_plan_ok = True
        if st.session_state._rj_plan_ok:
            for blk in st.session_state._rj_plan:
                st.markdown(f"<div class='tl-block'><span class='tl-time'>{blk['time'][:5]}</span><span class='tl-type ttype-song'>{blk['type'].upper()}</span><span class='tl-lbl'>{blk['label']}</span><span class='tl-dur'>{fmt_dur(blk['dur'])}</span></div>", unsafe_allow_html=True)
    with rj4:
        pl4 = st.session_state._playlist
        needed = [(i, s, "bas") for i, s in enumerate(pl4) if s.get("anons_bas") and not s.get("anons_wav_bas")] + [(i, s, "son") for i, s in enumerate(pl4) if s.get("anons_son") and not s.get("anons_wav_son")]
        if needed and st.button(f"🔴 {len(needed)} Anonsu Toplu Üret", type="primary", use_container_width=True, key="bulk_rj"):
            prg = st.progress(0)
            for ni, (nsi, nsong, ntype) in enumerate(needed):
                ntxt = (nsong.get("anons_bas_text") or auto_bas(nsong)) if ntype == "bas" else (nsong.get("anons_son_text") or auto_son(nsong))
                try:
                    rw_b, mm_b, _ = tts_single(st.session_state._rj_model, ntxt, st.session_state._rj_voice, st.session_state._rj_lang, st.session_state._rj_style)
                    wv_b = pcm2wav(rw_b, mm_b)
                    pl4[nsi]["anons_wav_bas" if ntype == "bas" else "anons_wav_son"] = wv_b
                    arc_add(st.session_state._rj_voice, st.session_state._rj_model, st.session_state._rj_lang, st.session_state._rj_style, ntxt, wv_b, "reji")
                except Exception as e:
                    st.error(f"{nsong['title']}: {e}")
                prg.progress((ni + 1) / len(needed))
            st.rerun()
        zip_rj = [(f"{i+1:02d}_BAS_{sfn(s['title'],10)}.wav", s["anons_wav_bas"]) for i, s in enumerate(pl4) if s.get("anons_wav_bas")] + [(f"{i+1:02d}_SON_{sfn(s['title'],10)}.wav", s["anons_wav_son"]) for i, s in enumerate(pl4) if s.get("anons_wav_son")]
        if zip_rj:
            st.download_button(f"📦 {len(zip_rj)} Anonsu ZIP İndir", make_zip(zip_rj), "reji_anonslar.zip", "application/zip", use_container_width=True, key="dl_rj_zip")

# ════════════════ T7 — FON+ANONS MİKSERİ ════════════════════════
with t7:
    st.markdown("<div class='rjhdr'><h2>🎛️ Fon + Anons Mikseri</h2><p>Anons TTS + Fon müziği · Duck efekti · Fade-in/out · Arşivden miksleme · ZIP</p></div>", unsafe_allow_html=True)
    if not PYDUB_OK:
        st.error("⚠️ PyDub kurulu değil.")
    else:
        fon_mx = list_audio(DIRS["fon"])
        mx1, mx2, mx3 = st.tabs(["🎛️ Tek Miksleme", "📦 Toplu Fon", "🗄️ Arşivden"])
        with mx1:
            cLm, cRm = st.columns([1.1, 1], gap="large")
            with cLm:
                mx_mdl = model_selector("mx")
                mx_vc = st.selectbox("MX Ses", list(VOICES.keys()), format_func=lambda x: f"{VOICES[x][0]} {x}", key="mx_v")
                mx_up = st.file_uploader("Veya Hazır Anons WAV/MP3 Yükle", type=["wav", "mp3", "ogg"], key="mx_up")
                mx_uwav = save_upload(mx_up, DIRS["anons"], f"up_{mx_up.name}")[1] if mx_up else None
            with cRm:
                mx_txt = st.text_area("Anons Metni", "", height=90, key="mx_txt", placeholder="Anons metni yaz veya soldan ses yükle…")
                sel_fon = st.selectbox("Fon Müziği", fon_mx, key="sel_fon") if fon_mx else None
                fvol = st.slider("Fon Ses (dB)", -24, 0, -8, key="mx_fvol")
                duck = st.slider("Duck dB", -30, -6, -16, key="mx_duck")
                if st.button("🎛️ MİKSLE & OLUŞTUR", type="primary", use_container_width=True, key="mx_btn"):
                    aw = mx_uwav
                    if not aw and mx_txt.strip():
                        rw, mm, _ = tts_single(mx_mdl, mx_txt, mx_vc, "tr-TR", "")
                        aw = pcm2wav(rw, mm)
                        arc_add(mx_vc, mx_mdl, "tr-TR", "", mx_txt, aw, "tek")
                    if aw and sel_fon:
                        mx_out = mix_fon_voice(AudioSegment.from_file(os.path.join(DIRS["fon"], sel_fon)), AudioSegment.from_file(io.BytesIO(aw)), fvol, duck)
                        st.session_state._last_mx = {"wav": seg_to_wav(norm_seg(mx_out)), "fn": f"fon_anons_{int(time.time())}.wav"}
                if st.session_state._last_mx:
                    st.audio(st.session_state._last_mx["wav"], format="audio/wav")
                    st.download_button("📦 WAV İndir", st.session_state._last_mx["wav"], st.session_state._last_mx["fn"], "audio/wav", use_container_width=True, key="dl_mx")
        with mx2:
            arc_mx = [e for e in st.session_state._archive if e.get("wav")]
            if arc_mx and fon_mx:
                sf_bulk = st.selectbox("Fon", fon_mx, key="sfb")
                opts_ab = [f"{i+1}. {e['ts_s']} · {e['voice']} · {e['prev'][:28]}" for i, e in enumerate(arc_mx)]
                sel_ab = st.multiselect("Arşivden Seç", opts_ab, key="sel_ab")
                if sel_ab and st.button("📦 Toplu Uygula", key="bulk_fon"):
                    fs2 = AudioSegment.from_file(os.path.join(DIRS["fon"], sf_bulk))
                    res_b = [(f"fon_{arc_mx[opts_ab.index(s)]['id']}.wav", seg_to_wav(mix_fon_voice(fs2, AudioSegment.from_file(io.BytesIO(arc_mx[opts_ab.index(s)]["wav"]))))) for s in sel_ab]
                    st.session_state._last_mx_bulk = {"zip": make_zip(res_b), "count": len(res_b)}
                if st.session_state._last_mx_bulk:
                    st.download_button("📦 ZIP İndir", st.session_state._last_mx_bulk["zip"], "fon_toplu.zip", "application/zip", key="dl_toplu_fon")
            else:
                st.info("Arşivde ses veya kütüphanede fon yok.")
        with mx3:
            arc_mx3 = [e for e in st.session_state._archive if e.get("wav")]
            if arc_mx3 and fon_mx:
                opts_a3 = [f"{i+1}. {e['ts_s']} | {e['voice']} | {e['prev'][:32]}" for i, e in enumerate(arc_mx3)]
                ent = arc_mx3[opts_a3.index(st.selectbox("Arşivden", opts_a3, key="sel_a3"))]
                sf3 = st.selectbox("Fon", fon_mx, key="sf3")
                if st.button("🎛️ Uygula", key="arc_mix3"):
                    m3 = mix_fon_voice(AudioSegment.from_file(os.path.join(DIRS["fon"], sf3)), AudioSegment.from_file(io.BytesIO(ent["wav"])))
                    st.session_state._last_mx_arc = {"wav": seg_to_wav(norm_seg(m3)), "fn": f"arc_fon_{ent['id']}.wav"}
                if st.session_state._last_mx_arc:
                    st.audio(st.session_state._last_mx_arc["wav"], format="audio/wav")
                    st.download_button("💾 WAV", st.session_state._last_mx_arc["wav"], st.session_state._last_mx_arc["fn"], "audio/wav", key="dl_arc3")
            else:
                st.info("Arşiv veya fon klasörü boş.")

# ════════════════ T8 — GELİŞMİŞ YAYIN OTOMASYONU ═══════════════
with t8:
    st.markdown(
        "<div class='rjhdr'>"
        "<h2>🚀 Akıllı Yayın Otomasyonu — Tam MP3 Yayın Stüdyosu</h2>"
        "<p>Şarkı Yükle & Seç · Her Şarkıya Özel Anons (Başı / İçi Talk-Over / Sonu), Fon & Jingle · Anında Hızlı TTS · Müzik Kısma · MP3 Çıktısı</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    if not PYDUB_OK:
        st.error("⚠️ PyDub kurulu değil.")
    else:
        yo1, yo2, yo3 = st.tabs(["🎛️ Playlist & Tam Yayın (MP3)", "🔗 Reji Zincir Yayın", "✂️ Hızlı Ses Birleştir"])

        with yo1:
            st.markdown("<span class='sl'>1️⃣ Adım: Yayına Şarkı Ekle</span>", unsafe_allow_html=True)
            add_c1, add_c2 = st.columns([1.2, 1], gap="medium")
            with add_c1:
                yo_song_ups = st.file_uploader("📤 Bilgisayardan Şarkı Yükle (MP3/WAV/OGG/FLAC)", type=["mp3", "wav", "ogg", "flac", "m4a"], accept_multiple_files=True, key="yo_direct_ups")
                if yo_song_ups:
                    added_yo = 0
                    for uf in yo_song_ups:
                        uid_y = f"yo_up_{uf.name}_{uf.size}"
                        if uid_y in st.session_state._processed_uploads:
                            continue
                        dp, _ = save_upload(uf, DIRS["playlist"], uf.name, convert_to_wav=False)
                        if dp:
                            st.session_state._processed_uploads.add(uid_y)
                            st.session_state._yo_tracks.append(make_yo_track(dp))
                            added_yo += 1
                    if added_yo > 0:
                        st.success(f"✅ {added_yo} şarkı eklendi!")
                        st.rerun()
            with add_c2:
                lib_songs = list_audio(DIRS["playlist"])
                pick_lib = st.multiselect("📚 Kütüphanedeki Şarkılardan Seç", lib_songs, key="yo_pick_lib", placeholder="Şarkı seçin…")
                b_add_lib, b_add_rj = st.columns(2)
                with b_add_lib:
                    if st.button("➕ Seçilenleri Ekle", use_container_width=True, key="yo_btn_add_lib") and pick_lib:
                        for fn_l in pick_lib:
                            st.session_state._yo_tracks.append(make_yo_track(os.path.join(DIRS["playlist"], fn_l)))
                        st.rerun()
                with b_add_rj:
                    if st.button("📻 Delay Reji'den Aktar", use_container_width=True, key="yo_btn_from_rj"):
                        imp = 0
                        for rs in st.session_state._playlist:
                            lf = rs.get("local_file")
                            if not lf or not os.path.exists(lf):
                                pf = next((f for f in lib_songs if rs.get("title", "").lower() in f.lower()), None)
                                lf = os.path.join(DIRS["playlist"], pf) if pf else None
                            if lf and os.path.exists(lf):
                                trk = make_yo_track(lf, rs.get("title", ""), rs.get("artist", ""))
                                if rs.get("anons_wav_bas"):
                                    trk["anons_src"], trk["anons_bytes"], trk["anons_name"], trk["anons_pos"] = "📤 Dosyadan Yükle", rs["anons_wav_bas"], "Reji Baş", ANONS_POSITIONS[0]
                                if rs.get("anons_wav_son"):
                                    trk["end_anons_enabled"], trk["end_anons_bytes"] = True, rs["anons_wav_son"]
                                st.session_state._yo_tracks.append(trk)
                                imp += 1
                        if imp:
                            st.rerun()
                        else:
                            st.warning("Reji'de yerel dosyayla eşleşen şarkı yok.")

            st.markdown("<hr>", unsafe_allow_html=True)
            tracks = st.session_state._yo_tracks
            arc_list = [e for e in st.session_state._archive if e.get("wav")]
            arc_map = {f"{e['ts_s']} · {e['voice']} · {e['prev'][:26]}": e for e in arc_list}
            fon_list, jingle_list, anons_lib_list = list_audio(DIRS["fon"]), list_audio(DIRS["jingles"]), list_audio(DIRS["anons"])

            if not tracks:
                st.markdown("<div class='card a'>🎵 Yayın listeniz boş. Yukarıdan şarkı yükleyin veya kütüphaneden ekleyin.</div>", unsafe_allow_html=True)
            else:
                st.markdown("<span class='sl'>2️⃣ Adım: Global Müzik Kısma & Yayın Kuralları</span>", unsafe_allow_html=True)
                with st.expander("⚙️ Global Ses Kısma (Ducking), Crossfade & Otomatik Jingle Ayarları", expanded=True):
                    g1, g2, g3, g4 = st.columns(4)
                    with g1:
                        g_duck = st.slider("📉 Müzik Kısılma (dB)", -30, -3, -16, 1, key="yo_g_duck")
                        g_ramp = st.slider("🎚️ Kısılma Yumuşaklığı (ms)", 150, 1500, 450, 50, key="yo_g_ramp")
                    with g2:
                        g_anons_gain = st.slider("🎙️ Anons Kazancı (dB)", -6.0, 9.0, 1.5, 0.5, key="yo_g_again")
                        g_fon_vol = st.slider("🎶 Fon Seviyesi (dB)", -24, 0, -8, 1, key="yo_g_fvol")
                    with g3:
                        g_cf = st.slider("🔀 Crossfade (ms)", 0, 4000, 1500, 100, key="yo_g_cf")
                        g_gap = st.slider("⏸️ Şarkı Arası Boşluk (ms)", 0, 3000, 0, 100, key="yo_g_gap")
                    with g4:
                        g_comp = st.checkbox("📻 Radyo Kompresör", value=True, key="yo_g_comp")
                        g_norm = st.checkbox("📏 Master Normalize (-14 dBFS)", value=True, key="yo_g_norm")
                        g_start_time = st.text_input("🕐 Yayın Başlangıç Saati", value="08:00", key="yo_g_stime")

                    aj1, aj2, aj3 = st.columns(3)
                    with aj1: open_jingle = st.selectbox("🎺 Açılış Jingle", ["Yok"] + jingle_list, key="yo_open_j")
                    with aj2: close_jingle = st.selectbox("🎺 Kapanış Jingle", ["Yok"] + jingle_list, key="yo_close_j")
                    with aj3:
                        auto_j_every = st.selectbox("🔄 Her X Şarkıda Otomatik Jingle", [0, 2, 3, 4, 5], format_func=lambda x: "Kapalı" if x == 0 else f"Her {x} şarkıda bir", key="yo_auto_j_n")
                        auto_j_file = st.selectbox("Otomatik Ara Jingle", jingle_list if jingle_list else ["Yok"], key="yo_auto_j_f") if auto_j_every > 0 else "Yok"

                    if st.button("⚡ Bu Müzik Kısma / Ses Değerlerini Tüm Şarkılara Uygula", use_container_width=True, key="yo_apply_global"):
                        for ti in range(len(tracks)):
                            tracks[ti].update({"duck_db": float(g_duck), "anons_gain_db": float(g_anons_gain), "ramp_ms": int(g_ramp), "fon_vol_db": float(g_fon_vol)})
                        st.success("✅ Tüm şarkılara uygulandı!")
                        st.rerun()

                st.markdown(f"<span class='sl'>3️⃣ Adım: Şarkı Bazlı Anons, Fon, Jingle & Konum ({len(tracks)} Şarkı)</span>", unsafe_allow_html=True)
                for ti, trk in enumerate(tracks):
                    tid = trk["id"]
                    has_a = bool(trk.get("anons_bytes") or trk.get("anons_file") or trk.get("anons_arc_id"))
                    has_f = bool(trk.get("fon_bytes") or trk.get("fon_file"))
                    has_j = bool(trk.get("jingle_bytes") or trk.get("jingle_file"))
                    badges = []
                    if has_a: badges.append(f"🎙️ {trk.get('anons_pos','').split('(')[0].strip()}")
                    if trk.get("end_anons_enabled"): badges.append("🎙️ +Ek Son")
                    if has_f: badges.append("🎶 Fon")
                    if has_j: badges.append(f"🎺 {trk.get('jingle_pos','Jingle')}")
                    badges.append(f"📉 {trk.get('duck_db', -16):.0f}dB")

                    with st.expander(f"🎵 {ti+1:02d}. {trk['artist']} — {trk['title']} [{fmt_dur(trk['dur'])}]  |  {' · '.join(badges)}", expanded=(ti == 0 and not has_a)):
                        ord1, ord2, ord3, _ = st.columns([1, 1, 1, 3])
                        with ord1:
                            if ti > 0 and st.button("⬆️ Yukarı", key=f"yo_up_{tid}", use_container_width=True):
                                tracks[ti-1], tracks[ti] = tracks[ti], tracks[ti-1]
                                st.rerun()
                        with ord2:
                            if ti < len(tracks) - 1 and st.button("⬇️ Aşağı", key=f"yo_dn_{tid}", use_container_width=True):
                                tracks[ti+1], tracks[ti] = tracks[ti], tracks[ti+1]
                                st.rerun()
                        with ord3:
                            if st.button("🗑️ Kaldır", key=f"yo_del_{tid}", use_container_width=True):
                                tracks.pop(ti)
                                st.rerun()

                        tc1, tc2 = st.columns([1.15, 1], gap="medium")
                        with tc1:
                            st.markdown("<span class='sl2'>▸ Ana Anons Seçimi & Konumu</span>", unsafe_allow_html=True)
                            src_opts = ["Yok", "📂 Arşivden Seç", "📚 Kütüphaneden Seç", "📤 Dosyadan Yükle", "🎙️ Anında Hızlı TTS"]
                            cur_src = trk.get("anons_src", "Yok")
                            if cur_src not in src_opts: cur_src = "📤 Dosyadan Yükle" if trk.get("anons_bytes") else "Yok"
                            a_src = st.radio("Kaynak", src_opts, index=src_opts.index(cur_src), horizontal=True, label_visibility="collapsed", key=f"yo_asrc_{tid}")
                            trk["anons_src"] = a_src

                            if a_src == "Yok":
                                trk["anons_arc_id"] = trk["anons_file"] = trk["anons_bytes"] = None
                            elif a_src == "📂 Arşivden Seç":
                                trk["anons_file"] = trk["anons_bytes"] = None
                                if arc_list:
                                    akeys = list(arc_map.keys())
                                    cak = next((k for k, v in arc_map.items() if v["id"] == trk.get("anons_arc_id")), akeys[0])
                                    sel_ak = st.selectbox("Arşiv Ses", akeys, index=akeys.index(cak), key=f"yo_aarc_{tid}")
                                    trk["anons_arc_id"] = arc_map[sel_ak]["id"]
                                else:
                                    st.info("Arşivde ses yok.")
                            elif a_src == "📚 Kütüphaneden Seç":
                                trk["anons_arc_id"] = trk["anons_bytes"] = None
                                if anons_lib_list:
                                    caf = trk.get("anons_file") if trk.get("anons_file") in anons_lib_list else anons_lib_list[0]
                                    trk["anons_file"] = st.selectbox("Kütüphane Anons", anons_lib_list, index=anons_lib_list.index(caf), key=f"yo_alib_{tid}")
                                else:
                                    st.info("Anons klasörü boş.")
                            elif a_src == "📤 Dosyadan Yükle":
                                trk["anons_arc_id"] = trk["anons_file"] = None
                                up_a = st.file_uploader("Anons Dosyası (WAV/MP3)", type=["wav", "mp3", "ogg"], key=f"yo_aup_{tid}")
                                if up_a:
                                    trk["anons_bytes"], trk["anons_name"] = up_a.getvalue(), up_a.name
                                if trk.get("anons_bytes"):
                                    st.caption(f"✅ Yüklü: {trk.get('anons_name','Anons')} ({dur_bytes(trk['anons_bytes']):.1f}s)")
                            elif a_src == "🎙️ Anında Hızlı TTS":
                                trk["anons_arc_id"] = trk["anons_file"] = None
                                q_key = f"yo_qtxt_{tid}"
                                if q_key not in st.session_state:
                                    st.session_state[q_key] = auto_bas(trk)
                                q_col1, q_col2 = st.columns([2, 1])
                                with q_col1:
                                    q_vc = st.selectbox("Ses", list(VOICES.keys()), index=list(VOICES.keys()).index("Kore"), key=f"yo_qvc_{tid}")
                                with q_col2:
                                    if st.button("✨ AI Metin", key=f"yo_qai_{tid}", use_container_width=True):
                                        try:
                                            st.session_state[q_key] = ai_write_anons(f"{trk['artist']} - {trk['title']}")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ {e}")
                                q_txt = st.text_area("Anons Metni", height=68, key=q_key)
                                if st.button("🔴 Anında Seslendir & Ata", key=f"yo_qgen_{tid}", use_container_width=True):
                                    try:
                                        rw_q, mm_q, _ = tts_single("gemini-3.1-flash-tts-preview", q_txt, q_vc, "tr-TR", "")
                                        wv_q = pcm2wav(rw_q, mm_q)
                                        trk["anons_bytes"], trk["anons_name"] = wv_q, f"TTS_{q_vc}"
                                        arc_add(q_vc, "gemini-3.1-flash-tts-preview", "tr-TR", "", q_txt, wv_q, "otomasyon")
                                        st.success(f"✅ Üretildi ve atandı ({dur_bytes(wv_q):.1f}s)!")
                                    except Exception as e:
                                        st.error(f"❌ {e}")

                            if a_src != "Yok":
                                cur_pos = trk.get("anons_pos", ANONS_POSITIONS[1])
                                sel_pos = st.selectbox("📍 Anons Konumu", ANONS_POSITIONS, index=ANONS_POSITIONS.index(cur_pos) if cur_pos in ANONS_POSITIONS else 1, key=f"yo_apos_{tid}")
                                trk["anons_pos"] = sel_pos
                                max_sec = max(10, int(trk["dur"]) - 2)
                                if "Başlangıçtan" in sel_pos:
                                    trk["anons_offset_sec"] = st.slider("⏱️ Başlangıçtan Kaç sn Sonra?", 0.0, float(min(60, max_sec)), float(min(trk.get("anons_offset_sec", 6.0), max_sec)), 0.5, key=f"yo_aoff_{tid}")
                                elif "Bitişten" in sel_pos:
                                    trk["anons_offset_sec"] = st.slider("⏱️ Bitişten Kaç sn Önce?", 3.0, float(min(60, max_sec)), float(min(max(3.0, trk.get("anons_offset_sec", 12.0)), max_sec)), 0.5, key=f"yo_aoff_end_{tid}")

                            end_en = st.checkbox("➕ Ayrıca Şarkı Sonuna da Ek Anons Ekle", value=bool(trk.get("end_anons_enabled", False)), key=f"yo_enda_en_{tid}")
                            trk["end_anons_enabled"] = end_en
                            if end_en:
                                e_src = st.radio("Son Anons", ["📂 Arşiv", "📤 Dosya"], horizontal=True, key=f"yo_endsrc_{tid}")
                                if e_src == "📂 Arşiv" and arc_list:
                                    akeys2 = list(arc_map.keys())
                                    cak2 = next((k for k, v in arc_map.items() if v["id"] == trk.get("end_anons_arc_id")), akeys2[0])
                                    trk["end_anons_arc_id"] = arc_map[st.selectbox("Son Anons (Arşiv)", akeys2, index=akeys2.index(cak2), key=f"yo_endarc_{tid}")]["id"]
                                    trk["end_anons_bytes"] = None
                                elif e_src == "📤 Dosya":
                                    up_ea = st.file_uploader("Son Anons Dosyası", type=["wav", "mp3", "ogg"], key=f"yo_endup_{tid}")
                                    if up_ea:
                                        trk["end_anons_bytes"], trk["end_anons_arc_id"] = up_ea.getvalue(), None

                        with tc2:
                            st.markdown("<span class='sl3'>▸ Fon Müziği (Şarkı Başı/Sonu Anons Altı)</span>", unsafe_allow_html=True)
                            f_opts = ["Yok", "📚 Fon Kütüphanesi", "📤 Dosyadan Yükle"]
                            f_src = st.radio("Fon", f_opts, index=f_opts.index(trk.get("fon_src", "Yok")) if trk.get("fon_src", "Yok") in f_opts else 0, horizontal=True, label_visibility="collapsed", key=f"yo_fsrc_{tid}")
                            trk["fon_src"] = f_src
                            if f_src == "Yok": trk["fon_file"] = trk["fon_bytes"] = None
                            elif f_src == "📚 Fon Kütüphanesi" and fon_list:
                                trk["fon_bytes"] = None
                                trk["fon_file"] = st.selectbox("Fon Dosyası", fon_list, index=fon_list.index(trk["fon_file"]) if trk.get("fon_file") in fon_list else 0, key=f"yo_flib_{tid}")
                            elif f_src == "📤 Dosyadan Yükle":
                                trk["fon_file"] = None
                                up_f = st.file_uploader("Fon Müziği", type=["mp3", "wav", "ogg"], key=f"yo_fup_{tid}")
                                if up_f: trk["fon_bytes"] = up_f.getvalue()

                            st.markdown("<span class='sl3'>▸ Jingle / Sweeper</span>", unsafe_allow_html=True)
                            j_opts = ["Yok", "📚 Jingle Kütüphanesi", "📤 Dosyadan Yükle"]
                            j_src = st.radio("Jingle", j_opts, index=j_opts.index(trk.get("jingle_src", "Yok")) if trk.get("jingle_src", "Yok") in j_opts else 0, horizontal=True, label_visibility="collapsed", key=f"yo_jsrc_{tid}")
                            trk["jingle_src"] = j_src
                            if j_src == "Yok": trk["jingle_file"] = trk["jingle_bytes"] = None
                            elif j_src == "📚 Jingle Kütüphanesi" and jingle_list:
                                trk["jingle_bytes"] = None
                                trk["jingle_file"] = st.selectbox("Jingle Dosyası", jingle_list, index=jingle_list.index(trk["jingle_file"]) if trk.get("jingle_file") in jingle_list else 0, key=f"yo_jlib_{tid}")
                            elif j_src == "📤 Dosyadan Yükle":
                                trk["jingle_file"] = None
                                up_j = st.file_uploader("Jingle Dosyası", type=["mp3", "wav", "ogg"], key=f"yo_jup_{tid}")
                                if up_j: trk["jingle_bytes"] = up_j.getvalue()
                            if j_src != "Yok":
                                trk["jingle_pos"] = st.selectbox("Jingle Konumu", JINGLE_POSITIONS, index=JINGLE_POSITIONS.index(trk.get("jingle_pos", "Şarkı Başı")), key=f"yo_jpos_{tid}")

                            st.markdown("<span class='sl3'>▸ Müzik Kısma (Ducking) & Ses Dengesi</span>", unsafe_allow_html=True)
                            sd1, sd2 = st.columns(2)
                            with sd1:
                                trk["duck_db"] = st.slider("📉 Kısılma (dB)", -30.0, -3.0, float(trk.get("duck_db", -16.0)), 1.0, key=f"yo_duck_{tid}")
                                trk["ramp_ms"] = st.slider("🎚️ Geçiş (ms)", 150, 1500, int(trk.get("ramp_ms", 450)), 50, key=f"yo_ramp_{tid}")
                            with sd2:
                                trk["anons_gain_db"] = st.slider("🎙️ Anons (dB)", -6.0, 9.0, float(trk.get("anons_gain_db", 1.5)), 0.5, key=f"yo_again_{tid}")
                                if f_src != "Yok":
                                    trk["fon_vol_db"] = st.slider("🎶 Fon (dB)", -24.0, 0.0, float(trk.get("fon_vol_db", -8.0)), 1.0, key=f"yo_fvol_{tid}")

                            if st.button("🎧 Bu Şarkıyı Önizle", use_container_width=True, key=f"yo_prev_{tid}"):
                                prev_seg, _ = build_track_audio(trk, g_cf)
                                if prev_seg is not None:
                                    st.session_state[f"_yo_prev_{tid}"] = seg_to_wav(prev_seg)
                            if st.session_state.get(f"_yo_prev_{tid}"):
                                st.audio(st.session_state[f"_yo_prev_{tid}"], format="audio/wav")

                st.markdown("<hr><span class='sl'>4️⃣ Adım: Yayın Akışı (Cue Sheet) & Tam MP3 Çıktısı</span>", unsafe_allow_html=True)
                cue_lines, cur_sec_t = [], 0
                for ci, trk in enumerate(tracks):
                    st_hhmm = add_time(g_start_time, cur_sec_t)
                    has_a = bool(trk.get("anons_bytes") or trk.get("anons_file") or trk.get("anons_arc_id"))
                    has_j = bool(trk.get("jingle_bytes") or trk.get("jingle_file"))
                    a_info = trk["anons_pos"].split("(")[0].strip() if has_a else "Anons Yok"
                    if trk.get("end_anons_enabled"): a_info += " + Ek Son"
                    j_info = f"🎺 {trk.get('jingle_pos','')}" if has_j else "—"
                    st.markdown(f"<div class='tl-block'><span class='tl-time'>{st_hhmm}</span><span class='tl-type ttype-song'>#{ci+1:02d}</span><span class='tl-lbl'><b>{trk['artist']} — {trk['title']}</b> · {a_info} · {j_info} · 📉 {trk['duck_db']:.0f}dB</span><span class='tl-dur'>{fmt_dur(trk['dur'])}</span></div>", unsafe_allow_html=True)
                    cue_lines.append(f"{st_hhmm} | #{ci+1:02d} | {trk['artist']} - {trk['title']} ({fmt_dur(trk['dur'])}) | {a_info} | {j_info} | Duck: {trk['duck_db']:.0f}dB")
                    cur_sec_t += int(trk["dur"])

                oc1, oc2, oc3, oc4 = st.columns([1.8, 1, 1, 1])
                with oc1: yo_out_name = st.text_input("Yayın Dosya Adı", value=f"ImajFM_Yayin_{datetime.datetime.now().strftime('%d%m_%H%M')}", key="yo_out_name")
                with oc2: yo_out_fmt = st.selectbox("Çıktı Formatı", ["mp3", "wav"], key="yo_out_fmt")
                with oc3: yo_mp3_br = st.selectbox("MP3 Kalitesi", ["128k", "192k", "256k", "320k"], index=1, key="yo_mp3_br", disabled=(yo_out_fmt != "mp3"))
                with oc4:
                    if st.button("🗑️ Listeyi Temizle", use_container_width=True, key="yo_clr_all"):
                        st.session_state._yo_tracks, st.session_state._last_yo = [], None
                        st.rerun()

                if st.button(f"🚀 TAM YAYINI OLUŞTUR ({yo_out_fmt.upper()})", type="primary", use_container_width=True, key="yo_render_master"):
                    with st.status("🎙️ Tam yayın kurgulanıyor ve miksleniyor…", expanded=True) as yo_st:
                        master = AudioSegment.silent(300, frame_rate=44100).set_channels(2).set_sample_width(2)
                        if open_jingle != "Yok":
                            oj_p = os.path.join(DIRS["jingles"], open_jingle)
                            if os.path.exists(oj_p):
                                master = safe_append(master, norm_seg(unify_seg(AudioSegment.from_file(oj_p)), -14.0), 400)
                        for idx_y, trk in enumerate(tracks):
                            st.write(f"🎵 [{idx_y+1}/{len(tracks)}] {trk['artist']} — {trk['title']}")
                            t_seg, t_notes = build_track_audio(trk, g_cf)
                            if t_seg is None:
                                continue
                            if t_notes: st.write(f"   ↳ {' · '.join(t_notes)}")
                            master = safe_append(master, t_seg, g_cf)
                            if auto_j_every > 0 and auto_j_file != "Yok" and (idx_y + 1) % auto_j_every == 0 and idx_y < len(tracks) - 1:
                                aj_p = os.path.join(DIRS["jingles"], auto_j_file)
                                if os.path.exists(aj_p):
                                    master = safe_append(master, norm_seg(unify_seg(AudioSegment.from_file(aj_p)), -14.0), min(500, g_cf))
                            if g_gap > 0 and idx_y < len(tracks) - 1:
                                master += AudioSegment.silent(g_gap, frame_rate=44100).set_channels(2).set_sample_width(2)
                        if close_jingle != "Yok":
                            cj_p = os.path.join(DIRS["jingles"], close_jingle)
                            if os.path.exists(cj_p):
                                master = safe_append(master, norm_seg(unify_seg(AudioSegment.from_file(cj_p)), -14.0), 400)
                        if g_comp and len(master) > 500:
                            try:
                                master = pydub_fx.compress_dynamic_range(master, threshold=-18.0, ratio=2.8, attack=5.0, release=80.0)
                            except Exception:
                                pass
                        if g_norm:
                            master = norm_seg(master, -14.0)
                        out_bytes, real_ext = export_audio_bytes(master, yo_out_fmt, yo_mp3_br, yo_out_name)
                        with open(os.path.join(DIRS["output"], f"{sfn(yo_out_name)}.{real_ext}"), "wb") as f_out:
                            f_out.write(out_bytes)
                        yo_st.update(label=f"✅ Tam Yayın Hazır ({real_ext.upper()})!", state="complete")
                        st.session_state._last_yo = {"data": out_bytes, "ext": real_ext, "dur": len(master)/1000.0, "name": yo_out_name, "cnt": len(tracks), "size_mb": len(out_bytes)/(1024*1024)}
                        st.session_state._last_yo_cue = f"İMAJ FM YAYIN AKIŞI ({yo_out_name})\n" + "=" * 60 + "\n" + "\n".join(cue_lines)
                        st.balloons()

                if st.session_state._last_yo:
                    lyo = st.session_state._last_yo
                    mime_out = "audio/mpeg" if lyo["ext"] == "mp3" else "audio/wav"
                    mt_yo = audio_metrics(lyo["data"])
                    st.markdown(f"<div class='card g'>✅ <b>{lyo['name']}.{lyo['ext']}</b> · {fmt_dur(lyo['dur'])} · {lyo['cnt']} şarkı · {lyo['size_mb']:.2f} MB · Seviye: {mt_yo['dbfs']} ({mt_yo['clip']})</div>", unsafe_allow_html=True)
                    st.audio(lyo["data"], format=mime_out)
                    dc1, dc2 = st.columns([2, 1])
                    with dc1:
                        st.download_button(f"📦 Tam Yayını İndir (.{lyo['ext'].upper()})", lyo["data"], f"{sfn(lyo['name'])}.{lyo['ext']}", mime_out, use_container_width=True, key="dl_yo")
                    with dc2:
                        if st.session_state._last_yo_cue:
                            st.download_button("📄 Cue Sheet (.TXT)", st.session_state._last_yo_cue, f"{sfn(lyo['name'])}_cuesheet.txt", "text/plain", use_container_width=True, key="dl_yo_cue")

        with yo2:
            st.markdown("<div class='card b'>Delay Reji anonsları + Kütüphane şarkıları → Zincir yayın</div>", unsafe_allow_html=True)
            pl_songs_ch, fon_ch_list, rj_pl = list_audio(DIRS["playlist"]), list_audio(DIRS["fon"]), st.session_state._playlist
            if pl_songs_ch and fon_ch_list and rj_pl:
                ch_fon = st.selectbox("Fon", fon_ch_list, key="ch_fon")
                ch_cf = st.slider("Crossfade", 0, 2000, 1000, key="ch_cf")
                ch_fmt = st.selectbox("Format", ["mp3", "wav"], key="ch_fmt")
                ch_name = st.text_input("Yayın Adı", value=f"Zincir_{datetime.datetime.now().strftime('%H%M')}", key="ch_name")
                if st.button("🔗 ZİNCİR YAYIN", type="primary", use_container_width=True, key="ch_btn"):
                    mch = AudioSegment.silent(500, frame_rate=44100).set_channels(2).set_sample_width(2)
                    fch = AudioSegment.from_file(os.path.join(DIRS["fon"], ch_fon))
                    for song in rj_pl:
                        aw_bas, aw_son, lf = song.get("anons_wav_bas"), song.get("anons_wav_son"), song.get("local_file")
                        pf = next((f for f in pl_songs_ch if song.get("title", "").lower() in f.lower()), None)
                        sp = lf if lf and os.path.exists(lf) else (os.path.join(DIRS["playlist"], pf) if pf else None)
                        blk = AudioSegment.empty()
                        if aw_bas: blk = safe_append(blk, mix_fon_voice(fch, AudioSegment.from_file(io.BytesIO(aw_bas))), ch_cf)
                        if sp and os.path.exists(sp): blk = safe_append(blk, norm_seg(unify_seg(AudioSegment.from_file(sp)), -14.0), ch_cf)
                        if aw_son: blk = safe_append(blk, mix_fon_voice(fch, AudioSegment.from_file(io.BytesIO(aw_son))), ch_cf)
                        if len(blk) > 0: mch = safe_append(mch, blk, ch_cf)
                    ch_bytes, ch_ext = export_audio_bytes(norm_seg(mch, -14.0), ch_fmt, "192k", ch_name)
                    st.session_state._last_ch = {"data": ch_bytes, "ext": ch_ext, "dur": len(mch)/1000.0, "name": ch_name}
                if st.session_state._last_ch:
                    lch = st.session_state._last_ch
                    mc2 = "audio/mpeg" if lch["ext"] == "mp3" else "audio/wav"
                    st.audio(lch["data"], format=mc2)
                    st.download_button(f"📦 İndir (.{lch['ext'].upper()})", lch["data"], f"{sfn(lch['name'])}.{lch['ext']}", mc2, key="dl_ch")
            else:
                st.info("Delay Reji playlist'i, şarkılar ve fon müziği gerekli.")

        with yo3:
            cnt1, cnt2 = st.tabs(["📂 Arşivden", "📤 Dosya Yükle"])
            with cnt1:
                arc_cnt = [e for e in st.session_state._archive if e.get("wav")]
                if arc_cnt:
                    opts_cnt = [f"{i+1}. {e['ts_s']} | {e['voice']} | {e['prev'][:30]}" for i, e in enumerate(arc_cnt)]
                    sel_cnt = st.multiselect("Sesler", opts_cnt, key="sel_cnt")
                    if sel_cnt and st.button("🔗 Birleştir", key="cnt_arc"):
                        segs = [AudioSegment.from_file(io.BytesIO(arc_cnt[opts_cnt.index(s)]["wav"])) for s in sel_cnt]
                        rc = segs[0]
                        for sc3 in segs[1:]: rc = safe_append(rc, sc3, 200)
                        st.session_state._last_cnt_arc = {"wav": seg_to_wav(norm_seg(rc)), "n": len(segs)}
                    if st.session_state._last_cnt_arc:
                        st.audio(st.session_state._last_cnt_arc["wav"], format="audio/wav")
                        st.download_button("📦 WAV", st.session_state._last_cnt_arc["wav"], "birlesik.wav", "audio/wav", key="dl_cnt_arc")
                else:
                    st.info("Arşiv boş.")
            with cnt2:
                cnt_ups = st.file_uploader("Ses Dosyaları", type=["wav", "mp3", "ogg", "flac"], accept_multiple_files=True, key="cnt_up2")
                if cnt_ups and st.button("🔗 MP3 Olarak Birleştir", key="cnt_up_btn"):
                    su = [AudioSegment.from_file(io.BytesIO(uf.getvalue())) for uf in cnt_ups]
                    ru = unify_seg(su[0])
                    for s in su[1:]: ru = safe_append(ru, s, 300)
                    udata, uext = export_audio_bytes(norm_seg(ru), "mp3", "192k", "Birlesik_Yayin")
                    st.session_state._last_cnt_up = {"data": udata, "ext": uext}
                if st.session_state._last_cnt_up:
                    lcu = st.session_state._last_cnt_up
                    st.audio(lcu["data"], format="audio/mpeg" if lcu["ext"] == "mp3" else "audio/wav")
                    st.download_button("📦 İndir", lcu["data"], f"birlesik.{lcu['ext']}", key="dl_cnt_up")

# ════════════════ T9 — SES EFEKTLERİ & SİNYAL ÜRETİCİ ════════════
with t9:
    st.markdown("<div class='rjhdr'><h2>🎚️ Ses Efektleri Galerisi & Sinyal Üretici</h2><p>Efekt presetleri · Özel preset kaydetme · Saat başı / Bip jingle ton üreteci</p></div>", unsafe_allow_html=True)
    if not PYDUB_OK:
        st.error("⚠️ PyDub kurulu değil.")
    else:
        ef1, ef2, ef3, ef4 = st.tabs(["🎛️ Efekt Uygula", "💾 Preset Kaydet", "📂 Kayıtlı Presetler", "🔔 Sinyal / Bip Üretici"])
        with ef1:
            ef_src_mode = st.radio("Kaynak", ["📤 Dosya Yükle", "📂 Arşivden Seç"], horizontal=True, key="ef_src_mode")
            ef_wav = None
            if ef_src_mode == "📤 Dosya Yükle":
                ef_up = st.file_uploader("Ses dosyası", type=["wav", "mp3", "ogg"], key="ef_up")
                if ef_up: _, ef_wav = save_upload(ef_up, DIRS["uploads"], f"ef_{ef_up.name}")
            else:
                arc_ef = [e for e in st.session_state._archive if e.get("wav")]
                if arc_ef:
                    opts_ef = [f"{i+1}. {e['ts_s']} | {e['voice']} | {e['prev'][:30]}" for i, e in enumerate(arc_ef)]
                    ef_wav = arc_ef[opts_ef.index(st.selectbox("Arşiv Ses", opts_ef, key="sel_aef"))]["wav"]
            if ef_wav:
                all_presets = dict(EFFECT_PRESETS)
                for cp in load_effect_presets(): all_presets[f"⭐ {cp['name']}"] = cp["params"]
                ef_preset = st.selectbox("Efekt Preseti", list(all_presets.keys()), key="ef_preset")
                ef_eq = st.selectbox("EQ", EQ_OPTS, key="ef_eq")
                if st.button("🎛️ Efekti Uygula", type="primary", use_container_width=True, key="ef_apply"):
                    seg = norm_seg(apply_eq(apply_effect(AudioSegment.from_file(io.BytesIO(ef_wav)), all_presets[ef_preset]), ef_eq))
                    st.session_state._last_ef = {"wav": seg_to_wav(seg), "preset": ef_preset}
            if st.session_state._last_ef:
                lef = st.session_state._last_ef
                st.audio(lef["wav"], format="audio/wav")
                draw_wf(lef["wav"])
                st.download_button("💾 Efektli Sesi İndir", lef["wav"], f"efektli_{int(time.time())}.wav", "audio/wav", key="dl_ef")
        with ef2:
            preset_name = st.text_input("Preset Adı", placeholder="Örn: Gece Radyosu", key="preset_name")
            low = st.slider("High-Pass Kesim (Hz)", 20, 3000, 300)
            high = st.slider("Low-Pass Kesim (Hz)", 1000, 20000, 8000)
            gain = st.slider("Gain (dB)", -12, 12, 0)
            noise = st.slider("Vinyl Gürültü", 0.0, 0.1, 0.0, 0.002)
            if st.button("💾 Preset Kaydet", key="save_preset") and preset_name.strip():
                if save_effect_preset(preset_name, {"low": low, "high": high, "gain": gain, "noise": noise}):
                    st.success(f"✅ '{preset_name}' kaydedildi!")
        with ef3:
            for p in load_effect_presets():
                with st.expander(f"🎚️ {p['name']}"):
                    st.json(p["params"])
                    if st.button("🗑️ Sil", key=f"del_preset_{p['name']}"):
                        fp_p = os.path.join(DIRS["effect_gallery"], f"{sfn(p['name'])}.json")
                        if os.path.exists(fp_p): os.remove(fp_p)
                        st.rerun()
        with ef4:
            sg1, sg2, sg3 = st.columns(3)
            with sg1:
                wave_type = st.selectbox("Dalga Formu", ["Sinüs (Sine)", "Kare (Square)", "Testere (Sawtooth)"], key="sig_wave")
                sig_freq = st.slider("Frekans (Hz)", 200, 3000, 1000, 50, key="sig_freq")
            with sg2:
                sig_dur = st.slider("Süre (ms)", 100, 3000, 400, 50, key="sig_dur")
                sig_cnt = st.slider("Tekrar Sayısı", 1, 6, 3, key="sig_cnt")
            with sg3:
                sig_gap = st.slider("Aralık (ms)", 100, 1500, 600, 50, key="sig_gap")
                sig_db = st.slider("Ses (dB)", -30, 0, -10, key="sig_db")
            if st.button("🔔 Sinyal Üret", type="primary", use_container_width=True, key="sig_gen_btn"):
                gen_cls = Sine if "Sinüs" in wave_type else (Square if "Kare" in wave_type else Sawtooth)
                tone = gen_cls(sig_freq).to_audio_segment(duration=sig_dur).apply_gain(sig_db).fade_in(15).fade_out(25)
                out_sig = tone
                for _ in range(sig_cnt - 1): out_sig = out_sig + AudioSegment.silent(sig_gap) + tone
                st.session_state._last_sig = {"wav": seg_to_wav(out_sig), "name": f"sinyal_{sig_freq}hz.wav"}
            if st.session_state._last_sig:
                lsig = st.session_state._last_sig
                st.audio(lsig["wav"], format="audio/wav")
                sc_a, sc_b = st.columns(2)
                with sc_a: st.download_button("💾 İndir", lsig["wav"], lsig["name"], "audio/wav", use_container_width=True, key="dl_sig")
                with sc_b:
                    if st.button("📥 Jingle Kütüphanesine Kaydet", use_container_width=True, key="save_sig_lib"):
                        with open(os.path.join(DIRS["jingles"], lsig["name"]), "wb") as fs_out: fs_out.write(lsig["wav"])
                        st.success("✅ Jingle klasörüne kaydedildi!")

# ════════════════ T10 — KÜTÜPHANE ════════════════════════════════
with t10:
    st.markdown("<span class='sl'>▶ Ses Kütüphanesi (ID3 Etiket Destekli)</span>", unsafe_allow_html=True)
    lib1, lib2, lib3, lib4 = st.tabs(["🎵 Şarkılar", "🎶 Fon Müzikleri", "🎺 Jinglelar", "🎭 Efektler"])
    def lib_panel(dir_p: str, tab, tk: str, info: str = ""):
        with tab:
            if info: st.markdown(f"<div class='card b'>{info}</div>", unsafe_allow_html=True)
            ups = st.file_uploader("Dosya Yükle", type=["mp3", "wav", "ogg", "flac", "m4a"], accept_multiple_files=True, key=f"lib_{tk}")
            if ups:
                cnt_l = 0
                for u in ups:
                    uid_l = f"lib_{tk}_{u.name}_{u.size}"
                    if uid_l in st.session_state._processed_uploads: continue
                    if save_upload(u, dir_p, u.name, convert_to_wav=False)[0]:
                        st.session_state._processed_uploads.add(uid_l)
                        cnt_l += 1
                if cnt_l > 0: st.rerun()
            files_l = list_audio(dir_p)
            st.markdown(f"<div style='font-size:.74rem;color:{CURRENT_THEME['muted']};margin:4px 0 8px;'>{len(files_l)} dosya · {fmt_dur(sum(dur_file(os.path.join(dir_p, f)) for f in files_l))} toplam</div>", unsafe_allow_html=True)
            for f in files_l:
                fp_l = os.path.join(dir_p, f)
                meta_l = read_id3_meta(fp_l)
                cc_l = st.columns([3, 1.3, .5])
                with cc_l[0]:
                    st.markdown(f'<div class="song-row"><span class="song-nm">🎵 {f[:36]} <span style="font-weight:400;opacity:.75;">({meta_l["artist"]})</span></span><span class="song-dur">{fmt_dur(dur_file(fp_l))} · {os.path.getsize(fp_l)//1024}KB</span></div>', unsafe_allow_html=True)
                with cc_l[1]: st.audio(fp_l)
                with cc_l[2]:
                    if st.button("🗑️", key=f"ldel_{tk}_{f}", use_container_width=True):
                        if os.path.exists(fp_l): os.remove(fp_l)
                        st.rerun()
    lib_panel(DIRS["playlist"], lib1, "songs")
    lib_panel(DIRS["fon"], lib2, "fon", "Anons arkası fon müzikleri.")
    lib_panel(DIRS["jingles"], lib3, "jingles", "İstasyon tanıtım & geçiş jingleları.")
    lib_panel(DIRS["effects"], lib4, "effects", "Saat başı, alkış ve geçiş efektleri.")

# ════════════════ T11 — ARŞİV ════════════════════════════════════
with t11:
    arc = st.session_state._archive
    if not arc:
        st.markdown("<div class='card b'>📂 Arşiv henüz boş. TTS üretilen sesler otomatik buraya eklenir.</div>", unsafe_allow_html=True)
    else:
        ah1, ah2, ah3 = st.columns([2, 1, 1])
        with ah1: st.markdown(f"<span class='sl'>▶ {len(arc)} Kayıt</span>", unsafe_allow_html=True)
        with ah2:
            if st.button("📦 ZIP Hazırla", use_container_width=True, key="arc_zip"):
                st.session_state._last_arc_zip = make_zip([(f"{e['voice']}_{e['id']}.wav", e["wav"]) for e in arc])
        with ah3:
            if st.button("🗑️ Tümünü Sil", use_container_width=True, key="arc_clr"):
                st.session_state._archive, st.session_state._last_arc_zip = [], None
                st.rerun()
        if st.session_state._last_arc_zip:
            st.download_button("💾 Arşiv ZIP İndir", st.session_state._last_arc_zip, "imajfm_arsiv.zip", "application/zip", use_container_width=True, key="arc_zip_dl")
        arc_srch = st.text_input("Ara", "", placeholder="🔍 Ses, metin, model ara…", label_visibility="collapsed", key="arc_srch")
        farce = [h for h in arc if not arc_srch.strip() or arc_srch.lower() in h["voice"].lower() or arc_srch.lower() in h["text"].lower()]
        gcols = st.columns(3)
        for gi, h in enumerate(farce):
            with gcols[gi % 3]:
                st.markdown(f"<div class='fav-card'><div class='fav-name'>{VOICES.get(h['voice'].split('+')[0],('🎙️',''))[0]} {h['voice']} · {h['ts_s']}</div><div class='fav-prev'>{h['dur']}s · {h['mode'].upper()} · {h['prev']}</div></div>", unsafe_allow_html=True)
                st.audio(h["wav"], format="audio/wav")
                dc1, dc2 = st.columns(2)
                with dc1: st.download_button("💾 WAV", h["wav"], f"imajfm_{h['id']}.wav", "audio/wav", use_container_width=True, key=f"adl_{h['id']}")
                with dc2:
                    if st.button("⭐ Favori", key=f"afav_{h['id']}", use_container_width=True):
                        st.session_state._favorites.append({"id": h["id"], "name": f"{h['voice']} {h['ts_s']}", "text": h["text"], "voice": h["voice"].split("+")[0], "model": h["model"], "lang": h["lang"]})
                        st.success("⭐ Eklendi!")

# ════════════════ T12 — PODCAST RSS ══════════════════════════════
with t12:
    st.markdown("<div class='rjhdr'><h2>📰 Podcast RSS Üretici</h2><p>Arşivdeki seslerden podcast feed oluştur · XML & Bölüm ZIP indir</p></div>", unsafe_allow_html=True)
    arc_pod = [e for e in st.session_state._archive if e.get("wav")]
    if not arc_pod:
        st.markdown("<div class='card a'>Arşivde ses yok. Önce ses üretin.</div>", unsafe_allow_html=True)
    else:
        pc_a, pc_b = st.columns(2)
        with pc_a:
            pod_title = st.text_input("Podcast Başlığı", value="İmaj FM Podcast", key="pod_title")
            pod_author = st.text_input("Yayıncı", value="İmaj FM", key="pod_author")
        with pc_b:
            pod_base = st.text_input("Sunucu Base URL", value="https://imajfm.com/podcast/", key="pod_base")
        pod_desc = st.text_area("Açıklama", value="İmaj FM radyo yayınlarından podcast bölümleri.", key="pod_desc")
        opts_pod = [f"{i+1}. {e['ts_s']} | {e['voice']} | {e['prev'][:30]}" for i, e in enumerate(arc_pod)]
        selected_ep = st.multiselect("Bölüm Seç", opts_pod, key="pod_sel")
        if st.button("📄 RSS Feed Oluştur", type="primary", use_container_width=True, key="pod_btn") and selected_ep:
            episodes, zip_items = [], []
            for sel in selected_ep:
                e = arc_pod[opts_pod.index(sel)]
                fn_ep = f"episode_{e['id']}.wav"
                episodes.append({"title": f"{e['voice']} - {e['ts_s']}", "description": e["text"][:200], "url": fn_ep, "length": str(len(e["wav"])), "guid": e["id"]})
                zip_items.append((fn_ep, e["wav"]))
            rss_xml = generate_podcast_rss(pod_title, pod_desc, pod_author, pod_base, episodes, os.path.join(DIRS["podcast"], f"podcast_{int(time.time())}.xml"))
            if rss_xml:
                st.session_state._last_rss = {"xml": rss_xml, "zip": make_zip(zip_items)}
        if st.session_state._last_rss:
            lrss = st.session_state._last_rss
            rc1, rc2 = st.columns(2)
            with rc1: st.download_button("📥 RSS XML İndir", lrss["xml"], "podcast.xml", "application/xml", use_container_width=True, key="dl_rss")
            with rc2: st.download_button("📦 Bölümleri ZIP İndir", lrss["zip"], "podcast_episodes.zip", "application/zip", use_container_width=True, key="dl_pod_zip")

# ════════════════ T13 — YAYIN TAKVİMİ ══════════════════════════
with t13:
    st.markdown("<div class='rjhdr'><h2>📅 Yayın Takvimi</h2><p>Gelecek yayınları planla · Otomasyona veya Delay Reji'ye aktar</p></div>", unsafe_allow_html=True)
    sc1, sc2 = st.tabs(["📋 Yeni Plan", "📂 Planlanan Yayınlar"])
    with sc1:
        sch_name = st.text_input("Yayın Adı", placeholder="Örn: Sabah Kuşağı", key="sch_name")
        sd1, sd2 = st.columns(2)
        with sd1: sch_date = st.date_input("Tarih", key="sch_date")
        with sd2: sch_time = st.time_input("Saat", key="sch_time")
        sch_songs = st.multiselect("Şarkılar", list_audio(DIRS["playlist"]), key="sch_songs")
        sch_notes = st.text_area("Notlar", placeholder="Özel notlar…", key="sch_notes")
        if st.button("📋 Yayın Planla", type="primary", use_container_width=True, key="sch_btn") and sch_name.strip() and sch_songs:
            if schedule_broadcast(sch_name.strip(), str(sch_date), sch_time.strftime("%H:%M"), sch_songs, sch_notes):
                st.success("✅ Yayın planlandı!")
                st.rerun()
    with sc2:
        schedules = get_scheduled_broadcasts()
        if not schedules:
            st.info("Planlanmış yayın yok.")
        else:
            for idx_s, s in enumerate(schedules):
                st_badge = "✅ Tamamlandı" if s.get("status") == "completed" else "⏳ Bekliyor"
                with st.expander(f"📅 {s.get('name')} — {s.get('date')} {s.get('time')} [{st_badge}]"):
                    st.write("Şarkılar:", ", ".join(s.get("songs", [])))
                    b1, b2, b3 = st.columns(3)
                    with b1:
                        if st.button("🚀 Otomasyona Aktar", key=f"sch_yo_{idx_s}", use_container_width=True):
                            st.session_state._yo_tracks = [make_yo_track(os.path.join(DIRS["playlist"], fn_s)) for fn_s in s.get("songs", []) if os.path.exists(os.path.join(DIRS["playlist"], fn_s))]
                            st.success("✅ Yayın Otomasyonu sekmesine aktarıldı!")
                    with b2:
                        if st.button("🔄 Durum Değiştir", key=f"sch_tog_{idx_s}", use_container_width=True):
                            fp_sch = os.path.join(DIRS["schedules"], s["_file"])
                            s_copy = {k: v for k, v in s.items() if k != "_file"}
                            s_copy["status"] = "completed" if s.get("status") != "completed" else "pending"
                            with open(fp_sch, "w", encoding="utf-8") as fw_s: json.dump(s_copy, fw_s, ensure_ascii=False, indent=2)
                            st.rerun()
                    with b3:
                        if st.button("🗑️ Sil", key=f"sch_del_{idx_s}", use_container_width=True):
                            fp_del = os.path.join(DIRS["schedules"], s["_file"])
                            if os.path.exists(fp_del): os.remove(fp_del)
                            st.rerun()

# ════════════════ T14 — SES KLONLAMA (RVC HAZIRLIK) ═════════════
with t14:
    st.markdown("<div class='rjhdr'><h2>🗣️ Ses Klonlama (RVC Hazırlık)</h2><p>RVC eğitimi için 44.1kHz Mono WAV segment veri seti hazırla · Normalize et · ZIP indir</p></div>", unsafe_allow_html=True)
    if not PYDUB_OK:
        st.error("⚠️ PyDub kurulu değil.")
    else:
        rvc1, rvc2 = st.tabs(["📤 Veri Seti Hazırla", "📂 Mevcut Klonlar"])
        with rvc1:
            rvc_ups = st.file_uploader("Ses dosyaları (MP3/WAV/OGG)", type=["mp3", "wav", "ogg", "flac"], accept_multiple_files=True, key="rvc_ups")
            rc1, rc2 = st.columns(2)
            with rc1: clone_name = st.text_input("Model Adı", placeholder="Örn: Kenan_Ses", key="clone_name")
            with rc2: rvc_chunk = st.slider("Segment Uzunluğu (sn)", 5, 30, 15, key="rvc_chunk")
            if rvc_ups and clone_name.strip() and st.button("📤 Kaydet ve RVC Veri Seti Hazırla", type="primary", use_container_width=True, key="rvc_save"):
                clone_dir = os.path.join(DIRS["voice_clones"], sfn(clone_name))
                saved_paths = [dp for uf in rvc_ups for dp, _ in [save_upload(uf, clone_dir, uf.name)] if dp]
                rvc_dir = os.path.join(DIRS["rvc_workspace"], sfn(clone_name))
                seg_cnt = prepare_rvc_dataset(saved_paths, rvc_dir, chunk_sec=rvc_chunk)
                if seg_cnt > 0:
                    zip_items = []
                    for f in sorted(os.listdir(rvc_dir)):
                        fp = os.path.join(rvc_dir, f)
                        if os.path.isfile(fp):
                            with open(fp, "rb") as fh: zip_items.append((f, fh.read()))
                    st.session_state._last_rvc_zip = {"zip": make_zip(zip_items), "name": sfn(clone_name), "cnt": seg_cnt, "dir": rvc_dir}
            if st.session_state._last_rvc_zip:
                lrvc = st.session_state._last_rvc_zip
                st.success(f"✅ {lrvc['cnt']} adet 44.1kHz Mono WAV segmenti hazır!")
                st.download_button("📦 RVC Veri Seti ZIP İndir", lrvc["zip"], f"{lrvc['name']}_rvc_dataset.zip", "application/zip", use_container_width=True, key="dl_rvc_zip")
        with rvc2:
            for c in [d for d in os.listdir(DIRS["voice_clones"]) if os.path.isdir(os.path.join(DIRS["voice_clones"], d))]:
                c_dir, r_dir = os.path.join(DIRS["voice_clones"], c), os.path.join(DIRS["rvc_workspace"], c)
                with st.expander(f"🗣️ {c} ({len(list_audio(c_dir))} ham · {len(list_audio(r_dir)) if os.path.isdir(r_dir) else 0} segment)"):
                    if st.button("🗑️ Sil", key=f"del_clone_{c}"):
                        shutil.rmtree(c_dir, ignore_errors=True)
                        shutil.rmtree(r_dir, ignore_errors=True)
                        st.rerun()

# ════════════════ T15 — DÖNÜŞTÜRÜCÜ & NORMALİZASYON ══════════════
with t15:
    st.markdown("<div class='rjhdr'><h2>🔄 Toplu Ses Dönüştürücü & Normalizasyon</h2><p>Format dönüştürme (MP3/WAV/OGG/FLAC) · Ses Normalizasyon (dBFS) · Sessizlik Kırpma · ZIP</p></div>", unsafe_allow_html=True)
    if not PYDUB_OK:
        st.error("⚠️ PyDub ve FFmpeg kurulu olmalıdır.")
    else:
        dn1, dn2 = st.tabs(["🔄 Toplu Format Dönüştürücü", "📏 Ses Normalizasyon & Temizleme"])
        with dn1:
            conv_ups = st.file_uploader("Dönüştürülecek Dosyalar", type=["mp3", "wav", "ogg", "flac", "m4a", "aac"], accept_multiple_files=True, key="conv_ups")
            cv1, cv2, cv3, cv4 = st.columns(4)
            with cv1: tgt_fmt = st.selectbox("Hedef Format", ["mp3", "wav", "ogg", "flac"], key="tgt_fmt")
            with cv2: tgt_br = st.selectbox("Bitrate", ["128k", "192k", "256k", "320k"], index=1, key="tgt_br")
            with cv3: tgt_sr = st.selectbox("Örnekleme (Hz)", [22050, 24000, 44100, 48000], index=2, key="tgt_sr")
            with cv4: tgt_ch = st.selectbox("Kanal", ["Orijinal", "Mono (1)", "Stereo (2)"], key="tgt_ch")
            if conv_ups and st.button("🔄 Toplu Dönüştür", type="primary", use_container_width=True, key="conv_btn"):
                res_conv = []
                for uf in conv_ups:
                    try:
                        seg = AudioSegment.from_file(io.BytesIO(uf.getvalue())).set_frame_rate(int(tgt_sr))
                        if tgt_ch == "Mono (1)": seg = seg.set_channels(1)
                        elif tgt_ch == "Stereo (2)": seg = seg.set_channels(2)
                        ob = io.BytesIO()
                        kw = {"format": tgt_fmt}
                        if tgt_fmt in ("mp3", "ogg"): kw["bitrate"] = tgt_br
                        seg.export(ob, **kw)
                        res_conv.append((f"{sfn(os.path.splitext(uf.name)[0])}.{tgt_fmt}", ob.getvalue()))
                    except Exception as e:
                        st.warning(f"{uf.name}: {e}")
                if res_conv: st.session_state._last_conv_zip = {"zip": make_zip(res_conv), "cnt": len(res_conv), "fmt": tgt_fmt}
            if st.session_state._last_conv_zip:
                lcz = st.session_state._last_conv_zip
                st.download_button(f"📦 {lcz['cnt']} Dosyayı (.{lcz['fmt']}) ZIP İndir", lcz["zip"], f"donusturulen_{lcz['fmt']}.zip", "application/zip", use_container_width=True, key="dl_conv_zip")
        with dn2:
            norm_ups = st.file_uploader("Normalize Edilecek Dosyalar", type=["mp3", "wav", "ogg", "flac"], accept_multiple_files=True, key="norm_ups")
            nm1, nm2, nm3 = st.columns(3)
            with nm1: tgt_dbfs = st.slider("Hedef Seviye (dBFS)", -24.0, -3.0, -14.0, 0.5, key="tgt_dbfs")
            with nm2: do_trim = st.checkbox("Baş/Son Sessizlik Kırp", value=True, key="do_trim")
            with nm3: trim_thresh = st.slider("Sessizlik Eşiği (dBFS)", -60, -25, -45, key="trim_thresh")
            if norm_ups and st.button("📏 Normalize Et & Temizle", type="primary", use_container_width=True, key="norm_btn"):
                res_norm = []
                for uf in norm_ups:
                    try:
                        seg = AudioSegment.from_file(io.BytesIO(uf.getvalue()))
                        if do_trim and len(seg) > 200:
                            lead = detect_leading_silence(seg, silence_threshold=trim_thresh, chunk_size=10)
                            trail = detect_leading_silence(seg.reverse(), silence_threshold=trim_thresh, chunk_size=10)
                            if lead + trail < len(seg) - 100: seg = seg[lead:len(seg) - trail]
                        seg = norm_seg(pydub_fx.normalize(seg), tgt_dbfs)
                        res_norm.append((f"{sfn(os.path.splitext(uf.name)[0])}_norm.wav", seg_to_wav(seg)))
                    except Exception as e:
                        st.warning(f"{uf.name}: {e}")
                if res_norm: st.session_state._last_norm_zip = {"zip": make_zip(res_norm), "cnt": len(res_norm)}
            if st.session_state._last_norm_zip:
                lnz = st.session_state._last_norm_zip
                st.download_button(f"📦 {lnz['cnt']} Normalize Dosyayı ZIP İndir", lnz["zip"], "normalize_sesler.zip", "application/zip", use_container_width=True, key="dl_norm_zip")

# ════════════════ FOOTER ═════════════════════════════════════════
st.markdown("<hr>", unsafe_allow_html=True)
tk_f, tr_f = pool_stats()
st.markdown(
    f"<div style='text-align:center;color:{CURRENT_THEME['muted']};font-size:.72rem;letter-spacing:.06em;padding:6px 0 12px;'>"
    f"<b>İMAJ FM TTS STÜDYO v7.5</b> · {'✅ Gemini' if GEMINI_OK else '❌ Gemini'} · "
    f"{'✅ PyDub' if PYDUB_OK else '❌ PyDub'} · {'✅ NumPy' if NP_OK else '❌ NumPy'} · "
    f"{'✅ Mutagen' if MUTAGEN_OK else '❌ Mutagen'} · API: {tk_f}/10 ({tr_f} kalan) · 2026</div>",
    unsafe_allow_html=True,
)
