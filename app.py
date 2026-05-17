"""
兽药智能推荐系统 - Web界面
使用Streamlit构建
"""

import streamlit as st
import pandas as pd
import sys
import os

# 设置页面配置
st.set_page_config(
    page_title="华英兽药智能推荐系统",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 导入推荐系统 完整版
from drug_recommendation_system_full import (
    create_recommender, quick_recommend
)
from disease_knowledge import get_disease_knowledge_base, get_online_searcher

# 初始化推荐器
@st.cache_resource
def get_recommender():
    excel_path = "合并产品信息表修改后.xlsx"
    recommender = create_recommender(excel_path)
    # 验证数据结构
    print(f"[DEBUG] 推荐器已创建，共 {len(recommender.db.get_all_drugs())} 个产品")
    return recommender

# 清除缓存按钮（用于调试）
if st.sidebar.button("🔄 清除缓存并刷新"):
    st.cache_resource.clear()
    st.rerun()

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

# 自定义CSS样式
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
    .main-header h1 {
        margin: 0;
        font-size: 2.5em;
    }
    .main-header p {
        margin: 10px 0 0 0;
        font-size: 1.2em;
        opacity: 0.9;
    }
    .drug-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        border-left: 5px solid #1e88e5;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .drug-card h3 {
        color: #1565c0;
        margin-bottom: 10px;
    }
    .combination-card {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        border-left: 5px solid #f57c00;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .combination-card h3 {
        color: #e65100;
        margin-bottom: 10px;
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
    .badge-purple { background-color: #f3e5f5; color: #7b1fa2; }
    .price-tag {
        font-size: 1.5em;
        color: #d32f2f;
        font-weight: bold;
    }
    .recommendation-reason {
        background-color: rgba(255,255,255,0.7);
        padding: 10px;
        border-radius: 8px;
        margin-top: 10px;
        font-style: italic;
        color: #555;
    }
    .sidebar-section {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
    }
    .stButton>button {
        background: linear-gradient(90deg, #1e88e5 0%, #43a047 100%);
        color: white;
        font-weight: bold;
        padding: 12px 24px;
        border-radius: 25px;
        border: none;
        width: 100%;
    }
    .stButton>button:hover {
        opacity: 0.9;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #28a745;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

local_css()

# 页面头部
st.markdown("""
<div class="main-header">
    <h1>💊 华英兽药智能推荐系统</h1>
    <p>专业的禽药推荐工具，为您的养殖保驾护航</p>
</div>
""", unsafe_allow_html=True)

# 侧边栏 - 输入表单
with st.sidebar:
    st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
    st.header("📝 病情信息录入")
    
    # 动物种类
    animal_type = st.selectbox(
        "动物种类",
        ["肉鸡", "蛋鸡", "种鸡", "肉鸭", "蛋鸭", "鹅", "火鸡", "鸽子", "鹌鹑"],
        help="选择养殖的动物种类"
    )
    
    # 日龄/养殖阶段
    age_stage = st.selectbox(
        "日龄/养殖阶段",
        ["育雏期(0-14日龄)", "育成期(15-35日龄)", "育肥期(36日龄-出栏)", 
         "产蛋前期", "产蛋高峰期", "产蛋后期"],
        help="选择当前的养殖阶段"
    )
    
    # 病症
    symptom = st.text_input(
        "主要症状",
        placeholder="例如：咳嗽、拉稀、球虫病、精神沉郁...",
        help="描述动物的主要症状"
    )
    
    # 发病类型
    disease_type = st.selectbox(
        "发病类型",
        ["呼吸道疾病", "消化道疾病", "寄生虫病", "细菌性疾病", "病毒性疾病", "营养代谢病", "混合感染"],
        help="选择疾病的类型"
    )
    
    # 用途
    usage = st.radio(
        "用途",
        ["治疗", "预防"],
        horizontal=True
    )
    
    # 产蛋期是否可用
    egg_period_safe = st.checkbox(
        "产蛋期可用（禁用产蛋期禁用的药物）",
        value=True if "蛋鸡" in animal_type or "蛋鸭" in animal_type else False
    )
    
    # 养殖规模
    farm_scale = st.selectbox(
        "养殖规模",
        ["小规模(1000只以下)", "中规模(1000-10000只)", "大规模(10000只以上)"],
        help="选择养殖规模以推荐合适规格"
    )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 推荐按钮
    recommend_clicked = st.button("🔍 获取用药推荐", use_container_width=True)

# 主内容区
if recommend_clicked:
    if not symptom:
        st.warning("⚠️ 请输入主要症状后再获取推荐")
    else:
        with st.spinner("正在分析病情并推荐最佳用药方案..."):
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
                    farm_scale=farm_scale
                )
                
                # 保存结果到session state
                st.session_state['recommendation_result'] = result
                st.session_state['show_results'] = True
                
            except Exception as e:
                st.error(f"推荐过程中出现错误: {str(e)}")

# 显示推荐结果
if st.session_state.get('show_results', False):
    result = st.session_state['recommendation_result']
    
    # 分析结果展示
    st.markdown("---")
    st.subheader("📊 病情分析")
    
    analysis = result['input_analysis']
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**症状:** {analysis['symptom']}")
        st.markdown(f"**动物种类:** {analysis['animal_type']}")
    with col2:
        st.markdown(f"**可能疾病:** {', '.join(analysis['possible_diseases'])}")
        st.markdown(f"**疾病类型:** {analysis['disease_type']}")
    with col3:
        st.markdown(f"**养殖阶段:** {analysis['age_stage']}")
        st.markdown(f"**用途:** {usage}")
    
    # 单药推荐
    st.markdown("---")
    st.subheader("💊 单药推荐（性价比TOP 3）")
    
    single_recs = result['single_recommendations']
    if single_recs:
        for i, rec in enumerate(single_recs, 1):
            drug = rec.get('drug', {})
            
            # 安全获取字段
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
            
            # 使用Streamlit原生组件显示
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"### #{i} {drug_name}")
                with col2:
                    st.write(f"**价格: ¥{drug_price:.1f}**")
                
                # 显示标签信息
                cols = st.columns(4)
                with cols[0]:
                    st.caption(f"主要成分: {drug_component}")
                with cols[1]:
                    st.caption(f"规格: {drug_spec}")
                with cols[2]:
                    st.caption(f"兑水量: {drug_water}")
                with cols[3]:
                    st.caption(f"来源: {drug_source}")
                
                # 产蛋期安全性
                if drug_egg_safe:
                    st.success("✅ 产蛋期可用")
                else:
                    st.error("❌ 产蛋期禁用")
                
                # 适应症
                if drug_indications:
                    st.write(f"**适应症:** {', '.join(drug_indications)}")
                else:
                    st.write("**适应症:** 详见说明书")
                
                # 推荐理由
                st.info(f"**推荐理由:** {rec_reason}")
                
                # 用法用量
                st.write(f"**用法用量:** {rec_dosage}")
                
                st.divider()
    else:
        st.warning("未找到匹配的单药推荐，请尝试调整搜索条件")
    
    # 配伍禁忌警告
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
    
    # 组合推荐
    st.markdown("---")
    st.subheader("🎯 药物组合方案推荐")
    
    combo_recs = result['combination_recommendations']
    if combo_recs:
        for i, combo in enumerate(combo_recs, 1):
            combo_name = combo.get('scheme_name', '未命名方案')
            combo_desc = combo.get('description', '')
            combo_price = combo.get('total_price', 0)
            combo_drugs = combo.get('drugs', [])
            
            # 配伍禁忌检测结果显示
            compatibility_check = combo.get('compatibility_check', {})
            is_safe = compatibility_check.get('is_safe', True)
            level = compatibility_check.get('level', '安全')
            
            # 使用容器和列来显示
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"### 🎖️ {combo_name}")
                with col2:
                    st.write(f"**合计: ¥{combo_price:.1f}**")
                with col3:
                    # 显示配伍安全性状态
                    if is_safe:
                        st.success("✅ 配伍安全")
                    elif level == '禁忌':
                        st.error("❌ 配伍禁忌")
                    else:
                        st.warning("⚠️ 慎用")
                
                st.write(f"**方案说明:** {combo_desc}")
                
                # 如果有配伍问题，显示详细信息
                if not is_safe:
                    conflicts = compatibility_check.get('conflicts', [])
                    suggestions = compatibility_check.get('suggestions', [])
                    
                    with st.expander("⚠️ 配伍问题详情", expanded=True):
                        for conflict in conflicts:
                            st.error(f"**配伍问题:** {conflict.get('drug_a', '')} + {conflict.get('drug_b', '')}")
                            st.write(f"原因: {conflict.get('reason', '')}")
                            st.write(f"建议: {conflict.get('suggestion', '')}")
                
                # 展开显示每款药物的完整信息
                with st.expander("查看药物详情"):
                    for j, drug in enumerate(combo_drugs, 1):
                        st.write(f"**药物{j}: {drug.get('name', '未知')}**")
                        st.write(f"  - 时机: {drug.get('timing', '/')}")
                        st.write(f"  - 商品名: {drug.get('brand_name', '/')}")
                        st.write(f"  - 产品名: {drug.get('product_name', '/')}")
                        st.write(f"  - 通用名称: {drug.get('content', '')}")
                        st.write(f"  - 成分: {drug.get('main_component', '')}")
                        st.write(f"  - 包装规格: {drug.get('spec', '')}")
                        st.write(f"  - 适应症状或产品功效: {', '.join(drug.get('indications', []))}")
                        st.write(f"  - 用法用量: {drug.get('usage_info', '')}")
                        st.write(f"  - 兑水量: {drug.get('water', '')}")
                        st.write(f"  - 类别: {drug.get('category', '')}")
                        st.write(f"  - 来源: {drug.get('source', '')}")
                        st.write(f"  - 价格: ¥{drug.get('price', 0):.1f}")
                        
                        # 产蛋期安全性
                        if drug.get('egg_period_safe', True):
                            st.success("  ✅ 产蛋期可用")
                        else:
                            st.error("  ❌ 产蛋期禁用")
                        
                        st.write("")
                
                st.divider()
    else:
        st.info("当前条件下暂无推荐的组合方案")
    
    # 疾病知识展示
    st.markdown("---")
    st.subheader("📚 疾病知识")
    
    try:
        kb = get_disease_knowledge_base()
        diseases = analysis['possible_diseases']
        
        for disease_name in diseases[:2]:  # 显示前2个可能的疾病
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
    
    # 用药提示
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

# 产品目录展示
st.markdown("---")
st.subheader("📋 产品目录展示")
st.info("💡 本产品目录严格按照Excel文件中的分类结构展示，所有数据完整显示")

try:
    excel_file = pd.ExcelFile("合并产品信息表修改后.xlsx")
    
    # 创建三个独立标签页
    tab_base, tab_star, tab_info = st.tabs([
        " 底价目录", 
        "⭐ 明星产品", 
        "🏭 产品信息-华英"
    ])
    
    # 底价目录
    with tab_base:
        st.markdown("### 📦 底价目录产品")
        st.caption("来源：底价目录_20260112 工作表")
        st.markdown("---")
        
        df_base = pd.read_excel(excel_file, sheet_name='底价目录_20260112')
        # 过滤有效产品行（序号为数字的行）
        df_base_filtered = df_base[df_base['序号'].apply(lambda x: str(x).isdigit() if pd.notna(x) else False)]
        
        st.write(f"**共 {len(df_base_filtered)} 个底价目录产品**")
        
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
                <div class="drug-card">
                    <h3>{name}</h3>
                    <div>
                        <span class="info-badge badge-blue">底价目录</span>
                        <span class="info-badge badge-green">¥{price}</span>
                    </div>
                    <p style="color: #666; margin: 10px 0;">
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
        
        st.markdown("---")
        st.caption("️ 底价产品均不抵任务量，运费需客户自行承担")
    
    # 明星产品
    with tab_star:
        st.markdown("### ⭐ 明星产品")
        st.caption("来源：明星产品_20260512 工作表")
        st.markdown("---")
        
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
                <div class="drug-card" style="border-left-color: #f57c00;">
                    <h3 style="color: #e65100;">⭐ {display_name}</h3>
                    <div>
                        <span class="info-badge badge-orange">¥{price}</span>
                    </div>
                    <p style="color: #666; margin: 10px 0;">
                        <b>商品名:</b> {brand_name}<br>
                        <b>产品名称:</b> {product_name}<br>
                        <b>规格:</b> {spec}<br>
                        <b>政策:</b> {policy}
                    </p>
                </div>
                """, unsafe_allow_html=True)
    
    # 产品信息-华英
    with tab_info:
        st.markdown("### 🏭 产品信息-华英")
        st.caption("来源：产品信息_华英 工作表")
        st.markdown("---")
        
        df_info = pd.read_excel(excel_file, sheet_name='产品信息_华英')
        
        st.write(f"**共 {len(df_info)} 个华英产品信息**")
        
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
                <div class="drug-card" style="border-left-color: #43a047;">
                    <h3 style="color: #2e7d32;">{name}</h3>
                    <div>
                        <span class="info-badge badge-green">¥{price}</span>
                        <span class="info-badge badge-blue">{category}</span>
                        <span class="info-badge badge-purple">{timing}</span>
                    </div>
                    <p style="color: #666; margin: 10px 0;">
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
    
    # 分类说明
    st.markdown("---")
    st.markdown("""
    **📌 产品分类说明：**
    - **底价目录**：基础价格产品，价格随原料变动，有效期10天
    - **明星产品**：重点推荐产品，涵盖中药、饲料添加剂、维生素等类别
    - **产品信息-华英**：完整产品信息库，包含详细的产品规格、功效、用法用量等信息
    
    ⚠️ **注意**：三个类别的产品信息相互独立，不可混淆使用
    """)

except Exception as e:
    st.error(f"加载产品目录失败: {str(e)}")
    st.info("请确保'合并产品信息表修改后.xlsx'文件存在于当前目录")

# 页脚
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>华英兽药智能推荐系统 v1.0 | 专业养殖用药助手</p>
    <p style="font-size: 0.9em;">本系统推荐仅供参考，具体用药请遵医嘱</p>
</div>
""", unsafe_allow_html=True)
