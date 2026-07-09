"use client";

import Link from "next/link";
import { Suspense, useEffect, useRef, useState, useTransition } from "react";
import { useSearchParams } from "next/navigation";

import { MarkdownContent } from "@/components/markdown-content";
import { LayoutShell } from "@/components/layout-shell";
import { api } from "@/lib/api";
import { PRD, Project } from "@/lib/types";

function PRDDetailContent() {
  const params = useSearchParams();
  const prdId = Number(params.get("prdId") ?? "");
  const [prd, setPRD] = useState<PRD | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [message, setMessage] = useState("");
  const [body, setBody] = useState("");
  const [isPending, startTransition] = useTransition();
  const [selectedProjectIds, setSelectedProjectIds] = useState<number[]>([]);
  const [taskTitles, setTaskTitles] = useState<string[]>([""]);
  const [showConvert, setShowConvert] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const load = () => { api.getPRD(prdId).then((p) => { setPRD(p); setBody(p.body_markdown ?? ""); }); };

  useEffect(() => { if (prdId) { load(); api.getProjects().then(setProjects); } }, [prdId]);

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [prd?.comments?.length]);

  const sendMessage = () => {
    if (!message.trim()) return;
    startTransition(async () => { await api.prdChat(prdId, message); setMessage(""); load(); });
  };

  const saveBody = () => {
    startTransition(async () => { await api.updatePRD(prdId, { body_markdown: body }); load(); });
  };

  const convertToTasks = () => {
    const filtered = taskTitles.filter((t) => t.trim());
    if (filtered.length === 0) return;
    startTransition(async () => {
      await api.convertPRD(prdId, { project_ids: selectedProjectIds.slice(0, filtered.length), task_titles: filtered });
      load(); setShowConvert(false);
    });
  };

  if (Number.isNaN(prdId)) return <LayoutShell><section className="panel"><div className="empty">Invalid PRD ID.</div></section></LayoutShell>;
  if (!prd) return <LayoutShell><section className="panel"><div className="empty">Loading...</div></section></LayoutShell>;

  return (
    <LayoutShell topbarContent={
      <div style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
        <div><div style={{ fontSize: 18, fontWeight: 600 }}>Dev Boss</div><div className="muted" style={{ marginTop: 2 }}>Beta version</div></div>
        <div className="topbar-actions"><Link className="button" href="/prds">Back to PRDs</Link></div>
      </div>
    }>
      <section className="panel">
        <div className="section-header">
          <div>
            <div className="eyebrow">PRD #{prd.id}</div>
            <h1>{prd.title}</h1>
            <span className="tag" style={{ marginTop: 4 }}>{prd.status}</span>
            {prd.tags?.map((t) => <span key={t.id} className="tag" style={{ backgroundColor: t.color ?? "var(--bg-subtle)", color: "#fff", marginLeft: 4 }}>{t.name}</span>)}
          </div>
          <div className="section-actions">
            <button className="button" onClick={() => setShowConvert(!showConvert)} type="button" disabled={prd.status === "converted"}>
              Convert to Tasks
            </button>
          </div>
        </div>

        {prd.summary ? <p className="muted">{prd.summary}</p> : null}

        {showConvert ? (
          <div className="task-card" style={{ marginBottom: 20 }}>
            <h3>Convert PRD to Tasks</h3>
            <p className="muted">Select projects and enter task titles.</p>
            {taskTitles.map((t, i) => (
              <div key={i} style={{ display: "flex", gap: 8, marginBottom: 8 }}>
                <select value={selectedProjectIds[i] ?? ""} onChange={(e) => { const ids = [...selectedProjectIds]; ids[i] = Number(e.target.value); setSelectedProjectIds(ids); }} style={{ width: 200 }}>
                  <option value="">Select project</option>
                  {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
                <input value={t} onChange={(e) => { const titles = [...taskTitles]; titles[i] = e.target.value; setTaskTitles(titles); }} placeholder="Task title" style={{ flex: 1 }} />
                {taskTitles.length > 1 ? <button className="button danger" onClick={() => setTaskTitles(taskTitles.filter((_, idx) => idx !== i))} type="button">X</button> : null}
              </div>
            ))}
            <div className="actions">
              <button className="button secondary" onClick={() => setTaskTitles([...taskTitles, ""])} type="button">+ Add task</button>
              <button className="button" disabled={isPending} onClick={convertToTasks} type="button">Convert</button>
              <button className="button secondary" onClick={() => setShowConvert(false)} type="button">Cancel</button>
            </div>
          </div>
        ) : null}

        <h2>Body</h2>
        <textarea className="editor-textarea" value={body} onChange={(e) => setBody(e.target.value)} style={{ minHeight: 200 }} />
        <div className="actions"><button className="button" disabled={isPending} onClick={saveBody} type="button">Save body</button></div>

        <h2 style={{ marginTop: 24 }}>Chat ({prd.comments?.length ?? 0})</h2>
        <div className="stack" style={{ maxHeight: 400, overflowY: "auto", marginBottom: 12 }}>
          {(prd.comments ?? []).map((c) => (
            <div className="comment" key={c.id}>
              <div className="comment-header">
                <strong>{c.author_name}</strong> <span className="muted">({c.author_type})</span>
                <div className="comment-timestamp">{new Date(c.created_at).toLocaleString()}</div>
              </div>
              <MarkdownContent content={c.body} />
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <input value={message} onChange={(e) => setMessage(e.target.value)} onKeyDown={(e) => e.key === "Enter" && sendMessage()} placeholder="Type your message to refine this PRD..." style={{ flex: 1 }} />
          <button className="button" disabled={isPending || !message.trim()} onClick={sendMessage} type="button">Send</button>
        </div>
      </section>
    </LayoutShell>
  );
}

export default function PRDDetailPage() {
  return (
    <Suspense fallback={<LayoutShell><section className="panel"><div className="empty">Loading...</div></section></LayoutShell>}>
      <PRDDetailContent />
    </Suspense>
  );
}
