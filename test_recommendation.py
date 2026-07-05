# -*- coding: utf-8 -*-
"""本地测试：验证智能推荐核心逻辑与输出内容"""
import os
import sys

_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_root, 'src'))
sys.path.insert(0, os.path.join(_root, 'src', 'core'))
sys.path.insert(0, os.path.join(_root, 'src', 'utils'))

from drug_recommendation_system_full import create_recommender, quick_recommend
from src.utils.lab_report_parser import parse_lab_report
from src.utils.data_manager import (
    create_farmer_profile, create_shed,
    add_medication_history, get_medication_history,
    start_new_batch, get_shed,
    delete_farmer_profile
)


def test_lab_report_parser():
    print("=" * 60)
    print("测试1：实验室检测报告文本识别")
    print("=" * 60)
    text = "PCR检测：支原体阳性，鸡群出现咳嗽、呼噜、甩鼻、呼吸困难等症状"
    parsed = parse_lab_report(text)
    assert parsed is not None, "识别失败"
    print(f"识别结果：{parsed['disease_category']} - {parsed['disease_name']}（置信度：{parsed['confidence']}）")
    print(f"症状摘要：{parsed['symptom_summary']}")
    assert parsed['disease_category'] == "呼吸道疾病"
    assert "支原体" in parsed['disease_name'] or "慢性呼吸道病" in parsed['disease_name']
    print("✅ 实验室报告识别测试通过\n")


def test_recommendation_output():
    print("=" * 60)
    print("测试2：推荐结果内容检查（确保删除项不存在）")
    print("=" * 60)
    json_path = os.path.join(_root, 'data', 'products', 'huaying_products_full.json')
    recommender = create_recommender(json_path)

    result = quick_recommend(
        recommender,
        animal_type="蛋鸭",
        age_stage="育成期(15-35日龄)",
        symptom="大群咳嗽、呼噜、甩鼻、流泪，部分张口呼吸，日死淘10只左右",
        disease_type="慢性呼吸道病（支原体/慢呼）",
        usage="治疗",
        egg_period_safe=False,
        farm_scale="大规模(10000只以上)",
        excluded_drugs=[],
        medication_history=[]
    )

    # 检查组合推荐理由
    for combo in result.get('combination_recommendations', []):
        rationale = combo.get('rationale', {})
        prevention = rationale.get('resistance_prevention_guide', '')
        combo_basis = rationale.get('combination_basis', '')

        print(f"\n方案：{combo.get('scheme_name', '')}")
        print(f"组合依据：{combo_basis[:80]}...")
        print(f"耐药预防指导条目数：{len([x for x in prevention.split('**') if x.strip()])}")
        print("耐药预防实操指导：")
        print(prevention)

        # 断言删除项不存在
        assert "临床有效性" not in prevention, "仍包含临床有效性"
        assert "预期效果" not in prevention, "仍包含预期效果"
        assert "禁止低剂量长期添加" not in prevention, "仍包含禁止低剂量长期添加"
        assert "定期药敏检测" not in prevention, "仍包含定期药敏检测"
        assert "生物安全减少发病" not in prevention, "仍包含生物安全减少发病"

        # 断言只保留 3 条核心指导
        guide_items = [x.strip() for x in prevention.split('**') if x.strip() and not x.strip().startswith('严格')]
        # 实际有三条：严格足量足疗程、轮换用药制度、联合用药降低耐药概率
        assert prevention.count('**') <= 6, f"耐药预防指导条目过多：{prevention}"

    print("\n✅ 推荐输出内容检查通过\n")


def test_excluded_drugs_and_history():
    print("=" * 60)
    print("测试3：耐药性排除与历史用药交叉耐药")
    print("=" * 60)
    json_path = os.path.join(_root, 'data', 'products', 'huaying_products_full.json')
    recommender = create_recommender(json_path)

    # 先获取无排除时的推荐
    result_no_exclude = quick_recommend(
        recommender,
        animal_type="蛋鸭",
        age_stage="育成期(15-35日龄)",
        symptom="大群咳嗽、呼噜、甩鼻、流泪，部分张口呼吸",
        disease_type="慢性呼吸道病（支原体/慢呼）",
        usage="治疗",
        egg_period_safe=False,
        farm_scale="大规模(10000只以上)",
        excluded_drugs=[],
        medication_history=[]
    )
    all_recommended_names = set()
    for combo in result_no_exclude.get('combination_recommendations', []):
        for drug in combo.get('drugs', []):
            all_recommended_names.add(drug.get('name', ''))
    print(f"无排除时推荐药物：{all_recommended_names}")

    # 排除多西环素并加入历史用药（同四环素类应被排除）
    result_exclude = quick_recommend(
        recommender,
        animal_type="蛋鸭",
        age_stage="育成期(15-35日龄)",
        symptom="大群咳嗽、呼噜、甩鼻、流泪，部分张口呼吸",
        disease_type="慢性呼吸道病（支原体/慢呼）",
        usage="治疗",
        egg_period_safe=False,
        farm_scale="大规模(10000只以上)",
        excluded_drugs=["多西环素"],
        medication_history=["多西环素"]
    )
    excluded_recommended_names = set()
    for combo in result_exclude.get('combination_recommendations', []):
        for drug in combo.get('drugs', []):
            excluded_recommended_names.add(drug.get('name', ''))
    print(f"排除/历史用药后推荐药物：{excluded_recommended_names}")

    # 多西环素不应出现
    assert "多西环素" not in excluded_recommended_names, "被排除药物仍出现"
    print("✅ 耐药性排除与历史用药测试通过\n")


def test_batch_isolation():
    print("=" * 60)
    print("测试4：养殖批次隔离历史用药")
    print("=" * 60)
    import uuid

    profile = create_farmer_profile(
        name="测试养殖户", phone="13800000000", id_card_hash="",
        farming_years=1, technical_level="一般"
    )
    farmer_id = profile.id
    shed = create_shed(
        farmer_id=farmer_id, name="测试棚舍", shed_type="鸭棚",
        area=100.0, breed="蛋鸭", scale="10000只以上", facilities=[],
        location="测试", environment_control=[], batch_id="batch_old"
    )
    shed_id = shed.id

    # 旧批次添加历史用药
    add_medication_history(shed_id, "多西环素", notes="旧批次用药", batch_id="batch_old")
    old_history = get_medication_history(shed_id, batch_id="batch_old")
    assert len(old_history) == 1 and old_history[0]["drug_name"] == "多西环素", "旧批次记录写入失败"

    # 开启新批次
    start_new_batch(shed_id, batch_name="2026年7月新批次", placement_date="2026-07-01")
    shed = get_shed(shed_id)
    new_batch_id = shed.batch_id
    assert new_batch_id != "batch_old", "新批次ID未变更"

    # 新批次不应看到旧记录
    new_history = get_medication_history(shed_id)
    assert len(new_history) == 0, f"新批次仍看到旧历史用药：{new_history}"

    # 新批次添加新记录
    add_medication_history(shed_id, "氟苯尼考", notes="新批次用药")
    new_history = get_medication_history(shed_id)
    assert len(new_history) == 1 and new_history[0]["drug_name"] == "氟苯尼考", "新批次记录写入失败"

    print(f"旧批次药物：多西环素（已隔离）")
    print(f"新批次药物：氟苯尼考（当前可见）")

    # 清理测试数据，避免污染本地数据文件
    delete_farmer_profile(farmer_id)
    print("🧹 已清理测试数据\n")
    print("✅ 养殖批次隔离历史用药测试通过\n")


if __name__ == "__main__":
    test_lab_report_parser()
    test_recommendation_output()
    test_excluded_drugs_and_history()
    test_batch_isolation()
    print("=" * 60)
    print("全部本地核心测试通过")
    print("=" * 60)
