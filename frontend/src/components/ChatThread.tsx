import { useEffect, useLayoutEffect, useRef, useState } from "react";
import type { ChatMessage } from "@/lib/useConsultationChat";
import { TypingDots } from "./TypingDots";
import { Markdown } from "./Markdown";

const bubbleUser = {
  maxWidth: "80%",
  background: "var(--accent)",
  color: "var(--accent-ink)",
  padding: "12px 16px",
  borderRadius: "var(--radius)",
  borderBottomRightRadius: 4,
  fontSize: 15,
  lineHeight: 1.5,
  whiteSpace: "pre-wrap",
} as const;

const bubbleAi = {
  maxWidth: "80%",
  background: "var(--surface)",
  color: "var(--ink)",
  padding: "12px 16px",
  borderRadius: "var(--radius)",
  borderBottomLeftRadius: 4,
  border: "1px solid var(--border)",
  fontSize: 15,
  lineHeight: 1.55,
} as const;

export function ChatThread({
  messages,
  typing,
}: {
  messages: ChatMessage[];
  typing: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, typing]);

  return (
    <div
      ref={ref}
      className="pm-scroll"
      style={{ flex: 1, overflowY: "auto", padding: "4px 4px 8px" }}
    >
      {messages
        // Hide the empty assistant placeholder while we wait — the TypingDots
        // below stands in for it, so we never show two bubbles at once.
        .filter((m) => m.role === "user" || m.text.trim() !== "")
        .map((m) => {
          const isUser = m.role === "user";
          return (
            <div
              key={m.id}
              style={{
                display: "flex",
                justifyContent: isUser ? "flex-end" : "flex-start",
                marginBottom: 14,
              }}
            >
              <div style={isUser ? bubbleUser : bubbleAi}>
                {isUser ? m.text : <Markdown>{m.text}</Markdown>}
              </div>
            </div>
          );
        })}
      {typing && <TypingDots />}
    </div>
  );
}

const chip = {
  background: "var(--surface)",
  border: "1px solid var(--accent)",
  color: "var(--accent)",
  fontSize: 14,
  fontWeight: 600,
  padding: "9px 15px",
  borderRadius: 99,
} as const;

const chipSelected = {
  ...chip,
  background: "var(--accent)",
  color: "var(--accent-ink)",
} as const;

/**
 * Quick-reply chips. Single-select by default (tapping a chip sends it
 * immediately). With `multiSelect`, chips toggle and a confirm button sends the
 * combined selection as one message.
 */
export function Chips({
  options,
  onPick,
  multiSelect = false,
}: {
  options: string[];
  onPick: (text: string) => void;
  multiSelect?: boolean;
}) {
  const [selected, setSelected] = useState<string[]>([]);

  if (!multiSelect) {
    return (
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 12 }}>
        {options.map((o) => (
          <button key={o} style={chip} onClick={() => onPick(o)}>
            {o}
          </button>
        ))}
      </div>
    );
  }

  const toggle = (o: string) =>
    setSelected((prev) => (prev.includes(o) ? prev.filter((x) => x !== o) : [...prev, o]));

  const confirm = () => {
    if (!selected.length) return;
    onPick(selected.join(", "));
    setSelected([]);
  };

  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        {options.map((o) => {
          const isSel = selected.includes(o);
          return (
            <button
              key={o}
              style={isSel ? chipSelected : chip}
              onClick={() => toggle(o)}
              aria-pressed={isSel}
            >
              {isSel ? "✓ " : ""}
              {o}
            </button>
          );
        })}
      </div>
      {selected.length > 0 && (
        <button
          onClick={confirm}
          style={{
            marginTop: 10,
            background: "var(--accent)",
            color: "var(--accent-ink)",
            border: "none",
            fontSize: 14,
            fontWeight: 700,
            padding: "9px 18px",
            borderRadius: 99,
          }}
        >
          Send {selected.length} {selected.length === 1 ? "answer" : "answers"} →
        </button>
      )}
    </div>
  );
}

export function ChatComposer({
  value,
  onChange,
  onSend,
  placeholder,
  disabled,
}: {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  placeholder: string;
  disabled?: boolean;
}) {
  const LINE_HEIGHT = 21;
  const MAX_LINES = 5;
  const ref = useRef<HTMLTextAreaElement>(null);

  // Auto-grow the textarea with its content, capped at MAX_LINES (then scroll).
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    const maxH = LINE_HEIGHT * MAX_LINES;
    el.style.height = `${Math.min(el.scrollHeight, maxH)}px`;
    el.style.overflowY = el.scrollHeight > maxH ? "auto" : "hidden";
  }, [value]);

  return (
    <div
      style={{
        display: "flex",
        gap: 10,
        alignItems: "flex-end",
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius)",
        padding: "8px 8px 8px 16px",
      }}
    >
      <textarea
        ref={ref}
        rows={1}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          // Enter sends; Shift+Enter inserts a newline.
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            onSend();
          }
        }}
        placeholder={placeholder}
        style={{
          flex: 1,
          border: "none",
          background: "transparent",
          fontSize: 15,
          lineHeight: `${LINE_HEIGHT}px`,
          color: "var(--ink)",
          padding: "8px 0",
          margin: 0,
          resize: "none",
          outline: "none",
          fontFamily: "inherit",
          maxHeight: LINE_HEIGHT * MAX_LINES,
          overflowY: "hidden",
        }}
      />
      <button
        onClick={onSend}
        disabled={disabled}
        style={{
          background: "var(--accent)",
          color: "var(--accent-ink)",
          border: "none",
          width: 40,
          height: 40,
          borderRadius: "50%",
          fontSize: 17,
          flexShrink: 0,
          opacity: disabled ? 0.5 : 1,
        }}
      >
        ↑
      </button>
    </div>
  );
}
