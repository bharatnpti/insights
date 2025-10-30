"""Entity extraction utilities for natural language queries."""

import re
from typing import Any, Optional

from nlap.utils.logger import get_logger

logger = get_logger(__name__)


class EntityExtractor:
    """Extract entities (field names, values, operators) from natural language text."""

    # Common operators and their variations
    OPERATOR_PATTERNS = {
        "equals": [r"equals?", r"equal to", r"is", r"==", r"="],
        "not_equals": [r"not equal", r"not equals", r"!=", r"<>", r"is not"],
        "greater_than": [r"greater than", r"more than", r">", r"above", r"over"],
        "less_than": [r"less than", r"fewer than", r"<", r"below", r"under"],
        "contains": [r"contains?", r"has", r"includes?"],
        "starts_with": [r"starts? with", r"begins? with"],
        "ends_with": [r"ends? with"],
        "in": [r"in", r"among", r"within"],
    }

    @classmethod
    def extract_field_names(cls, text: str, known_fields: Optional[list[str]] = None) -> list[str]:
        """Extract potential field names from text.

        Args:
            text: Natural language query text
            known_fields: Optional list of known field names to match against

        Returns:
            List of potential field names found
        """
        if not text:
            return []

        # If we have known fields, try to match them
        if known_fields:
            found_fields = []
            text_lower = text.lower()
            for field in known_fields:
                # Check for exact field name match (case-insensitive) using word boundary
                field_pattern = re.compile(
                    rf"\b{re.escape(field.lower())}\b", re.IGNORECASE
                )
                if field_pattern.search(text):
                    found_fields.append(field)

            return list(set(found_fields))  # Remove duplicates

        # If no known fields, try to extract potential field names using patterns
        # Look for patterns like "field name", "field_name", etc.
        potential_fields = []
        words = text.split()

        # Look for quoted strings (often field names)
        quoted_pattern = re.compile(r'"([^"]+)"')
        quoted = quoted_pattern.findall(text)
        potential_fields.extend(quoted)

        # Look for camelCase or snake_case patterns
        camel_case_pattern = re.compile(r"\b[a-z]+([A-Z][a-z]+)+\b")
        snake_case_pattern = re.compile(r"\b[a-z]+(_[a-z]+)+\b")

        camel_matches = camel_case_pattern.findall(text)
        snake_matches = snake_case_pattern.findall(text)

        potential_fields.extend(camel_matches)
        potential_fields.extend(snake_matches)

        return list(set(potential_fields))

    @classmethod
    def extract_operators(cls, text: str) -> list[str]:
        """Extract operator mentions from text.

        Args:
            text: Natural language query text

        Returns:
            List of operators found
        """
        if not text:
            return []

        found_operators = []
        text_lower = text.lower()

        for operator, patterns in cls.OPERATOR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    found_operators.append(operator)
                    break  # Found this operator, move to next

        return list(set(found_operators))

    @classmethod
    def extract_values(cls, text: str) -> list[Any]:
        """Extract potential values from text.

        Args:
            text: Natural language query text

        Returns:
            List of extracted values
        """
        if not text:
            return []

        values = []

        # Extract quoted strings
        quoted_pattern = re.compile(r'"([^"]+)"|\'([^\']+)\'')
        quoted = quoted_pattern.findall(text)
        for match in quoted:
            value = match[0] or match[1]
            if value:
                values.append(value)

        # Extract numbers
        number_pattern = re.compile(r"-?\d+\.?\d*")
        numbers = number_pattern.findall(text)
        values.extend([float(n) if "." in n else int(n) for n in numbers])

        # Extract boolean values
        text_lower = text.lower()
        if "true" in text_lower or "yes" in text_lower:
            values.append(True)
        if "false" in text_lower or "no" in text_lower:
            values.append(False)

        return values

    @classmethod
    def extract_aggregation_keywords(cls, text: str) -> list[str]:
        """Extract aggregation keywords from text.

        Args:
            text: Natural language query text

        Returns:
            List of aggregation types mentioned
        """
        if not text:
            return []

        aggregations = []
        text_lower = text.lower()

        aggregation_keywords = {
            "count": ["count", "number of", "how many", "total count"],
            "sum": ["sum", "total", "add up", "sum of"],
            "avg": ["average", "avg", "mean"],
            "min": ["minimum", "min", "least", "lowest"],
            "max": ["maximum", "max", "most", "highest", "largest"],
            "percentage": ["percentage", "percent", "%", "ratio"],
            "correlation": ["correlation", "correlate", "relationship between"],
        }

        for agg_type, keywords in aggregation_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    aggregations.append(agg_type)
                    break

        return list(set(aggregations))

    @classmethod
    def extract_time_periods(cls, text: str) -> list[str]:
        """Extract time period mentions from text.

        Args:
            text: Natural language query text

        Returns:
            List of time period mentions
        """
        if not text:
            return []

        time_periods = []
        text_lower = text.lower()

        # Common time period patterns
        patterns = [
            r"last\s+\d+\s+(day|days|week|weeks|month|months|year|years)",
            r"past\s+\d+\s+(day|days|week|weeks|month|months|year|years)",
            r"next\s+\d+\s+(day|days|week|weeks|month|months|year|years)",
            r"this\s+(week|month|year)",
            r"today",
            r"yesterday",
            r"tomorrow",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            time_periods.extend(matches)

        return list(set(time_periods))

    @classmethod
    def extract_group_by_keywords(cls, text: str) -> list[str]:
        """Extract group-by indicators from text.

        Args:
            text: Natural language query text

        Returns:
            List of group-by indicators
        """
        if not text:
            return []

        indicators = []
        text_lower = text.lower()

        group_by_patterns = [
            r"group\s+by\s+(\w+)",
            r"by\s+(\w+)",
            r"per\s+(\w+)",
            r"for\s+each\s+(\w+)",
            r"for\s+every\s+(\w+)",
        ]

        for pattern in group_by_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            indicators.extend(matches)

        return list(set(indicators))

