"""Main natural language parser using Azure OpenAI."""

import json
from typing import Any, Optional

from nlap.azureopenai.client import AzureOpenAIClient
from nlap.nlp.date_parser import DateRangeParser
from nlap.nlp.entity_extractor import EntityExtractor
from nlap.nlp.intent_classifier import IntentClassifier
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
from nlap.opensearch.schema_models import SchemaInfo
from nlap.utils.logger import get_logger

logger = get_logger(__name__)


class NaturalLanguageParser:
    """Parse natural language queries into structured query intentions using Azure OpenAI."""

    SYSTEM_PROMPT = """You are an expert natural language query parser for OpenSearch.
Your task is to parse natural language queries into structured JSON format that can be used to build OpenSearch queries.

You should extract:
1. Target index names (if mentioned)
2. Date ranges (e.g., "last 4 days", "October 27-30", "yesterday")
3. Filter conditions (field, operator, value)
4. Aggregations (count, sum, avg, group by, etc.)
5. Fields to retrieve
6. Sort order
7. Result limit

Date formats:
- Relative dates: "last 4 days", "yesterday", "this month", etc.
- Absolute dates: "2024-01-01", "October 27, 2024", etc.
- Date ranges: "October 27-30", "2024-01-01 to 2024-01-31", etc.

Operators:
- equals, not_equals, greater_than, less_than, contains, starts_with, ends_with, in, not_in, exists, range

Aggregation types:
- count, sum, avg, min, max, percentage, terms, date_histogram, correlation

Return a valid JSON object with this structure:
{
  "index_names": ["index1", "index2"],
  "date_range": {
    "start_date_str": "2024-01-01",
    "end_date_str": "2024-01-31",
    "relative_period": "last 4 days",
    "is_relative": true
  },
  "filters": {
    "must": [
      {"field": "field_name", "operator": "equals", "value": "field_value"}
    ],
    "should": [],
    "must_not": []
  },
  "aggregations": [
    {"type": "count", "field": "field_name", "group_by": ["field1"], "alias": "total_count"}
  ],
  "fields": ["field1", "field2"],
  "sort": {"field_name": "desc"},
  "limit": 100
}

If a field is not mentioned or cannot be determined, use null or empty array/list.
Be precise and only extract information that is explicitly stated or clearly implied.
"""

    def __init__(
        self,
        azure_openai_client: Optional[AzureOpenAIClient] = None,
        schema_info: Optional[SchemaInfo] = None,
    ):
        """Initialize natural language parser.

        Args:
            azure_openai_client: Optional Azure OpenAI client (creates new one if not provided)
            schema_info: Optional schema information for field validation
        """
        self.azure_client = azure_openai_client or AzureOpenAIClient()
        self.schema_info = schema_info
        self.date_parser = DateRangeParser()
        self.entity_extractor = EntityExtractor()
        self.intent_classifier = IntentClassifier()

    async def parse(
        self,
        query: str,
        index_names: Optional[list[str]] = None,
        schema_info: Optional[SchemaInfo] = None,
    ) -> ParsedQuery:
        """Parse natural language query into structured query intentions.

        Args:
            query: Natural language query text
            index_names: Optional list of target index names
            schema_info: Optional schema information for field validation

        Returns:
            ParsedQuery object with extracted information
        """
        if not query or not query.strip():
            logger.warning("Empty query provided")
            return ParsedQuery(
                original_query=query or "",
                confidence=0.0,
                errors=["Empty query provided"],
            )

        # Use provided schema_info or instance schema_info
        effective_schema = schema_info or self.schema_info

        try:
            # Step 1: Use Azure OpenAI to parse the query into structured format
            llm_result = await self._parse_with_llm(query, effective_schema, index_names)

            # Step 2: Extract entities using rule-based methods as fallback/enhancement
            entities = self._extract_entities(query, effective_schema)

            # Step 3: Parse date range using specialized parser
            date_range = self.date_parser.parse_date_range(query)

            # Step 4: Classify query intent
            schema_fields = (
                list(effective_schema.fields.keys()) if effective_schema else None
            )
            intent = self.intent_classifier.classify_intent(query, schema_fields)

            # Step 5: Combine LLM results with rule-based extractions
            parsed_query = self._combine_results(
                query, llm_result, date_range, intent, entities, effective_schema
            )

            # Step 6: Validate and enhance the parsed query
            parsed_query = self._validate_and_enhance(parsed_query, effective_schema)

            logger.info(
                "Query parsed successfully",
                query=query[:100],  # Log first 100 chars
                intent=parsed_query.intent.category,
                confidence=parsed_query.confidence,
            )

            return parsed_query

        except Exception as e:
            logger.error(
                "Error parsing query",
                error=str(e),
                error_type=type(e).__name__,
                query=query[:100],
            )
            return ParsedQuery(
                original_query=query,
                confidence=0.0,
                errors=[f"Parsing error: {str(e)}"],
                intent=QueryIntent(category=QueryIntentCategory.UNKNOWN, confidence=0.0),
            )

    async def _parse_with_llm(
        self,
        query: str,
        schema_info: Optional[SchemaInfo],
        index_names: Optional[list[str]],
    ) -> dict[str, Any]:
        """Parse query using Azure OpenAI LLM.

        Args:
            query: Natural language query
            schema_info: Optional schema information
            index_names: Optional index names

        Returns:
            Dictionary with parsed query components
        """
        # Enhance system prompt with schema information
        user_prompt = self._build_user_prompt(query, schema_info, index_names)

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = await self.azure_client.chat_completion(
                messages=messages,
                temperature=0.3,  # Lower temperature for more consistent parsing
                max_tokens=2000,
            )

            content = response["choices"][0]["message"]["content"]
            logger.debug("LLM response received", content_length=len(content))

            # Parse JSON response
            try:
                # Try to extract JSON if it's wrapped in markdown code blocks
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                elif "```" in content:
                    json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()

                parsed = json.loads(content)
                return parsed

            except json.JSONDecodeError as e:
                logger.warning("Failed to parse LLM JSON response", error=str(e), content=content[:500])
                return {}

        except Exception as e:
            logger.error("LLM parsing failed", error=str(e), error_type=type(e).__name__)
            return {}

    def _build_user_prompt(
        self,
        query: str,
        schema_info: Optional[SchemaInfo],
        index_names: Optional[list[str]],
    ) -> str:
        """Build user prompt for LLM with context.

        Args:
            query: Natural language query
            schema_info: Optional schema information
            index_names: Optional index names

        Returns:
            Formatted user prompt
        """
        prompt_parts = [f"Parse this natural language query:\n{query}\n"]

        if index_names:
            prompt_parts.append(f"\nTarget indices: {', '.join(index_names)}")

        if schema_info:
            prompt_parts.append(f"\nAvailable fields in schema (index: {schema_info.index_name}):")
            field_list = []
            for field_name, field_info in schema_info.fields.items():
                field_desc = f"- {field_name} ({field_info.field_type.value})"
                if field_info.description:
                    field_desc += f": {field_info.description}"
                field_list.append(field_desc)
            prompt_parts.append("\n".join(field_list[:50]))  # Limit to first 50 fields

        prompt_parts.append("\n\nReturn the parsed query in JSON format as specified.")

        return "\n".join(prompt_parts)

    def _extract_entities(
        self, query: str, schema_info: Optional[SchemaInfo]
    ) -> dict[str, Any]:
        """Extract entities using rule-based methods.

        Args:
            query: Natural language query
            schema_info: Optional schema information

        Returns:
            Dictionary of extracted entities
        """
        entities = {}

        # Extract field names
        known_fields = list(schema_info.fields.keys()) if schema_info else None
        entities["field_names"] = self.entity_extractor.extract_field_names(
            query, known_fields
        )

        # Extract operators
        entities["operators"] = self.entity_extractor.extract_operators(query)

        # Extract values
        entities["values"] = self.entity_extractor.extract_values(query)

        # Extract aggregation keywords
        entities["aggregations"] = self.entity_extractor.extract_aggregation_keywords(query)

        # Extract time periods
        entities["time_periods"] = self.entity_extractor.extract_time_periods(query)

        # Extract group-by keywords
        entities["group_by"] = self.entity_extractor.extract_group_by_keywords(query)

        return entities

    def _combine_results(
        self,
        query: str,
        llm_result: dict[str, Any],
        date_range: Optional[DateRange],
        intent: QueryIntent,
        entities: dict[str, Any],
        schema_info: Optional[SchemaInfo],
    ) -> ParsedQuery:
        """Combine LLM results with rule-based extractions.

        Args:
            query: Original query
            llm_result: LLM parsing result
            date_range: Parsed date range
            intent: Query intent
            entities: Extracted entities
            schema_info: Optional schema information

        Returns:
            ParsedQuery object
        """
        # Extract components from LLM result
        index_names = llm_result.get("index_names", [])

        # Use parsed date range if available, otherwise use LLM result
        final_date_range = date_range
        if not final_date_range and "date_range" in llm_result:
            date_range_data = llm_result["date_range"]
            if date_range_data:
                # Try to parse date range from LLM result
                start_str = date_range_data.get("start_date_str")
                end_str = date_range_data.get("end_date_str")
                if start_str or end_str:
                    final_date_range = self.date_parser.parse_date_range(
                        f"{start_str or ''} to {end_str or ''}"
                    )

        # Build filters from LLM result
        filters = self._build_filters(llm_result.get("filters", {}))

        # Build aggregations from LLM result
        aggregations = self._build_aggregations(llm_result.get("aggregations", []))

        # Get fields from LLM result (ensure it's a list)
        fields = llm_result.get("fields", [])
        if fields is None:
            fields = []

        # Get sort from LLM result
        sort = llm_result.get("sort")

        # Get limit from LLM result
        limit = llm_result.get("limit")

        # Calculate confidence based on multiple factors
        confidence = self._calculate_confidence(llm_result, intent, entities, final_date_range)

        # Collect errors/warnings
        errors = []
        if not index_names:
            errors.append("No index names specified")
        if not filters.conditions and not filters.must:
            logger.debug("No filters extracted from query")

        return ParsedQuery(
            original_query=query,
            index_names=index_names,
            date_range=final_date_range,
            filters=filters,
            aggregations=aggregations,
            fields=fields,
            sort=sort,
            limit=limit,
            intent=intent,
            confidence=confidence,
            entities=entities,
            errors=errors,
        )

    def _build_filters(self, filters_data: dict[str, Any]) -> Filter:
        """Build Filter object from LLM result.

        Args:
            filters_data: Filter data from LLM

        Returns:
            Filter object
        """
        filter_obj = Filter()

        # Process must conditions
        must_data = filters_data.get("must", [])
        filter_obj.must = [self._build_filter_condition(f) for f in must_data if f]

        # Process should conditions
        should_data = filters_data.get("should", [])
        filter_obj.should = [self._build_filter_condition(f) for f in should_data if f]

        # Process must_not conditions
        must_not_data = filters_data.get("must_not", [])
        filter_obj.must_not = [
            self._build_filter_condition(f) for f in must_not_data if f
        ]

        # Combine all conditions
        filter_obj.conditions = (
            filter_obj.must + filter_obj.should + filter_obj.must_not
        )

        return filter_obj

    def _build_filter_condition(self, condition_data: dict[str, Any]) -> FilterCondition:
        """Build FilterCondition from data.

        Args:
            condition_data: Condition data

        Returns:
            FilterCondition object
        """
        field = condition_data.get("field", "")
        operator_str = condition_data.get("operator", "equals")
        value = condition_data.get("value")
        nested_path = condition_data.get("nested_path")

        # Map operator string to FilterOperator enum
        try:
            operator = FilterOperator(operator_str.lower())
        except ValueError:
            operator = FilterOperator.EQUALS  # Default

        return FilterCondition(
            field=field,
            operator=operator,
            value=value,
            nested_path=nested_path,
        )

    def _build_aggregations(self, aggregations_data: list[dict[str, Any]]) -> list[Aggregation]:
        """Build Aggregation objects from LLM result.

        Args:
            aggregations_data: Aggregation data from LLM

        Returns:
            List of Aggregation objects
        """
        aggregations = []

        for agg_data in aggregations_data:
            if not agg_data:
                continue

            agg_type_str = agg_data.get("type", "count")
            try:
                agg_type = AggregationType(agg_type_str.lower())
            except ValueError:
                agg_type = AggregationType.COUNT  # Default

            aggregation = Aggregation(
                type=agg_type,
                field=agg_data.get("field"),
                group_by=agg_data.get("group_by"),
                alias=agg_data.get("alias"),
                buckets=agg_data.get("buckets"),
                interval=agg_data.get("interval"),
            )

            aggregations.append(aggregation)

        return aggregations

    def _calculate_confidence(
        self,
        llm_result: dict[str, Any],
        intent: QueryIntent,
        entities: dict[str, Any],
        date_range: Optional[DateRange],
    ) -> float:
        """Calculate overall parsing confidence.

        Args:
            llm_result: LLM parsing result
            intent: Query intent
            entities: Extracted entities
            date_range: Parsed date range

        Returns:
            Confidence score (0-1)
        """
        confidence_factors = []

        # Intent confidence (weight: 0.3)
        confidence_factors.append(("intent", intent.confidence, 0.3))

        # LLM result completeness (weight: 0.4)
        llm_completeness = 0.0
        if llm_result:
            has_filters = bool(llm_result.get("filters", {}).get("must"))
            has_aggregations = bool(llm_result.get("aggregations"))
            has_date_range = bool(date_range or llm_result.get("date_range"))
            llm_completeness = (has_filters + has_aggregations + has_date_range) / 3.0
        confidence_factors.append(("llm_completeness", llm_completeness, 0.4))

        # Entity extraction confidence (weight: 0.3)
        entity_confidence = 0.0
        if entities:
            has_fields = bool(entities.get("field_names"))
            has_operators = bool(entities.get("operators"))
            has_values = bool(entities.get("values"))
            entity_confidence = (has_fields + has_operators + has_values) / 3.0
        confidence_factors.append(("entity_extraction", entity_confidence, 0.3))

        # Calculate weighted average
        total_confidence = sum(score * weight for _, score, weight in confidence_factors)
        total_weight = sum(weight for _, _, weight in confidence_factors)

        if total_weight > 0:
            confidence = total_confidence / total_weight
        else:
            confidence = 0.0

        return min(1.0, max(0.0, confidence))

    def _validate_and_enhance(
        self, parsed_query: ParsedQuery, schema_info: Optional[SchemaInfo]
    ) -> ParsedQuery:
        """Validate and enhance parsed query with schema information.

        Args:
            parsed_query: Parsed query to validate
            schema_info: Optional schema information

        Returns:
            Enhanced ParsedQuery
        """
        if not schema_info:
            return parsed_query

        errors = list(parsed_query.errors)

        # Validate field names
        valid_fields = set(schema_info.fields.keys())

        # Validate filter fields
        for condition in parsed_query.filters.conditions:
            if condition.field and condition.field not in valid_fields:
                # Try to find similar field name
                similar_fields = [
                    f for f in valid_fields if condition.field.lower() in f.lower() or f.lower() in condition.field.lower()
                ]
                if similar_fields:
                    condition.field = similar_fields[0]
                    errors.append(f"Field '{condition.field}' adjusted to '{similar_fields[0]}'")
                else:
                    errors.append(f"Unknown field: {condition.field}")

        # Validate aggregation fields
        for aggregation in parsed_query.aggregations:
            if aggregation.field and aggregation.field not in valid_fields:
                similar_fields = [
                    f for f in valid_fields if aggregation.field.lower() in f.lower() or f.lower() in aggregation.field.lower()
                ]
                if similar_fields:
                    aggregation.field = similar_fields[0]
                    errors.append(f"Aggregation field '{aggregation.field}' adjusted to '{similar_fields[0]}'")

        # Validate fields to retrieve
        for i, field in enumerate(parsed_query.fields):
            if field not in valid_fields:
                similar_fields = [
                    f for f in valid_fields if field.lower() in f.lower() or f.lower() in field.lower()
                ]
                if similar_fields:
                    parsed_query.fields[i] = similar_fields[0]

        parsed_query.errors = errors
        return parsed_query

    async def close(self) -> None:
        """Close the Azure OpenAI client."""
        await self.azure_client.close()

