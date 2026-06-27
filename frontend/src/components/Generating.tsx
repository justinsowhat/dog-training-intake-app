import { PawIcon } from "./PawIcon";

export function Generating({ petName }: { petName: string }) {
  return (
    <div style={{ maxWidth: 520, margin: "0 auto", padding: "120px 24px", textAlign: "center" }}>
      <div style={{ position: "relative", width: 84, height: 84, margin: "0 auto 34px" }}>
        <span
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: "50%",
            background: "var(--accent)",
            opacity: 0.18,
            animation: "pm-ring 1.8s ease-out infinite",
          }}
        />
        <span
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: "50%",
            background: "var(--accent)",
            opacity: 0.18,
            animation: "pm-ring 1.8s ease-out infinite 0.9s",
          }}
        />
        <div
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: "50%",
            background: "var(--accent)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            animation: "pm-pulse 1.6s ease-in-out infinite",
          }}
        >
          <PawIcon size={36} />
        </div>
      </div>
      <h2 style={{ fontFamily: "var(--font-head)", fontSize: 26, fontWeight: 600, margin: "0 0 12px" }}>
        Building {petName}&apos;s plan
      </h2>
      <div style={{ fontSize: 15, color: "var(--muted)", lineHeight: 2 }}>
        <div style={{ animation: "pm-shimmer 1.8s infinite" }}>Reviewing the behavior history…</div>
        <div style={{ animation: "pm-shimmer 1.8s infinite 0.6s" }}>Mapping triggers and thresholds…</div>
        <div style={{ animation: "pm-shimmer 1.8s infinite 1.2s" }}>Designing force-free protocols…</div>
      </div>
    </div>
  );
}
