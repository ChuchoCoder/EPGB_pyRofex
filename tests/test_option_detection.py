"""
Quick test to verify option symbol detection works correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))

from epgb_options.market_data.instrument_cache import InstrumentCache


def test_option_detection():
    """Test that options are correctly identified."""
    
    print("=" * 70)
    print("OPTION DETECTION TEST")
    print("=" * 70)
    
    cache = InstrumentCache()
    
    # Test symbols from the log
    test_symbols = {
        # Options (should return True)
        "MERV - XMEV - GFGV38566O - 24hs": True,
        "MERV - XMEV - GFGV88566O - 24hs": True,
        "MERV - XMEV - GFGV78806O - 24hs": True,
        "MERV - XMEV - GFGC47566O - 24hs": True,
        "MERV - XMEV - GFGC67566O - 24hs": True,
        "MERV - XMEV - GFGC97354O - 24hs": True,
        
        # Securities (should return False)
        "MERV - XMEV - GGAL - 24hs": False,
        "MERV - XMEV - GGAL - CI": False,
        "MERV - XMEV - COME - 24hs": False,
        "MERV - XMEV - YPFD - 24hs": False,
    }
    
    print("\n🔍 Testing Option Detection:")
    print("-" * 70)
    
    passed = 0
    failed = 0
    
    for symbol, expected_is_option in test_symbols.items():
        result = cache.is_option_symbol(symbol)
        
        status = "✅ PASS" if result == expected_is_option else "❌ FAIL"
        expected_str = "OPTION" if expected_is_option else "SECURITY"
        actual_str = "OPTION" if result else "SECURITY"
        
        print(f"{status} | Expected: {expected_str:8} | Got: {actual_str:8} | {symbol}")
        
        if result == expected_is_option:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_symbols)} tests")
    
    if failed == 0:
        print("✅ All tests passed!")
    else:
        print(f"❌ {failed} tests failed")
    
    print("=" * 70)
    
    # Show cache stats
    stats = cache.get_cache_stats()
    print("\n📊 Cache Statistics:")
    print(f"   Memory cache active: {stats['memory_cache_active']}")
    print(f"   Total instruments: {stats['total_instruments']:,}")
    print(f"   Total options: {stats['total_options']:,}")
    print(f"   Lookup structures built: {stats['lookup_structures_built']}")

if __name__ == "__main__":
    test_option_detection()
