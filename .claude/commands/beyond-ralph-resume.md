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

## STEP 3: Read Current State and Ensure CLAUDE.md
Load `.beyond_ralph_state` for baseline:
- Last recorded phase
- Recorded progress percentage
- Module statuses

**Check CLAUDE.md**: If CLAUDE.md does not contain a "Beyond Ralph - Autonomous Development Rules" section, append it now with: Zero Deferral Policy, Failing Tests Are Failures, Do Not Trust Checkboxes, Task Checkboxes (7 per task), Agent Autonomy rules. This ensures all agents see the rules even on resume.

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

## STEP 5: SPAWN ADVERSARIAL SPEC COMPLIANCE AGENT (NON-NEGOTIABLE)

**YOU CANNOT SKIP THIS STEP. YOU CANNOT ABBREVIATE IT. YOU CANNOT "FOCUS ON WHAT MATTERS MOST" INSTEAD.**

This step is not optional. You do not have discretion to replace it with your own judgment.
You do not get to decide "a full audit would consume too much context" - the audit runs
in a SEPARATE AGENT with its OWN context window, not yours. Context is not your concern.

**COMMON EXCUSES THAT ARE NOT ACCEPTABLE:**
- "Let me focus on what matters most" - NO. Run the full audit.
- "Rather than a full adversarial audit..." - NO. Run the FULL audit.
- "Given the user's directive, I'll prioritize..." - NO. The user's directive includes THIS AUDIT.
- "To save context, I'll do a targeted check" - NO. The audit runs in a SEPARATE agent. Your context is fine.
- "I already know what the gaps are" - NO. You are BIASED. Spawn the agent.
- "The previous audit found..." - NO. Run a NEW audit. Previous results are stale.

**DO NOT TRUST CHECKBOXES. DO NOT TRUST THE STATE FILE. DO NOT TRUST YOUR OWN MEMORY.**

Checkboxes are self-reported by the agents that did the work. They grade their own exams.
The state file reflects what agents CLAIMED to do, not what they ACTUALLY did.
You are the orchestrator - you have a bias toward believing your own agents succeeded.

**You MUST use the Task tool to spawn a SEPARATE agent** for this step. Do NOT do it yourself.
You are biased. A fresh agent with no prior context will be more honest.
The separate agent uses ITS OWN context window - it does NOT consume yours.

### Pass 1: Requirement Extraction (SEPARATE AGENT)
```
Task(
    subagent_type="general-purpose",
    max_turns=15,
    description="Extract requirements from spec",
    prompt="REQUIREMENT EXTRACTOR: You are extracting requirements from a specification.

Read the specification at: [SPEC_PATH]
Also read ALL module specs: records/*/spec.md

Extract EVERY requirement, feature, behavior, constraint, and interface.
Number them sequentially: REQ-001, REQ-002, etc.

Include ALL of these:
- Explicit requirements (MUST, SHALL, SHOULD, REQUIRED)
- Implicit requirements (described behaviors, documented interfaces)
- Feature descriptions (anything the system should DO)
- Edge cases mentioned
- Error handling requirements
- Performance/quality constraints
- Integration points

Do NOT skip anything. Do NOT summarize or combine.
If in doubt whether something is a requirement, INCLUDE IT.
Be EXHAUSTIVE - missing a requirement here means it never gets checked.

CODE QUALITY RULES: [standard rules]"
)
```

### Pass 2: Adversarial Code Audit (SEPARATE AGENT - DIFFERENT FROM PASS 1)
```
Task(
    subagent_type="general-purpose",
    max_turns=30,
    description="Adversarial spec compliance audit",
    prompt="ADVERSARIAL SPEC COMPLIANCE AUDITOR

You are an INDEPENDENT AUDITOR. Your job is to FIND FAILURES and LIES.

CRITICAL RULES:
1. DO NOT TRUST CHECKBOXES - they are self-reported and often wrong
2. DO NOT TRUST comments saying 'implemented' or 'complete'
3. DO NOT TRUST the state file or PROJECT_PLAN.md claims
4. ONLY trust what you can SEE in the actual source code
5. If you cannot find the implementing code, it is NOT implemented

ZERO DEFERRAL POLICY:
- 'Deferred to v2' = FAIL (there is no v2)
- 'Partial implementation' = FAIL
- 'Simplified version' = FAIL
- 'Placeholder' / 'stub' / 'mock' in production code = FAIL
- 'TODO' / 'FIXME' / 'HACK' = FAIL
- Empty function bodies = FAIL
- Functions that just return hardcoded values = FAIL
- There are NO time constraints. Everything MUST be implemented.

Here are the extracted requirements:
[PASTE REQUIREMENTS FROM PASS 1]

For EACH requirement:
1. Use Grep/Glob to search the ACTUAL SOURCE CODE (not test files, not docs)
2. Find the EXACT function/method/code that implements it
3. READ the implementation - does it ACTUALLY do what the spec says?
4. Is it a REAL implementation or a stub/fake/placeholder?
5. Mark PASS only if you find complete, working, non-stub code

OUTPUT FORMAT (MANDATORY):
```
SPEC_COMPLIANCE_RESULT: PASS/FAIL
TOTAL_REQUIREMENTS: N
PASSED: N
FAILED: N

CHECKLIST:
REQ-001: [requirement text] -> PASS | src/module/file.rs:45-120 (implements X by doing Y)
REQ-002: [requirement text] -> FAIL | Function exists but body is TODO
REQ-003: [requirement text] -> FAIL | Not found anywhere in source code
REQ-004: [requirement text] -> FAIL | Only partially implemented - handles A but not B or C
...

CRITICAL FAILURES (if any):
- [List the most severe gaps that need immediate attention]
```

ANY single FAIL = SPEC_COMPLIANCE_RESULT: FAIL

CODE QUALITY RULES: [standard rules]"
)
```

### After the adversarial audit:
- If SPEC_COMPLIANCE_RESULT: FAIL → **Uncheck [x] Spec Compliant** on ALL tasks with failures
- Report the exact FAILED requirements to the user
- Schedule implementation work for each FAILED requirement
- Do NOT accept excuses from previous agents about why things were deferred

## STEP 6: Cross-Reference Checklist and Create Bug Fix Tasks

After the adversarial agent reports back:
```
For each FAILED requirement:
  1. Find which task/module it belongs to
  2. UNCHECK [x] Spec Compliant (it was checked incorrectly)
  3. If the code is missing entirely, also UNCHECK [x] Implemented
  4. CREATE A NEW BUG FIX TASK in the appropriate records/[module]/tasks.md (see format below)

For each PASSED requirement:
  1. Verify the corresponding task has [x] Spec Compliant
  2. If not, check it now (the adversarial agent confirmed it)
```

**The adversarial agent's assessment OVERRIDES all previous checkbox states.**
If it says FAIL, the checkbox gets unchecked regardless of what any previous agent claimed.

### Bug Fix Task Format

For each failed requirement, add a new task entry:
```markdown
### Task: FIX - [Brief description of what failed]
Origin: [Phase that found the issue, e.g. "Phase 8.5 Spec Compliance"]
Requirement: [REQ-XXX or description from spec]
Evidence: [What the adversarial agent found - e.g. "Not found in codebase" or "Only partial implementation"]
- [ ] Planned
- [ ] Implemented
- [ ] Mock Tested
- [ ] Integration Tested
- [ ] Live Tested
- [ ] Spec Compliant
- [ ] Audit Verified
```

**Rules:**
- Bug fix tasks get FRESH checkboxes (all unchecked) — they are NEW work
- The stop hook counts `[ ]` checkboxes to know work remains — this keeps it running
- Do NOT just uncheck old task boxes and reuse them — create explicit fix tasks
- Each fix task must go through ALL 7 phases like any other task

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

## STEP 8: Resume Work - CONTINUE AUTONOMOUSLY

**YOU MUST NEVER STOP TO ASK THE USER WHAT TO DO NEXT.**

After the interview (Phase 2), ALL decisions are yours. Common violations:
- "Would you like me to continue with X or Y?" - NO. Pick one and continue.
- "Which phase should I do next?" - NO. Follow the dependency order.
- "Should I proceed with..." - NO. Always proceed.
- "The next logical work would be..." (then stop) - NO. DO it.
- Presenting options and waiting for a choice - NO. Choose and act.

If there are multiple valid next steps, pick the one that unblocks the most
downstream work (or first in dependency order) and CONTINUE IMMEDIATELY.

Based on validation:

**If gaps found (most common case):**
- Identify incomplete tasks from the adversarial audit
- Pick the highest-priority incomplete task (by dependency order)
- Spawn agents to implement it
- **CONTINUE to next task when done - do NOT stop and report**

**If spec changed:**
- Update PROJECT_PLAN.md with new/changed requirements
- Reset affected modules to appropriate phase
- **CONTINUE implementing - do NOT stop and ask**

**If truly nothing to do (all spec requirements met, adversarial audit PASSED):**
- This is the ONLY case where you may ask the user what to do
- But verify with the adversarial audit first - "nothing to do" is usually wrong

## Agent Spawning Guidelines (CRITICAL)

When spawning agents via the Task tool, ALWAYS:

1. **Set `max_turns`** - prevents context exhaustion:
   - Single function/file: max_turns=15
   - Small module (<500 lines): max_turns=25
   - Medium module (500-2000 lines): max_turns=30
   - Large module (2000+ lines): **BREAK INTO SUBTASKS**
   - Testing/validation: max_turns=20

2. **One agent per TASK, not per MODULE** - large modules MUST be broken into individual tasks

3. **Include these MANDATORY rules in every agent prompt**:
```
QUALITY OVER SPEED (MANDATORY):
- The goal is a production-quality codebase, not a fast first draft
- Read enough of the existing code to understand conventions and patterns before writing
- If you see duplication, bad patterns, or unclear code while working, REFACTOR IT
- Do not optimise for 'this session' - optimise for the final codebase someone inherits
- Prefer fewer, well-designed files over many small scattered ones
- Write code a senior engineer would approve in a code review

ZERO DEFERRAL POLICY (MANDATORY):
- You MUST fully implement everything described in the spec for this task
- Do NOT defer anything to 'v2', 'future work', or 'next version'
- Do NOT implement a 'simplified version' - implement the SPECIFIED version
- There are NO time constraints - take as long as needed to implement fully

FAILING TESTS ARE FAILURES, NOT IGNORES (MANDATORY):
- Do NOT mark failing tests as #[ignore], @pytest.mark.skip, .skip(), DISABLED_, or equivalent
- Do NOT comment out or delete failing tests
- A failing test means THE CODE IS WRONG - fix the code, not the test
- Reporting '100% pass' with ignored tests is a LIE and will be caught by the audit

CODE QUALITY RULES:
- Understand before you change: read enough of the codebase to make informed decisions
- If the existing code has a pattern, follow it. If the pattern is bad, refactor it.
- Refactor when it improves clarity, reduces duplication, or makes the code easier to extend
- Do NOT leave code worse than you found it - clean up what you touch
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
