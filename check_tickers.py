import xlwings as xw

# Open the Excel file and check what's in the Tickers sheet
wb = xw.Book('EPGB OC-DI - Python.xlsb')
shtTickers = wb.sheets('Tickers')

print("🔍 Checking Tickers sheet content...")

# Check different ranges where symbols should be
ranges_to_check = [
    ('A2:A10', 'Options (Column A)'),
    ('C2:C10', 'Acciones (Column C)'), 
    ('E2:E10', 'Bonos (Column E)'),
    ('G2:G10', 'CEDEARs (Column G)'),
    ('I2:I10', 'Letras (Column I)'),
    ('K2:K10', 'ONs (Column K)'),
    ('M2:M10', 'Panel General (Column M)')
]

for range_addr, description in ranges_to_check:
    try:
        values = shtTickers.range(range_addr).value
        print(f"\n📊 {description} ({range_addr}):")
        if values is None:
            print("   → Empty/None")
        elif isinstance(values, list):
            non_none_values = [v for v in values if v is not None]
            print(f"   → Found {len(non_none_values)} non-empty values: {non_none_values[:3]}...")
        else:
            print(f"   → Single value: {values}")
    except Exception as e:
        print(f"   → Error reading {range_addr}: {e}")

# Also check the used range of the sheet
try:
    used_range = shtTickers.used_range
    if used_range:
        print(f"\n📏 Used range: {used_range.address}")
        print(f"📏 Used range size: {used_range.rows.count} rows x {used_range.columns.count} columns")
    else:
        print("\n📏 No used range found (sheet may be completely empty)")
except Exception as e:
    print(f"\n📏 Error getting used range: {e}")