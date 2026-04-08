"""Tests for technical checks."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from geo_audit.core.technical_checks import TechnicalChecker


def _make_page(url: str, response_time_ms: float = 500.0, html: str = "") -> dict:
    return {"url": url, "html": html, "status": 200, "response_time_ms": response_time_ms}


class TestHttpsCheck:
    def test_https_true(self):
        checker = TechnicalChecker("https://example.com", [])
        assert checker._check_https() is True

    def test_https_false_for_http(self):
        checker = TechnicalChecker("http://example.com", [])
        assert checker._check_https() is False


class TestAvgResponseTime:
    def test_calculates_average(self):
        pages = [_make_page("https://example.com", 200), _make_page("https://example.com/about", 400)]
        checker = TechnicalChecker("https://example.com", pages)
        assert checker._calculate_avg_response_time() == 300.0

    def test_empty_pages(self):
        checker = TechnicalChecker("https://example.com", [])
        assert checker._calculate_avg_response_time() == 0.0


class TestSpeedScore:
    def test_fast_page(self):
        checker = TechnicalChecker("https://example.com", [])
        assert checker._calculate_speed_score(400) == 100

    def test_moderate_page(self):
        checker = TechnicalChecker("https://example.com", [])
        assert checker._calculate_speed_score(800) == 80

    def test_slow_page(self):
        checker = TechnicalChecker("https://example.com", [])
        assert checker._calculate_speed_score(6000) == 0


class TestSemanticHtmlScore:
    def test_full_semantic_html(self):
        html = (
            "<html><head><meta name='description' content='test'></head>"
            "<body><main><nav></nav><header></header><footer></footer>"
            "<article><section><h1>Title</h1></section></article></main></body></html>"
        )
        checker = TechnicalChecker("https://example.com", [_make_page("https://example.com", html=html)])
        score = checker._calculate_semantic_score()
        assert score == 100

    def test_empty_html(self):
        checker = TechnicalChecker("https://example.com", [_make_page("https://example.com", html="<html></html>")])
        score = checker._calculate_semantic_score()
        assert score == 0

    def test_no_pages(self):
        checker = TechnicalChecker("https://example.com", [])
        assert checker._calculate_semantic_score() == 0


class TestFileChecks:
    def test_robots_txt_found(self):
        checker = TechnicalChecker("https://example.com", [])
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("requests.head", return_value=mock_resp):
            assert checker._check_file_exists("/robots.txt") is True

    def test_robots_txt_not_found(self):
        checker = TechnicalChecker("https://example.com", [])
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        with patch("requests.head", return_value=mock_resp):
            assert checker._check_file_exists("/robots.txt") is False

    def test_request_exception_returns_false(self):
        import requests as req

        checker = TechnicalChecker("https://example.com", [])
        with patch("requests.head", side_effect=req.RequestException("timeout")):
            assert checker._check_file_exists("/robots.txt") is False


class TestRunChecks:
    def test_run_checks_returns_all_keys(self):
        checker = TechnicalChecker("https://example.com", [])
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        with patch("requests.head", return_value=mock_resp):
            results = checker.run_checks()

        expected_keys = {
            "https", "robots_txt_present", "llms_txt_present",
            "avg_response_time_ms", "page_speed_score", "semantic_html_score", "issues",
        }
        assert expected_keys.issubset(results.keys())

    def test_https_issue_reported(self):
        checker = TechnicalChecker("http://example.com", [])
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        with patch("requests.head", return_value=mock_resp):
            results = checker.run_checks()
        assert any("HTTPS" in issue for issue in results["issues"])
