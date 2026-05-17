# -*- coding: utf-8 -*-
"""
综合验证脚本 - 验证产蛋期禁用药物修复
测试所有关键场景，确保禁用药物不会在产蛋期被错误推荐
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from drug_recommendation_system_full import create_recommender, quick_recommend

def test_all_scenarios():
    """测试所有关键场景"""
    print("=" * 80)
    print("产蛋期禁用药物综合验证测试")
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
    
    # 测试场景列表
    test_scenarios = [
        {
            "name": "蛋鸡产蛋期 - 呼吸道疾病",
            "animal_type": "蛋鸡",
            "age_stage": "产蛋高峰期",
            "symptom": "咳嗽、打喷嚏",
            "disease_type": "呼吸道疾病",
            "egg_period_safe": True
        },
        {
            "name": "蛋鸡产蛋期 - 肠道疾病",
            "animal_type": "蛋鸡",
            "age_stage": "产蛋后期",
            "symptom": "拉稀、腹泻",
            "disease_type": "消化道疾病",
            "egg_period_safe": True
        },
        {
            "name": "蛋鸡产蛋期 - 细菌感染",
            "animal_type": "蛋鸡",
            "age_stage": "产蛋前期",
            "symptom": "精神沉郁、发热",
            "disease_type": "细菌性疾病",
            "egg_period_safe": True
        },
        {
            "name": "蛋鸡产蛋期 - 病毒感染",
            "animal_type": "蛋鸡",
            "age_stage": "产蛋高峰期",
            "symptom": "羽毛松乱、不吃",
            "disease_type": "病毒性疾病",
            "egg_period_safe": True
        },
        {
            "name": "蛋鸡产蛋期 - 混合感染",
            "animal_type": "蛋鸡",
            "age_stage": "产蛋后期",
            "symptom": "精神沉郁、拉稀",
            "disease_type": "混合感染",
            "egg_period_safe": True
        },
        {
            "name": "蛋鸡产蛋期 - 寄生虫病",
            "animal_type": "蛋鸡",
            "age_stage": "产蛋高峰期",
            "symptom": "血便、消瘦",
            "disease_type": "寄生虫病",
            "egg_period_safe": True
        }
    ]
    
    all_passed = True
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'=' * 80}")
        print(f"[测试 {i}] {scenario['name']}")
        print(f"{'=' * 80}")
        
        result = quick_recommend(
            recommender,
            animal_type=scenario['animal_type'],
            age_stage=scenario['age_stage'],
            symptom=scenario['symptom'],
            disease_type=scenario['disease_type'],
            usage="治疗",
            egg_period_safe=scenario['egg_period_safe'],
            farm_scale="中规模(1000-10000只)"
        )
        
        print(f"  病情分析: {', '.join(result['input_analysis']['possible_diseases'])}")
        
        # 检查单药推荐
        errors = []
        print(f"\n  单药推荐:")
        for j, rec in enumerate(result['single_recommendations'], 1):
            drug = rec['drug']
            if not drug['egg_period_safe']:
                errors.append(f"单药 {j}: {drug['name']}")
            egg_status = "✅ 安全" if drug['egg_period_safe'] else "❌ 禁用"
            print(f"    {j}. {drug['name']} - {egg_status}")
        
        # 检查组合方案
        print(f"\n  组合方案:")
        for j, combo in enumerate(result['combination_recommendations'], 1):
            print(f"    {j}. {combo['scheme_name']}")
            for drug in combo['drugs']:
                if not drug['egg_period_safe']:
                    errors.append(f"组合方案 {combo['scheme_name']} 中的 {drug['name']}")
                egg_status = "✅ 安全" if drug['egg_period_safe'] else "❌ 禁用"
                print(f"       - {drug['name']}: {egg_status}")
        
        if errors:
            print(f"\n  ❌ 测试失败: 发现 {len(errors)} 个禁用药物被推荐")
            for error in errors:
                print(f"     - {error}")
            all_passed = False
        else:
            print(f"\n  ✅ 测试通过")
    
    # 最终结果
    print(f"\n{'=' * 80}")
    print("最终测试结果")
    print(f"{'=' * 80}")
    
    if all_passed:
        print("\n✅ 所有测试通过！产蛋期禁用药物拦截功能正常")
        print("\n修复内容总结:")
        print("  1. 修复了组合方案库中缺失的egg_safe标记")
        print("  2. 为所有疾病类型的组合方案添加了产蛋期安全方案")
        print("  3. 增强了禁用药物匹配逻辑（产品名称 + 活性成分双重检查）")
        print("  4. 更新了移动端应用的产品目录显示，增加产蛋期状态标签")
        print("\n现在手机软件应该能正确显示产蛋期禁用药物了！")
    else:
        print("\n❌ 部分测试失败，需要进一步修复")
    
    print(f"\n{'=' * 80}")

if __name__ == "__main__":
    test_all_scenarios()
