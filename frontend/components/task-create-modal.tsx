"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";

import { CreateTaskForm } from "@/components/forms";
import { Engineer, Project } from "@/lib/types";

export function TaskCreateModal({
  projects,
  engineers,
  initialProjectId,
  onCreated,
  triggerLabel = "Create Task",
  triggerClassName = "button"
}: {
  projects: Project[];
  engineers: Engineer[];
  initialProjectId?: number;
  onCreated?: (projectId: number) => void | Promise<void>;
  triggerLabel?: string;
  triggerClassName?: string;
}) {
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <>
      <button className={triggerClassName} onClick={() => setOpen(true)} type="button">
        {triggerLabel}
      </button>

      {mounted && open
        ? createPortal(
            <div className="modal-overlay" onClick={() => setOpen(false)} role="presentation">
              <div
                aria-modal="true"
                className="modal"
                onClick={(event) => event.stopPropagation()}
                role="dialog"
              >
                <div className="modal-header">
                  <div>
                    <div className="eyebrow">New Task</div>
                    <h2>Create task</h2>
                    <p className="muted">Add a task without leaving the current page.</p>
                  </div>
                  <button aria-label="Close modal" className="modal-close" onClick={() => setOpen(false)} type="button">
                    Close
                  </button>
                </div>

                {projects.length === 0 ? (
                  <div className="empty">Create a project first before adding a task.</div>
                ) : (
                  <CreateTaskForm
                    engineers={engineers}
                    initialProjectId={initialProjectId}
                    onCreated={async (task) => {
                      setOpen(false);
                      await onCreated?.(task.project_id);
                    }}
                    projects={projects}
                  />
                )}
              </div>
            </div>,
            document.body
          )
        : null}
    </>
  );
}
