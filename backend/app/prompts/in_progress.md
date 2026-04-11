# In Progress Stage Instructions

## Goal
Implement the task end to end inside the repository on a new git branch and push the branch after task is done. 

## What You Must Do
- Read the task bundle and inspect the codebase before making changes.
- Work on the task branch prepared for this task. The branch name should include the task ID and should be treated as the shared branch for later stages.
- Implement the task in the repository.
- Add or update tests where appropriate.
- Run the most relevant local verification you can in the current environment.
- Commit the changes to the branch created for the task and push the branch once the task is complete.
- Capture the outcome truthfully in the final structured response.

## What You Must Not Do
- Do not ask for human input unless a real blocker exists.
- Do not claim success if the implementation is incomplete or unverified.
- Do not silently skip important validation if it is available.
- Do not switch back to the default branch for implementation work.

## How To Decide The Outcome
- Emit `build_complete` only when the implementation is complete enough to move into AI testing and the task branch is ready to be pushed for the next stage to reuse.
- Emit `needs_human_input` if you are blocked by missing requirements, approvals, credentials, or decisions.
- Emit `blocked` if an external dependency, environment issue, or repository problem prevents completion.
- Emit `failed` for execution/tooling failures that prevent a reliable result.

## Summary Expectations
Your `summary` should:
- describe what was implemented
- mention what verification was performed
- mention the task branch used for the work
- make it clear that AI Testing should continue from that same branch after it is pushed
- call out any remaining caveats or notable assumptions
