"use client";

import { useRouter } from "next/navigation";
import { ChangeEvent } from "react";

import { TaskCreateModal } from "@/components/task-create-modal";
import { Engineer, Project } from "@/lib/types";

export function ProjectBoardHeader({
  projects,
  projectId,
  engineers,
  onTaskCreated
}: {
  projects: Project[];
  projectId: number;
  engineers: Engineer[];
  onTaskCreated?: (projectId: number) => void | Promise<void>;
}) {
  const router = useRouter();

  const onProjectChange = (event: ChangeEvent<HTMLSelectElement>) => {
    router.push(`/board?projectId=${event.target.value}`);
  };

  return (
    <div className="topbar-actions" style={{ width: "100%", justifyContent: "space-between", alignItems: "center" }}>
      <div className="board-project-picker" style={{ minWidth: 260 }}>
        <label className="board-project-label" htmlFor="board-project-select">
          Select project
        </label>
        <select className="board-project-select" id="board-project-select" onChange={onProjectChange} value={projectId}>
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </div>
      <TaskCreateModal engineers={engineers} initialProjectId={projectId} onCreated={onTaskCreated} projects={projects} />
    </div>
  );
}
