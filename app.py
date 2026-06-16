"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  İMAJ FM · TTS STÜDYO  v6.0 — TAM ENTEGRE YAYIN SİSTEMİ                   ║
║  Gemini TTS · Delay Reji · Fon+Anons Mikseri · Yayın Otomasyonu            ║
║  Playlist · Toplu TTS · A/B Test · Kütüphane · Arşiv · ZIP                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import streamlit as st
import wave, io, zipfile, re, time, datetime, hashlib, os, shutil

from google import genai
from google.genai import types

try:
    from pydub import AudioSegment, effects as pydub_fx
    PYDUB_OK = True
except ImportError:
    PYDUB_OK = False

try:
    import numpy as np
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    NP_OK = True
except ImportError:
    NP_OK = False

# Dizinler
BASE  = os.path.abspath("imajfm_data")
DIRS  = {k: os.path.join(BASE, k) for k in
         ["playlist","fon","jingles","effects","output","archive","uploads","anons"]}
for d in DIRS.values():
    os.makedirs(d, exist_ok=True)

st.set_page_config(page_title="İmaj FM TTS v6", page_icon="🎙️",
                   layout="wide", initial_sidebar_state="expanded")

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
[data-testid="stTabs"] [data-baseweb="tab"]{background:transparent!important;color:#2e3f55!important;font-family:'Syne',sans-serif!important;font-weight:700!important;font-size:.7rem!important;padding:8px 12px!important;border-bottom:2px solid transparent!important;}
[data-testid="stTabs"] [aria-selected="true"]{color:#e05252!important;border-bottom:2px solid #e05252!important;}
.qbar{background:#101828;border-radius:4px;height:5px;margin:3px 0;overflow:hidden;}
.qbar-f{height:100%;border-radius:4px;}
.song-row{display:flex;align-items:center;gap:9px;background:#0b0f1a;border:1px solid #131c2e;
  border-radius:7px;padding:8px 12px;margin-bottom:5px;transition:border-color .15s;}
.song-row:hover{border-color:#3a7bd5;}
.song-nm{font-family:'Syne',sans-serif;font-size:.8rem;font-weight:700;color:#dde2ee;flex:1;}
.song-dur{font-family:'JetBrains Mono',monospace;font-size:.66rem;color:#2e3f55;}
.tl-block{background:#0b0f1a;border:1px solid #131c2e;border-radius:7px;padding:7px 11px;
  margin:3px 0;display:flex;align-items:center;gap:9px;}
.tl-time{font-family:'JetBrains Mono',monospace;font-size:.7rem;color:#10b981;min-width:46px;}
.tl-type{font-size:.6rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
  padding:2px 7px;border-radius:4px;min-width:58px;text-align:center;}
.ttype-song{background:#071a2e;color:#60a5fa;border:1px solid #1a3a5e;}
.ttype-anons{background:#1a0d00;color:#f59e0b;border:1px solid #5e3a00;}
.ttype-fon{background:#071a0f;color:#34d399;border:1px solid #0a3d1f;}
.tl-lbl{font-size:.76rem;color:#6b7a8d;flex:1;}
.tl-dur{font-family:'JetBrains Mono',monospace;font-size:.63rem;color:#2e3f55;}
.rjhdr{background:linear-gradient(135deg,#071a0f,#07090f);border:1px solid #0d2e1a;
  border-radius:12px;padding:16px 20px;margin-bottom:14px;position:relative;overflow:hidden;}
.rjhdr::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,#10b981,#34d399,#10b981);background-size:200%;animation:scan 4s linear infinite;}
.rjhdr h2{font-family:'Syne',sans-serif;font-size:1.15rem;font-weight:800;margin:0 0 2px;
  background:linear-gradient(90deg,#fff 30%,#34d399);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.rjhdr p{margin:0;color:#2e5040;font-size:.73rem;}
.fav-card{background:#0b0f1a;border:1px solid #131c2e;border-radius:7px;padding:8px 11px;margin:4px 0;}
.fav-name{font-family:'Syne',sans-serif;font-size:.73rem;font-weight:700;color:#dde2ee;}
.fav-prev{font-size:.68rem;color:#3d4f68;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
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
    "gemini-2.5-flash-tts":"🚀 2.5 Flash (Stabil)",
    "gemini-2.5-pro-tts":"💎 2.5 Pro (Kaliteli)",
    "gemini-2.5-flash-lite-preview-tts":"💡 2.5 Lite (Ekonomik)",
    "gemini-3.1-flash-tts-preview":"⚡ 3.1 Flash (Güncel)",
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
    "🎉 Yarışma":"[excitedly] BÜYÜK YARIŞMA BAŞLIYOR!\n[laughs] Hazır mısınız?\n[shouting] BU HAFTA kazanan sizin aranızdan çıkacak!\n[seriously] Hemen arayın... [excitedly] KAZANMA ŞANSI SIZIN!",
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

# ═══════════════════════════ SESSION STATE ═══════════════════════
def _si(k, v):
    if k not in st.session_state: st.session_state[k] = v

_si("_archive",[]);_si("_favorites",[])
_si("_api_pool",[{"key":"","used":0,"label":f"API {i+1}"} for i in range(10)])
_si("_active_idx",0);_si("_secrets_loaded",False)
_si("_api_stats",{"calls":0,"chars":0,"secs":0.0})
_si("_giris",False)
_si("_t_tek","[excitedly] İmaj FM'e hoş geldiniz! BU GECE unutulmaz bir program var...\n[whispers] Sürprizler için kulaklarınız bizde olsun.\n[seriously] Şimdi haberlere geçiyoruz.")
_si("_t_cift","Sunucu: [excitedly] İmaj FM'e hoş geldiniz!\nMisafir: [laughs] Teşekkürler!\nSunucu: [seriously] Haberler... [normal] Müziğe dönüyoruz.")
_si("_t_bulk","İmaj FM sabah yayını başlıyor.\nHaber bülteni için bekleyiniz.\nMüzik programımıza hoş geldiniz.")
_si("_t_ab1","[excitedly] İmaj FM'e hoş geldiniz!")
_si("_t_ab2","[seriously] İmaj FM'e hoş geldiniz.")
_si("_playlist",[]);_si("_rj_voice","Kore");_si("_rj_model","gemini-2.5-flash-tts")
_si("_rj_lang","tr-TR");_si("_rj_style","");_si("_rj_start","06:00")
_si("_rj_plan",[]);_si("_rj_plan_ok",False)

# ═══════════════════════════ API HAVUZU ═════════════════════════
def load_secrets():
    if st.session_state._secrets_loaded: return
    st.session_state._secrets_loaded = True
    for i in range(10):
        try:
            v = st.secrets.get(f"GEMINI_API_KEY_{i+1}","")
            if v and not st.session_state._api_pool[i]["key"]:
                st.session_state._api_pool[i]["key"] = v
        except: pass

load_secrets()

def get_key():
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
    st.session_state._api_stats["calls"] += 1
    st.session_state._api_stats["chars"] += chars
    if st.session_state._api_pool[idx]["used"] >= MAX_PER_KEY:
        st.session_state._active_idx = (idx+1)%10

def pool_stats():
    p = st.session_state._api_pool
    loaded = sum(1 for s in p if s["key"].strip())
    remain = sum(max(0, MAX_PER_KEY-s["used"]) for s in p if s["key"].strip())
    return loaded, remain

# ═══════════════════════════ ARŞİV ══════════════════════════════
def arc_add(voice, model, lang, style, text, wav, mode="tek"):
    dur = len(wav)/(24000*2)
    uid = hashlib.md5((text+voice+str(time.time())).encode()).hexdigest()[:10]
    st.session_state._archive.insert(0,{
        "id":uid,"ts":datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "ts_s":datetime.datetime.now().strftime("%d.%m %H:%M"),
        "voice":voice,"model":model,"model_s":model.replace("gemini-","").replace("-preview","").replace("-tts",""),
        "lang":lang,"style":style[:40] if style else "",
        "text":text,"prev":text[:65].replace("\n"," ")+("…" if len(text)>65 else ""),
        "wav":wav,"dur":round(dur,1),"size":len(wav),"mode":mode,
    })
    if len(st.session_state._archive)>MAX_ARC:
        st.session_state._archive = st.session_state._archive[:MAX_ARC]
    st.session_state._api_stats["secs"] = st.session_state._api_stats.get("secs",0.0)+dur

# ═══════════════════════════ AUDIO CORE ══════════════════════════
def pcm2wav(pcm, rate=24000, ch=1, sw=2):
    buf=io.BytesIO()
    with wave.open(buf,"wb") as wf:
        wf.setnchannels(ch);wf.setsampwidth(sw);wf.setframerate(rate)
        wf.writeframes(pcm)
    return buf.getvalue()

def tts_single(api_key, model, text, voice, lang, style):
    full = f"{style}\n\n{text}" if style.strip() else text
    lc   = lang if lang!="otomatik" else None
    c    = genai.Client(api_key=api_key)
    r    = c.models.generate_content(
        model=model, contents=full,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                language_code=lc,
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)))))
    return r.candidates[0].content.parts[0].inline_data.data

def tts_multi(api_key, model, text, sp1, v1, sp2, v2, lang):
    lc = lang if lang!="otomatik" else None
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
                            voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=v1))),
                        types.SpeakerVoiceConfig(speaker=sp2,
                            voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=v2))),
                    ]))))
    return r.candidates[0].content.parts[0].inline_data.data

# ═══════════════════════════ PYDUB YARDIMCI ══════════════════════
def norm_seg(seg, db=-16.0):
    if not PYDUB_OK: return seg
    try: return seg.apply_gain(db-seg.dBFS)
    except: return seg

def apply_eq(seg, preset):
    if not PYDUB_OK or preset=="Ham": return seg
    try:
        if preset=="Broadcast": return pydub_fx.normalize(pydub_fx.compress_dynamic_range(seg,threshold=-18,ratio=3.0))
        elif preset=="Warm": return pydub_fx.normalize(seg)+1
        elif preset=="AM": return (seg.low_pass_filter(3000).high_pass_filter(400))+3
        elif preset=="Podcast": return pydub_fx.compress_dynamic_range(pydub_fx.normalize(seg),threshold=-20,ratio=2.5)
    except: pass
    return seg

EQ_OPTS = ["Ham","Broadcast","Warm","AM","Podcast"]

def mix_fon_voice(fon_seg, voice_seg, fon_vol=-8, duck_db=-16, fi=800, fo=1200):
    if not PYDUB_OK: return voice_seg
    try:
        fon=fon_seg+fon_vol; vl=len(voice_seg); fl=len(fon)
        if fl<vl+2000:
            loops=(vl+2000)//fl+1; fon=fon*loops
        fon=fon[:vl+2000].fade_in(fi)
        fp=fon[:vl]; fr=fon[vl:]; fm=min(500,vl//4)
        ducked=(fp[:fm].fade(to_gain=duck_db,start=0,duration=fm)+
                (fp[fm:vl-fm]+duck_db)+
                fp[vl-fm:].fade(from_gain=duck_db,start=0,duration=fm))
        return norm_seg(ducked.overlay(voice_seg)+fr.fade_out(fo))
    except: return voice_seg

def wav_bytes_to_seg(wb):
    if not PYDUB_OK: return None
    try: return AudioSegment.from_file(io.BytesIO(wb),format="wav")
    except: return None

def seg_to_wav(seg):
    if not PYDUB_OK or seg is None: return b""
    try:
        buf=io.BytesIO(); seg.export(buf,format="wav"); return buf.getvalue()
    except: return b""

def dur_bytes(wb):
    try: return len(wb)/(24000*2)
    except: return 0.0

def dur_file(path):
    if not PYDUB_OK or not os.path.exists(path): return 0.0
    try: return len(AudioSegment.from_file(path))/1000.0
    except: return 0.0

def fmt_dur(sec):
    m,s=divmod(int(sec),60); h,m=divmod(m,60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

def qs_bytes(wb):
    if not PYDUB_OK: return 70
    try:
        seg=AudioSegment.from_file(io.BytesIO(wb),format="wav"); sc=55
        if -22<=seg.dBFS<=-10: sc+=20
        elif -30<=seg.dBFS<=-22: sc+=10
        if -5<=seg.max_dBFS<=-0.5: sc+=20
        elif -8<=seg.max_dBFS<=-5: sc+=10
        if seg.frame_rate>=22050: sc+=5
        return min(100,max(0,sc))
    except: return 70

def draw_wf(wb, h=2.0):
    if not NP_OK: return
    try:
        buf=io.BytesIO(wb)
        with wave.open(buf,'r') as wf:
            frames=wf.readframes(wf.getnframes()); sr=wf.getframerate()
            sw_=wf.getsampwidth(); ch_=wf.getnchannels()
        dt=np.int16 if sw_==2 else np.int8
        s=np.frombuffer(frames,dtype=dt)
        if ch_==2: s=s[::2]
        step=max(1,len(s)//2000); ds=s[::step].astype(np.float32)
        mx=np.max(np.abs(ds)) or 1; ds/=mx
        t=np.linspace(0,len(s)/sr,len(ds))
        fig,ax=plt.subplots(figsize=(10,h),facecolor='#07090f')
        ax.set_facecolor('#07090f')
        ax.fill_between(t,ds,alpha=.65,color='#3b82f6')
        ax.fill_between(t,-np.abs(ds),alpha=.2,color='#a78bfa')
        ax.axhline(0,color='#1a2436',lw=.8)
        ax.set_xlim(0,t[-1]);ax.set_ylim(-1.1,1.1)
        for sp in ax.spines.values(): sp.set_visible(False)
        ax.tick_params(colors='#2e3f55',labelsize=7)
        plt.tight_layout(pad=.3)
        st.pyplot(fig,use_container_width=True); plt.close(fig)
    except: pass

def list_audio(d):
    exts=(".mp3",".wav",".ogg",".flac",".m4a",".aac")
    if not os.path.isdir(d): return []
    return sorted(f for f in os.listdir(d) if f.lower().endswith(exts))

def save_upload(uf, dest_dir, custom_name=""):
    if uf is None: return None, None
    try:
        os.makedirs(dest_dir,exist_ok=True)
        fname=custom_name or getattr(uf,'name','upload.wav')
        fname=re.sub(r'[^\w\-.]','_',fname)
        if '.' not in fname: fname+='.wav'
        dest=os.path.join(dest_dir,fname)
        raw=uf.getvalue() if hasattr(uf,'getvalue') else uf.read()
        if not raw or len(raw)<64: return None,None
        with open(dest,'wb') as f: f.write(raw)
        if PYDUB_OK:
            try:
                seg=AudioSegment.from_file(dest)
                wd=os.path.splitext(dest)[0]+'.wav'; seg.export(wd,format='wav')
                with open(wd,'rb') as f: return wd,f.read()
            except: pass
        with open(dest,'rb') as f: return dest,f.read()
    except Exception as e:
        st.error(f"Upload: {e}"); return None,None

def make_zip(items):
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as zf:
        for fn,data in items:
            safe=re.sub(r'[^\w\-.]','_',fn); zf.writestr(safe,data)
    return buf.getvalue()

# ═══════════════════════════ DELAY REJİ YARDIMCI ═════════════════
def song_uid():
    return hashlib.md5(str(time.time()+id({})).encode()).hexdigest()[:8]

def song_dur(s):
    return s.get("duration_min",3)*60+s.get("duration_sec",30)

def add_time(base, secs):
    try:
        p=base.split(":"); h,m=int(p[0]),int(p[1])
    except: h,m=6,0
    t=h*3600+m*60+secs; hh=(t//3600)%24; mm=(t%3600)//60; ss=t%60
    return f"{hh:02d}:{mm:02d}:{ss:02d}"

def auto_bas(s):
    return (f"[excitedly] Ve şimdi İmaj FM'de... {s.get('artist','?')}! "
            f"[normal] '{s.get('title','?')}' sizlerle. [whispers] Keyfini çıkarın...")

def auto_son(s):
    return (f"[normal] Dinlediğiniz {s.get('artist','?')} — '{s.get('title','?')}' idi. "
            f"[excitedly] İmaj FM'de devam ediyoruz!")

def build_plan(playlist, start):
    plan=[]; cur=0
    for song in playlist:
        sid=song["id"]; sd=song_dur(song)
        if song.get("anons_bas"):
            txt=song.get("anons_bas_text") or auto_bas(song)
            ad=max(5,len(txt)//15)
            plan.append({"time":add_time(start,cur),"off":cur,"type":"anons_bas","song_id":sid,
                         "label":f"🎙️ Baş → {song.get('title','?')}","sub":txt[:55]+"…" if len(txt)>55 else txt,
                         "dur":ad,"wav":song.get("anons_wav_bas"),"text":txt}); cur+=ad
        if song.get("fon_aktif"):
            plan.append({"time":add_time(start,cur),"off":cur,"type":"fon","song_id":sid,
                         "label":f"🎶 Fon [{song.get('fon_tip','?')}] → {song.get('title','?')}",
                         "sub":FON_TIPLERI.get(song.get("fon_tip","📻 Radyo Klasik"),"")[:55],
                         "dur":4,"wav":None,"text":""}); cur+=4
        plan.append({"time":add_time(start,cur),"off":cur,"type":"song","song_id":sid,
                     "label":f"🎵 {song.get('artist','?')} — {song.get('title','?')}",
                     "sub":fmt_dur(sd),"dur":sd,"wav":None,"text":""}); cur+=sd
        if song.get("anons_son"):
            txt=song.get("anons_son_text") or auto_son(song)
            ad=max(4,len(txt)//15)
            plan.append({"time":add_time(start,cur),"off":cur,"type":"anons_son","song_id":sid,
                         "label":f"🎙️ Son ← {song.get('title','?')}","sub":txt[:55]+"…" if len(txt)>55 else txt,
                         "dur":ad,"wav":song.get("anons_wav_son"),"text":txt}); cur+=ad
    return plan

# ═══════════════════════════ UI YARDIMCI ═════════════════════════
def txt_stats(text):
    cc=len(text);wc=len(text.split());sc=max(1,text.count(".")+text.count("!")+text.count("?"));est=max(1,cc/17)
    st.markdown(f"<div style='font-size:.67rem;color:#2e3f55;margin:3px 0 7px;'>📊 {cc} karakter · {wc} kelime · {sc} cümle · ~{est:.0f}s</div>",unsafe_allow_html=True)

def tag_btns(sk, prefix):
    cols=st.columns(len(ETAGS))
    for i,(em,lbl,tag) in enumerate(ETAGS):
        with cols[i]:
            if st.button(em,key=f"{prefix}_et{i}",help=f"{lbl}",use_container_width=True):
                st.session_state[sk]+=tag; st.rerun()

def style_w(prefix):
    ps=st.selectbox("Preset",list(STYLE_PRESETS.keys()),label_visibility="collapsed",key=f"{prefix}_ps")
    pv=STYLE_PRESETS[ps]
    ca,cb=st.columns(2)
    with ca:
        st.markdown("<div style='font-size:.63rem;color:#3b82f6;margin-bottom:3px;'>🇹🇷 TR Stil</div>",unsafe_allow_html=True)
        tr_=st.text_area("TR",value=pv,height=60,label_visibility="collapsed",key=f"{prefix}_str")
    with cb:
        st.markdown("<div style='font-size:.63rem;color:#f59e0b;margin-bottom:3px;'>🇬🇧 EN Style</div>",unsafe_allow_html=True)
        en_=st.text_area("EN",value="",height=60,label_visibility="collapsed",key=f"{prefix}_sen")
    return " / ".join(filter(None,[tr_.strip(),en_.strip()]))

def res_card(wav, raw, voice, ai, dk, dn):
    dur=len(raw)/(24000*2); qs=qs_bytes(wav)
    bc="#22c55e" if qs>=70 else "#f59e0b" if qs>=50 else "#ef4444"
    st.markdown(f"<div class='card g'>✅ {VOICES.get(voice,('?',''))[0]} {voice} · API {ai+1} · {dur:.1f}s · {qs}/100</div>",unsafe_allow_html=True)
    st.markdown(f"<div class='qbar'><div class='qbar-f' style='width:{qs}%;background:{bc};'></div></div>",unsafe_allow_html=True)
    st.audio(wav,format="audio/wav"); draw_wf(wav)
    st.download_button("💾 WAV İndir",wav,file_name=dn,mime="audio/wav",use_container_width=True,key=dk)

# ═══════════════════════════ GİRİŞ ══════════════════════════════
def login_page():
    _,col,_=st.columns([1,1.05,1])
    with col:
        st.markdown("""<div style='margin-top:60px;padding:32px 28px;background:#0b0f1a;border:1px solid #1a2d4a;border-radius:16px;box-shadow:0 20px 60px rgba(0,0,0,.8);'>
<h2 style='text-align:center;font-family:Syne,sans-serif;font-weight:800;font-size:1.45rem;margin:0 0 3px;background:linear-gradient(90deg,#fff 20%,#ff6060);-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>🎙️ İmaj FM</h2>
<p style='text-align:center;color:#2e3f55;font-size:.68rem;letter-spacing:.15em;margin:0 0 22px;'>TTS STÜDYO v6 · GÜVENLİ GİRİŞ</p></div>""",unsafe_allow_html=True)
        u=st.text_input("u","",placeholder="👤 kullanıcı adı",label_visibility="collapsed")
        p=st.text_input("p","",type="password",placeholder="🔑 şifre",label_visibility="collapsed")
        if st.button("Stüdyoya Bağlan →",type="primary",use_container_width=True):
            if u=="kenan" and p=="imajfm": st.session_state._giris=True; st.rerun()
            else: st.error("❌ Hatalı giriş.")

if not st.session_state._giris: login_page(); st.stop()

# ═══════════════════════════ SIDEBAR ════════════════════════════
with st.sidebar:
    st.markdown("""<div style='text-align:center;padding:4px 0 10px;'>
<span style='font-family:Syne,sans-serif;font-size:.92rem;font-weight:800;background:linear-gradient(90deg,#fff,#ff6060);-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>🎙️ İmaj FM</span>
<span style='font-size:.6rem;color:#2e3f55;letter-spacing:.1em;'> TTS v6</span></div>""",unsafe_allow_html=True)

    ak_sb,ai_sb=get_key(); tk_sb,tr_sb=pool_stats()
    used_a=st.session_state._api_pool[ai_sb]["used"] if ai_sb>=0 else 0
    rem_a=MAX_PER_KEY-used_a if ai_sb>=0 else 0
    pct_a=used_a/MAX_PER_KEY if ai_sb>=0 else 1
    bc_a="#22c55e" if pct_a<.6 else "#f59e0b" if pct_a<.9 else "#ef4444"

    with st.expander(f"🗝️ API Havuzu · {tk_sb}/10 · {tr_sb} kalan",expanded=True):
        if ak_sb:
            lbl_a=st.session_state._api_pool[ai_sb].get("label",f"API {ai_sb+1}")
            st.markdown(f"""<div style='background:#07090f;border-radius:7px;padding:7px 9px;margin-bottom:6px;font-size:.71rem;'>
<div style='display:flex;justify-content:space-between;margin-bottom:3px;'>
<span style='color:#6b7a8d;'>Aktif: <b style='color:#22c55e;'>{lbl_a}</b></span>
<span style='color:#6b7a8d;'>Kalan: <b style='color:{"#22c55e" if rem_a>3 else "#f59e0b"};'>{rem_a}/{MAX_PER_KEY}</b></span>
<span style='color:#6b7a8d;'>Top: <b style='color:#3b82f6;'>{tr_sb}</b></span></div>
<div class='qbar'><div class='qbar-f' style='width:{pct_a*100:.0f}%;background:{bc_a};'></div></div>
<div style='font-size:.6rem;color:#2e3f55;margin-top:2px;'>Otomatik rotasyon aktif</div></div>""",unsafe_allow_html=True)
        else:
            st.markdown("<div class='card r'>⛔ API yok!</div>",unsafe_allow_html=True)
        with st.expander("📋 Secrets Formatı",expanded=False):
            st.code('GEMINI_API_KEY_1 = "AIza..."',language="toml")
        for i in range(10):
            slot=st.session_state._api_pool[i]; used_i=slot["used"]; has=bool(slot["key"].strip())
            full=has and used_i>=MAX_PER_KEY; warn=has and used_i>=int(MAX_PER_KEY*.6) and not full
            is_ac=(i==st.session_state._active_idx) and has and not full
            lbl_i=slot.get("label",f"API {i+1}")
            icon="⬜" if not has else ("🔴" if full else ("🟡" if warn else "🟢"))
            badge="boş" if not has else ("DOLU" if full else f"{used_i}/{MAX_PER_KEY}")
            with st.expander(f"{icon} {lbl_i}{'◀' if is_ac else ''} · {badge}",expanded=False):
                nl=st.text_input(f"İ{i}",value=lbl_i,placeholder=f"API {i+1}",label_visibility="collapsed",key=f"lbl_{i}")
                if nl!=lbl_i: st.session_state._api_pool[i]["label"]=nl; st.rerun()
                nk=st.text_input(f"K{i}",value=slot["key"],type="password",placeholder="AIzaSy...",label_visibility="collapsed",key=f"key_{i}")
                if nk!=slot["key"]: st.session_state._api_pool[i]["key"]=nk; st.rerun()
                if has:
                    p2=min(used_i/MAX_PER_KEY,1); b2="#22c55e" if p2<.6 else "#f59e0b" if p2<.9 else "#ef4444"
                    st.markdown(f"<div class='qbar'><div class='qbar-f' style='width:{p2*100:.0f}%;background:{b2};'></div></div>",unsafe_allow_html=True)
                k1,k2,k3=st.columns(3)
                with k1:
                    if st.button("🔄",key=f"rst_{i}",use_container_width=True): st.session_state._api_pool[i]["used"]=0; st.rerun()
                with k2:
                    if st.button("▶",key=f"act_{i}",use_container_width=True): st.session_state._active_idx=i; st.rerun()
                with k3:
                    if st.button("🗑️",key=f"del_{i}",use_container_width=True): st.session_state._api_pool[i]={"key":"","used":0,"label":f"API {i+1}"}; st.rerun()

    pl_cnt=len(st.session_state._playlist)
    with st.expander(f"📻 Reji Playlist · {pl_cnt} şarkı",expanded=False):
        if not st.session_state._playlist: st.caption("Boş. Delay Reji sekmesinden ekleyin.")
        else:
            for i,s in enumerate(st.session_state._playlist[:5]):
                b=""
                if s.get("anons_bas"): b+="🎙️B "
                if s.get("anons_son"): b+="🎙️S "
                if s.get("fon_aktif"): b+="🎶 "
                st.markdown(f"<div style='font-size:.68rem;color:#3d4f68;padding:2px 0;border-bottom:1px solid #0d1420;'>{i+1}. <b style='color:#60a5fa;'>{s.get('title','?')[:16]}</b> {b}</div>",unsafe_allow_html=True)

    pl_songs=list_audio(DIRS["playlist"]); fon_files=list_audio(DIRS["fon"])
    with st.expander(f"📂 Kütüphane · {len(pl_songs)} şarkı · {len(fon_files)} fon",expanded=False):
        arc_cnt=len(st.session_state._archive)
        st.caption(f"Arşiv: {arc_cnt} ses · Çıktı: {len(list_audio(DIRS['output']))}")

    st.markdown("<hr>",unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;color:#101828;font-size:.61rem;'>İmaj FM v6 · 2026</div>",unsafe_allow_html=True)

# ═══════════════════════════ HEADER ═════════════════════════════
stat_g=st.session_state._api_stats; tk_m,tr_m=pool_stats()
_,ai_m=get_key(); rem_m=MAX_PER_KEY-st.session_state._api_pool[ai_m]["used"] if ai_m>=0 else 0
arc_m=len(st.session_state._archive); pl_m=len(st.session_state._playlist)

st.markdown("""<div class='hdr'><h1>🎙️ İmaj FM · Seslendirme Stüdyosu</h1>
<p><span class='ldot'></span>Gemini TTS v6 · Delay Reji · Yayın Otomasyonu · Fon+Anons · Playlist · ZIP · Kütüphane · Arşiv</p></div>""",unsafe_allow_html=True)

c8=st.columns(8)
defs=[("30","Ses"),( f"{tk_m}/10","API","g"),(f"{tr_m}","Kalan","a"),
      (f"{arc_m}","Arşiv","b"),(f"{stat_g['calls']}","İstek"),
      (f"{stat_g.get('secs',0):.0f}s","Ses","p"),(f"{pl_m}","Playlist","t"),
      (f"{len(pl_songs)}","Şarkı")]
for col,(val,lbl,*cls) in zip(c8,defs):
    c=cls[0] if cls else ""
    with col: st.markdown(f'<div class="mbox {c}"><div class="v">{val}</div><div class="l">{lbl}</div></div>',unsafe_allow_html=True)
st.markdown("<br>",unsafe_allow_html=True)

ak_chk,_=get_key()
if ak_chk is None: st.error("⛔ API anahtarı yok! Sol panelden ekleyin."); st.stop()
elif rem_m<=2: st.warning(f"⚠️ API {ai_m+1} limitine yakın ({rem_m} kaldı).")

# ═══════════════════════════ SEKMELER ════════════════════════════
tabs=st.tabs(["🎤 Tek","🎭 Çift","📦 Toplu","🔬 A/B Test",
              "⭐ Favoriler","📻 Delay Reji","🎛️ Fon+Anons",
              "🚀 Yayın Otomasyon","📁 Kütüphane","📂 Arşiv"])
t1,t2,t3,t4,t5,t6,t7,t8,t9,t10=tabs

# ════════════════ T1 — TEK KONUŞMACI ════════════════════════════
with t1:
    cL,cR=st.columns([1.05,1],gap="large")
    with cL:
        st.markdown("<span class='sl'>▶ Şablon</span>",unsafe_allow_html=True)
        tmpl1=st.selectbox("Ş1",["— Yok —"]+list(TEMPLATES.keys()),label_visibility="collapsed",key="tmpl1")
        if tmpl1!="— Yok —" and st.button("📥 Yükle",key="ltmpl1"):
            st.session_state._t_tek=TEMPLATES[tmpl1]; st.rerun()
        st.markdown("<span class='sl'>▶ Model</span>",unsafe_allow_html=True)
        m1l=st.selectbox("M1",list(MODELS.values()),label_visibility="collapsed",key="m1")
        mdl1=[k for k,v in MODELS.items() if v==m1l][0]
        st.markdown("<span class='sl'>▶ Dil</span>",unsafe_allow_html=True)
        l1l=st.selectbox("L1",list(LANGUAGES.values()),label_visibility="collapsed",index=1,key="l1")
        lng1=[k for k,v in LANGUAGES.items() if v==l1l][0]
        st.markdown("<span class='sl'>▶ Ses</span>",unsafe_allow_html=True)
        cn1=st.radio("CN1",["Tümü","♀ Kadın","♂ Erkek"],horizontal=True,label_visibility="collapsed",key="cn1")
        f1={k:v for k,v in VOICES.items() if cn1=="Tümü" or (cn1=="♀ Kadın" and v[0]=="♀") or (cn1=="♂ Erkek" and v[0]=="♂")}
        vc1=st.selectbox("V1",list(f1.keys()),format_func=lambda x:f"{VOICES[x][0]} {x} — {VOICES[x][1]}",label_visibility="collapsed",key="v1")
        eq1=st.selectbox("EQ",EQ_OPTS,label_visibility="collapsed",key="eq1")
        st.markdown("<span class='sl'>▶ Stil</span>",unsafe_allow_html=True)
        sty1=style_w("t1")
        ak1,ai1=get_key(); r1=MAX_PER_KEY-st.session_state._api_pool[ai1]["used"] if ai1>=0 else 0
        st.markdown(f"<div class='card b'><b>{VOICES[vc1][0]} {vc1}</b> — {VOICES[vc1][1]}<br><span style='color:#3a7bd5;'>{m1l[:18]}</span> · <span style='color:#22c55e;'>API {ai1+1}</span> · {r1} kalan</div>",unsafe_allow_html=True)
        st.markdown("<span class='sl'>▶ Favorilere Ekle</span>",unsafe_allow_html=True)
        fa,fb=st.columns([2,1])
        with fa: fname1=st.text_input("FN","",placeholder="Favori ismi…",label_visibility="collapsed",key="fname1")
        with fb:
            if st.button("⭐ Ekle",key="fadd1",use_container_width=True):
                if fname1.strip() and st.session_state._t_tek.strip():
                    st.session_state._favorites.append({"id":hashlib.md5((fname1+str(time.time())).encode()).hexdigest()[:8],"name":fname1.strip(),"text":st.session_state._t_tek,"voice":vc1,"model":mdl1,"lang":lng1})
                    st.success("⭐ Eklendi!"); time.sleep(0.4); st.rerun()
    with cR:
        st.markdown("<span class='sl'>▶ Anons Metni</span>",unsafe_allow_html=True)
        tag_btns("_t_tek","t1")
        txt1=st.text_area("TT1",value=st.session_state._t_tek,height=220,label_visibility="collapsed",key="ta1",placeholder="Metni buraya yazın…")
        st.session_state._t_tek=txt1; txt_stats(txt1)
        if st.button(f"🔴 {vc1} ile Seslendir",type="primary",use_container_width=True,key="btn1"):
            if not txt1.strip(): st.warning("⚠️ Metin boş.")
            else:
                ak1,ai1=get_key()
                if ak1 is None: st.error("❌ API kalmadı!")
                else:
                    with st.spinner(f"🎙️ {vc1}… [API {ai1+1}]"):
                        try:
                            raw=tts_single(ak1,mdl1,txt1,vc1,lng1,sty1); wav=pcm2wav(raw)
                            if PYDUB_OK and eq1!="Ham":
                                seg=apply_eq(AudioSegment.from_file(io.BytesIO(wav),format="wav"),eq1)
                                wav=seg_to_wav(norm_seg(seg))
                            consume(ai1,len(txt1)); arc_add(vc1,mdl1,lng1,sty1,txt1,wav,"tek")
                            res_card(wav,raw,vc1,ai1,"dl1",f"imajfm_{vc1.lower()}_{lng1}.wav")
                        except Exception as e: st.error(f"❌ {e}")

# ════════════════ T2 — ÇİFT KONUŞMACI ══════════════════════════
with t2:
    st.markdown("<div class='card b'>🎭 İki konuşmacı — Multi-speaker Gemini TTS · Tek WAV çıktı</div>",unsafe_allow_html=True)
    cL2,cR2=st.columns([1.05,1],gap="large")
    with cL2:
        tmpl2=st.selectbox("Ş2",["— Yok —"]+list(TEMPLATES.keys()),label_visibility="collapsed",key="tmpl2")
        if tmpl2!="— Yok —" and st.button("📥 Yükle",key="ltmpl2"): st.session_state._t_cift=TEMPLATES[tmpl2]; st.rerun()
        m2l=st.selectbox("M2",list(MODELS.values()),label_visibility="collapsed",key="m2")
        mdl2=[k for k,v in MODELS.items() if v==m2l][0]
        l2l=st.selectbox("L2",list(LANGUAGES.values()),label_visibility="collapsed",index=1,key="l2")
        lng2=[k for k,v in LANGUAGES.items() if v==l2l][0]
        st.markdown("<span class='sl'>▶ Konuşmacı 1</span>",unsafe_allow_html=True)
        ca,cb=st.columns([1,2])
        with ca: sp1n=st.text_input("S1N","Sunucu",label_visibility="collapsed",key="sp1n")
        with cb: sp1v=st.selectbox("S1V",list(VOICES.keys()),format_func=lambda x:f"{VOICES[x][0]} {x}",label_visibility="collapsed",index=list(VOICES.keys()).index("Kore"),key="sp1v")
        st.markdown("<span class='sl'>▶ Konuşmacı 2</span>",unsafe_allow_html=True)
        cc,cd=st.columns([1,2])
        with cc: sp2n=st.text_input("S2N","Misafir",label_visibility="collapsed",key="sp2n")
        with cd: sp2v=st.selectbox("S2V",list(VOICES.keys()),format_func=lambda x:f"{VOICES[x][0]} {x}",label_visibility="collapsed",index=list(VOICES.keys()).index("Fenrir"),key="sp2v")
        eq2=st.selectbox("EQ2",EQ_OPTS,label_visibility="collapsed",key="eq2")
        ak2,ai2=get_key(); r2=MAX_PER_KEY-st.session_state._api_pool[ai2]["used"] if ai2>=0 else 0
        st.markdown(f"<div class='card b'><code style='color:#60a5fa;'>{sp1n}</code>→<b>{sp1v}</b> · <code style='color:#f87171;'>{sp2n}</code>→<b>{sp2v}</b><br>API {ai2+1} · {r2} kalan</div>",unsafe_allow_html=True)
    with cR2:
        st.markdown("<span class='sl'>▶ Diyalog</span>",unsafe_allow_html=True)
        tag_btns("_t_cift","t2")
        txt2=st.text_area("TT2",value=st.session_state._t_cift,height=220,label_visibility="collapsed",key="ta2")
        st.session_state._t_cift=txt2; txt_stats(txt2)
        if st.button(f"🔴 {sp1n}&{sp2n} Diyalog",type="primary",use_container_width=True,key="btn2"):
            if not txt2.strip(): st.warning("⚠️ Metin boş.")
            else:
                ak2,ai2=get_key()
                if ak2 is None: st.error("❌ API kalmadı!")
                else:
                    with st.spinner(f"🎭 Diyalog… [API {ai2+1}]"):
                        try:
                            raw2=tts_multi(ak2,mdl2,txt2,sp1n,sp1v,sp2n,sp2v,lng2); wav2=pcm2wav(raw2)
                            if PYDUB_OK and eq2!="Ham":
                                s2=apply_eq(AudioSegment.from_file(io.BytesIO(wav2),format="wav"),eq2); wav2=seg_to_wav(norm_seg(s2))
                            consume(ai2,len(txt2)); arc_add(f"{sp1v}+{sp2v}",mdl2,lng2,"",txt2,wav2,"cift")
                            res_card(wav2,raw2,sp1v,ai2,"dl2",f"imajfm_diyalog_{sp1v.lower()}.wav")
                        except Exception as e: st.error(f"❌ {e}")

# ════════════════ T3 — TOPLU TTS ════════════════════════════════
with t3:
    st.markdown("<div class='card b'>📦 Her satır ayrı WAV — TXT/CSV yükle veya manuel yaz — ZIP indir</div>",unsafe_allow_html=True)
    btab1,btab2=st.tabs(["✏️ Manuel Liste","📄 TXT/CSV Yükle"])
    with btab1:
        cL3,cR3=st.columns([1,1.2],gap="large")
        with cL3:
            m3l=st.selectbox("M3",list(MODELS.values()),label_visibility="collapsed",key="m3")
            mdl3=[k for k,v in MODELS.items() if v==m3l][0]
            l3l=st.selectbox("L3",list(LANGUAGES.values()),label_visibility="collapsed",index=1,key="l3")
            lng3=[k for k,v in LANGUAGES.items() if v==l3l][0]
            cn3=st.radio("CN3",["Tümü","♀ Kadın","♂ Erkek"],horizontal=True,label_visibility="collapsed",key="cn3")
            f3={k:v for k,v in VOICES.items() if cn3=="Tümü" or (cn3=="♀ Kadın" and v[0]=="♀") or (cn3=="♂ Erkek" and v[0]=="♂")}
            vc3=st.selectbox("V3",list(f3.keys()),format_func=lambda x:f"{VOICES[x][0]} {x}",label_visibility="collapsed",key="v3")
            eq3=st.selectbox("EQ3",EQ_OPTS,label_visibility="collapsed",key="eq3")
            sty3=st.text_area("STY3","",height=50,label_visibility="collapsed",placeholder="Stil (opsiyonel)",key="sty3")
            _,tr3=pool_stats()
            lines3p=[l.strip() for l in st.session_state._t_bulk.splitlines() if l.strip()]
            st.markdown(f"<div class='card {'a' if len(lines3p)>tr3 else 'b'}'>{len(lines3p)} satır · {tr3} kalan</div>",unsafe_allow_html=True)
        with cR3:
            txt3=st.text_area("TT3",value=st.session_state._t_bulk,height=220,label_visibility="collapsed",key="ta3",placeholder="Her satır bir ses…")
            st.session_state._t_bulk=txt3; lines3=[l.strip() for l in txt3.splitlines() if l.strip()]
            st.markdown(f"<div style='font-size:.67rem;color:#2e3f55;'>{len(lines3)} satır</div>",unsafe_allow_html=True)
            if st.button(f"🔴 {len(lines3)} Satırı Üret",type="primary",use_container_width=True,key="btn3"):
                if not lines3: st.warning("⚠️ Satır yok.")
                else:
                    res3=[]; err3=[]; prog3=st.progress(0); sts3=st.empty()
                    for idx3,line3 in enumerate(lines3):
                        ak3,ai3=get_key()
                        if ak3 is None: err3.append(f"Satır {idx3+1}: API kalmadı"); break
                        sts3.markdown(f"<div style='font-size:.73rem;color:#6b7a8d;'>🎙️ {idx3+1}/{len(lines3)}: {line3[:40]} [API {ai3+1}]</div>",unsafe_allow_html=True)
                        try:
                            raw3=tts_single(ak3,mdl3,line3,vc3,lng3,sty3); wav3=pcm2wav(raw3)
                            if PYDUB_OK and eq3!="Ham":
                                s3=apply_eq(AudioSegment.from_file(io.BytesIO(wav3),format="wav"),eq3); wav3=seg_to_wav(norm_seg(s3))
                            consume(ai3,len(line3)); arc_add(vc3,mdl3,lng3,sty3,line3,wav3,"bulk")
                            fn3=f"{idx3+1:02d}_{vc3.lower()}_{re.sub(r'[^\\w]','_',line3[:12])}.wav"; res3.append((fn3,wav3,line3))
                        except Exception as e: err3.append(f"Satır {idx3+1}: {e}")
                        prog3.progress((idx3+1)/len(lines3))
                    prog3.empty(); sts3.empty()
                    if res3:
                        st.markdown(f"<div class='card g'>✅ {len(res3)}/{len(lines3)} tamamlandı</div>",unsafe_allow_html=True)
                        zd=make_zip([(fn,wb) for fn,wb,_ in res3])
                        st.download_button("📦 ZIP İndir",zd,file_name=f"bulk_{vc3.lower()}.zip",mime="application/zip",use_container_width=True,key="dl3zip")
                        for fn,wb,ln in res3:
                            with st.expander(f"🔊 {fn[:45]}",expanded=False):
                                st.audio(wb,format="audio/wav")
                                st.download_button("💾",wb,file_name=fn,mime="audio/wav",key=f"dl3_{fn}")
                    for e in err3: st.markdown(f"<div class='card r'>❌ {e}</div>",unsafe_allow_html=True)
    with btab2:
        up_f=st.file_uploader("TXT veya CSV Yükle",type=["txt","csv"],key="bulk_up")
        if up_f:
            content=up_f.read().decode("utf-8","ignore")
            lines_u=[l.strip() for l in content.splitlines() if l.strip()]
            if up_f.name.endswith(".csv"): lines_u=[l.split(",")[0].strip().strip('"') for l in lines_u]
            st.success(f"✅ {len(lines_u)} satır"); st.session_state["bulk_up_lines"]=lines_u
            for i,l in enumerate(lines_u[:5]): st.markdown(f"<div style='font-size:.73rem;color:#6b7a8d;'>{i+1}. {l[:70]}</div>",unsafe_allow_html=True)
        if st.session_state.get("bulk_up_lines"):
            mu_ml=st.selectbox("Model",list(MODELS.values()),label_visibility="collapsed",key="mu_m")
            mu_mdl=[k for k,v in MODELS.items() if v==mu_ml][0]
            mu_ll=st.selectbox("Dil",list(LANGUAGES.values()),label_visibility="collapsed",index=1,key="mu_l")
            mu_lng=[k for k,v in LANGUAGES.items() if v==mu_ll][0]
            mu_vc=st.selectbox("Ses",list(VOICES.keys()),format_func=lambda x:f"{VOICES[x][0]} {x}",label_visibility="collapsed",key="mu_v")
            if st.button("🚀 Dosyadan Toplu Üret",type="primary",use_container_width=True,key="mu_btn"):
                lu=st.session_state["bulk_up_lines"]; res_u=[]; prog_u=st.progress(0)
                for i,ln in enumerate(lu):
                    ak_u,ai_u=get_key()
                    if ak_u is None: break
                    try:
                        rw=tts_single(ak_u,mu_mdl,ln,mu_vc,mu_lng,""); wv=pcm2wav(rw)
                        consume(ai_u,len(ln)); arc_add(mu_vc,mu_mdl,mu_lng,"",ln,wv,"bulk-file")
                        res_u.append((f"{i+1:03d}_{mu_vc.lower()}.wav",wv))
                    except Exception as e: st.warning(f"Satır {i+1}: {e}")
                    prog_u.progress((i+1)/len(lu))
                if res_u:
                    z=make_zip(res_u)
                    st.download_button("📦 ZIP İndir",z,"bulk_dosya.zip","application/zip",key="mu_zip")
                    st.success(f"✅ {len(res_u)} ses üretildi!")

# ════════════════ T4 — A/B TEST ══════════════════════════════════
with t4:
    st.markdown("<div class='card p'>🔬 Aynı metni iki farklı ses/model/stil ile karşılaştır</div>",unsafe_allow_html=True)
    ab_c1,ab_c2=st.columns(2,gap="large")
    def ab_col(col,label,prefix,txt_key,txt_val,model_key,lang_key,voice_key,eq_key,style_key,dl_key,btn_key,arc_mode):
        with col:
            st.markdown(f"<div style='font-family:Syne,sans-serif;font-size:.7rem;font-weight:800;letter-spacing:.14em;color:{'#a78bfa' if 'A' in label else '#fb923c'};text-transform:uppercase;margin-bottom:7px;'>{label}</div>",unsafe_allow_html=True)
            ml=st.selectbox("M",list(MODELS.values()),label_visibility="collapsed",key=model_key)
            mdl=[k for k,v in MODELS.items() if v==ml][0]
            ll=st.selectbox("L",list(LANGUAGES.values()),label_visibility="collapsed",index=1,key=lang_key)
            lng=[k for k,v in LANGUAGES.items() if v==ll][0]
            cn=st.radio("CN",["Tümü","♀","♂"],horizontal=True,label_visibility="collapsed",key=f"{prefix}_cn")
            fv={k:v for k,v in VOICES.items() if cn=="Tümü" or (cn=="♀" and v[0]=="♀") or (cn=="♂" and v[0]=="♂")}
            vc=st.selectbox("V",list(fv.keys()),format_func=lambda x:f"{VOICES[x][0]} {x}",label_visibility="collapsed",key=voice_key)
            eq=st.selectbox("EQ",EQ_OPTS,label_visibility="collapsed",key=eq_key)
            ps=st.selectbox("PS",list(STYLE_PRESETS.keys()),label_visibility="collapsed",key=f"{prefix}_ps")
            sty=st.text_area("STY",value=STYLE_PRESETS[ps],height=50,label_visibility="collapsed",key=style_key)
            tag_btns(txt_key,prefix)
            txt=st.text_area("TXT",value=txt_val,height=120,label_visibility="collapsed",key=f"{prefix}_ta")
            st.session_state[txt_key]=txt
            if st.button(f"🔴 {label} Üret",use_container_width=True,key=btn_key):
                if not txt.strip(): st.warning("Metin boş")
                else:
                    ak,ai=get_key()
                    if ak is None: st.error("❌ API yok")
                    else:
                        with st.spinner(f"{vc}…"):
                            try:
                                rw=tts_single(ak,mdl,txt,vc,lng,sty); wv=pcm2wav(rw)
                                if PYDUB_OK and eq!="Ham":
                                    s=apply_eq(AudioSegment.from_file(io.BytesIO(wv),format="wav"),eq); wv=seg_to_wav(norm_seg(s))
                                consume(ai,len(txt)); arc_add(vc,mdl,lng,sty,txt,wv,arc_mode)
                                qs=qs_bytes(wv)
                                st.markdown(f"<div class='card {'p' if 'A' in label else 'a'}'>{vc} · {len(rw)/(24000*2):.1f}s · {qs}/100</div>",unsafe_allow_html=True)
                                st.audio(wv,format="audio/wav"); draw_wf(wv)
                                st.download_button(f"💾 {label}",wv,file_name=f"{prefix}_{vc.lower()}.wav",mime="audio/wav",key=dl_key)
                            except Exception as e: st.error(f"❌ {e}")
    ab_col(ab_c1,"🅐 VERSİYON A","ab_a","_t_ab1",st.session_state._t_ab1,"masel","lasel","vasel","eqasel","styasel","dlab","btnab1","ab-A")
    ab_col(ab_c2,"🅑 VERSİYON B","ab_b","_t_ab2",st.session_state._t_ab2,"mbsel","lbsel","vbsel","eqbsel","stybsel","dlbb","btnab2","ab-B")

# ════════════════ T5 — FAVORİLER ════════════════════════════════
with t5:
    favs=st.session_state._favorites
    if not favs:
        st.markdown("<div style='text-align:center;padding:45px;color:#2e3f55;'><div style='font-size:2rem;'>⭐</div><div style='font-family:Syne,sans-serif;margin-top:7px;'>Favori metin yok</div><div style='font-size:.78rem;margin-top:4px;'>Tek sekmesinden ⭐ Ekle butonunu kullanın.</div></div>",unsafe_allow_html=True)
    else:
        hf1,hf2=st.columns([3,1])
        with hf1: st.markdown(f"<span class='sl'>▶ {len(favs)} Favori</span>",unsafe_allow_html=True)
        with hf2:
            if st.button("🗑️ Tümünü Sil",use_container_width=True,key="fav_clr"): st.session_state._favorites=[]; st.rerun()
        for fi,fv in enumerate(favs):
            fc1,fc2,fc3,fc4=st.columns([2,.8,.8,.5])
            with fc1:
                st.markdown(f"<div class='fav-card'><div class='fav-name'>⭐ {fv['name']}</div><div class='fav-prev'>{fv.get('voice','—')} · {fv.get('lang','—')}</div><div class='fav-prev'>{fv['text'][:55]}</div></div>",unsafe_allow_html=True)
            with fc2:
                if st.button("📋",key=f"fcp_{fi}",use_container_width=True,help="Tek sekmesine yükle"): st.session_state._t_tek=fv["text"]; st.rerun()
            with fc3:
                if st.button("🔴",key=f"fsp_{fi}",use_container_width=True,help="Seslendir"):
                    akf,aif=get_key()
                    if akf is None: st.error("❌ API yok")
                    else:
                        with st.spinner("🎙️ Üretiyor…"):
                            try:
                                rwf=tts_single(akf,fv.get("model","gemini-2.5-flash-tts"),fv["text"],fv.get("voice","Kore"),fv.get("lang","tr-TR"),"")
                                wvf=pcm2wav(rwf); consume(aif,len(fv["text"]))
                                arc_add(fv.get("voice","Kore"),fv.get("model",""),fv.get("lang",""),"",fv["text"],wvf,"fav")
                                st.session_state[f"_fw_{fi}"]=wvf; st.rerun()
                            except Exception as e: st.error(f"❌ {e}")
            with fc4:
                if st.button("🗑️",key=f"fdel_{fi}",use_container_width=True): st.session_state._favorites.pop(fi); st.rerun()
            if f"_fw_{fi}" in st.session_state:
                fw=st.session_state[f"_fw_{fi}"]; st.audio(fw,format="audio/wav")
                st.download_button("💾",fw,file_name=f"fav_{fv['name'][:12]}.wav",mime="audio/wav",key=f"fdl_{fi}")

# ════════════════ T6 — DELAY REJİ ═══════════════════════════════
with t6:
    st.markdown("<div class='rjhdr'><h2>📻 Delay Reji — Yayın Otomasyonu</h2><p>Playlist · Şarkı başı/sonu anons · Fon müzik geçişleri · Yayın planı · ZIP</p></div>",unsafe_allow_html=True)
    rj1,rj2,rj3,rj4=st.tabs(["🎵 Playlist","⚙️ Ayarlar","📋 Yayın Planı","🎬 Üretim & ZIP"])

    # RJ1 - PLAYLİST
    with rj1:
        pl=st.session_state._playlist
        st.markdown("<span class='sl'>▶ Yeni Şarkı Ekle</span>",unsafe_allow_html=True)
        nc1,nc2,nc3,nc4=st.columns([2,1.5,.5,.5])
        with nc1: nt=st.text_input("Şarkı","",placeholder="Şarkı adı…",label_visibility="collapsed",key="nt")
        with nc2: na=st.text_input("Sanatçı","",placeholder="Sanatçı…",label_visibility="collapsed",key="na")
        with nc3: ndm=st.number_input("Dk",0,10,3,label_visibility="collapsed",key="ndm")
        with nc4: nds=st.number_input("Sn",0,59,30,label_visibility="collapsed",key="nds")
        ba,bb=st.columns(2)
        with ba:
            if st.button("➕ Ekle",use_container_width=True,key="add_song"):
                if nt.strip():
                    st.session_state._playlist.append({"id":song_uid(),"title":nt.strip(),"artist":na.strip() or "Bilinmeyen","duration_min":int(ndm),"duration_sec":int(nds),"anons_bas":False,"anons_son":False,"anons_bas_text":"","anons_son_text":"","fon_aktif":False,"fon_tip":"📻 Radyo Klasik","anons_wav_bas":None,"anons_wav_son":None})
                    st.session_state._rj_plan_ok=False; st.rerun()
                else: st.warning("Şarkı adı boş olamaz.")
        with bb:
            if st.button("🎲 Demo Playlist",use_container_width=True,key="demo_pl"):
                demos=[("Gece Yarısı","Sezen Aksu",3,45),("Yüksek Yüksek Tepelere","Barış Manço",4,12),("Oy Benim Sarı Turnam","Neşet Ertaş",3,55),("Hayatımın Anlamı","MFÖ",3,28),("Leylim Ley","Zülfü Livaneli",4,5),("Mavi Bisiklet","Sıla",3,48),("Seni Bana Verecekler","Tarkan",4,20)]
                st.session_state._playlist=[{"id":song_uid(),"title":t,"artist":ar,"duration_min":dm,"duration_sec":ds,"anons_bas":False,"anons_son":False,"anons_bas_text":"","anons_son_text":"","fon_aktif":False,"fon_tip":"📻 Radyo Klasik","anons_wav_bas":None,"anons_wav_son":None} for t,ar,dm,ds in demos]
                st.session_state._rj_plan_ok=False; st.rerun()

        st.markdown("<span class='sl'>▶ Şarkı Dosyası Yükle (Yerel MP3/WAV)</span>",unsafe_allow_html=True)
        pl_up=st.file_uploader("Şarkı dosyaları",type=["mp3","wav","ogg","flac","m4a"],accept_multiple_files=True,key="pl_up")
        if pl_up:
            added=0
            for uf in pl_up:
                dp,_=save_upload(uf,DIRS["playlist"],uf.name)
                if dp:
                    d=dur_file(dp); mn,sc=divmod(int(d),60); added+=1
                    nm=os.path.splitext(uf.name)[0]
                    st.session_state._playlist.append({"id":song_uid(),"title":nm,"artist":"Yüklenen","duration_min":mn,"duration_sec":sc,"anons_bas":False,"anons_son":False,"anons_bas_text":"","anons_son_text":"","fon_aktif":False,"fon_tip":"📻 Radyo Klasik","anons_wav_bas":None,"anons_wav_son":None,"local_file":dp})
            if added: st.success(f"✅ {added} şarkı eklendi!"); st.session_state._rj_plan_ok=False; st.rerun()

        st.markdown("<hr>",unsafe_allow_html=True)
        if not pl:
            st.markdown("<div style='text-align:center;padding:28px;color:#2e3f55;'>🎵 Playlist boş</div>",unsafe_allow_html=True)
        else:
            ts2=sum(song_dur(s) for s in pl); bc=sum(1 for s in pl if s.get("anons_bas")); sc2=sum(1 for s in pl if s.get("anons_son")); fc=sum(1 for s in pl if s.get("fon_aktif"))
            pm1,pm2,pm3,pm4,pm5=st.columns(5)
            with pm1: st.markdown(f'<div class="mbox t"><div class="v">{len(pl)}</div><div class="l">Şarkı</div></div>',unsafe_allow_html=True)
            with pm2: st.markdown(f'<div class="mbox b"><div class="v">{fmt_dur(ts2)}</div><div class="l">Süre</div></div>',unsafe_allow_html=True)
            with pm3: st.markdown(f'<div class="mbox a"><div class="v">{bc}</div><div class="l">Baş Anons</div></div>',unsafe_allow_html=True)
            with pm4: st.markdown(f'<div class="mbox a"><div class="v">{sc2}</div><div class="l">Son Anons</div></div>',unsafe_allow_html=True)
            with pm5: st.markdown(f'<div class="mbox g"><div class="v">{fc}</div><div class="l">Fon</div></div>',unsafe_allow_html=True)
            st.markdown("<br><span class='sl'>▶ Şarkı Listesi</span>",unsafe_allow_html=True)
            for si,song in enumerate(pl):
                sid=song["id"]; ds=song_dur(song)
                hb=song.get("anons_bas",False); hs=song.get("anons_son",False); hf=song.get("fon_aktif",False)
                with st.expander(f"🎵 {si+1:02d}. {song.get('artist','?')} — {song.get('title','?')}  [{fmt_dur(ds)}]",expanded=False):
                    e1,e2,e3,e4=st.columns([2,1.5,.5,.5])
                    with e1:
                        nt2=st.text_input("Başlık",value=song["title"],label_visibility="collapsed",key=f"et_{sid}")
                        if nt2!=song["title"]: st.session_state._playlist[si]["title"]=nt2; st.session_state._rj_plan_ok=False; st.rerun()
                    with e2:
                        na2=st.text_input("Sanatçı",value=song["artist"],label_visibility="collapsed",key=f"ea_{sid}")
                        if na2!=song["artist"]: st.session_state._playlist[si]["artist"]=na2; st.session_state._rj_plan_ok=False; st.rerun()
                    with e3:
                        ndm2=st.number_input("Dk",0,10,song["duration_min"],label_visibility="collapsed",key=f"edm_{sid}")
                        if ndm2!=song["duration_min"]: st.session_state._playlist[si]["duration_min"]=int(ndm2); st.session_state._rj_plan_ok=False; st.rerun()
                    with e4:
                        nds2=st.number_input("Sn",0,59,song["duration_sec"],label_visibility="collapsed",key=f"eds_{sid}")
                        if nds2!=song["duration_sec"]: st.session_state._playlist[si]["duration_sec"]=int(nds2); st.session_state._rj_plan_ok=False; st.rerun()
                    st.markdown("<hr>",unsafe_allow_html=True)
                    tg1,tg2,tg3=st.columns(3)
                    with tg1:
                        nb=st.checkbox("🎙️ Şarkı Başı Anonsu",value=hb,key=f"cb_{sid}")
                        if nb!=hb:
                            st.session_state._playlist[si]["anons_bas"]=nb
                            if nb and not song.get("anons_bas_text"): st.session_state._playlist[si]["anons_bas_text"]=auto_bas(song)
                            st.session_state._rj_plan_ok=False; st.rerun()
                    with tg2:
                        ns2=st.checkbox("🎙️ Şarkı Sonu Anonsu",value=hs,key=f"cs_{sid}")
                        if ns2!=hs:
                            st.session_state._playlist[si]["anons_son"]=ns2
                            if ns2 and not song.get("anons_son_text"): st.session_state._playlist[si]["anons_son_text"]=auto_son(song)
                            st.session_state._rj_plan_ok=False; st.rerun()
                    with tg3:
                        nf2=st.checkbox("🎶 Fon Müzik Geçişi",value=hf,key=f"cf_{sid}")
                        if nf2!=hf: st.session_state._playlist[si]["fon_aktif"]=nf2; st.session_state._rj_plan_ok=False; st.rerun()
                    if song.get("fon_aktif"):
                        fo=list(FON_TIPLERI.keys()); cf=song.get("fon_tip","📻 Radyo Klasik"); ci=fo.index(cf) if cf in fo else 0
                        nft=st.selectbox("Fon Tipi",fo,index=ci,label_visibility="collapsed",key=f"ft_{sid}")
                        if nft!=cf: st.session_state._playlist[si]["fon_tip"]=nft; st.session_state._rj_plan_ok=False; st.rerun()
                        st.markdown(f"<div style='font-size:.67rem;color:#10b981;'>ℹ️ {FON_TIPLERI[nft]}</div>",unsafe_allow_html=True)
                    if song.get("anons_bas"):
                        st.markdown("<span class='sl3'>▸ Baş Anons Metni</span>",unsafe_allow_html=True)
                        bd=song.get("anons_bas_text") or auto_bas(song)
                        nbt=st.text_area("BT",value=bd,height=78,label_visibility="collapsed",key=f"bat_{sid}")
                        if nbt!=song.get("anons_bas_text",""): st.session_state._playlist[si]["anons_bas_text"]=nbt; st.session_state._playlist[si]["anons_wav_bas"]=None
                        if song.get("anons_wav_bas"): st.markdown("<div class='card g' style='font-size:.71rem;'>✅ Ses üretildi</div>",unsafe_allow_html=True); st.audio(song["anons_wav_bas"],format="audio/wav")
                        else: st.markdown("<div class='card a' style='font-size:.71rem;'>⏳ Henüz ses yok — Üretim sekmesinden üretin</div>",unsafe_allow_html=True)
                    if song.get("anons_son"):
                        st.markdown("<span class='sl3'>▸ Son Anons Metni</span>",unsafe_allow_html=True)
                        sd=song.get("anons_son_text") or auto_son(song)
                        nst=st.text_area("ST",value=sd,height=78,label_visibility="collapsed",key=f"sot_{sid}")
                        if nst!=song.get("anons_son_text",""): st.session_state._playlist[si]["anons_son_text"]=nst; st.session_state._playlist[si]["anons_wav_son"]=None
                        if song.get("anons_wav_son"): st.markdown("<div class='card g' style='font-size:.71rem;'>✅ Ses üretildi</div>",unsafe_allow_html=True); st.audio(song["anons_wav_son"],format="audio/wav")
                        else: st.markdown("<div class='card a' style='font-size:.71rem;'>⏳ Henüz ses yok</div>",unsafe_allow_html=True)
                    st.markdown("<hr>",unsafe_allow_html=True)
                    or1,or2,or3,or4=st.columns(4)
                    with or1:
                        if si>0 and st.button("⬆️",key=f"up_{sid}",use_container_width=True):
                            p2=st.session_state._playlist; p2[si-1],p2[si]=p2[si],p2[si-1]; st.session_state._rj_plan_ok=False; st.rerun()
                    with or2:
                        if si<len(pl)-1 and st.button("⬇️",key=f"dn_{sid}",use_container_width=True):
                            p2=st.session_state._playlist; p2[si+1],p2[si]=p2[si],p2[si+1]; st.session_state._rj_plan_ok=False; st.rerun()
                    with or3:
                        if st.button("🔝",key=f"top_{sid}",use_container_width=True):
                            p2=st.session_state._playlist; p2.insert(0,p2.pop(si)); st.session_state._rj_plan_ok=False; st.rerun()
                    with or4:
                        if st.button("🗑️",key=f"dsong_{sid}",use_container_width=True): st.session_state._playlist.pop(si); st.session_state._rj_plan_ok=False; st.rerun()
            if st.button("🗑️ Playlist'i Temizle",use_container_width=True,key="clr_pl"): st.session_state._playlist=[]; st.session_state._rj_plan_ok=False; st.rerun()

    # RJ2 - AYARLAR
    with rj2:
        st.markdown("<div class='card b'>Bu ayarlar tüm Delay Reji anonslarına uygulanır.</div>",unsafe_allow_html=True)
        ra1,ra2=st.columns(2)
        with ra1:
            rjml=st.selectbox("Model",list(MODELS.values()),label_visibility="collapsed",key="rj_msel")
            rjmk=[k for k,v in MODELS.items() if v==rjml][0]
            if rjmk!=st.session_state._rj_model: st.session_state._rj_model=rjmk
            rjll=st.selectbox("Dil",list(LANGUAGES.values()),index=1,label_visibility="collapsed",key="rj_lsel")
            rjlk=[k for k,v in LANGUAGES.items() if v==rjll][0]
            if rjlk!=st.session_state._rj_lang: st.session_state._rj_lang=rjlk
            rj_st=st.text_input("Başlangıç Saati",value=st.session_state._rj_start,placeholder="HH:MM",label_visibility="collapsed",key="rj_start_inp")
            if rj_st!=st.session_state._rj_start: st.session_state._rj_start=rj_st; st.session_state._rj_plan_ok=False
        with ra2:
            rjcn=st.radio("Cinsiyet",["Tümü","♀ Kadın","♂ Erkek"],horizontal=True,label_visibility="collapsed",key="rj_cn")
            rjvf={k:v for k,v in VOICES.items() if rjcn=="Tümü" or (rjcn=="♀ Kadın" and v[0]=="♀") or (rjcn=="♂ Erkek" and v[0]=="♂")}
            rjvc=st.selectbox("Ses",list(rjvf.keys()),format_func=lambda x:f"{VOICES[x][0]} {x}",label_visibility="collapsed",key="rj_vsel")
            if rjvc!=st.session_state._rj_voice: st.session_state._rj_voice=rjvc
        st.markdown("<span class='sl'>▶ Reji Stil Talimatı</span>",unsafe_allow_html=True)
        rjps=st.selectbox("Stil Preset",list(STYLE_PRESETS.keys()),label_visibility="collapsed",key="rj_ps")
        rjsty=st.text_area("Stil",value=STYLE_PRESETS[rjps],height=72,label_visibility="collapsed",key="rj_sty")
        if rjsty!=st.session_state._rj_style: st.session_state._rj_style=rjsty
        st.markdown(f"<div class='card t'>🎙️ <b>{st.session_state._rj_voice}</b> · 🤖 <b>{st.session_state._rj_model.replace('gemini-','').replace('-tts','')}</b> · 🌐 <b>{st.session_state._rj_lang}</b> · 🕐 <b>{st.session_state._rj_start}</b></div>",unsafe_allow_html=True)
        if st.button("🔄 Tüm Anons Metinlerini Otomatik Yenile",use_container_width=True,key="regen_all"):
            for i,s in enumerate(st.session_state._playlist):
                if s.get("anons_bas"): st.session_state._playlist[i]["anons_bas_text"]=auto_bas(s); st.session_state._playlist[i]["anons_wav_bas"]=None
                if s.get("anons_son"): st.session_state._playlist[i]["anons_son_text"]=auto_son(s); st.session_state._playlist[i]["anons_wav_son"]=None
            st.success("✅ Metinler yenilendi!"); st.session_state._rj_plan_ok=False

    # RJ3 - YAYIN PLANI
    with rj3:
        pl3=st.session_state._playlist
        if not pl3: st.markdown("<div class='card r'>⚠️ Playlist boş.</div>",unsafe_allow_html=True)
        else:
            gc1,_=st.columns([1,2])
            with gc1:
                if st.button("📋 Yayın Planını Oluştur",type="primary",use_container_width=True,key="gen_plan"):
                    st.session_state._rj_plan=build_plan(pl3,st.session_state._rj_start); st.session_state._rj_plan_ok=True; st.rerun()
            if not st.session_state._rj_plan_ok:
                st.markdown("<div class='card a'>ℹ️ Plan henüz oluşturulmadı.</div>",unsafe_allow_html=True)
            else:
                plan=st.session_state._rj_plan; tp=sum(p["dur"] for p in plan)
                sb=[p for p in plan if p["type"]=="song"]; ab=[p for p in plan if p["type"] in ("anons_bas","anons_son")]; fb=[p for p in plan if p["type"]=="fon"]
                et=add_time(st.session_state._rj_start,int(tp))
                pc1,pc2,pc3,pc4=st.columns(4)
                with pc1: st.markdown(f'<div class="mbox t"><div class="v">{len(sb)}</div><div class="l">Şarkı</div></div>',unsafe_allow_html=True)
                with pc2: st.markdown(f'<div class="mbox a"><div class="v">{len(ab)}</div><div class="l">Anons</div></div>',unsafe_allow_html=True)
                with pc3: st.markdown(f'<div class="mbox g"><div class="v">{len(fb)}</div><div class="l">Fon</div></div>',unsafe_allow_html=True)
                with pc4: st.markdown(f'<div class="mbox b"><div class="v">{fmt_dur(tp)}</div><div class="l">Toplam</div></div>',unsafe_allow_html=True)
                st.markdown(f"<div style='background:#021409;border:2px solid #10b981;border-radius:10px;padding:12px 16px;margin:9px 0;'><div style='font-family:Syne,sans-serif;font-weight:800;color:#34d399;'>📡 {st.session_state._rj_start} → {et[:5]}</div><div style='font-size:.74rem;color:#2e5040;margin-top:3px;'>{len(plan)} blok · {len(sb)} şarkı · {len(ab)} anons · {len(fb)} fon</div></div>",unsafe_allow_html=True)
                tmap={"song":("ttype-song","🎵 ŞARKI"),"anons_bas":("ttype-anons","🎙️ BAŞ"),"anons_son":("ttype-anons","🎙️ SON"),"fon":("ttype-fon","🎶 FON")}
                for blk in plan:
                    tcls,tlbl=tmap.get(blk["type"],("ttype-song","?"))
                    wi="✅ " if blk.get("wav") else ("⏳ " if blk["type"] in ("anons_bas","anons_son") else "")
                    st.markdown(f"<div class='tl-block'><span class='tl-time'>{blk['time'][:5]}</span><span class='tl-type {tcls}'>{tlbl}</span><span class='tl-lbl'>{wi}{blk['label']}</span><span class='tl-dur'>{fmt_dur(blk['dur'])}</span></div>",unsafe_allow_html=True)

    # RJ4 - ÜRETİM & ZIP
    with rj4:
        pl4=st.session_state._playlist
        if not pl4: st.markdown("<div class='card r'>⚠️ Playlist boş.</div>",unsafe_allow_html=True)
        else:
            needed=[(i,s,"bas") for i,s in enumerate(pl4) if s.get("anons_bas") and not s.get("anons_wav_bas")]+[(i,s,"son") for i,s in enumerate(pl4) if s.get("anons_son") and not s.get("anons_wav_son")]
            done=[(i,s,"bas") for i,s in enumerate(pl4) if s.get("anons_bas") and s.get("anons_wav_bas")]+[(i,s,"son") for i,s in enumerate(pl4) if s.get("anons_son") and s.get("anons_wav_son")]
            _,trj=pool_stats()
            st.markdown(f"<div class='card {'t' if not needed else 'a'}'>✅ {len(done)} üretildi · ⏳ {len(needed)} bekliyor · Ses: <b>{st.session_state._rj_voice}</b> · {trj} kalan</div>",unsafe_allow_html=True)
            st.markdown("<span class='sl'>▶ Şarkı Bazlı Üretim</span>",unsafe_allow_html=True)
            for si,song in enumerate(pl4):
                sid=song["id"]
                if not song.get("anons_bas") and not song.get("anons_son"): continue
                with st.expander(f"🎵 {si+1:02d}. {song.get('title','?')}",expanded=False):
                    ub1,ub2=st.columns(2)
                    if song.get("anons_bas"):
                        with ub1:
                            st.markdown("<div style='font-size:.71rem;color:#f59e0b;font-weight:700;margin-bottom:3px;'>🎙️ BAŞ ANONSU</div>",unsafe_allow_html=True)
                            bt=song.get("anons_bas_text") or auto_bas(song)
                            st.text_area("bt2",value=bt,height=68,label_visibility="collapsed",key=f"pb_{sid}",disabled=True)
                            if song.get("anons_wav_bas"): st.audio(song["anons_wav_bas"],format="audio/wav"); st.download_button("💾 BAŞ",song["anons_wav_bas"],file_name=f"bas_{si+1:02d}.wav",mime="audio/wav",key=f"dlb_{sid}")
                            if st.button("🔴 Üret",key=f"gb_{sid}",use_container_width=True):
                                ak_r,ai_r=get_key()
                                if ak_r:
                                    with st.spinner("🎙️ Baş…"):
                                        try:
                                            rw=tts_single(ak_r,st.session_state._rj_model,bt,st.session_state._rj_voice,st.session_state._rj_lang,st.session_state._rj_style)
                                            wv=pcm2wav(rw); consume(ai_r,len(bt))
                                            st.session_state._playlist[si]["anons_wav_bas"]=wv; arc_add(st.session_state._rj_voice,st.session_state._rj_model,st.session_state._rj_lang,st.session_state._rj_style,bt,wv,"reji"); st.session_state._rj_plan_ok=False; st.rerun()
                                        except Exception as e: st.error(f"❌ {e}")
                    if song.get("anons_son"):
                        with ub2:
                            st.markdown("<div style='font-size:.71rem;color:#60a5fa;font-weight:700;margin-bottom:3px;'>🎙️ SON ANONSU</div>",unsafe_allow_html=True)
                            st2=song.get("anons_son_text") or auto_son(song)
                            st.text_area("st3",value=st2,height=68,label_visibility="collapsed",key=f"ps_{sid}",disabled=True)
                            if song.get("anons_wav_son"): st.audio(song["anons_wav_son"],format="audio/wav"); st.download_button("💾 SON",song["anons_wav_son"],file_name=f"son_{si+1:02d}.wav",mime="audio/wav",key=f"dls_{sid}")
                            if st.button("🔴 Üret",key=f"gs_{sid}",use_container_width=True):
                                ak_r2,ai_r2=get_key()
                                if ak_r2:
                                    with st.spinner("🎙️ Son…"):
                                        try:
                                            rw2=tts_single(ak_r2,st.session_state._rj_model,st2,st.session_state._rj_voice,st.session_state._rj_lang,st.session_state._rj_style)
                                            wv2=pcm2wav(rw2); consume(ai_r2,len(st2))
                                            st.session_state._playlist[si]["anons_wav_son"]=wv2; arc_add(st.session_state._rj_voice,st.session_state._rj_model,st.session_state._rj_lang,st.session_state._rj_style,st2,wv2,"reji"); st.session_state._rj_plan_ok=False; st.rerun()
                                        except Exception as e: st.error(f"❌ {e}")
            st.markdown("<hr><span class='sl'>▶ Toplu Üretim</span>",unsafe_allow_html=True)
            if needed:
                st.markdown(f"<div class='card {'a' if len(needed)>trj else 'b'}'>{len(needed)} anons üretilecek · {trj} kalan</div>",unsafe_allow_html=True)
                if st.button(f"🔴 {len(needed)} Anonsu Toplu Üret",type="primary",use_container_width=True,key="bulk_rj"):
                    prg=st.progress(0); sts_r=st.empty(); errs_r=[]
                    for ni,(nsi,nsong,ntype) in enumerate(needed):
                        ak_b,ai_b=get_key()
                        if ak_b is None: errs_r.append("API kalmadı"); break
                        ntxt=(nsong.get("anons_bas_text") or auto_bas(nsong)) if ntype=="bas" else (nsong.get("anons_son_text") or auto_son(nsong))
                        sts_r.markdown(f"<div style='font-size:.73rem;color:#6b7a8d;'>🎙️ {ni+1}/{len(needed)}: {nsong['title']} [{ntype}]</div>",unsafe_allow_html=True)
                        try:
                            rw_b=tts_single(ak_b,st.session_state._rj_model,ntxt,st.session_state._rj_voice,st.session_state._rj_lang,st.session_state._rj_style)
                            wv_b=pcm2wav(rw_b); consume(ai_b,len(ntxt))
                            if ntype=="bas": st.session_state._playlist[nsi]["anons_wav_bas"]=wv_b
                            else: st.session_state._playlist[nsi]["anons_wav_son"]=wv_b
                            arc_add(st.session_state._rj_voice,st.session_state._rj_model,st.session_state._rj_lang,st.session_state._rj_style,ntxt,wv_b,"reji")
                        except Exception as e: errs_r.append(f"{nsong['title']} ({ntype}): {e}")
                        prg.progress((ni+1)/len(needed))
                    sts_r.empty(); st.session_state._rj_plan_ok=False
                    if errs_r:
                        for er in errs_r: st.markdown(f"<div class='card r'>❌ {er}</div>",unsafe_allow_html=True)
                    else: st.success(f"✅ {len(needed)} anons üretildi!"); st.rerun()
            else: st.markdown("<div class='card g'>✅ Tüm anonslar üretildi!</div>",unsafe_allow_html=True)
            st.markdown("<hr><span class='sl'>▶ ZIP İndir</span>",unsafe_allow_html=True)
            zip_rj=[]
            for si2,s2 in enumerate(pl4):
                if s2.get("anons_wav_bas"): zip_rj.append((f"{si2+1:02d}_BAS_{s2.get('title','?')[:10]}.wav",s2["anons_wav_bas"]))
                if s2.get("anons_wav_son"): zip_rj.append((f"{si2+1:02d}_SON_{s2.get('title','?')[:10]}.wav",s2["anons_wav_son"]))
            if zip_rj:
                st.markdown(f"<div class='card t'>{len(zip_rj)} anons ZIP'e hazır</div>",unsafe_allow_html=True)
                st.download_button(f"📦 {len(zip_rj)} Anonsu ZIP İndir",make_zip(zip_rj),file_name=f"reji_{st.session_state._rj_start.replace(':','-')}.zip",mime="application/zip",use_container_width=True,key="dl_rj_zip")
            else: st.markdown("<div class='card a'>⏳ Üretilmiş anons yok.</div>",unsafe_allow_html=True)


# ════════════════ T7 — FON+ANONS MİKSERİ ════════════════════════
with t7:
    st.markdown("<div class='rjhdr' style='border-color:#1a1a3e;'><h2 style='background:linear-gradient(90deg,#fff 30%,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>🎛️ Fon+Anons Mikseri</h2><p style='color:#2e2040;'>Anons TTS + Fon müziği · Duck efekti · Fade-in/out · Arşivden miksleme · ZIP</p></div>",unsafe_allow_html=True)
    if not PYDUB_OK:
        st.markdown("<div class='card r'>⚠️ PyDub kurulu değil: <code>pip install pydub</code></div>",unsafe_allow_html=True)
    else:
        fon_mx=list_audio(DIRS["fon"])
        if not fon_mx: st.markdown("<div class='card a'>📁 Fon klasörü boş. Kütüphane sekmesinden müzik yükleyin.</div>",unsafe_allow_html=True)
        mx1,mx2,mx3=st.tabs(["🎛️ Tek Miksleme","📦 Toplu Fon","🗄️ Arşivden"])

        with mx1:
            cLm,cRm=st.columns([1.1,1],gap="large")
            with cLm:
                st.markdown("<span class='sl'>▶ Anons TTS Ayarları</span>",unsafe_allow_html=True)
                mx_ml=st.selectbox("MX Model",list(MODELS.values()),label_visibility="collapsed",key="mx_m")
                mx_mdl=[k for k,v in MODELS.items() if v==mx_ml][0]
                mx_ll=st.selectbox("MX Dil",list(LANGUAGES.values()),label_visibility="collapsed",index=1,key="mx_l")
                mx_lng=[k for k,v in LANGUAGES.items() if v==mx_ll][0]
                mx_cn=st.radio("MX Cins",["Tümü","♀ Kadın","♂ Erkek"],horizontal=True,label_visibility="collapsed",key="mx_cn")
                mx_vf={k:v for k,v in VOICES.items() if mx_cn=="Tümü" or (mx_cn=="♀ Kadın" and v[0]=="♀") or (mx_cn=="♂ Erkek" and v[0]=="♂")}
                mx_vc=st.selectbox("MX Ses",list(mx_vf.keys()),format_func=lambda x:f"{VOICES[x][0]} {x}",label_visibility="collapsed",key="mx_v")
                mx_ps=st.selectbox("MX Stil",list(STYLE_PRESETS.keys()),label_visibility="collapsed",key="mx_ps")
                mx_sty=st.text_area("MX Stil T",value=STYLE_PRESETS[mx_ps],height=58,label_visibility="collapsed",key="mx_sty")
                st.markdown("<span class='sl'>▶ Hazır Anons WAV Yükle</span>",unsafe_allow_html=True)
                mx_up=st.file_uploader("Hazır anons",type=["wav","mp3"],key="mx_up")
                mx_uwav=None
                if mx_up:
                    _,mx_uwav=save_upload(mx_up,DIRS["anons"],f"up_{int(time.time())}.wav")
                    if mx_uwav: st.audio(mx_uwav,format="audio/wav"); st.markdown(f"<div class='card g' style='font-size:.71rem;'>✅ Yüklendi — {dur_bytes(mx_uwav):.1f}s</div>",unsafe_allow_html=True)
            with cRm:
                st.markdown("<span class='sl'>▶ Anons Metni</span>",unsafe_allow_html=True)
                mx_txt=st.text_area("MX TXT","",height=95,label_visibility="collapsed",key="mx_txt",placeholder="Anons metni yaz veya sol taraftan WAV yükle…")
                if mx_txt: txt_stats(mx_txt)
                st.markdown("<span class='sl'>▶ Fon Müziği</span>",unsafe_allow_html=True)
                fon_src=st.radio("Fon Kaynak",["📁 Kütüphaneden","📤 Yükle"],horizontal=True,key="fon_src")
                sel_fon=None; fon_path=None
                if fon_src=="📁 Kütüphaneden":
                    if fon_mx:
                        sel_fon=st.selectbox("Fon",fon_mx,label_visibility="collapsed",key="sel_fon")
                        fon_path=os.path.join(DIRS["fon"],sel_fon)
                        st.markdown(f"<div style='font-size:.67rem;color:#2e3f55;'>{sel_fon} · {fmt_dur(dur_file(fon_path))}</div>",unsafe_allow_html=True)
                    else: st.markdown("<div class='card a'>Kütüphanede fon yok</div>",unsafe_allow_html=True)
                else:
                    fon_up2=st.file_uploader("Fon Müziği",type=["mp3","wav","ogg"],key="fon_up2")
                    if fon_up2:
                        dp2,_=save_upload(fon_up2,DIRS["fon"],fon_up2.name)
                        if dp2: sel_fon=fon_up2.name; fon_path=dp2; st.success(f"✅ Kütüphaneye eklendi")
                st.markdown("<span class='sl'>▶ Parametreler</span>",unsafe_allow_html=True)
                mx_p1,mx_p2=st.columns(2)
                with mx_p1:
                    fvol=st.slider("Fon Ses",-24,0,-8,key="mx_fvol")
                    duck=st.slider("Duck dB",-30,-6,-16,key="mx_duck")
                with mx_p2:
                    fi=st.slider("Fade-In ms",100,3000,800,key="mx_fi")
                    fo=st.slider("Fade-Out ms",100,5000,1500,key="mx_fo")
                mx_eq=st.selectbox("EQ",EQ_OPTS,label_visibility="collapsed",key="mx_eq")
                if st.button("🎛️ MİKSLE & OLUŞTUR",type="primary",use_container_width=True,key="mx_btn"):
                    anons_wav=mx_uwav
                    if not anons_wav and mx_txt.strip():
                        ak_mx,ai_mx=get_key()
                        if ak_mx:
                            with st.spinner(f"🎙️ {mx_vc}…"):
                                try:
                                    rw=tts_single(ak_mx,mx_mdl,mx_txt,mx_vc,mx_lng,mx_sty); anons_wav=pcm2wav(rw); consume(ai_mx,len(mx_txt)); arc_add(mx_vc,mx_mdl,mx_lng,mx_sty,mx_txt,anons_wav,"tek")
                                except Exception as e: st.error(f"❌ TTS: {e}")
                    if anons_wav and fon_path and os.path.exists(fon_path):
                        with st.spinner("🎛️ Miksliyor…"):
                            try:
                                vs=AudioSegment.from_file(io.BytesIO(anons_wav),format="wav")
                                fs=AudioSegment.from_file(fon_path)
                                mx_out=mix_fon_voice(fs,vs,fvol,duck,fi,fo)
                                if mx_eq!="Ham": mx_out=apply_eq(mx_out,mx_eq)
                                mxw=seg_to_wav(norm_seg(mx_out))
                                qs=qs_bytes(mxw)
                                st.markdown(f"<div class='card t'>✅ Fon+Anons Hazır · {fmt_dur(len(mx_out)/1000)} · {qs}/100</div>",unsafe_allow_html=True)
                                st.audio(mxw,format="audio/wav"); draw_wf(mxw)
                                st.download_button("📦 Fon+Anons WAV İndir",mxw,file_name=f"fon_anons_{int(time.time())}.wav",mime="audio/wav",use_container_width=True,key="dl_mx")
                            except Exception as e: st.error(f"❌ Miksleme: {e}")
                    elif anons_wav:
                        st.audio(anons_wav,format="audio/wav")
                        st.download_button("💾 Anons (fonsuz)",anons_wav,file_name="anons.wav",mime="audio/wav",key="dl_anons_only")
                    elif not (mx_txt.strip() or mx_uwav): st.warning("⚠️ Metin girin veya WAV yükleyin.")

        with mx2:
            st.markdown("<div class='card b'>Arşivdeki TTS seslerine toplu fon uygula</div>",unsafe_allow_html=True)
            arc_mx=[e for e in st.session_state._archive if e.get("wav")]
            if not arc_mx or not fon_mx: st.info("Arşivde ses veya kütüphanede fon yok.")
            else:
                sf_bulk=st.selectbox("Fon",fon_mx,key="sfb"); fv_b=st.slider("Fon Ses",-24,0,-8,key="fvb"); dd_b=st.slider("Duck",-30,-6,-16,key="ddb")
                sel_ab=st.multiselect("Arşivden Seç",[f"{e['ts_s']} · {e['voice']} · {e['prev'][:28]}" for e in arc_mx],key="sel_ab")
                if sel_ab and st.button("📦 Toplu Uygula",use_container_width=True,key="bulk_fon"):
                    idxs=[i for i,e in enumerate(arc_mx) if f"{e['ts_s']} · {e['voice']} · {e['prev'][:28]}" in sel_ab]
                    fs2=AudioSegment.from_file(os.path.join(DIRS["fon"],sf_bulk)); res_b=[]; prg_b=st.progress(0)
                    for ni,idx_b in enumerate(idxs):
                        try:
                            vs2=AudioSegment.from_file(io.BytesIO(arc_mx[idx_b]["wav"]),format="wav")
                            ms=mix_fon_voice(fs2,vs2,fv_b,dd_b); mw=seg_to_wav(ms)
                            res_b.append((f"fon_{arc_mx[idx_b]['voice']}_{arc_mx[idx_b]['id']}.wav",mw))
                        except Exception as e: st.warning(f"Hata: {e}")
                        prg_b.progress((ni+1)/len(idxs))
                    if res_b: z=make_zip(res_b); st.success(f"✅ {len(res_b)} ses miksleştirildi!"); st.download_button("📦 ZIP",z,"fon_toplu.zip","application/zip",key="dl_toplu_fon")

        with mx3:
            arc_mx3=[e for e in st.session_state._archive if e.get("wav")]
            if not arc_mx3: st.info("Arşiv boş.")
            else:
                sel_a3=st.selectbox("Arşivden",[f"{e['ts_s']} | {e['voice']} | {e['prev'][:38]}" for e in arc_mx3],key="sel_a3")
                idx_a3=next((i for i,e in enumerate(arc_mx3) if f"{e['ts_s']} | {e['voice']} | {e['prev'][:38]}"==sel_a3),0)
                ent=arc_mx3[idx_a3]; st.audio(ent["wav"],format="audio/wav"); draw_wf(ent["wav"])
                if fon_mx:
                    sf3=st.selectbox("Fon",fon_mx,key="sf3"); fv3=st.slider("Fon",-24,0,-8,key="fv3")
                    if st.button("🎛️ Uygula",use_container_width=True,key="arc_mix3"):
                        try:
                            vs3=AudioSegment.from_file(io.BytesIO(ent["wav"]),format="wav"); fs3=AudioSegment.from_file(os.path.join(DIRS["fon"],sf3))
                            m3=mix_fon_voice(fs3,vs3,fv3); mw3=seg_to_wav(norm_seg(m3)); st.audio(mw3,format="audio/wav"); st.download_button("💾 WAV",mw3,f"arc_fon_{ent['id']}.wav","audio/wav",key="dl_arc3")
                        except Exception as e: st.error(f"❌ {e}")

# ════════════════ T8 — YAYIN OTOMASYONU ══════════════════════════
with t8:
    st.markdown("<div class='rjhdr' style='border-color:#0d2e0a;'><h2 style='background:linear-gradient(90deg,#fff 30%,#22c55e);-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>🚀 Yayın Otomasyonu</h2><p style='color:#1a3010;'>Şarkı + Anons + Fon → Tam yayın akışı · Zincir · Ses Birleştir · ZIP</p></div>",unsafe_allow_html=True)
    if not PYDUB_OK:
        st.markdown("<div class='card r'>⚠️ PyDub gerekli: <code>pip install pydub</code></div>",unsafe_allow_html=True)
    else:
        yo1,yo2,yo3=st.tabs(["📋 Yayın Planla","🔗 Zincir Yayın","✂️ Ses Birleştir"])

        with yo1:
            pl_songs_yo=list_audio(DIRS["playlist"])
            if not pl_songs_yo: st.markdown("<div class='card a'>📁 Kütüphanede şarkı yok. Kütüphane sekmesinden ekleyin.</div>",unsafe_allow_html=True)
            else:
                yc1,yc2=st.columns([1.2,1])
                with yc1:
                    yo_sel=st.multiselect("Şarkı Sıralaması",pl_songs_yo,default=pl_songs_yo[:min(3,len(pl_songs_yo))],key="yo_sel")
                    yo_cf=st.slider("Crossfade ms",0,3000,1200,key="yo_cf"); yo_gap=st.slider("Boşluk ms",0,5000,1500,key="yo_gap")
                    fon_yo=list_audio(DIRS["fon"]); yo_fon=st.selectbox("Fon",["Yok"]+fon_yo,key="yo_fon")
                    yo_fvol=st.slider("Fon Ses",-24,0,-8,key="yo_fvol") if yo_fon!="Yok" else -8
                    yo_duck=st.slider("Duck",-30,-6,-16,key="yo_duck") if yo_fon!="Yok" else -16
                    yo_name=st.text_input("Yayın Adı",value=f"Yayin_{datetime.datetime.now().strftime('%H%M')}",key="yo_name")
                with yc2:
                    st.markdown("<span class='sl'>▶ Anons Ekle</span>",unsafe_allow_html=True)
                    arc_yo=[e for e in st.session_state._archive if e.get("wav")]
                    st.markdown(f"<div style='font-size:.67rem;color:#2e3f55;'>Arşivde {len(arc_yo)} ses · Sırayla şarkı başına atanır</div>",unsafe_allow_html=True)
                    yo_arc=st.checkbox("Arşiv seslerini şarkı başına ekle",key="yo_arc")
                    yo_up=st.file_uploader("Veya Anons WAV Yükle",type=["wav"],accept_multiple_files=True,key="yo_up")
                    up_anons=[]
                    if yo_up:
                        for uf in yo_up:
                            _,wv=save_upload(uf,DIRS["anons"],uf.name)
                            if wv: up_anons.append(wv)
                        if up_anons: st.success(f"✅ {len(up_anons)} anons yüklendi")
                if yo_sel and st.button("🚀 YAYIN OLUŞTUR",type="primary",use_container_width=True,key="yo_btn"):
                    with st.status("🎙️ Yayın oluşturuluyor…",expanded=True) as yo_st:
                        master=AudioSegment.silent(500)
                        fon_yo_seg=AudioSegment.from_file(os.path.join(DIRS["fon"],yo_fon)) if yo_fon!="Yok" else None
                        for idx_y,fn_y in enumerate(yo_sel):
                            sp_y=os.path.join(DIRS["playlist"],fn_y)
                            if not os.path.exists(sp_y): st.write(f"⚠️ {fn_y} bulunamadı"); continue
                            st.write(f"🎵 [{idx_y+1}/{len(yo_sel)}] {fn_y}")
                            try: sseg=AudioSegment.from_file(sp_y)
                            except Exception as e: st.write(f"❌ {e}"); continue
                            an_wav=None
                            if yo_arc and idx_y<len(arc_yo):
                                try: an_wav=arc_yo[idx_y]["wav"]
                                except: pass
                            elif idx_y<len(up_anons): an_wav=up_anons[idx_y]
                            if an_wav:
                                aseg=AudioSegment.from_file(io.BytesIO(an_wav),format="wav")
                                if fon_yo_seg: blk=mix_fon_voice(fon_yo_seg,aseg,yo_fvol,yo_duck).append(sseg,crossfade=min(yo_cf,len(sseg)//3))
                                else: blk=aseg+sseg
                            else: blk=sseg
                            master=master.append(blk,crossfade=min(yo_cf,len(blk)//3))
                            if yo_gap>0: master+=AudioSegment.silent(yo_gap)
                            st.write(f"✅ [{idx_y+1}] Tamamlandı")
                        master=norm_seg(master); out_yo=seg_to_wav(master); yo_st.update(label="✅ Hazır!",state="complete")
                    st.markdown(f"<div class='card g'>✅ {yo_name} · {fmt_dur(len(master)/1000)} · {len(yo_sel)} şarkı</div>",unsafe_allow_html=True)
                    st.audio(out_yo,format="audio/wav"); st.download_button(f"📦 {yo_name} İndir",out_yo,file_name=f"{yo_name}.wav",mime="audio/wav",use_container_width=True,key="dl_yo"); st.balloons()

        with yo2:
            st.markdown("<div class='card b'>Delay Reji anonsları + Kütüphane şarkıları → Zincir yayın</div>",unsafe_allow_html=True)
            pl_songs_ch=list_audio(DIRS["playlist"]); fon_ch_list=list_audio(DIRS["fon"])
            rj_pl=st.session_state._playlist
            if not pl_songs_ch or not fon_ch_list: st.markdown("<div class='card a'>Şarkı ve fon müziği gerekli.</div>",unsafe_allow_html=True)
            elif not rj_pl: st.markdown("<div class='card a'>Delay Reji playlist boş.</div>",unsafe_allow_html=True)
            else:
                ch_fon=st.selectbox("Fon",fon_ch_list,key="ch_fon"); ch_cf=st.slider("Crossfade",0,2000,1000,key="ch_cf"); ch_name=st.text_input("Yayın Adı",value=f"Zincir_{datetime.datetime.now().strftime('%H%M')}",key="ch_name")
                anr=[(s,s.get("anons_wav_bas") or s.get("anons_wav_son")) for s in rj_pl if s.get("anons_wav_bas") or s.get("anons_wav_son")]
                st.markdown(f"<div class='card t'>{len(anr)}/{len(rj_pl)} şarkı için anons hazır</div>",unsafe_allow_html=True)
                if st.button("🔗 ZİNCİR YAYIN",type="primary",use_container_width=True,key="ch_btn"):
                    with st.status("🔗 Zincir…",expanded=True) as ch_st:
                        mch=AudioSegment.silent(500); fch=AudioSegment.from_file(os.path.join(DIRS["fon"],ch_fon))
                        for i,song in enumerate(rj_pl):
                            st.write(f"🎵 [{i+1}/{len(rj_pl)}] {song.get('title','?')}")
                            aw=song.get("anons_wav_bas") or song.get("anons_wav_son"); lf=song.get("local_file")
                            pf=next((f for f in pl_songs_ch if song.get("title","").lower() in f.lower()),None)
                            sp=lf if lf and os.path.exists(lf) else (os.path.join(DIRS["playlist"],pf) if pf else None)
                            if sp and os.path.exists(sp):
                                try:
                                    sg=AudioSegment.from_file(sp)
                                    if aw:
                                        ag=AudioSegment.from_file(io.BytesIO(aw),format="wav"); blk=mix_fon_voice(fch,ag).append(sg,crossfade=ch_cf)
                                    else: blk=sg
                                    mch=mch.append(blk,crossfade=ch_cf); st.write(f"✅ [{i+1}]")
                                except Exception as e: st.write(f"❌ {e}")
                            elif aw:
                                ag2=AudioSegment.from_file(io.BytesIO(aw),format="wav"); mch=mch.append(mix_fon_voice(fch,ag2),crossfade=ch_cf)
                        mch=norm_seg(mch); chw=seg_to_wav(mch); ch_st.update(label="✅ Hazır!",state="complete")
                    st.markdown(f"<div class='card g'>✅ {ch_name} · {fmt_dur(len(mch)/1000)}</div>",unsafe_allow_html=True)
                    st.audio(chw,format="audio/wav"); st.download_button(f"📦 {ch_name}",chw,f"{ch_name}.wav","audio/wav",use_container_width=True,key="dl_ch"); st.balloons()

        with yo3:
            st.markdown("<div class='card b'>Birden fazla sesi sıralı birleştir → tek WAV</div>",unsafe_allow_html=True)
            cnt1,cnt2=st.tabs(["📂 Arşivden","📤 Dosya Yükle"])
            with cnt1:
                arc_cnt=[e for e in st.session_state._archive if e.get("wav")]
                if not arc_cnt: st.info("Arşiv boş.")
                else:
                    sel_cnt=st.multiselect("Sesler (sıra önemli)",[f"{e['ts_s']} | {e['voice']} | {e['prev'][:30]}" for e in arc_cnt],key="sel_cnt")
                    cg=st.slider("Boşluk ms",0,3000,500,key="cg"); cf2=st.slider("Crossfade ms",0,2000,200,key="cf2")
                    if sel_cnt and st.button("🔗 Birleştir",use_container_width=True,key="cnt_arc"):
                        idxs=[i for i,e in enumerate(arc_cnt) if f"{e['ts_s']} | {e['voice']} | {e['prev'][:30]}" in sel_cnt]
                        segs=[]; [segs.append(AudioSegment.from_file(io.BytesIO(arc_cnt[i]["wav"]),format="wav")) for i in idxs if True]
                        if segs:
                            rc=segs[0]
                            for sc3 in segs[1:]:
                                if cg>0: rc+=AudioSegment.silent(cg)
                                rc=rc.append(sc3,crossfade=cf2) if cf2>0 else rc+sc3
                            cw=seg_to_wav(norm_seg(rc)); st.success(f"✅ {len(segs)} ses · {fmt_dur(len(rc)/1000)}"); st.audio(cw,format="audio/wav"); st.download_button("📦 WAV",cw,"birlesik.wav","audio/wav",key="dl_cnt_arc")
            with cnt2:
                cnt_ups=st.file_uploader("Ses Dosyaları",type=["wav","mp3","ogg"],accept_multiple_files=True,key="cnt_up2")
                if cnt_ups:
                    gu=st.slider("Boşluk",0,3000,500,key="gu"); cu=st.slider("Crossfade",0,2000,200,key="cu")
                    if st.button("🔗 Birleştir",use_container_width=True,key="cnt_up_btn"):
                        su=[]
                        for uf in cnt_ups:
                            try: su.append(AudioSegment.from_file(io.BytesIO(uf.read())))
                            except Exception as e: st.warning(f"{uf.name}: {e}")
                        if su:
                            ru=su[0]
                            for s in su[1:]:
                                if gu>0: ru+=AudioSegment.silent(gu)
                                ru=ru.append(s,crossfade=cu) if cu>0 else ru+s
                            uw=seg_to_wav(norm_seg(ru)); st.success(f"✅ {len(su)} dosya · {fmt_dur(len(ru)/1000)}"); st.audio(uw,format="audio/wav"); st.download_button("📦 WAV",uw,"upload_birlesik.wav","audio/wav",key="dl_cnt_up")


# ════════════════ T9 — KÜTÜPHANE ════════════════════════════════
with t9:
    st.markdown("<span class='sl'>▶ Ses Kütüphanesi</span>",unsafe_allow_html=True)
    lib1,lib2,lib3,lib4=st.tabs(["🎵 Şarkılar","🎶 Fon Müzikleri","🎺 Jinglelar","🎭 Efektler"])

    def lib_panel(dir_p,tab,tk,info=""):
        with tab:
            if info: st.markdown(f"<div class='card b' style='font-size:.77rem;'>{info}</div>",unsafe_allow_html=True)
            ups=st.file_uploader("Dosya Yükle",type=["mp3","wav","ogg","flac","m4a"],accept_multiple_files=True,key=f"lib_{tk}")
            if ups:
                cnt_l=0
                for u in ups:
                    sp_l,_=save_upload(u,dir_p,u.name)
                    if sp_l: cnt_l+=1
                    else: st.warning(f"⚠️ {u.name} kaydedilemedi.")
                if cnt_l>0: st.success(f"✅ {cnt_l} dosya eklendi!"); st.rerun()
            files_l=list_audio(dir_p); tot_l=sum(dur_file(os.path.join(dir_p,f)) for f in files_l)
            st.markdown(f"<div style='font-size:.67rem;color:#2e3f55;margin:3px 0 9px;'>{len(files_l)} dosya · {fmt_dur(tot_l)} toplam</div>",unsafe_allow_html=True)
            for f in files_l:
                fp_l=os.path.join(dir_p,f); d_l=dur_file(fp_l); sz_l=os.path.getsize(fp_l)//1024
                cc_l=st.columns([3,1,1])
                with cc_l[0]: st.markdown(f'<div class="song-row"><span class="song-nm">🎵 {f[:38]}</span><span class="song-dur">{fmt_dur(d_l)} · {sz_l}KB</span></div>',unsafe_allow_html=True)
                with cc_l[1]: st.audio(fp_l)
                with cc_l[2]:
                    if st.button("🗑️",key=f"ldel_{tk}_{f}",help="Sil",use_container_width=True): os.remove(fp_l); st.rerun()

    lib_panel(DIRS["playlist"],lib1,"songs")
    lib_panel(DIRS["fon"],lib2,"fon","Enstrümental arka plan. Anons sırasında duck efekti ile otomatik alçalır.")
    lib_panel(DIRS["jingles"],lib3,"jingles")
    lib_panel(DIRS["effects"],lib4,"effects","Alkış, geçiş, ambians efektleri.")

# ════════════════ T10 — ARŞİV ════════════════════════════════════
with t10:
    arc=st.session_state._archive; stat_a=st.session_state._api_stats
    st.markdown("<span class='sl'>▶ Oturum İstatistikleri</span>",unsafe_allow_html=True)
    sa1,sa2,sa3,sa4,sa5=st.columns(5)
    with sa1: st.markdown(f'<div class="mbox b"><div class="v">{len(arc)}</div><div class="l">Kayıt</div></div>',unsafe_allow_html=True)
    with sa2: st.markdown(f'<div class="mbox g"><div class="v">{stat_a["calls"]}</div><div class="l">API Çağrısı</div></div>',unsafe_allow_html=True)
    with sa3: st.markdown(f'<div class="mbox a"><div class="v">{stat_a.get("secs",0):.0f}s</div><div class="l">Üretilen Ses</div></div>',unsafe_allow_html=True)
    with sa4: st.markdown(f'<div class="mbox p"><div class="v">{stat_a["chars"]:,}</div><div class="l">Karakter</div></div>',unsafe_allow_html=True)
    with sa5:
        tmb=sum(e["size"] for e in arc)/(1024*1024)
        st.markdown(f'<div class="mbox"><div class="v">{tmb:.1f}MB</div><div class="l">Boyut</div></div>',unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)
    if not arc:
        st.markdown("<div style='text-align:center;padding:45px;color:#2e3f55;'><div style='font-size:2rem;'>📂</div><div style='font-family:Syne,sans-serif;margin-top:7px;'>Arşiv Boş</div></div>",unsafe_allow_html=True)
    else:
        ah1,ah2,ah3=st.columns([2,1,1])
        with ah1: st.markdown(f"<span class='sl'>▶ {len(arc)} Kayıt</span>",unsafe_allow_html=True)
        with ah2:
            if st.button("📦 Tümünü ZIP",use_container_width=True,key="arc_zip"):
                zall=make_zip([(f"{e['ts_s'].replace(':','-').replace(' ','_')}_{e['voice']}_{e['id']}.wav",e["wav"]) for e in arc])
                st.download_button("💾 ZIP",zall,"imajfm_arsiv.zip","application/zip",key="arc_zip_dl")
        with ah3:
            if st.button("🗑️ Tümünü Sil",use_container_width=True,key="arc_clr"):
                st.session_state._archive=[]; st.session_state._api_stats={"calls":0,"chars":0,"secs":0.0}; st.rerun()
        af1,af2=st.columns([2,1])
        with af1: arc_srch=st.text_input("Ara","",placeholder="🔍 Ses, metin, model…",label_visibility="collapsed",key="arc_srch")
        with af2: arc_mode=st.selectbox("Mod",["Tümü","tek","cift","bulk","bulk-file","ab-A","ab-B","fav","reji"],label_visibility="collapsed",key="arc_mode")
        farce=arc
        if arc_srch.strip():
            q=arc_srch.lower(); farce=[h for h in farce if q in h["voice"].lower() or q in h["text"].lower() or q in h["model_s"].lower()]
        if arc_mode!="Tümü": farce=[h for h in farce if h.get("mode","")==arc_mode]
        st.markdown(f"<div style='font-size:.67rem;color:#2e3f55;margin:3px 0 9px;'>{len(farce)} kayıt</div>",unsafe_allow_html=True)
        mc={"tek":"#3b82f6","cift":"#a78bfa","bulk":"#22c55e","bulk-file":"#10b981","ab-A":"#a78bfa","ab-B":"#fb923c","fav":"#fbbf24","reji":"#10b981"}
        gcols=st.columns(3)
        for gi,h in enumerate(farce):
            with gcols[gi%3]:
                col=mc.get(h.get("mode","tek"),"#3b82f6")
                st.markdown(f"""<div style='background:#0b0f1a;border:1px solid #131c2e;border-radius:8px;padding:10px 12px;margin-bottom:7px;'>
<div style='display:flex;justify-content:space-between;margin-bottom:4px;'>
<span style='font-family:Syne,sans-serif;font-size:.77rem;font-weight:700;color:#60a5fa;'>{VOICES.get(h['voice'].split('+')[0],('?',''))[0]} {h['voice'][:11]}</span>
<span style='font-size:.63rem;color:#2e3f55;font-family:JetBrains Mono,monospace;'>{h['ts_s']}</span></div>
<div style='font-size:.66rem;color:#2e3f55;margin-bottom:4px;'>
<span style='color:{col};background:{col}18;border-radius:3px;padding:1px 5px;font-size:.6rem;font-weight:700;'>{h.get('mode','tek').upper()}</span>
 {h['model_s']} · {h['dur']}s · {h['size']//1024}KB</div>
<div style='font-size:.76rem;color:#6b7a8d;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>{h['prev']}</div></div>""",unsafe_allow_html=True)
                st.audio(h["wav"],format="audio/wav")
                dc1,dc2=st.columns(2)
                with dc1: st.download_button("💾 WAV",h["wav"],file_name=f"imajfm_{h['voice'].lower().replace('+','_')}_{h['id']}.wav",mime="audio/wav",use_container_width=True,key=f"adl_{h['id']}")
                with dc2:
                    if st.button("⭐",key=f"afav_{h['id']}",use_container_width=True,help="Favoriye ekle"):
                        st.session_state._favorites.append({"id":h["id"],"name":h["voice"]+" "+h["ts_s"],"text":h["text"],"voice":h["voice"].split("+")[0],"model":h["model"],"lang":h["lang"]}); st.rerun()

# ════════════════ FOOTER ═════════════════════════════════════════
st.markdown("<hr>",unsafe_allow_html=True)
pds="✅ PyDub" if PYDUB_OK else "❌ PyDub (pip install pydub)"
nps="✅ NumPy/Matplotlib" if NP_OK else "❌ NumPy"
tk_f,tr_f=pool_stats()
st.markdown(f"<div style='text-align:center;color:#0d1522;font-size:.63rem;letter-spacing:.09em;padding:4px 0 10px;'>İMAJ FM TTS STÜDYO v6 · Google Gemini TTS API · {pds} · {nps} · API: {tk_f}/10 yüklü · {tr_f} kalan · 2026</div>",unsafe_allow_html=True)
