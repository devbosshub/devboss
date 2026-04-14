"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { BoardLane } from "@/lib/types";

const ARCHIVED_PAGE_SIZE = 3;

const statusLabel: Record<string, string> = {
  draft: "Draft",
  ai_grooming: "AI Grooming",
  ready_for_build: "Ready for Build",
  in_progress: "In Progress",
  ai_testing: "AI Testing",
  human_testing: "Human Testing",
  ready_to_deploy: "Ready to Deploy",
  deployed: "Deployment",
  archived: "Archived"
};

export function TaskBoard({ lanes }: { lanes: BoardLane[] }) {
  const [visibleArchivedCount, setVisibleArchivedCount] = useState(ARCHIVED_PAGE_SIZE);

  useEffect(() => {
    setVisibleArchivedCount(ARCHIVED_PAGE_SIZE);
  }, [lanes]);

  return (
    <div className="board-scroll">
      <div className="board">
        {lanes.map((lane) => {
          const isArchivedLane = lane.status === "archived";
          const visibleTasks = isArchivedLane ? lane.tasks.slice(0, visibleArchivedCount) : lane.tasks;
          const remainingArchivedCount = isArchivedLane ? Math.max(lane.tasks.length - visibleTasks.length, 0) : 0;

          return (
            <section className="lane" key={lane.status}>
              <div className="lane-header">
                <h3>{statusLabel[lane.status]}</h3>
                <span className="tag">{lane.tasks.length}</span>
              </div>
              <div className="lane-body">
                {visibleTasks.length === 0 ? (
                  <div className="empty">No tasks here yet.</div>
                ) : (
                  visibleTasks.map((task) => (
                    <Link className="task-card" href={`/tasks/view?taskId=${task.id}`} key={task.id}>
                      <div className="task-meta">
                        <span>Task #{task.id}</span>
                        <span>{task.assigned_engineer_id ? `Engineer ${task.assigned_engineer_id}` : "Unassigned"}</span>
                      </div>
                      <div className="task-title">{task.title}</div>
                      <p className="task-preview">{task.requirement_markdown.slice(0, 120)}...</p>
                      <div className="actions">
                        {task.status === "ready_to_deploy" ? (
                          <span className="tag warning">{task.pr_url ? "Release prep" : "Queued for release"}</span>
                        ) : null}
                        {task.status === "deployed" ? <span className="tag warning">Releasing</span> : null}
                        {task.pr_url ? <span className="tag">PR linked</span> : null}
                        {task.blocked_reason ? <span className="tag danger">Blocked</span> : null}
                        {task.deploy_url ? <span className="tag warning">Dev live</span> : null}
                      </div>
                    </Link>
                  ))
                )}
                {isArchivedLane && lane.tasks.length > ARCHIVED_PAGE_SIZE ? (
                  <div className="lane-footer">
                    <div className="lane-footnote">
                      Showing {visibleTasks.length} of {lane.tasks.length} archived tasks
                    </div>
                    {remainingArchivedCount > 0 ? (
                      <button
                        className="button secondary lane-load-more"
                        onClick={() => setVisibleArchivedCount((count) => count + ARCHIVED_PAGE_SIZE)}
                        type="button"
                      >
                        Load {Math.min(ARCHIVED_PAGE_SIZE, remainingArchivedCount)} more
                      </button>
                    ) : null}
                  </div>
                ) : null}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}
