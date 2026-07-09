"use client";

import Link from "next/link";
import { Suspense, useEffect, useState, useTransition } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { LayoutShell } from "@/components/layout-shell";
import { api } from "@/lib/api";
import { Engineer, Workflow, WorkflowStage } from "@/lib/types";

function EditWorkflowPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const workflowId = Number(searchParams.get("workflowId") ?? "");
  const [isPending, startTransition] = useTransition();

  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [engineers, setEngineers] = useState<Engineer[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const [newStageName, setNewStageName] = useState("");
  const [editingStage, setEditingStage] = useState<WorkflowStage | null>(null);

  const loadWorkflow = () => {
    api.getWorkflow(workflowId).then((wf) => {
      setWorkflow(wf);
      setName(wf.name);
      setDescription(wf.description ?? "");
    });
  };

  useEffect(() => {
    if (!Number.isNaN(workflowId)) {
      loadWorkflow();
      api.getEngineers().then(setEngineers);
    }
  }, [workflowId]);

  const addStage = () => {
    if (!newStageName.trim()) return;
    startTransition(async () => {
      await api.createWorkflowStage(workflowId, { name: newStageName.trim(), is_ai_executable: false });
      setNewStageName("");
      loadWorkflow();
    });
  };

  const updateStage = (stageId: number, updates: Partial<WorkflowStage>) => {
    startTransition(async () => {
      await api.updateWorkflowStage(workflowId, stageId, updates);
      loadWorkflow();
    });
  };

  const deleteStage = (stageId: number) => {
    if (!window.confirm("Delete this stage?")) return;
    startTransition(async () => {
      await api.deleteWorkflowStage(workflowId, stageId);
      loadWorkflow();
    });
  };

  const moveStage = (stageId: number, direction: "up" | "down") => {
    if (!workflow) return;
    const stages = [...workflow.stages].sort((a, b) => a.stage_order - b.stage_order);
    const idx = stages.findIndex((s) => s.id === stageId);
    if (idx < 0) return;
    const swapIdx = direction === "up" ? idx - 1 : idx + 1;
    if (swapIdx < 0 || swapIdx >= stages.length) return;

    const updated = stages.map((s, i) => {
      if (i === idx) return { id: s.id, stage_order: stages[swapIdx].stage_order };
      if (i === swapIdx) return { id: s.id, stage_order: stages[idx].stage_order };
      return { id: s.id, stage_order: s.stage_order };
    });

    startTransition(async () => {
      await api.reorderWorkflowStages(workflowId, updated);
      loadWorkflow();
    });
  };

  const saveWorkflowDetails = () => {
    startTransition(async () => {
      await api.updateWorkflow(workflowId, { name, description });
      loadWorkflow();
    });
  };

  if (Number.isNaN(workflowId)) {
    return (
      <LayoutShell>
        <section className="panel"><div className="empty">Invalid workflow ID.</div></section>
      </LayoutShell>
    );
  }

  if (!workflow) {
    return (
      <LayoutShell>
        <section className="panel"><div className="empty">Loading workflow...</div></section>
      </LayoutShell>
    );
  }

  const sortedStages = [...workflow.stages].sort((a, b) => a.stage_order - b.stage_order);

  return (
    <LayoutShell>
      <section className="panel">
        <div className="section-header">
          <div>
            <div className="eyebrow">Edit Workflow</div>
            <h1>{workflow.name}</h1>
            <p className="muted">Configure stages, assign engineers, and define pipeline rules.</p>
          </div>
          <div className="section-actions">
            <Link className="button secondary" href="/workflows">
              Back to workflows
            </Link>
          </div>
        </div>

        <div className="stack">
          <label className="field">
            <span>Workflow name</span>
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </label>
          <label className="field">
            <span>Description</span>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} />
          </label>
          <div className="actions">
            <button className="button" disabled={isPending} onClick={saveWorkflowDetails} type="button">
              Save details
            </button>
          </div>
        </div>

        <h2 style={{ marginTop: 32 }}>Stages</h2>
        <p className="muted">Ordered pipeline stages. Drag to reorder (use arrows for now).</p>

        {sortedStages.length === 0 ? (
          <div className="empty">No stages yet. Add stages below to define the pipeline.</div>
        ) : (
          sortedStages.map((stage, idx) => (
            <div className="task-card" key={stage.id} style={{ marginBottom: 12 }}>
              <div className="actions" style={{ justifyContent: "space-between" }}>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <strong>{idx + 1}. {stage.name}</strong>
                  {stage.is_ai_executable ? <span className="tag">AI Executable</span> : null}
                  {stage.requires_human_approval ? <span className="tag warning">Needs Approval</span> : null}
                  {stage.assigned_engineer_id ? (
                    <span className="tag">Eng: {engineers.find((e) => e.id === stage.assigned_engineer_id)?.name ?? stage.assigned_engineer_id}</span>
                  ) : null}
                </div>
                <div className="table-actions">
                  <button className="icon-button" disabled={idx === 0} onClick={() => moveStage(stage.id, "up")} type="button">↑</button>
                  <button className="icon-button" disabled={idx === sortedStages.length - 1} onClick={() => moveStage(stage.id, "down")} type="button">↓</button>
                  <button className="button secondary" onClick={() => setEditingStage(editingStage?.id === stage.id ? null : stage)} type="button">
                    {editingStage?.id === stage.id ? "Cancel" : "Edit"}
                  </button>
                  <button className="button danger" onClick={() => deleteStage(stage.id)} type="button">Delete</button>
                </div>
              </div>

              {editingStage?.id === stage.id ? (
                <div className="stack" style={{ marginTop: 12 }}>
                  <label className="field">
                    <span>Stage name</span>
                    <input
                      value={editingStage.name}
                      onChange={(e) => setEditingStage({ ...editingStage, name: e.target.value })}
                    />
                  </label>
                  <label className="field">
                    <span>Assigned engineer</span>
                    <select
                      value={editingStage.assigned_engineer_id ?? ""}
                      onChange={(e) => setEditingStage({ ...editingStage, assigned_engineer_id: e.target.value ? Number(e.target.value) : null })}
                    >
                      <option value="">None</option>
                      {engineers.map((eng) => (
                        <option key={eng.id} value={eng.id}>{eng.name}</option>
                      ))}
                    </select>
                  </label>
                  <label className="field">
                    <span>AI executable</span>
                    <select
                      value={editingStage.is_ai_executable ? "yes" : "no"}
                      onChange={(e) => setEditingStage({ ...editingStage, is_ai_executable: e.target.value === "yes" })}
                    >
                      <option value="yes">Yes — engineer agent can work on this stage</option>
                      <option value="no">No — manual or approval-only stage</option>
                    </select>
                  </label>
                  <label className="field">
                    <span>Requires human approval</span>
                    <select
                      value={editingStage.requires_human_approval ? "yes" : "no"}
                      onChange={(e) => setEditingStage({ ...editingStage, requires_human_approval: e.target.value === "yes" })}
                    >
                      <option value="no">No</option>
                      <option value="yes">Yes — task pauses until a human approves</option>
                    </select>
                  </label>
                  <label className="field">
                    <span>Max rework attempts</span>
                    <input
                      type="number"
                      value={editingStage.max_rework_attempts}
                      onChange={(e) => setEditingStage({ ...editingStage, max_rework_attempts: Number(e.target.value) })}
                    />
                  </label>
                  <label className="field">
                    <span>Rework target stage</span>
                    <select
                      value={editingStage.rework_target_stage_id ?? ""}
                      onChange={(e) => setEditingStage({ ...editingStage, rework_target_stage_id: e.target.value ? Number(e.target.value) : null })}
                    >
                      <option value="">None (block task on failure)</option>
                      {sortedStages.filter((s) => s.id !== stage.id).map((s) => (
                        <option key={s.id} value={s.id}>{s.name}</option>
                      ))}
                    </select>
                  </label>
                  <label className="field">
                    <span>Stage instructions (markdown)</span>
                    <textarea
                      className="editor-textarea"
                      value={editingStage.stage_instructions ?? ""}
                      onChange={(e) => setEditingStage({ ...editingStage, stage_instructions: e.target.value })}
                      placeholder="Enter stage-specific instructions for the AI engineer..."
                    />
                  </label>
                  <div className="actions">
                    <button
                      className="button"
                      disabled={isPending}
                      onClick={() => {
                        updateStage(stage.id, {
                          name: editingStage.name,
                          assigned_engineer_id: editingStage.assigned_engineer_id,
                          is_ai_executable: editingStage.is_ai_executable,
                          requires_human_approval: editingStage.requires_human_approval,
                          max_rework_attempts: editingStage.max_rework_attempts,
                          rework_target_stage_id: editingStage.rework_target_stage_id,
                          stage_instructions: editingStage.stage_instructions,
                        });
                        setEditingStage(null);
                      }}
                      type="button"
                    >
                      Save stage
                    </button>
                  </div>
                </div>
              ) : null}
            </div>
          ))
        )}

        <div className="stack" style={{ marginTop: 24 }}>
          <h3>Add new stage</h3>
          <div style={{ display: "flex", gap: 8 }}>
            <input
              value={newStageName}
              onChange={(e) => setNewStageName(e.target.value)}
              placeholder="Stage name (e.g. Code Review)"
              style={{ flex: 1 }}
            />
            <button className="button" disabled={isPending || !newStageName.trim()} onClick={addStage} type="button">
              Add stage
            </button>
          </div>
        </div>
      </section>
    </LayoutShell>
  );
}

export default function EditWorkflowPage() {
  return (
    <Suspense fallback={<LayoutShell><section className="panel"><div className="empty">Loading workflow editor...</div></section></LayoutShell>}>
      <EditWorkflowPageContent />
    </Suspense>
  );
}
