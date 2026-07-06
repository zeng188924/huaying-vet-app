# -*- coding: utf-8 -*-
"""
产品库去重脚本

功能：
- 读取 data/products/huaying_products_full.json
- 按 product_group_id 分组，对同一产品的多条记录按包装规格去重
- 仅保留每组中包装规格最大的产品记录
- 将去重后的数据写回原 JSON 文件（覆盖前自动生成备份）
- 生成去重报告到 data/dedup_reports/ 目录

使用方式：
    python scripts/deduplicate_products.py

可选参数：
    --input   输入文件路径（默认：data/products/huaying_products_full.json）
    --output  输出文件路径（默认：覆盖输入文件）
    --no-backup  不生成 .bak 备份文件
"""

import argparse
import json
import os
import sys
import shutil
from datetime import datetime


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_UTILS = os.path.join(ROOT, "src", "utils")
if SRC_UTILS not in sys.path:
    sys.path.insert(0, SRC_UTILS)

from product_utils import deduplicate_products_by_spec, save_deduplication_report


def parse_args():
    parser = argparse.ArgumentParser(description="产品库按包装规格去重")
    parser.add_argument(
        "--input",
        default=os.path.join(ROOT, "data", "products", "huaying_products_full.json"),
        help="输入产品库 JSON 文件路径",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="输出文件路径，默认覆盖输入文件",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="禁用覆盖前的备份",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    input_path = os.path.abspath(args.input)
    output_path = os.path.abspath(args.output or input_path)

    if not os.path.exists(input_path):
        print(f"错误：输入文件不存在 {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"[{datetime.now().isoformat()}] 开始读取产品库：{input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    print(f"原始产品记录数：{len(products)}")

    deduped_products, report = deduplicate_products_by_spec(products)

    print(
        f"去重完成：保留 {report['retained_count']} 条，"
        f"删除 {report['deleted_count']} 条，"
        f"涉及重复组 {report['deduplicated_group_count']} 个"
    )

    # 生成报告
    report_dir = os.path.join(ROOT, "data", "dedup_reports")
    report_path = save_deduplication_report(report, output_dir=report_dir)
    print(f"去重报告已保存：{report_path}")

    # 备份原文件
    if not args.no_backup and input_path == output_path:
        backup_path = f"{input_path}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(input_path, backup_path)
        print(f"原文件已备份：{backup_path}")

    # 写入去重后的数据
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(deduped_products, f, ensure_ascii=False, indent=2)

    print(f"去重后的产品库已保存：{output_path}")
    print(f"[{datetime.now().isoformat()}] 处理结束")


if __name__ == "__main__":
    main()
