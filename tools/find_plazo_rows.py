"""Find all Plazo (period) values in column R."""
import xlwings as xw

# Connect to the Excel file
wb = xw.Book(r'c:\git\EPGB_pyRofex\EPGB OC-DI - Python.xlsb')
sheet = wb.sheets['HomeBroker']

# Check column R (Plazo) for all rows
print("Column R (Plazo) - All values:")
print("=" * 60)
plazo_col = sheet.range('R2:R50').value

if isinstance(plazo_col, list):
    for i, val in enumerate(plazo_col, start=2):
        if val and str(val).strip():
            print(f"  Row {i}: '{val}'")
else:
    print(f"  Row 2: {plazo_col}")

wb.close()
