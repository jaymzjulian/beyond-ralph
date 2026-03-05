# Beyond Ralph - Troubleshooting Guide

## Common Issues

### Installation Issues

#### "Module not found" errors

**Problem**: Python can't find Beyond Ralph modules.

**Solution**:
```bash
# Verify installation
uv sync
uv run python -c "import beyond_ralph"

# Or reinstall
uv pip install -e .
```

#### "Claude CLI not found"

**Problem**: Beyond Ralph can't find the Claude CLI.

**Solution**:
1. Verify Claude Code is installed:
   ```bash
   which claude
   ```
2. If not found, install Claude Code from https://claude.ai/code
3. Ensure it's in your PATH

### Runtime Issues

#### Orchestrator Stuck in Loop

**Problem**: Beyond Ralph keeps looping between phases.

**Solution**:
1. Check the records file:
   ```bash
   cat records/*/tasks.md
   ```
2. Verify all checkboxes are being updated
3. Reset state if needed:
   ```bash
   rm -rf .beyond_ralph_state
   ```

#### Quota Errors

**Problem**: "Quota limit reached" errors.

**Solution**:
1. Check current quota:
   ```bash
   uv run br-quota
   ```
2. If paused, wait for reset (automatic)
3. Manual override (not recommended):
   ```bash
   rm .beyond_ralph_quota
   ```

#### Session Spawn Failures

**Problem**: "Failed to spawn session" errors.

**Solution**:
1. Check if Claude Code is running:
   ```bash
   pgrep -f claude
   ```
2. Verify no orphan processes:
   ```bash
   pkill -f "claude.*--continue"
   ```
3. Clean up session files:
   ```bash
   rm -rf .beyond_ralph_sessions
   ```

### Testing Issues

#### Mock Server Not Starting

**Problem**: Mock API server fails to start.

**Solution**:
1. Check if port is in use:
   ```bash
   lsof -i :8080
   ```
2. Kill any existing process:
   ```bash
   kill $(lsof -t -i:8080)
   ```
3. Try a different port

#### Playwright Errors

**Problem**: Browser automation fails.

**Solution**:
1. Install browsers:
   ```bash
   playwright install
   ```
2. Install system dependencies:
   ```bash
   playwright install-deps
   ```
3. Check display availability (for non-headless):
   ```bash
   echo $DISPLAY
   ```

#### CLI Test Timeouts

**Problem**: CLI tests timing out.

**Solution**:
1. Increase timeout in test configuration
2. Check if process is blocking on input
3. Add explicit expect patterns for prompts

### Phase-Specific Issues

#### Phase 1: Spec Ingestion Fails

**Problem**: Can't read specification file.

**Solution**:
1. Verify file exists:
   ```bash
   ls -la SPEC.md
   ```
2. Check file permissions
3. Verify file is valid markdown

#### Phase 2: Interview Hangs

**Problem**: Interview phase never completes.

**Solution**:
1. Check for pending questions in output
2. Verify AskUserQuestion prompts are visible
3. Try running with verbose logging

#### Phase 7: Implementation Loops

**Problem**: Implementation keeps restarting.

**Solution**:
1. Check test output for failures
2. Review agent reviews items list
3. Verify all review items are being fixed
4. Check for infinite review-fix cycle

#### Phase 8: Testing Never Completes

**Problem**: Final testing phase loops back.

**Solution**:
1. Check checkbox status:
   ```bash
   grep -r "\[.\]" records/
   ```
2. Verify all 7 checkboxes are checked
3. Check for test failures in evidence

### Knowledge Base Issues

#### Knowledge Corruption

**Problem**: Knowledge base has invalid entries.

**Solution**:
1. Remove invalid entries:
   ```bash
   rm beyondralph_knowledge/corrupted-entry.md
   ```
2. Rebuild from sources:
   ```bash
   rm -rf beyondralph_knowledge
   # Restart Beyond Ralph
   ```

#### Duplicate Knowledge

**Problem**: Same knowledge appears multiple times.

**Solution**:
Knowledge entries have unique session IDs. Duplicates are typically harmless but can be cleaned manually.

### Records Issues

#### Task Not Updating

**Problem**: Checkboxes don't update after completion.

**Solution**:
1. Check file permissions:
   ```bash
   ls -la records/*/tasks.md
   ```
2. Verify task parsing:
   ```bash
   uv run python -c "from beyond_ralph.core.records import RecordsManager; rm = RecordsManager(); print(rm.get_all_tasks())"
   ```

#### Module Not Found in Records

**Problem**: RecordsManager can't find module.

**Solution**:
1. Check directory structure:
   ```bash
   ls -la records/
   ```
2. Verify module name matches exactly (case-sensitive)

## Error Messages

### "QuotaError: Cannot determine quota status"

**Cause**: Failed to parse Claude /usage output.

**Solution**:
1. Run quota check manually:
   ```bash
   uv run br-quota
   ```
2. Check Claude CLI is responsive
3. Clear quota cache:
   ```bash
   rm .beyond_ralph_quota
   ```

### "SessionError: Lock acquisition failed"

**Cause**: Another process is using the session.

**Solution**:
1. Check for running processes:
   ```bash
   ls -la .beyond_ralph_sessions/
   ```
2. Clean up stale locks:
   ```bash
   rm .beyond_ralph_sessions/*.lock
   ```

### "ValidationError: Evidence not found"

**Cause**: Testing agent didn't provide evidence.

**Solution**:
1. Check evidence directory:
   ```bash
   ls -la records/*/evidence/
   ```
2. Re-run testing phase
3. Check for test errors in logs

### "PhaseError: Maximum loop backs reached"

**Cause**: Phase 8 looped back to Phase 6 three times.

**Solution**:
This is a safety mechanism. Check:
1. Why tests keep failing
2. Why checkboxes aren't being checked
3. Review recent knowledge entries for clues

## Recovery Procedures

### Full Reset

To completely reset Beyond Ralph:

```bash
rm -rf .beyond_ralph_state
rm -rf .beyond_ralph_sessions
rm -rf .beyond_ralph_quota
rm -rf beyondralph_knowledge
rm -rf records
```

Then restart with:
```
/beyond-ralph start --spec SPEC.md
```

### Partial Reset (Keep Knowledge)

```bash
rm -rf .beyond_ralph_state
rm -rf .beyond_ralph_sessions
rm -rf records
```

This keeps learned knowledge but restarts execution.

### Resume from Checkpoint

If Beyond Ralph was interrupted:
```
/beyond-ralph resume
```

This restores from `.beyond_ralph_state`.

## Debugging

### Enable Verbose Logging

```bash
export BEYOND_RALPH_LOG_LEVEL=DEBUG
/beyond-ralph start --spec SPEC.md
```

### Check Agent Output

Agent output is logged to:
```
.beyond_ralph_sessions/[agent-id]/output.log
```

### Inspect State File

```bash
cat .beyond_ralph_state | python -m json.tool
```

## Getting Help

If issues persist:

1. Check the [GitHub Issues](https://github.com/jaymzee/beyond-ralph/issues)
2. Review recent knowledge base entries for error patterns
3. Run the diagnostic command:
   ```bash
   uv run br-diagnose
   ```

## Next Steps

- [Configuration](configuration.md) - Adjust settings
- [Testing Guide](testing.md) - Testing capabilities
