"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";

import { ProjectForm } from "@/components/forms";
import { Project } from "@/lib/types";

export function ProjectModal({
  project,
  triggerLabel,
  triggerClassName = "button",
  onSaved,
}: {
  project?: Project;
  triggerLabel: string;
  triggerClassName?: string;
  onSaved?: () => void | Promise<void>;
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
              <div aria-modal="true" className="modal" onClick={(event) => event.stopPropagation()} role="dialog">
                <div className="modal-header">
                  <div>
                    <div className="eyebrow">{project ? "Edit Project" : "New Project"}</div>
                    <h2>{project ? "Edit project" : "Create project"}</h2>
                    <p className="muted">
                      {project
                        ? "Update project details like name, repository URL, and default branch."
                        : "Add a new project and connect it to its repository."}
                    </p>
                  </div>
                  <button aria-label="Close modal" className="modal-close" onClick={() => setOpen(false)} type="button">
                    Close
                  </button>
                </div>
                <ProjectForm
                  onCreated={async () => {
                    setOpen(false);
                    await onSaved?.();
                  }}
                  onUpdated={async () => {
                    setOpen(false);
                    await onSaved?.();
                  }}
                  project={project}
                />
              </div>
            </div>,
            document.body
          )
        : null}
    </>
  );
}
