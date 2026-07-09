import { BoardResponse, ConfigSetting, Engineer, Organization, PRD, Project, Tag, Task, TokenUsage, TokenSummary, Workflow, WorkflowStage } from "@/lib/types";

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

  getWorkflows: () => request<Workflow[]>("/workflows"),
  getWorkflow: (workflowId: number) => request<Workflow>(`/workflows/${workflowId}`),
  createWorkflow: (payload: Partial<Workflow>) =>
    request<Workflow>("/workflows", { method: "POST", body: JSON.stringify(payload) }),
  updateWorkflow: (workflowId: number, payload: Partial<Workflow>) =>
    request<Workflow>(`/workflows/${workflowId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteWorkflow: (workflowId: number) =>
    requestWithoutBody<{ deleted: boolean }>(`/workflows/${workflowId}`, { method: "DELETE" }),
  createWorkflowStage: (workflowId: number, payload: Partial<WorkflowStage>) =>
    request<WorkflowStage>(`/workflows/${workflowId}/stages`, { method: "POST", body: JSON.stringify(payload) }),
  updateWorkflowStage: (workflowId: number, stageId: number, payload: Partial<WorkflowStage>) =>
    request<WorkflowStage>(`/workflows/${workflowId}/stages/${stageId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteWorkflowStage: (workflowId: number, stageId: number) =>
    requestWithoutBody<{ deleted: boolean }>(`/workflows/${workflowId}/stages/${stageId}`, { method: "DELETE" }),
  reorderWorkflowStages: (workflowId: number, stages: { id: number; stage_order: number }[]) =>
    request<WorkflowStage[]>(`/workflows/${workflowId}/stages/reorder`, { method: "PATCH", body: JSON.stringify({ stages }) }),

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
    requestWithoutBody<{ deleted: boolean }>(`/tasks/${taskId}/comments/${commentId}`, { method: "DELETE" }),

  getOrganizations: () => request<Organization[]>("/organizations"),
  getOrganization: (orgId: number) => request<Organization>(`/organizations/${orgId}`),
  createOrganization: (payload: { name: string; slug: string }) =>
    request<Organization>("/organizations", { method: "POST", body: JSON.stringify(payload) }),
  deleteOrganization: (orgId: number) =>
    requestWithoutBody<{ deleted: boolean }>(`/organizations/${orgId}`, { method: "DELETE" }),
  addOrgMember: (orgId: number, payload: { user_email: string; role: string }) =>
    request(`/organizations/${orgId}/members`, { method: "POST", body: JSON.stringify(payload) }),
  removeOrgMember: (orgId: number, memberId: number) =>
    requestWithoutBody<{ deleted: boolean }>(`/organizations/${orgId}/members/${memberId}`, { method: "DELETE" }),

  getPRDs: (orgId?: number) => request<PRD[]>(`/prds${orgId ? `?org_id=${orgId}` : ""}`),
  getPRD: (prdId: number) => request<PRD>(`/prds/${prdId}`),
  createPRD: (payload: { organization_id: number; title: string; summary?: string }) =>
    request<PRD>("/prds", { method: "POST", body: JSON.stringify(payload) }),
  updatePRD: (prdId: number, payload: Partial<PRD>) =>
    request<PRD>(`/prds/${prdId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deletePRD: (prdId: number) => requestWithoutBody<{ deleted: boolean }>(`/prds/${prdId}`, { method: "DELETE" }),
  addPRDComment: (prdId: number, body: string) =>
    request(`/prds/${prdId}/comments`, { method: "POST", body: JSON.stringify({ body }) }),
  prdChat: (prdId: number, message: string) =>
    request(`/prds/${prdId}/chat`, { method: "POST", body: JSON.stringify({ message }) }),
  convertPRD: (prdId: number, payload: { project_ids: number[]; task_titles: string[] }) =>
    request<PRD>(`/prds/${prdId}/convert`, { method: "POST", body: JSON.stringify(payload) }),
  updatePRDTags: (prdId: number, tagIds: number[]) =>
    request<Tag[]>(`/prds/${prdId}/tags`, { method: "PATCH", body: JSON.stringify({ tag_ids: tagIds }) }),

  recordTokenUsage: (payload: Partial<TokenUsage>) =>
    request<TokenUsage>("/token-usage", { method: "POST", body: JSON.stringify(payload) }),
  getProjectTokenSummary: (projectId: number) => request<TokenSummary>(`/projects/${projectId}/token-summary`),
  getTaskTokenSummary: (taskId: number) => request<TokenSummary>(`/tasks/${taskId}/token-summary`),

  getOrgTags: (orgId: number) => request<Tag[]>(`/organizations/${orgId}/tags`),
  createTag: (payload: { organization_id: number; name: string; color?: string }) =>
    request<Tag>("/tags", { method: "POST", body: JSON.stringify(payload) }),
  deleteTag: (tagId: number) => requestWithoutBody<{ deleted: boolean }>(`/tags/${tagId}`, { method: "DELETE" }),
  updateTaskTags: (taskId: number, tagIds: number[]) =>
    request<Tag[]>(`/tasks/${taskId}/tags`, { method: "PATCH", body: JSON.stringify({ tag_ids: tagIds }) }),
};
