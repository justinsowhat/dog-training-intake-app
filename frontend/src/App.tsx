import { useEffect, useState } from "react";
import { Header } from "@/components/Header";
import { Landing } from "@/components/Landing";
import { IntakeForm } from "@/components/IntakeForm";
import { ChatIntake } from "@/components/ChatIntake";
import { Generating } from "@/components/Generating";
import { TrainingPlan } from "@/components/TrainingPlan";
import { PostChat } from "@/components/PostChat";
import { startConsultation, finalizePlan } from "@/lib/api";
import { buildIntakePayload, firstName, type CoreForm } from "@/lib/intake";
import { SESSION_KEY, loadJSON, messagesKey, removeKeys, saveJSON } from "@/lib/storage";
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

export default function App() {
  const [restored] = useState(restoreSession);
  const [screen, setScreen] = useState<Screen>(restored?.screen ?? "landing");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [consultationId, setConsultationId] = useState<string | null>(restored?.consultationId ?? null);
  const [form, setForm] = useState<CoreForm | null>(restored?.form ?? null);
  const [plan, setPlan] = useState<ComprehensiveTrainingPlan | null>(restored?.plan ?? null);

  // Persist session state so an in-progress intake survives a browser restart.
  useEffect(() => {
    saveJSON(SESSION_KEY, { screen, consultationId, form, plan });
  }, [screen, consultationId, form, plan]);

  const petName = form?.pet_name.trim() || "your animal";
  const ownerFirst = firstName(form?.owner_name ?? "");

  async function handleContinueIntake(f: CoreForm) {
    setForm(f);
    setBusy(true);
    setError(null);
    try {
      const id = await startConsultation(buildIntakePayload(f));
      setConsultationId(id);
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
    setScreen("landing");
    setConsultationId(null);
    setForm(null);
    setPlan(null);
    setError(null);
  }

  return (
    <main style={{ minHeight: "100vh" }}>
      <Header showRestart={screen !== "landing"} onRestart={restart} />
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
