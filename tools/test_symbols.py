"""
Quick test to see what symbols are available and get real market data.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pyRofex

from epgb_options.config.pyrofex_config import (ACCOUNT, API_URL, ENVIRONMENT,
                                                PASSWORD, USER, WS_URL)

# Initialize
pyRofex._set_environment_parameter('url', API_URL, getattr(pyRofex.Environment, ENVIRONMENT))
pyRofex._set_environment_parameter('ws', WS_URL, getattr(pyRofex.Environment, ENVIRONMENT))

pyRofex.initialize(
    environment=getattr(pyRofex.Environment, ENVIRONMENT),
    user=USER,
    password=PASSWORD,
    account=ACCOUNT
)

# Try getting segments/instruments
print("=" * 80)
print("Testing symbol formats...")
print("=" * 80)

test_symbols = [
    "MERV - XMEV - GGAL - CI",
    "MERV - XMEV - GGAL - 24hs",
    "MERV - XMEV - GFGC9800OC - 24hs",
    "DLR/ABR26",  # Dollar April 2026
    "DLR/ABR26/MAY26",  # Pase Dollar
]

for symbol in test_symbols:
    try:
        result = pyRofex.get_market_data(
            [symbol],
            [pyRofex.MarketDataEntry.BIDS, pyRofex.MarketDataEntry.OFFERS, pyRofex.MarketDataEntry.LAST]
        )
        print(f"\n✅ {symbol}:")
        if result.get('marketData'):
            md = result['marketData']
            print(f"   BI: {md.get('BI')}, OF: {md.get('OF')}, LA: {md.get('LA')}")
        else:
            print(f"   Response: {result}")
    except Exception as e:
        print(f"\n❌ {symbol}: {e}")

print("\n" + "=" * 80)
