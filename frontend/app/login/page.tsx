"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export default function LoginPage() {
  const router = useRouter();
  const { login, user } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isPending, setIsPending] = useState(false);

  useEffect(() => {
    if (user) {
      router.replace("/");
    }
  }, [user, router]);

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: 24,
      }}
    >
      <form
        style={{
          width: "min(420px, 100%)",
          display: "flex",
          flexDirection: "column",
          gap: 16,
          padding: 28,
          borderRadius: 20,
          border: "1px solid var(--border)",
          background: "var(--bg-elevated)",
          boxShadow: "var(--shadow)",
        }}
        onSubmit={async (event) => {
          event.preventDefault();
          setError("");
          setIsPending(true);
          try {
            await login(email, password);
            router.replace("/");
          } catch (err) {
            setError(err instanceof Error ? err.message : "Login failed");
          } finally {
            setIsPending(false);
          }
        }}
      >
        <div>
          <div style={{ fontSize: "1.2rem", fontWeight: 600, letterSpacing: "-0.02em" }}>
            Dev Boss
          </div>
          <div className="muted" style={{ marginTop: 4 }}>
            Sign in to your workspace
          </div>
        </div>

        {error ? (
          <div
            style={{
              padding: "10px 14px",
              borderRadius: 12,
              background: "var(--danger-soft)",
              color: "var(--danger)",
              fontSize: "0.88rem",
            }}
          >
            {error}
          </div>
        ) : null}

        <label className="field">
          <span>Email</span>
          <input
            autoComplete="email"
            onChange={(e) => setEmail(e.target.value)}
            placeholder="user@example.com"
            required
            type="email"
            value={email}
          />
        </label>

        <label className="field">
          <span>Password</span>
          <input
            autoComplete="current-password"
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
            type="password"
            value={password}
          />
        </label>

        <button className="button" disabled={isPending} type="submit" style={{ width: "100%" }}>
          {isPending ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </div>
  );
}
