bash

cat > /mnt/user-data/outputs/app_v6.py << 'ENDOFFILE'
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  İMAJ FM · TTS STÜDYO  v6.0 — TAM ENTEGRE YAYIN SİSTEMİ                   ║
║  Gemini TTS API · Yayın Otomasyonu · Fon+Anons Mikseri                      ║
║  Delay Reji · Playlist Yönetimi · Toplu TTS · A/B Test                      ║
║  Ses Birleştirme · Dosya Upload · ZIP İndirme · Arşiv                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import wave, io, zipfile, re, time, datetime, hashlib, json, os, shutil

from google import genai
from google.genai import types

try:
    from pydub import AudioSegment, effects as pydub_fx
    PYDUB_OK = True
except ImportError:
    PYDUB_OK = False

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

# ─────────────────────────────────────────────────────────────────
# DİZİNLER
# ─────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.abspath("imajfm_data")
PLAYLIST_DIR = os.path.join(BASE_DIR, "playlist")
FON_DIR      = os.path.join(BASE_DIR, "fon")
JINGLE_DIR   = os.path.join(BASE_DIR, "jingles")
EFFECT_DIR   = os.path.join(BASE_DIR, "effects")
OUT_DIR      = os.path.join(BASE_DIR, "output")
ARCHIVE_DIR  = os.path.join(BASE_DIR, "archive")
UPLOAD_DIR   = os.path.join(BASE_DIR, "uploads")
ANONS_DIR    = os.path.join(BASE_DIR, "anons")

for _d in [PLAYLIST_DIR, FON_DIR, JINGLE_DIR, EFFECT_DIR,
           OUT_DIR, ARCHIVE_DIR, UPLOAD_DIR, ANONS_DIR]:
    os.makedirs(_d, exist_ok=True)

# ─────────────────────────────────────────────────────────────────
# SAYFA AYARI
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="İmaj FM · TTS Stüdyo v6",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────
# CSS — KARANLIK TEMA
# ─────────────────────────────────────────────────────────────────
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

.ldot{display:inline-block;width:7px;height:7px;background:#ff3a3a;
    border-radius:50%;margin-right:7px;animation:blink 1.2s ease-in-out infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.12}}

.sl{font-family:'Syne',sans-serif;font-size:.62rem;font-weight:700;
    letter-spacing:.18em;color:#e05252;text-transform:uppercase;
    margin:16px 0 5px;display:block;}
.sl2{font-family:'Syne',sans-serif;font-size:.57rem;font-weight:700;
    letter-spacing:.15em;color:#3a7bd5;text-transform:uppercase;
    margin:10px 0 4px;display:block;}
.sl3{font-family:'Syne',sans-serif;font-size:.57rem;font-weight:700;
    letter-spacing:.15em;color:#10b981;text-transform:uppercase;
    margin:10px 0 4px;display:block;}

.mbox{background:#0b0f1a;border:1px solid #131c2e;border-radius:10px;
    padding:12px;text-align:center;}
.mbox .v{font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;color:#e05252;}
.mbox .l{font-size:.6rem;letter-spacing:.12em;color:#2e3f55;text-transform:uppercase;margin-top:2px;}
.mbox.g .v{color:#22c55e;} .mbox.b .v{color:#3b82f6;}
.mbox.a .v{color:#f59e0b;} .mbox.p .v{color:#a78bfa;} .mbox.t .v{color:#10b981;}

.card{background:#0b0f1a;border:1px solid #131c2e;border-radius:9px;
    padding:11px 14px;margin:7px 0;font-size:.82rem;color:#6b7a8d;}
.card.b{border-left:3px solid #3a7bd5;}
.card.g{border-left:3px solid #22c55e;background:#021409;color:#4ade80;}
.card.a{border-left:3px solid #f59e0b;background:#100d00;color:#fbbf24;}
.card.r{border-left:3px solid #ef4444;background:#110404;color:#f87171;}
.card.p{border-left:3px solid #a78bfa;background:#090614;color:#c4b5fd;}
.card.t{border-left:3px solid #10b981;background:#011209;color:#34d399;}

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

[data-testid="stTextArea"] textarea{
    background:#090d18 !important;border:1px solid #131c2e !important;
    border-radius:10px !important;color:#dde2ee !important;
    font-family:'Inter',sans-serif !important;font-size:.91rem !important;
    line-height:1.65 !important;}
[data-testid="stSelectbox"]>div>div,
[data-testid="stSelectbox"]>div>div>div{
    background:#090d18 !important;border:1px solid #131c2e !important;
    border-radius:8px !important;color:#dde2ee !important;}
[data-testid="stTextInput"]>div>div>input{
    background:#090d18 !important;border:1px solid #131c2e !important;
    border-radius:8px !important;color:#dde2ee !important;}
[data-testid="stAudio"]{background:#0b0f1a;border-radius:10px;padding:8px;}
[data-testid="stFileUploader"]{
    background:#090d18 !important;border:2px dashed #1a2436 !important;
    border-radius:10px !important;}

[data-testid="stSidebar"] details{
    background:#0b0f1a !important;border:1px solid #131c2e !important;
    border-radius:9px !important;margin-bottom:5px !important;}
[data-testid="stSidebar"] details summary{
    font-family:'Syne',sans-serif !important;font-size:.75rem !important;
    font-weight:700 !important;color:#b0bac9 !important;padding:8px 11px !important;}
[data-testid="stSidebar"] details summary:hover{color:#e05252 !important;}
[data-testid="stSidebar"] details[open] summary{color:#e05252 !important;}

[data-testid="stTabs"] [data-baseweb="tab-list"]{
    background:transparent !important;border-bottom:1px solid #131c2e;gap:0;}
[data-testid="stTabs"] [data-baseweb="tab"]{
    background:transparent !important;color:#2e3f55 !important;
    font-family:'Syne',sans-serif !important;font-weight:700 !important;
    font-size:.72rem !important;letter-spacing:.07em !important;
    padding:9px 13px !important;border-bottom:2px solid transparent !important;}
[data-testid="stTabs"] [aria-selected="true"]{
    color:#e05252 !important;border-bottom:2px solid #e05252 !important;}

.qbar{background:#101828;border-radius:4px;height:5px;margin:3px 0;overflow:hidden;}
.qbar-f{height:100%;border-radius:4px;}

.song-row{display:flex;align-items:center;gap:10px;
    background:#0b0f1a;border:1px solid #131c2e;border-radius:8px;
    padding:9px 13px;margin-bottom:6px;transition:border-color .15s;}
.song-row:hover{border-color:#3a7bd5;}
.song-nm{font-family:'Syne',sans-serif;font-size:.82rem;font-weight:700;color:#dde2ee;flex:1;}
.song-dur{font-family:'JetBrains Mono',monospace;font-size:.68rem;color:#2e3f55;}

.reji-header{background:linear-gradient(135deg,#071a0f 0%,#07090f 100%);
    border:1px solid #0d2e1a;border-radius:14px;padding:18px 22px;
    margin-bottom:16px;position:relative;overflow:hidden;}
.reji-header::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
    background:linear-gradient(90deg,#10b981,#34d399,#10b981);
    background-size:200%;animation:scan 4s linear infinite;}
.reji-header h2{font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:800;
    margin:0 0 3px;background:linear-gradient(90deg,#fff 30%,#34d399 100%);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.reji-header p{margin:0;color:#2e5040;font-size:.75rem;}

.timeline-block{background:#0b0f1a;border:1px solid #131c2e;border-radius:8px;
    padding:8px 12px;margin:3px 0;display:flex;align-items:center;gap:10px;}
.timeline-time{font-family:'JetBrains Mono',monospace;font-size:.72rem;color:#10b981;min-width:48px;}
.timeline-type{font-size:.62rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
    padding:2px 7px;border-radius:4px;min-width:60px;text-align:center;}
.ttype-song{background:#071a2e;color:#60a5fa;border:1px solid #1a3a5e;}
.ttype-anons{background:#1a0d00;color:#f59e0b;border:1px solid #5e3a00;}
.ttype-fon{background:#071a0f;color:#34d399;border:1px solid #0a3d1f;}
.ttype-jingle{background:#14071a;color:#c4b5fd;border:1px solid #3d1a5e;}
.timeline-label{font-size:.78rem;color:#6b7a8d;flex:1;}
.timeline-dur{font-family:'JetBrains Mono',monospace;font-size:.65rem;color:#2e3f55;}

.fav-card{background:#0b0f1a;border:1px solid #131c2e;border-radius:8px;
    padding:9px 12px;margin:5px 0;}
.fav-name{font-family:'Syne',sans-serif;font-size:.75rem;font-weight:700;color:#dde2ee;}
.fav-prev{font-size:.7rem;color:#3d4f68;margin-top:2px;
    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}

.ttbl{width:100%;border-collapse:collapse;font-size:.69rem;}
.ttbl th{color:#e05252;font-family:'Syne',sans-serif;font-size:.57rem;
    letter-spacing:.1em;text-transform:uppercase;padding:4px 3px;
    border-bottom:1px solid #131c2e;text-align:left;}
.ttbl td{padding:4px 3px;color:#4a5a6e;border-bottom:1px solid #0d1420;vertical-align:top;}
.tc{color:#60a5fa;font-family:'JetBrains Mono',monospace;font-size:.73rem;}
.ten{color:#f59e0b;font-size:.65rem;}

.broadcast-live{background:#021409;border:2px solid #10b981;border-radius:12px;
    padding:14px 18px;margin:10px 0;position:relative;}
.broadcast-live::before{content:'● YAYIN PLANI';position:absolute;top:-9px;left:14px;
    background:#10b981;color:#000;font-family:'Syne',sans-serif;font-size:.58rem;
    font-weight:800;letter-spacing:.12em;padding:1px 8px;border-radius:4px;}
.now-playing{font-family:'Syne',sans-serif;font-size:1rem;font-weight:800;color:#34d399;}

.chip{display:inline-flex;align-items:center;padding:2px 8px;
    border-radius:20px;font-size:11px;font-weight:600;margin:2px;}
.chip-green{background:#071a0f;color:#34d399;border:1px solid #10b98140;}
.chip-blue{background:#071a2e;color:#60a5fa;border:1px solid #3b82f640;}
.chip-amber{background:#1a0d00;color:#fbbf24;border:1px solid #f59e0b40;}
.chip-purple{background:#0d071a;color:#c4b5fd;border:1px solid #a78bfa40;}
.chip-red{background:#110404;color:#f87171;border:1px solid #ef444440;}
.chip-gray{background:#0b0f1a;color:#6b7a8d;border:1px solid #131c2e;}
.chip-teal{background:#071a14;color:#34d399;border:1px solid #10b98140;}

hr{border-color:#101828 !important;margin:11px 0 !important;}
::-webkit-scrollbar{width:4px;height:4px;}
::-webkit-scrollbar-track{background:#07090f;}
::-webkit-scrollbar-thumb{background:#1a2436;border-radius:2px;}
</style>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════
# SABİTLER
# ═════════════════════════════════════════════════════════════════
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
    "gemini-3.1-flash-tts-preview":      "⚡ 3.1 Flash  (En Güncel)",
    "gemini-2.5-flash-tts":              "🚀 2.5 Flash  (Stabil)",
    "gemini-2.5-pro-tts":                "💎 2.5 Pro    (En Kaliteli)",
    "gemini-2.5-flash-lite-preview-tts": "💡 2.5 Lite   (Ekonomik)",
}

LANGUAGES = {
    "otomatik":"🌐 Oto","tr-TR":"🇹🇷 Türkçe","en-US":"🇺🇸 EN-US",
    "en-GB":"🇬🇧 EN-UK","de-DE":"🇩🇪 Almanca","fr-FR":"🇫🇷 Fransızca",
    "es-ES":"🇪🇸 İspanyolca","it-IT":"🇮🇹 İtalyanca",
    "ar-XA":"🇸🇦 Arapça","hi-IN":"🇮🇳 Hintçe",
}

STYLE_PRESETS = {
    "— Seçin —":"",
    "📻 Haber Sunucusu":   "Profesyonel haber sunucusu gibi net, otoriter ve güven verici bir tonla oku.",
    "🎉 Neşeli & Enerjik": "Çok neşeli ve coşkulu, müzik programı sunuyormuş gibi oku.",
    "🎭 Dramatik & Güçlü": "Dramatik ve etkileyici, büyük sahne duyurusu gibi oku.",
    "🌙 Sakin & Huzurlu":  "Sakin, huzurlu ve rahatlatıcı, gece kuşağı tonu ile oku.",
    "🚨 Acil & Hızlı":     "Acil haber tonu, hızlı ve yüksek enerjili sesle oku.",
    "☕ Sıcak & Samimi":   "Sıcak ve dostça, yakın arkadaşa anlatır gibi oku.",
    "📣 Reklam Sesi":      "Profesyonel reklam seslendirmesi, çekici ve ikna edici oku.",
    "📖 Hikaye Anlatıcısı":"Büyüleyici hikaye anlatıcısı gibi ritmik ve ifadeli oku.",
    "⚽ Spor Yorumcusu":   "Heyecanlı spor yorumcusu gibi yüksek tempo ile oku.",
}

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
        "[normal] Günün öne çıkan haberleriyle karşınızdayız.",
    "🎉 Yarışma":
        "[excitedly] BÜYÜK YARIŞMA BAŞLIYOR!\n"
        "[laughs] Hazır mısınız?\n"
        "[shouting] BU HAFTA kazanan sizin aranızdan çıkacak!\n"
        "[seriously] Hemen arayın... [excitedly] KAZANMA ŞANSI SIZIN!",
    "☀️ Öğle Bülteni":
        "[normal] İmaj FM Öğle Bülteni ile karşınızdayız.\n"
        "[seriously] Bugünün öne çıkan gelişmeleri...\n"
        "[normal] Haberlerden sonra müziğe devam.",
    "🎵 Şarkı Başı Anonsu":
        "[excitedly] Ve şimdi sizi muhteşem bir şarkıyla baş başa bırakıyoruz!\n"
        "[normal] İşte bu dakikanın en özel sesi...",
    "🎵 Şarkı Sonu Anonsu":
        "[normal] Dinlediğiniz şarkıydı... İmaj FM'de devam ediyoruz.\n"
        "[excitedly] Sıradaki sürpriz için kulaklarınız bizde kalsın!",
}

ETAGS = [
    ("🔥","Coşkulu",   "[excitedly] "),
    ("🤫","Fısıltı",   "[whispers] "),
    ("😄","Gülümseyen","[laughs] "),
    ("📰","Ciddi",     "[seriously] "),
    ("📢","Bağırma",   "[shouting] "),
    ("😮‍💨","Yorgun",   "[sighs] "),
    ("🎙️","Normal",   "[normal] "),
]

FON_TIPLERI = {
    "📻 Radyo Klasik":   "Standart radyo fade-out, anons, fade-in.",
    "🎵 Yumuşak Giriş":  "Müzik yavaşça yükseliyor, anons bitti, normale dönüyor.",
    "🎶 Hızlı Kesim":    "Müzik aniden kesiliyor, anons, geri geliyor.",
    "🌊 Dalgalı Geçiş":  "Müzik dalgalanarak düşüyor, anons, tekrar yükseliyor.",
    "⚡ Enerji Geçişi":  "Enerjik geçişle kesilip anons yapılıyor.",
}

EQ_PRESETS = {
    "Ham (Efektsiz)":    None,
    "Broadcast Clear":   "broadcast",
    "Radio Warm":        "warm",
    "AM Radio":          "am",
    "Podcast Studio":    "podcast",
}


# ═════════════════════════════════════════════════════════════════
# SESSION STATE
# ═════════════════════════════════════════════════════════════════
def _si(key, val):
    if key not in st.session_state:
        st.session_state[key] = val

_si("_archive",     [])
_si("_favorites",   [])
_si("_api_pool",    [{"key":"","used":0,"label":f"API {i+1}"} for i in range(10)])
_si("_active_idx",  0)
_si("_secrets_loaded", False)
_si("_api_stats",   {"total_calls":0,"total_chars":0,"total_secs":0.0})
_si("_giris",       False)

# Text buffers
_si("_t_tek",   "[excitedly] İmaj FM'e hoş geldiniz! BU GECE unutulmaz bir program var...\n[whispers] Sürprizler için kulaklarınız bizde olsun.\n[seriously] Şimdi haberlere geçiyoruz.")
_si("_t_cift",  "Sunucu: [excitedly] İmaj FM'e hoş geldiniz!\nMisafir: [laughs] Teşekkürler, burada olmak harika!\nSunucu: [seriously] Haberler... [normal] Müziğe dönüyoruz.")
_si("_t_bulk",  "İmaj FM sabah yayını başlıyor.\nHaber bülteni için bekleyiniz.\nMüzik programımıza hoş geldiniz.")
_si("_t_ab1",   "[excitedly] İmaj FM'e hoş geldiniz!")
_si("_t_ab2",   "[seriously] İmaj FM'e hoş geldiniz.")

# Delay Reji state
_si("_playlist", [])
_si("_reji_voice",   "Kore")
_si("_reji_model",   "gemini-2.5-flash-tts")
_si("_reji_lang",    "tr-TR")
_si("_reji_style",   "")
_si("_reji_start",   "06:00")
_si("_reji_plan",    [])
_si("_reji_plan_ok", False)

# Broadcast builder state
_si("_broadcast_segments", [])
_si("_broadcast_name",     "")


# ═════════════════════════════════════════════════════════════════
# API HAVUZU
# ═════════════════════════════════════════════════════════════════
def load_secrets():
    if st.session_state._secrets_loaded: return
    st.session_state._secrets_loaded = True
    for i in range(10):
        try:
            v = st.secrets.get(f"GEMINI_API_KEY_{i+1}", "")
            if v and not st.session_state._api_pool[i]["key"]:
                st.session_state._api_pool[i]["key"] = v
        except Exception: pass

load_secrets()

def get_active_key():
    pool = st.session_state._api_pool
    idx  = st.session_state._active_idx
    for _ in range(10):
        s = pool[idx]
        if s["key"].strip() and s["used"] < MAX_PER_KEY:
            st.session_state._active_idx = idx
            return s["key"].strip(), idx
        idx = (idx+1) % 10
    return None, -1

def consume(idx, chars=0):
    st.session_state._api_pool[idx]["used"] += 1
    st.session_state._api_stats["total_calls"] += 1
    st.session_state._api_stats["total_chars"] += chars
    if st.session_state._api_pool[idx]["used"] >= MAX_PER_KEY:
        st.session_state._active_idx = (idx+1) % 10

def pool_stats():
    p = st.session_state._api_pool
    loaded = sum(1 for s in p if s["key"].strip())
    remain = sum(max(0, MAX_PER_KEY - s["used"]) for s in p if s["key"].strip())
    return loaded, remain


# ═════════════════════════════════════════════════════════════════
# ARŞİV
# ═════════════════════════════════════════════════════════════════
def archive_add(voice, model, lang, style, text, wav_bytes, mode="tek"):
    dur = len(wav_bytes) / (24000 * 2)
    uid = hashlib.md5((text + voice + str(time.time())).encode()).hexdigest()[:10]
    entry = {
        "id":         uid,
        "ts":         datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "ts_short":   datetime.datetime.now().strftime("%d.%m %H:%M"),
        "voice":      voice,
        "model":      model,
        "model_short": model.replace("gemini-","").replace("-preview","").replace("-tts",""),
        "lang":       lang,
        "style":      style[:40] if style else "",
        "text":       text,
        "preview":    text[:70].replace("\n"," ") + ("…" if len(text)>70 else ""),
        "wav":        wav_bytes,
        "dur":        round(dur, 1),
        "size":       len(wav_bytes),
        "mode":       mode,
    }
    st.session_state._archive.insert(0, entry)
    if len(st.session_state._archive) > MAX_ARCHIVE:
        st.session_state._archive = st.session_state._archive[:MAX_ARCHIVE]
    st.session_state._api_stats["total_secs"] += dur


# ═════════════════════════════════════════════════════════════════
# AUDIO CORE
# ═════════════════════════════════════════════════════════════════
def pcm2wav(pcm: bytes, rate=24000, ch=1, sw=2) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(ch); wf.setsampwidth(sw); wf.setframerate(rate)
        wf.writeframes(pcm)
    return buf.getvalue()

def tts_single(api_key, model, text, voice, lang, style) -> bytes:
    full = f"{style}\n\n{text}" if style.strip() else text
    lc   = lang if lang != "otomatik" else None
    c    = genai.Client(api_key=api_key)
    r    = c.models.generate_content(
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

def tts_multi(api_key, model, text, sp1, v1, sp2, v2, lang) -> bytes:
    lc = lang if lang != "otomatik" else None
    c  = genai.Client(api_key=api_key)
    r  = c.models.generate_content(
        model=model, contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                language_code=lc,
                multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                    speaker_voice_configs=[
                        types.SpeakerVoiceConfig(speaker=sp1,
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=v1))),
                        types.SpeakerVoiceConfig(speaker=sp2,
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=v2))),
                    ]
                )
            )
        )
    )
    return r.candidates[0].content.parts[0].inline_data.data


# ═════════════════════════════════════════════════════════════════
# PYDUB YARDIMCILARI
# ═════════════════════════════════════════════════════════════════
def normalize_seg(seg, target=-16.0):
    if not PYDUB_OK: return seg
    try: return seg.apply_gain(target - seg.dBFS)
    except Exception: return seg

def apply_eq_preset(seg, preset_key):
    if not PYDUB_OK or preset_key == "Ham (Efektsiz)": return seg
    try:
        p = EQ_PRESETS.get(preset_key)
        if p == "broadcast":
            return pydub_fx.normalize(pydub_fx.compress_dynamic_range(seg, threshold=-18, ratio=3.0))
        elif p == "warm":
            return pydub_fx.normalize(seg) + 1
        elif p == "am":
            return (seg.low_pass_filter(3000).high_pass_filter(400)) + 3
        elif p == "podcast":
            return pydub_fx.compress_dynamic_range(pydub_fx.normalize(seg), threshold=-20, ratio=2.5)
    except Exception: pass
    return seg

def mix_fon_voice(fon_seg, voice_seg, fon_vol=-8, duck_db=-16, fade_in=800, fade_out=1200):
    """Fon müziğin üzerine anons sesi duck edilerek mikslenir."""
    if not PYDUB_OK: return voice_seg
    try:
        fon = fon_seg + fon_vol
        vl  = len(voice_seg)
        fl  = len(fon)
        # Fon yeterliyse döngüye al
        if fl < vl + 2000:
            loops = (vl + 2000) // fl + 1
            fon   = fon * loops
        fon = fon[:vl + 2000].fade_in(fade_in)
        fp  = fon[:vl]; fr = fon[vl:]
        fm  = min(500, vl // 4)
        ducked = (
            fp[:fm].fade(to_gain=duck_db, start=0, duration=fm) +
            (fp[fm:vl-fm] + duck_db) +
            fp[vl-fm:].fade(from_gain=duck_db, start=0, duration=fm)
        )
        return normalize_seg(ducked.overlay(voice_seg) + fr.fade_out(fade_out))
    except Exception: return voice_seg

def wav_bytes_to_seg(wav_bytes):
    if not PYDUB_OK: return None
    try:
        return AudioSegment.from_file(io.BytesIO(wav_bytes), format="wav")
    except Exception: return None

def seg_to_wav_bytes(seg):
    if not PYDUB_OK or seg is None: return b""
    try:
        buf = io.BytesIO()
        seg.export(buf, format="wav")
        return buf.getvalue()
    except Exception: return b""

def audio_dur_bytes(wav_bytes):
    try:
        return len(wav_bytes) / (24000 * 2)
    except Exception: return 0.0

def audio_dur_file(path):
    if not PYDUB_OK or not os.path.exists(path): return 0.0
    try: return len(AudioSegment.from_file(path)) / 1000.0
    except Exception: return 0.0

def fmt_dur(sec):
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    if h: return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def quality_score_bytes(wav_bytes):
    if not PYDUB_OK: return 70
    try:
        seg = AudioSegment.from_file(io.BytesIO(wav_bytes), format="wav")
        sc  = 55
        if -22 <= seg.dBFS <= -10:   sc += 20
        elif -30 <= seg.dBFS <= -22: sc += 10
        if -5 <= seg.max_dBFS <= -0.5:  sc += 20
        elif -8 <= seg.max_dBFS <= -5:  sc += 10
        if seg.frame_rate >= 22050: sc += 5
        return min(100, max(0, sc))
    except Exception: return 70

def draw_waveform_bytes(wav_bytes, h=2.0):
    if not NP_OK: return
    try:
        buf = io.BytesIO(wav_bytes)
        with wave.open(buf, 'r') as wf:
            frames = wf.readframes(wf.getnframes())
            sr = wf.getframerate(); sw = wf.getsampwidth(); ch = wf.getnchannels()
        dt = np.int16 if sw == 2 else np.int8
        s  = np.frombuffer(frames, dtype=dt)
        if ch == 2: s = s[::2]
        step = max(1, len(s)//2000); ds = s[::step].astype(np.float32)
        mx   = np.max(np.abs(ds)) or 1; ds /= mx
        t    = np.linspace(0, len(s)/sr, len(ds))
        fig, ax = plt.subplots(figsize=(10, h), facecolor='#07090f')
        ax.set_facecolor('#07090f')
        ax.fill_between(t, ds,  alpha=.65, color='#3b82f6')
        ax.fill_between(t, -np.abs(ds), alpha=.2, color='#a78bfa')
        ax.axhline(0, color='#1a2436', lw=.8)
        ax.set_xlim(0, t[-1]); ax.set_ylim(-1.1, 1.1)
        for sp in ax.spines.values(): sp.set_visible(False)
        ax.tick_params(colors='#2e3f55', labelsize=7)
        plt.tight_layout(pad=.3)
        st.pyplot(fig, use_container_width=True); plt.close(fig)
    except Exception: pass

def list_audio_files(directory):
    exts = (".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac")
    if not os.path.isdir(directory): return []
    return sorted(f for f in os.listdir(directory) if f.lower().endswith(exts))

def save_upload(uploaded_file, dest_dir, custom_name=""):
    """Yüklenen dosyayı kaydet, WAV bytes döndür."""
    if uploaded_file is None: return None, None
    try:
        os.makedirs(dest_dir, exist_ok=True)
        fname = custom_name or uploaded_file.name
        fname = re.sub(r'[^\w\-.]', '_', fname)
        if '.' not in fname: fname += '.wav'
        dest  = os.path.join(dest_dir, fname)
        raw   = uploaded_file.getvalue() if hasattr(uploaded_file,'getvalue') else uploaded_file.read()
        if not raw or len(raw) < 64: return None, None
        with open(dest, 'wb') as f: f.write(raw)
        # WAV bytes: eğer PYDUB varsa normalize et ve WAV formatına çevir
        if PYDUB_OK:
            try:
                seg = AudioSegment.from_file(dest)
                wav_dest = os.path.splitext(dest)[0] + '.wav'
                seg.export(wav_dest, format='wav')
                with open(wav_dest,'rb') as f: wav_bytes = f.read()
                return wav_dest, wav_bytes
            except Exception: pass
        with open(dest,'rb') as f: return dest, f.read()
    except Exception as e:
        st.error(f"Upload hatası: {e}"); return None, None

def zip_wavs(items):
    """items: [(filename, wav_bytes)] → ZIP bytes"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fn, data in items:
            safe = re.sub(r'[^\w\-.]', '_', fn)
            zf.writestr(safe, data)
    return buf.getvalue()


# ═════════════════════════════════════════════════════════════════
# DELAY REJİ YARDIMCILARI
# ═════════════════════════════════════════════════════════════════
def song_uid():
    return hashlib.md5(str(time.time() + id({})).encode()).hexdigest()[:8]

def total_dur_sec(song):
    return song.get("duration_min", 3) * 60 + song.get("duration_sec", 30)

def add_time_str(base_str, secs):
    try:
        parts = base_str.split(":")
        h, m  = int(parts[0]), int(parts[1])
    except Exception: h, m = 6, 0
    total = h*3600 + m*60 + secs
    hh = (total // 3600) % 24
    mm = (total % 3600)  // 60
    ss = total % 60
    return f"{hh:02d}:{mm:02d}:{ss:02d}"

def auto_anons_bas(song):
    t  = song.get("title","Bilinmeyen")
    ar = song.get("artist","Bilinmeyen Sanatçı")
    return (f"[excitedly] Ve şimdi İmaj FM'de... {ar}! "
            f"[normal] '{t}' sizlerle buluşuyor. [whispers] Keyfini çıkarın...")

def auto_anons_son(song):
    t  = song.get("title","Bilinmeyen")
    ar = song.get("artist","Bilinmeyen Sanatçı")
    return (f"[normal] Dinlediğiniz... {ar} — '{t}' idi. "
            f"[excitedly] İmaj FM'de devam ediyoruz!")

def build_plan(playlist, start_str):
    plan = []; cursor = 0
    for song in playlist:
        sid      = song["id"]
        song_dur = total_dur_sec(song)
        if song.get("anons_bas"):
            txt  = song.get("anons_bas_text") or auto_anons_bas(song)
            adur = max(5, len(txt)//15)
            plan.append({"time": add_time_str(start_str, cursor), "offset": cursor,
                         "type": "anons_bas", "song_id": sid,
                         "label": f"🎙️ Baş Anons → {song.get('title','?')}",
                         "sublabel": txt[:55]+"…" if len(txt)>55 else txt,
                         "dur": adur, "wav": song.get("anons_wav_bas"), "text": txt})
            cursor += adur
        if song.get("fon_aktif"):
            plan.append({"time": add_time_str(start_str, cursor), "offset": cursor,
                         "type": "fon",
                         "label": f"🎶 Fon Geçiş [{song.get('fon_tip','Klasik')}] → {song.get('title','?')}",
                         "sublabel": FON_TIPLERI.get(song.get("fon_tip","📻 Radyo Klasik"),"")[:55],
                         "dur": 4, "song_id": sid, "wav": None, "text": ""})
            cursor += 4
        plan.append({"time": add_time_str(start_str, cursor), "offset": cursor,
                     "type": "song",
                     "label": f"🎵 {song.get('artist','?')} — {song.get('title','?')}",
                     "sublabel": fmt_dur(song_dur),
                     "dur": song_dur, "song_id": sid, "wav": None, "text": ""})
        cursor += song_dur
        if song.get("anons_son"):
            txt  = song.get("anons_son_text") or auto_anons_son(song)
            adur = max(4, len(txt)//15)
            plan.append({"time": add_time_str(start_str, cursor), "offset": cursor,
                         "type": "anons_son", "song_id": sid,
                         "label": f"🎙️ Son Anons ← {song.get('title','?')}",
                         "sublabel": txt[:55]+"…" if len(txt)>55 else txt,
                         "dur": adur, "wav": song.get("anons_wav_son"), "text": txt})
            cursor += adur
    return plan


# ═════════════════════════════════════════════════════════════════
# UI YARDIMCILARI
# ═════════════════════════════════════════════════════════════════
def text_stats(text):
    cc  = len(text); wc = len(text.split())
    sc  = max(1, text.count(".")+text.count("!")+text.count("?"))
    est = max(1, cc/17)
    st.markdown(
        f"<div style='font-size:.68rem;color:#2e3f55;margin:3px 0 8px;'>"
        f"📊 {cc} karakter · {wc} kelime · {sc} cümle · ~{est:.0f}s tahmini süre</div>",
        unsafe_allow_html=True)

def tag_btns(state_key, prefix):
    cols = st.columns(len(ETAGS))
    for i,(em,lbl,tag) in enumerate(ETAGS):
        with cols[i]:
            if st.button(em, key=f"{prefix}_et_{i}", help=f"{lbl}: {tag.strip()}",
                         use_container_width=True):
                st.session_state[state_key] += tag; st.rerun()

def style_widget(prefix):
    ps   = st.selectbox("Preset", list(STYLE_PRESETS.keys()),
                        label_visibility="collapsed", key=f"{prefix}_ps")
    pval = STYLE_PRESETS[ps]
    ca,cb = st.columns(2)
    with ca:
        st.markdown("<div style='font-size:.65rem;color:#3b82f6;margin-bottom:3px;'>🇹🇷 TR Stil</div>",unsafe_allow_html=True)
        tr_ = st.text_area("TR",value=pval,height=62,label_visibility="collapsed",
                            placeholder="Coşkulu oku...",key=f"{prefix}_str")
    with cb:
        st.markdown("<div style='font-size:.65rem;color:#f59e0b;margin-bottom:3px;'>🇬🇧 EN Style</div>",unsafe_allow_html=True)
        en_ = st.text_area("EN",value="",height=62,label_visibility="collapsed",
                            placeholder="Read excited...",key=f"{prefix}_sen")
    return " / ".join(filter(None,[tr_.strip(),en_.strip()]))

def chip(text, color="gray"):
    return f'<span class="chip chip-{color}">{text}</span>'

def result_card(wav_bytes, raw_bytes, voice, api_idx, dl_key, dl_name, extra_chips=""):
    dur = len(raw_bytes)/(24000*2)
    qs  = quality_score_bytes(wav_bytes)
    bar_color = "#22c55e" if qs>=70 else "#f59e0b" if qs>=50 else "#ef4444"
    st.markdown(
        f"<div class='card g'>✅ {VOICES.get(voice,('?',''))[0]} {voice} &nbsp;·&nbsp; "
        f"API {api_idx+1} &nbsp;·&nbsp; {dur:.1f}s &nbsp;·&nbsp; {len(wav_bytes):,}B &nbsp; {extra_chips}</div>",
        unsafe_allow_html=True)
    st.markdown(f"<div class='qbar'><div class='qbar-f' style='width:{qs}%;background:{bar_color};'></div></div>",
                unsafe_allow_html=True)
    st.audio(wav_bytes, format="audio/wav")
    draw_waveform_bytes(wav_bytes)
    st.download_button("💾 WAV İndir", wav_bytes, file_name=dl_name,
                       mime="audio/wav", use_container_width=True, key=dl_key)


# ═════════════════════════════════════════════════════════════════
# GİRİŞ
# ═════════════════════════════════════════════════════════════════
def login_page():
    _,col,_ = st.columns([1,1.05,1])
    with col:
        st.markdown("""
        <div style='margin-top:65px;padding:34px 30px;background:#0b0f1a;
                    border:1px solid #1a2d4a;border-radius:18px;box-shadow:0 24px 64px rgba(0,0,0,.8);'>
            <h2 style='text-align:center;font-family:Syne,sans-serif;font-weight:800;font-size:1.5rem;
                       margin:0 0 3px;background:linear-gradient(90deg,#fff 20%,#ff6060);
                       -webkit-background-clip:text;-webkit-text-fill-color:transparent;'>
                🎙️ İmaj FM
            </h2>
            <p style='text-align:center;color:#2e3f55;font-size:.7rem;letter-spacing:.15em;margin:0 0 24px;'>
                TTS STÜDYO v6 · GÜVENLİ GİRİŞ
            </p>
        </div>""", unsafe_allow_html=True)
        u = st.text_input("u","",placeholder="👤  kullanıcı adı",label_visibility="collapsed")
        p = st.text_input("p","",type="password",placeholder="🔑  şifre",label_visibility="collapsed")
        if st.button("Stüdyoya Bağlan →", type="primary", use_container_width=True):
            if u == "kenan" and p == "imajfm":
                st.session_state._giris = True; st.rerun()
            else: st.error("❌ Hatalı giriş.")

if not st.session_state._giris:
    login_page(); st.stop()


# ═════════════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:5px 0 11px;'>
        <span style='font-family:Syne,sans-serif;font-size:.95rem;font-weight:800;
            background:linear-gradient(90deg,#fff,#ff6060);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;'>
            🎙️ İmaj FM
        </span>
        <span style='font-size:.62rem;color:#2e3f55;letter-spacing:.1em;'>  TTS v6</span>
    </div>
    """, unsafe_allow_html=True)

    ak_sb, ai_sb = get_active_key()
    tk_sb, tr_sb = pool_stats()

    if ak_sb:
        used_a = st.session_state._api_pool[ai_sb]["used"]
        rem_a  = MAX_PER_KEY - used_a
        pct_a  = used_a / MAX_PER_KEY
        bc_a   = "#22c55e" if pct_a<.6 else ("#f59e0b" if pct_a<.9 else "#ef4444")
    else:
        rem_a=0; pct_a=1; bc_a="#ef4444"

    with st.expander(f"🗝️  API Havuzu  ·  {tk_sb}/10  ·  {tr_sb} kalan", expanded=True):
        if ak_sb:
            lbl_a = st.session_state._api_pool[ai_sb].get("label", f"API {ai_sb+1}")
            rem_c = "#22c55e" if rem_a>3 else "#f59e0b"
            st.markdown(f"""
            <div style='background:#07090f;border-radius:8px;padding:8px 10px;margin-bottom:7px;font-size:.73rem;'>
                <div style='display:flex;justify-content:space-between;margin-bottom:4px;'>
                    <span style='color:#6b7a8d;'>Aktif: <b style='color:#22c55e;'>{lbl_a}</b></span>
                    <span style='color:#6b7a8d;'>Kalan: <b style='color:{rem_c};'>{rem_a}/{MAX_PER_KEY}</b></span>
                    <span style='color:#6b7a8d;'>Toplam: <b style='color:#3b82f6;'>{tr_sb}</b></span>
                </div>
                <div class='qbar'><div class='qbar-f' style='width:{pct_a*100:.0f}%;background:{bc_a};'></div></div>
                <div style='font-size:.61rem;color:#2e3f55;margin-top:2px;'>Otomatik rotasyon aktif</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("<div class='card r'>⛔ API yok! Aşağıdan ekleyin.</div>", unsafe_allow_html=True)

        with st.expander("📋 Secrets.toml Formatı", expanded=False):
            st.code('GEMINI_API_KEY_1 = "AIza..."\nGEMINI_API_KEY_2 = "AIza..."', language="toml")

        for i in range(10):
            slot = st.session_state._api_pool[i]
            used = slot["used"]; has = bool(slot["key"].strip())
            full = has and used >= MAX_PER_KEY
            warn = has and used >= int(MAX_PER_KEY*.6) and not full
            is_ac = (i == st.session_state._active_idx) and has and not full
            lbl = slot.get("label", f"API {i+1}")
            icon  = "⬜" if not has else ("🔴" if full else ("🟡" if warn else "🟢"))
            badge = "boş" if not has else ("DOLU" if full else f"{used}/{MAX_PER_KEY}")
            act   = " ◀" if is_ac else ""
            with st.expander(f"{icon} {lbl}{act}  ·  {badge}", expanded=False):
                nl = st.text_input(f"İsim{i}", value=lbl, placeholder=f"API {i+1}",
                                   label_visibility="collapsed", key=f"lbl_{i}")
                if nl != lbl: st.session_state._api_pool[i]["label"]=nl; st.rerun()
                nk = st.text_input(f"Key{i}", value=slot["key"], type="password",
                                   placeholder="AIzaSy...", label_visibility="collapsed", key=f"key_{i}")
                if nk != slot["key"]: st.session_state._api_pool[i]["key"]=nk; st.rerun()
                if has:
                    p2 = min(used/MAX_PER_KEY,1)
                    b2 = "#22c55e" if p2<.6 else ("#f59e0b" if p2<.9 else "#ef4444")
                    st.markdown(f"<div class='qbar'><div class='qbar-f' style='width:{p2*100:.0f}%;background:{b2};'></div></div>",
                                unsafe_allow_html=True)
                k1,k2,k3 = st.columns(3)
                with k1:
                    if st.button("🔄",key=f"rst_{i}",use_container_width=True):
                        st.session_state._api_pool[i]["used"]=0; st.rerun()
                with k2:
                    if st.button("▶",key=f"act_{i}",use_container_width=True):
                        st.session_state._active_idx=i; st.rerun()
                with k3:
                    if st.button("🗑️",key=f"del_{i}",use_container_width=True):
                        st.session_state._api_pool[i]={"key":"","used":0,"label":f"API {i+1}"}; st.rerun()

    with st.expander("🎭  Duygu Etiketleri", expanded=False):
        st.markdown("""
        <table class='ttbl'><thead><tr><th>Etiket</th><th>Açıklama</th></tr></thead><tbody>
        <tr><td><span class='tc'>[excitedly]</span></td><td>Coşkulu, hızlı</td></tr>
        <tr><td><span class='tc'>[whispers]</span></td><td>Fısıltı, gece tonu</td></tr>
        <tr><td><span class='tc'>[laughs]</span></td><td>Gülümseyen, sıcak</td></tr>
        <tr><td><span class='tc'>[seriously]</span></td><td>Ciddi, haber tonu</td></tr>
        <tr><td><span class='tc'>[shouting]</span></td><td>Bağırma, enerji</td></tr>
        <tr><td><span class='tc'>[sighs]</span></td><td>Yorgun, nefes</td></tr>
        <tr><td><span class='tc'>[normal]</span></td><td>Standart tona dön</td></tr>
        </tbody></table>
        """, unsafe_allow_html=True)

    # Playlist mini özet
    pl_count = len(st.session_state._playlist)
    with st.expander(f"📻  Reji Playlist  ·  {pl_count} şarkı", expanded=False):
        if not st.session_state._playlist:
            st.caption("Playlist boş. Delay Reji sekmesinden ekleyin.")
        else:
            for i, s in enumerate(st.session_state._playlist[:5]):
                b = ""
                if s.get("anons_bas"): b += "🎙️B "
                if s.get("anons_son"): b += "🎙️S "
                if s.get("fon_aktif"): b += "🎶 "
                st.markdown(f"<div style='font-size:.7rem;color:#3d4f68;padding:3px 0;border-bottom:1px solid #0d1420;'>"
                            f"{i+1}. <b style='color:#60a5fa;'>{s.get('title','?')[:18]}</b> {b}</div>",
                            unsafe_allow_html=True)

    # Kütüphane özeti
    pl_songs  = list_audio_files(PLAYLIST_DIR)
    fon_files = list_audio_files(FON_DIR)
    arc_count = len(st.session_state._archive)
    with st.expander(f"📂  Kütüphane  ·  {len(pl_songs)} şarkı  ·  {len(fon_files)} fon", expanded=False):
        st.caption(f"Playlist: {len(pl_songs)} | Fon: {len(fon_files)} | Arşiv: {arc_count}")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;color:#101828;font-size:.62rem;'>İmaj FM v6 · 2026</div>",
                unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════
# ANA BAŞLIK
# ═════════════════════════════════════════════════════════════════
stat_s = st.session_state._api_stats
tk_m, tr_m = pool_stats()
arc_m = len(st.session_state._archive)
pl_m  = len(st.session_state._playlist)

st.markdown("""
<div class='hdr'>
    <h1>🎙️ İmaj FM · Seslendirme Stüdyosu</h1>
    <p><span class='ldot'></span>Gemini TTS v6 &nbsp;·&nbsp; Delay Reji &nbsp;·&nbsp; Yayın Otomasyonu &nbsp;·&nbsp;
    Fon+Anons Mikseri &nbsp;·&nbsp; Playlist &nbsp;·&nbsp; ZIP &nbsp;·&nbsp; Kütüphane &nbsp;·&nbsp; Arşiv</p>
</div>
""", unsafe_allow_html=True)

_, ai_m = get_active_key()
rem_m = MAX_PER_KEY - st.session_state._api_pool[ai_m]["used"] if ai_m>=0 else 0

cols8 = st.columns(8)
defs8 = [
    ("30",                   "Ses"),
    (f"{tk_m}/10",           "API","g"),
    (f"{tr_m}",              "Kalan","a"),
    (f"{arc_m}",             "Arşiv","b"),
    (f"{stat_s['total_calls']}","İstekler"),
    (f"{stat_s['total_secs']:.0f}s","Ses","p"),
    (f"{pl_m}",              "Playlist","t"),
    (f"{len(list_audio_files(PLAYLIST_DIR))}","Şarkılar"),
]
for col8,(val,lbl,*cls) in zip(cols8,defs8):
    c = cls[0] if cls else ""
    with col8:
        st.markdown(f'<div class="mbox {c}"><div class="v">{val}</div><div class="l">{lbl}</div></div>',
                    unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

ak_chk, _ = get_active_key()
if ak_chk is None:
    st.error("⛔ Kullanılabilir API anahtarı yok! Sol panelden ekleyin.")
    st.stop()
elif rem_m <= 2:
    st.warning(f"⚠️ API {ai_m+1} limitine yakın ({rem_m} kaldı). Otomatik rotasyon devreye girecek.")


# ═════════════════════════════════════════════════════════════════
# SEKMELER
# ═════════════════════════════════════════════════════════════════
tabs = st.tabs([
    "🎤 Tek",
    "🎭 Çift",
    "📦 Toplu",
    "🔬 A/B Test",
    "⭐ Favoriler",
    "📻 Delay Reji",
    "🎛️ Fon+Anons",
    "🚀 Yayın Otomasyon",
    "📁 Kütüphane",
    "📂 Arşiv",
])
t1,t2,t3,t4,t5,t6,t7,t8,t9,t10 = tabs


# ══════════════════════════════════════════════════════════════════
# T1 — TEK KONUŞMACI
# ══════════════════════════════════════════════════════════════════
with t1:
    cL,cR = st.columns([1.05,1], gap="large")
    with cL:
        st.markdown("<span class='sl'>▶ Şablon</span>", unsafe_allow_html=True)
        tmpl1 = st.selectbox("Ş1",["— Yok —"]+list(TEMPLATES.keys()),
                             label_visibility="collapsed", key="tmpl1")
        if tmpl1!="— Yok —" and st.button("📥 Yükle",key="ltmpl1"):
            st.session_state._t_tek=TEMPLATES[tmpl1]; st.rerun()

        st.markdown("<span class='sl'>▶ Model</span>", unsafe_allow_html=True)
        m1l = st.selectbox("M1",list(MODELS.values()),label_visibility="collapsed",key="m1")
        mdl1 = [k for k,v in MODELS.items() if v==m1l][0]

        st.markdown("<span class='sl'>▶ Dil</span>", unsafe_allow_html=True)
        l1l = st.selectbox("L1",list(LANGUAGES.values()),label_visibility="collapsed",index=1,key="l1")
        lng1 = [k for k,v in LANGUAGES.items() if v==l1l][0]

        st.markdown("<span class='sl'>▶ Ses Karakteri</span>", unsafe_allow_html=True)
        cn1 = st.radio("CN1",["Tümü","♀ Kadın","♂ Erkek"],horizontal=True,
                       label_visibility="collapsed",key="cn1")
        f1  = {k:v for k,v in VOICES.items()
               if cn1=="Tümü" or (cn1=="♀ Kadın" and v[0]=="♀") or (cn1=="♂ Erkek" and v[0]=="♂")}
        vc1 = st.selectbox("V1",list(f1.keys()),
                           format_func=lambda x:f"{VOICES[x][0]} {x}  —  {VOICES[x][1]}",
                           label_visibility="collapsed",key="v1")

        st.markdown("<span class='sl'>▶ EQ</span>", unsafe_allow_html=True)
        eq1 = st.selectbox("EQ1",list(EQ_PRESETS.keys()),label_visibility="collapsed",key="eq1")

        st.markdown("<span class='sl'>▶ Duygu & Stil</span>", unsafe_allow_html=True)
        sty1 = style_widget("t1")

        ak1,ai1 = get_active_key()
        r1 = MAX_PER_KEY-st.session_state._api_pool[ai1]["used"] if ai1>=0 else 0
        st.markdown(f"""<div class='card b'>
            <b>{VOICES[vc1][0]} {vc1}</b> — {VOICES[vc1][1]}<br>
            <span style='color:#3a7bd5;'>{m1l[:20]}</span> &nbsp;
            <span style='color:#22c55e;'>API {ai1+1}</span> · {r1} kalan
        </div>""", unsafe_allow_html=True)

        st.markdown("<span class='sl'>▶ Favorilere Ekle</span>", unsafe_allow_html=True)
        fa,fb = st.columns([2,1])
        with fa:
            fname1 = st.text_input("FN","",placeholder="Favori ismi...",
                                   label_visibility="collapsed",key="fname1")
        with fb:
            if st.button("⭐ Ekle",key="fadd1",use_container_width=True):
                if fname1.strip() and st.session_state._t_tek.strip():
                    st.session_state._favorites.append({
                        "id":    hashlib.md5((fname1+str(time.time())).encode()).hexdigest()[:8],
                        "name":  fname1.strip(),
                        "text":  st.session_state._t_tek,
                        "voice": vc1,"model":mdl1,"lang":lng1,
                    })
                    st.success("⭐ Eklendi!"); time.sleep(0.4); st.rerun()

    with cR:
        st.markdown("<span class='sl'>▶ Anons Metni</span>", unsafe_allow_html=True)
        tag_btns("_t_tek","t1")
        txt1 = st.text_area("TT1",value=st.session_state._t_tek,height=230,
                            label_visibility="collapsed",key="ta1",placeholder="Metni buraya yazın…")
        st.session_state._t_tek = txt1
        text_stats(txt1)

        if st.button(f"🔴  {vc1} ile Seslendir",type="primary",use_container_width=True,key="btn1"):
            if not txt1.strip(): st.warning("⚠️ Metin boş.")
            else:
                ak1,ai1 = get_active_key()
                if ak1 is None: st.error("❌ API kalmadı!")
                else:
                    with st.spinner(f"🎙️  {vc1}…  [API {ai1+1}]"):
                        try:
                            raw = tts_single(ak1,mdl1,txt1,vc1,lng1,sty1)
                            wav = pcm2wav(raw)
                            if PYDUB_OK and eq1!="Ham (Efektsiz)":
                                seg = apply_eq_preset(AudioSegment.from_file(io.BytesIO(wav),format="wav"),eq1)
                                wav = seg_to_wav_bytes(normalize_seg(seg))
                            consume(ai1,len(txt1))
                            archive_add(vc1,mdl1,lng1,sty1,txt1,wav,"tek")
                            result_card(wav,raw,vc1,ai1,"dl1",f"imajfm_{vc1.lower()}_{lng1}.wav")
                        except Exception as e: st.error(f"❌ {e}")


# ══════════════════════════════════════════════════════════════════
# T2 — ÇİFT KONUŞMACI
# ══════════════════════════════════════════════════════════════════
with t2:
    st.markdown("<div class='card b'>🎭 İki konuşmacı için multi-speaker Gemini TTS</div>",unsafe_allow_html=True)
    cL2,cR2 = st.columns([1.05,1],gap="large")
    with cL2:
        tmpl2 = st.selectbox("Ş2",["— Yok —"]+list(TEMPLATES.keys()),
                             label_visibility="collapsed",key="tmpl2")
        if tmpl2!="— Yok —" and st.button("📥 Yükle",key="ltmpl2"):
            st.session_state._t_cift=TEMPLATES[tmpl2]; st.rerun()

        m2l = st.selectbox("M2",list(MODELS.values()),label_visibility="collapsed",key="m2")
        mdl2 = [k for k,v in MODELS.items() if v==m2l][0]
        l2l = st.selectbox("L2",list(LANGUAGES.values()),label_visibility="collapsed",index=1,key="l2")
        lng2 = [k for k,v in LANGUAGES.items() if v==l2l][0]

        st.markdown("<span class='sl'>▶ Konuşmacı 1</span>",unsafe_allow_html=True)
        ca,cb = st.columns([1,2])
        with ca: sp1n = st.text_input("S1N","Sunucu",label_visibility="collapsed",key="sp1n")
        with cb: sp1v = st.selectbox("S1V",list(VOICES.keys()),
                                     format_func=lambda x:f"{VOICES[x][0]} {x} — {VOICES[x][1]}",
                                     label_visibility="collapsed",
                                     index=list(VOICES.keys()).index("Kore"),key="sp1v")

        st.markdown("<span class='sl'>▶ Konuşmacı 2</span>",unsafe_allow_html=True)
        cc,cd = st.columns([1,2])
        with cc: sp2n = st.text_input("S2N","Misafir",label_visibility="collapsed",key="sp2n")
        with cd: sp2v = st.selectbox("S2V",list(VOICES.keys()),
                                     format_func=lambda x:f"{VOICES[x][0]} {x} — {VOICES[x][1]}",
                                     label_visibility="collapsed",
                                     index=list(VOICES.keys()).index("Fenrir"),key="sp2v")

        eq2 = st.selectbox("EQ2",list(EQ_PRESETS.keys()),label_visibility="collapsed",key="eq2")
        ak2,ai2 = get_active_key()
        r2 = MAX_PER_KEY-st.session_state._api_pool[ai2]["used"] if ai2>=0 else 0
        st.markdown(f"""<div class='card b'>
            <code style='color:#60a5fa;'>{sp1n}</code> → {VOICES[sp1v][0]} <b>{sp1v}</b><br>
            <code style='color:#f87171;'>{sp2n}</code> → {VOICES[sp2v][0]} <b>{sp2v}</b><br>
            API {ai2+1} · {r2} kalan · Tek WAV çıktı
        </div>""",unsafe_allow_html=True)

    with cR2:
        st.markdown("<span class='sl'>▶ Diyalog Metni</span>",unsafe_allow_html=True)
        tag_btns("_t_cift","t2")
        txt2 = st.text_area("TT2",value=st.session_state._t_cift,height=230,
                            label_visibility="collapsed",key="ta2",
                            placeholder=f"{sp1n}: [excitedly] ...\n{sp2n}: [laughs] ...")
        st.session_state._t_cift = txt2
        text_stats(txt2)
        if st.button(f"🔴  {sp1n} & {sp2n} — Diyalog",type="primary",use_container_width=True,key="btn2"):
            if not txt2.strip(): st.warning("⚠️ Metin boş.")
            else:
                ak2,ai2 = get_active_key()
                if ak2 is None: st.error("❌ API kalmadı!")
                else:
                    with st.spinner(f"🎭  Diyalog…  [API {ai2+1}]"):
                        try:
                            raw2 = tts_multi(ak2,mdl2,txt2,sp1n,sp1v,sp2n,sp2v,lng2)
                            wav2 = pcm2wav(raw2)
                            if PYDUB_OK and eq2!="Ham (Efektsiz)":
                                seg2 = apply_eq_preset(AudioSegment.from_file(io.BytesIO(wav2),format="wav"),eq2)
                                wav2 = seg_to_wav_bytes(normalize_seg(seg2))
                            consume(ai2,len(txt2))
                            archive_add(f"{sp1v}+{sp2v}",mdl2,lng2,"",txt2,wav2,"cift")
                            result_card(wav2,raw2,sp1v,ai2,"dl2",f"imajfm_diyalog_{sp1v.lower()}.wav")
                        except Exception as e: st.error(f"❌ {e}")


# ══════════════════════════════════════════════════════════════════
# T3 — TOPLU SESLENDİRME
# ══════════════════════════════════════════════════════════════════
with t3:
    st.markdown("<div class='card b'>📦 Her satır ayrı WAV — ZIP olarak indir</div>",unsafe_allow_html=True)
    tab_b1,tab_b2 = st.tabs(["✏️ Manuel Liste","📄 TXT/CSV Yükle"])

    with tab_b1:
        cL3,cR3 = st.columns([1,1.2],gap="large")
        with cL3:
            m3l = st.selectbox("M3",list(MODELS.values()),label_visibility="collapsed",key="m3")
            mdl3 = [k for k,v in MODELS.items() if v==m3l][0]
            l3l = st.selectbox("L3",list(LANGUAGES.values()),label_visibility="collapsed",index=1,key="l3")
            lng3 = [k for k,v in LANGUAGES.items() if v==l3l][0]
            cn3 = st.radio("CN3",["Tümü","♀ Kadın","♂ Erkek"],horizontal=True,
                           label_visibility="collapsed",key="cn3")
            f3  = {k:v for k,v in VOICES.items()
                   if cn3=="Tümü" or (cn3=="♀ Kadın" and v[0]=="♀") or (cn3=="♂ Erkek" and v[0]=="♂")}
            vc3 = st.selectbox("V3",list(f3.keys()),
                               format_func=lambda x:f"{VOICES[x][0]} {x} — {VOICES[x][1]}",
                               label_visibility="collapsed",key="v3")
            eq3 = st.selectbox("EQ3",list(EQ_PRESETS.keys()),label_visibility="collapsed",key="eq3")
            sty3 = st.text_area("STY3","",height=55,label_visibility="collapsed",
                                placeholder="Stil talimatı (opsiyonel)",key="sty3")
            _,tr3 = pool_stats()
            lines3_p = [l.strip() for l in st.session_state._t_bulk.splitlines() if l.strip()]
            st.markdown(f"""<div class='card {"a" if len(lines3_p)>tr3 else "b"}'>
                {len(lines3_p)} satır · {len(lines3_p)} istek · {tr3} kalan
            </div>""",unsafe_allow_html=True)

        with cR3:
            txt3 = st.text_area("TT3",value=st.session_state._t_bulk,height=230,
                                label_visibility="collapsed",key="ta3",placeholder="Her satır bir ses...")
            st.session_state._t_bulk = txt3
            lines3 = [l.strip() for l in txt3.splitlines() if l.strip()]
            st.markdown(f"<div style='font-size:.68rem;color:#2e3f55;'>{len(lines3)} satır</div>",unsafe_allow_html=True)

            if st.button(f"🔴 {len(lines3)} Satırı Toplu Seslendir",type="primary",
                         use_container_width=True,key="btn3"):
                if not lines3: st.warning("⚠️ Satır yok.")
                else:
                    results3=[]; errors3=[]
                    prog3=st.progress(0,"Başlatılıyor…"); sts3=st.empty()
                    for idx3,line3 in enumerate(lines3):
                        ak3,ai3 = get_active_key()
                        if ak3 is None: errors3.append(f"Satır {idx3+1}: API kalmadı"); break
                        sts3.markdown(f"<div style='font-size:.75rem;color:#6b7a8d;'>🎙️ {idx3+1}/{len(lines3)}: {line3[:40]}  [API {ai3+1}]</div>",unsafe_allow_html=True)
                        try:
                            raw3 = tts_single(ak3,mdl3,line3,vc3,lng3,sty3)
                            wav3 = pcm2wav(raw3)
                            if PYDUB_OK and eq3!="Ham (Efektsiz)":
                                seg3 = apply_eq_preset(AudioSegment.from_file(io.BytesIO(wav3),format="wav"),eq3)
                                wav3 = seg_to_wav_bytes(normalize_seg(seg3))
                            consume(ai3,len(line3))
                            archive_add(vc3,mdl3,lng3,sty3,line3,wav3,"bulk")
                            fname3 = f"{idx3+1:02d}_{vc3.lower()}_{re.sub(r'[^\\w]','_',line3[:15])}.wav"
                            results3.append((fname3,wav3,line3))
                        except Exception as e: errors3.append(f"Satır {idx3+1}: {e}")
                        prog3.progress((idx3+1)/len(lines3))
                    prog3.empty(); sts3.empty()

                    if results3:
                        st.markdown(f"<div class='card g'>✅ {len(results3)}/{len(lines3)} tamamlandı</div>",unsafe_allow_html=True)
                        zip_data = zip_wavs([(fn,wb) for fn,wb,_ in results3])
                        st.download_button("📦 ZIP İndir",zip_data,
                                           file_name=f"bulk_{vc3.lower()}.zip",
                                           mime="application/zip",use_container_width=True,key="dl3zip")
                        for fn,wb,ln in results3:
                            with st.expander(f"🔊 {fn[:50]}",expanded=False):
                                st.audio(wb,format="audio/wav")
                                st.download_button("💾",wb,file_name=fn,mime="audio/wav",key=f"dl3_{fn}")
                    for e3 in errors3:
                        st.markdown(f"<div class='card r'>❌ {e3}</div>",unsafe_allow_html=True)

    with tab_b2:
        st.markdown("<div class='card b'>Her satır ayrı ses — TXT veya CSV dosyası</div>",unsafe_allow_html=True)
        up_txt = st.file_uploader("TXT / CSV Dosyası Yükle",type=["txt","csv"],key="bulk_up")
        if up_txt:
            raw_content = up_txt.read().decode("utf-8","ignore")
            lines_up = [l.strip() for l in raw_content.splitlines() if l.strip()]
            if up_txt.name.endswith(".csv"):
                # CSV ise ilk sütunu al
                lines_up = [l.split(",")[0].strip().strip('"') for l in lines_up]
            st.success(f"✅ {len(lines_up)} satır bulundu")
            st.session_state["bulk_up_lines"] = lines_up
            for i,l in enumerate(lines_up[:5]):
                st.markdown(f"<div style='font-size:.75rem;color:#6b7a8d;'>{i+1}. {l[:70]}</div>",unsafe_allow_html=True)
            if len(lines_up)>5: st.caption(f"+{len(lines_up)-5} satır daha...")

        if st.session_state.get("bulk_up_lines"):
            mu_l = st.selectbox("Model",list(MODELS.values()),label_visibility="collapsed",key="mu_m")
            mu_mdl = [k for k,v in MODELS.items() if v==mu_l][0]
            mu_ll  = st.selectbox("Dil",list(LANGUAGES.values()),label_visibility="collapsed",index=1,key="mu_l")
            mu_lng = [k for k,v in LANGUAGES.items() if v==mu_ll][0]
            mu_vc  = st.selectbox("Ses",list(VOICES.keys()),
                                  format_func=lambda x:f"{VOICES[x][0]} {x} — {VOICES[x][1]}",
                                  label_visibility="collapsed",key="mu_v")
            if st.button("🚀 Dosyadan Toplu Üret",type="primary",use_container_width=True,key="mu_btn"):
                lines_u = st.session_state["bulk_up_lines"]
                results_u=[]; prog_u=st.progress(0)
                for i,ln in enumerate(lines_u):
                    ak_u,ai_u = get_active_key()
                    if ak_u is None: break
                    try:
                        raw_u = tts_single(ak_u,mu_mdl,ln,mu_vc,mu_lng,"")
                        wav_u = pcm2wav(raw_u); consume(ai_u,len(ln))
                        archive_add(mu_vc,mu_mdl,mu_lng,"",ln,wav_u,"bulk-file")
                        results_u.append((f"{i+1:03d}_{mu_vc.lower()}.wav",wav_u))
                    except Exception as e:
                        st.warning(f"Satır {i+1}: {e}")
                    prog_u.progress((i+1)/len(lines_u))
                if results_u:
                    zip_u = zip_wavs(results_u)
                    st.download_button("📦 ZIP İndir",zip_u,"bulk_dosya.zip","application/zip",key="mu_zip")
                    st.success(f"✅ {len(results_u)} ses üretildi!")


# ══════════════════════════════════════════════════════════════════
# T4 — A/B TEST
# ══════════════════════════════════════════════════════════════════
with t4:
    st.markdown("<div class='card p'>🔬 Aynı metni iki farklı ses / model / stil ile karşılaştır</div>",unsafe_allow_html=True)
    ab1,ab2 = st.columns(2,gap="large")

    with ab1:
        st.markdown("<div style='font-family:Syne,sans-serif;font-size:.72rem;font-weight:800;letter-spacing:.15em;color:#a78bfa;text-transform:uppercase;margin-bottom:8px;'>🅐 VERSİYON A</div>",unsafe_allow_html=True)
        ma_l  = st.selectbox("MA",list(MODELS.values()),label_visibility="collapsed",key="masel")
        mdla  = [k for k,v in MODELS.items() if v==ma_l][0]
        la_l  = st.selectbox("LA",list(LANGUAGES.values()),label_visibility="collapsed",index=1,key="lasel")
        lnga  = [k for k,v in LANGUAGES.items() if v==la_l][0]
        cna   = st.radio("CNA",["Tümü","♀","♂"],horizontal=True,label_visibility="collapsed",key="cnasel")
        fa_   = {k:v for k,v in VOICES.items() if cna=="Tümü" or (cna=="♀" and v[0]=="♀") or (cna=="♂" and v[0]=="♂")}
        vca   = st.selectbox("VA",list(fa_.keys()),format_func=lambda x:f"{VOICES[x][0]} {x} — {VOICES[x][1]}",
                             label_visibility="collapsed",key="vasel")
        eqa   = st.selectbox("EQA",list(EQ_PRESETS.keys()),label_visibility="collapsed",key="eqasel")
        ps_a  = st.selectbox("PSA",list(STYLE_PRESETS.keys()),label_visibility="collapsed",key="psasel")
        stya  = st.text_area("STYA",value=STYLE_PRESETS[ps_a],height=55,label_visibility="collapsed",key="styasel")
        tag_btns("_t_ab1","ab1")
        txta  = st.text_area("TTA",value=st.session_state._t_ab1,height=130,label_visibility="collapsed",key="tta")
        st.session_state._t_ab1 = txta

    with ab2:
        st.markdown("<div style='font-family:Syne,sans-serif;font-size:.72rem;font-weight:800;letter-spacing:.15em;color:#fb923c;text-transform:uppercase;margin-bottom:8px;'>🅑 VERSİYON B</div>",unsafe_allow_html=True)
        mb_l  = st.selectbox("MB",list(MODELS.values()),label_visibility="collapsed",key="mbsel")
        mdlb  = [k for k,v in MODELS.items() if v==mb_l][0]
        lb_l  = st.selectbox("LB",list(LANGUAGES.values()),label_visibility="collapsed",index=1,key="lbsel")
        lngb  = [k for k,v in LANGUAGES.items() if v==lb_l][0]
        cnb   = st.radio("CNB",["Tümü","♀","♂"],horizontal=True,label_visibility="collapsed",key="cnbsel")
        fb_   = {k:v for k,v in VOICES.items() if cnb=="Tümü" or (cnb=="♀" and v[0]=="♀") or (cnb=="♂" and v[0]=="♂")}
        vcb   = st.selectbox("VB",list(fb_.keys()),format_func=lambda x:f"{VOICES[x][0]} {x} — {VOICES[x][1]}",
                             label_visibility="collapsed",index=min(1,len(fb_)-1),key="vbsel")
        eqb   = st.selectbox("EQB",list(EQ_PRESETS.keys()),label_visibility="collapsed",key="eqbsel")
        ps_b  = st.selectbox("PSB",list(STYLE_PRESETS.keys()),label_visibility="collapsed",key="psbsel")
        styb  = st.text_area("STYB",value=STYLE_PRESETS[ps_b],height=55,label_visibility="collapsed",key="stybsel")
        tag_btns("_t_ab2","ab2")
        txtb  = st.text_area("TTB",value=st.session_state._t_ab2,height=130,label_visibility="collapsed",key="ttb")
        st.session_state._t_ab2 = txtb

    b1c,b2c,b3c = st.columns(3)
    with b1c: run_a  = st.button("🅐 Sadece A",use_container_width=True,key="btnab1")
    with b2c: run_b  = st.button("🅑 Sadece B",use_container_width=True,key="btnab2")
    with b3c: run_ab = st.button("🔴 İkisini Birlikte",type="primary",use_container_width=True,key="btnaboth")

    do_a = run_a or run_ab; do_b = run_b or run_ab
    if do_a or do_b:
        ra,rb = st.columns(2)
        with ra:
            if do_a:
                aka,aia = get_active_key()
                if aka is None: st.error("❌ API kalmadı (A)")
                else:
                    with st.spinner(f"🅐 {vca}…"):
                        try:
                            rwa = tts_single(aka,mdla,txta,vca,lnga,stya)
                            wva = pcm2wav(rwa)
                            if PYDUB_OK and eqa!="Ham (Efektsiz)":
                                sa = apply_eq_preset(AudioSegment.from_file(io.BytesIO(wva),format="wav"),eqa)
                                wva = seg_to_wav_bytes(normalize_seg(sa))
                            consume(aia,len(txta))
                            archive_add(vca,mdla,lnga,stya,txta,wva,"ab-A")
                            qs_a = quality_score_bytes(wva)
                            st.markdown(f"<div class='card p'>🅐 {vca} · {len(rwa)/(24000*2):.1f}s · {qs_a}/100</div>",unsafe_allow_html=True)
                            st.audio(wva,format="audio/wav")
                            st.download_button("💾 A WAV",wva,file_name=f"A_{vca.lower()}.wav",mime="audio/wav",key="dlab")
                        except Exception as e: st.error(f"❌ A: {e}")
        with rb:
            if do_b:
                akb,aib = get_active_key()
                if akb is None: st.error("❌ API kalmadı (B)")
                else:
                    with st.spinner(f"🅑 {vcb}…"):
                        try:
                            rwb = tts_single(akb,mdlb,txtb,vcb,lngb,styb)
                            wvb = pcm2wav(rwb)
                            if PYDUB_OK and eqb!="Ham (Efektsiz)":
                                sb = apply_eq_preset(AudioSegment.from_file(io.BytesIO(wvb),format="wav"),eqb)
                                wvb = seg_to_wav_bytes(normalize_seg(sb))
                            consume(aib,len(txtb))
                            archive_add(vcb,mdlb,lngb,styb,txtb,wvb,"ab-B")
                            qs_b = quality_score_bytes(wvb)
                            st.markdown(f"<div class='card a'>🅑 {vcb} · {len(rwb)/(24000*2):.1f}s · {qs_b}/100</div>",unsafe_allow_html=True)
                            st.audio(wvb,format="audio/wav")
                            st.download_button("💾 B WAV",wvb,file_name=f"B_{vcb.lower()}.wav",mime="audio/wav",key="dlbb")
                        except Exception as e: st.error(f"❌ B: {e}")


# ══════════════════════════════════════════════════════════════════
# T5 — FAVORİLER
# ══════════════════════════════════════════════════════════════════
with t5:
    favs = st.session_state._favorites
    if not favs:
        st.markdown("<div style='text-align:center;padding:50px;color:#2e3f55;'><div style='font-size:2rem;'>⭐</div><div style='font-family:Syne,sans-serif;margin-top:8px;'>Favori metin yok</div><div style='font-size:.8rem;margin-top:5px;'>Tek Konuşmacı sekmesinden ⭐ Ekle.</div></div>",unsafe_allow_html=True)
    else:
        hf1,hf2 = st.columns([3,1])
        with hf1: st.markdown(f"<span class='sl'>▶ {len(favs)} Favori</span>",unsafe_allow_html=True)
        with hf2:
            if st.button("🗑️ Tümünü Sil",use_container_width=True,key="fav_clr"):
                st.session_state._favorites=[]; st.rerun()

        for fi,fv in enumerate(favs):
            fc1,fc2,fc3,fc4 = st.columns([2,.8,.8,.5])
            with fc1:
                st.markdown(f"""<div class='fav-card'>
                    <div class='fav-name'>⭐ {fv['name']}</div>
                    <div class='fav-prev'>{fv.get('voice','—')} · {fv.get('lang','—')}</div>
                    <div class='fav-prev'>{fv['text'][:60]}</div>
                </div>""",unsafe_allow_html=True)
            with fc2:
                if st.button("📋",key=f"fcp_{fi}",use_container_width=True,help="Tek sekmesine yükle"):
                    st.session_state._t_tek=fv["text"]; st.rerun()
            with fc3:
                if st.button("🔴",key=f"fsp_{fi}",use_container_width=True,help="Hemen seslendir"):
                    akf,aif = get_active_key()
                    if akf is None: st.error("❌ API yok")
                    else:
                        with st.spinner(f"🎙️ {fv.get('voice','Kore')}…"):
                            try:
                                rawf = tts_single(akf,fv.get("model","gemini-2.5-flash-tts"),
                                                  fv["text"],fv.get("voice","Kore"),fv.get("lang","tr-TR"),"")
                                wavf = pcm2wav(rawf); consume(aif,len(fv["text"]))
                                archive_add(fv.get("voice","Kore"),fv.get("model",""),fv.get("lang",""),"",fv["text"],wavf,"fav")
                                st.session_state[f"_fwav_{fi}"]=wavf; st.rerun()
                            except Exception as e: st.error(f"❌ {e}")
            with fc4:
                if st.button("🗑️",key=f"fdel_{fi}",use_container_width=True):
                    st.session_state._favorites.pop(fi); st.rerun()
            if f"_fwav_{fi}" in st.session_state:
                fw = st.session_state[f"_fwav_{fi}"]
                st.audio(fw,format="audio/wav")
                st.download_button("💾",fw,file_name=f"fav_{fv['name'].replace(' ','_')}.wav",
                                   mime="audio/wav",key=f"fdl_{fi}")


# ══════════════════════════════════════════════════════════════════
# T6 — DELAY REJİ
# ══════════════════════════════════════════════════════════════════
with t6:
    st.markdown("""
    <div class='reji-header'>
        <h2>📻 Delay Reji — Yayın Otomasyonu</h2>
        <p>Playlist · Şarkı başı/sonu anons · Fon müzik geçişleri · Yayın planı · ZIP</p>
    </div>
    """,unsafe_allow_html=True)

    rj_tabs = st.tabs(["🎵 Playlist","⚙️ Reji Ayarları","📋 Yayın Planı","🎬 Üretim & ZIP"])

    # ── RJ TAB 1: PLAYLİST ──────────────────────────────────────
    with rj_tabs[0]:
        playlist = st.session_state._playlist

        st.markdown("<span class='sl'>▶ Yeni Şarkı Ekle</span>",unsafe_allow_html=True)
        nc1,nc2,nc3,nc4 = st.columns([2,1.5,.5,.5])
        with nc1: new_title  = st.text_input("Şarkı","",placeholder="Şarkı adı…",label_visibility="collapsed",key="nt")
        with nc2: new_artist = st.text_input("Sanatçı","",placeholder="Sanatçı…",label_visibility="collapsed",key="na")
        with nc3: new_min    = st.number_input("Dk",0,10,3,label_visibility="collapsed",key="ndm")
        with nc4: new_sec    = st.number_input("Sn",0,59,30,label_visibility="collapsed",key="nds")

        ba,bb = st.columns(2)
        with ba:
            if st.button("➕ Ekle",use_container_width=True,key="add_song"):
                if new_title.strip():
                    st.session_state._playlist.append({
                        "id":song_uid(),"title":new_title.strip(),
                        "artist":new_artist.strip() or "Bilinmeyen",
                        "duration_min":int(new_min),"duration_sec":int(new_sec),
                        "anons_bas":False,"anons_son":False,
                        "anons_bas_text":"","anons_son_text":"",
                        "fon_aktif":False,"fon_tip":"📻 Radyo Klasik",
                        "anons_wav_bas":None,"anons_wav_son":None,
                    })
                    st.session_state._reji_plan_ok=False; st.rerun()
                else: st.warning("Şarkı adı boş olamaz.")
        with bb:
            if st.button("🎲 Demo Playlist",use_container_width=True,key="demo_pl"):
                demos = [("Gece Yarısı","Sezen Aksu",3,45),("Yüksek Yüksek Tepelere","Barış Manço",4,12),
                         ("Oy Benim Sarı Turnam","Neşet Ertaş",3,55),("Hayatımın Anlamı","MFÖ",3,28),
                         ("Leylim Ley","Zülfü Livaneli",4,5),("Mavi Bisiklet","Sıla",3,48),
                         ("Seni Bana Verecekler","Tarkan",4,20)]
                st.session_state._playlist=[{
                    "id":song_uid(),"title":t,"artist":ar,"duration_min":dm,"duration_sec":ds,
                    "anons_bas":False,"anons_son":False,"anons_bas_text":"","anons_son_text":"",
                    "fon_aktif":False,"fon_tip":"📻 Radyo Klasik","anons_wav_bas":None,"anons_wav_son":None,
                } for t,ar,dm,ds in demos]
                st.session_state._reji_plan_ok=False; st.rerun()

        # Playlist şarkıları da dosyadan yüklenebilir
        st.markdown("<span class='sl'>▶ Playlist'e Şarkı Dosyası Yükle (Yerel)</span>",unsafe_allow_html=True)
        st.markdown("<div class='card b' style='font-size:.75rem;'>MP3/WAV dosyaları yüklenince süreleri otomatik hesaplanır ve playlist'e eklenir.</div>",unsafe_allow_html=True)
        pl_up = st.file_uploader("Şarkı Dosyaları Yükle",type=["mp3","wav","ogg","flac","m4a"],
                                  accept_multiple_files=True,key="pl_up")
        if pl_up:
            added_pl=0
            for uf in pl_up:
                dest_p,_ = save_upload(uf,PLAYLIST_DIR,uf.name)
                if dest_p:
                    dur_p = audio_dur_file(dest_p)
                    mn,sc = divmod(int(dur_p),60); added_pl+=1
                    nm    = os.path.splitext(uf.name)[0]
                    st.session_state._playlist.append({
                        "id":song_uid(),"title":nm,"artist":"Yüklenen",
                        "duration_min":mn,"duration_sec":sc,
                        "anons_bas":False,"anons_son":False,"anons_bas_text":"","anons_son_text":"",
                        "fon_aktif":False,"fon_tip":"📻 Radyo Klasik","anons_wav_bas":None,"anons_wav_son":None,
                        "local_file":dest_p,
                    })
            if added_pl: st.success(f"✅ {added_pl} şarkı eklendi!"); st.session_state._reji_plan_ok=False; st.rerun()

        st.markdown("<hr>",unsafe_allow_html=True)

        if not playlist:
            st.markdown("<div style='text-align:center;padding:30px;color:#2e3f55;'>🎵 Playlist boş</div>",unsafe_allow_html=True)
        else:
            total_s = sum(total_dur_sec(s) for s in playlist)
            bas_c   = sum(1 for s in playlist if s.get("anons_bas"))
            son_c   = sum(1 for s in playlist if s.get("anons_son"))
            fon_c   = sum(1 for s in playlist if s.get("fon_aktif"))

            pm1,pm2,pm3,pm4,pm5 = st.columns(5)
            with pm1: st.markdown(f'<div class="mbox t"><div class="v">{len(playlist)}</div><div class="l">Şarkı</div></div>',unsafe_allow_html=True)
            with pm2: st.markdown(f'<div class="mbox b"><div class="v">{fmt_dur(total_s)}</div><div class="l">Süre</div></div>',unsafe_allow_html=True)
            with pm3: st.markdown(f'<div class="mbox a"><div class="v">{bas_c}</div><div class="l">Baş Anons</div></div>',unsafe_allow_html=True)
            with pm4: st.markdown(f'<div class="mbox a"><div class="v">{son_c}</div><div class="l">Son Anons</div></div>',unsafe_allow_html=True)
            with pm5: st.markdown(f'<div class="mbox g"><div class="v">{fon_c}</div><div class="l">Fon Geçiş</div></div>',unsafe_allow_html=True)

            st.markdown("<br><span class='sl'>▶ Şarkı Listesi</span>",unsafe_allow_html=True)

            for si,song in enumerate(playlist):
                sid     = song["id"]
                dur_s   = total_dur_sec(song)
                has_bas = song.get("anons_bas",False)
                has_son = song.get("anons_son",False)
                has_fon = song.get("fon_aktif",False)

                with st.expander(f"🎵 {si+1:02d}. {song.get('artist','?')} — {song.get('title','?')}   [{fmt_dur(dur_s)}]",expanded=False):
                    et1,et2,et3,et4 = st.columns([2,1.5,.5,.5])
                    with et1:
                        nt2 = st.text_input("Başlık",value=song["title"],label_visibility="collapsed",key=f"et_{sid}")
                        if nt2!=song["title"]: st.session_state._playlist[si]["title"]=nt2; st.session_state._reji_plan_ok=False; st.rerun()
                    with et2:
                        na2 = st.text_input("Sanatçı",value=song["artist"],label_visibility="collapsed",key=f"ea_{sid}")
                        if na2!=song["artist"]: st.session_state._playlist[si]["artist"]=na2; st.session_state._reji_plan_ok=False; st.rerun()
                    with et3:
                        ndm2 = st.number_input("Dk",0,10,song["duration_min"],label_visibility="collapsed",key=f"edm_{sid}")
                        if ndm2!=song["duration_min"]: st.session_state._playlist[si]["duration_min"]=int(ndm2); st.session_state._reji_plan_ok=False; st.rerun()
                    with et4:
                        nds2 = st.number_input("Sn",0,59,song["duration_sec"],label_visibility="collapsed",key=f"eds_{sid}")
                        if nds2!=song["duration_sec"]: st.session_state._playlist[si]["duration_sec"]=int(nds2); st.session_state._reji_plan_ok=False; st.rerun()

                    st.markdown("<hr>",unsafe_allow_html=True)
                    tg1,tg2,tg3 = st.columns(3)
                    with tg1:
                        nb = st.checkbox("🎙️ Şarkı Başı Anonsu",value=has_bas,key=f"cb_{sid}")
                        if nb!=has_bas:
                            st.session_state._playlist[si]["anons_bas"]=nb
                            if nb and not song.get("anons_bas_text"):
                                st.session_state._playlist[si]["anons_bas_text"]=auto_anons_bas(song)
                            st.session_state._reji_plan_ok=False; st.rerun()
                    with tg2:
                        ns = st.checkbox("🎙️ Şarkı Sonu Anonsu",value=has_son,key=f"cs_{sid}")
                        if ns!=has_son:
                            st.session_state._playlist[si]["anons_son"]=ns
                            if ns and not song.get("anons_son_text"):
                                st.session_state._playlist[si]["anons_son_text"]=auto_anons_son(song)
                            st.session_state._reji_plan_ok=False; st.rerun()
                    with tg3:
                        nf = st.checkbox("🎶 Fon Müzik Geçişi",value=has_fon,key=f"cf_{sid}")
                        if nf!=has_fon:
                            st.session_state._playlist[si]["fon_aktif"]=nf
                            st.session_state._reji_plan_ok=False; st.rerun()

                    if song.get("fon_aktif"):
                        fon_opts = list(FON_TIPLERI.keys())
                        cur_fon  = song.get("fon_tip","📻 Radyo Klasik")
                        cur_idx  = fon_opts.index(cur_fon) if cur_fon in fon_opts else 0
                        nft = st.selectbox("Fon Tipi",fon_opts,index=cur_idx,label_visibility="collapsed",key=f"ft_{sid}")
                        if nft!=cur_fon: st.session_state._playlist[si]["fon_tip"]=nft; st.session_state._reji_plan_ok=False; st.rerun()
                        st.markdown(f"<div style='font-size:.68rem;color:#10b981;margin:2px 0 6px;'>ℹ️ {FON_TIPLERI[nft]}</div>",unsafe_allow_html=True)

                    if song.get("anons_bas"):
                        st.markdown("<span class='sl3'>▸ Başı Anons Metni</span>",unsafe_allow_html=True)
                        bas_def = song.get("anons_bas_text") or auto_anons_bas(song)
                        new_bt  = st.text_area("BT",value=bas_def,height=80,label_visibility="collapsed",key=f"bat_{sid}")
                        if new_bt!=song.get("anons_bas_text",""):
                            st.session_state._playlist[si]["anons_bas_text"]=new_bt
                            st.session_state._playlist[si]["anons_wav_bas"]=None
                        if song.get("anons_wav_bas"):
                            st.markdown("<div class='card g' style='font-size:.72rem;'>✅ Ses üretildi</div>",unsafe_allow_html=True)
                            st.audio(song["anons_wav_bas"],format="audio/wav")
                        else:
                            st.markdown("<div class='card a' style='font-size:.72rem;'>⏳ Üretilmedi — Üretim sekmesinden üretin</div>",unsafe_allow_html=True)

                    if song.get("anons_son"):
                        st.markdown("<span class='sl3'>▸ Sonu Anons Metni</span>",unsafe_allow_html=True)
                        son_def = song.get("anons_son_text") or auto_anons_son(song)
                        new_st2 = st.text_area("ST",value=son_def,height=80,label_visibility="collapsed",key=f"sot_{sid}")
                        if new_st2!=song.get("anons_son_text",""):
                            st.session_state._playlist[si]["anons_son_text"]=new_st2
                            st.session_state._playlist[si]["anons_wav_son"]=None
                        if song.get("anons_wav_son"):
                            st.markdown("<div class='card g' style='font-size:.72rem;'>✅ Ses üretildi</div>",unsafe_allow_html=True)
                            st.audio(song["anons_wav_son"],format="audio/wav")
                        else:
                            st.markdown("<div class='card a' style='font-size:.72rem;'>⏳ Üretilmedi</div>",unsafe_allow_html=True)

                    st.markdown("<hr>",unsafe_allow_html=True)
                    or1,or2,or3,or4 = st.columns(4)
                    with or1:
                        if si>0 and st.button("⬆️",key=f"up_{sid}",use_container_width=True):
                            pl=st.session_state._playlist; pl[si-1],pl[si]=pl[si],pl[si-1]
                            st.session_state._reji_plan_ok=False; st.rerun()
                    with or2:
                        if si<len(playlist)-1 and st.button("⬇️",key=f"dn_{sid}",use_container_width=True):
                            pl=st.session_state._playlist; pl[si+1],pl[si]=pl[si],pl[si+1]
                            st.session_state._reji_plan_ok=False; st.rerun()
                    with or3:
                        if st.button("🔝 Üste",key=f"top_{sid}",use_container_width=True):
                            pl=st.session_state._playlist; pl.insert(0,pl.pop(si))
                            st.session_state._reji_plan_ok=False; st.rerun()
                    with or4:
                        if st.button("🗑️ Sil",key=f"del_{sid}",use_container_width=True):
                            st.session_state._playlist.pop(si); st.session_state._reji_plan_ok=False; st.rerun()

            if st.button("🗑️ Tüm Playlist'i Temizle",use_container_width=True,key="clear_pl"):
                st.session_state._playlist=[]; st.session_state._reji_plan_ok=False; st.rerun()

    # ── RJ TAB 2: AYARLAR ────────────────────────────────────────
    with rj_tabs[1]:
        st.markdown("<div class='card b'>Bu ayarlar tüm Delay Reji anonslarına uygulanır.</div>",unsafe_allow_html=True)
        ra1,ra2 = st.columns(2)
        with ra1:
            rj_ml = st.selectbox("Model",list(MODELS.values()),label_visibility="collapsed",key="rj_msel")
            rj_mk = [k for k,v in MODELS.items() if v==rj_ml][0]
            if rj_mk!=st.session_state._reji_model: st.session_state._reji_model=rj_mk
            rj_ll = st.selectbox("Dil",list(LANGUAGES.values()),index=1,label_visibility="collapsed",key="rj_lsel")
            rj_lk = [k for k,v in LANGUAGES.items() if v==rj_ll][0]
            if rj_lk!=st.session_state._reji_lang: st.session_state._reji_lang=rj_lk
            rj_start = st.text_input("Yayın Başlangıç Saati",value=st.session_state._reji_start,
                                     placeholder="HH:MM",label_visibility="collapsed",key="rj_start")
            if rj_start!=st.session_state._reji_start:
                st.session_state._reji_start=rj_start; st.session_state._reji_plan_ok=False
        with ra2:
            rj_cn = st.radio("Cinsiyet",["Tümü","♀ Kadın","♂ Erkek"],horizontal=True,
                             label_visibility="collapsed",key="rj_cn")
            rj_vf = {k:v for k,v in VOICES.items()
                     if rj_cn=="Tümü" or (rj_cn=="♀ Kadın" and v[0]=="♀") or (rj_cn=="♂ Erkek" and v[0]=="♂")}
            rj_vc = st.selectbox("Ses",list(rj_vf.keys()),
                                 format_func=lambda x:f"{VOICES[x][0]} {x} — {VOICES[x][1]}",
                                 label_visibility="collapsed",key="rj_vsel")
            if rj_vc!=st.session_state._reji_voice: st.session_state._reji_voice=rj_vc

        st.markdown("<span class='sl'>▶ Reji Stil Talimatı</span>",unsafe_allow_html=True)
        rj_ps  = st.selectbox("Preset",list(STYLE_PRESETS.keys()),label_visibility="collapsed",key="rj_ps")
        rj_sty = st.text_area("Stil",value=STYLE_PRESETS[rj_ps],height=75,
                              label_visibility="collapsed",key="rj_sty")
        if rj_sty!=st.session_state._reji_style: st.session_state._reji_style=rj_sty

        st.markdown(f"""<div class='card t'>
            🎙️ Ses: <b>{st.session_state._reji_voice}</b> &nbsp;·&nbsp;
            🤖 Model: <b>{st.session_state._reji_model.replace('gemini-','').replace('-tts','')}</b> &nbsp;·&nbsp;
            🌐 Dil: <b>{st.session_state._reji_lang}</b> &nbsp;·&nbsp;
            🕐 Başlangıç: <b>{st.session_state._reji_start}</b>
        </div>""",unsafe_allow_html=True)

        if st.button("🔄 Tüm Anons Metinlerini Yenile",use_container_width=True,key="regen_all"):
            for i,s in enumerate(st.session_state._playlist):
                if s.get("anons_bas"):
                    st.session_state._playlist[i]["anons_bas_text"]=auto_anons_bas(s)
                    st.session_state._playlist[i]["anons_wav_bas"]=None
                if s.get("anons_son"):
                    st.session_state._playlist[i]["anons_son_text"]=auto_anons_son(s)
                    st.session_state._playlist[i]["anons_wav_son"]=None
            st.success("✅ Metinler yenilendi!"); st.session_state._reji_plan_ok=False

    # ── RJ TAB 3: YAYIN PLANI ────────────────────────────────────
    with rj_tabs[2]:
        playlist = st.session_state._playlist
        if not playlist:
            st.markdown("<div class='card r'>⚠️ Playlist boş.</div>",unsafe_allow_html=True)
        else:
            gc1,_ = st.columns([1,2])
            with gc1:
                if st.button("📋 Yayın Planını Oluştur",type="primary",use_container_width=True,key="gen_plan"):
                    st.session_state._reji_plan = build_plan(playlist,st.session_state._reji_start)
                    st.session_state._reji_plan_ok=True; st.rerun()

            if not st.session_state._reji_plan_ok:
                st.markdown("<div class='card a'>ℹ️ Henüz plan oluşturulmadı.</div>",unsafe_allow_html=True)
            else:
                plan = st.session_state._reji_plan
                total_plan = sum(p["dur"] for p in plan)
                song_bl    = [p for p in plan if p["type"]=="song"]
                anons_bl   = [p for p in plan if p["type"] in ("anons_bas","anons_son")]
                fon_bl     = [p for p in plan if p["type"]=="fon"]
                end_t      = add_time_str(st.session_state._reji_start,total_plan)

                pp1,pp2,pp3,pp4 = st.columns(4)
                with pp1: st.markdown(f'<div class="mbox t"><div class="v">{len(song_bl)}</div><div class="l">Şarkı</div></div>',unsafe_allow_html=True)
                with pp2: st.markdown(f'<div class="mbox a"><div class="v">{len(anons_bl)}</div><div class="l">Anons</div></div>',unsafe_allow_html=True)
                with pp3: st.markdown(f'<div class="mbox g"><div class="v">{len(fon_bl)}</div><div class="l">Fon</div></div>',unsafe_allow_html=True)
                with pp4: st.markdown(f'<div class="mbox b"><div class="v">{fmt_dur(total_plan)}</div><div class="l">Toplam</div></div>',unsafe_allow_html=True)

                st.markdown(f"""<div class='broadcast-live'>
                    <div class='now-playing'>📡 {st.session_state._reji_start} → {end_t[:5]}</div>
                    <div style='font-size:.75rem;color:#2e5040;margin-top:4px;'>{len(plan)} blok · {len(song_bl)} şarkı · {len(anons_bl)} anons · {len(fon_bl)} fon</div>
                </div>""",unsafe_allow_html=True)

                type_map = {
                    "song":      ("ttype-song","🎵 ŞARKI"),
                    "anons_bas": ("ttype-anons","🎙️ BAŞ"),
                    "anons_son": ("ttype-anons","🎙️ SON"),
                    "fon":       ("ttype-fon","🎶 FON"),
                }
                for block in plan:
                    tcls,tlbl = type_map.get(block["type"],("ttype-song","?"))
                    wav_ic = "✅ " if block.get("wav") else ("⏳ " if block["type"] in ("anons_bas","anons_son") else "")
                    st.markdown(f"""
                    <div class='timeline-block'>
                        <span class='timeline-time'>{block["time"][:5]}</span>
                        <span class='timeline-type {tcls}'>{tlbl}</span>
                        <span class='timeline-label'>{wav_ic}{block["label"]}</span>
                        <span class='timeline-dur'>{fmt_dur(block["dur"])}</span>
                    </div>""",unsafe_allow_html=True)

    # ── RJ TAB 4: ÜRETİM & ZIP ───────────────────────────────────
    with rj_tabs[3]:
        playlist = st.session_state._playlist
        if not playlist:
            st.markdown("<div class='card r'>⚠️ Playlist boş.</div>",unsafe_allow_html=True)
        else:
            needed = [(i,s,"bas") for i,s in enumerate(playlist) if s.get("anons_bas") and not s.get("anons_wav_bas")] + \
                     [(i,s,"son") for i,s in enumerate(playlist) if s.get("anons_son") and not s.get("anons_wav_son")]
            done   = [(i,s,"bas") for i,s in enumerate(playlist) if s.get("anons_bas") and s.get("anons_wav_bas")] + \
                     [(i,s,"son") for i,s in enumerate(playlist) if s.get("anons_son") and s.get("anons_wav_son")]

            _,tr_rj = pool_stats()
            st.markdown(f"""<div class='card {"t" if not needed else "a"}'>
                ✅ {len(done)} üretildi &nbsp;·&nbsp; ⏳ {len(needed)} bekliyor &nbsp;·&nbsp;
                Ses: <b>{st.session_state._reji_voice}</b> &nbsp;·&nbsp; {tr_rj} API isteği kalan
            </div>""",unsafe_allow_html=True)

            # Tek tek üretim
            st.markdown("<span class='sl'>▶ Şarkı Bazlı Üretim</span>",unsafe_allow_html=True)
            for si,song in enumerate(playlist):
                sid = song["id"]
                if not song.get("anons_bas") and not song.get("anons_son"): continue
                with st.expander(f"🎵 {si+1:02d}. {song.get('title','?')}",expanded=False):
                    ub1,ub2 = st.columns(2)
                    if song.get("anons_bas"):
                        with ub1:
                            st.markdown("<div style='font-size:.72rem;color:#f59e0b;font-weight:700;margin-bottom:4px;'>🎙️ BAŞ ANONSU</div>",unsafe_allow_html=True)
                            bt_txt = song.get("anons_bas_text") or auto_anons_bas(song)
                            st.text_area("bt",value=bt_txt,height=70,label_visibility="collapsed",key=f"pb_{sid}",disabled=True)
                            if song.get("anons_wav_bas"):
                                st.audio(song["anons_wav_bas"],format="audio/wav")
                                st.download_button("💾",song["anons_wav_bas"],
                                                   file_name=f"bas_{si+1:02d}_{song['title'][:10]}.wav",
                                                   mime="audio/wav",key=f"dl_bas_{sid}")
                            if st.button("🔴 Üret",key=f"gen_bas_{sid}",use_container_width=True):
                                ak_r,ai_r = get_active_key()
                                if ak_r is None: st.error("❌ API yok")
                                else:
                                    with st.spinner("🎙️ Baş anonsu üretiliyor…"):
                                        try:
                                            raw_r = tts_single(ak_r,st.session_state._reji_model,bt_txt,
                                                               st.session_state._reji_voice,
                                                               st.session_state._reji_lang,
                                                               st.session_state._reji_style)
                                            wav_r = pcm2wav(raw_r); consume(ai_r,len(bt_txt))
                                            st.session_state._playlist[si]["anons_wav_bas"]=wav_r
                                            archive_add(st.session_state._reji_voice,st.session_state._reji_model,
                                                        st.session_state._reji_lang,st.session_state._reji_style,bt_txt,wav_r,"reji")
                                            st.session_state._reji_plan_ok=False; st.rerun()
                                        except Exception as e: st.error(f"❌ {e}")
                    if song.get("anons_son"):
                        with ub2:
                            st.markdown("<div style='font-size:.72rem;color:#60a5fa;font-weight:700;margin-bottom:4px;'>🎙️ SON ANONSU</div>",unsafe_allow_html=True)
                            st_txt = song.get("anons_son_text") or auto_anons_son(song)
                            st.text_area("st2",value=st_txt,height=70,label_visibility="collapsed",key=f"ps_{sid}",disabled=True)
                            if song.get("anons_wav_son"):
                                st.audio(song["anons_wav_son"],format="audio/wav")
                                st.download_button("💾",song["anons_wav_son"],
                                                   file_name=f"son_{si+1:02d}_{song['title'][:10]}.wav",
                                                   mime="audio/wav",key=f"dl_son_{sid}")
                            if st.button("🔴 Üret",key=f"gen_son_{sid}",use_container_width=True):
                                ak_r2,ai_r2 = get_active_key()
                                if ak_r2 is None: st.error("❌ API yok")
                                else:
                                    with st.spinner("🎙️ Son anonsu üretiliyor…"):
                                        try:
                                            raw_r2 = tts_single(ak_r2,st.session_state._reji_model,st_txt,
                                                                st.session_state._reji_voice,
                                                                st.session_state._reji_lang,
                                                                st.session_state._reji_style)
                                            wav_r2 = pcm2wav(raw_r2); consume(ai_r2,len(st_txt))
                                            st.session_state._playlist[si]["anons_wav_son"]=wav_r2
                                            archive_add(st.session_state._reji_voice,st.session_state._reji_model,
                                                        st.session_state._reji_lang,st.session_state._reji_style,st_txt,wav_r2,"reji")
                                            st.session_state._reji_plan_ok=False; st.rerun()
                                        except Exception as e: st.error(f"❌ {e}")

            st.markdown("<hr>",unsafe_allow_html=True)
            st.markdown("<span class='sl'>▶ Toplu Üretim</span>",unsafe_allow_html=True)
            if needed:
                st.markdown(f"<div class='card {'a' if len(needed)>tr_rj else 'b'}'>{len(needed)} anons üretilecek · {tr_rj} istek kalan</div>",unsafe_allow_html=True)
                if st.button(f"🔴 {len(needed)} Anonsu Toplu Üret",type="primary",use_container_width=True,key="bulk_reji"):
                    prog_r=st.progress(0); sts_r=st.empty(); errs_r=[]
                    for ni,(nsi,nsong,ntype) in enumerate(needed):
                        ak_b,ai_b = get_active_key()
                        if ak_b is None: errs_r.append("API kalmadı"); break
                        ntxt = (nsong.get("anons_bas_text") or auto_anons_bas(nsong)) if ntype=="bas" \
                               else (nsong.get("anons_son_text") or auto_anons_son(nsong))
                        sts_r.markdown(f"<div style='font-size:.75rem;color:#6b7a8d;'>🎙️ {ni+1}/{len(needed)}: {nsong['title']} [{ntype}]</div>",unsafe_allow_html=True)
                        try:
                            raw_b = tts_single(ak_b,st.session_state._reji_model,ntxt,
                                               st.session_state._reji_voice,st.session_state._reji_lang,
                                               st.session_state._reji_style)
                            wav_b = pcm2wav(raw_b); consume(ai_b,len(ntxt))
                            if ntype=="bas": st.session_state._playlist[nsi]["anons_wav_bas"]=wav_b
                            else:            st.session_state._playlist[nsi]["anons_wav_son"]=wav_b
                            archive_add(st.session_state._reji_voice,st.session_state._reji_model,
                                        st.session_state._reji_lang,st.session_state._reji_style,ntxt,wav_b,"reji")
                        except Exception as e: errs_r.append(f"{nsong['title']} ({ntype}): {e}")
                        prog_r.progress((ni+1)/len(needed))
                    sts_r.empty(); st.session_state._reji_plan_ok=False
                    if errs_r:
                        for err in errs_r: st.markdown(f"<div class='card r'>❌ {err}</div>",unsafe_allow_html=True)
                    else: st.success(f"✅ {len(needed)} anons üretildi!"); st.rerun()
            else:
                st.markdown("<div class='card g'>✅ Tüm anonslar üretildi!</div>",unsafe_allow_html=True)

            # ZIP
            st.markdown("<hr><span class='sl'>▶ Tüm Anonsları ZIP İndir</span>",unsafe_allow_html=True)
            zip_items_r = []
            for si2,s2 in enumerate(playlist):
                if s2.get("anons_wav_bas"):
                    fn_r = f"{si2+1:02d}_BAS_{s2.get('artist','?')[:8]}_{s2.get('title','?')[:8]}.wav"
                    zip_items_r.append((fn_r,s2["anons_wav_bas"]))
                if s2.get("anons_wav_son"):
                    fn_r = f"{si2+1:02d}_SON_{s2.get('artist','?')[:8]}_{s2.get('title','?')[:8]}.wav"
                    zip_items_r.append((fn_r,s2["anons_wav_son"]))

            if zip_items_r:
                st.markdown(f"<div class='card t'>{len(zip_items_r)} anons ZIP'e hazır</div>",unsafe_allow_html=True)
                zip_r = zip_wavs(zip_items_r)
                st.download_button(f"📦 {len(zip_items_r)} Anonsu ZIP İndir",zip_r,
                                   file_name=f"reji_anonslar_{st.session_state._reji_start.replace(':','-')}.zip",
                                   mime="application/zip",use_container_width=True,key="dl_reji_zip")
            else:
                st.markdown("<div class='card a'>⏳ Üretilmiş anons yok.</div>",unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# T7 — FON + ANONS MİKSERİ
# ══════════════════════════════════════════════════════════════════
with t7:
    st.markdown("""<div class='reji-header' style='border-color:#1a1a3e;'>
        <h2 style='background:linear-gradient(90deg,#fff 30%,#a78bfa 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>🎛️ Fon+Anons Mikseri</h2>
        <p style='color:#2e2040;'>Anons sesi + fon müziği birleştir · Duck efekti · Fade-in/out · ZIP çıktı</p>
    </div>""",unsafe_allow_html=True)

    if not PYDUB_OK:
        st.markdown("<div class='card r'>⚠️ PyDub kurulu değil. Fon mikseri için: <code>pip install pydub</code></div>",unsafe_allow_html=True)
    else:
        fon_files_mx = list_audio_files(FON_DIR)
        if not fon_files_mx:
            st.markdown("<div class='card a'>📁 /fon klasörü boş. Kütüphane sekmesinden fon müziği yükleyin.</div>",unsafe_allow_html=True)

        mx_tabs = st.tabs(["🎛️ Tek Miksleme","📦 Toplu Fon Uygula","🎵 Arşivden Miksleme"])

        with mx_tabs[0]:
            cLm,cRm = st.columns([1.1,1],gap="large")
            with cLm:
                st.markdown("<span class='sl'>▶ Anons Metni & TTS</span>",unsafe_allow_html=True)
                mx_model_l = st.selectbox("Model",list(MODELS.values()),label_visibility="collapsed",key="mx_model")
                mx_mdl = [k for k,v in MODELS.items() if v==mx_model_l][0]
                mx_lang_l  = st.selectbox("Dil",list(LANGUAGES.values()),label_visibility="collapsed",index=1,key="mx_lang")
                mx_lng = [k for k,v in LANGUAGES.items() if v==mx_lang_l][0]
                mx_cn  = st.radio("Cinsiyet",["Tümü","♀ Kadın","♂ Erkek"],horizontal=True,
                                  label_visibility="collapsed",key="mx_cn")
                mx_vf  = {k:v for k,v in VOICES.items()
                          if mx_cn=="Tümü" or (mx_cn=="♀ Kadın" and v[0]=="♀") or (mx_cn=="♂ Erkek" and v[0]=="♂")}
                mx_vc  = st.selectbox("Ses",list(mx_vf.keys()),
                                      format_func=lambda x:f"{VOICES[x][0]} {x} — {VOICES[x][1]}",
                                      label_visibility="collapsed",key="mx_vc")
                mx_sty_ps = st.selectbox("Stil Preset",list(STYLE_PRESETS.keys()),label_visibility="collapsed",key="mx_sty_ps")
                mx_sty    = st.text_area("Stil",value=STYLE_PRESETS[mx_sty_ps],height=60,
                                        label_visibility="collapsed",key="mx_sty")

                st.markdown("<span class='sl'>▶ Anons Yükle (Hazır WAV)</span>",unsafe_allow_html=True)
                mx_anons_up = st.file_uploader("Hazır anons WAV",type=["wav","mp3"],key="mx_anons_up")
                mx_uploaded_wav = None
                if mx_anons_up:
                    _,mx_uploaded_wav = save_upload(mx_anons_up,ANONS_DIR,f"upload_{int(time.time())}.wav")
                    if mx_uploaded_wav:
                        st.audio(mx_uploaded_wav,format="audio/wav")
                        st.markdown(f"<div class='card g' style='font-size:.72rem;'>✅ Yüklendi — {fmt_dur(audio_dur_bytes(mx_uploaded_wav))}</div>",unsafe_allow_html=True)

            with cRm:
                st.markdown("<span class='sl'>▶ Anons Metni</span>",unsafe_allow_html=True)
                mx_txt = st.text_area("MXTXT","",height=100,label_visibility="collapsed",key="mx_txt",
                                     placeholder="Anons metni yaz veya yukarıdan dosya yükle…")
                text_stats(mx_txt) if mx_txt else None

                st.markdown("<span class='sl'>▶ Fon Müziği Seçimi</span>",unsafe_allow_html=True)
                fon_source = st.radio("Kaynak",["📁 Kütüphaneden Seç","📤 Fon Yükle"],horizontal=True,key="fon_src")
                sel_fon_mx = None
                if fon_source == "📁 Kütüphaneden Seç":
                    if fon_files_mx:
                        sel_fon_mx = st.selectbox("Fon",fon_files_mx,label_visibility="collapsed",key="sel_fon_mx")
                        fon_path = os.path.join(FON_DIR,sel_fon_mx)
                        dur_f = audio_dur_file(fon_path)
                        st.markdown(f"<div style='font-size:.68rem;color:#2e3f55;'>{sel_fon_mx} · {fmt_dur(dur_f)}</div>",unsafe_allow_html=True)
                    else:
                        st.markdown("<div class='card a'>Kütüphanede fon yok.</div>",unsafe_allow_html=True)
                else:
                    fon_up2 = st.file_uploader("Fon Müziği",type=["mp3","wav","ogg"],key="fon_up2")
                    if fon_up2:
                        fon_path2,_ = save_upload(fon_up2,FON_DIR,fon_up2.name)
                        if fon_path2:
                            sel_fon_mx = fon_up2.name
                            st.success(f"✅ Kütüphaneye eklendi: {fon_up2.name}")

                st.markdown("<span class='sl'>▶ Miksleme Parametreleri</span>",unsafe_allow_html=True)
                mx1,mx2 = st.columns(2)
                with mx1:
                    fon_vol  = st.slider("Fon Ses (dB)",-24,0,-8,key="mx_fvol")
                    duck_db  = st.slider("Duck Derinliği",-30,-6,-16,key="mx_duck")
                with mx2:
                    fade_in  = st.slider("Fade-In (ms)",100,3000,800,key="mx_fi")
                    fade_out = st.slider("Fade-Out (ms)",100,5000,1500,key="mx_fo")
                mx_eq = st.selectbox("EQ",list(EQ_PRESETS.keys()),label_visibility="collapsed",key="mx_eq")

                if st.button("🎛️ MİKSLE & OLUŞTUR",type="primary",use_container_width=True,key="mx_btn"):
                    has_text = mx_txt.strip()
                    has_wav  = mx_uploaded_wav is not None
                    has_fon  = sel_fon_mx is not None or (fon_source=="📤 Fon Yükle" and "fon_up2" in st.session_state and st.session_state.fon_up2)

                    if not (has_text or has_wav):
                        st.warning("⚠️ Anons metni yazın veya hazır WAV yükleyin.")
                    elif not sel_fon_mx and fon_source=="📁 Kütüphaneden Seç":
                        st.warning("⚠️ Fon müziği seçin.")
                    else:
                        # Anons ses üret veya yüklenenini kullan
                        anons_wav = mx_uploaded_wav
                        if not anons_wav and has_text:
                            ak_mx,ai_mx = get_active_key()
                            if ak_mx is None: st.error("❌ API kalmadı!")
                            else:
                                with st.spinner(f"🎙️ {mx_vc}…"):
                                    try:
                                        raw_mx = tts_single(ak_mx,mx_mdl,mx_txt,mx_vc,mx_lng,mx_sty)
                                        anons_wav = pcm2wav(raw_mx); consume(ai_mx,len(mx_txt))
                                        archive_add(mx_vc,mx_mdl,mx_lng,mx_sty,mx_txt,anons_wav,"tek")
                                    except Exception as e: st.error(f"❌ TTS: {e}"); anons_wav=None

                        if anons_wav:
                            fon_file_path = os.path.join(FON_DIR,sel_fon_mx) if sel_fon_mx else None
                            if fon_file_path and os.path.exists(fon_file_path):
                                try:
                                    with st.spinner("🎛️ Miksliyor…"):
                                        v_seg   = AudioSegment.from_file(io.BytesIO(anons_wav),format="wav")
                                        f_seg   = AudioSegment.from_file(fon_file_path)
                                        mixed   = mix_fon_voice(f_seg,v_seg,fon_vol,duck_db,fade_in,fade_out)
                                        if mx_eq!="Ham (Efektsiz)": mixed=apply_eq_preset(mixed,mx_eq)
                                        mixed   = normalize_seg(mixed)
                                        mix_wav = seg_to_wav_bytes(mixed)
                                    qs_mx = quality_score_bytes(mix_wav)
                                    st.markdown(f"<div class='card t'>✅ Fon+Anons Hazır · {fmt_dur(len(mixed)/1000)} · {qs_mx}/100</div>",unsafe_allow_html=True)
                                    st.audio(mix_wav,format="audio/wav")
                                    draw_waveform_bytes(mix_wav)
                                    st.download_button("📦 Fon+Anons WAV İndir",mix_wav,
                                                       file_name=f"fon_anons_{int(time.time())}.wav",
                                                       mime="audio/wav",use_container_width=True,key="dl_mx")
                                except Exception as e: st.error(f"❌ Miksleme: {e}")
                            else:
                                st.audio(anons_wav,format="audio/wav")
                                st.download_button("💾 Anons WAV",anons_wav,
                                                   file_name=f"anons_{int(time.time())}.wav",
                                                   mime="audio/wav",key="dl_anons_only")

        with mx_tabs[1]:
            st.markdown("<div class='card b'>Arşivdeki TTS seslerine toplu fon uygula</div>",unsafe_allow_html=True)
            arc_files_mx = [e for e in st.session_state._archive if e.get("wav")]
            if not arc_files_mx or not fon_files_mx:
                st.info("Arşivde ses veya kütüphanede fon yok.")
            else:
                sel_fon_bulk = st.selectbox("Fon Müziği",fon_files_mx,key="sel_fon_bulk")
                sel_arc_bulk = st.multiselect("Arşivden Ses Seç",
                                              [f"{e['ts_short']} · {e['voice']} · {e['preview'][:30]}" for e in arc_files_mx],
                                              key="sel_arc_bulk")
                fv_bulk = st.slider("Fon Ses",-24,0,-8,key="fv_bulk")
                dd_bulk = st.slider("Duck",-30,-6,-16,key="dd_bulk")
                if sel_arc_bulk and st.button("📦 Toplu Uygula",use_container_width=True,key="bulk_fon_btn"):
                    indices = [i for i,e in enumerate(arc_files_mx)
                               if f"{e['ts_short']} · {e['voice']} · {e['preview'][:30]}" in sel_arc_bulk]
                    fon_s  = AudioSegment.from_file(os.path.join(FON_DIR,sel_fon_bulk))
                    results_b=[]; prog_b=st.progress(0)
                    for ni,idx_b in enumerate(indices):
                        entry = arc_files_mx[idx_b]
                        try:
                            v_s = AudioSegment.from_file(io.BytesIO(entry["wav"]),format="wav")
                            m_s = mix_fon_voice(fon_s,v_s,fv_bulk,dd_bulk)
                            mw  = seg_to_wav_bytes(m_s)
                            fn_b = f"fon_{entry['voice']}_{entry['id']}.wav"
                            results_b.append((fn_b,mw))
                        except Exception as e: st.warning(f"Hata: {e}")
                        prog_b.progress((ni+1)/len(indices))
                    if results_b:
                        zip_b = zip_wavs(results_b)
                        st.success(f"✅ {len(results_b)} ses miksleştirildi!")
                        st.download_button("📦 ZIP İndir",zip_b,"fon_toplu.zip","application/zip",key="dl_bulk_fon")

        with mx_tabs[2]:
            st.markdown("<div class='card b'>Arşivdeki anons sesiyle tek anons dinle ve indir</div>",unsafe_allow_html=True)
            arc_items = st.session_state._archive
            if not arc_items:
                st.info("Arşiv boş.")
            else:
                sel_arc2 = st.selectbox("Arşivden Ses",
                                        [f"{e['ts_short']} | {e['voice']} | {e['preview'][:40]}" for e in arc_items],
                                        key="sel_arc2")
                arc_idx2 = next((i for i,e in enumerate(arc_items)
                                 if f"{e['ts_short']} | {e['voice']} | {e['preview'][:40]}" == sel_arc2), 0)
                sel_entry = arc_items[arc_idx2]
                st.audio(sel_entry["wav"],format="audio/wav")
                draw_waveform_bytes(sel_entry["wav"])
                if fon_files_mx:
                    sel_fon3 = st.selectbox("Fon",fon_files_mx,key="sel_fon3")
                    fv3 = st.slider("Fon Ses",-24,0,-8,key="fv3")
                    if st.button("🎛️ Miksleme Uygula",use_container_width=True,key="arc_mix_btn"):
                        try:
                            v3 = AudioSegment.from_file(io.BytesIO(sel_entry["wav"]),format="wav")
                            f3 = AudioSegment.from_file(os.path.join(FON_DIR,sel_fon3))
                            m3 = mix_fon_voice(f3,v3,fv3)
                            mw3 = seg_to_wav_bytes(normalize_seg(m3))
                            st.audio(mw3,format="audio/wav")
                            st.download_button("💾 WAV",mw3,f"arc_fon_{sel_entry['id']}.wav","audio/wav",key="dl_arc3")
                        except Exception as e: st.error(f"❌ {e}")


# ══════════════════════════════════════════════════════════════════
# T8 — YAYIN OTOMASYONU
# ══════════════════════════════════════════════════════════════════
with t8:
    st.markdown("""<div class='reji-header' style='border-color:#1a2e0d;'>
        <h2 style='background:linear-gradient(90deg,#fff 30%,#22c55e 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>🚀 Yayın Otomasyonu</h2>
        <p style='color:#1a3010;'>Şarkı + anons + fon → tam yayın akışı · Zincir yayın · ZIP çıktı</p>
    </div>""",unsafe_allow_html=True)

    if not PYDUB_OK:
        st.markdown("<div class='card r'>⚠️ PyDub gerekli: <code>pip install pydub</code></div>",unsafe_allow_html=True)
    else:
        yo_tabs = st.tabs(["📋 Yayın Planla","🔗 Zincir Yayın","✂️ Ses Birleştir"])

        with yo_tabs[0]:
            st.markdown("<div class='card b'>Playlist şarkıları + arşiv/yüklenen anonslar → birleşik yayın dosyası</div>",unsafe_allow_html=True)

            pl_songs = list_audio_files(PLAYLIST_DIR)
            if not pl_songs:
                st.markdown("<div class='card a'>📁 Kütüphanede şarkı yok. Kütüphane sekmesinden ekleyin.</div>",unsafe_allow_html=True)
            else:
                yo1,yo2 = st.columns([1.2,1])
                with yo1:
                    yo_sel = st.multiselect("Şarkı Sıralaması",pl_songs,default=pl_songs[:min(3,len(pl_songs))],key="yo_sel")
                    yo_cf  = st.slider("Crossfade (ms)",0,3000,1200,key="yo_cf")
                    yo_gap = st.slider("Şarkı Arası Boşluk (ms)",0,5000,1500,key="yo_gap")
                    fon_files_yo = list_audio_files(FON_DIR)
                    yo_fon  = st.selectbox("Otomatik Fon",["Yok"]+fon_files_yo,key="yo_fon")
                    yo_fvol = st.slider("Fon Ses",-24,0,-8,key="yo_fvol") if yo_fon!="Yok" else -8
                    yo_duck = st.slider("Duck",-30,-6,-16,key="yo_duck") if yo_fon!="Yok" else -16
                    yo_name = st.text_input("Yayın Adı",value=f"Yayin_{datetime.datetime.now().strftime('%H%M')}",key="yo_name")

                with yo2:
                    st.markdown("<span class='sl'>▶ Şarkı Başı Anons Ekle</span>",unsafe_allow_html=True)
                    # Arşivdeki üretilmiş sesler
                    arc_anons = [e for e in st.session_state._archive if e.get("wav")]
                    st.markdown(f"<div style='font-size:.68rem;color:#2e3f55;'>Arşivde {len(arc_anons)} ses var. Sıra ile atanır.</div>",unsafe_allow_html=True)
                    yo_use_arc = st.checkbox("Arşiv seslerini şarkı başına ekle",key="yo_use_arc")
                    yo_upload_anons = st.file_uploader("Veya Anons WAV Yükle",type=["wav"],
                                                       accept_multiple_files=True,key="yo_anons_up")
                    uploaded_anons = []
                    if yo_upload_anons:
                        for uf in yo_upload_anons:
                            _,wav_u = save_upload(uf,ANONS_DIR,uf.name)
                            if wav_u: uploaded_anons.append(wav_u)
                        if uploaded_anons: st.success(f"✅ {len(uploaded_anons)} anons yüklendi")

                if yo_sel and st.button("🚀 YAYIN OLUŞTUR",type="primary",use_container_width=True,key="yo_btn"):
                    with st.status("🎙️ Yayın oluşturuluyor…",expanded=True) as yo_stat:
                        master = AudioSegment.silent(500)
                        fon_seg_yo = AudioSegment.from_file(os.path.join(FON_DIR,yo_fon)) if yo_fon!="Yok" else None

                        for idx_y,fname_y in enumerate(yo_sel):
                            sp_y = os.path.join(PLAYLIST_DIR,fname_y)
                            if not os.path.exists(sp_y):
                                st.write(f"⚠️ {fname_y} bulunamadı, atlanıyor")
                                continue
                            st.write(f"🎵 [{idx_y+1}/{len(yo_sel)}] {fname_y}")
                            try:
                                song_seg = AudioSegment.from_file(sp_y)
                            except Exception as e:
                                st.write(f"❌ Yüklenemedi: {e}"); continue

                            # Anons belirleme
                            anons_seg_y = None
                            if yo_use_arc and idx_y < len(arc_anons):
                                try:
                                    anons_seg_y = AudioSegment.from_file(io.BytesIO(arc_anons[idx_y]["wav"]),format="wav")
                                except Exception: pass
                            elif idx_y < len(uploaded_anons):
                                try:
                                    anons_seg_y = AudioSegment.from_file(io.BytesIO(uploaded_anons[idx_y]),format="wav")
                                except Exception: pass

                            # Birleştir
                            if anons_seg_y is not None:
                                if fon_seg_yo is not None:
                                    block = mix_fon_voice(fon_seg_yo,anons_seg_y,yo_fvol,yo_duck)
                                    block = block.append(song_seg,crossfade=min(yo_cf,len(song_seg)//3))
                                else:
                                    block = anons_seg_y + song_seg
                            else:
                                block = song_seg

                            master = master.append(block,crossfade=min(yo_cf,len(block)//3))
                            if yo_gap>0: master += AudioSegment.silent(yo_gap)
                            st.write(f"✅ [{idx_y+1}] Tamamlandı")

                        master = normalize_seg(master)
                        out_wav_yo = seg_to_wav_bytes(master)
                        yo_stat.update(label="✅ Yayın hazır!",state="complete")

                    dur_yo = len(master)/1000
                    st.markdown(f"<div class='card g'>✅ {yo_name} · {fmt_dur(dur_yo)} · {len(yo_sel)} şarkı</div>",unsafe_allow_html=True)
                    st.audio(out_wav_yo,format="audio/wav")
                    st.download_button(f"📦 {yo_name} WAV İndir",out_wav_yo,
                                       file_name=f"{yo_name}.wav",mime="audio/wav",
                                       use_container_width=True,key="dl_yo")
                    st.balloons()

        with yo_tabs[1]:
            st.markdown("<div class='card b'>Her şarkı için sırayla: Fon → AI Anons (Delay Reji'den) → Şarkı zinciri</div>",unsafe_allow_html=True)
            pl_songs2 = list_audio_files(PLAYLIST_DIR)
            fon_files2 = list_audio_files(FON_DIR)

            if not pl_songs2 or not fon_files2:
                st.markdown("<div class='card a'>Playlist şarkısı ve fon müziği gerekli.</div>",unsafe_allow_html=True)
            elif not st.session_state._playlist:
                st.markdown("<div class='card a'>Delay Reji playlist boş. Önce Delay Reji sekmesinden şarkı ve anons ekleyin.</div>",unsafe_allow_html=True)
            else:
                ch_fon  = st.selectbox("Fon Müziği",fon_files2,key="ch_fon")
                ch_cf   = st.slider("Crossfade (ms)",0,2000,1000,key="ch_cf")
                ch_name = st.text_input("Yayın Adı",value=f"Zincir_{datetime.datetime.now().strftime('%H%M')}",key="ch_name")

                reji_pl = st.session_state._playlist
                anons_ready = [(s,s.get("anons_wav_bas") or s.get("anons_wav_son"))
                               for s in reji_pl if s.get("anons_wav_bas") or s.get("anons_wav_son")]
                st.markdown(f"<div class='card t'>{len(anons_ready)}/{len(reji_pl)} şarkı için anons üretilmiş</div>",unsafe_allow_html=True)

                if st.button("🔗 ZİNCİR YAYIN OLUŞTUR",type="primary",use_container_width=True,key="chain_btn"):
                    with st.status("🔗 Zincir yayın…",expanded=True) as ch_stat:
                        master_ch = AudioSegment.silent(500)
                        fon_ch = AudioSegment.from_file(os.path.join(FON_DIR,ch_fon))
                        for i,song in enumerate(reji_pl):
                            st.write(f"🎵 [{i+1}/{len(reji_pl)}] {song.get('title','?')}")
                            anons_w = song.get("anons_wav_bas") or song.get("anons_wav_son")
                            local_f = song.get("local_file")
                            pl_file = next((f for f in pl_songs2 if song.get("title","").lower() in f.lower()), None)
                            song_path = local_f if local_f and os.path.exists(local_f) else \
                                        (os.path.join(PLAYLIST_DIR,pl_file) if pl_file else None)
                            if song_path and os.path.exists(song_path):
                                try:
                                    s_seg = AudioSegment.from_file(song_path)
                                    if anons_w:
                                        a_seg = AudioSegment.from_file(io.BytesIO(anons_w),format="wav")
                                        block = mix_fon_voice(fon_ch,a_seg)
                                        block = block.append(s_seg,crossfade=ch_cf)
                                    else: block = s_seg
                                    master_ch = master_ch.append(block,crossfade=ch_cf)
                                    st.write(f"✅ [{i+1}]")
                                except Exception as e: st.write(f"❌ {e}")
                            else:
                                if anons_w:
                                    a_seg = AudioSegment.from_file(io.BytesIO(anons_w),format="wav")
                                    master_ch = master_ch.append(
                                        mix_fon_voice(fon_ch,a_seg),crossfade=ch_cf)
                        master_ch = normalize_seg(master_ch)
                        ch_wav = seg_to_wav_bytes(master_ch)
                        ch_stat.update(label="✅ Zincir yayın hazır!",state="complete")
                    st.markdown(f"<div class='card g'>✅ {ch_name} · {fmt_dur(len(master_ch)/1000)}</div>",unsafe_allow_html=True)
                    st.audio(ch_wav,format="audio/wav")
                    st.download_button(f"📦 {ch_name} WAV",ch_wav,f"{ch_name}.wav","audio/wav",
                                       use_container_width=True,key="dl_chain")
                    st.balloons()

        with yo_tabs[2]:
            st.markdown("<div class='card b'>Birden fazla ses dosyasını sıralı birleştir → tek WAV</div>",unsafe_allow_html=True)
            cnt_tabs2 = st.tabs(["📂 Arşivden Seç","📤 Dosya Yükle"])

            with cnt_tabs2[0]:
                arc_for_concat = st.session_state._archive
                if not arc_for_concat:
                    st.info("Arşiv boş.")
                else:
                    sel_concat = st.multiselect("Birleştirilecek Sesler (sıra önemli)",
                                               [f"{e['ts_short']} | {e['voice']} | {e['preview'][:35]}" for e in arc_for_concat],
                                               key="sel_concat")
                    concat_gap = st.slider("Arası Boşluk (ms)",0,3000,500,key="concat_gap")
                    concat_cf  = st.slider("Crossfade (ms)",0,2000,200,key="concat_cf")
                    if sel_concat and st.button("🔗 Birleştir",use_container_width=True,key="concat_arc_btn"):
                        indices_c = [i for i,e in enumerate(arc_for_concat)
                                     if f"{e['ts_short']} | {e['voice']} | {e['preview'][:35]}" in sel_concat]
                        segs_c = []
                        for idx_c in indices_c:
                            try:
                                segs_c.append(AudioSegment.from_file(
                                    io.BytesIO(arc_for_concat[idx_c]["wav"]),format="wav"))
                            except Exception as e: st.warning(f"Atlandı: {e}")
                        if segs_c:
                            result_c = segs_c[0]
                            for sc2 in segs_c[1:]:
                                if concat_gap>0: result_c += AudioSegment.silent(concat_gap)
                                if concat_cf>0:  result_c = result_c.append(sc2,crossfade=concat_cf)
                                else:            result_c += sc2
                            cw = seg_to_wav_bytes(normalize_seg(result_c))
                            st.success(f"✅ {len(segs_c)} ses birleştirildi · {fmt_dur(len(result_c)/1000)}")
                            st.audio(cw,format="audio/wav")
                            st.download_button("📦 Birleştirilmiş WAV",cw,"birlesik.wav","audio/wav",key="dl_concat_arc")

            with cnt_tabs2[1]:
                concat_ups = st.file_uploader("Ses Dosyaları Yükle (birden fazla seçilebilir)",
                                              type=["wav","mp3","ogg"],accept_multiple_files=True,key="concat_up2")
                if concat_ups:
                    gap_u  = st.slider("Boşluk (ms)",0,3000,500,key="gap_u")
                    cf_u   = st.slider("Crossfade (ms)",0,2000,200,key="cf_u")
                    if st.button("🔗 Birleştir",use_container_width=True,key="concat_up_btn"):
                        segs_u=[]
                        for uf in concat_ups:
                            try:
                                segs_u.append(AudioSegment.from_file(io.BytesIO(uf.read())))
                            except Exception as e: st.warning(f"{uf.name}: {e}")
                        if segs_u:
                            result_u = segs_u[0]
                            for su in segs_u[1:]:
                                if gap_u>0: result_u += AudioSegment.silent(gap_u)
                                if cf_u>0:  result_u = result_u.append(su,crossfade=cf_u)
                                else:       result_u += su
                            uw = seg_to_wav_bytes(normalize_seg(result_u))
                            st.success(f"✅ {len(segs_u)} dosya · {fmt_dur(len(result_u)/1000)}")
                            st.audio(uw,format="audio/wav")
                            st.download_button("📦 WAV",uw,"upload_birlesik.wav","audio/wav",key="dl_concat_up")


# ══════════════════════════════════════════════════════════════════
# T9 — KÜTÜPHANE
# ══════════════════════════════════════════════════════════════════
with t9:
    st.markdown("<span class='sl'>▶ Ses Kütüphanesi — Şarkılar · Fon · Jinglelar · Efektler</span>",unsafe_allow_html=True)
    lib_tabs = st.tabs(["🎵 Şarkılar","🎶 Fon Müzikleri","🎺 Jinglelar","🎭 Efektler"])

    def lib_panel_dark(dir_p, tab, tk, info=""):
        with tab:
            if info: st.markdown(f"<div class='card b' style='font-size:.78rem;'>{info}</div>",unsafe_allow_html=True)
            ups = st.file_uploader("Dosya Yükle",type=["mp3","wav","ogg","flac","m4a"],
                                   accept_multiple_files=True,key=f"lib_{tk}")
            if ups:
                cnt_l=0
                for u in ups:
                    sp_l,_ = save_upload(u,dir_p,u.name)
                    if sp_l: cnt_l+=1
                    else: st.warning(f"⚠️ {u.name} kaydedilemedi.")
                if cnt_l>0: st.success(f"✅ {cnt_l} dosya eklendi!"); st.rerun()

            files_l = list_audio_files(dir_p)
            total_l = sum(audio_dur_file(os.path.join(dir_p,f)) for f in files_l)
            st.markdown(
                f"<div style='font-size:.68rem;color:#2e3f55;margin:4px 0 10px;'>"
                f"{len(files_l)} dosya · {fmt_dur(total_l)} toplam süre</div>",
                unsafe_allow_html=True)
            for f in files_l:
                fp_l = os.path.join(dir_p,f); dur_l = audio_dur_file(fp_l)
                cc_l = st.columns([3,1,1])
                with cc_l[0]:
                    st.markdown(f'<div class="song-row"><span class="song-nm">🎵 {f[:40]}</span>'
                                f'<span class="song-dur">{fmt_dur(dur_l)}</span></div>',unsafe_allow_html=True)
                with cc_l[1]: st.audio(fp_l)
                with cc_l[2]:
                    if st.button("🗑️",key=f"ldel_{tk}_{f}",help="Sil"):
                        os.remove(fp_l); st.rerun()

    lib_panel_dark(PLAYLIST_DIR,lib_tabs[0],"songs")
    lib_panel_dark(FON_DIR,lib_tabs[1],"fon","Enstrümental arka plan müzikleri. Anons sırasında otomatik alçalır.")
    lib_panel_dark(JINGLE_DIR,lib_tabs[2],"jingles")
    lib_panel_dark(EFFECT_DIR,lib_tabs[3],"effects","Alkış, geçiş, ambians efektleri.")


# ══════════════════════════════════════════════════════════════════
# T10 — ARŞİV
# ══════════════════════════════════════════════════════════════════
with t10:
    arc = st.session_state._archive
    stat_a = st.session_state._api_stats

    st.markdown("<span class='sl'>▶ Oturum İstatistikleri</span>",unsafe_allow_html=True)
    sa1,sa2,sa3,sa4,sa5 = st.columns(5)
    with sa1: st.markdown(f'<div class="mbox b"><div class="v">{len(arc)}</div><div class="l">Kayıt</div></div>',unsafe_allow_html=True)
    with sa2: st.markdown(f'<div class="mbox g"><div class="v">{stat_a["total_calls"]}</div><div class="l">API Çağrısı</div></div>',unsafe_allow_html=True)
    with sa3: st.markdown(f'<div class="mbox a"><div class="v">{stat_a["total_secs"]:.0f}s</div><div class="l">Üretilen Ses</div></div>',unsafe_allow_html=True)
    with sa4: st.markdown(f'<div class="mbox p"><div class="v">{stat_a["total_chars"]:,}</div><div class="l">Karakter</div></div>',unsafe_allow_html=True)
    with sa5:
        total_mb = sum(e["size"] for e in arc)/(1024*1024)
        st.markdown(f'<div class="mbox"><div class="v">{total_mb:.1f}MB</div><div class="l">Boyut</div></div>',unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)

    if not arc:
        st.markdown("<div style='text-align:center;padding:50px;color:#2e3f55;'><div style='font-size:2rem;'>📂</div><div style='font-family:Syne,sans-serif;margin-top:8px;'>Arşiv Boş</div></div>",unsafe_allow_html=True)
    else:
        ah1,ah2,ah3 = st.columns([2,1,1])
        with ah1: st.markdown(f"<span class='sl'>▶ {len(arc)} Kayıt</span>",unsafe_allow_html=True)
        with ah2:
            if st.button("📦 Tümünü ZIP",use_container_width=True,key="arc_zip"):
                zip_all = zip_wavs([(f"{e['ts_short'].replace(':','-').replace(' ','_')}_{e['voice']}_{e['id']}.wav",e["wav"]) for e in arc])
                st.download_button("💾 ZIP",zip_all,"imajfm_arsiv.zip","application/zip",key="arc_zip_dl")
        with ah3:
            if st.button("🗑️ Tümünü Sil",use_container_width=True,key="arc_clr"):
                st.session_state._archive=[]
                st.session_state._api_stats={"total_calls":0,"total_chars":0,"total_secs":0.0}
                st.rerun()

        af1,af2 = st.columns([2,1])
        with af1:
            arc_search = st.text_input("Ara","",placeholder="🔍 Ses, metin veya model…",
                                       label_visibility="collapsed",key="arc_search")
        with af2:
            arc_mode = st.selectbox("Mod",["Tümü","tek","cift","bulk","bulk-file","ab-A","ab-B","fav","reji"],
                                    label_visibility="collapsed",key="arc_mode")

        filtered_arc = arc
        if arc_search.strip():
            q = arc_search.lower()
            filtered_arc = [h for h in filtered_arc
                            if q in h["voice"].lower() or q in h["text"].lower() or q in h["model"].lower()]
        if arc_mode!="Tümü":
            filtered_arc = [h for h in filtered_arc if h.get("mode","")==arc_mode]

        st.markdown(f"<div style='font-size:.68rem;color:#2e3f55;margin:4px 0 10px;'>{len(filtered_arc)} kayıt</div>",unsafe_allow_html=True)

        mode_colors = {"tek":"#3b82f6","cift":"#a78bfa","bulk":"#22c55e","bulk-file":"#10b981",
                       "ab-A":"#a78bfa","ab-B":"#fb923c","fav":"#fbbf24","reji":"#10b981"}
        gcols = st.columns(3)
        for gi,h in enumerate(filtered_arc):
            with gcols[gi%3]:
                mc = mode_colors.get(h.get("mode","tek"),"#3b82f6")
                st.markdown(f"""
                <div style='background:#0b0f1a;border:1px solid #131c2e;border-radius:9px;padding:11px 13px;margin-bottom:8px;'>
                    <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;'>
                        <span style='font-family:Syne,sans-serif;font-size:.78rem;font-weight:700;color:#60a5fa;'>
                            {VOICES.get(h["voice"].split("+")[0],("?",""))[0]} {h["voice"][:12]}
                        </span>
                        <span style='font-size:.65rem;color:#2e3f55;font-family:JetBrains Mono,monospace;'>{h["ts_short"]}</span>
                    </div>
                    <div style='font-size:.68rem;color:#2e3f55;margin-bottom:5px;'>
                        <span style='color:{mc};background:{mc}18;border-radius:4px;padding:1px 6px;font-size:.62rem;font-weight:700;'>{h.get("mode","tek").upper()}</span>
                        &nbsp;{h["model_short"]} · {h["dur"]}s · {h["size"]//1024}KB
                    </div>
                    <div style='font-size:.78rem;color:#6b7a8d;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>{h["preview"]}</div>
                </div>""",unsafe_allow_html=True)
                st.audio(h["wav"],format="audio/wav")
                dca,dcb = st.columns(2)
                with dca:
                    st.download_button("💾 WAV",h["wav"],
                                       file_name=f"imajfm_{h['voice'].lower().replace('+','_')}_{h['id']}.wav",
                                       mime="audio/wav",use_container_width=True,key=f"arc_dl_{h['id']}")
                with dcb:
                    if st.button("⭐",key=f"arc_fav_{h['id']}",use_container_width=True,help="Favoriye ekle"):
                        st.session_state._favorites.append({
                            "id":h["id"],"name":h["voice"]+" "+h["ts_short"],
                            "text":h["text"],"voice":h["voice"].split("+")[0],
                            "model":h["model"],"lang":h["lang"],})
                        st.rerun()


# ═════════════════════════════════════════════════════════════════
# FOOTER
# ═════════════════════════════════════════════════════════════════
st.markdown("<hr>",unsafe_allow_html=True)
pydub_s  = "✅ PyDub" if PYDUB_OK  else "❌ PyDub (pip install pydub)"
numpy_s  = "✅ NumPy" if NP_OK     else "❌ NumPy"
mutagen_s= "✅ Mutagen" if MUTAGEN_OK else "—"
tk_f, tr_f = pool_stats()
st.markdown(f"""
<div style='text-align:center;color:#101828;font-size:.65rem;letter-spacing:.1em;padding:5px 0 12px;'>
    İMAJ FM TTS STÜDYO v6 &nbsp;·&nbsp; Google Gemini TTS API &nbsp;·&nbsp;
    {pydub_s} &nbsp;·&nbsp; {numpy_s} &nbsp;·&nbsp;
    API: {tk_f}/10 yüklü · {tr_f} kalan &nbsp;·&nbsp; 2026
</div>
""",unsafe_allow_html=True)
ENDOFFILE
echo "Done"
Output

Command argument is 146_327 bytes, exceeding the 100_000-byte per-argument limit. For large content, pipe via stdin or use a file-write API instead of embedding the content inline in the command. Argument preview: 'cat > /mnt/user-data/outputs/app_v6.py << \'ENDOFFILE\'\n"""\n╔══════════════════════════════════════════════════════════════════════════════╗\n║  İMAJ FM · TTS STÜDYO  v6.0 — TAM ENTEGRE YAYIN SİSTEMİ    '
Done
