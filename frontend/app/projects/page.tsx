"use client";

import { useEffect, useState } from "react";

import { ConfirmModal } from "@/components/confirm-modal";
import { LayoutShell } from "@/components/layout-shell";
import { ProjectModal } from "@/components/project-modal";
import { api } from "@/lib/api";
import { Project } from "@/lib/types";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectToDelete, setProjectToDelete] = useState<Project | null>(null);

  const loadProjects = () => {
    api.getProjects().then(setProjects);
  };

  useEffect(() => {
    loadProjects();
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
            <ProjectModal onSaved={loadProjects} triggerLabel="Add Project" />
          </div>
        </div>
      }
    >
      <ConfirmModal
        confirmClassName="button danger"
        confirmLabel="Delete project"
        description={
          projectToDelete
            ? `This will delete ${projectToDelete.name} and all of its tasks, comments, task runs, and artifacts.`
            : ""
        }
        onCancel={() => setProjectToDelete(null)}
        onConfirm={async () => {
          if (!projectToDelete) {
            return;
          }
          const selectedProject = projectToDelete;
          setProjectToDelete(null);
          await api.deleteProject(selectedProject.id);
          await loadProjects();
        }}
        open={projectToDelete !== null}
        title="Delete project?"
      />
      <section className="panel">
        <div className="section-header">
          <div>
            <div className="eyebrow">Projects</div>
            <h1>Project registry</h1>
            <p className="muted">Manage repository details, default branches, and project-level metadata.</p>
          </div>
        </div>

        {projects.length === 0 ? (
          <div className="empty">No projects yet.</div>
        ) : (
          <div className="table-shell">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Repository</th>
                  <th>Default branch</th>
                  <th>Deploy type</th>
                  <th>Dashboard</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {projects.map((project) => (
                  <tr key={project.id}>
                    <td>{project.name}</td>
                    <td className="table-wrap">{project.repo_url}</td>
                    <td>{project.default_branch}</td>
                    <td>{(project.deploy_config.type as string) ?? "not configured"}</td>
                    <td>
                      <a className="dashboard-link" href={`/board?projectId=${project.id}`}>
                        <span>Open Dashboard</span>
                        <span aria-hidden="true">↗</span>
                      </a>
                    </td>
                    <td className="action-cell">
                      <div className="table-actions">
                        <ProjectModal onSaved={loadProjects} project={project} triggerClassName="button secondary" triggerLabel="Edit" />
                        <button className="button danger" onClick={() => setProjectToDelete(project)} type="button">
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
