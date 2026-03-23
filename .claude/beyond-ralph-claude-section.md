
## Beyond Ralph - Autonomous Development Rules

This project uses Beyond Ralph (`/beyond-ralph`, `/beyond-ralph-resume`) for autonomous multi-agent development. The following rules apply to ALL agents working on this project.

### Quality Over Speed (MANDATORY)
- Optimise for the **final codebase**, not for getting through phases quickly
- Read enough of the existing code to understand patterns before writing new code
- If you see duplication, bad patterns, or unclear code while working, **refactor it**
- Do not optimise for "this session" - write code as if it's the final version
- Prefer fewer, well-designed files over many scattered fragments
- Write code a senior engineer would approve in a code review

### Zero Deferral Policy (MANDATORY)
- There is NO "v2", "future version", "next release", or "out of scope"
- If the spec says it, it MUST be fully implemented. No exceptions.
- "Deferred", "partial", "simplified", "placeholder", "good enough" = **FAIL**
- There are NO time constraints - take as long as needed

### Failing Tests Are Failures, NOT Ignores (MANDATORY)
- Do NOT mark failing tests as `#[ignore]`, `@pytest.mark.skip`, `.skip()`, `DISABLED_`
- Do NOT comment out or delete failing tests
- A failing test means THE CODE IS WRONG - fix the code, not the test
- Test metric: passed / (passed + failed + ignored) - ignored counts as failed

### Do Not Trust Checkboxes
- Checkboxes in `records/*/tasks.md` are self-reported by implementing agents
- The ONLY source of truth is the actual source code
- Phase 8.5 adversarial audit verifies independently - its assessment OVERRIDES checkboxes

### Task Checkboxes (7 per task)
- [ ] Planned - design documented
- [ ] Implemented - code written FULLY (no stubs, no partial)
- [ ] Mock Tested - unit tests pass
- [ ] Integration Tested - module interaction tests pass
- [ ] Live Tested - ACTUAL built artifact executed with correct results (NOT more unit tests). Must be done by a SEPARATE agent.
- [ ] Spec Compliant - ADVERSARIAL agent verified EVERY requirement has matching code
- [ ] Audit Verified - static analysis + LLM interrogation passed (no stubs/fakes/TODOs)

### ALL Work Goes Through The Checkbox Workflow (MANDATORY)
- Every piece of work MUST have a task entry in `records/[module]/tasks.md` with 7 checkboxes
- Every task MUST go through ALL 7 phases: Planned → Implemented → Mock Tested → Integration Tested → Live Tested → Spec Compliant → Audit Verified
- Do NOT implement changes "directly" and skip the workflow
- Do NOT check boxes retroactively — if the work wasn't done through the workflow, it doesn't count
- "The work IS done, the checkboxes just aren't checked" = **the work is NOT done**
- If you discover new work mid-implementation, CREATE A NEW TASK before doing it
- The stop hook counts `[ ]` checkboxes — skipping the workflow breaks autonomous operation

### Bug Fixes Create New Tasks
- When Phases 8, 8.5, or 9 find issues, create NEW task entries in `records/[module]/tasks.md`
- Bug fix tasks get FRESH checkboxes (all 7 unchecked) — they are NEW work
- Do NOT just uncheck old task boxes — create explicit `FIX - [description]` tasks
- This keeps the stop hook aware that work remains (it counts `[ ]` checkboxes)

### Agent Autonomy
- After Phase 2 (Interview), ALL remaining work is FULLY AUTONOMOUS
- NEVER stop to ask the user "Would you like X or Y?" - just pick and continue
- NEVER skip the adversarial spec compliance audit (Phase 8.5) for any reason
