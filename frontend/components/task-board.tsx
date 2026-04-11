import Link from "next/link";

import { BoardLane } from "@/lib/types";

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
  return (
    <div className="board-scroll">
      <div className="board">
        {lanes.map((lane) => (
          <section className="lane" key={lane.status}>
            <div className="lane-header">
              <h3>{statusLabel[lane.status]}</h3>
              <span className="tag">{lane.tasks.length}</span>
            </div>
            <div className="lane-body">
              {lane.tasks.length === 0 ? (
                <div className="empty">No tasks here yet.</div>
              ) : (
                lane.tasks.map((task) => (
                  <Link className="task-card" href={`/tasks/view?taskId=${task.id}`} key={task.id}>
                    <div className="task-meta">
                      <span>Task #{task.id}</span>
                      <span>{task.assigned_engineer_id ? `Engineer ${task.assigned_engineer_id}` : "Unassigned"}</span>
                    </div>
                    <div className="task-title">{task.title}</div>
                    <p className="task-preview">{task.requirement_markdown.slice(0, 120)}...</p>
                    <div className="actions">
                      {task.pr_url ? <span className="tag">PR linked</span> : null}
                      {task.blocked_reason ? <span className="tag danger">Blocked</span> : null}
                      {task.deploy_url ? <span className="tag warning">Dev live</span> : null}
                    </div>
                  </Link>
                ))
              )}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
