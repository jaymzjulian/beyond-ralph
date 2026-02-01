# Beyond Ralph Knowledge Base

This directory contains shared knowledge accumulated by agents during development.

## Purpose

All agents contribute to and consume from this knowledge base. This enables:
- Knowledge sharing between agents
- Follow-up questions to knowledge sources
- Avoiding duplicate work
- Learning from previous agent experiences

## Entry Format

Each knowledge entry should follow this format:

```markdown
# Knowledge: [Topic Title]

**Created by**: [Session UUID]
**Date**: [ISO 8601 date]
**Category**: [design|implementation|testing|issue|resolution]

## Summary
[1-2 sentence summary]

## Details
[Detailed information]

## Related Topics
- [Link to related knowledge entry]

## Questions for Source
[Questions another agent might ask this session's creator]

## Tags
- [tag1]
- [tag2]
```

## Categories

- **design**: Architecture and design decisions
- **implementation**: How things were implemented
- **testing**: Testing approaches and results
- **issue**: Problems encountered
- **resolution**: How issues were resolved

## Usage Guidelines

### Before Creating Knowledge
1. Search existing knowledge for duplicates
2. Reference related existing entries
3. Include source session UUID

### When Reading Knowledge
1. Check if entry answers your question
2. Note source UUID for follow-up
3. Update entry if you have new information

### Follow-up Protocol
If knowledge is insufficient:
1. Note the source session UUID
2. The orchestrator can send follow-up to that session
3. Add clarifications to the knowledge entry
