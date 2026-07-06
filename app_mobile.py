"""
华英兽医宝（专家版） - 手机版
使用Streamlit构建，针对移动端优化
"""

import streamlit as st
import pandas as pd
import sys
import os
from collections import OrderedDict

# 将 src 及子包加入模块搜索路径，确保核心模块可被导入
_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_root, 'src'))
sys.path.insert(0, os.path.join(_root, 'src', 'core'))
sys.path.insert(0, os.path.join(_root, 'src', 'admin'))
sys.path.insert(0, os.path.join(_root, 'src', 'utils'))

try:
    from product_utils import (
        group_products,
        get_base_display_name,
        normalize_group_key,
        render_variant_table_html,
        collect_variant_images,
        format_indications,
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
    format_bottom_price_usage = None
    _PU_OK = False

# 设置页面配置 - 移动端优化
st.set_page_config(
    page_title="华英兽医宝（专家版）",
    page_icon="💊",
    layout="centered",  # 居中布局更适合手机
    initial_sidebar_state="collapsed"  # 默认收起侧边栏
)

# 导入推荐系统
from drug_recommendation_system_full import (
    create_recommender, quick_recommend, DrugDatabase,
    DISEASE_TYPE_CATEGORIES, DISEASE_CATEGORY_DISPLAY,
    DISEASE_CATEGORY_DISPLAY_REVERSE, classify_drug_type
)
from disease_knowledge import get_disease_knowledge_base, get_online_searcher
from db_admin import render_admin_tab
from src.utils.data_manager import (
    create_farmer_profile, get_all_farmer_profiles,
    get_farmer_profile, update_farmer_profile, delete_farmer_profile,
    create_shed, get_sheds_by_farmer, get_shed, update_shed, delete_shed,
    get_medication_history, add_medication_history, delete_medication_history,
    start_new_batch, get_all_batches
)
from src.utils.encryption import hash_id_card
from src.utils.lab_report_parser import parse_lab_report
from environment_adjustment import get_environment_adjustment_engine, ShedEnvironment
from key_matters import get_key_matters, get_summary_points
from src.admin.content_extractor import extract_product_info
from src.core.diagnosis_engine import (
    get_diagnosis_engine, get_questionnaire, get_safety_guardian,
    SymptomBasedDiagnosisEngine, SymptomQuestionnaire, MedicationSafetyGuardian,
    get_symptoms_by_disease_category
)

# 初始化推荐器 - 使用JSON文件加载数据
# _version 参数用于强制使旧缓存失效，当推荐逻辑更新时请修改版本号
# Cloud 部署触发标记: v20260706_14
@st.cache_resource
def get_recommender(_version="v20260706_14"):
    # 优先使用JSON文件，数据更新更可靠
    json_path = os.path.join(_root, 'data', 'products', 'huaying_products_full.json')
    if os.path.exists(json_path):
        recommender = create_recommender(json_path)
    else:
        # 回退到Excel文件
        excel_path = os.path.join(_root, 'assets', 'data_sources', '合并产品信息表修改后.xlsx')
        recommender = create_recommender(excel_path)
    return recommender

# 价格格式化函数
def format_price(price_value):
    """格式化价格，只显示小数点后一位"""
    if pd.isna(price_value) or str(price_value) in ['/', '-', '', 'nan', 'None']:
        return '/'
    try:
        price_float = float(price_value)
        return f"{price_float:.1f}"
    except (ValueError, TypeError):
        return str(price_value)

def disease_name_to_type(disease_name: str) -> str:
    """将疾病名称映射到疾病类型"""
    disease_type_map = {
        "球虫病": "寄生虫病",
        "盲肠球虫": "寄生虫病",
        "小肠球虫": "寄生虫病",
        "慢性呼吸道病": "呼吸道疾病",
        "大肠杆菌病": "细菌性疾病",
        "沙门氏菌病": "细菌性疾病",
        "鸡白痢": "细菌性疾病",
        "禽霍乱": "细菌性疾病",
        "传染性鼻炎": "呼吸道疾病",
        "坏死性肠炎": "消化道疾病",
        "滑液囊支原体": "呼吸道疾病",
        "新城疫": "病毒性疾病",
        "传染性支气管炎": "病毒性疾病",
        "组织滴虫病": "寄生虫病",
        "蛔虫病": "寄生虫病",
        "绦虫病": "寄生虫病",
    }
    return disease_type_map.get(disease_name, "混合感染")

# 移动端自定义CSS
def mobile_css():
    st.markdown("""
    <style>
    /* 全局字体优化 */
    html, body, [class*="css"] {
        font-size: 16px !important;
    }
    
    /* 头部样式 */
    .mobile-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .mobile-header h1 {
        margin: 0;
        font-size: 1.5em;
        font-weight: 600;
    }
    .mobile-header p {
        margin: 8px 0 0 0;
        font-size: 0.9em;
        opacity: 0.9;
    }
    
    /* 卡片样式 - 移动端优化 */
    .mobile-card {
        background: white;
        border-radius: 12px;
        padding: 15px;
        margin: 12px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid #667eea;
    }
    .mobile-card h3 {
        color: #667eea;
        margin: 0 0 10px 0;
        font-size: 1.1em;
    }
    
    /* 组合方案卡片 */
    .combo-card {
        background: linear-gradient(135deg, #fff5eb 0%, #ffe4cc 100%);
        border-radius: 12px;
        padding: 15px;
        margin: 12px 0;
        border-left: 4px solid #ff9500;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .combo-card h3 {
        color: #e67700;
        margin: 0 0 10px 0;
        font-size: 1.1em;
    }
    
    /* 信息标签 */
    .info-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 8px 0;
    }
    .info-tag {
        background: #f0f4ff;
        color: #4c63d2;
        padding: 4px 10px;
        border-radius: 15px;
        font-size: 0.8em;
        font-weight: 500;
    }
    .info-tag-green {
        background: #e8f5e9;
        color: #2e7d32;
    }
    .info-tag-orange {
        background: #fff3e0;
        color: #ef6c00;
    }
    .info-tag-red {
        background: #ffebee;
        color: #c62828;
    }
    
    /* 价格标签 */
    .price-tag {
        font-size: 1.3em;
        color: #d32f2f;
        font-weight: bold;
    }
    
    /* 按钮样式 */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 14px 24px !important;
        border-radius: 25px !important;
        border: none !important;
        width: 100% !important;
        font-size: 1.1em !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* 输入框优化 */
    .stTextInput>div>div>input {
        font-size: 16px !important;
        padding: 12px !important;
        border-radius: 10px !important;
    }
    
    /* 选择框优化 */
    .stSelectbox>div>div {
        font-size: 16px !important;
    }
    
    /* 折叠面板优化 */
    .streamlit-expanderHeader {
        font-size: 1em !important;
        font-weight: 600 !important;
        color: #667eea !important;
    }
    
    /* 底部导航 */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 10px;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        display: flex;
        justify-content: space-around;
        z-index: 999;
    }
    .nav-item {
        text-align: center;
        color: #666;
        font-size: 0.8em;
    }
    .nav-item.active {
        color: #667eea;
    }
    
    /* 产品目录标签页优化 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.9em;
        padding: 8px 12px;
    }
    
    /* 分割线 */
    hr {
        margin: 20px 0;
        border: none;
        border-top: 1px solid #e0e0e0;
    }
    
    /* 提示框 */
    .tip-box {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 12px;
        border-radius: 8px;
        margin: 12px 0;
        font-size: 0.9em;
    }
    
    /* 排名标识 */
    .rank-badge {
        display: inline-block;
        width: 28px;
        height: 28px;
        line-height: 28px;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 50%;
        font-weight: bold;
        font-size: 0.9em;
        margin-right: 8px;
    }
    
    /* 用法用量框 */
    .usage-box {
        background: #f8f9fa;
        padding: 12px;
        border-radius: 8px;
        margin-top: 10px;
        font-size: 0.9em;
        border: 1px dashed #ccc;
    }
    
    /* 隐藏默认的Streamlit元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

mobile_css()

# 初始化session state
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'recommendation_result' not in st.session_state:
    st.session_state.recommendation_result = None

# 页面路由
page = st.session_state.page

# 底部导航
if page != 'home':
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        if st.button("🏠 首页", use_container_width=True, key="nav_home"):
            st.session_state.page = 'home'
            st.rerun()
    with col2:
        if st.button("👤 档案", use_container_width=True, key="nav_profile"):
            st.session_state.page = 'profile'
            st.rerun()
    with col3:
        if st.button("🏘️ 棚舍", use_container_width=True, key="nav_shed"):
            st.session_state.page = 'shed'
            st.rerun()
    with col4:
        if st.button("💊 推荐", use_container_width=True, key="nav_recommend"):
            st.session_state.page = 'recommend'
            st.rerun()
    with col5:
        if st.button("📋 目录", use_container_width=True, key="nav_catalog"):
            st.session_state.page = 'catalog'
            st.rerun()
    with col6:
        if st.button("🛠️ 管理", use_container_width=True, key="nav_admin"):
            st.session_state.page = 'admin'
            st.rerun()

# ==================== 首页 ====================
if page == 'home':
    st.markdown("""
    <div class="mobile-header">
        <h1>💊 华英兽医宝（专家版）</h1>
        <p>用好华英兽医宝，专家药方护禽好</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 快速入口
    st.subheader("快速入口")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔍 智能推荐", use_container_width=True):
            st.session_state.page = 'recommend'
            st.rerun()
    with col2:
        if st.button("📋 产品目录", use_container_width=True):
            st.session_state.page = 'catalog'
            st.rerun()
    with col3:
        if st.button("🛠️ 数据库管理", use_container_width=True, type="primary"):
            st.session_state.page = 'admin'
            st.rerun()
    
    col4, col5 = st.columns(2)
    with col4:
        if st.button("👤 养殖户档案", use_container_width=True):
            st.session_state.page = 'profile'
            st.rerun()
    with col5:
        if st.button("🏠 棚舍管理", use_container_width=True):
            st.session_state.page = 'shed'
            st.rerun()

    st.markdown("---")
    
    # 功能介绍
    st.subheader("功能介绍")
    
    features = [
        ("🎯", "智能推荐", "根据症状自动推荐最合适的兽药"),
        ("💰", "性价比排序", "优先推荐效果好、价格优的产品"),
        ("🔒", "产蛋期安全", "自动过滤产蛋期禁用药物"),
        ("📱", "手机优化", "专为移动端设计的操作界面"),
    ]
    
    for icon, title, desc in features:
        with st.container():
            st.markdown(f"""
            <div class="mobile-card">
                <h3>{icon} {title}</h3>
                <p style="color: #666; margin: 0;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 使用提示
    st.markdown("""
    <div class="tip-box">
        💡 <b>使用提示：</b><br>
        1. 点击"智能推荐"开始<br>
        2. 填写动物信息和症状<br>
        3. 获取个性化用药方案
    </div>
    """, unsafe_allow_html=True)

# ==================== 智能推荐页面 ====================
elif page == 'recommend':
    st.markdown("""
    <div class="mobile-header">
        <h1>🔍 智能推荐</h1>
        <p>填写病情信息获取推荐</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'diagnosis_mode' not in st.session_state:
        st.session_state.diagnosis_mode = 'direct'
    if 'questionnaire_step' not in st.session_state:
        st.session_state.questionnaire_step = 0
    if 'selected_symptoms' not in st.session_state:
        st.session_state.selected_symptoms = []
    if 'diagnosis_result' not in st.session_state:
        st.session_state.diagnosis_result = None
    if 'show_diagnosis' not in st.session_state:
        st.session_state.show_diagnosis = False

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎯 我知道症状", use_container_width=True,
                    type="primary" if st.session_state.diagnosis_mode == 'direct' else "secondary"):
            st.session_state.diagnosis_mode = 'direct'
            st.session_state.questionnaire_step = 0
            st.session_state.selected_symptoms = []
            st.session_state.diagnosis_result = None
            st.session_state.show_diagnosis = False
            st.rerun()
    with col2:
        if st.button("❓ 我不确定", use_container_width=True,
                    type="primary" if st.session_state.diagnosis_mode == 'questionnaire' else "secondary"):
            # 重新进入问诊流程：清空诊断结果但保留各步骤已选记录，便于用户调整
            st.session_state.diagnosis_mode = 'questionnaire'
            st.session_state.questionnaire_step = 0
            st.session_state.selected_symptoms = []
            st.session_state.diagnosis_result = None
            st.session_state.show_diagnosis = False
            st.session_state.auto_symptom = ''
            st.session_state.auto_disease_type = ''
            st.rerun()
    
    if st.session_state.diagnosis_mode == 'questionnaire':
        questionnaire = get_questionnaire()
        current_step = st.session_state.questionnaire_step
        total_steps = questionnaire.get_total_steps()
        step = questionnaire.get_step(current_step)
        
        if step:
            st.markdown(f"""
            <div class="tip-box">
                <strong>📋 引导式问诊 ({current_step + 1}/{total_steps})</strong><br>
                请根据提示逐步选择症状，系统将帮助您判断疾病类型
            </div>
            """, unsafe_allow_html=True)
            
            st.subheader(step.title)
            st.write(step.description)
            
            default_selected = st.session_state.get(f"questionnaire_{step.step_id}_selected", [])
            
            selected_in_step = st.multiselect(
                "请选择符合的症状（可多选）",
                [sym.name for sym in step.symptoms],
                default=default_selected,
                key=f"questionnaire_{step.step_id}"
            )
            
            col_back, col_next = st.columns(2)
            with col_back:
                if current_step > 0:
                    if st.button("← 上一步", use_container_width=True):
                        st.session_state[f"questionnaire_{step.step_id}_selected"] = selected_in_step
                        for sym in step.symptoms:
                            if sym.name in selected_in_step:
                                if sym.id not in st.session_state.selected_symptoms:
                                    st.session_state.selected_symptoms.append(sym.id)
                            else:
                                if sym.id in st.session_state.selected_symptoms:
                                    st.session_state.selected_symptoms.remove(sym.id)
                        st.session_state.questionnaire_step -= 1
                        st.rerun()
            with col_next:
                if current_step < total_steps - 1:
                    if st.button("下一步 →", use_container_width=True):
                        st.session_state[f"questionnaire_{step.step_id}_selected"] = selected_in_step
                        for sym in step.symptoms:
                            if sym.name in selected_in_step:
                                if sym.id not in st.session_state.selected_symptoms:
                                    st.session_state.selected_symptoms.append(sym.id)
                            else:
                                if sym.id in st.session_state.selected_symptoms:
                                    st.session_state.selected_symptoms.remove(sym.id)
                        st.session_state.questionnaire_step += 1
                        st.rerun()
                else:
                    if st.button("✅ 完成问诊", use_container_width=True, type="primary"):
                        st.session_state[f"questionnaire_{step.step_id}_selected"] = selected_in_step
                        for sym in step.symptoms:
                            if sym.name in selected_in_step:
                                if sym.id not in st.session_state.selected_symptoms:
                                    st.session_state.selected_symptoms.append(sym.id)
                            else:
                                if sym.id in st.session_state.selected_symptoms:
                                    st.session_state.selected_symptoms.remove(sym.id)
                        diagnosis_engine = get_diagnosis_engine()
                        st.session_state.diagnosis_result = diagnosis_engine.diagnose(st.session_state.selected_symptoms)
                        st.session_state.show_diagnosis = True
                        st.rerun()
        
        if st.session_state.get('show_diagnosis', False) and st.session_state.diagnosis_result:
            diag_result = st.session_state.diagnosis_result
            
            st.markdown("---")
            st.subheader("📊 诊断结果")
            
            confidence_color = {
                "高": "#2e7d32",
                "中": "#ef6c00",
                "低": "#c62828"
            }
            
            st.markdown(f"""
            <div class="mobile-card">
                <h3 style="color: {confidence_color.get(diag_result.confidence_level, '#666')};">
                    🎯 诊断状态: {diag_result.status}
                </h3>
                <p><b>置信度:</b> <span style="color: {confidence_color.get(diag_result.confidence_level, '#666')}; font-weight: bold;">{diag_result.confidence_level}</span></p>
                <p><b>安全等级:</b> {diag_result.safety_level}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if diag_result.primary_disease:
                st.markdown(f"""
                <div class="mobile-card">
                    <h3>🔬 最可能疾病: {diag_result.primary_disease.name}</h3>
                    <p><b>匹配症状:</b> {', '.join(diag_result.primary_disease.matched_symptoms)}</p>
                    <p><b>治疗原则:</b> {diag_result.primary_disease.treatment_principle}</p>
                    <p><b>常用药物:</b> {', '.join(diag_result.primary_disease.common_drugs)}</p>
                </div>
                """, unsafe_allow_html=True)
            
            if diag_result.secondary_diseases:
                st.markdown("### 其他可能疾病")
                for disease in diag_result.secondary_diseases:
                    st.markdown(f"""
                    <div class="mobile-card" style="border-left-color: #ff9800;">
                        <h3 style="color: #e65100;">{disease.name} (匹配度: {disease.confidence})</h3>
                        <p><b>匹配症状:</b> {', '.join(disease.matched_symptoms)}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            if diag_result.recommendations:
                st.markdown("### 📋 诊疗建议")
                st.write(diag_result.recommendations.get("advice", ""))
                
                if diag_result.recommendations.get("action_items"):
                    st.markdown("**行动清单:**")
                    for i, item in enumerate(diag_result.recommendations["action_items"], 1):
                        st.markdown(f"{i}. {item}")
                
                if diag_result.recommendations.get("follow_up"):
                    st.markdown(f"**随访要求:** {diag_result.recommendations['follow_up']}")
                
                if diag_result.recommendations.get("consult_veterinarian"):
                    st.markdown("""
                    <div style="background: #ffebee; border-left: 4px solid #c62828; padding: 12px; border-radius: 8px; margin: 12px 0;">
                        ⚠️ <strong>建议咨询兽医:</strong> 诊断置信度较低，建议联系专业兽医进行确诊
                    </div>
                    """, unsafe_allow_html=True)
            
            safety_guardian = get_safety_guardian()
            follow_up_plan = safety_guardian.generate_follow_up_plan(
                diag_result.confidence_level, diag_result
            )
            
            st.markdown("### 📅 随访计划")
            st.markdown(f"""
            <div class="mobile-card">
                <p><b>随访时间:</b> {follow_up_plan['time']}</p>
                <p><b>观察指标:</b> {', '.join(follow_up_plan['indicators'])}</p>
                <p><b>无改善时:</b> {follow_up_plan['action_if_no_improvement']}</p>
                <p><b>有改善时:</b> {follow_up_plan['action_if_improvement']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if diag_result.primary_disease:
                st.markdown("---")
                st.subheader("💊 获取用药推荐")
                
                st.session_state.diagnosis_mode = 'direct'
                st.session_state.auto_symptom = diag_result.primary_disease.name
                st.session_state.auto_disease_type = disease_name_to_type(diag_result.primary_disease.name)
                
                st.info(f"已根据诊断结果自动填入：症状='{st.session_state.auto_symptom}'")
                st.rerun()
        
        st.stop()
    
    farmers = get_all_farmer_profiles()
    
    col_farmer, col_shed = st.columns(2)
    selected_farmer = None
    selected_shed = None
    
    with col_farmer:
        if farmers:
            farmer_options = [f"{f.id} - {f.name}" for f in farmers]
            selected_farmer_str = st.selectbox(
                "👤 选择养殖户",
                farmer_options,
                format_func=lambda x: x.split(" - ")[1],
                key="mobile_farmer_select"
            )
            selected_farmer_id = selected_farmer_str.split(" - ")[0]
            selected_farmer = get_farmer_profile(selected_farmer_id)
            
            sheds = get_sheds_by_farmer(selected_farmer_id)
            with col_shed:
                if sheds:
                    shed_options = [s.name for s in sheds]
                    selected_shed_name = st.selectbox(
                        "🏠 选择棚舍",
                        shed_options,
                        key="mobile_shed_select"
                    )
                    selected_shed = next((s for s in sheds if s.name == selected_shed_name), None)
                else:
                    st.info("暂无棚舍")
        else:
            st.warning("⚠️ 请先创建养殖户档案")
    
    if selected_shed:
        st.markdown(f"""
        <div class="tip-box">
            <strong>当前棚舍:</strong> {selected_shed.name} |
            <strong>品种:</strong> {selected_shed.breed} |
            <strong>规模:</strong> {selected_shed.scale}
        </div>
        """, unsafe_allow_html=True)

        # 历史用药记录
        with st.expander("📜 历史用药记录", expanded=False):
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
                    key=f"mobile_new_batch_{selected_shed.id}"
                )
                bcol1, bcol2 = st.columns(2)
                with bcol1:
                    new_placement_date = st.date_input(
                        "入舍日期 *",
                        value=None,
                        help="新一批禽的入舍日期，是判断是否换禽的核心依据",
                        key=f"mobile_new_placement_{selected_shed.id}"
                    )
                    new_current_age = st.number_input(
                        "当前日龄 *",
                        min_value=0, max_value=999, value=0,
                        help="新一批禽当前的实际日龄",
                        key=f"mobile_new_age_{selected_shed.id}"
                    )
                with bcol2:
                    new_expected_slaughter = st.date_input(
                        "预计出栏/换羽日期",
                        value=None,
                        help="预计这批禽出栏或换羽的日期",
                        key=f"mobile_new_slaughter_{selected_shed.id}"
                    )
                confirm_new_batch = st.checkbox(
                    "✅ 我确认该棚舍已经更换为新一批禽，上一批历史用药可隔离",
                    key=f"mobile_confirm_batch_{selected_shed.id}"
                )
                if st.button("🆕 确认新建批次", key=f"mobile_start_batch_{selected_shed.id}"):
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

            medication_history = get_medication_history(selected_shed.id, drug_type="化药")
            all_medication_history = get_medication_history(selected_shed.id)

            if medication_history:
                st.info(f"当前批次已记录 {len(medication_history)} 条化药历史用药，推荐时将自动排除同类/交叉耐药药物")
                for idx, entry in enumerate(medication_history):
                    cols = st.columns([3, 1])
                    with cols[0]:
                        st.markdown(f"- **{entry['drug_name']}** ({entry['usage_date'][:10]})")
                    with cols[1]:
                        if st.button("🗑️", key=f"mobile_del_hist_{selected_shed.id}_{idx}", help="删除"):
                            delete_medication_history(selected_shed.id, idx)
                            st.rerun()
            else:
                st.info("暂无历史用药记录。如果是刚开始使用软件，请手动添加之前使用过的药物。")

            json_path = os.path.join(_root, 'data', 'products', 'huaying_products_full.json')
            all_drugs = []
            if os.path.exists(json_path):
                db = DrugDatabase(json_path)
                all_drugs = db.get_all_drugs()

            def _display_name(d):
                for field in [d.product_name, d.name]:
                    if field and str(field).strip() not in ('', '/', 'nan', 'None'):
                        return str(field).strip()
                return d.name or "未命名药品"

            def _get_drug_type_by_name(drug_name: str) -> str:
                """根据药品显示名称或产品名判断药物类型（化药/中兽药）"""
                if not drug_name:
                    return "未知"
                for d in valid_drugs:
                    if _display_name(d) == drug_name or d.name == drug_name or (d.brand_name and d.brand_name == drug_name):
                        return classify_drug_type(d)
                return "未知"

            valid_drugs = [d for d in all_drugs if _display_name(d) not in ('/', '')]

            st.markdown("**添加历史用药**")
            used_drug_names = {entry['drug_name'] for entry in all_medication_history}
            available_drugs = sorted(
                [d for d in valid_drugs if _display_name(d) not in used_drug_names and classify_drug_type(d) == "化药"],
                key=lambda x: _display_name(x).lower()
            )
            available_names = [_display_name(d) for d in available_drugs]

            mobile_selected_history = []
            if not available_names:
                st.info("🎉 药品库中所有药物均已记录，暂无新的可选药物。可在下方手动输入补充。")
            else:
                mobile_selected_history = st.multiselect(
                    "选择药品（已排除已记录药物）",
                    available_names,
                    key=f"mobile_history_select_{selected_shed.id}",
                    help="列表已自动排除该棚舍已记录的药物"
                )

                with st.expander("📋 可选药物详情", expanded=False):
                    for d in available_drugs:
                        st.markdown(f"**{_display_name(d)}** ｜ 主要成分：{d.main_component or '—'}")
                        if d.indications:
                            st.caption(f"适应症：{', '.join(d.indications)}")
                        if d.usage_info:
                            st.caption(f"用法：{d.usage_info}")
                        st.divider()

            mobile_custom_history = st.text_input(
                "或手动输入（多个用逗号分隔）",
                key=f"mobile_custom_history_{selected_shed.id}",
                placeholder="例如：多西环素，阿莫西林"
            )
            if st.button("➕ 添加", key=f"mobile_add_history_{selected_shed.id}"):
                added = []
                for drug_name in mobile_selected_history:
                    if drug_name not in used_drug_names:
                        drug_type = _get_drug_type_by_name(drug_name)
                        add_medication_history(selected_shed.id, drug_name, source="manual", drug_type=drug_type)
                        added.append(drug_name)
                if mobile_custom_history:
                    for drug_name in [x.strip() for x in mobile_custom_history.replace('，', ',').split(',') if x.strip()]:
                        if drug_name not in used_drug_names:
                            drug_type = _get_drug_type_by_name(drug_name)
                            add_medication_history(selected_shed.id, drug_name, source="manual", drug_type=drug_type)
                            added.append(drug_name)
                        else:
                            st.toast(f"{drug_name} 已存在，已跳过", icon="⚠️")
                if added:
                    st.success(f"已添加：{', '.join(added)}")
                    st.rerun()
                else:
                    st.warning("请选择或输入至少一个药物")

    # 实验室检测报告识别（放在表单外部，避免识别按钮触发表单提交）
    st.markdown("---")
    st.subheader("🔬 实验室检测报告识别")
    mobile_lab_file = st.file_uploader(
        "上传检测报告（图片/PDF）",
        type=["jpg", "jpeg", "png", "pdf"],
        key="mobile_lab_file",
        help="系统会自动识别报告中的疾病和症状关键词，回填到下方表单"
    )
    mobile_lab_text = st.text_area(
        "或粘贴检测报告文本",
        placeholder="可直接粘贴检测报告的结论或全文...",
        key="mobile_lab_text",
        height=80
    )

    if st.button("🧪 识别报告内容", key="mobile_parse_lab"):
        parsed = None
        if mobile_lab_file is not None:
            import tempfile
            ext = mobile_lab_file.name.rsplit(".", 1)[-1].lower()
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                    tmp.write(mobile_lab_file.getvalue())
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
        if parsed is None and mobile_lab_text.strip():
            parsed = parse_lab_report(mobile_lab_text)

        if parsed:
            st.success(
                f"识别结果：{parsed['disease_category']} - {parsed['disease_name']}（置信度：{parsed['confidence']}）"
            )
            if parsed.get("symptom_summary"):
                st.caption(f"识别到的症状：{parsed['symptom_summary']}")
            st.session_state['auto_symptom'] = parsed['symptom_summary'] or f"实验室检测提示：{parsed['disease_name']}"
            st.session_state['auto_disease_type'] = parsed['disease_name']
            st.rerun()
        else:
            st.info("未能从报告中识别到明确疾病，请手动填写")

    # 养殖户默认值
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
        if st.session_state.get("mobile_prev_shed_id") != selected_shed.id:
            st.session_state["animal_type_mobile"] = animal_type_default
            st.session_state["mobile_prev_shed_id"] = selected_shed.id
    else:
        animal_type_default = "肉鸡"
        scale_default = "中规模(1000-10000只)"

    # 动物种类
    animal_type = st.selectbox(
        "🐔 动物种类",
        animal_type_options,
        index=animal_type_options.index(st.session_state.get("animal_type_mobile", animal_type_default)),
        key="animal_type_mobile"
    )

    # 日龄/养殖阶段
    age_stage = st.selectbox(
        "📅 养殖阶段",
        ["育雏期(0-14日龄)", "育成期(15-35日龄)", "育肥期(36日龄-出栏)",
         "产蛋前期", "产蛋高峰期", "产蛋后期"],
        key="age_stage_mobile"
    )

    # 主要症状
    st.info(
        "💡 **症状填写提示**：请尽量详细描述，至少包括：\n\n"
        "1. **呼吸道**：咳嗽/呼噜/甩鼻/流涕/流泪/张口呼吸/伸颈喘/怪叫；\n"
        "2. **消化道**：采食量/饮水量变化、粪便颜色形状（绿便/血便/水便/过料）；\n"
        "3. **精神状态**：沉郁、扎堆、羽毛松乱、运动障碍、神经症状；\n"
        "4. **死淘情况**：日死淘数、死亡率趋势、发病日龄；\n"
        "5. **其他**：体温、产蛋变化、皮肤/冠髯异常等。"
    )
    symptom = st.text_area(
        "🤒 主要症状（请详细描述）",
        value=st.session_state.get('auto_symptom', ''),
        placeholder="请尽量详细：咳嗽/呼噜/甩鼻/流涕/流泪/张口呼吸/减料/发热/粪便异常/死淘情况等",
        help="描述动物的主要症状，越详细推荐越准确。建议不少于20字。",
        key='auto_symptom',
        height=100
    )
    if symptom:
        symptom_len = len(symptom.strip())
        if symptom_len < 10:
            st.warning("⚠️ 症状描述较简略，建议补充咳嗽频率、呼吸方式、精神状态、采食量、粪便等细节，推荐会更准确。")
        elif symptom_len < 20:
            st.info("ℹ️ 症状描述尚可，如能补充发病日龄、死淘数、粪便/产蛋细节，推荐会更精准。")

    # 发病类型：二级分类，先选大类，再选具体疾病（放在 form 外部，保证切换时实时联动）
    auto_disease_type = st.session_state.get('auto_disease_type', '')
    disease_categories = list(DISEASE_TYPE_CATEGORIES.keys())
    category_display_options = [DISEASE_CATEGORY_DISPLAY.get(cat, cat) for cat in disease_categories]

    # 根据自动识别或旧数据尝试反推大类
    auto_category = None
    if auto_disease_type:
        for cat, diseases in DISEASE_TYPE_CATEGORIES.items():
            if auto_disease_type == cat or auto_disease_type in diseases:
                auto_category = cat
                break

    category_index = disease_categories.index(auto_category) if auto_category in disease_categories else 0
    disease_category_display = st.selectbox(
        "🏥 发病大类",
        category_display_options,
        index=category_index,
        help="先选择疾病大类，具体疾病会随大类自动调整",
        key="disease_category_mobile"
    )
    disease_category = DISEASE_CATEGORY_DISPLAY_REVERSE.get(disease_category_display, disease_category_display)

    specific_diseases = DISEASE_TYPE_CATEGORIES.get(disease_category, [])
    specific_index = 0
    if auto_disease_type in specific_diseases:
        specific_index = specific_diseases.index(auto_disease_type)
    disease_type = st.selectbox(
        "🔍 具体疾病",
        specific_diseases,
        index=specific_index,
        key="disease_type_mobile"
    )

    # 根据发病大类联动展示典型症状选项，供用户快速填充主要症状
    category_symptoms = get_symptoms_by_disease_category(disease_category)
    if category_symptoms:
        st.markdown("---")
        st.caption("🩺 选择典型症状（自动追加到上方主要症状）")
        symptoms_by_cat = {}
        for s in category_symptoms:
            symptoms_by_cat.setdefault(s.category, []).append(s)

        option_labels = []
        label_to_name = {}
        for cat_name, syms in symptoms_by_cat.items():
            for s in syms:
                label = f"{cat_name} - {s.name}（{s.description}）"
                option_labels.append(label)
                label_to_name[label] = s.name
        st.session_state['mobile_symptom_label_map'] = label_to_name

        def _append_mobile_symptoms():
            selected_labels = st.session_state.get('mobile_symptom_selector', [])
            label_map = st.session_state.get('mobile_symptom_label_map', {})
            selected_names = [label_map[label] for label in selected_labels if label in label_map]
            if selected_names:
                current = st.session_state.get('auto_symptom', '')
                to_add = [s for s in selected_names if s not in current]
                if to_add:
                    new_text = current + ('，' if current else '') + '、'.join(to_add)
                    st.session_state['auto_symptom'] = new_text
                # 清空选择器，已追加内容保留在主要症状中
                st.session_state['mobile_symptom_selector'] = []

        st.multiselect(
            "勾选与本群发病相关的典型症状",
            options=option_labels,
            on_change=_append_mobile_symptoms,
            key='mobile_symptom_selector'
        )

    # 表单区域（用途、规模、环境等）
    with st.form("recommend_form"):
        # 用途
        usage = st.radio(
            "💊 用途",
            ["治疗", "预防"],
            horizontal=True
        )

        # 产蛋期是否可用
        egg_period_safe = st.checkbox(
            "🥚 产蛋期可用",
            value=True if "蛋鸡" in animal_type or "蛋鸭" in animal_type else False
        )

        # 养殖规模
        farm_scale = st.selectbox(
            "📐 养殖规模",
            ["小规模(1000只以下)", "中规模(1000-10000只)", "大规模(10000只以上)"],
            index=["小规模(1000只以下)", "中规模(1000-10000只)", "大规模(10000只以上)"].index(scale_default)
        )

        # 耐药性药物排除
        drug_options = sorted(
            [f"{_display_name(d)} ({d.brand_name or '—'})" for d in valid_drugs],
            key=lambda x: x.lower()
        )
        excluded_drugs = st.multiselect(
            "🚫 耐药性药物排除（推荐时将排除这些药物）",
            drug_options,
            default=[],
            help="选择养殖场中已经产生耐药性或效果下降的药物，系统将在推荐时排除这些药物",
            key="mobile_excluded_drugs"
        )

        # 棚舍环境信息补充
        with st.expander("🌡️ 补充棚舍环境信息（让推荐更准确）", expanded=False):
            env_col1, env_col2 = st.columns(2)
            with env_col1:
                env_temperature = st.number_input(
                    "🌡️ 当前温度(℃)",
                    value=float(selected_shed.temperature) if selected_shed and selected_shed.temperature is not None else 0.0,
                    step=0.5,
                    key="mobile_env_temp"
                )
                env_humidity = st.number_input(
                    "💧 当前湿度(%)",
                    value=float(selected_shed.humidity) if selected_shed and selected_shed.humidity is not None else 0.0,
                    step=1.0,
                    key="mobile_env_humidity"
                )
                env_ammonia = st.selectbox(
                    "💨 氨气浓度",
                    ["请选择", "正常", "轻微超标", "明显超标", "严重超标"],
                    index=0,
                    key="mobile_env_ammonia"
                )
                env_dead_birds = st.number_input(
                    "☠️ 日死淘数",
                    value=int(selected_shed.dead_birds_daily) if selected_shed and selected_shed.dead_birds_daily is not None else 0,
                    step=1,
                    key="mobile_env_dead"
                )
            with env_col2:
                env_ventilation = st.selectbox(
                    "🌬️ 通风状况",
                    ["请选择", "良好", "一般", "较差", "很差"],
                    index=0,
                    key="mobile_env_ventilation"
                )
                env_density = st.selectbox(
                    "🏠 饲养密度",
                    ["请选择", "适宜", "略高", "过高"],
                    index=0,
                    key="mobile_env_density"
                )
                env_feed_intake = st.selectbox(
                    "🌾 采食情况",
                    ["请选择", "正常", "轻微下降", "明显下降", "几乎不吃"],
                    index=0,
                    key="mobile_env_feed"
                )
                env_water_intake = st.selectbox(
                    "💧 饮水情况",
                    ["请选择", "正常", "轻微下降", "明显下降", "几乎不喝"],
                    index=0,
                    key="mobile_env_water"
                )

        # 提交按钮
        submitted = st.form_submit_button("🔍 获取用药推荐", use_container_width=True)
    
    # 处理推荐请求
    if submitted:
        auto_symptom = st.session_state.get('auto_symptom', '')
        if auto_symptom:
            symptom = auto_symptom
            st.session_state.pop('auto_symptom', None)
        
        if not symptom:
            st.warning("⚠️ 请输入主要症状")
        else:
            with st.spinner("正在分析病情..."):
                try:
                    # 保存用户补充的棚舍环境信息
                    if selected_shed:
                        env_updates = {
                            "temperature": env_temperature if env_temperature != 0 else None,
                            "humidity": env_humidity if env_humidity != 0 else None,
                            "ammonia_level": None if env_ammonia == "请选择" else env_ammonia,
                            "ventilation_status": None if env_ventilation == "请选择" else env_ventilation,
                            "stocking_density": None if env_density == "请选择" else env_density,
                            "dead_birds_daily": env_dead_birds if env_dead_birds != 0 else None,
                            "feed_intake_status": None if env_feed_intake == "请选择" else env_feed_intake,
                            "water_intake_status": None if env_water_intake == "请选择" else env_water_intake,
                        }
                        # 只更新非空值
                        env_updates = {k: v for k, v in env_updates.items() if v is not None}
                        if env_updates:
                            update_shed(selected_shed.id, **env_updates)
                            selected_shed = get_shed(selected_shed.id)

                    recommender = get_recommender("v20260706_14")

                    medication_history = []
                    if selected_shed:
                        # 耐药性分析仅基于化药历史用药数据
                        medication_history = [entry['drug_name'] for entry in get_medication_history(selected_shed.id, drug_type="化药")]

                    excluded_drug_names = [d.split(' (')[0] for d in excluded_drugs] if excluded_drugs else []

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
                                drug_type = _get_drug_type_by_name(drug['name'])
                                add_medication_history(
                                    selected_shed.id,
                                    drug['name'],
                                    notes=f"推荐方案：{combo.get('scheme_name', '')}",
                                    source="recommendation",
                                    drug_type=drug_type
                                )

                    st.session_state.recommendation_result = result
                    st.session_state.recommendation_medication_history = medication_history
                    st.session_state.show_results = True
                    st.session_state.selected_shed = selected_shed
                    st.session_state.selected_farmer = selected_farmer

                except Exception as e:
                    st.error(f"推荐出错: {str(e)}")
    
    # 显示推荐结果
    if st.session_state.get('show_results', False) and st.session_state.recommendation_result:
        result = st.session_state.recommendation_result
        selected_shed = st.session_state.get('selected_shed')
        selected_farmer = st.session_state.get('selected_farmer')
        
        st.markdown("---")
        st.subheader("📊 病情分析")
        
        analysis = result['input_analysis']
        
        profile_info = ""
        if selected_farmer:
            profile_info = f"<p><b>养殖户:</b> {selected_farmer.name}（养殖{selected_farmer.farming_years}年）</p>"
        
        shed_info = ""
        if selected_shed:
            shed_info = f"<p><b>棚舍:</b> {selected_shed.name} | <b>品种:</b> {selected_shed.breed}</p>"
        
        st.markdown(f"""
        <div class="mobile-card">
            {profile_info}
            {shed_info}
            <p><b>症状:</b> {analysis['symptom']}</p>
            <p><b>可能疾病:</b> {', '.join(analysis['possible_diseases'])}</p>
            <p><b>动物:</b> {analysis['animal_type']} | <b>阶段:</b> {analysis['age_stage']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        safety_guardian = get_safety_guardian()
        
        if st.session_state.get('diagnosis_result'):
            diag_result = st.session_state['diagnosis_result']
            confidence_level = diag_result.confidence_level
            
            if confidence_level == '低':
                st.markdown("""
                <div style="background: #ffebee; border-left: 4px solid #c62828; padding: 12px; border-radius: 8px; margin: 12px 0;">
                    ⚠️ <strong>诊断置信度低</strong>: 仅显示中兽药推荐，建议咨询兽医确诊后再用药
                </div>
                """, unsafe_allow_html=True)
                
                single_recs = [r for r in result['single_recommendations'] 
                              if r.get('drug', {}).get('category') in ['中药', '免疫增强剂', '维生素', '饲料添加剂']]
                
                combo_recs = []
                for combo in result['combination_recommendations']:
                    drugs = combo.get('drugs', [])
                    chem_count = 0
                    for d in drugs:
                        cat = d.get('category', '')
                        if cat in ['抗生素', '化药']:
                            chem_count += 1
                    if chem_count == 0:
                        combo_recs.append(combo)
            elif confidence_level == '中':
                st.markdown("""
                <div style="background: #fff3e0; border-left: 4px solid #ff9800; padding: 12px; border-radius: 8px; margin: 12px 0;">
                    ⚠️ <strong>诊断置信度中</strong>: 化药推荐已限制，建议送检确认诊断
                </div>
                """, unsafe_allow_html=True)
                
                chem_count_in_single = 0
                filtered_single = []
                for r in result['single_recommendations']:
                    cat = r.get('drug', {}).get('category', '')
                    if cat in ['抗生素', '化药']:
                        if chem_count_in_single < 1:
                            filtered_single.append(r)
                            chem_count_in_single += 1
                    else:
                        filtered_single.append(r)
                single_recs = filtered_single
                
                combo_recs = []
                for combo in result['combination_recommendations']:
                    drugs = combo.get('drugs', [])
                    chem_count = 0
                    for d in drugs:
                        cat = d.get('category', '')
                        if cat in ['抗生素', '化药']:
                            chem_count += 1
                    if chem_count <= 1:
                        combo_recs.append(combo)
            else:
                single_recs = result['single_recommendations']
                combo_recs = result['combination_recommendations']
        else:
            single_recs = result['single_recommendations']
            combo_recs = result['combination_recommendations']

        # 病症-药物关联验证摘要（移动端简化展示）
        validation_summary = result.get('validation_summary', {})
        if validation_summary:
            st.markdown("---")
            st.subheader("✅ 关联验证")
            total = validation_summary.get('total_candidates', 0)
            valid = validation_summary.get('valid_candidates', 0)
            invalid = validation_summary.get('invalid_candidates', 0)
            valid_rate = validation_summary.get('valid_rate', 0.0)
            st.markdown(
                f"<div style='background:#e8f5e9;color:#2e7d32;padding:10px;border-radius:8px;font-size:0.9em;'>"
                f"✅ 已通过验证 {valid}/{total}（{valid_rate * 100:.0f}%），"
                f"排除 {invalid} 个无明确关联药物"
                f"</div>",
                unsafe_allow_html=True,
            )
            audit_log = result.get('audit_log', {})
            if audit_log:
                with st.expander("📋 审计日志", expanded=False):
                    st.caption(f"请求时间：{audit_log.get('timestamp', '')}")
                    st.caption(f"可能疾病：{', '.join(audit_log.get('diseases', []))}")
                    filtering = audit_log.get('filtering_decisions', [])
                    for decision in filtering:
                        if decision.get('decision') == '排除':
                            st.error(
                                f"❌ 排除 {decision.get('drug_name', '')}：{decision.get('reason', '')}",
                                icon=None,
                            )

        # 单药推荐
        st.markdown("---")
        st.subheader("💊 推荐药品 (TOP 3)")

        if selected_shed:
            medication_history = st.session_state.get('recommendation_medication_history', [])
            if medication_history:
                st.info(f"📜 已参考历史用药，已排除/规避同类交叉耐药药物：{', '.join(medication_history)}")

        if single_recs:
            for i, rec in enumerate(single_recs, 1):
                drug = rec.get('drug', {})
                
                with st.container():
                    st.markdown(f"""
                    <div class="mobile-card">
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <span class="rank-badge">{i}</span>
                            <h3 style="margin: 0;">{drug.get('name', '未知产品')}</h3>
                        </div>
                        <div class="info-row">
                            <span class="info-tag info-tag-green">¥{drug.get('price', 0):.1f}</span>
                            <span class="info-tag">{drug.get('main_component', '未知')[:15]}</span>
                            {'' if drug.get('egg_period_safe', True) else '<span class="info-tag info-tag-red">产蛋期禁用</span>'}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander("📖 查看详细信息", expanded=True):
                        if drug.get('timing'):
                            st.write(f"**时机:** {drug.get('timing')}")
                        if drug.get('brand_name'):
                            st.write(f"**商品名:** {drug.get('brand_name')}")
                        if drug.get('product_name'):
                            st.write(f"**产品名:** {drug.get('product_name')}")
                        st.write(f"**成分:** {drug.get('main_component', 'N/A')}")
                        st.write(f"**包装规格:** {drug.get('spec', 'N/A')}")
                        if drug.get('indications'):
                            st.write(f"**适应症状或产品功效:** {', '.join(drug.get('indications', []))}")
                        st.write(f"**用法用量:** {rec.get('dosage_recommendation', '详见说明书')}")
                        st.write(f"**兑水量:** {drug.get('water', 'N/A')}")
                        st.write(f"**类别:** {drug.get('category', 'N/A')}")
                        st.write(f"**来源:** {drug.get('source', 'N/A')}")
                        if drug.get('usage_info'):
                            st.write(f"**用法信息:** {drug.get('usage_info')}")
                        st.write(f"**价格:** ¥{drug.get('price', 0):.1f}")
                        egg_status = "✅ 产蛋期可用" if drug.get('egg_period_safe', True) else "❌ 产蛋期禁用"
                        st.write(f"**产蛋期:** {egg_status}")
                        st.write(f"**推荐理由:** {rec.get('reason', '')}")

                        reason_detail = rec.get('reason_detail', {})
                        if reason_detail:
                            st.markdown("---")
                            st.markdown("**📖 详细推荐理由**")
                            st.markdown(f"- **适用症状：** {reason_detail.get('applicable_symptoms', '')}")
                            st.markdown(f"- **成分优势：** {reason_detail.get('component_advantage', '')}")

        # 组合方案推荐
        st.markdown("---")
        st.subheader("🎯 推荐组合方案")
        
        if combo_recs:
            for i, combo in enumerate(combo_recs[:2], 1):
                # 类型合规校验结果
                type_compliance = combo.get('type_compliance', {})
                is_compliant = type_compliance.get('compliant', True)
                chem_count = type_compliance.get('chem_count', 0)
                tcm_count = type_compliance.get('tcm_count', 0)
                type_reason = type_compliance.get('reason', '')
                type_labels = type_compliance.get('drug_type_labels', [])
                was_adjusted = type_compliance.get('adjusted', False)
                type_rule = type_compliance.get('rule', '')

                # 合规状态徽章 HTML
                if is_compliant:
                    if chem_count > 0 and tcm_count > 0:
                        compliance_badge = (
                            "<span class='info-tag' style='background:#e8f5e9;color:#2e7d32;'>"
                            f"✅ 类型合规（化药 {chem_count} + 中兽药 {tcm_count}）</span>"
                        )
                    else:
                        compliance_badge = (
                            "<span class='info-tag' style='background:#e8f5e9;color:#2e7d32;'>"
                            f"✅ 类型合规</span>"
                        )
                else:
                    compliance_badge = (
                        "<span class='info-tag' style='background:#ffebee;color:#c62828;'>"
                        f"❌ 类型不合规（全部为化药）</span>"
                    )

                with st.container():
                    st.markdown(f"""
                    <div class="combo-card">
                        <h3>🎯 方案 {i}: {combo.get('scheme_name', combo.get('name', '组合方案'))}</h3>
                        <p style="color: #666; font-size: 0.9em;">{combo.get('description', '')}</p>
                        <div class="info-row">
                            <span class="info-tag info-tag-orange">总价格: ¥{combo.get('total_price', 0):.1f}</span>
                            {compliance_badge}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 默认展示推荐理由摘要（优先使用 rationale，没有则兜底显示方案描述）
                    rationale = combo.get('rationale', {})
                    combination_basis = rationale.get('combination_basis', '') if rationale else ''
                    if not combination_basis:
                        combination_basis = combo.get('description', '')
                    if combination_basis:
                        st.info(f"**📖 推荐理由：** {combination_basis}")

                    # 低耐药风险分析（突出展示）
                    low_resistance_analysis = rationale.get('low_resistance_analysis', '') if rationale else ''
                    if low_resistance_analysis:
                        st.success(f"**🛡️ 低耐药组合说明：** {low_resistance_analysis}")

                    # 类型构成详细展示
                    if type_labels:
                        st.markdown("**🧪 组合类型构成：**")
                        # 每行最多4个徽章
                        per_row = 4
                        for row_start in range(0, len(type_labels), per_row):
                            row = type_labels[row_start:row_start + per_row]
                            cols = st.columns(len(row))
                            for idx, lbl in enumerate(row):
                                dname = lbl.get('name', '未知')
                                dtype = lbl.get('drug_type', '未知')
                                with cols[idx]:
                                    if dtype == '化药':
                                        st.markdown(
                                            f"<div style='background:#e3f2fd;color:#1565c0;padding:6px 10px;border-radius:8px;text-align:center;font-size:0.85em;'>💊 {dname}<br><b>化药</b></div>",
                                            unsafe_allow_html=True,
                                        )
                                    elif dtype == '中兽药':
                                        st.markdown(
                                            f"<div style='background:#e8f5e9;color:#2e7d32;padding:6px 10px;border-radius:8px;text-align:center;font-size:0.85em;'>🌿 {dname}<br><b>中兽药</b></div>",
                                            unsafe_allow_html=True,
                                        )
                                    else:
                                        st.markdown(
                                            f"<div style='background:#fff3e0;color:#ef6c00;padding:6px 10px;border-radius:8px;text-align:center;font-size:0.85em;'>{dname}<br><b>{dtype}</b></div>",
                                            unsafe_allow_html=True,
                                        )

                    # 合规说明
                    if not is_compliant and type_rule:
                        st.warning(f"**规则说明：** {type_rule}")
                    if type_reason:
                        st.caption(f"📌 {type_reason}")

                    # 查看完整推荐理由（始终展示，字段缺失时自动生成兜底内容）
                    with st.expander("📖 查看完整推荐理由", expanded=False):
                        # 组合依据
                        basis = rationale.get('combination_basis', '') if rationale else ''
                        if not basis:
                            basis = combo.get('description', '')
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

                    with st.expander("💊 查看组合药品详情", expanded=True):
                        for j, drug in enumerate(combo.get('drugs', []), 1):
                            # 当前药物类型徽章
                            cur_label = next(
                                (lb for lb in type_labels if lb.get('name') == drug.get('name')),
                                None,
                            )
                            cur_type = cur_label.get('drug_type', '未知') if cur_label else '未知'
                            if cur_type == '化药':
                                type_badge = " <span style='background:#e3f2fd;color:#1565c0;padding:2px 8px;border-radius:10px;font-size:0.8em;'>💊 化药</span>"
                            elif cur_type == '中兽药':
                                type_badge = " <span style='background:#e8f5e9;color:#2e7d32;padding:2px 8px;border-radius:10px;font-size:0.8em;'>🌿 中兽药</span>"
                            else:
                                type_badge = f" <span style='background:#fff3e0;color:#ef6c00;padding:2px 8px;border-radius:10px;font-size:0.8em;'>{cur_type}</span>"

                            st.markdown(f"**药品 {j}: {drug.get('name', '')}** {type_badge}", unsafe_allow_html=True)
                            if drug.get('timing'):
                                st.write(f"  - **时机:** {drug.get('timing')}")
                            if drug.get('brand_name'):
                                st.write(f"  - **商品名:** {drug.get('brand_name')}")
                            if drug.get('product_name'):
                                st.write(f"  - **产品名:** {drug.get('product_name')}")
                            # 成分显示逻辑：如果有成分才显示
                            component = drug.get('component') or drug.get('main_component')
                            if component and component.strip() and component != 'N/A':
                                st.write(f"  - **成分:** {component}")
                            st.write(f"  - **包装规格:** {drug.get('spec', 'N/A')}")
                            # 适应症状显示逻辑：确保正确显示列表或字符串
                            indications = drug.get('indications')
                            if indications:
                                if isinstance(indications, list) and len(indications) > 0:
                                    st.write(f"  - **适应症状或产品功效:** {', '.join(indications)}")
                                elif isinstance(indications, str) and indications.strip():
                                    st.write(f"  - **适应症状或产品功效:** {indications}")
                            else:
                                st.write(f"  - **适应症状或产品功效:** 暂无")
                            # 用法用量显示逻辑：确保不为空
                            usage_info = drug.get('usage_info')
                            if usage_info and str(usage_info).strip():
                                st.write(f"  - **用法用量:** {usage_info}")
                            else:
                                st.write(f"  - **用法用量:** 详见说明书")
                            # 兑水量显示逻辑：如果为空则显示'N/A'
                            water = drug.get('water', '')
                            water_display = water if water and water.strip() else 'N/A'
                            st.write(f"  - **兑水量:** {water_display}")
                            st.write(f"  - **类别:** {drug.get('category', 'N/A')}")
                            st.write(f"  - **来源:** {drug.get('source', 'N/A')}")
                            st.write(f"  - **价格:** ¥{drug.get('price', 0):.1f}")
                            egg_status = "✅ 产蛋期可用" if drug.get('egg_period_safe', True) else "❌ 产蛋期禁用"
                            st.write(f"  - **产蛋期:** {egg_status}")
                            st.write("")
        
        # 环境调整建议
        st.markdown("---")
        st.subheader("🌡️ 环境调整建议")
        st.info("💡 根据当前病症和棚舍环境信息，制定科学的环境调整方案")
        
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
            
            if adjustments:
                for adj in adjustments:
                    with st.expander(f"🔧 {adj.category} - {adj.title}", expanded=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**当前状态:** {adj.current_value}")
                        with col2:
                            st.markdown(f"**目标状态:** <span style='color: #2e7d32; font-weight: bold;'>{adj.target_value}</span>", unsafe_allow_html=True)
                        
                        st.markdown("**调整步骤:**")
                        for i, step in enumerate(adj.adjustment_steps, 1):
                            st.markdown(f"{i}. {step}")
                        
                        if adj.precautions:
                            st.markdown("**注意事项:**")
                            for precaution in adj.precautions:
                                st.markdown(f"- ⚠️ {precaution}")
            else:
                st.info("当前病症暂无特定环境调整建议，请参考常规饲养管理")
        except Exception as e:
            st.info(f"环境调整建议加载中... ({str(e)})")
        
        # 用药安全保障
        st.markdown("---")
        st.subheader("🛡️ 用药安全保障")
        st.info("💡 根据诊断置信度制定的安全用药策略")
        
        if st.session_state.get('diagnosis_result'):
            diag_result = st.session_state['diagnosis_result']
            safety_guardian = get_safety_guardian()
            strategy = safety_guardian.get_recommendation_strategy(diag_result.confidence_level)
            
            warning_html = f"<p style='color: #c62828;'><b>⚠️ 警告:</b> {strategy['warning']}</p>" if strategy['warning'] else ""
            follow_up_text = '需要' if strategy['follow_up_required'] else '不需要'
            
            st.markdown(f"""
            <div class="mobile-card">
                <h3>🎯 推荐策略: {strategy['description']}</h3>
                <p><b>允许药物类型:</b> {', '.join(strategy['drug_types'])}</p>
                <p><b>最大药物数量:</b> {strategy['max_drugs']}种</p>
                {warning_html}
                <p><b>随访要求:</b> {follow_up_text} ({strategy['follow_up_time']})</p>
            </div>
            """, unsafe_allow_html=True)
            
            follow_up_plan = safety_guardian.generate_follow_up_plan(diag_result.confidence_level, diag_result)
            st.markdown("### 📅 用药后随访计划")
            st.markdown(f"""
            <div class="mobile-card">
                <p><b>观察指标:</b> {', '.join(follow_up_plan['indicators'])}</p>
                <p><b>用药后{follow_up_plan['time']}评估疗效</b></p>
                <p><b>无改善时:</b> {follow_up_plan['action_if_no_improvement']}</p>
                <p><b>有改善时:</b> {follow_up_plan['action_if_improvement']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 兽医诊疗关键事项
        st.markdown("---")
        st.subheader("📋 兽医诊疗关键事项")
        st.info("💡 根据病症同步整合的专业建议")
        
        summary_points = get_summary_points()
        st.markdown("### 🎯 核心要点")
        for point in summary_points:
            st.markdown(f"• {point}")
        
        key_matters = get_key_matters()
        for matter in key_matters:
            with st.expander(f"📌 {matter['title']}"):
                for item in matter['items']:
                    st.markdown(f"""
                    <div style="margin-bottom: 8px; padding-left: 15px; border-left: 2px solid #90caf9;">
                        <div style="font-weight: bold; color: #1565c0; margin-bottom: 5px;">• {item['title']}</div>
                        <div style="color: #424242; font-size: 0.9em;">{item['content']}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # 清除结果按钮
        if st.button("🔄 重新推荐", use_container_width=True):
            st.session_state.show_results = False
            st.session_state.recommendation_result = None
            st.session_state.selected_shed = None
            st.session_state.selected_farmer = None
            st.session_state.diagnosis_result = None
            st.session_state.show_diagnosis = False
            st.session_state.auto_symptom = ''
            st.session_state.auto_disease_type = ''
            st.session_state.questionnaire_step = 0
            st.session_state.selected_symptoms = []
            for key in list(st.session_state.keys()):
                if key.startswith('questionnaire_'):
                    del st.session_state[key]
            st.rerun()

# ==================== 产品目录页面 ====================
elif page == 'catalog':
    import json
    import os
    
    DB_PATH = os.path.join(_root, 'data', 'products', 'huaying_products_full.json')
    
    def load_products():
        if os.path.exists(DB_PATH):
            with open(DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def save_products(products):
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
    
    if 'editing_product' not in st.session_state:
        st.session_state.editing_product = None
    
    products = load_products()
    
    st.markdown("""
    <div class="mobile-header">
        <h1>📋 产品目录</h1>
        <p>浏览所有兽药产品</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("💡 产品目录数据来源于 JSON 文件，支持增删改查")
    
    tab_list, tab_add, tab_search = st.tabs([
        "📦 产品列表", 
        "➕ 新增产品",
        "🔍 搜索"
    ])
    
    with tab_list:
        st.markdown("### 📦 产品列表")
        
        source_filter = st.selectbox("按来源筛选", ["全部", "底价目录", "明星产品", "产品信息-华英", "用户上传"])
        
        filtered_products = products
        if source_filter != "全部":
            filtered_products = [p for p in products if p.get('source', '') == source_filter]
        
        groups = group_products(filtered_products) if _PU_OK and group_products else OrderedDict(
            (p.get('id'), [p]) for p in filtered_products
        )
        st.write(f"**共 {len(groups)} 个产品（{sum(len(v) for v in groups.values())} 条规格）**")

        for gid, variants in groups.items():
            primary = variants[0]
            base_name = get_base_display_name(variants) if _PU_OK and get_base_display_name else primary.get('name', '')
            if not base_name or base_name == '/':
                continue
            is_multi = len(variants) > 1
            main_component = primary.get('main_component', '')
            category = primary.get('category', '')
            source = primary.get('source', '')
            brand_name = primary.get('brand_name', '')
            efficacy = format_indications(primary.get('indications', [])) if _PU_OK and format_indications else ""
            usage = primary.get('usage_info', '')
            egg_period_safe = primary.get('egg_period_safe', True)

            if source == "底价目录" and _PU_OK and format_bottom_price_usage:
                bottom_usage = format_bottom_price_usage(variants)
                if bottom_usage:
                    usage_display = f'<p style="color: #666; font-size: 0.85em; margin: 8px 0;"><b>用法用量:</b><br>{bottom_usage.replace(chr(10), "<br>")}</p>'
                else:
                    usage_display = f'<p style="color: #666; font-size: 0.85em; margin: 8px 0;"><b>用法用量:</b> {usage}</p>' if usage else ''
            else:
                usage_display = f'<p style="color: #666; font-size: 0.85em; margin: 8px 0;"><b>用法用量:</b> {usage}</p>' if usage else ''

            with st.container():
                badge = f"<span style='color:#1976d2; font-weight:bold;'>📦 {len(variants)} 个规格</span>" if is_multi else ""
                st.markdown(f"""
                <div class="mobile-card" style="border-left-color: #2196f3;">
                    <h3 style="color: #1565c0;">{base_name} {badge}</h3>
                    <div class="info-row">
                        <span class="info-tag">{source}</span>
                        <span class="info-tag">{category}</span>
                    </div>
                    <p style="color: #666; font-size: 0.85em; margin: 8px 0;">
                        <b>成分:</b> {main_component}<br>
                        <b>商品名:</b> {brand_name}
                    </p>
                    {f'<p style="color: #666; font-size: 0.85em; margin: 8px 0;"><b>适应症:</b> {efficacy}</p>' if efficacy else ''}
                    {usage_display}
                    {f'<p style="color: #666; font-size: 0.85em; margin: 8px 0;">{"✅ 产蛋期可用" if egg_period_safe else "❌ 产蛋期禁用"}</p>'}
                </div>
                """, unsafe_allow_html=True)

                with st.expander("📋 查看规格详情 / 包装图片"):
                    if _PU_OK and render_variant_table_html:
                        st.markdown(render_variant_table_html(variants), unsafe_allow_html=True)
                    else:
                        for v in variants:
                            st.write(f"- {v.get('spec')} | ¥{v.get('price')} | 库存 {v.get('stock', 0)}")

                    images = collect_variant_images(variants) if _PU_OK and collect_variant_images else []
                    if images:
                        st.markdown("**包装图片：**")
                        img_cols = st.columns(min(len(images), 3))
                        for idx, img in enumerate(images):
                            p = img.get("path", "")
                            if p and os.path.exists(p):
                                with img_cols[idx % 3]:
                                    st.image(p, caption=img.get("filename", ""))

                    for v in variants:
                        c1, c2 = st.columns([1, 3])
                        with c1:
                            if st.button("编辑", key=f"mobile_edit_{v.get('id', '')}", use_container_width=True):
                                st.session_state.editing_product = v
                                st.rerun()
                        with c2:
                            if st.button(f"删除 {v.get('spec', v.get('name', ''))}", key=f"mobile_delete_{v.get('id', '')}", use_container_width=True, type="secondary"):
                                products = [p for p in products if p.get('id') != v.get('id')]
                                save_products(products)
                                st.success(f"已删除产品: {v.get('name', '')}")
                                st.rerun()
    
    with tab_add:
        st.markdown("### ➕ 新增产品")
        
        is_edit = st.session_state.editing_product is not None
        product = st.session_state.editing_product if is_edit else None
        
        if is_edit:
            st.info(f"正在编辑: {product.get('name', '')}")
        
        CATEGORY_OPTIONS = [
            "化药", "中药", "抗生素", "营养类", "微生态", "免疫增强剂",
            "消毒剂类", "抗病毒类产品", "抗支原体药", "抗球虫类",
            "驱霉菌类产品", "解热镇痛", "保肝类护肾类", "特色类产品",
            "腺胃炎产品", "气囊炎类产品", "气管栓塞呼吸道药", "肠道类产品",
            "饲料添加剂", "维生素", "抗体类产品", "增蛋类产品",
            "防暑降温类产品", "营养增料促生长", "明星产品"
        ]
        
        SOURCE_OPTIONS = ["底价目录", "明星产品", "产品信息-华英", "用户上传"]
        
        DISEASE_TYPE_OPTIONS = [
            "BACTERIAL", "RESPIRATORY", "DIGESTIVE", "PARASITIC",
            "VIRAL", "MIXED", "NUTRITIONAL", "ENVIRONMENTAL",
        ]
        
        with st.form("mobile_product_form", clear_on_submit=True):
            product_id = st.text_input("产品ID *", value=product.get('id', '') if product else "", 
                                     placeholder="如：B1、S1、H1")
            name = st.text_input("产品名称 *", value=product.get('name', '') if product else "", 
                               placeholder="请输入产品名称")
            brand_name = st.text_input("商品名", value=product.get('brand_name', '') if product else "", 
                                      placeholder="请输入商品名")
            content = st.text_input("成分/含量", value=product.get('content', '') if product else "", 
                                    placeholder="请输入成分或含量")
            main_component = st.text_input("主要成分 *", value=product.get('main_component', '') if product else "", 
                                          placeholder="请输入主要成分")
            spec = st.text_input("包装规格 *", value=product.get('spec', '') if product else "", 
                                 placeholder="如：100g/袋*100袋/箱")
            water = st.text_input("兑水量", value=product.get('water', '') if product else "", 
                                  placeholder="如：400斤")
            
            group_default = product.get('product_group_id', '') if product else ''
            if not group_default and _PU_OK and normalize_group_key and product:
                group_default = normalize_group_key(product.get('name', ''), product.get('main_component', ''))
            product_group_id = st.text_input(
                "产品分组 ID（同产品不同规格保持一致）",
                value=group_default,
                placeholder="如：硫酸黏菌素预混剂",
            )
            
            price = st.number_input("价格 *", min_value=0.0, max_value=100000.0, 
                                    value=float(product.get('price', 0)) if product else 0.0,
                                    step=0.01)
            
            stock = st.number_input("库存数量", min_value=0, max_value=99999999,
                                    value=int(product.get('stock', 0)) if product else 0,
                                    step=1)
            
            cat = product.get('category', CATEGORY_OPTIONS[0]) if product else CATEGORY_OPTIONS[0]
            category = st.selectbox("类别", CATEGORY_OPTIONS,
                                   index=CATEGORY_OPTIONS.index(cat) if cat in CATEGORY_OPTIONS else 0)
            
            src = product.get('source', '用户上传') if product else '用户上传'
            source = st.selectbox("数据来源", SOURCE_OPTIONS,
                                  index=SOURCE_OPTIONS.index(src) if src in SOURCE_OPTIONS else SOURCE_OPTIONS.index("用户上传"))
            
            disease_types = st.multiselect("疾病类型", DISEASE_TYPE_OPTIONS,
                                           default=product.get('disease_types', ['MIXED']) if product else ['MIXED'])
            
            egg_period_safe = st.checkbox("产蛋期可用", 
                                          value=bool(product.get('egg_period_safe', True)) if product else True)
            
            timing = st.text_input("时机", value=product.get('timing', '') if product else "", 
                                   placeholder="如：发病期间治疗使用")
            
            usage_info = st.text_area("用法用量", value=product.get('usage_info', '') if product else "", 
                                      placeholder="请输入用法用量")
            
            efficacy_str = ""
            if product and product.get('indications'):
                if isinstance(product['indications'], list):
                    efficacy_str = '、'.join(product['indications'])
                else:
                    efficacy_str = str(product['indications'])
            efficacy_input = st.text_input("适应症（用 、分隔）", 
                                           value=efficacy_str,
                                           placeholder="如：呼吸道感染、大肠杆菌病")
            
            remark = st.text_input("备注", value=product.get('remark', '') if product else "", 
                                    placeholder="请输入备注信息")
            
            retail_price = st.text_input("建议零售价", value=product.get('retail_price', '') if product else "", 
                                          placeholder="请输入建议零售价")
            
            submitted = st.form_submit_button("保存产品" if is_edit else "创建产品", use_container_width=True)
            
            if submitted:
                if not product_id or not name or not main_component or not spec:
                    st.warning("请填写必填项（产品ID、产品名称、主要成分、包装规格）")
                else:
                    existing_ids = {p.get('id') for p in products}
                    if not is_edit and product_id in existing_ids:
                        st.warning(f"产品ID {product_id} 已存在")
                    else:
                        efficacy_list = [p.strip() for p in efficacy_input.split('、') if p.strip()] if efficacy_input else []
                        
                        new_product = {
                            "id": product_id.strip(),
                            "name": name.strip(),
                            "brand_name": brand_name.strip(),
                            "content": content.strip(),
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
                            "indications": efficacy_list,
                            "remark": remark.strip(),
                            "retail_price": retail_price.strip(),
                            "product_name": name.strip(),
                            "product_group_id": product_group_id.strip() if product_group_id.strip() else normalize_group_key(name.strip(), main_component.strip()) if _PU_OK and normalize_group_key else product_id.strip(),
                            "media": product.get("media", []) if product else [],
                            "spec_media": product.get("spec_media", []) if product else [],
                        }
                        
                        if is_edit:
                            products = [p if p.get('id') != product.get('id') else new_product for p in products]
                            st.success(f"产品更新成功: {name}")
                        else:
                            products.append(new_product)
                            st.success(f"产品创建成功: {name}")
                        
                        save_products(products)
                        st.session_state.editing_product = None
        
        if is_edit and st.button("取消编辑", use_container_width=True):
            st.session_state.editing_product = None
            st.rerun()
    
    with tab_search:
        st.markdown("### 🔍 产品搜索")
        st.caption("在产品库中搜索产品")
        
        search_text = st.text_input("输入产品名称/成分搜索", placeholder="例如：氟苯尼考...")
        
        if search_text:
            ql = search_text.lower()
            results = [
                p for p in products
                if ql in str(p.get("name", "")).lower()
                or ql in str(p.get("main_component", "")).lower()
                or ql in str(p.get("category", "")).lower()
            ]
            
            groups = group_products(results) if _PU_OK and group_products else OrderedDict(
                (p.get('id'), [p]) for p in results
            )
            st.write(f"**搜索结果：共 {len(groups)} 个产品（{sum(len(v) for v in groups.values())} 条规格）**")
            
            for gid, variants in groups.items():
                primary = variants[0]
                base_name = get_base_display_name(variants) if _PU_OK and get_base_display_name else primary.get('name', '')
                is_multi = len(variants) > 1
                category = primary.get('category', '')
                source = primary.get('source', '')
                efficacy = format_indications(primary.get('indications', [])) if _PU_OK and format_indications else ""
                
                badge = f"<span style='color:#1976d2; font-weight:bold;'>📦 {len(variants)} 个规格</span>" if is_multi else ""
                st.markdown(f"""
                <div class="mobile-card" style="border-left-color: #667eea;">
                    <h3 style="color: #667eea;">{base_name} {badge}</h3>
                    <div class="info-row">
                        <span class="info-tag">{category}</span>
                        <span class="info-tag">{source}</span>
                    </div>
                    {f'<p style="color: #666; font-size: 0.85em; margin: 8px 0;"><b>适应症:</b> {efficacy}</p>' if efficacy else ''}
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("📋 查看规格详情 / 包装图片"):
                    if _PU_OK and render_variant_table_html:
                        st.markdown(render_variant_table_html(variants), unsafe_allow_html=True)
                    else:
                        for v in variants:
                            st.write(f"- {v.get('spec')} | ¥{v.get('price')} | 库存 {v.get('stock', 0)}")
                    
                    images = collect_variant_images(variants) if _PU_OK and collect_variant_images else []
                    if images:
                        st.markdown("**包装图片：**")
                        img_cols = st.columns(min(len(images), 3))
                        for idx, img in enumerate(images):
                            p = img.get("path", "")
                            if p and os.path.exists(p):
                                with img_cols[idx % 3]:
                                    st.image(p, caption=img.get("filename", ""))
                    
                    for v in variants:
                        c1, c2 = st.columns([1, 3])
                        with c1:
                            if st.button("编辑", key=f"mobile_search_edit_{v.get('id', '')}", use_container_width=True):
                                st.session_state.editing_product = v
                                st.rerun()
                        with c2:
                            if st.button(f"删除 {v.get('spec', v.get('name', ''))}", key=f"mobile_search_delete_{v.get('id', '')}", use_container_width=True, type="secondary"):
                                products = [p for p in products if p.get('id') != v.get('id')]
                                save_products(products)
                                st.success(f"已删除产品: {v.get('name', '')}")
                                st.rerun()
            
            if not results:
                st.info("未找到匹配的产品")
        else:
            st.info("请输入搜索关键词")
    
    # 分类说明
    st.markdown("---")
    st.markdown("""
    **📌 产品分类说明：**
    - **底价目录**：基础价格产品
    - **明星产品**：重点推荐产品
    - **产品信息-华英**：完整产品信息库
    - **用户上传**：用户自行添加的产品
    
    ⚠️ 所有产品数据存储在 `huaying_products_full.json` 文件中
    """)

# ==================== 数据库管理页面 ====================
elif page == 'admin':
    st.markdown("""
    <div class="mobile-header">
        <h1>🛠️ 数据库管理</h1>
        <p>增删改查 · 多媒体上传 · 配伍校验</p>
    </div>
    """, unsafe_allow_html=True)
    render_admin_tab()

# ==================== 养殖户档案管理页面 ====================
elif page == 'profile':
    st.markdown("""
    <div class="mobile-header">
        <h1>👤 养殖户档案管理</h1>
        <p>建立您的个人档案，享受个性化服务</p>
    </div>
    """, unsafe_allow_html=True)

    if 'editing_profile' not in st.session_state:
        st.session_state.editing_profile = None

    tab1, tab2 = st.tabs(["📋 档案列表", "➕ 新建/编辑"])

    with tab1:
        profiles = get_all_farmer_profiles()
        
        if not profiles:
            st.info("暂无档案，请点击右侧标签页创建")
        else:
            st.write(f"**共 {len(profiles)} 个档案**")
            st.divider()
            
            for profile in profiles:
                with st.container():
                    st.markdown(f"""
                    <div class="mobile-card" style="border-left-color: #1e88e5;">
                        <h3 style="color: #1e88e5;">👤 {profile.name}</h3>
                        <div class="info-row">
                            <span class="info-tag">📱 {profile.phone}</span>
                            <span class="info-tag">📅 {profile.farming_years}年</span>
                            <span class="info-tag">🏆 {profile.technical_level}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if st.button(f"编辑", key=f"mobile_edit_{profile.id}", use_container_width=True):
                            st.session_state.editing_profile = profile
                            st.rerun()
                    with col2:
                        if st.button(f"删除", key=f"mobile_delete_{profile.id}", use_container_width=True, type="secondary"):
                            if delete_farmer_profile(profile.id):
                                st.success(f"已删除档案: {profile.name}")
                                st.rerun()
                            else:
                                st.error("删除失败")

    with tab2:
        st.subheader("📝 填写档案信息")

        is_edit = st.session_state.editing_profile is not None
        profile = st.session_state.editing_profile if is_edit else None

        if is_edit:
            st.info(f"正在编辑: {profile.name}")

        with st.form("profile_form", clear_on_submit=True):
            name = st.text_input("姓名 *", value=profile.name if profile else "", placeholder="请输入姓名")
            phone = st.text_input("联系电话 *", value=profile.phone if profile else "", placeholder="请输入手机号码")
            id_card = st.text_input("身份证号", value="", placeholder="请输入身份证号（加密存储）")
            
            col1, col2 = st.columns(2)
            with col1:
                farming_years = st.number_input("养殖年限（年）", min_value=0, max_value=50,
                                               value=profile.farming_years if profile else 0)
            with col2:
                technical_level = st.selectbox("技术等级",
                                              ["初级", "中级", "高级", "技术员", "执业兽医", "专家"],
                                              index=["初级", "中级", "高级", "技术员", "执业兽医", "专家"].index(profile.technical_level) if profile else 0)

            submitted = st.form_submit_button("保存档案" if is_edit else "创建档案", use_container_width=True)

            if submitted:
                if not name or not phone:
                    st.warning("请填写必填项（姓名和电话）")
                else:
                    id_card_hash = hash_id_card(id_card) if id_card else (profile.id_card_hash if profile else "")

                    if is_edit:
                        result = update_farmer_profile(
                            profile.id,
                            name=name,
                            phone=phone,
                            id_card_hash=id_card_hash,
                            farming_years=farming_years,
                            technical_level=technical_level
                        )
                        if result:
                            st.success(f"档案更新成功: {name}")
                            st.session_state.editing_profile = None
                    else:
                        result = create_farmer_profile(
                            name=name,
                            phone=phone,
                            id_card_hash=id_card_hash,
                            farming_years=farming_years,
                            technical_level=technical_level
                        )
                        if result:
                            st.success(f"档案创建成功: {name}")

        if is_edit and st.button("取消编辑", use_container_width=True):
            st.session_state.editing_profile = None
            st.rerun()

    st.caption("💡 提示：身份证号采用加密存储，系统不会保存明文信息")

# ==================== 棚舍管理页面 ====================
elif page == 'shed':
    SHED_TYPES = ["肉鸡舍", "蛋鸡舍", "种鸡舍", "肉鸭舍", "蛋鸭舍", "鹅舍", "火鸡舍", "鸽子舍", "鹌鹑舍"]
    BREED_OPTIONS = ["白羽肉鸡", "黄羽肉鸡", "蛋鸡", "种鸡", "樱桃谷鸭", "麻鸭", "鹅", "火鸡", "鸽子", "鹌鹑", "其他"]
    SCALE_OPTIONS = ["小规模(1000只以下)", "中规模(1000-10000只)", "大规模(10000只以上)"]
    FACILITY_OPTIONS = [
        "自然通风", "机械通风", "地暖", "热风炉", "水帘降温",
        "自动饮水系统", "自动喂料系统", "粪污处理系统", "消毒设备",
        "监控设备", "温湿度控制", "光照控制", "氨气监测"
    ]
    ENV_CONTROL_OPTIONS = [
        "自动温控系统", "智能通风系统", "环境监测仪",
        "自动加湿/除湿", "CO2监测", "负压控制系统"
    ]

    def _parse_date(date_str):
        from datetime import date
        if not date_str:
            return None
        try:
            return date.fromisoformat(date_str[:10])
        except Exception:
            return None

    def _fmt_date(d):
        return d.isoformat() if d else ""

    def _none_if_default(value, default="请选择"):
        return None if value == default else value

    st.markdown("""
    <div class="mobile-header">
        <h1>🏠 棚舍信息管理</h1>
        <p>管理您的养殖棚舍信息</p>
    </div>
    """, unsafe_allow_html=True)

    farmers = get_all_farmer_profiles()

    if not farmers:
        st.warning("⚠️ 请先创建养殖户档案")
        st.info("点击底部导航「👤」进入档案管理")
    else:
        selected_farmer_id = st.selectbox(
            "选择养殖户 *",
            [f"{f.id} - {f.name}" for f in farmers],
            format_func=lambda x: x.split(" - ")[1]
        )
        selected_farmer_id = selected_farmer_id.split(" - ")[0]

        if 'editing_shed' not in st.session_state:
            st.session_state.editing_shed = None

        tab1, tab2 = st.tabs(["📋 棚舍列表", "➕ 新建/编辑"])

        with tab1:
            sheds = get_sheds_by_farmer(selected_farmer_id)

            if not sheds:
                st.info("该养殖户暂无棚舍信息，请点击右侧标签页添加")
            else:
                st.write(f"**共 {len(sheds)} 个棚舍**")
                st.divider()

                for shed in sheds:
                    with st.container():
                        batch_info = f"批次: {shed.batch_name or shed.batch_id}"
                        if shed.placement_date:
                            batch_info += f" | 入舍: {shed.placement_date[:10]}"
                        env_summary = []
                        if shed.temperature is not None:
                            env_summary.append(f"温度 {shed.temperature}℃")
                        if shed.humidity is not None:
                            env_summary.append(f"湿度 {shed.humidity}%")
                        if shed.ammonia_level:
                            env_summary.append(f"氨气 {shed.ammonia_level}")
                        st.markdown(f"""
                        <div class="mobile-card" style="border-left-color: #f57c00;">
                            <h3 style="color: #f57c00;">🏠 {shed.name}</h3>
                            <div class="info-row">
                                <span class="info-tag">🐔 {shed.type}</span>
                                <span class="info-tag">🌾 {shed.breed}</span>
                                <span class="info-tag">📐 {shed.area}㎡</span>
                                <span class="info-tag">📍 {shed.location}</span>
                            </div>
                            <p style="color:#1565c0; font-size:0.85em; margin-top:8px;">{batch_info}</p>
                            <p style="color:#666; font-size:0.85em;">{' | '.join(env_summary) if env_summary else '环境信息待补充'}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        col1, col2 = st.columns([1, 3])
                        with col1:
                            if st.button(f"编辑", key=f"mobile_edit_shed_{shed.id}", use_container_width=True):
                                st.session_state.editing_shed = shed
                                st.rerun()
                        with col2:
                            if st.button(f"删除", key=f"mobile_delete_shed_{shed.id}", use_container_width=True, type="secondary"):
                                if delete_shed(shed.id):
                                    st.success(f"已删除棚舍: {shed.name}")
                                    st.rerun()
                                else:
                                    st.error("删除失败")

        with tab2:
            st.subheader("📝 填写棚舍信息")

            is_edit = st.session_state.editing_shed is not None
            shed = st.session_state.editing_shed if is_edit else None

            if is_edit:
                st.info(f"正在编辑: {shed.name}")

            with st.form("shed_form", clear_on_submit=True):
                name = st.text_input("棚舍名称 *", value=shed.name if shed else "", placeholder="如：一号鸡舍")

                col1, col2 = st.columns(2)
                with col1:
                    shed_type = st.selectbox("棚舍类型", SHED_TYPES,
                                           index=SHED_TYPES.index(shed.type) if shed else 0)
                    area = st.number_input("面积（平方米）", min_value=1, max_value=10000,
                                          value=int(shed.area) if shed else 100)
                    breed = st.selectbox("养殖品种", BREED_OPTIONS,
                                        index=BREED_OPTIONS.index(shed.breed) if shed else 0)
                with col2:
                    scale = st.selectbox("养殖规模", SCALE_OPTIONS,
                                        index=SCALE_OPTIONS.index(shed.scale) if shed else 1)
                    location = st.text_input("地理位置", value=shed.location if shed else "", placeholder="如：山东省济南市")

                facilities = st.multiselect(
                    "设施条件",
                    FACILITY_OPTIONS,
                    default=shed.facilities if shed else []
                )

                environment_control = st.multiselect(
                    "环境控制设备",
                    ENV_CONTROL_OPTIONS,
                    default=shed.environment_control if shed else []
                )

                st.markdown("#### 🐣 当前养殖批次（换禽时请新建批次）")
                batch_name = st.text_input(
                    "批次名称",
                    value=shed.batch_name if shed else "",
                    placeholder="如：2026年7月第1批"
                )
                bcol1, bcol2 = st.columns(2)
                with bcol1:
                    placement_date = st.date_input(
                        "入舍日期",
                        value=_parse_date(shed.placement_date) if shed else None,
                        help="当前这批禽的入舍日期，用于判断养殖周期和历史用药隔离"
                    )
                with bcol2:
                    expected_slaughter_date = st.date_input(
                        "预计出栏/换羽日期",
                        value=_parse_date(shed.expected_slaughter_date) if shed else None,
                        help="预计出栏或换羽日期，便于系统提示换禽"
                    )
                current_age_days = st.number_input(
                    "当前日龄",
                    min_value=0, max_value=999,
                    value=int(shed.current_age_days) if shed and shed.current_age_days is not None else 0,
                    help="当前禽群的实际日龄"
                )

                st.markdown("#### 🌡️ 棚舍环境信息（越精确推荐越准）")
                ecol1, ecol2 = st.columns(2)
                with ecol1:
                    temperature = st.number_input(
                        "当前温度(℃)",
                        value=float(shed.temperature) if shed and shed.temperature is not None else 0.0,
                        step=0.5
                    )
                    humidity = st.number_input(
                        "当前湿度(%)",
                        value=float(shed.humidity) if shed and shed.humidity is not None else 0.0,
                        step=1.0
                    )
                    temperature_range = st.selectbox(
                        "温度区间",
                        ["请选择", "偏低", "适宜", "偏高", "过高"],
                        index=["请选择", "偏低", "适宜", "偏高", "过高"].index(shed.temperature_range) if shed and shed.temperature_range in ["请选择", "偏低", "适宜", "偏高", "过高"] else 0
                    )
                    lighting_hours = st.number_input(
                        "光照时长(小时/天)",
                        min_value=0, max_value=24,
                        value=int(shed.lighting_hours) if shed and shed.lighting_hours is not None else 0
                    )
                with ecol2:
                    ventilation_status = st.selectbox(
                        "通风状况",
                        ["请选择", "良好", "一般", "较差", "很差"],
                        index=["请选择", "良好", "一般", "较差", "很差"].index(shed.ventilation_status) if shed and shed.ventilation_status in ["请选择", "良好", "一般", "较差", "很差"] else 0
                    )
                    stocking_density = st.selectbox(
                        "饲养密度",
                        ["请选择", "适宜", "略高", "过高"],
                        index=["请选择", "适宜", "略高", "过高"].index(shed.stocking_density) if shed and shed.stocking_density in ["请选择", "适宜", "略高", "过高"] else 0
                    )
                    cleanliness_level = st.selectbox(
                        "清洁程度",
                        ["请选择", "优秀", "良好", "一般", "较差", "很差"],
                        index=["请选择", "优秀", "良好", "一般", "较差", "很差"].index(shed.cleanliness_level) if shed and shed.cleanliness_level in ["请选择", "优秀", "良好", "一般", "较差", "很差"] else 0
                    )
                    ammonia_level = st.selectbox(
                        "氨气浓度",
                        ["请选择", "正常", "轻微超标", "明显超标", "严重超标"],
                        index=["请选择", "正常", "轻微超标", "明显超标", "严重超标"].index(shed.ammonia_level) if shed and shed.ammonia_level in ["请选择", "正常", "轻微超标", "明显超标", "严重超标"] else 0
                    )

                ecol3, ecol4 = st.columns(2)
                with ecol3:
                    water_quality = st.selectbox(
                        "水质",
                        ["请选择", "良好", "一般", "较差"],
                        index=["请选择", "良好", "一般", "较差"].index(shed.water_quality) if shed and shed.water_quality in ["请选择", "良好", "一般", "较差"] else 0
                    )
                    dust_level = st.selectbox(
                        "粉尘浓度",
                        ["请选择", "正常", "轻微超标", "明显超标", "严重超标"],
                        index=["请选择", "正常", "轻微超标", "明显超标", "严重超标"].index(shed.dust_level) if shed and shed.dust_level in ["请选择", "正常", "轻微超标", "明显超标", "严重超标"] else 0
                    )
                    noise_level = st.selectbox(
                        "噪音水平",
                        ["请选择", "安静", "一般", "嘈杂", "严重嘈杂"],
                        index=["请选择", "安静", "一般", "嘈杂", "严重嘈杂"].index(shed.noise_level) if shed and shed.noise_level in ["请选择", "安静", "一般", "嘈杂", "严重嘈杂"] else 0
                    )
                    feeding_mode = st.selectbox(
                        "饲喂方式",
                        ["请选择", "自由采食", "定时限量", "人工投喂", "其他"],
                        index=["请选择", "自由采食", "定时限量", "人工投喂", "其他"].index(shed.feeding_mode) if shed and shed.feeding_mode in ["请选择", "自由采食", "定时限量", "人工投喂", "其他"] else 0
                    )
                with ecol4:
                    litter_condition = st.selectbox(
                        "垫料状况",
                        ["请选择", "干燥松散", "轻微潮湿", "潮湿结块", "严重潮湿/霉变"],
                        index=["请选择", "干燥松散", "轻微潮湿", "潮湿结块", "严重潮湿/霉变"].index(shed.litter_condition) if shed and shed.litter_condition in ["请选择", "干燥松散", "轻微潮湿", "潮湿结块", "严重潮湿/霉变"] else 0
                    )
                    air_quality = st.selectbox(
                        "空气质量",
                        ["请选择", "良好", "一般", "较差", "很差"],
                        index=["请选择", "良好", "一般", "较差", "很差"].index(shed.air_quality) if shed and shed.air_quality in ["请选择", "良好", "一般", "较差", "很差"] else 0
                    )
                    dead_birds_daily = st.number_input(
                        "日死淘数",
                        min_value=0,
                        value=int(shed.dead_birds_daily) if shed and shed.dead_birds_daily is not None else 0
                    )

                st.markdown("#### 🍽️ 采食饮水情况")
                icol1, icol2 = st.columns(2)
                with icol1:
                    feed_intake_status = st.selectbox(
                        "采食情况",
                        ["请选择", "正常", "轻微下降", "明显下降", "几乎不吃"],
                        index=["请选择", "正常", "轻微下降", "明显下降", "几乎不吃"].index(shed.feed_intake_status) if shed and shed.feed_intake_status in ["请选择", "正常", "轻微下降", "明显下降", "几乎不吃"] else 0
                    )
                with icol2:
                    water_intake_status = st.selectbox(
                        "饮水情况",
                        ["请选择", "正常", "轻微下降", "明显下降", "几乎不喝"],
                        index=["请选择", "正常", "轻微下降", "明显下降", "几乎不喝"].index(shed.water_intake_status) if shed and shed.water_intake_status in ["请选择", "正常", "轻微下降", "明显下降", "几乎不喝"] else 0
                    )

                submitted = st.form_submit_button("保存棚舍" if is_edit else "创建棚舍", use_container_width=True)

                if submitted:
                    if not name or not area:
                        st.warning("请填写必填项（棚舍名称和面积）")
                    else:
                        env_payload = {
                            "batch_name": batch_name,
                            "placement_date": _fmt_date(placement_date),
                            "expected_slaughter_date": _fmt_date(expected_slaughter_date),
                            "current_age_days": current_age_days if current_age_days > 0 else None,
                            "temperature": temperature if temperature != 0 else None,
                            "humidity": humidity if humidity != 0 else None,
                            "temperature_range": _none_if_default(temperature_range),
                            "ventilation_status": _none_if_default(ventilation_status),
                            "stocking_density": _none_if_default(stocking_density),
                            "cleanliness_level": _none_if_default(cleanliness_level),
                            "ammonia_level": _none_if_default(ammonia_level),
                            "lighting_hours": lighting_hours if lighting_hours > 0 else None,
                            "water_quality": _none_if_default(water_quality),
                            "dust_level": _none_if_default(dust_level),
                            "noise_level": _none_if_default(noise_level),
                            "feeding_mode": _none_if_default(feeding_mode),
                            "litter_condition": _none_if_default(litter_condition),
                            "air_quality": _none_if_default(air_quality),
                            "dead_birds_daily": dead_birds_daily if dead_birds_daily > 0 else None,
                            "feed_intake_status": _none_if_default(feed_intake_status),
                            "water_intake_status": _none_if_default(water_intake_status),
                        }
                        if is_edit:
                            result = update_shed(
                                shed.id,
                                name=name,
                                type=shed_type,
                                area=area,
                                breed=breed,
                                scale=scale,
                                facilities=facilities,
                                location=location,
                                environment_control=environment_control,
                                **env_payload
                            )
                            if result:
                                st.success(f"棚舍更新成功: {name}")
                                st.session_state.editing_shed = None
                        else:
                            result = create_shed(
                                farmer_id=selected_farmer_id,
                                name=name,
                                shed_type=shed_type,
                                area=area,
                                breed=breed,
                                scale=scale,
                                facilities=facilities,
                                location=location,
                                environment_control=environment_control,
                                batch_name=batch_name,
                                placement_date=_fmt_date(placement_date),
                                expected_slaughter_date=_fmt_date(expected_slaughter_date),
                                current_age_days=current_age_days if current_age_days > 0 else None,
                                **{k: v for k, v in env_payload.items() if k not in ("batch_name", "placement_date", "expected_slaughter_date", "current_age_days")}
                            )
                            if result:
                                st.success(f"棚舍创建成功: {name}")

            if is_edit and st.button("取消编辑", use_container_width=True):
                st.session_state.editing_shed = None
                st.rerun()

    st.caption("💡 提示：完善的棚舍信息有助于系统提供更精准的用药推荐")

# 底部信息
st.markdown("---")
st.caption("© 2025 华英兽医宝（专家版） | 手机版")
