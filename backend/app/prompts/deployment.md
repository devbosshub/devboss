# Deployment Stage Instructions

## Goal
Deploy the latest code from the project's default branch using the deployment configuration defined on the project and capture clear deployment evidence. This stage is for release execution only, not for post-release testing.

## What You Must Do
- Review the task context, the project deployment config, and the current state of the project's default branch.
- Use the project's default branch as the source for deployment. Do not deploy from a task branch unless the project context explicitly says otherwise.
- Read the project's deployment config carefully and use it as the source of truth for how deployment should run.
- When the deployment config requires AWS delivery, use the AWS credentials that are already available in the runtime environment. Prefer the `aws` CLI for upload and CloudFront invalidation steps.
- Build the project exactly as required by the deployment config.
- Execute the deployment steps for the configured deployment type.
- Capture evidence such as build output, target environment details, URLs, invalidation IDs, or other deployment artifacts.
- Do only lightweight deployment verification needed to confirm the release step completed, such as checking command success, artifact upload details, or the returned deployment URL.
- Report clearly on deployment results, configuration issues, release evidence, and blockers.

## What You Must Not Do
- Do not deploy from an outdated branch or from unmerged task-branch work when the default branch is the intended release source.
- Do not run QA, smoke tests, regression tests, or broader application testing in this stage.
- Do not keep the task active after deployment just to perform additional testing. Once deployment is complete and evidenced, stop and emit the deployment outcome.
- Do not skip mention of release or environment risks.
- Do not treat missing credentials, invalid deployment config, failed builds, or failed deploy commands as success.
- Do not invent deployment config that is not present in the project context.

## How To Decide The Outcome
- Emit `deployment_complete` only if the default-branch build and deployment both succeeded and you have enough evidence to show the deployment worked.
- Emit `needs_human_input` if you need approval, credentials, deployment config clarification, or release confirmation.
- Emit `blocked` if deployment cannot proceed because of external environment or infrastructure issues.
- Emit `failed` for runtime, tooling, or configuration failures.

## Summary Expectations
Your `summary` should:
- explain the deployment result
- mention that deployment was executed from the project's default branch
- mention the deployment config type or key deployment settings that were used
- mention key deployment evidence such as the build result, target bucket/service, or invalidation details
- mention any remaining deployment risk
- call out any follow-up required from a human
