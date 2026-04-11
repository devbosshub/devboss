"use client";

import Link from "next/link";
import { ReactNode } from "react";
import { usePathname } from "next/navigation";

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

          <div className="sidebar-footer">
            <div className="brand-kicker">MVP Mode</div>
            <div style={{ fontWeight: 600, marginBottom: 6 }}>Single-agent delivery</div>
            <div className="brand-subtitle">Human approvals still gate build start and deployment.</div>
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
                <div className="topbar-actions">
                  <div className="topbar-pill">Projects</div>
                  <div className="topbar-pill">Engineers</div>
                  <div className="topbar-pill">Task Runs</div>
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
