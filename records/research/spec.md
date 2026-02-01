# Module 9: Research Agent - Specification

**Module**: research
**Location**: `src/beyond_ralph/agents/research_agent.py`
**Dependencies**: system-capabilities

## Purpose

Autonomously discover and install tools, with mandatory fallback when tools fail.

## Requirements

### R1: Tool Discovery
- Web search for testing frameworks
- GitHub API for repo evaluation (stars, last commit)
- Evaluate platform compatibility
- Compare alternatives

### R2: Preferred Tools
- Has opinions when user doesn't specify
- Playwright for web, pytest for Python, etc.
- Use preferred tool by default

### R3: Mandatory Fallback
- When a tool fails, MUST find alternative
- Never ask user what to try
- Try alternatives until one works
- Only give up after exhausting options

### R4: Autonomous Installation
- Install without user approval (post-interview)
- Use appropriate package manager
- Verify installation success
- Document in knowledge base

## Preferred Tools

| Category | Tool |
|----------|------|
| Browser automation | playwright |
| Python testing | pytest |
| API mocking | respx |
| Screenshots | pillow |
| Video capture | opencv-python |
| Performance | locust |
| Linting | ruff |
| Documentation | mkdocs |

## Interface

```python
class ResearchAgent:
    async def find_tool(
        self,
        need: str,
        category: ToolCategory,
    ) -> DiscoveredTool

    async def install_tool(self, tool: DiscoveredTool) -> bool

    async def handle_failure(
        self,
        failed_tool: str,
        error: str,
        category: ToolCategory,
    ) -> DiscoveredTool | None

    def get_preferred_tool(self, category: ToolCategory) -> str
```

## Testing Requirements

- Mock web search
- Mock GitHub API
- Test fallback behavior
- Test installation verification
