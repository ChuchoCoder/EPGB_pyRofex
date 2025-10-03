"""Check raw tasa values in Excel (not formatted)"""
from datetime import datetime, timedelta

import xlwings as xw

# Connect to running Excel
app = xw.apps.active
wb = app.books.active
sheet = wb.sheets['HomeBroker']

print("Tasa Raw Values:")
print("=" * 80)
print(f"{'Row':<6} {'Plazo':<15} {'Tasa Raw Value':<20} {'Expected Decimal':<20}")
print("=" * 80)

today = datetime.today().date()

# Map periods to rows
period_map = {
    "3 días": 4, "4 días": 5, "5 días": 6, "6 días": 7,
    "10 días": 11, "11 días": 12, "12 días": 13, "13 días": 14, "14 días": 15
}

for period, row in period_map.items():
    plazo = sheet.range(f'R{row}').value
    tasa_raw = sheet.range(f'T{row}').value  # Get raw value
    
    # Calculate expected decimal (divide by 100)
    if tasa_raw is not None:
        expected_decimal = tasa_raw / 100 if tasa_raw > 1 else tasa_raw
    else:
        expected_decimal = None
    
    print(f"{row:<6} {plazo:<15} {tasa_raw:<20} {expected_decimal}")

print("=" * 80)
