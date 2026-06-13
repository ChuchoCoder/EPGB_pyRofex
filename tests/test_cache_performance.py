"""
Performance test for InstrumentCache multi-level caching.

This script demonstrates the performance improvements of the new caching strategy.
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))

from epgb_options.market_data.instrument_cache import InstrumentCache


def test_cache_performance():
    """Test cache performance at each level."""
    
    print("=" * 70)
    print("INSTRUMENT CACHE PERFORMANCE TEST")
    print("=" * 70)
    
    # Initialize cache
    cache = InstrumentCache(ttl_minutes=30)
    
    # Test symbols
    test_symbols = [
        "MERV - XMEV - GGAL - 24hs",
        "MERV - XMEV - YPFD - 24hs",
        "MERV - XMEV - GFGV78806O - CI",  # Option (CI settlement)
        "MERV - XMEV - GFGC47566O - CI",  # Option (CI settlement)
        "MERV - XMEV - ALUA - 24hs",
    ]
    
    # Get cache statistics
    print("\n📊 Initial Cache Statistics:")
    stats = cache.get_cache_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Test 1: First access (File cache or API)
    print("\n🔍 Test 1: First Access (File Cache Load)")
    print("-" * 70)
    
    start = time.perf_counter()
    cache_data = cache.get_cached_instruments()
    elapsed = (time.perf_counter() - start) * 1000
    
    if cache_data:
        print(f"✅ Loaded {cache_data['count']} instruments in {elapsed:.2f}ms")
        print(f"   Source: {'Memory' if stats['memory_cache_active'] else 'File'}")
    else:
        print("No cache available - would fetch from API")
    
    # Test 2: Memory cache lookups (should be very fast)
    print("\n🔍 Test 2: Memory Cache Lookups (O(1) Dictionary Access)")
    print("-" * 70)
    
    for symbol in test_symbols:
        start = time.perf_counter()
        instrument = cache.get_instrument_by_symbol(symbol)
        elapsed = (time.perf_counter() - start) * 1000000  # microseconds
        
        if instrument:
            is_option = cache.is_option_symbol(symbol)
            option_str = "📊 OPTION" if is_option else "💼 SECURITY"
            print(f"   {option_str} | {symbol[:40]:40} | {elapsed:.2f}μs")
        else:
            print(f"   ❌ NOT FOUND | {symbol[:40]:40} | {elapsed:.2f}μs")
    
    # Test 3: Batch lookups (simulate WebSocket processing)
    print("\n🔍 Test 3: Batch Processing (1000 lookups)")
    print("-" * 70)
    
    start = time.perf_counter()
    for _ in range(1000):
        for symbol in test_symbols:
            cache.is_option_symbol(symbol)
    elapsed = (time.perf_counter() - start) * 1000
    
    total_lookups = 1000 * len(test_symbols)
    avg_per_lookup = (elapsed / total_lookups) * 1000  # microseconds
    
    print(f"✅ {total_lookups:,} lookups in {elapsed:.2f}ms")
    print(f"   Average per lookup: {avg_per_lookup:.3f}μs")
    print(f"   Throughput: {total_lookups / (elapsed/1000):,.0f} lookups/second")
    
    # Test 4: Options filtering
    print("\n🔍 Test 4: Get All Options Symbols")
    print("-" * 70)
    
    start = time.perf_counter()
    options_symbols = cache.get_options_symbols()
    elapsed = (time.perf_counter() - start) * 1000
    
    print(f"✅ Retrieved {len(options_symbols):,} option symbols in {elapsed:.2f}ms")
    
    # Show sample options
    sample_options = list(options_symbols)[:5]
    print(f"\n   Sample options:")
    for opt in sample_options:
        print(f"      • {opt}")
    
    # Final statistics
    print("\n📊 Final Cache Statistics:")
    print("-" * 70)
    stats = cache.get_cache_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Performance summary
    print("\n" + "=" * 70)
    print("PERFORMANCE SUMMARY")
    print("=" * 70)
    print(f"✅ Memory cache active: {stats['memory_cache_active']}")
    print(f"✅ Total instruments cached: {stats['total_instruments']:,}")
    print(f"✅ Total options cached: {stats['total_options']:,}")
    print(f"✅ Lookup structures built: {stats['lookup_structures_built']}")
    
    if stats['memory_cache_valid']:
        print(f"✅ Cache age: {stats.get('memory_cache_age_minutes', 0):.2f} minutes")
    
    print("\n🚀 Cache is optimized for maximum performance!")
    print("=" * 70)


if __name__ == "__main__":
    test_cache_performance()
