# -*- coding: utf-8 -*-
"""
验证兽药推荐逻辑：
1. 病毒性疾病仅存在中兽药有效产品时，仅显示中兽药
2. 呼吸道疾病存在有效化药时，显示化药+中兽药
3. 所有化药必须对应当前病症具备明确适应症
"""
import sys
import os

# 将 src/core 加入路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src", "core"))

from drug_recommendation_system_full import create_recommender, quick_recommend

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "products", "huaying_products.json")


def classify_label(drug_name, indications, category):
    """简单判断药物类别"""
    cat_lower = str(category).lower()
    if "中兽药" in str(category) or "中药" in str(category):
        return "中兽药"
    if "化药" in str(category) or "西药" in str(category):
        return "化药"
    # 根据名称兜底
    tcm_keywords = ["口服液", "散", "颗粒", "黄芪", "双黄连", "板蓝根", "甘草", "肽", "健素", "甘舒乐"]
    chem_keywords = ["可溶性粉", "预混剂", "溶液", "霉素", "菌素", "康", "硝唑", "考", "西林", "沙星"]
    for kw in tcm_keywords:
        if kw in drug_name:
            return "中兽药"
    for kw in chem_keywords:
        if kw in drug_name:
            return "化药"
    return "其他"


def print_result(title, result):
    print(f"\n{'=' * 60}")
    print(f"【{title}】")
    print(f"症状: {result['input_analysis']['symptom']}")
    print(f"可能疾病: {result['input_analysis']['possible_diseases']}")
    print(f"疾病类型: {result['input_analysis']['disease_type']}")

    print("\n单药推荐:")
    for i, r in enumerate(result["single_recommendations"][:5], 1):
        drug = r["drug"]
        label = classify_label(drug["name"], drug["indications"], drug["category"])
        print(f"  {i}. [{label}] {drug['name']} | 类别:{drug['category']} | 适应症:{drug['indications']}")

    print("\n组合推荐:")
    for combo in result["combination_recommendations"][:3]:
        drugs = combo.get("drugs", [])
        labels = [classify_label(d["name"], d["indications"], d["category"]) for d in drugs]
        names = [d["name"] for d in drugs]
        rule = combo.get("type_compliance", {}).get("rule", "")
        adjusted = combo.get("type_compliance", {}).get("adjusted", False)
        compliant = combo.get("type_compliance", {}).get("compliant", False)
        print(f"  - {combo['scheme_name']}: {names}")
        print(f"    类型: {labels}")
        print(f"    合规: {compliant}, 是否调整过: {adjusted}")
        print(f"    合规规则: {rule}")
        for d in drugs:
            print(f"      * {d['name']} | category={d['category']} | indications={d['indications']}")


def main():
    if not os.path.exists(DATA_PATH):
        print(f"数据文件不存在: {DATA_PATH}")
        return

    recommender = create_recommender(DATA_PATH)

    # 场景1：病毒性疾病（新城疫/禽流感相关）—— 应主要显示中兽药
    result1 = quick_recommend(
        recommender,
        animal_type="蛋鸡",
        age_stage="产蛋期",
        symptom="精神沉郁",
        disease_type="",
        usage="治疗",
        egg_period_safe=False,
        farm_scale="小规模"
    )
    print_result("场景1：精神沉郁（病毒/混合感染为主）", result1)

    # 场景2：呼吸道疾病 —— 应显示有效化药+中兽药
    result2 = quick_recommend(
        recommender,
        animal_type="蛋鸡",
        age_stage="育成期",
        symptom="咳嗽",
        disease_type="",
        usage="治疗",
        egg_period_safe=False,
        farm_scale="小规模"
    )
    print_result("场景2：咳嗽（呼吸道疾病）", result2)

    # 场景3：消化道疾病 —— 应显示有效化药
    result3 = quick_recommend(
        recommender,
        animal_type="蛋鸡",
        age_stage="育雏期",
        symptom="拉稀",
        disease_type="",
        usage="治疗",
        egg_period_safe=False,
        farm_scale="小规模"
    )
    print_result("场景3：拉稀（消化道疾病）", result3)

    # 场景4：产蛋期安全模式下的呼吸道 —— 应过滤掉产蛋期禁用的化药
    result4 = quick_recommend(
        recommender,
        animal_type="蛋鸡",
        age_stage="产蛋期",
        symptom="咳嗽",
        disease_type="",
        usage="治疗",
        egg_period_safe=True,
        farm_scale="小规模"
    )
    print_result("场景4：产蛋期咳嗽（过滤禁用化药）", result4)

    # 场景5：病毒性疾病（流感）—— 应主要显示中兽药，不强制添加无适应症化药
    result5 = quick_recommend(
        recommender,
        animal_type="蛋鸡",
        age_stage="产蛋期",
        symptom="流感",
        disease_type="",
        usage="治疗",
        egg_period_safe=False,
        farm_scale="小规模"
    )
    print_result("场景5：流感（病毒性疾病）", result5)


if __name__ == "__main__":
    main()
