"""Field type identification and categorization."""

import json
from datetime import datetime
from typing import Any

from nlap.opensearch.schema_models import FieldType
from nlap.utils.logger import get_logger

logger = get_logger(__name__)


class TypeIdentifier:
    """Identifies field types from sample values following Single Responsibility Principle."""

    def __init__(self):
        """Initialize type identifier."""
        self._date_formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
        ]

    def identify_field_type(self, field_name: str, sample_values: list[Any]) -> FieldType:
        """Identify the field type from sample values.

        Args:
            field_name: Name of the field
            sample_values: List of sample values for the field

        Returns:
            Detected FieldType
        """
        if not sample_values:
            return FieldType.UNKNOWN

        # Filter out None values for type detection
        valid_samples = [v for v in sample_values if v is not None]
        if not valid_samples:
            return FieldType.UNKNOWN

        # Check if it's an array (values are lists)
        if all(isinstance(v, list) for v in valid_samples):
            # Check the type of array elements
            array_elements = [item for sublist in valid_samples for item in (sublist if isinstance(sublist, list) else [])]
            if array_elements:
                element_type = self._identify_primitive_type(array_elements)
                logger.debug(
                    "Identified array field type",
                    field_name=field_name,
                    element_type=element_type.value,
                )
                return FieldType.ARRAY
            return FieldType.ARRAY

        # Check if it's a nested object
        if all(isinstance(v, dict) for v in valid_samples):
            logger.debug("Identified object field type", field_name=field_name)
            return FieldType.OBJECT

        # Identify primitive type
        return self._identify_primitive_type(valid_samples)

    def _identify_primitive_type(self, samples: list[Any]) -> FieldType:
        """Identify primitive field type from samples.

        Args:
            samples: List of sample values

        Returns:
            Detected FieldType
        """
        # Boolean check
        if all(isinstance(v, bool) for v in samples):
            return FieldType.BOOLEAN

        # Numeric check
        if all(self._is_numeric(v) for v in samples):
            return FieldType.NUMERIC

        # Date check
        if all(self._is_date(v) for v in samples):
            return FieldType.DATE

        # IP address check (basic pattern)
        if all(self._is_ip_address(v) for v in samples):
            return FieldType.IP

        # Geo point check (lat,lon pattern or geo_json)
        if all(self._is_geo_point(v) for v in samples):
            return FieldType.GEO_POINT

        # Text/keyword (default for strings)
        if all(isinstance(v, str) for v in samples):
            # Check average length to distinguish text vs keyword
            avg_length = sum(len(str(v)) for v in samples) / len(samples)
            if avg_length > 256:
                return FieldType.TEXT
            return FieldType.KEYWORD

        # Binary check
        if all(isinstance(v, (bytes, bytearray)) for v in samples):
            return FieldType.BINARY

        # Default to unknown for mixed types
        return FieldType.UNKNOWN

    def _is_numeric(self, value: Any) -> bool:
        """Check if value is numeric.

        Args:
            value: Value to check

        Returns:
            True if numeric
        """
        if isinstance(value, (int, float, complex)):
            return True
        if isinstance(value, str):
            try:
                float(value)
                return True
            except (ValueError, TypeError):
                return False
        return False

    def _is_date(self, value: Any) -> bool:
        """Check if value is a date/datetime.

        Args:
            value: Value to check

        Returns:
            True if date
        """
        if isinstance(value, (datetime,)):
            return True
        if isinstance(value, str):
            # Try parsing as ISO format or common formats
            for fmt in self._date_formats:
                try:
                    datetime.strptime(value, fmt)
                    return True
                except (ValueError, TypeError):
                    continue
            # Try ISO format without explicit format
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
                return True
            except (ValueError, TypeError):
                pass
        return False

    def _is_ip_address(self, value: Any) -> bool:
        """Check if value is an IP address.

        Args:
            value: Value to check

        Returns:
            True if IP address
        """
        if not isinstance(value, str):
            return False

        import ipaddress

        try:
            ipaddress.ip_address(value)
            return True
        except ValueError:
            return False

    def _is_geo_point(self, value: Any) -> bool:
        """Check if value is a geo point.

        Args:
            value: Value to check

        Returns:
            True if geo point
        """
        if isinstance(value, str):
            # Check lat,lon format
            parts = value.split(",")
            if len(parts) == 2:
                try:
                    float(parts[0].strip())
                    float(parts[1].strip())
                    return True
                except (ValueError, TypeError):
                    pass

        if isinstance(value, dict):
            # Check geo_json format
            if "lat" in value and "lon" in value:
                try:
                    float(value["lat"])
                    float(value["lon"])
                    return True
                except (ValueError, TypeError):
                    pass
            # Check GeoJSON Point format
            if value.get("type") == "Point" and "coordinates" in value:
                coords = value["coordinates"]
                if isinstance(coords, list) and len(coords) == 2:
                    try:
                        float(coords[0])
                        float(coords[1])
                        return True
                    except (ValueError, TypeError):
                        pass

        return False

