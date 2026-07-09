export type TaskStatus =
  | "draft"
  | "ai_grooming"
  | "ready_for_build"
  | "in_progress"
  | "ai_testing"
  | "human_testing"
  | "ready_to_deploy"
  | "deployed"
  | "archived";

export type StatusGroup =
  | "todo"
  | "in_progress"
  | "waiting_approval"
  | "blocked"
  | "done";

export type EngineerTemplate =
  | "backend_engineer"
  | "frontend_engineer"
  | "qa_test_engineer"
  | "devops_deployment_engineer";

export type ModelProvider =
  | "deepseek"
  | "openai"
  | "anthropic"
  | "openrouter"
  | "google"
  | "groq";

export type EngineerRuntimeStatus =
  | "stopped"
  | "starting"
  | "healthy"
  | "heartbeat_missing"
  | "launch_failed";

export type RuntimeConfig = Record<string, unknown>;

export type CommentAuthorType = "human" | "agent" | "system";

export type WorkflowStage = {
  id: number;
  workflow_id: number;
  name: string;
  stage_order: number;
  assigned_engineer_id: number | null;
  requires_human_approval: boolean;
  is_ai_executable: boolean;
  stage_instructions: string | null;
  max_rework_attempts: number;
  rework_target_stage_id: number | null;
  created_at: string;
  updated_at: string;
};

export type Workflow = {
  id: number;
  name: string;
  description: string | null;
  stages: WorkflowStage[];
  created_at: string;
  updated_at: string;
};

export type Project = {
  id: number;
  name: string;
  repo_url: string;
  default_branch: string;
  deploy_config: Record<string, unknown>;
  deployment_instructions: string;
  engineer_pool: string[];
  workflow_id: number | null;
  organization_id: number | null;
  created_at: string;
  updated_at: string;
};

export type Engineer = {
  id: number;
  name: string;
  template: EngineerTemplate;
  skill_markdown: string;
  model_provider: ModelProvider;
  model_name: string;
  docker_image: string;
  poll_interval_seconds: number;
  allowed_projects: string[];
  is_active: boolean;
  runtime_status: EngineerRuntimeStatus;
  runtime_container_name: string | null;
  runtime_container_id: string | null;
  runtime_status_message: string | null;
  runtime_started_at: string | null;
  runtime_last_heartbeat_at: string | null;
  runtime_count: number;
  healthy_runtime_count: number;
  busy_runtime_count: number;
  runtimes: EngineerRuntime[];
  created_at: string;
  updated_at: string;
};

export type EngineerRuntime = {
  id: number;
  engineer_id: number;
  runtime_status: EngineerRuntimeStatus;
  container_name: string | null;
  container_id: string | null;
  status_message: string | null;
  started_at: string | null;
  last_heartbeat_at: string | null;
  current_task_run_id: number | null;
  created_at: string;
  updated_at: string;
};

export type TaskComment = {
  id: number;
  author_type: CommentAuthorType;
  author_name: string;
  body: string;
  action_required: boolean;
  created_at: string;
};

export type TaskRun = {
  id: number;
  task_id: number;
  engineer_id: number;
  claimed_by_runtime_id: number | null;
  phase: string;
  workflow_stage_id: number | null;
  status: string;
  outcome_type: string | null;
  summary: string | null;
  transcript_path: string | null;
  attempt_number: number;
  claimed_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  heartbeat_at: string | null;
  created_at: string;
  updated_at: string;
};

export type Artifact = {
  id: number;
  task_id: number;
  task_run_id: number | null;
  kind: string;
  name: string;
  file_path: string;
  content_type: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export type Task = {
  id: number;
  project_id: number;
  assigned_engineer_id: number | null;
  workflow_stage_id: number | null;
  title: string;
  requirement_markdown: string;
  acceptance_criteria: string;
  implementation_steps: string;
  status: TaskStatus;
  status_group: StatusGroup;
  branch_name: string | null;
  pr_url: string | null;
  deploy_url: string | null;
  blocked_reason: string | null;
  release_queue_entered_at?: string | null;
  rework_count: number;
  created_at: string;
  updated_at: string;
  comments: TaskComment[];
  task_runs: TaskRun[];
  artifacts: Artifact[];
};

export type BoardLane = {
  status: TaskStatus;
  tasks: Task[];
};

export type BoardResponse = {
  lanes: BoardLane[];
};

export type ConfigSetting = {
  id: number;
  key: string;
  value: string;
  is_secret: boolean;
  description: string | null;
  created_at: string;
  updated_at: string;
};

export type User = {
  id: number;
  email: string;
  name: string | null;
  external_id: number | null;
  created_at: string;
  updated_at: string;
};

export type OrganizationMember = {
  id: number;
  organization_id: number;
  user_id: number;
  role: "admin" | "member";
  user: User | null;
  created_at: string;
};

export type Organization = {
  id: number;
  name: string;
  slug: string;
  members: OrganizationMember[];
  tags: Tag[];
  created_at: string;
  updated_at: string;
};

export type PRDStatus = "draft" | "in_review" | "approved" | "converted" | "archived";

export type PRDComment = {
  id: number;
  prd_id: number;
  author_type: CommentAuthorType;
  author_name: string;
  body: string;
  created_at: string;
};

export type PRD = {
  id: number;
  organization_id: number;
  title: string;
  summary: string | null;
  body_markdown: string | null;
  status: PRDStatus;
  created_by_user_id: number | null;
  comments: PRDComment[];
  tags: Tag[];
  created_at: string;
  updated_at: string;
};

export type TokenUsage = {
  id: number;
  user_id: number | null;
  task_id: number | null;
  task_run_id: number | null;
  prd_id: number | null;
  model: string;
  tokens_in: number;
  tokens_out: number;
  cost_usd: number;
  created_at: string;
};

export type TokenSummary = {
  total_tokens_in: number;
  total_tokens_out: number;
  total_cost_usd: number;
};

export type Tag = {
  id: number;
  organization_id: number;
  name: string;
  color: string | null;
  created_at: string;
};
