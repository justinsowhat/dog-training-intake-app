export function TypingDots() {
  const dot = {
    width: 7,
    height: 7,
    borderRadius: 99,
    background: "var(--muted)",
  } as const;
  return (
    <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 14 }}>
      <div
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          padding: "14px 16px",
          borderRadius: "var(--radius)",
          borderBottomLeftRadius: 4,
          display: "flex",
          gap: 5,
        }}
      >
        <span style={{ ...dot, animation: "pm-blink 1.2s infinite" }} />
        <span style={{ ...dot, animation: "pm-blink 1.2s infinite 0.2s" }} />
        <span style={{ ...dot, animation: "pm-blink 1.2s infinite 0.4s" }} />
      </div>
    </div>
  );
}
