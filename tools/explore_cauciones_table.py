"""Explore the HomeBroker sheet structure to find the cauciones table."""
import xlwings as xw

# Connect to the Excel file
wb = xw.Book(r'c:\git\EPGB_pyRofex\EPGB OC-DI - Python.xlsb')
sheet = wb.sheets['HomeBroker']

# Check columns P through AA (right side of the sheet based on screenshot)
print("Exploring right side of HomeBroker sheet:")
print("=" * 80)

# Check row 1 headers
print("\nRow 1 (Headers) - Columns P through AA:")
headers_p_to_aa = sheet.range('P1:AA1').value
for i, header in enumerate(headers_p_to_aa, start=16):  # P is column 16
    col_letter = chr(64 + i) if i <= 26 else f"A{chr(64 + i - 26)}"
    print(f"  {col_letter}: {header}")

# Check row 2 (first data row on right side)
print("\nRow 2 (First data row) - Columns P through AA:")
row2_data = sheet.range('P2:AA2').value
for i, value in enumerate(row2_data, start=16):
    col_letter = chr(64 + i) if i <= 26 else f"A{chr(64 + i - 26)}"
    print(f"  {col_letter}: {value}")

# Check if there's data in column P (Plazo)
print("\n\nColumn P (Plazo) - First 40 rows:")
plazo_col = sheet.range('P2:P40').value
if isinstance(plazo_col, list):
    for i, val in enumerate(plazo_col, start=2):
        if val:
            print(f"  Row {i}: {val}")
else:
    print(f"  Row 2: {plazo_col}")

# Check column S (which might be Tasa based on screenshot)
print("\n\nColumn T (Tasa) - First 40 rows:")
tasa_col = sheet.range('T2:T40').value
if isinstance(tasa_col, list):
    for i, val in enumerate(tasa_col, start=2):
        if val:
            print(f"  Row {i}: {val}")
else:
    print(f"  Row 2: {tasa_col}")

wb.close()
