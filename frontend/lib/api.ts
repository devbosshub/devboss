import { BoardResponse, ConfigSetting, Engineer, Project, Task } from "@/lib/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });

  if (!response.ok) {
    const errorMessage = await readErrorMessage(response, path);
    throw new Error(errorMessage);
  }

  return response.json() as Promise<T>;
}

async function requestWithoutBody<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    cache: "no-store"
  });

  if (!response.ok) {
    const errorMessage = await readErrorMessage(response, path);
    throw new Error(errorMessage);
  }

  return response.json() as Promise<T>;
}

async function readErrorMessage(response: Response, path: string): Promise<string> {
  const fallback = `Request failed for ${path}: ${response.status}`;

  try {
    const payload = await response.json();
    if (typeof payload?.detail === "string" && payload.detail.length > 0) {
      return payload.detail;
    }
  } catch {
    try {
      const text = await response.text();
      if (text.trim()) {
        return text.trim();
      }
    } catch {
      return fallback;
    }
  }

  return fallback;
}

export const api = {
  getBoard: () => request<BoardResponse>("/board"),
  getAttentionTasks: () => request<Task[]>("/overview/attention-tasks"),
  getProjectBoard: (projectId: number) => request<BoardResponse>(`/projects/${projectId}/board`),
  getProjects: () => request<Project[]>("/projects"),
  getProject: (projectId: number) => request<Project>(`/projects/${projectId}`),
  createProject: (payload: Partial<Project>) =>
    request<Project>("/projects", { method: "POST", body: JSON.stringify(payload) }),
  updateProject: (projectId: number, payload: Partial<Project>) =>
    request<Project>(`/projects/${projectId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteProject: (projectId: number) =>
    requestWithoutBody<{ deleted: boolean }>(`/projects/${projectId}`, { method: "DELETE" }),
  getSettings: () => request<ConfigSetting[]>("/settings"),
  createSetting: (payload: Partial<ConfigSetting>) =>
    request<ConfigSetting>("/settings", { method: "POST", body: JSON.stringify(payload) }),
  updateSetting: (settingId: number, payload: Partial<ConfigSetting>) =>
    request<ConfigSetting>(`/settings/${settingId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteSetting: (settingId: number) =>
    requestWithoutBody<{ deleted: boolean }>(`/settings/${settingId}`, { method: "DELETE" }),
  getEngineers: () => request<Engineer[]>("/engineers"),
  getEngineer: (engineerId: number) => request<Engineer>(`/engineers/${engineerId}`),
  createEngineer: (payload: Partial<Engineer>) =>
    request<Engineer>("/engineers", { method: "POST", body: JSON.stringify(payload) }),
  updateEngineer: (engineerId: number, payload: Partial<Engineer>) =>
    request<Engineer>(`/engineers/${engineerId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  launchEngineer: (engineerId: number) => request<Engineer>(`/engineers/${engineerId}/launch`, { method: "POST" }),
  stopEngineer: (engineerId: number) => request<Engineer>(`/engineers/${engineerId}/stop`, { method: "POST" }),
  stopEngineerRuntime: (runtimeId: number) =>
    request(`/engineer-runtimes/${runtimeId}/stop`, { method: "POST" }),
  restartEngineerRuntime: (runtimeId: number) =>
    request(`/engineer-runtimes/${runtimeId}/restart`, { method: "POST" }),
  deleteEngineer: (engineerId: number) =>
    requestWithoutBody<{ deleted: boolean }>(`/engineers/${engineerId}`, { method: "DELETE" }),
  createTask: (payload: Partial<Task>) => request<Task>("/tasks", { method: "POST", body: JSON.stringify(payload) }),
  getTask: (taskId: number) => request<Task>(`/tasks/${taskId}`),
  updateTask: (taskId: number, payload: Partial<Task>) =>
    request<Task>(`/tasks/${taskId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  retryTask: (taskId: number) => requestWithoutBody<Task>(`/tasks/${taskId}/retry`, { method: "POST" }),
  deleteTask: (taskId: number) => requestWithoutBody<{ deleted: boolean }>(`/tasks/${taskId}`, { method: "DELETE" }),
  approveTaskRun: (taskRunId: number, payload: { summary?: string }) =>
    request(`/task-runs/${taskRunId}/approve`, { method: "POST", body: JSON.stringify(payload) }),
  addComment: (taskId: number, payload: { author_type: string; author_name: string; body: string; action_required?: boolean }) =>
    request(`/tasks/${taskId}/comments`, { method: "POST", body: JSON.stringify(payload) }),
  deleteComment: (taskId: number, commentId: number) =>
    requestWithoutBody<{ deleted: boolean }>(`/tasks/${taskId}/comments/${commentId}`, { method: "DELETE" })
};
