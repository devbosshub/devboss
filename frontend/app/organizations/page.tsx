"use client";

import Link from "next/link";
import { useEffect, useState, useTransition } from "react";

import { ConfirmModal } from "@/components/confirm-modal";
import { LayoutShell } from "@/components/layout-shell";
import { api } from "@/lib/api";
import { Organization } from "@/lib/types";

export default function OrganizationsPage() {
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [orgToDelete, setOrgToDelete] = useState<Organization | null>(null);
  const [isPending, startTransition] = useTransition();
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [showCreate, setShowCreate] = useState(false);

  const load = () => api.getOrganizations().then(setOrgs);

  useEffect(() => { load(); }, []);

  const createOrg = () => {
    startTransition(async () => {
      await api.createOrganization({ name, slug });
      setName(""); setSlug(""); setShowCreate(false);
      load();
    });
  };

  return (
    <LayoutShell topbarContent={
      <div style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
        <div><div style={{ fontSize: 18, fontWeight: 600 }}>Dev Boss</div><div className="muted" style={{ marginTop: 2 }}>Beta version</div></div>
        <div className="topbar-actions">
          <button className="button" onClick={() => setShowCreate(!showCreate)} type="button">New Organization</button>
        </div>
      </div>
    }>
      <ConfirmModal
        confirmClassName="button danger" confirmLabel="Delete"
        description={orgToDelete ? `Delete "${orgToDelete.name}"? Projects will be unlinked.` : ""}
        onCancel={() => setOrgToDelete(null)}
        onConfirm={async () => { if (!orgToDelete) return; const o = orgToDelete; setOrgToDelete(null); await api.deleteOrganization(o.id); load(); }}
        open={orgToDelete !== null} title="Delete organization?"
      />
      <section className="panel">
        <div className="section-header">
          <div><div className="eyebrow">Organizations</div><h1>Organizations</h1><p className="muted">Manage teams and their access to projects.</p></div>
        </div>

        {showCreate ? (
          <div className="task-card" style={{ marginBottom: 20 }}>
            <h3>Create Organization</h3>
            <form className="stack" onSubmit={(e) => { e.preventDefault(); createOrg(); }}>
              <label className="field"><span>Name</span><input value={name} onChange={(e) => setName(e.target.value)} required /></label>
              <label className="field"><span>Slug</span><input value={slug} onChange={(e) => setSlug(e.target.value)} required placeholder="my-team" /></label>
              <div className="actions">
                <button className="button" disabled={isPending} type="submit">{isPending ? "Creating..." : "Create"}</button>
                <button className="button secondary" onClick={() => setShowCreate(false)} type="button">Cancel</button>
              </div>
            </form>
          </div>
        ) : null}

        {orgs.length === 0 ? <div className="empty">No organizations yet.</div> : (
          <div className="table-shell"><table className="data-table"><thead><tr><th>Name</th><th>Slug</th><th>Members</th><th>Actions</th></tr></thead><tbody>
            {orgs.map((org) => (
              <tr key={org.id}>
                <td>{org.name}</td><td>{org.slug}</td><td>{org.members.length}</td>
                <td className="action-cell"><div className="table-actions">
                  <Link className="button secondary" href={`/organizations/detail?orgId=${org.id}`}>View</Link>
                  <button className="button danger" onClick={() => setOrgToDelete(org)} type="button">Delete</button>
                </div></td>
              </tr>
            ))}
          </tbody></table></div>
        )}
      </section>
    </LayoutShell>
  );
}
