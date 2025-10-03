"""Check market data values in HomeBroker Excel sheet."""
import xlwings as xw

# Connect to the Excel file
wb = xw.Book(r'c:\git\EPGB_pyRofex\EPGB OC-DI - Python.xlsb')
sheet = wb.sheets['HomeBroker']

# Read data from first few rows
print("HomeBroker Sheet Data (first 5 instruments):\n")
print(f"{'Row':<5} {'Symbol':<30} {'Bid':<10} {'Ask':<10} {'Last':<10}")
print("=" * 70)

for row in range(3, 8):  # Check rows 3-7
    symbol = sheet.range(f'A{row}').value
    bid = sheet.range(f'C{row}').value
    ask = sheet.range(f'D{row}').value
    last = sheet.range(f'F{row}').value
    
    print(f"{row:<5} {str(symbol):<30} {bid if bid else 0:<10} {ask if ask else 0:<10} {last if last else 0:<10}")

# Check one specific symbol in detail
print("\n" + "=" * 70)
print("Detailed view of row 3 (GGAL):")
print("=" * 70)
headers = sheet.range('A1:O1').value
values = sheet.range('A3:O3').value

for i, (header, value) in enumerate(zip(headers, values)):
    print(f"{header:<20}: {value}")

wb.close()
