"""Quick check of saved Excel values."""
import xlwings as xw

wb = xw.Book(r'data\EPGB OC-DI - Python.xlsb')
sh = wb.sheets['HomeBroker']

print('SPY (row 4):')
print(f'  Open: {sh.range("H4").value}')
print(f'  High: {sh.range("I4").value}')
print(f'  Low: {sh.range("J4").value}')
print(f'  Prev Close: {sh.range("K4").value}')
print(f'  Operations: {sh.range("N4").value}')

wb.close()
