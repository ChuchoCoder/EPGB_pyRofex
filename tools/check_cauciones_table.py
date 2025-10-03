"""Check if cauciones table is being populated."""
import xlwings as xw

# Connect to the Excel file
wb = xw.Book(r'c:\git\EPGB_pyRofex\EPGB OC-DI - Python.xlsb')
sheet = wb.sheets['HomeBroker']

# Check cauciones data in the table (columns S, T, U for rows with cauciones)
print("Cauciones Table Data (Columns S=Vencimiento, T=Tasa, U=Monto):")
print("=" * 80)
print(f"{'Row':<5} {'Plazo (Col R)':<20} {'Vencimiento (S)':<25} {'Tasa (T)':<15} {'Monto (U)':<15}")
print("=" * 80)

# Check rows for cauciones we have: 3D (row 4), 4D (row 5), 5D (row 6), 6D (row 7), 10-14D (rows 11-15)
caucion_rows = [4, 5, 6, 7, 11, 12, 13, 14, 15]

for row in caucion_rows:
    plazo = sheet.range(f'R{row}').value
    vencimiento = sheet.range(f'S{row}').value
    tasa = sheet.range(f'T{row}').value
    monto = sheet.range(f'U{row}').value
    
    print(f"{row:<5} {str(plazo):<20} {str(vencimiento):<25} {str(tasa):<15} {str(monto):<15}")

wb.close()
