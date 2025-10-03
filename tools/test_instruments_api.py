"""Test pyRofex instruments API to see which method works"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

import pyRofex

from epgb_options.config.pyrofex_config import (ACCOUNT, API_URL, ENVIRONMENT,
                                                PASSWORD, USER, WS_URL)

# Initialize
print("Initializing pyRofex...")
pyRofex._set_environment_parameter('url', API_URL, getattr(pyRofex.Environment, ENVIRONMENT))
pyRofex._set_environment_parameter('ws', WS_URL, getattr(pyRofex.Environment, ENVIRONMENT))

pyRofex.initialize(
    environment=getattr(pyRofex.Environment, ENVIRONMENT),
    user=USER,
    password=PASSWORD,
    account=ACCOUNT
)

print("\n" + "="*80)
print("Testing get_instruments('all')...")
print("="*80)
try:
    result = pyRofex.get_instruments('all')
    print(f"Type: {type(result)}")
    print(f"Result: {result if not isinstance(result, list) else f'List with {len(result)} items'}")
    if isinstance(result, list) and len(result) > 0:
        print(f"First item: {result[0]}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*80)
print("Testing get_all_instruments()...")
print("="*80)
try:
    result = pyRofex.get_all_instruments()
    print(f"Type: {type(result)}")
    print(f"Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
    if isinstance(result, dict):
        if 'instruments' in result:
            instruments = result['instruments']
            print(f"Instruments type: {type(instruments)}")
            print(f"Instruments count: {len(instruments) if isinstance(instruments, list) else 'N/A'}")
            if isinstance(instruments, list) and len(instruments) > 0:
                print(f"First instrument: {instruments[0]}")
                print(f"Sample of first 3: {instruments[:3]}")
        print(f"Full result: {str(result)[:500]}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*80)
print("Testing get_detailed_instruments()...")
print("="*80)
try:
    result = pyRofex.get_detailed_instruments()
    print(f"Type: {type(result)}")
    print(f"Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
    if isinstance(result, dict):
        if 'instruments' in result:
            instruments = result['instruments']
            print(f"Instruments type: {type(instruments)}")
            print(f"Instruments count: {len(instruments) if isinstance(instruments, list) else 'N/A'}")
            if isinstance(instruments, list) and len(instruments) > 0:
                print(f"First instrument: {instruments[0]}")
        print(f"Full result (truncated): {str(result)[:500]}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*80)
print("Testing get_segments()...")
print("="*80)
try:
    result = pyRofex.get_segments()
    print(f"Type: {type(result)}")
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")
