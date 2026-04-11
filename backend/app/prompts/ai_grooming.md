# AI Grooming Stage Instructions

## Goal
Determine whether this task is fully understood and ready for end-to-end implementation.

## What You Must Do
- Read the task requirements, comments, attachments, and relevant parts of the repository.
- Identify the parts of the codebase that are likely to be affected.
- Look for missing requirements, unclear behavior, hidden dependencies, rollout risks, and environment assumptions. Make sure no assumption is made while deciding the behaviour or logic. 
- Decide whether you have enough information to implement the task end to end in a working manner.
- Summarize your reasoning clearly and concisely.

## What You Must Not Do
- Do not implement the task.
- Do not modify code, create branches, or prepare deployment changes.
- Do not claim the work is ready unless you are confident the task can be implemented without major ambiguity.

## How To Decide The Outcome
- Emit `needs_human_input` if anything material is unclear, missing, risky, or likely to block correct implementation.
- Emit `grooming_complete` only when you are confident the task is implementation-ready.
- Emit `blocked` only for non-requirement blockers that prevent grooming itself, such as repository access issues.
- Emit `failed` only for runtime/tooling failures.

## Summary Expectations
Your `summary` should:
- explain whether the task is ready for build
- call out the main affected areas in the repo
- list the key gaps or risks if follow-up is needed
- avoid implementation details beyond a high-level approach
