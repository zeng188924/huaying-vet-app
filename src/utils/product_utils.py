# -*- coding: utf-8 -*-
"""
产品展示与规格聚合工具
- 通过 product_group_id 或名称归一化把同一产品的不同规格聚合在一起
- 提供统一的规格卡片渲染辅助函数
"""

import re
import os
import json
from datetime import datetime
from collections import OrderedDict
from typing import List, Dict, Optional, Tuple, Any


# 需要剔除的末尾规格/包装单位（出现一次或多次）
_SIZE_UNITS = re.compile(
    r"(\s*[0-9]+(?:\.[0-9]+)?\s*(?:g|kg|mg|ml|l|斤|升|克|千克|毫克|毫升|"
    r"瓶|袋|盒|箱|桶|粒|片|支|包|听|罐|板|套))+\s*$",
    re.IGNORECASE,
)

# 常见的末尾营销/来源标注，不会影响产品本身的分组
_PROMO_SUFFIX = re.compile(
    r"[（(]\s*(?:明星产品|明星|底价|推荐|特价|爆款|新款|热销)\s*[）)]\s*$",
    re.IGNORECASE,
)


def normalize_group_key(name: str, main_component: str) -> str:
    """
    把产品名称末尾的营销标注与尺寸/包装单位去掉后，与主要成分组合成稳定的分组键。
    用于自动识别同一产品的不同规格（如 100g 与 500g）。
    """
    base = str(name or "").strip()
    # 1. 去掉末尾营销标注，例如 “（明星产品）”
    base = _PROMO_SUFFIX.sub("", base)
    # 2. 去掉末尾规格/包装单位，例如 “500g”、“250ml”
    base = _SIZE_UNITS.sub("", base)
    # 3. 去掉所有空白并统一小写，减少因空格导致的不一致
    base = re.sub(r"\s+", "", base).lower()
    comp = re.sub(r"\s+", "", str(main_component or "").strip()).lower()
    if not base:
        return comp or str(id(name))
    if not comp:
        return base
    return f"{comp}::{base}"


def assign_product_group_ids(products: List[Dict]) -> None:
    """
    为每个产品补充分组标识 product_group_id。
    已有 product_group_id 的产品保持不变；缺失的按 normalize_group_key 自动生成。
    """
    for p in products:
        if not p.get("product_group_id"):
            p["product_group_id"] = normalize_group_key(
                p.get("name", ""), p.get("main_component", "")
            )


def group_products(products: List[Dict]) -> OrderedDict[str, List[Dict]]:
    """
    按 product_group_id 聚合产品，返回 OrderedDict[group_id -> variants]。
    同一组内按 id 排序，保证展示顺序稳定。
    """
    groups: Dict[str, List[Dict]] = {}
    for p in products:
        gid = p.get("product_group_id") or normalize_group_key(
            p.get("name", ""), p.get("main_component", "")
        )
        groups.setdefault(gid, []).append(p)
    for g in groups.values():
        g.sort(key=lambda x: str(x.get("id", "")))
    # 保持原始顺序
    return OrderedDict(
        (gid, groups[gid]) for gid in sorted(groups.keys(), key=lambda k: str(groups[k][0].get("id", k)))
    )


def get_base_display_name(variants: List[Dict]) -> str:
    """
    获取产品组的展示名称：对组内所有名称做规格/营销标注归一化后，
    取最短的共同基础名称。
    """
    if not variants:
        return ""

    def _clean(n: str) -> str:
        n = str(n or "").strip()
        n = _PROMO_SUFFIX.sub("", n)
        n = _SIZE_UNITS.sub("", n)
        n = re.sub(r"\s+", "", n)
        return n

    cleaned = [_clean(v.get("name", "")) for v in variants if v.get("name")]
    if not cleaned:
        return ""
    # 取最短且非空的基础名
    base = min((c for c in cleaned if c), key=len, default="")
    return base or cleaned[0]


def ensure_stock_field(product: Dict) -> None:
    """确保产品包含库存字段，缺失时默认 0。"""
    if "stock" not in product:
        product["stock"] = 0


def ensure_spec_media_field(product: Dict) -> None:
    """确保产品包含包装图片字段。"""
    if "spec_media" not in product:
        product["spec_media"] = []


def format_indications(value) -> str:
    """把适应症字段统一格式化为逗号分隔字符串。"""
    if isinstance(value, list):
        return ", ".join(str(v).strip() for v in value if str(v).strip())
    return str(value or "").strip()


def format_bottom_price_usage(variants: List[Dict]) -> str:
    """
    为底价产品按规格生成用法用量说明。
    根据每条规格的兑水量以及原始用法用量中的疗程/给药方式信息生成。
    """
    if not variants:
        return ""

    primary_usage = str(variants[0].get("usage_info", "") or "").strip()

    # 从原始用法用量中提取疗程信息
    duration = ""
    duration_patterns = [
        r"连用\s*\d+[-~～]?\d*\s*日?",
        r"饮用\s*\d+[-~～]?\d*\s*小时",
        r"连?用\s*\d+[-~～]?\d*\s*天",
        r"用\s*\d+[-~～]?\d*\s*日?",
    ]
    for pat in duration_patterns:
        m = re.search(pat, primary_usage)
        if m:
            duration = m.group(0)
            break

    # 根据原始说明推断给药方式，默认混饮
    admin_route = "混饮"
    if "混饲" in primary_usage:
        admin_route = "混饲"
    elif "内服" in primary_usage:
        admin_route = "内服"
    elif "饮水" in primary_usage:
        admin_route = "饮水"
    elif "灌服" in primary_usage:
        admin_route = "灌服"

    parts = []
    for v in variants:
        spec = str(v.get("spec", "") or "").strip()
        water = str(v.get("water", "") or "").strip()
        if not spec or not water:
            continue
        line = f"{admin_route}：每袋兑水{water}"
        if duration:
            line += f"，{duration}"
        parts.append(f"{spec}：{line}")

    if not parts:
        return primary_usage

    return "\n".join(parts)


def render_variant_table_html(variants: List[Dict]) -> str:
    """
    生成规格对比表格 HTML。不包含交互按钮，仅用于静态展示。
    """
    rows = []
    for v in variants:
        price = v.get("price", 0)
        try:
            price_str = f"¥{float(price):.2f}"
        except (TypeError, ValueError):
            price_str = f"¥{price}"
        rows.append(
            "<tr>"
            f"<td>{v.get('spec', '') or '-'}</td>"
            f"<td>{price_str}</td>"
            f"<td>{v.get('stock', 0)}</td>"
            f"<td>{v.get('water', '') or '-'}</td>"
            f"<td>{format_indications(v.get('indications', [])) or '-'}</td>"
            "</tr>"
        )
    return (
        "<table style='width:100%; border-collapse: collapse; margin-top:10px;'>"
        "<thead><tr>"
        "<th style='text-align:left; padding:6px; border-bottom:1px solid #ddd;'>规格</th>"
        "<th style='text-align:left; padding:6px; border-bottom:1px solid #ddd;'>价格</th>"
        "<th style='text-align:left; padding:6px; border-bottom:1px solid #ddd;'>库存</th>"
        "<th style='text-align:left; padding:6px; border-bottom:1px solid #ddd;'>兑水量</th>"
        "<th style='text-align:left; padding:6px; border-bottom:1px solid #ddd;'>适应症</th>"
        "</tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table>"
    )


def collect_variant_images(variants: List[Dict]) -> List[Dict]:
    """汇总组内所有规格的包装图片。"""
    images = []
    for v in variants:
        for m in v.get("media") or []:
            if m.get("media_type") == "image":
                images.append(m)
        for m in v.get("spec_media") or []:
            if isinstance(m, dict) and m.get("media_type") == "image":
                images.append(m)
    return images


# 规格数值解析相关常量
# 单位统一换算系数：质量统一为克(g)，体积统一为毫升(ml)
_SPEC_UNIT_FACTORS = {
    "g": 1.0, "克": 1.0,
    "kg": 1000.0, "千克": 1000.0,
    "mg": 0.001, "毫克": 0.001,
    "斤": 500.0,
    "ml": 1.0, "毫升": 1.0,
    "l": 1000.0, "升": 1000.0,
}

# 包装容器单位，无质量/体积信息时作为数量级兜底
_CONTAINER_UNITS = re.compile(
    r"([0-9]+(?:\.[0-9]+)?)\s*(瓶|袋|盒|箱|桶|粒|片|支|包|听|罐|板|套)",
    re.IGNORECASE,
)

# 规格字段中首个数值+单位的匹配模式（质量/体积）
_SPEC_WEIGHT_VOLUME_PATTERN = re.compile(
    r"([0-9]+(?:\.[0-9]+)?)\s*(g|kg|mg|ml|l|斤|克|千克|毫克|毫升|升)",
    re.IGNORECASE,
)


def parse_spec_size(spec: str) -> Tuple[float, str]:
    """
    将包装规格字符串解析为可比较的数值。

    解析规则：
    1. 优先提取规格中第一个“数值+质量/体积单位”的组合，并按统一单位换算；
       质量统一换算为克(g)，体积统一换算为毫升(ml)。
    2. 若无质量/体积单位，则退而求其次提取“数值+容器单位”作为数量级参考。
    3. 仍无法解析时，提取任意数字作为兜底；全部失败则返回 0。

    返回：
        (normalized_value, unit_or_flag)
        unit_or_flag 为换算后的单位(g/ml)或解析方式标识(count/numeric/empty)。
    """
    text = str(spec or "").strip()
    if not text:
        return 0.0, ""

    # 1. 质量/体积优先
    matches = _SPEC_WEIGHT_VOLUME_PATTERN.findall(text)
    if matches:
        value_str, unit = matches[0]
        unit_key = unit.lower()
        factor = _SPEC_UNIT_FACTORS.get(unit_key, 1.0)
        normalized = float(value_str) * factor
        # 根据原始单位类型返回归一化单位标识
        normalized_unit = "g" if unit_key in ("g", "克", "kg", "千克", "mg", "毫克", "斤") else "ml"
        return normalized, normalized_unit

    # 2. 容器单位兜底
    container_match = _CONTAINER_UNITS.search(text)
    if container_match:
        return float(container_match.group(1)), "count"

    # 3. 任意数字兜底
    number_match = re.search(r"[0-9]+(?:\.[0-9]+)?", text)
    if number_match:
        return float(number_match.group(0)), "numeric"

    return 0.0, ""


def deduplicate_products_by_spec(
    products: List[Dict[str, Any]],
    group_by: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    按包装规格对产品记录进行去重。

    去重规则：
    - “相同产品”判定：默认使用 product_group_id；缺失时按 normalize_group_key
      （产品名称去除末尾规格/营销标注 + 主要成分）自动生成分组键。
    - 同一分组内若存在多条记录，仅保留包装规格（parse_spec_size 解析值）最大的一条，
      其余记录视为重复并删除。
    - 保留原始列表顺序：同一组内保留的记录在原列表中的相对位置不变。

    参数：
        products: 产品字典列表。
        group_by: 可选，指定用作分组键的字段名；默认 None 表示使用 product_group_id。

    返回：
        (deduplicated_products, report)
        report 包含去重时间、原始/保留/删除数量、分组明细、删除记录及保留依据。
    """
    if not products:
        return [], {
            "timestamp": datetime.now().isoformat(),
            "original_count": 0,
            "retained_count": 0,
            "deleted_count": 0,
            "group_count": 0,
            "deduplicated_group_count": 0,
            "criteria": _get_dedup_criteria(group_by),
            "groups": [],
            "deleted_records": [],
        }

    # 按分组键聚合，同时记录原列表索引以保留顺序
    groups: Dict[str, List[Tuple[int, Dict[str, Any]]]] = {}
    for idx, p in enumerate(products):
        if group_by:
            gid = str(p.get(group_by, "")).strip() or normalize_group_key(
                p.get("name", ""), p.get("main_component", "")
            )
        else:
            gid = str(p.get("product_group_id", "")).strip() or normalize_group_key(
                p.get("name", ""), p.get("main_component", "")
            )
        groups.setdefault(gid, []).append((idx, p))

    retained_items: List[Tuple[int, Dict[str, Any]]] = []
    deleted_records: List[Dict[str, Any]] = []
    group_reports: List[Dict[str, Any]] = []
    dedup_group_count = 0

    for gid, variants in groups.items():
        if len(variants) == 1:
            retained_items.append((variants[0][0], variants[0][1]))
            continue

        # 计算每条记录的规格解析值
        scored = []
        for orig_idx, p in variants:
            size, unit = parse_spec_size(p.get("spec", ""))
            scored.append({
                "index": orig_idx,
                "product": p,
                "size": size,
                "unit": unit,
            })

        # 按规格从大到小排序；规格相同时按原列表顺序（索引小者优先）
        scored.sort(key=lambda x: (-x["size"], x["index"]))

        retained = scored[0]
        removed = scored[1:]
        dedup_group_count += 1

        # 记录保留项的原始索引，最后统一排序以保持原始顺序
        retained_items.append((retained["index"], retained["product"]))

        for item in removed:
            p = item["product"]
            deleted_records.append({
                "id": p.get("id"),
                "name": p.get("name"),
                "spec": p.get("spec"),
                "product_group_id": gid,
                "parsed_size": item["size"],
                "parsed_unit": item["unit"],
                "retention_id": retained["product"].get("id"),
                "retention_spec": retained["product"].get("spec"),
                "reason": "同一产品组内存在规格更大的记录，仅保留规格最大者",
            })

        group_reports.append({
            "product_group_id": gid,
            "product_name": get_base_display_name([v[1] for v in variants]),
            "variant_count": len(variants),
            "retained_id": retained["product"].get("id"),
            "retained_name": retained["product"].get("name"),
            "retained_spec": retained["product"].get("spec"),
            "retained_parsed_size": retained["size"],
            "retained_parsed_unit": retained["unit"],
            "deleted_count": len(removed),
            "deleted_records": [
                {
                    "id": item["product"].get("id"),
                    "name": item["product"].get("name"),
                    "spec": item["product"].get("spec"),
                    "parsed_size": item["size"],
                    "parsed_unit": item["unit"],
                }
                for item in removed
            ],
            "selection_basis": (
                f"按包装规格大小排序，保留解析值最大的记录 "
                f"（{retained['product'].get('spec')}，解析值 {retained['size']:.4f} {retained['unit']}）"
            ),
        })

    # 按保留项在原列表中的索引重新排序，保持输入顺序
    retained_items.sort(key=lambda x: x[0])
    deduplicated = [p for _, p in retained_items]

    report = {
        "timestamp": datetime.now().isoformat(),
        "original_count": len(products),
        "retained_count": len(deduplicated),
        "deleted_count": len(deleted_records),
        "group_count": len(groups),
        "deduplicated_group_count": dedup_group_count,
        "criteria": _get_dedup_criteria(group_by),
        "groups": group_reports,
        "deleted_records": deleted_records,
    }
    return deduplicated, report


def _get_dedup_criteria(group_by: Optional[str]) -> Dict[str, str]:
    """返回去重判定标准的说明。"""
    same_product = (
        f"以字段 '{group_by}' 作为同一产品判定键；该字段为空时，"
        f"按 normalize_group_key（产品名称去末尾规格/营销标注 + 主要成分）自动生成"
    ) if group_by else (
        "以 product_group_id 作为同一产品判定键；缺失时按 normalize_group_key "
        "（产品名称去末尾规格/营销标注 + 主要成分）自动生成"
    )
    return {
        "same_product_definition": same_product,
        "spec_comparison_method": (
            "解析规格字段中首个数值+单位，质量统一换算为克(g)，"
            "体积统一换算为毫升(ml)；无质量/体积单位时以容器数量作为兜底参考"
        ),
        "retention_rule": "仅保留同一产品组内包装规格解析值最大的产品记录；解析值相同时保留原列表中先出现的记录",
    }


def save_deduplication_report(
    report: Dict[str, Any],
    output_dir: Optional[str] = None,
    filename_prefix: str = "dedup_report",
) -> str:
    """
    保存去重报告到文件，并同步更新 latest 报告文件。

    返回保存的报告文件绝对路径。
    """
    if output_dir is None:
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data",
            "dedup_reports",
        )
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(output_dir, f"{filename_prefix}_{timestamp}.json")
    latest_path = os.path.join(output_dir, f"{filename_prefix}_latest.json")

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report_path
