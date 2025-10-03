"""Verify all Excel columns are being populated with market data."""
import xlwings as xw

# Connect to running Excel
app = xw.apps.active
wb = app.books.active
sheet = wb.sheets['HomeBroker']

print("Excel Market Data Verification")
print("=" * 120)
print(f"{'Row':<4} {'Symbol':<30} {'Bid':<10} {'Ask':<10} {'Last':<10} {'Open':<10} {'High':<10} {'Low':<10} {'PrevClose':<10} {'Volume':<10} {'Ops':<8}")
print("=" * 120)

# Check a few sample rows
sample_rows = [3, 4, 5, 10, 15, 20, 25, 30]

for row_num in sample_rows:
    symbol = sheet.range(f'A{row_num}').value
    if not symbol:
        continue
        
    bid = sheet.range(f'C{row_num}').value
    ask = sheet.range(f'D{row_num}').value
    last = sheet.range(f'F{row_num}').value
    open_price = sheet.range(f'H{row_num}').value
    high = sheet.range(f'I{row_num}').value
    low = sheet.range(f'J{row_num}').value
    prev_close = sheet.range(f'K{row_num}').value
    volume = sheet.range(f'M{row_num}').value
    operations = sheet.range(f'N{row_num}').value
    
    # Truncate symbol for display
    symbol_short = symbol[:28] if len(str(symbol)) > 28 else symbol
    
    print(f"{row_num:<4} {symbol_short:<30} {bid:<10.2f} {ask:<10.2f} {last:<10.2f} {open_price:<10.2f} {high:<10.2f} {low:<10.2f} {prev_close:<10.2f} {volume if volume else 0:<10} {operations if operations else 0:<8}")

print("=" * 120)
print("\nColumn Legend:")
print("  C = bid, D = ask, F = last, H = open, I = high, J = low, K = previous_close, M = volume, N = operations")
print("\nIf open/high/low/prev_close are now showing non-zero values, the fix is working! ✅")
