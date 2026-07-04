# -*- coding: utf-8 -*-
"""
数据库管理模块
- 药物的增删改查（CRUD）
- 多媒体文件上传（图片 / 视频 / 文档）
- 数据校验（必填、格式、ID 唯一性、价格等）
- 配伍禁忌实时校验（基于 drug_compatibility 模块）
"""

import os
import re
import json
import uuid
import shutil
from datetime import datetime
from typing import List, Dict, Optional
from collections import OrderedDict

import pandas as pd
import streamlit as st

try:
    from drug_compatibility import (
        check_drug_compatibility,
        CompatibilityLevel,
    )
    _COMPAT_OK = True
except Exception:
    check_drug_compatibility = None
    CompatibilityLevel = None
    _COMPAT_OK = False

try:
    from content_extractor import (
        extract_product_info,
        parse_product_text,
        is_format_supported,
        is_extraction_available,
    )
    _EXTRACTOR_OK = True
except Exception:
    extract_product_info = None
    parse_product_text = None
    is_format_supported = None
    is_extraction_available = None
    _EXTRACTOR_OK = False

try:
    from product_utils import (
        group_products,
        get_base_display_name,
        normalize_group_key,
        render_variant_table_html,
        collect_variant_images,
        format_indications,
        ensure_stock_field,
        format_bottom_price_usage,
    )
    _PU_OK = True
except Exception:
    group_products = None
    get_base_display_name = None
    normalize_group_key = None
    render_variant_table_html = None
    collect_variant_images = None
    format_indications = None
    ensure_stock_field = None
    format_bottom_price_usage = None
    _PU_OK = False


# ===================== 常量配置 =====================

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(_ROOT, 'data', 'products', 'huaying_products_full.json')
UPLOAD_DIR = os.path.join(_ROOT, 'data', 'uploaded_media')
MAX_FILE_SIZE_MB = 200

REQUIRED_FIELDS = ["id", "name", "spec", "price", "main_component"]

DISEASE_TYPE_OPTIONS = [
    "BACTERIAL", "RESPIRATORY", "DIGESTIVE", "PARASITIC",
    "VIRAL", "MIXED", "NUTRITIONAL", "ENVIRONMENTAL",
]

CATEGORY_OPTIONS = [
    "化药", "中药", "抗生素", "营养类", "微生态", "免疫增强剂",
    "消毒剂类", "抗病毒类产品", "抗支原体药", "抗球虫类",
    "驱霉菌类产品", "解热镇痛", "保肝类护肾类", "特色类产品",
    "腺胃炎产品", "气囊炎类产品", "气管栓塞呼吸道药", "肠道类产品",
    "饲料添加剂", "维生素", "抗体类产品", "增蛋类产品",
    "防暑降温类产品", "营养增料促生长",
]

SOURCE_OPTIONS = ["底价目录", "明星产品", "产品信息-华英", "用户上传"]

ALLOWED_IMAGE = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}
ALLOWED_VIDEO = {"mp4", "mov", "avi", "mkv", "webm", "flv"}
ALLOWED_DOC = {"pdf", "doc", "docx", "xls", "xlsx", "txt", "md", "csv"}


# ===================== 文件存储 =====================

def _ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def _safe_filename(name: str) -> str:
    name = name.strip().replace(" ", "_")
    name = re.sub(r"[^\w.\-]", "", name)
    return name[:80] or "file"


def classify_ext(ext: str) -> Optional[str]:
    if ext in ALLOWED_IMAGE:
        return "image"
    if ext in ALLOWED_VIDEO:
        return "video"
    if ext in ALLOWED_DOC:
        return "doc"
    return None


def save_uploaded_file(uploaded_file, sub_dir: str = "") -> Dict:
    """保存上传文件到磁盘，返回元信息"""
    _ensure_dir(UPLOAD_DIR)
    target_dir = os.path.join(UPLOAD_DIR, sub_dir) if sub_dir else UPLOAD_DIR
    _ensure_dir(target_dir)

    raw_name = uploaded_file.name
    ext = raw_name.rsplit(".", 1)[-1].lower() if "." in raw_name else ""
    media_type = classify_ext(ext)
    if not media_type:
        raise ValueError(f"不支持的文件类型: .{ext}")

    size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(f"文件过大: {size_mb:.1f}MB（限制 {MAX_FILE_SIZE_MB}MB）")

    unique = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}_{_safe_filename(raw_name)}"
    save_path = os.path.join(target_dir, unique)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return {
        "filename": raw_name,
        "saved_as": unique,
        "path": save_path,
        "media_type": media_type,
        "ext": ext,
        "size_kb": round(size_mb * 1024, 1),
        "uploaded_at": datetime.now().isoformat(timespec="seconds"),
    }


# ===================== 数据库读写 =====================

def load_db(json_path: str = DB_PATH) -> List[Dict]:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_db(products: List[Dict], json_path: str = DB_PATH) -> None:
    """保存前自动备份为 .bak"""
    if os.path.exists(json_path):
        try:
            shutil.copyfile(json_path, json_path + ".bak")
        except Exception:
            pass
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)


# ===================== 数据校验 =====================

class ValidationError:
    def __init__(self, field: str, msg: str):
        self.field = field
        self.msg = msg

    def __str__(self) -> str:
        return f"{self.field}: {self.msg}"


def _split_list_field(value) -> List[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if value is None:
        return []
    parts = re.split(r"[、,，;；/]+", str(value))
    return [p.strip() for p in parts if p.strip()]


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return True
    return str(value).strip().lower() in ("true", "1", "yes", "y", "是", "✓")


def validate_drug_record(rec: Dict, existing_ids: Optional[set] = None,
                         check_unique: bool = True) -> List[ValidationError]:
    errs: List[ValidationError] = []

    for f in REQUIRED_FIELDS:
        if not str(rec.get(f, "")).strip():
            errs.append(ValidationError(f, f"字段 {f} 不能为空"))

    drug_id = str(rec.get("id", "")).strip()
    if drug_id and not re.match(r"^[A-Za-z0-9_\-]{2,20}$", drug_id):
        errs.append(ValidationError("id", "ID 仅支持字母/数字/下划线/连字符，2-20 位"))
    if check_unique and existing_ids is not None and drug_id in existing_ids:
        errs.append(ValidationError("id", f"ID {drug_id} 已存在"))

    try:
        price = float(rec.get("price", 0))
        if price < 0:
            errs.append(ValidationError("price", "价格不能为负数"))
        if price > 100000:
            errs.append(ValidationError("price", "价格过高，请确认"))
    except (TypeError, ValueError):
        errs.append(ValidationError("price", "价格必须为数字"))

    spec = str(rec.get("spec", "")).strip()
    if spec and len(spec) > 100:
        errs.append(ValidationError("spec", "规格描述过长（>100 字符）"))

    rec["indications"] = _split_list_field(rec.get("indications"))

    rec["disease_types"] = _split_list_field(rec.get("disease_types"))
    if not rec["disease_types"]:
        rec["disease_types"] = ["MIXED"]
    for dt in rec["disease_types"]:
        if dt not in DISEASE_TYPE_OPTIONS:
            errs.append(ValidationError("disease_types", f"未知疾病类型: {dt}"))

    rec["egg_period_safe"] = _to_bool(rec.get("egg_period_safe", True))

    if rec.get("category") and rec["category"] not in CATEGORY_OPTIONS:
        pass

    return errs


# ===================== 配伍校验 =====================

def validate_combination(products: List[Dict]) -> Dict:
    """对一组药物进行配伍禁忌校验"""
    if not _COMPAT_OK or check_drug_compatibility is None:
        return {
            "is_safe": True,
            "level": "未知",
            "conflicts": [],
            "suggestions": ["未加载配伍检测模块（drug_compatibility）"],
        }

    drug_dicts = []
    for p in products:
        name = p.get("name") or p.get("product_name") or ""
        comp = p.get("main_component") or p.get("content") or ""
        if not (name or comp):
            continue
        drug_dicts.append({"name": name, "component": comp})

    if len(drug_dicts) < 2:
        return {
            "is_safe": True,
            "level": "安全",
            "conflicts": [],
            "suggestions": ["至少需要 2 种药物才能进行配伍校验"],
        }

    try:
        result = check_drug_compatibility(drug_dicts)
    except Exception as e:
        return {
            "is_safe": True,
            "level": "未知",
            "conflicts": [],
            "suggestions": [f"配伍检测失败: {e}"],
        }

    level_str = result.level.value if hasattr(result.level, "value") else str(result.level)
    conflicts = []
    for c in result.conflicts:
        c_level = c.get("level")
        conflicts.append({
            "drug_a": c.get("drug_a", ""),
            "drug_b": c.get("drug_b", ""),
            "component_a": c.get("component_a", ""),
            "component_b": c.get("component_b", ""),
            "level": c_level.value if hasattr(c_level, "value") else str(c_level),
            "reason": c.get("reason", ""),
            "suggestion": c.get("suggestion", ""),
        })

    return {
        "is_safe": bool(result.is_safe),
        "level": level_str,
        "conflicts": conflicts,
        "suggestions": list(result.suggestions or []),
    }


# ===================== Streamlit 渲染 =====================

def _media_uploader(key_prefix: str, enable_extraction: bool = False) -> Dict:
    extract_note = ""
    if enable_extraction and _EXTRACTOR_OK:
        extract_note = "（支持图片OCR识别和语音转文字）"
    
    files = st.file_uploader(
        f"📎 上传图片 / 视频 / 文档（可多选）{extract_note}",
        type=sorted(ALLOWED_IMAGE | ALLOWED_VIDEO | ALLOWED_DOC),
        accept_multiple_files=True,
        key=f"{key_prefix}_uploader",
        help=f"单文件最大 {MAX_FILE_SIZE_MB}MB。图片：{', '.join(sorted(ALLOWED_IMAGE))}；"
             f"视频：{', '.join(sorted(ALLOWED_VIDEO))}；"
             f"文档：{', '.join(sorted(ALLOWED_DOC))}"
             f"{extract_note}",
    )
    
    result = {
        "saved_files": [],
        "extracted_fields": {},
    }
    
    if files:
        for f in files:
            try:
                meta = save_uploaded_file(f, sub_dir=key_prefix)
                result["saved_files"].append(meta)
                
                if enable_extraction and _EXTRACTOR_OK:
                    ext = f.name.rsplit(".", 1)[-1].lower() if "." in f.name else ""
                    if is_format_supported(ext):
                        with st.spinner(f"🔍 正在识别 {f.name}..."):
                            ext_result = extract_product_info(meta["path"], ext)
                            if ext_result["success"]:
                                for k, v in ext_result["parsed_fields"].items():
                                    if k not in result["extracted_fields"] or not result["extracted_fields"][k]:
                                        result["extracted_fields"][k] = v
                                st.success(f"✅ 已从 {f.name} 提取信息")
            except Exception as e:
                st.error(f"❌ {f.name}: {e}")
        
        if result["saved_files"]:
            st.success(f"✅ 已成功上传 {len(result['saved_files'])} 个文件")
            for m in result["saved_files"]:
                with st.expander(f"📎 {m['filename']}  ({m['size_kb']} KB, {m['media_type']})"):
                    if m["media_type"] == "image" and os.path.exists(m["path"]):
                        st.image(m["path"])
                    elif m["media_type"] == "video" and os.path.exists(m["path"]):
                        st.video(m["path"])
                    else:
                        st.write(f"已保存至：{m['path']}")
                        try:
                            with open(m["path"], "rb") as fp:
                                st.download_button(
                                    "⬇️ 下载", fp,
                                    file_name=m["filename"],
                                    key=f"dl_{m['saved_as']}",
                                )
                        except Exception:
                            pass
    
    return result


def _field_name_mapping() -> Dict[str, str]:
    return {
        "name": "产品名称",
        "brand_name": "商品名",
        "main_component": "主要成分",
        "spec": "包装规格",
        "price": "价格",
        "stock": "库存数量",
        "category": "类别",
        "usage_info": "用法用量",
        "water": "兑水量",
        "indications": "适应症",
        "timing": "时机",
        "product_group_id": "产品分组ID",
    }


def _render_extracted_fields(fields: Dict, action_label: str = "已提取"):
    if not fields:
        return
    st.info(f"📝 {action_label}的产品信息：")
    field_names = _field_name_mapping()
    for k, v in fields.items():
        if isinstance(v, list):
            v = "、".join(str(x) for x in v)
        st.write(f"  - **{field_names.get(k, k)}:** {v}")


def _render_manual_text_input(key_prefix: str, extract_key: str):
    st.markdown("##### ⌨️ 手动粘贴识别文本（兜底方案）")
    st.caption("如果图片自动识别不可用，可先用微信/QQ/其他 OCR 工具识别图片文字，粘贴到下方后点击“解析并填充”。")
    with st.form(key=f"{key_prefix}_manual_form", clear_on_submit=False):
        manual_text = st.text_area(
            "粘贴识别到的产品说明文字",
            height=200,
            key=f"{key_prefix}_manual_text",
        )
        submitted = st.form_submit_button("🔍 解析并填充")
        if submitted:
            text_value = (manual_text or "").strip()
            # 兼容部分场景下 widget 返回值未同步的情况，额外尝试 session_state
            if not text_value:
                text_value = str(st.session_state.get(f"{key_prefix}_manual_text", "")).strip()
            if parse_product_text and text_value:
                parse_result = parse_product_text(text_value)
                if parse_result["success"] and parse_result.get("parsed_fields"):
                    st.session_state[extract_key] = parse_result["parsed_fields"]
                    st.success("✅ 已解析并填充到表单，请核对后保存。")
                    _render_extracted_fields(parse_result["parsed_fields"], "已解析")
                    st.rerun()
                else:
                    st.warning("未能从粘贴文本中解析出有效字段，请检查文本内容或手动填写。")
            else:
                st.warning("请先粘贴识别文本。")


def _drug_form(prefix: str, initial: Optional[Dict] = None, extracted: Optional[Dict] = None,
               all_products: Optional[List[Dict]] = None) -> Dict:
    initial = initial or {}
    extracted = extracted or {}
    all_products = all_products or []

    def get_val(field: str, default=""):
        if field in extracted and extracted[field]:
            return extracted[field]
        return initial.get(field, default)

    # 已有分组选项，用于快速选择
    existing_groups = sorted({
        str(p.get("product_group_id", "")).strip()
        for p in all_products
        if str(p.get("product_group_id", "")).strip()
    })

    c1, c2 = st.columns(2)
    with c1:
        drug_id = st.text_input("ID *", value=initial.get("id", ""), key=f"{prefix}_id")
        name = st.text_input("产品名称 *", value=get_val("name"), key=f"{prefix}_name")
        brand_name = st.text_input("商品名", value=get_val("brand_name"), key=f"{prefix}_brand")
        main_component = st.text_input("主要成分 *", value=get_val("main_component"), key=f"{prefix}_comp")
        spec = st.text_input("包装规格 *", value=get_val("spec"), key=f"{prefix}_spec")
        water = st.text_input("兑水量", value=get_val("water"), key=f"{prefix}_water")
    with c2:
        price_val = get_val("price", 0)
        price = st.number_input(
            "价格 *", min_value=0.0, max_value=100000.0,
            value=float(price_val) if isinstance(price_val, (int, float)) else 0.0,
            step=0.1, key=f"{prefix}_price",
        )
        stock_val = get_val("stock", 0)
        stock = st.number_input(
            "库存数量", min_value=0, max_value=99999999,
            value=int(stock_val) if isinstance(stock_val, (int, float)) else 0,
            step=1, key=f"{prefix}_stock",
        )
        cat = get_val("category", CATEGORY_OPTIONS[0])
        category = st.selectbox(
            "类别", CATEGORY_OPTIONS,
            index=CATEGORY_OPTIONS.index(cat) if cat in CATEGORY_OPTIONS else 0,
            key=f"{prefix}_cat",
        )
        src = initial.get("source", "用户上传")
        source = st.selectbox(
            "数据来源", SOURCE_OPTIONS,
            index=SOURCE_OPTIONS.index(src) if src in SOURCE_OPTIONS else SOURCE_OPTIONS.index("用户上传"),
            key=f"{prefix}_src",
        )
        disease_types = st.multiselect(
            "疾病类型", DISEASE_TYPE_OPTIONS,
            default=initial.get("disease_types") or ["MIXED"],
            key=f"{prefix}_dt",
        )
        egg_period_safe = st.checkbox(
            "产蛋期可用", value=bool(initial.get("egg_period_safe", True)),
            key=f"{prefix}_egg",
        )
        timing = st.text_input("时机", value=get_val("timing"), key=f"{prefix}_timing")
        usage_info = st.text_area("用法用量", value=get_val("usage_info"), key=f"{prefix}_usage")

    # 产品分组：既支持手工输入，也支持下拉选择已有分组
    group_default = str(initial.get("product_group_id", "")).strip()
    if not group_default and normalize_group_key:
        group_default = normalize_group_key(get_val("name"), get_val("main_component"))
    c_g1, c_g2 = st.columns([2, 1])
    with c_g1:
        group_id = st.text_input(
            "产品分组 ID（同产品不同规格请保持一致）",
            value=group_default,
            key=f"{prefix}_group_id",
        )
    with c_g2:
        selected_existing = st.selectbox(
            "或选择已有分组",
            ["-- 不选择 --"] + existing_groups,
            key=f"{prefix}_group_select",
        )
    if selected_existing and selected_existing != "-- 不选择 --":
        group_id = selected_existing

    indications_default = get_val("indications", [])
    if isinstance(indications_default, list):
        indications_default = "、".join(indications_default)
    elif initial.get("indications") and not indications_default:
        init_ind = initial.get("indications")
        if isinstance(init_ind, list):
            indications_default = "、".join(init_ind)
        else:
            indications_default = str(init_ind)
    indications_str = st.text_input(
        "适应症（用 、,;； 分隔）",
        value=indications_default,
        key=f"{prefix}_ind",
    )

    return {
        "id": drug_id.strip(),
        "name": name.strip(),
        "brand_name": brand_name.strip(),
        "main_component": main_component.strip(),
        "spec": spec.strip(),
        "water": water.strip(),
        "price": price,
        "stock": int(stock),
        "category": category,
        "source": source,
        "disease_types": disease_types,
        "egg_period_safe": egg_period_safe,
        "timing": timing.strip(),
        "usage_info": usage_info.strip(),
        "indications": indications_str,
        "product_group_id": group_id.strip(),
    }


def _normalize(rec: Dict) -> Dict:
    rec["indications"] = _split_list_field(rec.get("indications"))
    if not rec.get("disease_types"):
        rec["disease_types"] = ["MIXED"]
    rec["content"] = rec.get("main_component", "")
    rec["product_name"] = rec.get("product_name") or rec.get("name", "")
    rec["egg_period_safe"] = _to_bool(rec.get("egg_period_safe", True))
    # 规格相关字段
    if "stock" not in rec or rec["stock"] is None:
        rec["stock"] = 0
    else:
        try:
            rec["stock"] = int(rec["stock"])
        except (TypeError, ValueError):
            rec["stock"] = 0
    if "spec_media" not in rec:
        rec["spec_media"] = []
    if not rec.get("product_group_id") and normalize_group_key:
        rec["product_group_id"] = normalize_group_key(
            rec.get("name", ""), rec.get("main_component", "")
        )
    return rec


def _render_list(products: List[Dict], json_path: str = DB_PATH):
    st.markdown("#### 📋 产品列表")
    q = st.text_input("🔍 搜索（名称/成分/类别/ID）", "")

    groups = group_products(products) if _PU_OK and group_products else OrderedDict(
        (p.get("id"), [p]) for p in products
    )

    if q:
        ql = q.lower()
        filtered_groups = OrderedDict()
        for gid, variants in groups.items():
            if any(
                ql in str(v.get("name", "")).lower()
                or ql in str(v.get("main_component", "")).lower()
                or ql in str(v.get("category", "")).lower()
                or ql in str(v.get("id", "")).lower()
                for v in variants
            ):
                filtered_groups[gid] = variants
        groups = filtered_groups

    st.caption(f"显示 {len(groups)} 个产品（共 {sum(len(v) for v in groups.values())} 条规格）")
    if not groups:
        st.info("无数据")
        return

    for gid, variants in groups.items():
        primary = variants[0]
        is_multi = len(variants) > 1
        base_name = get_base_display_name(variants) if _PU_OK and get_base_display_name else primary.get("name", "")
        category = primary.get("category", "")
        source = primary.get("source", "")
        egg_safe = primary.get("egg_period_safe", True)
        usage = primary.get("usage_info", "")
        indications = format_indications(primary.get("indications", [])) if _PU_OK and format_indications else ""

        with st.container(border=True):
            cols = st.columns([4, 1])
            with cols[0]:
                st.markdown(f"**{base_name}**")
            with cols[1]:
                if is_multi:
                    st.markdown(f"<span style='color:#1976d2'>📦 {len(variants)} 个规格</span>", unsafe_allow_html=True)

            info_items = [
                f"🏷️ 类别: {category}",
                f"📦 来源: {source}",
                "✅ 产蛋期可用" if egg_safe else "❌ 产蛋期禁用",
            ]
            st.caption(" · ".join(info_items))

            if indications:
                st.markdown(f"**适应症：** {indications}")
            if source == "底价目录" and _PU_OK and format_bottom_price_usage:
                bottom_usage = format_bottom_price_usage(variants)
                if bottom_usage:
                    st.markdown(
                        f"**用法用量：**<br>{bottom_usage.replace(chr(10), '<br>')}",
                        unsafe_allow_html=True,
                    )
            elif usage:
                st.markdown(f"**用法用量：** {usage}")

            with st.expander("📋 查看规格详情 / 包装图片"):
                if _PU_OK and render_variant_table_html:
                    st.markdown(render_variant_table_html(variants), unsafe_allow_html=True)
                else:
                    for v in variants:
                        st.write(f"- {v.get('spec')} | ¥{v.get('price')} | 库存 {v.get('stock', 0)}")

                images = collect_variant_images(variants) if _PU_OK and collect_variant_images else []
                if images:
                    st.markdown("**包装图片：**")
                    img_cols = st.columns(min(len(images), 4))
                    for idx, img in enumerate(images):
                        p = img.get("path", "")
                        if p and os.path.exists(p):
                            with img_cols[idx % 4]:
                                st.image(p, caption=img.get("filename", ""))

                st.markdown("**操作：**")
                for v in variants:
                    c1, c2 = st.columns([1, 5])
                    with c1:
                        if st.button("编辑", key=f"list_edit_{v.get('id', '')}", use_container_width=True):
                            st.session_state["admin_op"] = "edit"
                            st.session_state["edit_target_id"] = v.get("id", "")
                            st.rerun()
                    with c2:
                        if st.button(f"删除 {v.get('spec', v.get('name', ''))}", key=f"list_del_{v.get('id', '')}", use_container_width=True, type="secondary"):
                            products[:] = [p for p in products if p.get("id") != v.get("id")]
                            save_db(products, json_path)
                            st.success(f"已删除 {v.get('name', '')}")
                            st.rerun()


def _render_add(products: List[Dict], json_path: str):
    st.markdown("#### ➕ 新增药物")

    extract_key = "extracted_add"
    if extract_key not in st.session_state:
        st.session_state[extract_key] = {}

    if st.button("🔄 重置提取内容", key="reset_extract_add"):
        st.session_state[extract_key] = {}
        st.rerun()

    # ========== 第一步：资料识别（必须在表单渲染之前完成，否则无法回填） ==========
    st.markdown("##### 📎 附加资料（图片/视频/文档）")
    st.caption("提示：上传图片或语音文件时，系统会自动识别并提取产品信息，填充到表单中。")

    if not _EXTRACTOR_OK:
        st.warning("⚠️ 图片自动识别当前不可用：未安装 OCR 依赖。建议方案：1）安装 Tesseract OCR（推荐）；2）使用下方的“手动粘贴识别文本”功能。")
    elif not is_extraction_available or not is_extraction_available():
        st.warning("⚠️ 图片自动识别当前不可用：OCR 引擎未能正常加载。请检查 Tesseract 是否已安装并配置到系统 PATH，或使用下方手动粘贴方案。")

    upload_result = _media_uploader("add_media", enable_extraction=True)
    if upload_result.get("extracted_fields"):
        st.session_state[extract_key] = upload_result["extracted_fields"]
        _render_extracted_fields(upload_result["extracted_fields"])

    _render_manual_text_input("add", extract_key)

    # ========== 第二步：渲染表单（使用已识别的字段作为默认值） ==========
    with st.form("add_drug_form", clear_on_submit=False):
        rec = _drug_form("add", extracted=st.session_state.get(extract_key, {}), all_products=products)
        submit = st.form_submit_button("✅ 保存", use_container_width=True)
        if submit:
            existing = {p.get("id", "") for p in products}
            errs = validate_drug_record(rec, existing, check_unique=True)
            if errs:
                st.error("❌ 数据校验未通过：")
                for e in errs:
                    st.write(f"  - {e}")
            else:
                rec = _normalize(rec)
                same_comp = [p for p in products
                             if p.get("main_component") == rec["main_component"]
                             and p.get("main_component")]
                warning_pairs = []
                if rec["main_component"] and same_comp:
                    res = validate_combination([rec] + same_comp[:1])
                    if not res["is_safe"]:
                        warning_pairs = res["conflicts"]

                products.append(rec)
                save_db(products, json_path)
                st.success(f"✅ 已保存 {rec['name']}（共 {len(products)} 条）")
                if warning_pairs:
                    st.warning("⚠️ 新增药物与已有药物存在配伍风险，请在'配伍校验'中确认：")
                    for c in warning_pairs:
                        st.write(f"  - {c['drug_a']} + {c['drug_b']}（{c['level']}）")
                st.cache_resource.clear()
                st.session_state[extract_key] = {}

    if st.button("↩️ 返回列表"):
        st.session_state["admin_op"] = "list"
        st.session_state[extract_key] = {}
        st.rerun()


def _render_edit(products: List[Dict], json_path: str):
    st.markdown("#### ✏️ 编辑药物")
    if not products:
        st.info("暂无药物可编辑")
        return

    target_id = st.session_state.get("edit_target_id")
    if target_id:
        try:
            idx = next(i for i, p in enumerate(products) if p.get("id") == target_id)
        except StopIteration:
            st.error("要编辑的药物不存在，已回到列表")
            st.session_state["admin_op"] = "list"
            st.session_state["edit_target_id"] = None
            st.rerun()
            return
        target = products[idx]
    else:
        options = {f"{p.get('id','')} - {p.get('name','')}": i for i, p in enumerate(products)}
        sel = st.selectbox("选择要编辑的药物", list(options.keys()))
        idx = options[sel]
        target = products[idx]

    extract_key = f"extracted_edit_{target.get('id', idx)}"
    if extract_key not in st.session_state:
        st.session_state[extract_key] = {}

    if st.button("🔄 重置提取内容", key=f"reset_extract_edit_{target.get('id', idx)}"):
        st.session_state[extract_key] = {}
        st.rerun()

    # 显示同组其它规格
    if _PU_OK and group_products:
        groups = group_products(products)
        gid = target.get("product_group_id", target.get("id"))
        siblings = [v for v in groups.get(gid, []) if v.get("id") != target.get("id")]
        if siblings:
            with st.expander("📦 同产品其它规格"):
                st.markdown(render_variant_table_html(siblings), unsafe_allow_html=True)

    # ========== 第一步：资料识别（必须在表单渲染之前完成，否则无法回填） ==========
    st.markdown("##### 📎 上传补充资料")

    if not _EXTRACTOR_OK:
        st.warning("⚠️ 图片自动识别当前不可用：未安装 OCR 依赖。建议方案：1）安装 Tesseract OCR（推荐）；2）使用下方的“手动粘贴识别文本”功能。")
    elif not is_extraction_available or not is_extraction_available():
        st.warning("⚠️ 图片自动识别当前不可用：OCR 引擎未能正常加载。请检查 Tesseract 是否已安装并配置到系统 PATH，或使用下方手动粘贴方案。")

    upload_result = _media_uploader(f"edit_{target.get('id', idx)}_media", enable_extraction=True)
    if upload_result.get("extracted_fields"):
        st.session_state[extract_key] = upload_result["extracted_fields"]
        _render_extracted_fields(upload_result["extracted_fields"])

    _render_manual_text_input(f"edit_{target.get('id', idx)}", extract_key)

    # ========== 第二步：渲染表单（使用已识别的字段覆盖原有字段） ==========
    with st.form(f"edit_form_{target.get('id', idx)}"):
        rec = _drug_form(f"edit_{target.get('id', idx)}", target, extracted=st.session_state.get(extract_key, {}), all_products=products)
        rec["id"] = target.get("id", "")
        c1, c2 = st.columns(2)
        with c1:
            save_btn = st.form_submit_button("💾 保存修改", use_container_width=True)
        with c2:
            cancel = st.form_submit_button("❌ 取消", use_container_width=True)
        if cancel:
            st.session_state["admin_op"] = "list"
            st.session_state["edit_target_id"] = None
            st.session_state[extract_key] = {}
            st.rerun()
        if save_btn:
            errs = validate_drug_record(rec, check_unique=False)
            if errs:
                st.error("❌ 数据校验未通过：")
                for e in errs:
                    st.write(f"  - {e}")
            else:
                rec = _normalize(rec)
                rec["id"] = target.get("id", "")
                rec["media"] = target.get("media", [])
                rec["spec_media"] = target.get("spec_media", [])
                products[idx] = rec
                save_db(products, json_path)
                st.success(f"✅ 已更新 {rec['name']}")
                st.cache_resource.clear()
                st.session_state["admin_op"] = "list"
                st.session_state["edit_target_id"] = None
                st.session_state[extract_key] = {}
                st.rerun()

    uploaded_files = upload_result.get("saved_files", [])
    if uploaded_files:
        if st.button(f"💾 将 {len(uploaded_files)} 个文件关联到该药物", type="primary"):
            media = list(target.get("media") or [])
            media.extend(uploaded_files)
            target["media"] = media
            products[idx] = target
            save_db(products, json_path)
            st.success("✅ 已关联")
            st.cache_resource.clear()
            st.rerun()

    media = target.get("media") or []
    if media:
        st.markdown("##### 已关联资料")
        cols = st.columns(3)
        for i, m in enumerate(media):
            with cols[i % 3]:
                with st.container(border=True):
                    st.caption(f"📎 {m.get('filename','')}")
                    p = m.get("path", "")
                    if m.get("media_type") == "image" and p and os.path.exists(p):
                        st.image(p)
                    elif m.get("media_type") == "video" and p and os.path.exists(p):
                        st.video(p)
                    else:
                        st.write(f"类型: {m.get('media_type','')}")
                        st.write(f"大小: {m.get('size_kb','')} KB")
                    if st.button("🗑️ 移除", key=f"rm_{m.get('saved_as', i)}"):
                        media.pop(i)
                        target["media"] = media
                        products[idx] = target
                        save_db(products, json_path)
                        st.cache_resource.clear()
                        st.rerun()

    if st.button("↩️ 返回列表"):
        st.session_state["admin_op"] = "list"
        st.session_state[extract_key] = {}
        st.rerun()


def _render_delete(products: List[Dict], json_path: str):
    st.markdown("#### 🗑️ 删除药物")
    if not products:
        st.info("暂无药物可删除")
        return
    options = {f"{p.get('id','')} - {p.get('name','')}": i for i, p in enumerate(products)}
    sel = st.multiselect("选择要删除的药物（可多选）", list(options.keys()))
    confirm = st.text_input("⚠️ 确认删除请输入 DELETE")
    if st.button("⚠️ 确认删除", type="primary"):
        if confirm != "DELETE":
            st.error("请先输入 DELETE 以确认")
        elif not sel:
            st.warning("请至少选择一项")
        else:
            deleted_ids = []
            for k in sel:
                idx = options[k]
                deleted_ids.append(products[idx].get("id", ""))
                products.pop(idx)
            save_db(products, json_path)
            st.success(f"✅ 已删除 {len(deleted_ids)} 项: {', '.join(deleted_ids)}")
            st.cache_resource.clear()
            st.session_state["admin_op"] = "list"
            st.rerun()

    if st.button("↩️ 返回列表"):
        st.session_state["admin_op"] = "list"
        st.rerun()


def _render_combo(products: List[Dict]):
    st.markdown("#### 🧪 药物搭配合理性校验")
    st.caption("从数据库选择 2 个及以上药物（最多 8 个），实时检测配伍禁忌与合理性")

    if not _COMPAT_OK:
        st.warning("⚠️ 未加载 drug_compatibility 模块，配伍校验不可用")

    name_map = {
        f"{p.get('name','')} | {p.get('main_component','')}": p
        for p in products
    }
    chosen = st.multiselect(
        "选择待组合药物",
        list(name_map.keys()),
        max_selections=8,
    )

    auto_run = st.checkbox("组合变化时自动校验", value=True)
    run = auto_run or st.button("🔍 开始校验")

    if run and chosen:
        sel_products = [name_map[c] for c in chosen]
        res = validate_combination(sel_products)

        if res["is_safe"]:
            st.success(f"✅ 组合{res['level']}（未发现已知配伍禁忌）")
        elif res["level"] in ("禁忌", "INCOMPATIBLE"):
            st.error(f"❌ 组合存在 **{res['level']}**，请勿同时使用")
        else:
            st.warning(f"⚠️ 组合需 **{res['level']}**，建议调整剂量或间隔使用")

        for c in res["conflicts"]:
            with st.expander(f"⚠️ {c['drug_a']} + {c['drug_b']}（{c['level']}）"):
                st.write(f"**涉及成分:** {c.get('component_a','')} ↔ {c.get('component_b','')}")
                st.write(f"**原因:** {c['reason']}")
                st.write(f"**建议:** {c['suggestion']}")

        if res["suggestions"]:
            st.info("💡 综合建议: " + " | ".join(res["suggestions"]))

    if st.button("↩️ 返回列表"):
        st.session_state["admin_op"] = "list"
        st.rerun()


def render_admin_tab(json_path: str = DB_PATH):
    """数据库管理 Tab 入口（在 app.py 中调用）"""
    st.subheader("🛠️ 数据库管理")
    st.caption(f"数据文件: `{json_path}` · 上传目录: `{UPLOAD_DIR}/`")

    try:
        products = load_db(json_path)
    except Exception as e:
        st.error(f"加载数据库失败: {e}")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("产品总数", len(products))
    sources = {p.get("source", "未知") for p in products}
    c2.metric("数据来源数", len(sources))
    media_count = sum(len(p.get("media") or []) + len(p.get("spec_media") or []) for p in products)
    c3.metric("已关联资料", media_count)

    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("➕ 新增", use_container_width=True):
        st.session_state["admin_op"] = "add"
    if c2.button("✏️ 编辑", use_container_width=True):
        st.session_state["admin_op"] = "edit"
    if c3.button("🗑️ 删除", use_container_width=True):
        st.session_state["admin_op"] = "delete"
    if c4.button("🧪 配伍校验", use_container_width=True):
        st.session_state["admin_op"] = "combo"

    op = st.session_state.get("admin_op", "list")
    st.divider()

    if op == "add":
        _render_add(products, json_path)
    elif op == "edit":
        _render_edit(products, json_path)
    elif op == "delete":
        _render_delete(products, json_path)
    elif op == "combo":
        _render_combo(products)
    else:
        _render_list(products, json_path)


# ===================== 实时调取辅助接口 =====================

def get_drug_by_id(drug_id: str, json_path: str = DB_PATH) -> Optional[Dict]:
    """供推荐系统实时调取药物详情"""
    for p in load_db(json_path):
        if p.get("id") == drug_id:
            return p
    return None


def get_drug_media(drug_id: str, json_path: str = DB_PATH) -> List[Dict]:
    """供 UI 实时展示药物关联的图片/视频/文档"""
    drug = get_drug_by_id(drug_id, json_path)
    if not drug:
        return []
    return drug.get("media") or []
