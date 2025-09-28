"""
Test configuration for EPGB Options.
"""

import pytest
import sys
from pathlib import Path

# Add src to Python path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

@pytest.fixture
def sample_market_data():
    """Sample market data for testing."""
    return {
        'symbol': 'GGAL - CI',
        'bid': 1000.0,
        'ask': 1005.0,
        'last': 1002.5,
        'volume': 1500
    }