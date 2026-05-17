# -*- coding: utf-8 -*-
"""
验证修复后的产蛋期禁用药物拦截功能
测试单药推荐和组合方案推荐是否正确标记禁用药物
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from drug_recommendation_system_full import create_recommender, quick_recommend

def test_egg_period_safety():
    """测试产蛋期安全性"""
    print("=" * 80)
    print("产蛋期禁用药物拦截验证测试")
    print("=" * 80)
    
    # 初始化推荐器
    print("\n[1] 加载产品数据库...")
    recommender = create_recommender("合并产品信息表修改后.xlsx")
    all_drugs = recommender.db.get_all_drugs()
    print(f"    共加载 {len(all_drugs)} 个产品")
    
    # 统计产蛋期禁用药物
    banned_drugs = [d for d in all_drugs if not d.egg_period_safe]
    safe_drugs = [d for d in all_drugs if d.egg_period_safe]
    print(f"    产蛋期禁用药物: {len(banned_drugs)} 种")
    print(f"    产蛋期安全药物: {len(safe_drugs)} 种")
    
    # 列出所有禁用药物
    print("\n[2] 产蛋期禁用药物清单:")
    for i, drug in enumerate(banned_drugs, 1):
        print(f"    {i}. {drug.name} (来源: {drug.source})")
    
    # 测试场景1: 蛋鸡产蛋期 - 应该只推荐安全药物
    print("\n" + "=" * 80)
    print("[3] 测试场景: 蛋鸡产蛋期 - 呼吸道疾病")
    print("=" * 80)
    
    result = quick_recommend(
        recommender,
        animal_type="蛋鸡",
        age_stage="产蛋高峰期",
        symptom="咳嗽、打喷嚏",
        disease_type="呼吸道疾病",
        usage="治疗",
        egg_period_safe=True,  # 产蛋期可用
        farm_scale="中规模(1000-10000只)"
    )
    
    print(f"\n病情分析: {', '.join(result['input_analysis']['possible_diseases'])}")
    
    print("\n单药推荐结果:")
    for i, rec in enumerate(result['single_recommendations'], 1):
        drug = rec['drug']
        egg_status = "✅ 安全" if drug['egg_period_safe'] else "❌ 禁用"
        print(f"  {i}. {drug['name']} - {egg_status}")
        if not drug['egg_period_safe']:
            print(f"     ⚠️ 警告: 该药物为产蛋期禁用药物!")
    
    print("\n组合方案推荐结果:")
    for i, combo in enumerate(result['combination_recommendations'], 1):
        print(f"  {i}. {combo['scheme_name']}")
        for drug in combo['drugs']:
            egg_status = "✅ 安全" if drug['egg_period_safe'] else "❌ 禁用"
            print(f"     - {drug['name']}: {egg_status}")
            if not drug['egg_period_safe']:
                print(f"       ⚠️ 警告: 该药物为产蛋期禁用药物!")
    
    # 测试场景2: 肉鸡 - 可以使用禁用药物
    print("\n" + "=" * 80)
    print("[4] 测试场景: 肉鸡 - 呼吸道疾病 (非产蛋期)")
    print("=" * 80)
    
    result2 = quick_recommend(
        recommender,
        animal_type="肉鸡",
        age_stage="育肥期(36日龄-出栏)",
        symptom="咳嗽、呼吸困难",
        disease_type="呼吸道疾病",
        usage="治疗",
        egg_period_safe=False,  # 非产蛋期
        farm_scale="中规模(1000-10000只)"
    )
    
    print(f"\n病情分析: {', '.join(result2['input_analysis']['possible_diseases'])}")
    
    print("\n单药推荐结果:")
    for i, rec in enumerate(result2['single_recommendations'], 1):
        drug = rec['drug']
        egg_status = "✅ 安全" if drug['egg_period_safe'] else "⚠️ 产蛋期禁用"
        print(f"  {i}. {drug['name']} - {egg_status}")
    
    print("\n组合方案推荐结果:")
    for i, combo in enumerate(result2['combination_recommendations'], 1):
        print(f"  {i}. {combo['scheme_name']}")
        for drug in combo['drugs']:
            egg_status = "✅ 安全" if drug['egg_period_safe'] else "⚠️ 产蛋期禁用"
            print(f"     - {drug['name']}: {egg_status}")
    
    # 验证结果
    print("\n" + "=" * 80)
    print("[5] 验证结果")
    print("=" * 80)
    
    # 检查场景1中是否有禁用药物
    egg_period_errors = []
    for rec in result['single_recommendations']:
        if not rec['drug']['egg_period_safe']:
            egg_period_errors.append(rec['drug']['name'])
    
    for combo in result['combination_recommendations']:
        for drug in combo['drugs']:
            if not drug['egg_period_safe']:
                egg_period_errors.append(f"{combo['scheme_name']} 中的 {drug['name']}")
    
    if egg_period_errors:
        print("\n❌ 发现错误: 产蛋期推荐了禁用药物:")
        for error in egg_period_errors:
            print(f"   - {error}")
    else:
        print("\n✅ 测试通过: 产蛋期推荐的所有药物均为安全药物")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

if __name__ == "__main__":
    test_egg_period_safety()
