import streamlit as st
import sys
import os

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_root, 'src'))
sys.path.insert(0, os.path.join(_root, 'src', 'utils'))

from utils.data_manager import (
    create_farmer_profile, get_all_farmer_profiles, 
    get_farmer_profile, update_farmer_profile, delete_farmer_profile
)
from utils.encryption import hash_id_card

st.set_page_config(
    page_title="用户档案管理",
    page_icon="👤",
    layout="wide"
)

def local_css():
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
    .profile-card h3 {
        color: #1565c0;
        margin-bottom: 15px;
    }
    .stButton>button {
        background: linear-gradient(90deg, #1e88e5 0%, #43a047 100%);
        color: white;
        font-weight: bold;
        padding: 10px 20px;
        border-radius: 20px;
        border: none;
    }
    .info-row {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        margin-bottom: 10px;
    }
    .info-item {
        background: white;
        padding: 8px 15px;
        border-radius: 8px;
        font-size: 0.95em;
    }
    </style>
    """, unsafe_allow_html=True)

local_css()

st.markdown("""
<div style="background: linear-gradient(90deg, #1e88e5 0%, #43a047 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 30px;">
    <h1>👤 养殖户档案管理</h1>
    <p>建立您的个人档案，享受个性化服务</p>
</div>
""", unsafe_allow_html=True)

if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 'list'
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
                    if st.button(f"编辑 {profile.name}", key=f"edit_{profile.id}", use_container_width=True):
                        st.session_state.editing_profile = profile
                        st.session_state.active_tab = 'edit'
                        st.rerun()
                with col2:
                    if st.button(f"删除 {profile.name}", key=f"delete_{profile.id}", use_container_width=True, type="secondary"):
                        if delete_farmer_profile(profile.id):
                            st.success(f"已删除档案: {profile.name}")
                            st.rerun()
                        else:
                            st.error("删除失败")

with tab2:
    st.subheader("📝 填写档案信息")
    
    is_edit = st.session_state.editing_profile is not None
    
    if is_edit:
        profile = st.session_state.editing_profile
        st.info(f"正在编辑: {profile.name}")
    else:
        profile = None
    
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