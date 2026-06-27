import { useState } from "react";
import type { ComprehensiveTrainingPlan } from "@/lib/types";

export function TrainingPlan({
  plan,
  onAsk,
}: {
  plan: ComprehensiveTrainingPlan;
  onAsk: () => void;
}) {
  const [view, setView] = useState<"document" | "actionable">("document");
  const [done, setDone] = useState<Set<string>>(new Set());
  const isAction = view === "actionable";

  const keys: string[] = [];
  plan.individualized_plans.forEach((iss, i) =>
    iss.training_protocols.forEach((p, j) =>
      p.step_by_step.forEach((_, k) => keys.push(`${i}-${j}-${k}`))
    )
  );
  const total = keys.length;
  const doneCount = keys.filter((k) => done.has(k)).length;
  const pct = total ? Math.round((doneCount / total) * 100) : 0;

  const toggle = (k: string) =>
    setDone((prev) => {
      const next = new Set(prev);
      if (next.has(k)) next.delete(k);
      else next.add(k);
      return next;
    });

  const planDate = new Date().toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  const tabBase = {
    border: "none",
    fontSize: 13.5,
    fontWeight: 700,
    padding: "8px 18px",
    borderRadius: 99,
  } as const;

  return (
    <div style={{ maxWidth: 780, margin: "0 auto", padding: "34px 22px 80px" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: 16,
          flexWrap: "wrap",
          marginBottom: 8,
        }}
      >
        <div>
          <div
            style={{
              fontSize: 13,
              fontWeight: 700,
              letterSpacing: "0.04em",
              textTransform: "uppercase",
              color: "var(--accent)",
              marginBottom: 6,
            }}
          >
            Personalized training plan
          </div>
          <h2
            style={{
              fontFamily: "var(--font-head)",
              fontSize: 32,
              fontWeight: 600,
              letterSpacing: "-0.01em",
              margin: 0,
            }}
          >
            {plan.pet_name}&apos;s Plan
          </h2>
          <div style={{ fontSize: 14, color: "var(--muted)", marginTop: 4 }}>
            Prepared {planDate} · force-free, positive-reinforcement
          </div>
        </div>
        <button
          className="pm-no-print"
          onClick={() => window.print()}
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            color: "var(--ink)",
            fontSize: 13.5,
            fontWeight: 600,
            padding: "9px 15px",
            borderRadius: 99,
            whiteSpace: "nowrap",
          }}
        >
          ⬇ Download PDF
        </button>
      </div>

      <div
        className="pm-no-print"
        style={{
          display: "inline-flex",
          background: "var(--surface2)",
          border: "1px solid var(--border)",
          borderRadius: 99,
          padding: 4,
          margin: "18px 0 24px",
        }}
      >
        <button
          onClick={() => setView("document")}
          style={{
            ...tabBase,
            background: isAction ? "transparent" : "var(--accent)",
            color: isAction ? "var(--muted)" : "var(--accent-ink)",
          }}
        >
          Document
        </button>
        <button
          onClick={() => setView("actionable")}
          style={{
            ...tabBase,
            background: isAction ? "var(--accent)" : "transparent",
            color: isAction ? "var(--accent-ink)" : "var(--muted)",
          }}
        >
          Actionable
        </button>
      </div>

      {isAction && (
        <div
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius)",
            padding: "16px 18px",
            marginBottom: 22,
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              fontSize: 13.5,
              fontWeight: 600,
              marginBottom: 9,
            }}
          >
            <span>Your progress</span>
            <span style={{ color: "var(--accent)" }}>
              {doneCount} / {total} steps
            </span>
          </div>
          <div style={{ height: 8, background: "var(--accent-soft)", borderRadius: 99, overflow: "hidden" }}>
            <div
              style={{
                width: `${pct}%`,
                height: "100%",
                background: "var(--accent)",
                borderRadius: 99,
                transition: "width 0.3s ease",
              }}
            />
          </div>
        </div>
      )}

      <div
        style={{
          background: "var(--accent-soft)",
          borderRadius: "var(--radius)",
          padding: "22px 24px",
          marginBottom: 24,
        }}
      >
        <div
          style={{
            fontSize: 12.5,
            fontWeight: 700,
            letterSpacing: "0.04em",
            textTransform: "uppercase",
            color: "var(--accent)",
            marginBottom: 9,
          }}
        >
          Summary
        </div>
        <p style={{ fontSize: 16, lineHeight: 1.6, margin: 0 }}>{plan.triage_summary}</p>
      </div>

      {plan.individualized_plans.map((issue, i) => (
        <div
          key={i}
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius)",
            padding: 26,
            marginBottom: 20,
          }}
        >
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 7,
              background: "var(--accent-soft)",
              color: "var(--accent)",
              fontSize: 12,
              fontWeight: 700,
              padding: "5px 11px",
              borderRadius: 99,
              marginBottom: 12,
            }}
          >
            Behavior {i + 1}
          </div>
          <h3
            style={{
              fontFamily: "var(--font-head)",
              fontSize: 23,
              fontWeight: 600,
              letterSpacing: "-0.01em",
              margin: "0 0 18px",
            }}
          >
            {issue.issue_title}
          </h3>

          <div style={{ borderLeft: "3px solid var(--accent2)", padding: "2px 0 2px 16px", marginBottom: 22 }}>
            <div
              style={{
                fontSize: 12.5,
                fontWeight: 700,
                letterSpacing: "0.03em",
                textTransform: "uppercase",
                color: "var(--accent2)",
                marginBottom: 7,
              }}
            >
              Do this right now
            </div>
            <p style={{ fontSize: 15, lineHeight: 1.6, margin: "0 0 12px" }}>
              {issue.immediate_management.setup}
            </p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 7 }}>
              {issue.immediate_management.tools_needed.map((tool, t) => (
                <span
                  key={t}
                  style={{
                    fontSize: 12.5,
                    fontWeight: 600,
                    color: "var(--muted)",
                    background: "var(--surface2)",
                    border: "1px solid var(--border)",
                    padding: "5px 11px",
                    borderRadius: 99,
                  }}
                >
                  {tool}
                </span>
              ))}
            </div>
          </div>

          {issue.training_protocols.map((proto, j) => (
            <div
              key={j}
              style={{
                background: "var(--surface2)",
                border: "1px solid var(--border)",
                borderRadius: 12,
                padding: "18px 20px",
                marginBottom: 14,
              }}
            >
              <div style={{ fontFamily: "var(--font-head)", fontSize: 17, fontWeight: 600, marginBottom: 14 }}>
                {proto.skill_name}
              </div>
              {proto.step_by_step.map((step, k) => {
                const key = `${i}-${j}-${k}`;
                const checked = done.has(key);
                return (
                  <div key={k} style={{ display: "flex", gap: 13, alignItems: "flex-start", padding: "7px 0" }}>
                    {isAction ? (
                      <button
                        onClick={() => toggle(key)}
                        style={{
                          flexShrink: 0,
                          width: 24,
                          height: 24,
                          borderRadius: 7,
                          border: `2px solid ${checked ? "var(--accent)" : "var(--border)"}`,
                          background: checked ? "var(--accent)" : "transparent",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          marginTop: 1,
                          padding: 0,
                        }}
                      >
                        {checked && <span style={{ color: "#fff", fontSize: 13, fontWeight: 800 }}>✓</span>}
                      </button>
                    ) : (
                      <div
                        style={{
                          flexShrink: 0,
                          width: 24,
                          height: 24,
                          borderRadius: "50%",
                          background: "var(--accent-soft)",
                          color: "var(--accent)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontSize: 12.5,
                          fontWeight: 700,
                          marginTop: 1,
                        }}
                      >
                        {k + 1}
                      </div>
                    )}
                    <div
                      style={{
                        fontSize: 15,
                        lineHeight: 1.6,
                        color: checked ? "var(--muted)" : "var(--ink)",
                        textDecoration: checked ? "line-through" : "none",
                      }}
                    >
                      {step}
                    </div>
                  </div>
                );
              })}
              <div
                style={{
                  marginTop: 12,
                  paddingTop: 12,
                  borderTop: "1px dashed var(--border)",
                  fontSize: 13.5,
                  lineHeight: 1.55,
                  color: "var(--muted)",
                }}
              >
                <span style={{ fontWeight: 700, color: "var(--accent)" }}>Ready to advance when: </span>
                {proto.success_criteria}
              </div>
            </div>
          ))}
        </div>
      ))}

      <div
        style={{
          border: "1.5px solid var(--accent2)",
          borderRadius: "var(--radius)",
          padding: "22px 24px",
          marginBottom: 30,
        }}
      >
        <div
          style={{
            fontSize: 12.5,
            fontWeight: 700,
            letterSpacing: "0.04em",
            textTransform: "uppercase",
            color: "var(--accent2)",
            marginBottom: 9,
          }}
        >
          ⚠ In a tough moment
        </div>
        <p style={{ fontSize: 15, lineHeight: 1.6, margin: 0 }}>{plan.emergency_protocol}</p>
      </div>

      <div
        className="pm-no-print"
        style={{
          textAlign: "center",
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius)",
          padding: "28px 24px",
        }}
      >
        <div style={{ fontFamily: "var(--font-head)", fontSize: 20, fontWeight: 600, marginBottom: 6 }}>
          Questions about the plan?
        </div>
        <p style={{ fontSize: 14.5, color: "var(--muted)", margin: "0 0 18px" }}>
          Chat with your consultant to clarify a step or adjust the pace.
        </p>
        <button
          onClick={onAsk}
          style={{
            background: "var(--accent)",
            color: "var(--accent-ink)",
            border: "none",
            fontSize: 15,
            fontWeight: 700,
            padding: "13px 26px",
            borderRadius: 99,
          }}
        >
          Continue the conversation →
        </button>
      </div>
    </div>
  );
}
