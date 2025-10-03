"""Check current Excel values - all important columns."""
import xlwings as xw

wb = xw.apps.active.books.active
sh = wb.sheets['HomeBroker']

print('=' * 100)
print('MARKET DATA COLUMN CHECK (Sample Rows)')
print('=' * 100)

# Check SPY row 4
print('\nSPY (row 4):')
print(f'  Symbol: {sh.range("A4").value}')
print(f'  Bid: {sh.range("C4").value}')
print(f'  Ask: {sh.range("D4").value}')
print(f'  Last: {sh.range("F4").value}')
print(f'  ✓ Open: {sh.range("H4").value}')
print(f'  ✓ High: {sh.range("I4").value}')
print(f'  ✓ Low: {sh.range("J4").value}')
print(f'  ✓ Prev Close: {sh.range("K4").value}')
print(f'  ✓ Volume: {sh.range("M4").value}')
print(f'  ✓ Operations: {sh.range("N4").value}')

# Check GGAL row 3
print('\nGGAL (row 3):')
print(f'  Symbol: {sh.range("A3").value}')
print(f'  Bid: {sh.range("C3").value}')
print(f'  Ask: {sh.range("D3").value}')
print(f'  Last: {sh.range("F3").value}')
print(f'  ✓ Open: {sh.range("H3").value}')
print(f'  ✓ High: {sh.range("I3").value}')
print(f'  ✓ Low: {sh.range("J3").value}')
print(f'  ✓ Prev Close: {sh.range("K3").value}')
print(f'  ✓ Volume: {sh.range("M3").value}')
print(f'  ✓ Operations: {sh.range("N3").value}')

print('\n' + '=' * 100)
print('✅ If Open/High/Low/Prev Close/Operations show non-zero values, the fix worked!')
print('=' * 100)
