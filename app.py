import streamlit as st
import sys
import os

# 将 src 及子包加入模块搜索路径，确保核心模块可被导入
_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_root, 'src'))
sys.path.insert(0, os.path.join(_root, 'src', 'core'))
sys.path.insert(0, os.path.join(_root, 'src', 'admin'))
sys.path.insert(0, os.path.join(_root, 'src', 'utils'))

from collections import OrderedDict

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

st.set_page_config(
    page_title="华英兽医宝（专家版）",
    page_icon="💊",
    layout="wide"
)

if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'

def show_home():
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #1e88e5 0%, #43a047 100%);
        padding: 30px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    }
    .main-header h1 { margin: 0; font-size: 2.8em; }
    .main-header p { margin: 15px 0 0 0; font-size: 1.3em; opacity: 0.9; }
    
    .feature-card {
        background: white;
        border-radius: 15px;
        padding: 30px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border: 2px solid #f0f0f0;
    }
    .feature-card .icon { font-size: 3.5em; margin-bottom: 15px; }
    .feature-card h3 { color: #1565c0; margin-bottom: 10px; }
    .feature-card p { color: #666; font-size: 0.95em; line-height: 1.6; }
    
    .info-box {
        background: #e3f2fd;
        border-left: 4px solid #1976d2;
        padding: 20px;
        border-radius: 10px;
        margin-top: 20px;
        color: #0d47a1;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="main-header">
        <h1>💊 华英兽医宝（专家版）</h1>
        <p>用好华英兽医宝，专家药方护禽好</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("## 📌 使用流程", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">👤</div>
            <h3>创建档案</h3>
            <p>录入养殖户基本信息，包括姓名、联系方式、养殖年限、技术等级等</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("开始创建 →", key="btn_profile", use_container_width=True):
            st.session_state.current_page = 'profile'
            st.rerun()

    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">🏠</div>
            <h3>管理棚舍</h3>
            <p>录入棚舍详细信息，包括类型、面积、品种、设施条件、环境控制设备等</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("管理棚舍 →", key="btn_shed", use_container_width=True):
            st.session_state.current_page = 'shed'
            st.rerun()

    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">💊</div>
            <h3>智能推荐</h3>
            <p>基于养殖环境和病症信息，获取精准的用药推荐方案和专业管理建议</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("获取推荐 →", key="btn_recommend", use_container_width=True):
            st.session_state.current_page = 'recommend'
            st.rerun()

    col4, col5, col6 = st.columns(3)

    with col4:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">📋</div>
            <h3>产品信息库</h3>
            <p>浏览所有兽药产品目录，包括底价目录、明星产品和华英产品详情</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("浏览产品 →", key="btn_catalog", use_container_width=True):
            st.session_state.current_page = 'catalog'
            st.rerun()

    with col5:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">🔍</div>
            <h3>产品搜索</h3>
            <p>在产品信息库中快速搜索药品名称，支持多类别联合检索</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("搜索产品 →", key="btn_search", use_container_width=True):
            st.session_state.current_page = 'catalog'
            st.rerun()

    with col6:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">📊</div>
            <h3>分类浏览</h3>
            <p>按底价目录、明星产品、华英产品三个类别分类查看所有产品</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("分类查看 →", key="btn_category", use_container_width=True):
            st.session_state.current_page = 'catalog'
            st.rerun()

    st.markdown("---")

    features = [
        ("✅ 信息持久化", "一次录入，重复使用，无需每次填写"),
        ("🔒 数据安全", "敏感信息加密存储，身份证号脱敏处理"),
        ("🎯 精准推荐", "结合养殖环境、品种、规模生成个性化方案"),
        ("📋 专业建议", "同步展示兽医诊疗关键事项和管理指导"),
        ("📱 多端适配", "支持桌面端和移动端访问"),
        ("🛠️ 数据管理", "提供档案和棚舍信息的增删改查功能"),
    ]

    cols = st.columns(3)
    for i, (title, desc) in enumerate(features):
        with cols[i % 3]:
            st.markdown(f"""
            <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 15px;">
                <strong style="color: #1565c0;">{title}</strong>
                <p style="color: #666; font-size: 0.9em; margin-top: 5px;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        <strong>💡 使用提示：</strong><br>
        首次使用请依次完成「用户档案」→「棚舍管理」→「智能推荐」三个步骤。<br>
        档案信息保存后，后续推荐将自动带入，无需重复填写。
    </div>
    """, unsafe_allow_html=True)

def show_profile():
    from src.utils.data_manager import (
        create_farmer_profile, get_all_farmer_profiles,
        get_farmer_profile, update_farmer_profile, delete_farmer_profile
    )
    from src.utils.encryption import hash_id_card

    st.markdown("""
    <style>
    .profile-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 15px;
        padding: 25px;
        margin: 15px 0;
        border-left: 5px solid #1e88e5;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .profile-card h3 { color: #1565c0; margin-bottom: 15px; }
    .info-row { display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 10px; }
    .info-item { background: white; padding: 8px 15px; border-radius: 8px; font-size: 0.95em; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background: linear-gradient(90deg, #1e88e5 0%, #43a047 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 30px;">
        <h1>👤 养殖户档案管理</h1>
        <p>建立您的个人档案，享受个性化服务</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("← 返回首页", key="back_home1"):
        st.session_state.current_page = 'home'
        st.rerun()

    if 'editing_profile' not in st.session_state:
        st.session_state.editing_profile = None

    tab1, tab2 = st.tabs(["📋 档案列表", "➕ 新建/编辑档案"])

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
                    <div class="profile-card">
                        <h3>👤 {profile.name}</h3>
                        <div class="info-row">
                            <span class="info-item">📱 电话: {profile.phone}</span>
                            <span class="info-item">📅 养殖年限: {profile.farming_years} 年</span>
                            <span class="info-item">🏆 技术等级: {profile.technical_level}</span>
                            <span class="info-item">📝 更新时间: {profile.update_time[:10]}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    col1, col2 = st.columns([1, 5])
                    with col1:
                        if st.button(f"编辑", key=f"edit_{profile.id}", use_container_width=True):
                            st.session_state.editing_profile = profile
                            st.rerun()
                    with col2:
                        if st.button(f"删除", key=f"delete_{profile.id}", use_container_width=True, type="secondary"):
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
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("姓名 *", value=profile.name if profile else "", placeholder="请输入姓名")
                phone = st.text_input("联系电话 *", value=profile.phone if profile else "", placeholder="请输入手机号码")
                id_card = st.text_input("身份证号", value="", placeholder="请输入身份证号（加密存储）")

            with col2:
                farming_years = st.number_input("养殖年限（年）*", min_value=0, max_value=50,
                                               value=profile.farming_years if profile else 0)
                technical_level = st.selectbox("技术等级 *",
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

    st.markdown("---")
    st.caption("💡 提示：身份证号采用加密存储，系统不会保存明文信息")

def show_shed():
    from src.utils.data_manager import (
        create_shed, get_sheds_by_farmer, get_shed, update_shed, delete_shed,
        get_all_farmer_profiles
    )

    FACILITY_OPTIONS = [
        "自然通风", "机械通风", "地暖", "热风炉", "水帘降温",
        "自动饮水系统", "自动喂料系统", "粪污处理系统", "消毒设备",
        "监控设备", "温湿度控制", "光照控制", "氨气监测"
    ]

    ENV_CONTROL_OPTIONS = [
        "自动温控系统", "智能通风系统", "环境监测仪",
        "自动加湿/除湿", "CO2监测", "负压控制系统"
    ]

    SHED_TYPES = ["肉鸡舍", "蛋鸡舍", "种鸡舍", "肉鸭舍", "蛋鸭舍", "鹅舍", "火鸡舍", "鸽子舍", "鹌鹑舍"]
    BREED_OPTIONS = ["白羽肉鸡", "黄羽肉鸡", "蛋鸡", "种鸡", "樱桃谷鸭", "麻鸭", "鹅", "火鸡", "鸽子", "鹌鹑", "其他"]
    SCALE_OPTIONS = ["小规模(1000只以下)", "中规模(1000-10000只)", "大规模(10000只以上)"]

    st.markdown("""
    <style>
    .shed-card {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        border-radius: 15px;
        padding: 25px;
        margin: 15px 0;
        border-left: 5px solid #f57c00;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .shed-card h3 { color: #e65100; margin-bottom: 15px; }
    .info-row { display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 10px; }
    .info-item { background: white; padding: 8px 12px; border-radius: 8px; font-size: 0.9em; }
    .tag { display: inline-block; background: #fff; padding: 4px 10px; border-radius: 15px; font-size: 0.85em; margin: 3px; border: 1px solid #ffb74d; color: #e65100; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background: linear-gradient(90deg, #f57c00 0%, #e65100 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 30px;">
        <h1>🏠 棚舍信息管理</h1>
        <p>管理您的养殖棚舍信息，为精准推荐提供数据支持</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("← 返回首页", key="back_home2"):
        st.session_state.current_page = 'home'
        st.rerun()

    farmers = get_all_farmer_profiles()

    if not farmers:
        st.warning("⚠️ 请先创建养殖户档案")
        return

    selected_farmer_id = st.selectbox(
        "选择养殖户 *",
        [f"{f.id} - {f.name}" for f in farmers],
        format_func=lambda x: x.split(" - ")[1]
    )
    selected_farmer_id = selected_farmer_id.split(" - ")[0]

    if 'editing_shed' not in st.session_state:
        st.session_state.editing_shed = None

    tab1, tab2 = st.tabs(["📋 棚舍列表", "➕ 新建/编辑棚舍"])

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
                    <div class="shed-card">
                        <h3>🏠 {shed.name}</h3>
                        <div class="info-row">
                            <span class="info-item">🐔 类型: {shed.type}</span>
                            <span class="info-item">🌾 品种: {shed.breed}</span>
                            <span class="info-item">📐 面积: {shed.area} ㎡</span>
                            <span class="info-item">📊 规模: {shed.scale}</span>
                            <span class="info-item">📍 位置: {shed.location}</span>
                        </div>
                        <div style="margin-top: 10px;">
                            <strong>设施条件:</strong><br>
                            {' '.join([f'<span class="tag">{f}</span>' for f in shed.facilities])}
                        </div>
                        <div style="margin-top: 10px;">
                            <strong>环境控制:</strong><br>
                            {' '.join([f'<span class="tag">{f}</span>' for f in shed.environment_control])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    col1, col2 = st.columns([1, 5])
                    with col1:
                        if st.button(f"编辑", key=f"edit_shed_{shed.id}", use_container_width=True):
                            st.session_state.editing_shed = shed
                            st.rerun()
                    with col2:
                        if st.button(f"删除", key=f"delete_shed_{shed.id}", use_container_width=True, type="secondary"):
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

        # 辅助函数：把 ISO 日期字符串解析为 date 对象，供 date_input 使用
        def _parse_date(date_str):
            from datetime import date
            if not date_str:
                return None
            try:
                return date.fromisoformat(date_str[:10])
            except Exception:
                return None

        with st.form("shed_form", clear_on_submit=True):
            st.markdown("#### 🏠 基础信息")
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("棚舍名称 *", value=shed.name if shed else "", placeholder="如：一号鸡舍")
                shed_type = st.selectbox("棚舍类型 *", SHED_TYPES,
                                       index=SHED_TYPES.index(shed.type) if shed else 0)
                area = st.number_input("面积（平方米）*", min_value=1, max_value=10000,
                                      value=int(shed.area) if shed else 100)
                breed = st.selectbox("养殖品种 *", BREED_OPTIONS,
                                    index=BREED_OPTIONS.index(shed.breed) if shed else 0)
                scale = st.selectbox("养殖规模 *", SCALE_OPTIONS,
                                    index=SCALE_OPTIONS.index(shed.scale) if shed else 1)

            with col2:
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
            batch_col1, batch_col2, batch_col3 = st.columns(3)
            with batch_col1:
                batch_name = st.text_input(
                    "批次名称",
                    value=shed.batch_name if shed else "",
                    placeholder="如：2026年7月第1批"
                )
            with batch_col2:
                placement_date = st.date_input(
                    "入舍日期",
                    value=_parse_date(shed.placement_date) if shed else None,
                    help="当前这批禽的入舍日期，用于判断养殖周期和历史用药隔离"
                )
            with batch_col3:
                expected_slaughter_date = st.date_input(
                    "预计出栏/换羽日期",
                    value=_parse_date(shed.expected_slaughter_date) if shed else None,
                    help="预计出栏或换羽日期，便于系统提示换禽"
                )
            batch_col4, batch_col5 = st.columns(2)
            with batch_col4:
                current_age_days = st.number_input(
                    "当前日龄",
                    min_value=0, max_value=999,
                    value=int(shed.current_age_days) if shed and shed.current_age_days is not None else 0,
                    help="当前禽群的实际日龄，如与入舍日期+养殖阶段不匹配会给出提醒"
                )

            st.markdown("#### 🌡️ 棚舍环境信息（越精确推荐越准）")
            env_col1, env_col2, env_col3, env_col4 = st.columns(4)
            with env_col1:
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
            with env_col2:
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
            with env_col3:
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
                air_quality = st.selectbox(
                    "空气质量",
                    ["请选择", "良好", "一般", "较差", "很差"],
                    index=["请选择", "良好", "一般", "较差", "很差"].index(shed.air_quality) if shed and shed.air_quality in ["请选择", "良好", "一般", "较差", "很差"] else 0
                )
            with env_col4:
                feeding_mode = st.selectbox(
                    "饲喂方式",
                    ["请选择", "自由采食", "定时限量", "人工投喂", "其他"],
                    index=["请选择", "自由采食", "定时限量", "人工投喂", "其他"].index(shed.feeding_mode) if shed and shed.feeding_mode in ["请选择", "自由采食", "定时限量", "人工投喂", "其他"] else 0
                )
                litter_condition = st.selectbox(
                    "垫料状况",
                    ["请选择", "干燥松散", "轻微潮湿", "潮湿结块", "严重潮湿/霉变"],
                    index=["请选择", "干燥松散", "轻微潮湿", "潮湿结块", "严重潮湿/霉变"].index(shed.litter_condition) if shed and shed.litter_condition in ["请选择", "干燥松散", "轻微潮湿", "潮湿结块", "严重潮湿/霉变"] else 0
                )
                dead_birds_daily = st.number_input(
                    "日死淘数",
                    min_value=0,
                    value=int(shed.dead_birds_daily) if shed and shed.dead_birds_daily is not None else 0
                )

            st.markdown("#### 🍽️ 采食饮水情况")
            intake_col1, intake_col2 = st.columns(2)
            with intake_col1:
                feed_intake_status = st.selectbox(
                    "采食情况",
                    ["请选择", "正常", "轻微下降", "明显下降", "几乎不吃"],
                    index=["请选择", "正常", "轻微下降", "明显下降", "几乎不吃"].index(shed.feed_intake_status) if shed and shed.feed_intake_status in ["请选择", "正常", "轻微下降", "明显下降", "几乎不吃"] else 0
                )
            with intake_col2:
                water_intake_status = st.selectbox(
                    "饮水情况",
                    ["请选择", "正常", "轻微下降", "明显下降", "几乎不喝"],
                    index=["请选择", "正常", "轻微下降", "明显下降", "几乎不喝"].index(shed.water_intake_status) if shed and shed.water_intake_status in ["请选择", "正常", "轻微下降", "明显下降", "几乎不喝"] else 0
                )

            submitted = st.form_submit_button("保存棚舍" if is_edit else "创建棚舍", use_container_width=True)

            def _fmt_date(d):
                return d.isoformat() if d else ""

            def _none_if_default(value, default="请选择"):
                return None if value == default else value

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

    st.markdown("---")
    st.caption("💡 提示：完善的棚舍信息有助于系统提供更精准的用药推荐")

def show_recommend():
    from drug_recommendation_system_full import (
        create_recommender, quick_recommend, DrugDatabase,
        DISEASE_TYPE_CATEGORIES, DISEASE_CATEGORY_DISPLAY,
        DISEASE_CATEGORY_DISPLAY_REVERSE
    )
    from disease_knowledge import get_disease_knowledge_base
    from key_matters import get_key_matters, get_summary_points
    from environment_adjustment import get_environment_adjustment_engine, ShedEnvironment
    from src.utils.data_manager import (
        get_all_farmer_profiles, get_sheds_by_farmer, get_shed, update_shed,
        get_medication_history, add_medication_history, delete_medication_history,
        start_new_batch
    )
    from src.admin.content_extractor import extract_product_info
    from src.utils.lab_report_parser import parse_lab_report

    @st.cache_resource
    def get_recommender_cache(_version="v20260706_2"):
        json_path = os.path.join(_root, 'data', 'products', 'huaying_products_full.json')
        recommender = create_recommender(json_path)
        return recommender

    st.markdown("""
    <style>
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

    st.markdown("""
    <div style="background: linear-gradient(90deg, #1e88e5 0%, #43a047 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 30px;">
        <h1>💊 智能用药推荐系统</h1>
        <p>基于养殖环境和病症信息，生成精准用药方案</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("← 返回首页", key="back_home3"):
        st.session_state.current_page = 'home'
        st.rerun()

    farmers = get_all_farmer_profiles()

    if not farmers:
        st.warning("⚠️ 请先创建养殖户档案")
        return

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
            help="选择养殖的动物种类",
            key="app_animal_type"
        )

        age_stage = st.selectbox(
            "日龄/养殖阶段",
            ["育雏期(0-14日龄)", "育成期(15-35日龄)", "育肥期(36日龄-出栏)",
             "产蛋前期", "产蛋高峰期", "产蛋后期"],
            help="选择当前的养殖阶段",
            key="app_age_stage"
        )

        # 实验室检测报告识别
        st.markdown("---")
        st.header("🔬 实验室检测报告识别")
        lab_file = st.file_uploader(
            "上传检测报告（图片/PDF）",
            type=["jpg", "jpeg", "png", "pdf"],
            key="app_lab_file",
            help="系统会自动识别报告中的疾病和症状关键词，回填到下方表单"
        )
        lab_text = st.text_area(
            "或粘贴检测报告文本",
            placeholder="可直接粘贴检测报告的结论或全文...",
            key="app_lab_text",
            height=80
        )

        if st.button("🧪 识别报告内容", key="app_parse_lab"):
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
                st.session_state['app_auto_symptom'] = parsed['symptom_summary'] or f"实验室检测提示：{parsed['disease_name']}"
                st.session_state['app_auto_disease'] = parsed['disease_name']
                st.rerun()
            else:
                st.info("未能从报告中识别到明确疾病，请手动填写")

        # 主要症状
        st.info(
            "💡 **症状填写提示**：请尽量详细描述，至少包括：\n\n"
            "1. **呼吸道**：咳嗽/呼噜/甩鼻/流涕/流泪/张口呼吸/伸颈喘/怪叫；\n"
            "2. **消化道**：采食量/饮水量变化、粪便颜色形状（绿便/血便/水便/过料）；\n"
            "3. **精神状态**：沉郁、扎堆、羽毛松乱、运动障碍、神经症状；\n"
            "4. **死淘情况**：日死淘数、死亡率趋势、发病日龄；\n"
            "5. **其他**：体温、产蛋变化、皮肤/冠髯异常等。"
        )
        auto_symptom = st.session_state.get('app_auto_symptom', '')
        symptom = st.text_area(
            "主要症状（请详细描述）",
            value=auto_symptom,
            placeholder="请尽量详细：咳嗽/呼噜/甩鼻/流涕/流泪/张口呼吸/减料/发热/粪便异常/死淘情况等",
            help="描述动物的主要症状，越详细推荐越准确。建议不少于20字。",
            key="app_symptom_input",
            height=100
        )
        if symptom:
            symptom_len = len(symptom.strip())
            if symptom_len < 10:
                st.warning("⚠️ 症状描述较简略，建议补充咳嗽频率、呼吸方式、精神状态、采食量、粪便等细节，推荐会更准确。")
            elif symptom_len < 20:
                st.info("ℹ️ 症状描述尚可，如能补充发病日龄、死淘数、粪便/产蛋细节，推荐会更精准。")

        # 发病类型：二级分类
        auto_disease = st.session_state.get('app_auto_disease', '')
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
            key="app_disease_category"
        )
        disease_category = DISEASE_CATEGORY_DISPLAY_REVERSE.get(disease_category_display, disease_category_display)
        specific_diseases = DISEASE_TYPE_CATEGORIES.get(disease_category, [])
        specific_index = specific_diseases.index(auto_disease) if auto_disease in specific_diseases else 0
        disease_type = st.selectbox(
            "具体疾病",
            specific_diseases,
            index=specific_index,
            help="再选择具体疾病",
            key="app_disease_type"
        )

        usage = st.radio(
            "用途",
            ["治疗", "预防"],
            horizontal=True,
            key="app_usage"
        )

        egg_period_safe = st.checkbox(
            "产蛋期可用（禁用产蛋期禁用的药物）",
            value=True if "蛋鸡" in animal_type or "蛋鸭" in animal_type else False,
            key="app_egg_safe"
        )

        farm_scale = st.selectbox(
            "养殖规模",
            ["小规模(1000只以下)", "中规模(1000-10000只)", "大规模(10000只以上)"],
            index=["小规模(1000只以下)", "中规模(1000-10000只)", "大规模(10000只以上)"].index(scale_default),
            help="选择养殖规模以推荐合适规格",
            key="app_farm_scale"
        )

        # 棚舍环境信息补充
        with st.expander("🌡️ 补充棚舍环境信息（让推荐更准确）", expanded=False):
            env_col1, env_col2 = st.columns(2)
            with env_col1:
                app_env_temperature = st.number_input(
                    "当前温度(℃)",
                    value=float(selected_shed.temperature) if selected_shed and selected_shed.temperature is not None else 0.0,
                    step=0.5,
                    key="app_env_temp"
                )
                app_env_humidity = st.number_input(
                    "当前湿度(%)",
                    value=float(selected_shed.humidity) if selected_shed and selected_shed.humidity is not None else 0.0,
                    step=1.0,
                    key="app_env_humidity"
                )
                app_env_ammonia = st.selectbox(
                    "氨气浓度",
                    ["请选择", "正常", "轻微超标", "明显超标", "严重超标"],
                    index=0,
                    key="app_env_ammonia"
                )
                app_env_dead_birds = st.number_input(
                    "日死淘数",
                    value=int(selected_shed.dead_birds_daily) if selected_shed and selected_shed.dead_birds_daily is not None else 0,
                    step=1,
                    key="app_env_dead"
                )
            with env_col2:
                app_env_ventilation = st.selectbox(
                    "通风状况",
                    ["请选择", "良好", "一般", "较差", "很差"],
                    index=0,
                    key="app_env_ventilation"
                )
                app_env_density = st.selectbox(
                    "饲养密度",
                    ["请选择", "适宜", "略高", "过高"],
                    index=0,
                    key="app_env_density"
                )
                app_env_feed_intake = st.selectbox(
                    "采食情况",
                    ["请选择", "正常", "轻微下降", "明显下降", "几乎不吃"],
                    index=0,
                    key="app_env_feed"
                )
                app_env_water_intake = st.selectbox(
                    "饮水情况",
                    ["请选择", "正常", "轻微下降", "明显下降", "几乎不喝"],
                    index=0,
                    key="app_env_water"
                )

        st.markdown("---")
        st.header("🚫 耐药性药物排除")

        json_path = os.path.join(_root, 'data', 'products', 'huaying_products_full.json')
        all_drugs = []
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
            help="选择您的养殖场中已经产生耐药性或经常使用导致效果下降的药物，系统将在推荐时排除这些药物",
            key="app_excluded_drugs"
        )

        st.markdown("---")
        st.header("🐣 当前养殖批次")

        if selected_shed:
            current_batch = selected_shed.batch_id or "default"
            batch_display = selected_shed.batch_name or current_batch
            st.markdown(f"**当前批次：** `{batch_display}`")
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
                    key=f"app_new_batch_{selected_shed.id}"
                )
                bcol1, bcol2 = st.columns(2)
                with bcol1:
                    new_placement_date = st.date_input(
                        "入舍日期 *",
                        value=None,
                        help="新一批禽的入舍日期，是判断是否换禽的核心依据",
                        key=f"app_new_placement_{selected_shed.id}"
                    )
                    new_current_age = st.number_input(
                        "当前日龄 *",
                        min_value=0, max_value=999, value=0,
                        help="新一批禽当前的实际日龄",
                        key=f"app_new_age_{selected_shed.id}"
                    )
                with bcol2:
                    new_expected_slaughter = st.date_input(
                        "预计出栏/换羽日期",
                        value=None,
                        help="预计这批禽出栏或换羽的日期",
                        key=f"app_new_slaughter_{selected_shed.id}"
                    )
                confirm_new_batch = st.checkbox(
                    "✅ 我确认该棚舍已经更换为新一批禽，上一批历史用药可隔离",
                    key=f"app_confirm_batch_{selected_shed.id}"
                )
                if st.button("🆕 确认新建批次", key=f"app_start_batch_{selected_shed.id}"):
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
        else:
            st.info("请先选择棚舍以管理批次")

        st.markdown("---")
        st.header("📜 历史用药记录")

        if selected_shed:
            medication_history = get_medication_history(selected_shed.id)

            if medication_history:
                st.info(f"当前批次已记录 {len(medication_history)} 条历史用药，系统推荐时将自动排除这些药物及同类易产生交叉耐药的药物")
                for idx, entry in enumerate(medication_history):
                    cols = st.columns([3, 1])
                    with cols[0]:
                        st.markdown(f"- **{entry['drug_name']}** ({entry['usage_date'][:10]})")
                    with cols[1]:
                        if st.button("🗑️", key=f"app_del_hist_{selected_shed.id}_{idx}", help="删除该条记录"):
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
                    key=f"app_history_select_{selected_shed.id}",
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
                key=f"app_custom_history_{selected_shed.id}",
                placeholder="例如：多西环素，阿莫西林"
            )
            if st.button("➕ 添加历史用药", key=f"app_add_history_{selected_shed.id}"):
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
        batch_info = f"**当前批次:** {selected_shed.batch_name or selected_shed.batch_id}"
        if selected_shed.placement_date:
            batch_info += f" | 入舍: {selected_shed.placement_date[:10]}"
        if selected_shed.current_age_days is not None:
            batch_info += f" | 日龄: {selected_shed.current_age_days}天"
        env_summary = []
        if selected_shed.temperature is not None:
            env_summary.append(f"温度 {selected_shed.temperature}℃")
        if selected_shed.humidity is not None:
            env_summary.append(f"湿度 {selected_shed.humidity}%")
        if selected_shed.ammonia_level:
            env_summary.append(f"氨气 {selected_shed.ammonia_level}")
        if selected_shed.ventilation_status:
            env_summary.append(f"通风 {selected_shed.ventilation_status}")
        if selected_shed.feed_intake_status:
            env_summary.append(f"采食 {selected_shed.feed_intake_status}")
        if selected_shed.water_intake_status:
            env_summary.append(f"饮水 {selected_shed.water_intake_status}")

        with st.container():
            st.markdown(f"""
            <div class="profile-section">
                <strong>棚舍名称:</strong> {selected_shed.name} |
                <strong>类型:</strong> {selected_shed.type} |
                <strong>品种:</strong> {selected_shed.breed} |
                <strong>面积:</strong> {selected_shed.area} ㎡ |
                <strong>规模:</strong> {selected_shed.scale}<br>
                <strong>位置:</strong> {selected_shed.location}<br>
                <span style="color:#1565c0;">{batch_info}</span><br>
                {' | '.join(env_summary) if env_summary else '环境信息待补充'}
            </div>
            """, unsafe_allow_html=True)

        # 日龄与养殖阶段一致性提醒
        if selected_shed.current_age_days is not None:
            stage_age_map = {
                "育雏期(0-14日龄)": (0, 14),
                "育成期(15-35日龄)": (15, 35),
                "育肥期(36日龄-出栏)": (36, 999),
                "产蛋前期": (0, 999),
                "产蛋高峰期": (0, 999),
                "产蛋后期": (0, 999),
            }
            low, high = stage_age_map.get(age_stage, (0, 999))
            if not (low <= selected_shed.current_age_days <= high):
                st.warning(
                    f"⚠️ 当前日龄（{selected_shed.current_age_days}天）与所选养殖阶段（{age_stage}）不匹配，请检查是否已换禽或日龄填写错误。"
                )

    recommend_clicked = st.button("🔍 获取用药推荐", use_container_width=True)

    if recommend_clicked:
        if not symptom:
            st.warning("⚠️ 请输入主要症状后再获取推荐")
        else:
            with st.spinner("正在分析病情并推荐最佳用药方案..."):
                try:
                    # 保存用户补充的棚舍环境信息
                    if selected_shed:
                        env_updates = {
                            "temperature": app_env_temperature if app_env_temperature != 0 else None,
                            "humidity": app_env_humidity if app_env_humidity != 0 else None,
                            "ammonia_level": None if app_env_ammonia == "请选择" else app_env_ammonia,
                            "ventilation_status": None if app_env_ventilation == "请选择" else app_env_ventilation,
                            "stocking_density": None if app_env_density == "请选择" else app_env_density,
                            "dead_birds_daily": app_env_dead_birds if app_env_dead_birds != 0 else None,
                            "feed_intake_status": None if app_env_feed_intake == "请选择" else app_env_feed_intake,
                            "water_intake_status": None if app_env_water_intake == "请选择" else app_env_water_intake,
                        }
                        env_updates = {k: v for k, v in env_updates.items() if v is not None}
                        if env_updates:
                            update_shed(selected_shed.id, **env_updates)
                            selected_shed = get_shed(selected_shed.id)

                    recommender = get_recommender_cache("v20260706_2")

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

        st.markdown("---")
        st.subheader("💊 单药推荐（性价比TOP 3）")

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
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**当前状态:** {adj.current_value if adj.current_value else '未知'}")
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

def show_product_catalog():
    import json
    import os
    import uuid

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
    <style>
    .catalog-card {
        background: white;
        border-radius: 15px;
        padding: 25px;
        margin: 15px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-left: 5px solid #1e88e5;
    }
    .catalog-card h3 { color: #1565c0; margin-bottom: 15px; }
    .catalog-row { display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 10px; }
    .catalog-item { background: #f5f7fa; padding: 8px 15px; border-radius: 8px; font-size: 0.95em; }
    .price-tag { color: #d32f2f; font-weight: bold; font-size: 1.2em; }
    .category-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85em;
        margin: 3px;
        font-weight: 500;
    }
    .badge-chem { background-color: #e3f2fd; color: #1565c0; }
    .badge-tcm { background-color: #e8f5e9; color: #2e7d32; }
    .badge-star { background-color: #fff3e0; color: #ef6c00; }
    .badge-base { background-color: #f3e5f5; color: #6a1b9a; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 30px;">
        <h1>📋 产品信息库</h1>
        <p>浏览所有兽药产品，了解详细信息</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("← 返回首页", key="back_home_catalog"):
        st.session_state.current_page = 'home'
        st.rerun()

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
            content = primary.get('content', '')
            category = primary.get('category', '')
            source = primary.get('source', '')
            brand_name = primary.get('brand_name', '')
            efficacy = format_indications(primary.get('indications', [])) if _PU_OK and format_indications else ""
            usage = primary.get('usage_info', '')
            remark = primary.get('remark', '')
            retail_price = primary.get('retail_price', '')
            egg_period_safe = primary.get('egg_period_safe', True)

            if source == "底价目录" and _PU_OK and format_bottom_price_usage:
                bottom_usage = format_bottom_price_usage(variants)
                if bottom_usage:
                    usage_display = f'<div style="margin-top: 5px;"><strong>用法用量:</strong><br>{bottom_usage.replace(chr(10), "<br>")}</div>'
                else:
                    usage_display = f'<div style="margin-top: 5px;"><strong>用法用量:</strong> {usage}</div>' if usage else ''
            else:
                usage_display = f'<div style="margin-top: 5px;"><strong>用法用量:</strong> {usage}</div>' if usage else ''

            with st.container():
                badge = f"<span style='color:#1976d2; font-weight:bold;'>📦 {len(variants)} 个规格</span>" if is_multi else ""
                st.markdown(f"""
                <div class="catalog-card">
                    <h3>{base_name} {badge}</h3>
                    <div class="catalog-row">
                        <span class="catalog-item">📦 成分: {content}</span>
                        <span class="catalog-item">🏷️ 类别: {category}</span>
                        <span class="catalog-item">📦 来源: {source}</span>
                    </div>
                    {f'<div class="catalog-row"><span class="catalog-item">🏷️ 商品名: {brand_name}</span></div>' if brand_name and brand_name != '/' else ''}
                    {f'<div class="catalog-row"><span class="catalog-item">💰 建议零售价: ¥{retail_price}</span></div>' if retail_price and retail_price != '/' else ''}
                    {f'<div style="margin-top: 10px;"><strong>适应症:</strong> {efficacy}</div>' if efficacy else ''}
                    {usage_display}
                    {f'<div style="margin-top: 5px;"><strong>备注:</strong> {remark}</div>' if remark else ''}
                    {f'<div style="margin-top: 5px;">{"✅ 产蛋期可用" if egg_period_safe else "❌ 产蛋期禁用"}</div>'}
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
                            if st.button("编辑", key=f"edit_prod_{v.get('id', '')}", use_container_width=True):
                                st.session_state.editing_product = v
                                st.rerun()
                        with c2:
                            if st.button(f"删除 {v.get('spec', v.get('name', ''))}", key=f"delete_prod_{v.get('id', '')}", use_container_width=True, type="secondary"):
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
        
        with st.form("product_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                product_id = st.text_input("产品ID *", value=product.get('id', '') if product else "", 
                                         placeholder="如：B1、S1、H1", key="prod_id")
                name = st.text_input("产品名称 *", value=product.get('name', '') if product else "", 
                                   placeholder="请输入产品名称", key="prod_name")
                brand_name = st.text_input("商品名", value=product.get('brand_name', '') if product else "", 
                                          placeholder="请输入商品名", key="prod_brand")
                content = st.text_input("成分/含量", value=product.get('content', '') if product else "", 
                                        placeholder="请输入成分或含量", key="prod_content")
                main_component = st.text_input("主要成分 *", value=product.get('main_component', '') if product else "", 
                                              placeholder="请输入主要成分", key="prod_main_comp")
                spec = st.text_input("包装规格 *", value=product.get('spec', '') if product else "", 
                                     placeholder="如：100g/袋*100袋/箱", key="prod_spec")
                water = st.text_input("兑水量", value=product.get('water', '') if product else "", 
                                      placeholder="如：400斤", key="prod_water")
                
                group_default = product.get('product_group_id', '') if product else ''
                if not group_default and _PU_OK and normalize_group_key and product:
                    group_default = normalize_group_key(product.get('name', ''), product.get('main_component', ''))
                product_group_id = st.text_input(
                    "产品分组 ID（同产品不同规格保持一致）",
                    value=group_default,
                    placeholder="如：硫酸黏菌素预混剂",
                    key="prod_group_id",
                )
            
            with col2:
                price = st.number_input("价格 *", min_value=0.0, max_value=100000.0, 
                                        value=float(product.get('price', 0)) if product else 0.0,
                                        step=0.01, key="prod_price")
                
                stock = st.number_input("库存数量", min_value=0, max_value=99999999,
                                        value=int(product.get('stock', 0)) if product else 0,
                                        step=1, key="prod_stock")
                
                cat = product.get('category', CATEGORY_OPTIONS[0]) if product else CATEGORY_OPTIONS[0]
                category = st.selectbox("类别", CATEGORY_OPTIONS,
                                       index=CATEGORY_OPTIONS.index(cat) if cat in CATEGORY_OPTIONS else 0,
                                       key="prod_cat")
                
                src = product.get('source', '用户上传') if product else '用户上传'
                source = st.selectbox("数据来源", SOURCE_OPTIONS,
                                      index=SOURCE_OPTIONS.index(src) if src in SOURCE_OPTIONS else SOURCE_OPTIONS.index("用户上传"),
                                      key="prod_src")
                
                disease_types = st.multiselect("疾病类型", DISEASE_TYPE_OPTIONS,
                                               default=product.get('disease_types', ['MIXED']) if product else ['MIXED'],
                                               key="prod_dt")
                
                egg_period_safe = st.checkbox("产蛋期可用", 
                                              value=bool(product.get('egg_period_safe', True)) if product else True,
                                              key="prod_egg")
                
                timing = st.text_input("时机", value=product.get('timing', '') if product else "", 
                                       placeholder="如：发病期间治疗使用", key="prod_timing")
            
            usage_info = st.text_area("用法用量", value=product.get('usage_info', '') if product else "", 
                                      placeholder="请输入用法用量", key="prod_usage")
            
            efficacy_str = ""
            if product and product.get('indications'):
                if isinstance(product['indications'], list):
                    efficacy_str = '、'.join(product['indications'])
                else:
                    efficacy_str = str(product['indications'])
            efficacy_input = st.text_input("适应症（用 、,;； 分隔）", 
                                           value=efficacy_str,
                                           placeholder="如：呼吸道感染、大肠杆菌病", 
                                           key="prod_efficacy")
            
            remark = st.text_input("备注", value=product.get('remark', '') if product else "", 
                                    placeholder="请输入备注信息", key="prod_remark")
            
            retail_price = st.text_input("建议零售价", value=product.get('retail_price', '') if product else "", 
                                          placeholder="请输入建议零售价", key="prod_retail")
            
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
                        st.cache_resource.clear()
        
        if is_edit and st.button("取消编辑", use_container_width=True):
            st.session_state.editing_product = None
            st.rerun()

    with tab_search:
        st.markdown("### 🔍 产品搜索")
        st.caption("在产品库中搜索产品")
        
        search_text = st.text_input("输入产品名称/成分/类别搜索", placeholder="例如：氟苯尼考...")
        
        if search_text:
            ql = search_text.lower()
            results = [
                p for p in products
                if ql in str(p.get("name", "")).lower()
                or ql in str(p.get("main_component", "")).lower()
                or ql in str(p.get("category", "")).lower()
                or ql in str(p.get("content", "")).lower()
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
                <div class="catalog-card">
                    <h3>{base_name} {badge}</h3>
                    <div class="catalog-row">
                        <span class="catalog-item">🏷️ 类别: {category}</span>
                        <span class="catalog-item">📦 来源: {source}</span>
                    </div>
                    {f'<div style="margin-top: 10px;"><strong>适应症:</strong> {efficacy}</div>' if efficacy else ''}
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
                        img_cols = st.columns(min(len(images), 4))
                        for idx, img in enumerate(images):
                            p = img.get("path", "")
                            if p and os.path.exists(p):
                                with img_cols[idx % 4]:
                                    st.image(p, caption=img.get("filename", ""))
                    
                    for v in variants:
                        c1, c2 = st.columns([1, 5])
                        with c1:
                            if st.button("编辑", key=f"search_edit_{v.get('id', '')}", use_container_width=True):
                                st.session_state.editing_product = v
                                st.rerun()
                        with c2:
                            if st.button(f"删除 {v.get('spec', v.get('name', ''))}", key=f"search_delete_{v.get('id', '')}", use_container_width=True, type="secondary"):
                                products = [p for p in products if p.get('id') != v.get('id')]
                                save_products(products)
                                st.success(f"已删除产品: {v.get('name', '')}")
                                st.rerun()
            
            if not results:
                st.info("未找到匹配的产品")
        else:
            st.info("请输入搜索关键词")

    st.markdown("---")
    st.markdown("""
    **📌 产品分类说明：**
    - **底价目录**：基础价格产品
    - **明星产品**：重点推荐产品
    - **产品信息-华英**：完整产品信息库
    - **用户上传**：用户自行添加的产品
    
    ⚠️ 所有产品数据存储在 `huaying_products_full.json` 文件中
    """)

if st.session_state.current_page == 'home':
    show_home()
elif st.session_state.current_page == 'profile':
    show_profile()
elif st.session_state.current_page == 'shed':
    show_shed()
elif st.session_state.current_page == 'recommend':
    show_recommend()
elif st.session_state.current_page == 'catalog':
    show_product_catalog()