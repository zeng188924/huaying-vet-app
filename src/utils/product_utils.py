# -*- coding: utf-8 -*-
"""
产品展示与规格聚合工具
- 通过 product_group_id 或名称归一化把同一产品的不同规格聚合在一起
- 提供统一的规格卡片渲染辅助函数
"""

import re
from collections import OrderedDict
from typing import List, Dict, Optional


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


def render_variant_table_html(variants: List[Dict]) -> str:
    """
    生成规格对比表格 HTML。不包含交互按钮，仅用于静态展示。
    """
    rows = []
    for v in variants:
        rows.append(
            "<tr>"
            f"<td>{v.get('spec', '') or '-'}</td>"
            f"<td>¥{v.get('price', 0)}</td>"
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
