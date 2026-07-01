import { useCallback, useEffect, useMemo, useState } from "react";
import { useConsultationChat, type ChatMessage } from "@/lib/useConsultationChat";
import { fetchFollowupSuggestions } from "@/lib/api";
import { messagesKey } from "@/lib/storage";
import type { ComprehensiveTrainingPlan } from "@/lib/types";
import { ChatThread, Chips, ChatComposer } from "./ChatThread";

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
  // Context-aware follow-up chips: fetched on mount and refreshed after each turn.
  const [chips, setChips] = useState<string[]>([]);
  // Set when the agent revises the plan, so we can surface a "view updated plan" CTA.
  const [planUpdated, setPlanUpdated] = useState(false);

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

  const handlePlan = useCallback(
    (plan: ComprehensiveTrainingPlan) => {
      setPlanUpdated(true);
      onPlanRevised(plan);
    },
    [onPlanRevised]
  );

  // Same consultation id -> the backend continues from the full stored history,
  // so this follow-up chat is aware of the plan it just generated and can revise it.
  const { messages, status, send: sendMessage } = useConsultationChat({
    consultationId,
    initialMessages,
    onPlan: handlePlan,
    storageKey: messagesKey(consultationId, "post"),
  });

  const isStreaming = status !== "ready";
  const ready = status === "ready";

  const refreshSuggestions = useCallback(() => {
    void fetchFollowupSuggestions(consultationId).then(setChips);
  }, [consultationId]);

  // Initial chips, tailored to the plan.
  useEffect(() => {
    let active = true;
    void fetchFollowupSuggestions(consultationId).then((s) => {
      if (active) setChips(s);
    });
    return () => {
      active = false;
    };
  }, [consultationId]);

  async function send(text: string) {
    const t = text.trim();
    if (!t || isStreaming) return;
    setInput("");
    setChips([]); // hide stale chips while the turn streams
    await sendMessage(t);
    refreshSuggestions(); // re-tailor chips to the latest exchange
  }

  function viewUpdatedPlan() {
    setPlanUpdated(false);
    onViewPlan();
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
        {planUpdated && (
          <button
            onClick={viewUpdatedPlan}
            style={{
              display: "block",
              width: "100%",
              background: "var(--accent-soft)",
              border: "1px solid var(--accent)",
              color: "var(--accent)",
              fontSize: 14,
              fontWeight: 700,
              padding: "11px 16px",
              borderRadius: "var(--radius)",
              marginBottom: 12,
            }}
          >
            ✓ Plan updated — view the updated plan →
          </button>
        )}
        {ready && chips.length > 0 && <Chips options={chips} onPick={send} />}
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
