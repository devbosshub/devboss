"use client";

import Link from "next/link";
import { useEffect, useState, useTransition } from "react";

import { LayoutShell } from "@/components/layout-shell";
import { api } from "@/lib/api";
import { Organization, PRD } from "@/lib/types";

export default function PRDsPage() {
  const [prds, setPRDs] = useState<PRD[]>([]);
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<number | "">("");

  const load = () => {
    const orgId = selectedOrgId === "" ? undefined : selectedOrgId;
    api.getPRDs(orgId).then(setPRDs);
  };

  useEffect(() => { api.getOrganizations().then(setOrgs); }, []);
  useEffect(() => { load(); }, [selectedOrgId]);

  const statusLabel: Record<string, string> = { draft: "Draft", in_review: "In Review", approved: "Approved", converted: "Converted", archived: "Archived" };

  return (
    <LayoutShell topbarContent={
      <div style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
        <div><div style={{ fontSize: 18, fontWeight: 600 }}>Dev Boss</div><div className="muted" style={{ marginTop: 2 }}>Beta version</div></div>
        <div className="topbar-actions">
          <Link className="button" href="/prds/new">New PRD</Link>
        </div>
      </div>
    }>
      <section className="panel">
        <div className="section-header">
          <div><div className="eyebrow">PRDs</div><h1>Product Requirements Documents</h1><p className="muted">Create and manage PRDs, then convert them to tasks.</p></div>
        </div>

        <div className="stack" style={{ marginBottom: 20 }}>
          <label className="field">
            <span>Filter by organization</span>
            <select value={selectedOrgId} onChange={(e) => setSelectedOrgId(e.target.value ? Number(e.target.value) : "")}>
              <option value="">All organizations</option>
              {orgs.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
            </select>
          </label>
        </div>

        {prds.length === 0 ? <div className="empty">No PRDs yet.</div> : (
          <div className="table-shell"><table className="data-table"><thead><tr><th>Title</th><th>Status</th><th>Org</th><th>Comments</th><th>Tags</th><th>Actions</th></tr></thead><tbody>
            {prds.map((prd) => (
              <tr key={prd.id}>
                <td>{prd.title}</td>
                <td><span className={`tag${prd.status === "converted" ? "" : prd.status === "approved" ? "" : ""}`}>{statusLabel[prd.status] ?? prd.status}</span></td>
                <td>#{prd.organization_id}</td>
                <td>{prd.comments?.length ?? 0}</td>
                <td>{(prd.tags ?? []).map((t) => <span key={t.id} className="tag" style={{ backgroundColor: t.color ?? "var(--bg-subtle)", color: "#fff", marginRight: 4 }}>{t.name}</span>)}</td>
                <td className="action-cell"><div className="table-actions">
                  <Link className="button secondary" href={`/prds/detail?prdId=${prd.id}`}>Open</Link>
                </div></td>
              </tr>
            ))}
          </tbody></table></div>
        )}
      </section>
    </LayoutShell>
  );
}
