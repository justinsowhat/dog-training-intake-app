import { useState } from "react";
import { PawIcon } from "./PawIcon";

const pillButton = {
  background: "transparent",
  border: "1px solid var(--border)",
  color: "var(--muted)",
  fontSize: 13,
  fontWeight: 600,
  padding: "7px 13px",
  borderRadius: 99,
} as const;

export function Header({
  showRestart,
  onRestart,
  shareUrl,
}: {
  showRestart: boolean;
  onRestart: () => void;
  /** When set, show a Share button that copies this link to the clipboard. */
  shareUrl?: string;
}) {
  const [copied, setCopied] = useState(false);

  async function copyShareLink() {
    if (!shareUrl) return;
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      /* clipboard blocked (insecure context / denied) — silently no-op */
    }
  }

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
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        {shareUrl && (
          <button
            onClick={copyShareLink}
            style={{
              ...pillButton,
              ...(copied ? { borderColor: "var(--accent)", color: "var(--accent)" } : null),
            }}
          >
            {copied ? "✓ Link copied" : "🔗 Share"}
          </button>
        )}
        {showRestart && (
          <button onClick={onRestart} style={pillButton}>
            Start over
          </button>
        )}
      </div>
    </header>
  );
}
