import pandas as pd

excel_path = "合并产品信息表修改后.xlsx"
excel_file = pd.ExcelFile(excel_path)

print("=== 产品信息_华英 Sheet ===")
df = pd.read_excel(excel_file, sheet_name='产品信息_华英')
print("Columns:", df.columns.tolist())
print("\nFirst 3 rows:")
for i in range(min(3, len(df))):
    print(f"\nRow {i}:")
    print(df.iloc[i].to_dict())
