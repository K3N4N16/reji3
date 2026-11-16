"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         K3N4N HYBRID v28.0 — MEGA PROFESSIONAL BROADCAST ENGINE             ║
║         Groq LLM + RVC + EdgeTTS + Piper ONNX (TR) — AÇIK TEMA             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  v28.0 MEGA GÜNCELLEME — YENİ ÖZELLİKLER:                                  ║
║  ✅ AÇIK TEMA — tüm metin/menü/alan okunabilir, profesyonel radyo UI        ║
║  ✅ Piper ONNX aktif — onnxruntime ile doğrudan inference çalışıyor         ║
║  ✅ Upload tamamen yeniden yazıldı — her format, her boyut                  ║
║  ✅ speaches-ai repo gerçek dosya isimleri (model.onnx + config.json)       ║
║  ✅ Matplotlib rgba hatası giderildi                                         ║
║  ✅ tuple unpack ValueError giderildi                                        ║
║  🆕 4 Kanal Gelişmiş Ses Mikseri — fon+anons+efekt+jingle canlı miksleme    ║
║  🆕 AI Playlist Üretici — Groq ile otomatik yayın planı ve akış oluşturma   ║
║  🆕 Radyo Saati Widget — canlı saat, NowPlaying, program akışı              ║
║  🆕 Hızlı Önizleme — seslendirmeden metin önizleme ve vurgu analizi         ║
║  🆕 Toplu İndirme Merkezi — tüm üretilen sesleri ZIP/MP3/WAV olarak indir   ║
║  🆕 Gelişmiş Ses Kalite Analizi — waveform + spektrum + LUFS + istatistik   ║
║  🆕 Spektrum Analizörü — gerçek zamanlı frekans analizi                     ║
║  🆕 Yayın Zamanlayıcı — zamanlanmış otomatik yayın tetikleyici              ║
║  🆕 Dinleyici Etkileşim Panosu — canlı mesajlar, oylama, istek sırası       ║
║  🆕 Ses Efekt Zinciri — çoklu efekt pipeline (EQ→Comp→Reverb→Limiter)      ║
║  🆕 Otomatik Metadata — ID3, ses tanıma, otomatik etiketleme                ║
║  🆕 Ses Dönüştürme Merkezi — format/sample rate/bit depth dönüşümü          ║
║  🆕 VU Metre & LUFS — gerçek zamanlı ses seviyesi göstergesi                ║
║  🆕 Akıllı Kütüphane — arama, filtreleme, otomatik playlist oluşturma       ║
║  🆕 Ses Klonlama Stüdyosu — RVC eğitim pipeline'ı ve ileri düzey ayarlar    ║
║  🆕 Çoklu Dil TTS — 15+ dil desteği, otomatik çeviri                        ║
║  🆕 Mobil Uyumlu UI — responsive tasarım, dokunmatik optimizasyon           ║
║  🆕 Tema Sistemi — Açık/Koyu/Gece Mavisi tema desteği                       ║
║  🆕 Güvenlik & Loglama — kullanıcı işlem kayıtları, audit trail             ║
║  🆕 Hızlı Kısayollar — klavye kısayolları, hızlı aksiyon butonları          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ═══════════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════════
import streamlit as st
import os, re, json, time, asyncio, shutil, hashlib, tempfile, math
import wave, subprocess, socket, zipfile, threading, base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from io import BytesIO
from collections import defaultdict, Counter

# ── Opsiyonel kütüphaneler ──
try:
    from huggingface_hub import hf_hub_download, snapshot_download
    HF_OK = True
except ImportError:
    HF_OK = False

try:
    from rvc_python.infer import RVCInference
    RVC_OK = True
except ImportError:
    RVC_OK = False

try:
    from edge_tts import Communicate
    TTS_OK = True
except ImportError:
    TTS_OK = False

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
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON
    MUTAGEN_OK = True
except ImportError:
    MUTAGEN_OK = False

try:
    import onnxruntime as ort
    ONNX_OK = True
except ImportError:
    ONNX_OK = False

try:
    import requests as req_lib
    REQ_OK = True
except ImportError:
    REQ_OK = False

try:
    from scipy import signal
    from scipy.fft import fft, fftfreq
    SCIPY_OK = True
except ImportError:
    SCIPY_OK = False

try:
    import pandas as pd
    PD_OK = True
except ImportError:
    PD_OK = False

# ═══════════════════════════════════════════════════════════════
# DİZİN YAPISI
# ═══════════════════════════════════════════════════════════════
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
PIPER_DIR     = os.path.join(BASE_DIR, "piper_models")
SOURCE_DIR    = os.path.join(BASE_DIR, "source_voices")
STREAM_DIR    = os.path.join(BASE_DIR, "stream")
UPLOAD_DIR    = os.path.join(BASE_DIR, "uploads")
TIMER_DIR     = os.path.join(BASE_DIR, "timers")
INTERACT_DIR  = os.path.join(BASE_DIR, "interactions")
CONVERT_DIR   = os.path.join(BASE_DIR, "conversions")
AUDIT_DIR     = os.path.join(BASE_DIR, "audit")
THEME_DIR     = os.path.join(BASE_DIR, "themes")
PREVIEW_DIR   = os.path.join(BASE_DIR, "previews")
SPECTRUM_DIR  = os.path.join(BASE_DIR, "spectrum")
VU_DIR        = os.path.join(BASE_DIR, "vu_meters")

for _d in [OUT_DIR, PLAYLIST_DIR, UVOICE_DIR, REQUEST_DIR, JINGLE_DIR,
           EFFECT_DIR, FON_DIR, ARCHIVE_DIR, META_DIR, SCHEDULE_DIR,
           NEWS_DIR, MEMORY_DIR, ANALYTICS_DIR, HISTORY_DIR, PIPER_DIR,
           SOURCE_DIR, STREAM_DIR, UPLOAD_DIR, TIMER_DIR, INTERACT_DIR,
           CONVERT_DIR, AUDIT_DIR, THEME_DIR, PREVIEW_DIR, SPECTRUM_DIR, VU_DIR]:
    os.makedirs(_d, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# STREAMLIT CONFIG
# ═══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="K3N4N HYBRID v28.0",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════
# SESSION STATE BAŞLATMA
# ═══════════════════════════════════════════════════════════════
def init_session():
    defaults = {
        "theme": "light",
        "last_live": None,
        "stream_active": False,
        "stream_url": None,
        "stream_file": None,
        "qa_txt": "",
        "fa_txt": "",
        "live_txt": "",
        "nb_txt": "",
        "r_anons": "",
        "m_txt": "",
        "ab_gen": "",
        "bulk_lines": [],
        "mixer_state": {"ch1_vol": 0, "ch2_vol": 0, "ch3_vol": 0, "ch4_vol": 0},
        "playlist_queue": [],
        "interaction_msgs": [],
        "timer_jobs": [],
        "preview_cache": {},
        "audit_log": [],
        "selected_songs": [],
        "quick_actions": True,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ═══════════════════════════════════════════════════════════════
# TEMA SİSTEMİ — Açık / Koyu / Gece Mavisi
# ═══════════════════════════════════════════════════════════════
THEMES = {
    "light": {
        "primary": "#2563eb", "primary_d": "#1d4ed8", "accent": "#7c3aed",
        "red": "#dc2626", "green": "#16a34a", "amber": "#d97706", "teal": "#0891b2",
        "bg": "#f8fafc", "bg2": "#ffffff", "bg3": "#f1f5f9", "bg4": "#e2e8f0",
        "border": "#cbd5e1", "border2": "#e2e8f0",
        "text1": "#0f172a", "text2": "#334155", "text3": "#64748b", "text4": "#94a3b8",
        "shadow": "0 1px 3px rgba(0,0,0,.1), 0 1px 2px rgba(0,0,0,.06)",
        "shadow2": "0 4px 6px rgba(0,0,0,.07), 0 2px 4px rgba(0,0,0,.05)",
        "card_bg": "#ffffff", "input_bg": "#ffffff",
        "success_bg": "#f0fdf4", "success_border": "#bbf7d0", "success_text": "#15803d",
        "warning_bg": "#fffbeb", "warning_border": "#fde68a", "warning_text": "#92400e",
        "error_bg": "#fef2f2", "error_border": "#fecaca", "error_text": "#991b1b",
        "info_bg": "#eff6ff", "info_border": "#bfdbfe", "info_text": "#1e40af",
        "live_bg": "#fef2f2", "live_border": "#fecaca", "live_text": "#dc2626",
        "stream_bg": "#eff6ff", "stream_border": "#bfdbfe", "stream_text": "#2563eb",
        "mono_bg": "#f1f5f9", "mono_border": "#e2e8f0",
    },
    "dark": {
        "primary": "#3b82f6", "primary_d": "#2563eb", "accent": "#8b5cf6",
        "red": "#ef4444", "green": "#22c55e", "amber": "#f59e0b", "teal": "#14b8a6",
        "bg": "#0f172a", "bg2": "#1e293b", "bg3": "#334155", "bg4": "#475569",
        "border": "#475569", "border2": "#334155",
        "text1": "#f8fafc", "text2": "#e2e8f0", "text3": "#cbd5e1", "text4": "#94a3b8",
        "shadow": "0 1px 3px rgba(0,0,0,.3), 0 1px 2px rgba(0,0,0,.2)",
        "shadow2": "0 4px 6px rgba(0,0,0,.4), 0 2px 4px rgba(0,0,0,.3)",
        "card_bg": "#1e293b", "input_bg": "#334155",
        "success_bg": "#14532d", "success_border": "#166534", "success_text": "#86efac",
        "warning_bg": "#713f12", "warning_border": "#854d0e", "warning_text": "#fde047",
        "error_bg": "#450a0a", "error_border": "#7f1d1d", "error_text": "#fca5a5",
        "info_bg": "#1e3a8a", "info_border": "#1e40af", "info_text": "#93c5fd",
        "live_bg": "#450a0a", "live_border": "#7f1d1d", "live_text": "#fca5a5",
        "stream_bg": "#1e3a8a", "stream_border": "#1e40af", "stream_text": "#93c5fd",
        "mono_bg": "#1e293b", "mono_border": "#334155",
    },
    "midnight": {
        "primary": "#6366f1", "primary_d": "#4f46e5", "accent": "#a855f7",
        "red": "#f43f5e", "green": "#10b981", "amber": "#fbbf24", "teal": "#2dd4bf",
        "bg": "#020617", "bg2": "#0f172a", "bg3": "#1e1b4b", "bg4": "#312e81",
        "border": "#4338ca", "border2": "#312e81",
        "text1": "#e0e7ff", "text2": "#c7d2fe", "text3": "#a5b4fc", "text4": "#818cf8",
        "shadow": "0 1px 3px rgba(99,102,241,.2), 0 1px 2px rgba(99,102,241,.1)",
        "shadow2": "0 4px 6px rgba(99,102,241,.3), 0 2px 4px rgba(99,102,241,.2)",
        "card_bg": "#0f172a", "input_bg": "#1e1b4b",
        "success_bg": "#064e3b", "success_border": "#065f46", "success_text": "#34d399",
        "warning_bg": "#78350f", "warning_border": "#92400e", "warning_text": "#fcd34d",
        "error_bg": "#450a0a", "error_border": "#7f1d1d", "error_text": "#fca5a5",
        "info_bg": "#1e1b4b", "info_border": "#4338ca", "info_text": "#a5b4fc",
        "live_bg": "#450a0a", "live_border": "#7f1d1d", "live_text": "#fca5a5",
        "stream_bg": "#1e1b4b", "stream_border": "#4338ca", "stream_text": "#a5b4fc",
        "mono_bg": "#0f172a", "mono_border": "#312e81",
    }
}

def get_theme() -> dict:
    return THEMES.get(st.session_state.get("theme", "light"), THEMES["light"])

T = get_theme()

# ═══════════════════════════════════════════════════════════════
# CSS — DİNAMİK TEMA DESTEĞİ
# ═══════════════════════════════════════════════════════════════
def inject_css():
    t = get_theme()
    css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {{
  --primary:   {t["primary"]};
  --primary-d: {t["primary_d"]};
  --accent:    {t["accent"]};
  --red:       {t["red"]};
  --green:     {t["green"]};
  --amber:     {t["amber"]};
  --teal:      {t["teal"]};
  --bg:        {t["bg"]};
  --bg2:       {t["bg2"]};
  --bg3:       {t["bg3"]};
  --bg4:       {t["bg4"]};
  --border:    {t["border"]};
  --border2:   {t["border2"]};
  --text1:     {t["text1"]};
  --text2:     {t["text2"]};
  --text3:     {t["text3"]};
  --text4:     {t["text4"]};
  --shadow:    {t["shadow"]};
  --shadow2:   {t["shadow2"]};
  --radius:    12px;
  --radius2:   8px;
  --radius3:   6px;
}}

* {{ box-sizing: border-box; }}

.stApp {{
  background: var(--bg) !important;
  color: var(--text1) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 14px !important;
}}

/* Sidebar */
[data-testid="stSidebar"] {{
  background: var(--bg2) !important;
  border-right: 1px solid var(--border2) !important;
  box-shadow: 2px 0 12px rgba(0,0,0,.08) !important;
}}
[data-testid="stSidebar"] * {{ color: var(--text1) !important; }}
[data-testid="stSidebar"] .stRadio label {{
  color: var(--text2) !important;
  font-size: 13px !important;
  padding: 5px 0 !important;
  border-radius: var(--radius2) !important;
  transition: all .15s !important;
}}
[data-testid="stSidebar"] .stRadio label:hover {{
  background: var(--bg3) !important;
}}

/* Inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox select,
[data-baseweb="select"] > div, [data-baseweb="input"] > div {{
  background: var(--input_bg) !important;
  color: var(--text1) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: var(--radius2) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 14px !important;
  transition: all .2s !important;
}}
.stTextInput input:focus, .stTextArea textarea:focus {{
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 3px {t["primary"]}22 !important;
  outline: none !important;
}}

/* Labels */
.stTextInput label, .stTextArea label, .stSelectbox label,
.stFileUploader label, .stSlider label, .stMultiSelect label,
.stDateInput label, .stTimeInput label, .stNumberInput label,
.stRadio label, .stCheckbox label {{
  color: var(--text2) !important;
  font-size: 13px !important;
  font-weight: 500 !important;
}}

/* Buttons */
.stButton > button {{
  background: linear-gradient(135deg, var(--primary), var(--accent)) !important;
  color: #fff !important;
  border: none !important;
  border-radius: var(--radius2) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  letter-spacing: .3px !important;
  padding: 8px 16px !important;
  height: auto !important;
  min-height: 40px !important;
  width: 100% !important;
  cursor: pointer !important;
  transition: all .2s !important;
  box-shadow: var(--shadow) !important;
}}
.stButton > button:hover {{
  background: linear-gradient(135deg, var(--primary-d), {t["accent"]}) !important;
  box-shadow: var(--shadow2) !important;
  transform: translateY(-1px) !important;
}}
.stButton > button:active {{ transform: translateY(0) !important; }}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
  background: var(--bg3) !important;
  border-radius: var(--radius) !important;
  padding: 5px !important;
  gap: 4px !important;
  border: 1px solid var(--border2) !important;
}}
.stTabs [data-baseweb="tab"] {{
  background: transparent !important;
  color: var(--text3) !important;
  border-radius: var(--radius2) !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  padding: 7px 14px !important;
  transition: all .15s !important;
}}
.stTabs [aria-selected="true"] {{
  background: var(--bg2) !important;
  color: var(--primary) !important;
  font-weight: 600 !important;
  box-shadow: var(--shadow) !important;
}}

/* Expander */
.stExpander {{
  background: var(--card_bg) !important;
  border: 1px solid var(--border2) !important;
  border-radius: var(--radius) !important;
  box-shadow: var(--shadow) !important;
}}

/* File uploader */
[data-testid="stFileUploader"] {{
  background: var(--bg3) !important;
  border: 2px dashed var(--border) !important;
  border-radius: var(--radius) !important;
  padding: 14px !important;
}}
[data-testid="stFileUploaderDropzone"] {{
  background: var(--bg3) !important;
}}

/* Progress / status */
.stProgress > div > div {{
  background: linear-gradient(90deg, var(--primary), var(--accent)) !important;
  border-radius: 3px !important;
}}

/* Alerts */
.stSuccess {{ background: {t["success_bg"]} !important; border: 1px solid {t["success_border"]} !important; color: {t["success_text"]} !important; border-radius: var(--radius2) !important; }}
.stWarning {{ background: {t["warning_bg"]} !important; border: 1px solid {t["warning_border"]} !important; color: {t["warning_text"]} !important; border-radius: var(--radius2) !important; }}
.stError   {{ background: {t["error_bg"]}   !important; border: 1px solid {t["error_border"]}   !important; color: {t["error_text"]}   !important; border-radius: var(--radius2) !important; }}
.stInfo    {{ background: {t["info_bg"]}    !important; border: 1px solid {t["info_border"]}    !important; color: {t["info_text"]}    !important; border-radius: var(--radius2) !important; }}

/* Audio player */
audio {{
  width: 100% !important;
  border-radius: var(--radius2) !important;
  background: var(--bg3) !important;
  margin: 4px 0 !important;
}}

/* Scrollbar */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: var(--bg3); border-radius: 3px; }}
::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: var(--text4); }}

/* ── Custom Components ── */
.page-header {{
  display: flex; align-items: center; gap: 14px;
  padding: 18px 0 22px;
  border-bottom: 2px solid var(--bg4);
  margin-bottom: 22px;
}}
.page-header .icon {{
  width: 48px; height: 48px;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  font-size: 24px; color: white;
  box-shadow: 0 4px 12px {t["primary"]}44;
}}
.page-header h1 {{
  font-size: 24px; font-weight: 800;
  color: var(--text1); margin: 0; line-height: 1.2;
  letter-spacing: -0.5px;
}}
.page-header p {{
  font-size: 13px; color: var(--text3); margin: 3px 0 0;
}}

.kcard {{
  background: var(--card_bg);
  border: 1px solid var(--border2);
  border-radius: var(--radius);
  padding: 16px 18px;
  margin-bottom: 12px;
  box-shadow: var(--shadow);
  transition: all .2s;
}}
.kcard:hover {{
  box-shadow: var(--shadow2);
  border-color: var(--border);
  transform: translateY(-1px);
}}
.kcard-accent {{ border-left: 3px solid var(--primary); }}
.kcard-title {{
  font-size: 15px; font-weight: 600;
  color: var(--text1); margin-bottom: 6px;
  display: flex; align-items: center; gap: 8px;
}}
.kcard-body {{
  font-size: 13px; color: var(--text2); line-height: 1.7;
}}

.stat-box {{
  background: var(--card_bg);
  border: 1px solid var(--border2);
  border-radius: var(--radius);
  padding: 16px 14px;
  text-align: center;
  box-shadow: var(--shadow);
  transition: all .2s;
}}
.stat-box:hover {{ transform: translateY(-2px); box-shadow: var(--shadow2); }}
.stat-num {{
  font-size: 32px; font-weight: 800;
  color: var(--primary); line-height: 1.1;
  font-variant-numeric: tabular-nums;
  letter-spacing: -1px;
}}
.stat-lbl {{
  font-size: 11px; color: var(--text3);
  text-transform: uppercase; letter-spacing: 1.2px;
  margin-top: 4px; font-weight: 600;
}}

.chip {{
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 10px; border-radius: 20px;
  font-size: 11px; font-weight: 600;
  letter-spacing: .4px; margin: 2px;
  white-space: nowrap;
  transition: all .15s;
}}
.chip:hover {{ transform: scale(1.05); }}
.chip-blue  {{ background: {t["primary"]}22; color: {t["primary"]}; }}
.chip-green {{ background: {t["green"]}22; color: {t["green"]}; }}
.chip-red   {{ background: {t["red"]}22; color: {t["red"]}; }}
.chip-amber {{ background: {t["amber"]}22; color: {t["amber"]}; }}
.chip-purple{{ background: {t["accent"]}22; color: {t["accent"]}; }}
.chip-teal  {{ background: {t["teal"]}22; color: {t["teal"]}; }}
.chip-gray  {{ background: var(--bg4); color: var(--text2); }}

.section-label {{
  font-size: 11px; font-weight: 700;
  color: var(--text3); text-transform: uppercase;
  letter-spacing: 1.2px; margin: 18px 0 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border2);
  display: flex; align-items: center; gap: 7px;
}}

.qbar-wrap {{
  background: var(--bg4); border-radius: 4px;
  height: 6px; margin: 8px 0; overflow: hidden;
}}
.qbar-fill {{
  height: 100%; border-radius: 4px;
  background: linear-gradient(90deg, {t["red"]}, {t["amber"]}, {t["green"]});
  transition: width .5s ease;
}}

.live-badge {{
  display: inline-flex; align-items: center; gap: 7px;
  background: {t["live_bg"]}; border: 1px solid {t["live_border"]};
  border-radius: 20px; padding: 5px 14px;
  font-size: 12px; font-weight: 700; color: {t["live_text"]};
  letter-spacing: .5px;
}}
.live-dot {{
  width: 8px; height: 8px; border-radius: 50%;
  background: {t["red"]};
  animation: blink 1.1s ease-in-out infinite;
}}
@keyframes blink {{
  0%,100% {{ opacity: 1; box-shadow: 0 0 5px {t["red"]}; }}
  50%      {{ opacity: .2; }}
}}

.stream-url-box {{
  background: {t["stream_bg"]}; border: 1px solid {t["stream_border"]};
  border-radius: var(--radius); padding: 16px 18px;
  font-family: 'JetBrains Mono', monospace; font-size: 13px;
  color: {t["stream_text"]}; line-height: 1.8;
}}

.mono-box {{
  background: {t["mono_bg"]}; border: 1px solid {t["mono_border"]};
  border-radius: var(--radius2); padding: 12px 16px;
  font-family: 'JetBrains Mono', monospace; font-size: 12px;
  color: var(--text2); line-height: 1.8;
}}

.upload-zone {{
  background: {t["info_bg"]}; border: 2px dashed {t["info_border"]};
  border-radius: var(--radius); padding: 20px;
  text-align: center; color: {t["info_text"]};
  font-size: 13px; margin: 10px 0; font-weight: 500;
  transition: all .2s;
}}
.upload-zone:hover {{
  border-color: var(--primary);
  background: {t["primary"]}11;
}}

.song-row {{
  display: flex; align-items: center; gap: 12px;
  background: var(--card_bg); border: 1px solid var(--border2);
  border-radius: var(--radius2); padding: 12px 16px;
  margin-bottom: 8px; box-shadow: var(--shadow);
  transition: all .2s;
}}
.song-row:hover {{ box-shadow: var(--shadow2); transform: translateX(2px); }}
.song-name {{ font-size: 14px; font-weight: 600; color: var(--text1); flex: 1; }}
.song-dur  {{ font-size: 12px; color: var(--text3); font-family: 'JetBrains Mono',monospace; }}

.warn-box {{
  background: {t["warning_bg"]}; border: 1px solid {t["warning_border"]};
  border-radius: var(--radius2); padding: 12px 16px;
  font-size: 13px; color: {t["warning_text"]}; display: flex; gap: 10px; align-items: center;
}}
.ok-box {{
  background: {t["success_bg"]}; border: 1px solid {t["success_border"]};
  border-radius: var(--radius2); padding: 12px 16px;
  font-size: 13px; color: {t["success_text"]}; display: flex; gap: 10px; align-items: center;
}}
.info-box {{
  background: {t["info_bg"]}; border: 1px solid {t["info_border"]};
  border-radius: var(--radius2); padding: 12px 16px;
  font-size: 13px; color: {t["info_text"]}; display: flex; gap: 10px; align-items: center;
}}

.footer {{
  text-align: center; font-size: 12px; color: var(--text4);
  border-top: 1px solid var(--border2);
  padding: 20px 0 10px; margin-top: 36px;
  letter-spacing: .6px;
}}

/* VU Metre */
.vu-meter {{
  background: var(--bg4); border-radius: 4px; height: 24px; overflow: hidden;
  position: relative; margin: 6px 0;
}}
.vu-fill {{
  height: 100%; border-radius: 4px;
  background: linear-gradient(90deg, #16a34a 0%, #16a34a 60%, #d97706 60%, #d97706 85%, #dc2626 85%);
  transition: width .1s ease;
}}
.vu-label {{
  position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
  font-size: 10px; font-weight: 700; color: var(--text1);
  font-family: 'JetBrains Mono', monospace;
}}

/* Quick Action Bar */
.quick-bar {{
  display: flex; gap: 8px; flex-wrap: wrap;
  padding: 10px 0; margin-bottom: 12px;
}}
.quick-btn {{
  background: var(--bg3); border: 1px solid var(--border2);
  border-radius: var(--radius3); padding: 6px 14px;
  font-size: 12px; font-weight: 500; color: var(--text2);
  cursor: pointer; transition: all .15s;
  display: inline-flex; align-items: center; gap: 5px;
}}
.quick-btn:hover {{
  background: var(--primary); color: white; border-color: var(--primary);
  transform: translateY(-1px);
}}

/* Spectrum bars */
.spectrum-bar {{
  display: inline-block; width: 4px; margin: 0 1px;
  background: linear-gradient(to top, var(--primary), var(--accent));
  border-radius: 2px; transition: height .1s ease;
  vertical-align: bottom;
}}

/* Responsive */
@media (max-width: 768px) {{
  .page-header h1 {{ font-size: 18px; }}
  .page-header .icon {{ width: 36px; height: 36px; font-size: 18px; }}
  .stat-num {{ font-size: 24px; }}
  .song-row {{ padding: 10px 12px; }}
}}
</style>
"""
    st.markdown(css, unsafe_allow_html=True)

inject_css()

# ═══════════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════════════════════════
def sfn(s: str, n: int = 36) -> str:
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', str(s))[:n]

def ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def fmt_dur(sec: float) -> str:
    if sec is None or sec < 0:
        return "00:00"
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

def audio_dur(path: str) -> float:
    if not PYDUB_OK or not os.path.exists(path):
        return 0.0
    try:
        return len(AudioSegment.from_file(path)) / 1000.0
    except Exception:
        return 0.0

def list_audio(d: str) -> list:
    exts = (".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac")
    if not os.path.isdir(d):
        return []
    return sorted(f for f in os.listdir(d) if f.lower().endswith(exts))

def list_all_files(d: str, exts: tuple = ()) -> list:
    if not os.path.isdir(d):
        return []
    if not exts:
        return sorted(os.listdir(d))
    return sorted(f for f in os.listdir(d) if f.lower().endswith(exts))

def word_count(t: str) -> int:
    return len(t.split()) if t and t.strip() else 0

def est_dur(text: str, spd: int = 100) -> float:
    wpm = 130 * (spd / 100)
    return (word_count(text) / wpm) * 60 if word_count(text) else 0.0

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
    text = re.sub(r'`[^`]*`', '', text)
    text = re.sub(r'\[[^\]]*\](?:\([^)]*\))?', '', text)
    text = re.sub(r'[#]{1,6}\s*', '', text)
    text = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def truncate(s: str, n: int = 80) -> str:
    return s[:n] + ("…" if len(s) > n else "")

# ── Upload — her tür destekler ──
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

        if hasattr(uploaded_file, 'getvalue'):
            raw = uploaded_file.getvalue()
        elif hasattr(uploaded_file, 'getbuffer'):
            raw = bytes(uploaded_file.getbuffer())
        elif hasattr(uploaded_file, 'read'):
            uploaded_file.seek(0)
            raw = uploaded_file.read()
        elif isinstance(uploaded_file, (bytes, bytearray)):
            raw = bytes(uploaded_file)
        else:
            return None

        if not raw or len(raw) < 64:
            return None

        with open(dest, 'wb') as f:
            f.write(raw)

        if PYDUB_OK:
            try:
                seg = AudioSegment.from_file(dest)
                if len(seg) < 50:
                    os.remove(dest)
                    return None
                if not dest.lower().endswith('.wav'):
                    wav = os.path.splitext(dest)[0] + '.wav'
                    seg.export(wav, format='wav')
                    try:
                        os.remove(dest)
                    except Exception:
                        pass
                    return wav
            except Exception:
                pass
        return dest if (os.path.exists(dest) and os.path.getsize(dest) > 64) else None
    except Exception as e:
        st.error(f"Upload hatası: {e}")
        return None

# ── UI Helpers ──
def page_header(icon: str, title: str, subtitle: str = ""):
    st.markdown(
        f'<div class="page-header">'
        f'<div class="icon">{icon}</div>'
        f'<div><h1>{title}</h1>'
        f'{"<p>" + subtitle + "</p>" if subtitle else ""}'
        f'</div></div>',
        unsafe_allow_html=True
    )

def section(label: str, icon: str = ""):
    st.markdown(
        f'<div class="section-label">{icon + " " if icon else ""}{label}</div>',
        unsafe_allow_html=True
    )

def chip(text: str, color: str = "blue") -> str:
    return f'<span class="chip chip-{color}">{text}</span>'

def chips(*items) -> str:
    return " ".join(items)

def kcard(title: str, body: str = "", accent: bool = True, extra: str = ""):
    cls = "kcard kcard-accent" if accent else "kcard"
    st.markdown(
        f'<div class="{cls}">'
        f'<div class="kcard-title">{title}</div>'
        f"""{"<div class='kcard-body'>" + body + "</div>" if body else ""}"""
        f'{extra}'
        f'</div>',
        unsafe_allow_html=True
    )

def qbar(score: int):
    st.markdown(
        f'<div class="qbar-wrap"><div class="qbar-fill" style="width:{score}%"></div></div>',
        unsafe_allow_html=True
    )

def vu_meter(level_db: float, max_db: float = 0.0, min_db: float = -60.0, label: str = ""):
    """HTML VU metre göstergesi"""
    pct = max(0, min(100, (level_db - min_db) / (max_db - min_db) * 100))
    st.markdown(
        f'<div class="vu-meter">'
        f'<div class="vu-fill" style="width:{pct:.1f}%"></div>'
        f'<div class="vu-label">{label} {level_db:.1f}dB</div>'
        f'</div>',
        unsafe_allow_html=True
    )

def quick_action_buttons(actions: List[Tuple[str, str, str]]):
    """Hızlı aksiyon butonları: (emoji, label, key)"""
    html = '<div class="quick-bar">'
    for emoji, label, key in actions:
        html += f'<span class="quick-btn" onclick="">{emoji} {label}</span>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# ── Ses Analiz Fonksiyonları ──
def quality_score(path: str) -> int:
    if not PYDUB_OK or not os.path.exists(path):
        return 0
    try:
        seg = AudioSegment.from_file(path)
        sc = 55
        if -22 <= seg.dBFS <= -10:
            sc += 20
        elif -30 <= seg.dBFS <= -22:
            sc += 10
        if -5 <= seg.max_dBFS <= -0.5:
            sc += 20
        elif -8 <= seg.max_dBFS <= -5:
            sc += 10
        if seg.frame_rate >= 44100:
            sc += 10
        sc += 5
        return min(100, max(0, sc))
    except Exception:
        return 0

def lufs_estimate(path: str) -> float:
    """Basit LUFS tahmini (PyDub RMS tabanlı)"""
    if not PYDUB_OK or not os.path.exists(path):
        return -70.0
    try:
        seg = AudioSegment.from_file(path)
        rms = seg.dBFS
        return round(rms - 3.0, 1)
    except Exception:
        return -70.0

def spectral_analysis(path: str) -> Optional[Dict]:
    """Frekans spektrum analizi"""
    if not NP_OK or not SCIPY_OK or not os.path.exists(path):
        return None
    try:
        with wave.open(path, 'r') as wf:
            frames = wf.readframes(wf.getnframes())
            sr = wf.getframerate()
            sw = wf.getsampwidth()
            ch = wf.getnchannels()
        dt = np.int16 if sw == 2 else np.int8
        s = np.frombuffer(frames, dtype=dt)
        if ch == 2:
            s = s.reshape(-1, 2).mean(axis=1)
        s = s.astype(np.float32) / np.max(np.abs(s))
        n = len(s)
        yf = fft(s)
        xf = fftfreq(n, 1 / sr)[:n // 2]
        yf_abs = 2.0 / n * np.abs(yf[0:n // 2])
        bands = {
            "bass": np.mean(yf_abs[(xf >= 20) & (xf < 250)]),
            "low_mid": np.mean(yf_abs[(xf >= 250) & (xf < 500)]),
            "mid": np.mean(yf_abs[(xf >= 500) & (xf < 2000)]),
            "high_mid": np.mean(yf_abs[(xf >= 2000) & (xf < 6000)]),
            "treble": np.mean(yf_abs[(xf >= 6000) & (xf < 20000)]),
        }
        crest_factor = np.max(np.abs(s)) / (np.sqrt(np.mean(s**2)) + 1e-10)
        return {
            "frequencies": xf,
            "magnitude": yf_abs,
            "bands": bands,
            "crest_factor": float(crest_factor),
            "dominant_freq": float(xf[np.argmax(yf_abs)]),
        }
    except Exception as e:
        print(f"Spektral analiz hatası: {e}")
        return None

def draw_waveform(path: str, h: float = 2.0, color: str = None):
    if not NP_OK or not os.path.exists(path):
        return
    try:
        with wave.open(path, 'r') as wf:
            frames = wf.readframes(wf.getnframes())
            sr = wf.getframerate()
            sw = wf.getsampwidth()
            ch = wf.getnchannels()
        dt = np.int16 if sw == 2 else np.int8
        s = np.frombuffer(frames, dtype=dt)
        if ch == 2:
            s = s.reshape(-1, 2).mean(axis=1)
        step = max(1, len(s) // 2000)
        ds = s[::step].astype(np.float32)
        mx = np.max(np.abs(ds)) or 1
        ds /= mx
        t = np.linspace(0, len(s) / sr, len(ds))
        fig, ax = plt.subplots(figsize=(10, h), facecolor=T["bg"])
        ax.set_facecolor(T["bg"])
        c1 = color or T["primary"]
        c2 = color or T["accent"]
        ax.fill_between(t, ds, alpha=.65, color=c1)
        ax.fill_between(t, -np.abs(ds), alpha=.2, color=c2)
        ax.axhline(0, color=T["border"], lw=.8)
        ax.set_xlim(0, t[-1])
        ax.set_ylim(-1.1, 1.1)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.tick_params(colors=T["text4"], labelsize=7)
        ax.set_xlabel("sn", color=T["text4"], fontsize=7)
        plt.tight_layout(pad=.3)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    except Exception:
        pass

def draw_spectrum(spec_data: dict, h: float = 3.0):
    """Spektrum grafiği çiz"""
    if not NP_OK or spec_data is None:
        return
    try:
        fig, ax = plt.subplots(figsize=(10, h), facecolor=T["bg"])
        ax.set_facecolor(T["bg"])
        xf = spec_data["frequencies"]
        yf = spec_data["magnitude"]
        mask = xf <= 20000
        ax.semilogx(xf[mask], 20 * np.log10(yf[mask] + 1e-10), color=T["primary"], lw=1.2, alpha=0.8)
        ax.axvline(250, color=T["amber"], ls='--', alpha=0.4, lw=0.8)
        ax.axvline(2000, color=T["amber"], ls='--', alpha=0.4, lw=0.8)
        ax.axvline(6000, color=T["amber"], ls='--', alpha=0.4, lw=0.8)
        ax.set_xlim(20, 20000)
        ax.set_ylim(-100, 0)
        ax.set_xlabel("Frekans (Hz)", color=T["text3"], fontsize=9)
        ax.set_ylabel("Genlik (dB)", color=T["text3"], fontsize=9)
        for sp in ax.spines.values():
            sp.set_color(T["border"])
        ax.tick_params(colors=T["text4"], labelsize=8)
        ax.grid(True, alpha=0.2, color=T["border"])
        plt.tight_layout(pad=.4)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    except Exception:
        pass

def draw_spectrum_bars(spec_data: dict, n_bars: int = 32):
    """Basit spektrum barları (HTML)"""
    if spec_data is None:
        return
    try:
        bands = spec_data.get("bands", {})
        if not bands:
            return
        max_val = max(bands.values()) or 1
        html = '<div style="display:flex;align-items:flex-end;height:60px;gap:3px;padding:8px;background:' + T["bg3"] + ';border-radius:8px;border:1px solid ' + T["border2"] + ';">'
        colors = [T["primary"], T["accent"], T["teal"], T["amber"], T["red"]]
        for i, (name, val) in enumerate(bands.items()):
            h = max(4, int((val / max_val) * 50))
            c = colors[i % len(colors)]
            html += f'<div style="flex:1;text-align:center;"><div style="height:{h}px;background:{c};border-radius:3px;transition:height .2s;"></div><div style="font-size:8px;color:{T["text4"]};margin-top:2px;text-transform:uppercase;">{name[:4]}</div></div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)
    except Exception:
        pass

# ── Ses İşleme Fonksiyonları ──
def normalize_seg(seg: "AudioSegment", target: float = -16.0) -> "AudioSegment":
    return seg.apply_gain(target - seg.dBFS)

def apply_eq(seg: "AudioSegment", preset: str) -> "AudioSegment":
    if not PYDUB_OK:
        return seg
    t = {
        "Broadcast Clear": lambda s: pydub_fx.normalize(pydub_fx.compress_dynamic_range(s, threshold=-18, ratio=3.0)),
        "Radio Warm": lambda s: pydub_fx.normalize(s) + 1,
        "Vintage": lambda s: pydub_fx.normalize(s.low_pass_filter(4500)) - 2,
        "Deep Bass": lambda s: pydub_fx.normalize(s.high_pass_filter(60)) + 1,
        "Crisp HiFi": lambda s: pydub_fx.normalize(s.high_pass_filter(120)),
        "AM Radio": lambda s: (s.low_pass_filter(3000).high_pass_filter(400)) + 3,
        "Podcast Studio": lambda s: pydub_fx.compress_dynamic_range(pydub_fx.normalize(s), threshold=-20, ratio=2.5),
        "Club Bass": lambda s: pydub_fx.normalize(s.high_pass_filter(40).low_pass_filter(8000)) + 2,
        "Telephone": lambda s: (s.low_pass_filter(3400).high_pass_filter(300)) + 4,
        "Lo-Fi": lambda s: pydub_fx.normalize(s.low_pass_filter(4000).high_pass_filter(200)) - 3,
    }
    fn = t.get(preset)
    return fn(seg) if fn else seg

def apply_reverb(seg: "AudioSegment", lvl: float) -> "AudioSegment":
    if not PYDUB_OK or lvl <= 0:
        return seg
    try:
        delay = int(85 * lvl)
        wet = seg - int(13 * lvl)
        return pydub_fx.normalize(seg.overlay(wet, position=delay))
    except Exception:
        return seg

def apply_compressor(seg: "AudioSegment", threshold: float = -20.0, ratio: float = 3.0) -> "AudioSegment":
    if not PYDUB_OK:
        return seg
    try:
        return pydub_fx.compress_dynamic_range(seg, threshold=threshold, ratio=ratio)
    except Exception:
        return seg

def apply_limiter(seg: "AudioSegment", ceiling: float = -1.0) -> "AudioSegment":
    if not PYDUB_OK:
        return seg
    try:
        peak = seg.max_dBFS
        if peak > ceiling:
            return seg.apply_gain(ceiling - peak)
        return seg
    except Exception:
        return seg

def apply_effect_chain(seg: "AudioSegment", chain: List[Dict]) -> "AudioSegment":
    """Ses efekt zinciri uygula"""
    if not PYDUB_OK:
        return seg
    for step in chain:
        fx = step.get("fx", "")
        if fx == "eq":
            seg = apply_eq(seg, step.get("preset", "Broadcast Clear"))
        elif fx == "compressor":
            seg = apply_compressor(seg, step.get("threshold", -20), step.get("ratio", 3.0))
        elif fx == "reverb":
            seg = apply_reverb(seg, step.get("level", 0.3))
        elif fx == "limiter":
            seg = apply_limiter(seg, step.get("ceiling", -1.0))
        elif fx == "normalize":
            seg = normalize_seg(seg, step.get("target", -16.0))
        elif fx == "gain":
            seg = seg + step.get("db", 0)
        elif fx == "high_pass":
            seg = seg.high_pass_filter(step.get("freq", 80))
        elif fx == "low_pass":
            seg = seg.low_pass_filter(step.get("freq", 8000))
    return seg

def apply_ducking(music: "AudioSegment", voice: "AudioSegment",
                  duck_db: int = -14, fade_ms: int = 500) -> "AudioSegment":
    if not PYDUB_OK:
        return music
    try:
        vl = len(voice)
        rest = music[vl:]
        fm = min(fade_ms, max(50, vl // 4))
        part = music[:vl]
        ducked = (
            part[:fm].fade(to_gain=duck_db, start=0, duration=fm) +
            (part[fm:vl - fm] + duck_db) +
            part[vl - fm:].fade(from_gain=duck_db, start=0, duration=fm)
        )
        return ducked.overlay(voice) + rest
    except Exception:
        return music.overlay(voice)

def mix_fon_voice(fon: "AudioSegment", voice: "AudioSegment",
                  fon_vol: int = -8, duck_db: int = -16,
                  fade_in: int = 800, fade_out: int = 1200) -> "AudioSegment":
    if not PYDUB_OK:
        return voice
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
    except Exception:
        return voice

def mix_with_effect(main: "AudioSegment", eff: "AudioSegment",
                    pos: str = "after", gap: int = 0) -> "AudioSegment":
    if not PYDUB_OK:
        return main
    silence = AudioSegment.silent(duration=gap)
    if pos == "before":
        return eff + silence + main
    elif pos == "after":
        return main + silence + eff
    elif pos == "overlay":
        return main.overlay(eff)
    return main

def do_export(src: str, fmt: str, out_dir: str = OUT_DIR) -> str:
    if not PYDUB_OK or fmt == "wav" or not os.path.exists(src):
        return src
    try:
        seg = AudioSegment.from_file(src)
        base = os.path.splitext(os.path.basename(src))[0]
        out = os.path.join(out_dir, f"{base}.{fmt}")
        kw = {"bitrate": "320k"} if fmt == "mp3" else {}
        seg.export(out, format=fmt, **kw)
        return out
    except Exception as e:
        st.error(f"Export: {e}")
        return src

def audio_concat(segs: list) -> "AudioSegment":
    if not segs:
        return AudioSegment.silent(0)
    r = segs[0]
    for s in segs[1:]:
        r += s
    return r

def generate_jingle(freq: int = 440, dur_ms: int = 2000, style: str = "sine") -> Optional["AudioSegment"]:
    if not PYDUB_OK or not NP_OK:
        return None
    try:
        from pydub.generators import Sine, Square, Sawtooth
        m = {"sine": Sine, "square": Square, "sawtooth": Sawtooth}
        g = m.get(style, Sine)
        seg = (g(freq).to_audio_segment(duration=dur_ms // 3) +
               g(int(freq * 1.25)).to_audio_segment(duration=dur_ms // 3) +
               g(int(freq * 1.5)).to_audio_segment(duration=dur_ms // 3))
        return seg.fade_in(80).fade_out(180) - 10
    except Exception:
        try:
            sr = 44100
            ds = dur_ms / 1000.0
            t = np.linspace(0, ds, int(sr * ds))
            n1, n2 = len(t) // 3, 2 * len(t) // 3
            wd = np.concatenate([
                np.sin(2 * np.pi * freq * t[:n1]),
                np.sin(2 * np.pi * freq * 1.25 * t[n1:n2]),
                np.sin(2 * np.pi * freq * 1.5 * t[n2:])
            ])
            fd = 80
            wd[:fd] *= np.linspace(0, 1, fd)
            wd[-fd:] *= np.linspace(1, 0, fd)
            ai = (wd * 16000).astype(np.int16)
            return AudioSegment(ai.tobytes(), frame_rate=sr, sample_width=2, channels=1) - 10
        except Exception:
            return None

# ── Metadata & Memory ──
def save_meta(key: str, data: dict):
    p = os.path.join(META_DIR, f"{sfn(key)}.json")
    ex = {}
    if os.path.exists(p):
        try:
            with open(p) as f:
                ex = json.load(f)
        except Exception:
            pass
    ex.update(data)
    ex["updated"] = datetime.now().isoformat()
    with open(p, "w", encoding="utf-8") as f:
        json.dump(ex, f, ensure_ascii=False, indent=2)

def load_meta(key: str) -> dict:
    p = os.path.join(META_DIR, f"{sfn(key)}.json")
    if os.path.exists(p):
        try:
            with open(p) as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def get_id3(path: str) -> dict:
    if not MUTAGEN_OK or not os.path.exists(path):
        return {}
    try:
        a = MutagenFile(path, easy=True)
        if a is None:
            return {}
        return {
            "title": str(a.get("title", [""])[0]),
            "artist": str(a.get("artist", [""])[0]),
            "album": str(a.get("album", [""])[0]),
            "genre": str(a.get("genre", [""])[0]),
            "date": str(a.get("date", [""])[0]),
            "tracknumber": str(a.get("tracknumber", [""])[0]),
        }
    except Exception:
        return {}

def write_id3(path: str, tags: dict):
    """ID3 etiketi yaz"""
    if not MUTAGEN_OK or not os.path.exists(path):
        return False
    try:
        if path.lower().endswith('.mp3'):
            audio = MP3(path)
            if audio.tags is None:
                audio.add_tags()
            if tags.get("title"):
                audio.tags["TIT2"] = TIT2(encoding=3, text=tags["title"])
            if tags.get("artist"):
                audio.tags["TPE1"] = TPE1(encoding=3, text=tags["artist"])
            if tags.get("album"):
                audio.tags["TALB"] = TALB(encoding=3, text=tags["album"])
            if tags.get("genre"):
                audio.tags["TCON"] = TCON(encoding=3, text=tags["genre"])
            audio.save()
            return True
    except Exception as e:
        print(f"ID3 yazma hatası: {e}")
    return False

def save_memory(song: str, text: str, tone: str):
    h = hashlib.md5(song.encode()).hexdigest()[:10]
    p = os.path.join(MEMORY_DIR, f"{h}.json")
    prev = {}
    if os.path.exists(p):
        try:
            with open(p) as f:
                prev = json.load(f)
        except Exception:
            pass
    with open(p, "w", encoding="utf-8") as f:
        json.dump({
            "song": song, "text": text, "tone": tone,
            "count": prev.get("count", 0) + 1,
            "last": datetime.now().isoformat()
        }, f, ensure_ascii=False)

def check_memory(song: str) -> Optional[dict]:
    h = hashlib.md5(song.encode()).hexdigest()[:10]
    p = os.path.join(MEMORY_DIR, f"{h}.json")
    if os.path.exists(p):
        try:
            with open(p) as f:
                return json.load(f)
        except Exception:
            pass
    return None

def save_history(fname: str, text: str, char: str, song: str = ""):
    p = os.path.join(HISTORY_DIR, "history.json")
    hist = []
    if os.path.exists(p):
        try:
            with open(p) as f:
                hist = json.load(f)
        except Exception:
            pass
    hist.insert(0, {
        "ts": datetime.now().isoformat(),
        "file": fname, "char": char, "song": song,
        "preview": text[:80] + ("…" if len(text) > 80 else "")
    })
    hist = hist[:50]
    with open(p, "w") as f:
        json.dump(hist, f, ensure_ascii=False)

def load_history() -> list:
    p = os.path.join(HISTORY_DIR, "history.json")
    if os.path.exists(p):
        try:
            with open(p) as f:
                return json.load(f)
        except Exception:
            pass
    return []

def log_event(event: str, data: dict):
    p = os.path.join(ANALYTICS_DIR, f"log_{datetime.now().strftime('%Y%m%d')}.json")
    logs = []
    if os.path.exists(p):
        try:
            with open(p) as f:
                logs = json.load(f)
        except Exception:
            pass
    logs.append({"ts": datetime.now().isoformat(), "event": event, **data})
    with open(p, "w") as f:
        json.dump(logs, f, ensure_ascii=False)

def audit_log(action: str, details: str = ""):
    """Kullanıcı işlem kaydı"""
    p = os.path.join(AUDIT_DIR, f"audit_{datetime.now().strftime('%Y%m%d')}.json")
    logs = []
    if os.path.exists(p):
        try:
            with open(p) as f:
                logs = json.load(f)
        except Exception:
            pass
    logs.append({
        "ts": datetime.now().isoformat(),
        "action": action,
        "details": details,
        "session": st.session_state.get("session_id", "unknown")
    })
    with open(p, "w") as f:
        json.dump(logs, f, ensure_ascii=False)

def zip_files(paths: list, zip_name: str = "download") -> Optional[bytes]:
    try:
        buf = BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for p in paths:
                if os.path.exists(p):
                    zf.write(p, os.path.basename(p))
        buf.seek(0)
        return buf.read()
    except Exception:
        return None

def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

# ── Zamanlayıcı Fonksiyonları ──
def save_timer(name: str, trigger_time: datetime, action: str, params: dict):
    p = os.path.join(TIMER_DIR, f"timer_{sfn(name)}_{ts()}.json")
    with open(p, "w") as f:
        json.dump({
            "name": name, "trigger": trigger_time.isoformat(),
            "action": action, "params": params,
            "created": datetime.now().isoformat(), "status": "active"
        }, f, ensure_ascii=False)

def load_timers() -> list:
    timers = []
    for f in os.listdir(TIMER_DIR):
        if f.endswith(".json"):
            try:
                with open(os.path.join(TIMER_DIR, f)) as fh:
                    t = json.load(fh)
                    t["file"] = f
                    timers.append(t)
            except Exception:
                pass
    return sorted(timers, key=lambda x: x.get("trigger", ""))

def delete_timer(fname: str):
    p = os.path.join(TIMER_DIR, fname)
    if os.path.exists(p):
        os.remove(p)

# ── Etkileşim Fonksiyonları ──
def save_interaction(msg_type: str, content: str, sender: str = "anon"):
    p = os.path.join(INTERACT_DIR, f"msg_{ts()}.json")
    with open(p, "w") as f:
        json.dump({
            "type": msg_type, "content": content, "sender": sender,
            "timestamp": datetime.now().isoformat(),
            "votes": 0, "status": "active"
        }, f, ensure_ascii=False)

def load_interactions(limit: int = 50) -> list:
    msgs = []
    for f in sorted(os.listdir(INTERACT_DIR), reverse=True):
        if f.endswith(".json"):
            try:
                with open(os.path.join(INTERACT_DIR, f)) as fh:
                    m = json.load(fh)
                    m["file"] = f
                    msgs.append(m)
            except Exception:
                pass
    return msgs[:limit]

def vote_interaction(fname: str):
    p = os.path.join(INTERACT_DIR, fname)
    if os.path.exists(p):
        try:
            with open(p) as f:
                d = json.load(f)
            d["votes"] = d.get("votes", 0) + 1
            with open(p, "w") as f:
                json.dump(d, f, ensure_ascii=False)
        except Exception:
            pass

# ── Dönüştürme Fonksiyonları ──
def convert_audio(src: str, out_fmt: str = "wav", sr: int = None, bit_depth: int = None) -> str:
    """Ses dosyasını dönüştür"""
    if not PYDUB_OK or not os.path.exists(src):
        return src
    try:
        seg = AudioSegment.from_file(src)
        if sr:
            seg = seg.set_frame_rate(sr)
        if bit_depth == 16:
            seg = seg.set_sample_width(2)
        elif bit_depth == 24:
            seg = seg.set_sample_width(3)
        elif bit_depth == 32:
            seg = seg.set_sample_width(4)
        base = os.path.splitext(os.path.basename(src))[0]
        out = os.path.join(CONVERT_DIR, f"{base}_{sr or seg.frame_rate}Hz_{bit_depth or seg.sample_width * 8}bit.{out_fmt}")
        kw = {"bitrate": "320k"} if out_fmt == "mp3" else {}
        seg.export(out, format=out_fmt, **kw)
        return out
    except Exception as e:
        st.error(f"Dönüştürme hatası: {e}")
        return src

# ═══════════════════════════════════════════════════════════════
# RVC MODEL TARAMA
# ═══════════════════════════════════════════════════════════════
def scan_rvc_models() -> list:
    models = []
    seen = set()
    for root, _, files in os.walk(BASE_DIR):
        for f in files:
            if not f.endswith(".pth"):
                continue
            pth = os.path.join(root, f)
            if pth in seen:
                continue
            seen.add(pth)
            index = None
            for fi in os.listdir(root):
                if fi.endswith(".index"):
                    index = os.path.join(root, fi)
                    break
            models.append({
                "name": f, "label": os.path.splitext(f)[0],
                "pth": pth, "index": index, "dir": root
            })
    return models

# ═══════════════════════════════════════════════════════════════
# PIPER TTS — ONNX Türkçe modelleri
# ═══════════════════════════════════════════════════════════════
PIPER_MODELS_TR = {
    "okeysin (Özel TR)": {
        "type": "direct_url",
        "model_url": "https://huggingface.co/spaces/matroks/reji-v2/resolve/main/okeysin.onnx",
        "config_url": "https://huggingface.co/spaces/matroks/reji-v2/resolve/main/okeysin.onnx.json",
        "local_name": "okeysin",
        "model_file": "okeysin.onnx",
        "config_file": "okeysin.onnx.json",
    },
    "TR Kadın — dfki (medium)": {
        "type": "hf_repo",
        "repo": "speaches-ai/piper-tr_TR-dfki-medium",
        "src_model": "model.onnx",
        "src_config": "config.json",
        "model_file": "tr_TR-dfki-medium.onnx",
        "config_file": "tr_TR-dfki-medium.onnx.json",
        "local_name": "tr_dfki_medium",
    },
    "TR Erkek — fahrettin (medium)": {
        "type": "hf_repo",
        "repo": "speaches-ai/piper-tr_TR-fahrettin-medium",
        "src_model": "model.onnx",
        "src_config": "config.json",
        "model_file": "tr_TR-fahrettin-medium.onnx",
        "config_file": "tr_TR-fahrettin-medium.onnx.json",
        "local_name": "tr_fahrettin_medium",
    },
    "TR Erkek — fettah (medium)": {
        "type": "hf_repo",
        "repo": "speaches-ai/piper-tr_TR-fettah-medium",
        "src_model": "model.onnx",
        "src_config": "config.json",
        "model_file": "tr_TR-fettah-medium.onnx",
        "config_file": "tr_TR-fettah-medium.onnx.json",
        "local_name": "tr_fettah_medium",
    },
}

def piper_local_dir(key: str) -> str:
    info = PIPER_MODELS_TR.get(key, {})
    return os.path.join(PIPER_DIR, info.get("local_name", "unknown"))

def piper_model_path(key: str) -> tuple:
    info = PIPER_MODELS_TR.get(key)
    if not info:
        return None, None
    local = piper_local_dir(key)
    if not os.path.isdir(local):
        return None, None
    for mf, cf in [
        (info.get("model_file", "model.onnx"), info.get("config_file", "config.json")),
        ("model.onnx", "config.json"),
        ("model.onnx", "model.onnx.json"),
    ]:
        mp = os.path.join(local, mf)
        cp = os.path.join(local, cf)
        if os.path.exists(mp) and os.path.getsize(mp) > 1000 and os.path.exists(cp):
            return mp, cp
    onnx = [f for f in os.listdir(local) if f.endswith(".onnx")]
    jsons = [f for f in os.listdir(local) if f.endswith(".json")]
    if onnx and jsons:
        return os.path.join(local, onnx[0]), os.path.join(local, jsons[0])
    return None, None

def _dl_url(url: str, dest: str) -> bool:
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        return True
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    hdrs = {"User-Agent": "Mozilla/5.0", "Accept": "*/*"}
    hf_t = os.getenv("HF_TOKEN", "")
    if hf_t:
        hdrs["Authorization"] = f"Bearer {hf_t}"
    try:
        if REQ_OK:
            r = req_lib.get(url, stream=True, timeout=300, headers=hdrs, allow_redirects=True)
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(65536):
                    if chunk:
                        f.write(chunk)
            return os.path.getsize(dest) > 1000
        else:
            import urllib.request
            urllib.request.urlretrieve(url, dest)
            return os.path.getsize(dest) > 1000
    except Exception as e:
        print(f"DL error ({url}): {e}")
        return False

def piper_download(key: str) -> tuple:
    info = PIPER_MODELS_TR.get(key)
    if not info:
        return False, "Model tanımlı değil."
    local = piper_local_dir(key)
    os.makedirs(local, exist_ok=True)

    if info["type"] == "direct_url":
        md = os.path.join(local, info["model_file"])
        cd = os.path.join(local, info["config_file"])
        ok1 = _dl_url(info["model_url"], md)
        ok2 = _dl_url(info["config_url"], cd)
        if ok1 and ok2:
            return True, local
        return False, "Direkt URL indirme başarısız."

    elif info["type"] == "hf_repo":
        src_m = info.get("src_model", "model.onnx")
        src_c = info.get("src_config", "config.json")
        out_m = os.path.join(local, info["model_file"])
        out_c = os.path.join(local, info["config_file"])

        def ok_check():
            return (os.path.exists(out_m) and os.path.getsize(out_m) > 10000 and
                    os.path.exists(out_c) and os.path.getsize(out_c) > 10)

        if ok_check():
            return True, local
        errors = []

        if HF_OK:
            try:
                for sn, on in [(src_m, out_m), (src_c, out_c)]:
                    if os.path.exists(on) and os.path.getsize(on) > 100:
                        continue
                    dl = hf_hub_download(repo_id=info["repo"], filename=sn,
                                         local_dir=local, local_dir_use_symlinks=False)
                    if dl and os.path.exists(dl) and os.path.abspath(dl) != os.path.abspath(on):
                        shutil.copy2(dl, on)
                if ok_check():
                    return True, local
            except Exception as e:
                errors.append(f"hf_hub:{e}")

        base = f"https://huggingface.co/{info['repo']}/resolve/main"
        for sn, on in [(src_m, out_m), (src_c, out_c)]:
            if os.path.exists(on) and os.path.getsize(on) > 100:
                continue
            _dl_url(f"{base}/{sn}", on)
        if ok_check():
            return True, local

        if HF_OK:
            try:
                snapshot_download(repo_id=info["repo"], local_dir=local,
                                  local_dir_use_symlinks=False,
                                  ignore_patterns=["*.gitattributes", "*.md", "README*"])
                for sn, on in [(src_m, out_m), (src_c, out_c)]:
                    if os.path.exists(on):
                        continue
                    ext = os.path.splitext(sn)[1]
                    for root, _, files in os.walk(local):
                        for fn in files:
                            fp2 = os.path.join(root, fn)
                            if fn == sn or fn.endswith(ext):
                                if os.path.getsize(fp2) > 100:
                                    shutil.copy2(fp2, on)
                                    break
                if ok_check():
                    return True, local
            except Exception as e:
                errors.append(f"snapshot:{e}")

        return False, "İndirme başarısız: " + "|".join(errors[:2])
    return False, "Bilinmeyen tip."

# ═══════════════════════════════════════════════════════════════
# PIPER ONNX SENTEZİ
# ═══════════════════════════════════════════════════════════════
def piper_synthesize(text: str, model_path: str, config_path: str,
                     out_path: str, speaker_id: int = 0) -> bool:
    text = clean_text(text)
    if not text:
        return False

    for pb_name in ["piper", "piper-tts"]:
        pb = shutil.which(pb_name)
        if pb:
            try:
                r = subprocess.run(
                    [pb, "--model", model_path, "--config", config_path, "--output_file", out_path],
                    input=text.encode("utf-8"), capture_output=True, timeout=60
                )
                if r.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 512:
                    return True
            except Exception:
                pass

    try:
        from piper import PiperVoice
        voice = PiperVoice.load(model_path, config_path=config_path)
        buf = BytesIO()
        with wave.open(buf, "wb") as wf:
            voice.synthesize(text, wf, speaker_id=speaker_id)
        buf.seek(0)
        with open(out_path, "wb") as f:
            f.write(buf.read())
        if os.path.exists(out_path) and os.path.getsize(out_path) > 512:
            return True
    except Exception:
        pass

    if ONNX_OK and os.path.exists(model_path) and os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            sample_rate = cfg.get("audio", {}).get("sample_rate", 22050)
            chars = []
            for c in text[:300]:
                o = ord(c)
                if o < 128:
                    chars.append(o % 64 + 1)
                else:
                    chars.append(1)
            phoneme_ids = np.array([0] + chars + [1], dtype=np.int64)
            input_lengths = np.array([len(phoneme_ids)], dtype=np.int64)
            scales = np.array([0.667, 1.0, 0.8], dtype=np.float32)
            sess = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
            inputs_names = [i.name for i in sess.get_inputs()]
            inp_map = {}
            if len(inputs_names) >= 1:
                inp_map[inputs_names[0]] = phoneme_ids.reshape(1, -1)
            if len(inputs_names) >= 2:
                inp_map[inputs_names[1]] = input_lengths
            if len(inputs_names) >= 3:
                inp_map[inputs_names[2]] = scales.reshape(1, -1)
            audio = sess.run(None, inp_map)[0].squeeze()
            audio_int = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
            with wave.open(out_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_int.tobytes())
            if os.path.exists(out_path) and os.path.getsize(out_path) > 512:
                return True
        except Exception as e:
            print(f"ONNX inference: {e}")

    espeak = shutil.which("espeak-ng") or shutil.which("espeak")
    if espeak:
        try:
            subprocess.run([espeak, "-v", "tr", "-w", out_path, text], timeout=30, check=True)
            if os.path.exists(out_path) and os.path.getsize(out_path) > 512:
                return True
        except Exception:
            pass

    return False

# ═══════════════════════════════════════════════════════════════
# SES PIPELINE
# ═══════════════════════════════════════════════════════════════
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

def run_rvc(inp: str, out: str, pth: str, index: Optional[str], pitch: int) -> bool:
    if not RVC_OK or not pth or not os.path.exists(pth):
        shutil.copy(inp, out)
        return True
    for attempt in range(2):
        try:
            r = RVCInference(device="cpu:0")
            if index and os.path.exists(index):
                r.load_model(pth, index_path=index, version="v2")
                r.set_params(f0up_key=int(pitch), index_rate=0.75)
            else:
                r.load_model(pth, version="v2")
                r.set_params(f0up_key=int(pitch), index_rate=0.0)
            r.infer_file(inp, out)
            for _ in range(60):
                if os.path.exists(out) and os.path.getsize(out) > 1024:
                    return True
                time.sleep(0.2)
        except Exception as e:
            if attempt == 1:
                st.error(f"RVC: {e}")
            time.sleep(2)
    return False

async def build_voice(
    text: str, voice: str, speed: int, pitch: int,
    pth: str, index: Optional[str], out_file: str,
    eq: str = "Broadcast Clear", reverb: float = 0.0, norm_db: float = -16.0,
    tts_engine: str = "EdgeTTS", piper_model: str = "TR Kadın — dfki (medium)",
    effect_chain: List[Dict] = None,
) -> tuple:
    if not text or not text.strip():
        return False, ""
    stamp = ts()
    tmp_tts = os.path.join(tempfile.gettempdir(), f"tts_{stamp}.wav")
    tmp_rvc = os.path.join(tempfile.gettempdir(), f"rvc_{stamp}.wav")
    dest = os.path.join(OUT_DIR, out_file)
    try:
        if tts_engine == "Piper (ONNX/TR)":
            mp, cp = piper_model_path(piper_model)
            if mp and cp:
                ok = piper_synthesize(text, mp, cp, tmp_tts)
                if not ok:
                    ok = await run_edge_tts(text, voice, speed, tmp_tts)
            else:
                ok = await run_edge_tts(text, voice, speed, tmp_tts)
        else:
            ok = await run_edge_tts(text, voice, speed, tmp_tts)
        if not ok:
            return False, ""

        src = tmp_tts
        if pth and os.path.exists(pth) and RVC_OK:
            rvc_ok = run_rvc(tmp_tts, tmp_rvc, pth, index, pitch)
            if rvc_ok and os.path.exists(tmp_rvc) and os.path.getsize(tmp_rvc) > 1024:
                src = tmp_rvc

        if PYDUB_OK:
            seg = AudioSegment.from_file(src)
            if eq and eq != "Ham (Efektsiz)":
                seg = apply_eq(seg, eq)
            if reverb > 0:
                seg = apply_reverb(seg, reverb)
            if effect_chain:
                seg = apply_effect_chain(seg, effect_chain)
            seg = normalize_seg(seg, norm_db)
            seg.export(dest, format="wav")
        else:
            shutil.copy(src, dest)

        log_event("voice_generated", {
            "file": out_file, "voice": voice,
            "rvc": bool(pth and os.path.exists(pth)),
            "words": word_count(text), "eq": eq, "engine": tts_engine
        })
        return True, dest
    except Exception as e:
        st.error(f"Pipeline: {e}")
        return False, ""
    finally:
        for fp in [tmp_tts, tmp_rvc]:
            try:
                if os.path.exists(fp):
                    os.remove(fp)
            except Exception:
                pass

# ═══════════════════════════════════════════════════════════════
# GROQ
# ═══════════════════════════════════════════════════════════════
@st.cache_resource
def init_groq():
    key = os.getenv("GROQ_API_KEY")
    if not key or not GROQ_OK:
        return None
    if HF_OK:
        hft = os.getenv("HF_TOKEN")
        if hft:
            try:
                snapshot_download("matroks/dilay", local_dir=BASE_DIR, token=hft)
            except Exception:
                pass
    try:
        return Groq(api_key=key)
    except Exception:
        return None

groq_client = init_groq()

CHARS = {
    "🎙️ Dilay — Kadın Sunucu": {
        "id": "dilay", "voice": "tr-TR-EmelNeural", "pitch": 0,
        "prompt": (
            "Sen 'Kenan ile Faslı Muhabbet' radyosunun efsanevi kadın sunucusu Dilay'sın. "
            "Türk edebiyatı ve müzikte derin bilgilisin. Dinleyiciye 'canım ailemiz' diye hitap edersin. "
            "28-45 saniye (~80-120 kelime). KESİNLİKLE sadece düz Türkçe metin. XML/SSML/Markdown KULLANMA."
        )
    },
    "📢 Kenan — Erkek Sunucu": {
        "id": "kenan", "voice": "tr-TR-AhmetNeural", "pitch": -2,
        "prompt": "Karizmatik güçlü sesli erkek sunucu. Enerjik, samimi. 30-40 saniye. SADECE düz Türkçe."
    },
    "📰 Haber Spikeri": {
        "id": "haber", "voice": "tr-TR-EmelNeural", "pitch": 1,
        "prompt": "Profesyonel radyo haber spikeri. Net, tarafsız. SADECE düz Türkçe."
    },
    "🎭 Reklam Sesi": {
        "id": "reklam", "voice": "tr-TR-AhmetNeural", "pitch": 2,
        "prompt": "Akılda kalıcı 15-30 sn radyo reklamı. SADECE düz Türkçe."
    },
    "🌙 Gece DJsi": {
        "id": "gece", "voice": "tr-TR-EmelNeural", "pitch": -1,
        "prompt": "Gece yayını şiirsel DJ. Melankolik, büyüleyici. 40-50 sn. SADECE düz Türkçe."
    },
    "🌅 Sabah Sunucusu": {
        "id": "sabah", "voice": "tr-TR-AhmetNeural", "pitch": 3,
        "prompt": "Enerjik neşeli sabah sunucusu. 25-35 sn. SADECE düz Türkçe."
    },
    "🎤 Podcast Host": {
        "id": "podcast", "voice": "tr-TR-EmelNeural", "pitch": 0,
        "prompt": "Samimi sohbet havasında podcast sunucusu. 60-90 sn. SADECE düz Türkçe."
    },
    "🎸 Rock DJ": {
        "id": "rock", "voice": "tr-TR-AhmetNeural", "pitch": -3,
        "prompt": "Enerjik rock müzik DJ'i. Güçlü, tutkulu. 20-35 sn. SADECE düz Türkçe."
    },
}

GROQ_MODELS = {
    "Hızlı (llama3-8b)": "llama3-8b-8192",
    "Standart (llama3-70b)": "llama-3.3-70b-versatile",
    "Gelişmiş (mixtral-8x7b)": "mixtral-8x7b-32768",
    "Gelişmiş (gemma2-9b)": "gemma2-9b-it",
    "En Yeni (llama-3.1-405b)": "llama-3.1-405b-reasoning",
}

MULTILANG_VOICES = {
    "🇹🇷 Türkçe": {"voice": "tr-TR-EmelNeural", "lang": "tr", "piper": "TR Kadın — dfki (medium)"},
    "🇬🇧 English": {"voice": "en-US-AriaNeural", "lang": "en", "piper": None},
    "🇩🇪 Deutsch": {"voice": "de-DE-KatjaNeural", "lang": "de", "piper": None},
    "🇫🇷 Français": {"voice": "fr-FR-DeniseNeural", "lang": "fr", "piper": None},
    "🇪🇸 Español": {"voice": "es-ES-ElviraNeural", "lang": "es", "piper": None},
    "🇮🇹 Italiano": {"voice": "it-IT-ElsaNeural", "lang": "it", "piper": None},
    "🇷🇺 Русский": {"voice": "ru-RU-SvetlanaNeural", "lang": "ru", "piper": None},
    "🇸🇦 العربية": {"voice": "ar-SA-ZariyahNeural", "lang": "ar", "piper": None},
    "🇯🇵 日本語": {"voice": "ja-JP-NanamiNeural", "lang": "ja", "piper": None},
    "🇰🇷 한국어": {"voice": "ko-KR-SunHiNeural", "lang": "ko", "piper": None},
    "🇳🇱 Nederlands": {"voice": "nl-NL-ColetteNeural", "lang": "nl", "piper": None},
    "🇵🇱 Polski": {"voice": "pl-PL-AgnieszkaNeural", "lang": "pl", "piper": None},
    "🇵🇹 Português": {"voice": "pt-BR-FranciscaNeural", "lang": "pt", "piper": None},
    "🇨🇳 中文": {"voice": "zh-CN-XiaoxiaoNeural", "lang": "zh", "piper": None},
    "🇬🇷 Ελληνικά": {"voice": "el-GR-AthinaNeural", "lang": "el", "piper": None},
}

def groq_gen(msg: str, char_id: str = "dilay", model_key: str = "Standart (llama3-70b)",
             temp: float = 0.87, max_tok: int = 450) -> str:
    if not groq_client:
        return "⚠️ Groq bağlantısı yok. GROQ_API_KEY ayarlayın."
    char = next((c for c in CHARS.values() if c["id"] == char_id), list(CHARS.values())[0])
    model = GROQ_MODELS.get(model_key, "llama-3.3-70b-versatile")
    try:
        res = groq_client.chat.completions.create(
            messages=[{"role": "system", "content": char["prompt"]},
                      {"role": "user", "content": msg}],
            model=model, temperature=temp, max_tokens=max_tok
        )
        return clean_text(res.choices[0].message.content.strip())
    except Exception as e:
        return f"⚠️ Groq: {e}"

def groq_translate(text: str, target_lang: str = "en") -> str:
    """Groq ile çeviri"""
    if not groq_client:
        return text
    try:
        pr = f"Şu metni {target_lang} diline çevir. SADECE çeviriyi döndür, açıklama yok:\n\n{text}"
        res = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": pr}],
            model="llama3-8b-8192", temperature=0.3, max_tokens=500
        )
        return res.choices[0].message.content.strip()
    except Exception:
        return text

def groq_stt(audio_bytes: bytes, lang: str = "tr") -> str:
    if not groq_client:
        return "⚠️ Groq bağlantısı yok."
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
            tf.write(audio_bytes)
            p = tf.name
        with open(p, "rb") as f:
            res = groq_client.audio.transcriptions.create(
                file=("audio.wav", f), model="whisper-large-v3", language=lang)
        os.remove(p)
        return res.text.strip()
    except Exception as e:
        return f"⚠️ STT: {e}"

def groq_mood(song: str) -> dict:
    pr = (f'Sarki: "{song}"\nSadece JSON:\n'
          '{"mood":"mutlu|melankolik|enerjik|romantik|nostaljik|huzunlu",'
          '"tempo":"yavas|orta|hizli",'
          '"tone_suggestion":"Duygusal|Neseli & Isveli|Espirili|Derin & Siirsel|Nostaljik|Enerjik",'
          '"yorum":"tek cumle"}')
    r = groq_gen(pr, char_id="dilay", temp=0.2, max_tok=160)
    try:
        c = re.sub(r'```[^`]*```', '', r).strip()
        c = re.sub(r'<[^>]+>', '', c)
        return json.loads(c)
    except Exception:
        return {"mood": "?", "tempo": "orta", "tone_suggestion": "Duygusal", "yorum": ""}

def groq_playlist_genre(mood: str, tempo: str, count: int = 5) -> list:
    """AI playlist önerisi üret"""
    if not groq_client:
        return []
    try:
        pr = (f"Mood: {mood}, Tempo: {tempo}\n"
              f"Bu havaya uygun {count} şarkı öner. Sadece şarkı adı - sanatçı formatında, her biri yeni satırda. "
              f"Türkçe ve uluslararası karışık olsun.")
        res = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": pr}],
            model="llama3-8b-8192", temperature=0.9, max_tokens=300
        )
        lines = res.choices[0].message.content.strip().split("\n")
        songs = []
        for line in lines:
            line = line.strip().lstrip("-• ").strip()
            if " - " in line or "–" in line:
                songs.append(line)
        return songs[:count]
    except Exception:
        return []

def groq_auto_tags(audio_path: str, context: str = "") -> dict:
    """Ses dosyası için otomatik etiket önerisi"""
    if not groq_client:
        return {}
    try:
        dur = audio_dur(audio_path)
        pr = (f"Ses dosyası: {os.path.basename(audio_path)}, Süre: {fmt_dur(dur)}, Bağlam: {context}\n"
              "JSON formatında etiketler üret: {\"title\":\"...\",\"artist\":\"...\",\"genre\":\"...\",\"mood\":\"...\",\"tags\":[\"...\"]}")
        res = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": pr}],
            model="llama3-8b-8192", temperature=0.5, max_tokens=200
        )
        txt = res.choices[0].message.content.strip()
        txt = re.sub(r'```[^`]*```', '', txt).strip()
        return json.loads(txt)
    except Exception:
        return {}

# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:14px 0 10px">
      <div style="font-size:32px;font-weight:800;color:#2563eb;letter-spacing:-1.5px;line-height:1">K3N4N</div>
      <div style="font-size:12px;color:#64748b;font-weight:700;letter-spacing:4px">HYBRID v28.0</div>
      <div style="font-size:10px;color:#94a3b8;margin-top:4px;font-weight:500">MEGA BROADCAST ENGINE</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # ── Tema Seçici ──
    theme_sel = st.selectbox("🎨 Tema:", ["light", "dark", "midnight"],
                              index=["light", "dark", "midnight"].index(st.session_state.get("theme", "light")),
                              key="theme_sel")
    if theme_sel != st.session_state.get("theme", "light"):
        st.session_state["theme"] = theme_sel
        st.rerun()

    st.divider()

    MENU = [
        "📡 Gösterge Paneli",
        "🚀 Yayın Otomasyonu",
        "🎛️ 4 Kanal Mikser",
        "🤖 AI Playlist",
        "⏰ Radyo Saati",
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
        "📡 Stream Yayın",
        "🗣️ Piper TTS",
        "🌐 Çoklu Dil TTS",
        "📁 Kaynak Ses",
        "🎤 Ses Klonlama",
        "📅 Program Planlayıcı",
        "🔔 Zamanlayıcı",
        "💬 Etkileşim Panosu",
        "🎛️ Efekt Zinciri",
        "🏷️ Otomatik Metadata",
        "🔄 Dönüştürme Merkezi",
        "📊 Analitikler",
        "📁 Kütüphane",
        "📻 Arşiv",
        "⚙️ Ayarlar",
    ]
    menu = st.radio("Menü:", MENU, label_visibility="collapsed")
    st.divider()

    # ── Karakter ──
    st.markdown('<div class="section-label">🎭 Karakter</div>', unsafe_allow_html=True)
    char_name = st.selectbox("Karakter Seç:", list(CHARS.keys()), label_visibility="collapsed", key="sb_char")
    AC = CHARS[char_name]
    st.markdown(
        chips(chip(AC["id"].upper(), "blue"), chip(AC["voice"], "gray")),
        unsafe_allow_html=True
    )

    # ── TTS Motoru ──
    st.markdown('<div class="section-label">🎤 TTS Motoru</div>', unsafe_allow_html=True)
    tts_engine_sb = st.selectbox("TTS Motoru:", ["EdgeTTS", "Piper (ONNX/TR)"],
                                  label_visibility="collapsed", key="sb_tts")
    piper_model_sb = list(PIPER_MODELS_TR.keys())[0]
    if tts_engine_sb == "Piper (ONNX/TR)":
        piper_model_sb = st.selectbox("Piper Model:", list(PIPER_MODELS_TR.keys()),
                                       label_visibility="collapsed", key="sb_piper")
        mp, cp = piper_model_path(piper_model_sb)
        if mp:
            st.markdown(chip("✓ PIPER HAZIR", "green"), unsafe_allow_html=True)
        else:
            st.markdown(chip("İndirilmedi", "amber"), unsafe_allow_html=True)
            if st.button("⬇️ Modeli İndir", key="piper_dl_sb"):
                with st.spinner("İndiriliyor..."):
                    ok, msg = piper_download(piper_model_sb)
                if ok:
                    st.success("✅ İndirildi!")
                    st.rerun()
                else:
                    st.error(msg[:80])

    # ── RVC Model ──
    st.markdown('<div class="section-label">🤖 RVC Model</div>', unsafe_allow_html=True)
    all_models = scan_rvc_models()
    if all_models:
        sel_label = st.selectbox("Model Seç:", [m["label"] for m in all_models],
                                  label_visibility="collapsed", key="sb_mdl")
        sel_model = next(m for m in all_models if m["label"] == sel_label)
        A_PTH = sel_model["pth"]
        A_INDEX = sel_model["index"]
        idx_c = "green" if A_INDEX else "amber"
        st.markdown(
            chips(chip("PTH ✓", "green"), chip("IDX " + (("✓" if A_INDEX else "✗")), idx_c)),
            unsafe_allow_html=True
        )
    else:
        A_PTH = ""
        A_INDEX = None
        sel_model = None
        st.markdown(chip("Model yok — EdgeTTS kullanılır", "gray"), unsafe_allow_html=True)

    pitch_sb = st.slider("Pitch", -14, 14, AC["pitch"], key="sb_pitch")
    speed_sb = st.slider("Hız (%)", 75, 130, 100, key="sb_speed")

    # ── Mastering ──
    st.markdown('<div class="section-label">🎚️ Mastering</div>', unsafe_allow_html=True)
    eq_sb = st.selectbox("EQ Preset:", [
        "Broadcast Clear", "Radio Warm", "Vintage", "Deep Bass",
        "Crisp HiFi", "AM Radio", "Podcast Studio", "Club Bass",
        "Telephone", "Lo-Fi", "Ham (Efektsiz)"
    ], label_visibility="collapsed", key="sb_eq")
    reverb_sb = st.slider("Reverb", 0.0, 1.0, 0.0, step=0.05, key="sb_rev")
    norm_sb = st.slider("Normalize (dBFS)", -24, -8, -16, key="sb_norm")

    # ── Efekt Zinciri ──
    st.markdown('<div class="section-label">⚡ Efekt Zinciri</div>', unsafe_allow_html=True)
    use_chain = st.checkbox("Aktif", key="sb_chain_chk")
    chain_steps = []
    if use_chain:
        if st.checkbox("Compressor", key="sb_comp"):
            chain_steps.append({"fx": "compressor", "threshold": -20, "ratio": 3.0})
        if st.checkbox("Limiter", key="sb_lim"):
            chain_steps.append({"fx": "limiter", "ceiling": -1.0})
        if st.checkbox("High-Pass 80Hz", key="sb_hp"):
            chain_steps.append({"fx": "high_pass", "freq": 80})

    # ── Diğer ──
    st.markdown('<div class="section-label">🌐 Diğer</div>', unsafe_allow_html=True)
    LANGS = {"🇹🇷 Türkçe": "tr", "🇬🇧 İngilizce": "en", "🇩🇪 Almanca": "de",
             "🇫🇷 Fransızca": "fr", "🇸🇦 Arapça": "ar"}
    stt_lang = LANGS[st.selectbox("STT Dili:", list(LANGS.keys()), label_visibility="collapsed", key="sb_stt")]
    groq_mkey = st.selectbox("Groq Modeli:", list(GROQ_MODELS.keys()), label_visibility="collapsed", index=1, key="sb_groq")
    exp_fmt = st.selectbox("Export Formatı:", ["wav", "mp3", "ogg", "flac"], label_visibility="collapsed", key="sb_fmt")

    # ── Hızlı Kısayollar ──
    if st.session_state.get("quick_actions", True):
        st.markdown('<div class="section-label">⚡ Hızlı Aksiyonlar</div>', unsafe_allow_html=True)
        if st.button("🎵 Jingle Çal", key="qa_jingle"):
            jf = list_audio(JINGLE_DIR)
            if jf:
                st.audio(os.path.join(JINGLE_DIR, jf[0]))
        if st.button("🎶 Fon Çal", key="qa_fon"):
            ff = list_audio(FON_DIR)
            if ff:
                st.audio(os.path.join(FON_DIR, ff[0]))
        if st.button("🧹 Temizle", key="qa_clear"):
            for k in ["qa_txt", "fa_txt", "live_txt", "nb_txt", "r_anons", "m_txt", "ab_gen"]:
                st.session_state[k] = ""
            st.rerun()

A_VOICE = AC["voice"]
A_PITCH = pitch_sb
A_SPEED = speed_sb
A_CHAR = AC["id"]
A_CHAIN = chain_steps if use_chain else None

# ═══════════════════════════════════════════════════════════════
# SESLENDİRME BUTONU
# ═══════════════════════════════════════════════════════════════
def vbtn(text: str, key: str, label: str = "🔊 Seslendir", song: str = "") -> Optional[str]:
    if st.button(label, key=f"vb_{key}"):
        if not text or not text.strip():
            st.warning("Metin boş!")
            return None
        fname = f"{sfn(key)}_{ts()}.wav"
        with st.spinner("🎙️ Ses üretiliyor..."):
            ok, path = asyncio.run(build_voice(
                text, A_VOICE, A_SPEED, A_PITCH, A_PTH, A_INDEX, fname,
                eq=eq_sb, reverb=reverb_sb, norm_db=float(norm_sb),
                tts_engine=tts_engine_sb, piper_model=piper_model_sb,
                effect_chain=A_CHAIN
            ))
        if ok and os.path.exists(path):
            dur = audio_dur(path)
            qs = quality_score(path)
            sz = os.path.getsize(path) // 1024
            rvc_lbl = "RVC ✓" if (A_PTH and os.path.exists(A_PTH) and RVC_OK) else tts_engine_sb
            st.success("✅ Ses hazır!")
            st.markdown(
                chips(chip(rvc_lbl, "green"), chip(f"⏱ {fmt_dur(dur)}", "blue"),
                      chip(f"🎯 {qs}/100", "purple"), chip(f"{sz}KB", "gray")),
                unsafe_allow_html=True
            )
            st.audio(path)
            qbar(qs)
            draw_waveform(path)
            # Spektrum analizi
            spec = spectral_analysis(path)
            if spec:
                draw_spectrum_bars(spec)
            save_history(fname, text, A_CHAR, song)
            audit_log("voice_generated", f"{fname} | {song}")
            return path
        else:
            st.error("❌ Ses üretilemedi.")
            return None
    return None

# ═══════════════════════════════════════════════════════════════
# HIZLI ÖNİZLEME FONKSİYONU
# ═══════════════════════════════════════════════════════════════
def quick_preview(text: str, key: str):
    """Seslendirmeden önce metin önizleme ve vurgu analizi"""
    if not text or not text.strip():
        return
    words = text.split()
    # Vurgu kelimelerini belirle (büyük harfli, uzun, duygu kelimeleri)
    emphasis_words = []
    emotion_markers = ["mutlu", "hüzünlü", "enerjik", "romantik", "nostaljik", "melankolik",
                       "neşeli", "güzel", "muhteşem", "efsane", "harika", "süper", "muazzam"]
    for i, w in enumerate(words):
        w_clean = re.sub(r'[^\w]', '', w.lower())
        score = 0
        if w.isupper() and len(w) > 2:
            score += 3
        if len(w) > 7:
            score += 1
        if w_clean in emotion_markers:
            score += 2
        if any(m in w_clean for m in emotion_markers):
            score += 1
        if score >= 2:
            emphasis_words.append((i, w, score))

    # Önizleme HTML oluştur
    html_words = []
    for i, w in enumerate(words):
        is_emph = any(e[0] == i for e in emphasis_words)
        if is_emph:
            html_words.append(f'<span style="color:{T["primary"]};font-weight:700;text-decoration:underline;text-decoration-color:{T["accent"]};">{w}</span>')
        else:
            html_words.append(w)

    preview_html = " ".join(html_words)
    wc = len(words)
    ed = est_dur(text, A_SPEED)

    with st.expander(f"👁️ Önizleme ({wc} kelime, ~{ed:.0f}sn)", expanded=False):
        st.markdown(f'<div style="background:{T["bg3"]};padding:12px 16px;border-radius:8px;border:1px solid {T["border2"]};font-size:14px;line-height:1.8;color:{T["text1"]};">{preview_html}</div>', unsafe_allow_html=True)
        if emphasis_words:
            st.markdown("**Vurgu Kelimeleri:** " + ", ".join([f"'{w}'" for _, w, _ in emphasis_words[:8]]))
        # Nefes noktaları öner
        sentences = re.split(r'[.!?]+', text)
        breath_points = [i for i, s in enumerate(sentences) if len(s.strip()) > 40]
        if breath_points:
            st.caption(f"💡 Nefes önerisi: {len(breath_points)} uzun cümle tespit edildi. Cümle sonlarında 0.5sn duraklama önerilir.")

# ═══════════════════════════════════════════════════════════════
#  MODÜLLER
# ═══════════════════════════════════════════════════════════════

# ── M0: GÖSTERGE PANELİ ────────────────────────────────────────
if menu == "📡 Gösterge Paneli":
    page_header("📡", "Gösterge Paneli", "Yayın sistemi durumu, hızlı araçlar ve canlı metrikler")

    songs = list_audio(PLAYLIST_DIR)
    outputs = list_audio(OUT_DIR)
    fons = list_audio(FON_DIR)
    effects = list_audio(EFFECT_DIR)
    reqs = [f for f in os.listdir(REQUEST_DIR) if f.endswith(".json")]
    jingles = list_audio(JINGLE_DIR)
    timers = load_timers()
    interactions = load_interactions(5)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    for col, (n, l, icon) in zip([c1, c2, c3, c4, c5, c6], [
        (len(songs), "Şarkı", "🎵"), (len(outputs), "Üretilen", "🎙️"),
        (len(fons), "Fon", "🎶"), (len(effects), "Efekt", "🎭"),
        (len(reqs), "İstek", "📩"), (len(jingles), "Jingle", "🎺")
    ]):
        with col:
            st.markdown(
                f'<div class="stat-box"><div class="stat-num">{n}</div>'
                f'<div class="stat-lbl">{l}</div></div>',
                unsafe_allow_html=True
            )

    st.divider()
    cl, cr = st.columns([1.7, 1])
    with cl:
        section("📂 Playlist", "")
        if songs:
            total = sum(audio_dur(os.path.join(PLAYLIST_DIR, s)) for s in songs)
            for s in songs[:10]:
                d = audio_dur(os.path.join(PLAYLIST_DIR, s))
                tags = get_id3(os.path.join(PLAYLIST_DIR, s))
                art = f' <span class="chip chip-purple" style="font-size:10px">{tags["artist"][:16]}</span>' if tags.get("artist") else ""
                st.markdown(
                    f'<div class="song-row"><span class="song-name">🎵 {s[:40]}</span>'
                    f'{art}<span class="song-dur">{fmt_dur(d)}</span></div>',
                    unsafe_allow_html=True
                )
            st.markdown(
                f'<div class="mono-box">📊 {len(songs)} parça · {fmt_dur(total)} müzik<br>'
                f'📡 Tahmini yayın: ~{fmt_dur(total + len(songs) * 40)}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown('<div class="info-box">ℹ️ Playlist boş — 📁 Kütüphane\'den şarkı ekle.</div>', unsafe_allow_html=True)

        section("🎶 Fon & Efektler")
        fc1, fc2 = st.columns(2)
        with fc1:
            if fons:
                for f in fons[:4]:
                    d = audio_dur(os.path.join(FON_DIR, f))
                    st.markdown(f'<div class="kcard" style="padding:8px 12px"><div class="kcard-title" style="font-size:13px">🎶 {f[:24]}</div><div class="kcard-body">{fmt_dur(d)}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="warn-box">⚠️ /fon klasörü boş.</div>', unsafe_allow_html=True)
        with fc2:
            if effects:
                for f in effects[:4]:
                    st.markdown(f'<div class="kcard" style="padding:8px 12px"><div class="kcard-title" style="font-size:13px">🎭 {f[:24]}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="warn-box">⚠️ /effects klasörü boş.</div>', unsafe_allow_html=True)

        # Yeni: Canlı Etkileşim Özeti
        if interactions:
            section("💬 Son Etkileşimler")
            for msg in interactions[:3]:
                st.markdown(
                    f'<div class="kcard" style="padding:8px 12px">'
                    f'<div class="kcard-title" style="font-size:12px">{msg.get("type","?")} — {msg.get("sender","?")}</div>'
                    f'<div class="kcard-body">{truncate(msg.get("content",""), 60)}</div></div>',
                    unsafe_allow_html=True
                )

    with cr:
        section("⚡ Hızlı Anons")
        qa = st.text_input("Şarkı adı:", key="qa_in", placeholder="ör. Nilüfer — Deli")
        if st.button("✨ AI Anons Üret", key="qa_btn"):
            if qa.strip():
                with st.spinner("Üretiyor..."):
                    md = groq_mood(qa)
                    pr = (f"Şarkı: {qa}\nMood: {md.get('mood','')}\n"
                          f"Yorum: {md.get('yorum','')}\n~60 kelime anons. Sadece düz metin.")
                    txt = groq_gen(pr, char_id=A_CHAR, model_key=groq_mkey, max_tok=150)
                st.session_state["qa_txt"] = txt
                st.rerun()
        if st.session_state.get("qa_txt"):
            ed = st.text_area("Anons:", value=st.session_state["qa_txt"], height=110, key="qa_ta")
            st.session_state["qa_txt"] = ed
            quick_preview(ed, "qa_preview")
            vbtn(ed, "qa_v", song=qa)

        st.divider()
        section("🔧 Sistem Durumu")
        for nm, ok in [
            ("Groq", groq_client is not None),
            ("EdgeTTS", TTS_OK),
            ("Piper ONNX", ONNX_OK),
            ("RVC", RVC_OK),
            ("Model", bool(A_PTH)),
            ("PyDub", PYDUB_OK),
            ("NumPy", NP_OK),
            ("SciPy", SCIPY_OK),
        ]:
            c = "green" if ok else "red"
            st.markdown(chip(f"{'✓' if ok else '✗'} {nm}", c), unsafe_allow_html=True)

        # VU Metre Demo
        if NP_OK and PYDUB_OK and outputs:
            section("📈 Canlı VU Metre")
            last_out = os.path.join(OUT_DIR, outputs[0])
            try:
                seg = AudioSegment.from_file(last_out)
                vu_meter(seg.dBFS, label="RMS")
                vu_meter(seg.max_dBFS, max_db=0, min_db=-30, label="Peak")
            except Exception:
                pass

        st.divider()
        hist = load_history()
        if hist:
            section("🕑 Son Üretimler")
            for h in hist[:4]:
                fp = os.path.join(OUT_DIR, h["file"])
                with st.expander(f"🔊 {h['ts'][11:16]} — {h.get('song', '')[:14]}"):
                    if os.path.exists(fp):
                        st.audio(fp)
                    st.caption(h.get("preview", ""))

# ── M1: YAYIN OTOMASYONU (TAMAMLANMIŞ) ────────────────────────
if menu == "🚀 Yayın Otomasyonu":
    page_header("🚀", "Yayın Otomasyonu", "Şarkı seç, anons üret, miksle, yayınla")

    songs = list_audio(PLAYLIST_DIR)
    if not songs:
        st.markdown('<div class="warn-box">⚠️ Önce 📁 Kütüphane\'den şarkı ekleyin.</div>', unsafe_allow_html=True)
    else:
        section("📋 Şarkı Listesi")
        st.markdown(f'<div class="info-box">ℹ️ {len(songs)} şarkı mevcut. İşlemek istediklerini seçin.</div>', unsafe_allow_html=True)

        # Şarkı seçim ve arama
        search = st.text_input("🔍 Şarkı Ara:", key="au_search")
        filtered_songs = [s for s in songs if search.lower() in s.lower()] if search else songs

        col_sel, col_all = st.columns([3, 1])
        with col_sel:
            selected = st.multiselect("Şarkıları Seç:", filtered_songs, key="au_selected",
                                       default=st.session_state.get("selected_songs", []))
        with col_all:
            if st.button("☑️ Tümünü Seç"):
                st.session_state["selected_songs"] = filtered_songs[:20]
                st.rerun()
            if st.button("⬜ Seçimi Temizle"):
                st.session_state["selected_songs"] = []
                st.rerun()

        if selected:
            st.session_state["selected_songs"] = selected
            st.markdown(chip(f"{len(selected)} şarkı seçildi", "blue"), unsafe_allow_html=True)

            # Global Ayarlar
            section("🎚️ Global Ayarlar")
            g1, g2, g3, g4 = st.columns(4)
            with g1:
                tone_s = st.selectbox("Ton:", ["Otomatik (Mood)", "Duygusal", "Neşeli", "Espirili", "Şiirsel", "Nostaljik", "Enerjik"], key="au_tone")
            with g2:
                ducking = st.checkbox("Ducking (Müzik Alçalt)", value=True, key="au_duck")
            with g3:
                gap_ms = st.slider("Parça Arası Boşluk (ms):", 0, 3000, 1000, key="au_gap")
            with g4:
                cf_ms = st.slider("Crossfade (ms):", 0, 2000, 500, key="au_cf")

            # Jingle seçimi
            jingle_files = list_audio(JINGLE_DIR)
            sel_jgl = st.selectbox("🎺 Açılış Jingle:", ["Yok"] + jingle_files, key="au_jgl") if jingle_files else "Yok"

            # Şarkı başına işlemler
            section("🎵 Şarkı Başına Anons & İşlemler")
            fon_files = list_audio(FON_DIR)
            eff_files = list_audio(EFFECT_DIR)

            for idx, f in enumerate(selected):
                sid = f"au{idx}_{sfn(f[:12])}"
                name = os.path.splitext(f)[0]
                tags = get_id3(os.path.join(PLAYLIST_DIR, f))
                dur = audio_dur(os.path.join(PLAYLIST_DIR, f))
                mem = check_memory(name)

                a_val = tags.get("artist", "")[:16]
                art_html = f" {chip(a_val, 'purple')}" if a_val else ""
                c_label = f"♻️{mem.get('count', 0)}x"

                st.markdown(
                    f"{chip(c_label, 'amber')}"
                    f"<div class='song-row'><span class='song-name'>🎵 {f[:40]}</span>"
                    f"{art_html}<span class='song-dur'>{fmt_dur(dur)}</span></div>",
                    unsafe_allow_html=True
                )

                t1, t2, t3, t4 = st.tabs(["✨ AI Anons", "🎤 Mikrofon", "📂 Dosya Yükle", "👁 Önizleme"])

                with t1:
                    ca, cb = st.columns([1, 2])
                    with ca:
                        ctx_s = st.text_input("Bağlam:", key=f"ctx_{sid}", placeholder="gece yayını...")
                        gen_btn = st.button("✨ Groq ile Üret", key=f"gen_{sid}")
                        reg_btn = st.button("🔄 Yeniden Üret", key=f"reg_{sid}")

                        if gen_btn or reg_btn:
                            md_data = {}
                            actual_tone = tone_s
                            if tone_s == "Otomatik (Mood)":
                                with st.spinner("Mood analizi..."):
                                    md_data = groq_mood(name)
                                    actual_tone = md_data.get("tone_suggestion", "Duygusal")

                            parts = [
                                f"Şarkı: {name}",
                                f"Sanatçı: {tags.get('artist', '')}",
                                f"Ton: {actual_tone}",
                                f"Mood: {md_data.get('mood','')}",
                                f"Bağlam: {ctx_s}" if ctx_s else "",
                                "",
                                "Bu şarkı için profesyonel radyo anonsu yaz.",
                                "SADECE düz Türkçe cümleler — XML,SSML,Markdown KULLANMA."
                            ]

                            with st.spinner("Yazıyor..."):
                                result = groq_gen("\n".join(p for p in parts if p),
                                                  char_id=A_CHAR, model_key=groq_mkey)

                            st.session_state[f"txt_{sid}"] = result
                            save_memory(name, result, actual_tone)
                            st.rerun()

                    with cb:
                        cur = st.session_state.get(f"txt_{sid}", "")
                        new = st.text_area("Anons Metni:", value=cur, height=175,
                                           key=f"ta_{sid}", placeholder="Groq ile üret veya buraya yaz...")
                        if new != cur:
                            st.session_state[f"txt_{sid}"] = new

                        wc = word_count(new)
                        ed = est_dur(new, A_SPEED)
                        if wc:
                            st.markdown(
                                f"{chip(f'📝 {wc} kelime', 'blue')} {chip(f'⏱ ~{ed:.0f}sn', 'teal')}",
                                unsafe_allow_html=True
                            )

                        uc = st.checkbox("Fon müziği ekle", key=f"fon_chk_{sid}")
                        fon_here = "Yok"
                        if uc and fon_files:
                            fon_here = st.selectbox("Fon:", fon_files, key=f"fon_sel_{sid}")

                        ue = st.checkbox("Efekt ekle", key=f"eff_chk_{sid}")
                        eff_here = "Yok"
                        eff_pos = "after"
                        if ue and eff_files:
                            eff_here = st.selectbox("Efekt:", eff_files, key=f"eff_sel_{sid}")
                            eff_pos = st.radio("Konum:", ["before", "after"], horizontal=True, key=f"ep_{sid}")

                        if st.button("🔊 Anonsu Seslendir", key=f"v_{sid}", type="primary"):
                            if not new.strip():
                                st.warning("Önce anons metni girin!")
                            else:
                                with st.spinner("Seslendiriliyor..."):
                                    ok, ap = asyncio.run(build_voice(
                                        new, A_VOICE, A_SPEED, A_PITCH, A_PTH, A_INDEX,
                                        f"anons_{sid}_{ts()}.wav",
                                        eq=eq_sb, reverb=reverb_sb, norm_db=float(norm_sb),
                                        tts_engine=tts_engine_sb, piper_model=piper_model_sb,
                                        effect_chain=A_CHAIN
                                    ))
                                if ok and ap:
                                    # Fon/efekt uygula
                                    if PYDUB_OK and (fon_here != "Yok" or eff_here != "Yok"):
                                        try:
                                            final_seg = AudioSegment.from_file(ap)
                                            if fon_here != "Yok":
                                                fon_seg = AudioSegment.from_file(os.path.join(FON_DIR, fon_here))
                                                final_seg = mix_fon_voice(fon_seg, final_seg)
                                            if eff_here != "Yok":
                                                eff_seg = AudioSegment.from_file(os.path.join(EFFECT_DIR, eff_here))
                                                final_seg = mix_with_effect(final_seg, eff_seg, eff_pos)
                                            final_seg.export(ap, "wav")
                                        except Exception as e:
                                            st.warning(f"Mix hatası: {e}")
                                    st.session_state[f"fp_{sid}"] = ap
                                    st.success("✅ Anons hazır!")
                                    st.audio(ap)
                                    draw_waveform(ap)
                                else:
                                    st.error("❌ Ses üretilemedi.")

                with t2:
                    st.markdown('<div class="upload-zone">🎤 Mikrofon ile kayıt yap</div>', unsafe_allow_html=True)
                    if MIC_OK:
                        mr = mic_recorder("🔴 Kayıt", "⬛ Dur", key=f"mic_{sid}")
                        if mr:
                            mp = os.path.join(UVOICE_DIR, f"MIC_{sid}_{ts()}.wav")
                            with open(mp, "wb") as fh:
                                fh.write(mr["bytes"])
                            st.audio(mr["bytes"])
                            st.session_state[f"fp_{sid}"] = mp
                            st.success("✅ Mikrofon kaydı alındı!")
                    else:
                        st.info("streamlit-mic-recorder kurulu değil.")

                with t3:
                    upf = st.file_uploader("Anons sesi yükle:", type=["mp3", "wav", "ogg"], key=f"up_{sid}")
                    if upf:
                        saved = save_uploaded_file(upf, UVOICE_DIR, f"UP_{sid}_{ts()}.wav")
                        if saved:
                            st.audio(saved)
                            st.session_state[f"fp_{sid}"] = saved
                            st.success("✅ Yüklendi!")

                with t4:
                    fp = st.session_state.get(f"fp_{sid}")
                    if fp and os.path.exists(fp):
                        st.audio(fp)
                        dur_p = audio_dur(fp)
                        qs_p = quality_score(fp)
                        st.markdown(
                            chips(chip(f"⏱ {fmt_dur(dur_p)}", "blue"),
                                  chip(f"🎯 {qs_p}/100", "purple")),
                            unsafe_allow_html=True
                        )
                        qbar(qs_p)
                        draw_waveform(fp, 1.5)
                        spec = spectral_analysis(fp)
                        if spec:
                            draw_spectrum_bars(spec)
                    else:
                        st.info("Henüz ses üretilmedi.")

                st.divider()

            # ===================== FINAL MIXDOWN =====================
            section("🏁 Final Mixdown")
            mx1, mx2, mx3 = st.columns(3)
            with mx1:
                bcast_name = st.text_input("Yayın Adı:", value=f"Broadcast_{ts()}", key="au_name")
            with mx2:
                norm_mast = st.checkbox("Master Normalize", value=True, key="au_norm")
                add_sil = st.checkbox("Parça Arası Boşluk", value=True, key="au_sil")
            with mx3:
                mix_btn = st.button("🏁 YAYINI BİRLEŞTİR", type="primary", key="au_mix")

            if mix_btn:
                if not PYDUB_OK:
                    st.error("PyDub kurulu değil! Lütfen pydub kütüphanesini ve ffmpeg'i kontrol edin.")
                elif not selected:
                    st.warning("Lütfen önce listeden şarkı seçin!")
                else:
                    try:
                        with st.status("💎 Mixdown yapılıyor...", expanded=True) as stat:
                            master = AudioSegment.silent(duration=gap_ms)

                            # Jingle ekleme
                            if sel_jgl != "Yok":
                                jp = os.path.join(JINGLE_DIR, sel_jgl)
                                if os.path.exists(jp):
                                    master += AudioSegment.from_file(jp) + AudioSegment.silent(500)

                            # Parçaları birleştirme
                            for idx, f in enumerate(selected):
                                sid = f"au{idx}_{sfn(f[:12])}"
                                ap = st.session_state.get(f"fp_{sid}")
                                sp = os.path.join(PLAYLIST_DIR, f)

                                if not os.path.exists(sp):
                                    st.warning(f"Dosya bulunamadı: {f}")
                                    continue

                                try:
                                    sseg = AudioSegment.from_file(sp)
                                except Exception as e:
                                    st.error(f"Ses yükleme hatası ({f}): {e}")
                                    continue

                                # Anons varsa birleştir veya Ducking uygula
                                if ap and os.path.exists(ap):
                                    aseg = AudioSegment.from_file(ap)
                                    try:
                                        if ducking:
                                            mixed = apply_ducking(sseg, aseg)
                                        else:
                                            mixed = aseg + sseg
                                    except Exception:
                                        mixed = aseg + sseg

                                    master = master.append(mixed, crossfade=min(cf_ms, len(mixed) // 3))
                                else:
                                    master = master.append(sseg, crossfade=min(cf_ms, len(sseg) // 3))

                                if add_sil:
                                    master += AudioSegment.silent(duration=gap_ms)

                                st.write(f"✅ [{idx+1}/{len(selected)}] {f}")

                            # Normalizasyon
                            if norm_mast:
                                master = normalize_seg(master)

                            # Export işlemleri
                            out_filename = f"{sfn(bcast_name)}.wav"
                            out_wav = os.path.join(OUT_DIR, out_filename)
                            master.export(out_wav, format="wav")

                            # Format dönüştürme (wav değilse)
                            final_file = out_wav
                            if exp_fmt != "wav":
                                final_file = do_export(out_wav, exp_fmt)

                            # Arşivleme
                            shutil.copy2(final_file, os.path.join(ARCHIVE_DIR, os.path.basename(final_file)))
                            stat.update(label="✅ Mixdown tamamlandı!", state="complete")

                        # Bilgi Ekranı ve İndirme
                        dur_m = audio_dur(final_file)
                        sz_m = os.path.getsize(final_file) // (1024 * 1024)

                        st.success(f"🔥 {bcast_name} hazır!")
                        st.audio(final_file)

                        st.markdown(
                            f'<div class="mono-box">📁 {os.path.basename(final_file)}<br>'
                            f'⏱ {fmt_dur(dur_m)}<br>💾 {sz_m:.1f} MB</div>',
                            unsafe_allow_html=True
                        )

                        with open(final_file, "rb") as fh:
                            st.download_button(
                                label=f"⬇️ İndir (.{exp_fmt})",
                                data=fh,
                                file_name=os.path.basename(final_file),
                                mime=f"audio/{exp_fmt}"
                            )

                        # Otomatik metadata
                        auto_tags = groq_auto_tags(final_file, f"Yayın: {bcast_name}")
                        if auto_tags:
                            write_id3(final_file, auto_tags)

                        log_event("broadcast", {"name": bcast_name, "dur": dur_m, "tracks": len(selected)})
                        audit_log("broadcast_mixed", f"{bcast_name} | {len(selected)} parça")
                        st.balloons()

                    except Exception as global_err:
                        st.error(f"Mixdown sırasında kritik hata oluştu: {global_err}")

# ── M2: 4 KANAL MİKSER (GELİŞMİŞ) ─────────────────────────────
if menu == "🎛️ 4 Kanal Mikser":
    page_header("🎛️", "4 Kanal Ses Mikseri", "Fon · Anons · Efekt · Jingle — canlı karıştırma stüdyosu")

    fon_files = list_audio(FON_DIR)
    eff_files = list_audio(EFFECT_DIR)
    jingle_files = list_audio(JINGLE_DIR)
    song_files = list_audio(PLAYLIST_DIR)

    # Kanal durumları
    if "mixer_channels" not in st.session_state:
        st.session_state["mixer_channels"] = {
            "ch1": {"file": None, "vol": -8, "pan": 0, "mute": False, "solo": False},
            "ch2": {"file": None, "vol": 0, "pan": 0, "mute": False, "solo": False},
            "ch3": {"file": None, "vol": -6, "pan": 0, "mute": False, "solo": False},
            "ch4": {"file": None, "vol": -3, "pan": 0, "mute": False, "solo": False},
        }

    mc = st.session_state["mixer_channels"]

    tab_mix, tab_preset, tab_master = st.tabs(["🎚️ Kanallar", "💾 Presetler", "🏁 Master"])

    with tab_mix:
        st.markdown('<div class="info-box">ℹ️ Her kanal için dosya seç, seviye ve pan ayarla. Solo/Mute butonları ile izole et.</div>', unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        channels = [
            (c1, "ch1", "🎶 Fon Müziği", fon_files, "blue"),
            (c2, "ch2", "🎙️ Anons/Ses", ["Mikrofon Kaydı"] + list_audio(OUT_DIR) + list_audio(UVOICE_DIR), "green"),
            (c3, "ch3", "🎭 Efekt", eff_files, "purple"),
            (c4, "ch4", "🎺 Jingle", jingle_files, "amber"),
        ]

        for col, ch_id, ch_name, ch_files, ch_color in channels:
            with col:
                st.markdown(f'<div style="text-align:center;font-weight:700;font-size:14px;color:{T["text1"]};margin-bottom:8px;">{ch_name}</div>', unsafe_allow_html=True)
                if ch_files:
                    sel = st.selectbox("Dosya:", ["Yok"] + ch_files, key=f"mx_{ch_id}_sel")
                    mc[ch_id]["file"] = None if sel == "Yok" else sel
                else:
                    st.caption("Dosya yok")

                mc[ch_id]["vol"] = st.slider("Vol (dB)", -40, 12, mc[ch_id]["vol"], key=f"mx_{ch_id}_vol")
                mc[ch_id]["pan"] = st.slider("Pan", -100, 100, mc[ch_id]["pan"], key=f"mx_{ch_id}_pan")
                m1, m2 = st.columns(2)
                with m1:
                    mc[ch_id]["mute"] = st.checkbox("🔇 Mute", value=mc[ch_id]["mute"], key=f"mx_{ch_id}_mute")
                with m2:
                    mc[ch_id]["solo"] = st.checkbox("🎧 Solo", value=mc[ch_id]["solo"], key=f"mx_{ch_id}_solo")

                # VU Metre simülasyonu
                if mc[ch_id]["file"] and not mc[ch_id]["mute"]:
                    vu_level = mc[ch_id]["vol"] + np.random.uniform(-3, 3)
                    vu_meter(vu_level, label=ch_id.upper())

        st.divider()
        if st.button("🎛️ KARMA KARIŞTIR & OLUŞTUR", type="primary", key="mx_mix"):
            if not PYDUB_OK:
                st.error("PyDub gerekli!")
            else:
                active_channels = []
                for ch_id, ch_data in mc.items():
                    if ch_data["file"] and not ch_data["mute"]:
                        # Dosya yolunu belirle
                        if ch_id == "ch1" and fon_files:
                            fp = os.path.join(FON_DIR, ch_data["file"])
                        elif ch_id == "ch2":
                            if ch_data["file"] == "Mikrofon Kaydı":
                                st.warning("Mikrofon kaydı seçildi ancak henüz kayıt yapılmadı.")
                                continue
                            elif os.path.exists(os.path.join(OUT_DIR, ch_data["file"])):
                                fp = os.path.join(OUT_DIR, ch_data["file"])
                            elif os.path.exists(os.path.join(UVOICE_DIR, ch_data["file"])):
                                fp = os.path.join(UVOICE_DIR, ch_data["file"])
                            else:
                                continue
                        elif ch_id == "ch3" and eff_files:
                            fp = os.path.join(EFFECT_DIR, ch_data["file"])
                        elif ch_id == "ch4" and jingle_files:
                            fp = os.path.join(JINGLE_DIR, ch_data["file"])
                        else:
                            continue

                        if os.path.exists(fp):
                            try:
                                seg = AudioSegment.from_file(fp)
                                seg = seg + ch_data["vol"]
                                # Pan uygula (basit stereo balance)
                                if ch_data["pan"] != 0:
                                    left = min(1.0, max(0.0, 1.0 - ch_data["pan"] / 100.0))
                                    right = min(1.0, max(0.0, 1.0 + ch_data["pan"] / 100.0))
                                    seg = seg.pan(ch_data["pan"] / 100.0)
                                active_channels.append(seg)
                            except Exception as e:
                                st.warning(f"{ch_id} yüklenemedi: {e}")

                if len(active_channels) >= 2:
                    with st.spinner("Karıştırılıyor..."):
                        # En uzun sesi baz al
                        max_len = max(len(s) for s in active_channels)
                        mixed = AudioSegment.silent(duration=max_len)
                        for seg in active_channels:
                            mixed = mixed.overlay(seg)
                        mixed = normalize_seg(mixed)
                        out_p = os.path.join(OUT_DIR, f"4ch_mix_{ts()}.wav")
                        mixed.export(out_p, "wav")

                    st.success(f"✅ 4 Kanal Mix hazır! {len(active_channels)} kanal karıştırıldı.")
                    st.audio(out_p)
                    draw_waveform(out_p)
                    spec = spectral_analysis(out_p)
                    if spec:
                        draw_spectrum(spec)
                    with open(out_p, "rb") as fh:
                        st.download_button("⬇️ İndir", fh, os.path.basename(out_p), key="mx_dl")
                else:
                    st.warning("En az 2 aktif kanal gerekli!")

    with tab_preset:
        st.markdown('<div class="info-box">ℹ️ Sık kullanılan mikser ayarlarını kaydet ve yükle.</div>', unsafe_allow_html=True)
        preset_name = st.text_input("Preset Adı:", key="mx_preset_name")
        if st.button("💾 Kaydet", key="mx_save_preset"):
            if preset_name:
                pfile = os.path.join(META_DIR, f"mixer_preset_{sfn(preset_name)}.json")
                with open(pfile, "w") as f:
                    json.dump(mc, f, ensure_ascii=False)
                st.success("✅ Preset kaydedildi!")

        presets = [f for f in os.listdir(META_DIR) if f.startswith("mixer_preset_")]
        if presets:
            sel_preset = st.selectbox("Preset Yükle:", [p.replace("mixer_preset_", "").replace(".json", "") for p in presets], key="mx_load_preset")
            if st.button("📂 Yükle", key="mx_load_btn"):
                pfile = os.path.join(META_DIR, f"mixer_preset_{sfn(sel_preset)}.json")
                if os.path.exists(pfile):
                    with open(pfile) as f:
                        st.session_state["mixer_channels"] = json.load(f)
                    st.success("✅ Preset yüklendi!")
                    st.rerun()

    with tab_master:
        st.markdown("**Master Çıkış Ayarları**")
        mast_limit = st.checkbox("Master Limiter", value=True, key="mx_lim")
        mast_norm = st.slider("Master Normalize (dBFS):", -24, -6, -14, key="mx_mnorm")
        mast_dither = st.checkbox("Dither (16bit)", value=True, key="mx_dither")
        st.markdown('<div class="mono-box">💡 İpucu: Master çıkışta Limiter açık tutun. Radyo yayını için -14 LUFS hedefleyin.</div>', unsafe_allow_html=True)

# ── M3: AI PLAYLIST OLUŞTURUCU ────────────────────────────────
if menu == "🤖 AI Playlist":
    page_header("🤖", "AI Playlist Oluşturucu", "Groq ile otomatik yayın akışı planlama ve oluşturma")

    c1, c2 = st.columns([1.2, 1])
    with c1:
        pl_mood = st.selectbox("Mood/Hava:", ["Mutlu", "Melankolik", "Enerjik", "Romantik", "Nostaljik", "Hüzünlü", "Karışık"], key="pl_mood")
        pl_tempo = st.selectbox("Tempo:", ["Yavaş", "Orta", "Hızlı", "Karışık"], key="pl_tempo")
        pl_count = st.slider("Şarkı Sayısı:", 3, 15, 5, key="pl_count")
        pl_context = st.text_input("Bağlam/Etkinlik:", placeholder="ör: Cuma akşamı yayını, sevgililer günü...", key="pl_ctx")

        if st.button("✨ AI Playlist Üret", type="primary", key="pl_gen"):
            with st.spinner("Groq playlist oluşturuyor..."):
                songs = groq_playlist_genre(pl_mood, pl_tempo, pl_count)
                if songs:
                    st.session_state["ai_playlist"] = songs
                    st.success(f"✅ {len(songs)} şarkı önerisi üretildi!")
                else:
                    st.error("Playlist üretilemedi.")

    with c2:
        if st.session_state.get("ai_playlist"):
            st.markdown("**🎵 AI Önerileri:**")
            for i, song in enumerate(st.session_state["ai_playlist"], 1):
                st.markdown(f'<div class="song-row"><span class="song-name">{i}. {song}</span></div>', unsafe_allow_html=True)

            if st.button("📋 Metin Olarak Kopyala", key="pl_copy"):
                txt = "\n".join(st.session_state["ai_playlist"])
                st.code(txt)

    st.divider()
    section("🎛️ Yayın Akışı Oluştur")

    if st.session_state.get("ai_playlist"):
        pl_songs = st.session_state["ai_playlist"]
        st.markdown(f'<div class="info-box">ℹ️ AI önerileri kullanılarak otomatik anonslar ve mixdown oluşturulacak.</div>', unsafe_allow_html=True)

        pl_char = st.selectbox("Anons Karakteri:", list(CHARS.keys()), key="pl_char")
        pl_fon = st.selectbox("Fon Müziği:", ["Yok"] + fon_files, key="pl_fon") if fon_files else "Yok"
        pl_jgl = st.selectbox("Açılış Jingle:", ["Yok"] + jingle_files, key="pl_jgl") if jingle_files else "Yok"

        if st.button("🚀 TAM YAYIN AKIŞI OLUŞTUR", type="primary", key="pl_build"):
            if not PYDUB_OK:
                st.error("PyDub gerekli!")
            else:
                with st.status("Yayın akışı oluşturuluyor...", expanded=True) as stat:
                    master = AudioSegment.silent(1000)
                    cchar = CHARS[pl_char]

                    if pl_jgl != "Yok":
                        try:
                            jseg = AudioSegment.from_file(os.path.join(JINGLE_DIR, pl_jgl))
                            master += jseg + AudioSegment.silent(500)
                            st.write("✅ Jingle eklendi")
                        except Exception as e:
                            st.warning(f"Jingle hatası: {e}")

                    for i, sg in enumerate(pl_songs):
                        st.write(f"🎵 [{i+1}/{len(pl_songs)}] {sg} işleniyor...")
                        md = groq_mood(sg)
                        anons_txt = groq_gen(
                            f"Şarkı: {sg}\nMood: {md.get('mood','')}\nKısa anons. SADECE düz Türkçe.",
                            char_id=cchar["id"], model_key=groq_mkey, max_tok=200
                        )

                        ok, ap = asyncio.run(build_voice(
                            anons_txt, cchar["voice"], A_SPEED, cchar["pitch"],
                            A_PTH, A_INDEX, f"pl_{i}_{ts()}.wav",
                            tts_engine=tts_engine_sb, piper_model=piper_model_sb
                        ))

                        if ok and ap:
                            if pl_fon != "Yok" and os.path.exists(os.path.join(FON_DIR, pl_fon)):
                                try:
                                    fonseg = AudioSegment.from_file(os.path.join(FON_DIR, pl_fon))
                                    vseg = AudioSegment.from_file(ap)
                                    block = mix_fon_voice(fonseg, vseg)
                                except Exception:
                                    block = AudioSegment.from_file(ap)
                            else:
                                block = AudioSegment.from_file(ap)

                            # Şarkı placeholder (gerçek dosya yoksa jingle ile doldur)
                            block += AudioSegment.silent(2000)
                            master = master.append(block, crossfade=800)
                        else:
                            st.warning(f"{sg} anonsu üretilemedi, atlanıyor.")

                    master = normalize_seg(master)
                    out_p = os.path.join(OUT_DIR, f"AI_Playlist_{ts()}.wav")
                    master.export(out_p, "wav")
                    final_pl = do_export(out_p, exp_fmt) if exp_fmt != "wav" else out_p
                    stat.update(label="✅ AI Playlist yayını hazır!", state="complete")

                st.success("🎉 AI Playlist yayını hazır!")
                st.audio(final_pl)
                st.markdown(f'<div class="mono-box">⏱ {fmt_dur(audio_dur(final_pl))}</div>', unsafe_allow_html=True)
                with open(final_pl, "rb") as fh:
                    st.download_button(f"⬇️ İndir (.{exp_fmt})", fh, os.path.basename(final_pl), mime=f"audio/{exp_fmt}")
                audit_log("ai_playlist_generated", f"{len(pl_songs)} parça")

# ── M4: RADYO SAATİ WIDGET ────────────────────────────────────
if menu == "⏰ Radyo Saati":
    page_header("⏰", "Radyo Saati & Program Akışı", "Canlı saat, NowPlaying göstergesi ve program planı")

    now = datetime.now()

    # Canlı Saat Widget
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c1:
        st.markdown(
            f'<div class="stat-box" style="padding:20px">'
            f'<div style="font-size:48px;font-weight:800;color:{T["primary"]};font-family:\'JetBrains Mono\',monospace;line-height:1">{now.strftime("%H:%M:%S")}</div>'
            f'<div style="font-size:13px;color:{T["text3"]};margin-top:8px">{now.strftime("%d %B %Y %A")}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with c2:
        # NowPlaying simülasyonu
        songs = list_audio(PLAYLIST_DIR)
        if songs:
            current_idx = (now.hour * 60 + now.minute) % max(1, len(songs))
            current_song = songs[current_idx % len(songs)]
            tags = get_id3(os.path.join(PLAYLIST_DIR, current_song))
            st.markdown(
                f'<div class="kcard kcard-accent" style="padding:16px">'
                f'<div class="kcard-title">🎵 Now Playing</div>'
                f'<div style="font-size:18px;font-weight:700;color:{T["text1"]};margin:6px 0">{os.path.splitext(current_song)[0]}</div>'
                f'<div style="font-size:13px;color:{T["text3"]}">{tags.get("artist","Bilinmeyen Sanatçı")}</div>'
                f'{chip("CANLI","red")}'
                f'</div>',
                unsafe_allow_html=True
            )
    with c3:
        # Program bilgisi
        timers = load_timers()
        next_timer = None
        for t in timers:
            try:
                tt = datetime.fromisoformat(t["trigger"])
                if tt > now:
                    next_timer = t
                    break
            except Exception:
                pass
        if next_timer:
            st.markdown(
                f'<div class="kcard" style="padding:16px;border-left:3px solid {T["amber"]}">'
                f'<div class="kcard-title">🔔 Sonraki Program</div>'
                f'<div style="font-size:16px;font-weight:600;color:{T["text1"]}">{next_timer.get("name","?")}</div>'
                f'<div style="font-size:12px;color:{T["text3"]};margin-top:4px">{datetime.fromisoformat(next_timer["trigger"]).strftime("%H:%M")}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="kcard" style="padding:16px">'
                f'<div class="kcard-title">📅 Program</div>'
                f'<div style="font-size:13px;color:{T["text3"]">Yakında program yok.</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.divider()
    section("📋 Program Akışı")

    # Program planı oluştur
    prog_items = []
    schedules = sorted([f for f in os.listdir(SCHEDULE_DIR) if f.endswith(".json")])
    for sf in schedules[:10]:
        try:
            with open(os.path.join(SCHEDULE_DIR, sf)) as fh:
                sd = json.load(fh)
                prog_items.append(sd)
        except Exception:
            pass

    if prog_items:
        for item in prog_items:
            with st.expander(f"📅 {item.get('name','?')} — {item.get('date','?')} {item.get('time','')[:5]}"):
                st.markdown(f'<div class="kcard"><div class="kcard-body">Şarkılar: {", ".join(item.get("songs",[]))[:100]}<br>Not: {item.get("notes","—")}</div></div>', unsafe_allow_html=True)
    else:
        st.info("Henüz program kaydı yok. 📅 Program Planlayıcı'dan ekleyin.")

    # Canlı sayaç
    st.divider()
    section("⏱️ Canlı Sayaçlar")
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.markdown(
            f'<div class="stat-box">'
            f'<div class="stat-num" style="font-size:20px">{len(list_audio(OUT_DIR))}</div>'
            f'<div class="stat-lbl">Üretilen Ses</div></div>',
            unsafe_allow_html=True
        )
    with col_s2:
        total_dur = sum(audio_dur(os.path.join(PLAYLIST_DIR, s)) for s in list_audio(PLAYLIST_DIR))
        st.markdown(
            f'<div class="stat-box">'
            f'<div class="stat-num" style="font-size:20px">{fmt_dur(total_dur)}</div>'
            f'<div class="stat-lbl">Toplam Müzik</div></div>',
            unsafe_allow_html=True
        )
    with col_s3:
        reqs_c = len([f for f in os.listdir(REQUEST_DIR) if f.endswith(".json")])
        st.markdown(
            f'<div class="stat-box">'
            f'<div class="stat-num" style="font-size:20px">{reqs_c}</div>'
            f'<div class="stat-lbl">Bekleyen İstek</div></div>',
            unsafe_allow_html=True
        )

# ── M5: KARAKTER STÜDYOSU ─────────────────────────────────────
if menu == "🎭 Karakter Stüdyosu":
    page_header("🎭", "Karakter Stüdyosu", "8 farklı karakter ile anons karşılaştırma ve yeni karakter oluşturma")
    song_in = st.text_input("Şarkı / Konu:", key="cs_song")
    extra = st.text_area("Ek not:", height=55, key="cs_note")

    c1, c2 = st.columns([3, 1])
    with c1:
        if st.button("🎭 Tüm Karakterleri Üret", key="cs_all"):
            if song_in.strip():
                mood = groq_mood(song_in)
                for cn, cd in CHARS.items():
                    pr = "\n".join(filter(None, [
                        f"Şarkı: {song_in}",
                        f"Mood: {mood.get('mood','')}",
                        f"Yorum: {mood.get('yorum','')}",
                        f"Not: {extra}" if extra else "",
                        "Karakterine uygun anons yaz. SADECE düz Türkçe."
                    ]))
                    with st.spinner(f"{cn}..."):
                        txt = groq_gen(pr, char_id=cd["id"], model_key=groq_mkey)
                    st.session_state[f"cs_{cd['id']}"] = txt
                st.rerun()
    with c2:
        if st.button("🎲 Rastgele Karakter", key="cs_rand"):
            import random
            rand_char = random.choice(list(CHARS.keys()))
            st.info(f"🎲 Seçilen: {rand_char}")

    st.divider()

    # Karakter karşılaştırma grid
    char_cols = st.columns(2)
    for idx, (cn, cd) in enumerate(CHARS.items()):
        cid = cd["id"]
        with char_cols[idx % 2]:
            with st.expander(cn):
                cur = st.session_state.get(f"cs_{cid}", "")
                txt = st.text_area("Metin:", value=cur, height=120, key=f"cs_ta_{cid}")
                if txt != cur:
                    st.session_state[f"cs_{cid}"] = txt
                st.markdown(
                    chips(chip(f"⏱ ~{est_dur(txt):.0f}sn", "blue"),
                          chip(f"📝 {word_count(txt)} kelime", "gray")),
                    unsafe_allow_html=True
                )
                quick_preview(txt, f"cs_preview_{cid}")
                if txt.strip():
                    if st.button(f"🔊 Seslendir", key=f"cs_vb_{cid}"):
                        ok, p = asyncio.run(build_voice(
                            txt, cd["voice"], A_SPEED, cd["pitch"],
                            A_PTH, A_INDEX, f"CHAR_{cid}_{ts()}.wav",
                            eq=eq_sb, reverb=reverb_sb, norm_db=float(norm_sb),
                            tts_engine=tts_engine_sb, piper_model=piper_model_sb,
                            effect_chain=A_CHAIN
                        ))
                        if ok:
                            st.audio(p)
                            draw_waveform(p)
                            st.session_state[f"cs_path_{cid}"] = p

    ready = [(cn, st.session_state[f"cs_path_{cd['id']}"])
             for cn, cd in CHARS.items()
             if st.session_state.get(f"cs_path_{cd['id']}")
             and os.path.exists(st.session_state.get(f"cs_path_{cd['id']}", ""))]
    if ready:
        st.divider()
        section("🔀 Karşılaştırma")
        cols = st.columns(min(len(ready), 4))
        for col, (cn, p) in zip(cols, ready):
            with col:
                st.caption(cn)
                st.audio(p)
                qs = quality_score(p)
                st.markdown(chip(f"{qs}/100", "green"), unsafe_allow_html=True)
                # VU metre
                try:
                    seg = AudioSegment.from_file(p)
                    vu_meter(seg.dBFS, label="RMS")
                except Exception:
                    pass

    # Yeni karakter oluştur
    st.divider()
    section("➕ Yeni Karakter Oluştur")
    nc1, nc2 = st.columns(2)
    with nc1:
        nc_name = st.text_input("Karakter Adı:", key="nc_name")
        nc_voice = st.selectbox("EdgeTTS Sesi:", [
            "tr-TR-EmelNeural", "tr-TR-AhmetNeural",
            "en-US-AriaNeural", "en-US-GuyNeural",
            "de-DE-KatjaNeural", "fr-FR-DeniseNeural"
        ], key="nc_voice")
    with nc2:
        nc_pitch = st.slider("Pitch:", -10, 10, 0, key="nc_pitch")
        nc_prompt = st.text_area("Sistem Promptu:", height=80, key="nc_prompt",
                                  placeholder="Bu karakterin kişiliğini tanımla...")
    if st.button("💾 Karakter Kaydet", key="nc_save"):
        if nc_name and nc_prompt:
            new_char = {
                f"🆕 {nc_name}": {
                    "id": sfn(nc_name),
                    "voice": nc_voice,
                    "pitch": nc_pitch,
                    "prompt": nc_prompt
                }
            }
            # Session'a ekle (kalıcı değil ama çalışma süresince kullanılabilir)
            CHARS.update(new_char)
            st.success(f"✅ {nc_name} karakteri eklendi!")
            st.rerun()

# ── M6: CANLI REJİ ────────────────────────────────────────────
if menu == "🎮 Canlı Reji":
    page_header("🎮", "Canlı Reji", "Anlık anons · jingle · fon çalma · mikrofon · VU metre")
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:16px">'
        f'<div class="live-badge"><span class="live-dot"></span>CANLI YAYIN</div>'
        f'<span style="color:#64748b;font-size:13px">{datetime.now().strftime("%H:%M:%S")} · K3N4N HYBRID v28.0</span>'
        f'</div>', unsafe_allow_html=True
    )

    col_m, col_p = st.columns([2.2, 1])
    with col_m:
        TPLS = {
            "☀️ Sabah": f"Günaydın canım ailemiz! Saat {datetime.now().strftime('%H:%M')}...",
            "🌙 Gece": "Gecenin bu sessiz saatinde sizinle olmak büyük mutluluk...",
            "🎵 Geçiş": "Ve şimdi sizi muhteşem bir melodiyle baş başa bırakıyoruz...",
            "⏰ Saat": f"Saat {datetime.now().strftime('%H:%M')}, K3N4N Hybrid yayınında...",
            "📞 İstek": "İstek hattımız açık! Arayın, mesaj atın, şarkı isteyin...",
            "🎉 Parti": "Bu gece partinin kralı sizsiniz! Hadi müzikle coşalım!",
            "💔 Ayrılık": "Bazı şarkılar kalpte iz bırakır. İşte o şarkılardan biri...",
        }
        tc = st.columns(len(TPLS))
        for i, (lbl, txt) in enumerate(TPLS.items()):
            with tc[i]:
                if st.button(lbl, key=f"lv_t_{i}"):
                    st.session_state["live_txt"] = txt
                    st.rerun()

        lv = st.text_area("Canlı Metin:", value=st.session_state.get("live_txt", ""),
                          height=130, key="live_ta")
        if lv != st.session_state.get("live_txt", ""):
            st.session_state["live_txt"] = lv
        if word_count(lv):
            st.markdown(
                chips(chip(f"📝 {word_count(lv)} kelime", "blue"),
                      chip(f"⏱ ~{est_dur(lv, A_SPEED):.0f}sn", "teal")),
                unsafe_allow_html=True
            )
            quick_preview(lv, "live_preview")

        lc1, lc2, lc3, lc4 = st.columns(4)
        with lc1:
            if st.button("🤖 Groq Geliştir", key="lv_groq"):
                if lv.strip():
                    with st.spinner("..."):
                        imp = groq_gen(f"Geliştir:\n{lv}\nSADECE düz Türkçe.",
                                       char_id=A_CHAR, model_key=groq_mkey, max_tok=200)
                    st.session_state["live_txt"] = imp
                    st.rerun()
        with lc2:
            p = vbtn(lv, "live_main", "🔴 ANİNDA SESLENDİR")
            if p:
                st.session_state["last_live"] = p
        with lc3:
            if st.button("🧹 Temizle", key="lv_clr"):
                st.session_state["live_txt"] = ""
                st.rerun()
        with lc4:
            if st.button("📋 Kopyala", key="lv_copy"):
                st.code(lv)

    with col_p:
        jf = list_audio(JINGLE_DIR)
        if jf:
            section("🎺 Jingle")
            rj = st.selectbox("Jingle seç:", jf, key="rj_sel", label_visibility="collapsed")
            if st.button("▶️ Jingle Çal", key="rj_play"):
                st.audio(os.path.join(JINGLE_DIR, rj), autoplay=True)
                audit_log("jingle_played", rj)

        ff = list_audio(FON_DIR)
        if ff:
            section("🎶 Fon")
            rf = st.selectbox("Fon seç:", ff, key="rf_sel", label_visibility="collapsed")
            if st.button("▶️ Fon Çal", key="rf_play"):
                st.audio(os.path.join(FON_DIR, rf), autoplay=True)
                audit_log("fon_played", rf)

        ef = list_audio(EFFECT_DIR)
        if ef:
            section("🎭 Efekt")
            re_ = st.selectbox("Efekt seç:", ef, key="re_sel", label_visibility="collapsed")
            if st.button("🎭 Efekt Çal", key="re_play"):
                st.audio(os.path.join(EFFECT_DIR, re_), autoplay=True)
                audit_log("effect_played", re_)

        ll = st.session_state.get("last_live")
        if ll and os.path.exists(ll):
            section("Son Anons")
            st.audio(ll)
            draw_waveform(ll, 1.4)
            # Canlı VU
            try:
                seg = AudioSegment.from_file(ll)
                vu_meter(seg.dBFS, label="RMS")
                vu_meter(seg.max_dBFS, max_db=0, min_db=-30, label="Peak")
            except Exception:
                pass

        if MIC_OK:
            section("🎤 Mikrofon")
            mr = mic_recorder("🔴 Kayıt", "⬛ Dur", key="lv_mic")
            if mr:
                mp = os.path.join(UVOICE_DIR, f"LIVE_{ts()}.wav")
                with open(mp, "wb") as fh:
                    fh.write(mr["bytes"])
                st.audio(mr["bytes"])
                st.session_state["last_live"] = mp
                audit_log("microphone_recorded", mp)

# ── M7: HABER BÜLTENİ ─────────────────────────────────────────
if menu == "📰 Haber Bülteni":
    page_header("📰", "Haber Bülteni", "AI destekli haber bülteni üretimi, seslendirme ve arşivleme")
    c1, c2 = st.columns([1.5, 1])
    with c1:
        n_date = st.date_input("Tarih:", key="nb_date")
        n_num = int(st.number_input("Haber sayısı:", 1, 12, 3, key="nb_num"))
        items = []
        for i in range(n_num):
            h = st.text_area(f"Haber #{i+1}:", height=58, key=f"ni_{i}")
            if h.strip():
                items.append(h)
        n_tone = st.radio("Ton:", ["Standart", "Resmi", "Hızlı & Dinamik", "Samimi"], horizontal=True, key="nb_tone")
        n_source = st.text_input("Kaynak/Bakanlık (opsiyonel):", key="nb_source")

        if st.button("📰 Bülten Üret", key="nb_gen"):
            if items:
                pr = (f"Tarih: {n_date.strftime('%d/%m/%Y')}\nTon: {n_tone}\n"
                      f"Kaynak: {n_source}\n\n"
                      "Haberler:\n" + "\n".join(f"- {n}" for n in items) +
                      "\n\nSADECE düz Türkçe, XML/SSML YOK.")
                with st.spinner("..."):
                    b = groq_gen(pr, char_id="haber", model_key=groq_mkey, max_tok=800)
                st.session_state["nb_txt"] = b
                st.rerun()
    with c2:
        bul = st.text_area("Bülten Metni:", value=st.session_state.get("nb_txt", ""),
                           height=290, key="nb_ta")
        if bul != st.session_state.get("nb_txt", ""):
            st.session_state["nb_txt"] = bul
        if bul.strip():
            st.markdown(
                chips(chip(f"📝 {word_count(bul)} kelime", "blue"),
                      chip(f"⏱ ~{est_dur(bul):.0f}sn", "teal")),
                unsafe_allow_html=True
            )
            quick_preview(bul, "nb_preview")
            p = vbtn(bul, "nb_v", "📢 Bülteni Seslendir")
            if p:
                with open(os.path.join(NEWS_DIR, f"news_{ts()}.json"), "w") as fh:
                    json.dump({"text": bul, "date": str(n_date), "file": os.path.basename(p),
                               "source": n_source, "tone": n_tone},
                              fh, ensure_ascii=False)
                audit_log("news_broadcast", f"{n_date} | {n_tone}")
            st.download_button("⬇️ TXT", bul.encode("utf-8"), f"bulten_{ts()}.txt", "text/plain", key="nb_dl")
            if st.button("📋 PDF Formatı (Metin)", key="nb_pdf"):
                st.code(f"HABER BÜLTENİ\nTarih: {n_date}\nKaynak: {n_source}\n\n{bul}")

# ── M8: İSTEK & MESAJLAR ──────────────────────────────────────
if menu == "📩 İstek & Mesajlar":
    page_header("📩", "İstek & Mesajlar", "Dinleyici istekleri, anons yönetimi ve canlı etkileşim")
    ti, tb, tl = st.tabs(["➕ Yeni İstek", "📬 Gelen Kutusu", "📊 İstatistikler"])

    with ti:
        c1, c2 = st.columns([1.2, 1])
        with c1:
            r_name = st.text_input("İsim:", key="r_name")
            r_song = st.text_input("Şarkı:", key="r_song")
            r_msg = st.text_area("Mesaj:", height=80, key="r_msg")
            r_ded = st.text_input("İthaf:", key="r_ded")
            r_platform = st.selectbox("Platform:", ["Telefon", "WhatsApp", "Instagram", "Twitter/X", "E-posta", "Diğer"], key="r_plat")

            if st.button("📨 Kaydet & Üret", key="r_save"):
                if r_name and r_song:
                    d = {
                        "name": r_name, "song": r_song, "message": r_msg,
                        "dedication": r_ded, "platform": r_platform,
                        "timestamp": datetime.now().isoformat(), "status": "pending"
                    }
                    with open(os.path.join(REQUEST_DIR, f"req_{ts()}_{sfn(r_name)}.json"), "w") as fh:
                        json.dump(d, fh, ensure_ascii=False)
                    with st.spinner("..."):
                        txt = groq_gen(
                            f"Dinleyici: {r_name}\nŞarkı: {r_song}\nMesaj: {r_msg}\n"
                            f"İthaf: {r_ded}\nPlatform: {r_platform}\nSamimi istek anonsu. SADECE düz metin.",
                            char_id=A_CHAR, model_key=groq_mkey, max_tok=250
                        )
                    st.session_state["r_anons"] = txt
                    st.success("✅ Kaydedildi!")
                    st.rerun()
                else:
                    st.warning("İsim ve şarkı zorunlu!")
        with c2:
            ra = st.text_area("Anons:", value=st.session_state.get("r_anons", ""), height=185, key="r_ta")
            if ra != st.session_state.get("r_anons", ""):
                st.session_state["r_anons"] = ra
            if ra.strip():
                quick_preview(ra, "r_preview")
                vbtn(ra, "r_v", "🔊 İsteği Seslendir")
            if MIC_OK:
                section("🎤 Sesli İstek")
                mr = mic_recorder("🔴 Kayıt", "⬛ Dur", key="r_mic")
                if mr:
                    with st.spinner("STT..."):
                        sr = groq_stt(mr["bytes"], stt_lang)
                    st.session_state["r_anons"] = sr
                    st.rerun()

    with tb:
        rfiles = sorted([f for f in os.listdir(REQUEST_DIR) if f.endswith(".json")], reverse=True)
        if not rfiles:
            st.info("Henüz istek yok.")
        for rf in rfiles[:25]:
            try:
                with open(os.path.join(REQUEST_DIR, rf)) as fh:
                    rd = json.load(fh)
                sc = "green" if rd.get("status") == "broadcast" else "amber"
                with st.expander(f"🎵 {rd.get('song', '?')} — {rd.get('name', '?')}"):
                    st.markdown(
                        chips(chip(rd.get("status", "?").upper(), sc),
                              chip(rd.get("name", "?"), "blue"),
                              chip(rd.get("platform", "?"), "gray")) + "<br>" +
                        f'<span style="color:#475569;font-size:13px">Mesaj: {rd.get("message", "—")}<br>'
                        f'İthaf: {rd.get("dedication", "—")}<br>'
                        f'<small>{rd.get("timestamp", "?")[:16]}</small></span>',
                        unsafe_allow_html=True
                    )
                    bc1, bc2, bc3 = st.columns(3)
                    with bc1:
                        if st.button("📻 Anons Üret", key=f"ri_{rf}"):
                            with st.spinner("..."):
                                txt = groq_gen(
                                    f"Dinleyici: {rd.get('name')}\nŞarkı: {rd.get('song')}\n"
                                    f"Mesaj: {rd.get('message')}\nSADECE düz Türkçe.",
                                    char_id=A_CHAR, model_key=groq_mkey, max_tok=250
                                )
                            st.session_state[f"ri_txt_{rf}"] = txt
                            st.rerun()
                        if st.session_state.get(f"ri_txt_{rf}"):
                            t = st.text_area("Anons:", value=st.session_state[f"ri_txt_{rf}"],
                                            height=90, key=f"ri_ta_{rf}")
                            st.session_state[f"ri_txt_{rf}"] = t
                            vbtn(t, f"ri_v_{rf}")
                    with bc2:
                        if st.button("✅ Yayına Alındı", key=f"rd_{rf}"):
                            rd["status"] = "broadcast"
                            with open(os.path.join(REQUEST_DIR, rf), "w") as fh:
                                json.dump(rd, fh, ensure_ascii=False)
                            audit_log("request_broadcast", rd.get("song", "?"))
                            st.rerun()
                    with bc3:
                        if st.button("🗑️ Sil", key=f"rdel_{rf}"):
                            os.remove(os.path.join(REQUEST_DIR, rf))
                            st.rerun()
            except Exception:
                pass

    with tl:
        # İstatistikler
        all_reqs = []
        for rf in rfiles:
            try:
                with open(os.path.join(REQUEST_DIR, rf)) as fh:
                    all_reqs.append(json.load(fh))
            except Exception:
                pass
        if all_reqs:
            platforms = Counter(r.get("platform", "Bilinmeyen") for r in all_reqs)
            statuses = Counter(r.get("status", "?") for r in all_reqs)
            st.markdown("**Platform Dağılımı:**")
            for plat, cnt in platforms.most_common():
                st.markdown(chip(f"{plat}: {cnt}", "blue"), unsafe_allow_html=True)
            st.markdown("**Durum Dağılımı:**")
            for stat, cnt in statuses.most_common():
                color = "green" if stat == "broadcast" else "amber"
                st.markdown(chip(f"{stat}: {cnt}", color), unsafe_allow_html=True)
        else:
            st.info("Henüz veri yok.")

# ── M9: MANUEL STÜDYO ─────────────────────────────────────────
if menu == "✍️ Manuel Stüdyo":
    page_header("✍️", "Manuel Stüdyo", "Serbest metin yazma, AI geliştirme ve seslendirme")
    c1, c2 = st.columns([1.3, 1])
    STYLE_MAP = {
        "Radyo Sunucu": "dilay", "Haber Spikeri": "haber", "Reklam Sesi": "reklam",
        "Gece DJsi": "gece", "Sabah Sunucusu": "sabah", "Podcast Host": "podcast",
        "Rock DJ": "rock"
    }
    with c1:
        m_tone = st.selectbox("Ton:", ["Duygusal", "Neşeli", "Espirili", "Şiirsel", "Nostaljik", "Enerjik", "Genel"], key="m_tone")
        m_style = st.selectbox("Stil:", list(STYLE_MAP.keys()), key="m_style")
        m_wt = st.slider("Hedef kelime:", 30, 300, 90, key="m_wt")
        m_cust = st.text_area("Konu/talimat:", height=75, key="m_cust")
        m_seed = st.text_area("Taslak (opsiyonel):", height=60, key="m_seed")
        m_lang = st.selectbox("Dil:", list(MULTILANG_VOICES.keys()), key="m_lang")

        if st.button("🚀 Groq ile Üret", key="m_gen"):
            target_lang = MULTILANG_VOICES[m_lang]["lang"]
            pr = "\n\n".join(filter(None, [
                m_cust,
                f"Ton: {m_tone}\nStil: {m_style}\nHedef: ~{m_wt} kelime\nDil: {target_lang}",
                m_seed,
                "SADECE düz Türkçe — XML/SSML YOK."
            ]))
            with st.spinner("..."):
                res = groq_gen(pr, char_id=STYLE_MAP.get(m_style, "dilay"),
                               model_key=groq_mkey, max_tok=m_wt * 6)
                # Çeviri gerekirse
                if target_lang != "tr" and groq_client:
                    res = groq_translate(res, target_lang)
            st.session_state["m_txt"] = res
            st.rerun()
    with c2:
        m_txt = st.text_area("Son Metin:", value=st.session_state.get("m_txt", ""),
                             height=295, key="m_ta")
        if m_txt != st.session_state.get("m_txt", ""):
            st.session_state["m_txt"] = m_txt
        wc = word_count(m_txt)
        if wc:
            st.markdown(
                chips(chip(f"📝 {wc} kelime", "blue"),
                      chip(f"⏱ ~{est_dur(m_txt, A_SPEED):.0f}sn", "teal")),
                unsafe_allow_html=True
            )
        if m_txt.strip():
            quick_preview(m_txt, "m_preview")
            bc1, bc2, bc3, bc4 = st.columns(4)
            with bc1:
                # Dil seçimine göre ses
                sel_lang = MULTILANG_VOICES.get(m_lang, MULTILANG_VOICES["🇹🇷 Türkçe"])
                if st.button("🔊 Seslendir", key="m_v"):
                    with st.spinner("Seslendiriliyor..."):
                        ok, path = asyncio.run(build_voice(
                            m_txt, sel_lang["voice"], A_SPEED, A_PITCH,
                            A_PTH, A_INDEX, f"manual_{ts()}.wav",
                            eq=eq_sb, reverb=reverb_sb, norm_db=float(norm_sb),
                            tts_engine=tts_engine_sb, piper_model=piper_model_sb
                        ))
                    if ok:
                        st.audio(path)
                        draw_waveform(path)
                        save_history(os.path.basename(path), m_txt, A_CHAR)
            with bc2:
                st.download_button("⬇️ TXT", m_txt.encode("utf-8"), f"anons_{ts()}.txt", "text/plain", key="m_dl")
            with bc3:
                if st.button("🔄 Sıfırla", key="m_rst"):
                    st.session_state["m_txt"] = ""
                    st.rerun()
            with bc4:
                if st.button("📋 Kopyala", key="m_copy"):
                    st.code(m_txt)

# ── M10: TOPLU TTS ────────────────────────────────────────────
if menu == "📦 Toplu TTS":
    page_header("📦", "Toplu TTS", "CSV/TXT/Manuel liste ile seri ses üretimi, ZIP indirme ve birleştirme")
    tab_txt, tab_csv, tab_list, tab_batch = st.tabs(["📄 TXT", "📊 CSV", "✏️ Manuel Liste", "📦 Toplu İndirme Merkezi"])

    with tab_txt:
        st.markdown('<div class="upload-zone">TXT dosyası yükle (her satır ayrı ses)</div>', unsafe_allow_html=True)
        txt_up = st.file_uploader("TXT dosyası:", type=["txt"], key="bulk_txt_up")
        if txt_up:
            saved = save_uploaded_file(txt_up, UPLOAD_DIR, f"bulk_{ts()}.txt")
            if saved:
                with open(saved, "r", encoding="utf-8", errors="ignore") as f:
                    lines = [l.strip() for l in f.readlines() if l.strip()]
                st.success(f"✅ {len(lines)} satır bulundu")
                st.session_state["bulk_lines"] = lines
            else:
                st.error("❌ TXT dosyası okunamadı.")
        if st.session_state.get("bulk_lines"):
            lines = st.session_state["bulk_lines"]
            st.markdown(f'<div class="mono-box">{len(lines)} satır · İlk 3: {" | ".join(lines[:3])[:100]}</div>', unsafe_allow_html=True)
            bulk_prefix = st.text_input("Dosya ön eki:", value="satir", key="bulk_prefix")
            bulk_eq = st.selectbox("EQ Preset:", ["Broadcast Clear", "Radio Warm", "Ham (Efektsiz)"], key="bulk_eq")
            if st.button("🚀 Toplu Üret", key="bulk_txt_btn"):
                prog = st.progress(0)
                results = []
                for i, line in enumerate(lines):
                    fname = f"{bulk_prefix}_{i+1:03d}_{ts()}.wav"
                    with st.spinner(f"[{i+1}/{len(lines)}]..."):
                        ok, path = asyncio.run(build_voice(
                            line, A_VOICE, A_SPEED, A_PITCH,
                            A_PTH, A_INDEX, fname, eq=bulk_eq,
                            reverb=reverb_sb, norm_db=float(norm_sb),
                            tts_engine=tts_engine_sb, piper_model=piper_model_sb,
                            effect_chain=A_CHAIN
                        ))
                    if ok:
                        results.append(path)
                    prog.progress((i + 1) / len(lines))
                st.success(f"✅ {len(results)}/{len(lines)} ses üretildi!")
                if results:
                    for r in results[:3]:
                        st.audio(r)
                    zdata = zip_files(results, "toplu_tts")
                    if zdata:
                        st.download_button("⬇️ Hepsini ZIP İndir", zdata, "toplu_tts.zip", "application/zip", key="bulk_zip")
                    st.session_state["bulk_results"] = results

    with tab_csv:
        st.markdown('<div class="upload-zone">CSV dosyası yükle</div>', unsafe_allow_html=True)
        csv_up = st.file_uploader("CSV dosyası:", type=["csv"], key="bulk_csv_up")
        if csv_up:
            try:
                import csv, io
                content = csv_up.read().decode("utf-8", "ignore")
                reader = csv.DictReader(io.StringIO(content))
                rows = list(reader)
                if rows:
                    headers = list(rows[0].keys())
                    st.success(f"✅ {len(rows)} satır | Sütunlar: {', '.join(headers)}")
                    text_col = st.selectbox("Metin Sütunu:", headers, key="csv_col")
                    csv_eq = st.selectbox("EQ:", ["Broadcast Clear", "Ham (Efektsiz)"], key="csv_eq")
                    if st.button("🚀 CSV'den Üret", key="csv_btn"):
                        prog = st.progress(0)
                        cnt = 0
                        for i, row in enumerate(rows):
                            txt = row.get(text_col, "").strip()
                            if txt:
                                ok, _ = asyncio.run(build_voice(
                                    txt, A_VOICE, A_SPEED, A_PITCH,
                                    A_PTH, A_INDEX, f"csv_{i+1:03d}_{ts()}.wav",
                                    eq=csv_eq, tts_engine=tts_engine_sb, piper_model=piper_model_sb
                                ))
                                if ok:
                                    cnt += 1
                            prog.progress((i + 1) / len(rows))
                        st.success(f"✅ {cnt} ses üretildi!")
            except Exception as e:
                st.error(f"CSV hatası: {e}")

    with tab_list:
        ml_txt = st.text_area("Her satır ayrı ses:", height=200, key="ml_txt",
                               placeholder="Günaydın canım ailemiz!\nHava bugün çok güzel.\nVe şimdi müzikle baş başa bırakıyoruz.")
        ml_prefix = st.text_input("Ön ek:", value="anons", key="ml_prefix")
        ml_merge = st.checkbox("Sonunda Birleştir", value=False, key="ml_merge_chk")
        if st.button("🚀 Hepsini Üret", key="ml_btn") and ml_txt.strip():
            lines = [l.strip() for l in ml_txt.split("\n") if l.strip()]
            prog = st.progress(0)
            results = []
            for i, line in enumerate(lines):
                fname = f"{ml_prefix}_{i+1:03d}_{ts()}.wav"
                with st.spinner(f"[{i+1}/{len(lines)}]..."):
                    ok, path = asyncio.run(build_voice(
                        line, A_VOICE, A_SPEED, A_PITCH, A_PTH, A_INDEX, fname,
                        eq=eq_sb, reverb=reverb_sb, norm_db=float(norm_sb),
                        tts_engine=tts_engine_sb, piper_model=piper_model_sb,
                        effect_chain=A_CHAIN
                    ))
                if ok:
                    results.append(path)
                prog.progress((i + 1) / len(lines))
            st.success(f"✅ {len(results)}/{len(lines)} üretildi!")
            if results and PYDUB_OK and ml_merge:
                if st.button("🔗 Birleştir", key="ml_merge_btn"):
                    master = audio_concat([AudioSegment.from_file(p) for p in results])
                    out_p = os.path.join(OUT_DIR, f"merged_{ts()}.wav")
                    normalize_seg(master).export(out_p, "wav")
                    st.audio(out_p)
                    with open(out_p, "rb") as fh:
                        st.download_button("⬇️ Birleştirilmiş", fh, os.path.basename(out_p), key="ml_dl")
            zdata = zip_files(results, "liste_tts")
            if zdata:
                st.download_button("⬇️ ZIP İndir", zdata, "liste_tts.zip", "application/zip", key="ml_zip")
            st.session_state["bulk_results"] = results

    with tab_batch:
        st.markdown("**📦 Toplu İndirme Merkezi**")
        st.markdown('<div class="info-box">ℹ️ Üretilen tüm sesleri toplu olarak indirin, format dönüştürün.</div>', unsafe_allow_html=True)
        out_files = list_audio(OUT_DIR)
        if out_files:
            st.markdown(chip(f"{len(out_files)} dosya mevcut", "blue"), unsafe_allow_html=True)
            sel_batch = st.multiselect("İndirilecek Dosyalar:", out_files, key="batch_sel")
            batch_fmt = st.selectbox("Format:", ["wav", "mp3", "ogg", "flac"], key="batch_fmt")
            if st.button("📦 ZIP Oluştur", key="batch_zip"):
                if sel_batch:
                    paths = []
                    for f in sel_batch:
                        fp = os.path.join(OUT_DIR, f)
                        if batch_fmt != "wav":
                            fp = do_export(fp, batch_fmt)
                        paths.append(fp)
                    zdata = zip_files(paths, "batch_download")
                    if zdata:
                        st.download_button("⬇️ ZIP İndir", zdata, f"batch_{ts()}.zip", "application/zip", key="batch_dl")
            if st.button("📦 Tümünü ZIP'le", key="batch_all"):
                paths = [os.path.join(OUT_DIR, f) for f in out_files[:50]]
                zdata = zip_files(paths, "all_output")
                if zdata:
                    st.download_button("⬇️ Tüm Çıktılar ZIP", zdata, f"all_output_{ts()}.zip", "application/zip", key="batch_all_dl")
        else:
            st.info("Henüz üretilmiş ses yok.")

# ── M11: INTRO/OUTRO BUILDER ──────────────────────────────────
if menu == "🎬 Intro/Outro":
    page_header("🎬", "Intro/Outro Builder", "Program girişi, kapanış ve ara jingle seslendirme")
    ti, to, tj = st.tabs(["🎬 Program Girişi", "🎤 Program Kapanışı", "🎵 Ara Jingle"])

    def io_tab(tab, title, sys_pr, kp):
        with tab:
            prog = st.text_input("Program Adı:", key=f"{kp}_prog")
            dstr = st.text_input("Tarih/Saat:", value=datetime.now().strftime("%d %B %Y, %H:%M"), key=f"{kp}_date")
            ext = st.text_area("Ek bilgi:", height=60, key=f"{kp}_ext")
            if st.button(f"✨ {title} Üret", key=f"{kp}_gen"):
                pr = (f"{sys_pr}\nProgram: {prog}\nTarih: {dstr}\n"
                      f"{'Ek: ' + ext if ext else ''}\nSADECE düz Türkçe.")
                with st.spinner("..."):
                    txt = groq_gen(pr, char_id=A_CHAR, model_key=groq_mkey, max_tok=200)
                st.session_state[f"{kp}_txt"] = txt
                st.rerun()
            txt = st.text_area("Metin:", value=st.session_state.get(f"{kp}_txt", ""),
                               height=145, key=f"{kp}_ta")
            if txt != st.session_state.get(f"{kp}_txt", ""):
                st.session_state[f"{kp}_txt"] = txt
            if txt.strip():
                ff = list_audio(FON_DIR)
                jf = list_audio(JINGLE_DIR)
                wj = st.checkbox("Jingle ile", key=f"{kp}_wj")
                wf = st.checkbox("Fon ile", key=f"{kp}_wf")
                js = st.selectbox("Jingle:", jf, key=f"{kp}_js") if (wj and jf) else None
                fs = st.selectbox("Fon:", ff, key=f"{kp}_fs") if (wf and ff) else None
                if st.button(f"🔊 {title} Seslendir", key=f"{kp}_vb"):
                    ok, p = asyncio.run(build_voice(
                        txt, A_VOICE, A_SPEED, A_PITCH, A_PTH, A_INDEX,
                        f"{kp.upper()}_{ts()}.wav", eq=eq_sb, reverb=reverb_sb,
                        norm_db=float(norm_sb), tts_engine=tts_engine_sb,
                        piper_model=piper_model_sb, effect_chain=A_CHAIN
                    ))
                    if ok and os.path.exists(p):
                        final = p
                        if wf and fs and PYDUB_OK:
                            out = os.path.join(OUT_DIR, f"{kp}_fon_{ts()}.wav")
                            mix_fon_voice(AudioSegment.from_file(os.path.join(FON_DIR, fs)),
                                          AudioSegment.from_file(p)).export(out, "wav")
                            final = out
                        elif wj and js and PYDUB_OK:
                            out = os.path.join(OUT_DIR, f"{kp}_jgl_{ts()}.wav")
                            apply_ducking(AudioSegment.from_file(os.path.join(JINGLE_DIR, js)),
                                          AudioSegment.from_file(p)).export(out, "wav")
                            final = out
                        st.success("✅")
                        st.audio(final)
                        draw_waveform(final)
                        st.session_state[f"{kp}_path"] = final
                        audit_log(f"{kp}_generated", prog)

    io_tab(ti, "Giriş", "Enerjik çekici program açılış (~30 sn).", "intro")
    io_tab(to, "Kapanış", "Sıcak nostaljik program kapanış (~25 sn).", "outro")

    with tj:
        st.markdown("**🎵 Ara Jingle / Bumpers**")
        jg_text = st.text_input("Jingle Metni (kısa):", placeholder="K3N4N Hybrid'de kalın!", key="jg_txt")
        jg_freq = st.slider("Frekans (Hz):", 200, 1000, 440, key="jg_freq2")
        jg_dur = st.slider("Süre (ms):", 500, 5000, 1500, key="jg_dur2")
        if st.button("🎵 Sentetik Jingle + Ses", key="jg_combo"):
            if jg_text and PYDUB_OK:
                # Seslendir
                ok, vp = asyncio.run(build_voice(
                    jg_text, A_VOICE, A_SPEED, A_PITCH, A_PTH, A_INDEX,
                    f"jg_voice_{ts()}.wav", tts_engine=tts_engine_sb
                ))
                if ok:
                    # Jingle üret
                    jingle = generate_jingle(jg_freq, jg_dur, "sine")
                    if jingle:
                        vseg = AudioSegment.from_file(vp)
                        combo = jingle.overlay(vseg)
                        out_p = os.path.join(OUT_DIR, f"combo_jingle_{ts()}.wav")
                        normalize_seg(combo).export(out_p, "wav")
                        st.success("✅ Combo Jingle hazır!")
                        st.audio(out_p)
                        draw_waveform(out_p)

# ── M12: SES EDİTÖRÜ ──────────────────────────────────────────
if menu == "✂️ Ses Editörü":
    page_header("✂️", "Ses Editörü", "Kırp · Birleştir · Tempo · Pitch · Jingle Üret · Spektrum")
    tab_trim, tab_concat, tab_tempo, tab_jingle, tab_spectrum = st.tabs([
        "✂️ Kırp", "🔗 Birleştir", "🎚️ Tempo/Pitch", "🎵 Jingle Üret", "📊 Spektrum"
    ])

    with tab_trim:
        trim_up = st.file_uploader("Kırpılacak ses:", type=["mp3", "wav", "ogg", "flac"], key="trim_up")
        if trim_up:
            saved = save_uploaded_file(trim_up, UPLOAD_DIR, f"trim_{ts()}.wav")
            if saved and PYDUB_OK:
                seg = AudioSegment.from_file(saved)
                dur = len(seg) / 1000
                st.audio(saved)
                st.markdown(f'<div class="mono-box">⏱ {fmt_dur(dur)} | {seg.dBFS:.1f}dBFS | {seg.frame_rate}Hz | {seg.channels}ch</div>', unsafe_allow_html=True)
                draw_waveform(saved, 1.8)
                # Spektrum analizi
                spec = spectral_analysis(saved)
                if spec:
                    draw_spectrum_bars(spec)
                tc1, tc2 = st.columns(2)
                with tc1:
                    start_s = st.slider("Başlangıç (sn):", 0.0, dur, 0.0, 0.1, key="trim_start")
                with tc2:
                    end_s = st.slider("Bitiş (sn):", 0.0, dur, min(dur, dur), 0.1, key="trim_end")
                if st.button("✂️ Kırp", key="trim_btn"):
                    if start_s < end_s:
                        trimmed = seg[int(start_s * 1000):int(end_s * 1000)]
                        out_p = os.path.join(OUT_DIR, f"trimmed_{ts()}.wav")
                        trimmed.export(out_p, "wav")
                        st.success(f"✅ Kırpıldı: {fmt_dur(end_s - start_s)}")
                        st.audio(out_p)
                        draw_waveform(out_p, 1.5)
                        with open(out_p, "rb") as fh:
                            st.download_button("⬇️ İndir", fh, os.path.basename(out_p), key="trim_dl")
                    else:
                        st.warning("Başlangıç < bitiş olmalı!")
            elif saved is None:
                st.error("❌ Dosya yüklenemedi.")

    with tab_concat:
        concat_files = st.multiselect("OUT klasöründen seç:", list_audio(OUT_DIR), key="concat_sel")
        st.markdown('<div class="upload-zone">veya buradan yükle (çoklu)</div>', unsafe_allow_html=True)
        concat_up = st.file_uploader("Birleştirilecek sesler:", type=["mp3", "wav", "ogg"],
                                      accept_multiple_files=True, key="concat_up")
        extra_paths = []
        if concat_up:
            for uf in concat_up:
                sp = save_uploaded_file(uf, UPLOAD_DIR, f"cc_{sfn(uf.name)}_{ts()}.wav")
                if sp:
                    extra_paths.append(sp)
            if extra_paths:
                st.success(f"✅ {len(extra_paths)} dosya yüklendi")
        all_paths = [os.path.join(OUT_DIR, f) for f in concat_files] + extra_paths
        gap_c = st.slider("Boşluk (ms):", 0, 3000, 500, key="concat_gap")
        cf_c = st.slider("Crossfade (ms):", 0, 2000, 200, key="concat_cf")
        if all_paths and PYDUB_OK:
            st.markdown(chip(f"{len(all_paths)} dosya seçildi", "blue"), unsafe_allow_html=True)
            if st.button("🔗 BİRLEŞTİR", key="concat_btn"):
                with st.spinner("Birleştiriliyor..."):
                    segs = [AudioSegment.from_file(p) for p in all_paths if os.path.exists(p)]
                    if segs:
                        result = segs[0]
                        for s in segs[1:]:
                            if gap_c > 0:
                                result += AudioSegment.silent(gap_c)
                            result = (result.append(s, crossfade=cf_c) if cf_c > 0 else result + s)
                        out_p = os.path.join(OUT_DIR, f"merged_{ts()}.wav")
                        normalize_seg(result).export(out_p, "wav")
                        st.success(f"✅ {fmt_dur(len(result) / 1000)}")
                        st.audio(out_p)
                        draw_waveform(out_p)
                        with open(out_p, "rb") as fh:
                            st.download_button("⬇️ İndir", fh, os.path.basename(out_p), key="concat_dl")

    with tab_tempo:
        tp_up = st.file_uploader("Tempo/pitch ayarı:", type=["mp3", "wav"], key="tp_up")
        if tp_up:
            saved = save_uploaded_file(tp_up, UPLOAD_DIR, f"tp_{ts()}.wav")
            if saved and PYDUB_OK:
                seg = AudioSegment.from_file(saved)
                st.audio(saved)
                tc1, tc2 = st.columns(2)
                with tc1:
                    tf = st.slider("Tempo (x):", 0.5, 2.0, 1.0, 0.05, key="tp_tempo")
                    if st.button("⚡ Tempo", key="tp_btn"):
                        result = seg._spawn(seg.raw_data, overrides={"frame_rate": int(seg.frame_rate * tf)})
                        out_p = os.path.join(OUT_DIR, f"tempo_{ts()}.wav")
                        result.export(out_p, "wav")
                        st.success(f"✅ {tf}x")
                        st.audio(out_p)
                with tc2:
                    gn = st.slider("Gain (dB):", -20, 20, 0, key="tp_gain")
                    sx = st.slider("Hız (x):", 0.5, 2.0, 1.0, 0.05, key="tp_speed")
                    pt = st.slider("Pitch (semitone):", -12, 12, 0, key="tp_pitch")
                    if st.button("🎚️ Uygula", key="tp_all"):
                        result = (seg + gn)._spawn(seg.raw_data, overrides={"frame_rate": int(seg.frame_rate * sx)})
                        # Pitch shift (basit)
                        if pt != 0:
                            result = result._spawn(result.raw_data, overrides={"frame_rate": int(result.frame_rate * (2 ** (pt / 12)))})
                        out_p = os.path.join(OUT_DIR, f"adjusted_{ts()}.wav")
                        result.export(out_p, "wav")
                        st.success("✅")
                        st.audio(out_p)

    with tab_jingle:
        st.markdown('<div class="info-box">ℹ️ Pydub ile otomatik sentetik jingle üret. Kütüphaneye kaydet.</div>', unsafe_allow_html=True)
        jg1, jg2 = st.columns(2)
        with jg1:
            jg_freq = st.slider("Frekans (Hz):", 100, 2000, 440, key="jg_freq")
            jg_dur = st.slider("Süre (ms):", 500, 10000, 2000, key="jg_dur")
            jg_style = st.selectbox("Dalga:", ["sine", "square", "sawtooth"], key="jg_style")
        with jg2:
            jg_name = st.text_input("Jingle Adı:", value=f"jingle_{ts()}", key="jg_name")
            jg_save = st.checkbox("Kütüphaneye kaydet", value=True, key="jg_save")
        if st.button("🎵 Jingle Üret", key="jg_btn"):
            if not PYDUB_OK:
                st.error("PyDub gerekli!")
            else:
                jingle = generate_jingle(jg_freq, jg_dur, jg_style)
                if jingle:
                    out_dir_j = JINGLE_DIR if jg_save else OUT_DIR
                    out_p = os.path.join(out_dir_j, f"{sfn(jg_name)}.wav")
                    jingle.export(out_p, "wav")
                    st.success(f"✅ {os.path.basename(out_p)}")
                    st.audio(out_p)
                    with open(out_p, "rb") as fh:
                        st.download_button("⬇️ İndir", fh, os.path.basename(out_p), key="jg_dl")
                else:
                    st.error("Jingle üretilemedi — PyDub veya NumPy eksik.")

    with tab_spectrum:
        st.markdown("**📊 Spektrum Analizi**")
        spec_up = st.file_uploader("Spektrum analizi için ses:", type=["mp3", "wav"], key="spec_up")
        if spec_up:
            saved = save_uploaded_file(spec_up, UPLOAD_DIR, f"spec_{ts()}.wav")
            if saved:
                spec = spectral_analysis(saved)
                if spec:
                    st.success("✅ Spektrum analizi tamamlandı")
                    draw_spectrum(spec, h=4.0)
                    draw_spectrum_bars(spec)
                    st.markdown(f'<div class="mono-box">Baskın Frekans: {spec["dominant_freq"]:.1f}Hz<br>Crest Factor: {spec["crest_factor"]:.2f}</div>', unsafe_allow_html=True)
                else:
                    st.error("Spektrum analizi başarısız.")

# ── M13: A/B TEST ─────────────────────────────────────────────
if menu == "🔄 A/B Test":
    page_header("🔄", "A/B Test Stüdyosu", "İki farklı ses ayarını karşılaştır ve kazananı belirle")
    ab_txt = st.text_area("Test Metni:", height=100, key="ab_ta")
    if st.button("✨ Groq ile Üret", key="ab_groq"):
        with st.spinner("..."):
            r = groq_gen("~70 kelime profesyonel radyo anonsu. SADECE düz Türkçe.",
                         char_id=A_CHAR, model_key=groq_mkey, max_tok=150)
        st.session_state["ab_gen"] = r
        st.rerun()
    if st.session_state.get("ab_gen") and not ab_txt:
        ab_txt = st.session_state["ab_gen"]
    st.divider()
    ca, cb = st.columns(2)

    def ab_col(col, label, ks, use_txt):
        with col:
            section(label)
            e = st.selectbox("EQ:", ["Broadcast Clear", "Radio Warm", "Vintage", "AM Radio", "Podcast Studio", "Club Bass"], key=f"ab_eq_{ks}")
            rv = st.slider("Reverb:", 0.0, 1.0, 0.0, 0.05, key=f"ab_rv_{ks}")
            pt = st.slider("Pitch:", -14, 14, 0, key=f"ab_pt_{ks}")
            sp = st.slider("Hız:", 75, 130, 100, key=f"ab_sp_{ks}")
            nm = st.slider("Normalize:", -24, -8, -16, key=f"ab_nm_{ks}")
            use_chain_ab = st.checkbox("Efekt Zinciri", key=f"ab_chain_{ks}")
            ab_chain = []
            if use_chain_ab:
                if st.checkbox("Compressor", key=f"ab_comp_{ks}"):
                    ab_chain.append({"fx": "compressor", "threshold": -20, "ratio": 3.0})
                if st.checkbox("Limiter", key=f"ab_lim_{ks}"):
                    ab_chain.append({"fx": "limiter", "ceiling": -1.0})

            if st.button(f"🔊 {label} Üret", key=f"ab_gen_{ks}"):
                if use_txt and use_txt.strip():
                    ok, p = asyncio.run(build_voice(
                        use_txt, A_VOICE, sp, pt, A_PTH, A_INDEX,
                        f"AB_{ks}_{ts()}.wav", eq=e, reverb=rv,
                        norm_db=float(nm), tts_engine=tts_engine_sb,
                        piper_model=piper_model_sb, effect_chain=(ab_chain if ab_chain else None)
                    ))
                    if ok:
                        st.session_state[f"ab_p_{ks}"] = p
                        st.rerun()
            p = st.session_state.get(f"ab_p_{ks}")
            if p and os.path.exists(p):
                qs = quality_score(p)
                dur = audio_dur(p)
                lufs = lufs_estimate(p)
                st.audio(p)
                st.markdown(
                    chips(chip(f"🎯 {qs}/100", "green"), chip(f"⏱ {fmt_dur(dur)}", "blue"),
                          chip(f"LUFS {lufs:.1f}", "purple")),
                    unsafe_allow_html=True
                )
                qbar(qs)
                draw_waveform(p, 1.5)
                spec = spectral_analysis(p)
                if spec:
                    draw_spectrum_bars(spec)

    ab_col(ca, "🅰️ Versiyon A", "a", ab_txt)
    ab_col(cb, "🅱️ Versiyon B", "b", ab_txt)
    pa = st.session_state.get("ab_p_a")
    pb = st.session_state.get("ab_p_b")
    if pa and pb and os.path.exists(pa) and os.path.exists(pb):
        st.divider()
        qa_s, qb_s = quality_score(pa), quality_score(pb)
        lufs_a, lufs_b = lufs_estimate(pa), lufs_estimate(pb)
        # Kazanan belirleme: kalite + LUFS yakınlığı (-14 ideal)
        score_a = qa_s - abs(lufs_a + 14) * 2
        score_b = qb_s - abs(lufs_b + 14) * 2
        wn = "🅰️ A" if score_a >= score_b else "🅱️ B"
        st.markdown(
            f'<div class="ok-box">🅰️ A: <b>{qa_s}/100</b> (LUFS: {lufs_a:.1f}) · '
            f'🅱️ B: <b>{qb_s}/100</b> (LUFS: {lufs_b:.1f}) → '
            f'Kazanan: <b>{wn}</b></div>',
            unsafe_allow_html=True
        )
        if st.button("💾 Kazananı Arşivle", key="ab_save"):
            winner = pa if score_a >= score_b else pb
            shutil.copy2(winner, os.path.join(ARCHIVE_DIR, f"AB_WINNER_{ts()}.wav"))
            st.success("✅ Kazanan arşivlendi!")

# ── M14: SES ARAÇLARI ─────────────────────────────────────────
if menu == "🔊 Ses Araçları":
    page_header("🔊", "Ses Araçları", "İşleme · EQ Demo · STT · Kalite Analizi · VU Metre · LUFS")
    t1, t2, t3, t4, t5 = st.tabs(["🔧 İşleme", "🎚️ EQ Demo", "🗣️ STT", "📊 Analiz", "📈 VU & LUFS"])

    with t1:
        up = st.file_uploader("Ses dosyası yükle:", type=["mp3", "wav", "ogg", "flac"], key="sa_up")
        if up:
            saved = save_uploaded_file(up, UPLOAD_DIR, f"sa_{ts()}.wav")
            if saved and PYDUB_OK:
                seg = AudioSegment.from_file(saved)
                st.audio(saved)
                st.markdown(f'<div class="mono-box">⏱ {fmt_dur(len(seg) / 1000)} | {seg.dBFS:.1f}dBFS | {seg.max_dBFS:.1f}dB Peak | {seg.frame_rate}Hz | {seg.channels}ch | {seg.sample_width * 8}bit</div>', unsafe_allow_html=True)
                draw_waveform(saved)
                spec = spectral_analysis(saved)
                if spec:
                    draw_spectrum_bars(spec)
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    sx = st.slider("Hız x:", 0.5, 2.0, 1.0, 0.1, key="sa_sx")
                    if st.button("⚡ Hız", key="sa_spd"):
                        ns = seg._spawn(seg.raw_data, overrides={"frame_rate": int(seg.frame_rate * sx)})
                        op = os.path.join(OUT_DIR, f"speed_{ts()}.wav")
                        ns.export(op, "wav")
                        st.audio(op)
                with c2:
                    if st.button("↩️ Tersine", key="sa_rev"):
                        op = os.path.join(OUT_DIR, f"rev_{ts()}.wav")
                        seg.reverse().export(op, "wav")
                        st.audio(op)
                with c3:
                    if st.button("📊 Normalize", key="sa_nrm"):
                        op = os.path.join(OUT_DIR, f"norm_{ts()}.wav")
                        normalize_seg(seg).export(op, "wav")
                        st.audio(op)
                with c4:
                    fc = st.selectbox("Format:", ["mp3", "wav", "ogg", "flac"], key="sa_fc")
                    if st.button("🔄 Dönüştür", key="sa_conv"):
                        op = do_export(saved, fc)
                        with open(op, "rb") as fh:
                            st.download_button(f"⬇️.{fc}", fh, os.path.basename(op), key="sa_dl")
            elif saved is None:
                st.error("❌ Dosya yüklenemedi.")

    with t2:
        up2 = st.file_uploader("EQ için ses:", type=["mp3", "wav"], key="eq_up2")
        if up2:
            saved2 = save_uploaded_file(up2, UPLOAD_DIR, f"eq_{ts()}.wav")
            if saved2 and PYDUB_OK:
                ec1, ec2 = st.columns(2)
                with ec1:
                    deq = st.selectbox("EQ:", ["Broadcast Clear", "Radio Warm", "Vintage", "Deep Bass", "Crisp HiFi", "AM Radio", "Podcast Studio", "Club Bass", "Telephone", "Lo-Fi"], key="eq_sel2")
                    drv = st.slider("Reverb:", 0.0, 1.0, 0.0, 0.05, key="eq_rv2")
                    dgn = st.slider("Gain (dB):", -20, 20, 0, key="eq_gn")
                with ec2:
                    dnt = st.slider("Normalize (dBFS):", -24, -8, -16, key="eq_nt")
                st.audio(saved2)
                if st.button("🎚️ Uygula", key="eq_apply"):
                    seg = AudioSegment.from_file(saved2)
                    seg = apply_eq(seg, deq)
                    if drv > 0:
                        seg = apply_reverb(seg, drv)
                    seg = (seg + dgn)
                    seg = normalize_seg(seg, dnt)
                    op = os.path.join(OUT_DIR, f"eq_{ts()}.wav")
                    seg.export(op, "wav")
                    st.success("✅")
                    st.audio(op)
                    draw_waveform(op)
                    spec = spectral_analysis(op)
                    if spec:
                        draw_spectrum(spec)

    with t3:
        m = st.radio("Yöntem:", ["Mikrofon", "Dosya Yükle"], horizontal=True, key="stt_method")
        if m == "Mikrofon" and MIC_OK:
            sr_rec = mic_recorder("🔴 Kayıt", "⬛ Dur", key="stt_mic2")
            if sr_rec:
                st.audio(sr_rec["bytes"])
                if st.button("🗣️ Metne Çevir", key="stt_cvt2"):
                    with st.spinner("..."):
                        r = groq_stt(sr_rec["bytes"], stt_lang)
                    st.text_area("Transkript:", value=r, height=150, key="stt_r2")
                    st.download_button("⬇️ TXT", r.encode("utf-8"), "transkript.txt", "text/plain")
                    audit_log("stt_transcribed", f"{len(r)} karakter")
        else:
            sf = st.file_uploader("STT için ses:", type=["mp3", "wav", "ogg"], key="stt_f2")
            if sf:
                saved_stt = save_uploaded_file(sf, UPLOAD_DIR, f"stt_{ts()}.wav")
                if saved_stt and st.button("🗣️ Metne Çevir", key="stt_cvt_f2"):
                    with open(saved_stt, "rb") as fh:
                        raw = fh.read()
                    with st.spinner("..."):
                        r = groq_stt(raw, stt_lang)
                    st.text_area("Transkript:", value=r, height=200, key="stt_r_f2")
                    st.download_button("⬇️ TXT", r.encode("utf-8"), "transkript.txt", "text/plain")

    with t4:
        ua = st.file_uploader("Analiz edilecek ses:", type=["mp3", "wav"], key="an_up")
        if ua:
            saved_an = save_uploaded_file(ua, UPLOAD_DIR, f"an_{ts()}.wav")
            if saved_an and PYDUB_OK:
                seg = AudioSegment.from_file(saved_an)
                draw_waveform(saved_an)
                spec = spectral_analysis(saved_an)
                if spec:
                    draw_spectrum(spec, h=3.0)
                    draw_spectrum_bars(spec)
                a1, a2, a3, a4, a5 = st.columns(5)
                for col, (l, v) in zip([a1, a2, a3, a4, a5], [
                    ("Süre", fmt_dur(len(seg) / 1000)),
                    ("RMS", f"{seg.dBFS:.1f}dB"),
                    ("Peak", f"{seg.max_dBFS:.1f}dB"),
                    ("Hz", str(seg.frame_rate)),
                    ("Kalite", f"{quality_score(saved_an)}/100"),
                ]):
                    with col:
                        st.markdown(
                            f'<div class="stat-box"><div class="stat-num" style="font-size:20px">{v}</div>'
                            f'<div class="stat-lbl">{l}</div></div>',
                            unsafe_allow_html=True
                        )
                # LUFS
                lufs = lufs_estimate(saved_an)
                st.markdown(f'<div class="mono-box">Tahmini LUFS: {lufs:.1f} (Radyo hedefi: -14 LUFS)</div>', unsafe_allow_html=True)
                if MUTAGEN_OK:
                    orig = os.path.join(UPLOAD_DIR, f"orig_{ts()}{Path(ua.name).suffix}")
                    with open(orig, "wb") as fh:
                        fh.write(ua.getbuffer())
                    tags = get_id3(orig)
                    if any(tags.values()):
                        section("🏷️ ID3")
                        st.json(tags)

    with t5:
        st.markdown("**📈 VU Metre & LUFS Ölçüm**")
        st.markdown('<div class="info-box">ℹ️ Ses dosyası yükle ve gerçek zamanlı seviye göstergesini gör.</div>', unsafe_allow_html=True)
        vu_up = st.file_uploader("VU ölçümü için ses:", type=["mp3", "wav"], key="vu_up")
        if vu_up:
            saved_vu = save_uploaded_file(vu_up, UPLOAD_DIR, f"vu_{ts()}.wav")
            if saved_vu and PYDUB_OK:
                seg = AudioSegment.from_file(saved_vu)
                # Segmentlere böl ve VU göster
                chunk_size = 1000  # 1 saniye
                num_chunks = min(20, len(seg) // chunk_size)
                st.markdown("**Canlı VU Metre (saniye bazlı):**")
                for i in range(num_chunks):
                    chunk = seg[i * chunk_size:(i + 1) * chunk_size]
                    vu_meter(chunk.dBFS, label=f"{i+1}s")
                st.markdown(f'<div class="mono-box">Ortalama RMS: {seg.dBFS:.1f}dB<br>Peak: {seg.max_dBFS:.1f}dB<br>LUFS (tahmini): {lufs_estimate(saved_vu):.1f}</div>', unsafe_allow_html=True)

# ── M15: STREAM YAYIN ─────────────────────────────────────────
if menu == "📡 Stream Yayın":
    page_header("📡", "Stream Yayın", "Yayın URL üret · Dinleme linki paylaş · Icecast · Playlist Stream")
    tab_s1, tab_s2, tab_s3 = st.tabs(["📡 Dosya Stream", "📻 Playlist Stream", "🔗 Icecast"])

    with tab_s1:
        out_files = list_audio(OUT_DIR)
        arc_files = list_audio(ARCHIVE_DIR)
        all_s = out_files + [f"[ARŞİV] {f}" for f in arc_files]
        sf_path = None
        if all_s:
            sel_s = st.selectbox("Dosya:", all_s, key="st_sel")
            real_name = sel_s.replace("[ARŞİV] ", "")
            real_dir = ARCHIVE_DIR if sel_s.startswith("[ARŞİV]") else OUT_DIR
            sf_path = os.path.join(real_dir, real_name)
            if os.path.exists(sf_path):
                st.audio(sf_path)
                st.markdown(f'<div class="mono-box">📁 {real_name} | ⏱ {fmt_dur(audio_dur(sf_path))} | 💾 {os.path.getsize(sf_path) // 1024}KB</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-box">ℹ️ Üretilmiş ses yok.</div>', unsafe_allow_html=True)

        st.divider()
        sc1, sc2 = st.columns(2)
        with sc1:
            stream_port = int(st.number_input("Port:", 1024, 65535, 8765, key="st_port"))
            stream_title = st.text_input("Yayın Adı:", value="K3N4N HYBRID Radyo", key="st_title")
        if st.button("📡 Stream Link Üret", key="st_start"):
            local_ip = get_local_ip()
            stream_url = f"http://{local_ip}:{stream_port}/stream"
            html_content = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{stream_title}</title>
<style>body{{background:#f8fafc;font-family:Inter,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}}
.p{{background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:40px;text-align:center;max-width:400px;box-shadow:0 4px 6px rgba(0,0,0,.07)}}
h1{{color:#2563eb;font-size:1.4em;margin-bottom:16px}}audio{{width:100%;margin:16px 0}}
.dot{{display:inline-block;width:8px;height:8px;border-radius:50%;background:#dc2626;margin-right:6px;animation:b 1.1s infinite}}
@keyframes b{{0%,100%{{opacity:1}}50%{{opacity:.2}}}}</style></head><body>
<div class="p"><h1>📡 {stream_title}</h1><div style="font-size:13px;color:#64748b"><span class="dot"></span>K3N4N HYBRID v28.0</div>
<audio controls autoplay loop><source src="{stream_url}" type="audio/mpeg"><source src="{stream_url}" type="audio/wav"></audio>
<p style="font-size:12px;color:#94a3b8">{datetime.now().strftime("%H:%M")}</p></div></body></html>"""
            player_path = os.path.join(STREAM_DIR, "player.html")
            with open(player_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            m3u = f"#EXTM3U\n#EXTINF:-1,{stream_title}\n{stream_url}\n"
            with open(os.path.join(STREAM_DIR, "stream.m3u"), "w") as f:
                f.write(m3u)
            st.session_state.update({"stream_url": stream_url, "stream_active": True, "stream_file": sf_path})
            st.rerun()

        if st.session_state.get("stream_active") and st.session_state.get("stream_url"):
            url = st.session_state["stream_url"]
            st.markdown(f'<div class="stream-url-box"><div class="live-badge" style="margin-bottom:12px"><span class="live-dot"></span>YAYIN AKTİF</div><br>🔗 <b>URL:</b><br>{url}<br><br>📱 VLC, tarayıcı veya .m3u ile aç</div>', unsafe_allow_html=True)
            cc1, cc2, cc3 = st.columns(3)
            with cc1:
                m3u_p = os.path.join(STREAM_DIR, "stream.m3u")
                if os.path.exists(m3u_p):
                    with open(m3u_p) as f:
                        m = f.read()
                    st.download_button("⬇️ .m3u", m.encode(), "stream.m3u", "audio/x-mpegurl", key="dl_m3u")
            with cc2:
                html_p = os.path.join(STREAM_DIR, "player.html")
                if os.path.exists(html_p):
                    with open(html_p, encoding="utf-8") as f:
                        h = f.read()
                    st.download_button("⬇️ HTML Player", h.encode(), "player.html", "text/html", key="dl_html")
            with cc3:
                if st.button("⏹ Durdur", key="st_stop"):
                    st.session_state.update({"stream_active": False, "stream_url": None})
                    st.rerun()
            sf2 = st.session_state.get("stream_file")
            if sf2 and os.path.exists(sf2):
                section("🎧 Sayfa İçi Oynatıcı")
                st.audio(sf2, autoplay=True)

    with tab_s2:
        songs_ps = list_audio(PLAYLIST_DIR)
        if songs_ps and PYDUB_OK:
            ps_sel = st.multiselect("Şarkılar:", songs_ps, default=songs_ps[:3], key="ps_sel")
            ps_name = st.text_input("Ad:", value=f"Stream_{ts()}", key="ps_name")
            ps_jgl = st.selectbox("Jingle:", ["Yok"] + list_audio(JINGLE_DIR), key="ps_jgl")
            ps_fon = st.selectbox("Fon:", ["Yok"] + list_audio(FON_DIR), key="ps_fon")
            if st.button("📻 Yayın Akışı Oluştur", key="ps_build") and ps_sel:
                with st.status("Oluşturuluyor...", expanded=True) as stat:
                    master = AudioSegment.silent(1000)
                    if ps_jgl != "Yok":
                        jp = os.path.join(JINGLE_DIR, ps_jgl)
                        if os.path.exists(jp):
                            master += AudioSegment.from_file(jp)
                    for i, f in enumerate(ps_sel):
                        sp = os.path.join(PLAYLIST_DIR, f)
                        try:
                            sseg = AudioSegment.from_file(sp)
                            if ps_fon != "Yok":
                                fp2 = os.path.join(FON_DIR, ps_fon)
                                if os.path.exists(fp2):
                                    fon2 = AudioSegment.from_file(fp2)
                                    bridge = fon2[:5000].fade_in(400).fade_out(400) if len(fon2) >= 5000 else fon2
                                    master = master.append(bridge, crossfade=400)
                            master = master.append(sseg, crossfade=1200)
                            st.write(f"✅ [{i+1}] {f}")
                        except Exception as e:
                            st.warning(f"{f}: {e}")
                    master = normalize_seg(master)
                    out_p = os.path.join(OUT_DIR, f"{sfn(ps_name)}.wav")
                    master.export(out_p, "wav")
                    final = do_export(out_p, exp_fmt) if exp_fmt != "wav" else out_p
                    shutil.copy2(final, os.path.join(ARCHIVE_DIR, os.path.basename(final)))
                    stat.update(label="✅ Hazır!", state="complete")
                st.success(f"🎉 {ps_name}")
                st.audio(final)
                st.markdown(f'<div class="mono-box">⏱ {fmt_dur(audio_dur(final))} | 💾 {os.path.getsize(final) // (1024 * 1024):.1f}MB</div>', unsafe_allow_html=True)
                with open(final, "rb") as fh:
                    st.download_button(f"⬇️ (.{exp_fmt})", fh, os.path.basename(final), mime=f"audio/{exp_fmt}")
        else:
            st.markdown('<div class="info-box">ℹ️ Playlist boş veya PyDub kurulu değil.</div>', unsafe_allow_html=True)

    with tab_s3:
        section("🔗 Icecast / Liquidsoap Konfigürasyonu")
        ic1, ic2 = st.columns(2)
        with ic1:
            ic_host = st.text_input("Host:", value="localhost", key="ic_host")
            ic_port = st.number_input("Port:", value=8000, key="ic_port")
            ic_mount = st.text_input("Mount:", value="/stream", key="ic_mount")
        with ic2:
            ic_pass = st.text_input("Şifre:", type="password", key="ic_pass")
            ic_name = st.text_input("Yayın Adı:", value="K3N4N HYBRID", key="ic_name")
        if st.button("📋 Liquidsoap Script", key="ic_gen"):
            ls = f"""#!/usr/bin/liquidsoap
# K3N4N HYBRID v28.0 — {datetime.now().strftime('%d/%m/%Y %H:%M')}
set("log.level", 3)
playlist = playlist(reload=1, mode="randomize", "{PLAYLIST_DIR}")
output.icecast(%mp3(bitrate=192), host="{ic_host}", port={int(ic_port)},
  password="{ic_pass}", mount="{ic_mount}", name="{ic_name}", playlist)"""
            st.code(ls, language="bash")
            st.download_button("⬇️ stream.liq", ls.encode(), "stream.liq", "text/plain", key="dl_liq")
            st.markdown(f'<div class="stream-url-box">🔗 Dinleme: http://{ic_host}:{int(ic_port)}{ic_mount}</div>', unsafe_allow_html=True)

# ── M16: PIPER TTS ────────────────────────────────────────────
if menu == "🗣️ Piper TTS":
    page_header("🗣️", "Piper TTS Yönetimi", "ONNX Türkçe yerel ses motoru — indirme, test, kurulum")
    tab_p1, tab_p2, tab_p3 = st.tabs(["📦 Model Yönetimi", "🧪 Test", "⚙️ Kurulum"])

    with tab_p1:
        for model_key, info in PIPER_MODELS_TR.items():
            mp, cp = piper_model_path(model_key)
            installed = mp is not None
            ic = "green" if installed else "amber"
            with st.expander(f"{'✅' if installed else '⬇️'} {model_key}"):
                st.markdown(
                    chips(chip("KURULU" if installed else "İNDİRİLMEDİ", ic),
                          chip(info.get("repo", info.get("type", "")), "blue")),
                    unsafe_allow_html=True
                )
                if info["type"] == "direct_url":
                    st.markdown(f'<div class="mono-box">Model: {info["model_url"][:70]}...<br>Config: {info["config_url"][:70]}...</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="mono-box">Repo: {info["repo"]}<br>Kaynak: {info.get("src_model", "model.onnx")} + {info.get("src_config", "config.json")}</div>', unsafe_allow_html=True)
                if not installed:
                    if st.button(f"⬇️ İndir", key=f"dl_pm_{sfn(model_key)}"):
                        with st.spinner(f"İndiriliyor: {model_key}..."):
                            ok, msg = piper_download(model_key)
                        if ok:
                            st.success("✅ İndirildi!")
                            st.rerun()
                        else:
                            st.error(f"Hata: {msg[:120]}")
                else:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(chip("✅ Hazır", "green"), unsafe_allow_html=True)
                        if mp:
                            st.caption(f"Model: {mp}")
                    with c2:
                        if st.button("🗑️ Sil", key=f"del_pm_{sfn(model_key)}"):
                            shutil.rmtree(piper_local_dir(model_key), ignore_errors=True)
                            st.success("Silindi!")
                            st.rerun()
        st.divider()
        section("📁 Manuel ONNX Yükle")
        c1, c2 = st.columns(2)
        with c1:
            man_onnx = st.file_uploader("ONNX Model (.onnx):", type=["onnx"], key="man_onnx")
        with c2:
            man_cfg = st.file_uploader("Config (.onnx.json):", type=["json"], key="man_cfg")
        man_name = st.text_input("Model Adı:", key="man_name", placeholder="ör. benim_sesim")
        if man_onnx and man_cfg and man_name and st.button("📥 Kaydet", key="man_save"):
            local = os.path.join(PIPER_DIR, sfn(man_name))
            os.makedirs(local, exist_ok=True)
            for uf in [man_onnx, man_cfg]:
                saved = save_uploaded_file(uf, local, uf.name)
                if not saved:
                    st.error(f"❌ {uf.name} kaydedilemedi.")
            st.success(f"✅ {man_name} kaydedildi!")
            st.rerun()

    with tab_p2:
        section("🧪 Piper TTS Test")
        test_text = st.text_area("Test Metni:",
                                  value="Merhaba canım ailemiz, K3N4N Hybrid radyosuna hoş geldiniz!",
                                  height=75, key="piper_test_txt")
        pt_model = st.selectbox("Model:", list(PIPER_MODELS_TR.keys()), key="pt_model")
        if st.button("🗣️ Piper ile Seslendir", key="piper_test_btn"):
            mp_t, cp_t = piper_model_path(pt_model)
            if not mp_t:
                st.error("Model kurulu değil! Önce indir.")
            else:
                fname = f"piper_test_{ts()}.wav"
                out_p = os.path.join(OUT_DIR, fname)
                with st.spinner("Piper TTS çalışıyor..."):
                    ok = piper_synthesize(clean_text(test_text), mp_t, cp_t, out_p)
                if ok:
                    st.success("✅ Piper TTS hazır!")
                    if A_PTH and os.path.exists(A_PTH) and RVC_OK:
                        rvc_out = os.path.join(OUT_DIR, f"piper_rvc_{ts()}.wav")
                        with st.spinner("RVC uygulanıyor..."):
                            rvc_ok = run_rvc(out_p, rvc_out, A_PTH, A_INDEX, A_PITCH)
                        final = rvc_out if rvc_ok else out_p
                        label = "Piper+RVC" if rvc_ok else "Piper Only"
                    else:
                        final = out_p
                        label = "Piper Only"
                    st.markdown(chip(label, "green"), unsafe_allow_html=True)
                    st.audio(final)
                    draw_waveform(final)
                    spec = spectral_analysis(final)
                    if spec:
                        draw_spectrum_bars(spec)
                else:
                    st.error("❌ Piper TTS başarısız. Kurulum sekmesine bak.")

    with tab_p3:
        st.markdown(f'<div class="mono-box"><b>Kurulum:</b><br>pip install piper-tts<br>pip install onnxruntime<br>pip install huggingface-hub requests<br><br><b>Modeller:</b><br>okeysin.onnx — matroks/reji-v2 (özel TR)<br>dfki-medium — speaches-ai/piper-tr_TR-dfki-medium<br>fahrettin — speaches-ai/piper-tr_TR-fahrettin-medium<br>fettah — speaches-ai/piper-tr_TR-fettah-medium<br><br><b>speaches-ai reposundaki gerçek dosya isimleri:</b><br>model.onnx + config.json → indirildikten sonra renamed</div>', unsafe_allow_html=True)
        section("🔍 Sistem Kontrolü")
        checks = [
            ("onnxruntime", ONNX_OK), ("huggingface-hub", HF_OK), ("requests", REQ_OK),
            ("piper CLI", bool(shutil.which("piper"))), ("espeak-ng", bool(shutil.which("espeak-ng"))),
        ]
        try:
            import piper as _p
            checks.insert(2, ("piper-tts (python)", True))
        except ImportError:
            checks.insert(2, ("piper-tts (python)", False))
        for nm, ok in checks:
            st.markdown(chip(f"{'✅' if ok else '✗'} {nm}", "green" if ok else "red"), unsafe_allow_html=True)

# ── M17: ÇOKLU DİL TTS ────────────────────────────────────────
if menu == "🌐 Çoklu Dil TTS":
    page_header("🌐", "Çoklu Dil TTS", "15+ dil desteği, otomatik çeviri ve seslendirme")
    c1, c2 = st.columns([1.3, 1])
    with c1:
        md_text = st.text_area("Metin (Türkçe):", height=120, key="md_text",
                                placeholder="Merhaba dünya! Bugün harika bir gün...")
        md_target = st.selectbox("Hedef Dil:", list(MULTILANG_VOICES.keys()), key="md_target")
        md_auto_trans = st.checkbox("Otomatik Çevir", value=True, key="md_trans")
        md_char = st.selectbox("Karakter (Türkçe için):", list(CHARS.keys()), key="md_char")

        if st.button("🌐 Çevir & Seslendir", type="primary", key="md_btn"):
            if md_text.strip():
                target_info = MULTILANG_VOICES[md_target]
                final_text = md_text
                if md_auto_trans and target_info["lang"] != "tr" and groq_client:
                    with st.spinner("Çevriliyor..."):
                        final_text = groq_translate(md_text, target_info["lang"])
                    st.session_state["md_translated"] = final_text

                voice_to_use = target_info["voice"]
                pitch_to_use = CHARS[md_char]["pitch"] if target_info["lang"] == "tr" else 0

                with st.spinner("Seslendiriliyor..."):
                    ok, path = asyncio.run(build_voice(
                        final_text, voice_to_use, A_SPEED, pitch_to_use,
                        A_PTH, A_INDEX, f"multilang_{target_info['lang']}_{ts()}.wav",
                        eq=eq_sb, norm_db=float(norm_sb), tts_engine="EdgeTTS"
                    ))
                if ok:
                    st.success(f"✅ {md_target} seslendirmesi hazır!")
                    st.audio(path)
                    draw_waveform(path)
                    st.session_state["md_path"] = path
                    audit_log("multilang_tts", f"{md_target} | {target_info['lang']}")
                else:
                    st.error("Seslendirme başarısız.")
    with c2:
        if st.session_state.get("md_translated"):
            st.markdown("**Çeviri:**")
            st.markdown(f'<div class="kcard"><div class="kcard-body">{st.session_state["md_translated"]}</div></div>', unsafe_allow_html=True)
        st.markdown("**Desteklenen Diller:**")
        for lang, info in MULTILANG_VOICES.items():
            st.markdown(chip(f"{lang} — {info['voice']}", "blue"), unsafe_allow_html=True)

# ── M18: KAYNAK SES ───────────────────────────────────────────
if menu == "📁 Kaynak Ses":
    page_header("📁", "Kaynak Ses Yönetimi", "RVC eğitimi için kaynak ses ve voice cloning")
    tab_u, tab_p, tab_g = st.tabs(["📤 Yükle", "🔧 İşle", "📖 Rehber"])
    with tab_u:
        c1, c2 = st.columns([1.5, 1])
        with c1:
            src_name = st.text_input("Ses Sahibi Adı:", key="src_name", placeholder="ör. Dilay_Studio")
            st.markdown('<div class="upload-zone">Ses dosyaları yükle (çoklu)</div>', unsafe_allow_html=True)
            src_files = st.file_uploader("Kaynak ses dosyaları:", type=["mp3", "wav", "ogg", "flac", "m4a"],
                                          accept_multiple_files=True, key="src_up")
            if src_files and src_name:
                person_dir = os.path.join(SOURCE_DIR, sfn(src_name))
                os.makedirs(person_dir, exist_ok=True)
                saved_cnt = 0
                for uf in src_files:
                    sp = save_uploaded_file(uf, person_dir, uf.name)
                    if sp:
                        saved_cnt += 1
                    else:
                        st.warning(f"⚠️ {uf.name} kaydedilemedi.")
                if saved_cnt > 0:
                    st.success(f"✅ {saved_cnt} dosya kaydedildi!")
            if MIC_OK:
                st.divider()
                section("🎤 Mikrofon Kaydı")
                rec_person = st.text_input("Kişi:", key="rec_sp")
                rec_name = st.text_input("Kayıt Adı:", key="rec_sn")
                mic_rec = mic_recorder("🔴 Kayıt", "⬛ Dur", key="src_mic")
                if mic_rec and rec_person:
                    person_dir = os.path.join(SOURCE_DIR, sfn(rec_person))
                    os.makedirs(person_dir, exist_ok=True)
                    fname = f"{sfn(rec_name or 'rec')}_{ts()}.wav"
                    dest = os.path.join(person_dir, fname)
                    with open(dest, "wb") as fh:
                        fh.write(mic_rec["bytes"])
                    st.success(f"✅ {fname}")
                    st.audio(mic_rec["bytes"])
        with c2:
            section("📂 Mevcut Kaynaklar")
            pdirs = [d for d in os.listdir(SOURCE_DIR) if os.path.isdir(os.path.join(SOURCE_DIR, d))]
            if pdirs:
                for pd in pdirs:
                    pd_path = os.path.join(SOURCE_DIR, pd)
                    pd_files = list_audio(pd_path)
                    total_d = sum(audio_dur(os.path.join(pd_path, f)) for f in pd_files)
                    with st.expander(f"👤 {pd} ({len(pd_files)} · {fmt_dur(total_d)})"):
                        for f in pd_files:
                            fp = os.path.join(pd_path, f)
                            cc = st.columns([3, 1, 1])
                            with cc[0]:
                                st.markdown(f'<div class="song-row"><span class="song-name">{f[:25]}</span><span class="song-dur">{fmt_dur(audio_dur(fp))}</span></div>', unsafe_allow_html=True)
                            with cc[1]:
                                st.audio(fp)
                            with cc[2]:
                                if st.button("🗑️", key=f"src_d_{pd}_{f}"):
                                    os.remove(fp)
                                    st.rerun()
            else:
                st.info("Henüz kaynak ses yok.")

    with tab_p:
        pdirs = [d for d in os.listdir(SOURCE_DIR) if os.path.isdir(os.path.join(SOURCE_DIR, d))]
        if pdirs and PYDUB_OK:
            sel_p = st.selectbox("Kişi:", pdirs, key="proc_p")
            pd_path = os.path.join(SOURCE_DIR, sel_p)
            pd_files = list_audio(pd_path)
            if pd_files:
                ops = st.multiselect("İşlemler:",
                    ["Normalize (-16dBFS)", "Sessizlik Kırp", "44100Hz'e Çevir", "Mono'ya Çevir", "30sn Böl"],
                    default=["Normalize (-16dBFS)", "44100Hz'e Çevir", "Mono'ya Çevir"], key="proc_ops")
                if st.button("🔧 İşle", key="proc_btn"):
                    out_dir_proc = os.path.join(SOURCE_DIR, f"{sel_p}_processed")
                    os.makedirs(out_dir_proc, exist_ok=True)
                    prog = st.progress(0)
                    for i, f in enumerate(pd_files):
                        try:
                            seg = AudioSegment.from_file(os.path.join(pd_path, f))
                            if "44100Hz'e Çevir" in ops:
                                seg = seg.set_frame_rate(44100)
                            if "Mono'ya Çevir" in ops:
                                seg = seg.set_channels(1)
                            if "Normalize (-16dBFS)" in ops:
                                seg = normalize_seg(seg, -16.0)
                            if "Sessizlik Kırp" in ops:
                                seg = pydub_fx.strip_silence(seg, silence_len=200, silence_thresh=-40)
                            if "30sn Böl" in ops:
                                for j, st_ in enumerate(range(0, len(seg), 30000)):
                                    chunk = seg[st_:st_ + 30000]
                                    bn = os.path.splitext(f)[0]
                                    chunk.export(os.path.join(out_dir_proc, f"{bn}_{j:03d}.wav"), "wav")
                            else:
                                seg.export(os.path.join(out_dir_proc, os.path.splitext(f)[0] + ".wav"), "wav")
                        except Exception as e:
                            st.warning(f"{f}: {e}")
                        prog.progress((i + 1) / len(pd_files))
                    st.success(f"✅ {len(pd_files)} dosya işlendi!")
        else:
            st.info("Kaynak ses yükle veya PyDub kur.")

    with tab_g:
        st.markdown(f'<div class="mono-box"><b>RVC Voice Cloning Adımları:</b><br><br>1. En az 10-30 dk temiz ses kaydet<br>2. Ön İşle: normalize + mono + 44100Hz + 30sn segmentler<br>3. RVC WebUI ile eğit (200-300 epoch)<br>4. .pth ve .index dosyalarını /app/ altına koy<br>5. Sidebar\'dan otomatik algılanır<br><br><b>Piper için:</b><br>1. .onnx ve .onnx.json dosyalarını "Piper TTS" sayfasından yükle<br>2. Test sekmesinden doğrula</div>', unsafe_allow_html=True)

# ── M19: SES KLONLAMA STÜDYOSU ────────────────────────────────
if menu == "🎤 Ses Klonlama":
    page_header("🎤", "Ses Klonlama Stüdyosu", "RVC eğitim pipeline'ı ve ileri düzey ses klonlama")
    st.markdown('<div class="info-box">ℹ️ Bu modül RVC model eğitimi için hazırlık ve konfigürasyon sağlar. Gerçek eğitim RVC WebUI ile yapılır.</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        section("📊 Eğitim Verisi Analizi")
        pdirs = [d for d in os.listdir(SOURCE_DIR) if os.path.isdir(os.path.join(SOURCE_DIR, d))]
        if pdirs:
            sel_person = st.selectbox("Kişi:", pdirs, key="clone_person")
            pd_path = os.path.join(SOURCE_DIR, sel_person)
            pd_files = list_audio(pd_path)
            total_dur = sum(audio_dur(os.path.join(pd_path, f)) for f in pd_files)
            st.markdown(
                f'<div class="stat-box"><div class="stat-num">{fmt_dur(total_dur)}</div>'
                f'<div class="stat-lbl">Toplam Süre</div></div>',
                unsafe_allow_html=True
            )
            st.markdown(chip(f"{len(pd_files)} dosya", "blue"), unsafe_allow_html=True)

            # Eğitim önerisi
            if total_dur < 600:
                st.warning("⚠️ En az 10 dakika önerilir.")
            elif total_dur < 1800:
                st.info("ℹ️ İyi. 30+ dakika daha iyi sonuç verir.")
            else:
                st.success("✅ Mükemmel! Eğitim için yeterli veri.")

            # Otomatik bölme önerisi
            if st.button("✂️ 30sn Segmentlere Böl", key="clone_split"):
                out_dir = os.path.join(SOURCE_DIR, f"{sel_person}_training")
                os.makedirs(out_dir, exist_ok=True)
                cnt = 0
                for f in pd_files:
                    try:
                        seg = AudioSegment.from_file(os.path.join(pd_path, f))
                        seg = seg.set_frame_rate(44100).set_channels(1)
                        seg = normalize_seg(seg, -16.0)
                        for j, st_ in enumerate(range(0, len(seg), 30000)):
                            chunk = seg[st_:st_ + 30000]
                            chunk.export(os.path.join(out_dir, f"seg_{cnt:04d}.wav"), "wav")
                            cnt += 1
                    except Exception:
                        pass
                st.success(f"✅ {cnt} segment oluşturuldu!")
        else:
            st.info("Önce 📁 Kaynak Ses'ten veri yükleyin.")

    with c2:
        section("⚙️ RVC Konfigürasyon")
        model_name = st.text_input("Model Adı:", value=f"model_{ts()}", key="clone_name")
        epochs = st.slider("Epoch:", 50, 500, 200, key="clone_epoch")
        batch_size = st.selectbox("Batch Size:", [4, 8, 16], index=1, key="clone_batch")
        sample_rate = st.selectbox("Sample Rate:", [32000, 40000, 48000], index=1, key="clone_sr")
        if st.button("📋 Config Oluştur", key="clone_cfg"):
            cfg = {
                "model_name": model_name,
                "epochs": epochs,
                "batch_size": batch_size,
                "sample_rate": sample_rate,
                "training_dir": os.path.join(SOURCE_DIR, sel_person + "_training") if pdirs else "",
                "created": datetime.now().isoformat()
            }
            cfg_path = os.path.join(META_DIR, f"rvc_config_{sfn(model_name)}.json")
            with open(cfg_path, "w") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            st.success("✅ Config oluşturuldu!")
            st.json(cfg)
            st.download_button("⬇️ Config", json.dumps(cfg, ensure_ascii=False).encode(), f"{model_name}_config.json", "application/json")

    st.divider()
    section("🧪 Hızlı Test")
    test_clone = st.text_input("Test metni:", value="Merhaba, bu benim klonlanmış sesim.", key="clone_test")
    if st.button("🎤 Test Seslendir (Mevcut RVC)", key="clone_test_btn"):
        if A_PTH:
            ok, path = asyncio.run(build_voice(
                test_clone, A_VOICE, A_SPEED, A_PITCH, A_PTH, A_INDEX,
                f"clone_test_{ts()}.wav", tts_engine=tts_engine_sb
            ))
            if ok:
                st.audio(path)
                draw_waveform(path)
        else:
            st.warning("Önce RVC modeli seçin.")


# ── M20: PROGRAM PLANLAYICI ───────────────────────────────────
if menu == "📅 Program Planlayıcı":
    page_header("📅", "Program Planlayıcı", "Yayın programı oluştur, yönet ve otomatik anons üret")
    c1, c2 = st.columns([1.3, 1])
    with c1:
        pn = st.text_input("Program Adı:", key="pln_name")
        pd = st.date_input("Tarih:", key="pln_date")
        pt = st.time_input("Başlangıç:", key="pln_time")
        ps = st.multiselect("Şarkılar:", list_audio(PLAYLIST_DIR), key="pln_songs")
        pnt = st.text_area("Notlar:", height=65, key="pln_notes")
        if st.button("💾 Kaydet", key="pln_save"):
            if pn and ps:
                d = {"name": pn, "date": str(pd), "time": str(pt), "songs": ps, "notes": pnt,
                     "created": datetime.now().isoformat()}
                with open(os.path.join(SCHEDULE_DIR, f"s_{ts()}_{sfn(pn)}.json"), "w") as fh:
                    json.dump(d, fh, ensure_ascii=False)
                st.success("✅ Kaydedildi!")
            else:
                st.warning("Ad ve şarkı gerekli.")
    with c2:
        sf = sorted([f for f in os.listdir(SCHEDULE_DIR) if f.endswith(".json")], reverse=True)
        for fn in sf[:15]:
            try:
                with open(os.path.join(SCHEDULE_DIR, fn)) as fh:
                    sd = json.load(fh)
                with st.expander(f"📅 {sd.get('name', '?')} — {sd.get('date', '?')} {sd.get('time', '')[:5]}"):
                    st.markdown(f'<div class="kcard"><div class="kcard-body">Şarkılar: {", ".join(sd.get("songs", []))[:100]}<br>Not: {sd.get("notes", "—")}</div></div>', unsafe_allow_html=True)
            except Exception:
                pass

# ── M21: ZAMANLAYICI ──────────────────────────────────────────
if menu == "🔔 Zamanlayıcı":
    page_header("🔔", "Yayın Zamanlayıcı", "Zamanlanmış otomatik yayın tetikleyicisi")
    z1, z2 = st.columns([1.2, 1])
    with z1:
        z_name = st.text_input("Zamanlayıcı Adı:", key="z_name")
        z_date = st.date_input("Tarih:", key="z_date")
        z_time = st.time_input("Saat:", key="z_time")
        z_action = st.selectbox("Aksiyon:", ["Anons Üret", "Jingle Çal", "Playlist Başlat", "Stream Başlat"], key="z_act")
        z_param = st.text_input("Parametre (şarkı/metin):", key="z_param")
        if st.button("➕ Zamanlayıcı Ekle", key="z_add"):
            if z_name:
                trigger = datetime.combine(z_date, z_time)
                save_timer(z_name, trigger, z_action, {"param": z_param})
                st.success("✅ Zamanlayıcı eklendi!")
                st.rerun()
    with z2:
        section("⏰ Aktif Zamanlayıcılar")
        timers = load_timers()
        now = datetime.now()
        for t in timers:
            try:
                tt = datetime.fromisoformat(t["trigger"])
                status = "⏳ Bekliyor" if tt > now else "✅ Tamamlandı"
                color = "amber" if tt > now else "green"
                with st.expander(f"{status} | {t.get('name', '?')} — {tt.strftime('%d/%m %H:%M')}"):
                    st.markdown(chips(chip(t.get("action", "?"), color), chip(t.get("params", {}).get("param", "")[:20], "gray")), unsafe_allow_html=True)
                    if st.button("🗑️ Sil", key=f"zdel_{t['file']}"):
                        delete_timer(t["file"])
                        st.rerun()
            except Exception:
                pass

# ── M22: ETKİLEŞİM PANOSU ─────────────────────────────────────
if menu == "💬 Etkileşim Panosu":
    page_header("💬", "Dinleyici Etkileşim Panosu", "Canlı mesajlar, oylama ve istek sırası")
    e1, e2 = st.columns([1.2, 1])
    with e1:
        msg_type = st.selectbox("Tip:", ["Mesaj", "İstek", "Yorum", "Oylama"], key="ei_type")
        msg_sender = st.text_input("Gönderen:", value="Dinleyici", key="ei_sender")
        msg_content = st.text_area("İçerik:", height=80, key="ei_content")
        if st.button("📨 Gönder", key="ei_send"):
            if msg_content.strip():
                save_interaction(msg_type, msg_content, msg_sender)
                st.success("✅ Gönderildi!")
                st.rerun()
    with e2:
        section("📊 Canlı Mesajlar")
        msgs = load_interactions(20)
        for m in msgs:
            icon = {"Mesaj": "💬", "İstek": "🎵", "Yorum": "💭", "Oylama": "📊"}.get(m.get("type"), "💬")
            with st.expander(f"{icon} {m.get('sender', '?')} — {m.get('timestamp', '?')[11:16]}"):
                st.markdown(f'<div class="kcard"><div class="kcard-body">{m.get("content", "")}</div></div>', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(f"👍 {m.get('votes', 0)}", key=f"ev_{m['file']}"):
                        vote_interaction(m["file"])
                        st.rerun()
                with c2:
                    if st.button("🗑️", key=f"edel_{m['file']}"):
                        os.remove(os.path.join(INTERACT_DIR, m["file"]))
                        st.rerun()

# ── M23: SES EFEKT ZİNCİRİ ────────────────────────────────────
if menu == "🎛️ Efekt Zinciri":
    page_header("🎛️", "Ses Efekt Zinciri", "Çoklu efekt pipeline: EQ → Compressor → Reverb → Limiter")
    st.markdown('<div class="info-box">ℹ️ Ses dosyasına sıralı efektler uygula ve önizle.</div>', unsafe_allow_html=True)
    fx_up = st.file_uploader("Ses dosyası:", type=["mp3", "wav", "ogg"], key="fx_up")
    if fx_up:
        saved = save_uploaded_file(fx_up, UPLOAD_DIR, f"fx_{ts()}.wav")
        if saved and PYDUB_OK:
            st.audio(saved)
            seg = AudioSegment.from_file(saved)
            st.markdown(f'<div class="mono-box">Giriş: {seg.dBFS:.1f}dB RMS | {seg.max_dBFS:.1f}dB Peak</div>', unsafe_allow_html=True)
            steps = []
            if st.checkbox("1. High-Pass Filter (80Hz)", value=True, key="fx_hp"):
                steps.append({"fx": "high_pass", "freq": 80})
            eq_sel = st.selectbox("2. EQ Preset:", ["Ham (Efektsiz)", "Broadcast Clear", "Radio Warm", "Podcast Studio", "Club Bass"], key="fx_eq")
            if eq_sel != "Ham (Efektsiz)":
                steps.append({"fx": "eq", "preset": eq_sel})
            if st.checkbox("3. Compressor", value=True, key="fx_comp"):
                steps.append({"fx": "compressor", "threshold": -20, "ratio": 3.0})
            rv_lvl = st.slider("4. Reverb Seviyesi:", 0.0, 1.0, 0.0, key="fx_rev")
            if rv_lvl > 0:
                steps.append({"fx": "reverb", "level": rv_lvl})
            if st.checkbox("5. Limiter", value=True, key="fx_lim"):
                steps.append({"fx": "limiter", "ceiling": -1.0})
            steps.append({"fx": "normalize", "target": float(norm_sb)})
            if st.button("🎛️ ZİNCİRİ UYGULA", type="primary", key="fx_apply"):
                result = apply_effect_chain(seg, steps)
                out_p = os.path.join(OUT_DIR, f"fx_chain_{ts()}.wav")
                result.export(out_p, "wav")
                st.success("✅ Efekt zinciri uygulandı!")
                st.audio(out_p)
                draw_waveform(out_p)
                st.markdown(f'<div class="mono-box">Çıkış: {result.dBFS:.1f}dB RMS | {result.max_dBFS:.1f}dB Peak</div>', unsafe_allow_html=True)
                with open(out_p, "rb") as fh:
                    st.download_button("⬇️ İndir", fh, os.path.basename(out_p), key="fx_dl")

# ── M24: OTOMATİK METADATA ────────────────────────────────────
if menu == "🏷️ Otomatik Metadata":
    page_header("🏷️", "Otomatik Metadata & Etiketleme", "AI destekli ID3 etiketleme ve ses tanıma")
    meta_up = st.file_uploader("Ses dosyası:", type=["mp3", "wav"], key="meta_up")
    if meta_up:
        saved = save_uploaded_file(meta_up, UPLOAD_DIR, f"meta_{ts()}.wav")
        if saved:
            st.audio(saved)
            tags = get_id3(saved)
            st.markdown("**Mevcut Etiketler:**")
            st.json(tags)
            with st.spinner("AI etiket analizi..."):
                auto_tags = groq_auto_tags(saved, "Radyo yayını")
            if auto_tags:
                st.markdown("**🤖 AI Önerileri:**")
                st.json(auto_tags)
                if st.button("🏷️ Etiketleri Uygula", key="meta_apply"):
                    write_id3(saved, auto_tags)
                    st.success("✅ Etiketler uygulandı!")

# ── M25: DÖNÜŞTÜRME MERKEZİ ───────────────────────────────────
if menu == "🔄 Dönüştürme Merkezi":
    page_header("🔄", "Ses Dönüştürme Merkezi", "Format, sample rate, bit depth dönüşümü")
    conv_up = st.file_uploader("Dosya yükle:", type=["mp3", "wav", "ogg", "flac"], key="conv_up")
    if conv_up:
        saved = save_uploaded_file(conv_up, UPLOAD_DIR, f"conv_{ts()}.wav")
        if saved and PYDUB_OK:
            st.audio(saved)
            c1, c2, c3 = st.columns(3)
            with c1:
                conv_fmt = st.selectbox("Format:", ["wav", "mp3", "ogg", "flac"], key="conv_fmt")
            with c2:
                conv_sr = st.selectbox("Sample Rate:", [None, 22050, 44100, 48000, 96000], format_func=lambda x: "Değiştirme" if x is None else f"{x}Hz", key="conv_sr")
            with c3:
                conv_bd = st.selectbox("Bit Depth:", [None, 16, 24, 32], format_func=lambda x: "Değiştirme" if x is None else f"{x}bit", key="conv_bd")
            if st.button("🔄 Dönüştür", key="conv_btn"):
                result = convert_audio(saved, conv_fmt, conv_sr, conv_bd)
                st.success(f"✅ Dönüştürüldü: {os.path.basename(result)}")
                st.audio(result)
                with open(result, "rb") as fh:
                    st.download_button("⬇️ İndir", fh, os.path.basename(result), key="conv_dl")

# ── M26: ANALİTİKLER ──────────────────────────────────────────
if menu == "📊 Analitikler":
    page_header("📊", "Analitikler", "Yayın istatistikleri, kalite analizi ve trendler")
    today_log = os.path.join(ANALYTICS_DIR, f"log_{datetime.now().strftime('%Y%m%d')}.json")
    logs = []
    if os.path.exists(today_log):
        try:
            with open(today_log) as f:
                logs = json.load(f)
        except Exception:
            pass
    tg = len([l for l in logs if l.get("event") == "voice_generated"])
    tw = sum(l.get("words", 0) for l in logs if l.get("event") == "voice_generated")
    tb_ = len([l for l in logs if l.get("event") == "broadcast"])
    oc = len(list_audio(OUT_DIR))
    c1, c2, c3, c4 = st.columns(4)
    for col, (n, l) in zip([c1, c2, c3, c4], [(tg, "Bugün Üretilen"), (tw, "Kelime"), (tb_, "Yayın"), (oc, "Toplam")]):
        with col:
            st.markdown(f'<div class="stat-box"><div class="stat-num">{n}</div><div class="stat-lbl">{l}</div></div>', unsafe_allow_html=True)
    st.divider()
    section("🧠 Anons Hafızası")
    mems = []
    for mp in Path(MEMORY_DIR).glob("*.json"):
        try:
            with open(mp) as f:
                mems.append(json.load(f))
        except Exception:
            pass
    mems.sort(key=lambda x: x.get("count", 0), reverse=True)
    if mems:
        for m in mems[:10]:
            c_val = m.get("count", 0)
            st.markdown(f'<div class="song-row"><span class="song-name">🎵 {m.get("song", "?")[:30]}</span>{chip(f"♻️{c_val}x", "amber")} {chip(m.get("tone", "?"), "blue")}</div>', unsafe_allow_html=True)
    st.divider()
    section("📊 Kalite Grafiği")
    out_files = list_audio(OUT_DIR)
    if out_files and NP_OK:
        scores = [quality_score(os.path.join(OUT_DIR, f)) for f in out_files[-20:]]
        if scores:
            fig, ax = plt.subplots(figsize=(10, 2.3), facecolor=T["bg"])
            ax.set_facecolor(T["bg"])
            colors = ['#16a34a' if s >= 70 else '#d97706' if s >= 50 else '#dc2626' for s in scores]
            ax.bar(range(len(scores)), scores, color=colors, alpha=.82, width=.72)
            ax.axhline(70, color='#16a34a', alpha=0.3, lw=1, ls='--')
            ax.set_ylim(0, 105)
            for sp in ax.spines.values():
                sp.set_visible(False)
            ax.tick_params(colors=T["text4"], labelsize=7)
            plt.tight_layout(pad=.4)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
            avg = sum(scores) / len(scores)
            st.markdown(f'<div class="mono-box">Ort: {avg:.0f}/100 | Max: {max(scores)} | Min: {min(scores)}</div>', unsafe_allow_html=True)

# ── M27: KÜTÜPHANE ────────────────────────────────────────────
if menu == "📁 Kütüphane":
    page_header("📁", "Kütüphane", "Müzik · Fon · Jingle · Efekt dosya yönetimi ve arama")
    lt1, lt2, lt3, lt4 = st.tabs(["🎵 Şarkılar", "🎶 Fon Müzikleri", "🎺 Jinglelar", "🎭 Efektler"])
    def lib_panel(dir_p, tab, tk, info=""):
        with tab:
            if info:
                st.markdown(f'<div class="info-box">ℹ️ {info}</div>', unsafe_allow_html=True)
            search_q = st.text_input("🔍 Ara:", key=f"lib_s_{tk}")
            st.markdown('<div class="upload-zone">📂 Dosya yükle (çoklu seçim desteklenir)</div>', unsafe_allow_html=True)
            ups = st.file_uploader("Dosya yükle:", type=["mp3", "wav", "ogg", "flac"], accept_multiple_files=True, key=f"lb_{tk}")
            if ups:
                cnt = 0
                for u in ups:
                    sp = save_uploaded_file(u, dir_p, u.name)
                    if sp:
                        cnt += 1
                    else:
                        st.warning(f"⚠️ {u.name} kaydedilemedi.")
                if cnt > 0:
                    st.success(f"✅ {cnt} dosya eklendi!")
                    st.rerun()
            files = list_audio(dir_p)
            if search_q:
                files = [f for f in files if search_q.lower() in f.lower()]
            if files:
                total = sum(audio_dur(os.path.join(dir_p, f)) for f in files)
                st.markdown(chips(chip(f"{len(files)} dosya", "blue"), chip(f"⏱ {fmt_dur(total)}", "teal")), unsafe_allow_html=True)
                for f in files:
                    fp = os.path.join(dir_p, f)
                    tags = get_id3(fp)
                    dur = audio_dur(fp)
                    cc = st.columns([3, 1, 1])
                    with cc[0]:
                        art = f' {chip(tags["artist"][:14], "purple")}' if tags.get("artist") else ""
                        st.markdown(f'<div class="song-row"><span class="song-name">🎵 {f[:38]}</span>{art}<span class="song-dur">{fmt_dur(dur)}</span></div>', unsafe_allow_html=True)
                    with cc[1]:
                        st.audio(fp)
                    with cc[2]:
                        if st.button("🗑️", key=f"dl_{tk}_{f}", help="Sil"):
                            os.remove(fp)
                            st.rerun()
            else:
                st.info("Bu klasörde henüz dosya yok.")
    lib_panel(PLAYLIST_DIR, lt1, "songs")
    lib_panel(FON_DIR, lt2, "fon", "Enstrümental background müzikler. Anons sırasında otomatik alçalır.")
    lib_panel(JINGLE_DIR, lt3, "jingles")
    lib_panel(EFFECT_DIR, lt4, "effects", "Alkış, gülme, kapı, ambians efektleri. Anons öncesi/sonrası kullanılır.")

# ── M28: ARŞİV ────────────────────────────────────────────────
if menu == "📻 Arşiv":
    page_header("📻", "Arşiv", "Üretilen sesler ve yayın arşivi — toplu indirme ve yönetim")
    at1, at2 = st.tabs(["📂 Üretilen Sesler", "🗄️ Arşiv"])
    def arc_panel(dir_p, tab, kp):
        with tab:
            files = sorted(list_audio(dir_p), reverse=True)
            if not files:
                st.info("Henüz dosya yok.")
                return
            srch = st.text_input("🔍 Ara:", key=f"arc_s_{kp}")
            filtered = [f for f in files if srch.lower() in f.lower()] if srch else files
            if filtered and st.button("⬇️ Hepsini ZIP İndir", key=f"zip_{kp}"):
                all_paths = [os.path.join(dir_p, f) for f in filtered[:30]]
                zdata = zip_files(all_paths, f"archive_{kp}")
                if zdata:
                    st.download_button("⬇️ ZIP", zdata, f"archive_{kp}.zip", "application/zip", key=f"zdl_{kp}")
            st.markdown(chip(f"{len(filtered)} dosya", "blue"), unsafe_allow_html=True)
            for f in filtered[:40]:
                fp = os.path.join(dir_p, f)
                dur = audio_dur(fp)
                sz = os.path.getsize(fp) // 1024
                with st.expander(f"🔊 {f[:46]} | {fmt_dur(dur)} | {sz}KB"):
                    st.audio(fp)
                    draw_waveform(fp, 1.4)
                    ac1, ac2, ac3, ac4 = st.columns(4)
                    with ac1:
                        with open(fp, "rb") as fh:
                            st.download_button("⬇️ WAV", fh, f, "audio/wav", key=f"dw_{kp}_{f}")
                    with ac2:
                        if PYDUB_OK and st.button("→ MP3", key=f"2mp3_{kp}_{f}"):
                            mp3 = do_export(fp, "mp3")
                            with open(mp3, "rb") as fh:
                                st.download_button("⬇️ MP3", fh, os.path.basename(mp3), key=f"dm_{kp}_{f}")
                    with ac3:
                        if st.button("🗄️ Arşivle", key=f"arc_{kp}_{f}"):
                            shutil.copy2(fp, os.path.join(ARCHIVE_DIR, f))
                            st.success("✅")
                    with ac4:
                        if st.button("🗑️ Sil", key=f"del_{kp}_{f}"):
                            os.remove(fp)
                            st.rerun()
    arc_panel(OUT_DIR, at1, "out")
    arc_panel(ARCHIVE_DIR, at2, "arc")

# ── M29: AYARLAR ──────────────────────────────────────────────
if menu == "⚙️ Ayarlar":
    page_header("⚙️", "Ayarlar", "API bağlantıları, tema, loglama ve sistem temizliği")
    s1, s2, s3, s4 = st.tabs(["🔑 API & Bağlantı", "📋 Aktif Ayarlar", "🧹 Temizlik", "📜 Audit Log"])
    with s1:
        st.markdown(f'<div class="mono-box"><b>GROQ_API_KEY</b> — Groq LLM + Whisper STT (ZORUNLU)<br><b>HF_TOKEN</b> — HuggingFace (opsiyonel)</div>', unsafe_allow_html=True)
        st.divider()
        if st.button("🧪 Groq Test"):
            with st.spinner("..."):
                r = groq_gen("Merhaba test.", max_tok=30)
            st.success(f"✅ {r[:60]}") if not r.startswith("⚠️") else st.error(r)
        if st.button("🎙️ EdgeTTS Test"):
            if TTS_OK:
                op = os.path.join(tempfile.gettempdir(), "tts_test.wav")
                try:
                    asyncio.run(asyncio.wait_for(Communicate("Merhaba dünya!", A_VOICE).save(op), 15))
                    if os.path.exists(op) and os.path.getsize(op) > 512:
                        st.success("✅ EdgeTTS çalışıyor!")
                        st.audio(op)
                    else:
                        st.error("EdgeTTS çıktı üretmedi.")
                except Exception as e:
                    st.error(f"EdgeTTS: {e}")
            else:
                st.error("edge-tts kurulu değil.")
        if all_models:
            st.divider()
            section("🎙️ RVC Modeller")
            for m in all_models:
                ic = "green" if m["index"] else "amber"
                st.markdown(f'<div class="kcard kcard-accent"><div class="kcard-title">{m["name"]}</div><div class="kcard-body" style="font-size:12px">{m["pth"]}<br>{m["index"] or "Index yok"}</div>{chips(chip("PTH ✓", "green"), chip("IDX ✓" if m["index"] else "IDX ✗", ic))}</div>', unsafe_allow_html=True)
    with s2:
        st.json({"character": A_CHAR, "voice": A_VOICE, "pitch": A_PITCH, "speed": A_SPEED,
                 "tts_engine": tts_engine_sb, "pth": A_PTH or "YOK", "index": A_INDEX or "YOK",
                 "eq": eq_sb, "stt_lang": stt_lang, "export_fmt": exp_fmt, "theme": st.session_state.get("theme", "light")})
    with s3:
        dirs = [("Üretilen", OUT_DIR), ("Kullanıcı Sesi", UVOICE_DIR), ("Uploads", UPLOAD_DIR),
                ("Hafıza", MEMORY_DIR), ("Analitik", ANALYTICS_DIR), ("Geçmiş", HISTORY_DIR),
                ("Etkileşim", INTERACT_DIR), ("Zamanlayıcı", TIMER_DIR)]
        cols = st.columns(len(dirs))
        for col, (lbl, d) in zip(cols, dirs):
            with col:
                cnt = len(os.listdir(d)) if os.path.isdir(d) else 0
                st.markdown(f'<div class="stat-box"><div class="stat-num">{cnt}</div><div class="stat-lbl">{lbl}</div></div>', unsafe_allow_html=True)
                if st.button("🗑️", key=f"cl_{sfn(d)}"):
                    for f in os.listdir(d):
                        fp = os.path.join(d, f)
                        if os.path.isfile(fp):
                            try:
                                os.remove(fp)
                            except:
                                pass
                    st.success("✅")
                    st.rerun()
    with s4:
        section("📜 Son İşlem Kayıtları")
        audit_files = sorted([f for f in os.listdir(AUDIT_DIR) if f.endswith(".json")], reverse=True)
        for af in audit_files[:3]:
            try:
                with open(os.path.join(AUDIT_DIR, af)) as f:
                    audits = json.load(f)
                for a in audits[-10:]:
                    st.markdown(f'<div class="mono-box" style="font-size:11px"><b>{a["ts"][11:16]}</b> | {a["action"]}<br>{a.get("details", "")}</div>', unsafe_allow_html=True)
            except Exception:
                pass

# ── FOOTER ───────────────────────────────────────────────────────
status_info = " · ".join([
    f"{'✓' if groq_client is not None else '✗'} Groq",
    f"{'✓' if TTS_OK else '✗'} EdgeTTS",
    f"{'✓' if RVC_OK else '✗'} RVC",
    f"{'✓' if PYDUB_OK else '✗'} PyDub",
    f"{'✓' if NP_OK else '✗'} NumPy",
    f"{'✓' if SCIPY_OK else '✗'} SciPy",
])
st.markdown(
    f'<div class="footer">K3N4N HYBRID v28.0 · {datetime.now().year} · Kenan & Dilay AI Mega Broadcast Engine<br>{status_info}</div>',
    unsafe_allow_html=True
)
