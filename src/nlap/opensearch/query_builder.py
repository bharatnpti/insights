"""OpenSearch query builder that converts parsed natural language queries to OpenSearch queries."""

from datetime import datetime
from typing import Any, Optional

from nlap.nlp.models import (
    Aggregation,
    AggregationType,
    DateRange,
    FilterCondition,
    FilterOperator,
    ParsedQuery,
)
from nlap.opensearch.schema_models import FieldInfo, FieldType, SchemaInfo
from nlap.utils.logger import get_logger

logger = get_logger(__name__)


class QueryBuilder:
    """Build OpenSearch queries from parsed natural language queries."""

    # Default date format for OpenSearch
    DEFAULT_DATE_FORMAT = "strict_date_optional_time||epoch_millis"
    
    # Default page size
    DEFAULT_SIZE = 100
    MAX_SIZE = 10000

    def __init__(self, schema_info: Optional[SchemaInfo] = None):
        """Initialize query builder.

        Args:
            schema_info: Optional schema information for field type optimization
        """
        self.schema_info = schema_info

    def build_query(
        self,
        parsed_query: ParsedQuery,
        size: Optional[int] = None,
        from_: int = 0,
    ) -> dict[str, Any]:
        """Build complete OpenSearch query from parsed query.

        Args:
            parsed_query: Parsed natural language query
            size: Number of results to return (overrides parsed_query.limit)
            from_: Starting offset for pagination

        Returns:
            Complete OpenSearch query dictionary with query, size, from, sort, _source, aggs
        """
        # Build the query clause
        query_clause = self._build_query_clause(parsed_query)

        # Determine size
        result_size = size if size is not None else parsed_query.limit or self.DEFAULT_SIZE
        result_size = min(result_size, self.MAX_SIZE)

        # Build sort
        sort_clause = self._build_sort(parsed_query.sort)

        # Build _source (field selection)
        source_clause = self._build_source(parsed_query.fields)

        # Build aggregations
        aggs_clause = self._build_aggregations(parsed_query.aggregations, schema_info=self.schema_info)

        # Assemble complete query
        query = {
            "query": query_clause,
            "size": result_size,
            "from": from_,
        }

        if sort_clause:
            query["sort"] = sort_clause

        if source_clause:
            query["_source"] = source_clause

        if aggs_clause:
            query["aggs"] = aggs_clause

        logger.debug(
            "Query built successfully",
            query_size=result_size,
            has_aggs=bool(aggs_clause),
            has_sort=bool(sort_clause),
        )

        return query

    def _build_query_clause(self, parsed_query: ParsedQuery) -> dict[str, Any]:
        """Build the main query clause from parsed query.

        Args:
            parsed_query: Parsed query

        Returns:
            OpenSearch query clause (bool query, match_all, etc.)
        """
        # Collect all query clauses
        must_clauses = []
        should_clauses = []
        must_not_clauses = []

        # Check if user explicitly wants istio-proxy logs
        wants_istio_logs = False
        all_conditions = (
            parsed_query.filters.must +
            parsed_query.filters.should +
            parsed_query.filters.must_not +
            (parsed_query.filters.conditions or [])
        )
        
        for condition in all_conditions:
            # Check if user is filtering for istio-proxy
            if condition.field in ("k8s_container", "container") and condition.operator == FilterOperator.EQUALS:
                if condition.value == "istio-proxy" or str(condition.value).lower() == "istio-proxy":
                    wants_istio_logs = True
                    break

        # Automatically exclude istio-proxy logs unless explicitly requested
        if not wants_istio_logs:
            # Exclude istio-proxy container logs (these are infrastructure proxy logs, not application events)
            must_not_clauses.append({
                "term": {"k8s_container.keyword": "istio-proxy"}
            })

        # Add date range filter if present
        if parsed_query.date_range:
            date_clause = self._build_date_range_query(parsed_query.date_range)
            if date_clause:
                must_clauses.append(date_clause)

        # Add filter conditions
        if parsed_query.filters.must:
            for condition in parsed_query.filters.must:
                clause = self._build_filter_clause(condition)
                if clause:
                    must_clauses.append(clause)

        if parsed_query.filters.should:
            for condition in parsed_query.filters.should:
                clause = self._build_filter_clause(condition)
                if clause:
                    should_clauses.append(clause)

        if parsed_query.filters.must_not:
            for condition in parsed_query.filters.must_not:
                clause = self._build_filter_clause(condition)
                if clause:
                    must_not_clauses.append(clause)

        # Also process general conditions list if present
        if parsed_query.filters.conditions:
            for condition in parsed_query.filters.conditions:
                # Skip if already processed in must/should/must_not
                if condition not in parsed_query.filters.must:
                    clause = self._build_filter_clause(condition)
                    if clause:
                        must_clauses.append(clause)

        # Build bool query if we have any clauses
        if must_clauses or should_clauses or must_not_clauses:
            bool_query: dict[str, Any] = {}

            if must_clauses:
                # Optimize: if only one must clause, we can simplify
                if len(must_clauses) == 1:
                    bool_query["must"] = must_clauses[0]
                else:
                    bool_query["must"] = must_clauses

            if should_clauses:
                bool_query["should"] = should_clauses
                # At least one should clause must match if there are no must clauses
                if not must_clauses:
                    bool_query["minimum_should_match"] = 1

            if must_not_clauses:
                bool_query["must_not"] = must_not_clauses

            return {"bool": bool_query}

        # Default: match_all if no filters
        return {"match_all": {}}

    def _build_filter_clause(self, condition: FilterCondition) -> Optional[dict[str, Any]]:
        """Build OpenSearch query clause from filter condition.

        Args:
            condition: Filter condition

        Returns:
            OpenSearch query clause or None if invalid
        """
        if not condition.field:
            logger.warning("Filter condition missing field", condition=condition)
            return None

        field_name = condition.field
        operator = condition.operator
        value = condition.value

        # Handle nested fields
        if condition.nested_path:
            return self._build_nested_query(condition)

        # Get field type for optimization
        field_type = self._get_field_type(field_name)

        # Build clause based on operator
        if operator == FilterOperator.EQUALS:
            return self._build_term_query(field_name, value, field_type)

        elif operator == FilterOperator.NOT_EQUALS:
            return {"bool": {"must_not": [self._build_term_query(field_name, value, field_type)]}}

        elif operator == FilterOperator.GREATER_THAN:
            return self._build_range_query(field_name, gt=value)

        elif operator == FilterOperator.GREATER_THAN_OR_EQUAL:
            return self._build_range_query(field_name, gte=value)

        elif operator == FilterOperator.LESS_THAN:
            return self._build_range_query(field_name, lt=value)

        elif operator == FilterOperator.LESS_THAN_OR_EQUAL:
            return self._build_range_query(field_name, lte=value)

        elif operator == FilterOperator.CONTAINS:
            return self._build_match_query(field_name, value, field_type)

        elif operator == FilterOperator.NOT_CONTAINS:
            return {"bool": {"must_not": [self._build_match_query(field_name, value, field_type)]}}

        elif operator == FilterOperator.STARTS_WITH:
            return self._build_prefix_query(field_name, value)

        elif operator == FilterOperator.ENDS_WITH:
            return self._build_wildcard_query(field_name, f"*{value}")

        elif operator == FilterOperator.IN:
            return self._build_terms_query(field_name, value)

        elif operator == FilterOperator.NOT_IN:
            return {"bool": {"must_not": [self._build_terms_query(field_name, value)]}}

        elif operator == FilterOperator.EXISTS:
            return {"exists": {"field": field_name}}

        elif operator == FilterOperator.NOT_EXISTS:
            return {"bool": {"must_not": [{"exists": {"field": field_name}}]}}

        elif operator == FilterOperator.RANGE:
            return self._build_range_query(field_name, **value if isinstance(value, dict) else {})

        elif operator == FilterOperator.WILDCARD:
            return self._build_wildcard_query(field_name, value)

        elif operator == FilterOperator.REGEX:
            return self._build_regexp_query(field_name, value)

        else:
            logger.warning(
                "Unknown filter operator, defaulting to term query",
                operator=operator,
                field=field_name,
            )
            return self._build_term_query(field_name, value, field_type)

    def _build_term_query(
        self, field_name: str, value: Any, field_type: Optional[FieldType] = None
    ) -> dict[str, Any]:
        """Build term query (exact match).

        Args:
            field_name: Field name
            value: Value to match
            field_type: Optional field type for optimization

        Returns:
            Term query clause
        """
        # For text fields, prefer match query
        if field_type == FieldType.TEXT:
            return {"match": {field_name: value}}

        # For keyword, numeric, boolean, date fields, use term query
        return {"term": {field_name: value}}

    def _build_terms_query(self, field_name: str, values: Any) -> dict[str, Any]:
        """Build terms query (multiple exact matches).

        Args:
            field_name: Field name
            values: List of values or single value

        Returns:
            Terms query clause
        """
        # Ensure values is a list
        if not isinstance(values, list):
            values = [values]

        return {"terms": {field_name: values}}

    def _build_match_query(
        self, field_name: str, value: Any, field_type: Optional[FieldType] = None
    ) -> dict[str, Any]:
        """Build match query (full-text search).

        Args:
            field_name: Field name
            value: Value to match
            field_type: Optional field type

        Returns:
            Match query clause
        """
        return {"match": {field_name: value}}

    def _build_range_query(
        self,
        field_name: str,
        gt: Any = None,
        gte: Any = None,
        lt: Any = None,
        lte: Any = None,
    ) -> dict[str, Any]:
        """Build range query.

        Args:
            field_name: Field name
            gt: Greater than value
            gte: Greater than or equal value
            lt: Less than value
            lte: Less than or equal value

        Returns:
            Range query clause
        """
        range_params: dict[str, Any] = {}

        if gt is not None:
            range_params["gt"] = gt
        if gte is not None:
            range_params["gte"] = gte
        if lt is not None:
            range_params["lt"] = lt
        if lte is not None:
            range_params["lte"] = lte

        if not range_params:
            logger.warning("Range query with no parameters", field=field_name)
            return {"match_all": {}}

        return {"range": {field_name: range_params}}

    def _build_prefix_query(self, field_name: str, value: str) -> dict[str, Any]:
        """Build prefix query.

        Args:
            field_name: Field name
            value: Prefix value

        Returns:
            Prefix query clause
        """
        return {"prefix": {field_name: value}}

    def _build_wildcard_query(self, field_name: str, pattern: str) -> dict[str, Any]:
        """Build wildcard query.

        Args:
            field_name: Field name
            pattern: Wildcard pattern

        Returns:
            Wildcard query clause
        """
        return {"wildcard": {field_name: pattern}}

    def _build_regexp_query(self, field_name: str, pattern: str) -> dict[str, Any]:
        """Build regexp query.

        Args:
            field_name: Field name
            pattern: Regex pattern

        Returns:
            Regexp query clause
        """
        return {"regexp": {field_name: pattern}}

    def _build_date_range_query(self, date_range: DateRange) -> Optional[dict[str, Any]]:
        """Build date range query from DateRange object.

        Args:
            date_range: Date range specification

        Returns:
            Range query clause for date field or None if no dates
        """
        # Always prefer @timestamp as it's the standard OpenSearch timestamp field
        # Even if schema identifies it as a different type, @timestamp is always
        # the primary timestamp field in OpenSearch
        date_field = "@timestamp"
        
        # Only use alternative if @timestamp doesn't exist in schema AND we find another date field
        if self.schema_info:
            if "@timestamp" not in self.schema_info.fields:
                # @timestamp not found, try to find another date field
                alternative = self._find_date_field()
                if alternative:
                    date_field = alternative

        # Format dates as ISO strings
        start_value = None
        end_value = None

        if date_range.start_date:
            start_value = date_range.start_date.isoformat()
        elif date_range.start_date_str:
            start_value = date_range.start_date_str

        if date_range.end_date:
            end_value = date_range.end_date.isoformat()
        elif date_range.end_date_str:
            end_value = date_range.end_date_str

        # If we have at least one date, build range query
        if start_value or end_value:
            range_params: dict[str, Any] = {}
            if start_value:
                range_params["gte"] = start_value
            if end_value:
                range_params["lte"] = end_value

            return {"range": {date_field: range_params}}

        return None

    def _build_nested_query(self, condition: FilterCondition) -> dict[str, Any]:
        """Build nested query for nested fields.

        Args:
            condition: Filter condition with nested_path

        Returns:
            Nested query clause
        """
        nested_path = condition.nested_path or condition.field.split(".")[0]

        # Build inner query without nested path prefix
        inner_field = condition.field.replace(f"{nested_path}.", "") if "." in condition.field else condition.field

        inner_condition = FilterCondition(
            field=inner_field,
            operator=condition.operator,
            value=condition.value,
        )

        inner_clause = self._build_filter_clause(inner_condition)

        return {
            "nested": {
                "path": nested_path,
                "query": inner_clause or {"match_all": {}},
            }
        }

    def _build_aggregations(
        self,
        aggregations: list[Aggregation],
        schema_info: Optional[SchemaInfo] = None,
    ) -> Optional[dict[str, Any]]:
        """Build OpenSearch aggregations from aggregation list.

        Args:
            aggregations: List of aggregations
            schema_info: Optional schema information

        Returns:
            Aggregations dictionary or None
        """
        if not aggregations:
            return None

        aggs: dict[str, Any] = {}

        for agg in aggregations:
            agg_name = agg.alias or f"{agg.type}_{agg.field or 'all'}"

            if agg.type == AggregationType.COUNT:
                if agg.field:
                    # Count specific field (non-null values)
                    aggs[agg_name] = {
                        "filter": {"exists": {"field": agg.field}},
                        "aggs": {"count": {"value_count": {"field": agg.field}}},
                    }
                else:
                    # Total count
                    aggs[agg_name] = {"value_count": {"field": "_id"}}

            elif agg.type == AggregationType.SUM:
                if agg.field:
                    aggs[agg_name] = {"sum": {"field": agg.field}}
                else:
                    logger.warning("Sum aggregation requires field", aggregation=agg)
                    continue

            elif agg.type == AggregationType.AVG:
                if agg.field:
                    aggs[agg_name] = {"avg": {"field": agg.field}}
                else:
                    logger.warning("Avg aggregation requires field", aggregation=agg)
                    continue

            elif agg.type == AggregationType.MIN:
                if agg.field:
                    aggs[agg_name] = {"min": {"field": agg.field}}
                else:
                    logger.warning("Min aggregation requires field", aggregation=agg)
                    continue

            elif agg.type == AggregationType.MAX:
                if agg.field:
                    aggs[agg_name] = {"max": {"field": agg.field}}
                else:
                    logger.warning("Max aggregation requires field", aggregation=agg)
                    continue

            elif agg.type == AggregationType.TERMS:
                if agg.field:
                    terms_agg: dict[str, Any] = {"terms": {"field": agg.field}}
                    if agg.buckets:
                        terms_agg["terms"]["size"] = agg.buckets
                    aggs[agg_name] = terms_agg
                elif agg.group_by:
                    # Multiple group_by fields - use composite aggregation
                    aggs[agg_name] = {
                        "composite": {
                            "sources": [
                                {"agg_" + str(i): {"terms": {"field": field}}}
                                for i, field in enumerate(agg.group_by)
                            ],
                            "size": agg.buckets or 100,
                        }
                    }
                else:
                    logger.warning("Terms aggregation requires field or group_by", aggregation=agg)
                    continue

            elif agg.type == AggregationType.DATE_HISTOGRAM:
                if agg.field:
                    date_agg: dict[str, Any] = {
                        "date_histogram": {
                            "field": agg.field,
                            "calendar_interval": agg.interval or "1d",
                        }
                    }
                    if agg.buckets:
                        date_agg["date_histogram"]["min_doc_count"] = 1
                    aggs[agg_name] = date_agg
                else:
                    # Try to find date field
                    date_field = self._find_date_field(schema_info)
                    if date_field:
                        aggs[agg_name] = {
                            "date_histogram": {
                                "field": date_field,
                                "calendar_interval": agg.interval or "1d",
                            }
                        }
                    else:
                        logger.warning("Date histogram requires field or date field in schema", aggregation=agg)
                        continue

            elif agg.type == AggregationType.PERCENTAGE:
                # Percentage aggregation needs a base (total) - this is complex
                # For now, use filter aggregation and calculate count
                if agg.field:
                    aggs[agg_name] = {
                        "filter": {"exists": {"field": agg.field}},
                        "aggs": {
                            "count": {"value_count": {"field": agg.field}},
                        },
                    }
                else:
                    logger.warning("Percentage aggregation requires field", aggregation=agg)
                    continue

            elif agg.type == AggregationType.CORRELATION:
                # Correlation is complex - requires multiple fields
                # For now, return terms aggregation with both fields
                if agg.group_by and len(agg.group_by) >= 2:
                    aggs[agg_name] = {
                        "composite": {
                            "sources": [
                                {"field_" + str(i): {"terms": {"field": field}}}
                                for i, field in enumerate(agg.group_by[:2])
                            ],
                            "size": agg.buckets or 100,
                        }
                    }
                else:
                    logger.warning("Correlation aggregation requires at least 2 group_by fields", aggregation=agg)

        return aggs if aggs else None

    def _build_sort(self, sort_spec: Optional[dict[str, str]]) -> Optional[list[dict[str, Any]]]:
        """Build sort clause from sort specification.

        Args:
            sort_spec: Sort specification (field -> order)

        Returns:
            Sort clause list or None
        """
        if not sort_spec:
            return None

        sort_clauses = []
        for field, order in sort_spec.items():
            sort_clauses.append({field: {"order": order.lower()}})

        return sort_clauses if sort_clauses else None

    def _build_source(self, fields: list[str]) -> Optional[list[str]]:
        """Build _source clause from fields list.

        Args:
            fields: List of fields to retrieve

        Returns:
            _source clause or None (None means return all fields)
        """
        if not fields:
            return None

        return fields

    def _get_field_type(self, field_name: str) -> Optional[FieldType]:
        """Get field type from schema if available.

        Args:
            field_name: Field name

        Returns:
            FieldType or None if not found
        """
        if not self.schema_info:
            return None

        field_info = self.schema_info.fields.get(field_name)
        if field_info:
            return field_info.field_type

        return None

    def _find_date_field(self, schema_info: Optional[SchemaInfo] = None) -> Optional[str]:
        """Find a date field in the schema.

        Args:
            schema_info: Optional schema info (uses instance schema if not provided)

        Returns:
            Date field name or None
        """
        effective_schema = schema_info or self.schema_info
        if not effective_schema:
            return None

        # Look for common date field names first
        common_date_fields = ["@timestamp", "timestamp", "date", "created_at", "updated_at", "time"]
        for field_name in common_date_fields:
            if field_name in effective_schema.fields:
                field_info = effective_schema.fields[field_name]
                if field_info.field_type == FieldType.DATE:
                    return field_name

        # Search all fields for date type
        for field_name, field_info in effective_schema.fields.items():
            if field_info.field_type == FieldType.DATE:
                return field_name

        return None

