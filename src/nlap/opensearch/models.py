"""OpenSearch data models."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class ConnectionHealth(BaseModel):
    """OpenSearch connection health status."""

    healthy: bool = Field(..., description="Connection health status")
    cluster_name: Optional[str] = Field(default=None, description="Cluster name")
    version: Optional[str] = Field(default=None, description="OpenSearch version")
    error: Optional[str] = Field(default=None, description="Error message if unhealthy")


class QueryResult(BaseModel):
    """OpenSearch query result model."""

    hits: list[dict[str, Any]] = Field(default_factory=list, description="Search hits")
    total: int = Field(default=0, description="Total number of hits")
    took: int = Field(default=0, description="Query execution time in milliseconds")
    aggregations: Optional[dict[str, Any]] = Field(
        default=None, description="Aggregation results"
    )

