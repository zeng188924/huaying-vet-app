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

# 初始化推荐器
@st.cache_resource
def get_recommender():
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
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🏠 首页", use_container_width=True):
            st.session_state.page = 'home'
            st.rerun()
    with col2:
        if st.button("💊 推荐", use_container_width=True):
            st.session_state.page = 'recommend'
            st.rerun()
    with col3:
        if st.button("📋 目录", use_container_width=True):
            st.session_state.page = 'catalog'
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
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 智能推荐", use_container_width=True):
            st.session_state.page = 'recommend'
            st.rerun()
    with col2:
        if st.button("📋 产品目录", use_container_width=True):
            st.session_state.page = 'catalog'
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
                with st.container():
                    st.markdown(f"""
                    <div class="combo-card">
                        <h3>🎯 方案 {i}: {combo.get('scheme_name', combo.get('name', '组合方案'))}</h3>
                        <p style="color: #666; font-size: 0.9em;">{combo.get('description', '')}</p>
                        <div class="info-row">
                            <span class="info-tag info-tag-orange">总价格: ¥{combo.get('total_price', 0):.1f}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander("💊 查看组合药品详情", expanded=True):
                        for j, drug in enumerate(combo.get('drugs', []), 1):
                            st.markdown(f"**药品 {j}: {drug.get('name', '')}**")
                            if drug.get('timing'):
                                st.write(f"  - **时机:** {drug.get('timing')}")
                            if drug.get('brand_name'):
                                st.write(f"  - **商品名:** {drug.get('brand_name')}")
                            if drug.get('product_name'):
                                st.write(f"  - **产品名:** {drug.get('product_name')}")
                            st.write(f"  - **通用名称:** {drug.get('name', '')}")
                            st.write(f"  - **成分:** {drug.get('component', drug.get('main_component', 'N/A'))}")
                            st.write(f"  - **包装规格:** {drug.get('spec', 'N/A')}")
                            if drug.get('indications'):
                                indications = drug.get('indications')
                                if isinstance(indications, list):
                                    st.write(f"  - **适应症状或产品功效:** {', '.join(indications)}")
                                else:
                                    st.write(f"  - **适应症状或产品功效:** {indications}")
                            st.write(f"  - **用法用量:** {drug.get('usage_info', '详见说明书')}")
                            st.write(f"  - **兑水量:** {drug.get('water', 'N/A')}")
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
    st.markdown("""
    <div class="mobile-header">
        <h1>📋 产品目录</h1>
        <p>浏览所有兽药产品</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("💡 产品目录严格按Excel分类展示，三个类别相互独立")
    
    # 读取Excel文件
    try:
        excel_file = pd.ExcelFile("合并产品信息表修改后.xlsx")
        
        # 创建三个独立标签页
        tab_base, tab_star, tab_info, tab_search = st.tabs([
            "📦 底价目录", 
            "⭐ 明星产品", 
            "🏭 华英产品",
            "🔍 搜索"
        ])
        
        # 底价目录
        with tab_base:
            st.markdown("### 📦 底价目录")
            st.caption("来源：底价目录_20260112")
            
            df_base = pd.read_excel(excel_file, sheet_name='底价目录_20260112')
            df_base_filtered = df_base[df_base['序号'].apply(lambda x: str(x).isdigit() if pd.notna(x) else False)]
            
            st.write(f"**共 {len(df_base_filtered)} 个产品**")
            
            for idx, drug_row in df_base_filtered.iterrows():
                name = str(drug_row.get('品名', ''))
                content = str(drug_row.get('含量', ''))
                spec = str(drug_row.get('规格型号', ''))
                water = str(drug_row.get('兑水量', ''))
                price = format_price(drug_row.get('单价        元/袋/瓶', ''))
                spec2 = str(drug_row.get('规格型号.1', ''))
                water2 = str(drug_row.get('兑水量.1', ''))
                price2 = format_price(drug_row.get('单价        元/袋/瓶.1', ''))
                remark = str(drug_row.get('备注', ''))
                
                with st.container():
                    st.markdown(f"""
                    <div class="mobile-card" style="border-left-color: #2196f3;">
                        <h3 style="color: #1565c0;">{name}</h3>
                        <div class="info-row">
                            <span class="info-tag">底价目录</span>
                            <span class="info-tag info-tag-green">¥{price}</span>
                        </div>
                        <p style="color: #666; font-size: 0.85em; margin: 8px 0;">
                            <b>含量:</b> {content}<br>
                            <b>规格:</b> {spec}<br>
                            <b>兑水量:</b> {water}<br>
                            <b>规格2:</b> {spec2}<br>
                            <b>兑水量2:</b> {water2}<br>
                            <b>单价2:</b> ¥{price2}<br>
                            <b>备注:</b> {remark}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # 明星产品
        with tab_star:
            st.markdown("### ⭐ 明星产品")
            st.caption("来源：明星产品_20260512")
            
            df_star = pd.read_excel(excel_file, sheet_name='明星产品_20260512')
            
            st.write(f"**共 {len(df_star)} 个明星产品**")
            
            for idx, drug_row in df_star.iterrows():
                brand_name = str(drug_row.get('商品名', ''))
                product_name = str(drug_row.get('产品名称', ''))
                spec = str(drug_row.get('规格型号', ''))
                price = format_price(drug_row.get('经销商单价', ''))
                policy = str(drug_row.get('政策', ''))
                
                display_name = brand_name if brand_name != '/' and brand_name != 'nan' and brand_name else product_name
                
                with st.container():
                    st.markdown(f"""
                    <div class="mobile-card" style="border-left-color: #ff9500;">
                        <h3 style="color: #e67700;">⭐ {display_name}</h3>
                        <div class="info-row">
                            <span class="info-tag info-tag-orange">¥{price}</span>
                        </div>
                        <p style="color: #666; font-size: 0.85em; margin: 8px 0;">
                            <b>商品名:</b> {brand_name}<br>
                            <b>产品名称:</b> {product_name}<br>
                            <b>规格:</b> {spec}<br>
                            <b>政策:</b> {policy}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # 华英产品
        with tab_info:
            st.markdown("### 🏭 产品信息-华英")
            st.caption("来源：产品信息_华英")
            
            df_info = pd.read_excel(excel_file, sheet_name='产品信息_华英')
            
            st.write(f"**共 {len(df_info)} 个华英产品**")
            
            for idx, drug_row in df_info.iterrows():
                name = str(drug_row.get('产品名称', ''))
                if name == '/' or name == 'nan' or not name:
                    continue
                    
                category = str(drug_row.get('类别', ''))
                timing = str(drug_row.get('时\xa0机', ''))
                brand_name = str(drug_row.get('商品名', ''))
                spec = str(drug_row.get('包装规格', ''))
                efficacy = str(drug_row.get('适应症状或产品功效', ''))
                usage = str(drug_row.get('用法用量', ''))
                water = str(drug_row.get('兑水量', ''))
                price = format_price(drug_row.get('价\xa0格', ''))
                remark = str(drug_row.get('备注', ''))
                retail_price = format_price(drug_row.get('建议零售价', ''))
                
                with st.container():
                    st.markdown(f"""
                    <div class="mobile-card" style="border-left-color: #43a047;">
                        <h3 style="color: #2e7d32;">{name}</h3>
                        <div class="info-row">
                            <span class="info-tag info-tag-green">¥{price}</span>
                            <span class="info-tag">{category}</span>
                            <span class="info-tag">{timing}</span>
                        </div>
                        <p style="color: #666; font-size: 0.85em; margin: 8px 0;">
                            <b>商品名:</b> {brand_name}<br>
                            <b>类别:</b> {category}<br>
                            <b>时机:</b> {timing}<br>
                            <b>包装规格:</b> {spec}<br>
                            <b>适应症状或产品功效:</b> {efficacy}<br>
                            <b>用法用量:</b> {usage}<br>
                            <b>兑水量:</b> {water}<br>
                            <b>价格:</b> ¥{price}<br>
                            <b>备注:</b> {remark}<br>
                            <b>建议零售价:</b> ¥{retail_price}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # 搜索功能
        with tab_search:
            st.markdown("### 🔍 产品搜索")
            st.caption("在三个类别中搜索产品")
            
            search_text = st.text_input("输入产品名称搜索", placeholder="例如：氟苯尼考...")
            
            if search_text:
                # 在三个类别中分别搜索
                results_base = df_base[df_base['品名'].str.contains(search_text, na=False, case=False)]
                results_star = df_star[df_star['商品名'].str.contains(search_text, na=False, case=False) | 
                                       df_star['产品名称'].str.contains(search_text, na=False, case=False)]
                results_info = df_info[df_info['产品名称'].str.contains(search_text, na=False, case=False)]
                
                st.write(f"**搜索结果：**")
                
                if len(results_base) > 0:
                    st.markdown(f"**底价目录 ({len(results_base)} 个)**")
                    for _, row in results_base.iterrows():
                        name = row['品名']
                        price = format_price(row['单价        元/袋/瓶'])
                        st.write(f"- {name} - ¥{price}")
                
                if len(results_star) > 0:
                    st.markdown(f"**明星产品 ({len(results_star)} 个)**")
                    for _, row in results_star.iterrows():
                        name = row['商品名'] if row['商品名'] != '/' else row['产品名称']
                        price = format_price(row['价格'])
                        st.write(f"- {name} - ¥{price}")
                
                if len(results_info) > 0:
                    st.markdown(f"**华英产品 ({len(results_info)} 个)**")
                    for _, row in results_info.iterrows():
                        name = row['产品名称']
                        price = format_price(row['价格'])
                        st.write(f"- {name} - ¥{price}")
                
                if len(results_base) == 0 and len(results_star) == 0 and len(results_info) == 0:
                    st.info("未找到匹配的产品")
            else:
                st.info("请输入搜索关键词")
        
        # 分类说明
        st.markdown("---")
        st.markdown("""
        **📌 产品分类说明：**
        - **底价目录**：基础价格产品，共22个
        - **明星产品**：重点推荐产品，共23个
        - **产品信息-华英**：完整产品信息库，共66个
        
        ⚠️ 三个类别的产品信息相互独立，不可混淆
        """)
    
    except Exception as e:
        st.error(f"加载产品目录失败: {str(e)}")

# 底部信息
st.markdown("---")
st.caption("© 2025 华英兽药智能推荐系统 | 手机版")
