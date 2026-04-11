"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";

export function ConfirmModal({
  open,
  title,
  description,
  confirmLabel,
  confirmClassName = "button danger",
  onCancel,
  onConfirm
}: {
  open: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  confirmClassName?: string;
  onCancel: () => void;
  onConfirm: () => void | Promise<void>;
}) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted || !open) {
    return null;
  }

  return createPortal(
    <div className="modal-overlay" onClick={onCancel} role="presentation">
      <div
        aria-modal="true"
        className="modal modal-compact"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
      >
        <div className="modal-header">
          <div>
            <div className="eyebrow">Confirm Action</div>
            <h2>{title}</h2>
            <p className="muted">{description}</p>
          </div>
          <button aria-label="Close modal" className="modal-close" onClick={onCancel} type="button">
            Close
          </button>
        </div>
        <div className="actions">
          <button className="button secondary" onClick={onCancel} type="button">
            Cancel
          </button>
          <button className={confirmClassName} onClick={() => void onConfirm()} type="button">
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
