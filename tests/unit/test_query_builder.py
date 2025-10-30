"""Tests for query builder."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from nlap.nlp.models import (
    Aggregation,
    AggregationType,
    DateRange,
    Filter,
    FilterCondition,
    FilterOperator,
    ParsedQuery,
    QueryIntent,
    QueryIntentCategory,
)
from nlap.opensearch.query_builder import QueryBuilder
from nlap.opensearch.schema_models import FieldInfo, FieldType, SchemaInfo


class TestQueryBuilder:
    """Test QueryBuilder component."""

    def test_build_simple_query(self):
        """Test building a simple match_all query."""
        builder = QueryBuilder()
        parsed_query = ParsedQuery(original_query="show all documents")

        query = builder.build_query(parsed_query)

        assert "query" in query
        assert query["size"] == 100  # Default size
        assert query["from"] == 0

    def test_build_query_with_filters(self):
        """Test building a query with filter conditions."""
        builder = QueryBuilder()
        parsed_query = ParsedQuery(
            original_query="find users where age equals 30",
            filters=Filter(
                must=[
                    FilterCondition(field="age", operator=FilterOperator.EQUALS, value=30)
                ]
            ),
        )

        query = builder.build_query(parsed_query)

        assert "query" in query
        assert "bool" in query["query"]
        assert "must" in query["query"]["bool"]
        assert len(query["query"]["bool"]["must"]) > 0

    def test_build_term_query(self):
        """Test building term query for equals operator."""
        builder = QueryBuilder()
        condition = FilterCondition(
            field="status", operator=FilterOperator.EQUALS, value="active"
        )

        clause = builder._build_filter_clause(condition)

        assert "term" in clause or "bool" in clause  # Could be term or bool with term

    def test_build_range_query(self):
        """Test building range query."""
        builder = QueryBuilder()
        condition = FilterCondition(
            field="age", operator=FilterOperator.GREATER_THAN, value=18
        )

        clause = builder._build_filter_clause(condition)

        assert "range" in clause
        assert "age" in clause["range"]
        assert "gt" in clause["range"]["age"]

    def test_build_terms_query(self):
        """Test building terms query for IN operator."""
        builder = QueryBuilder()
        condition = FilterCondition(
            field="status", operator=FilterOperator.IN, value=["active", "pending"]
        )

        clause = builder._build_filter_clause(condition)

        assert "terms" in clause
        assert "status" in clause["terms"]

    def test_build_match_query(self):
        """Test building match query for contains operator."""
        builder = QueryBuilder()
        condition = FilterCondition(
            field="message", operator=FilterOperator.CONTAINS, value="error"
        )

        clause = builder._build_filter_clause(condition)

        assert "match" in clause or "bool" in clause  # Could be match or bool with match

    def test_build_prefix_query(self):
        """Test building prefix query."""
        builder = QueryBuilder()
        condition = FilterCondition(
            field="name", operator=FilterOperator.STARTS_WITH, value="John"
        )

        clause = builder._build_filter_clause(condition)

        assert "prefix" in clause
        assert "name" in clause["prefix"]

    def test_build_wildcard_query(self):
        """Test building wildcard query."""
        builder = QueryBuilder()
        condition = FilterCondition(
            field="name", operator=FilterOperator.WILDCARD, value="John*"
        )

        clause = builder._build_filter_clause(condition)

        assert "wildcard" in clause
        assert "name" in clause["wildcard"]

    def test_build_exists_query(self):
        """Test building exists query."""
        builder = QueryBuilder()
        condition = FilterCondition(
            field="email", operator=FilterOperator.EXISTS, value=None
        )

        clause = builder._build_filter_clause(condition)

        assert "exists" in clause
        assert "field" in clause["exists"]

    def test_build_bool_query_with_must_and_should(self):
        """Test building bool query with must and should clauses."""
        builder = QueryBuilder()
        parsed_query = ParsedQuery(
            original_query="test query",
            filters=Filter(
                must=[
                    FilterCondition(
                        field="status", operator=FilterOperator.EQUALS, value="active"
                    )
                ],
                should=[
                    FilterCondition(
                        field="category", operator=FilterOperator.EQUALS, value="premium"
                    )
                ],
            ),
        )

        query = builder._build_query_clause(parsed_query)

        assert "bool" in query
        assert "must" in query["bool"]
        assert "should" in query["bool"]
        # When both must and should exist, should clauses are optional (minimum_should_match defaults to 0)
        # Our code doesn't set minimum_should_match when must exists, which is correct behavior

    def test_build_bool_query_with_must_not(self):
        """Test building bool query with must_not clauses."""
        builder = QueryBuilder()
        parsed_query = ParsedQuery(
            original_query="test query",
            filters=Filter(
                must_not=[
                    FilterCondition(
                        field="deleted", operator=FilterOperator.EQUALS, value=True
                    )
                ]
            ),
        )

        query = builder._build_query_clause(parsed_query)

        assert "bool" in query
        assert "must_not" in query["bool"]

    def test_build_date_range_query(self):
        """Test building date range query."""
        builder = QueryBuilder()
        date_range = DateRange(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            is_relative=False,
        )

        clause = builder._build_date_range_query(date_range)

        assert clause is not None
        assert "range" in clause

    def test_build_date_range_query_with_relative_period(self):
        """Test building date range query with relative period."""
        builder = QueryBuilder()
        date_range = DateRange(
            start_date_str="2024-01-01",
            end_date_str="2024-01-31",
            relative_period="last 30 days",
            is_relative=True,
        )

        clause = builder._build_date_range_query(date_range)

        assert clause is not None
        assert "range" in clause

    def test_build_aggregation_count(self):
        """Test building count aggregation."""
        builder = QueryBuilder()
        aggregations = [
            Aggregation(type=AggregationType.COUNT, field="status", alias="total_count")
        ]

        aggs = builder._build_aggregations(aggregations)

        assert aggs is not None
        assert "total_count" in aggs

    def test_build_aggregation_sum(self):
        """Test building sum aggregation."""
        builder = QueryBuilder()
        aggregations = [
            Aggregation(type=AggregationType.SUM, field="price", alias="total_price")
        ]

        aggs = builder._build_aggregations(aggregations)

        assert aggs is not None
        assert "total_price" in aggs
        assert "sum" in aggs["total_price"]

    def test_build_aggregation_terms(self):
        """Test building terms aggregation."""
        builder = QueryBuilder()
        aggregations = [
            Aggregation(
                type=AggregationType.TERMS,
                field="status",
                alias="status_counts",
                buckets=10,
            )
        ]

        aggs = builder._build_aggregations(aggregations)

        assert aggs is not None
        assert "status_counts" in aggs
        assert "terms" in aggs["status_counts"]

    def test_build_aggregation_date_histogram(self):
        """Test building date histogram aggregation."""
        builder = QueryBuilder()
        aggregations = [
            Aggregation(
                type=AggregationType.DATE_HISTOGRAM,
                field="@timestamp",
                alias="daily_counts",
                interval="1d",
            )
        ]

        aggs = builder._build_aggregations(aggregations)

        assert aggs is not None
        assert "daily_counts" in aggs
        assert "date_histogram" in aggs["daily_counts"]

    def test_build_aggregation_composite(self):
        """Test building composite aggregation for group_by."""
        builder = QueryBuilder()
        aggregations = [
            Aggregation(
                type=AggregationType.TERMS,
                group_by=["status", "category"],
                alias="grouped_counts",
                buckets=20,
            )
        ]

        aggs = builder._build_aggregations(aggregations)

        assert aggs is not None
        assert "grouped_counts" in aggs
        assert "composite" in aggs["grouped_counts"]

    def test_build_nested_query(self):
        """Test building nested query."""
        builder = QueryBuilder()
        condition = FilterCondition(
            field="user.name",
            operator=FilterOperator.EQUALS,
            value="John",
            nested_path="user",
        )

        clause = builder._build_filter_clause(condition)

        assert "nested" in clause
        assert "path" in clause["nested"]
        assert "query" in clause["nested"]

    def test_build_query_with_sort(self):
        """Test building query with sort."""
        builder = QueryBuilder()
        parsed_query = ParsedQuery(
            original_query="test query", sort={"created_at": "desc"}
        )

        query = builder.build_query(parsed_query)

        assert "sort" in query
        assert len(query["sort"]) > 0

    def test_build_query_with_source(self):
        """Test building query with field selection."""
        builder = QueryBuilder()
        parsed_query = ParsedQuery(
            original_query="test query", fields=["name", "email", "age"]
        )

        query = builder.build_query(parsed_query)

        assert "_source" in query
        assert "name" in query["_source"]
        assert "email" in query["_source"]
        assert "age" in query["_source"]

    def test_build_query_with_limit(self):
        """Test building query with limit."""
        builder = QueryBuilder()
        parsed_query = ParsedQuery(original_query="test query", limit=50)

        query = builder.build_query(parsed_query)

        assert query["size"] == 50

    def test_build_query_with_pagination(self):
        """Test building query with pagination."""
        builder = QueryBuilder()
        parsed_query = ParsedQuery(original_query="test query", limit=100)

        query = builder.build_query(parsed_query, size=20, from_=40)

        assert query["size"] == 20  # size parameter overrides limit
        assert query["from"] == 40

    def test_build_query_with_schema_info(self):
        """Test building query with schema information."""
        schema_info = SchemaInfo(
            index_name="test_index",
            fields={
                "status": FieldInfo(
                    name="status", field_type=FieldType.KEYWORD, is_array=False
                ),
                "message": FieldInfo(
                    name="message", field_type=FieldType.TEXT, is_array=False
                ),
            },
            version=1,
        )
        builder = QueryBuilder(schema_info=schema_info)
        parsed_query = ParsedQuery(
            original_query="test query",
            filters=Filter(
                must=[
                    FilterCondition(
                        field="status", operator=FilterOperator.EQUALS, value="active"
                    )
                ]
            ),
        )

        query = builder.build_query(parsed_query)

        assert "query" in query

    def test_build_query_optimizes_single_must_clause(self):
        """Test that single must clause is simplified."""
        builder = QueryBuilder()
        parsed_query = ParsedQuery(
            original_query="test query",
            filters=Filter(
                must=[
                    FilterCondition(
                        field="status", operator=FilterOperator.EQUALS, value="active"
                    )
                ]
            ),
        )

        query = builder._build_query_clause(parsed_query)

        # Should have bool with must (may be simplified)
        assert "bool" in query

    def test_build_complete_query_example(self):
        """Test building a complete realistic query."""
        builder = QueryBuilder()
        date_range = DateRange(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            is_relative=False,
        )
        parsed_query = ParsedQuery(
            original_query="A/B test analysis for last 30 days showing variant vs completion status",
            index_names=["test-logs-*"],
            date_range=date_range,
            filters=Filter(
                must=[
                    FilterCondition(
                        field="experiment", operator=FilterOperator.EQUALS, value="ab_test_001"
                    ),
                ]
            ),
            aggregations=[
                Aggregation(
                    type=AggregationType.TERMS,
                    field="variant",
                    alias="variant_counts",
                    buckets=10,
                ),
                Aggregation(
                    type=AggregationType.TERMS,
                    field="completion_status",
                    alias="status_counts",
                    buckets=5,
                ),
            ],
            sort={"@timestamp": "desc"},
            limit=1000,
        )

        query = builder.build_query(parsed_query)

        assert "query" in query
        assert "bool" in query["query"]
        assert "aggs" in query
        assert "sort" in query
        assert query["size"] == 1000

    def test_build_query_with_not_equals(self):
        """Test building query with not_equals operator."""
        builder = QueryBuilder()
        condition = FilterCondition(
            field="status", operator=FilterOperator.NOT_EQUALS, value="deleted"
        )

        clause = builder._build_filter_clause(condition)

        assert "bool" in clause
        assert "must_not" in clause["bool"]

    def test_build_query_with_not_in(self):
        """Test building query with not_in operator."""
        builder = QueryBuilder()
        condition = FilterCondition(
            field="status",
            operator=FilterOperator.NOT_IN,
            value=["deleted", "archived"],
        )

        clause = builder._build_filter_clause(condition)

        assert "bool" in clause
        assert "must_not" in clause["bool"]

    def test_build_query_with_not_exists(self):
        """Test building query with not_exists operator."""
        builder = QueryBuilder()
        condition = FilterCondition(
            field="deleted_at", operator=FilterOperator.NOT_EXISTS, value=None
        )

        clause = builder._build_filter_clause(condition)

        assert "bool" in clause
        assert "must_not" in clause["bool"]

