"""
╔══════════════════════════════════════════════════════════════════╗
║  İMAJ FM · TTS STÜDYO  v5.0                                      ║
║  YENİ: DELAY REJİ — YAYIN OTOMASYONU                             ║
║  · Playlist / Şarkı Listesi Yönetimi                             ║
║  · Şarkı Başı / Sonu Anons Planlama (TTS ile otomatik üretim)    ║
║  · Fon Müzik Geçişleri (fade-in / fade-out simülasyonu)          ║
║  · Yayın Sırası Yönetimi (drag-drop benzeri sıralama)            ║
║  · Saat Bazlı Zamanlama / Yayın Planı                            ║
║  · Kalıcı ses arşivi · A/B Test · Favoriler                      ║
║  · Toplu seslendirme + ZIP · Radyo şablonları                    ║
╚══════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import wave, io, zipfile, re, time, datetime, hashlib, json

from google import genai
from google.genai import types

# ─────────────────────────────────────────────────────────────────
# SAYFA AYARI
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="İmaj FM · TTS Stüdyo v5",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────
# CSS
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
.sl3{font-family:'Syne',sans-serif;font-size:.57rem;font-weight:700;
    letter-spacing:.15em;color:#10b981;text-transform:uppercase;
    margin:10px 0 4px;display:block;}

/* ── METRIC ── */
.mbox{background:#0b0f1a;border:1px solid #131c2e;border-radius:10px;
    padding:12px;text-align:center;}
.mbox .v{font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;color:#e05252;}
.mbox .l{font-size:.6rem;letter-spacing:.12em;color:#2e3f55;text-transform:uppercase;margin-top:2px;}
.mbox.g .v{color:#22c55e;} .mbox.b .v{color:#3b82f6;} .mbox.a .v{color:#f59e0b;} .mbox.p .v{color:#a78bfa;} .mbox.t .v{color:#10b981;}

/* ── CARDS ── */
.card{background:#0b0f1a;border:1px solid #131c2e;border-radius:9px;
    padding:11px 14px;margin:7px 0;font-size:.82rem;color:#6b7a8d;}
.card.b{border-left:3px solid #3a7bd5;}
.card.g{border-left:3px solid #22c55e;background:#021409;color:#4ade80;}
.card.a{border-left:3px solid #f59e0b;background:#100d00;color:#fbbf24;}
.card.r{border-left:3px solid #ef4444;background:#110404;color:#f87171;}
.card.p{border-left:3px solid #a78bfa;background:#090614;color:#c4b5fd;}
.card.t{border-left:3px solid #10b981;background:#011209;color:#34d399;}

/* ── BUTTONS ── */
[data-testid="stButton"]>button{
    font-family:'Syne',sans-serif;font-weight:700;letter-spacing:.04em;
    border-radius:9px;transition:all .2s;}
[data-testid="stButton"]>button[kind="primary"]{
    background:linear-gradient(135deg,#b91c1c,#dc2626) !important;
    border:none !important;color:#fff !important;}
[data-testid="stButton"]>button[kind="primary"]:hover{
    background:linear-gradient(135deg,#dc2626,#ef4444) !important;
    transform:translateY(-1px);
    box-shadow:0 5px 18px rgba(220,38,38,.4) !important;}
[data-testid="stButton"]>button[kind="secondary"]{
    background:#0f1420 !important;border:1px solid #131c2e !important;color:#b0bac9 !important;}
[data-testid="stButton"]>button[kind="secondary"]:hover{
    border-color:#3a7bd5 !important;color:#fff !important;}

/* ── INPUTS ── */
[data-testid="stTextArea"] textarea{
    background:#090d18 !important;border:1px solid #131c2e !important;
    border-radius:10px !important;color:#dde2ee !important;
    font-family:'Inter',sans-serif !important;font-size:.91rem !important;
    line-height:1.65 !important;caret-color:#e05252 !important;}
[data-testid="stTextArea"] textarea:focus{
    border-color:#e04040 !important;box-shadow:0 0 0 1px #e0303022 !important;}
[data-testid="stSelectbox"]>div>div,
[data-testid="stSelectbox"]>div>div>div{
    background:#090d18 !important;border:1px solid #131c2e !important;
    border-radius:8px !important;color:#dde2ee !important;}
[data-testid="stTextInput"]>div>div>input{
    background:#090d18 !important;border:1px solid #131c2e !important;
    border-radius:8px !important;color:#dde2ee !important;}
[data-testid="stAudio"]{background:#0b0f1a;border-radius:10px;padding:8px;}

/* ── SIDEBAR EXP ── */
[data-testid="stSidebar"] details{
    background:#0b0f1a !important;border:1px solid #131c2e !important;
    border-radius:9px !important;margin-bottom:5px !important;}
[data-testid="stSidebar"] details summary{
    font-family:'Syne',sans-serif !important;font-size:.75rem !important;
    font-weight:700 !important;color:#b0bac9 !important;padding:8px 11px !important;}
[data-testid="stSidebar"] details summary:hover{color:#e05252 !important;}
[data-testid="stSidebar"] details[open] summary{color:#e05252 !important;}

/* ── TABS ── */
[data-testid="stTabs"] [data-baseweb="tab-list"]{
    background:transparent !important;border-bottom:1px solid #131c2e;gap:0;}
[data-testid="stTabs"] [data-baseweb="tab"]{
    background:transparent !important;color:#2e3f55 !important;
    font-family:'Syne',sans-serif !important;font-weight:700 !important;
    font-size:.72rem !important;letter-spacing:.07em !important;
    padding:9px 14px !important;border-bottom:2px solid transparent !important;}
[data-testid="stTabs"] [aria-selected="true"]{
    color:#e05252 !important;border-bottom:2px solid #e05252 !important;}

/* ── QBAR ── */
.qbar{background:#101828;border-radius:4px;height:5px;margin:3px 0;overflow:hidden;}
.qbar-f{height:100%;border-radius:4px;transition:width .4s;}

/* ── ARCHIVE GRID ── */
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
    padding:9px 12px;margin:5px 0;cursor:pointer;transition:all .15s;}
.fav-card:hover{border-color:#e05252;}
.fav-name{font-family:'Syne',sans-serif;font-size:.75rem;font-weight:700;color:#dde2ee;}
.fav-prev{font-size:.7rem;color:#3d4f68;margin-top:2px;
    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}

/* ── TAG TABLE ── */
.ttbl{width:100%;border-collapse:collapse;font-size:.69rem;}
.ttbl th{color:#e05252;font-family:'Syne',sans-serif;font-size:.57rem;
    letter-spacing:.1em;text-transform:uppercase;padding:4px 3px;
    border-bottom:1px solid #131c2e;text-align:left;}
.ttbl td{padding:4px 3px;color:#4a5a6e;border-bottom:1px solid #0d1420;vertical-align:top;}
.tc{color:#60a5fa;font-family:'JetBrains Mono',monospace;font-size:.73rem;}
.ten{color:#f59e0b;font-size:.65rem;}

/* ── DELAY REJİ ÖZEL ── */
.reji-header{
    background:linear-gradient(135deg,#071a0f 0%,#07090f 100%);
    border:1px solid #0d2e1a;border-radius:14px;padding:18px 22px;
    margin-bottom:16px;position:relative;overflow:hidden;}
.reji-header::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
    background:linear-gradient(90deg,#10b981,#34d399,#10b981);
    background-size:200%;animation:scan 4s linear infinite;}
.reji-header h2{font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:800;
    margin:0 0 3px;background:linear-gradient(90deg,#fff 30%,#34d399 100%);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.reji-header p{margin:0;color:#2e5040;font-size:.75rem;}

.playlist-row{
    background:#0b0f1a;border:1px solid #131c2e;border-radius:9px;
    padding:10px 13px;margin:4px 0;transition:all .2s;position:relative;}
.playlist-row:hover{border-color:#10b981;}
.playlist-row.active-song{
    border-color:#10b981;background:#021409;
    box-shadow:0 0 12px rgba(16,185,129,.15);}
.playlist-row.has-anons{border-left:3px solid #f59e0b;}
.song-num{font-family:'JetBrains Mono',monospace;font-size:.65rem;
    color:#2e3f55;min-width:22px;display:inline-block;}
.song-title{font-family:'Syne',sans-serif;font-size:.82rem;font-weight:700;
    color:#dde2ee;}
.song-artist{font-size:.72rem;color:#3d4f68;margin-left:6px;}
.song-dur{font-family:'JetBrains Mono',monospace;font-size:.68rem;
    color:#2e3f55;margin-left:8px;}
.anons-badge{display:inline-block;font-size:.58rem;font-weight:700;
    letter-spacing:.08em;border-radius:4px;padding:1px 5px;margin-left:5px;}
.anons-badge.bas{background:#1a0d00;color:#f59e0b;border:1px solid #f59e0b44;}
.anons-badge.son{background:#000d1a;color:#60a5fa;border:1px solid #60a5fa44;}
.anons-badge.fon{background:#071a0f;color:#34d399;border:1px solid #34d39944;}

.timeline-block{
    background:#0b0f1a;border:1px solid #131c2e;border-radius:8px;
    padding:8px 12px;margin:3px 0;display:flex;align-items:center;gap:10px;}
.timeline-time{font-family:'JetBrains Mono',monospace;font-size:.72rem;
    color:#10b981;min-width:48px;}
.timeline-type{font-size:.62rem;font-weight:700;letter-spacing:.08em;
    text-transform:uppercase;padding:2px 7px;border-radius:4px;min-width:55px;text-align:center;}
.ttype-song{background:#071a2e;color:#60a5fa;border:1px solid #1a3a5e;}
.ttype-anons{background:#1a0d00;color:#f59e0b;border:1px solid #5e3a00;}
.ttype-fon{background:#071a0f;color:#34d399;border:1px solid #0a3d1f;}
.timeline-label{font-size:.78rem;color:#6b7a8d;flex:1;}
.timeline-dur{font-family:'JetBrains Mono',monospace;font-size:.65rem;color:#2e3f55;}

.broadcast-live{
    background:#021409;border:2px solid #10b981;border-radius:12px;
    padding:14px 18px;margin:10px 0;position:relative;}
.broadcast-live::before{content:'● CANLI';position:absolute;top:-9px;left:14px;
    background:#10b981;color:#000;font-family:'Syne',sans-serif;font-size:.58rem;
    font-weight:800;letter-spacing:.12em;padding:1px 8px;border-radius:4px;}
.now-playing{font-family:'Syne',sans-serif;font-size:1rem;font-weight:800;color:#34d399;}
.next-up{font-size:.75rem;color:#2e5040;margin-top:4px;}

hr{border-color:#101828 !important;margin:11px 0 !important;}
::-webkit-scrollbar{width:4px;height:4px;}
::-webkit-scrollbar-track{background:#07090f;}
::-webkit-scrollbar-thumb{background:#1a2436;border-radius:2px;}
::-webkit-scrollbar-thumb:hover{background:#3a7bd5;}

/* number input fix */
[data-testid="stNumberInput"] input{
    background:#090d18 !important;border:1px solid #131c2e !important;
    border-radius:8px !important;color:#dde2ee !important;}
[data-testid="stTimeInput"] input{
    background:#090d18 !important;border:1px solid #131c2e !important;
    border-radius:8px !important;color:#dde2ee !important;}
</style>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════
# SABİTLER
# ═════════════════════════════════════════════════════════════════
MAX_PER_KEY  = 10
MAX_ARCHIVE  = 50

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
    "es-ES":"🇪🇸 İspanyolca","it-IT":"🇮🇹 İtalyanca","pt-BR":"🇧🇷 PT-BR",
    "ru-RU":"🇷🇺 Rusça","ja-JP":"🇯🇵 Japonca","ko-KR":"🇰🇷 Korece",
    "zh-CN":"🇨🇳 Çince","ar-XA":"🇸🇦 Arapça","hi-IN":"🇮🇳 Hintçe",
    "nl-NL":"🇳🇱 Felemenkçe","pl-PL":"🇵🇱 Lehçe","sv-SE":"🇸🇪 İsveççe",
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
    "🎬 Belgesel Sesi":    "Derin belgesel anlatıcısı, ağır ve anlamlı tonla oku.",
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
        "[normal] Günün öne çıkan haberleriyle karşınızdayız.\n"
        "[seriously] Şimdi tüm ayrıntılarıyla...",
    "🎉 Yarışma":
        "[excitedly] BÜYÜK YARIŞMA BAŞLIYOR!\n"
        "[laughs] Hazır mısınız?\n"
        "[shouting] BU HAFTA kazanan sizin aranızdan çıkacak!\n"
        "[seriously] Hemen arayın... [excitedly] KAZANMA ŞANSI SIZIN!",
    "☀️ Öğle Bülteni":
        "[normal] İmaj FM Öğle Bülteni ile karşınızdayız.\n"
        "[seriously] Bugünün öne çıkan gelişmeleri...\n"
        "[normal] Haberlerden sonra müziğe devam.",
    "🌟 Program Tanıtım":
        "[excitedly] BU AKŞAM İmaj FM'de çok özel bir program!\n"
        "[whispers] Fısıltıyla söyleyelim... sürpriz konuklar var.\n"
        "[excitedly] Saat tam sekizde... SADECE İMAJ FM'DE!",
    # Delay Reji için yeni şablonlar
    "🎵 Şarkı Başı Anonsu":
        "[excitedly] Ve şimdi sizi muhteşem bir şarkıyla baş başa bırakıyoruz!\n"
        "[normal] İşte bu dakikanın en özel sesi...",
    "🎵 Şarkı Sonu Anonsu":
        "[normal] Dinlediğiniz şarkıydı... İmaj FM'de devam ediyoruz.\n"
        "[excitedly] Sıradaki sürpriz için kulaklarınız bizde kalsın!",
    "🎶 Fon Müzik Geçişi":
        "[whispers] Ve şimdi sayfamızı çeviriyoruz...\n"
        "[normal] İmaj FM, kesintisiz müzik ve haberlerle devam ediyor.",
}

ETAGS = [
    ("🔥","Coşkulu",   "[excitedly] ","#ff6b35"),
    ("🤫","Fısıltı",   "[whispers] ", "#a78bfa"),
    ("😄","Gülümseyen","[laughs] ",   "#34d399"),
    ("📰","Ciddi",     "[seriously] ","#60a5fa"),
    ("📢","Bağırma",   "[shouting] ", "#f59e0b"),
    ("😮‍💨","Yorgun",   "[sighs] ",    "#94a3b8"),
    ("🎙️","Normal",   "[normal] ",   "#cbd5e1"),
]

# Fon müzik geçiş türleri
FON_TIPLERI = {
    "🎵 Yumuşak Giriş":    "Müzik yavaşça yükseliyor, anons bitti, müzik normale dönüyor.",
    "🎶 Hızlı Kesim":       "Müzik aniden kesiliyor, anons yapılıyor, müzik geri geliyor.",
    "🌊 Dalgalı Geçiş":    "Müzik dalgalanarak düşüyor, anons, tekrar yükseliyor.",
    "📻 Radyo Klasik":      "Standart radyo fade-out, anons, fade-in.",
    "⚡ Enerji Geçişi":     "Müzik enerjik bir geçişle kesilip anons yapılıyor.",
}


# ═════════════════════════════════════════════════════════════════
# SESSION STATE
# ═════════════════════════════════════════════════════════════════
def _safe_init(key, val):
    if key not in st.session_state:
        st.session_state[key] = val

_safe_init("_archive", [])
_safe_init("_favorites", [])
_safe_init("_api_pool", [{"key":"","used":0,"label":f"API {i+1}"} for i in range(10)])
_safe_init("_active_idx", 0)
_safe_init("_secrets_loaded", False)
_safe_init("_api_stats", {"total_calls":0,"total_chars":0,"total_secs":0.0})
_safe_init("_giris", False)

# Metin buffer'ları
_safe_init("_t_tek",   "[excitedly] İmaj FM'e hoş geldiniz! BU GECE unutulmaz bir program var...\n[whispers] Sürprizler için kulaklarınız bizde olsun.\n[seriously] Şimdi haberlere geçiyoruz.")
_safe_init("_t_cift",  "Sunucu: [excitedly] İmaj FM'e hoş geldiniz!\nMisafir: [laughs] Teşekkürler, burada olmak harika!\nSunucu: [seriously] Haberler... [normal] Müziğe dönüyoruz.")
_safe_init("_t_split", "Sunucu: [excitedly] İmaj FM'e hoş geldiniz! BU GECE özel konuğumuz var...\nMisafir: [laughs] Teşekkürler! Burada olmak harika.\nSunucu: [seriously] Önce haberler... [normal] Müziğe dönüyoruz.\nMisafir: [whispers] Sürpriz için beklemeye devam edin!")
_safe_init("_t_bulk",  "İmaj FM sabah yayını başlıyor.\nHaber bülteni için bekleyiniz.\nMüzik programımıza hoş geldiniz.\nİyi dinlemeler dileriz.")
_safe_init("_t_ab1",   "[excitedly] İmaj FM'e hoş geldiniz!")
_safe_init("_t_ab2",   "[seriously] İmaj FM'e hoş geldiniz.")

# ── DELAY REJİ STATE ──────────────────────────────────────────
# Playlist: [{id, title, artist, duration_min, duration_sec, anons_bas, anons_son, anons_bas_text, anons_son_text, fon_tip, fon_aktif, anons_wav_bas, anons_wav_son, order}]
_safe_init("_playlist", [])
_safe_init("_reji_voice", "Kore")
_safe_init("_reji_model", "gemini-2.5-flash-tts")
_safe_init("_reji_lang", "tr-TR")
_safe_init("_reji_style", "")
_safe_init("_reji_baslangic_saat", "06:00")
_safe_init("_reji_plan_generated", False)
_safe_init("_reji_plan", [])          # Oluşturulan yayın planı timeline
_safe_init("_reji_active_song_idx", 0)


# ═════════════════════════════════════════════════════════════════
# API HAVUZU
# ═════════════════════════════════════════════════════════════════
def load_secrets_once():
    if st.session_state._secrets_loaded: return
    st.session_state._secrets_loaded = True
    for i in range(10):
        try:
            v = st.secrets.get(f"GEMINI_API_KEY_{i+1}","")
            if v and not st.session_state._api_pool[i]["key"]:
                st.session_state._api_pool[i]["key"] = v
        except Exception: pass

load_secrets_once()

def get_active_key():
    pool = st.session_state._api_pool
    idx  = st.session_state._active_idx
    for _ in range(10):
        s = pool[idx]
        if s["key"].strip() and s["used"] < MAX_PER_KEY:
            st.session_state._active_idx = idx
            return s["key"].strip(), idx
        idx = (idx+1)%10
    return None, -1

def consume(idx, chars=0):
    st.session_state._api_pool[idx]["used"] += 1
    st.session_state._api_stats["total_calls"] += 1
    st.session_state._api_stats["total_chars"] += chars
    if st.session_state._api_pool[idx]["used"] >= MAX_PER_KEY:
        st.session_state._active_idx = (idx+1)%10

def pool_stats():
    p = st.session_state._api_pool
    loaded  = sum(1 for s in p if s["key"].strip())
    used_t  = sum(s["used"] for s in p if s["key"].strip())
    remain  = sum(max(0,MAX_PER_KEY-s["used"]) for s in p if s["key"].strip())
    return loaded, used_t, remain


# ═════════════════════════════════════════════════════════════════
# ARŞİV
# ═════════════════════════════════════════════════════════════════
def archive_add(voice, model, lang, style, text, wav_bytes, mode="tek"):
    dur  = len(wav_bytes) / (24000*2)
    uid  = hashlib.md5((text+voice+str(time.time())).encode()).hexdigest()[:10]
    entry = {
        "id":    uid,
        "ts":    datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "ts_short": datetime.datetime.now().strftime("%d.%m %H:%M"),
        "voice": voice, "model": model,
        "model_short": model.replace("gemini-","").replace("-preview","").replace("-tts",""),
        "lang":  lang, "style": style[:40] if style else "",
        "text":  text,
        "preview": text[:70].replace("\n"," ") + ("…" if len(text)>70 else ""),
        "wav":   wav_bytes,
        "dur":   round(dur,1), "size":  len(wav_bytes), "mode":  mode,
    }
    st.session_state._archive.insert(0, entry)
    if len(st.session_state._archive) > MAX_ARCHIVE:
        st.session_state._archive = st.session_state._archive[:MAX_ARCHIVE]
    st.session_state._api_stats["total_secs"] += dur


# ═════════════════════════════════════════════════════════════════
# AUDIO
# ═════════════════════════════════════════════════════════════════
def pcm2wav(pcm:bytes,rate=24000,ch=1,sw=2)->bytes:
    buf=io.BytesIO()
    with wave.open(buf,"wb") as wf:
        wf.setnchannels(ch);wf.setsampwidth(sw);wf.setframerate(rate)
        wf.writeframes(pcm)
    return buf.getvalue()

def tts_single(api_key,model,text,voice,lang,style)->bytes:
    full=f"{style}\n\n{text}" if style.strip() else text
    lc=lang if lang!="otomatik" else None
    c=genai.Client(api_key=api_key)
    r=c.models.generate_content(
        model=model,contents=full,
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

def tts_multi(api_key,model,text,sp1,v1,sp2,v2,lang)->bytes:
    lc=lang if lang!="otomatik" else None
    c=genai.Client(api_key=api_key)
    r=c.models.generate_content(
        model=model,contents=text,
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


# ═════════════════════════════════════════════════════════════════
# DELAY REJİ YARDIMCI FONKSİYONLAR
# ═════════════════════════════════════════════════════════════════
def song_uid():
    return hashlib.md5(str(time.time()+id({})).encode()).hexdigest()[:8]

def total_dur_sec(song):
    return song.get("duration_min",3)*60 + song.get("duration_sec",30)

def format_dur(secs):
    m = secs // 60
    s = secs % 60
    return f"{m}:{s:02d}"

def add_time(base_str, secs):
    """'HH:MM' formatındaki saate saniye ekle, yeni 'HH:MM:SS' döner"""
    try:
        parts = base_str.split(":")
        h,m = int(parts[0]),int(parts[1])
    except:
        h,m = 6,0
    total = h*3600 + m*60 + secs
    hh = (total // 3600) % 24
    mm = (total % 3600) // 60
    ss = total % 60
    return f"{hh:02d}:{mm:02d}:{ss:02d}"

def generate_anons_text_bas(song):
    """Şarkı başı için otomatik anons metni oluştur"""
    title  = song.get("title","Bilinmeyen Şarkı")
    artist = song.get("artist","Bilinmeyen Sanatçı")
    return (f"[excitedly] Ve şimdi İmaj FM'de... {artist}! "
            f"[normal] '{title}' dinleyicilerimizle buluşuyor. "
            f"[whispers] Keyfini çıkarın...")

def generate_anons_text_son(song):
    """Şarkı sonu için otomatik anons metni oluştur"""
    title  = song.get("title","Bilinmeyen Şarkı")
    artist = song.get("artist","Bilinmeyen Sanatçı")
    return (f"[normal] Dinlediğiniz... {artist} ve '{title}' idi. "
            f"[excitedly] İmaj FM'de devam ediyoruz!")

def build_yayın_plani(playlist, baslangic_str):
    """
    Playlist'ten timeline (yayın planı) oluşturur.
    Her şarkı için: (opsiyonel) şarkı-başı anons → şarkı → (opsiyonel) şarkı-sonu anons
    Fon müzik geçişi varsa ek zaman eklenir.
    Döner: [{time, type, label, duration_sec, song_id, wav}]
    """
    plan = []
    cursor = 0  # saniye cinsinden offset

    for song in playlist:
        sid = song["id"]
        song_dur = total_dur_sec(song)
        fon_aktif = song.get("fon_aktif", False)
        fon_ekstra = 8 if fon_aktif else 0  # fon geçişi için ekstra süre tahmini

        # --- Şarkı başı anons ---
        if song.get("anons_bas", False):
            anons_text = song.get("anons_bas_text", generate_anons_text_bas(song))
            anons_dur = max(5, len(anons_text) // 15)  # tahmini süre
            plan.append({
                "time": add_time(baslangic_str, cursor),
                "time_offset": cursor,
                "type": "anons_bas",
                "label": f"🎙️ Anons (Başı) → {song.get('title','?')}",
                "sublabel": anons_text[:55] + ("…" if len(anons_text)>55 else ""),
                "duration_sec": anons_dur,
                "song_id": sid,
                "wav": song.get("anons_wav_bas"),
                "text": anons_text,
            })
            cursor += anons_dur

        # --- Fon müzik geçişi başı ---
        if fon_aktif:
            plan.append({
                "time": add_time(baslangic_str, cursor),
                "time_offset": cursor,
                "type": "fon",
                "label": f"🎶 Fon Geçiş → {song.get('title','?')} [{song.get('fon_tip','Radyo Klasik')}]",
                "sublabel": FON_TIPLERI.get(song.get("fon_tip","📻 Radyo Klasik"),"")[:55],
                "duration_sec": 4,
                "song_id": sid,
                "wav": None,
                "text": "",
            })
            cursor += 4

        # --- Şarkı ---
        plan.append({
            "time": add_time(baslangic_str, cursor),
            "time_offset": cursor,
            "type": "song",
            "label": f"🎵 {song.get('artist','?')} — {song.get('title','?')}",
            "sublabel": f"{format_dur(song_dur)}",
            "duration_sec": song_dur,
            "song_id": sid,
            "wav": None,
            "text": "",
        })
        cursor += song_dur

        # --- Şarkı sonu anons ---
        if song.get("anons_son", False):
            anons_text = song.get("anons_son_text", generate_anons_text_son(song))
            anons_dur = max(4, len(anons_text) // 15)
            plan.append({
                "time": add_time(baslangic_str, cursor),
                "time_offset": cursor,
                "type": "anons_son",
                "label": f"🎙️ Anons (Sonu) ← {song.get('title','?')}",
                "sublabel": anons_text[:55] + ("…" if len(anons_text)>55 else ""),
                "duration_sec": anons_dur,
                "song_id": sid,
                "wav": song.get("anons_wav_son"),
                "text": anons_text,
            })
            cursor += anons_dur

    return plan


# ═════════════════════════════════════════════════════════════════
# YARDIMCI UI
# ═════════════════════════════════════════════════════════════════
def text_stats_bar(text:str, key_prefix:str=""):
    cc  = len(text)
    wc  = len(text.split())
    sc  = max(1, text.count(".")+text.count("!")+text.count("?"))
    est = max(1, cc/17)
    st.markdown(
        f"<div style='font-size:.68rem;color:#2e3f55;margin:3px 0 8px;'>"
        f"📊 {cc} karakter · {wc} kelime · {sc} cümle · ~{est:.0f}s tahmini süre</div>",
        unsafe_allow_html=True)

def tag_buttons(state_key:str, prefix:str):
    cols = st.columns(len(ETAGS))
    for i,(em,lbl,tag,col) in enumerate(ETAGS):
        with cols[i]:
            if st.button(em, key=f"{prefix}_et_{i}", help=f"{lbl}: {tag.strip()}",
                         use_container_width=True):
                st.session_state[state_key] += tag
                st.rerun()

def style_widget(prefix:str) -> str:
    ps = st.selectbox("Preset", list(STYLE_PRESETS.keys()),
                      label_visibility="collapsed", key=f"{prefix}_ps")
    pval = STYLE_PRESETS[ps]
    ca,cb = st.columns(2)
    with ca:
        st.markdown("<div style='font-size:.65rem;color:#3b82f6;margin-bottom:3px;'>🇹🇷 Türkçe</div>",unsafe_allow_html=True)
        tr_ = st.text_area("TR",value=pval,height=62,label_visibility="collapsed",
                            placeholder="Coşkulu oku...",key=f"{prefix}_str")
    with cb:
        st.markdown("<div style='font-size:.65rem;color:#f59e0b;margin-bottom:3px;'>🇬🇧 English</div>",unsafe_allow_html=True)
        en_ = st.text_area("EN",value="",height=62,label_visibility="collapsed",
                            placeholder="Read excited...",key=f"{prefix}_sen")
    return " / ".join(filter(None,[tr_.strip(),en_.strip()]))

def result_card(wav:bytes, raw:bytes, voice:str, api_idx:int, dl_key:str, dl_name:str):
    dur=len(raw)/(24000*2)
    st.markdown(f"<div class='card g'>✅  Tamamlandı &nbsp;·&nbsp; {VOICES[voice][0]} {voice} &nbsp;·&nbsp; API {api_idx+1} &nbsp;·&nbsp; {dur:.1f}s &nbsp;·&nbsp; {len(wav):,} byte</div>",
                unsafe_allow_html=True)
    st.audio(wav,format="audio/wav")
    st.download_button("💾 WAV İndir",wav,file_name=dl_name,
                       mime="audio/wav",use_container_width=True,key=dl_key)


# ═════════════════════════════════════════════════════════════════
# GİRİŞ
# ═════════════════════════════════════════════════════════════════
def login():
    _,col,_ = st.columns([1,1.05,1])
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
                TTS STÜDYO v5 · GÜVENLİ GİRİŞ
            </p>
        </div>""",unsafe_allow_html=True)
        u=st.text_input("u","",placeholder="👤  kullanıcı adı",label_visibility="collapsed")
        p=st.text_input("p","",type="password",placeholder="🔑  şifre",label_visibility="collapsed")
        if st.button("Stüdyoya Bağlan →",type="primary",use_container_width=True):
            if u=="kenan" and p=="imajfm":
                st.session_state._giris=True; st.rerun()
            else: st.error("❌ Hatalı giriş.")

if not st.session_state._giris:
    login(); st.stop()


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
        <span style='font-size:.62rem;color:#2e3f55;letter-spacing:.1em;'>  TTS v5</span>
    </div>
    """,unsafe_allow_html=True)

    ak_sb, ai_sb = get_active_key()
    tk_sb, tu_sb, tr_sb = pool_stats()

    if ak_sb:
        used_act = st.session_state._api_pool[ai_sb]["used"]
        rem_act  = MAX_PER_KEY - used_act
        pct_act  = used_act/MAX_PER_KEY
        bc_act   = "#22c55e" if pct_act<.6 else ("#f59e0b" if pct_act<.9 else "#ef4444")
    else:
        rem_act=0; pct_act=1; bc_act="#ef4444"

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
                <div style='font-size:.61rem;color:#2e3f55;margin-top:2px;'>Otomatik rotasyon · Dolan API atlanır</div>
            </div>
            """,unsafe_allow_html=True)
        else:
            st.markdown("<div class='card r'>⛔ API yok! Aşağıdan ekleyin.</div>",unsafe_allow_html=True)

        with st.expander("📋 Secrets.toml Formatı",expanded=False):
            st.code("GEMINI_API_KEY_1  = \"AIza...\"\nGEMINI_API_KEY_2  = \"AIza...\"\n...",language="toml")

        st.markdown("<span class='sl2'>▸ 10 API SLOTU</span>",unsafe_allow_html=True)
        for i in range(10):
            slot=st.session_state._api_pool[i]
            used=slot["used"]; has=bool(slot["key"].strip())
            full=has and used>=MAX_PER_KEY
            warn=has and used>=int(MAX_PER_KEY*.6) and not full
            is_ac=(i==st.session_state._active_idx) and has and not full
            lbl=slot.get("label",f"API {i+1}")
            if not has: icon="⬜"; badge="boş"
            elif full:  icon="🔴"; badge="DOLU"
            elif warn:  icon="🟡"; badge=f"{used}/{MAX_PER_KEY}"
            else:       icon="🟢"; badge=f"{used}/{MAX_PER_KEY}"
            act_m=" ◀" if is_ac else ""

            with st.expander(f"{icon} {lbl}{act_m}  ·  {badge}",expanded=False):
                nl=st.text_input(f"İsim{i}",value=lbl,placeholder=f"API {i+1}",
                                  label_visibility="collapsed",key=f"lbl_{i}")
                if nl!=lbl: st.session_state._api_pool[i]["label"]=nl; st.rerun()
                nk=st.text_input(f"Key{i}",value=slot["key"],type="password",
                                  placeholder="AIzaSy...",label_visibility="collapsed",key=f"key_{i}")
                if nk!=slot["key"]: st.session_state._api_pool[i]["key"]=nk; st.rerun()
                if has:
                    p2=min(used/MAX_PER_KEY,1); b2="#22c55e" if p2<.6 else ("#f59e0b" if p2<.9 else "#ef4444")
                    st.markdown(f"<div class='qbar'><div class='qbar-f' style='width:{p2*100:.0f}%;background:{b2};'></div></div><div style='font-size:.62rem;color:#2e3f55;'>{used}/{MAX_PER_KEY} · {MAX_PER_KEY-used} kalan</div>",unsafe_allow_html=True)
                k1,k2,k3=st.columns(3)
                with k1:
                    if st.button("🔄",key=f"rst_{i}",help="Sıfırla",use_container_width=True):
                        st.session_state._api_pool[i]["used"]=0; st.rerun()
                with k2:
                    if st.button("▶",key=f"act_{i}",help="Aktif yap",use_container_width=True):
                        st.session_state._active_idx=i; st.rerun()
                with k3:
                    if st.button("🗑️",key=f"del_{i}",help="Sil",use_container_width=True):
                        st.session_state._api_pool[i]={"key":"","used":0,"label":f"API {i+1}"}; st.rerun()

    with st.expander("🎭  Duygu Etiketleri",expanded=False):
        st.markdown("""
        <table class='ttbl'>
        <thead><tr><th>Etiket</th><th>TR</th><th>EN</th></tr></thead>
        <tbody>
        <tr><td><span class='tc'>[excitedly]</span></td><td>Coşkulu, hızlı</td><td class='ten'>Excited</td></tr>
        <tr><td><span class='tc'>[whispers]</span></td><td>Fısıltı, gece tonu</td><td class='ten'>Whisper</td></tr>
        <tr><td><span class='tc'>[laughs]</span></td><td>Gülümseyen, sıcak</td><td class='ten'>Smiling</td></tr>
        <tr><td><span class='tc'>[seriously]</span></td><td>Ciddi, haber tonu</td><td class='ten'>News anchor</td></tr>
        <tr><td><span class='tc'>[shouting]</span></td><td>Bağırma, enerji</td><td class='ten'>Loud shout</td></tr>
        <tr><td><span class='tc'>[sighs]</span></td><td>Yorgun, nefes</td><td class='ten'>Tired sigh</td></tr>
        <tr><td><span class='tc'>[normal]</span></td><td>Standart tona dön</td><td class='ten'>Normal</td></tr>
        </tbody></table>
        """,unsafe_allow_html=True)

    # Delay Reji hızlı özet
    pl_count = len(st.session_state._playlist)
    with st.expander(f"📻  Delay Reji  ·  {pl_count} şarkı",expanded=False):
        if not st.session_state._playlist:
            st.caption("Playlist boş. Delay Reji sekmesinden şarkı ekleyin.")
        else:
            for i,s in enumerate(st.session_state._playlist[:5]):
                badges = ""
                if s.get("anons_bas"): badges += "🎙️B "
                if s.get("anons_son"): badges += "🎙️S "
                if s.get("fon_aktif"): badges += "🎶 "
                st.markdown(f"<div style='font-size:.7rem;color:#3d4f68;padding:3px 0;border-bottom:1px solid #0d1420;'>{i+1}. <b style='color:#60a5fa;'>{s.get('title','?')[:20]}</b> {badges}</div>",unsafe_allow_html=True)
            if pl_count>5:
                st.caption(f"+{pl_count-5} daha — Delay Reji sekmesinde")

    arc_count = len(st.session_state._archive)
    total_secs = st.session_state._api_stats["total_secs"]
    with st.expander(f"📂  Arşiv  ·  {arc_count} kayıt  ·  {total_secs:.0f}s",expanded=False):
        if not st.session_state._archive:
            st.caption("Henüz kayıt yok.")
        else:
            for h in st.session_state._archive[:5]:
                st.markdown(f"<div style='font-size:.7rem;color:#3d4f68;padding:3px 0;border-bottom:1px solid #0d1420;'>{h['ts_short']} · <b style='color:#60a5fa;'>{h['voice']}</b> · {h['dur']}s</div>",unsafe_allow_html=True)

    fav_count = len(st.session_state._favorites)
    with st.expander(f"⭐  Favoriler  ·  {fav_count} metin",expanded=False):
        if not st.session_state._favorites:
            st.caption("Favori metin yok.")
        else:
            for fv in st.session_state._favorites:
                st.markdown(f"<div class='fav-card'><div class='fav-name'>⭐ {fv['name']}</div><div class='fav-prev'>{fv['text'][:55]}</div></div>",unsafe_allow_html=True)

    st.markdown("<hr>",unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;color:#101828;font-size:.62rem;'>İmaj FM v5 · 2026</div>",unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════
# ANA SAYFA — HEADER
# ═════════════════════════════════════════════════════════════════
st.markdown("""
<div class='hdr'>
    <h1>🎙️ İmaj FM · Seslendirme Stüdyosu</h1>
    <p><span class='ldot'></span>Gemini TTS v5 &nbsp;·&nbsp; Delay Reji &nbsp;·&nbsp; 30 Ses &nbsp;·&nbsp; Kalıcı Arşiv &nbsp;·&nbsp; A/B Test &nbsp;·&nbsp; Toplu &nbsp;·&nbsp; Şablonlar</p>
</div>
""",unsafe_allow_html=True)

tk_m,tu_m,tr_m = pool_stats()
ak_m,ai_m = get_active_key()
rem_m  = MAX_PER_KEY-st.session_state._api_pool[ai_m]["used"] if ai_m>=0 else 0
arc_m  = len(st.session_state._archive)
pl_m   = len(st.session_state._playlist)
stat_m = st.session_state._api_stats
total_calls = stat_m["total_calls"]
total_secs2 = stat_m["total_secs"]

cols7 = st.columns(7)
defs7 = [
    ("30",              "Ses"),
    (f"{tk_m}/10",      "API Yüklü","g"),
    (f"{tr_m}",         "Kalan İstek","a"),
    (f"{arc_m}",        "Arşiv","b"),
    (f"{total_calls}",  "Toplam İstek"),
    (f"{total_secs2:.0f}s","Üretilen Ses","p"),
    (f"{pl_m}",         "Playlist","t"),
]
for col7,(val,lbl,*cls) in zip(cols7,defs7):
    c = cls[0] if cls else ""
    with col7:
        st.markdown(f'<div class="mbox {c}"><div class="v">{val}</div><div class="l">{lbl}</div></div>',unsafe_allow_html=True)

st.markdown("<br>",unsafe_allow_html=True)

if ak_m is None:
    st.error("⛔ Kullanılabilir API anahtarı yok! Sol panelden ekleyin.")
    st.stop()
elif rem_m <= 2:
    st.warning(f"⚠️ API {ai_m+1} limitine yakın ({rem_m} kaldı). Otomatik rotasyon devreye girecek.")


# ═════════════════════════════════════════════════════════════════
# SEKMELER
# ═════════════════════════════════════════════════════════════════
t1,t2,t3,t4,t5,t6,t7,t8 = st.tabs([
    "🎤  Tek",
    "🎭  Çift",
    "🎬  Ayrı Ses",
    "📦  Toplu",
    "🔬  A/B Test",
    "⭐  Favoriler",
    "📂  Arşiv",
    "📻  Delay Reji",
])


# ══════════════════════════════════════════════════════════════════
# TAB 1 — TEK KONUŞMACI
# ══════════════════════════════════════════════════════════════════
with t1:
    cL,cR = st.columns([1.05,1],gap="large")
    with cL:
        st.markdown("<span class='sl'>▶ Şablon</span>",unsafe_allow_html=True)
        tmpl1 = st.selectbox("Ş1",["— Yok —"]+list(TEMPLATES.keys()),
                              label_visibility="collapsed",key="tmpl1")
        if tmpl1!="— Yok —" and st.button("📥 Yükle",key="ltmpl1"):
            st.session_state._t_tek = TEMPLATES[tmpl1]; st.rerun()

        st.markdown("<span class='sl'>▶ Model</span>",unsafe_allow_html=True)
        m1l = st.selectbox("M1",list(MODELS.values()),label_visibility="collapsed",key="m1")
        mdl1= [k for k,v in MODELS.items() if v==m1l][0]

        st.markdown("<span class='sl'>▶ Dil</span>",unsafe_allow_html=True)
        l1l = st.selectbox("L1",list(LANGUAGES.values()),label_visibility="collapsed",index=1,key="l1")
        lng1= [k for k,v in LANGUAGES.items() if v==l1l][0]

        st.markdown("<span class='sl'>▶ Ses Karakteri</span>",unsafe_allow_html=True)
        cn1 = st.radio("CN1",["Tümü","♀ Kadın","♂ Erkek"],horizontal=True,
                        label_visibility="collapsed",key="cn1")
        f1  = {k:v for k,v in VOICES.items()
               if cn1=="Tümü" or (cn1=="♀ Kadın" and v[0]=="♀") or (cn1=="♂ Erkek" and v[0]=="♂")}
        vc1 = st.selectbox("V1",list(f1.keys()),
                            format_func=lambda x:f"{VOICES[x][0]} {x}  —  {VOICES[x][1]}",
                            label_visibility="collapsed",key="v1")

        st.markdown("<span class='sl'>▶ Duygu & Stil</span>",unsafe_allow_html=True)
        sty1 = style_widget("t1")

        ak1,ai1 = get_active_key()
        r1 = MAX_PER_KEY-st.session_state._api_pool[ai1]["used"] if ai1>=0 else 0
        st.markdown(f"""<div class='card b'>
            <b>{VOICES[vc1][0]} {vc1}</b> — {VOICES[vc1][1]}<br>
            <span style='color:#3a7bd5;'>Model:</span> {m1l[:22]}&nbsp;
            <span style='color:#22c55e;'>API {ai1+1}</span> · {r1} kalan
        </div>""",unsafe_allow_html=True)

        st.markdown("<span class='sl'>▶ Favorilere Ekle</span>",unsafe_allow_html=True)
        fa,fb=st.columns([2,1])
        with fa:
            fname=st.text_input("FN","",placeholder="Favori ismi...",
                                 label_visibility="collapsed",key="fname1")
        with fb:
            if st.button("⭐ Ekle",key="fadd1",use_container_width=True):
                if fname.strip() and st.session_state._t_tek.strip():
                    st.session_state._favorites.append({
                        "id":  hashlib.md5((fname+str(time.time())).encode()).hexdigest()[:8],
                        "name": fname.strip(),
                        "text": st.session_state._t_tek,
                        "voice": vc1, "model": mdl1, "lang": lng1,
                    })
                    st.success("⭐ Eklendi!"); time.sleep(0.5); st.rerun()

    with cR:
        st.markdown("<span class='sl'>▶ Anons Metni</span>",unsafe_allow_html=True)
        tag_buttons("_t_tek","t1")
        txt1=st.text_area("TT1",value=st.session_state._t_tek,height=230,
                           label_visibility="collapsed",key="ta1",
                           placeholder="Metni buraya yazın…")
        st.session_state._t_tek=txt1
        text_stats_bar(txt1,"t1")

        if st.button(f"🔴  {vc1} ile Seslendir",type="primary",use_container_width=True,key="btn1"):
            if not txt1.strip(): st.warning("⚠️ Metin boş.")
            else:
                ak1,ai1=get_active_key()
                if ak1 is None: st.error("❌ API kalmadı!")
                else:
                    with st.spinner(f"🎙️  {vc1}…  [API {ai1+1}]"):
                        try:
                            raw=tts_single(ak1,mdl1,txt1,vc1,lng1,sty1)
                            wav=pcm2wav(raw)
                            consume(ai1,len(txt1))
                            archive_add(vc1,mdl1,lng1,sty1,txt1,wav,"tek")
                            result_card(wav,raw,vc1,ai1,"dl1",f"imajfm_{vc1.lower()}_{lng1}.wav")
                        except Exception as e: st.error(f"❌ {e}")


# ══════════════════════════════════════════════════════════════════
# TAB 2 — ÇİFT KONUŞMACI
# ══════════════════════════════════════════════════════════════════
with t2:
    cL2,cR2=st.columns([1.05,1],gap="large")
    with cL2:
        tmpl2=st.selectbox("Ş2",["— Yok —"]+list(TEMPLATES.keys()),
                            label_visibility="collapsed",key="tmpl2")
        if tmpl2!="— Yok —" and st.button("📥 Yükle",key="ltmpl2"):
            st.session_state._t_cift=TEMPLATES[tmpl2]; st.rerun()

        st.markdown("<span class='sl'>▶ Model</span>",unsafe_allow_html=True)
        m2l=st.selectbox("M2",list(MODELS.values()),label_visibility="collapsed",key="m2")
        mdl2=[k for k,v in MODELS.items() if v==m2l][0]

        st.markdown("<span class='sl'>▶ Dil</span>",unsafe_allow_html=True)
        l2l=st.selectbox("L2",list(LANGUAGES.values()),label_visibility="collapsed",index=1,key="l2")
        lng2=[k for k,v in LANGUAGES.items() if v==l2l][0]

        st.markdown("<span class='sl'>▶ Konuşmacı 1</span>",unsafe_allow_html=True)
        ca,cb=st.columns([1,2])
        with ca: sp1n=st.text_input("S1N","Sunucu",label_visibility="collapsed",key="sp1n")
        with cb: sp1v=st.selectbox("S1V",list(VOICES.keys()),
                                    format_func=lambda x:f"{VOICES[x][0]} {x} — {VOICES[x][1]}",
                                    label_visibility="collapsed",
                                    index=list(VOICES.keys()).index("Kore"),key="sp1v")

        st.markdown("<span class='sl'>▶ Konuşmacı 2</span>",unsafe_allow_html=True)
        cc,cd=st.columns([1,2])
        with cc: sp2n=st.text_input("S2N","Misafir",label_visibility="collapsed",key="sp2n")
        with cd: sp2v=st.selectbox("S2V",list(VOICES.keys()),
                                    format_func=lambda x:f"{VOICES[x][0]} {x} — {VOICES[x][1]}",
                                    label_visibility="collapsed",
                                    index=list(VOICES.keys()).index("Fenrir"),key="sp2v")

        ak2,ai2=get_active_key()
        r2=MAX_PER_KEY-st.session_state._api_pool[ai2]["used"] if ai2>=0 else 0
        st.markdown(f"""<div class='card b'>
            <code style='color:#60a5fa;'>{sp1n}</code> → <b>{VOICES[sp1v][0]} {sp1v}</b><br>
            <code style='color:#f87171;'>{sp2n}</code> → <b>{VOICES[sp2v][0]} {sp2v}</b><br>
            <span style='color:#22c55e;'>API {ai2+1}</span> · {r2} kalan · Tek WAV
        </div>""",unsafe_allow_html=True)

    with cR2:
        st.markdown("<span class='sl'>▶ Diyalog Metni</span>",unsafe_allow_html=True)
        tag_buttons("_t_cift","t2")
        txt2=st.text_area("TT2",value=st.session_state._t_cift,height=230,
                           label_visibility="collapsed",key="ta2",
                           placeholder=f"{sp1n}: [excitedly] ...\n{sp2n}: [laughs] ...")
        st.session_state._t_cift=txt2
        text_stats_bar(txt2,"t2")

        if st.button(f"🔴  {sp1n} & {sp2n} — Diyalog Seslendir",type="primary",
                     use_container_width=True,key="btn2"):
            if not txt2.strip(): st.warning("⚠️ Metin boş.")
            else:
                ak2,ai2=get_active_key()
                if ak2 is None: st.error("❌ API kalmadı!")
                else:
                    with st.spinner(f"🎭  Diyalog…  [API {ai2+1}]"):
                        try:
                            raw2=tts_multi(ak2,mdl2,txt2,sp1n,sp1v,sp2n,sp2v,lng2)
                            wav2=pcm2wav(raw2)
                            consume(ai2,len(txt2))
                            archive_add(f"{sp1v}+{sp2v}",mdl2,lng2,"",txt2,wav2,"cift")
                            result_card(wav2,raw2,sp1v,ai2,"dl2",f"imajfm_diyalog_{sp1v.lower()}_{sp2v.lower()}.wav")
                        except Exception as e: st.error(f"❌ {e}")


# ══════════════════════════════════════════════════════════════════
# TAB 3 — AYRI SES
# ══════════════════════════════════════════════════════════════════
with t3:
    st.markdown("<div class='card b' style='margin-bottom:12px;'><b>🎬 Ayrı Ses</b> — Her konuşmacı ayrı API çağrısı, ayrı WAV. ZIP ile indirilir.</div>",unsafe_allow_html=True)
    cL3,cR3=st.columns([1.05,1],gap="large")

    with cL3:
        st.markdown("<span class='sl'>▶ Model / Dil</span>",unsafe_allow_html=True)
        m3l=st.selectbox("M3",list(MODELS.values()),label_visibility="collapsed",key="m3")
        mdl3=[k for k,v in MODELS.items() if v==m3l][0]
        l3l=st.selectbox("L3",list(LANGUAGES.values()),label_visibility="collapsed",index=1,key="l3")
        lng3=[k for k,v in LANGUAGES.items() if v==l3l][0]

        st.markdown("<span class='sl'>▶ Konuşmacı 1</span>",unsafe_allow_html=True)
        ce,cf=st.columns([1,2])
        with ce: sp1n3=st.text_input("S1N3","Sunucu",label_visibility="collapsed",key="sp1n3")
        with cf: sp1v3=st.selectbox("S1V3",list(VOICES.keys()),
                                     format_func=lambda x:f"{VOICES[x][0]} {x} — {VOICES[x][1]}",
                                     label_visibility="collapsed",
                                     index=list(VOICES.keys()).index("Kore"),key="sp1v3")

        st.markdown("<span class='sl'>▶ Konuşmacı 2</span>",unsafe_allow_html=True)
        cg,ch=st.columns([1,2])
        with cg: sp2n3=st.text_input("S2N3","Misafir",label_visibility="collapsed",key="sp2n3")
        with ch: sp2v3=st.selectbox("S2V3",list(VOICES.keys()),
                                     format_func=lambda x:f"{VOICES[x][0]} {x} — {VOICES[x][1]}",
                                     label_visibility="collapsed",
                                     index=list(VOICES.keys()).index("Fenrir"),key="sp2v3")

    with cR3:
        st.markdown("<span class='sl'>▶ Diyalog Metni</span>",unsafe_allow_html=True)
        tag_buttons("_t_split","t3")
        txt3=st.text_area("TT3",value=st.session_state._t_split,height=230,
                           label_visibility="collapsed",key="ta3")
        st.session_state._t_split=txt3

        lines3=[l.strip() for l in txt3.splitlines() if l.strip()]
        c1l=[l for l in lines3 if l.lower().startswith(sp1n3.lower()+":")]
        c2l=[l for l in lines3 if l.lower().startswith(sp2n3.lower()+":")]
        st.markdown(f"<div style='font-size:.68rem;color:#2e3f55;margin:3px 0 8px;'>{sp1n3}: {len(c1l)} satır &nbsp;·&nbsp; {sp2n3}: {len(c2l)} satır</div>",unsafe_allow_html=True)

        if st.button("🔴  Ayrı Ses Üret",type="primary",use_container_width=True,key="btn3"):
            if not c1l and not c2l:
                st.warning(f"⚠️ '{sp1n3}:' veya '{sp2n3}:' satırı bulunamadı.")
            else:
                wav3a=wav3b=raw3a=raw3b=None
                err3a=err3b=None
                if c1l:
                    ak3a,ai3a=get_active_key()
                    if ak3a:
                        with st.spinner(f"🎤 {sp1n3} ({sp1v3})… [API {ai3a+1}]"):
                            try:
                                t3a=" ".join(l[len(sp1n3)+1:].strip() for l in c1l)
                                raw3a=tts_single(ak3a,mdl3,t3a,sp1v3,lng3,"")
                                wav3a=pcm2wav(raw3a); consume(ai3a,len(t3a))
                                archive_add(sp1v3,mdl3,lng3,"",t3a,wav3a,"split")
                            except Exception as e: err3a=str(e)
                if c2l:
                    ak3b,ai3b=get_active_key()
                    if ak3b:
                        with st.spinner(f"🎤 {sp2n3} ({sp2v3})… [API {ai3b+1}]"):
                            try:
                                t3b=" ".join(l[len(sp2n3)+1:].strip() for l in c2l)
                                raw3b=tts_single(ak3b,mdl3,t3b,sp2v3,lng3,"")
                                wav3b=pcm2wav(raw3b); consume(ai3b,len(t3b))
                                archive_add(sp2v3,mdl3,lng3,"",t3b,wav3b,"split")
                            except Exception as e: err3b=str(e)

                st.markdown("---")
                r3a,r3b=st.columns(2)
                with r3a:
                    st.markdown(f"<div style='font-family:Syne,sans-serif;font-size:.7rem;font-weight:700;color:#60a5fa;letter-spacing:.12em;text-transform:uppercase;margin-bottom:6px;'>🎤 {sp1n3} · {sp1v3}</div>",unsafe_allow_html=True)
                    if wav3a:
                        d3a=len(raw3a)/(24000*2)
                        st.markdown(f"<div class='card g'>✅ {len(c1l)} satır · {d3a:.1f}s</div>",unsafe_allow_html=True)
                        st.audio(wav3a,format="audio/wav")
                        st.download_button(f"💾 {sp1n3}",wav3a,file_name=f"imajfm_{sp1n3.lower()}_{sp1v3.lower()}.wav",mime="audio/wav",use_container_width=True,key="dl3a")
                    elif err3a: st.error(f"❌ {err3a}")
                    else: st.info("Satır bulunamadı.")
                with r3b:
                    st.markdown(f"<div style='font-family:Syne,sans-serif;font-size:.7rem;font-weight:700;color:#f87171;letter-spacing:.12em;text-transform:uppercase;margin-bottom:6px;'>🎤 {sp2n3} · {sp2v3}</div>",unsafe_allow_html=True)
                    if wav3b:
                        d3b=len(raw3b)/(24000*2)
                        st.markdown(f"<div class='card g'>✅ {len(c2l)} satır · {d3b:.1f}s</div>",unsafe_allow_html=True)
                        st.audio(wav3b,format="audio/wav")
                        st.download_button(f"💾 {sp2n3}",wav3b,file_name=f"imajfm_{sp2n3.lower()}_{sp2v3.lower()}.wav",mime="audio/wav",use_container_width=True,key="dl3b")
                    elif err3b: st.error(f"❌ {err3b}")
                    else: st.info("Satır bulunamadı.")

                if wav3a and wav3b:
                    zb=io.BytesIO()
                    with zipfile.ZipFile(zb,"w",zipfile.ZIP_DEFLATED) as zf:
                        zf.writestr(f"{sp1n3}_{sp1v3}.wav",wav3a)
                        zf.writestr(f"{sp2n3}_{sp2v3}.wav",wav3b)
                    st.download_button("📦 İkisini ZIP İndir",zb.getvalue(),file_name="imajfm_split.zip",mime="application/zip",use_container_width=True,key="dl3zip")


# ══════════════════════════════════════════════════════════════════
# TAB 4 — TOPLU SESLENDİRME
# ══════════════════════════════════════════════════════════════════
with t4:
    st.markdown("<div class='card b' style='margin-bottom:12px;'><b>📦 Toplu Seslendirme</b> — Her satır ayrı WAV. Tümü ZIP olarak indirilir.</div>",unsafe_allow_html=True)
    cL4,cR4=st.columns([1,1.2],gap="large")

    with cL4:
        st.markdown("<span class='sl'>▶ Model / Dil</span>",unsafe_allow_html=True)
        m4l=st.selectbox("M4",list(MODELS.values()),label_visibility="collapsed",key="m4")
        mdl4=[k for k,v in MODELS.items() if v==m4l][0]
        l4l=st.selectbox("L4",list(LANGUAGES.values()),label_visibility="collapsed",index=1,key="l4")
        lng4=[k for k,v in LANGUAGES.items() if v==l4l][0]

        st.markdown("<span class='sl'>▶ Ses</span>",unsafe_allow_html=True)
        cn4=st.radio("CN4",["Tümü","♀ Kadın","♂ Erkek"],horizontal=True,
                      label_visibility="collapsed",key="cn4")
        f4={k:v for k,v in VOICES.items()
            if cn4=="Tümü" or (cn4=="♀ Kadın" and v[0]=="♀") or (cn4=="♂ Erkek" and v[0]=="♂")}
        vc4=st.selectbox("V4",list(f4.keys()),
                          format_func=lambda x:f"{VOICES[x][0]} {x}  —  {VOICES[x][1]}",
                          label_visibility="collapsed",key="v4")

        st.markdown("<span class='sl'>▶ Stil</span>",unsafe_allow_html=True)
        sty4=st.text_area("STY4","",height=55,label_visibility="collapsed",
                           placeholder="Tüm satırlara uygulanacak stil…",key="sty4")

        _,_,tr4=pool_stats()
        lines4_prev=[l.strip() for l in st.session_state._t_bulk.splitlines() if l.strip()]
        st.markdown(f"""<div class='card {"a" if len(lines4_prev)>tr4 else "b"}'>
            {len(lines4_prev)} satır · {len(lines4_prev)} API isteği · Kalan: <b>{tr4}</b>
            {"<br><span style='color:#f87171;'>⚠️ Kota yetersiz!</span>" if len(lines4_prev)>tr4 else ""}
        </div>""",unsafe_allow_html=True)

    with cR4:
        st.markdown("<span class='sl'>▶ Metinler (her satır = 1 ses)</span>",unsafe_allow_html=True)
        txt4=st.text_area("TT4",value=st.session_state._t_bulk,height=230,
                           label_visibility="collapsed",key="ta4",
                           placeholder="Her satıra bir metin…")
        st.session_state._t_bulk=txt4
        lines4=[l.strip() for l in txt4.splitlines() if l.strip()]
        st.markdown(f"<div style='font-size:.68rem;color:#2e3f55;margin:3px 0 8px;'>{len(lines4)} satır · {len(lines4)} istek</div>",unsafe_allow_html=True)

        if st.button(f"🔴  {len(lines4)} Satırı Toplu Seslendir",type="primary",
                     use_container_width=True,key="btn4"):
            if not lines4: st.warning("⚠️ Satır yok.")
            else:
                results4=[]; errors4=[]
                prog=st.progress(0,"Başlatılıyor…"); sts=st.empty()
                for idx4,line4 in enumerate(lines4):
                    ak4l,ai4l=get_active_key()
                    if ak4l is None: errors4.append(f"Satır {idx4+1}: API kalmadı"); break
                    sts.markdown(f"<div style='font-size:.75rem;color:#6b7a8d;'>🎙️ {idx4+1}/{len(lines4)}: {line4[:45]}…  [API {ai4l+1}]</div>",unsafe_allow_html=True)
                    try:
                        raw4=tts_single(ak4l,mdl4,line4,vc4,lng4,sty4)
                        wav4=pcm2wav(raw4); consume(ai4l,len(line4))
                        archive_add(vc4,mdl4,lng4,sty4,line4,wav4,"bulk")
                        results4.append({"line":line4,"wav":wav4,"idx":idx4+1})
                    except Exception as e: errors4.append(f"Satır {idx4+1}: {e}")
                    prog.progress((idx4+1)/len(lines4),f"{idx4+1}/{len(lines4)}")
                prog.empty(); sts.empty()

                if results4:
                    st.markdown(f"<div class='card g'>✅ {len(results4)}/{len(lines4)} tamamlandı{' · '+str(len(errors4))+' hata' if errors4 else ''}</div>",unsafe_allow_html=True)
                    zb4=io.BytesIO()
                    with zipfile.ZipFile(zb4,"w",zipfile.ZIP_DEFLATED) as zf4:
                        for r4 in results4:
                            fn=f"{r4['idx']:02d}_{vc4.lower()}_{re.sub(r'[^\\w]','_',r4['line'][:18])}.wav"
                            zf4.writestr(fn,r4["wav"])
                    st.download_button("📦 ZIP İndir",zb4.getvalue(),file_name=f"imajfm_bulk_{vc4.lower()}.zip",mime="application/zip",use_container_width=True,key="dl4zip")
                    for r4 in results4:
                        with st.expander(f"🔊 {r4['idx']}. {r4['line'][:55]}",expanded=False):
                            st.audio(r4["wav"],format="audio/wav")
                            st.download_button(f"💾",r4["wav"],file_name=f"{r4['idx']:02d}.wav",mime="audio/wav",key=f"dl4_{r4['idx']}")
                if errors4:
                    for e4 in errors4:
                        st.markdown(f"<div class='card r'>❌ {e4}</div>",unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# TAB 5 — A/B TEST
# ══════════════════════════════════════════════════════════════════
with t5:
    st.markdown("<div class='card p' style='margin-bottom:14px;'><b>🔬 A/B Test</b> — Aynı metni iki farklı ses / model / stil ile üret. Yan yana dinle ve karşılaştır.</div>",unsafe_allow_html=True)
    ab_col1,ab_col2 = st.columns(2,gap="large")

    with ab_col1:
        st.markdown("<div style='font-family:Syne,sans-serif;font-size:.72rem;font-weight:800;letter-spacing:.15em;color:#a78bfa;text-transform:uppercase;margin-bottom:8px;'>🅐 VERSİYON A</div>",unsafe_allow_html=True)
        ma_l=st.selectbox("MA",list(MODELS.values()),label_visibility="collapsed",key="masel")
        mdla=[k for k,v in MODELS.items() if v==ma_l][0]
        la_l=st.selectbox("LA",list(LANGUAGES.values()),label_visibility="collapsed",index=1,key="lasel")
        lnga=[k for k,v in LANGUAGES.items() if v==la_l][0]
        cna=st.radio("CNA",["Tümü","♀","♂"],horizontal=True,label_visibility="collapsed",key="cnasel")
        fa_={k:v for k,v in VOICES.items() if cna=="Tümü" or (cna=="♀" and v[0]=="♀") or (cna=="♂" and v[0]=="♂")}
        vca=st.selectbox("VA",list(fa_.keys()),format_func=lambda x:f"{VOICES[x][0]} {x} — {VOICES[x][1]}",label_visibility="collapsed",key="vasel")
        ps_a=st.selectbox("PSA",list(STYLE_PRESETS.keys()),label_visibility="collapsed",key="psasel")
        stya=st.text_area("STYA",value=STYLE_PRESETS[ps_a],height=55,label_visibility="collapsed",placeholder="Stil A…",key="styasel")
        st.markdown("<span class='sl'>▶ Metin A</span>",unsafe_allow_html=True)
        tag_buttons("_t_ab1","ab1")
        txta=st.text_area("TTA",value=st.session_state._t_ab1,height=140,label_visibility="collapsed",key="tta")
        st.session_state._t_ab1=txta

    with ab_col2:
        st.markdown("<div style='font-family:Syne,sans-serif;font-size:.72rem;font-weight:800;letter-spacing:.15em;color:#fb923c;text-transform:uppercase;margin-bottom:8px;'>🅑 VERSİYON B</div>",unsafe_allow_html=True)
        mb_l=st.selectbox("MB",list(MODELS.values()),label_visibility="collapsed",key="mbsel")
        mdlb=[k for k,v in MODELS.items() if v==mb_l][0]
        lb_l=st.selectbox("LB",list(LANGUAGES.values()),label_visibility="collapsed",index=1,key="lbsel")
        lngb=[k for k,v in LANGUAGES.items() if v==lb_l][0]
        cnb=st.radio("CNB",["Tümü","♀","♂"],horizontal=True,label_visibility="collapsed",key="cnbsel")
        fb_={k:v for k,v in VOICES.items() if cnb=="Tümü" or (cnb=="♀" and v[0]=="♀") or (cnb=="♂" and v[0]=="♂")}
        vcb=st.selectbox("VB",list(fb_.keys()),format_func=lambda x:f"{VOICES[x][0]} {x} — {VOICES[x][1]}",label_visibility="collapsed",index=min(1,len(fb_)-1),key="vbsel")
        ps_b=st.selectbox("PSB",list(STYLE_PRESETS.keys()),label_visibility="collapsed",key="psbsel")
        styb=st.text_area("STYB",value=STYLE_PRESETS[ps_b],height=55,label_visibility="collapsed",placeholder="Stil B…",key="stybsel")
        st.markdown("<span class='sl'>▶ Metin B</span>",unsafe_allow_html=True)
        tag_buttons("_t_ab2","ab2")
        txtb=st.text_area("TTB",value=st.session_state._t_ab2,height=140,label_visibility="collapsed",key="ttb")
        st.session_state._t_ab2=txtb

    st.markdown("<br>",unsafe_allow_html=True)
    btn_ab1,btn_ab2,btn_ab3=st.columns(3)
    with btn_ab1: run_a=st.button("🅐 Sadece A'yı Üret",use_container_width=True,key="btnab1")
    with btn_ab2: run_b=st.button("🅑 Sadece B'yi Üret",use_container_width=True,key="btnab2")
    with btn_ab3: run_ab=st.button("🔴 A ve B'yi Birlikte Üret",type="primary",use_container_width=True,key="btnaboth")

    do_a=run_a or run_ab; do_b=run_b or run_ab
    if do_a or do_b:
        st.markdown("---")
        res_a,res_b=st.columns(2)
        with res_a:
            if do_a:
                aka,aia=get_active_key()
                if aka is None: st.error("❌ API kalmadı (A)")
                else:
                    with st.spinner(f"🅐 {vca}… [API {aia+1}]"):
                        try:
                            rwa=tts_single(aka,mdla,txta,vca,lnga,stya)
                            wva=pcm2wav(rwa); consume(aia,len(txta))
                            archive_add(vca,mdla,lnga,stya,txta,wva,"ab-A")
                            dura=len(rwa)/(24000*2)
                            st.markdown(f"<div class='card p'>🅐 {vca} · {dura:.1f}s</div>",unsafe_allow_html=True)
                            st.audio(wva,format="audio/wav")
                            st.download_button("💾 A WAV",wva,file_name=f"imajfm_A_{vca.lower()}.wav",mime="audio/wav",use_container_width=True,key="dlab")
                        except Exception as e: st.error(f"❌ A: {e}")
        with res_b:
            if do_b:
                akb,aib=get_active_key()
                if akb is None: st.error("❌ API kalmadı (B)")
                else:
                    with st.spinner(f"🅑 {vcb}… [API {aib+1}]"):
                        try:
                            rwb=tts_single(akb,mdlb,txtb,vcb,lngb,styb)
                            wvb=pcm2wav(rwb); consume(aib,len(txtb))
                            archive_add(vcb,mdlb,lngb,styb,txtb,wvb,"ab-B")
                            durb=len(rwb)/(24000*2)
                            st.markdown(f"<div class='card a'>🅑 {vcb} · {durb:.1f}s</div>",unsafe_allow_html=True)
                            st.audio(wvb,format="audio/wav")
                            st.download_button("💾 B WAV",wvb,file_name=f"imajfm_B_{vcb.lower()}.wav",mime="audio/wav",use_container_width=True,key="dlbb")
                        except Exception as e: st.error(f"❌ B: {e}")


# ══════════════════════════════════════════════════════════════════
# TAB 6 — FAVORİLER
# ══════════════════════════════════════════════════════════════════
with t6:
    favs=st.session_state._favorites
    if not favs:
        st.markdown("<div style='text-align:center;padding:50px;color:#2e3f55;'><div style='font-size:2rem;'>⭐</div><div style='font-family:Syne,sans-serif;font-size:.95rem;font-weight:700;margin-top:8px;'>Favori metin yok</div><div style='font-size:.8rem;margin-top:5px;'>Tek Konuşmacı sekmesinde ⭐ Ekle butonunu kullanın.</div></div>",unsafe_allow_html=True)
    else:
        hf1,hf2=st.columns([3,1])
        with hf1: st.markdown(f"<span class='sl'>▶ {len(favs)} Favori Metin</span>",unsafe_allow_html=True)
        with hf2:
            if st.button("🗑️ Tümünü Sil",use_container_width=True,key="fav_clr"):
                st.session_state._favorites=[]; st.rerun()

        for fi,fv in enumerate(favs):
            fc1,fc2,fc3,fc4=st.columns([2,.8,.8,.5])
            with fc1:
                st.markdown(f"""<div class='fav-card'>
                    <div class='fav-name'>⭐ {fv['name']}</div>
                    <div class='fav-prev'>{fv.get('voice','—')} · {fv.get('lang','—')}</div>
                    <div class='fav-prev' style='margin-top:3px;'>{fv['text'][:70]}</div>
                </div>""",unsafe_allow_html=True)
            with fc2:
                if st.button("📋 Kopyala",key=f"fcp_{fi}",use_container_width=True):
                    st.session_state._t_tek=fv["text"]; st.rerun()
            with fc3:
                if st.button("🔴 Seslendir",key=f"fsp_{fi}",use_container_width=True):
                    akf,aif=get_active_key()
                    if akf is None: st.error("❌ API yok")
                    else:
                        with st.spinner(f"🎙️ {fv.get('voice','Kore')}…"):
                            try:
                                rawf=tts_single(akf,fv.get("model","gemini-2.5-flash-tts"),
                                                fv["text"],fv.get("voice","Kore"),fv.get("lang","tr-TR"),"")
                                wavf=pcm2wav(rawf); consume(aif,len(fv["text"]))
                                archive_add(fv.get("voice","Kore"),fv.get("model",""),fv.get("lang",""),"",fv["text"],wavf,"fav")
                                st.session_state[f"_fwav_{fi}"]=wavf; st.rerun()
                            except Exception as e: st.error(f"❌ {e}")
            with fc4:
                if st.button("🗑️",key=f"fdel_{fi}",use_container_width=True):
                    st.session_state._favorites.pop(fi); st.rerun()

            if f"_fwav_{fi}" in st.session_state:
                fw=st.session_state[f"_fwav_{fi}"]
                st.audio(fw,format="audio/wav")
                st.download_button("💾",fw,file_name=f"fav_{fv['name'].replace(' ','_')}.wav",mime="audio/wav",key=f"fdl_{fi}")


# ══════════════════════════════════════════════════════════════════
# TAB 7 — ARŞİV
# ══════════════════════════════════════════════════════════════════
with t7:
    arc=st.session_state._archive
    stat=st.session_state._api_stats

    st.markdown("<span class='sl'>▶ Oturum İstatistikleri</span>",unsafe_allow_html=True)
    si1,si2,si3,si4,si5=st.columns(5)
    with si1: st.markdown(f'<div class="mbox b"><div class="v">{len(arc)}</div><div class="l">Toplam Kayıt</div></div>',unsafe_allow_html=True)
    with si2: st.markdown(f'<div class="mbox g"><div class="v">{stat["total_calls"]}</div><div class="l">API Çağrısı</div></div>',unsafe_allow_html=True)
    with si3: st.markdown(f'<div class="mbox a"><div class="v">{stat["total_secs"]:.0f}s</div><div class="l">Üretilen Ses</div></div>',unsafe_allow_html=True)
    with si4: st.markdown(f'<div class="mbox p"><div class="v">{stat["total_chars"]:,}</div><div class="l">İşlenen Karakter</div></div>',unsafe_allow_html=True)
    with si5:
        total_mb=sum(e["size"] for e in arc)/(1024*1024)
        st.markdown(f'<div class="mbox"><div class="v">{total_mb:.1f}MB</div><div class="l">Arşiv Boyutu</div></div>',unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)

    if not arc:
        st.markdown("<div style='text-align:center;padding:50px;color:#2e3f55;'><div style='font-size:2rem;'>📂</div><div style='font-family:Syne,sans-serif;font-size:.95rem;font-weight:700;margin-top:8px;'>Arşiv Boş</div></div>",unsafe_allow_html=True)
    else:
        ah1,ah2,ah3=st.columns([2,1,1])
        with ah1: st.markdown(f"<span class='sl'>▶ {len(arc)} Kayıt</span>",unsafe_allow_html=True)
        with ah2:
            if st.button("📦 Tümünü ZIP",use_container_width=True,key="arc_zip"):
                zba=io.BytesIO()
                with zipfile.ZipFile(zba,"w",zipfile.ZIP_DEFLATED) as za:
                    for h in arc:
                        fn=f"{h['ts_short'].replace(':','-').replace(' ','_')}_{h['voice']}_{h['id']}.wav"
                        za.writestr(fn,h["wav"])
                st.download_button("💾 ZIP İndir",zba.getvalue(),file_name="imajfm_arsiv.zip",mime="application/zip",key="arc_zip_dl")
        with ah3:
            if st.button("🗑️ Tümünü Sil",use_container_width=True,key="arc_clr"):
                st.session_state._archive=[]
                st.session_state._api_stats={"total_calls":0,"total_chars":0,"total_secs":0.0}
                st.rerun()

        af1,af2=st.columns([2,1])
        with af1:
            arc_search=st.text_input("Ara","",placeholder="🔍 Ses, metin veya model ara…",label_visibility="collapsed",key="arc_search")
        with af2:
            arc_mode=st.selectbox("Mod",["Tümü","tek","cift","split","bulk","ab-A","ab-B","fav","reji"],label_visibility="collapsed",key="arc_mode")

        filtered_arc=arc
        if arc_search.strip():
            q=arc_search.lower()
            filtered_arc=[h for h in filtered_arc if q in h["voice"].lower() or q in h["text"].lower() or q in h["model"].lower()]
        if arc_mode!="Tümü":
            filtered_arc=[h for h in filtered_arc if h.get("mode","")==arc_mode]

        st.markdown(f"<div style='font-size:.68rem;color:#2e3f55;margin:4px 0 10px;'>{len(filtered_arc)} kayıt gösteriliyor</div>",unsafe_allow_html=True)

        gcols=st.columns(3)
        for gi,h in enumerate(filtered_arc):
            with gcols[gi%3]:
                mode_badge_colors={"tek":"#3b82f6","cift":"#a78bfa","split":"#f59e0b",
                                    "bulk":"#22c55e","ab-A":"#a78bfa","ab-B":"#fb923c",
                                    "fav":"#fbbf24","reji":"#10b981"}
                mc=mode_badge_colors.get(h.get("mode","tek"),"#3b82f6")
                st.markdown(f"""
                <div class='arc-card'>
                    <div class='arc-meta'>
                        <span class='arc-voice'>{VOICES.get(h["voice"].split("+")[0],("?",""))[0]} {h["voice"]}</span>
                        <span class='arc-ts'>{h["ts_short"]}</span>
                    </div>
                    <div class='arc-info'>
                        <span style='color:{mc};background:{mc}18;border-radius:4px;padding:1px 6px;font-size:.62rem;font-weight:700;'>{h.get("mode","tek").upper()}</span>
                        &nbsp;{h["model_short"]} · {h["lang"]} · {h["dur"]}s · {h["size"]//1024}KB
                    </div>
                    <div class='arc-text'>{h["preview"]}</div>
                </div>
                """,unsafe_allow_html=True)
                st.audio(h["wav"],format="audio/wav")
                dca,dcb=st.columns(2)
                with dca:
                    st.download_button("💾 WAV",h["wav"],file_name=f"imajfm_{h['voice'].lower().replace('+','_')}_{h['id']}.wav",mime="audio/wav",use_container_width=True,key=f"arc_dl_{h['id']}")
                with dcb:
                    if st.button("⭐",key=f"arc_fav_{h['id']}",help="Favorilere ekle",use_container_width=True):
                        st.session_state._favorites.append({"id":h["id"],"name":h["voice"]+" "+h["ts_short"],"text":h["text"],"voice":h["voice"].split("+")[0],"model":h["model"],"lang":h["lang"]})
                        st.rerun()


# ══════════════════════════════════════════════════════════════════
# TAB 8 — DELAY REJİ (YAYIN OTOMASYONU)
# ══════════════════════════════════════════════════════════════════
with t8:

    # ── BAŞLIK ──────────────────────────────────────────────────
    st.markdown("""
    <div class='reji-header'>
        <h2>📻 Delay Reji — Yayın Otomasyonu</h2>
        <p>Playlist oluştur · Şarkı başı/sonu anons ayarla · Fon müzik geçişleri · Yayın planı üret · Tüm anonları ZIP ile indir</p>
    </div>
    """,unsafe_allow_html=True)

    # ── ANA SEKMELER: Playlist · Ayarlar · Plan · Önizleme ──────
    rj1, rj2, rj3, rj4 = st.tabs([
        "🎵  Playlist",
        "⚙️  Reji Ayarları",
        "📋  Yayın Planı",
        "🎬  Üretim & İndir",
    ])

    # ══════════════════════════════════════════════════════════
    # REJI TAB 1 — PLAYLİST
    # ══════════════════════════════════════════════════════════
    with rj1:
        playlist = st.session_state._playlist

        # Yeni şarkı ekleme formu
        st.markdown("<span class='sl'>▶ Yeni Şarkı Ekle</span>",unsafe_allow_html=True)
        nc1,nc2,nc3,nc4 = st.columns([2,1.5,.5,.5])
        with nc1:
            new_title  = st.text_input("Şarkı Adı","",placeholder="Şarkı adı…",label_visibility="collapsed",key="new_title")
        with nc2:
            new_artist = st.text_input("Sanatçı","",placeholder="Sanatçı adı…",label_visibility="collapsed",key="new_artist")
        with nc3:
            new_min    = st.number_input("Dk",min_value=0,max_value=10,value=3,label_visibility="collapsed",key="new_min")
        with nc4:
            new_sec    = st.number_input("Sn",min_value=0,max_value=59,value=30,label_visibility="collapsed",key="new_sec")

        btn_add_col, btn_demo_col = st.columns([1,1])
        with btn_add_col:
            if st.button("➕ Playlist'e Ekle",use_container_width=True,key="add_song"):
                if new_title.strip():
                    st.session_state._playlist.append({
                        "id":          song_uid(),
                        "title":       new_title.strip(),
                        "artist":      new_artist.strip() or "Bilinmeyen",
                        "duration_min": int(new_min),
                        "duration_sec": int(new_sec),
                        "anons_bas":   False,
                        "anons_son":   False,
                        "anons_bas_text": "",
                        "anons_son_text": "",
                        "fon_aktif":   False,
                        "fon_tip":     "📻 Radyo Klasik",
                        "anons_wav_bas": None,
                        "anons_wav_son": None,
                    })
                    st.session_state._reji_plan_generated = False
                    st.rerun()
                else:
                    st.warning("⚠️ Şarkı adı boş olamaz.")

        with btn_demo_col:
            if st.button("🎲 Demo Playlist Yükle",use_container_width=True,key="demo_playlist"):
                demo_songs = [
                    ("Gece Yarısı",        "Sezen Aksu",    3,45),
                    ("Yüksek Yüksek Tepelere","Barış Manço",4,12),
                    ("Oy Benim Sarı Turnam","Neşet Ertaş",  3,55),
                    ("Hayatımın Anlamı",   "MFÖ",           3,28),
                    ("Leylim Ley",         "Zülfü Livaneli", 4, 5),
                    ("Mavi Bisiklet",      "Sıla",          3,48),
                    ("Seni Bana Verecekler","Tarkan",        4,20),
                ]
                st.session_state._playlist = []
                for t,ar,dm,ds in demo_songs:
                    st.session_state._playlist.append({
                        "id": song_uid(), "title":t, "artist":ar,
                        "duration_min":dm, "duration_sec":ds,
                        "anons_bas":False,"anons_son":False,
                        "anons_bas_text":"","anons_son_text":"",
                        "fon_aktif":False,"fon_tip":"📻 Radyo Klasik",
                        "anons_wav_bas":None,"anons_wav_son":None,
                    })
                st.session_state._reji_plan_generated = False
                st.rerun()

        st.markdown("<hr>",unsafe_allow_html=True)

        if not playlist:
            st.markdown("<div style='text-align:center;padding:40px;color:#2e3f55;'><div style='font-size:2rem;'>🎵</div><div style='font-family:Syne,sans-serif;font-size:.9rem;font-weight:700;margin-top:8px;'>Playlist boş</div><div style='font-size:.78rem;margin-top:5px;'>Yukarıdan şarkı ekleyin veya Demo Playlist yükleyin.</div></div>",unsafe_allow_html=True)
        else:
            # Özet
            total_song_secs = sum(total_dur_sec(s) for s in playlist)
            anons_bas_count = sum(1 for s in playlist if s.get("anons_bas"))
            anons_son_count = sum(1 for s in playlist if s.get("anons_son"))
            fon_count       = sum(1 for s in playlist if s.get("fon_aktif"))

            ps1,ps2,ps3,ps4,ps5 = st.columns(5)
            with ps1: st.markdown(f'<div class="mbox t"><div class="v">{len(playlist)}</div><div class="l">Şarkı</div></div>',unsafe_allow_html=True)
            with ps2: st.markdown(f'<div class="mbox b"><div class="v">{format_dur(total_song_secs)}</div><div class="l">Toplam Süre</div></div>',unsafe_allow_html=True)
            with ps3: st.markdown(f'<div class="mbox a"><div class="v">{anons_bas_count}</div><div class="l">Baş Anons</div></div>',unsafe_allow_html=True)
            with ps4: st.markdown(f'<div class="mbox a"><div class="v">{anons_son_count}</div><div class="l">Son Anons</div></div>',unsafe_allow_html=True)
            with ps5: st.markdown(f'<div class="mbox g"><div class="v">{fon_count}</div><div class="l">Fon Geçiş</div></div>',unsafe_allow_html=True)

            st.markdown("<br>",unsafe_allow_html=True)
            st.markdown("<span class='sl'>▶ Şarkı Listesi  —  Her şarkıyı düzenleyip anons/fon ayarlayın</span>",unsafe_allow_html=True)

            for si, song in enumerate(playlist):
                sid = song["id"]
                dur_s = total_dur_sec(song)
                has_bas = song.get("anons_bas",False)
                has_son = song.get("anons_son",False)
                has_fon = song.get("fon_aktif",False)

                badges_html = ""
                if has_bas: badges_html += "<span class='anons-badge bas'>🎙️ BAŞ</span>"
                if has_son: badges_html += "<span class='anons-badge son'>🎙️ SON</span>"
                if has_fon: badges_html += "<span class='anons-badge fon'>🎶 FON</span>"

                with st.expander(
                    f"{'🎵'} {si+1:02d}.  {song.get('artist','?')} — {song.get('title','?')}   [{format_dur(dur_s)}]",
                    expanded=False
                ):
                    ec1,ec2,ec3,ec4 = st.columns([2,1.5,.5,.5])
                    with ec1:
                        nt = st.text_input("Başlık",value=song["title"],label_visibility="collapsed",key=f"et_{sid}")
                        if nt != song["title"]: st.session_state._playlist[si]["title"]=nt; st.session_state._reji_plan_generated=False; st.rerun()
                    with ec2:
                        na = st.text_input("Sanatçı",value=song["artist"],label_visibility="collapsed",key=f"ea_{sid}")
                        if na != song["artist"]: st.session_state._playlist[si]["artist"]=na; st.session_state._reji_plan_generated=False; st.rerun()
                    with ec3:
                        ndm = st.number_input("Dk",min_value=0,max_value=10,value=song["duration_min"],label_visibility="collapsed",key=f"edm_{sid}")
                        if ndm != song["duration_min"]: st.session_state._playlist[si]["duration_min"]=int(ndm); st.session_state._reji_plan_generated=False; st.rerun()
                    with ec4:
                        nds = st.number_input("Sn",min_value=0,max_value=59,value=song["duration_sec"],label_visibility="collapsed",key=f"eds_{sid}")
                        if nds != song["duration_sec"]: st.session_state._playlist[si]["duration_sec"]=int(nds); st.session_state._reji_plan_generated=False; st.rerun()

                    st.markdown("<hr>",unsafe_allow_html=True)

                    # Anons & Fon toggle satırı
                    tog1,tog2,tog3 = st.columns(3)
                    with tog1:
                        new_bas = st.checkbox("🎙️ Şarkı Başı Anonsu",value=has_bas,key=f"cb_{sid}")
                        if new_bas != has_bas:
                            st.session_state._playlist[si]["anons_bas"]=new_bas
                            if new_bas and not song.get("anons_bas_text"):
                                st.session_state._playlist[si]["anons_bas_text"] = generate_anons_text_bas(song)
                            st.session_state._reji_plan_generated=False; st.rerun()
                    with tog2:
                        new_son = st.checkbox("🎙️ Şarkı Sonu Anonsu",value=has_son,key=f"cs_{sid}")
                        if new_son != has_son:
                            st.session_state._playlist[si]["anons_son"]=new_son
                            if new_son and not song.get("anons_son_text"):
                                st.session_state._playlist[si]["anons_son_text"] = generate_anons_text_son(song)
                            st.session_state._reji_plan_generated=False; st.rerun()
                    with tog3:
                        new_fon = st.checkbox("🎶 Fon Müzik Geçişi",value=has_fon,key=f"cf_{sid}")
                        if new_fon != has_fon:
                            st.session_state._playlist[si]["fon_aktif"]=new_fon
                            st.session_state._reji_plan_generated=False; st.rerun()

                    # Fon tipi
                    if song.get("fon_aktif"):
                        cur_fon = song.get("fon_tip","📻 Radyo Klasik")
                        fon_opts = list(FON_TIPLERI.keys())
                        cur_idx  = fon_opts.index(cur_fon) if cur_fon in fon_opts else 3
                        nf = st.selectbox("Fon Tipi",fon_opts,index=cur_idx,
                                          label_visibility="collapsed",key=f"ft_{sid}")
                        if nf != cur_fon:
                            st.session_state._playlist[si]["fon_tip"]=nf
                            st.session_state._reji_plan_generated=False; st.rerun()
                        st.markdown(f"<div style='font-size:.68rem;color:#10b981;margin:2px 0 6px;'>ℹ️ {FON_TIPLERI[nf]}</div>",unsafe_allow_html=True)

                    # Şarkı başı anons metni
                    if song.get("anons_bas"):
                        st.markdown("<span class='sl3'>▸ Şarkı Başı Anons Metni</span>",unsafe_allow_html=True)
                        bas_def = song.get("anons_bas_text") or generate_anons_text_bas(song)
                        new_bas_txt = st.text_area("BAS",value=bas_def,height=80,
                                                    label_visibility="collapsed",key=f"bat_{sid}")
                        if new_bas_txt != song.get("anons_bas_text",""):
                            st.session_state._playlist[si]["anons_bas_text"]=new_bas_txt
                            st.session_state._playlist[si]["anons_wav_bas"]=None

                        # Üretilmiş WAV göster
                        if song.get("anons_wav_bas"):
                            st.markdown("<div class='card g' style='font-size:.72rem;'>✅ Anons üretildi</div>",unsafe_allow_html=True)
                            st.audio(song["anons_wav_bas"],format="audio/wav")
                        else:
                            st.markdown("<div class='card a' style='font-size:.72rem;'>⏳ Henüz ses üretilmedi — Üretim sekmesinden üretin</div>",unsafe_allow_html=True)

                    # Şarkı sonu anons metni
                    if song.get("anons_son"):
                        st.markdown("<span class='sl3'>▸ Şarkı Sonu Anons Metni</span>",unsafe_allow_html=True)
                        son_def = song.get("anons_son_text") or generate_anons_text_son(song)
                        new_son_txt = st.text_area("SON",value=son_def,height=80,
                                                    label_visibility="collapsed",key=f"sot_{sid}")
                        if new_son_txt != song.get("anons_son_text",""):
                            st.session_state._playlist[si]["anons_son_text"]=new_son_txt
                            st.session_state._playlist[si]["anons_wav_son"]=None

                        if song.get("anons_wav_son"):
                            st.markdown("<div class='card g' style='font-size:.72rem;'>✅ Anons üretildi</div>",unsafe_allow_html=True)
                            st.audio(song["anons_wav_son"],format="audio/wav")
                        else:
                            st.markdown("<div class='card a' style='font-size:.72rem;'>⏳ Henüz ses üretilmedi — Üretim sekmesinden üretin</div>",unsafe_allow_html=True)

                    st.markdown("<hr>",unsafe_allow_html=True)

                    # Sıra değiştirme + sil
                    ord1,ord2,ord3,ord4 = st.columns(4)
                    with ord1:
                        if si > 0 and st.button("⬆️ Yukarı",key=f"up_{sid}",use_container_width=True):
                            pl = st.session_state._playlist
                            pl[si-1],pl[si] = pl[si],pl[si-1]
                            st.session_state._reji_plan_generated=False; st.rerun()
                    with ord2:
                        if si < len(playlist)-1 and st.button("⬇️ Aşağı",key=f"dn_{sid}",use_container_width=True):
                            pl = st.session_state._playlist
                            pl[si+1],pl[si] = pl[si],pl[si+1]
                            st.session_state._reji_plan_generated=False; st.rerun()
                    with ord3:
                        if st.button("🔝 En Üste",key=f"top_{sid}",use_container_width=True):
                            pl = st.session_state._playlist
                            pl.insert(0, pl.pop(si))
                            st.session_state._reji_plan_generated=False; st.rerun()
                    with ord4:
                        if st.button("🗑️ Sil",key=f"del_song_{sid}",use_container_width=True):
                            st.session_state._playlist.pop(si)
                            st.session_state._reji_plan_generated=False; st.rerun()

            st.markdown("<hr>",unsafe_allow_html=True)
            if st.button("🗑️ Tüm Playlist'i Temizle",use_container_width=True,key="clear_pl"):
                st.session_state._playlist=[]
                st.session_state._reji_plan_generated=False; st.rerun()


    # ══════════════════════════════════════════════════════════
    # REJI TAB 2 — AYARLAR
    # ══════════════════════════════════════════════════════════
    with rj2:
        st.markdown("<span class='sl'>▶ TTS Ses Karakteri</span>",unsafe_allow_html=True)
        st.markdown("<div class='card b' style='margin-bottom:10px;font-size:.78rem;'>Bu ayarlar tüm Delay Reji anonslarına uygulanır.</div>",unsafe_allow_html=True)

        ra1,ra2 = st.columns(2)
        with ra1:
            rj_m_l = st.selectbox("Reji Model",list(MODELS.values()),label_visibility="collapsed",key="rj_model_sel")
            rj_model_key = [k for k,v in MODELS.items() if v==rj_m_l][0]
            if rj_model_key != st.session_state._reji_model:
                st.session_state._reji_model = rj_model_key

            rj_l_l = st.selectbox("Reji Dil",list(LANGUAGES.values()),index=1,label_visibility="collapsed",key="rj_lang_sel")
            rj_lang_key = [k for k,v in LANGUAGES.items() if v==rj_l_l][0]
            if rj_lang_key != st.session_state._reji_lang:
                st.session_state._reji_lang = rj_lang_key

        with ra2:
            rj_cn = st.radio("Reji Cinsiyet",["Tümü","♀ Kadın","♂ Erkek"],horizontal=True,
                              label_visibility="collapsed",key="rj_cn")
            rj_vf = {k:v for k,v in VOICES.items()
                     if rj_cn=="Tümü" or (rj_cn=="♀ Kadın" and v[0]=="♀") or (rj_cn=="♂ Erkek" and v[0]=="♂")}
            rj_vc = st.selectbox("Reji Ses",list(rj_vf.keys()),
                                  format_func=lambda x:f"{VOICES[x][0]} {x}  —  {VOICES[x][1]}",
                                  label_visibility="collapsed",key="rj_voice_sel")
            if rj_vc != st.session_state._reji_voice:
                st.session_state._reji_voice = rj_vc

        st.markdown("<span class='sl'>▶ Stil Talimatı</span>",unsafe_allow_html=True)
        rj_ps = st.selectbox("Reji Preset",list(STYLE_PRESETS.keys()),label_visibility="collapsed",key="rj_ps")
        rj_sty = st.text_area("Reji Stil",value=STYLE_PRESETS[rj_ps],height=80,
                               label_visibility="collapsed",
                               placeholder="Anonslar için stil talimatı…",key="rj_style_txt")
        if rj_sty != st.session_state._reji_style:
            st.session_state._reji_style = rj_sty

        st.markdown("<span class='sl'>▶ Yayın Başlangıç Saati</span>",unsafe_allow_html=True)
        rj_saat = st.text_input("Başlangıç Saati",value=st.session_state._reji_baslangic_saat,
                                  placeholder="HH:MM  örn: 06:00",
                                  label_visibility="collapsed",key="rj_saat")
        if rj_saat != st.session_state._reji_baslangic_saat:
            st.session_state._reji_baslangic_saat = rj_saat
            st.session_state._reji_plan_generated  = False

        st.markdown("<hr>",unsafe_allow_html=True)
        st.markdown(f"""<div class='card t'>
            <b>Aktif Reji Ayarları</b><br>
            🎙️ Ses: <b>{st.session_state._reji_voice}</b> ({VOICES.get(st.session_state._reji_voice,('?',''))[1]})<br>
            🤖 Model: <b>{st.session_state._reji_model}</b><br>
            🌐 Dil: <b>{st.session_state._reji_lang}</b><br>
            🕐 Başlangıç: <b>{st.session_state._reji_baslangic_saat}</b>
        </div>""",unsafe_allow_html=True)

        st.markdown("<span class='sl'>▶ Toplu Anons Metni Yenile</span>",unsafe_allow_html=True)
        if st.button("🔄 Tüm Anons Metinlerini Otomatik Yenile",use_container_width=True,key="regen_texts"):
            for i,s in enumerate(st.session_state._playlist):
                if s.get("anons_bas"):
                    st.session_state._playlist[i]["anons_bas_text"] = generate_anons_text_bas(s)
                    st.session_state._playlist[i]["anons_wav_bas"]  = None
                if s.get("anons_son"):
                    st.session_state._playlist[i]["anons_son_text"] = generate_anons_text_son(s)
                    st.session_state._playlist[i]["anons_wav_son"]  = None
            st.success("✅ Tüm anons metinleri yenilendi. Üretim sekmesinden sesleri üretin."); time.sleep(0.8); st.rerun()


    # ══════════════════════════════════════════════════════════
    # REJI TAB 3 — YAYIN PLANI
    # ══════════════════════════════════════════════════════════
    with rj3:
        playlist = st.session_state._playlist

        if not playlist:
            st.markdown("<div class='card r'>⚠️ Playlist boş. Önce Playlist sekmesinden şarkı ekleyin.</div>",unsafe_allow_html=True)
        else:
            gen_col, _ = st.columns([1,2])
            with gen_col:
                if st.button("📋 Yayın Planını Oluştur / Güncelle",type="primary",use_container_width=True,key="gen_plan"):
                    plan = build_yayın_plani(playlist, st.session_state._reji_baslangic_saat)
                    st.session_state._reji_plan = plan
                    st.session_state._reji_plan_generated = True
                    st.rerun()

            if not st.session_state._reji_plan_generated:
                st.markdown("<div class='card a'>ℹ️ Playlist değişti veya plan henüz oluşturulmadı. Yukarıdaki butona tıklayın.</div>",unsafe_allow_html=True)
            else:
                plan = st.session_state._reji_plan

                # Özet
                total_plan_secs = sum(p["duration_sec"] for p in plan)
                song_blocks     = [p for p in plan if p["type"]=="song"]
                anons_blocks    = [p for p in plan if p["type"] in ("anons_bas","anons_son")]
                fon_blocks      = [p for p in plan if p["type"]=="fon"]
                end_time        = add_time(st.session_state._reji_baslangic_saat, total_plan_secs)

                pc1,pc2,pc3,pc4 = st.columns(4)
                with pc1: st.markdown(f'<div class="mbox t"><div class="v">{len(song_blocks)}</div><div class="l">Şarkı Bloğu</div></div>',unsafe_allow_html=True)
                with pc2: st.markdown(f'<div class="mbox a"><div class="v">{len(anons_blocks)}</div><div class="l">Anons Bloğu</div></div>',unsafe_allow_html=True)
                with pc3: st.markdown(f'<div class="mbox g"><div class="v">{len(fon_blocks)}</div><div class="l">Fon Geçiş</div></div>',unsafe_allow_html=True)
                with pc4: st.markdown(f'<div class="mbox b"><div class="v">{format_dur(total_plan_secs)}</div><div class="l">Toplam Süre</div></div>',unsafe_allow_html=True)

                st.markdown(f"""
                <div class='broadcast-live'>
                    <div class='now-playing'>📡 Yayın: {st.session_state._reji_baslangic_saat} → {end_time[:5]}</div>
                    <div class='next-up'>Toplam {len(plan)} blok · {len(song_blocks)} şarkı · {len(anons_blocks)} anons · {len(fon_blocks)} fon geçişi</div>
                </div>
                """,unsafe_allow_html=True)

                st.markdown("<span class='sl'>▶ Zaman Çizelgesi</span>",unsafe_allow_html=True)

                type_map = {
                    "song":      ("ttype-song",  "🎵 ŞARKI"),
                    "anons_bas": ("ttype-anons", "🎙️ BAŞ"),
                    "anons_son": ("ttype-anons", "🎙️ SON"),
                    "fon":       ("ttype-fon",   "🎶 FON"),
                }

                for pi, block in enumerate(plan):
                    tcls, tlbl = type_map.get(block["type"], ("ttype-song","?"))
                    wav_icon = "✅" if block.get("wav") else ("⏳" if block["type"] in ("anons_bas","anons_son") else "")
                    st.markdown(f"""
                    <div class='timeline-block'>
                        <span class='timeline-time'>{block["time"][:5]}</span>
                        <span class='timeline-type {tcls}'>{tlbl}</span>
                        <span class='timeline-label'>{wav_icon} {block["label"]}</span>
                        <span class='timeline-dur'>{format_dur(block["duration_sec"])}</span>
                    </div>
                    """,unsafe_allow_html=True)

                # JSON export
                st.markdown("<br>",unsafe_allow_html=True)
                plan_export = [{k:v for k,v in b.items() if k!="wav"} for b in plan]
                st.download_button("📥 Yayın Planını JSON İndir",
                                   data=json.dumps(plan_export,ensure_ascii=False,indent=2),
                                   file_name="imajfm_yayin_plani.json",
                                   mime="application/json",
                                   use_container_width=True,key="dl_plan_json")


    # ══════════════════════════════════════════════════════════
    # REJI TAB 4 — ÜRETİM & İNDİR
    # ══════════════════════════════════════════════════════════
    with rj4:
        playlist = st.session_state._playlist

        if not playlist:
            st.markdown("<div class='card r'>⚠️ Playlist boş.</div>",unsafe_allow_html=True)
        else:
            anons_needed = [(i,s) for i,s in enumerate(playlist)
                            if (s.get("anons_bas") and not s.get("anons_wav_bas"))
                            or (s.get("anons_son") and not s.get("anons_wav_son"))]
            anons_done   = [(i,s) for i,s in enumerate(playlist)
                            if (s.get("anons_bas") and s.get("anons_wav_bas"))
                            or (s.get("anons_son") and s.get("anons_wav_son"))]

            st.markdown(f"""<div class='card {"t" if not anons_needed else "a"}'>
                📊 {len(anons_done)} anons üretildi &nbsp;·&nbsp;
                {len(anons_needed)} bekliyor &nbsp;·&nbsp;
                Ses: <b>{st.session_state._reji_voice}</b> &nbsp;·&nbsp;
                Model: <b>{st.session_state._reji_model.replace("gemini-","").replace("-tts","")}</b>
            </div>""",unsafe_allow_html=True)

            # Tek tek üretim butonu her şarkı için
            st.markdown("<span class='sl'>▶ Şarkı Bazlı Anons Üretimi</span>",unsafe_allow_html=True)

            for si,song in enumerate(playlist):
                sid = song["id"]
                if not song.get("anons_bas") and not song.get("anons_son"):
                    continue

                with st.expander(f"🎵 {si+1:02d}. {song.get('artist','?')} — {song.get('title','?')}",expanded=False):
                    ub1,ub2,ub3 = st.columns(3)

                    # Şarkı başı
                    if song.get("anons_bas"):
                        with ub1:
                            st.markdown(f"<div style='font-size:.72rem;color:#f59e0b;font-weight:700;margin-bottom:4px;'>🎙️ BAŞ ANONSU</div>",unsafe_allow_html=True)
                            bas_text = song.get("anons_bas_text") or generate_anons_text_bas(song)
                            st.text_area("bt",value=bas_text,height=80,label_visibility="collapsed",key=f"prod_bat_{sid}",disabled=True)
                            if song.get("anons_wav_bas"):
                                st.audio(song["anons_wav_bas"],format="audio/wav")
                                st.download_button("💾 BAŞ WAV",song["anons_wav_bas"],
                                                   file_name=f"bas_{si+1:02d}_{song['title'][:12]}.wav",
                                                   mime="audio/wav",key=f"dl_bas_{sid}")
                            if st.button("🔴 Baş Anonsu Üret",key=f"gen_bas_{sid}",use_container_width=True):
                                akr,air=get_active_key()
                                if akr is None: st.error("❌ API kalmadı!")
                                else:
                                    with st.spinner(f"🎙️ Baş anonsu… [{st.session_state._reji_voice}]"):
                                        try:
                                            rawrb=tts_single(akr,st.session_state._reji_model,
                                                              bas_text,st.session_state._reji_voice,
                                                              st.session_state._reji_lang,
                                                              st.session_state._reji_style)
                                            wavrb=pcm2wav(rawrb)
                                            consume(air,len(bas_text))
                                            st.session_state._playlist[si]["anons_wav_bas"]=wavrb
                                            archive_add(st.session_state._reji_voice,
                                                        st.session_state._reji_model,
                                                        st.session_state._reji_lang,
                                                        st.session_state._reji_style,
                                                        bas_text,wavrb,"reji")
                                            st.session_state._reji_plan_generated=False
                                            st.rerun()
                                        except Exception as e: st.error(f"❌ {e}")

                    # Şarkı sonu
                    if song.get("anons_son"):
                        with ub2:
                            st.markdown(f"<div style='font-size:.72rem;color:#60a5fa;font-weight:700;margin-bottom:4px;'>🎙️ SON ANONSU</div>",unsafe_allow_html=True)
                            son_text = song.get("anons_son_text") or generate_anons_text_son(song)
                            st.text_area("st",value=son_text,height=80,label_visibility="collapsed",key=f"prod_sot_{sid}",disabled=True)
                            if song.get("anons_wav_son"):
                                st.audio(song["anons_wav_son"],format="audio/wav")
                                st.download_button("💾 SON WAV",song["anons_wav_son"],
                                                   file_name=f"son_{si+1:02d}_{song['title'][:12]}.wav",
                                                   mime="audio/wav",key=f"dl_son_{sid}")
                            if st.button("🔴 Son Anonsu Üret",key=f"gen_son_{sid}",use_container_width=True):
                                akr,air=get_active_key()
                                if akr is None: st.error("❌ API kalmadı!")
                                else:
                                    with st.spinner(f"🎙️ Son anonsu… [{st.session_state._reji_voice}]"):
                                        try:
                                            rawrs=tts_single(akr,st.session_state._reji_model,
                                                              son_text,st.session_state._reji_voice,
                                                              st.session_state._reji_lang,
                                                              st.session_state._reji_style)
                                            wavrs=pcm2wav(rawrs)
                                            consume(air,len(son_text))
                                            st.session_state._playlist[si]["anons_wav_son"]=wavrs
                                            archive_add(st.session_state._reji_voice,
                                                        st.session_state._reji_model,
                                                        st.session_state._reji_lang,
                                                        st.session_state._reji_style,
                                                        son_text,wavrs,"reji")
                                            st.session_state._reji_plan_generated=False
                                            st.rerun()
                                        except Exception as e: st.error(f"❌ {e}")

            st.markdown("<hr>",unsafe_allow_html=True)

            # TOPLU ÜRETİM
            st.markdown("<span class='sl'>▶ Toplu Anons Üretimi</span>",unsafe_allow_html=True)
            st.markdown("<div class='card b' style='font-size:.78rem;'>Aşağıdaki buton, tüm işaretlenmiş anonsları (bas + son) otomatik olarak sırayla üretir. Her anons için 1 API isteği kullanılır.</div>",unsafe_allow_html=True)

            needed_list = []
            for si2,s2 in enumerate(playlist):
                if s2.get("anons_bas") and not s2.get("anons_wav_bas"):
                    needed_list.append((si2, s2, "bas"))
                if s2.get("anons_son") and not s2.get("anons_wav_son"):
                    needed_list.append((si2, s2, "son"))

            _,_,tr_rj=pool_stats()
            st.markdown(f"""<div class='card {"a" if len(needed_list)>tr_rj else "t"}'>
                {len(needed_list)} anons üretilecek · {tr_rj} API isteği kalan
                {"<br><span style='color:#f87171;'>⚠️ Kota yetersiz olabilir!</span>" if len(needed_list)>tr_rj else ""}
            </div>""",unsafe_allow_html=True)

            if needed_list:
                if st.button(f"🔴 {len(needed_list)} Anonsu Toplu Üret",type="primary",use_container_width=True,key="bulk_reji_gen"):
                    prog_rj=st.progress(0,"Başlatılıyor…")
                    sts_rj=st.empty()
                    errors_rj=[]
                    for ni,(nsi,nsong,ntype) in enumerate(needed_list):
                        akrj,airj=get_active_key()
                        if akrj is None:
                            errors_rj.append(f"{nsong['title']} ({ntype}): API kalmadı"); break
                        ntext = (nsong.get("anons_bas_text") or generate_anons_text_bas(nsong)) if ntype=="bas" \
                                else (nsong.get("anons_son_text") or generate_anons_text_son(nsong))
                        sts_rj.markdown(f"<div style='font-size:.75rem;color:#6b7a8d;'>🎙️ {ni+1}/{len(needed_list)}: {nsong['title']} [{ntype}]  [API {airj+1}]</div>",unsafe_allow_html=True)
                        try:
                            rawrj=tts_single(akrj,st.session_state._reji_model,ntext,
                                              st.session_state._reji_voice,
                                              st.session_state._reji_lang,
                                              st.session_state._reji_style)
                            wavrj=pcm2wav(rawrj)
                            consume(airj,len(ntext))
                            if ntype=="bas":
                                st.session_state._playlist[nsi]["anons_wav_bas"]=wavrj
                            else:
                                st.session_state._playlist[nsi]["anons_wav_son"]=wavrj
                            archive_add(st.session_state._reji_voice,st.session_state._reji_model,
                                        st.session_state._reji_lang,st.session_state._reji_style,
                                        ntext,wavrj,"reji")
                        except Exception as e:
                            errors_rj.append(f"{nsong['title']} ({ntype}): {e}")
                        prog_rj.progress((ni+1)/len(needed_list),f"{ni+1}/{len(needed_list)}")
                    prog_rj.empty(); sts_rj.empty()
                    st.session_state._reji_plan_generated=False
                    if errors_rj:
                        for err in errors_rj:
                            st.markdown(f"<div class='card r'>❌ {err}</div>",unsafe_allow_html=True)
                    else:
                        st.success(f"✅ {len(needed_list)} anons başarıyla üretildi!")
                    time.sleep(0.5); st.rerun()
            else:
                st.markdown("<div class='card g'>✅ Tüm anonslar üretildi!</div>",unsafe_allow_html=True)

            # ZIP İNDİR
            st.markdown("<hr>",unsafe_allow_html=True)
            st.markdown("<span class='sl'>▶ ZIP Paketi İndir</span>",unsafe_allow_html=True)

            zip_items=[]
            for si3,s3 in enumerate(playlist):
                if s3.get("anons_wav_bas"):
                    fn=f"{si3+1:02d}_BAS_{s3['artist'][:10]}_{s3['title'][:10]}.wav"
                    zip_items.append((fn, s3["anons_wav_bas"]))
                if s3.get("anons_wav_son"):
                    fn=f"{si3+1:02d}_SON_{s3['artist'][:10]}_{s3['title'][:10]}.wav"
                    zip_items.append((fn, s3["anons_wav_son"]))

            if zip_items:
                zbr=io.BytesIO()
                with zipfile.ZipFile(zbr,"w",zipfile.ZIP_DEFLATED) as zfr:
                    for fn,wav_data in zip_items:
                        safe_fn = re.sub(r'[^\w\-.]','_',fn)
                        zfr.writestr(safe_fn, wav_data)
                st.markdown(f"<div class='card t'>{len(zip_items)} anons dosyası ZIP'e hazır</div>",unsafe_allow_html=True)
                st.download_button(
                    f"📦 {len(zip_items)} Anonsu ZIP İndir",
                    zbr.getvalue(),
                    file_name=f"imajfm_reji_anonslar_{st.session_state._reji_baslangic_saat.replace(':','-')}.zip",
                    mime="application/zip",
                    use_container_width=True,
                    key="dl_reji_zip"
                )
            else:
                st.markdown("<div class='card a'>⏳ Henüz üretilmiş anons yok. Yukarıdan üretin.</div>",unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════
# FOOTER
# ═════════════════════════════════════════════════════════════════
st.markdown("<hr>",unsafe_allow_html=True)
st.markdown("""
<div style='text-align:center;color:#0d1522;font-size:.65rem;letter-spacing:.1em;padding:5px 0 12px;'>
    İMAJ FM TTS STÜDYO v5 &nbsp;·&nbsp; Delay Reji Modülü &nbsp;·&nbsp; Google Gemini TTS API &nbsp;·&nbsp; 2026
</div>
""",unsafe_allow_html=True)