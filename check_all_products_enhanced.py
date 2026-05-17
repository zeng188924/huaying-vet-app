import pandas as pd
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

excel_path = "合并产品信息表修改后.xlsx"
df = pd.read_excel(excel_path, sheet_name='产品信息_华英')

# 87种蛋鸡产蛋期禁用兽药清单
banned_drugs_87 = [
    "二硝托胺预混剂", "马杜米星铵预混剂", "磷酸泰乐菌素预混剂",
    "磺胺喹噁啉钠可溶性粉", "磺胺喹噁啉钠溶液", "复方磺胺喹噁啉溶液",
    "复方磺胺喹噁啉钠可溶性粉", "磺胺喹噁啉二甲氧苄啶预混剂",
    "磺胺氯吡嗪钠可溶性粉", "复方磺胺氯吡嗪钠预混剂", "复方磺胺氯哒嗪钠粉",
    "磺胺对甲氧嘧啶二甲氧苄啶预混剂", "复方磺胺二甲嘧啶钠可溶性粉",
    "复方磺胺间甲氧嘧啶可溶性粉", "磺胺间甲氧嘧啶预混剂",
    "复方磺胺间甲氧嘧啶钠可溶性粉", "复方磺胺间甲氧嘧啶预混剂",
    "盐酸氨丙啉磺胺喹噁啉钠可溶性粉", "氯羟吡啶预混剂",
    "硫酸黏菌素可溶性粉", "硫酸黏菌素预混剂",
    "硫酸新霉素可溶性粉", "硫酸新霉素溶液", "硫酸安普霉素可溶性粉",
    "硫氰酸红霉素可溶性粉", "替米考星溶液",
    "酒石酸泰乐菌素可溶性粉", "酒石酸泰乐菌素磺胺二甲嘧啶可溶性粉",
    "酒石酸吉他霉素可溶性粉",
    "恩诺沙星溶液", "恩诺沙星片", "恩诺沙星可溶性粉",
    "盐霉素钠预混剂", "盐酸氯苯胍预混剂",
    "盐酸氨丙啉乙氧酰胺苯甲酯磺胺喹噁啉预混剂",
    "盐酸氨丙啉乙氧酰胺苯甲酯预混剂",
    "盐酸多西环素片", "盐酸多西环素可溶性粉", "盐酸大观霉素可溶性粉",
    "氟苯尼考粉", "氟苯尼考预混剂", "氟苯尼考溶液", "氟苯尼考注射液", "氟苯尼考可溶性粉",
    "阿莫西林可溶性粉", "阿莫西林片", "复方阿莫西林粉",
    "氨苄西林可溶性粉", "氨苄西林钠可溶性粉", "复方氨苄西林粉",
    "杆菌肽锌预混剂",
    "地克珠利预混剂", "地克珠利溶液", "地克珠利颗粒",
    "吉他霉素预混剂", "吉他霉素片",
    "马杜米星铵尼卡巴嗪预混剂", "复方马度米星铵预混剂",
    "三苯氯达唑片", "三苯氯达唑颗粒",
    "甲磺酸达氟沙星粉", "甲磺酸达氟沙星溶液",
    "甲磺酸培氟沙星可溶性粉", "甲磺酸培氟沙星注射液",
    "地美硝唑预混剂", "那西肽预混剂",
    "乳酸环丙沙星可溶性粉", "乳酸诺氟沙星可溶性粉",
    "金霉素预混剂", "盐酸金霉素可溶性粉",
    "洛克沙胂预混剂",
    "盐酸沙拉沙星片", "盐酸沙拉沙星可溶性粉", "盐酸沙拉沙星注射液", "盐酸沙拉沙星溶液",
    "盐酸环丙沙星可溶性粉", "盐酸环丙沙星注射液",
    "氨苯砷酸预混剂",
    "烟酸诺氟沙星可溶性粉", "烟酸诺氟沙星溶液",
    "酒石酸泰万菌素可溶性粉", "酒石酸泰万菌素预混剂",
    "海南霉素钠预混剂", "越霉素A预混剂",
    "硫酸庆大霉素可溶性粉", "甲砜霉素可溶性粉", "氯霉素可溶性粉"
]

# 关键活性成分及其禁用原因
banned_ingredients = {
    "恩诺沙星": {"reason": "喹诺酮类合成抗菌药，GB 31650-2019规定产蛋期禁用", "basis": "GB 31650-2019"},
    "氟苯尼考": {"reason": "酰胺醇类抗菌药，GB 31650-2019规定蛋鸡产蛋期不得使用", "basis": "GB 31650-2019"},
    "阿莫西林": {"reason": "β-内酰胺类抗菌药，GB 31650-2019规定蛋鸡产蛋期不得使用", "basis": "GB 31650-2019"},
    "氨苄西林": {"reason": "β-内酰胺类抗菌药，GB 31650-2019规定蛋鸡产蛋期不得使用", "basis": "GB 31650-2019"},
    "多西环素": {"reason": "四环素类抗菌药，GB 31650-2019规定产蛋期禁用", "basis": "GB 31650-2019"},
    "金霉素": {"reason": "四环素类抗菌药，GB 31650-2019规定产蛋期禁用", "basis": "GB 31650-2019"},
    "沙拉沙星": {"reason": "氟喹诺酮类抗菌药，GB 31650-2019规定产蛋期禁用", "basis": "GB 31650-2019"},
    "替米考星": {"reason": "大环内酯类抗菌药，GB 31650-2019规定产蛋期禁用", "basis": "GB 31650-2019"},
    "庆大霉素": {"reason": "氨基糖苷类抗菌药，兽药质量标准规定产蛋期禁用", "basis": "兽药质量标准"},
    "大观霉素": {"reason": "氨基糖苷类抗菌药，兽药质量标准规定产蛋期禁用", "basis": "兽药质量标准"},
    "林可霉素": {"reason": "林可胺类抗菌药，兽药质量标准规定产蛋期禁用", "basis": "兽药质量标准"},
    "地美硝唑": {"reason": "硝基咪唑类，GB 31650-2019规定产蛋期禁用", "basis": "GB 31650-2019"},
    "达氟沙星": {"reason": "氟喹诺酮类抗菌药，GB 31650-2019规定产蛋期禁用", "basis": "GB 31650-2019"},
    "培氟沙星": {"reason": "氟喹诺酮类，农业农村部公告第2292号停用药物", "basis": "农业农村部公告第2292号"},
    "环丙沙星": {"reason": "氟喹诺酮类抗菌药，GB 31650-2019规定产蛋期禁用", "basis": "GB 31650-2019"},
    "诺氟沙星": {"reason": "氟喹诺酮类，农业农村部公告第2292号停用药物", "basis": "农业农村部公告第2292号"},
    "泰乐菌素": {"reason": "大环内酯类抗菌药，兽药质量标准规定产蛋期禁用", "basis": "兽药质量标准"},
    "泰万菌素": {"reason": "大环内酯类抗菌药，兽药质量标准规定产蛋期禁用", "basis": "兽药质量标准"},
    "磺胺": {"reason": "磺胺类抗菌药，GB 31650-2019规定产蛋期禁用", "basis": "GB 31650-2019"},
    "地克珠利": {"reason": "抗球虫药，GB 31650-2019规定产蛋期禁用", "basis": "GB 31650-2019"},
    "二硝托胺": {"reason": "抗球虫药，兽药典2000版规定产蛋期禁用", "basis": "兽药典2000版"},
    "马杜米星": {"reason": "聚醚类抗球虫药，部颁标准规定产蛋期禁用", "basis": "部颁标准"},
    "氯羟吡啶": {"reason": "抗球虫药，兽药质量标准规定产蛋期禁用", "basis": "兽药质量标准"},
    "盐酸氯苯胍": {"reason": "抗球虫药，兽药质量标准规定产蛋期禁用", "basis": "兽药质量标准"},
    "盐霉素": {"reason": "聚醚类抗球虫药，兽药质量标准规定产蛋期禁用", "basis": "兽药质量标准"},
    "黏菌素": {"reason": "多肽类抗菌药，兽药质量标准规定产蛋期禁用", "basis": "兽药质量标准"},
    "新霉素": {"reason": "氨基糖苷类抗菌药，兽药质量标准规定产蛋期禁用", "basis": "兽药质量标准"},
    "安普霉素": {"reason": "氨基糖苷类抗菌药，兽药质量标准规定产蛋期禁用", "basis": "兽药质量标准"},
    "红霉素": {"reason": "大环内酯类抗菌药，兽药质量标准规定产蛋期禁用", "basis": "兽药质量标准"},
    "吉他霉素": {"reason": "大环内酯类抗菌药，兽药质量标准规定产蛋期禁用", "basis": "兽药质量标准"},
    "杆菌肽": {"reason": "多肽类抗菌药，兽药质量标准规定产蛋期禁用", "basis": "兽药质量标准"},
    "那西肽": {"reason": "大环内酯类抗菌药，已禁止作为饲料添加剂使用", "basis": "农业农村部公告"},
    "甲砜霉素": {"reason": "酰胺醇类抗菌药，GB 31650-2019规定产蛋期禁用", "basis": "GB 31650-2019"},
    "氯霉素": {"reason": "酰胺醇类，农业农村部公告第250号禁止使用药品", "basis": "农业农村部公告第250号"},
    "氨苯砷酸": {"reason": "砷制剂，已停止使用", "basis": "农业农村部公告"},
    "洛克沙胂": {"reason": "砷制剂，已停止使用", "basis": "农业农村部公告"},
    "三苯氯达唑": {"reason": "抗寄生虫药，兽药质量标准规定产蛋期禁用", "basis": "兽药质量标准"},
    "海南霉素": {"reason": "聚醚类抗球虫药，兽药质量标准规定产蛋期禁用", "basis": "兽药质量标准"},
    "越霉素": {"reason": "氨基糖苷类抗球虫药，兽药质量标准规定产蛋期禁用", "basis": "兽药质量标准"},
    "氨丙啉": {"reason": "抗球虫药，兽药质量标准规定产蛋期禁用", "basis": "兽药质量标准"},
    "头孢喹肟": {"reason": "头孢类抗菌药，兽药质量标准规定产蛋期禁用", "basis": "兽药质量标准"},
}

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

print("=" * 80)
print("华英公司所有产品产蛋期禁用药物详细检查（增强版）")
print("=" * 80)

matched_banned = []
not_matched = []

for product in products:
    name = product['product_name']
    if name == '/' or name == 'nan' or not name:
        not_matched.append(product)
        continue
    
    is_banned = False
    matched_banned_name = None
    matched_ingredients = []
    
    # 方法1：匹配87种清单
    for banned_name in banned_drugs_87:
        if banned_name in name or name in banned_name:
            is_banned = True
            matched_banned_name = banned_name
            break
    
    # 方法2：匹配关键活性成分（更严格）
    for ingredient, info in banned_ingredients.items():
        if ingredient in name:
            is_banned = True
            matched_ingredients.append(ingredient)
    
    if is_banned:
        # 收集所有匹配的活性成分
        all_ingredients = []
        for ingredient, info in banned_ingredients.items():
            if ingredient in name:
                all_ingredients.append(ingredient)
        
        if all_ingredients:
            # 使用第一个匹配的活性成分的信息
            primary_ingredient = all_ingredients[0]
            reason_info = banned_ingredients[primary_ingredient]
        elif matched_banned_name:
            # 从87种清单中匹配
            for ingredient, info in banned_ingredients.items():
                if ingredient in matched_banned_name:
                    reason_info = info
                    all_ingredients.append(ingredient)
                    break
            else:
                reason_info = {"reason": "列入87种蛋鸡产蛋期禁用兽药清单", "basis": "GB 31650-2019/兽药质量标准"}
        else:
            reason_info = {"reason": "列入87种蛋鸡产蛋期禁用兽药清单", "basis": "GB 31650-2019/兽药质量标准"}
        
        matched_banned.append({
            'row': product['row'],
            'product_name': name,
            'category': product['category'],
            'package': product['package'],
            'matched_banned_drug': matched_banned_name or '活性成分匹配',
            'active_ingredient': '、'.join(all_ingredients) if all_ingredients else '未知',
            'all_ingredients': all_ingredients,
            'ban_reason': reason_info['reason'],
            'legal_basis': reason_info['basis'],
            'efficacy': product['efficacy'],
            'usage': product['usage'],
            'water_ratio': product['water_ratio'],
            'remark': product['remark']
        })
    else:
        not_matched.append(product)

print(f"\n产品总数: {len(products)}")
print(f"产蛋期禁用药物: {len(matched_banned)} 种")
print(f"非禁用/其他产品: {len([p for p in not_matched if p['product_name'] != '/' and p['product_name'] != 'nan' and p['product_name']])} 种")

print("\n" + "=" * 80)
print("【产蛋期禁用药物清单】")
print("=" * 80)

for item in sorted(matched_banned, key=lambda x: x['row']):
    print(f"\nRow {item['row']}: {item['product_name']}")
    print(f"  类别: {item['category']}")
    print(f"  包装: {item['package']}")
    print(f"  匹配禁用药: {item['matched_banned_drug']}")
    print(f"  有效成分: {item['active_ingredient']}")
    print(f"  禁用原因: {item['ban_reason']}")
    print(f"  法规依据: {item['legal_basis']}")

print("\n" + "=" * 80)
print("【非禁用产品清单】")
print("=" * 80)

for p in not_matched:
    if p['product_name'] != '/' and p['product_name'] != 'nan' and p['product_name']:
        print(f"  Row {p['row']}: {p['product_name']} ({p['category']})")

# Save results
result = {
    'total_products': len(products),
    'banned_count': len(matched_banned),
    'non_banned_count': len([p for p in not_matched if p['product_name'] != '/' and p['product_name'] != 'nan' and p['product_name']]),
    'banned_drugs': sorted(matched_banned, key=lambda x: x['row']),
    'non_banned_products': [p for p in not_matched if p['product_name'] != '/' and p['product_name'] != 'nan' and p['product_name']]
}

with open('banned_drugs_enhanced_report.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"\n结果已保存到 banned_drugs_enhanced_report.json")
