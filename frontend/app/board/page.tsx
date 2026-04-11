"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { LayoutShell } from "@/components/layout-shell";
import { ProjectBoardHeader } from "@/components/project-board-header";
import { TaskBoard } from "@/components/task-board";
import { api } from "@/lib/api";
import { BoardResponse, Engineer, Project } from "@/lib/types";

function BoardPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [engineers, setEngineers] = useState<Engineer[]>([]);
  const [board, setBoard] = useState<BoardResponse | null>(null);
  const projectId = Number(searchParams.get("projectId") ?? "");

  const loadBoard = (nextProjectId: number) => {
    api.getProjectBoard(nextProjectId).then(setBoard);
  };

  useEffect(() => {
    Promise.all([api.getProjects(), api.getEngineers()]).then(([projectItems, engineerItems]) => {
      setProjects(projectItems);
      setEngineers(engineerItems);
      const fallbackProjectId = projectItems[0]?.id;
      const nextProjectId = Number.isNaN(projectId) ? fallbackProjectId : projectId;
      if (!nextProjectId) {
        return;
      }
      if (Number.isNaN(projectId) && fallbackProjectId) {
        router.replace(`/board?projectId=${fallbackProjectId}`);
      }
      loadBoard(nextProjectId);
    });
  }, [projectId, router]);

  useEffect(() => {
    const nextProjectId = Number.isNaN(projectId) ? projects[0]?.id : projectId;
    if (!nextProjectId) {
      return;
    }

    const refreshBoard = () => {
      if (document.hidden) {
        return;
      }
      loadBoard(nextProjectId);
    };

    const intervalId = window.setInterval(refreshBoard, 12000);
    const onVisibilityChange = () => {
      if (!document.hidden) {
        loadBoard(nextProjectId);
      }
    };

    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => {
      window.clearInterval(intervalId);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [projectId, projects]);

  const activeProjectId = Number.isNaN(projectId) ? projects[0]?.id ?? 0 : projectId;
  const activeProject = projects.find((project) => project.id === activeProjectId);

  return (
    <LayoutShell
      topbarContent={
        <ProjectBoardHeader
          engineers={engineers}
          onTaskCreated={(createdProjectId) => {
            if (createdProjectId !== activeProjectId) {
              router.push(`/board?projectId=${createdProjectId}`);
              return;
            }
            loadBoard(createdProjectId);
          }}
          projectId={activeProjectId}
          projects={projects}
        />
      }
    >
      <section className="panel">
        <div className="section-header">
          <div>
            <div className="eyebrow">Execution</div>
            <h1>{activeProject?.name ?? "Task dashboard"}</h1>
            <p className="muted">Task dashboard for this project. Switch projects from the dropdown above.</p>
          </div>
        </div>
        <TaskBoard lanes={board?.lanes ?? []} />
      </section>
    </LayoutShell>
  );
}

export default function BoardPage() {
  return (
    <Suspense fallback={<LayoutShell><section className="panel"><div className="empty">Loading task dashboard...</div></section></LayoutShell>}>
      <BoardPageContent />
    </Suspense>
  );
}
