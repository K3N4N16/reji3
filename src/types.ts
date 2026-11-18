export interface AudioMetrics {
  dbfs: string;
  peak: string;
  clip: string;
  qs: number;
  duration: number;
}

export interface ArchiveItem {
  id: string;
  ts: string;
  ts_s: string;
  voice: string;
  model: string;
  model_s: string;
  lang: string;
  style: string;
  text: string;
  prev: string;
  wavBase64: string;
  dur: number;
  mode: string;
  metrics?: AudioMetrics;
}

export interface FavoriteItem {
  id: string;
  name: string;
  text: string;
  voice: string;
  model: string;
  lang: string;
  wavBase64?: string;
}

export interface RejiSong {
  id: string;
  title: string;
  artist: string;
  duration_min: number;
  duration_sec: number;
  anons_bas: boolean;
  anons_son: boolean;
  anons_bas_text: string;
  anons_son_text: string;
  fon_aktif: boolean;
  fon_tip: string;
  anons_wav_bas?: string | null;
  anons_wav_son?: string | null;
  local_file?: string | null;
}

export interface RejiPlanBlock {
  time: string;
  off: number;
  type: "anons_bas" | "anons_son" | "fon" | "song";
  song_id: string;
  label: string;
  dur: number;
  text: string;
}

export interface AutomationTrack {
  id: string;
  songFilename: string;
  title: string;
  artist: string;
  dur: number;
  anonsSrc: string;
  anonsArcId: string | null;
  anonsLibFile: string | null;
  anonsBase64: string | null;
  anonsName: string;
  anonsPos: string;
  anonsOffsetSec: number;
  endAnonsEnabled: boolean;
  endAnonsSrc: string;
  endAnonsArcId: string | null;
  endAnonsBase64: string | null;
  fonSrc: string;
  fonLibFile: string | null;
  fonBase64: string | null;
  fonVolDb: number;
  jingleSrc: string;
  jingleLibFile: string | null;
  jingleBase64: string | null;
  jinglePos: string;
  duckDb: number;
  anonsGainDb: number;
  rampMs: number;
  previewBase64?: string | null;
}

export interface LibraryFile {
  name: string;
  sizeKb: number;
  duration: number;
  title: string;
  artist: string;
  bitrate: string;
}

export interface ScheduleItem {
  id: string;
  _file: string;
  name: string;
  date: string;
  time: string;
  songs: string[];
  notes: string;
  status: "pending" | "completed";
}

export interface EffectPresetItem {
  name: string;
  params: { low: number; high: number; gain: number; noise: number };
  created?: string;
}

export interface RvcCloneInfo {
  name: string;
  rawCount: number;
  segCount: number;
}
