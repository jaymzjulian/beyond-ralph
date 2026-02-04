"""Tests for API Documentation Ingestion."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from beyond_ralph.core.api_docs import (
    APIDocIngester,
    APIDocType,
    APIDocumentation,
    APIEndpoint,
    APISchema,
    get_api_doc_ingester,
)


# Sample OpenAPI 3.0 spec
SAMPLE_OPENAPI_3 = """
openapi: "3.0.0"
info:
  title: "Pet Store API"
  version: "1.0.0"
  description: "A sample API for pets"
servers:
  - url: "https://api.petstore.com/v1"
paths:
  /pets:
    get:
      summary: "List all pets"
      tags:
        - pets
      responses:
        "200":
          description: "A list of pets"
    post:
      summary: "Create a pet"
      tags:
        - pets
      requestBody:
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/Pet"
      responses:
        "201":
          description: "Pet created"
  /pets/{petId}:
    get:
      summary: "Get a pet by ID"
      parameters:
        - name: petId
          in: path
          required: true
          schema:
            type: integer
      responses:
        "200":
          description: "A pet"
components:
  schemas:
    Pet:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
        status:
          type: string
      required:
        - id
        - name
  securitySchemes:
    api_key:
      type: apiKey
      name: X-API-Key
      in: header
"""

# Sample Swagger 2.0 spec
SAMPLE_SWAGGER_2 = """
{
  "swagger": "2.0",
  "info": {
    "title": "User API",
    "version": "2.0"
  },
  "host": "api.users.com",
  "paths": {
    "/users": {
      "get": {
        "summary": "List users",
        "responses": {
          "200": {
            "description": "Success"
          }
        }
      }
    }
  },
  "definitions": {
    "User": {
      "type": "object",
      "properties": {
        "id": {"type": "integer"},
        "email": {"type": "string"}
      }
    }
  }
}
"""

# Sample GraphQL schema
SAMPLE_GRAPHQL = """
type Query {
  users: [User]
  user(id: ID!): User
}

type Mutation {
  createUser(name: String!, email: String!): User
}

type User {
  id: ID!
  name: String!
  email: String!
  posts: [Post]
}

type Post {
  id: ID!
  title: String!
  content: String
}
"""


class TestAPIEndpoint:
    """Tests for APIEndpoint dataclass."""

    def test_endpoint_creation(self):
        """Test creating an endpoint."""
        endpoint = APIEndpoint(
            path="/users",
            method="GET",
            summary="List all users",
        )

        assert endpoint.path == "/users"
        assert endpoint.method == "GET"
        assert endpoint.summary == "List all users"

    def test_endpoint_to_dict(self):
        """Test serialization."""
        endpoint = APIEndpoint(
            path="/users/{id}",
            method="GET",
            summary="Get user",
            parameters=[{"name": "id", "in": "path"}],
            tags=["users"],
        )

        data = endpoint.to_dict()

        assert data["path"] == "/users/{id}"
        assert data["tags"] == ["users"]

    def test_endpoint_from_dict(self):
        """Test deserialization."""
        data = {
            "path": "/products",
            "method": "POST",
            "summary": "Create product",
            "parameters": [],
            "responses": {"201": {}},
            "tags": ["products"],
        }

        endpoint = APIEndpoint.from_dict(data)

        assert endpoint.path == "/products"
        assert endpoint.method == "POST"


class TestAPISchema:
    """Tests for APISchema dataclass."""

    def test_schema_creation(self):
        """Test creating a schema."""
        schema = APISchema(
            name="User",
            schema_type="object",
            properties={"id": {"type": "integer"}},
            required=["id"],
        )

        assert schema.name == "User"
        assert schema.schema_type == "object"

    def test_schema_to_dict(self):
        """Test serialization."""
        schema = APISchema(
            name="Product",
            schema_type="object",
            properties={"price": {"type": "number"}},
        )

        data = schema.to_dict()

        assert data["name"] == "Product"
        assert "price" in data["properties"]


class TestAPIDocumentation:
    """Tests for APIDocumentation dataclass."""

    def test_documentation_creation(self):
        """Test creating documentation."""
        doc = APIDocumentation(
            name="Test API",
            doc_type=APIDocType.OPENAPI_3,
            version="1.0.0",
            base_url="https://api.test.com",
        )

        assert doc.name == "Test API"
        assert doc.doc_type == APIDocType.OPENAPI_3

    def test_get_endpoint(self):
        """Test getting specific endpoint."""
        doc = APIDocumentation(
            name="Test",
            doc_type=APIDocType.OPENAPI_3,
            endpoints=[
                APIEndpoint(path="/users", method="GET", summary="List"),
                APIEndpoint(path="/users", method="POST", summary="Create"),
            ],
        )

        endpoint = doc.get_endpoint("/users", "GET")
        assert endpoint is not None
        assert endpoint.summary == "List"

        endpoint2 = doc.get_endpoint("/users", "post")  # Case insensitive
        assert endpoint2 is not None
        assert endpoint2.summary == "Create"

    def test_get_endpoint_not_found(self):
        """Test getting non-existent endpoint."""
        doc = APIDocumentation(name="Test", doc_type=APIDocType.OPENAPI_3)
        assert doc.get_endpoint("/missing", "GET") is None

    def test_get_endpoints_by_tag(self):
        """Test filtering endpoints by tag."""
        doc = APIDocumentation(
            name="Test",
            doc_type=APIDocType.OPENAPI_3,
            endpoints=[
                APIEndpoint(path="/users", method="GET", tags=["users"]),
                APIEndpoint(path="/products", method="GET", tags=["products"]),
                APIEndpoint(path="/users/{id}", method="GET", tags=["users"]),
            ],
        )

        user_endpoints = doc.get_endpoints_by_tag("users")
        assert len(user_endpoints) == 2

    def test_generate_summary(self):
        """Test generating summary."""
        doc = APIDocumentation(
            name="Test API",
            doc_type=APIDocType.OPENAPI_3,
            version="1.0",
            base_url="https://api.test.com",
            description="A test API",
            endpoints=[
                APIEndpoint(path="/users", method="GET", summary="List users"),
            ],
            schemas=[
                APISchema(name="User", schema_type="object"),
            ],
        )

        summary = doc.generate_summary()

        assert "Test API" in summary
        assert "1.0" in summary
        assert "GET /users" in summary
        assert "User" in summary

    def test_to_dict_from_dict(self):
        """Test round-trip serialization."""
        original = APIDocumentation(
            name="Round Trip",
            doc_type=APIDocType.OPENAPI_3,
            version="2.0",
            endpoints=[
                APIEndpoint(path="/test", method="GET"),
            ],
        )

        data = original.to_dict()
        restored = APIDocumentation.from_dict(data)

        assert restored.name == original.name
        assert restored.doc_type == original.doc_type
        assert len(restored.endpoints) == 1


class TestAPIDocIngester:
    """Tests for APIDocIngester."""

    @pytest.fixture
    def ingester(self, tmp_path):
        """Create an ingester for testing."""
        return APIDocIngester(project_root=tmp_path)

    def test_detect_openapi_3(self, ingester):
        """Test detecting OpenAPI 3.0."""
        doc_type = ingester.detect_doc_type(SAMPLE_OPENAPI_3)
        assert doc_type == APIDocType.OPENAPI_3

    def test_detect_swagger_2(self, ingester):
        """Test detecting Swagger 2.0."""
        doc_type = ingester.detect_doc_type(SAMPLE_SWAGGER_2)
        assert doc_type == APIDocType.OPENAPI_2

    def test_detect_graphql(self, ingester):
        """Test detecting GraphQL."""
        doc_type = ingester.detect_doc_type(SAMPLE_GRAPHQL)
        assert doc_type == APIDocType.GRAPHQL

    def test_detect_markdown(self, ingester):
        """Test detecting Markdown."""
        doc_type = ingester.detect_doc_type("# API Documentation\n\n## Endpoints\n")
        assert doc_type == APIDocType.MARKDOWN

    def test_detect_by_extension(self, ingester):
        """Test detecting by file extension."""
        assert ingester.detect_doc_type("content", "api.graphql") == APIDocType.GRAPHQL
        assert ingester.detect_doc_type("content", "api.md") == APIDocType.MARKDOWN
        assert ingester.detect_doc_type("content", "api.html") == APIDocType.HTML

    def test_ingest_openapi_3(self, ingester):
        """Test ingesting OpenAPI 3.0 spec."""
        doc = ingester.ingest_openapi(SAMPLE_OPENAPI_3, "petstore")

        assert doc.name == "petstore"
        assert doc.doc_type == APIDocType.OPENAPI_3
        assert doc.version == "1.0.0"
        assert doc.base_url == "https://api.petstore.com/v1"
        assert len(doc.endpoints) == 3
        assert len(doc.schemas) == 1
        assert "api_key" in doc.security_schemes

    def test_ingest_swagger_2(self, ingester):
        """Test ingesting Swagger 2.0 spec."""
        doc = ingester.ingest_openapi(SAMPLE_SWAGGER_2, "users")

        assert doc.name == "users"
        assert doc.doc_type == APIDocType.OPENAPI_2
        assert doc.version == "2.0"
        assert len(doc.endpoints) == 1
        assert len(doc.schemas) == 1

    def test_ingest_graphql(self, ingester):
        """Test ingesting GraphQL schema."""
        doc = ingester.ingest_graphql(SAMPLE_GRAPHQL, "graphql-api")

        assert doc.name == "graphql-api"
        assert doc.doc_type == APIDocType.GRAPHQL
        assert len(doc.endpoints) >= 3  # Query and Mutation operations
        assert len(doc.schemas) >= 2  # User and Post types

    def test_ingest_from_file(self, ingester, tmp_path):
        """Test ingesting from a file."""
        spec_file = tmp_path / "api.yaml"
        spec_file.write_text(SAMPLE_OPENAPI_3)

        doc = ingester.ingest_from_file(spec_file)

        assert doc.name == "api"
        assert doc.doc_type == APIDocType.OPENAPI_3

    def test_ingest_from_file_with_name(self, ingester, tmp_path):
        """Test ingesting from file with custom name."""
        spec_file = tmp_path / "spec.json"
        spec_file.write_text(SAMPLE_SWAGGER_2)

        doc = ingester.ingest_from_file(spec_file, name="custom-api")

        assert doc.name == "custom-api"

    def test_ingest_file_not_found(self, ingester, tmp_path):
        """Test error when file not found."""
        with pytest.raises(FileNotFoundError):
            ingester.ingest_from_file(tmp_path / "missing.yaml")

    def test_get_doc(self, ingester):
        """Test getting ingested documentation."""
        ingester.ingest_openapi(SAMPLE_OPENAPI_3, "test-api")

        doc = ingester.get_doc("test-api")
        assert doc is not None
        assert doc.name == "test-api"

    def test_get_doc_not_found(self, ingester):
        """Test getting non-existent documentation."""
        assert ingester.get_doc("missing") is None

    def test_list_docs(self, ingester):
        """Test listing all documentation."""
        ingester.ingest_openapi(SAMPLE_OPENAPI_3, "api1")
        ingester.ingest_openapi(SAMPLE_SWAGGER_2, "api2")

        docs = ingester.list_docs()

        assert "api1" in docs
        assert "api2" in docs

    def test_get_all_endpoints(self, ingester):
        """Test getting all endpoints from all docs."""
        ingester.ingest_openapi(SAMPLE_OPENAPI_3, "petstore")
        ingester.ingest_openapi(SAMPLE_SWAGGER_2, "users")

        endpoints = ingester.get_all_endpoints()

        assert len(endpoints) >= 4  # 3 from petstore + 1 from users
        # Each is (doc_name, endpoint) tuple
        assert all(isinstance(e, tuple) for e in endpoints)

    def test_search_endpoints(self, ingester):
        """Test searching endpoints."""
        ingester.ingest_openapi(SAMPLE_OPENAPI_3, "petstore")

        results = ingester.search_endpoints("pet")

        assert len(results) >= 1
        # Should find /pets endpoints
        paths = [e[1].path for e in results]
        assert any("/pets" in p for p in paths)

    def test_search_endpoints_by_summary(self, ingester):
        """Test searching by summary."""
        ingester.ingest_openapi(SAMPLE_OPENAPI_3, "petstore")

        results = ingester.search_endpoints("create")

        assert len(results) >= 1

    def test_generate_knowledge_entry(self, ingester):
        """Test generating knowledge entry."""
        ingester.ingest_openapi(SAMPLE_OPENAPI_3, "petstore")

        entry = ingester.generate_knowledge_entry("petstore")

        assert "API Documentation" in entry
        assert "petstore" in entry
        assert "openapi_3" in entry

    def test_generate_knowledge_entry_not_found(self, ingester):
        """Test generating entry for missing doc."""
        entry = ingester.generate_knowledge_entry("missing")
        assert entry == ""

    def test_state_persistence(self, tmp_path):
        """Test state persists across instances."""
        ingester1 = APIDocIngester(project_root=tmp_path)
        ingester1.ingest_openapi(SAMPLE_OPENAPI_3, "persistent-api")

        ingester2 = APIDocIngester(project_root=tmp_path)
        doc = ingester2.get_doc("persistent-api")

        assert doc is not None
        assert doc.name == "persistent-api"
        assert len(doc.endpoints) > 0


class TestAPIDocIngesterAsync:
    """Async tests for APIDocIngester."""

    @pytest.fixture
    def ingester(self, tmp_path):
        """Create an ingester for testing."""
        return APIDocIngester(project_root=tmp_path)

    @pytest.mark.asyncio
    async def test_ingest_from_url(self, ingester):
        """Test that ingest_from_url method exists."""
        # Full URL testing would require httpx_mock from pytest-httpx
        # For now, just verify the method exists and is async
        import inspect

        assert hasattr(ingester, "ingest_from_url")
        assert inspect.iscoroutinefunction(ingester.ingest_from_url)


class TestGetAPIDocIngester:
    """Tests for singleton getter."""

    def test_singleton_pattern(self, tmp_path, monkeypatch):
        """Test singleton pattern."""
        import beyond_ralph.core.api_docs as module

        module._api_ingester = None

        ingester1 = get_api_doc_ingester(tmp_path)
        ingester2 = get_api_doc_ingester(tmp_path)

        assert ingester1 is ingester2

        module._api_ingester = None
