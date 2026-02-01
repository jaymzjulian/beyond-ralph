# Knowledge: Interview Decisions for Beyond Ralph

**Created by**: Initial Session (Interview Phase)
**Date**: 2024-02-01
**Category**: design

## Summary

Complete record of all decisions made during the Phase 2 interview for Beyond Ralph implementation.

---

## Platform & Environment

| Decision | Choice |
|----------|--------|
| Deployment environments | ALL: WSL2, Native Linux, macOS, **Native Windows** |
| Windows package managers | Chocolatey + winget + Scoop + **manual installation** |
| Plugin scope | Both global (~/.claude/plugins) and project-local |
| Persistence level | Very aggressive - continue until 100% complete |

## Quota & Subscription

| Decision | Choice |
|----------|--------|
| Claude tier | Detect at runtime |
| Max parallel agents | 7 (Claude Code limit) |
| Quota threshold | 85% (PAUSE, not stop) |

## Interview Agent Behavior

| Decision | Choice |
|----------|--------|
| Wait for answers | Indefinitely |
| Persistence on same topic | 3 follow-ups then INSIST |
| Minimum questions | No minimum, quality over quantity |

## Knowledge Base & Records

| Decision | Choice |
|----------|--------|
| KB format | Markdown with YAML frontmatter |
| Git strategy | Frequent atomic commits |
| Logging | Full logs with timestamps |
| State persistence | Full state across sessions |
| Checkpoints | Automatic after each phase/task |

## Code Quality

| Decision | Choice |
|----------|--------|
| Test coverage | **100% STRICTLY REQUIRED** (only destructive APIs exempt) |
| Test gap documentation | UNTESTABLE.md with justification |
| Security findings | ALL findings blocking (zero tolerance) |
| Review loop | Same Review Agent re-reviews |
| Rollback on failure | Only uncheck failed item (minimal) |

## Autonomous Behavior

| Decision | Choice |
|----------|--------|
| Unknown tech | Research autonomously |
| Crashes/errors | Research and fix autonomously |
| Capability gaps | Research → Document → Ask (sequence) |
| Tool failures | MANDATORY fallback, find alternatives |
| System installs | Do whatever it takes (sudo, manual) |

## Project Configuration

| Decision | Choice |
|----------|--------|
| Secrets handling | Require in .env file |
| Config format | YAML (beyond-ralph.yaml) |
| Dependency versions | Pin major versions only |
| Caching | Aggressive caching |
| Disk space | No limit |
| Encryption | Encrypt sensitive data at rest |

## Testing Capabilities

| Decision | Choice |
|----------|--------|
| Web browsers | Chromium only (default) |
| Mobile testing | Android emulator supported |
| Mock → Real APIs | Automatic transition when mock tests pass |
| Long-running tests | Run in background, continue other work |
| Video formats | MP4 + WebM |
| Display servers | Detect available (Wayland > xvnc > xvfb), try alternatives |
| Hardware projects | Simulation first, emulators, real hardware when available |

## Remote Access & Notifications

| Decision | Choice |
|----------|--------|
| Remote viewing | VNC with random password (auto-setup) |
| Notification services | Slack, Discord, Email, WhatsApp (whatsmeow) |
| Notification triggers | Only when blocked/needs input |
| Webhooks | Yes, outgoing webhooks |
| OS notifications | When available |

## Documentation & Output

| Decision | Choice |
|----------|--------|
| User docs | Markdown in docs/ |
| Diagrams | Mermaid |
| Evidence format | Markdown report + raw logs |
| Architecture diagrams | Yes, generated |
| Benchmarks | Ask during interview |
| Licensing | No license by default |

## GitHub Integration

| Decision | Choice |
|----------|--------|
| Features | Push, PR creation, issue tracking |
| Auto-issues | Yes, create for blockers |
| Webhooks | Outgoing webhooks for CI/CD |

## Project Handling

| Decision | Choice |
|----------|--------|
| Multiple projects | Parallel projects supported |
| Max duration | No practical limit |
| Completion action | Generate report, await next project |
| Dry run mode | Yes, plan-only mode |
| Import existing | Yes, analyze and enhance |
| Compatibility | Major versions only (1.x compatible) |

## Per-Interview Decisions

These are asked during each project's interview:
- CI/CD setup (GitHub Actions, GitLab CI, etc.)
- Database approach
- Container/Docker usage
- Performance benchmarks

## Distribution

| Decision | Choice |
|----------|--------|
| Package | Both PyPI and Claude plugin |
| Telemetry | Local metrics only |
| Dashboard | Optional, user can enable |

---

## Implementation Notes

1. **Windows support is first-class** - not just WSL2, native Windows with full package manager support
2. **100% coverage is non-negotiable** - document any gaps with justification
3. **Zero tolerance for security issues** - ALL findings must be fixed
4. **Do whatever it takes** - install packages, research unknown tech, find alternatives
5. **Notify only when stuck** - don't spam user with progress updates
6. **Encrypt secrets** - credentials must be protected at rest
