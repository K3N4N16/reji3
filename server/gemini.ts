import { GoogleGenAI } from "@google/genai";
import { pcmToWav } from "./audio.ts";

const FALLBACK_TTS_CHAIN = [
  "gemini-3.8-flash-tts",
  "gemini-3.8-flash-lite-tts",
  "gemini-2.5-flash-preview-tts",
];

function getGeminiClient(): GoogleGenAI {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    throw new Error(
      "GEMINI_API_KEY tanımlı değil. Lütfen Settings > Secrets panelinden API anahtarınızı ekleyin."
    );
  }
  return new GoogleGenAI({
    apiKey,
    httpOptions: {
      headers: {
        "User-Agent": "aistudio-build",
      },
    },
  });
}

function extractAudioFromResponse(resp: unknown): { data: Buffer; mimeType: string } {
  const r = resp as {
    candidates?: Array<{
      content?: {
        parts?: Array<{
          inlineData?: { data?: string; mimeType?: string };
          text?: string;
        }>;
      };
    }>;
  };
  const parts = r?.candidates?.[0]?.content?.parts;
  if (!parts || parts.length === 0) {
    throw new Error("API yanıtında ses içeriği bulunamadı.");
  }
  for (const part of parts) {
    if (part.inlineData?.data) {
      return {
        data: Buffer.from(part.inlineData.data, "base64"),
        mimeType: part.inlineData.mimeType || "",
      };
    }
  }
  const textMsgs = parts.map((p) => p.text).filter(Boolean).join(" ");
  throw new Error(`Ses üretilemedi: ${textMsgs || "Boş yanıt"}`);
}

async function runTtsWithModelFallback<T>(
  requestedModel: string,
  fn: (client: GoogleGenAI, model: string) => Promise<T>
): Promise<{ result: T; usedModel: string }> {
  const client = getGeminiClient();
  const modelsToTry = [
    requestedModel,
    ...FALLBACK_TTS_CHAIN.filter((m) => m !== requestedModel),
  ];
  let lastErr: unknown = null;

  for (const mdl of modelsToTry) {
    try {
      const result = await fn(client, mdl);
      return { result, usedModel: mdl };
    } catch (err) {
      lastErr = err;
      const msg = String(err instanceof Error ? err.message : err).toUpperCase();
      if (
        msg.includes("404") ||
        msg.includes("NOT_FOUND") ||
        msg.includes("NOT SUPPORTED") ||
        msg.includes("IS NOT FOUND")
      ) {
        continue;
      }
      throw err;
    }
  }
  throw lastErr instanceof Error ? lastErr : new Error("TTS modeli çalıştırılamadı.");
}

export async function aiWriteAnons(topic: string, tone = "Enerjik radyo sunucusu"): Promise<string> {
  const client = getGeminiClient();
  const prompt =
    `İmaj FM radyosu için kısa, akıcı ve profesyonel bir Türkçe radyo anonsu yaz (maksimum 2-3 cümle). ` +
    `Konu / Şarkı: '${topic}'. Ton: ${tone}. ` +
    `Cümle başlarına uygun yerlere sadece şu duygu etiketlerinden koy: [excitedly], [normal], [whispers], [seriously]. ` +
    `Sadece okunacak anons metnini döndür, açıklama yazma.`;

  const resp = await client.models.generateContent({
    model: "gemini-4-hydrogen",
    contents: prompt,
  });
  return (resp.text ?? "").trim();
}

export async function ttsSingle(opts: {
  model: string;
  text: string;
  voice: string;
  lang: string;
  style: string;
}): Promise<{ wav: Buffer; usedModel: string }> {
  const fullText = opts.style.trim() ? `${opts.style.trim()}\n\n${opts.text}` : opts.text;
  const lc = opts.lang && opts.lang !== "otomatik" ? opts.lang : undefined;

  const { result, usedModel } = await runTtsWithModelFallback(opts.model, async (client, mdl) => {
    const speechConfig: Record<string, unknown> = {
      voiceConfig: {
        prebuiltVoiceConfig: { voiceName: opts.voice },
      },
    };
    if (lc) {
      speechConfig.languageCode = lc;
    }

    const r = await client.models.generateContent({
      model: mdl,
      contents: [
        {
          role: "user",
          parts: [
            opts.style.trim()
              ? {
                  text: opts.text,
                  speechMetadata: { style: opts.style.trim() },
                }
              : { text: fullText },
          ],
        },
      ],
      config: {
        responseModalities: ["AUDIO"],
        speechConfig: speechConfig as never,
      },
    });
    return extractAudioFromResponse(r);
  });

  return {
    wav: pcmToWav(result.data, result.mimeType),
    usedModel,
  };
}

export function parseDialogueTurns(
  text: string,
  sp1: string,
  sp2: string
): Array<{ speaker: string; utt: string }> {
  const turns: Array<{ speaker: string; utt: string }> = [];
  let curSp = sp1;
  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line) continue;
    if (line.toLowerCase().startsWith(`${sp1.toLowerCase()}:`)) {
      curSp = sp1;
      const utt = line.slice(sp1.length + 1).trim();
      if (utt) turns.push({ speaker: curSp, utt });
    } else if (line.toLowerCase().startsWith(`${sp2.toLowerCase()}:`)) {
      curSp = sp2;
      const utt = line.slice(sp2.length + 1).trim();
      if (utt) turns.push({ speaker: curSp, utt });
    } else {
      turns.push({ speaker: curSp, utt: line });
    }
  }
  return turns.length > 0 ? turns : [{ speaker: sp1, utt: text.trim() }];
}

export async function ttsMulti(opts: {
  model: string;
  text: string;
  sp1: string;
  v1: string;
  sp2: string;
  v2: string;
  lang: string;
}): Promise<{ wav: Buffer; usedModel: string }> {
  const turns = parseDialogueTurns(opts.text, opts.sp1, opts.sp2);
  const lc = opts.lang && opts.lang !== "otomatik" ? opts.lang : undefined;

  const makeSpeechConfig = () => {
    const sc: Record<string, unknown> = {
      multiSpeakerVoiceConfig: {
        speakerVoiceConfigs: [
          {
            speaker: opts.sp1,
            voiceConfig: { prebuiltVoiceConfig: { voiceName: opts.v1 } },
          },
          {
            speaker: opts.sp2,
            voiceConfig: { prebuiltVoiceConfig: { voiceName: opts.v2 } },
          },
        ],
      },
    };
    if (lc) sc.languageCode = lc;
    return sc;
  };

  // Layer 1: structured parts with speechMetadata
  try {
    const { result, usedModel } = await runTtsWithModelFallback(opts.model, async (client, mdl) => {
      const r = await client.models.generateContent({
        model: mdl,
        contents: [
          {
            role: "user",
            parts: turns.map((t) => ({
              text: `${t.speaker}: ${t.utt}`,
              speechMetadata: { speaker: t.speaker },
            })),
          },
        ],
        config: {
          responseModalities: ["AUDIO"],
          speechConfig: makeSpeechConfig() as never,
        },
      });
      return extractAudioFromResponse(r);
    });
    return { wav: pcmToWav(result.data, result.mimeType), usedModel };
  } catch (err1) {
    const m1 = String(err1 instanceof Error ? err1.message : err1).toUpperCase();
    if (!m1.includes("400") && !m1.includes("INVALID_ARGUMENT") && !m1.includes("SPEECH_METADATA")) {
      // Continue to Layer 2/3 anyway for robustness if it's multi-speaker format error
    }
  }

  // Layer 2: plain dialogue prompt
  try {
    const plainContents =
      `TTS the following conversation between ${opts.sp1} and ${opts.sp2}:\n` +
      turns.map((t) => `${t.speaker}: ${t.utt}`).join("\n");
    const targetModel = opts.model.startsWith("gemini-3") ? "gemini-3.8-flash-tts" : opts.model;
    const { result, usedModel } = await runTtsWithModelFallback(targetModel, async (client, mdl) => {
      const r = await client.models.generateContent({
        model: mdl,
        contents: plainContents,
        config: {
          responseModalities: ["AUDIO"],
          speechConfig: makeSpeechConfig() as never,
        },
      });
      return extractAudioFromResponse(r);
    });
    return { wav: pcmToWav(result.data, result.mimeType), usedModel };
  } catch {
    // Layer 3: sequential single-speaker synthesis + concat
    const { concatWavBuffers, generateSilenceWav } = await import("./audio.ts");
    const gap = await generateSilenceWav(150);
    const segs: Buffer[] = [];
    let lastModel = opts.model;
    for (let i = 0; i < turns.length; i++) {
      const t = turns[i];
      const v = t.speaker === opts.sp1 ? opts.v1 : opts.v2;
      const single = await ttsSingle({
        model: opts.model,
        text: t.utt,
        voice: v,
        lang: opts.lang,
        style: "",
      });
      lastModel = single.usedModel;
      if (i > 0) segs.push(gap);
      segs.push(single.wav);
    }
    const merged = await concatWavBuffers(segs, 0);
    return { wav: merged, usedModel: `${lastModel} (sıralı)` };
  }
}
