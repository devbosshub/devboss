"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import { CreateTaskForm } from "@/components/forms";
import { LayoutShell } from "@/components/layout-shell";
import { api } from "@/lib/api";
import { Engineer, Project } from "@/lib/types";

function NewTaskPageContent() {
  const searchParams = useSearchParams();
  const initialProjectId = Number(searchParams.get("projectId") ?? "");
  const [projects, setProjects] = useState<Project[]>([]);
  const [engineers, setEngineers] = useState<Engineer[]>([]);

  useEffect(() => {
    Promise.all([api.getProjects(), api.getEngineers()]).then(([projectItems, engineerItems]) => {
      setProjects(projectItems);
      setEngineers(engineerItems);
    });
  }, []);

  return (
    <LayoutShell>
      <section className="panel">
        <div className="section-header">
          <div>
            <div className="eyebrow">New Task</div>
            <h1>Create task</h1>
            <p className="muted">Define the project, requirements, acceptance criteria, and assigned engineer for a new task.</p>
          </div>
          <div className="section-actions">
            <Link className="button secondary" href={Number.isNaN(initialProjectId) ? "/board" : `/board?projectId=${initialProjectId}`}>
              Back to task dashboard
            </Link>
          </div>
        </div>

        {projects.length === 0 ? (
          <div className="empty">Create a project first before adding a task.</div>
        ) : (
          <CreateTaskForm
            engineers={engineers}
            initialProjectId={Number.isNaN(initialProjectId) ? undefined : initialProjectId}
            onSuccessPath={Number.isNaN(initialProjectId) ? "/board" : `/board?projectId=${initialProjectId}`}
            projects={projects}
          />
        )}
      </section>
    </LayoutShell>
  );
}

export default function NewTaskPage() {
  return (
    <Suspense fallback={<LayoutShell><section className="panel"><div className="empty">Loading task form...</div></section></LayoutShell>}>
      <NewTaskPageContent />
    </Suspense>
  );
}
