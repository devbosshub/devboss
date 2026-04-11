"use client";

import { useEffect, useState } from "react";

import { ConfirmModal } from "@/components/confirm-modal";
import { LayoutShell } from "@/components/layout-shell";
import { SettingModal } from "@/components/setting-modal";
import { api } from "@/lib/api";
import { ConfigSetting } from "@/lib/types";

function maskValue(value: string, isSecret: boolean) {
  if (!isSecret) {
    return value;
  }
  return "****";
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<ConfigSetting[]>([]);
  const [settingToDelete, setSettingToDelete] = useState<ConfigSetting | null>(null);

  const loadSettings = () => {
    api.getSettings().then(setSettings);
  };

  useEffect(() => {
    loadSettings();
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
            <SettingModal onSaved={loadSettings} triggerLabel="Add Global Config" />
          </div>
        </div>
      }
    >
      <ConfirmModal
        confirmClassName="button danger"
        confirmLabel="Delete global config"
        description={
          settingToDelete
            ? `This will permanently delete the global config ${settingToDelete.key}.`
            : ""
        }
        onCancel={() => setSettingToDelete(null)}
        onConfirm={async () => {
          if (!settingToDelete) {
            return;
          }
          const selectedSetting = settingToDelete;
          setSettingToDelete(null);
          await api.deleteSetting(selectedSetting.id);
          await loadSettings();
        }}
        open={settingToDelete !== null}
        title="Delete global config?"
      />
      <section className="panel">
        <div className="section-header">
          <div>
            <div className="eyebrow">Configuration</div>
            <h1>Global Configs</h1>
            <p className="muted">Manage workspace-wide integration keys and platform configuration.</p>
          </div>
        </div>

        {settings.length === 0 ? (
          <div className="empty">No global configs saved yet.</div>
        ) : (
          <div className="table-shell">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Key</th>
                  <th>Value</th>
                  <th>Type</th>
                  <th>Description</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {settings.map((setting) => (
                  <tr key={setting.id}>
                    <td>{setting.key}</td>
                    <td className="table-wrap">{maskValue(setting.value, setting.is_secret)}</td>
                    <td>{setting.is_secret ? "Secret" : "Plain text"}</td>
                    <td className="table-wrap">{setting.description ?? "No description provided."}</td>
                    <td className="action-cell">
                      <div className="table-actions">
                        <SettingModal onSaved={loadSettings} setting={setting} triggerClassName="button secondary" triggerLabel="Edit" />
                        <button className="button danger" onClick={() => setSettingToDelete(setting)} type="button">
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
