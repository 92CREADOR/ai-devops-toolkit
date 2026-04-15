"""Unit tests for LogAnalyzer.

Uses mocking to avoid real OpenAI API calls during testing.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from log_analyzer import AnalysisResult, LogAnalyzer


# ─── Fixtures ────────────────────────────────────────────────────────────────

SAMPLE_LOG_SUCCESS = """
[2024-01-15 10:23:01] Starting build pipeline...
[2024-01-15 10:23:02] Cloning repository...
[2024-01-15 10:23:05] Installing dependencies...
[2024-01-15 10:23:10] Running tests...
[2024-01-15 10:23:15] All tests passed.
[2024-01-15 10:23:16] Build completed successfully.
"""

SAMPLE_LOG_FAILURE = """
[2024-01-15 10:23:01] Starting build pipeline...
[2024-01-15 10:23:05] Installing dependencies...
[2024-01-15 10:23:10] Running tests...
[2024-01-15 10:23:12] ERROR: ModuleNotFoundError: No module named 'pydantic'
[2024-01-15 10:23:12] Traceback (most recent call last):
[2024-01-15 10:23:12]   File "log_analyzer.py", line 5, in <module>
[2024-01-15 10:23:12]     from pydantic import BaseModel
[2024-01-15 10:23:12] ModuleNotFoundError: No module named 'pydantic'
[2024-01-15 10:23:13] FAILED: Build failed with exit code 1
"""

MOCK_ANALYSIS_RESULT = AnalysisResult(
    root_cause="ModuleNotFoundError: pydantic is not installed in the Python environment",
    suggested_fix=(
        "Add 'pydantic>=2.0.0' to requirements.txt and run 'pip install -r requirements.txt'"
    ),
    confidence_score=0.95,
    error_type="dependency",
    affected_file="log_analyzer.py",
)


@pytest.fixture
def analyzer():
    """Create a LogAnalyzer instance with a fake API key."""
    return LogAnalyzer(model="gpt-4o-mini", api_key="fake-api-key-for-testing")


@pytest.fixture
def mock_openai_response():
    """Mock a successful OpenAI API response."""
    mock_response = MagicMock()
    mock_response.choices[0].message.parsed = MOCK_ANALYSIS_RESULT
    return mock_response


# ─── Tests: AnalysisResult model ─────────────────────────────────────────────


class TestAnalysisResult:
    def test_valid_result(self):
        result = AnalysisResult(
            root_cause="Test error",
            suggested_fix="Fix the test",
            confidence_score=0.8,
        )
        assert result.root_cause == "Test error"
        assert result.confidence_score == 0.8

    def test_confidence_score_bounds(self):
        with pytest.raises(Exception):
            AnalysisResult(
                root_cause="error",
                suggested_fix="fix",
                confidence_score=1.5,  # > 1.0, should fail
            )

    def test_optional_fields_default_to_none(self):
        result = AnalysisResult(
            root_cause="error",
            suggested_fix="fix",
            confidence_score=0.5,
        )
        assert result.error_type is None
        assert result.affected_file is None


# ─── Tests: LogAnalyzer initialization ───────────────────────────────────────


class TestLogAnalyzerInit:
    def test_default_model(self, analyzer):
        assert analyzer.model == "gpt-4o-mini"

    def test_custom_model(self):
        a = LogAnalyzer(model="gpt-4o", api_key="fake")
        assert a.model == "gpt-4o"

    def test_default_max_log_chars(self, analyzer):
        assert analyzer.max_log_chars == 8000


# ─── Tests: LogAnalyzer.analyze() ────────────────────────────────────────────


class TestLogAnalyzerAnalyze:
    def test_analyze_nonexistent_file(self, analyzer):
        with pytest.raises(FileNotFoundError):
            analyzer.analyze("/nonexistent/path/to/log.txt")

    def test_analyze_empty_file(self, analyzer, tmp_path):
        empty_log = tmp_path / "empty.log"
        empty_log.write_text("")
        with pytest.raises(ValueError, match="empty"):
            analyzer.analyze(empty_log)

    @patch("log_analyzer.OpenAI")
    def test_analyze_success(self, mock_openai_class, tmp_path, mock_openai_response):
        mock_client = MagicMock()
        mock_client.beta.chat.completions.parse.return_value = mock_openai_response
        mock_openai_class.return_value = mock_client

        log_file = tmp_path / "failed.log"
        log_file.write_text(SAMPLE_LOG_FAILURE)

        analyzer = LogAnalyzer(api_key="fake")
        result = analyzer.analyze(log_file)

        assert isinstance(result, AnalysisResult)
        assert result.root_cause == MOCK_ANALYSIS_RESULT.root_cause
        assert result.confidence_score == 0.95

    @patch("log_analyzer.OpenAI")
    def test_analyze_calls_openai_with_log_content(self, mock_openai_class, tmp_path):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.parsed = MOCK_ANALYSIS_RESULT
        mock_client.beta.chat.completions.parse.return_value = mock_response
        mock_openai_class.return_value = mock_client

        log_file = tmp_path / "test.log"
        log_file.write_text(SAMPLE_LOG_FAILURE)

        analyzer = LogAnalyzer(api_key="fake")
        analyzer.analyze(log_file)

        mock_client.beta.chat.completions.parse.assert_called_once()
        call_args = mock_client.beta.chat.completions.parse.call_args
        assert call_args.kwargs["model"] == "gpt-4o-mini"


# ─── Tests: LogAnalyzer.analyze_content() ────────────────────────────────────


class TestAnalyzeContent:
    def test_empty_content_raises_error(self, analyzer):
        with pytest.raises(ValueError, match="empty"):
            analyzer.analyze_content("   ")

    @patch("log_analyzer.OpenAI")
    def test_analyze_content_success(self, mock_openai_class, mock_openai_response):
        mock_client = MagicMock()
        mock_client.beta.chat.completions.parse.return_value = mock_openai_response
        mock_openai_class.return_value = mock_client

        analyzer = LogAnalyzer(api_key="fake")
        result = analyzer.analyze_content(SAMPLE_LOG_FAILURE)

        assert isinstance(result, AnalysisResult)


# ─── Tests: LogAnalyzer._truncate_log() ──────────────────────────────────────


class TestTruncateLog:
    def test_short_log_not_truncated(self, analyzer):
        short_log = "ERROR: something failed"
        result = analyzer._truncate_log(short_log)
        assert result == short_log

    def test_long_log_is_truncated(self, analyzer):
        long_log = "x" * 20000
        result = analyzer._truncate_log(long_log)
        assert len(result) < len(long_log)
        assert "LOG TRUNCATED" in result

    def test_truncated_log_keeps_start_and_end(self, analyzer):
        start_marker = "START_OF_LOG " * 100
        end_marker = " END_OF_LOG" * 100
        middle = "MIDDLE " * 2000
        long_log = start_marker + middle + end_marker

        result = analyzer._truncate_log(long_log)
        assert "START_OF_LOG" in result
        assert "END_OF_LOG" in result


# ─── Tests: LogAnalyzer.extract_errors() ─────────────────────────────────────


class TestExtractErrors:
    def test_extracts_error_lines(self):
        errors = LogAnalyzer.extract_errors(SAMPLE_LOG_FAILURE)
        assert len(errors) > 0
        assert any("ERROR" in line or "FAILED" in line for line in errors)

    def test_no_errors_in_success_log(self):
        errors = LogAnalyzer.extract_errors(SAMPLE_LOG_SUCCESS)
        assert len(errors) == 0

    def test_empty_log_returns_empty_list(self):
        errors = LogAnalyzer.extract_errors("")
        assert errors == []

    def test_detects_exception_keyword(self):
        log = "Traceback (most recent call last):\n  Exception: something went wrong"
        errors = LogAnalyzer.extract_errors(log)
        assert len(errors) > 0
