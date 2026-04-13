import { useEffect, useMemo, useRef, useState } from "react";
import {
  Globe,
  MessageSquare,
  Mic,
  MicOff,
  Send,
  Settings,
  Square,
  Volume2,
  VolumeX,
  X,
} from "lucide-react";
import type {
  AppSettings,
  AssistantState,
  LanguageMode,
  ServerMessage,
} from "./types";

type ChatItem = {
  role: "user" | "assistant" | "system";
  text: string;
};

const DEFAULT_SETTINGS: AppSettings = {
  assistantName: "NYRA",
  languageMode: "english",
  alwaysListening: true,
  ttsEnabled: true,
  animationIntensity: 0.65,
  micSensitivity: 0.018,
};

function getLanguageLabel(mode: LanguageMode) {
  if (mode === "english") return "English";
  if (mode === "german") return "Deutsch";
  return "Auto";
}

function OrbitalMesh({
  state,
  micLevel,
  outputLevel,
  intensity,
}: {
  state: AssistantState;
  micLevel: number;
  outputLevel: number;
  intensity: number;
}) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let frame = 0;
    let width = 0;
    let height = 0;
    let t = 0;
    let dpr = Math.min(window.devicePixelRatio || 1, 2);

    const nodes = Array.from({ length: 75 }, (_, i) => ({
      angle: (i / 75) * Math.PI * 2,
      radius: 90 + Math.random() * 240,
      size: 1 + Math.random() * 2.2,
      speed: 0.05 + Math.random() * 0.12,
      offset: Math.random() * 1000,
    }));

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const render = () => {
      t += 0.005;
      const cx = width / 2;
      const cy = height / 2;

      ctx.clearRect(0, 0, width, height);

      let spread = 1;
      let motion = 0.08;
      let lineAlpha = 0.12;
      let nodeAlpha = 0.7;

      if (state === "idle") {
        spread = 0.9;
        motion = 0.05;
        lineAlpha = 0.08;
        nodeAlpha = 0.5;
      } else if (state === "listening") {
        spread = 0.95 + micLevel * (0.15 + intensity * 0.18);
        motion = 0.06 + micLevel * 0.08;
        lineAlpha = 0.11 + micLevel * 0.06;
        nodeAlpha = 0.62 + micLevel * 0.14;
      } else if (state === "thinking") {
        spread = 0.88;
        motion = 0.04;
        lineAlpha = 0.1;
        nodeAlpha = 0.58;
      } else if (state === "speaking") {
        spread = 1.05 + outputLevel * (0.35 + intensity * 0.22);
        motion = 0.08 + outputLevel * 0.06;
        lineAlpha = 0.16 + outputLevel * 0.05;
        nodeAlpha = 0.78 + outputLevel * 0.1;
      }

      const positions = nodes.map((n) => {
        const wave =
          Math.sin(t * (0.8 + n.speed) + n.offset) * 10 +
          Math.cos(t * 0.45 + n.offset) * 4;

        const radius = n.radius * spread + wave;
        const angle = n.angle + t * n.speed + Math.sin(t + n.offset) * motion;

        return {
          x: cx + Math.cos(angle) * radius,
          y: cy + Math.sin(angle) * radius,
          size: n.size,
        };
      });

      const glow = ctx.createRadialGradient(cx, cy, 0, cx, cy, 420);
      glow.addColorStop(0, "rgba(255,255,255,0.08)");
      glow.addColorStop(0.25, "rgba(255,255,255,0.025)");
      glow.addColorStop(1, "rgba(255,255,255,0)");
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(cx, cy, 420, 0, Math.PI * 2);
      ctx.fill();

      ctx.lineWidth = 1;

      for (let i = 0; i < positions.length; i += 1) {
        for (let j = i + 1; j < positions.length; j += 1) {
          const dx = positions[i].x - positions[j].x;
          const dy = positions[i].y - positions[j].y;
          const dist = Math.hypot(dx, dy);

          if (dist < 110) {
            const alpha = Math.max(0, lineAlpha - dist / 1100);
            ctx.strokeStyle = `rgba(255,255,255,${alpha})`;
            ctx.beginPath();
            ctx.moveTo(positions[i].x, positions[i].y);
            ctx.lineTo(positions[j].x, positions[j].y);
            ctx.stroke();
          }
        }
      }

      for (const p of positions) {
        ctx.fillStyle = `rgba(255,255,255,${nodeAlpha})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
      }

      const coreRadius =
        state === "speaking"
          ? 30 + outputLevel * 9
          : state === "listening"
            ? 22 + micLevel * 7
            : 20;

      const core = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreRadius * 3.2);
      core.addColorStop(0, "rgba(255,255,255,1)");
      core.addColorStop(0.18, "rgba(255,255,255,0.95)");
      core.addColorStop(0.42, "rgba(255,255,255,0.16)");
      core.addColorStop(1, "rgba(255,255,255,0)");
      ctx.fillStyle = core;
      ctx.beginPath();
      ctx.arc(cx, cy, coreRadius * 3.2, 0, Math.PI * 2);
      ctx.fill();

      frame = requestAnimationFrame(render);
    };

    resize();
    window.addEventListener("resize", resize);
    render();

    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("resize", resize);
    };
  }, [state, micLevel, outputLevel, intensity]);

  return <canvas ref={canvasRef} className="particle-canvas" />;
}

function float32ToWav(samples: Float32Array, sampleRate: number): Blob {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  const writeString = (offset: number, text: string) => {
    for (let i = 0; i < text.length; i += 1) {
      view.setUint8(offset + i, text.charCodeAt(i));
    }
  };

  writeString(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, "data");
  view.setUint32(40, samples.length * 2, true);

  let offset = 44;
  for (let i = 0; i < samples.length; i += 1) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    offset += 2;
  }

  return new Blob([view], { type: "audio/wav" });
}

async function blobToBase64(blob: Blob): Promise<string> {
  const arrayBuffer = await blob.arrayBuffer();
  let binary = "";
  const bytes = new Uint8Array(arrayBuffer);
  const chunkSize = 0x8000;

  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunkSize));
  }

  return btoa(binary);
}

export default function App() {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(true);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatItem[]>([]);
  const [wsStatus, setWsStatus] = useState("Connecting...");
  const [assistantState, setAssistantState] = useState<AssistantState>("idle");
  const [micRunning, setMicRunning] = useState(false);
  const [micLevel, setMicLevel] = useState(0);
  const [outputLevel, setOutputLevel] = useState(0);

  const [settings, setSettings] = useState<AppSettings>(() => {
    const raw = localStorage.getItem("nyra-settings");
    if (!raw) return DEFAULT_SETTINGS;
    try {
      return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) } as AppSettings;
    } catch {
      return DEFAULT_SETTINGS;
    }
  });

  const socketRef = useRef<WebSocket | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const outputAnimationRef = useRef<number | null>(null);

  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);

  const chunksRef = useRef<Float32Array[]>([]);
  const isCapturingSpeechRef = useRef(false);
  const lastVoiceAtRef = useRef(0);
  const finalizingRef = useRef(false);
  const speakingRef = useRef(false);

  const wsUrl = useMemo(() => "ws://127.0.0.1:8000/ws", []);

  useEffect(() => {
    localStorage.setItem("nyra-settings", JSON.stringify(settings));
  }, [settings]);

  useEffect(() => {
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      setWsStatus("Connected");
    };

    socket.onclose = () => {
      setWsStatus("Disconnected");
      setAssistantState("idle");
    };

    socket.onerror = () => {
      setWsStatus("Error");
      setAssistantState("idle");
    };

    socket.onmessage = async (event) => {
      const data = JSON.parse(event.data) as ServerMessage;

      if (data.type === "status") {
        setMessages((prev) => [...prev, { role: "system", text: data.text }]);

        const lower = data.text.toLowerCase();
        if (lower.includes("thinking") || lower.includes("denke")) {
          setAssistantState("thinking");
        } else if (lower.includes("listening") || lower.includes("höre")) {
          setAssistantState("listening");
        }

        return;
      }

      if (data.type === "transcript") {
        setMessages((prev) => [...prev, { role: "user", text: data.text }]);
        return;
      }

      if (
        data.type === "assistant_text" ||
        data.type === "tool_result" ||
        data.type === "error"
      ) {
        setMessages((prev) => [...prev, { role: "assistant", text: data.text }]);
        return;
      }

      if (data.type === "assistant_audio") {
        if (!settings.ttsEnabled) return;

        stopSpeaking();

        try {
          const mimeType = data.mime_type || "audio/mpeg";
          const src = `data:${mimeType};base64,${data.text}`;
          const audio = new Audio(src);
          currentAudioRef.current = audio;
          speakingRef.current = true;
          setAssistantState("speaking");
          startOutputAnimation();

          audio.onended = () => {
            speakingRef.current = false;
            stopOutputAnimation();
            currentAudioRef.current = null;
            setAssistantState(micRunning ? "listening" : "idle");
          };

          audio.onerror = () => {
            speakingRef.current = false;
            stopOutputAnimation();
            currentAudioRef.current = null;
            setAssistantState(micRunning ? "listening" : "idle");
          };

          await audio.play();
        } catch {
          speakingRef.current = false;
          stopOutputAnimation();
          setAssistantState(micRunning ? "listening" : "idle");
        }
      }
    };

    return () => {
      socket.close();
    };
  }, [wsUrl, settings.ttsEnabled, micRunning]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const startOutputAnimation = () => {
    let t = 0;

    const tick = () => {
      t += 0.08;
      const value =
        0.22 +
        Math.abs(Math.sin(t * 1.08)) * 0.28 +
        Math.abs(Math.cos(t * 0.72)) * 0.1;

      setOutputLevel(Math.min(value, 1));
      outputAnimationRef.current = requestAnimationFrame(tick);
    };

    if (outputAnimationRef.current) {
      cancelAnimationFrame(outputAnimationRef.current);
    }

    tick();
  };

  const stopOutputAnimation = () => {
    if (outputAnimationRef.current) {
      cancelAnimationFrame(outputAnimationRef.current);
      outputAnimationRef.current = null;
    }
    setOutputLevel(0);
  };

  const stopSpeaking = () => {
    speakingRef.current = false;
    stopOutputAnimation();

    if (currentAudioRef.current) {
      try {
        currentAudioRef.current.pause();
        currentAudioRef.current.currentTime = 0;
      } catch {}
      currentAudioRef.current = null;
    }

    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: "stop_tts" }));
    }

    setAssistantState(micRunning ? "listening" : "idle");
  };

  const finalizeSegment = async () => {
    if (finalizingRef.current) return;
    if (!chunksRef.current.length) return;
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) return;

    finalizingRef.current = true;

    const chunks = chunksRef.current;
    chunksRef.current = [];

    let totalLength = 0;
    for (const chunk of chunks) totalLength += chunk.length;

    if (totalLength < 3200) {
      finalizingRef.current = false;
      isCapturingSpeechRef.current = false;
      return;
    }

    const merged = new Float32Array(totalLength);
    let offset = 0;
    for (const chunk of chunks) {
      merged.set(chunk, offset);
      offset += chunk.length;
    }

    const sampleRate = audioContextRef.current?.sampleRate ?? 16000;
    const wavBlob = float32ToWav(merged, sampleRate);
    const audioBase64 = await blobToBase64(wavBlob);

    socketRef.current.send(
      JSON.stringify({
        type: "audio_chunk",
        audio_base64: audioBase64,
        language_mode: settings.languageMode,
        tts_enabled: settings.ttsEnabled,
      })
    );

    isCapturingSpeechRef.current = false;
    finalizingRef.current = false;
  };

  const startMicrophone = async () => {
    if (micRunning) return;

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const context = new AudioContext({ sampleRate: 16000 });
    const source = context.createMediaStreamSource(stream);
    const processor = context.createScriptProcessor(4096, 1, 1);

    processor.onaudioprocess = async (event) => {
      const pcm = new Float32Array(event.inputBuffer.getChannelData(0));

      let sum = 0;
      for (let i = 0; i < pcm.length; i += 1) {
        sum += pcm[i] * pcm[i];
      }
      const rms = Math.sqrt(sum / pcm.length);
      const visualLevel = Math.min(rms * 10, 1);

      setMicLevel((prev) => prev * 0.72 + visualLevel * 0.28);

      const threshold = settings.micSensitivity;
      const now = performance.now();

      if (rms >= threshold) {
        if (speakingRef.current) {
          stopSpeaking();
        }

        if (!isCapturingSpeechRef.current) {
          isCapturingSpeechRef.current = true;
          chunksRef.current = [];
        }

        lastVoiceAtRef.current = now;
        chunksRef.current.push(pcm);

        if (assistantState !== "thinking") {
          setAssistantState("listening");
        }
        return;
      }

      if (isCapturingSpeechRef.current) {
        chunksRef.current.push(pcm);

        if (now - lastVoiceAtRef.current > 800) {
          await finalizeSegment();
        }
      } else {
        setMicLevel((prev) => prev * 0.93);
      }
    };

    source.connect(processor);
    processor.connect(context.destination);

    mediaStreamRef.current = stream;
    audioContextRef.current = context;
    processorRef.current = processor;

    setMicRunning(true);
    setAssistantState("listening");
  };

  const stopMicrophone = async () => {
    processorRef.current?.disconnect();
    mediaStreamRef.current?.getTracks().forEach((track) => track.stop());

    if (audioContextRef.current) {
      await audioContextRef.current.close().catch(() => {});
    }

    processorRef.current = null;
    audioContextRef.current = null;
    mediaStreamRef.current = null;
    chunksRef.current = [];
    isCapturingSpeechRef.current = false;
    finalizingRef.current = false;

    setMicRunning(false);
    setMicLevel(0);
    setAssistantState("idle");
  };

  useEffect(() => {
    if (settings.alwaysListening && !micRunning) {
      startMicrophone().catch(() => {
        setMessages((prev) => [
          ...prev,
          { role: "system", text: "Microphone could not be started." },
        ]);
      });
    }

    if (!settings.alwaysListening && micRunning) {
      stopMicrophone().catch(() => {});
    }
  }, [settings.alwaysListening]);

  useEffect(() => {
    return () => {
      stopSpeaking();
      stopMicrophone().catch(() => {});
    };
  }, []);

  const toggleListening = () => {
    setSettings((prev) => ({ ...prev, alwaysListening: !prev.alwaysListening }));
  };

  const sendMessage = (override?: string) => {
    const text = (override ?? input).trim();
    if (!text || !socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    stopSpeaking();
    setAssistantState("thinking");
    setMessages((prev) => [...prev, { role: "user", text }]);
    socketRef.current.send(
      JSON.stringify({
        type: "user_text",
        text,
        language_mode: settings.languageMode,
        tts_enabled: settings.ttsEnabled,
      })
    );
    setInput("");
  };

  const stateLabel =
    assistantState === "idle"
      ? "Idle"
      : assistantState === "listening"
        ? "Listening"
        : assistantState === "thinking"
          ? "Thinking"
          : "Speaking";

  return (
    <div className="app-shell">
      <OrbitalMesh
        state={assistantState}
        micLevel={micLevel}
        outputLevel={outputLevel}
        intensity={settings.animationIntensity}
      />

      <div className="top-left">
        <div className="brand">{settings.assistantName}</div>
        <div className="subline">
          {stateLabel} · {wsStatus} · {getLanguageLabel(settings.languageMode)}
        </div>
      </div>

      <div className="top-right">
        <button
          className={`mini-btn ${micRunning ? "active" : ""}`}
          onClick={toggleListening}
          title="Microphone"
        >
          {micRunning ? <MicOff size={14} /> : <Mic size={14} />}
        </button>

        <button
          className={`mini-btn ${settings.ttsEnabled ? "active" : ""}`}
          onClick={() =>
            setSettings((prev) => ({ ...prev, ttsEnabled: !prev.ttsEnabled }))
          }
          title="Speech"
        >
          {settings.ttsEnabled ? <Volume2 size={14} /> : <VolumeX size={14} />}
        </button>

        <button className="mini-btn" onClick={stopSpeaking} title="Stop speaking">
          <Square size={12} />
        </button>

        <button
          className="mini-btn"
          onClick={() => setChatOpen((prev) => !prev)}
          title="Chat"
        >
          <MessageSquare size={14} />
        </button>

        <button
          className="mini-btn"
          onClick={() => setSettingsOpen(true)}
          title="Settings"
        >
          <Settings size={14} />
        </button>
      </div>

      {chatOpen && (
        <div className="chat-overlay">
          <div className="chat-header">
            <div>
              <div className="chat-title">{settings.assistantName}</div>
              <div className="chat-subtitle">English primary · German secondary</div>
            </div>

            <button className="mini-btn" onClick={() => setChatOpen(false)} title="Close">
              <X size={14} />
            </button>
          </div>

          <div className="chat-box">
            {messages.map((message, index) => (
              <div
                key={`${message.role}-${index}-${message.text}`}
                className={`msg ${message.role}`}
              >
                <div className="msg-label">
                  {message.role === "user"
                    ? "You"
                    : message.role === "assistant"
                      ? settings.assistantName
                      : "System"}
                </div>
                <div className="msg-text">{message.text}</div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>

          <div className="composer">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") sendMessage();
              }}
              placeholder={
                settings.languageMode === "german"
                  ? "Schreib etwas…"
                  : "Type something…"
              }
            />
            <button className="send-btn" onClick={() => sendMessage()}>
              <Send size={14} />
            </button>
          </div>
        </div>
      )}

      {settingsOpen && (
        <div className="settings-backdrop" onClick={() => setSettingsOpen(false)}>
          <div className="settings-panel" onClick={(e) => e.stopPropagation()}>
            <div className="settings-header">
              <div>
                <div className="settings-title">NYRA Settings</div>
                <div className="settings-subtitle">Voice, language, behavior</div>
              </div>
              <button className="mini-btn" onClick={() => setSettingsOpen(false)}>
                <X size={14} />
              </button>
            </div>

            <div className="settings-grid">
              <label className="setting-item">
                <span>Name</span>
                <input
                  value={settings.assistantName}
                  onChange={(e) =>
                    setSettings((prev) => ({
                      ...prev,
                      assistantName: e.target.value || "NYRA",
                    }))
                  }
                />
              </label>

              <label className="setting-item">
                <span>Language</span>
                <div className="segmented">
                  {(["english", "german", "auto"] as LanguageMode[]).map((mode) => (
                    <button
                      type="button"
                      key={mode}
                      className={
                        settings.languageMode === mode
                          ? "segmented-btn active"
                          : "segmented-btn"
                      }
                      onClick={() =>
                        setSettings((prev) => ({ ...prev, languageMode: mode }))
                      }
                    >
                      {mode === "english" ? "EN" : mode === "german" ? "DE" : "AUTO"}
                    </button>
                  ))}
                </div>
              </label>

              <label className="setting-item checkbox-row">
                <span>Always listening</span>
                <input
                  type="checkbox"
                  checked={settings.alwaysListening}
                  onChange={(e) =>
                    setSettings((prev) => ({
                      ...prev,
                      alwaysListening: e.target.checked,
                    }))
                  }
                />
              </label>

              <label className="setting-item checkbox-row">
                <span>Speech output</span>
                <input
                  type="checkbox"
                  checked={settings.ttsEnabled}
                  onChange={(e) =>
                    setSettings((prev) => ({
                      ...prev,
                      ttsEnabled: e.target.checked,
                    }))
                  }
                />
              </label>

              <label className="setting-item">
                <span>Animation intensity</span>
                <input
                  type="range"
                  min="0.2"
                  max="1"
                  step="0.01"
                  value={settings.animationIntensity}
                  onChange={(e) =>
                    setSettings((prev) => ({
                      ...prev,
                      animationIntensity: Number(e.target.value),
                    }))
                  }
                />
              </label>

              <label className="setting-item">
                <span>Mic sensitivity</span>
                <input
                  type="range"
                  min="0.005"
                  max="0.06"
                  step="0.001"
                  value={settings.micSensitivity}
                  onChange={(e) =>
                    setSettings((prev) => ({
                      ...prev,
                      micSensitivity: Number(e.target.value),
                    }))
                  }
                />
              </label>

              <div className="setting-note">
                <Globe size={14} />
                <span>
                  English is primary. German also works. Auto mode follows the spoken input.
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}