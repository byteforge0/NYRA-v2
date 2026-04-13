export type ServerMessageType =
  | "assistant_text"
  | "assistant_audio"
  | "tool_result"
  | "status"
  | "error"
  | "pong"
  | "transcript";

export interface ServerMessage {
  type: ServerMessageType;
  text: string;
  mime_type?: string;
}

export type AssistantState = "idle" | "listening" | "thinking" | "speaking";

export type LanguageMode = "english" | "german" | "auto";

export interface AppSettings {
  assistantName: string;
  languageMode: LanguageMode;
  alwaysListening: boolean;
  ttsEnabled: boolean;
  animationIntensity: number;
  micSensitivity: number;
}