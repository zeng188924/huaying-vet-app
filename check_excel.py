import pandas as pd

excel_path = "合并产品信息表修改后.xlsx"
excel_file = pd.ExcelFile(excel_path)

print("Sheet names:", excel_file.sheet_names)
print("\n=== 明星产品 Sheet ===")
df = pd.read_excel(excel_file, sheet_name='明星产品_20260512')
print("Columns:", df.columns.tolist())
print("\nFirst row:")
print(df.iloc[0].to_dict())
