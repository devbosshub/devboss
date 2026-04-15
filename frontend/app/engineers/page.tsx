"use client";

import Link from "next/link";
import { useEffect, useMemo, useState, useTransition } from "react";

import { ConfirmModal } from "@/components/confirm-modal";
import { LayoutShell } from "@/components/layout-shell";
import { api } from "@/lib/api";
import { Engineer, EngineerRuntime } from "@/lib/types";

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

function formatRuntimeDetails(runtime: EngineerRuntime) {
  const isBusy = runtime.current_task_run_id !== null;
  const isRunning = ["starting", "healthy", "heartbeat_missing"].includes(runtime.runtime_status);
  const statusLine = runtime.status_message?.trim();

  if (isRunning) {
    return `Running for ${formatRuntimeDuration(runtime.started_at)}${isBusy ? ` • Task run #${runtime.current_task_run_id}` : ""}`;
  }

  if (statusLine) {
    return statusLine;
  }

  return "Runtime is not running.";
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

type ConfirmAction =
  | { kind: "stop-runtime" | "restart-runtime"; engineerName: string; runtime: EngineerRuntime }
  | { kind: "delete-engineer"; engineer: Engineer };

export default function EngineersPage() {
  const [engineers, setEngineers] = useState<Engineer[]>([]);
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const [confirmAction, setConfirmAction] = useState<ConfirmAction | null>(null);
  const [isPending, startTransition] = useTransition();

  const loadEngineers = async () => {
    const items = await api.getEngineers();
    setEngineers(items);
  };

  useEffect(() => {
    loadEngineers();
  }, []);

  useEffect(() => {
    const interval = window.setInterval(loadEngineers, 15000);
    return () => window.clearInterval(interval);
  }, []);

  const executeAction = async (action: ConfirmAction) => {
    if (action.kind === "delete-engineer") {
      setActiveKey(`engineer-${action.engineer.id}`);
      try {
        await api.deleteEngineer(action.engineer.id);
        await loadEngineers();
      } finally {
        setActiveKey(null);
      }
      return;
    }

    setActiveKey(`runtime-${action.runtime.id}`);
    try {
      if (action.kind === "stop-runtime") {
        await api.stopEngineerRuntime(action.runtime.id);
      } else {
        await api.restartEngineerRuntime(action.runtime.id);
      }
      await loadEngineers();
    } finally {
      setActiveKey(null);
    }
  };

  const confirmText = useMemo(() => {
    if (!confirmAction) {
      return null;
    }
    if (confirmAction.kind === "delete-engineer") {
      return {
        title: "Delete engineer?",
        label: "Delete engineer",
        className: "button danger",
        description: `This will permanently delete ${confirmAction.engineer.name}. Make sure no tasks are assigned and all runtime instances are stopped first.`
      };
    }

    return confirmAction.kind === "restart-runtime"
      ? ["stopped", "launch_failed"].includes(confirmAction.runtime.runtime_status)
        ? {
            title: "Start runtime?",
            label: "Start runtime",
            className: "button",
            description: `This will start runtime #${confirmAction.runtime.id} for ${confirmAction.engineerName}.`
          }
        : {
            title: "Restart runtime?",
            label: "Restart runtime",
            className: "button",
            description: `This will restart runtime #${confirmAction.runtime.id} for ${confirmAction.engineerName}.`
          }
      : {
          title: "Stop runtime?",
          label: "Stop runtime",
          className: "button danger",
          description: `This will stop runtime #${confirmAction.runtime.id} for ${confirmAction.engineerName}.`
        };
  }, [confirmAction]);

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
        confirmClassName={confirmText?.className ?? "button"}
        confirmLabel={confirmText?.label ?? "Confirm"}
        description={confirmText?.description ?? ""}
        onCancel={() => setConfirmAction(null)}
        onConfirm={async () => {
          if (!confirmAction) {
            return;
          }
          const nextAction = confirmAction;
          setConfirmAction(null);
          startTransition(async () => {
            try {
              await executeAction(nextAction);
            } catch (error) {
              const message = error instanceof Error ? error.message : "Engineer action failed.";
              window.alert(message);
            }
          });
        }}
        open={confirmAction !== null}
        title={confirmText?.title ?? "Confirm action"}
      />
      <section className="panel">
        <div className="section-header">
          <div>
            <div className="eyebrow">Engineers</div>
            <h1>Engineer registry</h1>
            <p className="muted">Launch multiple runtime containers per engineer and let queued tasks wait for the next free runtime.</p>
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
                  <th>Runtime capacity</th>
                  <th>Runtime status</th>
                  <th>Runtime instances</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {engineers.map((engineer) => {
                  const hasReusableRuntime = engineer.runtimes.some((runtime) =>
                    ["stopped", "launch_failed"].includes(runtime.runtime_status)
                  );
                  return (
                  <tr key={engineer.id}>
                    <td>{engineer.name}</td>
                    <td>{templateLabels[engineer.template] ?? engineer.template}</td>
                    <td>{engineer.model_name}</td>
                    <td className="table-wrap">{engineer.docker_image}</td>
                    <td>{engineer.healthy_runtime_count}/{engineer.runtime_count || 0} healthy</td>
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
                        {engineer.runtime_status_message ? <span className="table-subtext">{engineer.runtime_status_message}</span> : null}
                      </div>
                    </td>
                    <td>
                      {engineer.runtimes.length === 0 ? (
                        <span className="muted">No runtime instances</span>
                      ) : (
                        <div className="stack-compact">
                          {engineer.runtimes.map((runtime) => {
                            const runtimeKey = `runtime-${runtime.id}`;
                            const isRunning = ["starting", "healthy", "heartbeat_missing"].includes(runtime.runtime_status);
                            return (
                              <div className="table-runtime-row" key={runtime.id}>
                                <div className="table-runtime-meta">
                                  <span className={`tag compact${runtime.runtime_status === "healthy" ? "" : runtime.runtime_status === "heartbeat_missing" || runtime.runtime_status === "launch_failed" ? " danger" : " warning"}`}>
                                    #{runtime.id} {runtimeStatusLabels[runtime.runtime_status] ?? runtime.runtime_status}
                                  </span>
                                  <span className="table-subtext">{formatRuntimeDetails(runtime)}</span>
                                </div>
                                <div className="table-actions">
                                  <button
                                    aria-label={isRunning ? "Restart runtime" : "Start runtime"}
                                    className={`icon-button ${isRunning ? "warning" : "success"}`}
                                    disabled={activeKey === runtimeKey || isPending}
                                    onClick={() => setConfirmAction({ kind: "restart-runtime", engineerName: engineer.name, runtime })}
                                    title={isRunning ? "Restart runtime" : "Start runtime"}
                                    type="button"
                                  >
                                    <ActionIcon kind={isRunning ? "restart" : "launch"} />
                                  </button>
                                  {isRunning ? (
                                    <>
                                      <button
                                        aria-label="Stop runtime"
                                        className="icon-button danger"
                                        disabled={activeKey === runtimeKey || isPending}
                                        onClick={() => setConfirmAction({ kind: "stop-runtime", engineerName: engineer.name, runtime })}
                                        title="Stop runtime"
                                        type="button"
                                      >
                                        <ActionIcon kind="stop" />
                                      </button>
                                    </>
                                  ) : null}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </td>
                    <td className="action-cell">
                      <div className="table-actions">
                        <button
                          aria-label={hasReusableRuntime ? "Run stopped runtime" : "Launch new runtime"}
                          className="icon-button success"
                          disabled={activeKey === `engineer-${engineer.id}` || isPending}
                          onClick={() =>
                            startTransition(async () => {
                              setActiveKey(`engineer-${engineer.id}`);
                              try {
                                await api.launchEngineer(engineer.id);
                                await loadEngineers();
                              } catch (error) {
                                const message = error instanceof Error ? error.message : "Runtime launch failed.";
                                window.alert(message);
                              } finally {
                                setActiveKey(null);
                              }
                            })
                          }
                          title={hasReusableRuntime ? "Run stopped runtime" : "Launch new runtime"}
                          type="button"
                        >
                          <ActionIcon kind="launch" />
                        </button>
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
                          disabled={activeKey === `engineer-${engineer.id}` || isPending}
                          onClick={() => setConfirmAction({ kind: "delete-engineer", engineer })}
                          title="Delete engineer"
                          type="button"
                        >
                          <ActionIcon kind="delete" />
                        </button>
                      </div>
                    </td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </LayoutShell>
  );
}
