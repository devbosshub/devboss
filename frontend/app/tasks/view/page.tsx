"use client";

import Link from "next/link";
import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useSearchParams } from "next/navigation";

import { ConfirmModal } from "@/components/confirm-modal";
import { AddCommentForm, TaskEditorForm } from "@/components/forms";
import { LayoutShell } from "@/components/layout-shell";
import { MarkdownContent } from "@/components/markdown-content";
import { TaskActions } from "@/components/task-actions";
import { api } from "@/lib/api";
import { Engineer, Project, Task } from "@/lib/types";

function formatCommentTimestamp(value: string) {
  const timestamp = new Date(value);
  if (Number.isNaN(timestamp.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(timestamp);
}

function formatRunTimestamp(value: string | null) {
  if (!value) {
    return null;
  }
  return formatCommentTimestamp(value);
}

function formatRunPhase(phase: string) {
  const labels: Record<string, string> = {
    grooming: "AI Grooming",
    build: "In Progress",
    testing: "AI Testing",
    ready_to_deploy: "Ready to Deploy",
    deployment: "Deployment",
  };
  return labels[phase] ?? phase;
}

function getProjectWebBase(repoUrl: string | null) {
  if (!repoUrl) {
    return null;
  }

  const normalized = repoUrl.replace(/^git@github\.com:/, "https://github.com/").replace(/\.git$/, "");
  return normalized;
}

function TaskDetailPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const taskId = Number(searchParams.get("taskId") ?? "");
  const [task, setTask] = useState<Task | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [engineers, setEngineers] = useState<Engineer[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [confirmDeleteTask, setConfirmDeleteTask] = useState(false);
  const [isActionMenuOpen, setIsActionMenuOpen] = useState(false);
  const actionMenuRef = useRef<HTMLDivElement | null>(null);

  const loadTask = () => {
    if (Number.isNaN(taskId) || isDeleting) {
      return Promise.resolve();
    }
    return api.getTask(taskId).then((nextTask) => {
      setTask(nextTask);
      return api.getProject(nextTask.project_id).then(setProject);
    }).catch(() => setTask(null));
  };

  useEffect(() => {
    loadTask();
  }, [taskId, isDeleting]);

  useEffect(() => {
    api.getEngineers().then(setEngineers);
  }, []);

  useEffect(() => {
    if (Number.isNaN(taskId) || isDeleting) {
      return;
    }

    const refreshTask = () => {
      if (document.hidden) {
        return;
      }
      loadTask();
    };

    const intervalId = window.setInterval(refreshTask, 7000);
    const onVisibilityChange = () => {
      if (!document.hidden) {
        loadTask();
      }
    };

    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => {
      window.clearInterval(intervalId);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [taskId, isDeleting]);

  useEffect(() => {
    if (!isActionMenuOpen) {
      return;
    }

    const handlePointerDown = (event: MouseEvent) => {
      if (!actionMenuRef.current?.contains(event.target as Node)) {
        setIsActionMenuOpen(false);
      }
    };

    document.addEventListener("mousedown", handlePointerDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
    };
  }, [isActionMenuOpen]);

  const latestRun = task?.task_runs.at(-1) ?? null;
  const canEditTask = task?.status === "draft" || task?.status === "ai_grooming";
  const projectWebBase = getProjectWebBase(project?.repo_url ?? null);
  const branchUrl = projectWebBase && task?.branch_name ? `${projectWebBase}/tree/${encodeURIComponent(task.branch_name)}` : null;
  const canShowPullRequest = task ? ["ready_to_deploy", "deployed", "archived"].includes(task.status) : false;
  const sortedTaskRuns = [...(task?.task_runs ?? [])].sort(
    (left, right) => new Date(left.created_at).getTime() - new Date(right.created_at).getTime()
  );
  const sortedComments = [...(task?.comments ?? [])].sort(
    (left, right) => new Date(left.created_at).getTime() - new Date(right.created_at).getTime()
  );

  return (
    <LayoutShell
      hideTopbar={!task}
      topbarContent={
        task ? (
          <div style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
            <div>
              <div style={{ fontSize: 18, fontWeight: 600 }}>Dev Boss</div>
              <div className="muted" style={{ marginTop: 2 }}>Beta version</div>
            </div>
            <div className="topbar-actions">
              <Link className="button" href={`/board?projectId=${task.project_id}`}>
                Back to dashboard
              </Link>
            </div>
          </div>
        ) : undefined
      }
    >
      <ConfirmModal
        confirmClassName="button danger"
        confirmLabel="Delete task"
        description={
          task
            ? "This will permanently delete the task and all of its comments, task runs, and artifacts."
            : ""
        }
        onCancel={() => setConfirmDeleteTask(false)}
        onConfirm={async () => {
          if (!task) {
            return;
          }
          setConfirmDeleteTask(false);
          setIsDeleting(true);
          await api.deleteTask(task.id);
          window.location.href = `/board?projectId=${task.project_id}`;
        }}
        open={confirmDeleteTask}
        title="Delete task?"
      />
      {!task ? (
        <section className="panel">
          <div className="empty">{Number.isNaN(taskId) ? "Select a valid task." : "Task not found."}</div>
        </section>
      ) : (
        <div className="split">
          <section className="panel">
            <div className="task-header">
              <div className="task-header-chips">
                <span className="tag">{task.status}</span>
                {canShowPullRequest && task.pr_url ? <span className="tag">PR attached</span> : null}
                {task.deploy_url ? <span className="tag warning">Dev deployed</span> : null}
              </div>
              <div className="task-header-actions" ref={actionMenuRef}>
                <button
                  aria-expanded={isActionMenuOpen}
                  aria-haspopup="menu"
                  className="icon-button"
                  onClick={() => setIsActionMenuOpen((current) => !current)}
                  type="button"
                >
                  ⋯
                </button>
                {isActionMenuOpen ? (
                  <div className="task-menu-popover" role="menu">
                    <div className="task-menu-list">
                      <button
                        className="task-menu-item"
                        onClick={async () => {
                          setIsActionMenuOpen(false);
                          await api.retryTask(task.id);
                          await loadTask();
                          router.refresh();
                        }}
                        type="button"
                      >
                        Retry task
                      </button>
                      {canEditTask ? (
                        <button
                          className="task-menu-item"
                          onClick={() => {
                            setIsEditing((current) => !current);
                            setIsActionMenuOpen(false);
                          }}
                          type="button"
                        >
                          {isEditing ? "Cancel editing" : "Edit task"}
                        </button>
                      ) : null}
                      <TaskActions
                        latestRun={latestRun}
                        onAfterAction={() => setIsActionMenuOpen(false)}
                        onRefresh={loadTask}
                        renderMode="menu-items"
                        task={task}
                      />
                      <button
                        className="task-menu-item danger-text"
                        onClick={() => {
                          setIsActionMenuOpen(false);
                          setConfirmDeleteTask(true);
                        }}
                        type="button"
                      >
                        Delete task
                      </button>
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
            <h1>{task.title}</h1>
            <p className="muted">Project #{task.project_id}</p>

            <div className="stack">
              {canEditTask && isEditing ? (
                <div className="task-card">
                  <h3>Edit Task</h3>
                  <p className="muted">Draft and AI grooming tasks can still be refined before the build moves forward.</p>
                  <TaskEditorForm
                    engineers={engineers}
                    onUpdated={async (updatedTask) => {
                      setTask(updatedTask);
                      setIsEditing(false);
                    }}
                    task={task}
                  />
                </div>
              ) : null}
              <div>
                <h3>Requirements</h3>
                <p>{task.requirement_markdown}</p>
              </div>
              <div>
                <h3>Acceptance Criteria</h3>
                <p>{task.acceptance_criteria}</p>
              </div>
              <div>
                <h3>Implementation Steps</h3>
                <p>{task.implementation_steps || "No implementation steps yet."}</p>
              </div>
              <div className="grid two">
                <div className="task-card">
                  <h4>Git</h4>
                  <p>
                    Branch:{" "}
                    {branchUrl ? (
                      <a className="mini-link" href={branchUrl} rel="noreferrer" target="_blank">
                        {task.branch_name}
                      </a>
                    ) : (
                      task.branch_name ?? "Not created yet"
                    )}
                  </p>
                  <p>
                    PR:{" "}
                    {canShowPullRequest && task.pr_url ? (
                      <a className="mini-link" href={task.pr_url} rel="noreferrer" target="_blank">
                        Open pull request
                      </a>
                    ) : (
                      "Not opened yet"
                    )}
                  </p>
                </div>
                <div className="task-card">
                  <h4>Deploy</h4>
                  <p>Dev URL: {task.deploy_url ?? "Not deployed yet"}</p>
                  <p>Blocked reason: {task.blocked_reason ?? "None"}</p>
                </div>
              </div>
              <div>
                <h3>Task Runs</h3>
                {sortedTaskRuns.length === 0 ? (
                  <div className="empty">No task runs yet.</div>
                ) : (
                  <div className="stack">
                    {sortedTaskRuns.map((run) => (
                      <div className="task-card" key={run.id}>
                        <div className="actions">
                          <span className="tag">{formatRunPhase(run.phase)}</span>
                          <span className="tag">{run.status}</span>
                          {run.outcome_type ? <span className="tag warning">{run.outcome_type}</span> : null}
                        </div>
                        <div className="run-timestamps">
                          <span>Created: {formatRunTimestamp(run.created_at) ?? "—"}</span>
                          <span>Started: {formatRunTimestamp(run.started_at) ?? "—"}</span>
                          <span>Completed: {formatRunTimestamp(run.completed_at) ?? "—"}</span>
                          <span>Latest heartbeat: {formatRunTimestamp(run.heartbeat_at) ?? "—"}</span>
                        </div>
                        <p>{run.summary ?? "No summary yet."}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </section>

          <section className="panel">
            <h2>Conversation</h2>
            <p className="muted">The task thread is the source of truth for human-agent collaboration.</p>
            <div className="stack">
              {sortedComments.length === 0 ? (
                <div className="empty">No comments yet.</div>
              ) : (
                sortedComments.map((comment) => (
                  <div className="comment" key={comment.id}>
                    <div className="comment-header">
                      <div>
                        <strong>{comment.author_name}</strong>
                        <div className="muted">{comment.author_type}</div>
                        <div className="comment-timestamp">{formatCommentTimestamp(comment.created_at)}</div>
                      </div>
                      <button
                        className="button tertiary danger-text"
                        onClick={async () => {
                          if (!window.confirm("Delete this comment?")) {
                            return;
                          }
                          await api.deleteComment(task.id, comment.id);
                          await loadTask();
                          router.refresh();
                        }}
                        type="button"
                      >
                        Delete
                      </button>
                    </div>
                    <MarkdownContent content={comment.body} />
                    {comment.action_required ? <span className="tag danger">Needs reply</span> : null}
                  </div>
                ))
              )}
            </div>
            <AddCommentForm onAdded={loadTask} taskId={task.id} />

            <div className="stack" style={{ marginTop: 24 }}>
              <h3>Evidence</h3>
              {task.artifacts.length === 0 ? (
                <div className="empty">Artifacts will appear here after runs upload logs, screenshots, or reports.</div>
              ) : (
                task.artifacts.map((artifact) => (
                  <div className="task-card" key={artifact.id}>
                    <div className="actions">
                      <span className="tag">{artifact.kind}</span>
                    </div>
                    <p>{artifact.name}</p>
                    <p className="muted">{artifact.file_path}</p>
                  </div>
                ))
              )}
            </div>
          </section>
        </div>
      )}
    </LayoutShell>
  );
}

export default function TaskDetailPage() {
  return (
    <Suspense fallback={<LayoutShell><section className="panel"><div className="empty">Loading task...</div></section></LayoutShell>}>
      <TaskDetailPageContent />
    </Suspense>
  );
}
