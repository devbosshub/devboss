import Link from "next/link";

import { EngineerForm } from "@/components/forms";
import { LayoutShell } from "@/components/layout-shell";

export default function NewEngineerPage() {
  return (
    <LayoutShell>
      <section className="panel">
        <div className="section-header">
          <div>
            <div className="eyebrow">New Engineer</div>
            <h1>Create engineer</h1>
            <p className="muted">Define an engineer profile, choose its specialization, and edit the full skill markdown.</p>
          </div>
          <div className="section-actions">
            <Link className="button secondary" href="/engineers">
              Back to engineers
            </Link>
          </div>
        </div>
        <EngineerForm onSuccessPath="/engineers" />
      </section>
    </LayoutShell>
  );
}
