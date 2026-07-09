"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ConfirmModal } from "@/components/confirm-modal";
import { LayoutShell } from "@/components/layout-shell";
import { api } from "@/lib/api";
import { Workflow } from "@/lib/types";

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [workflowToDelete, setWorkflowToDelete] = useState<Workflow | null>(null);

  const loadWorkflows = () => {
    api.getWorkflows().then(setWorkflows);
  };

  useEffect(() => {
    loadWorkflows();
  }, []);

  return (
    <LayoutShell
      topbarContent={
        <div style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
          <div>
            <div style={{ fontSize: 18, fontWeight: 600 }}>Dev Boss</div>
            <div className="muted" style={{ marginTop: 2 }}>Beta version</div>
          </div>
          <div className="topbar-actions">
            <Link className="button" href="/workflows/new">
              Add New Workflow
            </Link>
          </div>
        </div>
      }
    >
      <ConfirmModal
        confirmClassName="button danger"
        confirmLabel="Delete workflow"
        description={
          workflowToDelete
            ? `This will delete the workflow "${workflowToDelete.name}" and all of its stages.`
            : ""
        }
        onCancel={() => setWorkflowToDelete(null)}
        onConfirm={async () => {
          if (!workflowToDelete) return;
          const selectedWorkflow = workflowToDelete;
          setWorkflowToDelete(null);
          await api.deleteWorkflow(selectedWorkflow.id);
          await loadWorkflows();
        }}
        open={workflowToDelete !== null}
        title="Delete workflow?"
      />
      <section className="panel">
        <div className="section-header">
          <div>
            <div className="eyebrow">Workflows</div>
            <h1>Workflow registry</h1>
            <p className="muted">Define configurable pipelines with stages, each assigned to an engineer.</p>
          </div>
        </div>

        {workflows.length === 0 ? (
          <div className="empty">No workflows yet.</div>
        ) : (
          <div className="table-shell">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Description</th>
                  <th>Stages</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {workflows.map((workflow) => (
                  <tr key={workflow.id}>
                    <td>{workflow.name}</td>
                    <td>{workflow.description ?? "—"}</td>
                    <td>{workflow.stages.length} stage{workflow.stages.length !== 1 ? "s" : ""}</td>
                    <td>{new Date(workflow.created_at).toLocaleDateString()}</td>
                    <td className="action-cell">
                      <div className="table-actions">
                        <Link className="button secondary" href={`/workflows/edit?workflowId=${workflow.id}`}>
                          Edit
                        </Link>
                        <button className="button danger" onClick={() => setWorkflowToDelete(workflow)} type="button">
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </LayoutShell>
  );
}
