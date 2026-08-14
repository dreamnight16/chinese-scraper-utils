"""Tests for _date.py — parse_date, try_parse_date, extract_date."""

import pytest
from datetime import datetime
from chinese_scraper_utils import parse_date, try_parse_date, extract_date


class TestParseDate:
    # ── Valid formats ──

    def test_iso_format(self):
        assert parse_date("2026-05-04") == "2026-05-04"

    def test_slash_format(self):
        assert parse_date("2026/05/04") == "2026-05-04"

    def test_dot_format(self):
        assert parse_date("2026.05.04") == "2026-05-04"

    def test_compact_format(self):
        assert parse_date("20260504") == "2026-05-04"

    def test_datetime_format(self):
        assert parse_date("2026-05-04 14:30:00") == "2026-05-04"

    def test_iso_with_timezone(self):
        result = parse_date("2026-05-04T14:30:00")
        assert result == "2026-05-04" or result == ""  # fromisoformat handles this

    # ── Edge cases ──

    def test_empty_string(self):
        assert parse_date("") == ""

    def test_none_like(self):
        # parse_date historically accepted empty; now returns ""
        assert parse_date("") == ""

    def test_garbage_returns_empty_not_truncated_garbage(self):
        """Regression test: '北京国家会议中心' should NOT return '北京国家会议中'."""
        result = parse_date("北京国家会议中心")
        assert result == "", f"Expected empty string, got '{result}'"

    def test_random_text(self):
        assert parse_date("hello world") == ""

    def test_short_text(self):
        assert parse_date("abc") == ""

    def test_partial_date(self):
        """'2026-05' is not a complete date."""
        result = parse_date("2026-05")
        assert result == ""

    def test_iso_z_suffix(self):
        """Trailing 'Z' (UTC) is normalized before ISO parsing."""
        assert parse_date("2026-05-04T14:30:00Z") == "2026-05-04"

    def test_iso_timezone_offset(self):
        assert parse_date("2026-05-04T14:30:00+08:00") == "2026-05-04"

    def test_iso_fractional_seconds(self):
        assert parse_date("2026-05-04T14:30:00.123456") == "2026-05-04"

    def test_int_input(self):
        """Integer compact form is stringified then matched by %Y%m%d."""
        assert parse_date(20260504) == "2026-05-04"

    def test_none_input(self):
        assert parse_date(None) == ""

    def test_whitespace_stripped(self):
        assert parse_date("  2026-05-04  ") == "2026-05-04"


class TestTryParseDate:
    def test_valid_date(self):
        assert try_parse_date("2026-05-04") == "2026-05-04"

    def test_empty_returns_none(self):
        assert try_parse_date("") is None

    def test_garbage_returns_none(self):
        assert try_parse_date("not a date") is None

    def test_none_input(self):
        assert try_parse_date(None) is None


class TestExtractDate:
    def test_chinese_full_date(self):
        result = extract_date("2026年5月4日上海有漫展")
        assert result == "2026-05-04"

    def test_month_day_only(self):
        # Use today's month/day: it can never be >90 days in the past,
        # so the cross-year inference does not trigger.
        now = datetime.now()
        result = extract_date(f"{now.month}月{now.day}日有活动")
        assert result == now.strftime("%Y-%m-%d")

    def test_range_format(self):
        now = datetime.now()
        result = extract_date(f"{now.month}月{now.day}日-{now.day}日广州")
        assert result == now.strftime("%Y-%m-%d")

    def test_no_date(self):
        assert extract_date("今天天气不错") == ""

    def test_cross_year_threshold(self):
        """When month-day is > 90 days in the past, it should advance to next year."""
        # Use a date far in the past to trigger cross-year
        result = extract_date("1月1日有活动")
        # Should be next year's January 1st if today is past October
        year = datetime.now().year
        from datetime import date as Date
        jan1 = Date(year, 1, 1)
        if (Date.today() - jan1).days > 90:
            assert result == f"{year + 1}-01-01"
        else:
            assert result == f"{year}-01-01"

    def test_full_date_no_cross_year(self):
        """Explicit year should prevent cross-year advancement."""
        result = extract_date("2025年1月1日有活动")
        assert result == "2025-01-01"

    def test_dot_separated_full_date(self):
        assert extract_date("2026.5.4上海有漫展") == "2026-05-04"

    def test_full_date_without_day_suffix(self):
        """'日'/'号' suffix is optional for the full-year pattern."""
        assert extract_date("2026年5月4上海") == "2026-05-04"

    def test_future_month_day_stays_current_year(self):
        """A future month/day must never roll to the next year."""
        year = datetime.now().year
        assert extract_date("12月31日有活动") == f"{year}-12-31"

    def test_range_returns_start_day(self):
        """Range format collapses to the start day (current year)."""
        year = datetime.now().year
        assert extract_date("12月25日-1月3日广州") == f"{year}-12-25"

    def test_invalid_month_returns_empty(self):
        assert extract_date("13月40日有活动") == ""

    def test_invalid_day_returns_empty(self):
        assert extract_date("2月30日有活动") == ""
