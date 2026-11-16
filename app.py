"""
╔══════════════════════════════════════════════════════════════════╗
║  İMAJ FM · YAYIN OTOMASYONU (Playout Studio)  v1.1               ║
║  Profesyonel radyo otomasyon modülü — TTS Stüdyo'nun 2. sayfası  ║
║                                                                  ║
║  · Medya kütüphanesi: şarkı · jingle · anons · fon müziği ·      ║
║    reklam (MP3/WAV/OGG/FLAC); sanatçı/etiket/kazanç/intro/cue    ║
║  · Dosyadan VEYA uygulama içinden (yapay ses / TTS arşivi) anons ║
║  · Her parçaya sınırsız katman (overlay): başa · intro'ya sığdır ║
║    · sona · tam saniyeye · önce/sonra; anons başlayınca müzik    ║
║    OTOMATİK kısılır (ducking); anonsa fon müziği/jingle eklenir  ║
║  · Crossfade, fade, ses seviyesi eşitleme (RMS), cue in/out      ║
║  · Otomatik akış (saat çarkı): sanatçı ayrımı, jingle/anons      ║
║    döngüsü, tam süreye oturtma                                   ║
║  · Zaman çizelgesi, önizleme (baştan / seçili öğeden)            ║
║  · Tam yayın çıktısı MP3 veya WAV + akış listesi/telif raporu    ║
║                                                                  ║
║  Kurulum: ana uygulamanın yanında  pages/  klasörüne koyun.      ║
║  pip install streamlit numpy miniaudio lameenc "google-genai>=2.25.0"
╚══════════════════════════════════════════════════════════════════╝
"""
import streamlit as st
import wave, io, zipfile, re, time, datetime, hashlib, json, os, hmac, base64, random, inspect, shutil
import html as _html
from pathlib import Path
import numpy as np
try:
    import miniaudio          # MP3/OGG/FLAC okuma
except Exception:
    miniaudio = None
try:
    import lameenc            # MP3 yazma
except Exception:
    lameenc = None
from google import genai
from google.genai import types

st.set_page_config(page_title="İmaj FM · Yayın Otomasyonu", page_icon="📻",
                   layout="wide", initial_sidebar_state="expanded")

def _ucw():
    try:
        if "width" in inspect.signature(st.button).parameters:
            return {"width": "stretch"}
    except Exception:
        pass
    return {"use_container_width": True}
UCW = _ucw()

def _ucw_df():
    # st.dataframe için genişlik parametresi sürüme göre değişir.
    try:
        ps = inspect.signature(st.dataframe).parameters
        if "use_container_width" in ps:
            return {"use_container_width": True}
        if "width" in ps:
            return {"width": "stretch"}
    except Exception:
        pass
    return {}
UCW_DF = _ucw_df()

# ─────────────────────────────────────────────────────────────────
# DİSK
# ─────────────────────────────────────────────────────────────────
DATA = Path(os.environ.get("IMAJFM_DATA", "imajfm_data"))
PO = DATA / "playout"
MEDIA = PO / "media"
OUT = PO / "out"
TTSC = PO / "tts_cache"
for _p in (DATA, PO, MEDIA, OUT, TTSC):
    _p.mkdir(parents=True, exist_ok=True)

def jload(name, default):
    try:
        return json.loads((DATA / name).read_text(encoding="utf-8"))
    except Exception:
        return default

def jsave(name, obj):
    try:
        tmp = DATA / (name + ".tmp")
        tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(DATA / name)
    except Exception as e:
        st.session_state["_io_err"] = str(e)

def _init(k, v):
    if k not in st.session_state:
        st.session_state[k] = v

# ═════════════════════════════════════════════════════════════════
# SABİTLER
# ═════════════════════════════════════════════════════════════════
SR = 24000
MAX_ARCHIVE = 80

VOICES = {
    "Zephyr":("♀","Parlak · Neşeli"), "Puck":("♂","Enerjik · Hareketli"),
    "Charon":("♂","Bilgilendirici · Açık"), "Kore":("♀","Sıcak · Güven Veren"),
    "Fenrir":("♂","Heyecanlı · Dinamik"), "Aoede":("♀","Akıcı · Doğal"),
    "Leda":("♀","Genç · Enerjik"), "Orus":("♂","Kararlı · Güçlü"),
    "Achird":("♂","Dostane · Samimi"), "Algenib":("♂","Pürüzlü · Özgün"),
    "Algieba":("♂","Yumuşak · Hoş"), "Alnilam":("♂","Sağlam · Güçlü"),
    "Autonoe":("♀","Parlak · İyimser"), "Callirrhoe":("♀","Rahat · Akıcı"),
    "Despina":("♀","Pürüzsüz · Zarif"), "Enceladus":("♂","Yumuşak · Nefes"),
    "Erinome":("♀","Net · Hassas"), "Gacrux":("♂","Olgun · Deneyimli"),
    "Iapetus":("♂","Net · Anlaşılır"), "Laomedeia":("♀","Neşeli · Canlı"),
    "Pulcherrima":("♀","İfadeli · Çarpıcı"), "Rasalgethi":("♂","Profesyonel"),
    "Sadachbia":("♂","Canlı · Hareketli"), "Sadaltager":("♂","Bilgili · Otoriter"),
    "Schedar":("♂","Güçlü · Etkileyici"), "Sulafat":("♀","Sıcak · Davetkar"),
    "Umbriel":("♂","Derin · Gizemli"), "Vindemiatrix":("♀","Nazik · Kibar"),
    "Achernar":("♀","Yumuşak · Hassas"), "Zubenelgenubi":("♂","Rahat · Dengeli"),
}
MODELS = {
    "gemini-3.8-flash-tts":"💎 3.8 Flash  (En Kaliteli)",
    "gemini-3.8-flash-lite-tts":"⚡ 3.8 Flash-Lite  (Hızlı · Ekonomik)",
    "gemini-3.1-flash-tts-preview":"🎭 3.1 Flash Preview  (Köşeli etiketler)",
    "gemini-2.5-pro-preview-tts":"🧪 2.5 Pro Preview",
}
# Eski/geçersiz adlar → güncel Gemini API adı.
MODEL_ALIAS = {
    "gemini-2.5-flash-tts":"gemini-3.8-flash-lite-tts",
    "gemini-2.5-flash-preview-tts":"gemini-3.8-flash-lite-tts",
    "gemini-2.5-flash-lite-preview-tts":"gemini-3.8-flash-lite-tts",
    "gemini-2.5-pro-tts":"gemini-2.5-pro-preview-tts",
}
LANGUAGES = {
    "otomatik":"🌐 Oto","tr-TR":"🇹🇷 Türkçe","en-US":"🇺🇸 EN-US","en-GB":"🇬🇧 EN-UK",
    "de-DE":"🇩🇪 Almanca","fr-FR":"🇫🇷 Fransızca","es-ES":"🇪🇸 İspanyolca","it-IT":"🇮🇹 İtalyanca",
    "pt-BR":"🇧🇷 PT-BR","ru-RU":"🇷🇺 Rusça","ja-JP":"🇯🇵 Japonca","ko-KR":"🇰🇷 Korece",
    "zh-CN":"🇨🇳 Çince","ar-XA":"🇸🇦 Arapça","hi-IN":"🇮🇳 Hintçe","nl-NL":"🇳🇱 Felemenkçe",
    "pl-PL":"🇵🇱 Lehçe","sv-SE":"🇸🇪 İsveççe",
}
STYLE_PRESETS = {
    "— Seçin —":"",
    "📻 Haber Sunucusu":"Profesyonel haber sunucusu gibi net, otoriter ve güven verici bir tonla oku.",
    "🎉 Neşeli & Enerjik":"Çok neşeli ve coşkulu, müzik programı sunuyormuş gibi oku.",
    "🎭 Dramatik & Güçlü":"Dramatik ve etkileyici, büyük sahne duyurusu gibi oku.",
    "🌙 Sakin & Huzurlu":"Sakin, huzurlu ve rahatlatıcı, gece kuşağı tonu ile oku.",
    "🚨 Acil & Hızlı":"Acil haber tonu, hızlı ve yüksek enerjili sesle oku.",
    "☕ Sıcak & Samimi":"Sıcak ve dostça, yakın arkadaşa anlatır gibi oku.",
    "📣 Reklam Sesi":"Profesyonel reklam seslendirmesi, çekici ve ikna edici oku.",
    "📖 Hikaye Anlatıcısı":"Büyüleyici hikaye anlatıcısı gibi ritmik ve ifadeli oku.",
    "⚽ Spor Yorumcusu":"Heyecanlı spor yorumcusu gibi yüksek tempo ile oku.",
    "🎬 Belgesel Sesi":"Derin belgesel anlatıcısı, ağır ve anlamlı tonla oku.",
}
TEMPLATES = {
    "🎙️ Sabah Açılış":"[excitedly] Günaydın! İmaj FM ile sabahın en güzel sesine uyanıyorsunuz!\n[seriously] Bugün haber bültenimizle başlıyoruz... [normal] hoş geldiniz!\n[excitedly] BU SABAH müzik, haber ve çok daha fazlası burada!",
    "🌙 Gece Kapanış":"[whispers] Ve gece yarısına yaklaşırken... İmaj FM sizinle.\n[sighs] Uzun bir günün ardından... kulaklarınıza iyi geceler.\n[whispers] Yarın yeniden buradayız. Tatlı rüyalar.",
    "📢 Özel Duyuru":"[excitedly] DUYURU DUYURU!\n[seriously] Değerli dinleyicilerimiz, önemli bir bildirimiz var.\n[excitedly] BU HAFTA sonu unutulmaz bir etkinlik sizi bekliyor!\n[shouting] KAÇIRMAYIN!",
    "🎵 Müzik Geçişi":"[normal] Ve müziğimiz devam ediyor...\n[whispers] Şimdi sizin için harika bir seçim var.\n[excitedly] İşte o şarkı!",
    "📰 Haber Girişi":"[seriously] İmaj FM Ana Haber Bülteni.\n[pause 0.6]\n[normal] Günün öne çıkan haberleriyle karşınızdayız.\n[seriously] Şimdi tüm ayrıntılarıyla...",
    "🎉 Yarışma":"[excitedly] BÜYÜK YARIŞMA BAŞLIYOR!\n[laughs] Hazır mısınız?\n[shouting] BU HAFTA kazanan sizin aranızdan çıkacak!\n[seriously] Hemen arayın... [excitedly] KAZANMA ŞANSI SİZİN!",
    "☀️ Öğle Bülteni":"[normal] İmaj FM Öğle Bülteni ile karşınızdayız.\n[seriously] Bugünün öne çıkan gelişmeleri...\n[normal] Haberlerden sonra müziğe devam.",
    "🌟 Program Tanıtım":"[excitedly] BU AKŞAM İmaj FM'de çok özel bir program!\n[whispers] Fısıltıyla söyleyelim... sürpriz konuklar var.\n[pause 0.8]\n[excitedly] Saat tam 20:00'de... SADECE İMAJ FM'DE!",
    "🌡️ Hava Durumu":"[normal] İmaj FM hava durumu. İstanbul'da bugün hava parçalı bulutlu, sıcaklık 18 derece. Yağış ihtimali %30.",
}
ETAGS = [("🔥","Coşkulu","[excitedly] "),("🤫","Fısıltı","[whispers] "),("😄","Gülümseyen","[laughs] "),
         ("📰","Ciddi","[seriously] "),("📢","Bağırma","[shouting] "),("😮‍💨","Yorgun","[sighs] "),
         ("🎙️","Normal","[normal] "),("⏸️","Duraklama","[pause 1] ")]

TAG_RE = re.compile(r"\[(excitedly|whispers|laughs|seriously|shouting|sighs|normal)\]", re.I)
PAUSE_RE = re.compile(r"\[(?:pause|bekle)\s*([0-9]+(?:[.,][0-9]+)?)\s*(?:s|sn)?\]", re.I)

CFG_DEF = {"theme":"dark","fsize":100,"norm":True,"trim":True,"comp":False,"fade_ms":40,"head":0.10,"tail":0.30,
           "nums":True,"use_dict":True,"chunk":True,"chunk_chars":800,"max_per_key":10,
           "usd_min":0.015,"custom_model":"","dict":"FM=Ef Em\nDJ=Di Ci\nTRT=Te Er Te"}

# ─────────────────────────────────────────────────────────────────
# OTURUM DURUMU (ana uygulamayla ortak: ayarlar · API havuzu · istatistik)
# ─────────────────────────────────────────────────────────────────
def _load_pool():
    saved = jload("pool.json", {})
    today = datetime.date.today().isoformat()
    used = saved.get("used", []) if saved.get("date") == today else []
    labels = saved.get("labels", [])
    return [{"key": "", "used": int(used[i]) if i < len(used) else 0,
             "label": labels[i] if i < len(labels) else f"API {i+1}"} for i in range(10)]

def save_pool():
    p = st.session_state._pool
    jsave("pool.json", {"date": datetime.date.today().isoformat(),
                        "used": [s["used"] for s in p], "labels": [s["label"] for s in p]})

_init("cfg", {**CFG_DEF, **jload("settings.json", {})})
for _k, _v in CFG_DEF.items():
    st.session_state.cfg.setdefault(_k, _v)
_init("_stats", jload("stats.json", {"calls": 0, "chars": 0, "secs": 0.0}))
_init("_pool", _load_pool())
_init("_active", 0)
_init("_auth", False)
_init("_secrets_loaded", False)

def cfg():
    return st.session_state.cfg

def mpk():
    return int(cfg()["max_per_key"])

def save_look():
    d = jload("settings.json", {})
    d["theme"], d["fsize"] = cfg().get("theme", "dark"), cfg().get("fsize", 100)
    jsave("settings.json", d)

def get_models():
    m = dict(MODELS)
    cm = cfg().get("custom_model", "").strip()
    if cm and cm not in m:
        m[cm] = f"🧪 {cm}"
    return m

def esc(s):
    return _html.escape(str(s))

def slug(s, n=28):
    return re.sub(r"[^\w\-]+", "_", s)[:n].strip("_") or "dosya"

def fmt_t(sec):
    sec = int(max(0, sec))
    return f"{sec//3600:02d}:{(sec%3600)//60:02d}:{sec%60:02d}"

THEMES = {
 "dark": dict(bg="#0b1220", bg2="#0d1626", panel="#162033", panel2="#1b2840", border="#5b7099",
              text="#ffffff", text2="#e6edf7", muted="#c3d0e4", accent="#ff7b7b", link="#9ccbff",
              inp="#0f1a2d", h1a="#ffffff", btn="#c62828", btnfg="#ffffff",
              hdr="linear-gradient(135deg,#17315e 0%,#0f1b30 60%,#0b1220 100%)",
              gbg="#06381b", gfg="#a7f3c0", abg="#3a2800", afg="#ffe08a",
              rbg="#3d0f0f", rfg="#ffc2c2", pbg="#2a1750", pfg="#e6dcff", bbg="#10294d", scheme="dark"),
 "light": dict(bg="#f4f6fb", bg2="#e6ebf5", panel="#ffffff", panel2="#eef2f9", border="#7f8fab",
               text="#0b1220", text2="#1e293b", muted="#334155", accent="#b91c1c", link="#1d4ed8",
               inp="#ffffff", h1a="#0b1220", btn="#c62828", btnfg="#ffffff",
               hdr="linear-gradient(135deg,#ffffff 0%,#e8eefb 70%,#e1e8f5 100%)",
               gbg="#dff5e7", gfg="#0f4d27", abg="#fff0cf", afg="#6b3500",
               rbg="#fde2e2", rfg="#7a1313", pbg="#ece4fd", pfg="#3f1a8a", bbg="#e3edff", scheme="light"),
 "hc": dict(bg="#000000", bg2="#0a0a0a", panel="#121212", panel2="#1c1c1c", border="#ffffff",
            text="#ffffff", text2="#ffffff", muted="#f0f0f0", accent="#ffd60a", link="#5fd0ff",
            inp="#000000", h1a="#ffffff", btn="#ffd60a", btnfg="#000000",
            hdr="linear-gradient(135deg,#1a1a1a 0%,#0a0a0a 100%)",
            gbg="#002b10", gfg="#8dffb0", abg="#2b2000", afg="#ffe45c",
            rbg="#330000", rfg="#ffb3b3", pbg="#20103f", pfg="#ddd0ff", bbg="#001a33", scheme="dark"),
}
LOOKS = {"dark": "🌙 Koyu", "light": "☀️ Açık", "hc": "🔆 Yüksek Kontrast"}
SIZES = {100: "Yazı: Normal", 112: "Yazı: Büyük", 125: "Yazı: Çok büyük"}
TOML_THEME = {
 "dark":  {"base": "dark",  "primaryColor": "#ff7b7b", "backgroundColor": "#0b1220", "secondaryBackgroundColor": "#162033", "textColor": "#ffffff"},
 "light": {"base": "light", "primaryColor": "#b91c1c", "backgroundColor": "#f4f6fb", "secondaryBackgroundColor": "#ffffff", "textColor": "#0b1220"},
 "hc":    {"base": "dark",  "primaryColor": "#ffd60a", "backgroundColor": "#000000", "secondaryBackgroundColor": "#121212", "textColor": "#ffffff"},
}

def write_streamlit_theme(theme):
    # Streamlit'in yerel öğeleri (üst menü, açılır pencereler) bu dosyadaki temayı kullanır.
    try:
        p = Path(".streamlit") / "config.toml"
        p.parent.mkdir(exist_ok=True)
        old = p.read_text(encoding="utf-8") if p.exists() else ""
        out, skip = [], False
        for ln in old.splitlines():
            if ln.strip().startswith("["):
                skip = ln.strip() == "[theme]"
            if not skip:
                out.append(ln)
        out += ["", "[theme]"] + [f'{k} = "{v}"' for k, v in TOML_THEME.get(theme, TOML_THEME["dark"]).items()]
        p.write_text("\n".join(out).strip() + "\n", encoding="utf-8")
    except Exception:
        pass

STATIC_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;600&display=swap');
*,*::before,*::after{box-sizing:border-box;}
html,body,.stApp,[data-testid="stApp"],[data-testid="stAppViewContainer"],.main{background:var(--bg)!important;color:var(--text);font-family:'Inter',sans-serif;}
[data-testid="stHeader"]{background:var(--bg)!important;}
[data-testid="stSidebar"]{background:var(--bg2)!important;border-right:1px solid var(--border)!important;}
[data-testid="stSidebarContent"]{padding:.65rem .75rem;}
h1,h2,h3,h4,h5,h6{color:var(--text)!important;}
[data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li,[data-testid="stMarkdownContainer"] td,[data-testid="stMarkdownContainer"] th,[data-testid="stWidgetLabel"],[data-testid="stWidgetLabel"] p,[data-testid="stWidgetLabel"] label,label,[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p,[data-testid="stRadio"] label p,[data-testid="stCheckbox"] label p,[data-testid="stToggle"] label p,[data-testid="stSlider"] label p,[data-testid="stTickBarMin"],[data-testid="stTickBarMax"],[data-testid="stFileUploader"] label p{color:var(--text)!important;}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p{color:var(--text2)!important;}
.stApp :is(p,li,label,small):not([style*="color"]){color:var(--text)!important;opacity:1!important;}
[data-testid="stWidgetLabel"] *,[data-testid="stWidgetLabel"]{color:var(--text)!important;opacity:1!important;font-weight:600;}
[data-testid="stCaptionContainer"] *,[data-testid="stCaptionContainer"]{color:var(--text2)!important;opacity:1!important;}
[data-testid="stSidebar"] :is(p,li,label,small){color:var(--text)!important;opacity:1!important;}
[data-baseweb="radio"]>div:first-child,[data-baseweb="checkbox"]>span:first-child{border-color:var(--text2)!important;}
[data-testid="stMarkdownContainer"] code{background:var(--panel2)!important;color:var(--link)!important;border:1px solid var(--border);border-radius:4px;padding:0 4px;}
[data-testid="stMarkdownContainer"] a{color:var(--link)!important;}
.hdr{background:var(--hdr);border:1px solid var(--border);border-radius:16px;padding:22px 28px;margin-bottom:18px;position:relative;overflow:hidden;}
.hdr::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#e02020,#f07800,#e02020);background-size:200%;animation:scan 3s linear infinite;}
@keyframes scan{0%{background-position:0%}100%{background-position:200%}}
.hdr h1{font-family:'Syne',sans-serif;font-size:1.75rem;font-weight:800;margin:0 0 4px;background:linear-gradient(90deg,var(--h1a) 25%,#e02020 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.hdr p{margin:0;color:var(--text2);font-size:.84rem;letter-spacing:.03em;}
.ldot{display:inline-block;width:7px;height:7px;background:#ff3a3a;border-radius:50%;margin-right:7px;animation:blink 1.2s ease-in-out infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.12}}
.sl{font-family:'Syne',sans-serif;font-size:.7rem;font-weight:800;letter-spacing:.14em;color:var(--accent);text-transform:uppercase;margin:16px 0 6px;display:block;}
.sl2{font-family:'Syne',sans-serif;font-size:.64rem;font-weight:800;letter-spacing:.12em;color:var(--link);text-transform:uppercase;margin:10px 0 4px;display:block;}
.mbox{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:12px;text-align:center;}
.mbox .v{font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;color:var(--accent);}
.mbox .l{font-size:.64rem;letter-spacing:.1em;color:var(--text2);text-transform:uppercase;margin-top:2px;font-weight:600;}
.mbox.g .v{color:#16a34a;}.mbox.b .v{color:#2563eb;}.mbox.a .v{color:#d97706;}.mbox.p .v{color:#7c3aed;}
.card{background:var(--panel);border:1px solid var(--border);border-radius:9px;padding:11px 14px;margin:7px 0;font-size:.88rem;color:var(--text);line-height:1.5;}
.card.b{border-left:4px solid #3a7bd5;background:var(--bbg);}
.card.g{border-left:4px solid #22c55e;background:var(--gbg);color:var(--gfg);}
.card.a{border-left:4px solid #f59e0b;background:var(--abg);color:var(--afg);}
.card.r{border-left:4px solid #ef4444;background:var(--rbg);color:var(--rfg);}
.card.p{border-left:4px solid #a78bfa;background:var(--pbg);color:var(--pfg);}
.card code{color:inherit;font-weight:700;}
[data-testid="stButton"]>button,[data-testid="stDownloadButton"]>button,[data-testid="stBaseButton-secondary"]{font-family:'Syne',sans-serif;font-weight:700;letter-spacing:.03em;border-radius:9px;transition:all .2s;background:var(--panel)!important;border:1px solid var(--border)!important;color:var(--text)!important;}
[data-testid="stButton"]>button p,[data-testid="stDownloadButton"]>button p{color:var(--text)!important;}
[data-testid="stButton"]>button:hover,[data-testid="stDownloadButton"]>button:hover{border-color:var(--link)!important;color:var(--link)!important;}
[data-testid="stButton"]>button[kind="primary"],[data-testid^="stBaseButton-primary"]{background:var(--btn)!important;border:none!important;color:var(--btnfg)!important;}
html body .stApp [data-testid^="stBaseButton-primary"] *,html body .stApp button[kind="primary"] *{color:var(--btnfg)!important;}
[data-testid="stButton"]>button[kind="primary"]:hover{filter:brightness(1.12);transform:translateY(-1px);}
button:disabled{opacity:.5!important;}
input,textarea,[data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="textarea"]{background:var(--inp)!important;color:var(--text)!important;-webkit-text-fill-color:var(--text)!important;caret-color:var(--accent)!important;}
[data-baseweb="input"],[data-baseweb="textarea"],[data-baseweb="select"]>div{border:1px solid var(--border)!important;border-radius:9px!important;}
[data-testid="stTextArea"] textarea{font-size:.95rem!important;line-height:1.65!important;border-radius:10px!important;}
textarea:focus,input:focus{border-color:var(--accent)!important;}
::placeholder{color:var(--muted)!important;opacity:1!important;-webkit-text-fill-color:var(--muted)!important;}
[data-baseweb="select"]>div{background:var(--inp)!important;}
[data-baseweb="select"] *{color:var(--text)!important;}
[data-baseweb="select"] svg{fill:var(--text2)!important;}
[data-baseweb="popover"],[data-baseweb="popover"]>div,[data-baseweb="menu"],ul[role="listbox"]{background:var(--panel)!important;border:1px solid var(--border);}
[data-baseweb="popover"] li,[role="option"],[data-baseweb="menu"] li{background:var(--panel)!important;color:var(--text)!important;}
[role="option"]:hover,[data-baseweb="menu"] li:hover,li[aria-selected="true"]{background:var(--panel2)!important;color:var(--link)!important;}
[data-testid="stNumberInput"] button{background:var(--panel2)!important;color:var(--text)!important;border-color:var(--border)!important;}
[data-testid="stAudio"]{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:8px;}
[data-testid="stExpander"] details,[data-testid="stSidebar"] details{background:var(--panel)!important;border:1px solid var(--border)!important;border-radius:9px!important;margin-bottom:5px!important;}
details summary p{font-family:'Syne',sans-serif!important;font-size:.82rem!important;font-weight:700!important;color:var(--text)!important;}
details summary{color:var(--text)!important;}
[data-testid="stIconMaterial"],[data-testid="stExpanderToggleIcon"],span[class*="material"]{font-family:'Material Symbols Rounded','Material Symbols Outlined','Material Icons'!important;font-weight:400!important;font-style:normal!important;letter-spacing:normal!important;text-transform:none!important;white-space:nowrap!important;font-feature-settings:'liga'!important;-webkit-font-feature-settings:'liga'!important;line-height:1!important;font-size:1.35rem!important;color:var(--text2)!important;}
details summary{padding:9px 12px!important;}
details summary:hover,details summary:hover p,details[open]>summary,details[open]>summary p{color:var(--accent)!important;}
details summary svg{fill:var(--text2)!important;color:var(--text2)!important;}
[data-testid="stTabs"] [data-baseweb="tab-list"]{background:transparent!important;border-bottom:1px solid var(--border);gap:0;overflow-x:auto;}
[data-testid="stTabs"] [data-baseweb="tab"]{background:transparent!important;color:var(--text2)!important;font-family:'Syne',sans-serif!important;font-weight:700!important;font-size:.8rem!important;letter-spacing:.04em!important;padding:10px 14px!important;border-bottom:2px solid transparent!important;white-space:nowrap;}
[data-testid="stTabs"] [data-baseweb="tab"] p{color:inherit!important;}
[data-testid="stTabs"] [aria-selected="true"]{color:var(--accent)!important;border-bottom:3px solid var(--accent)!important;}
[data-testid="stFileUploaderDropzone"]{background:var(--panel2)!important;border:1px dashed var(--border)!important;}
[data-testid="stFileUploaderDropzone"] *{color:var(--text2)!important;}
[data-testid="stFileUploaderDropzone"] button{color:var(--text)!important;background:var(--panel)!important;border:1px solid var(--border)!important;}
[data-testid="stAlert"]{background:var(--panel2)!important;border:1px solid var(--border)!important;}
[data-testid="stAlert"] *{color:var(--text)!important;}
[data-testid="stCode"] pre,pre{background:var(--panel2)!important;border:1px solid var(--border);}
pre code,pre code span{color:var(--text)!important;}
[data-testid="stProgress"] *{color:var(--text2)!important;}
.qbar{background:var(--border);border-radius:4px;height:5px;margin:3px 0;overflow:hidden;}
.qbar-f{height:100%;border-radius:4px;transition:width .4s;}
.arc-card{background:var(--panel);border:1px solid var(--border);border-radius:9px;padding:11px 13px;margin-bottom:6px;}
.arc-card:hover{border-color:var(--link);}
.arc-meta{display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;}
.arc-voice{font-family:'Syne',sans-serif;font-size:.82rem;font-weight:800;color:var(--link);}
.arc-ts{font-size:.7rem;color:var(--muted);font-family:'JetBrains Mono',monospace;}
.arc-info{font-size:.72rem;color:var(--text2);margin-bottom:5px;}
.arc-text{font-size:.82rem;color:var(--text);line-height:1.4;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.fav-card{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:9px 12px;margin:5px 0;}
.fav-name{font-family:'Syne',sans-serif;font-size:.8rem;font-weight:800;color:var(--text);}
.fav-prev{font-size:.74rem;color:var(--text2);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.ttbl{width:100%;border-collapse:collapse;font-size:.74rem;}
.ttbl th{color:var(--accent);font-family:'Syne',sans-serif;font-size:.62rem;letter-spacing:.1em;text-transform:uppercase;padding:4px 3px;border-bottom:1px solid var(--border);text-align:left;}
.ttbl td{padding:4px 3px;color:var(--text);border-bottom:1px solid var(--border);vertical-align:top;}
.tc{color:var(--link);font-family:'JetBrains Mono',monospace;font-size:.76rem;font-weight:600;}
.wf-wrap{background:var(--panel2);border:1px solid var(--border);border-radius:8px;padding:4px 6px;margin:6px 0;}
.tiny{font-size:.76rem;color:var(--text2);margin:3px 0 8px;}
[data-testid="stExpander"] details{box-shadow:none;}
hr{border-color:var(--border)!important;margin:11px 0!important;}
::-webkit-scrollbar{width:5px;height:5px;}::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px;}
@media (max-width:768px){
.hdr{padding:16px 16px;}.hdr h1{font-size:1.25rem;}.hdr p{font-size:.78rem;}
.sl{font-size:.78rem;}.sl2{font-size:.72rem;}.tiny{font-size:.82rem;}.card{font-size:.92rem;}
.mbox .v{font-size:1.1rem;}.mbox .l{font-size:.68rem;}
[data-testid="stTabs"] [data-baseweb="tab"]{font-size:.86rem!important;padding:10px 12px!important;}
details summary p{font-size:.9rem!important;}
[data-testid="stMarkdownContainer"] p,label{font-size:1rem;}
}
"""

def inject_css():
    c = cfg()
    th = c.get("theme", "dark")
    t = THEMES.get(th, THEMES["dark"])
    fs = int(c.get("fsize", 100))
    root = ":root{" + ";".join(f"--{k}:{v}" for k, v in t.items() if k != "scheme") + f";color-scheme:{t['scheme']}" + "}"
    root += f"html{{font-size:{fs}%;}}@media (max-width:768px){{html{{font-size:{fs + 6}%;}}}}"
    if th == "hc":
        root += ".card,.mbox,.arc-card,.fav-card,[data-testid=\"stExpander\"] details{border-width:2px!important;}"
    st.markdown("<style>" + root + STATIC_CSS + "</style>", unsafe_allow_html=True)

def _look_cb(src):
    ss = st.session_state
    th, fs = ss[f"look_theme{src}"], int(ss[f"look_size{src}"])
    cfg()["theme"], cfg()["fsize"] = th, fs
    for k in ("", "_sb"):
        ss[f"look_theme{k}"], ss[f"look_size{k}"] = th, fs
    write_streamlit_theme(th)
    save_look()

def look_controls(sfx):
    th = cfg().get("theme", "dark")
    fs = int(cfg().get("fsize", 100))
    _init(f"look_theme{sfx}", th if th in LOOKS else "dark")
    _init(f"look_size{sfx}", fs if fs in SIZES else 100)
    c1, c2 = st.columns(2)
    c1.selectbox("Tema", list(LOOKS), format_func=LOOKS.get, key=f"look_theme{sfx}",
                 on_change=_look_cb, args=(sfx,), label_visibility="collapsed")
    c2.selectbox("Yazı boyutu", list(SIZES), format_func=SIZES.get, key=f"look_size{sfx}",
                 on_change=_look_cb, args=(sfx,), label_visibility="collapsed")

inject_css()
if not st.session_state.get("_toml"):
    write_streamlit_theme(cfg().get("theme", "dark"))
    st.session_state["_toml"] = True

# ─────────────────────────────────────────────────────────────────
# GİRİŞ (ana uygulamada giriş yapıldıysa tekrar sorulmaz)
# ─────────────────────────────────────────────────────────────────
def check_login(u, p):
    try:
        su, sp = st.secrets.get("APP_USER", "kenan"), st.secrets.get("APP_PASS", "imajfm")
    except Exception:
        su, sp = "kenan", "imajfm"
    return hmac.compare_digest(u.encode(), str(su).encode()) and hmac.compare_digest(p.encode(), str(sp).encode())

if not st.session_state._auth:
    _, _c, _ = st.columns([1, 1.05, 1])
    with _c:
        st.markdown("<div class='hdr' style='margin-top:60px;'><h1>📻 Yayın Otomasyonu</h1><p>Güvenli giriş</p></div>", unsafe_allow_html=True)
        with st.form("login_po"):
            _u = st.text_input("Kullanıcı", placeholder="👤  kullanıcı adı", label_visibility="collapsed")
            _p = st.text_input("Şifre", type="password", placeholder="🔑  şifre", label_visibility="collapsed")
            if st.form_submit_button("Bağlan →", type="primary", **UCW):
                if check_login(_u, _p):
                    st.session_state._auth = True
                    st.rerun()
                else:
                    st.error("❌ Hatalı giriş.")
    st.stop()

# ═════════════════════════════════════════════════════════════════
# API HAVUZU
# ═════════════════════════════════════════════════════════════════
def load_secrets_once():
    if st.session_state._secrets_loaded:
        return
    st.session_state._secrets_loaded = True
    for i in range(10):
        try:
            v = st.secrets.get(f"GEMINI_API_KEY_{i+1}", "")
            if not v and i == 0:
                v = st.secrets.get("GEMINI_API_KEY", "")
            if v and not st.session_state._pool[i]["key"]:
                st.session_state._pool[i]["key"] = v
                st.session_state[f"key_{i}"] = v
        except Exception:
            pass

load_secrets_once()

def get_active_key():
    pool, idx, m = st.session_state._pool, st.session_state._active, mpk()
    for _ in range(10):
        s = pool[idx]
        if s["key"].strip() and s["used"] < m:
            st.session_state._active = idx
            return s["key"].strip(), idx
        idx = (idx + 1) % 10
    return None, -1

def consume(idx, chars=0):
    p, s = st.session_state._pool, st.session_state._stats
    p[idx]["used"] += 1
    s["calls"] += 1
    s["chars"] += chars
    _d = datetime.date.today().isoformat()
    dl = s.setdefault("daily", {})
    dl[_d] = dl.get(_d, 0) + 1
    for _k in sorted(dl)[:-60]:
        dl.pop(_k, None)
    if p[idx]["used"] >= mpk():
        st.session_state._active = (idx + 1) % 10
    save_pool()
    jsave("stats.json", s)

def exhaust(idx):
    st.session_state._pool[idx]["used"] = mpk()
    st.session_state._active = (idx + 1) % 10
    save_pool()

def pool_stats():
    p, m = st.session_state._pool, mpk()
    loaded = sum(1 for s in p if s["key"].strip())
    used = sum(s["used"] for s in p if s["key"].strip())
    remain = sum(max(0, m - s["used"]) for s in p if s["key"].strip())
    return loaded, used, remain

def pool_reset(i):
    st.session_state._pool[i]["used"] = 0
    save_pool()

def pool_activate(i):
    st.session_state._active = i

def pool_delete(i):
    st.session_state._pool[i] = {"key": "", "used": 0, "label": f"API {i+1}"}
    st.session_state[f"key_{i}"] = ""
    st.session_state[f"lbl_{i}"] = f"API {i+1}"
    save_pool()

# ═════════════════════════════════════════════════════════════════
# METİN ÖN İŞLEME
# ═════════════════════════════════════════════════════════════════
def num_tr(n: int) -> str:
    if n == 0:
        return "sıfır"
    O = ["", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
    T = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]
    def h(x):
        y, r = divmod(x, 100); t, o = divmod(r, 10); w = []
        if y > 1: w.append(O[y])
        if y: w.append("yüz")
        if t: w.append(T[t])
        if o: w.append(O[o])
        return " ".join(w)
    parts = []
    for div, name in ((10**9, "milyar"), (10**6, "milyon"), (1000, "bin")):
        q, n = divmod(n, div)
        if q:
            parts.append("bin" if (name == "bin" and q == 1) else f"{h(q)} {name}")
    if n:
        parts.append(h(n))
    return " ".join(parts)

def prepare_text(t: str) -> str:
    c = cfg()
    if c["nums"]:
        t = re.sub(r"%\s?(\d{1,9})", lambda m: "yüzde " + num_tr(int(m.group(1))), t)
        def _time(m):
            hh, mm = int(m.group(1)), int(m.group(2))
            return num_tr(hh) + ("" if mm == 0 else (" sıfır " + num_tr(mm) if mm < 10 else " " + num_tr(mm)))
        t = re.sub(r"(?<!\d)(\d{1,2}):(\d{2})(?!\d)", _time, t)
        t = re.sub(r"(?<![\d.,])(\d{1,12})(?!\d|[.,]\d)", lambda m: num_tr(int(m.group(1))), t)
    if c["use_dict"]:
        for line in c["dict"].splitlines():
            if "=" in line:
                a, b = line.split("=", 1)
                a, b = a.strip(), b.strip()
                if a:
                    t = re.sub(r"(?<!\w)" + re.escape(a) + r"(?!\w)", lambda m, b=b: b, t)
    return t

def split_segments(text):
    out, pos = [], 0
    for m in PAUSE_RE.finditer(text):
        seg = text[pos:m.start()].strip()
        if seg:
            out.append(("t", seg))
        out.append(("p", min(float(m.group(1).replace(",", ".")), 15.0)))
        pos = m.end()
    tail = text[pos:].strip()
    if tail:
        out.append(("t", tail))
    return out

def chunk_text(t, limit):
    if len(t) <= limit:
        return [t]
    sents = re.split(r"(?<=[.!?…])\s+", t)
    chunks, cur = [], ""
    for s in sents:
        if cur and len(cur) + len(s) + 1 > limit:
            chunks.append(cur); cur = s
        else:
            cur = (cur + " " + s).strip()
    if cur:
        chunks.append(cur)
    return chunks

def count_calls(text):
    n = 0
    for kind, val in split_segments(prepare_text(text)):
        if kind == "t":
            n += len(chunk_text(val, cfg()["chunk_chars"])) if cfg()["chunk"] else 1
    return n

# ═════════════════════════════════════════════════════════════════
# SES İŞLEME
# ═════════════════════════════════════════════════════════════════
def pcm2wav(pcm: bytes, rate=SR, ch=1, sw=2) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(ch); wf.setsampwidth(sw); wf.setframerate(rate)
        wf.writeframes(pcm)
    return buf.getvalue()

def wav_dur(b: bytes) -> float:
    try:
        with wave.open(io.BytesIO(b), "rb") as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        return 0.0

def read_wav_np(b: bytes):
    with wave.open(io.BytesIO(b), "rb") as w:
        ch, sw, sr = w.getnchannels(), w.getsampwidth(), w.getframerate()
        raw = w.readframes(w.getnframes())
    if sw != 2:
        raise ValueError("Yalnızca 16-bit PCM WAV destekleniyor.")
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        a = a[: len(a) // ch * ch].reshape(-1, ch).mean(axis=1)
    if sr != SR and len(a) > 1:
        a = np.interp(np.linspace(0, len(a) - 1, int(len(a) * SR / sr)),
                      np.arange(len(a)), a).astype(np.float32)
    return a, SR

def np_to_wav(a) -> bytes:
    return pcm2wav((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())

def silence(sec: float) -> bytes:
    return b"\x00\x00" * int(sec * SR)

def postprocess(pcm: bytes) -> bytes:
    c = cfg()
    a = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
    if len(a) == 0:
        return pcm
    if c["trim"]:
        idx = np.where(np.abs(a) > 0.008)[0]
        if len(idx):
            a = a[max(0, idx[0] - int(0.05 * SR)): idx[-1] + int(0.10 * SR)]
    if c["comp"]:
        a = np.tanh(a * 1.9) / np.tanh(1.9)
    if c["norm"]:
        pk = float(np.abs(a).max())
        if pk > 0:
            a = a * (0.89 / pk)
    f = int(c["fade_ms"] / 1000 * SR)
    if f > 0 and len(a) > 2 * f:
        a[:f] *= np.linspace(0, 1, f)
        a[-f:] *= np.linspace(1, 0, f)
    a = np.concatenate([np.zeros(int(c["head"] * SR), np.float32), a,
                        np.zeros(int(c["tail"] * SR), np.float32)])
    return (np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes()

def waveform_svg(wav: bytes, w=600, h=54, bars=110) -> str:
    try:
        a, _ = read_wav_np(wav)
    except Exception:
        return ""
    if len(a) == 0:
        return ""
    step = max(1, len(a) // bars)
    peaks = [float(np.abs(a[i:i + step]).max()) for i in range(0, len(a), step)][:bars]
    bw = w / len(peaks)
    rects = "".join(
        f"<rect x='{i*bw:.1f}' y='{(h-max(2, p*h))/2:.1f}' width='{bw*0.7:.1f}' "
        f"height='{max(2, p*h):.1f}' rx='1' fill='#e05252'/>" for i, p in enumerate(peaks))
    return (f"<div class='wf-wrap'><svg viewBox='0 0 {w} {h}' width='100%' height='{h}' "
            f"preserveAspectRatio='none'>{rects}</svg></div>")

# ═════════════════════════════════════════════════════════════════
# MP3 / DECODE / YAYIN MOTORU  (44.1 kHz stereo, diske akışlı yazım)
# ═════════════════════════════════════════════════════════════════
SR2 = 44100
MP3_OK = lameenc is not None

def smooth(env, k):
    k = max(1, int(k))
    pad = np.pad(env, (k // 2, k - k // 2), mode="edge")
    c = np.concatenate([[0.0], np.cumsum(pad, dtype=np.float64)])
    return ((c[k:] - c[:-k]) / k)[:len(env)].astype(np.float32)

def decode_mono(data) -> np.ndarray:
    data = bytes(data)
    if miniaudio is not None:
        d = miniaudio.decode(data, output_format=miniaudio.SampleFormat.SIGNED16, nchannels=1, sample_rate=SR)
        return np.frombuffer(d.samples, dtype=np.int16).astype(np.float32) / 32768.0
    if data[:4] == b"RIFF":
        return read_wav_np(data)[0]
    raise RuntimeError("MP3 okumak için: pip install miniaudio")

def decode_stereo(data) -> np.ndarray:
    data = bytes(data)
    if miniaudio is not None:
        d = miniaudio.decode(data, output_format=miniaudio.SampleFormat.SIGNED16, nchannels=2, sample_rate=SR2)
        a = np.frombuffer(d.samples, dtype=np.int16).astype(np.float32) / 32768.0
        return a[: len(a) // 2 * 2].reshape(-1, 2)
    if data[:4] == b"RIFF":
        with wave.open(io.BytesIO(data), "rb") as w:
            ch, sw, sr = w.getnchannels(), w.getsampwidth(), w.getframerate()
            raw = w.readframes(w.getnframes())
        if sw != 2:
            raise ValueError("Yalnızca 16-bit WAV destekleniyor.")
        a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        a = a[: len(a) // ch * ch].reshape(-1, ch)
        a = np.stack([a[:, 0], a[:, 1] if ch > 1 else a[:, 0]], axis=1)
        if sr != SR2 and len(a) > 1:
            n = int(len(a) * SR2 / sr)
            idx = np.linspace(0, len(a) - 1, n)
            a = np.stack([np.interp(idx, np.arange(len(a)), a[:, c]) for c in (0, 1)], axis=1).astype(np.float32)
        return a
    raise RuntimeError("MP3 okumak için: pip install miniaudio")

def mono_to_st(a) -> np.ndarray:
    if len(a) == 0:
        return np.zeros((0, 2), np.float32)
    n = int(len(a) * SR2 / SR)
    x = np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a).astype(np.float32)
    return np.stack([x, x], axis=1)

def wav_to_st(wav: bytes) -> np.ndarray:
    return mono_to_st(read_wav_np(wav)[0])

def wav_to_mp3(wav: bytes, kbps=192):
    if lameenc is None:
        return None
    a, _ = read_wav_np(wav)
    e = lameenc.Encoder()
    e.set_bit_rate(kbps); e.set_in_sample_rate(SR); e.set_channels(1); e.set_quality(2)
    return bytes(e.encode((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes()) + e.flush())

@st.cache_data(show_spinner=False, max_entries=20)
def mp3_bytes(wav: bytes):
    try:
        return wav_to_mp3(wav)
    except Exception:
        return None

def rms_norm(a, target_db=-16.0):
    if len(a) == 0:
        return a
    rms = float(np.sqrt(np.mean(np.square(a[::4]))))
    if rms < 1e-5:
        return a
    g = 10 ** ((target_db - 20 * np.log10(rms)) / 20)
    pk = float(np.abs(a).max())
    if pk * g > 0.97:
        g = 0.97 / pk
    return a * np.float32(g)

def _guard(a):
    pk = float(np.abs(a).max()) if len(a) else 0.0
    return a * np.float32(0.98 / pk) if pk > 0.98 else a

def _duck_env(n, start, length, duck_db, ramp=0.3):
    env = np.ones(n, np.float32)
    s, e = max(0, start), min(n, start + length)
    if e > s:
        env[s:e] = 10 ** (-duck_db / 20)
    return smooth(env, int(ramp * SR2))

def _fade(a, fi, fo):
    n = len(a)
    if fi > 0 and n:
        fi = min(fi, n); a[:fi] *= np.linspace(0, 1, fi, dtype=np.float32)[:, None]
    if fo > 0 and n:
        fo = min(fo, n); a[-fo:] *= np.linspace(1, 0, fo, dtype=np.float32)[:, None]
    return a

def _overlay(seg, voice, start, duck_db):
    start = max(0, start)
    need = start + len(voice)
    if need > len(seg):
        seg = np.concatenate([seg, np.zeros((need - len(seg), 2), np.float32)])
    out = seg * _duck_env(len(seg), start, len(voice), duck_db)[:, None]
    out[start:start + len(voice)] += voice
    return _guard(out)

def _bed_mix(voice, bed, o):
    pre, post = int(float(o["bed_pre"]) * SR2), int(float(o["bed_post"]) * SR2)
    total = pre + len(voice) + post
    if len(bed) == 0:
        return voice
    if len(bed) >= total:
        bed = bed[:total]
    else:
        bed = np.tile(bed, (int(np.ceil(total / len(bed))), 1))[:total]
    bed = rms_norm(bed, float(o["target_db"])) * np.float32(10 ** (float(o["bed_level"]) / 20))
    bed = bed * _duck_env(total, pre, len(voice), float(o["bed_duck"]))[:, None]
    bed = _fade(bed, int(0.3 * SR2), int(1.5 * SR2))
    bed[pre:pre + len(voice)] += voice
    return _guard(bed)

def mix_music(voice_wav, music_data, level_db, duck_db, pre, post):
    v, _ = read_wav_np(voice_wav)
    m = decode_mono(music_data)
    if len(m) == 0:
        raise ValueError("Müzik dosyası boş.")
    p, q = int(pre * SR), int(post * SR)
    total = p + len(v) + q
    m = np.tile(m, int(np.ceil(total / len(m))))[:total]
    env = np.ones(total, np.float32)
    env[p:p + len(v)] = 10 ** (-duck_db / 20)
    env = smooth(env, int(0.35 * SR))
    m = m * env * (10 ** (level_db / 20))
    fo = min(len(m), int(1.5 * SR))
    m[-fo:] *= np.linspace(1, 0, fo)
    out = m.copy()
    out[p:p + len(v)] += v
    pk = float(np.abs(out).max())
    if pk > 0.95:
        out *= 0.95 / pk
    return np_to_wav(out)

def fill_vars(text, ctx):
    t = text
    for k, v in ctx.items():
        t = t.replace("{" + k + "}", v)
    return t

class _Sink:
    def __init__(self, path, fmt, kbps):
        self.fmt, self.n, self.path = fmt, 0, path
        if fmt == "mp3":
            if lameenc is None:
                raise RuntimeError("MP3 çıktı için: pip install lameenc")
            self.f = open(path, "wb")
            self.enc = lameenc.Encoder()
            self.enc.set_bit_rate(int(kbps)); self.enc.set_in_sample_rate(SR2)
            self.enc.set_channels(2); self.enc.set_quality(2)
        else:
            self.w = wave.open(str(path), "wb")
            self.w.setnchannels(2); self.w.setsampwidth(2); self.w.setframerate(SR2)
    limit = 0
    def write(self, a):
        if len(a) == 0:
            return
        if self.limit:
            room = self.limit - self.n
            if room <= 0:
                return
            if len(a) >= room:
                a = a[:room].copy()
                _fade(a, 0, min(len(a), int(0.6 * SR2)))
        b = np.ascontiguousarray((np.clip(a, -1, 1) * 32767).astype(np.int16)).tobytes()
        self.n += len(a)
        if self.fmt == "mp3":
            self.f.write(self.enc.encode(b))
        else:
            self.w.writeframes(b)
    def close(self):
        if self.fmt == "mp3":
            self.f.write(self.enc.flush()); self.f.close()
        else:
            self.w.close()
    def abort(self):
        try: self.close()
        except Exception: pass
        try: Path(self.path).unlink()
        except Exception: pass

# ═════════════════════════════════════════════════════════════════
# GEMINI ÇAĞRILARI
# ═════════════════════════════════════════════════════════════════
TAG_STYLE = {"excitedly":"excited and energetic","whispers":"whispering","laughs":"cheerful, smiling",
             "seriously":"serious, newsreader tone","shouting":"loud and forceful",
             "sighs":"tired, sighing","normal":""}

def is_new_schema(model):
    """3.8+ modeller speech_metadata kullanır; 3.1 ve 2.5 düz metin + köşeli etiket."""
    return not (model.startswith("gemini-3.1") or model.startswith("gemini-2.5"))

def _turn(text, style="", speaker=None):
    """[excitedly] vb. etiketleri speech_metadata.style'a, [laughs]/[sighs]'i <laugh>/<sigh>'a çevirir."""
    parts = [style.strip()] if style.strip() else []
    first = TAG_RE.search(text)
    if first and TAG_STYLE.get(first.group(1).lower()):
        parts.append(TAG_STYLE[first.group(1).lower()])
    t = re.sub(r"\[laughs\]", "<laugh>", text, flags=re.I)
    t = re.sub(r"\[sighs\]", "<sigh>", t, flags=re.I)
    t = re.sub(r"[ \t]+", " ", TAG_RE.sub("", t)).strip()
    ann = {"type": "speech_metadata"}
    if speaker: ann["speaker"] = speaker
    if parts: ann["style"] = ", ".join(parts)
    item = {"type": "text", "text": t}
    if len(ann) > 1: item["annotations"] = [ann]
    return item

def _audio_from_interaction(it) -> bytes:
    try:
        d = it.output_audio.data
    except Exception:
        d = None
    if not d:
        raise RuntimeError("Model ses döndürmedi (metin filtreye takılmış veya çok uzun olabilir).")
    b = base64.b64decode(d) if isinstance(d, str) else bytes(d)
    if b[:4] == b"RIFF":      # 3.8 modelleri WAV döndürür -> ham PCM'e çevir
        with wave.open(io.BytesIO(b), "rb") as w:
            return w.readframes(w.getnframes())
    return b                   # 3.1 / 2.5: ham 24 kHz PCM

def make_client(api_key):
    # Interactions/TTS uçları v1beta'dadır; SDK varsayılanı v1 olduğundan 404 verebilir.
    return genai.Client(api_key=api_key, http_options=types.HttpOptions(api_version="v1beta"))

def _interaction(api_key, model, input_, speech_cfg):
    c = make_client(api_key)
    if not hasattr(c, "interactions"):
        raise RuntimeError('google-genai sürümü eski. Güncelleyin: pip install -U "google-genai>=2.25.0"')
    it = c.interactions.create(model=model, input=input_, response_format={"type": "audio"},
                               generation_config={"speech_config": speech_cfg})
    return _audio_from_interaction(it)

FALLBACK = ["gemini-3.8-flash-lite-tts", "gemini-3.1-flash-tts-preview", "gemini-2.5-pro-preview-tts"]

def _is_404(e):
    m = str(e)
    return "404" in m or "NOT_FOUND" in m or "not_found" in m

def _with_fallback(model, fn):
    """Model 404 verirse sıradaki TTS modelini dener; çalışanı hatırlar."""
    orig = MODEL_ALIAS.get(model, model)
    fixed = st.session_state.get("_model_fix", {}).get(orig, orig)
    chain = [fixed] + [m for m in FALLBACK if m != fixed]
    last = None
    for m in chain:
        try:
            r = fn(m)
            if m != fixed:
                st.session_state.setdefault("_model_fix", {})[orig] = m
                st.toast(f"ℹ️ {fixed} bulunamadı → {m} kullanıldı")
            return r
        except Exception as e:
            if _is_404(e):
                last = e
                continue
            raise
    raise RuntimeError("Hiçbir TTS modeli bu anahtarla bulunamadı (404). Sidebar > Ayarlar > "
                       "'Anahtarımın TTS modellerini listele' ile erişimi kontrol edin.") from last

def _single_call(api_key, model, text, voice, lang, style):
    def go(m):
        if is_new_schema(m):
            inp = [{"type": "user_input", "content": [_turn(text, style)]}]
        else:
            inp = f"{style}\n\n{text}" if style.strip() else text
        return _interaction(api_key, m, inp, [{"voice": voice}])
    return _with_fallback(model, go)

def _multi_call(api_key, model, text, sp1, v1, sp2, v2, lang):
    def go(m):
        if is_new_schema(m):
            names = {sp1.lower(): sp1, sp2.lower(): sp2}
            items = []
            for line in text.splitlines():
                if not line.strip():
                    continue
                mm = re.match(r"^\s*([^:]{1,40}):\s*(.*)$", line)
                if mm and mm.group(1).strip().lower() in names:
                    items.append([names[mm.group(1).strip().lower()], mm.group(2)])
                elif items:
                    items[-1][1] += " " + line.strip()
            if not items:
                raise ValueError("Diyalog satırı bulunamadı (Ad: metin biçiminde olmalı).")
            content = [_turn(t, "", sp) for sp, t in items]
            return _interaction(api_key, m, [{"type": "user_input", "content": content}],
                                {"speakers": [{"speaker": sp1, "voice": v1}, {"speaker": sp2, "voice": v2}]})
        return _interaction(api_key, m, text,
                            [{"speaker": sp1, "voice": v1}, {"speaker": sp2, "voice": v2}])
    return _with_fallback(model, go)

def list_tts_models(api_key):
    c = make_client(api_key)
    out = []
    for m in c.models.list():
        n = getattr(m, "name", "") or ""
        if "tts" in n.lower():
            out.append(n.replace("models/", ""))
    return sorted(out)

def run_tts(call, chars):
    """Anahtar rotasyonu + yeniden deneme. call(api_key) -> pcm bytes"""
    last = None
    for attempt in range(4):
        key, idx = get_active_key()
        if key is None:
            raise RuntimeError("Kullanılabilir API anahtarı kalmadı.")
        try:
            raw = call(key)
            consume(idx, chars)
            return raw
        except Exception as e:
            last = e
            msg = str(e)
            low = msg.lower()
            if isinstance(e, (RuntimeError, ValueError)) and "429" not in msg:
                raise                      # bizim hatalarımız: tekrar denemenin anlamı yok
            if "INVALID_ARGUMENT" in msg:
                raise                      # 400: istek biçimi/model adı hatası, tekrar deneme
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in low:
                exhaust(idx); continue
            if "API_KEY_INVALID" in msg or "401" in msg or "403" in msg or "api key" in low:
                exhaust(idx); continue
            time.sleep(1.2 * (attempt + 1))
    raise last if last else RuntimeError("Bilinmeyen hata")

def synthesize(text, voice, model, lang, style):
    segs = split_segments(prepare_text(text))
    pcm, calls, tag, after_pause = bytearray(), 0, None, True
    for kind, val in segs:
        if kind == "p":
            pcm += silence(val); after_pause = True; continue
        chunks = chunk_text(val, cfg()["chunk_chars"]) if cfg()["chunk"] else [val]
        for ch in chunks:
            send = f"[{tag}] {ch}" if (tag and not TAG_RE.match(ch.lstrip())) else ch
            found = TAG_RE.findall(ch)
            if found:
                tag = found[-1].lower()
            raw = run_tts(lambda k, s=send: _single_call(k, model, s, voice, lang, style), len(send))
            if pcm and not after_pause:
                pcm += silence(0.12)
            pcm += raw; calls += 1; after_pause = False
    if calls == 0:
        raise ValueError("Seslendirilecek metin yok.")
    return pcm2wav(postprocess(bytes(pcm))), calls

def synthesize_multi(text, model, lang, sp1, v1, sp2, v2):
    raw = run_tts(lambda k: _multi_call(k, model, prepare_text(text), sp1, v1, sp2, v2, lang), len(text))
    return pcm2wav(postprocess(raw)), 1

# ═════════════════════════════════════════════════════════════════
# MEDYA KÜTÜPHANESİ
# ═════════════════════════════════════════════════════════════════
CATS = {"song": "🎵 Şarkı", "jingle": "🔔 Jingle / Sweeper", "voice": "🎙️ Anons", "bed": "🎼 Fon müziği",
        "ad": "📣 Reklam", "other": "📁 Diğer"}
CAT_COL = {"song": "#3b82f6", "jingle": "#f59e0b", "voice": "#22c55e", "bed": "#a78bfa", "ad": "#ec4899", "other": "#94a3b8"}
CAT_INV = {v: k for k, v in CATS.items()}
AUDIO_EXT = (".mp3", ".wav", ".ogg", ".flac")

_init("_media", jload("playout/media.json", []))
_init("_upv", 0)

def media_map():
    return {m["id"]: m for m in st.session_state._media}

def mtags(m):
    return [t.strip().lower() for t in (m.get("tags") or "").split(",") if t.strip()]

def media_label(m):
    a = f" · {m['artist']}" if m.get("artist") else ""
    return f"{CATS.get(m['cat'], '')[:2]} {m['name']}{a} [{m['id'][:4]}]"

def media_bytes(m):
    try:
        return (MEDIA / m["file"]).read_bytes()
    except Exception:
        return None

def parse_name(fn):
    stem = Path(fn).stem.replace("_", " ").strip()
    stem = re.sub(r"^\d{1,3}[\s.\-]+", "", stem)
    if " - " in stem:
        a, t = stem.split(" - ", 1)
        return t.strip(), a.strip()
    return stem, ""

def _rms_db(a):
    if len(a) == 0:
        return -60.0
    r = float(np.sqrt(np.mean(np.square(a[::4]))))
    return round(20 * np.log10(max(r, 1e-6)), 1)

def media_add(fname, data, cat, tags="", parse=True, src="upload", text="", name=None, artist=None):
    md5 = hashlib.md5(data).hexdigest()
    if any(m["md5"] == md5 for m in st.session_state._media):
        return None
    ext = Path(fname).suffix.lower()
    ext = ext if ext in AUDIO_EXT else (".wav" if data[:4] == b"RIFF" else ".mp3")
    a = decode_stereo(data)
    if len(a) == 0:
        raise ValueError("Ses çözülemedi / boş dosya.")
    t, ar = parse_name(fname) if parse else (Path(fname).stem, "")
    mid = md5[:10]
    (MEDIA / f"{mid}{ext}").write_bytes(data)
    m = {"id": mid, "name": name or t, "artist": artist if artist is not None else ar, "cat": cat, "file": f"{mid}{ext}",
         "dur": round(len(a) / SR2, 1), "size": len(data), "tags": tags, "gain_db": 0.0, "rms_db": _rms_db(a),
         "peak": round(float(np.abs(a).max()), 3), "intro_s": 0.0, "cue_in": 0.0, "cue_out": 0.0,
         "src": src, "text": text, "md5": md5, "added": datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}
    st.session_state._media.append(m)
    jsave("playout/media.json", st.session_state._media)
    return m

def media_delete(mid):
    m = media_map().get(mid)
    if m:
        try: (MEDIA / m["file"]).unlink()
        except Exception: pass
    st.session_state._media = [x for x in st.session_state._media if x["id"] != mid]
    jsave("playout/media.json", st.session_state._media)

def media_save(mid):
    ss = st.session_state
    for m in ss._media:
        if m["id"] == mid:
            g = lambda k, d=None: ss.get(f"m_{k}_{mid}", d)
            m["name"] = g("name", m["name"]).strip() or m["name"]
            m["artist"] = g("artist", m.get("artist", "")).strip()
            m["cat"] = CAT_INV.get(g("cat"), m["cat"])
            m["tags"] = g("tags", m.get("tags", "")).strip()
            m["gain_db"] = float(g("gain", m.get("gain_db", 0)))
            m["intro_s"] = float(g("intro", m.get("intro_s", 0)))
            m["cue_in"] = float(g("cin", m.get("cue_in", 0)))
            m["cue_out"] = float(g("cout", m.get("cue_out", 0)))
    jsave("playout/media.json", ss._media)

def import_main_songs():
    n = 0
    for s in jload("songs.json", []):
        f = DATA / "songs" / s.get("file", "")
        if not f.exists():
            continue
        try:
            tg = (s.get("tag") or "").lower()
            r = media_add(f.name, f.read_bytes(), "jingle" if "jingle" in tg else "song", tags=s.get("tag", ""),
                          parse=False, src="app", name=s["name"], artist="")
            n += 1 if r else 0
        except Exception:
            pass
    return n

def main_archive():
    out = []
    for e in jload("archive.json", []):
        if (DATA / "audio" / f"{e['id']}.wav").exists():
            out.append(e)
    return out

def import_main_archive(ids):
    n = 0
    for e in main_archive():
        if e["id"] in ids:
            r = media_add(f"{e['id']}.wav", (DATA / "audio" / f"{e['id']}.wav").read_bytes(), "voice", parse=False,
                          src="app", text=e.get("text", ""), name=f"{e['voice']} · {e['preview'][:36]}", artist="")
            n += 1 if r else 0
    return n

# ═════════════════════════════════════════════════════════════════
# YAYIN AKIŞI MODELİ
# ═════════════════════════════════════════════════════════════════
# ── yedekleme / geri yükleme ───────────────────────────────────
def make_backup() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as z:
        for f in MEDIA.glob("*"):
            if f.is_file():
                z.write(f, f"media/{f.name}")
        for n in ("media.json", "playlists.json", "current.json"):
            p = PO / n
            if p.exists():
                z.write(p, n)
    return buf.getvalue()

def restore_backup(raw: bytes):
    """Medya dosyalarını ve kayıtlı akışları mevcut verinin ÜSTÜNE EKLER (silmez)."""
    added, pls = 0, 0
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = z.namelist()
        for info in z.infolist():
            nm = info.filename
            if info.is_dir() or ".." in nm or nm.startswith(("/", "\\")):
                continue
            if nm.startswith("media/"):
                dst = MEDIA / Path(nm).name
                if not dst.exists():
                    dst.write_bytes(z.read(nm))
        have = {m["id"] for m in st.session_state._media}
        if "media.json" in names:
            for m in json.loads(z.read("media.json").decode("utf-8")):
                if m.get("id") not in have and (MEDIA / m.get("file", "")).exists():
                    st.session_state._media.append(m); have.add(m["id"]); added += 1
            jsave("playout/media.json", st.session_state._media)
        if "playlists.json" in names:
            cur = jload("playout/playlists.json", {})
            inc = json.loads(z.read("playlists.json").decode("utf-8"))
            for k, v in inc.items():
                if k not in cur:
                    cur[k] = v; pls += 1
            jsave("playout/playlists.json", cur)
    return added, pls

POS = {"start": "▶ Parça başından t sn sonra", "intro": "🎼 Intro'ya sığdır (vokal girmeden biter)",
       "end": "⏹ Parça bitmeden t sn önce biter", "at": "📍 Tam saniyede (t)",
       "pre": "⏮ Parçadan önce (ayrı söyle)", "post": "⏭ Parçadan sonra (ayrı söyle)"}
POS_DEF_T = {"start": 1.5, "intro": 0.0, "end": 2.0, "at": 10.0, "pre": 0.0, "post": 0.0}

MX_DEF = {"voice": "Kore", "model": next(iter(MODELS)), "style": "", "crossfade": 4.0, "fade_in": 0.3, "fade_out": 2.0,
          "duck_db": 12.0, "voice_db": 0.0, "normalize": True, "target_db": -16.0, "max_boost": 12.0,
          "bed_level": -6.0, "bed_duck": 14.0, "bed_pre": 2.0, "bed_post": 3.0, "voice_gap": 0.25,
          "fmt": "MP3", "kbps": 192}

def _pl_merge(d):
    base = {"name": "Yayın 1", "items": [], "mx": dict(MX_DEF)}
    if isinstance(d, dict):
        base["name"] = d.get("name", base["name"])
        base["items"] = d.get("items", [])
        base["mx"].update(d.get("mx", {}))
    return base

_init("_pl", _pl_merge(jload("playout/current.json", None)))
_init("_plv", 0)

def K(name, uid=""):
    return f"q{st.session_state._plv}_{name}_{uid}"

def _uid():
    return hashlib.md5((str(time.time()) + str(random.random())).encode()).hexdigest()[:8]

def new_src(text="", lib=None):
    return {"type": "lib" if lib else "tts", "text": text, "voice": "", "lib": lib}

def new_overlay(pos="start", text=""):
    return {"uid": _uid(), "pos": pos, "t": POS_DEF_T[pos], "src": new_src(text), "duck_db": None,
            "gain_db": 0.0, "bed": None, "bed_level": -6.0}

def new_track(mid):
    return {"uid": _uid(), "kind": "track", "media": mid, "limit": 0.0, "gain_db": 0.0, "fade_in": None,
            "fade_out": None, "xfade": None, "overlays": []}

def new_voice(text="", lib=None):
    return {"uid": _uid(), "kind": "voice", "src": new_src(text, lib), "bed": None, "bed_level": None,
            "pre": None, "post": None, "gain_db": 0.0}

def new_gap(sec=2.0):
    return {"uid": _uid(), "kind": "gap", "sec": float(sec)}

def pl_items():
    return st.session_state._pl["items"]

def pl_add_media(mid):
    m = media_map().get(mid)
    if not m:
        return
    if m["cat"] == "voice":
        pl_items().append(new_voice(lib=mid))
    elif m["cat"] == "bed":
        st.session_state["_msg"] = "ℹ️ Fon müziği tek başına eklenmez; anons/parça katmanlarında 'fon müziği' olarak seçin."
    else:
        pl_items().append(new_track(mid))

def pl_add_voice():
    pl_items().append(new_voice("[excitedly] İmaj FM'e hoş geldiniz!"))

def pl_add_gap():
    pl_items().append(new_gap(2.0))

def pl_move(i, d):
    it = pl_items(); j = i + d
    if 0 <= i < len(it) and 0 <= j < len(it):
        it[i], it[j] = it[j], it[i]

def pl_del(i):
    if 0 <= i < len(pl_items()):
        pl_items().pop(i)

def pl_dup(i):
    it = pl_items()
    if 0 <= i < len(it):
        c = json.loads(json.dumps(it[i])); c["uid"] = _uid()
        for ov in c.get("overlays", []):
            ov["uid"] = _uid()
        it.insert(i + 1, c)

def pl_clear():
    st.session_state._pl["items"] = []
    st.session_state._plv += 1

def pl_new():
    st.session_state._pl = _pl_merge({"name": f"Yayın {datetime.datetime.now().strftime('%d.%m %H:%M')}"})
    st.session_state._plv += 1

def _find(uid):
    for it in pl_items():
        if it["uid"] == uid:
            return it

def ov_add(uid, pos):
    it = _find(uid)
    if it is not None and it["kind"] == "track":
        it["overlays"].append(new_overlay(pos))

def ov_del(uid, ouid):
    it = _find(uid)
    if it is not None:
        it["overlays"] = [o for o in it["overlays"] if o["uid"] != ouid]

def pl_save():
    saved = jload("playout/playlists.json", {})
    pl = st.session_state._pl
    saved[pl["name"]] = json.loads(json.dumps(pl))
    jsave("playout/playlists.json", saved)

def pl_load(name):
    saved = jload("playout/playlists.json", {})
    if name in saved:
        st.session_state._pl = _pl_merge(json.loads(json.dumps(saved[name])))
        st.session_state._plv += 1

def pl_forget(name):
    saved = jload("playout/playlists.json", {})
    saved.pop(name, None)
    jsave("playout/playlists.json", saved)

# ── süre tahmini & zaman çizelgesi ─────────────────────────────────
def est_src(src, mm):
    if src.get("type") == "lib":
        m = mm.get(src.get("lib"))
        return float(m["dur"]) if m else 0.0
    return len(src.get("text", "")) / 15.0 + 0.3 if src.get("text", "").strip() else 0.0

def est_item(it, mm, mx):
    k = it["kind"]
    if k == "track":
        m = mm.get(it["media"])
        if not m:
            return 0.0
        d = (float(m.get("cue_out") or 0) or float(m["dur"])) - float(m.get("cue_in", 0))
        lim = float(it.get("limit") or 0)
        d = min(d, lim) if lim > 0 else d
        for ov in it["overlays"]:
            if ov["pos"] in ("pre", "post"):
                d += est_src(ov["src"], mm) + float(mx["voice_gap"])
        return max(0.0, d)
    if k == "voice":
        pre = mx["bed_pre"] if it.get("pre") is None else it["pre"]
        post = mx["bed_post"] if it.get("post") is None else it["post"]
        return est_src(it["src"], mm) + (float(pre) + float(post) if it.get("bed") else 0.0)
    return float(it.get("sec", 0))

def est_total(items, mm, mx):
    tot = sum(est_item(i, mm, mx) for i in items)
    for a, b in zip(items, items[1:]):
        if a["kind"] == "track" and b["kind"] == "track":
            x = mx["crossfade"] if a.get("xfade") is None else a["xfade"]
            tot -= float(x)
    return max(0.0, tot)

def timeline_html(items, mm, mx):
    durs = [est_item(i, mm, mx) for i in items]
    tot = sum(durs) or 1.0
    cells = []
    for it, d in zip(items, durs):
        if it["kind"] == "track":
            m = mm.get(it["media"])
            col, nm = (CAT_COL.get(m["cat"], "#94a3b8"), m["name"]) if m else ("#ef4444", "⚠ dosya yok")
            if it["overlays"]:
                nm += f" (+{len(it['overlays'])} katman)"
        elif it["kind"] == "voice":
            col, nm = "#22c55e", "Anons: " + (it["src"].get("text", "")[:30] or "klip")
        else:
            col, nm = "#64748b", "boşluk"
        w = max(0.6, d / tot * 100)
        cells.append(f"<div title='{esc(nm)} · {d:.0f} sn' style='flex:0 0 {w:.2f}%;background:{col};height:26px;border-right:1px solid var(--bg);'></div>")
    return f"<div style='display:flex;width:100%;border-radius:6px;overflow:hidden;border:1px solid var(--border);'>{''.join(cells)}</div>"

def make_ctx(items, idx, mm):
    def nm(i):
        m = mm.get(items[i].get("media")) if items[i]["kind"] == "track" else None
        return (m["name"], m.get("artist", "")) if (m and m["cat"] == "song") else None
    prev = next((nm(i) for i in range(idx - 1, -1, -1) if nm(i)), ("", ""))
    nxt = next((nm(i) for i in range(idx + 1, len(items)) if nm(i)), ("", ""))
    cur = nm(idx) if items[idx]["kind"] == "track" else None
    now = datetime.datetime.now()
    s = cur or nxt
    return {"sarki": s[0], "sanatci": s[1], "onceki": prev[0], "onceki_sanatci": prev[1], "sonraki": nxt[0],
            "sonraki_sanatci": nxt[1], "saat": now.strftime("%H:%M"), "tarih": now.strftime("%d.%m.%Y")}

# ── otomatik akış (saat çarkı) ──────────────────────────────────
def autofill():
    ss = st.session_state
    mm = media_map(); mx = ss._pl["mx"]
    rnd = random.Random(int(ss.get("af_seed", 0)) or None)
    sel = [t.lower() for t in ss.get("af_tags", [])]
    pool = [m for m in ss._media if m["cat"] == "song" and (not sel or any(t in mtags(m) for t in sel))]
    jingles = [m for m in ss._media if m["cat"] == "jingle"]
    if not pool:
        ss["_af_msg"] = "⚠️ Uygun şarkı yok. Kütüphaneye şarkı ekleyin veya etiket seçimini değiştirin."
        return
    texts = [l.strip() for l in ss.get("af_pool", "").splitlines() if l.strip()]
    target, sep, every = float(ss.get("af_min", 30)) * 60, int(ss.get("af_sep", 3)), int(ss.get("af_every", 3))
    bed = ss.get("af_bed_id")
    items, total, n, recent, order = [], 0.0, 0, [], []
    def voice(t):
        v = new_voice(t)
        if bed:
            v["bed"] = bed
        return v
    if ss.get("af_open", "").strip():
        v = voice(ss.af_open.strip()); items.append(v); total += est_item(v, mm, mx)
    while total < target and n < 500:
        if not order:
            order = pool[:]; rnd.shuffle(order)
        pick = 0
        for i, m in enumerate(order):
            art = (m.get("artist") or "").lower()
            if not art or sep <= 0 or art not in recent[-sep:]:
                pick = i; break
        m = order.pop(pick); recent.append((m.get("artist") or "").lower())
        t = new_track(m["id"])
        if ss.get("af_intro", "").strip():
            t["overlays"].append(new_overlay("intro", ss.af_intro.strip()))
        if ss.get("af_outro", "").strip():
            t["overlays"].append(new_overlay("end", ss.af_outro.strip()))
        if float(ss.get("af_cap", 0)) > 0:
            t["limit"] = float(ss.af_cap)
        items.append(t); total += est_item(t, mm, mx) - float(mx["crossfade"]); n += 1
        if every > 0 and n % every == 0 and total < target:
            if texts:
                v = voice(rnd.choice(texts)); items.append(v); total += est_item(v, mm, mx)
            if jingles:
                j = rnd.choice(jingles); jt = new_track(j["id"]); items.append(jt); total += est_item(jt, mm, mx)
    if ss.get("af_close", "").strip():
        items.append(voice(ss.af_close.strip()))
    if ss.get("af_exact") and total > target:
        over = total - target
        for it in reversed(items):
            if it["kind"] == "track" and mm.get(it["media"], {}).get("cat") == "song":
                d = est_item(it, mm, mx)
                it["limit"] = float(max(20.0, d - over)); break
    if ss.get("af_append"):
        ss._pl["items"].extend(items)
    else:
        ss._pl["items"] = items
    ss._plv += 1
    ss["_af_msg"] = f"✅ {n} parçalık akış oluşturuldu (tahmini ~{est_total(ss._pl['items'], mm, mx)/60:.0f} dk)."

# ═════════════════════════════════════════════════════════════════
# YAYIN MOTORU (44.1 kHz stereo · diske akışlı yazım · katmanlı mix)
# ═════════════════════════════════════════════════════════════════
def trim_silence(a, thr=0.012, keep=0.04):
    if len(a) == 0:
        return a
    idx = np.where(np.abs(a).max(axis=1) > thr)[0]
    if len(idx) == 0:
        return a
    k = int(keep * SR2)
    return a[max(0, idx[0] - k): idx[-1] + k + 1]

def gl(db):
    return np.float32(10 ** (float(db) / 20))

def tts_cached(text, voice, mx):
    key = hashlib.md5(f"{prepare_text(text)}|{voice}|{mx['model']}|{mx.get('style','')}".encode()).hexdigest()[:16]
    f = TTSC / f"{key}.wav"
    if f.exists():
        return f.read_bytes()
    wav, _ = synthesize(text, voice, mx["model"], "tr-TR", mx.get("style", ""))
    f.write_bytes(wav)
    return wav

def tts_is_cached(text, voice, mx):
    key = hashlib.md5(f"{prepare_text(text)}|{voice}|{mx['model']}|{mx.get('style','')}".encode()).hexdigest()[:16]
    return (TTSC / f"{key}.wav").exists()

def voice_from_media(m, mx):
    a = trim_silence(decode_stereo(media_bytes(m)))
    if m["cat"] == "voice":
        pk = float(np.abs(a).max())
        if pk > 0:
            a = a * np.float32(0.89 / pk)
    else:
        a = rms_norm(a, float(mx["target_db"]))
    return _guard(a * gl(m.get("gain_db", 0)))

def resolve_audio(src, ctx, mm, mx, tts):
    if src.get("type") == "lib":
        m = mm.get(src.get("lib"))
        return (voice_from_media(m, mx), m["name"]) if m else (None, "")
    txt = fill_vars(src.get("text", ""), ctx).strip()
    if not txt:
        return None, ""
    wav = tts(txt, src.get("voice") or mx["voice"])
    return trim_silence(wav_to_st(wav)), txt[:80]

def overlay_audio(ov, ctx, mm, mx, tts):
    v, label = resolve_audio(ov["src"], ctx, mm, mx, tts)
    if v is None:
        return None
    v = _guard(v * gl(float(mx["voice_db"]) + float(ov.get("gain_db", 0))))
    bm = mm.get(ov.get("bed")) if ov.get("bed") else None
    if bm is not None and media_bytes(bm) is not None:
        o = {"bed_pre": 0.4, "bed_post": 0.9, "target_db": mx["target_db"],
             "bed_level": float(ov.get("bed_level", -6)), "bed_duck": float(mx["bed_duck"])}
        return _bed_mix(v, decode_stereo(media_bytes(bm)), o), int(0.4 * SR2), len(v), label
    return v, 0, len(v), label

def prep_track(m, it, mx):
    a = decode_stereo(media_bytes(m))
    ci = int(float(m.get("cue_in", 0)) * SR2)
    co = float(m.get("cue_out", 0))
    a = a[ci: (len(a) if co <= 0 else min(len(a), int(co * SR2)))]
    lim = float(it.get("limit") or 0)
    if lim > 0:
        a = a[: int(lim * SR2)]
    g = float(m.get("gain_db", 0)) + float(it.get("gain_db", 0))
    if mx.get("normalize", True) and m["cat"] != "bed":
        r = m.get("rms_db")
        if r is not None:
            g += float(np.clip(float(mx["target_db"]) - float(r), -18.0, float(mx["max_boost"])))
    a = _guard(a * gl(g))
    fi = mx["fade_in"] if it.get("fade_in") is None else it["fade_in"]
    fo = mx["fade_out"] if it.get("fade_out") is None else it["fade_out"]
    return _fade(a, int(float(fi) * SR2), int(float(fo) * SR2))

def build_track(m, it, mx, ctx, mm, tts, xf_in, xf_out):
    seg = prep_track(m, it, mx)
    intro_eff = max(0.0, float(m.get("intro_s", 0)) - float(m.get("cue_in", 0)))
    gap = np.zeros((int(float(mx["voice_gap"]) * SR2), 2), np.float32)
    pre, post, plc = [], [], []
    for ov in it.get("overlays", []):
        r = overlay_audio(ov, ctx, mm, mx, tts)
        if r is None:
            continue
        au, off, vlen, label = r
        pos, t = ov["pos"], float(ov.get("t", 0))
        if pos == "pre":
            pre.append((au, label)); continue
        if pos == "post":
            post.append((au, label)); continue
        if pos == "start":
            sv = int(max(t, xf_in) * SR2)
        elif pos == "intro":
            sv = max(0, int(intro_eff * SR2) - vlen) if intro_eff > 0 else int(max(t, 1.0, xf_in) * SR2)
        elif pos == "end":
            sv = len(seg) - vlen - int(max(t, xf_out) * SR2)
        else:
            sv = int(t * SR2)
        plc.append((max(0, sv), au, off, label, ov))
    plc.sort(key=lambda x: x[0])
    rel_ov = []
    for sv, au, off, label, ov in plc:
        d = ov.get("duck_db")
        d = float(mx["duck_db"]) if d is None else float(d)
        st_ = sv - off
        if st_ < 0:
            au = au[-st_:]; st_ = 0
        seg = _overlay(seg, au, st_, d)
        rel_ov.append((sv, label))
    parts, cur, rel = [], 0, []
    for au, label in pre:
        rel.append((cur / SR2, label)); parts += [au, gap]; cur += len(au) + len(gap)
    song_off = cur / SR2
    for sv, label in rel_ov:
        rel.append(((cur + sv) / SR2, label))
    parts.append(seg); cur += len(seg)
    for au, label in post:
        parts += [gap, au]; rel.append(((cur + len(gap)) / SR2, label)); cur += len(gap) + len(au)
    return (np.concatenate(parts) if len(parts) > 1 else seg), bool(pre), bool(post), rel, song_off

def build_voice(it, ctx, mm, mx, tts):
    v, label = resolve_audio(it["src"], ctx, mm, mx, tts)
    if v is None:
        return None, ""
    v = _guard(v * gl(float(mx["voice_db"]) + float(it.get("gain_db", 0))))
    bm = mm.get(it.get("bed")) if it.get("bed") else None
    if bm is not None and media_bytes(bm) is not None:
        o = {"bed_pre": mx["bed_pre"] if it.get("pre") is None else it["pre"],
             "bed_post": mx["bed_post"] if it.get("post") is None else it["post"],
             "target_db": mx["target_db"], "bed_level": mx["bed_level"] if it.get("bed_level") is None else it["bed_level"],
             "bed_duck": mx["bed_duck"]}
        return _bed_mix(v, decode_stereo(media_bytes(bm)), o), label
    return v, label

def render_playout(items, mm, mx, tts, out_path, fmt="mp3", progress=None, start=0, max_sec=0):
    n = len(items)
    def xf_sec(i):
        if i < 0 or i + 1 >= n:
            return 0.0
        a, b = items[i], items[i + 1]
        if a["kind"] != "track" or b["kind"] != "track":
            return 0.0
        if any(o["pos"] == "post" for o in a["overlays"]) or any(o["pos"] == "pre" for o in b["overlays"]):
            return 0.0
        x = mx["crossfade"] if a.get("xfade") is None else a["xfade"]
        return max(0.0, float(x))
    K_ = max(int((max([xf_sec(i) for i in range(n)] + [0.0]) + 0.5) * SR2), 1)
    sink = _Sink(out_path, fmt, mx.get("kbps", 192))
    sink.limit = int(float(max_sec) * SR2) if max_sec else 0
    carry, tl, cues, prev_idx, prev_len, prev_post = None, 0, [], None, 0, False
    try:
        for idx in range(start, n):
            it, kind = items[idx], items[idx]["kind"]
            if progress:
                progress((idx - start) / max(1, n - start), f"{idx+1}/{n} · " + ("parça" if kind == "track" else "anons" if kind == "voice" else "boşluk"))
            ctx = make_ctx(items, idx, mm)
            seg, has_pre, has_post, rel, song_off, cue = None, False, False, [], 0.0, None
            if kind == "track":
                m = mm.get(it["media"])
                if not m or media_bytes(m) is None:
                    continue
                xin = xf_sec(idx - 1) if (prev_idx == idx - 1 and idx > start) else 0.0
                seg, has_pre, has_post, rel, song_off = build_track(m, it, mx, ctx, mm, tts, xin, xf_sec(idx))
                cue = {"kind": "track", "cat": m["cat"], "name": m["name"], "artist": m.get("artist", "")}
            elif kind == "voice":
                seg, label = build_voice(it, ctx, mm, mx, tts)
                cue = {"kind": "voice", "cat": "voice", "name": label, "artist": ""}
            else:
                seg = np.zeros((int(float(it.get("sec", 2)) * SR2), 2), np.float32)
            if seg is None or len(seg) == 0:
                continue
            xf = xf_sec(prev_idx) if (prev_idx == idx - 1 and kind == "track" and not has_pre and not prev_post) else 0.0
            if carry is None:
                xe, carry = 0, seg
            else:
                xe = min(int(xf * SR2), len(carry), len(seg), int(0.45 * len(seg)), int(0.45 * prev_len))
                if xe > 0:
                    t = np.linspace(0, np.pi / 2, xe, dtype=np.float32)[:, None]
                    blend = carry[-xe:] * np.cos(t) + seg[:xe] * np.sin(t)
                    sink.write(carry[:-xe])
                    carry = np.concatenate([blend, seg[xe:]])
                else:
                    sink.write(carry); carry = seg
            start_pos = tl - xe
            if cue:
                cue.update({"t": round(max(0, start_pos) / SR2 + song_off, 1), "dur": round(len(seg) / SR2 - song_off, 1)})
                cues.append(cue)
            if kind == "track":
                for rt, label in rel:
                    cues.append({"t": round(max(0, start_pos) / SR2 + rt, 1), "kind": "anons", "cat": "voice",
                                 "name": label, "artist": "", "dur": 0})
            tl = start_pos + len(seg)
            prev_idx, prev_len, prev_post = idx, len(seg), has_post
            if len(carry) > K_:
                sink.write(carry[:-K_]); carry = carry[-K_:]
            if sink.limit and (sink.n + len(carry)) >= sink.limit:
                break
        if carry is not None:
            sink.write(carry)
        if sink.n == 0:
            raise ValueError("Üretilecek ses yok (akış boş, anons metinleri boş veya dosyalar bulunamadı).")
        total = sink.n / SR2
        sink.close()
        if progress:
            progress(1.0, "Tamamlandı")
        cues.sort(key=lambda c: c["t"])
        return total, cues
    except Exception:
        sink.abort()
        raise

def collect_tts(items, mm, mx):
    need = {}
    def add(src, ctx):
        if src.get("type") == "tts":
            t = fill_vars(src.get("text", ""), ctx).strip()
            if t:
                v = src.get("voice") or mx["voice"]
                need[(t, v)] = tts_is_cached(t, v, mx)
    for idx, it in enumerate(items):
        ctx = make_ctx(items, idx, mm)
        if it["kind"] == "voice":
            add(it["src"], ctx)
        elif it["kind"] == "track":
            for ov in it["overlays"]:
                add(ov["src"], ctx)
    return need

def cue_text(cues, name=""):
    lines = [f"YAYIN AKIŞ LİSTESİ — {name}", ""]
    for c in cues:
        who = f" — {c['artist']}" if c.get("artist") else ""
        lines.append(f"{fmt_t(c['t'])}  [{ {'track':'Parça','voice':'Anons','anons':'Anons (katman)'}.get(c['kind'],c['kind']) }] {c['name']}{who}")
    return "\n".join(lines)

def cue_csv(cues):
    rows = ["zaman,tur,kategori,sanatci,baslik,sure_sn"]
    for c in cues:
        q = lambda s: '"' + str(s).replace('"', "'") + '"'
        rows.append(f"{fmt_t(c['t'])},{c['kind']},{c.get('cat','')},{q(c.get('artist',''))},{q(c['name'])},{c.get('dur',0)}")
    return "\n".join(rows)

# ═════════════════════════════════════════════════════════════════
# ARAYÜZ — ORTAK
# ═════════════════════════════════════════════════════════════════
_init("_bcs", jload("playout/outputs.json", []))
_init("_pv_media", None)
VOICE_LABELS = {v: f"{d[0]} {v} — {d[1]}" for v, d in VOICES.items()}

def sel_map(label, mapping, current, key, **kw):
    ids = list(mapping)
    labs = [str(mapping[i]) for i in ids]
    idx = ids.index(current) if current in ids else 0
    r = st.selectbox(label, labs, index=idx, key=key, **kw)
    return ids[labs.index(r)] if r in labs else ids[0]

def add_tag(k, t):
    st.session_state[k] = st.session_state.get(k, "") + t

def set_state(k, v):
    st.session_state[k] = v

def set_pv(mid):
    st.session_state["_pv_media"] = mid

def add_key_cb():
    k = st.session_state.get("new_key", "").strip()
    if k:
        for i, s in enumerate(st.session_state._pool):
            if not s["key"].strip():
                s["key"] = k; st.session_state[f"key_{i}"] = k
                break
        st.session_state["new_key"] = ""

def clear_tts_cache():
    for f in TTSC.glob("*.wav"):
        try: f.unlink()
        except Exception: pass

def item_title(i, it, mm):
    if it["kind"] == "track":
        m = mm.get(it["media"])
        nm = f"{CATS[m['cat']][:2]} {m['name']}" if m else "⚠️ dosya yok"
        ex = f" · +{len(it['overlays'])} katman" if it["overlays"] else ""
        return f"{i+1}. {nm}{ex}"
    if it["kind"] == "voice":
        s = it["src"]
        t = s.get("text", "") if s.get("type") != "lib" else (mm.get(s.get("lib"), {}).get("name", "klip"))
        return f"{i+1}. 🎙️ {t[:36] or '(boş anons)'}"
    return f"{i+1}. ⏸ {float(it.get('sec', 0)):.1f} sn boşluk"

# ═════════════════════════════════════════════════════════════════
# YAN MENÜ
# ═════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("<div style='text-align:center;padding:5px 0 11px;'><span style='font-family:Syne,sans-serif;font-size:.95rem;font-weight:800;background:linear-gradient(90deg,var(--h1a),#e02020);-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>📻 Yayın Otomasyonu</span></div>", unsafe_allow_html=True)
    look_controls("_sb")
    _tk, _tu, _tr = pool_stats()
    st.markdown(f"<div class='card {'b' if _tk else 'r'}'>🗝️ Yüklü anahtar: <b>{_tk}</b> · kalan istek: <b>{_tr}</b><br><span class='tiny'>Ana uygulamayla ortak havuz.</span></div>", unsafe_allow_html=True)
    with st.expander("➕ API anahtarı ekle", expanded=(_tk == 0)):
        st.text_input("Anahtar", type="password", key="new_key", placeholder="AIzaSy...", label_visibility="collapsed")
        st.button("Ekle", key="add_key", on_click=add_key_cb, **UCW)
    with st.expander("🧹 Önbellek", expanded=False):
        _fs = list(TTSC.glob("*.wav"))
        st.caption(f"Anons önbelleği: {len(_fs)} dosya · {sum(f.stat().st_size for f in _fs)/(1024*1024):.1f} MB")
        st.button("Önbelleği temizle", key="clr_tts", on_click=clear_tts_cache, **UCW)
    st.caption("Ana sayfa (TTS Stüdyo) için sol üstteki sayfa menüsünü kullanın.")

# ═════════════════════════════════════════════════════════════════
# BAŞLIK
# ═════════════════════════════════════════════════════════════════
st.markdown("<div class='hdr'><h1>📻 İmaj FM · Yayın Otomasyonu</h1><p><span class='ldot'></span>Medya kütüphanesi · Katmanlı anons &amp; fon müziği · Otomatik kısma (ducking) · Crossfade · Otomatik akış · MP3 / WAV tam yayın çıktısı</p></div>", unsafe_allow_html=True)
_lc, _lc2 = st.columns([3, 2])
with _lc:
    look_controls("")

_pl = st.session_state._pl
_mm = media_map()
_mx = _pl["mx"]
_est = est_total(_pl["items"], _mm, _mx)
for _col, (_v, _l, _c) in zip(st.columns(4), [
        (len(st.session_state._media), "Kütüphane", "b"), (len(_pl["items"]), "Akış öğesi", ""),
        (f"{_est/60:.1f} dk", "Tahmini süre", "p"), (str(pool_stats()[2]), "Kalan istek", "a")]):
    _col.markdown(f'<div class="mbox {_c}"><div class="v">{_v}</div><div class="l">{_l}</div></div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)
if st.session_state.get("_msg"):
    st.markdown(f"<div class='card b'>{esc(st.session_state.pop('_msg'))}</div>", unsafe_allow_html=True)

t1, t2, t3, t4, t5 = st.tabs(["📚 Kütüphane", "🎙️ Anons Stüdyosu", "📋 Yayın Akışı", "📻 Yayın Çıktısı", "⚙️ Ayarlar"])

# ══════════════════════════════════════════════════════════════════
# TAB 1 — KÜTÜPHANE
# ══════════════════════════════════════════════════════════════════
with t1:
    media = st.session_state._media
    st.markdown("<div class='card b'><b>📚 Medya Kütüphanesi</b> — Şarkı, jingle, anons, fon müziği ve reklam dosyalarınız. Dosyadan yükleyebilir ya da ana uygulamada ürettiğiniz anonsları içe aktarabilirsiniz.</div>", unsafe_allow_html=True)
    miss = []
    if miniaudio is None: miss.append("MP3 okumak için `pip install miniaudio`")
    if lameenc is None: miss.append("MP3 çıktı için `pip install lameenc`")
    if miss:
        st.warning(" · ".join(miss))
    with st.expander("⬆️ Dosyadan ekle (MP3 · WAV · OGG · FLAC)", expanded=not media):
        ups = st.file_uploader("Dosyalar (birden fazla seçilebilir)", type=[e.strip(".") for e in AUDIO_EXT],
                               accept_multiple_files=True, key=f"up_{st.session_state._upv}")
        u1, u2 = st.columns(2)
        up_cat = u1.selectbox("Kategori", list(CATS.values()), key="up_cat")
        up_tags = u2.text_input("Etiketler (virgülle)", key="up_tags", placeholder="pop, 90lar, enerjik")
        up_parse = st.checkbox("Dosya adından 'Sanatçı - Şarkı' ayır", True, key="up_parse")
        if st.button("📥 Kütüphaneye ekle", type="primary", key="up_go", disabled=not ups, **UCW):
            prog = st.progress(0.0, "Analiz ediliyor…")
            ok, dup, bad = 0, 0, []
            for i, f in enumerate(ups):
                prog.progress(i / len(ups), f"{i+1}/{len(ups)} · {f.name}")
                try:
                    r = media_add(f.name, f.getvalue(), CAT_INV[up_cat], up_tags, up_parse)
                    ok += 1 if r else 0
                    dup += 0 if r else 1
                except Exception as ex:
                    bad.append(f"{f.name}: {ex}")
            prog.empty()
            st.session_state["_msg"] = f"✅ {ok} dosya eklendi" + (f" · {dup} zaten vardı" if dup else "") + (" · ❌ " + " | ".join(bad) if bad else "")
            st.session_state._upv += 1
            st.rerun()
    with st.expander("🔗 Ana uygulamadan içe aktar (şarkılar · üretilmiş anonslar)", expanded=False):
        ms = jload("songs.json", [])
        st.caption(f"Ana uygulamanın şarkı kütüphanesi: {len(ms)} kayıt")
        if st.button("🎵 Şarkıları içe aktar", key="imp_songs", disabled=not ms, **UCW):
            st.session_state["_msg"] = f"✅ {import_main_songs()} şarkı içe aktarıldı"
            st.rerun()
        arc = main_archive()
        labs = {e["id"]: f"{e['ts_short']} · {e['voice']} · {e['dur']}s · {e['preview'][:34]} #{e['id'][:4]}" for e in arc}
        inv = {v: k for k, v in labs.items()}
        pick = st.multiselect("Anons arşivi (ana uygulama)", list(labs.values()), key="imp_arc_pick")
        if st.button("🎙️ Seçili anonsları içe aktar", key="imp_arc", disabled=not pick, **UCW):
            st.session_state["_msg"] = f"✅ {import_main_archive({inv[p] for p in pick})} anons içe aktarıldı"
            st.rerun()

    f1, f2, f3 = st.columns([1.2, 2, 1.2])
    fcat = f1.selectbox("Kategori", ["Tümü"] + list(CATS.values()), key="lib_cat")
    fq = f2.text_input("Ara", key="lib_q", placeholder="ad, sanatçı veya etiket").lower().strip()
    sort = f3.selectbox("Sırala", ["Yeni → eski", "Ad", "Sanatçı", "Süre"], key="lib_sort")
    lst = [m for m in media if (fcat == "Tümü" or m["cat"] == CAT_INV[fcat]) and
           (not fq or fq in m["name"].lower() or fq in m.get("artist", "").lower() or fq in m.get("tags", "").lower())]
    if sort == "Yeni → eski": lst = lst[::-1]
    elif sort == "Ad": lst = sorted(lst, key=lambda m: m["name"].lower())
    elif sort == "Sanatçı": lst = sorted(lst, key=lambda m: m.get("artist", "").lower())
    else: lst = sorted(lst, key=lambda m: -m["dur"])
    PER = 15
    pages = max(1, (len(lst) + PER - 1) // PER)
    pg = st.number_input("Sayfa", 1, pages, 1, key="lib_pg") if pages > 1 else 1
    cnt = {c: sum(1 for m in media if m["cat"] == c) for c in CATS}
    st.markdown("<div class='tiny'>" + " · ".join(f"{CATS[c]} {n}" for c, n in cnt.items() if n) + f" — {len(lst)} sonuç</div>", unsafe_allow_html=True)
    pvm = _mm.get(st.session_state.get("_pv_media"))
    if pvm and media_bytes(pvm):
        st.markdown(f"<div class='card p'>▶ {esc(pvm['name'])}</div>", unsafe_allow_html=True)
        st.audio(media_bytes(pvm), format="audio/wav" if pvm["file"].endswith(".wav") else "audio/mpeg")
    if not media:
        st.caption("Kütüphane boş. Yukarıdan dosya yükleyin.")
    for m in lst[(pg - 1) * PER: pg * PER]:
        mid = m["id"]
        with st.expander(f"{CATS[m['cat']][:2]} {m['name']}" + (f" · {m['artist']}" if m.get("artist") else "") + f" · {m['dur']:.0f} sn", expanded=False):
            st.caption(f"{CATS[m['cat']]} · RMS {m['rms_db']} dB · tepe {m['peak']} · {m['size']//1024} KB · {m['file']}" + (f" · etiket: {m['tags']}" if m.get("tags") else ""))
            e1, e2 = st.columns(2)
            e1.text_input("Ad", m["name"], key=f"m_name_{mid}")
            e2.text_input("Sanatçı", m.get("artist", ""), key=f"m_artist_{mid}")
            e3, e4 = st.columns(2)
            e3.selectbox("Kategori", list(CATS.values()), index=list(CATS).index(m["cat"]), key=f"m_cat_{mid}")
            e4.text_input("Etiketler", m.get("tags", ""), key=f"m_tags_{mid}")
            g1, g2, g3, g4 = st.columns(4)
            g1.number_input("Kazanç dB", -24.0, 12.0, float(m.get("gain_db", 0)), 0.5, key=f"m_gain_{mid}")
            g2.number_input("Intro (sn)", 0.0, 120.0, float(m.get("intro_s", 0)), 0.5, key=f"m_intro_{mid}", help="Vokalin girdiği an. 'Intro'ya sığdır' anonsu bu ana kadar biter.")
            g3.number_input("Cue in (sn)", 0.0, 600.0, float(m.get("cue_in", 0)), 0.5, key=f"m_cin_{mid}", help="Parçanın başlangıç noktası.")
            g4.number_input("Cue out (sn)", 0.0, 3600.0, float(m.get("cue_out", 0)), 1.0, key=f"m_cout_{mid}", help="0 = sonuna kadar.")
            b1, b2, b3, b4 = st.columns(4)
            b1.button("💾 Kaydet", key=f"msv_{mid}", on_click=media_save, args=(mid,), **UCW)
            b2.button("▶ Dinle", key=f"mpv_{mid}", on_click=set_pv, args=(mid,), **UCW)
            b3.button("➕ Akışa", key=f"mad_{mid}", on_click=pl_add_media, args=(mid,), **UCW)
            b4.button("🗑️ Sil", key=f"mdl_{mid}", on_click=media_delete, args=(mid,), **UCW)

# ══════════════════════════════════════════════════════════════════
# TAB 2 — ANONS STÜDYOSU (uygulama içi yapay ses)
# ══════════════════════════════════════════════════════════════════
with t2:
    st.markdown("<div class='card b'><b>🎙️ Anons Stüdyosu</b> — Metinden yapay sesle anons üretin, kütüphaneye kaydedin; her yerde (parça katmanı, anons bloğu) dosya gibi kullanın. Katman/anons bloklarına doğrudan metin de yazabilirsiniz (otomatik üretilir ve önbelleğe alınır).</div>", unsafe_allow_html=True)
    _init("st_text", "[excitedly] İmaj FM'e hoş geldiniz! [pause 0.5] [normal] Şimdi müziğe devam ediyoruz.")
    tm = st.selectbox("Şablon", ["— Yok —"] + list(TEMPLATES), key="st_tmpl")
    if tm != "— Yok —":
        st.button("📥 Şablonu yükle", key="st_tmpl_go", on_click=set_state, args=("st_text", TEMPLATES[tm]))
    tc = st.columns(len(ETAGS))
    for i, (em, lbl, tag) in enumerate(ETAGS):
        tc[i].button(em, key=f"st_et_{i}", help=f"{lbl}: {tag.strip()}", on_click=add_tag, args=("st_text", tag), **UCW)
    txt = st.text_area("Anons metni", height=150, key="st_text", help="{saat} {tarih} değişkenleri yayın anında doldurulur.")
    s1, s2 = st.columns(2)
    sv = sel_map("Ses", VOICE_LABELS, _mx["voice"], "st_voice")
    models = get_models()
    sm = sel_map("Model", models, _mx["model"], "st_model")
    def _apply_preset():
        p = STYLE_PRESETS.get(st.session_state.get("st_preset", ""), "")
        if p:
            st.session_state["st_style"] = p
    st.selectbox("Stil şablonu", list(STYLE_PRESETS), key="st_preset", on_change=_apply_preset)
    _init("st_style", _mx.get("style", ""))
    sty = st.text_input("Stil (opsiyonel)", key="st_style", placeholder="Sıcak bir radyo sunucusu gibi oku")
    plain = PAUSE_RE.sub("", TAG_RE.sub("", prepare_text(txt)))
    st.markdown(f"<div class='tiny'>📊 {len(plain)} karakter · ~{max(1, len(plain)/15):.0f} sn · {count_calls(txt)} API isteği</div>", unsafe_allow_html=True)
    if st.button("🎤 Anonsu üret", type="primary", key="st_go", **UCW):
        if not txt.strip():
            st.warning("⚠️ Metin boş.")
        else:
            with st.spinner("Seslendiriliyor…"):
                try:
                    wav, _ = synthesize(txt, sv, sm, "tr-TR", sty)
                    st.session_state["_st_wav"], st.session_state["_st_txt"] = wav, txt
                except Exception as ex:
                    st.session_state["_st_wav"] = None
                    st.error(f"❌ {ex}")
    wv = st.session_state.get("_st_wav")
    if wv:
        st.markdown(f"<div class='card g'>✅ Hazır · {wav_dur(wv):.1f} sn</div>", unsafe_allow_html=True)
        st.markdown(waveform_svg(wv), unsafe_allow_html=True)
        st.audio(wv, format="audio/wav")
        n1, n2 = st.columns([3, 1])
        nm = n1.text_input("Kütüphane adı", st.session_state.get("_st_txt", "")[:40].replace("\n", " "), key="st_name")
        if n2.button("📚 Kaydet", key="st_save", **UCW):
            r = media_add(f"{slug(nm)}.wav", wv, "voice", parse=False, src="tts", text=st.session_state.get("_st_txt", ""), name=nm or "Anons", artist="")
            st.toast("📚 Kütüphaneye eklendi" if r else "Bu ses zaten kütüphanede")
        st.download_button("💾 WAV indir", wv, file_name=f"{slug(nm)}.wav", mime="audio/wav", key="st_dl", **UCW)
    with st.expander("📦 Toplu üret (her satır ayrı anons → kütüphane)", expanded=False):
        bt = st.text_area("Satırlar", height=120, key="st_bulk", placeholder="Her satıra bir anons yazın")
        lines = [l.strip() for l in bt.splitlines() if l.strip()]
        st.caption(f"{len(lines)} satır · ~{sum(count_calls(l) for l in lines)} API isteği")
        if st.button("Toplu üret ve kaydet", key="st_bulk_go", disabled=not lines, **UCW):
            prog = st.progress(0.0, "Başlıyor…")
            ok, errs = 0, []
            for i, l in enumerate(lines):
                prog.progress(i / len(lines), f"{i+1}/{len(lines)}")
                try:
                    w, _ = synthesize(l, sv, sm, "tr-TR", sty)
                    ok += 1 if media_add(f"{slug(l,20)}.wav", w, "voice", parse=False, src="tts", text=l, name=l[:40], artist="") else 0
                except Exception as ex:
                    errs.append(f"{i+1}: {ex}")
                    if "kalmadı" in str(ex):
                        break
            prog.empty()
            st.session_state["_msg"] = f"✅ {ok}/{len(lines)} anons kütüphaneye eklendi" + (" · ❌ " + " | ".join(errs[:2]) if errs else "")
            st.rerun()

    with st.expander("👥 Diyalog (iki sesli · 'Ad: metin' biçimi)", expanded=False):
        dc1, dc2 = st.columns(2)
        with dc1:
            sp1 = st.text_input("1. konuşmacı", "Ayşe", key="dl_sp1")
            dv1 = sel_map("1. konuşmacı sesi", VOICE_LABELS, "Kore", "dl_v1")
        with dc2:
            sp2 = st.text_input("2. konuşmacı", "Mehmet", key="dl_sp2")
            dv2 = sel_map("2. konuşmacı sesi", VOICE_LABELS, "Puck", "dl_v2")
        dtx = st.text_area("Diyalog", height=130, key="dl_text",
                           value="Ayşe: Günaydın! İmaj FM'de sabah kuşağı başlıyor.\nMehmet: Bugün çok güzel şarkılar ve sürprizler var.\nAyşe: O zaman hemen müziğe geçelim!")
        if st.button("🎤 Diyaloğu üret", key="dl_go", disabled=not (sp1.strip() and sp2.strip() and dtx.strip()), **UCW):
            with st.spinner("Diyalog seslendiriliyor…"):
                try:
                    w, _ = synthesize_multi(dtx, sm, "tr-TR", sp1.strip(), dv1, sp2.strip(), dv2)
                    st.session_state["_dl_wav"], st.session_state["_dl_txt"] = w, dtx
                except Exception as ex:
                    st.session_state["_dl_wav"] = None
                    st.error(f"❌ {ex}")
        dw = st.session_state.get("_dl_wav")
        if dw:
            st.markdown(f"<div class='card g'>✅ Diyalog hazır · {wav_dur(dw):.1f} sn</div>", unsafe_allow_html=True)
            st.audio(dw, format="audio/wav")
            dn = st.text_input("Kütüphane adı", "Diyalog " + datetime.datetime.now().strftime("%H:%M"), key="dl_name")
            q1, q2 = st.columns(2)
            if q1.button("📚 Kütüphaneye kaydet", key="dl_save", **UCW):
                r = media_add(f"{slug(dn)}.wav", dw, "voice", parse=False, src="tts", text=st.session_state.get("_dl_txt", ""), name=dn, artist="")
                st.toast("📚 Kütüphaneye eklendi" if r else "Bu ses zaten kütüphanede")
            q2.download_button("💾 WAV indir", dw, file_name=f"{slug(dn)}.wav", mime="audio/wav", key="dl_dl", **UCW)

    with st.expander("🎼 Anons + fon müziği (hazır karışım → kütüphane)", expanded=False):
        _voices = {m["id"]: media_label(m) for m in st.session_state._media if m["cat"] == "voice"}
        _beds = {m["id"]: media_label(m) for m in st.session_state._media if m["cat"] in ("bed", "jingle")}
        vsrc = ["Az önce üretilen anons"] + (["Kütüphaneden"] if _voices else [])
        vch = st.radio("Anons kaynağı", vsrc, horizontal=True, key="bm_src")
        vmid = ""
        if vch == "Kütüphaneden":
            vmid = sel_map("Anons", _voices, next(iter(_voices)), "bm_voice")
        if not _beds:
            st.caption("Kütüphaneye 'Fon müziği' veya 'Jingle' kategorisinde bir dosya ekleyin.")
        else:
            bmid = sel_map("Fon müziği", _beds, next(iter(_beds)), "bm_bed")
            r1, r2 = st.columns(2)
            bl = r1.slider("Fon seviyesi (dB)", -30.0, 0.0, -8.0, 1.0, key="bm_lvl")
            bd = r2.slider("Konuşmada kıs (dB)", 0.0, 30.0, 14.0, 1.0, key="bm_duck")
            r3, r4 = st.columns(2)
            bp = r3.number_input("Anons öncesi müzik (sn)", 0.0, 20.0, 2.0, 0.5, key="bm_pre")
            bq = r4.number_input("Anons sonrası müzik (sn)", 0.0, 30.0, 3.0, 0.5, key="bm_post")
            if st.button("🎛️ Karıştır", key="bm_go", **UCW):
                try:
                    if vch == "Kütüphaneden":
                        vm = media_map().get(vmid)
                        vw = np_to_wav(decode_mono(media_bytes(vm))) if vm and media_bytes(vm) else None
                    else:
                        vw = st.session_state.get("_st_wav")
                    bmm = media_map().get(bmid)
                    if not vw:
                        st.warning("Önce bir anons üretin veya kütüphaneden seçin.")
                    elif not bmm or media_bytes(bmm) is None:
                        st.warning("Fon müziği dosyası bulunamadı.")
                    else:
                        st.session_state["_bm_wav"] = mix_music(vw, media_bytes(bmm), bl, bd, bp, bq)
                except Exception as ex:
                    st.session_state["_bm_wav"] = None
                    st.error(f"❌ {ex}")
            bw = st.session_state.get("_bm_wav")
            if bw:
                st.markdown(f"<div class='card g'>✅ Karışım hazır · {wav_dur(bw):.1f} sn</div>", unsafe_allow_html=True)
                st.markdown(waveform_svg(bw), unsafe_allow_html=True)
                st.audio(bw, format="audio/wav")
                bn = st.text_input("Kütüphane adı", "Anons+müzik " + datetime.datetime.now().strftime("%H:%M"), key="bm_name")
                k1, k2 = st.columns(2)
                if k1.button("📚 Kütüphaneye kaydet", key="bm_save", **UCW):
                    r = media_add(f"{slug(bn)}.wav", bw, "voice", parse=False, src="tts", name=bn, artist="")
                    st.toast("📚 Kütüphaneye eklendi" if r else "Bu ses zaten kütüphanede")
                k2.download_button("💾 WAV indir", bw, file_name=f"{slug(bn)}.wav", mime="audio/wav", key="bm_dl", **UCW)

# ══════════════════════════════════════════════════════════════════
# TAB 3 — YAYIN AKIŞI
# ══════════════════════════════════════════════════════════════════
def src_editor(src, key_prefix, mm, allow_voice_pick=True):
    """Anons kaynağı: yapay ses metni VEYA kütüphane dosyası."""
    typ = st.radio("Kaynak", ["Metin (yapay ses)", "Kütüphane (dosya / hazır anons)"], index=1 if src.get("type") == "lib" else 0,
                   horizontal=True, key=key_prefix + "_t")
    if typ.startswith("Metin"):
        src["type"] = "tts"
        src["text"] = st.text_area("Anons metni", value=src.get("text", ""), height=80, key=key_prefix + "_x",
                                   placeholder="{sarki} - {sanatci}  ·  {onceki} · {sonraki} · {saat} · {tarih} değişkenleri kullanılabilir")
        vopt = ["(varsayılan)"] + list(VOICES)
        v = st.selectbox("Ses", vopt, index=vopt.index(src["voice"]) if src.get("voice") in VOICES else 0, key=key_prefix + "_v")
        src["voice"] = "" if v == "(varsayılan)" else v
    else:
        src["type"] = "lib"
        mp = {"": "— seçin —"}
        mp.update({m["id"]: media_label(m) for m in mm.values() if m["cat"] in ("voice", "jingle", "ad", "other", "song")})
        r = sel_map("Dosya", mp, src.get("lib") or "", key_prefix + "_l")
        src["lib"] = r or None

def overlay_editor(it, ov, mm):
    ou = ov["uid"]
    with st.container(border=True):
        h1, h2 = st.columns([5, 1])
        ov["pos"] = sel_map("Konum", POS, ov["pos"], K("pos", ou))
        h2.button("🗑️", key=K("odel", ou), on_click=ov_del, args=(it["uid"], ou), **UCW)
        if ov["pos"] == "intro":
            st.caption("Anons, parçanın 'Intro (sn)' değerinde biter (Kütüphane'de parça için intro süresini girin). Girilmediyse 1 sn sonra başlar.")
        elif ov["pos"] not in ("pre", "post"):
            ov["t"] = st.number_input("t (sn)", 0.0, 3600.0, float(ov["t"]), 0.5, key=K("ot", ou))
        src_editor(ov["src"], K("os", ou), mm)
        d1, d2 = st.columns(2)
        dk = d1.number_input("Kısma dB (−1 = varsayılan)", -1.0, 40.0, -1.0 if ov["duck_db"] is None else float(ov["duck_db"]), 1.0, key=K("od", ou),
                             help="Anons süresince parçanın ne kadar kısılacağı.")
        ov["duck_db"] = None if dk < 0 else float(dk)
        ov["gain_db"] = d2.slider("Anons seviyesi dB", -12.0, 8.0, float(ov["gain_db"]), 0.5, key=K("og", ou))
        bmp = {"": "Yok"}
        bmp.update({m["id"]: media_label(m) for m in mm.values() if m["cat"] in ("bed", "jingle")})
        b = sel_map("🎼 Fon müziği / jingle (anonsun altında)", bmp, ov.get("bed") or "", K("ob", ou))
        ov["bed"] = b or None
        if ov["bed"]:
            ov["bed_level"] = st.slider("Fon seviyesi dB", -30.0, 0.0, float(ov["bed_level"]), 1.0, key=K("obl", ou))

with t3:
    mm = media_map()
    pl, mx = st.session_state._pl, st.session_state._pl["mx"]
    items = pl["items"]
    st.markdown("<div class='card b'><b>📋 Yayın Akışı</b> — Parçaları sıralayın; her parçaya <b>katman</b> ekleyin: başa, sona, intro'ya sığdır, tam saniyeye anons/jingle. Anons başlayınca müzik otomatik kısılır. Anonsa fon müziği de eklenebilir.</div>", unsafe_allow_html=True)
    n1, n2 = st.columns([3, 1])
    pl["name"] = n1.text_input("Akış adı", value=pl["name"], key=K("pname"))
    n2.button("🆕 Yeni akış", key="pl_new", on_click=pl_new, **UCW)
    with st.expander("💾 Kaydet / yükle / dışa aktar", expanded=False):
        s1, s2 = st.columns(2)
        s1.button("💾 Kaydet", key="pl_save", on_click=pl_save, **UCW)
        saved = jload("playout/playlists.json", {})
        if saved:
            pk = st.selectbox("Kayıtlı akışlar", list(saved), key="pl_pick")
            l1, l2 = st.columns(2)
            l1.button("📂 Yükle", key="pl_load", on_click=pl_load, args=(pk,), **UCW)
            l2.button("🗑️ Sil", key="pl_forget", on_click=pl_forget, args=(pk,), **UCW)
        st.download_button("⬇️ Akışı JSON olarak indir", json.dumps(pl, ensure_ascii=False, indent=1), file_name=f"{slug(pl['name'])}.json",
                           mime="application/json", key="pl_exp", **UCW)
        up = st.file_uploader("Akış JSON yükle", type="json", key="pl_imp")
        if up is not None:
            raw = up.getvalue(); hs = hashlib.md5(raw).hexdigest()
            if hs != st.session_state.get("_pl_imp_hash"):
                try:
                    st.session_state._pl = _pl_merge(json.loads(raw.decode("utf-8")))
                    st.session_state._plv += 1
                    st.session_state["_pl_imp_hash"] = hs
                    st.rerun()
                except Exception as ex:
                    st.error(f"Geçersiz dosya: {ex}")

    # ── ekleme
    st.markdown("<span class='sl'>▶ Akışa ekle</span>", unsafe_allow_html=True)
    addmap = {"": "— kütüphaneden seçin —"}
    addmap.update({m["id"]: media_label(m) for m in mm.values() if m["cat"] != "bed"})
    pick_id = sel_map("Kütüphane", addmap, "", "add_pick")
    a1, a2, a3 = st.columns(3)
    a1.button("➕ Seçileni ekle", key="add_media", on_click=pl_add_media, args=(pick_id,), disabled=not pick_id, **UCW)
    a2.button("➕ Anons bloğu (metin)", key="add_voice", on_click=pl_add_voice, **UCW)
    a3.button("➕ Boşluk", key="add_gap", on_click=pl_add_gap, **UCW)

    # ── zaman çizelgesi
    if items:
        st.markdown("<span class='sl'>▶ Zaman çizelgesi</span>", unsafe_allow_html=True)
        st.markdown(timeline_html(items, mm, mx), unsafe_allow_html=True)
        st.markdown("<div class='tiny'>" + " · ".join(f"<span style='color:{c}'>■</span> {CATS[k]}" for k, c in CAT_COL.items() if k in ("song", "jingle", "voice")) + f" · tahmini toplam <b>{est_total(items, mm, mx)/60:.1f} dk</b></div>", unsafe_allow_html=True)

    # ── otomatik akış
    with st.expander("🤖 Otomatik akış oluşturucu (saat çarkı)", expanded=not items):
        st.caption("Hedef süreye kadar şarkıları karıştırır; aynı sanatçıyı arka arkaya çalmaz; belli aralıklarla anons ve jingle ekler; her şarkıya başlangıç/bitiş anonsu katmanı koyar.")
        st.slider("Hedef süre (dk)", 10, 240, 60, 5, key="af_min")
        st.multiselect("Şarkı etiketleri (boş = tümü)", sorted({t for m in st.session_state._media if m["cat"] == "song" for t in mtags(m)}), key="af_tags")
        q1, q2, q3 = st.columns(3)
        q1.slider("Her N şarkıda anons/jingle", 0, 8, 3, key="af_every")
        q2.slider("Sanatçı ayrımı (şarkı)", 0, 8, 3, key="af_sep")
        q3.number_input("Şarkı en fazla (sn) · 0 = tamamı", 0.0, 900.0, 0.0, 15.0, key="af_cap")
        st.text_input("Şarkı başı anonsu (intro'ya sığar)", value="Şimdi İmaj FM'de {sanatci} - {sarki}.", key="af_intro")
        st.text_input("Şarkı sonu anonsu", value="{sanatci} ile {sarki} dinlediniz. Saat {saat}.", key="af_outro")
        st.text_area("Anons havuzu (her satır bir anons; rastgele seçilir)", height=80, key="af_pool",
                     value="[excitedly] İmaj FM, müziğin adresi!\nSaat {saat}, İmaj FM ile devam ediyoruz.\n[normal] Sıradaki şarkı: {sonraki}.")
        st.text_input("Açılış anonsu", value="[excitedly] İmaj FM'e hoş geldiniz!", key="af_open")
        st.text_input("Kapanış anonsu", value="İmaj FM'i dinlediğiniz için teşekkürler.", key="af_close")
        bmp2 = {"": "Yok"}
        bmp2.update({m["id"]: media_label(m) for m in mm.values() if m["cat"] == "bed"})
        st.session_state["af_bed_id"] = sel_map("🎼 Anons blokları altında fon müziği", bmp2, "", "af_bed_sel") or None
        z1, z2, z3 = st.columns(3)
        z1.checkbox("Süreyi tam oturt (son şarkıyı kısalt)", True, key="af_exact")
        z2.checkbox("Mevcut akışa ekle", False, key="af_append")
        z3.number_input("Tohum (0 = rastgele)", 0, 99999, 0, key="af_seed")
        st.button("🤖 Akışı oluştur", key="af_go", on_click=autofill, type="primary", **UCW)
        if st.session_state.get("_af_msg"):
            st.markdown(f"<div class='card b'>{esc(st.session_state['_af_msg'])}</div>", unsafe_allow_html=True)

    # ── öğe listesi
    st.markdown("<span class='sl'>▶ Akış öğeleri</span>", unsafe_allow_html=True)
    if not items:
        st.info("Akış boş. Kütüphaneden parça ekleyin veya otomatik oluşturucuyu kullanın.")
    st.button("🧹 Akışı temizle", key="pl_clear", on_click=pl_clear, disabled=not items, **UCW)
    for i, it in enumerate(items):
        uid = it["uid"]
        with st.expander(item_title(i, it, mm), expanded=False):
            m1, m2, m3, m4 = st.columns(4)
            m1.button("⬆️", key=K("up", uid), on_click=pl_move, args=(i, -1), disabled=(i == 0), **UCW)
            m2.button("⬇️", key=K("dn", uid), on_click=pl_move, args=(i, 1), disabled=(i == len(items) - 1), **UCW)
            m3.button("📄 Çoğalt", key=K("dp", uid), on_click=pl_dup, args=(i,), **UCW)
            m4.button("🗑️", key=K("rm", uid), on_click=pl_del, args=(i,), **UCW)
            if it["kind"] == "track":
                m = mm.get(it["media"])
                if m:
                    st.caption(f"{CATS[m['cat']]} · {m['dur']:.0f} sn · RMS {m['rms_db']} dB · intro {m.get('intro_s',0)} sn")
                else:
                    st.warning("Kütüphanede bulunamadı; bu öğe atlanır.")
                c1, c2, c3 = st.columns(3)
                it["limit"] = c1.number_input("Süre sınırı (sn) · 0 = tamamı", 0.0, 3600.0, float(it["limit"]), 5.0, key=K("lim", uid))
                it["gain_db"] = c2.number_input("Kazanç dB", -24.0, 12.0, float(it["gain_db"]), 0.5, key=K("gn", uid))
                xf = c3.number_input("Crossfade sn (−1 = varsayılan)", -1.0, 15.0, -1.0 if it["xfade"] is None else float(it["xfade"]), 0.5, key=K("xf", uid))
                it["xfade"] = None if xf < 0 else float(xf)
                f1, f2 = st.columns(2)
                fi = f1.number_input("Fade-in sn (−1 = varsayılan)", -1.0, 10.0, -1.0 if it["fade_in"] is None else float(it["fade_in"]), 0.1, key=K("fi", uid))
                fo = f2.number_input("Fade-out sn (−1 = varsayılan)", -1.0, 15.0, -1.0 if it["fade_out"] is None else float(it["fade_out"]), 0.1, key=K("fo", uid))
                it["fade_in"], it["fade_out"] = (None if fi < 0 else float(fi)), (None if fo < 0 else float(fo))
                st.markdown("<span class='sl2'>▸ KATMANLAR (anons · jingle · fon müziği)</span>", unsafe_allow_html=True)
                qa = st.columns(5)
                for col, (pos, lbl) in zip(qa, (("start", "▶ Başa"), ("intro", "🎼 Intro'ya"), ("end", "⏹ Sona"), ("pre", "⏮ Önce"), ("post", "⏭ Sonra"))):
                    col.button(lbl, key=K("q" + pos, uid), on_click=ov_add, args=(uid, pos), **UCW)
                if not it["overlays"]:
                    st.caption("Henüz katman yok. Yukarıdaki düğmelerle anons ekleyin.")
                for ov in it["overlays"]:
                    overlay_editor(it, ov, mm)
            elif it["kind"] == "voice":
                src_editor(it["src"], K("vs", uid), mm)
                gg1, gg2 = st.columns(2)
                it["gain_db"] = gg1.slider("Anons seviyesi dB", -12.0, 8.0, float(it["gain_db"]), 0.5, key=K("vg", uid))
                bmp3 = {"": "Yok"}
                bmp3.update({m["id"]: media_label(m) for m in mm.values() if m["cat"] in ("bed", "jingle")})
                b = sel_map("🎼 Fon müziği (anonsun altında)", bmp3, it.get("bed") or "", K("vb", uid))
                it["bed"] = b or None
                if it["bed"]:
                    b1, b2, b3 = st.columns(3)
                    it["bed_level"] = b1.number_input("Fon dB", -40.0, 0.0, float(mx["bed_level"] if it["bed_level"] is None else it["bed_level"]), 1.0, key=K("vbl", uid))
                    it["pre"] = b2.number_input("Önce müzik sn", 0.0, 20.0, float(mx["bed_pre"] if it["pre"] is None else it["pre"]), 0.5, key=K("vpr", uid))
                    it["post"] = b3.number_input("Sonra müzik sn", 0.0, 30.0, float(mx["bed_post"] if it["post"] is None else it["post"]), 0.5, key=K("vpo", uid))
            else:
                it["sec"] = st.number_input("Boşluk (sn)", 0.0, 120.0, float(it["sec"]), 0.5, key=K("gap", uid))

    _js = json.dumps(pl, sort_keys=True, ensure_ascii=False)
    if _js != st.session_state.get("_pl_saved"):
        jsave("playout/current.json", pl)
        st.session_state["_pl_saved"] = _js

# ══════════════════════════════════════════════════════════════════
# TAB 4 — YAYIN ÇIKTISI
# ══════════════════════════════════════════════════════════════════
def out_delete(bid):
    for e in st.session_state._bcs:
        if e["id"] == bid:
            try: (OUT / f"{bid}.{e['fmt']}").unlink()
            except Exception: pass
    st.session_state._bcs = [e for e in st.session_state._bcs if e["id"] != bid]
    jsave("playout/outputs.json", st.session_state._bcs)

with t4:
    mm = media_map()
    pl, mx = st.session_state._pl, st.session_state._pl["mx"]
    items = pl["items"]
    st.markdown("<div class='card b'><b>📻 Yayın Çıktısı</b> — Akışı tek parça tam yayın dosyasına birleştirir (44.1 kHz stereo). Önce önizleme alıp mix'i kontrol edin; yapay ses anonsları bir kez üretilir ve önbellekte kalır.</div>", unsafe_allow_html=True)
    o1, o2 = st.columns(2)
    fopts = ["MP3", "WAV"]
    mx["fmt"] = o1.radio("Çıktı biçimi", fopts, index=fopts.index(mx["fmt"]) if mx["fmt"] in fopts else 0, horizontal=True, key=K("o_fmt"))
    mx["kbps"] = o2.select_slider("MP3 kalitesi (kbps)", [128, 192, 256, 320], value=int(mx["kbps"]), key=K("o_kb"))
    need = collect_tts(items, mm, mx)
    miss_n = sum(1 for v in need.values() if not v)
    _, _, rem = pool_stats()
    warn = miss_n > rem
    st.markdown(f"<div class='card {'a' if warn else 'b'}'>{len(items)} öğe · tahmini <b>{est_total(items, mm, mx)/60:.1f} dk</b> · yapay ses anonsu: {len(need)} "
                f"(<b>{miss_n}</b> üretilecek, kalan istek <b>{rem}</b>)"
                f"{'<br>⚠️ Kota yetmeyebilir; üretilenler korunur, kota gelince devam edilir.' if warn else ''}</div>", unsafe_allow_html=True)
    if miss_n:
        if st.button(f"⚙️ Eksik {miss_n} anonsu önceden üret", key="pre_tts", **UCW):
            prog = st.progress(0.0, "Üretiliyor…")
            done, err = 0, ""
            todo = [(t, v) for (t, v), c in need.items() if not c]
            for i, (t, v) in enumerate(todo):
                prog.progress(i / len(todo), f"{i+1}/{len(todo)} · {t[:40]}")
                try:
                    tts_cached(t, v, mx); done += 1
                except Exception as ex:
                    err = str(ex); break
            prog.empty()
            st.session_state["_msg"] = f"✅ {done}/{len(todo)} anons hazır" + (f" · ❌ {err}" if err else "")
            st.rerun()
    # önizleme
    st.markdown("<span class='sl'>▶ Önizleme</span>", unsafe_allow_html=True)
    p1, p2 = st.columns(2)
    pv_sec = p1.number_input("Süre (sn)", 15, 600, 60, 15, key="pv_sec")
    smap = {-1: "Baştan"}
    smap.update({i: item_title(i, it, mm) for i, it in enumerate(items)})
    pv_from = sel_map("Başlangıç öğesi", smap, -1, "pv_from")
    run_prev = st.button("🎧 Önizleme", key="bc_prev", disabled=not items, **UCW)
    run_full = st.button("📻 Tam Yayını Oluştur", type="primary", key="bc_go", disabled=not items, **UCW)
    if run_prev or run_full:
        fmt = "mp3" if mx["fmt"] == "MP3" else "wav"
        if fmt == "mp3" and lameenc is None:
            st.error("MP3 için `pip install lameenc` gerekli (veya WAV seçin).")
        else:
            bid = hashlib.md5(str(time.time()).encode()).hexdigest()[:10]
            out = OUT / (f"{bid}.{fmt}" if run_full else f"_preview.{fmt}")
            prog = st.progress(0.0, "Başlıyor…")
            try:
                total, cues = render_playout(items, mm, mx, lambda t, v: tts_cached(t, v, mx), out, fmt,
                                             lambda f, t: prog.progress(min(max(f, 0.0), 1.0), t),
                                             start=0 if (run_full or pv_from < 0) else pv_from,
                                             max_sec=0 if run_full else pv_sec)
                if run_full:
                    st.session_state._bcs.insert(0, {"id": bid, "name": pl["name"], "fmt": fmt, "dur": round(total, 1),
                                                     "size": out.stat().st_size, "n": len(items), "cues": cues,
                                                     "ts": datetime.datetime.now().strftime("%d.%m %H:%M")})
                    jsave("playout/outputs.json", st.session_state._bcs)
                else:
                    st.session_state["_pv_path"] = str(out)
                st.session_state["_bc_err"] = ""
            except Exception as ex:
                st.session_state["_bc_err"] = str(ex)
            prog.empty()
    if st.session_state.get("_bc_err"):
        st.markdown(f"<div class='card r'>❌ {esc(st.session_state['_bc_err'])}</div>", unsafe_allow_html=True)
    pvp = st.session_state.get("_pv_path")
    if pvp and Path(pvp).exists():
        st.markdown("<div class='card p'>🎧 Önizleme (kayıtlı çıktılara eklenmez)</div>", unsafe_allow_html=True)
        st.audio(Path(pvp).read_bytes(), format="audio/mpeg" if pvp.endswith("mp3") else "audio/wav")
    st.markdown("<span class='sl'>▶ Tamamlanan yayınlar</span>", unsafe_allow_html=True)
    if not st.session_state._bcs:
        st.caption("Henüz çıktı yok.")
    for e in st.session_state._bcs[:10]:
        f = OUT / f"{e['id']}.{e['fmt']}"
        if not f.exists():
            continue
        st.markdown(f"<div class='card g'>✅ <b>{esc(e['name'])}</b> · {e['ts']} · {e['dur']/60:.1f} dk · {e['n']} öğe · {e['size']//1024} KB · {e['fmt'].upper()}</div>", unsafe_allow_html=True)
        data = f.read_bytes()
        mime = "audio/mpeg" if e["fmt"] == "mp3" else "audio/wav"
        st.audio(data, format=mime)
        d1, d2 = st.columns([4, 1])
        d1.download_button(f"💾 İndir ({e['fmt'].upper()})", data, file_name=f"{slug(e['name'])}_{e['id']}.{e['fmt']}", mime=mime, key=f"dl_{e['id']}", **UCW)
        d2.button("🗑️", key=f"del_{e['id']}", on_click=out_delete, args=(e["id"],), **UCW)
        cues_ = e.get("cues", [])
        if cues_:
            with st.expander("📋 Yayın akış listesi (zaman damgalı · telif raporu)", expanded=False):
                st.dataframe([{"Zaman": fmt_t(c["t"]), "Tür": {"track": "Parça", "voice": "Anons", "anons": "Anons (katman)"}.get(c["kind"], c["kind"]),
                               "Sanatçı": c.get("artist", ""), "Ad": c["name"]} for c in cues_], hide_index=True, **UCW_DF)
                x1, x2 = st.columns(2)
                x1.download_button("📄 TXT", cue_text(cues_, e["name"]), file_name=f"akis_{e['id']}.txt", mime="text/plain", key=f"ct_{e['id']}", **UCW)
                x2.download_button("📊 CSV (rapor)", cue_csv(cues_), file_name=f"rapor_{e['id']}.csv", mime="text/csv", key=f"cc_{e['id']}", **UCW)

# ══════════════════════════════════════════════════════════════════
# TAB 5 — AYARLAR
# ══════════════════════════════════════════════════════════════════
with t5:
    pl, mx = st.session_state._pl, st.session_state._pl["mx"]
    st.markdown("<div class='card b'><b>⚙️ Mix ayarları</b> bu yayın akışına özeldir ve akışla birlikte kaydedilir. Parça/katman bazında değer girilmezse bunlar kullanılır.</div>", unsafe_allow_html=True)
    st.markdown("<span class='sl'>▶ Geçiş ve fade</span>", unsafe_allow_html=True)
    mx["crossfade"] = st.slider("Parçalar arası crossfade (sn)", 0.0, 12.0, float(mx["crossfade"]), 0.5, key=K("x_cf"))
    c1, c2 = st.columns(2)
    mx["fade_in"] = c1.slider("Fade-in (sn)", 0.0, 5.0, float(mx["fade_in"]), 0.1, key=K("x_fi"))
    mx["fade_out"] = c2.slider("Fade-out (sn)", 0.0, 10.0, float(mx["fade_out"]), 0.1, key=K("x_fo"))
    st.markdown("<span class='sl'>▶ Anons ve otomatik kısma (ducking)</span>", unsafe_allow_html=True)
    mx["duck_db"] = st.slider("Anons sırasında parçayı kıs (dB)", 0.0, 30.0, float(mx["duck_db"]), 1.0, key=K("x_dk"))
    mx["voice_db"] = st.slider("Anons ses seviyesi (dB)", -12.0, 8.0, float(mx["voice_db"]), 0.5, key=K("x_vd"))
    mx["voice_gap"] = st.slider("'Önce/Sonra' anonslarda boşluk (sn)", 0.0, 2.0, float(mx["voice_gap"]), 0.05, key=K("x_vg"))
    st.markdown("<span class='sl'>▶ Seviye eşitleme</span>", unsafe_allow_html=True)
    mx["normalize"] = st.checkbox("Parçaları aynı ses seviyesine getir (RMS)", bool(mx["normalize"]), key=K("x_nm"))
    l1, l2 = st.columns(2)
    mx["target_db"] = l1.slider("Hedef seviye (dB RMS)", -24.0, -10.0, float(mx["target_db"]), 0.5, key=K("x_tg"))
    mx["max_boost"] = l2.slider("En fazla yükseltme (dB)", 0.0, 20.0, float(mx["max_boost"]), 1.0, key=K("x_mb"))
    st.markdown("<span class='sl'>▶ Anons + fon müziği</span>", unsafe_allow_html=True)
    mx["bed_level"] = st.slider("Fon müziği seviyesi (tek başınayken, dB)", -30.0, 0.0, float(mx["bed_level"]), 1.0, key=K("x_bl"))
    mx["bed_duck"] = st.slider("Konuşmada fon müziği kısma (dB)", 0.0, 30.0, float(mx["bed_duck"]), 1.0, key=K("x_bd"))
    b1, b2 = st.columns(2)
    mx["bed_pre"] = b1.slider("Anons öncesi müzik (sn)", 0.0, 15.0, float(mx["bed_pre"]), 0.5, key=K("x_bp"))
    mx["bed_post"] = b2.slider("Anons sonrası müzik (sn)", 0.0, 20.0, float(mx["bed_post"]), 0.5, key=K("x_bq"))
    st.markdown("<span class='sl'>▶ Yapay ses (anons) varsayılanları</span>", unsafe_allow_html=True)
    mx["voice"] = sel_map("Varsayılan anons sesi", VOICE_LABELS, mx["voice"], K("x_voice"))
    models = get_models()
    mx["model"] = sel_map("Model", models, mx["model"], K("x_model"))
    mx["style"] = st.text_input("Stil (opsiyonel)", mx.get("style", ""), key=K("x_style"), placeholder="Sıcak bir radyo sunucusu gibi oku")
    cfg()["custom_model"] = st.text_input("Özel model adı", cfg().get("custom_model", ""), key="x_cm", placeholder="örn. gemini-3.8-flash-tts")
    st.caption("Değişkenler: {sarki} {sanatci} {onceki} {sonraki} {saat} {tarih}. Köşeli duygu etiketleri ve [pause 1] anons metinlerinde çalışır.")
    st.markdown("<span class='sl'>▶ Yapay ses işleme (tüm anonslar)</span>", unsafe_allow_html=True)
    _c = cfg()
    pp1, pp2, pp3 = st.columns(3)
    _c["nums"] = pp1.checkbox("Sayıları yazıya çevir", bool(_c["nums"]), key="x_nums", help="%30 → yüzde otuz, 18:05 → on sekiz sıfır beş")
    _c["use_dict"] = pp2.checkbox("Okunuş sözlüğü", bool(_c["use_dict"]), key="x_ud")
    _c["chunk"] = pp3.checkbox("Uzun metni böl", bool(_c["chunk"]), key="x_ck")
    pq1, pq2, pq3 = st.columns(3)
    _c["trim"] = pq1.checkbox("Baş/son sessizliği kırp", bool(_c["trim"]), key="x_tr")
    _c["norm"] = pq2.checkbox("Anonsu normalize et", bool(_c["norm"]), key="x_no")
    _c["comp"] = pq3.checkbox("Hafif sıkıştırma", bool(_c["comp"]), key="x_cp")
    pr1, pr2, pr3, pr4 = st.columns(4)
    _c["fade_ms"] = pr1.number_input("Fade (ms)", 0, 500, int(_c["fade_ms"]), 5, key="x_fms")
    _c["head"] = pr2.number_input("Baş boşluk (sn)", 0.0, 2.0, float(_c["head"]), 0.05, key="x_hd")
    _c["tail"] = pr3.number_input("Son boşluk (sn)", 0.0, 3.0, float(_c["tail"]), 0.05, key="x_tl")
    _c["chunk_chars"] = pr4.number_input("Parça karakter", 200, 4000, int(_c["chunk_chars"]), 100, key="x_cc")
    _c["dict"] = st.text_area("Okunuş sözlüğü (her satır KISALTMA=okunuşu)", _c["dict"], height=90, key="x_dict")
    st.caption("Bu ayarlar ana uygulamayla ortaktır (settings.json). Değişiklik yeni üretilen anonslarda geçerli olur; önbellekteki eski anonslar için önbelleği temizleyin.")

    st.markdown("<span class='sl'>▶ API anahtar havuzu</span>", unsafe_allow_html=True)
    _c["max_per_key"] = int(st.number_input("Anahtar başına istek sınırı (günlük)", 1, 1000, int(_c["max_per_key"]), 1, key="x_mpk"))
    _pool = st.session_state._pool
    _lbl_before = [s["label"] for s in _pool]
    for _i in range(10):
        _s = _pool[_i]
        if f"key_{_i}" not in st.session_state:
            st.session_state[f"key_{_i}"] = _s["key"]
        if f"lbl_{_i}" not in st.session_state:
            st.session_state[f"lbl_{_i}"] = _s["label"]
        _title = f"{'🟢' if _s['key'].strip() else '⚪'} {_s['label']} · {_s['used']}/{mpk()}" + (" · ▶ aktif" if _i == st.session_state._active and _s["key"].strip() else "")
        with st.expander(_title, expanded=False):
            ka, kb = st.columns([1, 2])
            _s["label"] = ka.text_input("Ad", key=f"lbl_{_i}").strip() or f"API {_i+1}"
            _s["key"] = kb.text_input("Anahtar", type="password", key=f"key_{_i}", placeholder="AIzaSy...")
            _pct = min(100, int(_s["used"] / max(1, mpk()) * 100))
            _col = "#22c55e" if _pct < 60 else "#f59e0b" if _pct < 90 else "#ef4444"
            st.markdown(f"<div class='qbar'><div class='qbar-f' style='width:{_pct}%;background:{_col};'></div></div>", unsafe_allow_html=True)
            ba, bb, bc = st.columns(3)
            ba.button("▶ Aktif yap", key=f"pa_{_i}", on_click=pool_activate, args=(_i,), disabled=not _s["key"].strip(), **UCW)
            bb.button("♻️ Sayacı sıfırla", key=f"pr_{_i}", on_click=pool_reset, args=(_i,), **UCW)
            bc.button("🗑️ Sil", key=f"pd_{_i}", on_click=pool_delete, args=(_i,), **UCW)
    if [s["label"] for s in _pool] != _lbl_before:
        save_pool()
    _stt = st.session_state._stats
    _dl = _stt.get("daily", {})
    st.caption(f"Toplam istek: {_stt.get('calls', 0)} · karakter: {_stt.get('chars', 0)} · bugün: {_dl.get(datetime.date.today().isoformat(), 0)} istek. "
               "Anahtarlar güvenlik için diske yazılmaz; kalıcı olması için secrets.toml içine GEMINI_API_KEY_1… olarak ekleyin.")
    if st.button("🔎 Anahtarımın TTS modellerini listele", key="x_listm", **UCW):
        _k, _ix = get_active_key()
        if _k is None:
            st.warning("Kullanılabilir API anahtarı yok.")
        else:
            try:
                st.session_state["_tts_list"] = list_tts_models(_k)
            except Exception as ex:
                st.session_state["_tts_list"] = []
                st.error(f"❌ {ex}")
    if st.session_state.get("_tts_list") is not None and st.session_state.get("_tts_list") != []:
        st.code("\n".join(st.session_state["_tts_list"]), language="text")
        st.caption("Listedeki adı yukarıdaki 'Özel model adı' alanına yazarak kullanabilirsiniz.")

    st.markdown("<span class='sl'>▶ Yedekle / geri yükle</span>", unsafe_allow_html=True)
    st.caption("Kütüphane (ses dosyaları + bilgiler) ve kayıtlı akışlar tek ZIP'te. Geri yükleme mevcut verinin üstüne ekler, hiçbir şeyi silmez.")
    y1, y2 = st.columns(2)
    if y1.button("📦 Yedek ZIP hazırla", key="bk_make", **UCW):
        try:
            st.session_state["_bk_zip"] = make_backup()
        except Exception as ex:
            st.error(f"❌ {ex}")
    if st.session_state.get("_bk_zip"):
        y1.download_button("⬇️ Yedeği indir", st.session_state["_bk_zip"], file_name=f"imajfm_yedek_{datetime.date.today().isoformat()}.zip",
                           mime="application/zip", key="bk_dl", **UCW)
    _bz = y2.file_uploader("Yedek ZIP yükle", type="zip", key="bk_up")
    if _bz is not None:
        _raw = _bz.getvalue(); _h = hashlib.md5(_raw).hexdigest()
        if _h != st.session_state.get("_bk_hash"):
            try:
                _a, _p = restore_backup(_raw)
                st.session_state["_bk_hash"] = _h
                st.session_state["_msg"] = f"✅ Geri yüklendi: {_a} medya kaydı · {_p} akış"
                st.rerun()
            except Exception as ex:
                st.error(f"Geçersiz yedek: {ex}")

    st.markdown("<span class='sl'>▶ Veri</span>", unsafe_allow_html=True)
    st.caption(f"Veri klasörü: {DATA.resolve()} · Kütüphane: {len(st.session_state._media)} dosya · Çıktılar: {len(st.session_state._bcs)}")
    if st.session_state.get("_io_err"):
        st.warning(f"Diske yazılamadı: {st.session_state['_io_err']}")

_js = json.dumps(st.session_state._pl, sort_keys=True, ensure_ascii=False)
if _js != st.session_state.get("_pl_saved"):
    jsave("playout/current.json", st.session_state._pl)
    st.session_state["_pl_saved"] = _js
_cj = json.dumps(cfg(), sort_keys=True)
if _cj != st.session_state.get("_cfg_saved_po"):
    d = jload("settings.json", {})
    d.update({k: cfg()[k] for k in CFG_DEF if k in cfg()})
    jsave("settings.json", d)
    st.session_state["_cfg_saved_po"] = _cj
