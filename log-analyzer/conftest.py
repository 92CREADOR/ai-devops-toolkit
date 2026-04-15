"""pytest configuration for log-analyzer tests."""
import sys
from pathlib import Path

# Add the log-analyzer directory to sys.path so tests can import log_analyzer
sys.path.insert(0, str(Path(__file__).parent))
