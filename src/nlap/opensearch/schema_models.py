"""Schema discovery data models."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class FieldType(str, Enum):
    """OpenSearch field type enumeration."""

    TEXT = "text"
    KEYWORD = "keyword"
    NUMERIC = "numeric"  # Includes long, integer, short, byte, double, float
    DATE = "date"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    NESTED = "nested"
    GEO_POINT = "geo_point"
    IP = "ip"
    BINARY = "binary"
    UNKNOWN = "unknown"


class FieldInfo(BaseModel):
    """Information about a single field in the schema."""

    name: str = Field(..., description="Field name (full path for nested fields)")
    field_type: FieldType = Field(..., description="Detected field type")
    sample_values: list[Any] = Field(default_factory=list, description="Sample values from documents")
    is_array: bool = Field(default=False, description="Whether field is an array type")
    is_nested: bool = Field(default=False, description="Whether field is nested")
    description: Optional[str] = Field(default=None, description="Field description")


class SchemaInfo(BaseModel):
    """Complete schema information for an index."""

    index_name: str = Field(..., description="OpenSearch index name")
    fields: dict[str, FieldInfo] = Field(default_factory=dict, description="Field name to FieldInfo mapping")
    version: int = Field(default=1, description="Schema version number")
    discovered_at: datetime = Field(default_factory=datetime.utcnow, description="When schema was discovered")
    total_documents_analyzed: int = Field(default=0, description="Number of documents analyzed")
    sample_size: int = Field(default=0, description="Sample size used for discovery")


class CachedSchema(BaseModel):
    """Cached schema with metadata."""

    model_config = ConfigDict(populate_by_name=True)

    schema_info: SchemaInfo = Field(..., description="The schema information", alias="schema")
    cached_at: datetime = Field(default_factory=datetime.utcnow, description="When schema was cached")
    cache_key: str = Field(..., description="Cache key identifier")
    expires_at: Optional[datetime] = Field(default=None, description="Cache expiration time")

