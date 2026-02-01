# Knowledge: Phase 5 Research Items

**Created by**: Phase 5 Uncertainty Analysis
**Date**: 2024-02-01
**Category**: planning

## Summary

Items identified during Phase 5 that require autonomous research during implementation.

---

## Claude Code CLI Research Required

### Session Management
- [ ] Exact CLI syntax for spawning sessions with UUID return
- [ ] Mechanism for sending messages to existing sessions
- [ ] How to extract "final result" vs work logs
- [ ] Session cleanup commands

### Quota Detection
- [ ] `claude /usage` exact output format
- [ ] Parsing logic for session and weekly percentages
- [ ] Escape + /quit sequence implementation

### Plugin System
- [ ] Verify hook exit code behavior
- [ ] SubagentStop hook payload format
- [ ] Output streaming mechanism to parent
- [ ] AskUserQuestion routing from subagents

### Task Tool
- [ ] 7-agent parallel limit mechanics
- [ ] Background vs foreground execution API
- [ ] Context window allocation per subagent
- [ ] Result payload structure

---

## Platform Research Required

### Windows Native
- [ ] Package manager APIs (choco, winget, scoop)
- [ ] Virtual display alternatives to Xvfb
- [ ] Browser installation without WSL

### WhatsApp
- [ ] whatsmeow library API usage
- [ ] Authentication flow
- [ ] Session persistence

---

## Design Decisions Required

These can be made autonomously during implementation:

1. **Compaction Detection**: Monitor context size OR use Claude Code hooks
2. **Plan Update Detection**: File watching OR git diff monitoring
3. **Evidence Schema**: Define what constitutes valid test evidence
4. **Inter-Module Requirement Format**: Structured markdown format
5. **Credential Encryption**: AES-256-GCM with keyring for key storage

---

## Resolution Protocol

Per interview-decisions.md:
1. Research autonomously - DO NOT ask user
2. Document findings in knowledge base
3. Only escalate if fundamentally blocked (rare)
4. Use mandatory fallback when tools fail
