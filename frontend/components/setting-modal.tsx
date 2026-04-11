"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";

import { SettingForm } from "@/components/forms";
import { ConfigSetting } from "@/lib/types";

export function SettingModal({
  setting,
  triggerLabel,
  triggerClassName = "button",
  onSaved,
}: {
  setting?: ConfigSetting;
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
                    <div className="eyebrow">{setting ? "Edit Global Config" : "New Global Config"}</div>
                    <h2>{setting ? "Edit global config" : "Add global config"}</h2>
                    <p className="muted">
                      {setting
                        ? "Update the stored value, description, or secret flag for this workspace-wide config."
                        : "Store a new workspace-wide config value for integrations like GitHub or AWS."}
                    </p>
                  </div>
                  <button aria-label="Close modal" className="modal-close" onClick={() => setOpen(false)} type="button">
                    Close
                  </button>
                </div>
                <SettingForm
                  onCreated={async () => {
                    setOpen(false);
                    await onSaved?.();
                  }}
                  onUpdated={async () => {
                    setOpen(false);
                    await onSaved?.();
                  }}
                  setting={setting}
                />
              </div>
            </div>,
            document.body
          )
        : null}
    </>
  );
}
