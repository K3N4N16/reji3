export interface ThemeConfig {
  bg: string;
  sb: string;
  card: string;
  inp: string;
  border: string;
  text: string;
  muted: string;
  dim: string;
  accent: string;
  accent2: string;
  sec_btn: string;
  hdr_bg: string;
  plt_bg: string;
  isLight: boolean;
}

export const THEMES: Record<string, ThemeConfig> = {
  "🌙 Yüksek Kontrast Koyu": {
    bg: "#090d16",
    sb: "#060911",
    card: "#111827",
    inp: "#0f172a",
    border: "#334155",
    text: "#f8fafc",
    muted: "#cbd5e1",
    dim: "#94a3b8",
    accent: "#ef4444",
    accent2: "#60a5fa",
    sec_btn: "#1e293b",
    hdr_bg: "linear-gradient(135deg,#13223d,#0d1526)",
    plt_bg: "#090d16",
    isLight: false,
  },
  "☀️ Aydınlık Stüdyo": {
    bg: "#f1f5f9",
    sb: "#e2e8f0",
    card: "#ffffff",
    inp: "#ffffff",
    border: "#94a3b8",
    text: "#0f172a",
    muted: "#1e293b",
    dim: "#334155",
    accent: "#dc2626",
    accent2: "#2563eb",
    sec_btn: "#e2e8f0",
    hdr_bg: "linear-gradient(135deg,#ffffff,#e2e8f0)",
    plt_bg: "#f8fafc",
    isLight: true,
  },
  "🌊 Stüdyo Lacivert": {
    bg: "#0b132b",
    sb: "#070d1f",
    card: "#1c2541",
    inp: "#141d38",
    border: "#3a506b",
    text: "#ffffff",
    muted: "#e0e7ff",
    dim: "#a5b4fc",
    accent: "#f97316",
    accent2: "#38bdf8",
    sec_btn: "#243154",
    hdr_bg: "linear-gradient(135deg,#1c2541,#0b132b)",
    plt_bg: "#0b132b",
    isLight: false,
  },
};

export const VOICES: Record<string, [string, string]> = {
  Zephyr: ["♀", "Parlak·Neşeli"],
  Puck: ["♂", "Enerjik·Hareketli"],
  Charon: ["♂", "Bilgilendirici"],
  Kore: ["♀", "Sıcak·Güven"],
  Fenrir: ["♂", "Heyecanlı·Dinamik"],
  Aoede: ["♀", "Akıcı·Doğal"],
  Leda: ["♀", "Genç·Enerjik"],
  Orus: ["♂", "Kararlı·Güçlü"],
  Achird: ["♂", "Dostane·Samimi"],
  Algenib: ["♂", "Pürüzlü·Özgün"],
  Algieba: ["♂", "Yumuşak·Hoş"],
  Alnilam: ["♂", "Sağlam·Güçlü"],
  Autonoe: ["♀", "Parlak·İyimser"],
  Callirrhoe: ["♀", "Rahat·Akıcı"],
  Despina: ["♀", "Pürüzsüz·Zarif"],
  Enceladus: ["♂", "Yumuşak·Nefes"],
  Erinome: ["♀", "Net·Hassas"],
  Gacrux: ["♂", "Olgun·Deneyimli"],
  Iapetus: ["♂", "Net·Anlaşılır"],
  Laomedeia: ["♀", "Neşeli·Canlı"],
  Pulcherrima: ["♀", "İfadeli·Çarpıcı"],
  Rasalgethi: ["♂", "Profesyonel"],
  Sadachbia: ["♂", "Canlı·Hareketli"],
  Sadaltager: ["♂", "Bilgili·Otoriter"],
  Schedar: ["♂", "Güçlü·Etkileyici"],
  Sulafat: ["♀", "Sıcak·Davetkar"],
  Umbriel: ["♂", "Derin·Gizemli"],
  Vindemiatrix: ["♀", "Nazik·Kibar"],
  Achernar: ["♀", "Yumuşak·Hassas"],
  Zubenelgenubi: ["♂", "Rahat·Dengeli"],
};

export const MODELS: Record<string, string> = {
  "gemini-3.8-flash-tts": "✨ 3.8 Flash TTS (En Güncel · Diyalog)",
  "gemini-3.8-flash-lite-tts": "⚡ 3.8 Flash Lite TTS (Hızlı · Genel)",
  "gemini-2.5-flash-preview-tts": "🚀 2.5 Flash Preview TTS",
  "gemini-2.5-pro-preview-tts": "💎 2.5 Pro Preview TTS",
};

export const LANGUAGES: Record<string, string> = {
  otomatik: "🌐 Oto",
  "tr-TR": "🇹🇷 Türkçe",
  "en-US": "🇺🇸 EN-US",
  "en-GB": "🇬🇧 EN-UK",
  "de-DE": "🇩🇪 Almanca",
  "fr-FR": "🇫🇷 Fransızca",
  "ar-XA": "🇸🇦 Arapça",
  "es-ES": "🇪🇸 İspanyolca",
};

export const STYLE_PRESETS: Record<string, string> = {
  "— Seçin —": "",
  "📻 Haber Sunucusu": "Profesyonel haber sunucusu gibi net, otoriter ve güven verici oku.",
  "🎉 Neşeli & Enerjik": "Çok neşeli ve coşkulu, müzik programı sunuyormuş gibi oku.",
  "🎭 Dramatik & Güçlü": "Dramatik ve etkileyici, büyük sahne duyurusu gibi oku.",
  "🌙 Sakin & Huzurlu": "Sakin, huzurlu ve rahatlatıcı, gece kuşağı tonu ile oku.",
  "🚨 Acil & Hızlı": "Acil haber tonu, hızlı ve yüksek enerjili oku.",
  "☕ Sıcak & Samimi": "Sıcak ve dostça, yakın arkadaşa anlatır gibi oku.",
  "📣 Reklam Sesi": "Profesyonel reklam seslendirmesi, çekici ve ikna edici oku.",
  "📖 Hikaye": "Büyüleyici hikaye anlatıcısı gibi ritmik ve ifadeli oku.",
};

export const TEMPLATES: Record<string, string> = {
  "🎙️ Sabah Açılış":
    "[excitedly] Günaydın! İmaj FM ile sabahın en güzel sesine uyanıyorsunuz!\n[seriously] Bugün haber bültenimizle başlıyoruz... [normal] hoş geldiniz!\n[excitedly] BU SABAH müzik, haber ve çok daha fazlası burada!",
  "🌙 Gece Kapanış":
    "[whispers] Ve gece yarısına yaklaşırken... İmaj FM sizinle.\n[sighs] Uzun bir günün ardından... kulaklarınıza iyi geceler.\n[whispers] Yarın yeniden buradayız. Tatlı rüyalar.",
  "📢 Özel Duyuru":
    "[excitedly] DUYURU DUYURU!\n[seriously] Değerli dinleyicilerimiz, önemli bir bildirimiz var.\n[excitedly] BU HAFTA sonu unutulmaz bir etkinlik sizi bekliyor!\n[shouting] KAÇIRMAYIN!",
  "🎵 Müzik Geçişi":
    "[normal] Ve müziğimiz devam ediyor...\n[whispers] Şimdi sizin için harika bir seçim var.\n[excitedly] İşte o şarkı!",
  "📰 Haber Girişi":
    "[seriously] İmaj FM Ana Haber Bülteni.\n[normal] Günün öne çıkan haberleriyle karşınızdayız.",
  "🎵 Şarkı Başı":
    "[excitedly] Ve şimdi sizi muhteşem bir şarkıyla baş başa bırakıyoruz!\n[normal] İşte bu dakikanın en özel sesi...",
  "🎵 Şarkı Sonu":
    "[normal] Dinlediğiniz şarkıydı... İmaj FM'de devam ediyoruz.\n[excitedly] Sıradaki sürpriz için kulaklarınız bizde kalsın!",
  "🎉 Yarışma":
    "[excitedly] BÜYÜK YARIŞMA BAŞLIYOR!\n[laughs] Hazır mısınız?\n[shouting] BU HAFTA kazanan sizin aranızdan çıkacak!\n[seriously] Hemen arayın... [excitedly] KAZANMA ŞANSI SİZİN!",
};

export const ETAGS: Array<[string, string, string]> = [
  ["🔥", "Coşkulu", "[excitedly] "],
  ["🤫", "Fısıltı", "[whispers] "],
  ["😄", "Gülen", "[laughs] "],
  ["📰", "Ciddi", "[seriously] "],
  ["📢", "Bağırma", "[shouting] "],
  ["😮‍💨", "Yorgun", "[sighs] "],
  ["🎙️", "Normal", "[normal] "],
];

export const FON_TIPLERI: Record<string, string> = {
  "📻 Radyo Klasik": "Standart radyo fade-out, anons, fade-in.",
  "🎵 Yumuşak Giriş": "Müzik yavaşça yükseliyor, anons bitti, normale dönüyor.",
  "🌊 Dalgalı Geçiş": "Müzik dalgalanarak düşüyor, anons, tekrar yükseliyor.",
  "⚡ Enerji Geçişi": "Enerjik geçişle kesilip anons yapılıyor.",
};

export const EFFECT_PRESETS: Record<
  string,
  { low: number; high: number; gain: number; noise: number }
> = {
  "Radyo Efekti": { low: 300, high: 3000, gain: 3, noise: 0.0 },
  "Telefon Ses": { low: 400, high: 3400, gain: 5, noise: 0.0 },
  Ambians: { low: 100, high: 8000, gain: -2, noise: 0.0 },
  "Dolby Atmos": { low: 50, high: 20000, gain: 0, noise: 0.0 },
  Vinyl: { low: 120, high: 7500, gain: -1, noise: 0.015 },
};

export const EQ_OPTS = ["Ham", "Broadcast", "Warm", "AM", "Podcast", "Vinyl"];

export const ANONS_POSITIONS = [
  "⏮️ Şarkı Başı (Önce Anons, Sonra Şarkı)",
  "🎚️ Şarkı İçi (Başlangıçtan X sn Sonra · Talk-Over)",
  "🎙️ Şarkı İçi (Bitişten X sn Önce · Outro Üzeri)",
  "⏭️ Şarkı Sonu (Şarkı Biter, Sonra Anons)",
];

export const JINGLE_POSITIONS = ["Şarkı Başı", "Şarkı Sonu", "Anons Öncesi"];

export const DEFAULT_TEK =
  "[excitedly] İmaj FM'e hoş geldiniz! BU GECE unutulmaz bir program var...\n[whispers] Sürprizler için kulaklarınız bizde olsun.\n[seriously] Şimdi haberlere geçiyoruz.";

export const DEFAULT_CIFT =
  "Sunucu: [excitedly] İmaj FM'e hoş geldiniz!\nMisafir: [laughs] Teşekkürler!\nSunucu: [seriously] Haberler... [normal] Müziğe dönüyoruz.";
