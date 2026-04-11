"use client";

import { useEffect, useState } from "react";

import { LayoutShell } from "@/components/layout-shell";
import { api } from "@/lib/api";
import { BoardResponse, Engineer, Project } from "@/lib/types";

export default function HomePage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [engineers, setEngineers] = useState<Engineer[]>([]);
  const [board, setBoard] = useState<BoardResponse | null>(null);

  const loadOverview = () => {
    Promise.all([api.getProjects(), api.getEngineers(), api.getBoard()]).then(([projectItems, engineerItems, boardData]) => {
      setProjects(projectItems);
      setEngineers(engineerItems);
      setBoard(boardData);
    });
  };

  useEffect(() => {
    loadOverview();
  }, []);

  const activeTasks = board ? board.lanes.reduce((count, lane) => count + lane.tasks.length, 0) : 0;
  const blockedTasks = board
    ? board.lanes.reduce((count, lane) => count + lane.tasks.filter((task) => Boolean(task.blocked_reason)).length, 0)
    : 0;
  return (
    <LayoutShell
      topbarContent={
        <div style={{ width: "100%" }}>
          <div style={{ fontSize: 18, fontWeight: 600 }}>Dev Boss</div>
          <div className="muted" style={{ marginTop: 2 }}>Beta version</div>
        </div>
      }
    >
      <section className="panel">
        <div className="section-header">
          <div>
            <div className="eyebrow">Overview</div>
            <h1>Workspace summary</h1>
            <p className="muted">A quick count of what the Dev Boss workspace is currently tracking.</p>
          </div>
        </div>
        <div className="metric-grid">
          <div className="metric-card">
            <span className="metric-value">{projects.length}</span>
            <span className="metric-label">Projects</span>
          </div>
          <div className="metric-card">
            <span className="metric-value">{engineers.length}</span>
            <span className="metric-label">Engineers</span>
          </div>
          <div className="metric-card">
            <span className="metric-value">{activeTasks}</span>
            <span className="metric-label">Tracked tasks</span>
          </div>
          <div className="metric-card">
            <span className="metric-value">{blockedTasks}</span>
            <span className="metric-label">Blocked</span>
          </div>
        </div>
      </section>
    </LayoutShell>
  );
}
