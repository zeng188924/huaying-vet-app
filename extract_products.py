import pandas as pd
import json
import os
from datetime import datetime

excel_path = "合并产品信息表修改后.xlsx"
excel_file = pd.ExcelFile(excel_path)

df = pd.read_excel(excel_file, sheet_name='产品信息_华英')

products = []
for idx, row in df.iterrows():
    product = {
        'row': idx + 1,
        'category': str(row.get('类别', '')),
        'timing': str(row.get('时机', '')),
        'product_name': str(row.get('产品名称', '')),
        'package': str(row.get('包装规格', '')),
        'efficacy': str(row.get('适应症状或产品功效', '')),
        'usage': str(row.get('用法用量', '')),
        'water_ratio': str(row.get('兑水量', '')),
        'price': str(row.get('价格', '')),
        'remark': str(row.get('备注', '')),
        'retail_price': str(row.get('建议零售价', ''))
    }
    products.append(product)

with open('huaying_products.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, ensure_ascii=False, indent=2)

print(f"Total products: {len(products)}")
print("Products saved to huaying_products.json")

for p in products:
    print(f"  {p['product_name']}")
