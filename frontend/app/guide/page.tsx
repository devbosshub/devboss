"use client";

import { LayoutShell } from "@/components/layout-shell";
import { MarkdownContent } from "@/components/markdown-content";
import { usageGuideMarkdown } from "@/content/usage-guide";

export default function GuidePage() {
  return (
    <LayoutShell
      topbarContent={
        <div style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
          <div>
            <div style={{ fontSize: 18, fontWeight: 600 }}>Dev Boss</div>
            <div className="muted" style={{ marginTop: 2 }}>
              Beta version
            </div>
          </div>
        </div>
      }
    >
      <section className="panel doc-panel">
        <div className="section-header">
          <div>
            <div className="eyebrow">Documentation</div>
            <h1>Usage Guide</h1>
            <p className="muted">How Dev Boss works, how to operate it, and what assumptions shape the current MVP.</p>
          </div>
        </div>
        <MarkdownContent content={usageGuideMarkdown} />
      </section>
    </LayoutShell>
  );
}
