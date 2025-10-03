"""
Quick test to verify symbol display cleaning works correctly.
"""

from src.epgb_options.utils.helpers import (clean_symbol_for_display,
                                            restore_symbol_prefix)

# Test cases
test_symbols = [
    "MERV - XMEV - GGAL - 24hs",
    "MERV - XMEV - SPY - 24hs",
    "MERV - XMEV - PESOS - 3D",
    "MERV - XMEV - YPFD - CI",
    "GGAL - 24hs",  # Already cleaned
]

print("Testing symbol display cleaning:")
print("=" * 80)

for symbol in test_symbols:
    cleaned = clean_symbol_for_display(symbol)
    restored = restore_symbol_prefix(cleaned)
    print(f"Original:  {symbol}")
    print(f"Cleaned:   {cleaned}")
    print(f"Restored:  {restored}")
    print("-" * 80)

print("\nTesting round-trip:")
print("=" * 80)

for symbol in test_symbols:
    cleaned = clean_symbol_for_display(symbol)
    restored = restore_symbol_prefix(cleaned)
    
    # If original had prefix, restored should match
    if symbol.startswith("MERV - XMEV - "):
        assert restored == symbol, f"Round-trip failed for {symbol}"
        print(f"✅ {symbol} -> {cleaned} -> {restored}")
    else:
        # If original didn't have prefix, cleaned should be unchanged
        assert cleaned == symbol, f"Clean failed for {symbol}"
        print(f"✅ {symbol} (no prefix)")

print("\n✅ All tests passed!")
