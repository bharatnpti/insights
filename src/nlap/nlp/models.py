"""Data models for natural language query parsing."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class QueryIntentCategory(str, Enum):
    """Query intent categories."""

    CORRELATION = "correlation"
    TREND = "trend"
    DISTRIBUTION = "distribution"
    COMPARISON = "comparison"
    AGGREGATION = "aggregation"
    FILTER = "filter"
    SEARCH = "search"
    UNKNOWN = "unknown"


class FilterOperator(str, Enum):
    """Filter operators."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IN = "in"
    NOT_IN = "not_in"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    RANGE = "range"
    WILDCARD = "wildcard"
    REGEX = "regex"


class AggregationType(str, Enum):
    """Aggregation types."""

    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    PERCENTAGE = "percentage"
    TERMS = "terms"
    DATE_HISTOGRAM = "date_histogram"
    CORRELATION = "correlation"


class DateRange(BaseModel):
    """Date range specification."""

    start_date: Optional[datetime] = Field(default=None, description="Start date")
    end_date: Optional[datetime] = Field(default=None, description="End date")
    start_date_str: Optional[str] = Field(default=None, description="Original start date string")
    end_date_str: Optional[str] = Field(default=None, description="Original end date string")
    relative_period: Optional[str] = Field(
        default=None, description="Relative period (e.g., 'last 4 days', 'this month')"
    )
    is_relative: bool = Field(default=False, description="Whether the date range is relative")
    timezone: Optional[str] = Field(default=None, description="Timezone for date range")


class FilterCondition(BaseModel):
    """Single filter condition."""

    field: str = Field(..., description="Field name to filter on")
    operator: FilterOperator = Field(..., description="Filter operator")
    value: Any = Field(default=None, description="Filter value")
    nested_path: Optional[str] = Field(default=None, description="Nested field path if applicable")


class Filter(BaseModel):
    """Filter specification with multiple conditions."""

    conditions: list[FilterCondition] = Field(default_factory=list, description="Filter conditions")
    must: list[FilterCondition] = Field(default_factory=list, description="Must match conditions")
    should: list[FilterCondition] = Field(default_factory=list, description="Should match conditions")
    must_not: list[FilterCondition] = Field(
        default_factory=list, description="Must not match conditions"
    )


class Aggregation(BaseModel):
    """Aggregation specification."""

    type: AggregationType = Field(..., description="Aggregation type")
    field: Optional[str] = Field(default=None, description="Field to aggregate on")
    group_by: Optional[list[str]] = Field(default=None, description="Fields to group by")
    alias: Optional[str] = Field(default=None, description="Alias for aggregation result")
    buckets: Optional[int] = Field(default=None, description="Number of buckets for histogram aggregations")
    interval: Optional[str] = Field(default=None, description="Interval for date histogram")


class QueryIntent(BaseModel):
    """Query intent information."""

    category: QueryIntentCategory = Field(..., description="Intent category")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score (0-1)")
    description: Optional[str] = Field(default=None, description="Intent description")
    suggested_visualization: Optional[str] = Field(
        default=None, description="Suggested visualization type"
    )


class ParsedQuery(BaseModel):
    """Parsed natural language query."""

    original_query: str = Field(..., description="Original natural language query")
    index_names: list[str] = Field(default_factory=list, description="Target OpenSearch indices")
    date_range: Optional[DateRange] = Field(default=None, description="Date range filter")
    filters: Filter = Field(default_factory=Filter, description="Filter conditions")
    aggregations: list[Aggregation] = Field(default_factory=list, description="Aggregations to perform")
    fields: list[str] = Field(default_factory=list, description="Fields to retrieve")
    sort: Optional[dict[str, str]] = Field(
        default=None, description="Sort specification (field -> order)"
    )
    limit: Optional[int] = Field(default=None, description="Result limit")
    intent: QueryIntent = Field(default_factory=lambda: QueryIntent(category=QueryIntentCategory.UNKNOWN), description="Query intent")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall parsing confidence")
    entities: dict[str, Any] = Field(
        default_factory=dict, description="Extracted entities (field names, values, etc.)"
    )
    errors: list[str] = Field(default_factory=list, description="Parsing errors or warnings")

