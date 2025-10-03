"""Test pyRofex REST API to see what fields are available for market data."""

import json
import os

import pyRofex as pyr
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Initialize pyRofex
pyr.initialize(
    user=os.getenv("PYROFEX_USER"),
    password=os.getenv("PYROFEX_PASSWORD"),
    account=os.getenv("PYROFEX_ACCOUNT"),
    environment=pyr.Environment.LIVE
)

# Test a few symbols
test_symbols = [
    "MERV - XMEV - GGAL - 24hs",
    "MERV - XMEV - SPY - 24hs",
    "MERV - XMEV - PESOS - 3D"
]

print("=" * 100)
print("Testing pyRofex REST API for Market Data Fields")
print("=" * 100)

for symbol in test_symbols:
    print(f"\n{'='*100}")
    print(f"Symbol: {symbol}")
    print(f"{'='*100}")
    
    try:
        # Get market data snapshot
        md = pyr.get_market_data(
            ticker=symbol,
            entries=[
                pyr.MarketDataEntry.BIDS,
                pyr.MarketDataEntry.OFFERS,
                pyr.MarketDataEntry.LAST,
                pyr.MarketDataEntry.OPENING_PRICE,
                pyr.MarketDataEntry.CLOSING_PRICE,
                pyr.MarketDataEntry.HIGH_PRICE,
                pyr.MarketDataEntry.LOW_PRICE,
                pyr.MarketDataEntry.SETTLEMENT_PRICE,
                pyr.MarketDataEntry.TRADE_EFFECTIVE_VOLUME,
                pyr.MarketDataEntry.NOMINAL_VOLUME,
                pyr.MarketDataEntry.TRADE_VOLUME,
                pyr.MarketDataEntry.OPEN_INTEREST,
            ]
        )
        
        print(json.dumps(md, indent=2, default=str))
        
    except Exception as e:
        print(f"ERROR: {e}")

print("\n" + "=" * 100)
print("Test Complete")
print("=" * 100)
