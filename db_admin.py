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


# ===================== 常量配置 =====================

DB_PATH = "huaying_products_full.json"
UPLOAD_DIR = "uploaded_media"
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

def _media_uploader(key_prefix: str) -> List[Dict]:
    files = st.file_uploader(
        "📎 上传图片 / 视频 / 文档（可多选）",
        type=sorted(ALLOWED_IMAGE | ALLOWED_VIDEO | ALLOWED_DOC),
        accept_multiple_files=True,
        key=f"{key_prefix}_uploader",
        help=f"单文件最大 {MAX_FILE_SIZE_MB}MB。图片：{', '.join(sorted(ALLOWED_IMAGE))}；"
             f"视频：{', '.join(sorted(ALLOWED_VIDEO))}；"
             f"文档：{', '.join(sorted(ALLOWED_DOC))}",
    )
    saved: List[Dict] = []
    if files:
        for f in files:
            try:
                meta = save_uploaded_file(f, sub_dir=key_prefix)
                saved.append(meta)
            except Exception as e:
                st.error(f"❌ {f.name}: {e}")
        if saved:
            st.success(f"✅ 已成功上传 {len(saved)} 个文件")
            for m in saved:
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
    return saved


def _drug_form(prefix: str, initial: Optional[Dict] = None) -> Dict:
    initial = initial or {}
    c1, c2 = st.columns(2)
    with c1:
        drug_id = st.text_input("ID *", value=initial.get("id", ""), key=f"{prefix}_id")
        name = st.text_input("产品名称 *", value=initial.get("name", ""), key=f"{prefix}_name")
        brand_name = st.text_input("商品名", value=initial.get("brand_name", ""), key=f"{prefix}_brand")
        main_component = st.text_input("主要成分 *", value=initial.get("main_component", ""), key=f"{prefix}_comp")
        spec = st.text_input("包装规格 *", value=initial.get("spec", ""), key=f"{prefix}_spec")
        water = st.text_input("兑水量", value=initial.get("water", ""), key=f"{prefix}_water")
    with c2:
        price = st.number_input(
            "价格 *", min_value=0.0, max_value=100000.0,
            value=float(initial.get("price", 0) or 0),
            step=0.1, key=f"{prefix}_price",
        )
        cat = initial.get("category", CATEGORY_OPTIONS[0])
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
        timing = st.text_input("时机", value=initial.get("timing", ""), key=f"{prefix}_timing")
        usage_info = st.text_area("用法用量", value=initial.get("usage_info", ""), key=f"{prefix}_usage")

    indications_default = initial.get("indications") or []
    if isinstance(indications_default, list):
        indications_default = "、".join(indications_default)
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
        "category": category,
        "source": source,
        "disease_types": disease_types,
        "egg_period_safe": egg_period_safe,
        "timing": timing.strip(),
        "usage_info": usage_info.strip(),
        "indications": indications_str,
    }


def _normalize(rec: Dict) -> Dict:
    rec["indications"] = _split_list_field(rec.get("indications"))
    if not rec.get("disease_types"):
        rec["disease_types"] = ["MIXED"]
    rec["content"] = rec.get("main_component", "")
    rec["product_name"] = rec.get("product_name") or rec.get("name", "")
    rec["egg_period_safe"] = _to_bool(rec.get("egg_period_safe", True))
    return rec


def _render_list(products: List[Dict]):
    st.markdown("#### 📋 产品列表")
    q = st.text_input("🔍 搜索（名称/成分/类别/ID）", "")
    if q:
        ql = q.lower()
        products = [
            p for p in products
            if ql in str(p.get("name", "")).lower()
            or ql in str(p.get("main_component", "")).lower()
            or ql in str(p.get("category", "")).lower()
            or ql in str(p.get("id", "")).lower()
        ]
    st.caption(f"显示 {len(products)} 条")
    if not products:
        st.info("无数据")
        return
    df = pd.DataFrame(products)
    show_cols = [c for c in ["id", "name", "main_component", "category", "spec",
                              "price", "source", "egg_period_safe"] if c in df.columns]
    st.dataframe(df[show_cols], use_container_width=True, height=420)


def _render_add(products: List[Dict], json_path: str):
    st.markdown("#### ➕ 新增药物")
    with st.form("add_drug_form", clear_on_submit=False):
        rec = _drug_form("add")
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

    st.markdown("##### 📎 附加资料（图片/视频/文档）")
    st.caption("提示：新增模式下附件会暂存到 `uploaded_media/add_media/`，"
                "保存药物时如需关联附件，请先保存药物后到'编辑'中再次上传。")
    _media_uploader("add_media")

    if st.button("↩️ 返回列表"):
        st.session_state["admin_op"] = "list"
        st.rerun()


def _render_edit(products: List[Dict], json_path: str):
    st.markdown("#### ✏️ 编辑药物")
    if not products:
        st.info("暂无药物可编辑")
        return

    options = {f"{p.get('id','')} - {p.get('name','')}": i for i, p in enumerate(products)}
    sel = st.selectbox("选择要编辑的药物", list(options.keys()))
    idx = options[sel]
    target = products[idx]

    with st.form(f"edit_form_{target.get('id', idx)}"):
        rec = _drug_form(f"edit_{target.get('id', idx)}", target)
        rec["id"] = target.get("id", "")
        c1, c2 = st.columns(2)
        with c1:
            save_btn = st.form_submit_button("💾 保存修改", use_container_width=True)
        with c2:
            cancel = st.form_submit_button("❌ 取消", use_container_width=True)
        if cancel:
            st.session_state["admin_op"] = "list"
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
                products[idx] = rec
                save_db(products, json_path)
                st.success(f"✅ 已更新 {rec['name']}")
                st.cache_resource.clear()
                st.session_state["admin_op"] = "list"
                st.rerun()

    st.markdown("##### 📎 上传补充资料")
    uploaded = _media_uploader(f"edit_{target.get('id', idx)}_media")
    if uploaded:
        if st.button(f"💾 将 {len(uploaded)} 个文件关联到该药物", type="primary"):
            media = list(target.get("media") or [])
            media.extend(uploaded)
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
    media_count = sum(len(p.get("media") or []) for p in products)
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
        _render_list(products)


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
