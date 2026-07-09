"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { LayoutShell } from "@/components/layout-shell";
import { api } from "@/lib/api";

export default function NewWorkflowPage() {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  return (
    <LayoutShell>
      <section className="panel">
        <div className="section-header">
          <div>
            <div className="eyebrow">New Workflow</div>
            <h1>Create workflow</h1>
            <p className="muted">Define a new delivery pipeline. Add stages after creation.</p>
          </div>
          <div className="section-actions">
            <Link className="button secondary" href="/workflows">
              Back to workflows
            </Link>
          </div>
        </div>
        <form
          className="stack"
          onSubmit={(event) => {
            event.preventDefault();
            startTransition(async () => {
              const workflow = await api.createWorkflow({ name, description });
              setName("");
              setDescription("");
              router.push(`/workflows/edit?workflowId=${workflow.id}`);
            });
          }}
        >
          <label className="field">
            <span>Workflow name</span>
            <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Standard SDLC Pipeline" required />
          </label>
          <label className="field">
            <span>Description</span>
            <textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Plan → Build → Test → Deploy for web applications" />
          </label>
          <div className="actions">
            <button className="button" disabled={isPending} type="submit">
              {isPending ? "Creating..." : "Create workflow"}
            </button>
          </div>
        </form>
      </section>
    </LayoutShell>
  );
}
