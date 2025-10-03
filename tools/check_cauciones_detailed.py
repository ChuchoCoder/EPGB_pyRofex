"""Check cauciones table with better formatting."""
from datetime import date, datetime

import xlwings as xw

# Connect to the Excel file
wb = xw.Book(r'c:\git\EPGB_pyRofex\EPGB OC-DI - Python.xlsb')
sheet = wb.sheets['HomeBroker']

# Check cauciones data in the table (columns S, T, U for rows with cauciones)
print("Cauciones Table Data:")
print("=" * 100)
print(f"{'Row':<5} {'Plazo':<12} {'Vencimiento (S)':<20} {'Tasa (T)':<15} {'Monto (U)':<20}")
print("=" * 100)

# Check rows for cauciones we have: 3D (row 4), 4D (row 5), 5D (row 6), 6D (row 7), 10-14D (rows 11-15)
caucion_rows = [4, 5, 6, 7, 11, 12, 13, 14, 15]

today = datetime.now().date()

for row in caucion_rows:
    plazo = sheet.range(f'R{row}').value
    vencimiento_raw = sheet.range(f'S{row}').value
    tasa = sheet.range(f'T{row}').value
    monto = sheet.range(f'U{row}').value
    
    # Format vencimiento
    if isinstance(vencimiento_raw, datetime):
        vencimiento = vencimiento_raw.date()
    elif isinstance(vencimiento_raw, date):
        vencimiento = vencimiento_raw
    else:
        vencimiento = vencimiento_raw
    
    # Calculate expected vencimiento
    if plazo:
        days_str = plazo.replace(' días', '').replace(' día', '')
        try:
            num_days = int(days_str)
            from datetime import timedelta
            expected_vencimiento = today + timedelta(days=num_days)
        except:
            expected_vencimiento = "N/A"
    else:
        expected_vencimiento = "N/A"
    
    # Format tasa as percentage if it's a decimal
    if tasa and tasa < 1:
        tasa_display = f"{tasa*100:.2f}%"
    elif tasa:
        tasa_display = f"{tasa:.2f}"
    else:
        tasa_display = "N/A"
    
    print(f"{row:<5} {str(plazo):<12} {str(vencimiento):<20} {tasa_display:<15} {monto if monto else 'N/A':<20}")
    print(f"      Expected: {expected_vencimiento}")

wb.close()
