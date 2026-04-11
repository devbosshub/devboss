"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import { EngineerForm } from "@/components/forms";
import { LayoutShell } from "@/components/layout-shell";
import { api } from "@/lib/api";
import { Engineer } from "@/lib/types";

function EditEngineerPageContent() {
  const searchParams = useSearchParams();
  const engineerId = Number(searchParams.get("engineerId") ?? "");
  const [engineer, setEngineer] = useState<Engineer | null>(null);

  useEffect(() => {
    api.getEngineers().then((items) => {
      const found = items.find((item) => item.id === engineerId) ?? null;
      setEngineer(found);
    });
  }, [engineerId]);

  return (
    <LayoutShell>
      <section className="panel">
        <div className="section-header">
          <div>
            <div className="eyebrow">Edit Engineer</div>
            <h1>{engineer?.name ?? "Engineer"}</h1>
            <p className="muted">Update the engineer profile, runtime settings, and full skill markdown.</p>
          </div>
          <div className="section-actions">
            <Link className="button secondary" href="/engineers">
              Back to engineers
            </Link>
          </div>
        </div>
        {engineer ? <EngineerForm engineer={engineer} onSuccessPath="/engineers" /> : <div className="empty">Engineer not found.</div>}
      </section>
    </LayoutShell>
  );
}

export default function EditEngineerPage() {
  return (
    <Suspense fallback={<LayoutShell><section className="panel"><div className="empty">Loading engineer...</div></section></LayoutShell>}>
      <EditEngineerPageContent />
    </Suspense>
  );
}
