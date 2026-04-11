# Ready To Deploy Stage Instructions

## Goal
Prepare the task branch for final handoff by making sure it is up to date with the default branch, resolving any merge issues, and leaving it ready for a pull request to be created against the default branch.

## What You Must Do
- Review the task context, current repo state, and any deployment-specific configuration in the project context.
- Use the existing task branch context when validating deployment readiness, rather than assuming the default branch contains the latest task work.
- Sync the task branch with the latest default branch state and resolve merge or rebase conflicts if they can be handled safely.
- Make any final branch-level fixes needed to leave the implementation ready for review.
- Ensure the task branch is pushed and suitable for a pull request against the default branch.
- Report clearly on pull-request readiness, conflict resolution, and any blockers.

## What You Must Not Do
- Do not emit success if the task branch still has unresolved conflicts with the default branch.
- Do not skip mention of release or environment risks.
- Do not treat missing GitHub access, missing branch push, or merge conflicts as success.

## How To Decide The Outcome
- Emit `deployment_complete` only if the task branch is pushed, conflicts are resolved, and the task is ready for a pull request against the default branch.
- Emit `needs_human_input` if you need approval, credentials, repository decisions, or release confirmation.
- Emit `blocked` if pull-request preparation cannot proceed because of external environment or infrastructure issues.
- Emit `failed` for runtime/tooling failures.

## Summary Expectations
Your `summary` should:
- explain the pull-request readiness result
- mention the task branch and whether it was brought up to date with the default branch
- mention any conflict resolution or remaining review risk
- call out any follow-up required from a human
