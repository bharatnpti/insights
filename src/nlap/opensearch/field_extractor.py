"""Field extraction from OpenSearch documents with recursive nested object support."""

from typing import Any

from nlap.utils.logger import get_logger

logger = get_logger(__name__)


class FieldExtractor:
    """Extracts fields recursively from documents following Single Responsibility Principle."""

    MAX_SAMPLE_VALUES = 10
    MAX_RECURSION_DEPTH = 20

    def __init__(self, max_sample_values: int = MAX_SAMPLE_VALUES, max_depth: int = MAX_RECURSION_DEPTH):
        """Initialize field extractor.

        Args:
            max_sample_values: Maximum number of sample values to collect per field
            max_depth: Maximum recursion depth for nested objects
        """
        self.max_sample_values = max_sample_values
        self.max_depth = max_depth

    def extract_fields(self, documents: list[dict[str, Any]]) -> dict[str, Any]:
        """Extract all fields from a list of documents recursively.

        Args:
            documents: List of document dictionaries

        Returns:
            Dictionary mapping field paths to their values
        """
        field_values: dict[str, list[Any]] = {}

        for doc in documents:
            self._extract_fields_recursive(doc, field_values, prefix="", depth=0)

        return {path: values for path, values in field_values.items()}

    def _extract_fields_recursive(
        self,
        obj: Any,
        field_values: dict[str, list[Any]],
        prefix: str = "",
        depth: int = 0,
    ) -> None:
        """Recursively extract fields from a nested object.

        Args:
            obj: Object to extract fields from (dict, list, or primitive)
            field_values: Dictionary to store field paths and their values
            prefix: Current field path prefix (for nested fields)
            depth: Current recursion depth
        """
        if depth > self.max_depth:
            logger.warning(
                "Maximum recursion depth reached",
                prefix=prefix,
                depth=depth,
                max_depth=self.max_depth,
            )
            return

        if obj is None:
            return

        if isinstance(obj, dict):
            self._extract_from_dict(obj, field_values, prefix, depth)
        elif isinstance(obj, list):
            self._extract_from_list(obj, field_values, prefix, depth)
        else:
            self._extract_primitive(obj, field_values, prefix)

    def _extract_from_dict(
        self,
        obj: dict[str, Any],
        field_values: dict[str, list[Any]],
        prefix: str,
        depth: int,
    ) -> None:
        """Extract fields from a dictionary object.

        Args:
            obj: Dictionary to process
            field_values: Dictionary to store field paths and values
            prefix: Current field path prefix
            depth: Current recursion depth
        """
        for key, value in obj.items():
            field_path = f"{prefix}.{key}" if prefix else key

            if isinstance(value, (dict, list)):
                # Recursively process nested structures
                self._extract_fields_recursive(value, field_values, field_path, depth + 1)
            else:
                # Store primitive value
                self._extract_primitive(value, field_values, field_path)

    def _extract_from_list(
        self,
        obj: list[Any],
        field_values: dict[str, list[Any]],
        prefix: str,
        depth: int,
    ) -> None:
        """Extract fields from a list/array object.

        Args:
            obj: List to process
            field_values: Dictionary to store field paths and values
            prefix: Current field path prefix
            depth: Current recursion depth
        """
        if not obj:
            return

        # For arrays, we check the first non-None element to determine structure
        first_element = next((item for item in obj if item is not None), None)

        if first_element is None:
            return

        if isinstance(first_element, (dict, list)):
            # If array contains objects/arrays, recursively process each element
            for idx, item in enumerate(obj[:5]):  # Limit to first 5 items to avoid explosion
                if item is not None:
                    self._extract_fields_recursive(item, field_values, prefix, depth + 1)
        else:
            # Array of primitives - store values for the array field itself
            self._extract_primitive(obj, field_values, prefix)

    def _extract_primitive(
        self,
        value: Any,
        field_values: dict[str, list[Any]],
        prefix: str,
    ) -> None:
        """Extract and store a primitive field value.

        Args:
            value: Primitive value to store
            field_values: Dictionary to store field paths and values
            prefix: Current field path
        """
        if prefix not in field_values:
            field_values[prefix] = []

        # Only store up to max_sample_values
        if len(field_values[prefix]) < self.max_sample_values:
            field_values[prefix].append(value)

