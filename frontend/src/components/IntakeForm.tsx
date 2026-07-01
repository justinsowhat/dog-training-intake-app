import { useState } from "react";
import { CoreForm, emptyForm, sampleForm } from "@/lib/intake";

const fieldLabel = {
  display: "block",
  fontSize: 13,
  fontWeight: 600,
  marginBottom: 7,
} as const;

const fieldInput = {
  width: "100%",
  padding: "11px 13px",
  border: "1px solid var(--border)",
  borderRadius: 10,
  fontSize: 15,
  color: "var(--ink)",
  background: "var(--surface2)",
} as const;

export function IntakeForm({
  busy,
  onBack,
  onContinue,
}: {
  busy: boolean;
  onBack: () => void;
  onContinue: (form: CoreForm) => void;
}) {
  const [form, setForm] = useState<CoreForm>(emptyForm);

  const set = (k: keyof CoreForm) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const canContinue =
    form.owner_name.trim() &&
    form.pet_name.trim() &&
    form.breed.trim() &&
    (form.species !== "Other" || form.other_species_description.trim()) &&
    !busy;

  return (
    <div style={{ maxWidth: 640, margin: "0 auto", padding: "44px 24px 72px" }}>
      <div
        style={{
          fontSize: 13,
          fontWeight: 700,
          letterSpacing: "0.04em",
          textTransform: "uppercase",
          color: "var(--accent)",
          marginBottom: 8,
        }}
      >
        Step 1 of 2 · The basics
      </div>
      <h2
        style={{
          fontFamily: "var(--font-head)",
          fontSize: 30,
          fontWeight: 600,
          letterSpacing: "-0.01em",
          margin: "0 0 6px",
        }}
      >
        Tell us about your animal
      </h2>
      <p style={{ fontSize: 15.5, lineHeight: 1.55, color: "var(--muted)", margin: "0 0 8px" }}>
        Just the essentials — we&apos;ll explore the behavior together in the next step.
      </p>
      <button
        onClick={() => setForm(sampleForm)}
        style={{
          background: "transparent",
          border: "1px dashed var(--border)",
          color: "var(--accent)",
          fontSize: 13,
          fontWeight: 600,
          padding: "7px 13px",
          borderRadius: 99,
          marginBottom: 26,
        }}
      >
        ✨ Use sample animal (Chance)
      </button>

      <div
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius)",
          padding: 26,
        }}
      >
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
          <label>
            <span style={fieldLabel}>Your name</span>
            <input style={fieldInput} value={form.owner_name} onChange={set("owner_name")} placeholder="Jamie Rivera" />
          </label>
          <label>
            <span style={fieldLabel}>Pet&apos;s name</span>
            <input style={fieldInput} value={form.pet_name} onChange={set("pet_name")} placeholder="Chance" />
          </label>
          <label>
            <span style={fieldLabel}>Species</span>
            <select style={fieldInput} value={form.species} onChange={set("species") as (e: React.ChangeEvent<HTMLSelectElement>) => void}>
              <option value="Dog">Dog</option>
              <option value="Cat">Cat</option>
              <option value="Other">Other</option>
            </select>
          </label>
          <label>
            <span style={fieldLabel}>Breed</span>
            <input style={fieldInput} value={form.breed} onChange={set("breed")} placeholder="e.g. Australian Cattle Dog" />
          </label>
          {form.species === "Other" && (
            <label style={{ gridColumn: "1 / -1" }}>
              <span style={fieldLabel}>What kind of animal?</span>
              <input style={fieldInput} value={form.other_species_description} onChange={set("other_species_description")} placeholder="e.g. Ferret, Cockatiel, Rabbit" />
            </label>
          )}
          <label>
            <span style={fieldLabel}>Sex</span>
            <select style={fieldInput} value={form.sex} onChange={set("sex") as (e: React.ChangeEvent<HTMLSelectElement>) => void}>
              <option value="M/N">Male, neutered</option>
              <option value="F/S">Female, spayed</option>
              <option value="M">Male, intact</option>
              <option value="F">Female, intact</option>
            </select>
          </label>
          <label>
            <span style={fieldLabel}>Age (years)</span>
            <input style={fieldInput} value={form.age_years} onChange={set("age_years")} inputMode="decimal" placeholder="5" />
          </label>
          <label style={{ gridColumn: "1 / -1" }}>
            <span style={fieldLabel}>Weight (lbs)</span>
            <input style={fieldInput} value={form.weight_lbs} onChange={set("weight_lbs")} inputMode="decimal" placeholder="38" />
          </label>
          <label style={{ gridColumn: "1 / -1" }}>
            <span style={fieldLabel}>What&apos;s worrying you most?</span>
            <input style={fieldInput} value={form.primary_concern} onChange={set("primary_concern")} placeholder="e.g. Reactive to people on walks" />
          </label>
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 24 }}>
        <button
          onClick={onBack}
          style={{ background: "transparent", border: "none", color: "var(--muted)", fontSize: 14, fontWeight: 600 }}
        >
          ← Back
        </button>
        <button
          onClick={() => onContinue(form)}
          disabled={!canContinue}
          style={{
            background: "var(--accent)",
            color: "var(--accent-ink)",
            border: "none",
            fontSize: 15,
            fontWeight: 700,
            padding: "13px 26px",
            borderRadius: 99,
            opacity: canContinue ? 1 : 0.5,
            cursor: canContinue ? "pointer" : "not-allowed",
          }}
        >
          {busy ? "Starting…" : "Continue to chat →"}
        </button>
      </div>
    </div>
  );
}
