# Research Module Tasks

## Overview

The research module provides the ResearchAgent for autonomous tool discovery, evaluation, and installation.

**Dependencies**: agents/base, knowledge
**Required By**: testing, orchestrator
**Location**: `src/beyond_ralph/agents/research_agent.py`
**Tests**: `tests/unit/test_research_agent.py` (48 tests)
**LOC**: 740

---

## Task: Implement ResearchAgent Base Class

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: Base ResearchAgent class for tool discovery.

**Acceptance Criteria**:
1. Extends `BaseAgent` with research capabilities
2. `research(topic)` method for web research
3. `discover_tool(requirement)` finds appropriate tools
4. Store findings in knowledge base
5. Log all research activities

**Tests**: tests/unit/test_research_agent.py::TestResearchAgentBase
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/research/evidence/base-class/

---

## Task: Implement PREFERRED_TOOLS Dictionary

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: Beyond Ralph's preferred tool choices.

**Acceptance Criteria**:
1. `PREFERRED_TOOLS` constant dictionary
2. Categories: testing, linting, security, build
3. Platform-aware recommendations
4. Fallback alternatives listed
5. Rationale for each preference

**Tool Preferences**:
```python
PREFERRED_TOOLS = {
    "web_testing": "playwright",  # Cross-platform, actively maintained
    "python_lint": "ruff",        # Fast, comprehensive
    "security_scan": "semgrep",   # Multi-language, OWASP rules
    ...
}
```

**Tests**: tests/unit/test_research_agent.py::TestPreferredTools
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/research/evidence/preferred-tools/

---

## Task: Implement Tool Discovery

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: Search web for appropriate tools.

**Acceptance Criteria**:
1. `search_for_tool(requirement)` searches web
2. Evaluate candidates for:
   - Platform compatibility
   - Active maintenance
   - Documentation quality
   - Community adoption
3. Rank candidates by suitability
4. Return top recommendations

**Tests**: tests/unit/test_research_agent.py::TestToolDiscovery
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/research/evidence/tool-discovery/

---

## Task: Implement Autonomous Tool Installation

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: Install tools WITHOUT user approval (post-interview).

**Acceptance Criteria**:
1. `install_tool(tool_name)` installs via appropriate method
2. Use uv/pip for Python packages
3. Use system package manager with sudo if available
4. NO user approval requested (approved during interview)
5. Verify installation works
6. Log all installations to knowledge base

**Tests**: tests/unit/test_research_agent.py::TestAutonomousInstallation
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/research/evidence/autonomous-installation/

---

## Task: Implement MANDATORY Fallback on Failure

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: MANDATORY - Search for alternatives when tools fail.

**Acceptance Criteria**:
1. `handle_tool_failure(tool, error)` triggers fallback
2. Search for alternative tools automatically
3. NEVER give up without trying alternatives
4. Log failure reason to knowledge base
5. Install and verify alternative
6. Document what failed and why

**Example Flow**:
```
[AGENT:research] Playwright failing: Chrome not available
[AGENT:research] Searching for alternatives...
[AGENT:research] Found: Selenium with Firefox
[AGENT:research] Installing selenium...
[KNOWLEDGE] Stored: playwright-chrome-failure-arm64-linux.md
```

**Tests**: tests/unit/test_research_agent.py::TestMandatoryFallback
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/research/evidence/mandatory-fallback/

---

## Task: Implement Tool Verification

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: Verify tools work after installation.

**Acceptance Criteria**:
1. `verify_tool(tool_name)` tests tool works
2. Run basic sanity check for each tool type
3. Check version output
4. Test basic functionality
5. Return verification result with evidence

**Tests**: tests/unit/test_research_agent.py::TestToolVerification
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/research/evidence/tool-verification/

---

## Task: Implement Knowledge Base Integration

- [x] Planned - 2024-02-01
- [x] Implemented - 2024-02-01
- [x] Mock tested - 2024-02-01
- [ ] Integration tested
- [ ] Live tested
- [ ] Spec compliant

**Description**: Store research findings in knowledge base.

**Acceptance Criteria**:
1. Store tool evaluations
2. Store installation successes/failures
3. Store platform-specific notes
4. Include session UUID for follow-up
5. Enable cross-project learning

**Tests**: tests/unit/test_research_agent.py::TestKnowledgeIntegration
**Implementation Agent**: auto
**Validation Agent**: TBD
**Evidence**: records/research/evidence/knowledge-integration/

---

## Summary

| Task | Planned | Implemented | Mock | Integration | Live | Spec |
|------|:-------:|:-----------:|:----:|:-----------:|:----:|:----:|
| ResearchAgent Base Class | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| PREFERRED_TOOLS Dictionary | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| Tool Discovery | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| Autonomous Tool Installation | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| MANDATORY Fallback on Failure | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| Tool Verification | [x] | [x] | [x] | [ ] | [ ] | [ ] |
| Knowledge Base Integration | [x] | [x] | [x] | [ ] | [ ] | [ ] |

**Overall Progress**: 7/7 implemented, 0/7 integration tested, 0/7 live tested, 0/7 spec compliant
