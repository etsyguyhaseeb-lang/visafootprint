"use client";
import { useState } from "react";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface Props {
  tier: "standard" | "attorney" | "monitor";
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

export default function CheckoutButton({ tier, children, className, style }: Props) {
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${BASE}/api/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tier }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail ?? "Something went wrong. Please try again.");
        return;
      }
      const data = await res.json();
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      }
    } catch {
      alert("Could not connect to payment service. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      className={className}
      style={{ cursor: loading ? "wait" : "pointer", opacity: loading ? 0.7 : 1, ...style }}
    >
      {loading ? "Redirecting to payment…" : children}
    </button>
  );
}
