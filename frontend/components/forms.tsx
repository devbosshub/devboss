"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import { ConfigSetting, Engineer, EngineerTemplate, Project, Task, TaskStatus } from "@/lib/types";

export function ProjectForm({
  project,
  onCreated,
  onUpdated
}: {
  project?: Project;
  onCreated?: () => void;
  onUpdated?: () => void;
}) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [name, setName] = useState(project?.name ?? "");
  const [repoUrl, setRepoUrl] = useState(project?.repo_url ?? "");
  const [defaultBranch, setDefaultBranch] = useState(project?.default_branch ?? "main");
  const [deployConfigText, setDeployConfigText] = useState(
    JSON.stringify(project?.deploy_config ?? {}, null, 2)
  );
  const [deploymentInstructions, setDeploymentInstructions] = useState(project?.deployment_instructions ?? "");
  const [deployConfigError, setDeployConfigError] = useState("");

  return (
    <form
      className="stack"
      onSubmit={(event) => {
        event.preventDefault();
        startTransition(async () => {
          let parsedDeployConfig: Record<string, unknown> = {};
          const trimmedDeployConfig = deployConfigText.trim();
          if (trimmedDeployConfig) {
            try {
              const candidate = JSON.parse(trimmedDeployConfig);
              if (candidate === null || Array.isArray(candidate) || typeof candidate !== "object") {
                setDeployConfigError("Deployment config must be a JSON object.");
                return;
              }
              parsedDeployConfig = candidate as Record<string, unknown>;
            } catch {
              setDeployConfigError("Deployment config must be valid JSON.");
              return;
            }
          }

          setDeployConfigError("");
          if (project) {
            await api.updateProject(project.id, {
              name,
              repo_url: repoUrl,
              default_branch: defaultBranch,
              deploy_config: parsedDeployConfig,
              deployment_instructions: deploymentInstructions,
            } satisfies Partial<Project>);
            onUpdated?.();
          } else {
            await api.createProject({
              name,
              repo_url: repoUrl,
              default_branch: defaultBranch,
              deploy_config: parsedDeployConfig,
              deployment_instructions: deploymentInstructions,
              engineer_pool: []
            } satisfies Partial<Project>);
            onCreated?.();
          }
          setName("");
          setRepoUrl("");
          setDefaultBranch("main");
          setDeployConfigText("{}");
          setDeploymentInstructions("");
          router.refresh();
        });
      }}
    >
      <label className="field">
        <span>Project name</span>
        <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Payments Revamp" required />
      </label>
      <label className="field">
        <span>GitHub repo URL</span>
        <input
          value={repoUrl}
          onChange={(event) => setRepoUrl(event.target.value)}
          placeholder="https://github.com/acme/payments"
          required
        />
      </label>
      <label className="field">
        <span>Default branch</span>
        <input value={defaultBranch} onChange={(event) => setDefaultBranch(event.target.value)} required />
      </label>
      <div className="task-card">
        <h3>Deployment Config</h3>
        <p className="muted">Store project-level deployment details as JSON. This will be passed into the deployment stage.</p>
        <label className="field">
          <span>Deployment config JSON</span>
          <textarea
            className="editor-textarea"
            value={deployConfigText}
            onChange={(event) => {
              setDeployConfigText(event.target.value);
              if (deployConfigError) {
                setDeployConfigError("");
              }
            }}
            placeholder={`{\n  "type": "frontend_static_s3",\n  "build_command": "npm run build",\n  "output_dir": "out",\n  "s3_bucket": "my-site-bucket",\n  "cloudfront_distribution_id": "E1234567890",\n  "aws_region": "ap-south-1"\n}`}
          />
        </label>
        {deployConfigError ? <div className="field-error">{deployConfigError}</div> : null}
        <label className="field">
          <span>Deployment instructions</span>
          <textarea
            className="editor-textarea"
            value={deploymentInstructions}
            onChange={(event) => setDeploymentInstructions(event.target.value)}
            placeholder={"Build with npm run build, upload the out directory to the configured S3 bucket, then invalidate the configured CloudFront distribution."}
          />
        </label>
      </div>
      <div className="actions">
        <button className="button" disabled={isPending} type="submit">
          {isPending ? (project ? "Saving..." : "Creating...") : project ? "Save changes" : "Create project"}
        </button>
      </div>
    </form>
  );
}

export function CreateProjectForm() {
  return <ProjectForm />;
}

const templateDescriptions: Record<EngineerTemplate, string> = {
  backend_engineer: "# Backend Engineer\n\nFocus on FastAPI, services, data models, and tests.",
  frontend_engineer: "# Frontend Engineer\n\nFocus on Next.js, React UI, state, and visual polish.",
  qa_test_engineer: "# QA/Test Engineer\n\nFocus on acceptance criteria, testing, and evidence capture.",
  devops_deployment_engineer: "# DevOps/Deployment Engineer\n\nFocus on CI, containers, deployment, and health checks."
};

export function EngineerForm({
  engineer,
  onSuccessPath
}: {
  engineer?: Engineer;
  onSuccessPath?: string;
}) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [name, setName] = useState(engineer?.name ?? "");
  const [template, setTemplate] = useState<EngineerTemplate>(engineer?.template ?? "backend_engineer");
  const [skillMarkdown, setSkillMarkdown] = useState(engineer?.skill_markdown ?? templateDescriptions[engineer?.template ?? "backend_engineer"]);
  const [modelName, setModelName] = useState(engineer?.model_name ?? "gpt-5.4");
  const [dockerImage, setDockerImage] = useState(engineer?.docker_image ?? "devboss-engineer:latest");
  const [pollIntervalSeconds, setPollIntervalSeconds] = useState(String(engineer?.poll_interval_seconds ?? 30));
  const [isActive, setIsActive] = useState(engineer?.is_active ?? true);

  return (
    <form
      className="stack"
      onSubmit={(event) => {
        event.preventDefault();
        startTransition(async () => {
          const payload = {
            name,
            template,
            skill_markdown: skillMarkdown,
            model_name: modelName,
            docker_image: dockerImage,
            poll_interval_seconds: Number(pollIntervalSeconds),
            enabled_tools: engineer?.enabled_tools ?? ["git", "shell", "tests"],
            allowed_projects: engineer?.allowed_projects ?? [],
            runtime_config: engineer?.runtime_config ?? {
              max_active_tasks: 1
            },
            is_active: isActive
          } satisfies Partial<Engineer>;

          if (engineer) {
            await api.updateEngineer(engineer.id, payload);
          } else {
            await api.createEngineer(payload);
          }

          if (onSuccessPath) {
            router.push(onSuccessPath);
            return;
          }

          setName("");
          router.refresh();
        });
      }}
    >
      <label className="field">
        <span>Engineer name</span>
        <input value={name} onChange={(event) => setName(event.target.value)} placeholder="API Captain" required />
      </label>
      <label className="field">
        <span>Template</span>
        <select
          value={template}
          onChange={(event) => {
            const nextTemplate = event.target.value as EngineerTemplate;
            setTemplate(nextTemplate);
            if (!engineer) {
              setSkillMarkdown(templateDescriptions[nextTemplate]);
            }
          }}
        >
          <option value="backend_engineer">Backend Engineer</option>
          <option value="frontend_engineer">Frontend Engineer</option>
          <option value="qa_test_engineer">QA/Test Engineer</option>
          <option value="devops_deployment_engineer">DevOps/Deployment Engineer</option>
        </select>
      </label>
      <label className="field">
        <span>Model</span>
        <input value={modelName} onChange={(event) => setModelName(event.target.value)} />
      </label>
      <label className="field">
        <span>Docker image</span>
        <input value={dockerImage} onChange={(event) => setDockerImage(event.target.value)} />
      </label>
      <label className="field">
        <span>Poll interval (seconds)</span>
        <input value={pollIntervalSeconds} onChange={(event) => setPollIntervalSeconds(event.target.value)} />
      </label>
      <label className="field">
        <span>Status</span>
        <select value={isActive ? "active" : "inactive"} onChange={(event) => setIsActive(event.target.value === "active")}>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </label>
      <label className="field">
        <span>Skill markdown</span>
        <textarea className="editor-textarea" value={skillMarkdown} onChange={(event) => setSkillMarkdown(event.target.value)} />
      </label>
      <div className="actions">
        <button className="button" disabled={isPending} type="submit">
          {isPending ? (engineer ? "Saving..." : "Creating...") : engineer ? "Save engineer" : "Create engineer"}
        </button>
      </div>
    </form>
  );
}

export function CreateEngineerForm() {
  return <EngineerForm />;
}

export function CreateTaskForm({
  projects,
  engineers,
  onSuccessPath,
  initialProjectId,
  onCreated
}: {
  projects: Project[];
  engineers: Engineer[];
  onSuccessPath?: string;
  initialProjectId?: number;
  onCreated?: (task: Task) => void | Promise<void>;
}) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [projectId, setProjectId] = useState<number>(initialProjectId ?? projects[0]?.id ?? 0);
  const [engineerId, setEngineerId] = useState<number | "">(engineers[0]?.id ?? "");
  const [title, setTitle] = useState("");
  const [requirements, setRequirements] = useState("");
  const [acceptanceCriteria, setAcceptanceCriteria] = useState("The above requirements should be completed");
  const [steps, setSteps] = useState("Change code to implement the given requirements");
  const [status, setStatus] = useState<TaskStatus>("draft");

  return (
    <form
      className="stack"
      onSubmit={(event) => {
        event.preventDefault();
        startTransition(async () => {
          const createdTask = await api.createTask({
            project_id: projectId,
            assigned_engineer_id: engineerId === "" ? null : engineerId,
            title,
            requirement_markdown: requirements,
            acceptance_criteria: acceptanceCriteria,
            implementation_steps: steps,
            status
          });
          setTitle("");
          setRequirements("");
          setAcceptanceCriteria("The above requirements should be completed");
          setSteps("Change code to implement the given requirements");
          await onCreated?.(createdTask);
          if (onSuccessPath) {
            router.push(onSuccessPath);
            return;
          }
          router.refresh();
        });
      }}
    >
      <label className="field">
        <span>Project</span>
        <select value={projectId} onChange={(event) => setProjectId(Number(event.target.value))}>
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        <span>Assigned engineer</span>
        <select value={engineerId} onChange={(event) => setEngineerId(event.target.value ? Number(event.target.value) : "")}>
          <option value="">Unassigned</option>
          {engineers.map((engineer) => (
            <option key={engineer.id} value={engineer.id}>
              {engineer.name}
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        <span>Title</span>
        <input value={title} onChange={(event) => setTitle(event.target.value)} required />
      </label>
      <label className="field">
        <span>Requirements</span>
        <textarea value={requirements} onChange={(event) => setRequirements(event.target.value)} required />
      </label>
      <label className="field">
        <span>Acceptance criteria</span>
        <textarea value={acceptanceCriteria} onChange={(event) => setAcceptanceCriteria(event.target.value)} required />
      </label>
      <label className="field">
        <span>Implementation steps</span>
        <textarea value={steps} onChange={(event) => setSteps(event.target.value)} />
      </label>
      <label className="field">
        <span>Initial status</span>
        <select value={status} onChange={(event) => setStatus(event.target.value as TaskStatus)}>
          <option value="draft">Draft</option>
          <option value="ai_grooming">AI Grooming</option>
        </select>
      </label>
      <div className="actions">
        <button className="button" disabled={isPending || projects.length === 0} type="submit">
          {isPending ? "Creating..." : "Create task"}
        </button>
      </div>
    </form>
  );
}

export function TaskEditorForm({
  task,
  engineers,
  onUpdated
}: {
  task: Task;
  engineers: Engineer[];
  onUpdated?: (task: Task) => void | Promise<void>;
}) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [title, setTitle] = useState(task.title);
  const [engineerId, setEngineerId] = useState<number | "">(task.assigned_engineer_id ?? "");
  const [requirements, setRequirements] = useState(task.requirement_markdown);
  const [acceptanceCriteria, setAcceptanceCriteria] = useState(task.acceptance_criteria);
  const [steps, setSteps] = useState(task.implementation_steps ?? "");
  const [status, setStatus] = useState<TaskStatus>(task.status);

  return (
    <form
      className="stack"
      onSubmit={(event) => {
        event.preventDefault();
        startTransition(async () => {
          const updatedTask = await api.updateTask(task.id, {
            assigned_engineer_id: engineerId === "" ? null : engineerId,
            title,
            requirement_markdown: requirements,
            acceptance_criteria: acceptanceCriteria,
            implementation_steps: steps,
            status
          });
          await onUpdated?.(updatedTask);
          router.refresh();
        });
      }}
    >
      <label className="field">
        <span>Title</span>
        <input onChange={(event) => setTitle(event.target.value)} required value={title} />
      </label>
      <label className="field">
        <span>Assigned engineer</span>
        <select value={engineerId} onChange={(event) => setEngineerId(event.target.value ? Number(event.target.value) : "")}>
          <option value="">Unassigned</option>
          {engineers.map((engineer) => (
            <option key={engineer.id} value={engineer.id}>
              {engineer.name}
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        <span>Requirements</span>
        <textarea onChange={(event) => setRequirements(event.target.value)} required value={requirements} />
      </label>
      <label className="field">
        <span>Acceptance criteria</span>
        <textarea onChange={(event) => setAcceptanceCriteria(event.target.value)} required value={acceptanceCriteria} />
      </label>
      <label className="field">
        <span>Implementation steps</span>
        <textarea onChange={(event) => setSteps(event.target.value)} value={steps} />
      </label>
      <label className="field">
        <span>Status</span>
        <select value={status} onChange={(event) => setStatus(event.target.value as TaskStatus)}>
          <option value="draft">Draft</option>
          <option value="ai_grooming">AI Grooming</option>
        </select>
      </label>
      <div className="actions">
        <button className="button" disabled={isPending} type="submit">
          {isPending ? "Saving..." : "Save task changes"}
        </button>
      </div>
    </form>
  );
}

export function AddCommentForm({ taskId, onAdded }: { taskId: number; onAdded?: () => void | Promise<void> }) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [body, setBody] = useState("");

  return (
    <form
      className="stack"
      onSubmit={(event) => {
        event.preventDefault();
        startTransition(async () => {
          await api.addComment(taskId, {
            author_type: "human",
            author_name: "Human Reviewer",
            body,
            action_required: false
          });
          setBody("");
          await onAdded?.();
          router.refresh();
        });
      }}
    >
      <label className="field">
        <span>Add a comment</span>
        <span className="field-help">Markdown is supported for formatting, lists, links, and code snippets.</span>
        <textarea value={body} onChange={(event) => setBody(event.target.value)} required />
      </label>
      <div className="actions">
        <button className="button" disabled={isPending} type="submit">
          {isPending ? "Posting..." : "Post reply"}
        </button>
      </div>
    </form>
  );
}

export function SettingForm({
  setting,
  onCreated,
  onUpdated
}: {
  setting?: ConfigSetting;
  onCreated?: () => void;
  onUpdated?: () => void;
}) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [key, setKey] = useState(setting?.key ?? "");
  const [value, setValue] = useState(setting?.value ?? "");
  const [description, setDescription] = useState(setting?.description ?? "");
  const [isSecret, setIsSecret] = useState(setting?.is_secret ?? true);

  return (
    <form
      className="stack"
      onSubmit={(event) => {
        event.preventDefault();
        startTransition(async () => {
          if (setting) {
            await api.updateSetting(setting.id, {
              value,
              description,
              is_secret: isSecret
            } satisfies Partial<ConfigSetting>);
            onUpdated?.();
          } else {
            await api.createSetting({
              key,
              value,
              description,
              is_secret: isSecret
            } satisfies Partial<ConfigSetting>);
            setKey("");
            setValue("");
            setDescription("");
            setIsSecret(true);
            onCreated?.();
          }
          router.refresh();
        });
      }}
    >
      <label className="field">
        <span>Config key</span>
        <input
          disabled={Boolean(setting)}
          value={key}
          onChange={(event) => setKey(event.target.value)}
          placeholder="github_token"
          required
        />
      </label>
      <label className="field">
        <span>Value</span>
        <textarea value={value} onChange={(event) => setValue(event.target.value)} required />
      </label>
      <label className="field">
        <span>Description</span>
        <input
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          placeholder="GitHub token for repo automation"
        />
      </label>
      <label className="field">
        <span>Secret type</span>
        <select value={isSecret ? "secret" : "plain"} onChange={(event) => setIsSecret(event.target.value === "secret")}>
          <option value="secret">Secret</option>
          <option value="plain">Plain text</option>
        </select>
      </label>
      <div className="actions">
        <button className="button" disabled={isPending} type="submit">
          {isPending ? (setting ? "Saving..." : "Creating...") : setting ? "Save config" : "Add config"}
        </button>
      </div>
    </form>
  );
}

export function CreateSettingForm() {
  return <SettingForm />;
}
