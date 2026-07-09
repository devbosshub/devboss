"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, useTransition } from "react";

import { LayoutShell } from "@/components/layout-shell";
import { api } from "@/lib/api";
import { Organization } from "@/lib/types";

export default function NewPRDPage() {
  const router = useRouter();
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [isPending, startTransition] = useTransition();
  const [orgId, setOrgId] = useState<number>(0);
  const [title, setTitle] = useState("");
  const [summary, setSummary] = useState("");

  useEffect(() => { api.getOrganizations().then(setOrgs).then(() => {}); }, []);

  useEffect(() => { if (orgs.length > 0 && orgId === 0) setOrgId(orgs[0].id); }, [orgs]);

  return (
    <LayoutShell>
      <section className="panel">
        <div className="section-header">
          <div><div className="eyebrow">New PRD</div><h1>Create PRD</h1><p className="muted">Start a product requirements document to refine before converting to tasks.</p></div>
          <div className="section-actions"><Link className="button secondary" href="/prds">Back</Link></div>
        </div>
        <form className="stack" onSubmit={(e) => { e.preventDefault();
          startTransition(async () => {
            const prd = await api.createPRD({ organization_id: orgId, title, summary: summary || undefined });
            setTitle(""); setSummary("");
            router.push(`/prds/detail?prdId=${prd.id}`);
          });
        }}>
          <label className="field"><span>Organization</span>
            <select value={orgId} onChange={(e) => setOrgId(Number(e.target.value))}>
              {orgs.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
            </select>
          </label>
          <label className="field"><span>Title</span><input value={title} onChange={(e) => setTitle(e.target.value)} required /></label>
          <label className="field"><span>Summary</span><textarea value={summary} onChange={(e) => setSummary(e.target.value)} /></label>
          <div className="actions">
            <button className="button" disabled={isPending || orgs.length === 0} type="submit">{isPending ? "Creating..." : "Create PRD"}</button>
          </div>
        </form>
      </section>
    </LayoutShell>
  );
}
