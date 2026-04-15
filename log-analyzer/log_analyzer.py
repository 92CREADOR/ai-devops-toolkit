"""
AI-powered log analyzer for CI/CD pipelines.

Uses LLMs (OpenAI GPT) to parse logs, identify root causes,
and suggest fixes automatically.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

from openai import OpenAI
from pydantic import BaseModel, Field


class AnalysisResult(BaseModel):
    """Structured result from log analysis."""

    root_cause: str = Field(
        description="The identified root cause of the failure"
    )
    suggested_fix: str = Field(
        description="Actionable suggestion to fix the issue"
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="Confidence level of the analysis (0.0 - 1.0)"
    )
    error_type: Optional[str] = Field(
        default=None,
        description="Classified error type (e.g., 'dependency', 'syntax', 'network')"
    )
    affected_file: Optional[str] = Field(
        default=None,
        description="File or component where the error originated"
    )


class LogAnalyzer:
    """
    Analyzes CI/CD log files using LLMs to identify root causes and suggest fixes.

    Args:
        model: OpenAI model to use (default: gpt-4o-mini).
        api_key: OpenAI API key. Reads from OPENAI_API_KEY env var if not provided.
        max_log_chars: Maximum number of log characters to send to the LLM.

    Example:
        >>> analyzer = LogAnalyzer(model="gpt-4o-mini")
        >>> result = analyzer.analyze("path/to/failed-pipeline.log")
        >>> print(result.root_cause)
        >>> print(result.suggested_fix)
    """

    SYSTEM_PROMPT = """You are an expert DevOps engineer specializing in CI/CD pipeline debugging.
Your task is to analyze build/deployment logs and identify the root cause of failures.

For each log you analyze, provide:
1. The specific root cause of the failure (be precise, reference line numbers if visible)
2. A clear, actionable fix the developer can apply
3. Your confidence level (0.0-1.0) in the analysis
4. The error type category
5. The affected file or component if identifiable

Focus on the most critical error. Ignore warnings unless they are the root cause.
"""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        max_log_chars: int = 8000,
    ) -> None:
        self.model = model
        self.max_log_chars = max_log_chars
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

    def analyze(self, log_path: str | Path) -> AnalysisResult:
        """
        Analyze a log file and return a structured analysis result.

        Args:
            log_path: Path to the log file to analyze.

        Returns:
            AnalysisResult with root_cause, suggested_fix, and confidence_score.

        Raises:
            FileNotFoundError: If the log file does not exist.
            ValueError: If the log file is empty.
        """
        log_path = Path(log_path)

        if not log_path.exists():
            raise FileNotFoundError(f"Log file not found: {log_path}")

        log_content = log_path.read_text(encoding="utf-8", errors="replace")

        if not log_content.strip():
            raise ValueError(f"Log file is empty: {log_path}")

        return self._analyze_content(log_content)

    def analyze_content(self, log_content: str) -> AnalysisResult:
        """
        Analyze raw log content string.

        Args:
            log_content: The raw log text to analyze.

        Returns:
            AnalysisResult with root_cause, suggested_fix, and confidence_score.
        """
        if not log_content.strip():
            raise ValueError("Log content is empty")

        return self._analyze_content(log_content)

    def _analyze_content(self, log_content: str) -> AnalysisResult:
        """Internal method to call the LLM and parse the response."""
        truncated_log = self._truncate_log(log_content)

        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Analyze this CI/CD log and identify the root cause:\n\n```\n{truncated_log}\n```",
                },
            ],
            response_format=AnalysisResult,
        )

        return response.choices[0].message.parsed

    def _truncate_log(self, log_content: str) -> str:
        """
        Intelligently truncate logs to fit within token limits.

        Keeps the beginning (context) and end (where errors usually appear)
        of the log, removing the middle if necessary.
        """
        if len(log_content) <= self.max_log_chars:
            return log_content

        half = self.max_log_chars // 2
        start = log_content[:half]
        end = log_content[-half:]

        return f"{start}\n\n[... LOG TRUNCATED - middle section omitted ...]\n\n{end}"

    @staticmethod
    def extract_errors(log_content: str) -> list[str]:
        """
        Extract error lines from log content using regex patterns.

        Useful for pre-filtering before sending to the LLM.

        Args:
            log_content: Raw log text.

        Returns:
            List of lines containing error indicators.
        """
        error_patterns = [
            r"(?i)\bERROR\b",
            r"(?i)\bFAILED\b",
            r"(?i)\bFATAL\b",
            r"(?i)exception",
            r"(?i)traceback",
            r"(?i)\bnot found\b",
            r"(?i)permission denied",
            r"exit code [1-9]",
        ]

        combined_pattern = "|".join(error_patterns)
        error_lines = []

        for line in log_content.splitlines():
            if re.search(combined_pattern, line):
                error_lines.append(line.strip())

        return error_lines
