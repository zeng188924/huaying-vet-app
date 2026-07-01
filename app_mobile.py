"""
华英兽药智能推荐系统 - 手机版
使用Streamlit构建，针对移动端优化
"""

import streamlit as st
import pandas as pd
import sys
import os

# 设置页面配置 - 移动端优化
st.set_page_config(
    page_title="华英兽药推荐",
    page_icon="💊",
    layout="centered",  # 居中布局更适合手机
    initial_sidebar_state="collapsed"  # 默认收起侧边栏
)

# 导入推荐系统
from drug_recommendation_system_full import (
    create_recommender, quick_recommend
)
from disease_knowledge import get_disease_knowledge_base, get_online_searcher
from db_admin import render_admin_tab
from utils.data_manager import (
    create_farmer_profile, get_all_farmer_profiles,
    get_farmer_profile, update_farmer_profile, delete_farmer_profile,
    create_shed, get_sheds_by_farmer, get_shed, update_shed, delete_shed
)
from utils.encryption import hash_id_card

# 初始化推荐器 - 使用JSON文件加载数据
@st.cache_resource
def get_recommender():
    # 优先使用JSON文件，数据更新更可靠
    json_path = "huaying_products_full.json"
    if os.path.exists(json_path):
        recommender = create_recommender(json_path)
    else:
        # 回退到Excel文件
        excel_path = "合并产品信息表修改后.xlsx"
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
        <h1>💊 华英兽药智能推荐</h1>
        <p>专业的禽药推荐工具</p>
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
    
    # 表单区域
    with st.form("recommend_form"):
        # 动物种类
        animal_type = st.selectbox(
            "🐔 动物种类",
            ["肉鸡", "蛋鸡", "种鸡", "肉鸭", "蛋鸭", "鹅", "火鸡", "鸽子", "鹌鹑"]
        )
        
        # 日龄/养殖阶段
        age_stage = st.selectbox(
            "📅 养殖阶段",
            ["育雏期(0-14日龄)", "育成期(15-35日龄)", "育肥期(36日龄-出栏)", 
             "产蛋前期", "产蛋高峰期", "产蛋后期"]
        )
        
        # 病症
        symptom = st.text_input(
            "🤒 主要症状",
            placeholder="例如：咳嗽、拉稀、精神沉郁..."
        )
        
        # 发病类型
        disease_type = st.selectbox(
            "🏥 发病类型",
            ["呼吸道疾病", "消化道疾病", "寄生虫病", "细菌性疾病", "病毒性疾病", "营养代谢病", "混合感染"]
        )
        
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
        
        # 提交按钮
        submitted = st.form_submit_button("🔍 获取用药推荐", use_container_width=True)
    
    # 处理推荐请求
    if submitted:
        if not symptom:
            st.warning("⚠️ 请输入主要症状")
        else:
            with st.spinner("正在分析病情..."):
                try:
                    recommender = get_recommender()
                    result = quick_recommend(
                        recommender,
                        animal_type=animal_type,
                        age_stage=age_stage,
                        symptom=symptom,
                        disease_type=disease_type,
                        usage=usage,
                        egg_period_safe=egg_period_safe,
                        farm_scale="中规模(1000-10000只)"
                    )
                    
                    st.session_state.recommendation_result = result
                    st.session_state.show_results = True
                    
                except Exception as e:
                    st.error(f"推荐出错: {str(e)}")
    
    # 显示推荐结果
    if st.session_state.get('show_results', False) and st.session_state.recommendation_result:
        result = st.session_state.recommendation_result
        
        st.markdown("---")
        st.subheader("📊 病情分析")
        
        analysis = result['input_analysis']
        st.markdown(f"""
        <div class="mobile-card">
            <p><b>症状:</b> {analysis['symptom']}</p>
            <p><b>可能疾病:</b> {', '.join(analysis['possible_diseases'])}</p>
            <p><b>动物:</b> {analysis['animal_type']} | <b>阶段:</b> {analysis['age_stage']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 单药推荐
        st.markdown("---")
        st.subheader("💊 推荐药品 (TOP 3)")
        
        single_recs = result['single_recommendations']
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
                        st.write(f"**通用名称:** {drug.get('name', '')}")
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
                        st.write(f"** 推荐理由:** {rec.get('reason', '')}")
        
        # 组合方案推荐
        st.markdown("---")
        st.subheader("🎯 推荐组合方案")
        
        combo_recs = result['combination_recommendations']
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
                            f"✅ 类型合规（中兽药 {tcm_count} + 中兽药 {tcm_count}）</span>"
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
                    if was_adjusted:
                        st.info(
                            "ℹ️ 系统已自动调整：原方案中包含全部化药，"
                            "已自动将其中一款化药替换为同适应症的中兽药，"
                            "以满足「化药+中兽药」的搭配规则。"
                        )

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
                            # 通用名称显示逻辑：优先使用content，如果为空则使用name
                            content = drug.get('content', '')
                            generic_name = content if content and content.strip() else drug.get('name', 'N/A')
                            st.write(f"  - **通用名称:** {generic_name}")
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
        
        # 清除结果按钮
        if st.button("🔄 重新推荐", use_container_width=True):
            st.session_state.show_results = False
            st.session_state.recommendation_result = None
            st.rerun()

# ==================== 产品目录页面 ====================
elif page == 'catalog':
    import json
    import os
    
    DB_PATH = "huaying_products_full.json"
    
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
        
        st.write(f"**共 {len(filtered_products)} 个产品**")
        
        for product in filtered_products:
            name = product.get('name', '')
            if not name or name == '/':
                continue
            
            content = product.get('content', '')
            spec = product.get('spec', '')
            water = product.get('water', '')
            price = product.get('price', 0)
            category = product.get('category', '')
            source = product.get('source', '')
            brand_name = product.get('brand_name', '')
            efficacy = product.get('indications', [])
            usage = product.get('usage_info', '')
            egg_period_safe = product.get('egg_period_safe', True)
            
            if isinstance(efficacy, list):
                efficacy = ', '.join(efficacy)
            
            with st.container():
                st.markdown(f"""
                <div class="mobile-card" style="border-left-color: #2196f3;">
                    <h3 style="color: #1565c0;">{name}</h3>
                    <div class="info-row">
                        <span class="info-tag">{source}</span>
                        <span class="info-tag info-tag-green">¥{price}</span>
                    </div>
                    <p style="color: #666; font-size: 0.85em; margin: 8px 0;">
                        <b>成分:</b> {content}<br>
                        <b>规格:</b> {spec}<br>
                        <b>兑水量:</b> {water}<br>
                        <b>类别:</b> {category}<br>
                        <b>商品名:</b> {brand_name}
                    </p>
                    {f'<p style="color: #666; font-size: 0.85em; margin: 8px 0;"><b>功效:</b> {efficacy}</p>' if efficacy else ''}
                    {f'<p style="color: #666; font-size: 0.85em; margin: 8px 0;"><b>用法用量:</b> {usage}</p>' if usage else ''}
                    {f'<p style="color: #666; font-size: 0.85em; margin: 8px 0;">{"✅ 产蛋期可用" if egg_period_safe else "❌ 产蛋期禁用"}</p>'}
                </div>
                """, unsafe_allow_html=True)
                
                col_edit, col_delete = st.columns([1, 3])
                with col_edit:
                    if st.button(f"编辑", key=f"mobile_edit_{product.get('id', '')}", use_container_width=True):
                        st.session_state.editing_product = product
                        st.rerun()
                with col_delete:
                    if st.button(f"删除", key=f"mobile_delete_{product.get('id', '')}", use_container_width=True, type="secondary"):
                        products = [p for p in products if p.get('id') != product.get('id')]
                        save_products(products)
                        st.success(f"已删除产品: {name}")
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
            
            price = st.number_input("价格 *", min_value=0.0, max_value=100000.0, 
                                    value=float(product.get('price', 0)) if product else 0.0,
                                    step=0.01)
            
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
                            "category": category,
                            "source": source,
                            "disease_types": disease_types,
                            "egg_period_safe": egg_period_safe,
                            "timing": timing.strip(),
                            "usage_info": usage_info.strip(),
                            "indications": efficacy_list,
                            "remark": remark.strip(),
                            "retail_price": retail_price.strip(),
                            "product_name": name.strip()
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
            
            st.write(f"**搜索结果：共 {len(results)} 个产品**")
            
            for product in results:
                name = product.get('name', '')
                price = product.get('price', 0)
                category = product.get('category', '')
                source = product.get('source', '')
                
                st.markdown(f"""
                <div class="mobile-card" style="border-left-color: #667eea;">
                    <h3 style="color: #667eea;">{name}</h3>
                    <div class="info-row">
                        <span class="info-tag info-tag-green">¥{price}</span>
                        <span class="info-tag">{category}</span>
                        <span class="info-tag">{source}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col_edit, col_delete = st.columns([1, 3])
                with col_edit:
                    if st.button(f"编辑", key=f"mobile_search_edit_{product.get('id', '')}", use_container_width=True):
                        st.session_state.editing_product = product
                        st.rerun()
                with col_delete:
                    if st.button(f"删除", key=f"mobile_search_delete_{product.get('id', '')}", use_container_width=True, type="secondary"):
                        products = [p for p in products if p.get('id') != product.get('id')]
                        save_products(products)
                        st.success(f"已删除产品: {name}")
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
    render_admin_tab("huaying_products_full.json")

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
                        st.markdown(f"""
                        <div class="mobile-card" style="border-left-color: #f57c00;">
                            <h3 style="color: #f57c00;">🏠 {shed.name}</h3>
                            <div class="info-row">
                                <span class="info-tag">🐔 {shed.type}</span>
                                <span class="info-tag">🌾 {shed.breed}</span>
                                <span class="info-tag">📐 {shed.area}㎡</span>
                                <span class="info-tag">📍 {shed.location}</span>
                            </div>
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

                submitted = st.form_submit_button("保存棚舍" if is_edit else "创建棚舍", use_container_width=True)

                if submitted:
                    if not name or not area:
                        st.warning("请填写必填项（棚舍名称和面积）")
                    else:
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
                                environment_control=environment_control
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
                                environment_control=environment_control
                            )
                            if result:
                                st.success(f"棚舍创建成功: {name}")

            if is_edit and st.button("取消编辑", use_container_width=True):
                st.session_state.editing_shed = None
                st.rerun()

    st.caption("💡 提示：完善的棚舍信息有助于系统提供更精准的用药推荐")

# 底部信息
st.markdown("---")
st.caption("© 2025 华英兽药智能推荐系统 | 手机版")
