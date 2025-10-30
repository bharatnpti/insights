"""Query intent classification utilities."""

from typing import Optional

from nlap.nlp.models import QueryIntent, QueryIntentCategory
from nlap.utils.logger import get_logger

logger = get_logger(__name__)


class IntentClassifier:
    """Classify query intent from natural language text."""

    # Intent keywords mapping
    INTENT_KEYWORDS = {
        QueryIntentCategory.CORRELATION: [
            "correlation",
            "correlate",
            "relationship",
            "relationship between",
            "correlated with",
            "association",
            "link between",
        ],
        QueryIntentCategory.TREND: [
            "trend",
            "over time",
            "time series",
            "change over",
            "over the past",
            "over the last",
            "growth",
            "decline",
            "increase",
            "decrease",
        ],
        QueryIntentCategory.DISTRIBUTION: [
            "distribution",
            "spread",
            "frequency",
            "how many",
            "count by",
            "group by",
            "breakdown",
        ],
        QueryIntentCategory.COMPARISON: [
            "compare",
            "comparison",
            "versus",
            "vs",
            "vs.",
            "compared to",
            "against",
            "difference between",
            "a/b test",
            "ab test",
        ],
        QueryIntentCategory.AGGREGATION: [
            "sum",
            "total",
            "average",
            "count",
            "min",
            "max",
            "aggregate",
            "statistics",
        ],
        QueryIntentCategory.FILTER: [
            "where",
            "filter",
            "show",
            "find",
            "search",
            "with",
            "having",
        ],
        QueryIntentCategory.SEARCH: [
            "search",
            "find",
            "look for",
            "query",
        ],
    }

    # Suggested visualizations by intent
    VISUALIZATION_MAP = {
        QueryIntentCategory.CORRELATION: "scatter_plot",
        QueryIntentCategory.TREND: "line_chart",
        QueryIntentCategory.DISTRIBUTION: "histogram",
        QueryIntentCategory.COMPARISON: "bar_chart",
        QueryIntentCategory.AGGREGATION: "table",
        QueryIntentCategory.FILTER: "table",
        QueryIntentCategory.SEARCH: "table",
    }

    @classmethod
    def classify_intent(
        cls, query: str, schema_fields: Optional[list[str]] = None
    ) -> QueryIntent:
        """Classify query intent from natural language text.

        Args:
            query: Natural language query text
            schema_fields: Optional list of known schema fields

        Returns:
            QueryIntent object with classification
        """
        if not query:
            return QueryIntent(
                category=QueryIntentCategory.UNKNOWN,
                confidence=0.0,
                description="Empty query",
            )

        query_lower = query.lower()
        intent_scores: dict[QueryIntentCategory, float] = {}

        # Score each intent category based on keyword matches
        for category, keywords in cls.INTENT_KEYWORDS.items():
            score = 0.0
            matches = 0

            for keyword in keywords:
                if keyword.lower() in query_lower:
                    matches += 1
                    # Weight longer keywords more heavily
                    score += len(keyword) / 10.0

            # Normalize score
            if matches > 0:
                intent_scores[category] = min(score / len(keywords), 1.0)
            else:
                intent_scores[category] = 0.0

        # Special handling for complex queries
        # If query contains multiple intent indicators, use the highest scoring one
        # or default to AGGREGATION if multiple are close
        if len([s for s in intent_scores.values() if s > 0.3]) > 1:
            # Multiple intents detected - prefer more specific ones
            sorted_intents = sorted(
                intent_scores.items(), key=lambda x: x[1], reverse=True
            )
            top_intent = sorted_intents[0]

            # If top two are close, prefer AGGREGATION or COMPARISON
            if (
                len(sorted_intents) > 1
                and sorted_intents[1][1] > top_intent[1] * 0.8
            ):
                # Check if one is AGGREGATION or COMPARISON
                for category, score in sorted_intents[:2]:
                    if category in [
                        QueryIntentCategory.AGGREGATION,
                        QueryIntentCategory.COMPARISON,
                    ]:
                        return cls._create_intent(category, score, query)

            return cls._create_intent(top_intent[0], top_intent[1], query)

        # Find the highest scoring intent
        if intent_scores:
            max_category = max(intent_scores.items(), key=lambda x: x[1])
            return cls._create_intent(max_category[0], max_category[1], query)

        # Default to UNKNOWN if no intent detected
        return QueryIntent(
            category=QueryIntentCategory.UNKNOWN,
            confidence=0.1,
            description="No clear intent detected",
        )

    @classmethod
    def _create_intent(
        cls, category: QueryIntentCategory, confidence: float, query: str
    ) -> QueryIntent:
        """Create QueryIntent object with metadata.

        Args:
            category: Intent category
            confidence: Confidence score (0-1)
            query: Original query text

        Returns:
            QueryIntent object
        """
        # Normalize confidence to 0-1 range
        normalized_confidence = max(0.0, min(1.0, confidence))

        # Generate description
        descriptions = {
            QueryIntentCategory.CORRELATION: "Query seeks to find correlations or relationships between fields",
            QueryIntentCategory.TREND: "Query seeks to analyze trends over time",
            QueryIntentCategory.DISTRIBUTION: "Query seeks to analyze distribution of data",
            QueryIntentCategory.COMPARISON: "Query seeks to compare different values or groups",
            QueryIntentCategory.AGGREGATION: "Query seeks to perform aggregations (sum, count, etc.)",
            QueryIntentCategory.FILTER: "Query seeks to filter and retrieve specific data",
            QueryIntentCategory.SEARCH: "Query seeks to search for specific data",
        }

        description = descriptions.get(category, "Query intent classified")
        suggested_visualization = cls.VISUALIZATION_MAP.get(category)

        return QueryIntent(
            category=category,
            confidence=normalized_confidence,
            description=description,
            suggested_visualization=suggested_visualization,
        )

