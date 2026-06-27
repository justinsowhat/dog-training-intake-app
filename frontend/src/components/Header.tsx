import { PawIcon } from "./PawIcon";

export function Header({
  showRestart,
  onRestart,
}: {
  showRestart: boolean;
  onRestart: () => void;
}) {
  return (
    <header
      className="pm-no-print"
      style={{
        position: "sticky",
        top: 0,
        zIndex: 20,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "14px 22px",
        background: "var(--bg)",
        borderBottom: "1px solid var(--border)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div
          style={{
            width: 34,
            height: 34,
            borderRadius: 10,
            background: "var(--accent)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <PawIcon />
        </div>
        <span
          style={{
            fontFamily: "var(--font-head)",
            fontSize: 19,
            fontWeight: 600,
            letterSpacing: "-0.01em",
          }}
        >
          PawsitiveMind
        </span>
      </div>
      {showRestart && (
        <button
          onClick={onRestart}
          style={{
            background: "transparent",
            border: "1px solid var(--border)",
            color: "var(--muted)",
            fontSize: 13,
            fontWeight: 600,
            padding: "7px 13px",
            borderRadius: 99,
          }}
        >
          Start over
        </button>
      )}
    </header>
  );
}
