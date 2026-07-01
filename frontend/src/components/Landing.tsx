const STEPS = [
  { n: "1", title: "Share the basics", body: "A quick profile of your animal — name, species, breed, age, the essentials." },
  { n: "2", title: "Have a conversation", body: "Chat with a certified consultant about what\u2019s really going on." },
  { n: "3", title: "Get your plan", body: "A personalized, force-free training plan you can start today." },
];

export function Landing({ onStart }: { onStart: () => void }) {
  return (
    <div
      style={{
        maxWidth: 760,
        margin: "0 auto",
        padding: "64px 24px 80px",
        textAlign: "center",
        animation: "pm-fade 0.5s ease",
      }}
    >
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 7,
          background: "var(--accent-soft)",
          color: "var(--accent)",
          fontSize: 12.5,
          fontWeight: 700,
          letterSpacing: "0.02em",
          padding: "6px 13px",
          borderRadius: 99,
          marginBottom: 26,
        }}
      >
        Force-free behavior consulting
      </div>

      <h1
        style={{
          fontFamily: "var(--font-head)",
          fontSize: 46,
          lineHeight: 1.08,
          fontWeight: 600,
          letterSpacing: "-0.02em",
          margin: "0 0 18px",
          textWrap: "balance",
        }}
      >
        A calmer animal starts with understanding the why.
      </h1>

      <p
        style={{
          fontSize: 18,
          lineHeight: 1.6,
          color: "var(--muted)",
          maxWidth: 540,
          margin: "0 auto 34px",
        }}
      >
        Tell us a little about your animal, have a short conversation with a certified
        consultant, and walk away with a personalized, step-by-step training plan.
      </p>

      <button
        onClick={onStart}
        style={{
          background: "var(--accent)",
          color: "var(--accent-ink)",
          border: "none",
          fontSize: 16,
          fontWeight: 700,
          padding: "15px 30px",
          borderRadius: 99,
          boxShadow: "0 6px 20px -8px var(--accent)",
        }}
      >
        Start a consultation
      </button>
      <p style={{ fontSize: 13, color: "var(--muted)", margin: "16px 0 0" }}>
        Free first consultation · about 5 minutes
      </p>

      <div
        style={{
          display: "flex",
          gap: 16,
          justifyContent: "center",
          flexWrap: "wrap",
          marginTop: 60,
        }}
      >
        {STEPS.map((s) => (
          <div
            key={s.n}
            style={{
              flex: 1,
              minWidth: 200,
              maxWidth: 230,
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius)",
              padding: "22px 20px",
              textAlign: "left",
            }}
          >
            <div
              style={{
                width: 30,
                height: 30,
                borderRadius: 9,
                background: "var(--accent-soft)",
                color: "var(--accent)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: 700,
                fontSize: 14,
                marginBottom: 14,
              }}
            >
              {s.n}
            </div>
            <div
              style={{
                fontFamily: "var(--font-head)",
                fontSize: 17,
                fontWeight: 600,
                marginBottom: 6,
              }}
            >
              {s.title}
            </div>
            <div style={{ fontSize: 14, lineHeight: 1.5, color: "var(--muted)" }}>
              {s.body}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
