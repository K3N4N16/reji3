import React from "react";
import { VOICES, type ThemeConfig } from "../constants";
import type { AudioMetrics } from "../types";
import { base64ToDataUrl, downloadBase64 } from "../utils/audioClient";
import { WaveformCanvas } from "./WaveformCanvas";

interface ResultCardProps {
  wavBase64: string;
  voice: string;
  usedModel?: string;
  metrics: AudioMetrics;
  downloadName: string;
  theme: ThemeConfig;
}

export const ResultCard: React.FC<ResultCardProps> = ({
  wavBase64,
  voice,
  usedModel,
  metrics,
  downloadName,
  theme,
}) => {
  const qs = metrics.qs ?? 75;
  const bc = qs >= 70 ? "#16a34a" : qs >= 50 ? "#d97706" : "#dc2626";
  const icon = VOICES[voice]?.[0] || "🎙️";

  return (
    <div style={{ marginTop: "10px" }}>
      <div className="card g">
        ✅ {icon} <b>{voice}</b>
        {usedModel ? ` · ${usedModel}` : ""} · {metrics.duration.toFixed(1)}s · Kalite:{" "}
        {qs}/100 · Seviye: {metrics.dbfs} · {metrics.clip}
      </div>
      <div className="qbar">
        <div className="qbar-f" style={{ width: `${qs}%`, background: bc }} />
      </div>
      <audio controls src={base64ToDataUrl(wavBase64, "audio/wav")} />
      <WaveformCanvas
        wavBase64={wavBase64}
        bgColor={theme.plt_bg}
        borderColor={theme.border}
      />
      <button
        type="button"
        className="btn btn-secondary btn-full"
        onClick={() => downloadBase64(wavBase64, downloadName, "audio/wav")}
      >
        💾 WAV İndir
      </button>
    </div>
  );
};
