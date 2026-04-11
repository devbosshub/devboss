# AI Testing Stage Instructions

## Goal
Verify that the task meets its acceptance criteria and is ready for human testing.

## What You Must Do
- Review the task requirements, acceptance criteria, and prior implementation context.
- Continue from the existing task branch prepared during the implementation stage. Pull and test that branch rather than starting from the default branch.
- Inspect the relevant code and test coverage.
- Run the strongest practical verification available in the current environment.
- Look for regressions, missing edge cases, or incomplete behavior.
- Base your conclusion on evidence, not optimism.

## What You Must Not Do
- Do not do broad new feature work unless a tiny fix is necessary to complete verification.
- Do not mark the task as tested if you were unable to validate the key acceptance criteria.
- Do not hide gaps in verification.
- Do not discard, reset, or ignore the implementation branch created for this task.

## How To Decide The Outcome
- Emit `testing_complete` only when the task appears ready for human testing based on the evidence you gathered.
- Emit `needs_human_input` if you need a missing expectation, credential, environment detail, or manual clarification to test correctly.
- Emit `blocked` if environment limitations or missing dependencies prevent meaningful verification.
- Emit `failed` for runtime/tooling failures.

## Summary Expectations
Your `summary` should:
- state what was tested
- mention the strongest evidence collected
- mention whether testing ran against the expected task branch
- mention the branch name explicitly so the task thread makes the implementation-to-testing handoff visible
- call out any residual risk or gaps the human tester should pay attention to
