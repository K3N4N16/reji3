import type { RejiPlanBlock, RejiSong } from "../types";

export function base64ToBlob(b64: string, mime: string): Blob {
  const byteChars = atob(b64);
  const bytes = new Uint8Array(byteChars.length);
  for (let i = 0; i < byteChars.length; i++) {
    bytes[i] = byteChars.charCodeAt(i);
  }
  return new Blob([bytes], { type: mime });
}

export function base64ToDataUrl(b64: string, mime = "audio/wav"): string {
  return `data:${mime};base64,${b64}`;
}

export function downloadBase64(b64: string, filename: string, mime: string): void {
  const blob = base64ToBlob(b64, mime);
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function downloadText(content: string, filename: string, mime = "text/plain"): void {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export async function fileToBase64(file: File): Promise<string> {
  const buf = await file.arrayBuffer();
  const bytes = new Uint8Array(buf);
  let binary = "";
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
  }
  return btoa(binary);
}

export function fmtDur(sec: number): string {
  const s0 = Math.max(0, Math.floor(sec || 0));
  const m = Math.floor(s0 / 60);
  const s = s0 % 60;
  const h = Math.floor(m / 60);
  const mm = m % 60;
  if (h > 0) {
    return `${String(h).padStart(2, "0")}:${String(mm).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  }
  return `${String(mm).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export function addTime(base: string, secs: number): string {
  const p = (base || "06:00").split(":");
  const h = parseInt(p[0], 10) || 6;
  const m = parseInt(p[1], 10) || 0;
  const t = h * 3600 + m * 60 + Math.floor(secs);
  const hh = Math.floor(t / 3600) % 24;
  const mm = Math.floor((t % 3600) / 60);
  const ss = t % 60;
  return `${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}:${String(ss).padStart(2, "0")}`;
}

export function txtStats(text: string): { chars: number; words: number; sentences: number; estSec: number } {
  const chars = text.length;
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  const sentences = Math.max(1, (text.match(/[.!?]/g) || []).length);
  const estSec = Math.max(1, Math.round(chars / 17));
  return { chars, words, sentences, estSec };
}

export function songDur(s: RejiSong): number {
  return (s.duration_min || 3) * 60 + (s.duration_sec || 30);
}

export function autoBas(artist: string, title: string): string {
  return `[excitedly] Ve şimdi İmaj FM'de... ${artist || "?"}! [normal] '${title || "?"}' sizlerle. [whispers] Keyfini çıkarın...`;
}

export function autoSon(artist: string, title: string): string {
  return `[normal] Dinlediğiniz ${artist || "?"} — '${title || "?"}' idi. [excitedly] İmaj FM'de devam ediyoruz!`;
}

export function buildRejiPlan(playlist: RejiSong[], start: string): RejiPlanBlock[] {
  const plan: RejiPlanBlock[] = [];
  let cur = 0;
  for (const song of playlist) {
    const sd = songDur(song);
    if (song.anons_bas) {
      const txt = song.anons_bas_text || autoBas(song.artist, song.title);
      const ad = Math.max(5, Math.floor(txt.length / 15));
      plan.push({
        time: addTime(start, cur),
        off: cur,
        type: "anons_bas",
        song_id: song.id,
        label: `🎙️ Baş → ${song.title}`,
        dur: ad,
        text: txt,
      });
      cur += ad;
    }
    if (song.fon_aktif) {
      plan.push({
        time: addTime(start, cur),
        off: cur,
        type: "fon",
        song_id: song.id,
        label: `🎶 Fon [${song.fon_tip || "?"}] → ${song.title}`,
        dur: 4,
        text: "",
      });
      cur += 4;
    }
    plan.push({
      time: addTime(start, cur),
      off: cur,
      type: "song",
      song_id: song.id,
      label: `🎵 ${song.artist} — ${song.title}`,
      dur: sd,
      text: "",
    });
    cur += sd;
    if (song.anons_son) {
      const txt = song.anons_son_text || autoSon(song.artist, song.title);
      const ad = Math.max(4, Math.floor(txt.length / 15));
      plan.push({
        time: addTime(start, cur),
        off: cur,
        type: "anons_son",
        song_id: song.id,
        label: `🎙️ Son ← ${song.title}`,
        dur: ad,
        text: txt,
      });
      cur += ad;
    }
  }
  return plan;
}
