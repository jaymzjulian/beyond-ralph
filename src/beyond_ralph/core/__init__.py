"""Core modules for Beyond Ralph.

This package contains the core infrastructure:
- Orchestrator: Main control loop
- Session Manager: Claude Code session spawning
- Quota Manager: Usage limit monitoring
- Knowledge Base: Shared knowledge storage
- Records: Task tracking system
"""

from beyond_ralph.core.knowledge import (
    KnowledgeBase,
    KnowledgeEntry,
    create_knowledge_entry,
)
from beyond_ralph.core.quota_manager import (
    QuotaManager,
    QuotaStatus,
    check_quota,
    get_quota_manager,
)
from beyond_ralph.core.records import (
    Checkbox,
    RecordsManager,
    Task,
)
from beyond_ralph.core.session_manager import (
    SessionInfo,
    SessionManager,
    SessionStatus,
    get_session_manager,
)

__all__ = [
    # Knowledge Base
    "KnowledgeBase",
    "KnowledgeEntry",
    "create_knowledge_entry",
    # Quota Manager
    "QuotaManager",
    "QuotaStatus",
    "check_quota",
    "get_quota_manager",
    # Records
    "Checkbox",
    "RecordsManager",
    "Task",
    # Session Manager
    "SessionInfo",
    "SessionManager",
    "SessionStatus",
    "get_session_manager",
]
