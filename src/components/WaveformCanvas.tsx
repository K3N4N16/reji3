import React, { useEffect, useRef } from "react";
import { base64ToBlob } from "../utils/audioClient";

interface WaveformCanvasProps {
  wavBase64: string;
  bgColor: string;
  borderColor: string;
  height?: number;
}

export const WaveformCanvas: React.FC<WaveformCanvasProps> = ({
  wavBase64,
  bgColor,
  borderColor,
  height = 96,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function renderWave() {
      const canvas = canvasRef.current;
      if (!canvas || !wavBase64) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const w = canvas.width;
      const h = canvas.height;
      ctx.fillStyle = bgColor;
      ctx.fillRect(0, 0, w, h);

      try {
        const blob = base64ToBlob(wavBase64, "audio/wav");
        const arr = await blob.arrayBuffer();
        const audioCtx = new AudioContext();
        const decoded = await audioCtx.decodeAudioData(arr);
        await audioCtx.close();
        if (cancelled) return;

        const ch = decoded.getChannelData(0);
        const step = Math.max(1, Math.floor(ch.length / w));
        const mid = h / 2;

        // Upper wave (#3b82f6)
        ctx.fillStyle = "rgba(59, 130, 246, 0.72)";
        ctx.beginPath();
        ctx.moveTo(0, mid);
        for (let x = 0; x < w; x++) {
          let maxVal = 0;
          const start = x * step;
          for (let j = 0; j < step && start + j < ch.length; j++) {
            const v = Math.abs(ch[start + j]);
            if (v > maxVal) maxVal = v;
          }
          ctx.lineTo(x, mid - maxVal * (mid - 4));
        }
        ctx.lineTo(w, mid);
        ctx.closePath();
        ctx.fill();

        // Lower mirror (#8b5cf6)
        ctx.fillStyle = "rgba(139, 92, 246, 0.30)";
        ctx.beginPath();
        ctx.moveTo(0, mid);
        for (let x = 0; x < w; x++) {
          let maxVal = 0;
          const start = x * step;
          for (let j = 0; j < step && start + j < ch.length; j++) {
            const v = Math.abs(ch[start + j]);
            if (v > maxVal) maxVal = v;
          }
          ctx.lineTo(x, mid + maxVal * (mid - 4));
        }
        ctx.lineTo(w, mid);
        ctx.closePath();
        ctx.fill();

        // Center line
        ctx.strokeStyle = borderColor;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, mid);
        ctx.lineTo(w, mid);
        ctx.stroke();
      } catch {
        ctx.strokeStyle = borderColor;
        ctx.beginPath();
        ctx.moveTo(0, h / 2);
        ctx.lineTo(w, h / 2);
        ctx.stroke();
      }
    }
    renderWave();
    return () => {
      cancelled = true;
    };
  }, [wavBase64, bgColor, borderColor]);

  return (
    <canvas
      ref={canvasRef}
      width={720}
      height={height}
      style={{
        width: "100%",
        height: `${height}px`,
        borderRadius: "6px",
        display: "block",
        margin: "4px 0 8px",
      }}
    />
  );
};
