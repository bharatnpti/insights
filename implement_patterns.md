# Agentic Patterns Integration: Reflection, Planning, and ReAct

## Table of Contents

1. [Overview](#overview)
2. [Architecture Design](#architecture-design)
3. [Reflection Pattern](#reflection-pattern)
4. [Planning Pattern](#planning-pattern)
5. [ReAct Pattern](#react-pattern)
6. [Integrated Workflow](#integrated-workflow)
7. [Implementation Details](#implementation-details)
8. [Configuration](#configuration)
9. [Testing Strategy](#testing-strategy)
10. [Examples](#examples)
11. [Performance Considerations](#performance-considerations)
12. [Migration Guide](#migration-guide)

---

## Overview

This document describes the integration of three agentic patterns into the Natural Language Analytics Platform (NLAP):

- **Reflection**: Self-validation and refinement of generated queries
- **Planning**: Decomposition of complex queries into sequential steps
- **ReAct**: Iterative reasoning and action loops for query refinement

These patterns enhance NLAP's ability to handle complex, multi-step queries with improved accuracy and robustness.

### Benefits

- **Improved Accuracy**: Reflection catches and fixes errors before execution
- **Complex Query Support**: Planning handles multi-step queries that require data correlation
- **Adaptive Query Generation**: ReAct enables iterative refinement based on schema and constraints
- **Better Error Handling**: Self-correction reduces query failures
- **Schema-Aware Optimization**: Patterns leverage schema information for better field mapping

---

## Architecture Design

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Input                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              ReAct Query Orchestrator                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Observation: Analyze user query                      │  │
│  │  Thought: Determine complexity & required steps        │  │
│  │  Action: Initialize Planning or direct parsing       │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Planning Agent (if complex)                     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Step 1: Identify required indices                   │  │
│  │  Step 2: Plan schema discovery strategy               │  │
│  │  Step 3: Decompose query into sub-queries             │  │
│  │  Step 4: Plan correlation/join strategy               │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           Schema Discovery (guided by plan)                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              NLP Parser (existing)                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Parse natural language to structured query            │  │
│  │  Use schema information for field validation           │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Query Builder (existing)                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Build OpenSearch query from parsed query             │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Reflection Agent                                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Reflection Loop:                                      │  │
│  │  1. Validate query completeness                       │  │
│  │  2. Check field existence in schema                   │  │
│  │  3. Verify query logic                                 │  │
│  │  4. Suggest improvements                              │  │
│  │  5. Refine query if needed                            │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          Final OpenSearch Query                              │
└─────────────────────────────────────────────────────────────┘
```

### Component Structure

```
src/nlap/
├── agentic/                      # New module for agentic patterns
│   ├── __init__.py
│   ├── reflection/              # Reflection pattern implementation
│   │   ├── __init__.py
│   │   ├── agent.py             # ReflectionAgent class
│   │   ├── validator.py         # Query validators
│   │   └── models.py            # Reflection-specific models
│   ├── planning/                # Planning pattern implementation
│   │   ├── __init__.py
│   │   ├── agent.py             # PlanningAgent class
│   │   ├── planner.py           # Query planner
│   │   └── models.py            # Planning-specific models
│   └── react/                   # ReAct pattern implementation
│       ├── __init__.py
│       ├── orchestrator.py      # ReActOrchestrator class
│       ├── tools.py             # Available tools/actions
│       └── models.py            # ReAct-specific models
└── ... (existing modules)
```

---

## Reflection Pattern

### Overview

The Reflection pattern enables the system to validate, critique, and refine its own output. After generating a query, the system reflects on:

1. **Completeness**: Are all user requirements addressed?
2. **Correctness**: Are fields valid? Is the query logic sound?
3. **Optimization**: Can the query be improved?
4. **Clarity**: Are there ambiguities that need resolution?

### Implementation

#### ReflectionAgent Class

```python
# src/nlap/agentic/reflection/agent.py

from typing import Optional, List
from pydantic import BaseModel
from nlap.nlp.models import ParsedQuery, AggregationType
from nlap.opensearch.schema_models import SchemaInfo, FieldType
from nlap.opensearch.query_builder import QueryBuilder
from nlap.azureopenai.client import AzureOpenAIClient
from nlap.utils.logger import get_logger
from nlap.utils.prompt_loader import load_prompt

logger = get_logger(__name__)


class ReflectionResult(BaseModel):
    """Result of reflection process."""
    
    is_valid: bool
    confidence: float
    issues: List[str]
    suggestions: List[str]
    refined_query: Optional[ParsedQuery] = None
    refinement_reason: Optional[str] = None


class ReflectionAgent:
    """Agent that reflects on and refines generated queries."""
    
    def __init__(
        self,
        azure_client: AzureOpenAIClient,
        schema_info: Optional[SchemaInfo] = None,
        max_reflections: int = 3,
    ):
        """Initialize reflection agent.
        
        Args:
            azure_client: Azure OpenAI client
            schema_info: Optional schema information for validation
            max_reflections: Maximum number of reflection iterations
        """
        self.azure_client = azure_client
        self.schema_info = schema_info
        self.max_reflections = max_reflections
        from nlap.agentic.reflection.validator import QueryValidator
        self.validator = QueryValidator(schema_info)
    
    async def reflect(
        self,
        parsed_query: ParsedQuery,
        original_query: str,
        opensearch_query: Optional[dict] = None,
    ) -> ReflectionResult:
        """Reflect on a parsed query and potentially refine it.
        
        Args:
            parsed_query: The parsed query to reflect on
            original_query: Original user query for context
            opensearch_query: Optional OpenSearch query for validation
            
        Returns:
            ReflectionResult with validation and suggestions
        """
        issues = []
        suggestions = []
        
        # 1. Schema validation
        schema_issues = await self.validator.validate_against_schema(parsed_query)
        issues.extend(schema_issues)
        
        # 2. Completeness check
        completeness_issues = self._check_completeness(parsed_query, original_query)
        issues.extend(completeness_issues)
        
        # 3. Logic validation
        logic_issues = self._validate_query_logic(parsed_query)
        issues.extend(logic_issues)
        
        # 4. LLM-based reflection for complex issues
        if issues or self._should_reflect_deeply(parsed_query):
            llm_reflection = await self._llm_reflect(
                parsed_query, original_query, opensearch_query, issues
            )
            issues.extend(llm_reflection.issues)
            suggestions.extend(llm_reflection.suggestions)
        
        # 5. Determine if refinement is needed
        needs_refinement = len(issues) > 0
        confidence = self._calculate_confidence(parsed_query, issues)
        
        # 6. Attempt refinement if needed
        refined_query = None
        refinement_reason = None
        if needs_refinement and self.max_reflections > 0:
            refined_result = await self._attempt_refinement(
                parsed_query, original_query, issues, suggestions
            )
            refined_query = refined_result.refined_query
            refinement_reason = refined_result.refinement_reason
        
        return ReflectionResult(
            is_valid=len(issues) == 0,
            confidence=confidence,
            issues=issues,
            suggestions=suggestions,
            refined_query=refined_query,
            refinement_reason=refinement_reason,
        )
    
    async def _llm_reflect(
        self,
        parsed_query: ParsedQuery,
        original_query: str,
        opensearch_query: Optional[dict],
        existing_issues: List[str],
    ) -> ReflectionResult:
        """Use LLM to reflect on query quality and completeness."""
        
        reflection_prompt = self._build_reflection_prompt(
            parsed_query, original_query, opensearch_query, existing_issues
        )
        
        messages = [
            {"role": "system", "content": load_prompt("reflection_system.txt")},
            {"role": "user", "content": reflection_prompt},
        ]
        
        response = await self.azure_client.chat_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=2000,
        )
        
        content = response["choices"][0]["message"]["content"]
        # Parse reflection result from LLM response
        return self._parse_reflection_response(content, existing_issues)
    
    def _check_completeness(
        self, parsed_query: ParsedQuery, original_query: str
    ) -> List[str]:
        """Check if parsed query captures all user requirements."""
        issues = []
        
        # Check for date range if query mentions time
        time_keywords = ["last", "yesterday", "today", "date", "time", "when"]
        if any(kw in original_query.lower() for kw in time_keywords):
            if not parsed_query.date_range:
                issues.append("Query mentions time but no date range specified")
        
        # Check for filters if query mentions conditions
        condition_keywords = ["where", "with", "contains", "equals", "filter"]
        if any(kw in original_query.lower() for kw in condition_keywords):
            if not parsed_query.filters.must and not parsed_query.filters.should:
                issues.append("Query mentions conditions but no filters specified")
        
        # Check for aggregations if query mentions statistics
        aggregation_keywords = ["count", "sum", "average", "group by", "aggregate"]
        if any(kw in original_query.lower() for kw in aggregation_keywords):
            if not parsed_query.aggregations:
                issues.append("Query mentions aggregations but none specified")
        
        return issues
    
    def _validate_query_logic(self, parsed_query: ParsedQuery) -> List[str]:
        """Validate logical consistency of query."""
        issues = []
        
        # Check date range logic
        if parsed_query.date_range:
            if parsed_query.date_range.start_date and parsed_query.date_range.end_date:
                if parsed_query.date_range.start_date > parsed_query.date_range.end_date:
                    issues.append("Start date is after end date")
        
        # Check aggregation field types
        for agg in parsed_query.aggregations:
            if agg.field and self.schema_info:
                field_info = self.schema_info.fields.get(agg.field)
                if field_info:
                    # SUM/AVG on text fields doesn't make sense
                    if agg.type in [AggregationType.SUM, AggregationType.AVG]:
                        if field_info.field_type == FieldType.TEXT:
                            issues.append(
                                f"Cannot perform {agg.type} on text field '{agg.field}'"
                            )
        
        return issues
    
    def _should_reflect_deeply(self, parsed_query: ParsedQuery) -> bool:
        """Determine if deep LLM reflection is needed."""
        # Use deep reflection for complex queries
        complexity_indicators = [
            len(parsed_query.aggregations) > 1,
            len(parsed_query.filters.must) + len(parsed_query.filters.should) > 3,
            parsed_query.confidence < 0.7,
            len(parsed_query.index_names) > 1,
        ]
        return any(complexity_indicators)
    
    async def _attempt_refinement(
        self,
        parsed_query: ParsedQuery,
        original_query: str,
        issues: List[str],
        suggestions: List[str],
    ) -> ReflectionResult:
        """Attempt to refine query based on reflection."""
        
        if self.max_reflections <= 0:
            return ReflectionResult(
                is_valid=False,
                confidence=0.5,
                issues=issues,
                suggestions=suggestions,
            )
        
        refinement_prompt = self._build_refinement_prompt(
            parsed_query, original_query, issues, suggestions
        )
        
        messages = [
            {"role": "system", "content": load_prompt("refinement_system.txt")},
            {"role": "user", "content": refinement_prompt},
        ]
        
        response = await self.azure_client.chat_completion(
            messages=messages,
            temperature=0.2,  # Lower temperature for refinement
            max_tokens=3000,
        )
        
        content = response["choices"][0]["message"]["content"]
        refined_query = self._parse_refined_query(content, parsed_query)
        
        # Recursively reflect on refined query (with reduced max_reflections)
        agent = ReflectionAgent(
            self.azure_client,
            self.schema_info,
            max_reflections=self.max_reflections - 1,
        )
        
        refined_reflection = await agent.reflect(refined_query, original_query)
        
        return ReflectionResult(
            is_valid=refined_reflection.is_valid,
            confidence=refined_reflection.confidence,
            issues=refined_reflection.issues,
            suggestions=refined_reflection.suggestions,
            refined_query=refined_query,
            refinement_reason="Applied suggestions from reflection",
        )
    
    def _calculate_confidence(
        self, parsed_query: ParsedQuery, issues: List[str]
    ) -> float:
        """Calculate confidence score based on query quality."""
        base_confidence = parsed_query.confidence
        
        # Reduce confidence based on issues
        issue_penalty = len(issues) * 0.1
        final_confidence = max(0.0, base_confidence - issue_penalty)
        
        return final_confidence
    
    def _build_reflection_prompt(
        self,
        parsed_query: ParsedQuery,
        original_query: str,
        opensearch_query: Optional[dict],
        existing_issues: List[str],
    ) -> str:
        """Build prompt for reflection."""
        # Implementation details for building reflection prompt
        prompt_parts = [
            f"Original query: {original_query}",
            f"\nParsed query: {parsed_query.model_dump_json()}",
        ]
        if existing_issues:
            prompt_parts.append(f"\nExisting issues: {existing_issues}")
        return "\n".join(prompt_parts)
    
    def _parse_reflection_response(self, content: str, existing_issues: List[str]) -> ReflectionResult:
        """Parse LLM reflection response."""
        # Implementation for parsing JSON response from LLM
        # This would extract issues and suggestions from the response
        import json
        try:
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            parsed = json.loads(content)
            return ReflectionResult(
                is_valid=not parsed.get("issues", []),
                confidence=parsed.get("confidence", 0.5),
                issues=parsed.get("issues", []),
                suggestions=parsed.get("suggestions", []),
            )
        except Exception as e:
            logger.warning(f"Failed to parse reflection response: {e}")
            return ReflectionResult(
                is_valid=False,
                confidence=0.5,
                issues=existing_issues,
                suggestions=[],
            )
    
    def _build_refinement_prompt(
        self,
        parsed_query: ParsedQuery,
        original_query: str,
        issues: List[str],
        suggestions: List[str],
    ) -> str:
        """Build prompt for query refinement."""
        prompt_parts = [
            f"Original query: {original_query}",
            f"\nParsed query with issues: {parsed_query.model_dump_json()}",
            f"\nIssues found: {issues}",
            f"\nSuggestions: {suggestions}",
            "\nRefine the parsed query to fix these issues.",
        ]
        return "\n".join(prompt_parts)
    
    def _parse_refined_query(self, content: str, original_parsed: ParsedQuery) -> ParsedQuery:
        """Parse refined query from LLM response."""
        # Implementation for parsing and creating refined ParsedQuery
        import json
        try:
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            parsed_data = json.loads(content)
            # Reconstruct ParsedQuery from JSON
            # This would need proper deserialization logic
            return original_parsed  # Placeholder
        except Exception as e:
            logger.warning(f"Failed to parse refined query: {e}")
            return original_parsed
```

#### QueryValidator Class

```python
# src/nlap/agentic/reflection/validator.py

from typing import List, Optional
from nlap.nlp.models import ParsedQuery, FilterCondition, Aggregation
from nlap.opensearch.schema_models import SchemaInfo, FieldType
from nlap.utils.logger import get_logger

logger = get_logger(__name__)


class QueryValidator:
    """Validates queries against schema and constraints."""
    
    def __init__(self, schema_info: Optional[SchemaInfo] = None):
        """Initialize validator.
        
        Args:
            schema_info: Schema information for validation
        """
        self.schema_info = schema_info
    
    async def validate_against_schema(
        self, parsed_query: ParsedQuery
    ) -> List[str]:
        """Validate query fields against discovered schema.
        
        Args:
            parsed_query: Query to validate
            
        Returns:
            List of validation issues
        """
        if not self.schema_info:
            return []  # Can't validate without schema
        
        issues = []
        
        # Validate filter fields
        for condition in parsed_query.filters.must + parsed_query.filters.should:
            if condition.field:
                issues.extend(self._validate_field(condition.field, "filter"))
        
        # Validate aggregation fields
        for agg in parsed_query.aggregations:
            if agg.field:
                issues.extend(self._validate_field(agg.field, "aggregation"))
        
        # Validate fields to retrieve
        for field in parsed_query.fields:
            issues.extend(self._validate_field(field, "source"))
        
        # Validate sort fields
        if parsed_query.sort:
            for field in parsed_query.sort.keys():
                issues.extend(self._validate_field(field, "sort"))
        
        return issues
    
    def _validate_field(self, field_name: str, context: str) -> List[str]:
        """Validate a single field.
        
        Args:
            field_name: Field name to validate
            context: Context where field is used
            
        Returns:
            List of issues (empty if valid)
        """
        if not self.schema_info:
            return []
        
        issues = []
        
        if field_name not in self.schema_info.fields:
            # Try fuzzy matching
            similar_fields = self._find_similar_fields(field_name)
            if similar_fields:
                issues.append(
                    f"Field '{field_name}' not found in schema. "
                    f"Did you mean: {', '.join(similar_fields[:3])}?"
                )
            else:
                issues.append(
                    f"Field '{field_name}' not found in schema for {context}"
                )
        
        return issues
    
    def _find_similar_fields(self, field_name: str) -> List[str]:
        """Find similar field names using fuzzy matching."""
        if not self.schema_info:
            return []
        
        field_name_lower = field_name.lower()
        similar = []
        
        for schema_field in self.schema_info.fields.keys():
            schema_field_lower = schema_field.lower()
            
            # Exact substring match
            if field_name_lower in schema_field_lower or schema_field_lower in field_name_lower:
                similar.append(schema_field)
            # Word-based similarity
            elif any(word in schema_field_lower for word in field_name_lower.split("_")):
                similar.append(schema_field)
        
        return similar[:5]  # Return top 5 matches
```

### Prompt Templates

```text
# prompts/reflection_system.txt

You are a query quality analyzer for OpenSearch queries.

Your task is to:
1. Review parsed natural language queries for completeness and correctness
2. Identify potential issues or missing elements
3. Suggest improvements

Consider:
- Does the query capture all user requirements?
- Are all referenced fields valid?
- Is the query logic sound?
- Are there any ambiguities?
- Can the query be optimized?

Return your analysis as JSON:
{
  "issues": ["issue1", "issue2"],
  "suggestions": ["suggestion1", "suggestion2"],
  "confidence": 0.0-1.0,
  "needs_refinement": true/false
}
```

```text
# prompts/refinement_system.txt

You are a query refinement agent for OpenSearch.

Given:
- Original user query
- Parsed query with issues
- Reflection feedback

Your task:
1. Fix identified issues
2. Apply suggestions
3. Improve query completeness
4. Maintain query intent

Return the refined parsed query in the same JSON format as the original.
```

---

## Planning Pattern

### Overview

The Planning pattern decomposes complex queries into sequential steps, enabling:

1. **Multi-step queries**: Queries requiring data from multiple sources
2. **Correlation analysis**: Queries needing to join/correlate data across indices
3. **Progressive schema discovery**: Discover schema incrementally as needed
4. **Query optimization**: Plan efficient query execution order

### Implementation

#### PlanningAgent Class

```python
# src/nlap/agentic/planning/agent.py

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from nlap.nlp.models import ParsedQuery
from nlap.opensearch.schema_models import SchemaInfo
from nlap.azureopenai.client import AzureOpenAIClient
from nlap.opensearch.schema_discovery import SchemaDiscoveryEngine
from nlap.utils.logger import get_logger
from nlap.utils.prompt_loader import load_prompt

logger = get_logger(__name__)


class QueryStep(BaseModel):
    """A single step in a query plan."""
    
    step_number: int
    description: str
    required_indices: List[str]
    required_schema_fields: List[str]
    sub_query: Optional[ParsedQuery] = None
    dependencies: List[int] = Field(
        default_factory=list, description="Step numbers this step depends on"
    )
    output_fields: List[str] = Field(
        default_factory=list, description="Fields this step produces"
    )


class QueryPlan(BaseModel):
    """Complete plan for executing a complex query."""
    
    original_query: str
    plan_steps: List[QueryStep]
    execution_order: List[int]
    correlation_strategy: Optional[str] = None
    correlation_fields: List[str] = Field(default_factory=list)


class PlanningAgent:
    """Agent that plans complex query execution."""
    
    def __init__(
        self,
        azure_client: AzureOpenAIClient,
        schema_discovery: Optional[SchemaDiscoveryEngine] = None,
    ):
        """Initialize planning agent.
        
        Args:
            azure_client: Azure OpenAI client
            schema_discovery: Optional schema discovery engine
        """
        self.azure_client = azure_client
        self.schema_discovery = schema_discovery
    
    async def create_plan(
        self,
        user_query: str,
        initial_parsed_query: Optional[ParsedQuery] = None,
    ) -> QueryPlan:
        """Create execution plan for a complex query.
        
        Args:
            user_query: Original user query
            initial_parsed_query: Optional initial parsed query
            
        Returns:
            QueryPlan with execution steps
        """
        # Determine if planning is needed
        complexity_score = self._assess_complexity(user_query, initial_parsed_query)
        
        if complexity_score < 0.5:
            # Simple query, create single-step plan
            return await self._create_simple_plan(user_query, initial_parsed_query)
        
        # Complex query, use LLM to plan
        return await self._create_complex_plan(user_query, initial_parsed_query)
    
    def _assess_complexity(
        self,
        user_query: str,
        parsed_query: Optional[ParsedQuery],
    ) -> float:
        """Assess query complexity (0.0 = simple, 1.0 = very complex)."""
        score = 0.0
        
        # Multiple indices
        if parsed_query and len(parsed_query.index_names) > 1:
            score += 0.3
        
        # Correlation keywords
        correlation_keywords = [
            "correlate", "join", "match", "related", "across", "together"
        ]
        if any(kw in user_query.lower() for kw in correlation_keywords):
            score += 0.4
        
        # Multiple aggregations
        if parsed_query and len(parsed_query.aggregations) > 1:
            score += 0.2
        
        # Time-based correlation
        time_correlation_keywords = ["then", "after", "before", "sequence"]
        if any(kw in user_query.lower() for kw in time_correlation_keywords):
            score += 0.3
        
        # Multiple conditions
        if parsed_query:
            total_conditions = (
                len(parsed_query.filters.must) +
                len(parsed_query.filters.should)
            )
            if total_conditions > 3:
                score += 0.2
        
        return min(1.0, score)
    
    async def _create_simple_plan(
        self,
        user_query: str,
        parsed_query: Optional[ParsedQuery],
    ) -> QueryPlan:
        """Create plan for simple query (single step)."""
        step = QueryStep(
            step_number=1,
            description="Execute main query",
            required_indices=parsed_query.index_names if parsed_query else [],
            required_schema_fields=[],
            sub_query=parsed_query,
        )
        
        return QueryPlan(
            original_query=user_query,
            plan_steps=[step],
            execution_order=[1],
        )
    
    async def _create_complex_plan(
        self,
        user_query: str,
        parsed_query: Optional[ParsedQuery],
    ) -> QueryPlan:
        """Create plan for complex query using LLM."""
        
        planning_prompt = self._build_planning_prompt(
            user_query, parsed_query
        )
        
        messages = [
            {"role": "system", "content": load_prompt("planning_system.txt")},
            {"role": "user", "content": planning_prompt},
        ]
        
        response = await self.azure_client.chat_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=3000,
        )
        
        content = response["choices"][0]["message"]["content"]
        plan = self._parse_plan_response(content, user_query, parsed_query)
        
        # Validate and optimize plan
        plan = await self._validate_plan(plan)
        plan = self._optimize_execution_order(plan)
        
        return plan
    
    def _build_planning_prompt(
        self,
        user_query: str,
        parsed_query: Optional[ParsedQuery],
    ) -> str:
        """Build prompt for LLM planning."""
        prompt_parts = [
            f"User query: {user_query}",
            "\nCreate an execution plan that breaks this query into sequential steps.",
        ]
        
        if parsed_query:
            prompt_parts.append(f"\nInitial parsed query:")
            prompt_parts.append(f"- Indices: {parsed_query.index_names}")
            prompt_parts.append(f"- Filters: {len(parsed_query.filters.must)} must conditions")
            prompt_parts.append(f"- Aggregations: {len(parsed_query.aggregations)}")
        
        prompt_parts.append(
            "\nConsider:"
            "\n- What data sources are needed?"
            "\n- What is the order of operations?"
            "\n- Are there dependencies between steps?"
            "\n- How should data be correlated?"
        )
        
        return "\n".join(prompt_parts)
    
    async def _validate_plan(self, plan: QueryPlan) -> QueryPlan:
        """Validate plan and ensure dependencies are correct."""
        # Check that dependencies are valid
        step_numbers = {step.step_number for step in plan.plan_steps}
        
        for step in plan.plan_steps:
            for dep in step.dependencies:
                if dep not in step_numbers:
                    logger.warning(
                        f"Invalid dependency {dep} in step {step.step_number}"
                    )
                    step.dependencies = [
                        d for d in step.dependencies if d in step_numbers
                    ]
        
        return plan
    
    def _optimize_execution_order(self, plan: QueryPlan) -> QueryPlan:
        """Optimize execution order based on dependencies."""
        # Topological sort of steps based on dependencies
        ordered_steps = []
        remaining_steps = {step.step_number: step for step in plan.plan_steps}
        completed_steps = set()
        
        while remaining_steps:
            # Find steps with no unmet dependencies
            ready_steps = [
                step_num
                for step_num, step in remaining_steps.items()
                if all(dep in completed_steps for dep in step.dependencies)
            ]
            
            if not ready_steps:
                # Circular dependency or invalid plan
                # Execute remaining steps in order
                ready_steps = list(remaining_steps.keys())
            
            for step_num in sorted(ready_steps):
                ordered_steps.append(step_num)
                completed_steps.add(step_num)
                del remaining_steps[step_num]
        
        plan.execution_order = ordered_steps
        return plan
    
    def _parse_plan_response(
        self,
        content: str,
        user_query: str,
        parsed_query: Optional[ParsedQuery],
    ) -> QueryPlan:
        """Parse plan from LLM response."""
        import json
        try:
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            plan_data = json.loads(content)
            # Reconstruct QueryPlan from JSON
            # This would need proper deserialization logic
            # For now, return a simple plan
            return QueryPlan(
                original_query=user_query,
                plan_steps=[],
                execution_order=[],
            )
        except Exception as e:
            logger.warning(f"Failed to parse plan response: {e}")
            # Return simple plan as fallback
            return QueryPlan(
                original_query=user_query,
                plan_steps=[
                    QueryStep(
                        step_number=1,
                        description="Execute query",
                        required_indices=parsed_query.index_names if parsed_query else [],
                        required_schema_fields=[],
                        sub_query=parsed_query,
                    )
                ],
                execution_order=[1],
            )
```

#### Planner Class

```python
# src/nlap/agentic/planning/planner.py

from typing import List
from nlap.agentic.planning.agent import QueryPlan, QueryStep


class QueryPlanner:
    """Planner for complex multi-step queries."""
    
    @staticmethod
    def plan_correlation_query(
        user_query: str,
        source_indices: List[str],
        correlation_fields: List[str],
    ) -> QueryPlan:
        """Plan a correlation query across multiple indices.
        
        Example:
            User: "Find conversations where user asked about X, 
                   then show agent responses and outcomes"
            
            Plan:
            Step 1: Query conversations index for conversations with query content "X"
            Step 2: Extract conversation IDs
            Step 3: Query agent response events using conversation IDs
            Step 4: Query outcome events using conversation IDs
            Step 5: Correlate and combine results
        """
        steps = []
        
        # Step 1: Find source conversations
        steps.append(QueryStep(
            step_number=1,
            description="Find source conversations matching criteria",
            required_indices=[source_indices[0]] if source_indices else [],
            required_schema_fields=[correlation_fields[0]] if correlation_fields else [],
        ))
        
        # Step 2: Extract correlation IDs
        steps.append(QueryStep(
            step_number=2,
            description="Extract correlation identifiers",
            required_indices=[],
            required_schema_fields=correlation_fields,
            dependencies=[1],
            output_fields=correlation_fields,
        ))
        
        # Step 3: Query related events
        for i, index in enumerate(source_indices[1:], start=3):
            steps.append(QueryStep(
                step_number=i,
                description=f"Query related events from {index}",
                required_indices=[index],
                required_schema_fields=correlation_fields,
                dependencies=[2],
            ))
        
        # Final step: Correlate
        final_step_num = len(steps) + 1
        steps.append(QueryStep(
            step_number=final_step_num,
            description="Correlate results from all steps",
            required_indices=[],
            dependencies=list(range(1, final_step_num)),
        ))
        
        return QueryPlan(
            original_query=user_query,
            plan_steps=steps,
            execution_order=list(range(1, final_step_num + 1)),
            correlation_strategy="id_based",
            correlation_fields=correlation_fields,
        )
```

### Prompt Templates

```text
# prompts/planning_system.txt

You are a query planning expert for OpenSearch.

Your task is to break down complex natural language queries into 
sequential execution steps.

For each step, specify:
- Step number and description
- Required indices
- Required schema fields
- Dependencies on other steps
- Output fields that will be used by subsequent steps

Example query: "Find conversations where user asked about X, 
                then show agent responses grouped by service"

Plan:
Step 1: Query conversations index for conversations matching "X"
  - Index: conversations-*
  - Fields: conv_id, user_query
  - Output: conversation IDs

Step 2: Query agent responses using conversation IDs
  - Index: agent-events-*
  - Fields: conv_id, response, service
  - Dependencies: Step 1 (needs conv_id)
  - Output: Responses with service grouping

Return plan as JSON matching QueryPlan structure.
```

---

## ReAct Pattern

### Overview

ReAct (Reasoning + Acting) enables iterative refinement through observation-thought-action loops. The agent:

1. **Observes**: Current state (query, schema, constraints)
2. **Thinks**: Reasons about what to do next
3. **Acts**: Performs an action (discover schema, refine query, etc.)
4. **Repeats**: Until query is complete and validated

### Implementation

#### ReActOrchestrator Class

```python
# src/nlap/agentic/react/orchestrator.py

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel
from nlap.nlp.models import ParsedQuery
from nlap.nlp.parser import NaturalLanguageParser
from nlap.opensearch.schema_models import SchemaInfo
from nlap.opensearch.query_builder import QueryBuilder
from nlap.opensearch.schema_discovery import SchemaDiscoveryEngine
from nlap.azureopenai.client import AzureOpenAIClient
from nlap.agentic.reflection.agent import ReflectionAgent
from nlap.agentic.planning.agent import PlanningAgent
from nlap.utils.logger import get_logger
from nlap.utils.prompt_loader import load_prompt

logger = get_logger(__name__)


class ActionType(str, Enum):
    """Types of actions available to ReAct agent."""
    
    DISCOVER_SCHEMA = "discover_schema"
    PARSE_QUERY = "parse_query"
    REFLECT_ON_QUERY = "reflect_on_query"
    REFINE_QUERY = "refine_query"
    BUILD_QUERY = "build_query"
    VALIDATE_QUERY = "validate_query"
    PLAN_QUERY = "plan_query"


class ReActObservation(BaseModel):
    """Observation from environment."""
    
    observation_type: str
    description: str
    data: Dict[str, Any]


class ReActThought(BaseModel):
    """Agent's thought/reasoning."""
    
    reasoning: str
    next_action: Optional[ActionType] = None
    action_params: Dict[str, Any] = {}


class ReActStep(BaseModel):
    """A single ReAct step (observation-thought-action)."""
    
    step_number: int
    observation: ReActObservation
    thought: ReActThought
    action_result: Optional[Dict[str, Any]] = None


class ReActOrchestrator:
    """Orchestrator for ReAct pattern query processing."""
    
    def __init__(
        self,
        azure_client: AzureOpenAIClient,
        schema_discovery: SchemaDiscoveryEngine,
        parser: NaturalLanguageParser,
        query_builder: QueryBuilder,
        max_iterations: int = 10,
    ):
        """Initialize ReAct orchestrator.
        
        Args:
            azure_client: Azure OpenAI client
            schema_discovery: Schema discovery engine
            parser: Natural language parser
            query_builder: Query builder
            max_iterations: Maximum ReAct loop iterations
        """
        self.azure_client = azure_client
        self.schema_discovery = schema_discovery
        self.parser = parser
        self.query_builder = query_builder
        self.max_iterations = max_iterations
        self.reflection_agent = ReflectionAgent(azure_client)
        self.planning_agent = PlanningAgent(azure_client, schema_discovery)
        
        # Available tools
        from nlap.agentic.react.tools import ReActTools
        self.tools = ReActTools(
            schema_discovery, parser, query_builder, self.reflection_agent
        )
    
    async def process_query(
        self,
        user_query: str,
        index_names: Optional[List[str]] = None,
        discover_fields: bool = True,
    ) -> Dict[str, Any]:
        """Process query using ReAct pattern.
        
        Args:
            user_query: Natural language query
            index_names: Optional target indices
            discover_fields: Whether to discover schema
            
        Returns:
            Dictionary with final query and execution trace
        """
        steps = []
        current_state = {
            "query": user_query,
            "index_names": index_names or [],
            "schema_info": None,
            "parsed_query": None,
            "opensearch_query": None,
            "confidence": 0.0,
        }
        
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            
            # 1. Observe current state
            observation = self._observe(current_state)
            
            # 2. Think about next action
            thought = await self._think(observation, current_state, steps)
            
            # 3. Act based on thought
            if thought.next_action:
                action_result = await self._act(
                    thought.next_action, thought.action_params, current_state
                )
            else:
                break
            
            # 4. Update state
            current_state.update(action_result.get("state_updates", {}))
            
            # 5. Record step
            steps.append(ReActStep(
                step_number=iteration,
                observation=observation,
                thought=thought,
                action_result=action_result,
            ))
            
            # 6. Check termination conditions
            if self._should_terminate(current_state, thought):
                break
        
        return {
            "final_query": current_state.get("opensearch_query"),
            "parsed_query": current_state.get("parsed_query"),
            "schema_info": current_state.get("schema_info"),
            "confidence": current_state.get("confidence"),
            "steps": [step.model_dump() for step in steps],
            "iterations": iteration,
        }
    
    def _observe(self, state: Dict[str, Any]) -> ReActObservation:
        """Observe current state."""
        
        # Determine what's missing or needs attention
        if not state.get("schema_info") and state.get("index_names"):
            return ReActObservation(
                observation_type="missing_schema",
                description="Schema not discovered for indices",
                data={"indices": state["index_names"]},
            )
        
        if not state.get("parsed_query"):
            return ReActObservation(
                observation_type="query_not_parsed",
                description="Query has not been parsed yet",
                data={"query": state["query"]},
            )
        
        if not state.get("opensearch_query"):
            return ReActObservation(
                observation_type="query_not_built",
                description="OpenSearch query not built yet",
                data={"parsed_query": state["parsed_query"]},
            )
        
        # Query built, check if validation needed
        return ReActObservation(
            observation_type="query_ready",
            description="Query is built and ready for validation",
            data={
                "confidence": state.get("confidence", 0.0),
                "has_schema": state.get("schema_info") is not None,
            },
        )
    
    async def _think(
        self,
        observation: ReActObservation,
        state: Dict[str, Any],
        previous_steps: List[ReActStep],
    ) -> ReActThought:
        """Think about next action using LLM."""
        
        thought_prompt = self._build_thought_prompt(
            observation, state, previous_steps
        )
        
        messages = [
            {"role": "system", "content": load_prompt("react_system.txt")},
            {"role": "user", "content": thought_prompt},
        ]
        
        response = await self.azure_client.chat_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=1500,
        )
        
        content = response["choices"][0]["message"]["content"]
        return self._parse_thought_response(content, observation)
    
    async def _act(
        self,
        action_type: ActionType,
        action_params: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute action."""
        
        if action_type == ActionType.DISCOVER_SCHEMA:
            return await self.tools.discover_schema(
                state["index_names"][0] if state["index_names"] else None,
                action_params,
            )
        
        elif action_type == ActionType.PARSE_QUERY:
            return await self.tools.parse_query(
                state["query"],
                state["index_names"],
                state.get("schema_info"),
            )
        
        elif action_type == ActionType.REFLECT_ON_QUERY:
            return await self.tools.reflect_on_query(
                state["parsed_query"],
                state["query"],
                state.get("opensearch_query"),
            )
        
        elif action_type == ActionType.BUILD_QUERY:
            return await self.tools.build_query(
                state["parsed_query"],
                action_params,
            )
        
        elif action_type == ActionType.PLAN_QUERY:
            return await self.tools.plan_query(
                state["query"],
                state["parsed_query"],
            )
        
        else:
            logger.warning(f"Unknown action type: {action_type}")
            return {"state_updates": {}}
    
    def _should_terminate(
        self, state: Dict[str, Any], thought: ReActThought
    ) -> bool:
        """Determine if ReAct loop should terminate."""
        
        # Terminate if query is built and validated
        if state.get("opensearch_query"):
            confidence = state.get("confidence", 0.0)
            if confidence > 0.8:
                return True
        
        # Terminate if next action is None (agent thinks we're done)
        if not thought.next_action:
            return True
        
        return False
    
    def _build_thought_prompt(
        self,
        observation: ReActObservation,
        state: Dict[str, Any],
        previous_steps: List[ReActStep],
    ) -> str:
        """Build prompt for thinking."""
        prompt_parts = [
            f"Current observation: {observation.description}",
            f"\nCurrent state:",
            f"- Query: {state.get('query')}",
            f"- Has schema: {state.get('schema_info') is not None}",
            f"- Has parsed query: {state.get('parsed_query') is not None}",
            f"- Has OpenSearch query: {state.get('opensearch_query') is not None}",
            f"- Confidence: {state.get('confidence', 0.0)}",
        ]
        if previous_steps:
            prompt_parts.append(f"\nPrevious steps: {len(previous_steps)}")
        return "\n".join(prompt_parts)
    
    def _parse_thought_response(
        self, content: str, observation: ReActObservation
    ) -> ReActThought:
        """Parse thought from LLM response."""
        import json
        try:
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            thought_data = json.loads(content)
            return ReActThought(
                reasoning=thought_data.get("reasoning", ""),
                next_action=ActionType(thought_data.get("next_action")) if thought_data.get("next_action") else None,
                action_params=thought_data.get("action_params", {}),
            )
        except Exception as e:
            logger.warning(f"Failed to parse thought response: {e}")
            # Default action based on observation
            if observation.observation_type == "query_not_parsed":
                return ReActThought(
                    reasoning="Need to parse query first",
                    next_action=ActionType.PARSE_QUERY,
                    action_params={},
                )
            elif observation.observation_type == "missing_schema":
                return ReActThought(
                    reasoning="Need to discover schema",
                    next_action=ActionType.DISCOVER_SCHEMA,
                    action_params={},
                )
            return ReActThought(
                reasoning="Unknown state, need to build query",
                next_action=ActionType.BUILD_QUERY,
                action_params={},
            )
```

#### ReActTools Class

```python
# src/nlap/agentic/react/tools.py

from typing import Dict, Any, Optional, List
from nlap.opensearch.schema_models import SchemaInfo
from nlap.nlp.models import ParsedQuery


class ReActTools:
    """Tools available to ReAct agent."""
    
    def __init__(
        self,
        schema_discovery,
        parser,
        query_builder,
        reflection_agent,
    ):
        """Initialize tools."""
        self.schema_discovery = schema_discovery
        self.parser = parser
        self.query_builder = query_builder
        self.reflection_agent = reflection_agent
    
    async def discover_schema(
        self, index_name: Optional[str], params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Discover schema for index."""
        if not index_name:
            return {"state_updates": {}, "error": "No index specified"}
        
        schema_info = await self.schema_discovery.discover_index_schema(
            index_name,
            sample_size=params.get("sample_size", 500),
            use_cache=True,
        )
        
        return {
            "state_updates": {"schema_info": schema_info},
            "result": f"Discovered {len(schema_info.fields)} fields",
        }
    
    async def parse_query(
        self,
        query: str,
        index_names: Optional[List[str]],
        schema_info: Optional[SchemaInfo],
    ) -> Dict[str, Any]:
        """Parse natural language query."""
        parsed_query = await self.parser.parse(
            query=query,
            index_names=index_names,
            schema_info=schema_info,
        )
        
        return {
            "state_updates": {
                "parsed_query": parsed_query,
                "confidence": parsed_query.confidence,
            },
            "result": f"Parsed query with {len(parsed_query.filters.must)} filters",
        }
    
    async def reflect_on_query(
        self,
        parsed_query: ParsedQuery,
        original_query: str,
        opensearch_query: Optional[dict],
    ) -> Dict[str, Any]:
        """Reflect on parsed query."""
        reflection = await self.reflection_agent.reflect(
            parsed_query, original_query, opensearch_query
        )
        
        state_updates = {
            "confidence": reflection.confidence,
        }
        
        if reflection.refined_query:
            state_updates["parsed_query"] = reflection.refined_query
        
        return {
            "state_updates": state_updates,
            "result": {
                "is_valid": reflection.is_valid,
                "issues": reflection.issues,
                "suggestions": reflection.suggestions,
            },
        }
    
    async def build_query(
        self, parsed_query: ParsedQuery, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build OpenSearch query."""
        self.query_builder.schema_info = params.get("schema_info")
        
        opensearch_query = self.query_builder.build_query(
            parsed_query=parsed_query,
            size=params.get("size"),
            from_=params.get("from_", 0),
        )
        
        return {
            "state_updates": {"opensearch_query": opensearch_query},
            "result": "Query built successfully",
        }
    
    async def plan_query(
        self,
        user_query: str,
        parsed_query: Optional[ParsedQuery],
    ) -> Dict[str, Any]:
        """Plan complex query."""
        from nlap.agentic.planning.agent import PlanningAgent
        planning_agent = PlanningAgent(self.reflection_agent.azure_client, self.schema_discovery)
        plan = await planning_agent.create_plan(user_query, parsed_query)
        
        return {
            "state_updates": {"plan": plan},
            "result": f"Created plan with {len(plan.plan_steps)} steps",
        }
```

### Prompt Templates

```text
# prompts/react_system.txt

You are a ReAct (Reasoning + Acting) agent for query processing.

Your task is to reason about what action to take next based on the current 
state and observations.

Available actions:
- discover_schema: Discover schema for an index
- parse_query: Parse natural language to structured query
- reflect_on_query: Validate and reflect on query quality
- build_query: Build OpenSearch query from parsed query
- validate_query: Validate query against schema

For each observation, think about:
1. What is the current state?
2. What is missing or needs attention?
3. What action should be taken next?
4. What parameters are needed for that action?

Return your thought as JSON:
{
  "reasoning": "Your reasoning about the situation",
  "next_action": "action_type",
  "action_params": {"param1": "value1"}
}
```

---

## Integrated Workflow

### Complete Flow with All Patterns

```python
# src/nlap/api/routes/query_agentic.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from nlap.api.dependencies import (
    get_azure_openai_client,
    get_opensearch_manager,
)
from nlap.agentic.react.orchestrator import ReActOrchestrator
from nlap.nlp.parser import NaturalLanguageParser
from nlap.opensearch.client import OpenSearchManager
from nlap.opensearch.query_builder import QueryBuilder
from nlap.opensearch.schema_discovery import SchemaDiscoveryEngine
from nlap.azureopenai.client import AzureOpenAIClient

router = APIRouter(prefix="/query/agentic", tags=["query"])


class QueryRequest(BaseModel):
    """Request model for agentic query processing."""
    
    query: str = Field(..., description="Natural language query to process")
    index_names: list[str] = Field(
        default_factory=list,
        description="Optional list of OpenSearch index names",
    )
    discover_fields: bool = Field(
        default=True,
        description="Whether to discover schema fields",
    )


@router.post("")
async def process_query_agentic(
    request: QueryRequest,
    azure_openai_client: AzureOpenAIClient = Depends(get_azure_openai_client),
    opensearch_manager: OpenSearchManager = Depends(get_opensearch_manager),
) -> dict:
    """Process query using agentic patterns (ReAct + Planning + Reflection).
    
    This endpoint uses:
    - ReAct: Iterative reasoning and action
    - Planning: Complex query decomposition
    - Reflection: Self-validation and refinement
    """
    # Initialize components
    parser = NaturalLanguageParser(azure_openai_client=azure_openai_client)
    schema_discovery = SchemaDiscoveryEngine(opensearch_manager)
    query_builder = QueryBuilder()
    
    # Initialize ReAct orchestrator
    orchestrator = ReActOrchestrator(
        azure_client=azure_openai_client,
        schema_discovery=schema_discovery,
        parser=parser,
        query_builder=query_builder,
        max_iterations=10,
    )
    
    # Process query using ReAct
    result = await orchestrator.process_query(
        user_query=request.query,
        index_names=request.index_names if request.index_names else None,
        discover_fields=request.discover_fields,
    )
    
    return {
        "success": True,
        "opensearch_query": result["final_query"],
        "parsed_query": result["parsed_query"].model_dump() if result["parsed_query"] else None,
        "confidence": result["confidence"],
        "execution_trace": {
            "steps": result["steps"],
            "iterations": result["iterations"],
        },
    }
```

---

## Configuration

### Settings Extension

```python
# src/nlap/config/settings.py (addition)

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class AgenticSettings(BaseSettings):
    """Agentic patterns configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="AGENTIC_",
        env_file=".env",
        case_sensitive=False,
    )
    
    # Reflection settings
    enable_reflection: bool = Field(default=True, description="Enable reflection pattern")
    max_reflections: int = Field(default=3, description="Max reflection iterations")
    
    # Planning settings
    enable_planning: bool = Field(default=True, description="Enable planning pattern")
    complexity_threshold: float = Field(default=0.5, description="Complexity threshold for planning")
    
    # ReAct settings
    enable_react: bool = Field(default=True, description="Enable ReAct pattern")
    max_react_iterations: int = Field(default=10, description="Max ReAct loop iterations")
    
    # LLM settings for agentic patterns
    reflection_temperature: float = Field(default=0.3, description="Temperature for reflection")
    planning_temperature: float = Field(default=0.3, description="Temperature for planning")
    react_temperature: float = Field(default=0.3, description="Temperature for ReAct")


class Settings(BaseSettings):
    # ... existing fields ...
    agentic: AgenticSettings = Field(default_factory=AgenticSettings)
```

### Environment Variables

```bash
# .env.example additions

# Agentic Patterns Configuration
AGENTIC_ENABLE_REFLECTION=true
AGENTIC_MAX_REFLECTIONS=3
AGENTIC_ENABLE_PLANNING=true
AGENTIC_COMPLEXITY_THRESHOLD=0.5
AGENTIC_ENABLE_REACT=true
AGENTIC_MAX_REACT_ITERATIONS=10
AGENTIC_REFLECTION_TEMPERATURE=0.3
AGENTIC_PLANNING_TEMPERATURE=0.3
AGENTIC_REACT_TEMPERATURE=0.3
```

---

## Testing Strategy

### Unit Tests

```python
# tests/unit/test_reflection_agent.py

import pytest
from nlap.agentic.reflection.agent import ReflectionAgent
from nlap.nlp.models import ParsedQuery, FilterCondition, Filter
from nlap.opensearch.schema_models import SchemaInfo, FieldInfo, FieldType


@pytest.mark.asyncio
async def test_reflection_validates_schema():
    """Test that reflection validates fields against schema."""
    # Mock schema with known fields
    schema_info = SchemaInfo(
        index_name="test-index",
        fields={
            "valid_field": FieldInfo(name="valid_field", field_type=FieldType.TEXT),
        },
    )
    
    agent = ReflectionAgent(azure_client=mock_client, schema_info=schema_info)
    
    parsed_query = ParsedQuery(
        original_query="Find documents with field 'invalid_field'",
        filters=Filter(must=[FilterCondition(field="invalid_field", operator="equals", value="test")]),
    )
    
    result = await agent.reflect(parsed_query, "Find documents with field 'invalid_field'")
    
    assert not result.is_valid
    assert len(result.issues) > 0
    assert "invalid_field" in str(result.issues[0])


# tests/unit/test_planning_agent.py
# tests/unit/test_react_orchestrator.py
```

### Integration Tests

```python
# tests/integration/test_agentic_patterns.py

import pytest
from nlap.agentic.react.orchestrator import ReActOrchestrator


@pytest.mark.asyncio
async def test_complex_correlation_query():
    """Test complex query requiring planning and reflection."""
    orchestrator = ReActOrchestrator(...)
    
    result = await orchestrator.process_query(
        "Find conversations where user asked about X, then show agent responses grouped by service"
    )
    
    assert result["final_query"] is not None
    assert result["confidence"] > 0.7
    assert len(result["steps"]) > 1  # Should have multiple steps
```

---

## Examples

### Example 1: Simple Query with Reflection

```
User Query: "Show me all events from the last 4 days"

ReAct Flow:
1. Observe: Query not parsed, schema not discovered
2. Think: Need to parse query first, then discover schema if needed
3. Act: Parse query → discovers date range and index names
4. Observe: Query parsed, but schema not discovered
5. Think: Should discover schema for field validation
6. Act: Discover schema for index
7. Observe: Schema discovered, query parsed
8. Think: Should build OpenSearch query
9. Act: Build query
10. Observe: Query built
11. Think: Should reflect on query quality
12. Act: Reflect → validates query, finds no issues
13. Terminate: Query ready with high confidence
```

### Example 2: Complex Query with Planning

```
User Query: "Find conversations where user asked about 'agent selection', 
             then show the agent responses and their completion status, 
             grouped by service"

Planning Steps:
1. Plan created with 5 steps:
   - Step 1: Query conversations index for "agent selection"
   - Step 2: Extract conversation IDs
   - Step 3: Query agent responses using conversation IDs
   - Step 4: Query completion events and correlate
   - Step 5: Group by service and aggregate

ReAct Flow:
1. Observe: Complex query requiring planning
2. Think: Should create execution plan
3. Act: Create plan → identifies 5 sequential steps
4. Observe: Plan created, need to execute steps
5. Think: Start with Step 1
6. Act: Execute Step 1 → find conversations
7. ... continue for each step ...
8. Observe: All steps completed
9. Think: Build final correlated query
10. Act: Build composite query
11. Reflect: Validate final query
12. Terminate: Query ready
```

### Example 3: Query Refinement with Reflection

```
User Query: "Count response times by service"

Initial Parsed Query:
- Aggregation: COUNT on field "response_time"
- Issue: "response_time" is a numeric field, not suitable for COUNT

Reflection:
- Identifies issue: COUNT on numeric field
- Suggests: Use AVG or SUM instead, or group by service

Refinement:
- Changes aggregation to AVG(response_time)
- Adds group_by: ["service"]
- Validates: AVG is appropriate for numeric field

Final Query:
- Aggregation: AVG on "response_time" grouped by "service"
```

---

## Performance Considerations

### Caching Strategy

1. **Schema Caching**: Already implemented, reuse for agentic patterns
2. **Reflection Results Caching**: Cache reflection results for similar queries
3. **Plan Caching**: Cache plans for common query patterns

### Optimization

1. **Early Termination**: Stop ReAct loop early if confidence is high
2. **Parallel Schema Discovery**: Discover schema for multiple indices in parallel
3. **Incremental Planning**: Only plan complex parts, handle simple parts directly

### Cost Management

1. **LLM Call Reduction**: Use reflection only when needed (complex queries)
2. **Batch Processing**: Batch similar operations
3. **Caching**: Aggressively cache intermediate results

---

## Migration Guide

### Step 1: Add Agentic Module Structure

```bash
mkdir -p src/nlap/agentic/{reflection,planning,react}
touch src/nlap/agentic/__init__.py
touch src/nlap/agentic/reflection/{__init__.py,agent.py,validator.py,models.py}
touch src/nlap/agentic/planning/{__init__.py,agent.py,planner.py,models.py}
touch src/nlap/agentic/react/{__init__.py,orchestrator.py,tools.py,models.py}
```

### Step 2: Create Prompt Templates

```bash
touch prompts/reflection_system.txt
touch prompts/refinement_system.txt
touch prompts/planning_system.txt
touch prompts/react_system.txt
```

### Step 3: Update Dependencies

No new dependencies required - uses existing:
- Azure OpenAI client
- OpenSearch manager
- NLP parser
- Query builder

### Step 4: Add Configuration

Add `AgenticSettings` to `settings.py` as shown in Configuration section.

### Step 5: Create New Endpoint

Add `/query/agentic` endpoint as shown in Integrated Workflow section.

### Step 6: Testing

1. Add unit tests for each pattern
2. Add integration tests for combined flow
3. Test with complex queries

### Step 7: Gradual Rollout

1. Deploy behind feature flag
2. Test with subset of queries
3. Monitor performance and costs
4. Gradually increase adoption

---

## Conclusion

This integration of Reflection, Planning, and ReAct patterns significantly enhances NLAP's capability to handle complex queries with improved accuracy and robustness. The patterns work together to provide:

- **Self-validation** through Reflection
- **Complex query handling** through Planning  
- **Iterative refinement** through ReAct

All patterns integrate seamlessly with existing NLAP architecture while maintaining backward compatibility.

---

This documentation covers:

1. **Architecture**: Component design and integration points
2. **Implementation**: Code examples for each pattern
3. **Integration**: How patterns work together
4. **Configuration**: Settings and environment variables
5. **Testing**: Unit and integration test strategies
6. **Examples**: Real-world usage scenarios
7. **Migration**: Step-by-step integration guide

Use this documentation to integrate the patterns into NLAP. Each section includes implementation details and examples.
