---
name: beyond-ralph-resume
prefix: "@br-resume"
category: orchestration
color: yellow
description: "Resume or re-validate a Beyond Ralph project"
---

# /beyond-ralph-resume - Resume & Validate Project

Resume a Beyond Ralph project OR re-validate after spec changes. This command does NOT blindly trust the state file - it always validates against the current spec.

## Resume Process (MANDATORY STEPS)

### 1. Check Quota
Run quota check first - don't proceed if limited:
```
If session >= 85% OR weekly >= 85%:
  Report "Cannot resume - quota limited"
  Exit and wait for reset
```

### 2. Read Current State
Load `.beyond_ralph_state` for baseline:
- Last recorded phase
- Recorded progress percentage
- Module statuses

### 3. VALIDATE SPEC (CRITICAL - Never Skip)
**The spec is the source of truth, NOT the state file.**

Read `SPEC.md` (or configured spec path) and:
1. **Hash the spec** - compare to stored hash in state
2. **If spec changed**:
   - Report: "Spec has changed since last run"
   - Re-parse requirements
   - Identify NEW requirements not in current plan
   - Identify REMOVED requirements that were implemented
   - Identify MODIFIED requirements that need re-validation

### 4. Validate Project Plan
Read `PROJECT_PLAN.md` and cross-reference:
1. **All spec requirements covered?** - Every MUST/REQUIRED in spec has a task
2. **All modules accounted for?** - Check `records/*/tasks.md` exist
3. **Checkboxes accurate?** - Verify claimed completions:
   - "Implemented" → code actually exists
   - "Tested" → tests actually pass
   - "Spec Compliant" → implementation matches spec

### 5. Identify Gaps
Compare spec requirements vs actual state:
```
For each requirement in SPEC.md:
  - Is it in PROJECT_PLAN.md?
  - Is there a module for it?
  - Are all 6 checkboxes checked?
  - Does the implementation ACTUALLY match the requirement?

If ANY gaps found:
  - State is NOT "complete" regardless of what state file says
  - Report gaps and schedule work
```

### 6. Resume or Re-plan
Based on validation:

**If spec unchanged AND all validations pass:**
- Resume from last phase
- Continue pending tasks

**If spec changed OR gaps found:**
- Report discrepancies
- Update PROJECT_PLAN.md with new/changed requirements
- Reset affected modules to appropriate phase
- Schedule validation tasks for changed requirements

## Spec Change Detection

When spec changes are detected, categorize:

| Change Type | Action |
|-------------|--------|
| NEW requirement | Add to plan, schedule implementation |
| REMOVED requirement | Mark obsolete, clean up if needed |
| MODIFIED requirement | Re-validate implementation, may need rework |
| CLARIFIED (same intent) | Update docs, verify implementation still valid |

## Quota Check

If quota is still limited (≥85%), report:
```
Cannot resume - quota still limited
Session: X% | Weekly: Y%
Will auto-retry when quota resets.
```

## Example Output

```
[BEYOND-RALPH] Resuming project br-5adbb6ea...

[VALIDATE] Checking spec hash...
[VALIDATE] ⚠️  SPEC.md has changed (hash mismatch)
[VALIDATE] Analyzing changes...

[CHANGES DETECTED]
  NEW: Project Installation section added
    - Requirement: Installer must bundle MCP servers
    - Requirement: --allow-free-tier-with-key flag
    - Requirement: DuckDuckGo search MCP server

  MODIFIED: Web Research section
    - Added: arXiv, Wikipedia MCP servers

[GAP ANALYSIS]
  ❌ "DuckDuckGo MCP server" - Not implemented
  ❌ "arXiv MCP server" - Not configured
  ❌ "Wikipedia MCP server" - Not configured
  ✅ All other requirements validated

[ACTION] Updating project plan...
[ACTION] Scheduling new tasks:
  - Task: Add DuckDuckGo to installer
  - Task: Add arXiv to installer
  - Task: Add Wikipedia to installer
  - Task: Update spec compliance verification

[RESUME] Continuing from Phase 7 (Implementation)...
```

## Start Now

1. Check quota
2. Read state file (baseline only)
3. **Validate spec** (compare to state)
4. **Validate project plan** (compare to spec)
5. **Validate implementations** (spot-check completions)
6. Report gaps/changes
7. Resume with accurate state
