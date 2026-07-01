# -*- coding: utf-8 -*-
"""
产品信息库综合测试脚本
检查数据完整性、一致性、异常值等问题
"""

import json
import pandas as pd
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_json_data_integrity():
    """测试JSON数据完整性"""
    print("=" * 80)
    print("【测试1】JSON数据完整性检查")
    print("=" * 80)
    
    with open('data/产品信息_华英_已标注.json', 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    print(f"\n产品总数: {len(products)}")
    
    required_fields = ['id', 'name', 'content', 'spec', 'water', 'price', 
                       'indications', 'main_component', 'category', 'egg_period_safe',
                       'disease_types', 'usage_info', 'source', 'timing']
    
    missing_fields = []
    for product in products:
        for field in required_fields:
            if field not in product:
                missing_fields.append(f"产品 {product.get('id', '未知')} ({product.get('name', '')}) 缺少字段: {field}")
    
    if missing_fields:
        print(f"\n❌ 发现 {len(missing_fields)} 个缺失字段问题:")
        for issue in missing_fields:
            print(f"  - {issue}")
    else:
        print("\n✅ 所有必需字段完整")
    
    return len(missing_fields) == 0

def test_duplicate_products():
    """测试重复产品"""
    print("\n" + "=" * 80)
    print("【测试2】重复产品检查")
    print("=" * 80)
    
    with open('data/产品信息_华英_已标注.json', 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    name_counts = {}
    for product in products:
        name = product.get('name', '')
        if name:
            name_counts[name] = name_counts.get(name, 0) + 1
    
    duplicates = {name: count for name, count in name_counts.items() if count > 1}
    
    if duplicates:
        print(f"\n❌ 发现 {len(duplicates)} 个重复产品:")
        for name, count in duplicates.items():
            print(f"  - {name}: 出现 {count} 次")
        return False
    else:
        print("\n✅ 无重复产品")
        return True

def test_price_anomalies():
    """测试价格异常值"""
    print("\n" + "=" * 80)
    print("【测试3】价格数据异常检查")
    print("=" * 80)
    
    with open('data/产品信息_华英_已标注.json', 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    anomalies = []
    for product in products:
        price = product.get('price', 0)
        if isinstance(price, (int, float)):
            if price <= 0:
                anomalies.append(f"产品 {product.get('id', '未知')} ({product.get('name', '')}): 价格 {price} 异常（<= 0）")
            if price > 1000:
                anomalies.append(f"产品 {product.get('id', '未知')} ({product.get('name', '')}): 价格 {price} 异常（> 1000）")
        else:
            anomalies.append(f"产品 {product.get('id', '未知')} ({product.get('name', '')}): 价格格式异常")
    
    if anomalies:
        print(f"\n❌ 发现 {len(anomalies)} 个价格异常:")
        for issue in anomalies:
            print(f"  - {issue}")
        return False
    else:
        prices = [p['price'] for p in products if isinstance(p.get('price'), (int, float)) and p['price'] > 0]
        if prices:
            print(f"\n✅ 价格范围: ¥{min(prices):.2f} ~ ¥{max(prices):.2f}")
            print(f"   平均价格: ¥{sum(prices)/len(prices):.2f}")
        return True

def test_egg_period_consistency():
    """测试产蛋期安全性标记一致性"""
    print("\n" + "=" * 80)
    print("【测试4】产蛋期安全性标记一致性检查")
    print("=" * 80)
    
    with open('data/产品信息_华英_已标注.json', 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    banned_ingredients = [
        "氟苯尼考", "阿莫西林", "多西环素", "金霉素", "沙拉沙星", "替米考星",
        "庆大霉素", "大观霉素", "林可霉素", "地美硝唑", "达氟沙星", "培氟沙星",
        "环丙沙星", "诺氟沙星", "泰乐菌素", "泰万菌素", "磺胺", "地克珠利",
        "二硝托胺", "马杜米星", "氯羟吡啶", "盐酸氯苯胍", "盐霉素", "黏菌素",
        "新霉素", "安普霉素", "红霉素", "吉他霉素", "杆菌肽", "那西肽",
        "甲砜霉素", "氯霉素", "氨苯砷酸", "洛克沙胂", "三苯氯达唑", "海南霉素",
        "越霉素", "氨丙啉", "头孢喹肟"
    ]
    
    inconsistencies = []
    for product in products:
        name = product.get('name', '')
        egg_safe = product.get('egg_period_safe', True)
        contains_banned = any(ingredient in name for ingredient in banned_ingredients)
        
        if contains_banned and egg_safe:
            inconsistencies.append(f"产品 {product.get('id', '未知')} ({name}): 含禁用成分但标记为安全")
        elif not contains_banned and not egg_safe:
            pass
    
    if inconsistencies:
        print(f"\n❌ 发现 {len(inconsistencies)} 个产蛋期安全性标记不一致:")
        for issue in inconsistencies:
            print(f"  - {issue}")
        return False
    else:
        banned_count = sum(1 for p in products if not p.get('egg_period_safe', True))
        safe_count = sum(1 for p in products if p.get('egg_period_safe', True))
        print(f"\n✅ 产蛋期安全性标记一致")
        print(f"   禁用药物: {banned_count} 种")
        print(f"   安全药物: {safe_count} 种")
        return True

def test_excel_json_consistency():
    """测试Excel和JSON数据一致性"""
    print("\n" + "=" * 80)
    print("【测试5】Excel与JSON数据一致性检查")
    print("=" * 80)
    
    df = pd.read_excel('合并产品信息表修改后.xlsx', sheet_name='产品信息_华英')
    excel_products = set()
    
    for _, row in df.iterrows():
        name = str(row.get('产品名称', '')).strip()
        if name and name != 'nan' and name != '/':
            excel_products.add(name)
    
    with open('data/产品信息_华英_已标注.json', 'r', encoding='utf-8') as f:
        json_products = json.load(f)
    
    json_names = set(p['name'] for p in json_products)
    
    excel_only = excel_products - json_names
    json_only = json_names - excel_products
    
    all_consistent = True
    
    if excel_only:
        print(f"\n❌ Excel中有但JSON中没有的产品 ({len(excel_only)}个):")
        for name in sorted(excel_only):
            print(f"  - {name}")
        all_consistent = False
    
    if json_only:
        print(f"\n❌ JSON中有但Excel中没有的产品 ({len(json_only)}个):")
        for name in sorted(json_only):
            print(f"  - {name}")
        all_consistent = False
    
    if all_consistent:
        print(f"\n✅ Excel与JSON数据一致")
        print(f"   Excel产品数: {len(excel_products)}")
        print(f"   JSON产品数: {len(json_names)}")
    
    return all_consistent

def test_disease_types():
    """测试疾病类型数据"""
    print("\n" + "=" * 80)
    print("【测试6】疾病类型数据检查")
    print("=" * 80)
    
    with open('data/产品信息_华英_已标注.json', 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    valid_disease_types = ['RESPIRATORY', 'GASTROINTESTINAL', 'BACTERIAL', 'VIRAL', 
                           'PARASITIC', 'MIXED', 'ANTI_MYCOPLASMA', 'IMMUNITY', 
                           'NUTRITION', 'NUTRITIONAL', 'LIVER_KIDNEY', 'HEAT_STROKE', 'DISINFECTANT',
                           'ANTI_CYTOZOON', 'ADENOGASTROENTERITIS', 'UNKNOWN']
    
    invalid_types = []
    empty_types = []
    
    for product in products:
        disease_types = product.get('disease_types', [])
        if not disease_types:
            empty_types.append(f"产品 {product.get('id', '未知')} ({product.get('name', '')})")
        else:
            for dt in disease_types:
                if dt not in valid_disease_types:
                    invalid_types.append(f"产品 {product.get('id', '未知')} ({product.get('name', '')}): 无效类型 '{dt}'")
    
    all_valid = True
    
    if empty_types:
        print(f"\n❌ 发现 {len(empty_types)} 个产品疾病类型为空:")
        for issue in empty_types[:5]:
            print(f"  - {issue}")
        if len(empty_types) > 5:
            print(f"  ... 还有 {len(empty_types) - 5} 个")
        all_valid = False
    
    if invalid_types:
        print(f"\n❌ 发现 {len(invalid_types)} 个无效疾病类型:")
        for issue in invalid_types[:5]:
            print(f"  - {issue}")
        if len(invalid_types) > 5:
            print(f"  ... 还有 {len(invalid_types) - 5} 个")
        all_valid = False
    
    if all_valid:
        type_counts = {}
        for product in products:
            for dt in product.get('disease_types', []):
                type_counts[dt] = type_counts.get(dt, 0) + 1
        
        print("\n✅ 疾病类型数据有效")
        print("   各类别产品数量:")
        for dt, count in sorted(type_counts.items()):
            print(f"   - {dt}: {count} 个")
    
    return all_valid

def test_category_data():
    """测试类别数据"""
    print("\n" + "=" * 80)
    print("【测试7】类别数据检查")
    print("=" * 80)
    
    with open('data/产品信息_华英_已标注.json', 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    valid_categories = ['化药', '中药', '饲料添加剂', '抗体', '消毒剂', '营养类', '未知']
    
    invalid_categories = []
    empty_categories = []
    
    for product in products:
        category = product.get('category', '').strip()
        if not category:
            empty_categories.append(f"产品 {product.get('id', '未知')} ({product.get('name', '')})")
        elif category not in valid_categories:
            invalid_categories.append(f"产品 {product.get('id', '未知')} ({product.get('name', '')}): 无效类别 '{category}'")
    
    all_valid = True
    
    if empty_categories:
        print(f"\n❌ 发现 {len(empty_categories)} 个产品类别为空:")
        for issue in empty_categories[:5]:
            print(f"  - {issue}")
        if len(empty_categories) > 5:
            print(f"  ... 还有 {len(empty_categories) - 5} 个")
        all_valid = False
    
    if invalid_categories:
        print(f"\n❌ 发现 {len(invalid_categories)} 个无效类别:")
        for issue in invalid_categories[:5]:
            print(f"  - {issue}")
        if len(invalid_categories) > 5:
            print(f"  ... 还有 {len(invalid_categories) - 5} 个")
        all_valid = False
    
    if all_valid:
        cat_counts = {}
        for product in products:
            cat = product.get('category', '未知')
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
        
        print("\n✅ 类别数据有效")
        print("   各类别产品数量:")
        for cat, count in sorted(cat_counts.items()):
            print(f"   - {cat}: {count} 个")
    
    return all_valid

def test_product_name_normalization():
    """测试产品名称规范化"""
    print("\n" + "=" * 80)
    print("【测试8】产品名称规范化检查")
    print("=" * 80)
    
    with open('data/产品信息_华英_已标注.json', 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    issues = []
    
    for product in products:
        name = product.get('name', '')
        content = product.get('content', '')
        brand_name = product.get('brand_name', '')
        product_name = product.get('product_name', '')
        
        if name != content:
            issues.append(f"产品 {product.get('id', '未知')}: name='{name}' 与 content='{content}' 不一致")
        
        if name != brand_name:
            issues.append(f"产品 {product.get('id', '未知')}: name='{name}' 与 brand_name='{brand_name}' 不一致")
        
        if name != product_name:
            issues.append(f"产品 {product.get('id', '未知')}: name='{name}' 与 product_name='{product_name}' 不一致")
    
    if issues:
        print(f"\n❌ 发现 {len(issues)} 个名称字段不一致问题:")
        for issue in issues[:10]:
            print(f"  - {issue}")
        if len(issues) > 10:
            print(f"  ... 还有 {len(issues) - 10} 个")
        return False
    else:
        print("\n✅ 所有名称字段一致")
        return True

def test_drug_recommendation_system():
    """测试药物推荐系统加载"""
    print("\n" + "=" * 80)
    print("【测试9】药物推荐系统加载测试")
    print("=" * 80)
    
    try:
        from drug_recommendation_system_full import create_recommender
        
        recommender = create_recommender("合并产品信息表修改后.xlsx")
        all_drugs = recommender.db.get_all_drugs()
        
        print(f"\n✅ 推荐系统加载成功")
        print(f"   加载产品数: {len(all_drugs)}")
        
        banned_count = sum(1 for d in all_drugs if not d.egg_period_safe)
        safe_count = sum(1 for d in all_drugs if d.egg_period_safe)
        
        print(f"   产蛋期禁用: {banned_count} 种")
        print(f"   产蛋期安全: {safe_count} 种")
        
        return True
    except Exception as e:
        print(f"\n❌ 推荐系统加载失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 80)
    print("产品信息库综合测试")
    print("=" * 80)
    
    test_results = []
    
    test_results.append(test_json_data_integrity())
    test_results.append(test_duplicate_products())
    test_results.append(test_price_anomalies())
    test_results.append(test_egg_period_consistency())
    test_results.append(test_excel_json_consistency())
    test_results.append(test_disease_types())
    test_results.append(test_category_data())
    test_results.append(test_product_name_normalization())
    test_results.append(test_drug_recommendation_system())
    
    print("\n" + "=" * 80)
    print("测试汇总")
    print("=" * 80)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n通过: {passed}/{total}")
    
    if passed == total:
        print("\n✅ 所有测试通过！产品信息库状态良好")
    else:
        print(f"\n❌ {total - passed} 个测试失败，请检查并修复上述问题")

if __name__ == "__main__":
    main()