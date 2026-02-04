"""API Documentation Ingestion.

Handles ingesting and storing API documentation for use during development:
- OpenAPI/Swagger specifications
- GraphQL schemas
- Plain text API documentation
- Auto-discovery from URLs

This is required by the SPEC: "It must, as a first part of development,
ingest any API documentation that is relevant, and keep them with the project"
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

logger = logging.getLogger(__name__)


class APIDocType(Enum):
    """Type of API documentation."""

    OPENAPI_3 = "openapi_3"
    OPENAPI_2 = "openapi_2"  # Swagger 2.0
    GRAPHQL = "graphql"
    ASYNCAPI = "asyncapi"
    RAML = "raml"
    PLAIN_TEXT = "plain_text"
    HTML = "html"
    MARKDOWN = "markdown"


@dataclass
class APIEndpoint:
    """A single API endpoint."""

    path: str
    method: str
    summary: str | None = None
    description: str | None = None
    parameters: list[dict[str, Any]] = field(default_factory=list)
    request_body: dict[str, Any] | None = None
    responses: dict[str, Any] = field(default_factory=dict)
    security: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "path": self.path,
            "method": self.method,
            "summary": self.summary,
            "description": self.description,
            "parameters": self.parameters,
            "request_body": self.request_body,
            "responses": self.responses,
            "security": self.security,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "APIEndpoint":
        """Create from dictionary."""
        return cls(
            path=data["path"],
            method=data["method"],
            summary=data.get("summary"),
            description=data.get("description"),
            parameters=data.get("parameters", []),
            request_body=data.get("request_body"),
            responses=data.get("responses", {}),
            security=data.get("security", []),
            tags=data.get("tags", []),
        )


@dataclass
class APISchema:
    """A schema/model definition."""

    name: str
    schema_type: str  # "object", "array", etc.
    properties: dict[str, Any] = field(default_factory=dict)
    required: list[str] = field(default_factory=list)
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "schema_type": self.schema_type,
            "properties": self.properties,
            "required": self.required,
            "description": self.description,
        }


@dataclass
class APIDocumentation:
    """Ingested API documentation."""

    name: str
    doc_type: APIDocType
    version: str | None = None
    base_url: str | None = None
    description: str | None = None
    endpoints: list[APIEndpoint] = field(default_factory=list)
    schemas: list[APISchema] = field(default_factory=list)
    security_schemes: dict[str, Any] = field(default_factory=dict)
    raw_content: str | None = None
    source_path: str | None = None
    source_url: str | None = None
    ingested_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "name": self.name,
            "doc_type": self.doc_type.value,
            "version": self.version,
            "base_url": self.base_url,
            "description": self.description,
            "endpoints": [e.to_dict() for e in self.endpoints],
            "schemas": [s.to_dict() for s in self.schemas],
            "security_schemes": self.security_schemes,
            "source_path": self.source_path,
            "source_url": self.source_url,
            "ingested_at": self.ingested_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "APIDocumentation":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            doc_type=APIDocType(data["doc_type"]),
            version=data.get("version"),
            base_url=data.get("base_url"),
            description=data.get("description"),
            endpoints=[APIEndpoint.from_dict(e) for e in data.get("endpoints", [])],
            schemas=[
                APISchema(
                    name=s["name"],
                    schema_type=s["schema_type"],
                    properties=s.get("properties", {}),
                    required=s.get("required", []),
                    description=s.get("description"),
                )
                for s in data.get("schemas", [])
            ],
            security_schemes=data.get("security_schemes", {}),
            source_path=data.get("source_path"),
            source_url=data.get("source_url"),
            ingested_at=datetime.fromisoformat(data["ingested_at"]),
        )

    def get_endpoint(self, path: str, method: str) -> APIEndpoint | None:
        """Get a specific endpoint."""
        method = method.upper()
        for endpoint in self.endpoints:
            if endpoint.path == path and endpoint.method.upper() == method:
                return endpoint
        return None

    def get_endpoints_by_tag(self, tag: str) -> list[APIEndpoint]:
        """Get all endpoints with a specific tag."""
        return [e for e in self.endpoints if tag in e.tags]

    def generate_summary(self) -> str:
        """Generate a human-readable summary."""
        lines = [
            f"# API: {self.name}",
            f"Type: {self.doc_type.value}",
        ]
        if self.version:
            lines.append(f"Version: {self.version}")
        if self.base_url:
            lines.append(f"Base URL: {self.base_url}")
        if self.description:
            lines.append(f"\n{self.description}")

        lines.append(f"\n## Endpoints ({len(self.endpoints)})")
        for endpoint in self.endpoints[:20]:  # First 20
            summary = endpoint.summary or endpoint.description or ""
            if len(summary) > 50:
                summary = summary[:47] + "..."
            lines.append(f"- {endpoint.method.upper()} {endpoint.path}: {summary}")

        if len(self.endpoints) > 20:
            lines.append(f"  ... and {len(self.endpoints) - 20} more")

        if self.schemas:
            lines.append(f"\n## Schemas ({len(self.schemas)})")
            for schema in self.schemas[:10]:
                lines.append(f"- {schema.name}")

        return "\n".join(lines)


class APIDocIngester:
    """Ingests API documentation from various sources."""

    def __init__(self, project_root: Path | None = None):
        """Initialize the ingester.

        Args:
            project_root: Root directory for the project.
        """
        self.project_root = project_root or Path.cwd()
        self.docs_dir = self.project_root / "api_docs"
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self._docs: dict[str, APIDocumentation] = {}
        self._load_stored_docs()

    def _load_stored_docs(self) -> None:
        """Load previously ingested documentation."""
        index_file = self.docs_dir / "index.json"
        if index_file.exists():
            try:
                data = json.loads(index_file.read_text())
                for name, doc_data in data.get("docs", {}).items():
                    self._docs[name] = APIDocumentation.from_dict(doc_data)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load API docs index: {e}")

    def _save_index(self) -> None:
        """Save the documentation index."""
        index_file = self.docs_dir / "index.json"
        data = {
            "docs": {name: doc.to_dict() for name, doc in self._docs.items()},
            "updated_at": datetime.now().isoformat(),
        }
        index_file.write_text(json.dumps(data, indent=2))

    def detect_doc_type(self, content: str, file_path: str | None = None) -> APIDocType:
        """Detect the type of API documentation.

        Args:
            content: The content to analyze.
            file_path: Optional file path for extension hints.

        Returns:
            Detected APIDocType.
        """
        # Check file extension first
        if file_path:
            ext = Path(file_path).suffix.lower()
            if ext == ".graphql":
                return APIDocType.GRAPHQL
            if ext == ".raml":
                return APIDocType.RAML
            if ext == ".md":
                return APIDocType.MARKDOWN
            if ext == ".html":
                return APIDocType.HTML

        # Try to parse as YAML/JSON
        try:
            if content.strip().startswith("{"):
                data = json.loads(content)
            else:
                data = yaml.safe_load(content)

            if isinstance(data, dict):
                # OpenAPI 3.x
                if data.get("openapi", "").startswith("3."):
                    return APIDocType.OPENAPI_3
                # Swagger 2.0
                if data.get("swagger") == "2.0":
                    return APIDocType.OPENAPI_2
                # AsyncAPI
                if "asyncapi" in data:
                    return APIDocType.ASYNCAPI

        except (json.JSONDecodeError, yaml.YAMLError):
            pass

        # GraphQL schema detection
        if re.search(r"type\s+\w+\s*\{", content) and re.search(r"(Query|Mutation|Subscription)", content):
            return APIDocType.GRAPHQL

        # RAML detection
        if content.strip().startswith("#%RAML"):
            return APIDocType.RAML

        # Markdown detection
        if re.search(r"^#+ ", content, re.MULTILINE):
            return APIDocType.MARKDOWN

        return APIDocType.PLAIN_TEXT

    def ingest_openapi(self, content: str, name: str, source: str | None = None) -> APIDocumentation:
        """Ingest OpenAPI/Swagger specification.

        Args:
            content: OpenAPI spec content (YAML or JSON).
            name: Name for this API.
            source: Source path or URL.

        Returns:
            Parsed APIDocumentation.
        """
        # Parse content
        if content.strip().startswith("{"):
            data = json.loads(content)
        else:
            data = yaml.safe_load(content)

        # Determine version
        is_openapi_3 = data.get("openapi", "").startswith("3.")
        doc_type = APIDocType.OPENAPI_3 if is_openapi_3 else APIDocType.OPENAPI_2

        # Extract info
        info = data.get("info", {})
        servers = data.get("servers", [])
        base_url = servers[0].get("url") if servers else data.get("host", "")

        # Extract endpoints
        endpoints: list[APIEndpoint] = []
        paths = data.get("paths", {})

        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            for method, details in methods.items():
                if method.startswith("x-") or method == "parameters":
                    continue
                if not isinstance(details, dict):
                    continue

                # Parameters
                params = details.get("parameters", [])
                # Include path-level parameters
                params.extend(methods.get("parameters", []))

                # Request body (OpenAPI 3)
                request_body = details.get("requestBody")

                # Responses
                responses = details.get("responses", {})

                endpoints.append(APIEndpoint(
                    path=path,
                    method=method.upper(),
                    summary=details.get("summary"),
                    description=details.get("description"),
                    parameters=params,
                    request_body=request_body,
                    responses=responses,
                    security=details.get("security", []),
                    tags=details.get("tags", []),
                ))

        # Extract schemas
        schemas: list[APISchema] = []
        components = data.get("components", data.get("definitions", {}))
        if isinstance(components, dict):
            schema_defs = components.get("schemas", components)
            if isinstance(schema_defs, dict):
                for schema_name, schema_def in schema_defs.items():
                    if isinstance(schema_def, dict):
                        schemas.append(APISchema(
                            name=schema_name,
                            schema_type=schema_def.get("type", "object"),
                            properties=schema_def.get("properties", {}),
                            required=schema_def.get("required", []),
                            description=schema_def.get("description"),
                        ))

        # Security schemes
        security_schemes = {}
        if is_openapi_3:
            security_schemes = components.get("securitySchemes", {}) if isinstance(components, dict) else {}
        else:
            security_schemes = data.get("securityDefinitions", {})

        doc = APIDocumentation(
            name=name,
            doc_type=doc_type,
            version=info.get("version"),
            base_url=base_url,
            description=info.get("description"),
            endpoints=endpoints,
            schemas=schemas,
            security_schemes=security_schemes,
            raw_content=content,
            source_path=source if source and not source.startswith("http") else None,
            source_url=source if source and source.startswith("http") else None,
        )

        # Store the doc
        self._docs[name] = doc
        self._save_index()

        logger.info(f"[API-DOCS] Ingested OpenAPI: {name} ({len(endpoints)} endpoints)")
        return doc

    def ingest_graphql(self, content: str, name: str, source: str | None = None) -> APIDocumentation:
        """Ingest GraphQL schema.

        Args:
            content: GraphQL schema content.
            name: Name for this API.
            source: Source path or URL.

        Returns:
            Parsed APIDocumentation.
        """
        # Basic GraphQL parsing (type definitions)
        endpoints: list[APIEndpoint] = []
        schemas: list[APISchema] = []

        # Find type definitions
        type_pattern = re.compile(r"type\s+(\w+)\s*\{([^}]+)\}", re.MULTILINE | re.DOTALL)
        for match in type_pattern.finditer(content):
            type_name = match.group(1)
            type_body = match.group(2)

            # Parse fields
            properties: dict[str, Any] = {}
            field_pattern = re.compile(r"(\w+)\s*(?:\([^)]*\))?\s*:\s*([^\n]+)")
            for field_match in field_pattern.finditer(type_body):
                field_name = field_match.group(1)
                field_type = field_match.group(2).strip()
                properties[field_name] = {"type": field_type}

            if type_name in ("Query", "Mutation", "Subscription"):
                # These are endpoints
                for field_name, field_info in properties.items():
                    endpoints.append(APIEndpoint(
                        path=f"/{type_name.lower()}/{field_name}",
                        method=type_name.upper(),
                        summary=field_name,
                        description=f"GraphQL {type_name}: {field_name}",
                    ))
            else:
                schemas.append(APISchema(
                    name=type_name,
                    schema_type="object",
                    properties=properties,
                ))

        doc = APIDocumentation(
            name=name,
            doc_type=APIDocType.GRAPHQL,
            description="GraphQL API",
            endpoints=endpoints,
            schemas=schemas,
            raw_content=content,
            source_path=source if source and not source.startswith("http") else None,
            source_url=source if source and source.startswith("http") else None,
        )

        # Store the doc
        self._docs[name] = doc
        self._save_index()

        logger.info(f"[API-DOCS] Ingested GraphQL: {name} ({len(endpoints)} operations)")
        return doc

    def ingest_from_file(self, file_path: Path | str, name: str | None = None) -> APIDocumentation:
        """Ingest API documentation from a file.

        Args:
            file_path: Path to the documentation file.
            name: Optional name (defaults to filename).

        Returns:
            Parsed APIDocumentation.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"API doc file not found: {file_path}")

        content = file_path.read_text()
        name = name or file_path.stem
        doc_type = self.detect_doc_type(content, str(file_path))

        if doc_type in (APIDocType.OPENAPI_3, APIDocType.OPENAPI_2):
            # ingest_openapi handles storage
            doc = self.ingest_openapi(content, name, str(file_path))
        elif doc_type == APIDocType.GRAPHQL:
            # ingest_graphql handles storage
            doc = self.ingest_graphql(content, name, str(file_path))
        else:
            # Store as plain text - must store manually
            doc = APIDocumentation(
                name=name,
                doc_type=doc_type,
                raw_content=content,
                source_path=str(file_path),
            )
            self._docs[name] = doc
            self._save_index()
            logger.info(f"[API-DOCS] Ingested {doc_type.value}: {name}")

        # Save the raw content as JSON file
        doc_file = self.docs_dir / f"{name}.json"
        doc_file.write_text(json.dumps(doc.to_dict(), indent=2))

        return doc

    async def ingest_from_url(self, url: str, name: str | None = None) -> APIDocumentation:
        """Ingest API documentation from a URL.

        Args:
            url: URL to fetch documentation from.
            name: Optional name (defaults to URL path).

        Returns:
            Parsed APIDocumentation.
        """
        import httpx

        parsed_url = urlparse(url)
        name = name or parsed_url.path.split("/")[-1] or parsed_url.netloc

        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            content = response.text

        doc_type = self.detect_doc_type(content)

        if doc_type in (APIDocType.OPENAPI_3, APIDocType.OPENAPI_2):
            # ingest_openapi handles storage
            doc = self.ingest_openapi(content, name, url)
        elif doc_type == APIDocType.GRAPHQL:
            # ingest_graphql handles storage
            doc = self.ingest_graphql(content, name, url)
        else:
            # Plain text/other - must store manually
            doc = APIDocumentation(
                name=name,
                doc_type=doc_type,
                raw_content=content,
                source_url=url,
            )
            self._docs[name] = doc
            self._save_index()
            logger.info(f"[API-DOCS] Ingested from URL {doc_type.value}: {name}")

        # Save the raw content as JSON file
        doc_file = self.docs_dir / f"{name}.json"
        doc_file.write_text(json.dumps(doc.to_dict(), indent=2))

        return doc

    def get_doc(self, name: str) -> APIDocumentation | None:
        """Get ingested documentation by name."""
        return self._docs.get(name)

    def list_docs(self) -> list[str]:
        """List all ingested documentation names."""
        return list(self._docs.keys())

    def get_all_endpoints(self) -> list[tuple[str, APIEndpoint]]:
        """Get all endpoints from all docs.

        Returns:
            List of (doc_name, endpoint) tuples.
        """
        endpoints = []
        for name, doc in self._docs.items():
            for endpoint in doc.endpoints:
                endpoints.append((name, endpoint))
        return endpoints

    def search_endpoints(self, query: str) -> list[tuple[str, APIEndpoint]]:
        """Search endpoints by path or description.

        Args:
            query: Search query.

        Returns:
            Matching (doc_name, endpoint) tuples.
        """
        query = query.lower()
        results = []
        for name, doc in self._docs.items():
            for endpoint in doc.endpoints:
                if (query in endpoint.path.lower() or
                    (endpoint.summary and query in endpoint.summary.lower()) or
                    (endpoint.description and query in endpoint.description.lower())):
                    results.append((name, endpoint))
        return results

    def generate_knowledge_entry(self, doc_name: str) -> str:
        """Generate a knowledge base entry for an API doc.

        Args:
            doc_name: Name of the documentation.

        Returns:
            Markdown content for knowledge base.
        """
        doc = self._docs.get(doc_name)
        if not doc:
            return ""

        lines = [
            f"---",
            f"title: API Documentation - {doc.name}",
            f"type: api_doc",
            f"doc_type: {doc.doc_type.value}",
            f"created: {doc.ingested_at.isoformat()}",
            f"---",
            "",
            doc.generate_summary(),
        ]

        return "\n".join(lines)


# Singleton instance
_api_ingester: APIDocIngester | None = None


def get_api_doc_ingester(project_root: Path | None = None) -> APIDocIngester:
    """Get the API doc ingester singleton."""
    global _api_ingester
    if _api_ingester is None:
        _api_ingester = APIDocIngester(project_root=project_root)
    return _api_ingester
