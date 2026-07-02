import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_manager import (
    create_shed, get_sheds_by_farmer, get_shed, update_shed, delete_shed,
    get_all_farmer_profiles
)

st.set_page_config(
    page_title="棚舍管理",
    page_icon="🏠",
    layout="wide"
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

VENTILATION_OPTIONS = ["良好", "一般", "较差", "未评估"]

DENSITY_OPTIONS = ["低密度", "适中", "较高", "高密度", "未评估"]

CLEANLINESS_OPTIONS = ["干净", "一般", "较脏", "脏乱", "未评估"]

def local_css():
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
    .shed-card h3 {
        color: #e65100;
        margin-bottom: 15px;
    }
    .stButton>button {
        background: linear-gradient(90deg, #f57c00 0%, #e65100 100%);
        color: white;
        font-weight: bold;
        padding: 10px 20px;
        border-radius: 20px;
        border: none;
    }
    .info-row {
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
        margin-bottom: 10px;
    }
    .info-item {
        background: white;
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 0.9em;
    }
    .tag {
        display: inline-block;
        background: #fff;
        padding: 4px 10px;
        border-radius: 15px;
        font-size: 0.85em;
        margin: 3px;
        border: 1px solid #ffb74d;
        color: #e65100;
    }
    </style>
    """, unsafe_allow_html=True)

local_css()

st.markdown("""
<div style="background: linear-gradient(90deg, #f57c00 0%, #e65100 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 30px;">
    <h1>🏠 棚舍信息管理</h1>
    <p>管理您的养殖棚舍信息，为精准推荐提供数据支持</p>
</div>
""", unsafe_allow_html=True)

farmers = get_all_farmer_profiles()

if not farmers:
    st.warning("⚠️ 请先在「用户档案」页面创建养殖户档案")
    st.stop()

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
                temp_display = f"{shed.temperature}℃" if shed.temperature else "未记录"
                humidity_display = f"{shed.humidity}%" if shed.humidity else "未记录"
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
                    <div style="margin-top: 10px; display: flex; flex-wrap: wrap; gap: 15px;">
                        <span class="info-item">🌡️ 温度: {temp_display}</span>
                        <span class="info-item">💧 湿度: {humidity_display}</span>
                        <span class="info-item">💨 通风: {shed.ventilation_status or '未记录'}</span>
                        <span class="info-item">👥 密度: {shed.stocking_density or '未记录'}</span>
                        <span class="info-item">✨ 清洁度: {shed.cleanliness_level or '未记录'}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button(f"编辑 {shed.name}", key=f"edit_shed_{shed.id}", use_container_width=True):
                        st.session_state.editing_shed = shed
                        st.rerun()
                with col2:
                    if st.button(f"删除 {shed.name}", key=f"delete_shed_{shed.id}", use_container_width=True, type="secondary"):
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
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("棚舍名称 *", value=shed.name if shed else "", placeholder="如：一号鸡舍")
            shed_type = st.selectbox("棚舍类型 *", SHED_TYPES,
                                   index=SHED_TYPES.index(shed.type) if shed else 0)
            area = st.number_input("面积（平方米）*", min_value=1, max_value=10000,
                                  value=int(shed.area) if shed else 100)
            breed = st.selectbox("养殖品种 *", BREED_OPTIONS,
                                index=BREED_OPTIONS.index(shed.breed) if shed else 0)
        
        with col2:
            scale = st.selectbox("养殖规模 *", SCALE_OPTIONS,
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
        
        st.divider()
        st.subheader("🌡️ 环境信息")
        col3, col4 = st.columns(2)
        
        with col3:
            temperature = st.number_input("当前温度（℃）", min_value=-10, max_value=50,
                                         value=shed.temperature if shed and shed.temperature else 25)
            humidity = st.number_input("当前湿度（%）", min_value=0, max_value=100,
                                      value=shed.humidity if shed and shed.humidity else 60)
            lighting_hours = st.number_input("光照时长（小时）", min_value=0, max_value=24,
                                            value=shed.lighting_hours if shed and shed.lighting_hours else 16)
        
        with col4:
            ventilation_status = st.selectbox("通风状况", VENTILATION_OPTIONS,
                                             index=VENTILATION_OPTIONS.index(shed.ventilation_status) 
                                             if shed and shed.ventilation_status else 3)
            stocking_density = st.selectbox("饲养密度", DENSITY_OPTIONS,
                                           index=DENSITY_OPTIONS.index(shed.stocking_density) 
                                           if shed and shed.stocking_density else 4)
            cleanliness_level = st.selectbox("清洁程度", CLEANLINESS_OPTIONS,
                                            index=CLEANLINESS_OPTIONS.index(shed.cleanliness_level) 
                                            if shed and shed.cleanliness_level else 4)
        
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
                        environment_control=environment_control,
                        temperature=temperature,
                        humidity=humidity,
                        ventilation_status=ventilation_status,
                        stocking_density=stocking_density,
                        cleanliness_level=cleanliness_level,
                        lighting_hours=lighting_hours
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
                        temperature=temperature,
                        humidity=humidity,
                        ventilation_status=ventilation_status,
                        stocking_density=stocking_density,
                        cleanliness_level=cleanliness_level,
                        lighting_hours=lighting_hours
                    )
                    if result:
                        st.success(f"棚舍创建成功: {name}")
        
        if is_edit and st.button("取消编辑", use_container_width=True):
            st.session_state.editing_shed = None
            st.rerun()

st.markdown("---")
st.caption("💡 提示：完善的棚舍信息有助于系统提供更精准的用药推荐")