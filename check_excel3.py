import pandas as pd
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

excel_path = "合并产品信息表修改后.xlsx"
excel_file = pd.ExcelFile(excel_path)

print("Sheet names:", excel_file.sheet_names)
print("\n=== 产品信息_华英 Sheet ===")
df = pd.read_excel(excel_file, sheet_name='产品信息_华英')
print("Columns:", df.columns.tolist())
print("\nTotal rows:", len(df))
print("\nAll data:")
for idx, row in df.iterrows():
    print(f"\n--- Row {idx+1} ---")
    for col in df.columns:
        val = row[col]
        if pd.notna(val):
            print(f"  {col}: {val}")
