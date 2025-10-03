"""Check vencimiento date types"""
import xlwings as xw

wb = xw.apps.active.books.active
sheet = wb.sheets['HomeBroker']

print("Vencimiento Date Types:")
print("=" * 60)
for row in [4, 5, 6, 7, 11, 12, 13, 14, 15]:
    val = sheet.range(f'S{row}').value
    print(f"Row {row}: {val} (type: {type(val).__name__})")
print("=" * 60)
