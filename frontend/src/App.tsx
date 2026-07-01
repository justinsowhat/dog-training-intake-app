import { useEffect, useMemo, useState } from "react";
import { Header } from "@/components/Header";
import { Landing } from "@/components/Landing";
import { IntakeForm } from "@/components/IntakeForm";
import { ChatIntake } from "@/components/ChatIntake";
import { Generating } from "@/components/Generating";
import { TrainingPlan } from "@/components/TrainingPlan";
import { PostChat } from "@/components/PostChat";
import {
  startConsultation,
  finalizePlan,
  fetchConsultation,
  type ConsultationMessage,
} from "@/lib/api";
import { buildIntakePayload, firstName, formFromIntake, type CoreForm } from "@/lib/intake";
import { SESSION_KEY, loadJSON, messagesKey, removeKeys, saveJSON } from "@/lib/storage";
import type { ChatMessage } from "@/lib/useConsultationChat";
import type { ComprehensiveTrainingPlan } from "@/lib/types";

type Screen = "landing" | "intake" | "chat" | "generating" | "plan" | "post";

interface PersistedSession {
  screen: Screen;
  consultationId: string | null;
  form: CoreForm | null;
  plan: ComprehensiveTrainingPlan | null;
}

/** Restore a saved session, repairing states that can't be safely resumed. */
function restoreSession(): PersistedSession | null {
  const p = loadJSON<PersistedSession>(SESSION_KEY);
  if (!p) return null;
  let screen = p.screen;
  // "generating" is transient (the request may never have finished) -> back to chat.
  if (screen === "generating") screen = "chat";
  if (screen === "chat" && !p.consultationId) screen = p.form ? "intake" : "landing";
  if ((screen === "plan" || screen === "post") && !(p.consultationId && p.plan)) {
    screen = p.consultationId ? "chat" : "landing";
  }
  return { ...p, screen };
}

/** Map the server transcript to UI messages (the plan renders separately, so drop plan rows). */
function toChatMessages(msgs: ConsultationMessage[]): ChatMessage[] {
  return msgs
    .filter((m) => m.role === "user" || m.role === "assistant")
    .map((m, i) => ({ id: `srv-${i}`, role: m.role as "user" | "assistant", text: m.content }));
}

export default function App() {
  const [restored] = useState(restoreSession);
  // A `?c=` link points at a server-persisted consultation anyone can open/review.
  const urlConsultationId = useMemo(
    () => new URLSearchParams(window.location.search).get("c"),
    []
  );
  // Block with a loader only when the link points at a consultation we have no local
  // copy of (a different person/device); the owner's own session renders immediately.
  const needsHydration = !!urlConsultationId && urlConsultationId !== (restored?.consultationId ?? null);

  const [screen, setScreen] = useState<Screen>(restored?.screen ?? "landing");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [consultationId, setConsultationId] = useState<string | null>(restored?.consultationId ?? null);
  const [form, setForm] = useState<CoreForm | null>(restored?.form ?? null);
  const [plan, setPlan] = useState<ComprehensiveTrainingPlan | null>(restored?.plan ?? null);
  const [hydrating, setHydrating] = useState(needsHydration);

  // Hydrate from the server when a `?c=` link is present. Seeds the transcript caches
  // so the chat screens restore the authoritative server state (shared snapshot).
  useEffect(() => {
    if (!urlConsultationId) return;
    let active = true;
    void fetchConsultation(urlConsultationId).then((snap) => {
      if (!active) return;
      if (snap) {
        const transcript = toChatMessages(snap.messages);
        saveJSON(messagesKey(snap.consultation_id, "intake"), transcript);
        saveJSON(messagesKey(snap.consultation_id, "post"), transcript);
        setConsultationId(snap.consultation_id);
        setForm(formFromIntake(snap.intake_snapshot));
        setPlan(snap.plan);
        // Only route on a fresh open; don't yank the owner off their current screen.
        if (needsHydration) setScreen(snap.plan ? "plan" : "chat");
      }
      setHydrating(false);
    });
    return () => {
      active = false;
    };
  }, [urlConsultationId, needsHydration]);

  // Persist session state so an in-progress intake survives a browser restart.
  useEffect(() => {
    saveJSON(SESSION_KEY, { screen, consultationId, form, plan });
  }, [screen, consultationId, form, plan]);

  const petName = form?.pet_name.trim() || "your animal";
  const ownerFirst = firstName(form?.owner_name ?? "");
  const shareUrl = consultationId ? `${window.location.origin}/?c=${consultationId}` : undefined;

  async function handleContinueIntake(f: CoreForm) {
    setForm(f);
    setBusy(true);
    setError(null);
    try {
      const id = await startConsultation(buildIntakePayload(f));
      setConsultationId(id);
      // Make the address bar shareable from the moment the consultation exists.
      window.history.replaceState(null, "", `?c=${id}`);
      setScreen("chat");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not start consultation.");
    } finally {
      setBusy(false);
    }
  }

  async function handleGenerate() {
    if (!consultationId) return;
    setScreen("generating");
    setError(null);
    try {
      const p = await finalizePlan(consultationId);
      setPlan(p);
      setScreen("plan");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not generate the plan.");
      setScreen("chat");
    }
  }

  function restart() {
    const keys = [SESSION_KEY];
    if (consultationId) {
      keys.push(messagesKey(consultationId, "intake"), messagesKey(consultationId, "post"));
    }
    removeKeys(...keys);
    // Drop the `?c=` link so a fresh start isn't tied to the old consultation.
    window.history.replaceState(null, "", window.location.pathname);
    setScreen("landing");
    setConsultationId(null);
    setForm(null);
    setPlan(null);
    setError(null);
  }

  if (hydrating) {
    return (
      <main style={{ minHeight: "100vh" }}>
        <Header showRestart={false} onRestart={restart} />
        <div style={{ textAlign: "center", padding: "80px 20px", color: "var(--muted)" }}>
          Loading shared consultation…
        </div>
      </main>
    );
  }

  return (
    <main style={{ minHeight: "100vh" }}>
      <Header showRestart={screen !== "landing"} onRestart={restart} shareUrl={shareUrl} />
      {error && <div className="pm-error">{error}</div>}

      {screen === "landing" && <Landing onStart={() => setScreen("intake")} />}

      {screen === "intake" && (
        <IntakeForm busy={busy} onBack={() => setScreen("landing")} onContinue={handleContinueIntake} />
      )}

      {screen === "chat" && consultationId && (
        <ChatIntake
          consultationId={consultationId}
          petName={petName}
          ownerFirst={ownerFirst}
          planReady={!!plan}
          onGenerate={handleGenerate}
          onViewPlan={() => setScreen("plan")}
          onPlanProposed={setPlan}
        />
      )}

      {screen === "generating" && <Generating petName={petName} />}

      {screen === "plan" && plan && (
        <TrainingPlan plan={plan} onAsk={() => setScreen("post")} />
      )}

      {screen === "post" && consultationId && plan && (
        <PostChat
          consultationId={consultationId}
          petName={plan.pet_name}
          ownerFirst={ownerFirst}
          onViewPlan={() => setScreen("plan")}
          onPlanRevised={setPlan}
        />
      )}
    </main>
  );
}
