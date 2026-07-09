"use client";

import Link from "next/link";
import { ReactNode, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export function LayoutShell({
  children,
  topbarContent,
  hideTopbar = false
}: {
  children: ReactNode;
  topbarContent?: ReactNode;
  hideTopbar?: boolean;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const [loggingOut, setLoggingOut] = useState(false);

  const isActive = (href: string) => {
    if (href === "/") {
      return pathname === "/";
    }
    return pathname === href || pathname.startsWith(`${href}/`);
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-inner">
          <div className="brand">
            <div className="brand-kicker">Workspace</div>
            <div className="brand-title">Dev Boss</div>
            <div className="brand-subtitle">AI engineering team that designs, builds, tests and deploys software for you</div>
          </div>

          <nav className="nav">
            <Link className={isActive("/") ? "active" : undefined} href="/">
              Overview
            </Link>
            <Link className={isActive("/projects") ? "active" : undefined} href="/projects">
              Projects
            </Link>
            <Link className={isActive("/workflows") ? "active" : undefined} href="/workflows">
              Workflows
            </Link>
            <Link className={isActive("/prds") ? "active" : undefined} href="/prds">
              PRDs
            </Link>
            <Link className={isActive("/organizations") ? "active" : undefined} href="/organizations">
              Organizations
            </Link>
            <Link className={isActive("/engineers") ? "active" : undefined} href="/engineers">
              Engineers
            </Link>
            <Link className={isActive("/settings") ? "active" : undefined} href="/settings">
              Global Configs
            </Link>
            <Link className={isActive("/guide") ? "active" : undefined} href="/guide">
              Usage Guide
            </Link>
          </nav>

          <div style={{ marginTop: "auto", display: "flex", flexDirection: "column", gap: 12 }}>
            {user ? (
              <div
                style={{
                  padding: "10px 12px",
                  borderRadius: 12,
                  border: "1px solid var(--border)",
                  background: "var(--bg-subtle)",
                  fontSize: "0.82rem",
                  color: "var(--text-muted)",
                }}
              >
                <div style={{ fontWeight: 600, color: "var(--text)", marginBottom: 2 }}>
                  {user.email}
                </div>
                <div>Signed in</div>
              </div>
            ) : null}

            <div className="sidebar-footer">
              <div className="brand-kicker">MVP Mode</div>
              <div style={{ fontWeight: 600, marginBottom: 6 }}>Single-agent delivery</div>
              <div className="brand-subtitle">Human approvals still gate build start and deployment.</div>
            </div>

            <button
              className="button secondary"
              disabled={loggingOut}
              onClick={async () => {
                setLoggingOut(true);
                try {
                  await logout();
                  router.replace("/login");
                } finally {
                  setLoggingOut(false);
                }
              }}
              style={{ width: "100%" }}
              type="button"
            >
              {loggingOut ? "Signing out..." : "Sign out"}
            </button>
          </div>
        </div>
      </aside>

      <main className="shell">
        {hideTopbar ? null : (
          <header className="topbar">
            {topbarContent ?? (
              <>
                <div>
                  <div className="topbar-title">Dev Boss Workspace</div>
                  <div className="topbar-meta">Monitor AI execution, unblock approvals, and keep delivery moving.</div>
                </div>
              </>
            )}
          </header>
        )}
        {children}
      </main>
    </div>
  );
}
