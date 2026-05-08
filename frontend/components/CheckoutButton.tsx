"use client";
import { useState } from "react";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface Props {
  tier: "standard" | "attorney" | "monitor";
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  block?: boolean;
}

export default function CheckoutButton({ tier, children, className, style, block }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleClick = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${BASE}/api/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tier }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(data.detail ?? `Error ${res.status} — please try again.`);
        return;
      }
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        setError("No checkout URL returned. Check payment configuration.");
      }
    } catch {
      setError("Could not reach payment service. Check your connection.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: block ? "block" : "inline-flex", flexDirection: "column", alignItems: block ? "stretch" : "center", gap: 6, width: block ? "100%" : undefined }}>
      <button
        onClick={handleClick}
        disabled={loading}
        className={className}
        style={{ cursor: loading ? "wait" : "pointer", opacity: loading ? 0.7 : 1, width: block ? "100%" : undefined, ...style }}
      >
        {loading ? "Redirecting to payment…" : children}
      </button>
      {error && (
        <span style={{ fontSize: 12, color: "#c0392b", textAlign: "center", lineHeight: 1.4, padding: "4px 0" }}>
          {error}
        </span>
      )}
    </div>
  );
}
