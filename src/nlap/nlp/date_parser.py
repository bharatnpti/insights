"""Date range parsing utilities for natural language queries."""

import re
from datetime import datetime, timedelta
from typing import Optional

from dateutil.parser import parse as date_parse
from dateutil.relativedelta import relativedelta

from nlap.nlp.models import DateRange
from nlap.utils.logger import get_logger

logger = get_logger(__name__)


class DateRangeParser:
    """Parse date ranges from natural language text."""

    # Patterns for relative date ranges
    RELATIVE_PATTERNS = [
        (r"last\s+(\d+)\s+(day|days|hour|hours|week|weeks|month|months|year|years)", "last"),
        (r"past\s+(\d+)\s+(day|days|hour|hours|week|weeks|month|months|year|years)", "last"),
        (r"previous\s+(\d+)\s+(day|days|hour|hours|week|weeks|month|months|year|years)", "last"),
        (r"next\s+(\d+)\s+(day|days|hour|hours|week|weeks|month|months|year|years)", "next"),
        (r"this\s+(day|week|month|year)", "this"),
        (r"today", "today"),
        (r"yesterday", "yesterday"),
        (r"tomorrow", "tomorrow"),
        (r"this\s+week", "this_week"),
        (r"last\s+week", "last_week"),
        (r"next\s+week", "next_week"),
        (r"this\s+month", "this_month"),
        (r"last\s+month", "last_month"),
        (r"next\s+month", "next_month"),
        (r"this\s+year", "this_year"),
        (r"last\s+year", "last_year"),
        (r"next\s+year", "next_year"),
    ]

    # Date range patterns (e.g., "October 27-30", "2024-01-01 to 2024-01-31")
    RANGE_PATTERNS = [
        (r"(\w+\s+\d{1,2})\s*-\s*(\w+\s+\d{1,2})", "month_day_range"),
        (r"(\d{4}-\d{2}-\d{2})\s*to\s*(\d{4}-\d{2}-\d{2})", "iso_range"),
        (r"(\d{4}-\d{2}-\d{2})\s*-\s*(\d{4}-\d{2}-\d{2})", "iso_range"),
        (r"from\s+([\w\s,]+)\s+to\s+([\w\s,]+)", "from_to_range"),
    ]

    @classmethod
    def parse_date_range(cls, text: str, reference_date: Optional[datetime] = None) -> Optional[DateRange]:
        """Parse date range from natural language text.

        Args:
            text: Natural language text containing date range
            reference_date: Reference date for relative dates (defaults to now)

        Returns:
            DateRange object or None if no date range found
        """
        if not text:
            return None

        reference = reference_date or datetime.utcnow()
        text_lower = text.lower().strip()

        # Try relative patterns first
        for pattern, pattern_type in cls.RELATIVE_PATTERNS:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                date_range = cls._parse_relative_pattern(match, pattern_type, reference)
                if date_range:
                    return date_range

        # Try date range patterns
        for pattern, pattern_type in cls.RANGE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_range = cls._parse_range_pattern(match, pattern_type, reference)
                if date_range:
                    return date_range

        # Try parsing as single date
        single_date = cls._parse_single_date(text, reference)
        if single_date:
            return DateRange(
                start_date=single_date,
                end_date=single_date,
                start_date_str=text,
                end_date_str=text,
                is_relative=False,
            )

        logger.debug("No date range found in text", text=text)
        return None

    @classmethod
    def _parse_relative_pattern(
        cls, match: re.Match, pattern_type: str, reference: datetime
    ) -> Optional[DateRange]:
        """Parse relative date pattern.

        Args:
            match: Regex match object
            pattern_type: Type of pattern matched
            reference: Reference date

        Returns:
            DateRange object or None
        """
        try:
            if pattern_type == "last":
                groups = match.groups()
                if len(groups) >= 2:
                    amount = int(groups[0])
                    unit = groups[1].lower()
                    end_date = reference
                    start_date = cls._subtract_time(end_date, amount, unit)
                    relative_period = f"last {amount} {unit}"
                    return DateRange(
                        start_date=start_date,
                        end_date=end_date,
                        relative_period=relative_period,
                        is_relative=True,
                    )

            elif pattern_type == "next":
                groups = match.groups()
                if len(groups) >= 2:
                    amount = int(groups[0])
                    unit = groups[1].lower()
                    start_date = reference
                    end_date = cls._add_time(start_date, amount, unit)
                    relative_period = f"next {amount} {unit}"
                    return DateRange(
                        start_date=start_date,
                        end_date=end_date,
                        relative_period=relative_period,
                        is_relative=True,
                    )

            elif pattern_type == "today":
                start_date = reference.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=1) - timedelta(microseconds=1)
                return DateRange(
                    start_date=start_date,
                    end_date=end_date,
                    relative_period="today",
                    is_relative=True,
                )

            elif pattern_type == "yesterday":
                yesterday = reference - timedelta(days=1)
                start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=1) - timedelta(microseconds=1)
                return DateRange(
                    start_date=start_date,
                    end_date=end_date,
                    relative_period="yesterday",
                    is_relative=True,
                )

            elif pattern_type == "this_week":
                start_date = reference - timedelta(days=reference.weekday())
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=7) - timedelta(microseconds=1)
                return DateRange(
                    start_date=start_date,
                    end_date=end_date,
                    relative_period="this week",
                    is_relative=True,
                )

            elif pattern_type == "last_week":
                last_week_start = reference - timedelta(days=reference.weekday() + 7)
                start_date = last_week_start.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=7) - timedelta(microseconds=1)
                return DateRange(
                    start_date=start_date,
                    end_date=end_date,
                    relative_period="last week",
                    is_relative=True,
                )

            elif pattern_type == "this_month":
                start_date = reference.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + relativedelta(months=1) - timedelta(microseconds=1)
                return DateRange(
                    start_date=start_date,
                    end_date=end_date,
                    relative_period="this month",
                    is_relative=True,
                )

            elif pattern_type == "last_month":
                start_date = (reference - relativedelta(months=1)).replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )
                end_date = start_date + relativedelta(months=1) - timedelta(microseconds=1)
                return DateRange(
                    start_date=start_date,
                    end_date=end_date,
                    relative_period="last month",
                    is_relative=True,
                )

            elif pattern_type == "this":
                unit = match.groups()[0] if match.groups() else "day"
                if unit == "day":
                    start_date = reference.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_date = start_date + timedelta(days=1) - timedelta(microseconds=1)
                elif unit == "week":
                    start_date = reference - timedelta(days=reference.weekday())
                    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_date = start_date + timedelta(days=7) - timedelta(microseconds=1)
                elif unit == "month":
                    start_date = reference.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    end_date = start_date + relativedelta(months=1) - timedelta(microseconds=1)
                elif unit == "year":
                    start_date = reference.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                    end_date = start_date + relativedelta(years=1) - timedelta(microseconds=1)
                else:
                    return None

                return DateRange(
                    start_date=start_date,
                    end_date=end_date,
                    relative_period=f"this {unit}",
                    is_relative=True,
                )

        except Exception as e:
            logger.warning("Error parsing relative date pattern", error=str(e), pattern=pattern_type)
            return None

        return None

    @classmethod
    def _parse_range_pattern(
        cls, match: re.Match, pattern_type: str, reference: datetime
    ) -> Optional[DateRange]:
        """Parse date range pattern (e.g., "October 27-30").

        Args:
            match: Regex match object
            pattern_type: Type of pattern matched
            reference: Reference date for context

        Returns:
            DateRange object or None
        """
        try:
            groups = match.groups()
            if len(groups) < 2:
                return None

            start_str = groups[0].strip()
            end_str = groups[1].strip()

            if pattern_type == "month_day_range":
                # Parse "October 27" format - need current year
                year = reference.year
                try:
                    start_date = date_parse(f"{start_str}, {year}")
                    end_date = date_parse(f"{end_str}, {year}")
                    # If end date is before start date, assume next year
                    if end_date < start_date:
                        end_date = date_parse(f"{end_str}, {year + 1}")
                except Exception:
                    return None
            else:
                # Parse ISO or other formats
                try:
                    start_date = date_parse(start_str)
                    end_date = date_parse(end_str)
                except Exception:
                    return None

            # Set time boundaries
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

            return DateRange(
                start_date=start_date,
                end_date=end_date,
                start_date_str=start_str,
                end_date_str=end_str,
                is_relative=False,
            )

        except Exception as e:
            logger.warning("Error parsing date range pattern", error=str(e), pattern=pattern_type)
            return None

    @classmethod
    def _parse_single_date(cls, text: str, reference: datetime) -> Optional[datetime]:
        """Try to parse text as a single date.

        Args:
            text: Text to parse
            reference: Reference date for context

        Returns:
            Parsed datetime or None
        """
        try:
            parsed = date_parse(text, default=reference)
            return parsed
        except Exception:
            return None

    @classmethod
    def _subtract_time(cls, date: datetime, amount: int, unit: str) -> datetime:
        """Subtract time from a date.

        Args:
            date: Base date
            amount: Amount to subtract
            unit: Unit (day, week, month, year)

        Returns:
            New datetime
        """
        unit_lower = unit.lower().rstrip("s")  # Normalize plural/singular

        if unit_lower == "day":
            return date - timedelta(days=amount)
        elif unit_lower == "week":
            return date - timedelta(weeks=amount)
        elif unit_lower == "month":
            return date - relativedelta(months=amount)
        elif unit_lower == "year":
            return date - relativedelta(years=amount)
        elif unit_lower == "hour":
            return date - timedelta(hours=amount)
        else:
            return date - timedelta(days=amount)  # Default to days

    @classmethod
    def _add_time(cls, date: datetime, amount: int, unit: str) -> datetime:
        """Add time to a date.

        Args:
            date: Base date
            amount: Amount to add
            unit: Unit (day, week, month, year)

        Returns:
            New datetime
        """
        unit_lower = unit.lower().rstrip("s")  # Normalize plural/singular

        if unit_lower == "day":
            return date + timedelta(days=amount)
        elif unit_lower == "week":
            return date + timedelta(weeks=amount)
        elif unit_lower == "month":
            return date + relativedelta(months=amount)
        elif unit_lower == "year":
            return date + relativedelta(years=amount)
        elif unit_lower == "hour":
            return date + timedelta(hours=amount)
        else:
            return date + timedelta(days=amount)  # Default to days

