import { useMemo, useState } from "react";
import { useConsultationChat, type ChatMessage } from "@/lib/useConsultationChat";
import { messagesKey } from "@/lib/storage";
import type { ComprehensiveTrainingPlan } from "@/lib/types";
import { ChatThread, Chips, ChatComposer } from "./ChatThread";

const SUGGESTIONS = [
  "How do I start the first protocol?",
  "What if a visitor shows up?",
  "Can we make week 1 lighter?",
  "Show me the emergency steps",
];

export function PostChat({
  consultationId,
  petName,
  ownerFirst,
  onViewPlan,
  onPlanRevised,
}: {
  consultationId: string;
  petName: string;
  ownerFirst: string;
  onViewPlan: () => void;
  /** The agent revised the plan in response to a follow-up message. */
  onPlanRevised: (plan: ComprehensiveTrainingPlan) => void;
}) {
  const [input, setInput] = useState("");

  const initialMessages = useMemo<ChatMessage[]>(
    () => [
      {
        id: "plan-intro",
        role: "assistant",
        text: `${petName}'s plan is ready to go, ${ownerFirst}. Ask me anything — how to start a protocol, what to do in a tough moment, or how to tweak the plan to fit your week.`,
      },
    ],
    [petName, ownerFirst]
  );

  // Same consultation id -> the backend continues from the full stored history,
  // so this follow-up chat is aware of the plan it just generated and can revise it.
  const { messages, status, send: sendMessage } = useConsultationChat({
    consultationId,
    initialMessages,
    onPlan: onPlanRevised,
    storageKey: messagesKey(consultationId, "post"),
  });

  const isStreaming = status !== "ready";
  const ready = status === "ready";

  function send(text: string) {
    const t = text.trim();
    if (!t || isStreaming) return;
    setInput("");
    void sendMessage(t);
  }

  return (
    <div
      style={{
        maxWidth: 720,
        margin: "0 auto",
        padding: "24px 18px",
        display: "flex",
        flexDirection: "column",
        height: "calc(100vh - 63px)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
        <div>
          <div style={{ fontFamily: "var(--font-head)", fontSize: 18, fontWeight: 600 }}>
            {petName}&apos;s plan · follow-up
          </div>
          <div style={{ fontSize: 13, color: "var(--muted)" }}>
            Ask anything or adjust the plan
          </div>
        </div>
        <button
          onClick={onViewPlan}
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            color: "var(--ink)",
            fontSize: 13,
            fontWeight: 600,
            padding: "7px 13px",
            borderRadius: 99,
          }}
        >
          📄 View plan
        </button>
      </div>

      <ChatThread messages={messages} typing={status === "submitting"} />

      <div style={{ paddingTop: 12 }}>
        {ready && <Chips options={SUGGESTIONS} onPick={send} />}
        <ChatComposer
          value={input}
          onChange={setInput}
          onSend={() => send(input)}
          placeholder="Ask about a step, or how to adjust the plan…"
          disabled={isStreaming}
        />
      </div>
    </div>
  );
}
