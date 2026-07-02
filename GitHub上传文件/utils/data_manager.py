import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

FARMER_DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'farmer_profiles.json')
SHED_DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'shed_profiles.json')

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
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    ventilation_status: Optional[str] = None
    stocking_density: Optional[str] = None
    cleanliness_level: Optional[str] = None
    ammonia_level: Optional[str] = None
    lighting_hours: Optional[int] = None
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
                environment_control: List[str], temperature: Optional[float] = None,
                humidity: Optional[float] = None, ventilation_status: Optional[str] = None,
                stocking_density: Optional[str] = None, cleanliness_level: Optional[str] = None,
                ammonia_level: Optional[str] = None, lighting_hours: Optional[int] = None) -> ShedInfo:
    now = datetime.now().isoformat()
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
        temperature=temperature,
        humidity=humidity,
        ventilation_status=ventilation_status,
        stocking_density=stocking_density,
        cleanliness_level=cleanliness_level,
        ammonia_level=ammonia_level,
        lighting_hours=lighting_hours,
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