---
name: beyond-ralph-resume
prefix: "@br-resume"
category: orchestration
color: yellow
description: "Resume or re-validate a Beyond Ralph project"
argument-hint: ""
---

# /beyond-ralph-resume - Resume & Validate Project

Resume a Beyond Ralph project OR re-validate after spec changes. This command does NOT blindly trust the state file - it always validates against the current spec.

## STEP 1: SET STATE TO RUNNING IMMEDIATELY (NON-NEGOTIABLE)

**THIS IS THE VERY FIRST THING YOU DO. NO EXCEPTIONS.**

The user invoked `/beyond-ralph-resume` because they want work to continue. You MUST set the state to `"running"` RIGHT NOW, before doing anything else.

Read `.beyond_ralph_state`, then **IMMEDIATELY** write it back with these changes:
```json
{
  "state": "running",
  "hook_iteration": 0,
  "last_activity": "<current_timestamp>"
}
```

**DO NOT** leave state as "complete", "done", "finished", or any terminal state.
**DO NOT** skip this step because you think the project is already done.
**DO NOT** validate first then decide - the user explicitly asked to resume.

The stop hook checks `state` to decide whether to keep you running. If state is "complete", the hook allows exit and you will stop. Setting state to "running" is what keeps the autonomous loop alive.

## STEP 2: Check Quota
Run quota check - don't proceed if limited:
```
If session >= 85% OR weekly >= 85%:
  Report "Cannot resume - quota limited"
  Set state to "waiting_for_quota"
  Exit and wait for reset
```

## STEP 3: Read Current State
Load `.beyond_ralph_state` for baseline:
- Last recorded phase
- Recorded progress percentage
- Module statuses

## STEP 4: VALIDATE SPEC (CRITICAL - Never Skip)
**The spec is the source of truth, NOT the state file.**

Read `SPEC.md` (or configured spec path) and:
1. **Hash the spec** - compare to stored hash in state
2. **If spec changed**:
   - Report: "Spec has changed since last run"
   - Re-parse requirements
   - Identify NEW requirements not in current plan
   - Identify REMOVED requirements that were implemented
   - Identify MODIFIED requirements that need re-validation

## STEP 5: Validate Project Plan
Read `PROJECT_PLAN.md` and cross-reference:
1. **All spec requirements covered?** - Every MUST/REQUIRED in spec has a task
2. **All modules accounted for?** - Check `records/*/tasks.md` exist
3. **Checkboxes accurate?** - Verify claimed completions:
   - "Implemented" → code actually exists (FULLY - no stubs, no partial)
   - "Tested" → tests actually pass (mock, integration, AND live)
   - "Spec Compliant" → adversarial per-requirement check passed

**ZERO DEFERRAL POLICY**: If ANY requirement in the spec is marked "deferred to v2", "future work", "simplified version", or similar, that is a FAILURE. There is no v2. There are no time constraints. Everything in the spec MUST be fully implemented.

## STEP 6: Identify Gaps
Compare spec requirements vs actual state:
```
For each requirement in SPEC.md:
  - Is it in PROJECT_PLAN.md?
  - Is there a module for it?
  - Are all 7 checkboxes checked?
  - Does the implementation ACTUALLY match the requirement?

If ANY gaps found:
  - State is NOT "complete" regardless of what state file says
  - Report gaps and schedule work
```

## STEP 7: Update Prompt in State File
**Update `.beyond_ralph_state` with a continuation prompt describing the work to do:**
```json
{
  "state": "running",
  "phase": "<current_phase>",
  "last_activity": "<current_timestamp>",
  "hook_iteration": 0,
  "prompt": "You are the Beyond Ralph Orchestrator. You have N incomplete tasks.\n\nRead records/*/tasks.md to find incomplete tasks ([ ] checkboxes).\nUse the Task tool to spawn agents for implementation and testing.\nMark checkboxes as complete [x] when verified.\nContinue until ALL tasks have 7/7 checkboxes.\n\nPhase: PHASE | Spec: SPEC_PATH\n\nOutput AUTOMATION_COMPLETE only when all N remaining tasks are done."
}
```

The `prompt` field is CRITICAL. The stop hook re-feeds this SAME prompt back to you on each iteration (like ralph-wiggum). Without it, the stop hook falls back to a generic prompt.

**IMPORTANT:** Make sure `"state"` appears only ONCE in the JSON. Duplicate keys cause bugs.

## STEP 8: Resume Work
Based on validation:

**If spec unchanged AND all validations pass:**
- Resume from last phase
- Continue pending tasks

**If spec changed OR gaps found:**
- Report discrepancies
- Update PROJECT_PLAN.md with new/changed requirements
- Reset affected modules to appropriate phase
- Schedule validation tasks for changed requirements

**If truly nothing to do (all spec requirements met, all tests pass):**
- Ask the user what additional work they want done
- Do NOT just set state back to "complete" and stop

## Agent Spawning Guidelines (CRITICAL)

When spawning agents via the Task tool, ALWAYS:

1. **Set `max_turns`** - prevents context exhaustion:
   - Single function/file: max_turns=15
   - Small module (<500 lines): max_turns=25
   - Medium module (500-2000 lines): max_turns=30
   - Large module (2000+ lines): **BREAK INTO SUBTASKS**
   - Testing/validation: max_turns=20

2. **One agent per TASK, not per MODULE** - large modules MUST be broken into individual tasks

3. **Include CONTEXT BUDGET RULES and ZERO DEFERRAL POLICY in every prompt**:
```
ZERO DEFERRAL POLICY (MANDATORY):
- You MUST fully implement everything described in the spec for this task
- Do NOT defer anything to 'v2', 'future work', or 'next version'
- Do NOT implement a 'simplified version' - implement the SPECIFIED version
- There are NO time constraints - take as long as needed to implement fully

CONTEXT BUDGET RULES:
- Use Grep/Glob to find specific code - do NOT read entire files unless small (<200 lines)
- Read only the functions/sections you need to modify
- Do NOT explore the whole codebase - focus ONLY on your specific task
- If a file is large, read only the relevant section using offset/limit
- Write targeted changes, not full file rewrites
```

## Spec Change Detection

When spec changes are detected, categorize:

| Change Type | Action |
|-------------|--------|
| NEW requirement | Add to plan, schedule implementation |
| REMOVED requirement | Mark obsolete, clean up if needed |
| MODIFIED requirement | Re-validate implementation, may need rework |
| CLARIFIED (same intent) | Update docs, verify implementation still valid |

## Quota Check

If quota is still limited (>=85%), report:
```
Cannot resume - quota still limited
Session: X% | Weekly: Y%
Will auto-retry when quota resets.
```

## Example Output

```
[BEYOND-RALPH] Setting state to RUNNING (non-negotiable first step)
[BEYOND-RALPH] Resuming project br-5adbb6ea...

[VALIDATE] Checking spec hash...
[VALIDATE] SPEC.md has changed (hash mismatch)
[VALIDATE] Analyzing changes...

[CHANGES DETECTED]
  NEW: Project Installation section added
    - Requirement: Installer must bundle MCP servers

[GAP ANALYSIS]
  Missing: "DuckDuckGo MCP server" - Not implemented
  OK: All other requirements validated

[ACTION] Updating project plan...
[ACTION] Scheduling new tasks

[RESUME] Continuing from Phase 7 (Implementation)...
```

## Start Now

1. **SET STATE TO "running"** in `.beyond_ralph_state` (DO THIS FIRST - NON-NEGOTIABLE)
2. Check quota
3. Read state file (baseline only)
4. **Validate spec** (compare to state)
5. **Validate project plan** (compare to spec)
6. **Validate implementations** (spot-check completions)
7. Report gaps/changes
8. **Update prompt** in state file with remaining work description
9. Resume work - the stop hook will now keep you running until complete
