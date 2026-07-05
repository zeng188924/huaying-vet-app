import streamlit as st
import pandas as pd
import sys
import os

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_root, 'src'))
sys.path.insert(0, os.path.join(_root, 'src', 'core'))
sys.path.insert(0, os.path.join(_root, 'src', 'utils'))

from drug_recommendation_system_full import create_recommender, quick_recommend, DrugDatabase
from disease_knowledge import get_disease_knowledge_base
from key_matters import get_key_matters, get_summary_points
from environment_adjustment import get_environment_adjustment_engine, ShedEnvironment
from diagnosis_engine import get_diagnosis_engine, get_safety_guardian
from src.utils.data_manager import (
    get_all_farmer_profiles, get_sheds_by_farmer,
    get_medication_history, add_medication_history, delete_medication_history
)

st.set_page_config(
    page_title="智能用药推荐",
    page_icon="💊",
    layout="wide"
)

@st.cache_resource
def get_recommender():
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
    
    if selected_shed:
        breed_mapping = {
            "白羽肉鸡": "肉鸡", "黄羽肉鸡": "肉鸡", "蛋鸡": "蛋鸡",
            "种鸡": "种鸡", "樱桃谷鸭": "肉鸭", "麻鸭": "蛋鸭",
            "鹅": "鹅", "火鸡": "火鸡", "鸽子": "鸽子", "鹌鹑": "鹌鹑"
        }
        animal_type_default = breed_mapping.get(selected_shed.breed, selected_shed.breed)
        scale_default = selected_shed.scale
    else:
        animal_type_default = "肉鸡"
        scale_default = "中规模(1000-10000只)"
    
    animal_type = st.selectbox(
        "动物种类",
        ["肉鸡", "蛋鸡", "种鸡", "肉鸭", "蛋鸭", "鹅", "火鸡", "鸽子", "鹌鹑"],
        index=["肉鸡", "蛋鸡", "种鸡", "肉鸭", "蛋鸭", "鹅", "火鸡", "鸽子", "鹌鹑"].index(animal_type_default),
        help="选择养殖的动物种类"
    )
    
    age_stage = st.selectbox(
        "日龄/养殖阶段",
        ["育雏期(0-14日龄)", "育成期(15-35日龄)", "育肥期(36日龄-出栏)", 
         "产蛋前期", "产蛋高峰期", "产蛋后期"],
        help="选择当前的养殖阶段"
    )
    
    symptom = st.text_input(
        "主要症状",
        placeholder="例如：咳嗽、拉稀、球虫病、精神沉郁...",
        help="描述动物的主要症状",
        key="symptom_input"
    )
    
    disease_type = st.selectbox(
        "发病类型",
        ["呼吸道疾病", "消化道疾病", "寄生虫病", "细菌性疾病", "病毒性疾病", "营养代谢病", "混合感染"],
        help="选择疾病的类型"
    )
    
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
    
    st.markdown("---")
    st.header("🚫 耐药性药物排除")
    
    all_drugs = []
    json_path = os.path.join(_root, 'data', 'products', 'huaying_products_full.json')
    if os.path.exists(json_path):
        db = DrugDatabase(json_path)
        all_drugs = db.get_all_drugs()
    
    def _display_name(d):
        for field in [d.product_name, d.content, d.name]:
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
        medication_history = get_medication_history(selected_shed.id)

        if medication_history:
            st.info(f"已记录 {len(medication_history)} 条历史用药，系统推荐时将自动排除这些药物及同类易产生交叉耐药的药物")
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
                recommender = get_recommender()
                
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
    
    st.markdown("---")
    st.subheader("💊 用药推荐")

    if selected_shed:
        medication_history = [entry['drug_name'] for entry in get_medication_history(selected_shed.id)]
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
                        st.markdown(f"**🎯 核心功效：** {reason_detail.get('core_efficacy', '')}")
                        st.markdown(f"**✅ 适用症状：** {reason_detail.get('applicable_symptoms', '')}")
                        st.markdown(f"**🔬 成分优势：** {reason_detail.get('component_advantage', '')}")
                        st.markdown(f"**📊 临床依据：** {reason_detail.get('clinical_support', '')}")
                        st.markdown(f"**💬 用户反馈：** {reason_detail.get('user_feedback', '')}")
                        st.markdown(f"**⚠️ 安全提示：** {reason_detail.get('safety_notes', '')}")
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
                        if rationale.get('clinical_effectiveness'):
                            st.markdown(f"**📊 临床有效性：** {rationale.get('clinical_effectiveness', '')}")
                        if rationale.get('expected_outcome'):
                            st.markdown(f"**🎯 预期效果：** {rationale.get('expected_outcome', '')}")
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
                ventilation_status=selected_shed.ventilation_status,
                stocking_density=selected_shed.stocking_density,
                cleanliness_level=selected_shed.cleanliness_level,
                ammonia_level=selected_shed.ammonia_level,
                lighting_hours=selected_shed.lighting_hours
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
                    
                    st.markdown(f"""
                    <div class="adjustment-effect">
                        <strong>🎯 预期效果:</strong> {adj.expected_effect}
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