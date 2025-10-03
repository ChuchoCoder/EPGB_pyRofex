"""Check what symbols are actually in the HomeBroker Excel sheet."""
import xlwings as xw

# Connect to the Excel file
wb = xw.Book(r'c:\git\EPGB_pyRofex\EPGB OC-DI - Python.xlsb')
sheet = wb.sheets['HomeBroker']

# Read column A (first 50 rows)
symbols = sheet.range('A2:A50').value

print(f"Total cells read: {len(symbols)}")
print("\nColumn A symbols (HomeBroker sheet):")
for i, s in enumerate(symbols):
    if s:
        print(f"  Row {i+2}: '{s}'")

# Also check if this is a list or single value
print(f"\nType of symbols: {type(symbols)}")

wb.close()
