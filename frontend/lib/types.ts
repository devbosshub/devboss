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

export type EngineerTemplate =
  | "backend_engineer"
  | "frontend_engineer"
  | "qa_test_engineer"
  | "devops_deployment_engineer";

export type EngineerRuntimeStatus =
  | "stopped"
  | "starting"
  | "healthy"
  | "heartbeat_missing"
  | "launch_failed";

export type CommentAuthorType = "human" | "agent" | "system";

export type Project = {
  id: number;
  name: string;
  repo_url: string;
  default_branch: string;
  deploy_config: Record<string, unknown>;
  deployment_instructions: string;
  engineer_pool: string[];
  created_at: string;
  updated_at: string;
};

export type Engineer = {
  id: number;
  name: string;
  template: EngineerTemplate;
  skill_markdown: string;
  model_name: string;
  docker_image: string;
  poll_interval_seconds: number;
  enabled_tools: string[];
  allowed_projects: string[];
  runtime_config: Record<string, unknown>;
  is_active: boolean;
  runtime_status: EngineerRuntimeStatus;
  runtime_container_name: string | null;
  runtime_container_id: string | null;
  runtime_status_message: string | null;
  runtime_started_at: string | null;
  runtime_last_heartbeat_at: string | null;
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
  phase: string;
  status: string;
  outcome_type: string | null;
  summary: string | null;
  transcript_path: string | null;
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
  title: string;
  requirement_markdown: string;
  acceptance_criteria: string;
  implementation_steps: string;
  status: TaskStatus;
  branch_name: string | null;
  pr_url: string | null;
  deploy_url: string | null;
  blocked_reason: string | null;
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
