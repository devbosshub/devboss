"use client";

import Link from "next/link";
import { Suspense, useEffect, useState, useTransition } from "react";
import { useSearchParams } from "next/navigation";

import { LayoutShell } from "@/components/layout-shell";
import { api } from "@/lib/api";
import { Organization, Tag } from "@/lib/types";

function OrgDetailContent() {
  const params = useSearchParams();
  const orgId = Number(params.get("orgId") ?? "");
  const [org, setOrg] = useState<Organization | null>(null);
  const [tags, setTags] = useState<Tag[]>([]);
  const [isPending, startTransition] = useTransition();
  const [email, setEmail] = useState("");
  const [tagName, setTagName] = useState("");
  const [tagColor, setTagColor] = useState("#3b82f6");

  const load = () => {
    api.getOrganization(orgId).then((o) => { setOrg(o); setTags(o.tags ?? []); });
  };

  useEffect(() => { if (orgId) load(); }, [orgId]);

  const addMember = () => {
    if (!email.trim()) return;
    startTransition(async () => { await api.addOrgMember(orgId, { user_email: email, role: "member" }); setEmail(""); load(); });
  };

  const createTag = () => {
    if (!tagName.trim()) return;
    startTransition(async () => { await api.createTag({ organization_id: orgId, name: tagName, color: tagColor }); setTagName(""); load(); });
  };

  if (Number.isNaN(orgId)) return <LayoutShell><section className="panel"><div className="empty">Invalid organization ID.</div></section></LayoutShell>;
  if (!org) return <LayoutShell><section className="panel"><div className="empty">Loading...</div></section></LayoutShell>;

  return (
    <LayoutShell>
      <section className="panel">
        <div className="section-header">
          <div><div className="eyebrow">Organization</div><h1>{org.name}</h1><p className="muted">Slug: {org.slug}</p></div>
          <Link className="button secondary" href="/organizations">Back</Link>
        </div>

        <h2>Members ({org.members.length})</h2>
        <div className="stack" style={{ marginBottom: 24 }}>
          {org.members.map((m) => (
            <div className="task-card" key={m.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <strong>{m.user?.email ?? m.user_id}</strong>
                <span className="tag" style={{ marginLeft: 8 }}>{m.role}</span>
              </div>
              <button className="button danger" onClick={() => startTransition(async () => { await api.removeOrgMember(orgId, m.id); load(); })} type="button">Remove</button>
            </div>
          ))}
          <div style={{ display: "flex", gap: 8 }}>
            <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="user@example.com" style={{ flex: 1 }} />
            <button className="button" disabled={isPending || !email.trim()} onClick={addMember} type="button">Add member</button>
          </div>
        </div>

        <h2>Tags ({tags.length})</h2>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
          {tags.map((tag) => (
            <span key={tag.id} className="tag" style={{ backgroundColor: tag.color ?? "var(--bg-subtle)", color: "#fff", display: "flex", alignItems: "center", gap: 6 }}>
              {tag.name}
              <button onClick={() => startTransition(async () => { await api.deleteTag(tag.id); load(); })} style={{ background: "none", border: "none", color: "inherit", cursor: "pointer", fontSize: 14 }} type="button">&times;</button>
            </span>
          ))}
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <input value={tagName} onChange={(e) => setTagName(e.target.value)} placeholder="Tag name" />
          <input type="color" value={tagColor} onChange={(e) => setTagColor(e.target.value)} style={{ width: 40 }} />
          <button className="button" disabled={isPending || !tagName.trim()} onClick={createTag} type="button">Add tag</button>
        </div>
      </section>
    </LayoutShell>
  );
}

export default function OrganizationDetailPage() {
  return (
    <Suspense fallback={<LayoutShell><section className="panel"><div className="empty">Loading...</div></section></LayoutShell>}>
      <OrgDetailContent />
    </Suspense>
  );
}
