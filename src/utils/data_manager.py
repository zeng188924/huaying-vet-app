import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

FARMER_DATA_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'profiles', 'farmer_profiles.json')
SHED_DATA_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'profiles', 'shed_profiles.json')

@dataclass
class FarmerProfile:
    id: str
    name: str
    phone: str
    id_card_hash: str
    farming_years: int
    technical_level: str
    create_time: str
    update_time: str

@dataclass
class ShedInfo:
    id: str
    farmer_id: str
    name: str
    type: str
    area: float
    breed: str
    scale: str
    facilities: List[str]
    location: str
    environment_control: List[str]
    # 当前养殖批次标识，用于隔离不同批次的历史用药记录
    batch_id: str = "default"
    batch_name: str = ""
    batch_start_date: str = ""
    # 换禽/批次判定字段
    placement_date: str = ""          # 当前批次入舍日期
    current_age_days: Optional[int] = None  # 当前日龄
    expected_slaughter_date: str = ""  # 预计出栏/换羽日期
    # 基础环境指标
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    temperature_range: Optional[str] = None
    ventilation_status: Optional[str] = None
    stocking_density: Optional[str] = None
    cleanliness_level: Optional[str] = None
    ammonia_level: Optional[str] = None
    lighting_hours: Optional[int] = None
    # 扩展环境指标
    water_quality: Optional[str] = None
    dust_level: Optional[str] = None
    noise_level: Optional[str] = None
    feeding_mode: Optional[str] = None
    litter_condition: Optional[str] = None
    air_quality: Optional[str] = None
    dead_birds_daily: Optional[int] = None
    feed_intake_status: Optional[str] = None
    water_intake_status: Optional[str] = None
    medication_history: List[Dict] = None
    create_time: str = ""
    update_time: str = ""

def _ensure_data_dir():
    data_dir = os.path.dirname(FARMER_DATA_FILE)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)

def _load_json(file_path: str) -> List[Dict]:
    _ensure_data_dir()
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def _save_json(file_path: str, data: List[Dict]):
    _ensure_data_dir()
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def create_farmer_profile(name: str, phone: str, id_card_hash: str, 
                          farming_years: int, technical_level: str) -> FarmerProfile:
    now = datetime.now().isoformat()
    profile = FarmerProfile(
        id=str(uuid.uuid4()),
        name=name,
        phone=phone,
        id_card_hash=id_card_hash,
        farming_years=farming_years,
        technical_level=technical_level,
        create_time=now,
        update_time=now
    )
    data = _load_json(FARMER_DATA_FILE)
    data.append(asdict(profile))
    _save_json(FARMER_DATA_FILE, data)
    return profile

def get_farmer_profile(farmer_id: str) -> Optional[FarmerProfile]:
    data = _load_json(FARMER_DATA_FILE)
    for item in data:
        if item['id'] == farmer_id:
            return FarmerProfile(**item)
    return None

def get_all_farmer_profiles() -> List[FarmerProfile]:
    data = _load_json(FARMER_DATA_FILE)
    return [FarmerProfile(**item) for item in data]

def update_farmer_profile(farmer_id: str, **kwargs) -> Optional[FarmerProfile]:
    data = _load_json(FARMER_DATA_FILE)
    for i, item in enumerate(data):
        if item['id'] == farmer_id:
            item.update(kwargs)
            item['update_time'] = datetime.now().isoformat()
            _save_json(FARMER_DATA_FILE, data)
            return FarmerProfile(**item)
    return None

def delete_farmer_profile(farmer_id: str) -> bool:
    data = _load_json(FARMER_DATA_FILE)
    original_len = len(data)
    data = [item for item in data if item['id'] != farmer_id]
    if len(data) < original_len:
        _save_json(FARMER_DATA_FILE, data)
        delete_sheds_by_farmer(farmer_id)
        return True
    return False

def create_shed(farmer_id: str, name: str, shed_type: str, area: float,
                breed: str, scale: str, facilities: List[str], location: str,
                environment_control: List[str], batch_id: str = None,
                batch_name: str = "", placement_date: str = "",
                current_age_days: Optional[int] = None,
                expected_slaughter_date: str = "",
                temperature: Optional[float] = None,
                humidity: Optional[float] = None, temperature_range: Optional[str] = None,
                ventilation_status: Optional[str] = None,
                stocking_density: Optional[str] = None, cleanliness_level: Optional[str] = None,
                ammonia_level: Optional[str] = None, lighting_hours: Optional[int] = None,
                water_quality: Optional[str] = None, dust_level: Optional[str] = None,
                noise_level: Optional[str] = None, feeding_mode: Optional[str] = None,
                litter_condition: Optional[str] = None, air_quality: Optional[str] = None,
                dead_birds_daily: Optional[int] = None,
                feed_intake_status: Optional[str] = None, water_intake_status: Optional[str] = None) -> ShedInfo:
    now = datetime.now().isoformat()
    if batch_id is None:
        safe_name = "".join([c for c in name if c.isalnum() or c in ('_', '-')]) or "shed"
        batch_id = f"batch_{safe_name}_{datetime.now().strftime('%Y%m%d')}"
    if not batch_name:
        batch_name = f"{name} 初始批次"
    shed = ShedInfo(
        id=str(uuid.uuid4()),
        farmer_id=farmer_id,
        name=name,
        type=shed_type,
        area=area,
        breed=breed,
        scale=scale,
        facilities=facilities,
        location=location,
        environment_control=environment_control,
        batch_id=batch_id,
        batch_name=batch_name,
        batch_start_date=now,
        placement_date=placement_date,
        current_age_days=current_age_days,
        expected_slaughter_date=expected_slaughter_date,
        temperature=temperature,
        humidity=humidity,
        temperature_range=temperature_range,
        ventilation_status=ventilation_status,
        stocking_density=stocking_density,
        cleanliness_level=cleanliness_level,
        ammonia_level=ammonia_level,
        lighting_hours=lighting_hours,
        water_quality=water_quality,
        dust_level=dust_level,
        noise_level=noise_level,
        feeding_mode=feeding_mode,
        litter_condition=litter_condition,
        air_quality=air_quality,
        dead_birds_daily=dead_birds_daily,
        feed_intake_status=feed_intake_status,
        water_intake_status=water_intake_status,
        create_time=now,
        update_time=now
    )
    data = _load_json(SHED_DATA_FILE)
    data.append(asdict(shed))
    _save_json(SHED_DATA_FILE, data)
    return shed

def get_shed(shed_id: str) -> Optional[ShedInfo]:
    data = _load_json(SHED_DATA_FILE)
    for item in data:
        if item['id'] == shed_id:
            return ShedInfo(**item)
    return None

def get_sheds_by_farmer(farmer_id: str) -> List[ShedInfo]:
    data = _load_json(SHED_DATA_FILE)
    return [ShedInfo(**item) for item in data if item['farmer_id'] == farmer_id]


def get_medication_history(shed_id: str, batch_id: str = None, drug_type: str = None) -> List[Dict]:
    """获取指定棚舍的历史用药记录

    Args:
        shed_id: 棚舍ID
        batch_id: 指定批次ID，None 则只返回当前批次记录
        drug_type: 按药物类型过滤，如 "化药"、"中兽药"，None 返回全部
    """
    shed = get_shed(shed_id)
    if not shed or not shed.medication_history:
        return []

    current_batch = batch_id if batch_id is not None else shed.batch_id
    history = []
    for entry in shed.medication_history:
        # 兼容旧数据：没有 batch_id 的记录视为默认批次
        entry_batch = entry.get("batch_id", "default")
        if entry_batch == current_batch:
            if drug_type is None or entry.get("drug_type") == drug_type:
                history.append(entry)
    return history


def add_medication_history(shed_id: str, drug_name: str, notes: str = "", source: str = "manual",
                           batch_id: str = None, drug_type: str = None) -> Optional[ShedInfo]:
    """为指定棚舍添加一条历史用药记录

    Args:
        shed_id: 棚舍ID
        drug_name: 药物名称
        notes: 备注信息
        source: 记录来源，如 'manual'（手动录入）或 'recommendation'（系统推荐）
        batch_id: 批次ID，None 则使用棚舍当前批次
        drug_type: 药物类型，如 "化药"、"中兽药"，用于后续按类型过滤
    """
    data = _load_json(SHED_DATA_FILE)
    for item in data:
        if item['id'] == shed_id:
            if 'medication_history' not in item or item['medication_history'] is None:
                item['medication_history'] = []
            if batch_id is None:
                batch_id = item.get('batch_id', 'default')
            entry = {
                "drug_name": drug_name,
                "usage_date": datetime.now().isoformat(),
                "notes": notes,
                "source": source,
                "batch_id": batch_id,
                "drug_type": drug_type
            }
            item['medication_history'].append(entry)
            item['update_time'] = datetime.now().isoformat()
            _save_json(SHED_DATA_FILE, data)
            return ShedInfo(**item)
    return None


def delete_medication_history(shed_id: str, index: int) -> Optional[ShedInfo]:
    """删除指定棚舍的某条历史用药记录"""
    data = _load_json(SHED_DATA_FILE)
    for item in data:
        if item['id'] == shed_id:
            history = item.get('medication_history') or []
            if 0 <= index < len(history):
                history.pop(index)
                item['update_time'] = datetime.now().isoformat()
                _save_json(SHED_DATA_FILE, data)
                return ShedInfo(**item)
    return None

def start_new_batch(shed_id: str, batch_id: str = None, batch_name: str = "",
                     placement_date: str = "", expected_slaughter_date: str = "",
                     current_age_days: Optional[int] = None) -> Optional[ShedInfo]:
    """为棚舍开启新养殖批次，历史用药按 batch_id 隔离

    Args:
        shed_id: 棚舍ID
        batch_id: 新批次ID，None 则自动生成
        batch_name: 批次显示名称
        placement_date: 新批次入舍日期
        expected_slaughter_date: 预计出栏日期
        current_age_days: 当前日龄
    """
    if batch_id is None:
        batch_id = datetime.now().strftime("batch_%Y%m%d_%H%M%S")
    now = datetime.now().isoformat()
    data = _load_json(SHED_DATA_FILE)
    for item in data:
        if item['id'] == shed_id:
            item['batch_id'] = batch_id
            item['batch_name'] = batch_name or batch_id
            item['batch_start_date'] = now
            item['placement_date'] = placement_date
            item['expected_slaughter_date'] = expected_slaughter_date
            item['current_age_days'] = current_age_days
            item['update_time'] = now
            _save_json(SHED_DATA_FILE, data)
            return ShedInfo(**item)
    return None

def get_all_batches(shed_id: str) -> List[Dict]:
    """获取棚舍所有历史批次列表"""
    shed = get_shed(shed_id)
    if not shed:
        return []
    batches = {}
    # 当前批次
    current = {
        "batch_id": shed.batch_id,
        "batch_start_date": shed.batch_start_date,
        "is_current": True
    }
    batches[shed.batch_id] = current
    # 从历史用药中提取旧批次
    for entry in shed.medication_history or []:
        bid = entry.get("batch_id", "default")
        if bid not in batches:
            batches[bid] = {
                "batch_id": bid,
                "batch_start_date": "",
                "is_current": False
            }
    return list(batches.values())

def update_shed(shed_id: str, **kwargs) -> Optional[ShedInfo]:
    data = _load_json(SHED_DATA_FILE)
    for i, item in enumerate(data):
        if item['id'] == shed_id:
            item.update(kwargs)
            item['update_time'] = datetime.now().isoformat()
            _save_json(SHED_DATA_FILE, data)
            return ShedInfo(**item)
    return None

def delete_shed(shed_id: str) -> bool:
    data = _load_json(SHED_DATA_FILE)
    original_len = len(data)
    data = [item for item in data if item['id'] != shed_id]
    if len(data) < original_len:
        _save_json(SHED_DATA_FILE, data)
        return True
    return False

def delete_sheds_by_farmer(farmer_id: str):
    data = _load_json(SHED_DATA_FILE)
    data = [item for item in data if item['farmer_id'] != farmer_id]
    _save_json(SHED_DATA_FILE, data)