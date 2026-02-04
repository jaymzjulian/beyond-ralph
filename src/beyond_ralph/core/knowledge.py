"""Knowledge Base for Beyond Ralph.

Provides shared knowledge storage and retrieval for agents.
Uses Markdown with YAML frontmatter format.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

# Default knowledge base location
DEFAULT_KB_PATH = Path("beyondralph_knowledge")


@dataclass
class KnowledgeEntry:
    """A knowledge base entry."""

    uuid: str
    created_by_session: str
    created_at: datetime
    category: str
    tags: list[str]
    title: str
    content: str
    questions: list[str] = field(default_factory=list)

    @classmethod
    def from_file(cls, path: Path) -> "KnowledgeEntry":
        """Parse a knowledge entry from a Markdown file with YAML frontmatter."""
        text = path.read_text()

        # Split frontmatter and content
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                content = parts[2].strip()
            else:
                raise ValueError(f"Invalid frontmatter in {path}")
        else:
            raise ValueError(f"No frontmatter found in {path}")

        # Extract title from content (first # heading)
        title = ""
        for line in content.split("\n"):
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Handle date - YAML may parse it as datetime or keep as string
        date_value = frontmatter.get("date", datetime.now())
        if isinstance(date_value, str):
            created_at = datetime.fromisoformat(date_value)
        elif isinstance(date_value, datetime):
            created_at = date_value
        else:
            created_at = datetime.now()

        return cls(
            uuid=frontmatter.get("uuid", ""),
            created_by_session=frontmatter.get("created_by_session", ""),
            created_at=created_at,
            category=frontmatter.get("category", "general"),
            tags=frontmatter.get("tags", []),
            title=title,
            content=content,
            questions=frontmatter.get("questions", []),
        )

    def to_markdown(self) -> str:
        """Convert to Markdown with YAML frontmatter."""
        frontmatter = {
            "uuid": self.uuid,
            "created_by_session": self.created_by_session,
            "date": self.created_at.isoformat(),
            "category": self.category,
            "tags": self.tags,
        }
        if self.questions:
            frontmatter["questions"] = self.questions

        yaml_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        return f"---\n{yaml_str}---\n\n{self.content}"


class KnowledgeBase:
    """Knowledge base manager."""

    def __init__(self, path: Path | None = None):
        """Initialize knowledge base.

        Args:
            path: Path to knowledge base directory. Defaults to beyondralph_knowledge/
        """
        self.path = path or DEFAULT_KB_PATH
        self.path.mkdir(parents=True, exist_ok=True)

    def write(self, entry: KnowledgeEntry) -> str:
        """Write a knowledge entry.

        Args:
            entry: The knowledge entry to write.

        Returns:
            UUID of the written entry.
        """
        if not entry.uuid:
            entry.uuid = str(uuid.uuid4())[:8]

        # Generate filename from title or uuid
        safe_title = "".join(c if c.isalnum() or c in "-_ " else "" for c in entry.title)
        safe_title = safe_title.lower().replace(" ", "-")[:50]
        filename = f"{safe_title}.md" if safe_title else f"{entry.uuid}.md"

        filepath = self.path / filename
        filepath.write_text(entry.to_markdown())

        return entry.uuid

    def read(self, uuid_or_path: str) -> KnowledgeEntry | None:
        """Read a knowledge entry by UUID or filename.

        Args:
            uuid_or_path: UUID prefix or filename.

        Returns:
            KnowledgeEntry if found, None otherwise.
        """
        # Try as filename first
        filepath = self.path / uuid_or_path
        if filepath.exists():
            return KnowledgeEntry.from_file(filepath)

        # Try as UUID prefix
        for file in self.path.glob("*.md"):
            try:
                entry = KnowledgeEntry.from_file(file)
                if entry.uuid.startswith(uuid_or_path):
                    return entry
            except (ValueError, yaml.YAMLError):
                continue

        return None

    def search(self, query: str, category: str | None = None) -> list[KnowledgeEntry]:
        """Search knowledge base.

        Args:
            query: Text to search for in title, content, or tags.
            category: Optional category filter.

        Returns:
            List of matching entries.
        """
        results = []
        query_lower = query.lower()

        for file in self.path.glob("*.md"):
            try:
                entry = KnowledgeEntry.from_file(file)

                # Apply category filter
                if category and entry.category != category:
                    continue

                # Search in title, content, and tags
                if (
                    query_lower in entry.title.lower()
                    or query_lower in entry.content.lower()
                    or any(query_lower in tag.lower() for tag in entry.tags)
                ):
                    results.append(entry)

            except (ValueError, yaml.YAMLError):
                continue

        # Sort by date (most recent first)
        results.sort(key=lambda e: e.created_at, reverse=True)
        return results

    def list_recent(self, hours: int = 24) -> list[KnowledgeEntry]:
        """List entries created within the last N hours.

        Args:
            hours: Number of hours to look back.

        Returns:
            List of recent entries.
        """
        cutoff = datetime.now().replace(
            hour=datetime.now().hour - hours if datetime.now().hour >= hours else 0
        )
        results = []

        for file in self.path.glob("*.md"):
            try:
                entry = KnowledgeEntry.from_file(file)
                if entry.created_at >= cutoff:
                    results.append(entry)
            except (ValueError, yaml.YAMLError):
                continue

        results.sort(key=lambda e: e.created_at, reverse=True)
        return results

    def get_by_session(self, session_id: str) -> list[KnowledgeEntry]:
        """Get entries created by a specific session.

        Args:
            session_id: Session UUID or prefix.

        Returns:
            List of entries from that session.
        """
        results = []

        for file in self.path.glob("*.md"):
            try:
                entry = KnowledgeEntry.from_file(file)
                if entry.created_by_session.startswith(session_id):
                    results.append(entry)
            except (ValueError, yaml.YAMLError):
                continue

        results.sort(key=lambda e: e.created_at, reverse=True)
        return results

    def get_all_categories(self) -> list[str]:
        """Get all unique categories in the knowledge base.

        Returns:
            List of category names.
        """
        categories = set()

        for file in self.path.glob("*.md"):
            try:
                entry = KnowledgeEntry.from_file(file)
                categories.add(entry.category)
            except (ValueError, yaml.YAMLError):
                continue

        return sorted(categories)

    def get_all_tags(self) -> list[str]:
        """Get all unique tags in the knowledge base.

        Returns:
            List of tag names.
        """
        tags = set()

        for file in self.path.glob("*.md"):
            try:
                entry = KnowledgeEntry.from_file(file)
                tags.update(entry.tags)
            except (ValueError, yaml.YAMLError):
                continue

        return sorted(tags)


def create_knowledge_entry(
    title: str,
    content: str,
    session_id: str,
    category: str = "general",
    tags: list[str] | None = None,
    questions: list[str] | None = None,
) -> KnowledgeEntry:
    """Helper to create a new knowledge entry.

    Args:
        title: Entry title.
        content: Entry content (Markdown).
        session_id: UUID of the creating session.
        category: Category for the entry.
        tags: Optional tags.
        questions: Optional follow-up questions.

    Returns:
        New KnowledgeEntry ready to be written.
    """
    return KnowledgeEntry(
        uuid=str(uuid.uuid4())[:8],
        created_by_session=session_id,
        created_at=datetime.now(),
        category=category,
        tags=tags or [],
        title=title,
        content=f"# {title}\n\n{content}",
        questions=questions or [],
    )
