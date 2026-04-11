"use client";

import Link from "next/link";
import { useEffect, useState, useTransition } from "react";

import { ConfirmModal } from "@/components/confirm-modal";
import { LayoutShell } from "@/components/layout-shell";
import { api } from "@/lib/api";
import { Engineer } from "@/lib/types";

const templateLabels: Record<string, string> = {
  backend_engineer: "Backend Engineer",
  frontend_engineer: "Frontend Engineer",
  qa_test_engineer: "QA/Test Engineer",
  devops_deployment_engineer: "DevOps Engineer"
};

const runtimeStatusLabels: Record<string, string> = {
  stopped: "Stopped",
  starting: "Starting",
  healthy: "Healthy",
  heartbeat_missing: "Health ping missing",
  launch_failed: "Launch failed"
};

function formatRuntimeDuration(startedAt: string | null) {
  if (!startedAt) {
    return "—";
  }

  const started = new Date(startedAt);
  if (Number.isNaN(started.getTime())) {
    return "—";
  }

  const elapsedSeconds = Math.max(0, Math.floor((Date.now() - started.getTime()) / 1000));
  const days = Math.floor(elapsedSeconds / 86400);
  const hours = Math.floor((elapsedSeconds % 86400) / 3600);
  const minutes = Math.floor((elapsedSeconds % 3600) / 60);

  if (days > 0) {
    return hours > 0 ? `${days}d ${hours}h` : `${days}d`;
  }
  if (hours > 0) {
    return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`;
  }
  if (minutes > 0) {
    return `${minutes}m`;
  }
  return `${elapsedSeconds}s`;
}

function ActionIcon({ kind }: { kind: "launch" | "stop" | "restart" | "edit" | "delete" }) {
  if (kind === "launch") {
    return (
      <svg aria-hidden="true" fill="none" height="16" viewBox="0 0 16 16" width="16">
        <path d="M5 3.5L11.5 8L5 12.5V3.5Z" fill="currentColor" />
      </svg>
    );
  }

  if (kind === "stop") {
    return (
      <svg aria-hidden="true" fill="none" height="16" viewBox="0 0 16 16" width="16">
        <rect fill="currentColor" height="7" rx="1" width="7" x="4.5" y="4.5" />
      </svg>
    );
  }

  if (kind === "restart") {
    return (
      <svg aria-hidden="true" fill="none" height="16" viewBox="0 0 16 16" width="16">
        <path
          d="M12.5 5.5V2.8M12.5 2.8H9.8M12.5 2.8L10.9 4.4A5 5 0 1 0 13 8"
          stroke="currentColor"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="1.2"
        />
      </svg>
    );
  }

  if (kind === "delete") {
    return (
      <svg aria-hidden="true" fill="none" height="16" viewBox="0 0 16 16" width="16">
        <path
          d="M3.5 4.5H12.5M6.5 2.8H9.5M5.2 4.5L5.7 12.3C5.75 13 6.33 13.5 7 13.5H9C9.67 13.5 10.25 13 10.3 12.3L10.8 4.5"
          stroke="currentColor"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="1.2"
        />
      </svg>
    );
  }

  return (
    <svg aria-hidden="true" fill="none" height="16" viewBox="0 0 16 16" width="16">
      <path
        d="M10.8 2.3L13.7 5.2L6.1 12.8L3 13L3.2 9.9L10.8 2.3Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.2"
      />
    </svg>
  );
}

export default function EngineersPage() {
  const [engineers, setEngineers] = useState<Engineer[]>([]);
  const [activeEngineerId, setActiveEngineerId] = useState<number | null>(null);
  const [confirmAction, setConfirmAction] = useState<{ kind: "stop" | "restart" | "delete"; engineer: Engineer } | null>(null);
  const [isPending, startTransition] = useTransition();

  const loadEngineers = async () => {
    const items = await api.getEngineers();
    setEngineers(items);
  };

  useEffect(() => {
    loadEngineers();
  }, []);

  useEffect(() => {
    const interval = window.setInterval(loadEngineers, 30000);
    return () => window.clearInterval(interval);
  }, []);

  const executeLifecycleAction = async (engineer: Engineer, kind: "stop" | "restart" | "delete") => {
    setActiveEngineerId(engineer.id);
    try {
      if (kind === "delete") {
        await api.deleteEngineer(engineer.id);
      } else {
        await api.stopEngineer(engineer.id);
        if (kind === "restart") {
          await api.launchEngineer(engineer.id);
        }
      }
      await loadEngineers();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Engineer action failed.";
      window.alert(message);
    } finally {
      setActiveEngineerId(null);
    }
  };

  return (
    <LayoutShell
      topbarContent={
        <div style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
          <div>
            <div style={{ fontSize: 18, fontWeight: 600 }}>Dev Boss</div>
            <div className="muted" style={{ marginTop: 2 }}>Beta version</div>
          </div>
          <div className="topbar-actions">
            <Link className="button" href="/engineers/new">
              Add New Engineer
            </Link>
          </div>
        </div>
      }
    >
      <ConfirmModal
        confirmClassName={confirmAction?.kind === "restart" ? "button" : "button danger"}
        confirmLabel={
          confirmAction?.kind === "restart"
            ? "Restart engineer"
            : confirmAction?.kind === "delete"
              ? "Delete engineer"
              : "Stop engineer"
        }
        description={
          confirmAction
            ? confirmAction.kind === "restart"
              ? `This will stop and immediately relaunch ${confirmAction.engineer.name}'s runtime container.`
              : confirmAction.kind === "delete"
                ? `This will stop ${confirmAction.engineer.name}'s runtime container if needed and permanently delete the engineer record.`
                : `This will stop ${confirmAction.engineer.name}'s runtime container.`
            : ""
        }
        onCancel={() => setConfirmAction(null)}
        onConfirm={async () => {
          if (!confirmAction) {
            return;
          }
          const nextAction = confirmAction;
          setConfirmAction(null);
          startTransition(async () => {
            await executeLifecycleAction(nextAction.engineer, nextAction.kind);
          });
        }}
        open={confirmAction !== null}
        title={
          confirmAction?.kind === "restart"
            ? "Restart engineer?"
            : confirmAction?.kind === "delete"
              ? "Delete engineer?"
              : "Stop engineer?"
        }
      />
      <section className="panel">
        <div className="section-header">
          <div>
            <div className="eyebrow">Engineers</div>
            <h1>Engineer registry</h1>
            <p className="muted">Manage Codex-powered engineer profiles, runtime settings, and specialization templates.</p>
          </div>
        </div>

        {engineers.length === 0 ? (
          <div className="empty">No engineers yet.</div>
        ) : (
          <div className="table-shell">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Template</th>
                  <th>Model</th>
                  <th>Docker image</th>
                  <th>Running for</th>
                  <th>Runtime status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {engineers.map((engineer) => (
                  <tr key={engineer.id}>
                    <td>{engineer.name}</td>
                    <td>{templateLabels[engineer.template] ?? engineer.template}</td>
                    <td>{engineer.model_name}</td>
                    <td className="table-wrap">{engineer.docker_image}</td>
                    <td>{formatRuntimeDuration(engineer.runtime_started_at)}</td>
                    <td>
                      <div className="stack-compact">
                        <span
                          className={`tag compact${
                            engineer.runtime_status === "healthy"
                              ? ""
                              : engineer.runtime_status === "heartbeat_missing" || engineer.runtime_status === "launch_failed"
                                ? " danger"
                                : " warning"
                          }`}
                        >
                          {runtimeStatusLabels[engineer.runtime_status] ?? engineer.runtime_status}
                        </span>
                        {engineer.runtime_status_message ? (
                          <span className="table-subtext">{engineer.runtime_status_message}</span>
                        ) : null}
                      </div>
                    </td>
                    <td className="action-cell">
                      <div className="table-actions">
                        {engineer.runtime_status === "healthy" ||
                        engineer.runtime_status === "starting" ||
                        engineer.runtime_status === "heartbeat_missing" ? (
                          <>
                            <button
                              aria-label="Restart engineer"
                              className="icon-button warning"
                              disabled={activeEngineerId === engineer.id || isPending}
                              onClick={() => setConfirmAction({ kind: "restart", engineer })}
                              title={isPending && activeEngineerId === engineer.id ? "Restarting..." : "Restart engineer"}
                              type="button"
                            >
                              <ActionIcon kind="restart" />
                            </button>
                            <button
                              aria-label="Stop engineer"
                              className="icon-button danger"
                              disabled={activeEngineerId === engineer.id || isPending}
                              onClick={() => setConfirmAction({ kind: "stop", engineer })}
                              title={isPending && activeEngineerId === engineer.id ? "Stopping..." : "Stop engineer"}
                              type="button"
                            >
                              <ActionIcon kind="stop" />
                            </button>
                          </>
                        ) : (
                          <button
                            aria-label="Launch engineer"
                            className="icon-button success"
                            disabled={activeEngineerId === engineer.id || isPending}
                            onClick={() =>
                              startTransition(async () => {
                                setActiveEngineerId(engineer.id);
                                try {
                                  await api.launchEngineer(engineer.id);
                                  await loadEngineers();
                                } finally {
                                  setActiveEngineerId(null);
                                }
                              })
                            }
                            title={isPending && activeEngineerId === engineer.id ? "Launching..." : "Launch engineer"}
                            type="button"
                          >
                            <ActionIcon kind="launch" />
                          </button>
                        )}
                        <Link
                          aria-label="Edit engineer"
                          className="icon-button"
                          href={`/engineers/edit?engineerId=${engineer.id}`}
                          title="Edit engineer"
                        >
                          <ActionIcon kind="edit" />
                        </Link>
                        <button
                          aria-label="Delete engineer"
                          className="icon-button danger"
                          disabled={activeEngineerId === engineer.id || isPending}
                          onClick={() => setConfirmAction({ kind: "delete", engineer })}
                          title={isPending && activeEngineerId === engineer.id ? "Deleting..." : "Delete engineer"}
                          type="button"
                        >
                          <ActionIcon kind="delete" />
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
