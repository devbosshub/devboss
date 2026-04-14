"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";

import { api } from "@/lib/api";
import { Task, TaskRun } from "@/lib/types";

export function TaskActions({
  task,
  latestRun,
  onRefresh,
  renderMode = "buttons",
  onAfterAction
}: {
  task: Task;
  latestRun: TaskRun | null;
  onRefresh?: () => void | Promise<void>;
  renderMode?: "buttons" | "menu-items";
  onAfterAction?: () => void;
}) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  const advanceToGrooming = task.status === "draft";
  const advanceToReadyToDeploy = task.status === "human_testing";
  const canStartDeployment = task.status === "ready_to_deploy" && Boolean(task.pr_url);
  const canArchiveTask = task.status === "ready_to_deploy" || task.status === "deployed";
  const canApproveRun =
    latestRun !== null &&
    (task.status === "ai_grooming" ||
      task.status === "ready_for_build" ||
      canStartDeployment);

  if (!advanceToGrooming && !advanceToReadyToDeploy && !canApproveRun && !canArchiveTask) {
    return null;
  }

  const actionClassName = renderMode === "menu-items" ? "task-menu-item" : "button";
  const readyToDeployClassName = renderMode === "menu-items" ? "task-menu-item" : "button secondary";
  const containerClassName = renderMode === "menu-items" ? "task-menu-list" : "actions";

  return (
    <div className={containerClassName}>
      {advanceToGrooming ? (
        <button
          className={actionClassName}
          disabled={isPending}
          onClick={() =>
            startTransition(async () => {
              await api.updateTask(task.id, { status: "ai_grooming" });
              await onRefresh?.();
              onAfterAction?.();
              router.refresh();
            })
          }
          type="button"
        >
          Start AI grooming
        </button>
      ) : null}

      {advanceToReadyToDeploy ? (
        <button
          className={readyToDeployClassName}
          disabled={isPending}
          onClick={() =>
            startTransition(async () => {
              await api.updateTask(task.id, { status: "ready_to_deploy" });
              await onRefresh?.();
              onAfterAction?.();
              router.refresh();
            })
          }
          type="button"
        >
          Queue for release
        </button>
      ) : null}

      {canApproveRun ? (
        <button
          className={actionClassName}
          disabled={isPending}
          onClick={() =>
            startTransition(async () => {
              await api.approveTaskRun(latestRun.id, {
                summary:
                  task.status === "ready_to_deploy"
                    ? "Human merged the PR and started deployment."
                    : "Human approved the next execution step."
              });
              await onRefresh?.();
              onAfterAction?.();
              router.refresh();
            })
          }
          type="button"
        >
          {canStartDeployment
            ? "Start deployment"
            : task.status === "ready_for_build"
              ? "Approve build start"
              : "Approve grooming handoff"}
        </button>
      ) : null}

      {canArchiveTask ? (
        <button
          className={actionClassName}
          disabled={isPending}
          onClick={() => {
            const confirmed = window.confirm("Archive this task and remove it from the release queue?");
            if (!confirmed) {
              return;
            }

            startTransition(async () => {
              await api.updateTask(task.id, { status: "archived" });
              await onRefresh?.();
              onAfterAction?.();
              router.refresh();
            });
          }}
          type="button"
        >
          Archive task
        </button>
      ) : null}
    </div>
  );
}
