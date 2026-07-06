import streamlit as st
import pandas as pd
import sys
import os

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_root, 'src'))
sys.path.insert(0, os.path.join(_root, 'src', 'core'))
sys.path.insert(0, os.path.join(_root, 'src', 'utils'))

from drug_recommendation_system_full import (
    create_recommender, quick_recommend, DrugDatabase,
    DISEASE_TYPE_CATEGORIES, DISEASE_CATEGORY_DISPLAY,
    DISEASE_CATEGORY_DISPLAY_REVERSE
)
from disease_knowledge import get_disease_knowledge_base
from key_matters import get_key_matters, get_summary_points
from environment_adjustment import get_environment_adjustment_engine, ShedEnvironment
from src.core.diagnosis_engine import get_diagnosis_engine, get_safety_guardian, get_symptoms_by_disease_category
from src.utils.data_manager import (
    get_all_farmer_profiles, get_sheds_by_farmer, get_shed, update_shed,
    get_medication_history, add_medication_history, delete_medication_history,
    start_new_batch
)
from src.admin.content_extractor import extract_product_info
from src.utils.lab_report_parser import parse_lab_report

st.set_page_config(
    page_title="智能用药推荐",
    page_icon="💊",
    layout="wide"
)

@st.cache_resource
def get_recommender(_version="v20260706_11"):
    json_path = os.path.join(_root, 'data', 'products', 'huaying_products_full.json')
    recommender = create_recommender(json_path)
    return recommender

def local_css():
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #1e88e5 0%, #43a047 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
    }
    .main-header h1 { margin: 0; font-size: 2.2em; }
    .main-header p { margin: 10px 0 0 0; font-size: 1.1em; opacity: 0.9; }
    
    .drug-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        border-left: 5px solid #1e88e5;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .drug-card h3 { color: #1565c0; margin-bottom: 10px; }
    
    .combination-card {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        border-left: 5px solid #f57c00;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .info-badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.85em;
        margin: 3px;
        font-weight: 500;
    }
    .badge-blue { background-color: #e3f2fd; color: #1565c0; }
    .badge-green { background-color: #e8f5e9; color: #2e7d32; }
    .badge-orange { background-color: #fff3e0; color: #ef6c00; }
    .badge-red { background-color: #ffebee; color: #c62828; }
    
    .stButton>button {
        background: linear-gradient(90deg, #1e88e5 0%, #43a047 100%);
        color: white;
        font-weight: bold;
        padding: 12px 24px;
        border-radius: 25px;
        border: none;
        width: 100%;
    }
    
    .key-matter-card {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-radius: 10px;
        padding: 15px;
        margin: 8px 0;
        border-left: 4px solid #1976d2;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .profile-section {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        border: 1px solid #e9ecef;
    }
    </style>
    """, unsafe_allow_html=True)

local_css()

st.markdown("""
<div class="main-header">
    <h1>💊 智能用药推荐系统</h1>
    <p>基于养殖环境和病症信息，生成精准用药方案</p>
</div>
""", unsafe_allow_html=True)

farmers = get_all_farmer_profiles()

if not farmers:
    st.warning("⚠️ 请先在「用户档案」页面创建养殖户档案")
    st.stop()

col1, col2 = st.columns(2)

with col1:
    selected_farmer = st.selectbox(
        "选择养殖户",
        farmers,
        format_func=lambda f: f"{f.name} (养殖{str(f.farming_years)}年)",
        key="farmer_select"
    )

with col2:
    sheds = get_sheds_by_farmer(selected_farmer.id) if selected_farmer else []
    shed_options = [(s.id, s.name) for s in sheds]
    
    if sheds:
        selected_shed_name = st.selectbox(
            "选择棚舍",
            [s.name for s in sheds],
            key="shed_select"
        )
        selected_shed = next((s for s in sheds if s.name == selected_shed_name), None)
    else:
        selected_shed = None
        st.info("该养殖户暂无棚舍信息，请先添加")

st.divider()

with st.sidebar:
    st.header("📝 病情信息录入")
    
    animal_type_options = ["肉鸡", "蛋鸡", "种鸡", "肉鸭", "蛋鸭", "鹅", "火鸡", "鸽子", "鹌鹑"]
    if selected_shed:
        shed_type_mapping = {
            "肉鸡舍": "肉鸡", "蛋鸡舍": "蛋鸡", "种鸡舍": "种鸡",
            "肉鸭舍": "肉鸭", "蛋鸭舍": "蛋鸭", "鹅舍": "鹅",
            "火鸡舍": "火鸡", "鸽子舍": "鸽子", "鹌鹑舍": "鹌鹑"
        }
        breed_mapping = {
            "白羽肉鸡": "肉鸡", "黄羽肉鸡": "肉鸡", "蛋鸡": "蛋鸡",
            "种鸡": "种鸡", "樱桃谷鸭": "肉鸭", "麻鸭": "蛋鸭",
            "鹅": "鹅", "火鸡": "火鸡", "鸽子": "鸽子", "鹌鹑": "鹌鹑"
        }
        animal_type_default = shed_type_mapping.get(selected_shed.type, breed_mapping.get(selected_shed.breed, "肉鸡"))
        scale_default = selected_shed.scale
        # 切换棚舍时自动同步动物种类
        if st.session_state.get("pc_prev_shed_id") != selected_shed.id:
            st.session_state["pc_animal_type"] = animal_type_default
            st.session_state["pc_prev_shed_id"] = selected_shed.id
    else:
        animal_type_default = "肉鸡"
        scale_default = "中规模(1000-10000只)"

    animal_type = st.selectbox(
        "动物种类",
        animal_type_options,
        index=animal_type_options.index(st.session_state.get("pc_animal_type", animal_type_default)),
        help="选择养殖的动物种类",
        key="pc_animal_type"
    )
    
    age_stage = st.selectbox(
        "日龄/养殖阶段",
        ["育雏期(0-14日龄)", "育成期(15-35日龄)", "育肥期(36日龄-出栏)", 
         "产蛋前期", "产蛋高峰期", "产蛋后期"],
        help="选择当前的养殖阶段"
    )

    # 实验室检测报告识别
    st.markdown("---")
    st.header("🔬 实验室检测报告识别")
    lab_file = st.file_uploader(
        "上传检测报告（图片/PDF）",
        type=["jpg", "jpeg", "png", "pdf"],
        key="pc_lab_file",
        help="系统会自动识别报告中的疾病和症状关键词，回填到下方表单"
    )
    lab_text = st.text_area(
        "或粘贴检测报告文本",
        placeholder="可直接粘贴检测报告的结论或全文...",
        key="pc_lab_text",
        height=80
    )

    if st.button("🧪 识别报告内容", key="pc_parse_lab"):
        parsed = None
        if lab_file is not None:
            import tempfile
            ext = lab_file.name.rsplit(".", 1)[-1].lower()
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                    tmp.write(lab_file.getvalue())
                    tmp_path = tmp.name
                extract_result = extract_product_info(tmp_path, ext)
                if extract_result.get("success"):
                    parsed = parse_lab_report(extract_result.get("raw_text", ""))
                else:
                    st.warning(f"报告识别失败：{extract_result.get('error', '未知错误')}，可尝试粘贴文本")
            except Exception as e:
                st.warning(f"报告处理出错：{e}")
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        if parsed is None and lab_text.strip():
            parsed = parse_lab_report(lab_text)

        if parsed:
            st.success(
                f"识别结果：{parsed['disease_category']} - {parsed['disease_name']}（置信度：{parsed['confidence']}）"
            )
            if parsed.get("symptom_summary"):
                st.caption(f"识别到的症状：{parsed['symptom_summary']}")
            st.session_state['pc_auto_symptom'] = parsed['symptom_summary'] or f"实验室检测提示：{parsed['disease_name']}"
            st.session_state['pc_auto_disease'] = parsed['disease_name']
            st.rerun()
        else:
            st.info("未能从报告中识别到明确疾病，请手动填写")

    # 主要症状
    st.markdown("---")
    st.header("📝 主要症状")
    # 若典型症状选择器要求回填，则在实例化 text_area 前先设置其 key 值
    if 'pc_pending_symptom_fill' in st.session_state:
        st.session_state['symptom_input'] = st.session_state['pc_pending_symptom_fill']
        del st.session_state['pc_pending_symptom_fill']
    auto_symptom = st.session_state.get('pc_auto_symptom', '')
    symptom = st.text_area(
        "主要症状（请详细描述）",
        value=auto_symptom,
        placeholder="请尽量详细：咳嗽/呼噜/甩鼻/流涕/流泪/张口呼吸/减料/发热/粪便异常/死淘情况等",
        help="描述动物的主要症状，越详细推荐越准确。建议不少于20字。",
        key="symptom_input",
        height=100
    )
    if symptom:
        symptom_len = len(symptom.strip())
        if symptom_len < 10:
            st.warning("⚠️ 症状描述较简略，建议补充咳嗽频率、呼吸方式、精神状态、采食量、粪便等细节，推荐会更准确。")
        elif symptom_len < 20:
            st.info("ℹ️ 症状描述尚可，如能补充发病日龄、死淘数、粪便/产蛋细节，推荐会更精准。")

    # 发病类型：二级分类
    auto_disease = st.session_state.get('pc_auto_disease', '')
    disease_categories = list(DISEASE_TYPE_CATEGORIES.keys())
    category_display_options = [DISEASE_CATEGORY_DISPLAY.get(cat, cat) for cat in disease_categories]
    auto_category = None
    if auto_disease:
        for cat, diseases in DISEASE_TYPE_CATEGORIES.items():
            if auto_disease == cat or auto_disease in diseases:
                auto_category = cat
                break
    category_index = disease_categories.index(auto_category) if auto_category in disease_categories else 0
    disease_category_display = st.selectbox(
        "发病大类",
        category_display_options,
        index=category_index,
        help="先选择疾病大类，具体疾病会随大类自动调整",
        key="disease_category_pc"
    )
    disease_category = DISEASE_CATEGORY_DISPLAY_REVERSE.get(disease_category_display, disease_category_display)
    specific_diseases = DISEASE_TYPE_CATEGORIES.get(disease_category, [])
    specific_index = specific_diseases.index(auto_disease) if auto_disease in specific_diseases else 0
    disease_type = st.selectbox(
        "具体疾病",
        specific_diseases,
        index=specific_index,
        help="再选择具体疾病",
        key="disease_type_pc"
    )

    # 根据发病大类联动展示典型症状选项，供用户快速填充主要症状
    category_symptoms = get_symptoms_by_disease_category(disease_category)
    if category_symptoms:
        with st.expander("🩺 选择典型症状（自动填充到上方主要症状）", expanded=True):
            st.caption("勾选与本群发病相关的典型症状，点击“填入主要症状”即可追加到上方输入框")
            symptoms_by_cat = {}
            for s in category_symptoms:
                symptoms_by_cat.setdefault(s.category, []).append(s)

            selected_symptom_names = []
            for cat_name, syms in symptoms_by_cat.items():
                option_labels = [f"{s.name}（{s.description}）" for s in syms]
                label_to_name = {f"{s.name}（{s.description}）": s.name for s in syms}
                picked = st.multiselect(
                    f"{cat_name}症状",
                    options=option_labels,
                    key=f"pc_symptom_sel_{cat_name}"
                )
                selected_symptom_names.extend([label_to_name[p] for p in picked])

            if selected_symptom_names:
                st.markdown(f"**已选症状：** {'、'.join(selected_symptom_names)}")
                if st.button("➕ 将选中症状填入主要症状", key="pc_add_symptoms_btn"):
                    current = st.session_state.get('pc_auto_symptom', '')
                    to_add = [s for s in selected_symptom_names if s not in current]
                    if to_add:
                        new_text = current + ('，' if current else '') + '、'.join(to_add)
                        st.session_state['pc_auto_symptom'] = new_text
                        st.session_state['pc_pending_symptom_fill'] = new_text
                    # 清空已选症状，便于继续选择
                    for cat_name in symptoms_by_cat:
                        st.session_state.pop(f"pc_symptom_sel_{cat_name}", None)
                    st.rerun()

    usage = st.radio(
        "用途",
        ["治疗", "预防"],
        horizontal=True
    )
    
    egg_period_safe = st.checkbox(
        "产蛋期可用（禁用产蛋期禁用的药物）",
        value=True if "蛋鸡" in animal_type or "蛋鸭" in animal_type else False
    )
    
    farm_scale = st.selectbox(
        "养殖规模",
        ["小规模(1000只以下)", "中规模(1000-10000只)", "大规模(10000只以上)"],
        index=["小规模(1000只以下)", "中规模(1000-10000只)", "大规模(10000只以上)"].index(scale_default),
        help="选择养殖规模以推荐合适规格"
    )
    
    # 棚舍环境信息补充
    with st.expander("🌡️ 补充棚舍环境信息（让推荐更准确）", expanded=False):
        env_col1, env_col2 = st.columns(2)
        with env_col1:
            pc_env_temperature = st.number_input(
                "当前温度(℃)",
                value=float(selected_shed.temperature) if selected_shed and selected_shed.temperature is not None else 0.0,
                step=0.5,
                key="pc_env_temp"
            )
            pc_env_humidity = st.number_input(
                "当前湿度(%)",
                value=float(selected_shed.humidity) if selected_shed and selected_shed.humidity is not None else 0.0,
                step=1.0,
                key="pc_env_humidity"
            )
            pc_env_ammonia = st.selectbox(
                "氨气浓度",
                ["请选择", "正常", "轻微超标", "明显超标", "严重超标"],
                index=0,
                key="pc_env_ammonia"
            )
            pc_env_dead_birds = st.number_input(
                "日死淘数",
                value=int(selected_shed.dead_birds_daily) if selected_shed and selected_shed.dead_birds_daily is not None else 0,
                step=1,
                key="pc_env_dead"
            )
        with env_col2:
            pc_env_ventilation = st.selectbox(
                "通风状况",
                ["请选择", "良好", "一般", "较差", "很差"],
                index=0,
                key="pc_env_ventilation"
            )
            pc_env_density = st.selectbox(
                "饲养密度",
                ["请选择", "适宜", "略高", "过高"],
                index=0,
                key="pc_env_density"
            )
            pc_env_feed_intake = st.selectbox(
                "采食情况",
                ["请选择", "正常", "轻微下降", "明显下降", "几乎不吃"],
                index=0,
                key="pc_env_feed"
            )
            pc_env_water_intake = st.selectbox(
                "饮水情况",
                ["请选择", "正常", "轻微下降", "明显下降", "几乎不喝"],
                index=0,
                key="pc_env_water"
            )
    
    st.markdown("---")
    st.header("🚫 耐药性药物排除")
    
    all_drugs = []
    json_path = os.path.join(_root, 'data', 'products', 'huaying_products_full.json')
    if os.path.exists(json_path):
        db = DrugDatabase(json_path)
        all_drugs = db.get_all_drugs()
    
    def _display_name(d):
        for field in [d.product_name, d.name]:
            if field and str(field).strip() not in ('', '/', 'nan', 'None'):
                return str(field).strip()
        return d.name or "未命名药品"

    valid_drugs = [d for d in all_drugs if _display_name(d) not in ('/', '')]
    drug_options = sorted(
        [f"{_display_name(d)} ({d.brand_name or '—'})" for d in valid_drugs],
        key=lambda x: x.lower()
    )

    excluded_drugs = st.multiselect(
        "选择已产生耐药性的药物（推荐时将排除这些药物）",
        drug_options,
        default=[],
        help="选择您的养殖场中已经产生耐药性或经常使用导致效果下降的药物，系统将在推荐时排除这些药物"
    )

    st.markdown("---")
    st.header("📜 历史用药记录")

    if selected_shed:
        # 当前批次管理
        current_batch = selected_shed.batch_id or "default"
        batch_display = selected_shed.batch_name or current_batch
        st.markdown(f"**当前养殖批次：** `{batch_display}`")
        if selected_shed.placement_date:
            st.caption(f"入舍日期：{selected_shed.placement_date[:10]}")
        if selected_shed.current_age_days is not None:
            st.caption(f"当前日龄：{selected_shed.current_age_days} 天")
        st.caption("历史用药按批次隔离，换一批新禽时请新建批次，避免旧记录导致无药可用。")

        # 根据预计出栏日期提示是否该换禽
        if selected_shed.expected_slaughter_date:
            from datetime import date
            try:
                expected = date.fromisoformat(selected_shed.expected_slaughter_date[:10])
                if date.today() > expected:
                    st.warning(
                        f"⚠️ 当前批次预计出栏/换羽日期（{expected.isoformat()}）已过，"
                        "若已进新禽，请立即新建批次以隔离历史用药记录。"
                    )
            except Exception:
                pass

        with st.expander("🆕 新建养殖批次（换禽确认）", expanded=False):
            st.info(
                "**换禽确认**：请确认该棚舍已经进了一批新禽，并填写以下信息。"
                "新建批次后，上一批的历史用药记录将自动隔离，不再影响本次推荐。"
            )
            new_batch_name = st.text_input(
                "批次名称 *",
                placeholder="例如：2026年7月第2批",
                key=f"pc_new_batch_{selected_shed.id}"
            )
            bcol1, bcol2 = st.columns(2)
            with bcol1:
                new_placement_date = st.date_input(
                    "入舍日期 *",
                    value=None,
                    help="新一批禽的入舍日期，是判断是否换禽的核心依据",
                    key=f"pc_new_placement_{selected_shed.id}"
                )
                new_current_age = st.number_input(
                    "当前日龄 *",
                    min_value=0, max_value=999, value=0,
                    help="新一批禽当前的实际日龄",
                    key=f"pc_new_age_{selected_shed.id}"
                )
            with bcol2:
                new_expected_slaughter = st.date_input(
                    "预计出栏/换羽日期",
                    value=None,
                    help="预计这批禽出栏或换羽的日期",
                    key=f"pc_new_slaughter_{selected_shed.id}"
                )
            confirm_new_batch = st.checkbox(
                "✅ 我确认该棚舍已经更换为新一批禽，上一批历史用药可隔离",
                key=f"pc_confirm_batch_{selected_shed.id}"
            )
            if st.button("🆕 确认新建批次", key=f"pc_start_batch_{selected_shed.id}"):
                if not new_batch_name.strip():
                    st.warning("请输入批次名称")
                elif new_placement_date is None:
                    st.warning("请填写入舍日期，这是判断是否换禽的核心依据")
                elif new_current_age <= 0:
                    st.warning("请填写当前日龄")
                elif not confirm_new_batch:
                    st.warning("请勾选确认已换禽，才能新建批次")
                else:
                    start_new_batch(
                        selected_shed.id,
                        batch_name=new_batch_name.strip(),
                        placement_date=new_placement_date.isoformat(),
                        expected_slaughter_date=new_expected_slaughter.isoformat() if new_expected_slaughter else "",
                        current_age_days=int(new_current_age)
                    )
                    st.success(f"已新建批次：{new_batch_name.strip()}，历史用药已按新批次隔离")
                    st.rerun()

        medication_history = get_medication_history(selected_shed.id)

        if medication_history:
            st.info(f"当前批次已记录 {len(medication_history)} 条历史用药，系统推荐时将自动排除这些药物及同类易产生交叉耐药的药物")
            for idx, entry in enumerate(medication_history):
                cols = st.columns([3, 1])
                with cols[0]:
                    st.markdown(f"- **{entry['drug_name']}** ({entry['usage_date'][:10]})")
                with cols[1]:
                    if st.button("🗑️", key=f"del_hist_{selected_shed.id}_{idx}", help="删除该条记录"):
                        delete_medication_history(selected_shed.id, idx)
                        st.rerun()
        else:
            st.info("暂无历史用药记录。如果是刚开始使用软件，请手动添加之前使用过的药物。")

        st.markdown("**手动添加历史用药**")
        used_drug_names = {entry['drug_name'] for entry in medication_history}
        available_drugs = sorted(
            [d for d in valid_drugs if _display_name(d) not in used_drug_names],
            key=lambda x: _display_name(x).lower()
        )
        available_names = [_display_name(d) for d in available_drugs]

        selected_history = []
        if not available_names:
            st.info("🎉 药品库中所有药物均已记录在历史用药中，暂无新的可选药物。如需补充，可在下方手动输入药品名称。")
        else:
            selected_history = st.multiselect(
                "从药品库选择（已自动排除已记录药物）",
                available_names,
                key=f"history_select_{selected_shed.id}",
                help="列表已自动排除该棚舍已记录的药物，避免重复添加"
            )

            with st.expander("📋 查看可选药物详细信息", expanded=False):
                for d in available_drugs:
                    st.markdown(f"**{_display_name(d)}** ｜ 主要成分：{d.main_component or '—'}")
                    if d.indications:
                        st.caption(f"适应症/功效：{', '.join(d.indications)}")
                    if d.usage_info:
                        st.caption(f"用法用量：{d.usage_info}")
                    st.divider()

        custom_history = st.text_input(
            "或手动输入其他药物（多个用逗号分隔）",
            key=f"custom_history_{selected_shed.id}",
            placeholder="例如：多西环素，阿莫西林"
        )
        if st.button("➕ 添加历史用药", key=f"add_history_{selected_shed.id}"):
            added = []
            for drug_name in selected_history:
                if drug_name not in used_drug_names:
                    add_medication_history(selected_shed.id, drug_name, source="manual")
                    added.append(drug_name)
            if custom_history:
                for drug_name in [x.strip() for x in custom_history.replace('，', ',').split(',') if x.strip()]:
                    if drug_name not in used_drug_names:
                        add_medication_history(selected_shed.id, drug_name, source="manual")
                        added.append(drug_name)
                    else:
                        st.toast(f"{drug_name} 已存在于历史用药记录中，已跳过", icon="⚠️")
            if added:
                st.success(f"已添加历史用药：{', '.join(added)}")
                st.rerun()
            else:
                st.warning("请选择或输入至少一个药物名称")
    else:
        st.info("请先选择棚舍以查看或添加历史用药记录")

if selected_shed:
    st.subheader("📊 当前棚舍信息")
    with st.container():
        st.markdown(f"""
        <div class="profile-section">
            <strong>棚舍名称:</strong> {selected_shed.name}<br>
            <strong>类型:</strong> {selected_shed.type} | 
            <strong>品种:</strong> {selected_shed.breed} | 
            <strong>面积:</strong> {selected_shed.area} ㎡ | 
            <strong>规模:</strong> {selected_shed.scale} | 
            <strong>位置:</strong> {selected_shed.location}
        </div>
        """, unsafe_allow_html=True)

recommend_clicked = st.button("🔍 获取用药推荐", use_container_width=True)

if recommend_clicked:
    if not symptom:
        st.warning("⚠️ 请输入主要症状后再获取推荐")
    else:
        with st.spinner("正在分析病情并推荐最佳用药方案..."):
            try:
                # 保存用户在侧边栏补充的棚舍环境信息
                if selected_shed:
                    env_updates = {
                        "temperature": pc_env_temperature if pc_env_temperature != 0 else None,
                        "humidity": pc_env_humidity if pc_env_humidity != 0 else None,
                        "ammonia_level": None if pc_env_ammonia == "请选择" else pc_env_ammonia,
                        "ventilation_status": None if pc_env_ventilation == "请选择" else pc_env_ventilation,
                        "stocking_density": None if pc_env_density == "请选择" else pc_env_density,
                        "dead_birds_daily": pc_env_dead_birds if pc_env_dead_birds != 0 else None,
                        "feed_intake_status": None if pc_env_feed_intake == "请选择" else pc_env_feed_intake,
                        "water_intake_status": None if pc_env_water_intake == "请选择" else pc_env_water_intake,
                    }
                    env_updates = {k: v for k, v in env_updates.items() if v is not None}
                    if env_updates:
                        update_shed(selected_shed.id, **env_updates)
                        selected_shed = get_shed(selected_shed.id)

                recommender = get_recommender("v20260706_11")
                
                environment_factors = {}
                if selected_shed:
                    environment_factors = {
                        'facilities': selected_shed.facilities,
                        'environment_control': selected_shed.environment_control,
                        'location': selected_shed.location,
                        'area': selected_shed.area
                    }
                
                excluded_drug_names = [d.split(' (')[0] for d in excluded_drugs] if excluded_drugs else []

                medication_history = []
                if selected_shed:
                    medication_history = [entry['drug_name'] for entry in get_medication_history(selected_shed.id)]

                result = quick_recommend(
                    recommender,
                    animal_type=animal_type,
                    age_stage=age_stage,
                    symptom=symptom,
                    disease_type=disease_type,
                    usage=usage,
                    egg_period_safe=egg_period_safe,
                    farm_scale=farm_scale,
                    excluded_drugs=excluded_drug_names,
                    medication_history=medication_history
                )

                # 将本次推荐的组合方案用药记录到棚舍历史用药中，便于后续推荐参考
                if selected_shed:
                    for combo in result.get('combination_recommendations', []):
                        for drug in combo.get('drugs', []):
                            add_medication_history(
                                selected_shed.id,
                                drug['name'],
                                notes=f"推荐方案：{combo.get('scheme_name', '')}",
                                source="recommendation"
                            )

                st.session_state['recommendation_result'] = result
                st.session_state['recommendation_medication_history'] = medication_history
                st.session_state['show_results'] = True

            except Exception as e:
                st.error(f"推荐过程中出现错误: {str(e)}")

if st.session_state.get('show_results', False):
    result = st.session_state['recommendation_result']
    analysis = result['input_analysis']
    
    st.markdown("---")
    st.subheader("🔍 症状分析与病因诊断")
    
    diagnosis_col1, diagnosis_col2 = st.columns(2)
    with diagnosis_col1:
        st.markdown("### 📋 症状信息")
        st.markdown(f"""
        <div class="profile-section">
            <strong>主要症状:</strong> {analysis['symptom']}<br>
            <strong>动物种类:</strong> {analysis['animal_type']}<br>
            <strong>养殖阶段:</strong> {analysis['age_stage']}<br>
            <strong>发病类型:</strong> {analysis['disease_type']}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🎯 病因诊断")
        disease_engine = get_disease_knowledge_base()
        for disease_name in analysis['possible_diseases'][:2]:
            disease_info = disease_engine.get_disease_info(disease_name)
            if disease_info:
                with st.expander(f"🩺 {disease_name}"):
                    st.markdown(f"**病原体:** {disease_info.pathogen}")
                    st.markdown(f"**传播途径:** {disease_info.transmission}")
                    st.markdown(f"**典型症状:** {', '.join(disease_info.symptoms[:5])}")
                    st.markdown(f"**治疗原则:** {disease_info.treatment_principles}")
    
    with diagnosis_col2:
        st.markdown("### 📊 诊断置信度评估")
        safety_guardian = get_safety_guardian()
        st.markdown(f"""
        <div class="profile-section">
            <strong>可能疾病:</strong> {', '.join(analysis['possible_diseases'])}<br>
            <strong>用途:</strong> {usage}<br>
            <strong>用药安全等级:</strong> 
            <span style="color: {'#2e7d32' if len(analysis['possible_diseases']) >= 2 else '#f57c00'}; font-weight: bold;">
                {'常规用药' if len(analysis['possible_diseases']) >= 2 else '谨慎用药'}
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🔬 病因分类分析")
        etiological_factors = []
        for disease_name in analysis['possible_diseases'][:2]:
            disease_info = disease_engine.get_disease_info(disease_name)
            if disease_info:
                if '病毒' in disease_info.pathogen:
                    etiological_factors.append(f"🦠 {disease_name}: 病毒感染")
                elif '细菌' in disease_info.pathogen or '杆菌' in disease_info.pathogen or '球菌' in disease_info.pathogen:
                    etiological_factors.append(f"🔬 {disease_name}: 细菌感染")
                elif '球虫' in disease_info.pathogen or '虫' in disease_info.pathogen:
                    etiological_factors.append(f"🐛 {disease_name}: 寄生虫感染")
                elif '支原体' in disease_info.pathogen:
                    etiological_factors.append(f"🦠 {disease_name}: 支原体感染")
                else:
                    etiological_factors.append(f"🤔 {disease_name}: 其他病因")
        
        for factor in etiological_factors:
            st.markdown(f"- {factor}")

    # 病症-药物关联验证结果展示
    validation_summary = result.get('validation_summary', {})
    if validation_summary:
        st.markdown("---")
        st.subheader("✅ 病症-药物关联验证")

        total = validation_summary.get('total_candidates', 0)
        valid = validation_summary.get('valid_candidates', 0)
        invalid = validation_summary.get('invalid_candidates', 0)
        valid_rate = validation_summary.get('valid_rate', 0.0)
        disease_type_cn = validation_summary.get('disease_type_cn', '')
        dimensions = validation_summary.get('check_dimensions', [])

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("候选药物总数", total)
        with col2:
            st.metric("通过验证", valid, delta=f"{valid_rate * 100:.0f}%")
        with col3:
            st.metric("已排除", invalid)
        with col4:
            st.metric("当前病症类型", disease_type_cn)

        st.caption(f"多维度校验项：{'、'.join(dimensions)}")

        audit_log = result.get('audit_log', {})
        if audit_log:
            with st.expander("📋 查看推荐决策审计日志", expanded=False):
                st.markdown(f"**请求时间：** {audit_log.get('timestamp', '')}")
                st.markdown(f"**动物种类：** {audit_log.get('animal_type', '')} | **养殖阶段：** {audit_log.get('age_stage', '')}")
                st.markdown(f"**主诉症状：** {audit_log.get('symptom', '')}")
                st.markdown(f"**可能疾病：** {', '.join(audit_log.get('diseases', []))}")

                filtering = audit_log.get('filtering_decisions', [])
                if filtering:
                    st.markdown("**🧪 候选药物过滤决策：**")
                    for decision in filtering:
                        if decision.get('decision') == '排除':
                            st.error(
                                f"❌ 排除 **{decision.get('drug_name', '')}** "
                                f"（{decision.get('drug_type', '')}）- "
                                f"关联度：{decision.get('association_level', '')}，得分：{decision.get('score', 0)}，"
                                f"原因：{decision.get('reason', '')}"
                            )
                        else:
                            st.success(
                                f"✅ 保留 **{decision.get('drug_name', '')}** "
                                f"（{decision.get('drug_type', '')}）- "
                                f"关联度：{decision.get('association_level', '')}，得分：{decision.get('score', 0)}"
                            )

                final_recs = audit_log.get('final_recommendations', [])
                if final_recs:
                    st.markdown(f"**💊 最终推荐药物：** {', '.join(final_recs)}")

    st.markdown("---")
    st.subheader("💊 用药推荐")

    if selected_shed:
        medication_history = st.session_state.get('recommendation_medication_history', [])
        if medication_history:
            st.info(f"📜 本次推荐已参考该棚舍历史用药记录，已自动排除或规避同类/交叉耐药药物：{', '.join(medication_history)}")

    single_recs = result['single_recommendations']
    if single_recs:
        for i, rec in enumerate(single_recs, 1):
            drug = rec.get('drug', {})
            
            drug_name = drug.get('name', '未知产品')
            drug_price = drug.get('price', 0)
            drug_component = drug.get('main_component', '未知')
            drug_spec = drug.get('spec', '')
            drug_water = drug.get('water', '')
            drug_source = drug.get('source', '')
            drug_egg_safe = drug.get('egg_period_safe', True)
            drug_indications = drug.get('indications', [])
            rec_reason = rec.get('reason', '')
            rec_dosage = rec.get('dosage_recommendation', '')
            
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"### #{i} {drug_name}")
                with col2:
                    st.write(f"**价格: ¥{drug_price:.1f}**")
                
                cols = st.columns(4)
                with cols[0]:
                    st.caption(f"主要成分: {drug_component}")
                with cols[1]:
                    st.caption(f"规格: {drug_spec}")
                with cols[2]:
                    st.caption(f"兑水量: {drug_water}")
                with cols[3]:
                    st.caption(f"来源: {drug_source}")
                
                if drug_egg_safe:
                    st.success("✅ 产蛋期可用")
                else:
                    st.error("❌ 产蛋期禁用")
                
                if drug_indications:
                    st.write(f"**适应症:** {', '.join(drug_indications)}")
                else:
                    st.write("**适应症:** 详见说明书")

                reason_detail = rec.get('reason_detail', {})
                if reason_detail:
                    with st.expander("📖 查看详细推荐理由", expanded=False):
                        st.markdown(f"**✅ 适用症状：** {reason_detail.get('applicable_symptoms', '')}")
                        st.markdown(f"**🔬 成分优势：** {reason_detail.get('component_advantage', '')}")
                else:
                    st.info(f"**推荐理由:** {rec_reason}")

                st.write(f"**用法用量：** {rec_dosage}")

                st.divider()
    else:
        st.warning("未找到匹配的单药推荐，请尝试调整搜索条件")
    
    compatibility_warnings = result.get('compatibility_warnings', [])
    if compatibility_warnings:
        st.markdown("---")
        st.subheader("⚠️ 配伍禁忌警告")
        st.error("检测到以下药物组合存在配伍禁忌，请谨慎使用！")
        
        for warning in compatibility_warnings:
            with st.container():
                st.warning(f"**方案: {warning.get('scheme_name', '未知方案')}** - 等级: {warning.get('level', '未知')}")
                
                conflicts = warning.get('conflicts', [])
                for conflict in conflicts:
                    with st.expander(f"查看详情: {conflict.get('drug_a', '')} + {conflict.get('drug_b', '')}"):
                        st.markdown(f"**涉及药物:** {conflict.get('drug_a', '')} + {conflict.get('drug_b', '')}")
                        st.markdown(f"**禁忌原因:** {conflict.get('reason', '')}")
                        st.markdown(f"**处理建议:** {conflict.get('suggestion', '')}")
    
    st.markdown("---")
    st.subheader("🎯 药物组合方案推荐")
    
    combo_recs = result['combination_recommendations']
    if combo_recs:
        for i, combo in enumerate(combo_recs, 1):
            combo_name = combo.get('scheme_name', '未命名方案')
            combo_desc = combo.get('description', '')
            combo_price = combo.get('total_price', 0)
            combo_drugs = combo.get('drugs', [])
            
            compatibility_check = combo.get('compatibility_check', {})
            is_safe = compatibility_check.get('is_safe', True)
            level = compatibility_check.get('level', '安全')
            
            type_compliance = combo.get('type_compliance', {})
            is_compliant = type_compliance.get('compliant', True)
            chem_count = type_compliance.get('chem_count', 0)
            tcm_count = type_compliance.get('tcm_count', 0)
            type_labels = type_compliance.get('drug_type_labels', [])
            
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"### 🎖️ {combo_name}")
                with col2:
                    st.write(f"**合计: ¥{combo_price:.1f}**")
                with col3:
                    if is_safe:
                        st.success("✅ 配伍安全")
                    elif level == '禁忌':
                        st.error("❌ 配伍禁忌")
                    else:
                        st.warning("⚠️ 慎用")
                
                st.write(f"**方案说明:** {combo_desc}")

                rationale = combo.get('rationale', {})
                combination_basis = rationale.get('combination_basis', '') if rationale else ''
                if not combination_basis:
                    combination_basis = combo_desc
                if combination_basis:
                    st.info(f"**📖 推荐理由：** {combination_basis}")

                # 低耐药风险分析（突出展示）
                low_resistance_analysis = rationale.get('low_resistance_analysis', '') if rationale else ''
                if low_resistance_analysis:
                    st.success(f"**🛡️ 低耐药组合说明：** {low_resistance_analysis}")

                # 查看完整推荐理由（始终展示，字段缺失时自动生成兜底内容）
                with st.expander("📖 查看完整推荐理由", expanded=False):
                    # 组合依据
                    basis = rationale.get('combination_basis', '') if rationale else ''
                    if not basis:
                        basis = combo_desc
                    st.markdown(f"**🎯 组合依据：** {basis}")

                    # 各产品作用
                    st.markdown("**💊 各产品作用：**")
                    drug_roles = rationale.get('drug_roles', []) if rationale else []
                    if drug_roles:
                        for role in drug_roles:
                            st.markdown(f"- **{role.get('name', '')}**：{role.get('role', '')}")
                    else:
                        for drug in combo.get('drugs', []):
                            name = drug.get('name', '未知')
                            drug_type = drug.get('drug_type', '未知')
                            indications = drug.get('indications', [])
                            indications_text = ', '.join(indications[:3]) if isinstance(indications, list) and indications else '当前病症'
                            if drug_type == '化药':
                                st.markdown(f"- **{name}**：属于化药，直接抑制或杀灭病原微生物，针对{indications_text}等病症起到快速控制感染的作用。")
                            else:
                                st.markdown(f"- **{name}**：属于中兽药/保健类，帮助调理机体、缓解症状、增强免疫力，对{indications_text}相关表现起到辅助改善作用。")

                    # 协同效应
                    synergy = rationale.get('synergy_effect', '') if rationale else ''
                    if not synergy:
                        drugs = combo.get('drugs', [])
                        names = [d.get('name', '') for d in drugs if d.get('name')]
                        has_chem = any(d.get('drug_type') == '化药' for d in drugs)
                        has_tcm = any(d.get('drug_type') == '中兽药' for d in drugs)
                        if has_chem and has_tcm:
                            synergy = f"{'、'.join(names)}联合使用，可以发挥协同作用：化药类产品快速控制病原，中兽药类产品帮助机体恢复、减少不良反应，从而提高整体治疗效果，缩短病程。"
                        elif len(names) >= 2:
                            synergy = f"{'、'.join(names)}联合使用，可从多个角度同时改善相关症状，相互配合增强整体疗效。"
                        else:
                            synergy = "单一药物按推荐方案使用，针对当前病症进行治疗。"
                    st.markdown(f"**🤝 协同效应：** {synergy}")

                    # 其他详细字段（有则显示）
                    if rationale:
                        if rationale.get('mechanism'):
                            st.markdown(f"**⚙️ 作用机制：** {rationale.get('mechanism', '')}")

                    # 耐药预防实操指导
                    prevention_guide = rationale.get('resistance_prevention_guide', '') if rationale else ''
                    if prevention_guide:
                        st.markdown("**🛡️ 耐药预防实操指导：**")
                        st.markdown(prevention_guide)

                if not is_safe:
                    conflicts = compatibility_check.get('conflicts', [])
                    with st.expander("⚠️ 配伍问题详情", expanded=True):
                        for conflict in conflicts:
                            st.error(f"**配伍问题:** {conflict.get('drug_a', '')} + {conflict.get('drug_b', '')}")
                            st.write(f"原因: {conflict.get('reason', '')}")
                            st.write(f"建议: {conflict.get('suggestion', '')}")
                
                with st.expander("查看药物详情"):
                    for j, drug in enumerate(combo_drugs, 1):
                        cur_label = next(
                            (lb for lb in type_labels if lb.get('name') == drug.get('name')),
                            None,
                        )
                        cur_type = cur_label.get('drug_type', '未知') if cur_label else '未知'
                        
                        if cur_type == '化药':
                            type_badge = "<span class='info-badge badge-blue'>💊 化药</span>"
                        elif cur_type == '中兽药':
                            type_badge = "<span class='info-badge badge-green'>🌿 中兽药</span>"
                        else:
                            type_badge = f"<span class='info-badge badge-orange'>{cur_type}</span>"
                        
                        st.markdown(
                            f"**药物{j}: {drug.get('name', '未知')}** {type_badge}",
                            unsafe_allow_html=True,
                        )
                        st.write(f"  - 时机: {drug.get('timing', '/')}")
                        st.write(f"  - 商品名: {drug.get('brand_name', '/')}")
                        st.write(f"  - 包装规格: {drug.get('spec', '')}")
                        st.write(f"  - 适应症状: {', '.join(drug.get('indications', []))}")
                        st.write(f"  - 用法用量: {drug.get('usage_info', '')}")
                        st.write(f"  - 价格: ¥{drug.get('price', 0):.1f}")
                        
                        if drug.get('egg_period_safe', True):
                            st.success("  ✅ 产蛋期可用")
                        else:
                            st.error("  ❌ 产蛋期禁用")
                        
                        st.write("")
                
                st.divider()
    else:
        st.info("当前条件下暂无推荐的组合方案")
    
    st.markdown("---")
    st.subheader("📚 疾病知识")
    
    try:
        kb = get_disease_knowledge_base()
        diseases = analysis['possible_diseases']
        
        for disease_name in diseases[:2]:
            disease_info = kb.get_disease_info(disease_name)
            if disease_info:
                with st.expander(f"🔍 {disease_name} 详细信息"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**病原体:** {disease_info.pathogen}")
                        st.markdown(f"**传播途径:** {disease_info.transmission}")
                        st.markdown(f"**典型症状:** {', '.join(disease_info.symptoms[:5])}")
                    with col2:
                        st.markdown(f"**治疗原则:** {disease_info.treatment_principles}")
                        st.markdown(f"**常用药物:** {', '.join(disease_info.common_drugs)}")
                        st.markdown(f"**注意事项:** {disease_info.notes}")
                    
                    st.markdown("**预防措施:**")
                    for i, prevention in enumerate(disease_info.prevention, 1):
                        st.markdown(f"{i}. {prevention}")
    except Exception as e:
        st.info("疾病知识库加载中...")
    
    st.markdown("---")
    st.subheader("⚠️ 用药注意事项")
    
    st.markdown("""
    <div class="warning-box">
        <strong>重要提示:</strong>
        <ul>
            <li>请严格按照推荐剂量使用，不可随意增减</li>
            <li>产蛋期禁用药物在蛋鸡/蛋鸭养殖中严禁使用</li>
            <li>用药期间注意观察动物反应，如有异常立即停药</li>
            <li>建议轮换使用不同作用机制的药物，防止耐药性产生</li>
            <li>严重病例请及时联系兽医进行诊断治疗</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("🌡️ 环境调整建议")
    st.info("💡 根据当前病症和棚舍环境信息，制定科学的环境调整方案，助力疾病康复和预防复发")
    
    try:
        env_engine = get_environment_adjustment_engine()
        
        shed_env = None
        if selected_shed:
            shed_env = ShedEnvironment(
                temperature=selected_shed.temperature,
                humidity=selected_shed.humidity,
                temperature_range=selected_shed.temperature_range,
                ventilation_status=selected_shed.ventilation_status,
                stocking_density=selected_shed.stocking_density,
                cleanliness_level=selected_shed.cleanliness_level,
                ammonia_level=selected_shed.ammonia_level,
                lighting_hours=selected_shed.lighting_hours,
                water_quality=selected_shed.water_quality,
                dust_level=selected_shed.dust_level,
                noise_level=selected_shed.noise_level,
                feeding_mode=selected_shed.feeding_mode,
                litter_condition=selected_shed.litter_condition,
                air_quality=selected_shed.air_quality,
                dead_birds_daily=selected_shed.dead_birds_daily,
                feed_intake_status=selected_shed.feed_intake_status,
                water_intake_status=selected_shed.water_intake_status
            )
        
        diseases = analysis['possible_diseases']
        adjustments = env_engine.generate_comprehensive_adjustments(diseases, shed_env=shed_env, age_stage=age_stage)
        
        adjustment_order = ["温度控制", "湿度控制", "通风管理", "光照管理", "饲养密度", "清洁消毒", "氨气控制", "垫料管理"]
        
        if adjustments:
            adjustments.sort(key=lambda x: adjustment_order.index(x.category) if x.category in adjustment_order else 99)
            
            for adj in adjustments:
                with st.expander(f"🔧 {adj.category} - {adj.title}", expanded=True):
                    st.markdown("""
                    <style>
                    .adjustment-grid {
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        gap: 15px;
                        margin-bottom: 15px;
                    }
                    .adjustment-item {
                        background: #f8f9fa;
                        padding: 12px;
                        border-radius: 8px;
                        border-left: 4px solid #1e88e5;
                    }
                    .adjustment-step {
                        background: #e8f5e9;
                        padding: 10px 15px;
                        border-radius: 6px;
                        margin-bottom: 8px;
                        border-left: 3px solid #43a047;
                    }
                    .adjustment-effect {
                        background: #e3f2fd;
                        padding: 12px;
                        border-radius: 8px;
                        margin-bottom: 15px;
                    }
                    .adjustment-precaution {
                        background: #fff3e0;
                        padding: 8px 12px;
                        border-radius: 4px;
                        margin-bottom: 5px;
                        font-size: 0.9em;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div class="adjustment-grid">
                        <div class="adjustment-item">
                            <strong>当前状态:</strong> {adj.current_value if adj.current_value else '未知'}
                        </div>
                        <div class="adjustment-item">
                            <strong>目标状态:</strong> <span style='color: #2e7d32; font-weight: bold;'>{adj.target_value}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("**📝 调整步骤:**")
                    for i, step in enumerate(adj.adjustment_steps, 1):
                        st.markdown(f"""
                        <div class="adjustment-step">
                            <strong>{i}.</strong> {step}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if adj.precautions:
                        st.markdown("**⚠️ 注意事项:**")
                        for precaution in adj.precautions:
                            st.markdown(f"""
                            <div class="adjustment-precaution">
                                {precaution}
                            </div>
                            """, unsafe_allow_html=True)
        else:
            st.info("当前病症暂无特定环境调整建议，请参考常规饲养管理")
    except Exception as e:
        st.info(f"环境调整建议加载中... ({str(e)})")
    
    st.markdown("---")
    st.subheader("📋 兽医诊疗关键事项（同步告知）")
    st.info("💡 根据病症同步整合的专业建议，确保用药效果和养殖安全")
    
    summary_points = get_summary_points()
    st.markdown("### 🎯 核心要点速览")
    summary_cols = st.columns(3)
    for i, point in enumerate(summary_points):
        with summary_cols[i % 3]:
            st.markdown(f"""
            <div class="key-matter-card">
                <span style="font-size: 1.2em;">{'🔸' if i % 2 == 0 else '🔹'}</span> {point}
            </div>
            """, unsafe_allow_html=True)
    
    key_matters = get_key_matters()
    for matter in key_matters:
        with st.expander(f"📌 {matter['title']}（{matter['description']}）"):
            for item in matter['items']:
                st.markdown(f"""
                <div style="margin-bottom: 8px; padding-left: 15px; border-left: 2px solid #90caf9;">
                    <div style="font-weight: bold; color: #1565c0; margin-bottom: 5px;">• {item['title']}</div>
                    <div style="color: #424242; font-size: 0.9em;">{item['content']}</div>
                </div>
                """, unsafe_allow_html=True)

st.markdown("---")
st.caption("© 2025 华英兽医宝（专家版） | 专业养殖用药助手")