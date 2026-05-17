import pandas as pd

excel_path = "合并产品信息表修改后.xlsx"
excel_file = pd.ExcelFile(excel_path)

print("=== 产品信息_华英 Sheet ===")
df = pd.read_excel(excel_file, sheet_name='产品信息_华英')
print("Columns:", df.columns.tolist())

# Check if there's a column related to egg-laying period
for col in df.columns:
    if '产蛋' in str(col) or '蛋' in str(col):
        print(f"\nColumn: {col}")
        print(df[col].value_counts())
