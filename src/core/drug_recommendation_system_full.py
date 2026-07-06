# -*- coding: utf-8 -*-
"""
兽药智能推荐系统 - 完整版（数据清理后）
整合清洗后的产品数据：
- 底价目录：21个产品
- 产品信息_华英：74个产品
总计：95个产品

清理说明：已移除所有标记为"明星产品"（source=明星产品）的记录，
仅保留同时属于"底价目录"和"产品信息_华英"分类体系的产品数据。

推荐逻辑调整：
- 取消对明星产品的额外加权，确保底价目录与华英产品公平竞争
- 以适应症匹配为核心权重，疾病类型与用途场景作为辅助权重
- 华英产品信息来源给予少量信息完整度加成

新增功能：配伍禁忌自动检测
"""

import pandas as pd
import json
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

# 导入配伍禁忌检测模块
from drug_compatibility import (
    DrugCompatibilityChecker, 
    CompatibilityLevel,
    check_drug_compatibility
)

# 导入病症-药物关联验证模块
from disease_drug_validator import (
    DiseaseDrugValidator,
    get_disease_drug_validator,
)


# 发病类型二级分类映射：大类 + 具体疾病 -> 内部疾病类型编码
# 设计原则：
# 1. 先按疾病系统/病因分大类，便于用户快速定位
# 2. 每个大类下列举常见、多发、易误诊的具体疾病，覆盖鸡/鸭/鹅/鸽/鹌鹑
# 3. 保留"其他"兜底项，避免用户因找不到精确病名而无法提交
DISEASE_TYPE_CATEGORIES = {
    "呼吸道疾病": [
        "慢性呼吸道病（支原体/慢呼）",
        "滑液囊支原体（MS）",
        "传染性鼻炎",
        "传染性喉气管炎",
        "传染性支气管炎",
        "气囊炎",
        "气管栓塞/呼吸道堵塞",
        "肺炎",
        "流行性感冒（禽流感/H5/H7/H9）",
        "新城疫（呼吸道型）",
        "鸭传染性浆膜炎",
        "鸭疫里默氏杆菌病",
        "鸭坦布苏病毒病（黄病毒病）",
        "鹅流感",
        "普通感冒/受凉",
        "其他呼吸道感染",
    ],
    "消化道疾病": [
        "大肠杆菌病",
        "沙门氏菌病（白痢/伤寒/副伤寒）",
        "坏死性肠炎",
        "溃疡性肠炎",
        "病毒性肠炎",
        "腺胃炎",
        "肌胃炎",
        "嗉囊炎/嗉囊积液",
        "肠炎/腹泻",
        "消化不良",
        "过料/饲料便",
        "霍乱（巴氏杆菌引起的腹泻型）",
        "其他消化道感染",
    ],
    "寄生虫病": [
        "球虫病（盲肠球虫）",
        "球虫病（小肠球虫）",
        "蛔虫病",
        "绦虫病",
        "羽虱/螨虫",
        "组织滴虫病（黑头病）",
        "毛滴虫病",
        "前殖吸虫病",
        "其他寄生虫病",
    ],
    "细菌性疾病": [
        "大肠杆菌病",
        "沙门氏菌病",
        "巴氏杆菌病（禽霍乱）",
        "葡萄球菌病",
        "链球菌病",
        "绿脓杆菌病",
        "鸭疫里默氏杆菌病",
        "支原体感染（慢性呼吸道/滑液囊）",
        "细菌性败血症",
        "禽结核",
        "其他细菌感染",
    ],
    "病毒性疾病": [
        "禽流感（H5/H7/H9）",
        "新城疫",
        "传染性支气管炎",
        "传染性喉气管炎",
        "传染性法氏囊病",
        "马立克氏病",
        "禽白血病",
        "禽脑脊髓炎",
        "鸡传染性贫血",
        "禽痘",
        "鸭瘟",
        "鸭病毒性肝炎",
        "鸭坦布苏病毒病",
        "小鹅瘟",
        "鹅流感",
        "其他病毒感染",
    ],
    "营养代谢病": [
        "维生素A缺乏症",
        "维生素D/E缺乏症",
        "B族维生素缺乏症",
        "矿物质缺乏症（钙/磷/锰/锌）",
        "痛风",
        "脂肪肝综合征",
        "腹水综合征",
        "热应激/冷应激",
        "转群/惊吓应激",
        "啄癖（啄肛/啄羽/啄蛋）",
        "异食癖",
        "霉菌毒素中毒",
        "药物/饲料中毒",
        "其他营养代谢/中毒病",
    ],
    "混合感染": [
        "呼吸道+消化道混合感染",
        "细菌+病毒混合感染",
        "病毒+寄生虫混合感染",
        "细菌+寄生虫混合感染",
        "支原体+大肠杆菌混合感染",
        "新城疫+禽流感混合感染",
        "其他混合感染",
    ],
    "生殖系统疾病": [
        "输卵管炎",
        "卵巢炎",
        "产蛋下降综合征",
        "血斑蛋/沙壳蛋/畸形蛋",
        "软壳蛋/薄壳蛋",
        "脱肛/难产",
        "输卵管脱垂",
        "其他生殖系统疾病",
    ],
}

# 疾病大类展示名称（在 UI 下拉框中显示更详细的分类提示）
DISEASE_CATEGORY_DISPLAY = {
    "呼吸道疾病": "呼吸道疾病（支原体/细菌/病毒/真菌）",
    "消化道疾病": "消化道疾病（细菌/病毒/寄生虫/毒素）",
    "寄生虫病": "寄生虫病（球虫/蠕虫/体外寄生虫）",
    "细菌性疾病": "细菌性疾病（革兰氏阴性/阳性菌）",
    "病毒性疾病": "病毒性疾病（呼吸道/消化道/神经型）",
    "营养代谢病": "营养代谢与中毒病（维生素/矿物质/应激/毒素）",
    "混合感染": "混合感染（细菌+病毒/细菌+寄生虫/病毒+寄生虫）",
    "生殖系统疾病": "生殖系统疾病（输卵管/卵巢/产蛋异常）",
}

# 展示名称 -> 内部短名称 的反向映射，便于 UI 选择后还原为内部键
DISEASE_CATEGORY_DISPLAY_REVERSE = {v: k for k, v in DISEASE_CATEGORY_DISPLAY.items()}

# 中文疾病名称到内部编码的映射（包含大类和具体疾病）
DISEASE_TYPE_MAPPING = {
    # 大类
    "寄生虫病": "PARASITIC",
    "呼吸道疾病": "RESPIRATORY",
    "消化道疾病": "DIGESTIVE",
    "细菌性疾病": "BACTERIAL",
    "病毒性疾病": "VIRAL",
    "营养代谢病": "NUTRITIONAL",
    "混合感染": "MIXED",
    "生殖系统疾病": "REPRODUCTIVE",
}

# 自动将具体疾病加入映射
for _category, _diseases in DISEASE_TYPE_CATEGORIES.items():
    for _disease in _diseases:
        if _disease not in DISEASE_TYPE_MAPPING:
            DISEASE_TYPE_MAPPING[_disease] = DISEASE_TYPE_MAPPING[_category]


@dataclass
class DrugInfo:
    """药物信息"""
    id: str
    name: str  # 产品名称
    content: str  # 通用名称
    spec: str  # 包装规格
    water: str  # 兑水量
    price: float  # 价格
    indications: List[str]  # 适应症状或产品功效
    main_component: str  # 成分
    category: str  # 类别
    egg_period_safe: bool  # 产蛋期安全性
    disease_types: List[str]  # 疾病类型
    usage_info: str  # 用法用量
    source: str  # 数据来源
    # 新增字段
    timing: str = ""  # 时机
    brand_name: str = ""  # 商品名
    product_name: str = ""  # 产品名（完整名称）
    
    def to_dict(self):
        return asdict(self)


@dataclass
class RecommendationRequest:
    """推荐请求"""
    animal_type: str
    age_stage: str
    symptom: str
    disease_type: str
    usage: str
    egg_period_safe: bool
    farm_scale: str
    excluded_drugs: List[str] = None
    medication_history: List[str] = None  # 历史用药记录（药物名称列表）


@dataclass
class DrugRecommendation:
    """药物推荐结果"""
    drug: DrugInfo
    match_score: float
    reason: str
    dosage_recommendation: str
    reason_detail: "DrugRecommendationReason" = None
    
    def to_dict(self):
        result = {
            'drug': self.drug.to_dict(),
            'match_score': self.match_score,
            'reason': self.reason,
            'dosage_recommendation': self.dosage_recommendation
        }
        if self.reason_detail is not None:
            result['reason_detail'] = self.reason_detail.to_dict()
        return result


@dataclass
class DrugRecommendationReason:
    """单个药品推荐理由详情（通俗化、结构化展示）"""
    applicable_symptoms: str = ""    # 适用症状
    component_advantage: str = ""    # 成分优势
    usage_summary: str = ""          # 用法概要

    def to_dict(self):
        return asdict(self)


@dataclass
class CombinationRationale:
    """组合方案推荐理由详情"""
    combination_basis: str = ""           # 组合依据
    drug_roles: List[Dict] = None         # 各产品在组合中的作用
    synergy_effect: str = ""              # 产品间协同效应
    mechanism: str = ""                   # 解决病症的具体机制
    low_resistance_analysis: str = ""     # 低耐药风险分析
    resistance_prevention_guide: str = "" # 耐药预防操作指导

    def to_dict(self):
        result = asdict(self)
        if result['drug_roles'] is None:
            result['drug_roles'] = []
        return result


class DrugDatabase:
    """药物数据库 - 包含所有114个产品"""
    
    def __init__(self, data_path: str):
        self.drugs: List[DrugInfo] = []
        # 根据文件扩展名判断加载方式
        if data_path.endswith('.json'):
            self.load_from_json(data_path)
        else:
            self.load_all_products(data_path)
    
    def load_from_json(self, json_path: str):
        """从JSON文件加载产品数据"""
        import json
        with open(json_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        for p in products:
            drug = DrugInfo(
                id=p.get('id', ''),
                name=p.get('name', ''),
                content=p.get('content', ''),
                spec=p.get('spec', ''),
                water=p.get('water', ''),
                price=float(p.get('price', 0)),
                indications=p.get('indications', []),
                main_component=p.get('main_component', ''),
                category=p.get('category', ''),
                egg_period_safe=p.get('egg_period_safe', True),
                disease_types=p.get('disease_types', ['MIXED']),
                usage_info=p.get('usage_info', ''),
                source=p.get('source', ''),
                timing=p.get('timing', ''),
                brand_name=p.get('brand_name', ''),
                product_name=p.get('product_name', '')
            )
            self.drugs.append(drug)
        
        print(f"[数据库] 从JSON加载 {len(self.drugs)} 个产品")
    
    def _parse_price(self, value) -> float:
        """解析价格字段"""
        if pd.isna(value):
            return 0.0
        value_str = str(value).strip()
        if value_str in ['/', '-', '', 'NaN', 'nan', 'None']:
            return 0.0
        try:
            return float(value_str)
        except ValueError:
            return 0.0
    
    def load_all_products(self, excel_path: str):
        """从Excel加载所有产品数据"""
        excel_file = pd.ExcelFile(excel_path)
        
        # 1. 加载底价目录产品
        self._load_base_products(excel_file)
        
        # 2. 加载产品信息_华英（包含明星产品信息）
        self._load_info_products(excel_file)
        
        print(f"[数据库] 从Excel加载 {len(self.drugs)} 个产品")
    
    def _load_base_products(self, excel_file):
        """加载底价目录产品（22个）"""
        df = pd.read_excel(excel_file, sheet_name='底价目录_20260112')
        
        base_knowledge = {
            "氟苯尼考粉": {"component": "氟苯尼考", "indications": ["鸡霍乱", "鸡白痢", "大肠杆菌病", "慢性呼吸道病"], "types": ["BACTERIAL", "RESPIRATORY"], "egg_safe": False, "usage": "混饮：每袋兑水2000斤，连用3-5日", "timing": "发病期间治疗使用"},
            "盐酸多西环素可溶性粉": {"component": "盐酸多西环素", "indications": ["鸡慢性呼吸道病", "大肠杆菌病", "巴氏杆菌病", "沙门氏菌病"], "types": ["BACTERIAL", "RESPIRATORY"], "egg_safe": False, "usage": "混饮：每袋兑水1500斤，连用3-5日", "timing": "发病期间治疗使用"},
            "卡巴匹林钙粉": {"component": "卡巴匹林钙", "indications": ["解热", "镇痛", "消炎", "退热"], "types": ["MIXED"], "egg_safe": False, "usage": "混饮：每袋兑水2000斤，连用3日", "timing": "发热时使用"},
            "阿莫西林可溶性粉": {"component": "阿莫西林", "indications": ["大肠杆菌病", "沙门氏菌病", "葡萄球菌病", "链球菌病"], "types": ["BACTERIAL", "DIGESTIVE"], "egg_safe": False, "usage": "混饮：每袋兑水900斤，连用3-5日", "timing": "发病期间治疗使用"},
            "硫酸黏菌素预混剂1000g": {"component": "硫酸黏菌素", "indications": ["革兰氏阴性菌引起的肠道感染", "大肠杆菌病", "沙门氏菌病"], "types": ["BACTERIAL", "DIGESTIVE"], "egg_safe": False, "usage": "混饲：每袋拌料1000斤，连用3-5日", "timing": "发病期间治疗使用"},
            "硫酸黏菌素预混剂500g": {"component": "硫酸黏菌素", "indications": ["革兰氏阴性菌引起的肠道感染", "大肠杆菌病", "沙门氏菌病"], "types": ["BACTERIAL", "DIGESTIVE"], "egg_safe": False, "usage": "混饲：每袋拌料500斤，连用3-5日", "timing": "发病期间治疗使用"},
            "硫酸新霉素可溶性粉": {"component": "硫酸新霉素", "indications": ["禽大肠杆菌病", "沙门氏菌病", "禽霍乱", "鸡白痢"], "types": ["BACTERIAL", "DIGESTIVE"], "egg_safe": False, "usage": "混饮：每袋兑水800斤，连用3-5日", "timing": "发病期间治疗使用"},
            "盐酸恩诺沙星可溶性粉": {"component": "盐酸恩诺沙星", "indications": ["禽大肠杆菌病", "鸡白痢", "禽霍乱", "慢性呼吸道病"], "types": ["BACTERIAL", "RESPIRATORY", "DIGESTIVE"], "egg_safe": False, "usage": "混饮：每袋兑水1000斤，连用3-5日", "timing": "发病期间治疗使用"},
            "硫酸庆大霉素可溶性粉": {"component": "硫酸庆大霉素", "indications": ["革兰氏阴性菌和阳性菌感染", "大肠杆菌病", "沙门氏菌病"], "types": ["BACTERIAL", "DIGESTIVE"], "egg_safe": False, "usage": "混饮：每袋兑水800斤，连用3-5日", "timing": "发病期间治疗使用"},
            "盐酸林可霉素可溶性粉": {"component": "盐酸林可霉素", "indications": ["革兰氏阳性菌感染", "支原体感染", "坏死性肠炎"], "types": ["BACTERIAL", "DIGESTIVE", "RESPIRATORY"], "egg_safe": False, "usage": "混饮：每袋兑水1000斤，连用3-5日", "timing": "发病期间治疗使用"},
            "地美硝唑预混剂": {"component": "地美硝唑", "indications": ["禽组织滴虫病", "禽毛滴虫病", "坏死性肠炎", "球虫病辅助治疗"], "types": ["PARASITIC", "DIGESTIVE"], "egg_safe": False, "usage": "混饲：每袋拌料1000斤，连用3-5日", "timing": "发病期间治疗使用"},
            "单硫酸卡那霉素可溶性粉": {"component": "单硫酸卡那霉素", "indications": ["禽大肠杆菌病", "沙门氏菌病", "禽霍乱"], "types": ["BACTERIAL", "DIGESTIVE", "RESPIRATORY"], "egg_safe": False, "usage": "混饮：每袋兑水800斤，连用3-5日", "timing": "发病期间治疗使用"},
            "替米考星溶液": {"component": "替米考星", "indications": ["鸡慢性呼吸道病", "传染性鼻炎", "禽霍乱"], "types": ["RESPIRATORY", "BACTERIAL"], "egg_safe": False, "usage": "混饮：每瓶兑水1000斤，连用3-5日", "timing": "发病期间治疗使用"},
            "硫酸安普霉素可溶性粉": {"component": "硫酸安普霉素", "indications": ["禽大肠杆菌病", "沙门氏菌病", "禽霍乱"], "types": ["BACTERIAL", "DIGESTIVE"], "egg_safe": False, "usage": "混饮：每袋兑水800斤，连用3-5日", "timing": "发病期间治疗使用"},
            "替米考星预混剂": {"component": "替米考星", "indications": ["鸡慢性呼吸道病", "传染性鼻炎", "禽霍乱"], "types": ["RESPIRATORY", "BACTERIAL"], "egg_safe": False, "usage": "混饲：每袋拌料1000斤，连用3-5日", "timing": "发病期间治疗使用"},
            "复方磺胺间甲氧嘧啶钠可溶性粉": {"component": "磺胺间甲氧嘧啶钠+甲氧苄啶", "indications": ["禽大肠杆菌病", "沙门氏菌病", "禽霍乱", "球虫病"], "types": ["BACTERIAL", "DIGESTIVE", "PARASITIC"], "egg_safe": False, "usage": "混饮：每袋兑水800斤，连用3-5日", "timing": "发病期间治疗使用"},
            "酒石酸泰万菌素预混剂": {"component": "酒石酸泰万菌素", "indications": ["鸡慢性呼吸道病", "滑液囊支原体", "猪支原体肺炎"], "types": ["RESPIRATORY"], "egg_safe": False, "usage": "混饲：每袋拌料1000斤，连用5-7日", "timing": "发病期间治疗使用"},
            "磺胺喹噁啉钠可溶性粉（去球虫）": {"component": "磺胺喹噁啉钠", "indications": ["鸡球虫病", "兔球虫病", "盲肠球虫", "小肠球虫"], "types": ["PARASITIC"], "egg_safe": False, "usage": "混饮：每袋兑水1000斤，连用3日", "timing": "发病期间治疗使用"},
            "磺胺氯吡嗪钠可溶性粉（去球虫）": {"component": "磺胺氯吡嗪钠", "indications": ["鸡球虫病", "兔球虫病", "盲肠球虫", "禽霍乱"], "types": ["PARASITIC", "BACTERIAL"], "egg_safe": False, "usage": "混饮：每袋兑水800斤，连用3日", "timing": "发病期间治疗使用"},
            "30%氟苯尼考可溶性粉": {"component": "氟苯尼考", "indications": ["鸡霍乱", "鸡白痢", "大肠杆菌病", "慢性呼吸道病"], "types": ["BACTERIAL", "RESPIRATORY"], "egg_safe": False, "usage": "混饮：每袋兑水1500斤，连用3-5日", "timing": "发病期间治疗使用"},
            "10%盐酸多西环素可溶性粉": {"component": "盐酸多西环素", "indications": ["鸡慢性呼吸道病", "大肠杆菌病", "巴氏杆菌病", "沙门氏菌病"], "types": ["BACTERIAL", "RESPIRATORY"], "egg_safe": False, "usage": "混饮：每袋兑水1200斤，连用3-5日", "timing": "发病期间治疗使用"},
            "80%延胡索酸泰妙菌素（呼吸道）": {"component": "延胡索酸泰妙菌素", "indications": ["鸡慢性呼吸道病", "滑液囊支原体", "猪支原体肺炎"], "types": ["RESPIRATORY"], "egg_safe": False, "usage": "混饲：每袋拌料1000斤，连用5-7日", "timing": "发病期间治疗使用"},
        }
        
        for _, row in df.iterrows():
            if pd.notna(row['序号']) and str(row['序号']).isdigit():
                name = str(row['品名'])
                knowledge = base_knowledge.get(name, {})
                
                # 选择规格（优先小规格）
                if pd.notna(row['单价        元/袋/瓶.1']) and str(row['单价        元/袋/瓶.1']) not in ['/', '']:
                    spec = str(row['规格型号.1']) if pd.notna(row['规格型号.1']) else ""
                    water = str(row['兑水量.1']) if pd.notna(row['兑水量.1']) else ""
                    price = self._parse_price(row['单价        元/袋/瓶.1'])
                else:
                    spec = str(row['规格型号']) if pd.notna(row['规格型号']) else ""
                    water = str(row['兑水量']) if pd.notna(row['兑水量']) else ""
                    price = self._parse_price(row['单价        元/袋/瓶'])
                
                # 获取含量字段（仅用于参考）
                content_value = str(row['含量']) if pd.notna(row['含量']) else ""
                
                # 通用名称应该使用成分名称，而不是含量
                generic_name = knowledge.get("component", name)
                
                # 如果兑水量为空，显示提示
                if not water:
                    water = "详见说明书"
                
                drug = DrugInfo(
                    id=f"B{int(row['序号'])}",
                    name=name,
                    content=generic_name,
                    spec=spec,
                    water=water,
                    price=price,
                    indications=knowledge.get("indications", []),
                    main_component=knowledge.get("component", name),
                    category="化药",
                    egg_period_safe=knowledge.get("egg_safe", True),
                    disease_types=knowledge.get("types", ["MIXED"]),
                    usage_info=knowledge.get("usage", "详见说明书"),
                    source="底价目录",
                    timing=knowledge.get("timing", "发病期间治疗使用"),
                    brand_name=name,
                    product_name=name
                )
                self.drugs.append(drug)
    
    def _load_info_products(self, excel_file):
        """加载产品信息_华英（包含明星产品信息）"""
        df = pd.read_excel(excel_file, sheet_name='产品信息_华英')
        
        # 明星产品知识库 - 用于识别和增强明星产品信息
        star_knowledge = {
            "浆小白": {"component": "中药提取物", "indications": ["水禽浆膜炎", "大肠杆菌病", "沙门氏菌病"], "types": ["BACTERIAL", "RESPIRATORY"], "egg_safe": True, "category": "中药", "timing": "发病期间治疗使用", "usage": "混饮：每袋兑水1000斤，连用3-5日"},
            "浆小白（清解合剂）": {"component": "中药提取物", "indications": ["肺部发黑", "肺部淤血", "支气管栓塞", "怪叫", "呼噜", "伸颈喘", "气管透明", "喉头出血"], "types": ["RESPIRATORY"], "egg_safe": True, "category": "中药", "timing": "发病期间治疗使用", "usage": "混饮：每瓶兑水400斤，饮用6-8小时，连用4天"},
            "控孤": {"component": "混合型饲料添加剂L-抗坏血酸", "indications": ["弧菌感染", "肠道疾病", "免疫增强"], "types": ["BACTERIAL", "DIGESTIVE"], "egg_safe": True, "category": "饲料添加剂", "timing": "发病期间治疗使用", "usage": "混饮：每袋兑水2000斤，连用3-5日"},
            "抚风": {"component": "混合型饲料添加剂牛磺酸", "indications": ["抗应激", "保肝护肾", "提高免疫力"], "types": ["MIXED"], "egg_safe": True, "category": "饲料添加剂", "timing": "日常保健使用", "usage": "混饮：每袋兑水2000斤，连用5-7日"},
            "海健素": {"component": "黄芪多糖口服液(β防御素、干扰素β、γ）", "indications": ["维生素缺乏", "营养补充", "抗应激"], "types": ["NUTRITIONAL"], "egg_safe": True, "category": "维生素", "timing": "日常保健使用", "usage": "混饮：每袋兑水2000斤，连用5-7日"},
            "金舒利": {"component": "混合型饲料添加剂 牛磺酸", "indications": ["退烧", "抗炎", "增料", "抗病毒"], "types": ["NUTRITIONAL", "MIXED"], "egg_safe": True, "category": "饲料添加剂", "timing": "增免抗病毒类产品", "usage": "本品兑水使用，全天量集中饮用7-8小时，连用3-5天"},
            "严立康": {"component": "盐酸大观霉素盐酸林可霉素可溶性粉", "indications": ["肠道菌群失调", "腹泻", "消化不良"], "types": ["DIGESTIVE"], "egg_safe": False, "category": "微生态", "timing": "日常保健使用", "usage": "混饮：每袋兑水2000斤，连用5-7日"},
            "超吉拍档": {"component": "盐酸大观霉素盐酸林可霉素可溶性粉", "indications": ["促进消化", "提高饲料利用率", "肠道健康"], "types": ["NUTRITIONAL", "DIGESTIVE"], "egg_safe": False, "category": "酶制剂", "timing": "日常保健使用", "usage": "混饲：每袋拌料1000斤，连用5-7日"},
            "新达罗": {"component": "硫酸庆大霉素可溶性粉", "indications": ["细菌感染", "呼吸道感染", "肠道感染"], "types": ["BACTERIAL", "RESPIRATORY", "DIGESTIVE"], "egg_safe": False, "category": "抗生素", "timing": "发病期间治疗使用", "usage": "混饮：每袋兑水1000斤，连用3-5日"},
            "菲清": {"component": "液态甘草鱼腥草粗提物(复配型)", "indications": ["清肺止咳", "呼吸道感染", "痰多"], "types": ["RESPIRATORY"], "egg_safe": True, "category": "中药", "timing": "发病期间治疗使用", "usage": "混饮：每瓶兑水2000斤，连用3-5日"},
            "热感清": {"component": "鱼腥草提取液", "indications": ["退热", "感冒", "发热"], "types": ["MIXED", "VIRAL"], "egg_safe": True, "category": "中药", "timing": "增免抗病毒类产品", "usage": "全天量集中饮用4-5小时，连用3天"},
            "肽芪剑（蛋鸡）": {"component": "液态低聚壳聚糖", "indications": ["免疫增强", "抗病毒", "提高产蛋率"], "types": ["VIRAL", "MIXED"], "egg_safe": True, "category": "免疫增强剂", "timing": "日常保健使用", "usage": "混饮：每袋兑水2000斤，连用5-7日"},
            "卡迪欧": {"component": "鸡传染性法氏囊病精制蛋黄抗体", "indications": ["退热", "止痛", "消炎"], "types": ["MIXED"], "egg_safe": True, "category": "解热镇痛", "timing": "发热时使用", "usage": "混饮使用，连用3日"},
            "甘舒乐": {"component": "甘露寡糖", "indications": ["保肝护肾", "解毒", "抗应激"], "types": ["NUTRITIONAL", "MIXED"], "egg_safe": True, "category": "中药", "timing": "日常保健使用", "usage": "混饮：每袋兑水2000斤，连用5-7日"},
            "温炎消": {"component": "混合型饲料添加剂液态牛磺酸", "indications": ["消炎", "肠道疾病", "腹泻"], "types": ["DIGESTIVE", "BACTERIAL"], "egg_safe": True, "category": "中药", "timing": "发病期间治疗使用", "usage": "混饮：每袋兑水1000斤，连用3-5日"},
            "双胃康": {"component": "液态苍术木香粗提物(复配型)", "indications": ["腺胃炎", "肌胃炎", "消化不良"], "types": ["DIGESTIVE"], "egg_safe": True, "category": "中药", "timing": "发病期间治疗使用", "usage": "混饮：每袋兑水1000斤，连用3-5日"},
            "羡康": {"component": "天然植物饲料原料、干姜粗提物", "indications": ["腺胃炎", "肌胃炎", "采食量低", "鸡大小不均"], "types": ["DIGESTIVE"], "egg_safe": True, "category": "腺胃炎产品", "timing": "发病期间治疗使用", "usage": "混饮使用，连用3-5日"},
            "畅健": {"component": "混合型饲料添加剂液态甘露寡糖", "indications": ["肠道健康", "腹泻", "消化不良"], "types": ["DIGESTIVE"], "egg_safe": True, "category": "中药", "timing": "发病期间治疗使用", "usage": "混饮：每袋兑水1000斤，连用3-5日"},
            "卵舒康": {"component": "中药提取物", "indications": ["输卵管炎", "卵巢炎", "产蛋下降", "血斑蛋", "沙壳蛋", "畸形蛋"], "types": ["REPRODUCTIVE", "BACTERIAL"], "egg_safe": True, "category": "中药", "timing": "发病期间治疗使用", "usage": "混饮：每袋兑水1000斤，连用3-5日"},
        }
        
        # 明星产品商品名列表（用于识别）
        star_brand_names = [
            "浆小白", "控孤", "抚风", "海健素", "金舒利", "严立康", 
            "超吉拍档", "新达罗", "菲清", "热感清", "肽芪剑", 
            "卡迪欧", "甘舒乐", "温炎消", "双胃康", "羡康", 
            "畅健", "卵舒康"
        ]
        
        # 产蛋期禁用药物清单（根据GB 31650-2019和兽药质量标准）
        egg_unsafe_products = [
            # 氨基糖苷类
            "硫酸庆大霉素可溶性粉", "盐酸大观霉素可溶性粉", "盐酸大观霉素盐酸林可霉素可溶性粉",
            "硫酸新霉素可溶性粉", "硫酸安普霉素可溶性粉", "单硫酸卡那霉素可溶性粉",
            # 林可胺类
            "盐酸林可霉素可溶性粉",
            # 四环素类
            "盐酸多西环素可溶性粉", "10%盐酸多西环素可溶性粉", "盐酸金霉素可溶性粉",
            # 大环内酯类
            "替米考星溶液", "替米考星预混剂", "酒石酸泰万菌素预混剂", "20%酒石酸泰万菌素预混剂",
            "80%延胡索酸泰妙菌素",
            # 酰胺醇类
            "氟苯尼考粉", "30%氟苯尼考可溶性粉", "10%氟苯尼考溶液",
            # β-内酰胺类
            "阿莫西林可溶性粉", "10%阿莫西林可溶性粉", "复方阿莫西林粉",
            # 喹诺酮类
            "盐酸恩诺沙星可溶性粉", "恩诺沙星溶液", "5%盐酸沙拉沙星溶液",
            # 头孢类
            "硫酸头孢喹肟注射液",
            # 磺胺类
            "复方磺胺间甲氧嘧啶钠可溶性粉", "磺胺喹噁啉钠可溶性粉", "磺胺氯吡嗪钠可溶性粉",
            # 其他
            "卡巴匹林钙粉", "硫酸黏菌素预混剂", "地美硝唑预混剂",
            "地克珠利预混剂", "地克珠利溶液",
            # 明星产品中的禁用药物（商品名）
            "严立康", "超吉拍档", "新达罗", "杆福",
        ]
        
        # 补充匹配规则：通过活性成分判断
        egg_unsafe_ingredients = [
            "庆大霉素", "大观霉素", "林可霉素", "新霉素", "安普霉素", "卡那霉素",
            "多西环素", "金霉素", "替米考星", "泰万菌素", "泰妙菌素",
            "氟苯尼考", "阿莫西林", "恩诺沙星", "沙拉沙星", "头孢喹肟",
            "磺胺间甲氧嘧啶", "磺胺喹噁啉", "磺胺氯吡嗪",
            "卡巴匹林钙", "黏菌素", "地美硝唑", "地克珠利"
        ]
        
        def is_star_product(brand_name, product_name):
            """判断是否为明星产品"""
            name_to_check = brand_name if brand_name and brand_name != "/" else product_name
            if not name_to_check:
                return False, None
            
            for star_name in star_brand_names:
                if star_name in name_to_check:
                    return True, star_name
            return False, None
        
        for idx, row in df.iterrows():
            if pd.notna(row['产品名称']) and row['产品名称'] != '/':
                name = str(row['产品名称'])
                category = str(row['类别']) if pd.notna(row['类别']) else "其他"
                
                # 获取商品名
                brand_name = str(row['商品名']) if pd.notna(row['商品名']) else ""
                if not brand_name or brand_name == "/":
                    brand_name = name
                
                # 判断是否为明星产品
                is_star, star_key = is_star_product(brand_name, name)
                
                # 获取明星产品知识库数据（如果是明星产品）
                star_data = star_knowledge.get(star_key, {}) if is_star else {}
                
                # 根据禁用清单判断产蛋期安全性（双重检查：产品名称 + 活性成分）
                egg_safe = True  # 默认安全
                
                # 第一重：检查产品名称是否匹配禁用清单
                for unsafe_name in egg_unsafe_products:
                    if unsafe_name in name or name in unsafe_name:
                        egg_safe = False
                        break
                
                # 第二重：如果产品名称未匹配，检查成分是否包含禁用活性成分
                if egg_safe:
                    component = str(row['成分']) if pd.notna(row.get('成分')) else ""
                    for unsafe_ingredient in egg_unsafe_ingredients:
                        if unsafe_ingredient in component:
                            egg_safe = False
                            break
                
                # 如果是明星产品，使用知识库中的产蛋期安全性
                if is_star and "egg_safe" in star_data:
                    egg_safe = star_data["egg_safe"]
                
                # 根据类别判断疾病类型（如果是明星产品，优先使用知识库）
                if is_star and "types" in star_data:
                    disease_types = star_data["types"]
                elif category == '抗生素':
                    disease_types = ["BACTERIAL"]
                elif category == '中药':
                    disease_types = ["VIRAL", "MIXED"]
                elif category == '呼吸道':
                    disease_types = ["RESPIRATORY"]
                elif category == '肠道':
                    disease_types = ["DIGESTIVE"]
                elif category == '抗寄生虫':
                    disease_types = ["PARASITIC"]
                else:
                    disease_types = ["MIXED"]
                
                # 获取适应症（如果是明星产品，优先使用知识库）
                if is_star and "indications" in star_data:
                    indications = star_data["indications"]
                else:
                    indications_str = str(row['适应症状或产品功效']) if pd.notna(row['适应症状或产品功效']) else ""
                    indications = [i.strip() for i in indications_str.split('、')] if indications_str else ["详见产品说明"]
                
                # 获取兑水量，如果为空则显示提示
                water_amount = str(row['兑水量']) if pd.notna(row['兑水量']) else ""
                if not water_amount or water_amount == "/":
                    water_amount = "详见说明书"
                
                # 获取时机（处理列名中的不间断空格）
                timing = "/"
                for col in df.columns:
                    if '时机' in str(col) or ('时' in str(col) and '机' in str(col)):
                        if pd.notna(row[col]):
                            timing = str(row[col])
                            break
                
                # 如果是明星产品，优先使用知识库中的时机
                if is_star and "timing" in star_data:
                    timing = star_data["timing"]
                
                # 获取价格（产品信息_华英的价格更准确，处理列名中的不间断空格）
                price = 0
                for col in df.columns:
                    if '价' in str(col) or '价格' in str(col):
                        price = self._parse_price(row[col])
                        break
                
                # 获取用法用量（如果是明星产品，优先使用知识库）
                if is_star and "usage" in star_data:
                    usage_info = star_data["usage"]
                else:
                    usage_info = str(row['用法用量']) if pd.notna(row['用法用量']) else ""
                
                # 获取主要成分（如果是明星产品，优先使用知识库）
                if is_star and "component" in star_data:
                    main_component = star_data["component"]
                else:
                    main_component = str(row['成分']) if pd.notna(row.get('成分')) else name
                
                # 获取类别（如果是明星产品，优先使用知识库）
                if is_star and "category" in star_data:
                    product_category = star_data["category"]
                else:
                    product_category = category
                
                # 检查产品是否已存在（从底价目录加载的）
                # 使用产品名称+商品名+规格来唯一标识产品，支持同一产品名称的不同规格
                existing_drug = None
                for drug in self.drugs:
                    if drug.name == name and drug.brand_name == brand_name:
                        existing_drug = drug
                        break
                
                if existing_drug:
                    # 产品已存在，跳过以保持分类独立性
                    continue
                else:
                    # 添加新产品
                    # 如果是明星产品，标记source为"明星产品"，否则为"产品信息_华英"
                    source = "明星产品" if is_star else "产品信息_华英"
                    
                    drug = DrugInfo(
                        id=f"{'S' if is_star else 'H'}{idx+1}",
                        name=name,
                        content=brand_name,
                        spec=str(row['包装规格']) if pd.notna(row['包装规格']) else "",
                        water=water_amount,
                        price=price,
                        indications=indications,
                        main_component=main_component,
                        category=product_category,
                        egg_period_safe=egg_safe,
                        disease_types=disease_types,
                        usage_info=usage_info,
                        source=source,
                        timing=timing,
                        brand_name=brand_name,
                        product_name=name
                    )
                    self.drugs.append(drug)
    
    def get_drug_by_name(self, name: str) -> Optional[DrugInfo]:
        """根据名称获取药物（支持 product_name / content / name / brand_name 匹配）"""
        for drug in self.drugs:
            if _drug_name_matches(drug, name):
                return drug
        return None
    
    def get_all_drugs(self) -> List[DrugInfo]:
        """获取所有药物"""
        return self.drugs
    
    def get_drugs_by_category(self, category: str) -> List[DrugInfo]:
        """根据类别获取药物"""
        return [d for d in self.drugs if d.category == category]


class SymptomDiseaseMapper:
    """症状-疾病映射器"""
    
    def __init__(self):
        self.symptom_disease_map = {
            # 呼吸道症状
            "咳嗽": {"diseases": ["慢性呼吸道病", "传染性支气管炎", "传染性喉气管炎"], "type": "RESPIRATORY"},
            "打喷嚏": {"diseases": ["慢性呼吸道病", "传染性鼻炎"], "type": "RESPIRATORY"},
            "流鼻涕": {"diseases": ["传染性鼻炎", "慢性呼吸道病"], "type": "RESPIRATORY"},
            "呼吸困难": {"diseases": ["传染性喉气管炎", "新城疫", "传染性支气管炎"], "type": "RESPIRATORY"},
            "啰音": {"diseases": ["慢性呼吸道病", "传染性支气管炎"], "type": "RESPIRATORY"},
            "喘": {"diseases": ["慢性呼吸道病", "传染性支气管炎"], "type": "RESPIRATORY"},
            "呼吸": {"diseases": ["慢性呼吸道病", "传染性支气管炎"], "type": "RESPIRATORY"},
            
            # 消化道症状
            "拉稀": {"diseases": ["大肠杆菌病", "沙门氏菌病", "球虫病", "坏死性肠炎"], "type": "DIGESTIVE"},
            "腹泻": {"diseases": ["大肠杆菌病", "沙门氏菌病", "球虫病", "坏死性肠炎"], "type": "DIGESTIVE"},
            "血便": {"diseases": ["球虫病", "坏死性肠炎"], "type": "DIGESTIVE"},
            "绿色粪便": {"diseases": ["新城疫", "禽霍乱", "传染性支气管炎"], "type": "DIGESTIVE"},
            "白色粪便": {"diseases": ["鸡白痢", "传染性法氏囊病", "痛风"], "type": "DIGESTIVE"},
            "食欲不振": {"diseases": ["大肠杆菌病", "沙门氏菌病", "禽霍乱", "球虫病"], "type": "DIGESTIVE"},
            "不吃": {"diseases": ["大肠杆菌病", "沙门氏菌病", "禽霍乱", "球虫病"], "type": "DIGESTIVE"},
            "肠炎": {"diseases": ["坏死性肠炎", "大肠杆菌病"], "type": "DIGESTIVE"},
            "肠道": {"diseases": ["大肠杆菌病", "沙门氏菌病", "坏死性肠炎"], "type": "DIGESTIVE"},
            
            # 全身症状
            "精神沉郁": {"diseases": ["新城疫", "禽霍乱", "大肠杆菌病", "沙门氏菌病"], "type": "MIXED"},
            "羽毛松乱": {"diseases": ["新城疫", "禽霍乱", "球虫病"], "type": "MIXED"},
            "掉毛厉害": {"diseases": ["蛔虫病", "绦虫病", "滑液囊支原体", "营养代谢病"], "type": "PARASITIC"},
            "掉毛": {"diseases": ["蛔虫病", "绦虫病", "滑液囊支原体", "营养代谢病"], "type": "PARASITIC"},
            "脱毛": {"diseases": ["蛔虫病", "绦虫病", "滑液囊支原体", "营养代谢病"], "type": "PARASITIC"},
            "缩颈闭眼": {"diseases": ["新城疫", "禽霍乱", "大肠杆菌病"], "type": "MIXED"},
            "发热": {"diseases": ["禽霍乱", "大肠杆菌病", "新城疫"], "type": "MIXED"},
            "发烧": {"diseases": ["禽霍乱", "大肠杆菌病", "新城疫"], "type": "MIXED"},
            
            # 寄生虫症状
            "消瘦": {"diseases": ["球虫病", "蛔虫病", "绦虫病", "组织滴虫病"], "type": "PARASITIC"},
            "贫血": {"diseases": ["球虫病", "组织滴虫病", "住白细胞虫病"], "type": "PARASITIC"},
            
            # 特定疾病 - 球虫病
            "球虫": {"diseases": ["球虫病"], "type": "PARASITIC"},
            "盲肠球虫": {"diseases": ["盲肠球虫"], "type": "PARASITIC"},
            "小肠球虫": {"diseases": ["小肠球虫"], "type": "PARASITIC"},
            
            # 特定疾病 - 细菌性疾病
            "大肠杆菌": {"diseases": ["大肠杆菌病"], "type": "BACTERIAL"},
            "沙门氏菌": {"diseases": ["沙门氏菌病", "鸡白痢", "禽伤寒"], "type": "BACTERIAL"},
            "白痢": {"diseases": ["鸡白痢"], "type": "BACTERIAL"},
            "霍乱": {"diseases": ["禽霍乱"], "type": "BACTERIAL"},
            "伤寒": {"diseases": ["禽伤寒"], "type": "BACTERIAL"},
            
            # 特定疾病 - 呼吸道疾病
            "支原体": {"diseases": ["慢性呼吸道病", "滑液囊支原体"], "type": "RESPIRATORY"},
            "慢呼": {"diseases": ["慢性呼吸道病"], "type": "RESPIRATORY"},
            
            # 特定疾病 - 其他
            "鼻炎": {"diseases": ["传染性鼻炎"], "type": "RESPIRATORY"},
            "组织滴虫": {"diseases": ["组织滴虫病"], "type": "PARASITIC"},
            "黑头病": {"diseases": ["组织滴虫病"], "type": "PARASITIC"},
            "流感": {"diseases": ["禽流感", "新城疫"], "type": "VIRAL"},
            "病毒": {"diseases": ["新城疫", "传染性支气管炎"], "type": "VIRAL"},
            
            # 生殖系统疾病
            "输卵管炎": {"diseases": ["输卵管炎", "卵巢炎"], "type": "REPRODUCTIVE"},
            "卵巢炎": {"diseases": ["卵巢炎", "输卵管炎"], "type": "REPRODUCTIVE"},
            "产蛋下降": {"diseases": ["输卵管炎", "卵巢炎", "新城疫", "禽流感"], "type": "REPRODUCTIVE"},
            "畸形蛋": {"diseases": ["输卵管炎", "卵巢炎"], "type": "REPRODUCTIVE"},
            "沙壳蛋": {"diseases": ["输卵管炎", "卵巢炎"], "type": "REPRODUCTIVE"},
            "血斑蛋": {"diseases": ["输卵管炎", "卵巢炎"], "type": "REPRODUCTIVE"},
        }
    
    def get_diseases_by_symptom(self, symptom: str) -> Dict:
        """根据症状获取可能的疾病"""
        symptom_lower = symptom.lower()
        for key, value in self.symptom_disease_map.items():
            if key in symptom_lower or symptom_lower in key:
                return value
        return {"diseases": [symptom], "type": "MIXED"}


# ===================== 药物类型分类与组合合规校验 =====================

# 化药类类别关键词（命中任一即判定为"化药"）
CHEMICAL_DRUG_CATEGORIES = {
    "化药", "抗生素", "抗支原体药", "抗球虫类",
    "驱霉菌类产品", "消毒剂类", "解热镇痛",
}

# 化药成分关键词（用于"明星产品"等仅凭类别无法判断时的兜底识别）
CHEMICAL_COMPONENT_KEYWORDS = [
    "氟苯尼考", "多西环素", "卡巴匹林", "阿莫西林", "黏菌素",
    "新霉素", "恩诺沙星", "庆大霉素", "林可霉素", "地美硝唑",
    "卡那霉素", "替米考星", "安普霉素", "磺胺", "泰万菌素",
    "泰妙菌素", "大观霉素", "土霉素", "金霉素", "头孢",
    "喹诺酮", "红霉素", "青霉素", "链霉素", "壮观霉素",
]

# 交叉耐药性分组（同类化药易产生交叉耐药，历史用药命中某一类后，推荐时应避免同类药物）
CROSS_RESISTANCE_GROUPS = {
    "四环素类": ["多西环素", "金霉素", "土霉素", "四环素", "米诺环素"],
    "大环内酯类": ["替米考星", "泰万菌素", "泰乐菌素", "红霉素", "吉他霉素", "螺旋霉素", "阿奇霉素"],
    "截短侧耳素/林可胺类": ["泰妙菌素", "沃尼妙林", "林可霉素", "克林霉素"],
    "氟喹诺酮类": ["恩诺沙星", "沙拉沙星", "环丙沙星", "达氟沙星", "氧氟沙星", "诺氟沙星", "培氟沙星"],
    "氨基糖苷类": ["庆大霉素", "新霉素", "安普霉素", "卡那霉素", "大观霉素", "阿米卡星", "链霉素", "壮观霉素"],
    "β-内酰胺类": ["阿莫西林", "青霉素", "氨苄西林", "头孢", "头孢喹肟", "苯唑西林"],
    "酰胺醇类": ["氟苯尼考", "甲砜霉素", "氯霉素"],
    "磺胺类": ["磺胺", "磺胺间甲氧嘧啶", "磺胺喹噁啉", "磺胺氯吡嗪", "甲氧苄啶"],
    "多肽类": ["黏菌素", "多黏菌素", "杆菌肽"],
    "硝基咪唑类": ["地美硝唑", "甲硝唑", "替硝唑", "奥硝唑"],
    "解热镇痛类": ["卡巴匹林", "阿司匹林", "扑热息痛", "对乙酰氨基酚", "布洛芬", "氟尼辛"],
}


def _get_resistance_groups(component: str) -> List[str]:
    """根据药物成分判断其所属的交叉耐药类别"""
    if not component:
        return []
    groups = []
    for group_name, keywords in CROSS_RESISTANCE_GROUPS.items():
        for kw in keywords:
            if kw in component:
                groups.append(group_name)
                break
    return groups


def _drug_name_matches(drug: DrugInfo, query: str) -> bool:
    """检查药物名称是否与查询字符串匹配，支持 name / brand_name / product_name / content 多个字段"""
    if not query or not str(query).strip():
        return False
    q = str(query).strip()
    for field in (drug.name, drug.brand_name, drug.product_name, drug.content):
        if field and str(field).strip():
            f = str(field).strip()
            if f == q or q in f or f in q:
                return True
    return False


def _get_history_excluded_drugs(history: List[str], all_drugs: List[DrugInfo]) -> set:
    """根据历史用药记录，计算需要避免重复或交叉耐药的药物名称集合

    规则：
      1. 历史用药本身一定排除；
      2. 化药若与历史用药属于同一交叉耐药类别，则排除；
      3. 中兽药/保健类产品仅排除与历史用药名称完全相同的品种。
    """
    excluded = set()
    if not history:
        return excluded

    history_names = set(h.strip() for h in history if h and str(h).strip())
    excluded.update(history_names)

    # 收集历史用药涉及的所有耐药类别（仅化药）
    affected_groups = set()
    for hist_name in history_names:
        # 尝试在数据库中匹配完整药物
        matched = None
        for d in all_drugs:
            if _drug_name_matches(d, hist_name):
                matched = d
                break
        if matched:
            if classify_drug_type(matched) == "化药":
                affected_groups.update(_get_resistance_groups(matched.main_component))
                affected_groups.update(_get_resistance_groups(matched.name))
        else:
            # 未匹配到产品时，把历史用药名称本身当作自由文本进行类别关键词匹配
            affected_groups.update(_get_resistance_groups(hist_name))

    if not affected_groups:
        # 没有命中耐药类别时，仅做精确名称排除
        return excluded

    # 再次遍历所有药物，排除同类化药
    for d in all_drugs:
        if d.name in excluded or (d.brand_name and d.brand_name in excluded):
            continue
        if classify_drug_type(d) != "化药":
            continue
        drug_groups = set(_get_resistance_groups(d.main_component) + _get_resistance_groups(d.name))
        if drug_groups & affected_groups:
            excluded.add(d.name)
            if d.brand_name:
                excluded.add(d.brand_name)

    return excluded


def _get_drug_resistance_groups(drug: DrugInfo) -> List[str]:
    """获取药物涉及的所有交叉耐药类别"""
    if not drug:
        return []
    return list(set(_get_resistance_groups(drug.main_component) + _get_resistance_groups(drug.name)))


def _analyze_low_resistance(drug_details: List[Dict]) -> Dict:
    """分析组合方案的耐药风险并给出低耐药说明

    返回字段：
      - risk_level: "低" / "中" / "高"
      - same_class_chemicals: 同类别化药名称列表
      - mechanism_groups: 所有化药作用机制类别列表
      - has_tcm: 是否包含中兽药
      - description: 面向用户的低耐药分析文案
    """
    chemicals = [d for d in drug_details if d.get("drug_type") == "化药"]
    tcm_count = sum(1 for d in drug_details if d.get("drug_type") == "中兽药")

    group_to_drugs: Dict[str, List[str]] = {}
    for d in chemicals:
        name = d.get("name", "")
        groups = list(set(_get_resistance_groups(d.get("component", "")) + _get_resistance_groups(name)))
        for g in groups:
            group_to_drugs.setdefault(g, []).append(name)

    same_class_drugs = []
    seen_names = set()
    for g, names in group_to_drugs.items():
        if len(names) >= 2:
            for n in names:
                if n not in seen_names:
                    same_class_drugs.append(n)
                    seen_names.add(n)

    mechanism_groups = sorted(group_to_drugs.keys())
    has_tcm = tcm_count > 0

    if same_class_drugs:
        risk_level = "高"
    elif len(chemicals) >= 2 and len(mechanism_groups) >= 2:
        risk_level = "低"
    elif len(chemicals) == 1 and has_tcm:
        risk_level = "低"
    elif len(chemicals) == 0 and has_tcm:
        risk_level = "低"
    else:
        risk_level = "中"

    # 生成文案
    drug_names = [d.get("name", "") for d in drug_details if d.get("name")]
    if risk_level == "低":
        if len(chemicals) >= 2 and len(mechanism_groups) >= 2:
            desc = (
                f"{'、'.join(drug_names)} 采用不同作用机制的化药搭配（{ '、'.join(mechanism_groups) }），"
                f"可通过多靶点杀菌显著降低耐药菌存活概率；同时包含中兽药/保健类产品，可调理机体、减少化药用量，"
                f"从而延缓耐药性产生。"
            )
        elif len(chemicals) == 1 and has_tcm:
            desc = (
                f"{'、'.join(drug_names)} 采用“1种化药 + 中兽药/保健”模式：化药快速控制病原，"
                f"中兽药调理机体、增强免疫力；中兽药作用靶点多、不易耐药，可辅助减少化药使用强度，"
                f"整体耐药风险较低。"
            )
        elif len(chemicals) == 0 and has_tcm:
            desc = (
                f"{'、'.join(drug_names)} 均为中兽药/保健类产品，作用靶点多元，天然不易产生耐药性，"
                f"适合用于预防、调理及产蛋期安全用药。"
            )
        else:
            desc = "本方案药物作用机制互补，联合使用可降低耐药菌被筛选出来的风险。"
    elif risk_level == "高":
        desc = (
            f"⚠️ 本方案中包含同类别化药（{ '、'.join(same_class_drugs) }），作用机制相近，"
            f"容易交叉耐药。建议优先选择不同作用机制的药物搭配，或增加中兽药辅助，"
            f"以降低耐药风险。"
        )
    else:
        if has_tcm:
            desc = "本方案含中兽药辅助，可在一定程度上降低耐药风险；建议足量足疗程使用并定期轮换。"
        else:
            desc = "本方案以化药为主，按推荐剂量和疗程规范使用，并注意后续轮换用药以延缓耐药。"

    return {
        "risk_level": risk_level,
        "same_class_chemicals": same_class_drugs,
        "mechanism_groups": mechanism_groups,
        "has_tcm": has_tcm,
        "description": desc,
    }


def _generate_resistance_prevention_guide(disease_type: str, has_chemical: bool) -> str:
    """根据疾病类型和是否含化药生成耐药预防操作指导"""
    guides = []

    if has_chemical:
        guides.append(
            "**严格足量足疗程**：细菌感染常规疗程 3～5 天，抗病毒化药/提取物需按完整周期使用，"
            "即使症状当天好转也必须用完规定天数，杜绝残留活菌变异。"
        )
        guides.append(
            "**轮换用药制度**：同一种抗菌化药连续治疗不超过 2 批家禽，下一批换用不同作用机制的药物；"
            "例如本批大肠杆菌用氟苯尼考，下批可换头孢类或恩诺沙星。"
        )
        guides.append(
            "**联合用药降低耐药概率**：两种不同机理药物搭配可双重杀菌，大幅降低耐药菌存活概率；"
            "但必须遵守兽药配伍禁忌。"
        )

    if disease_type == "VIRAL":
        guides.append(
            "**抗病毒药不宜单一长期使用**：病毒变异快，频繁单一用药 3～4 次流行周期后可能出现毒株耐药，"
            "建议不同抗病毒机制药物轮换或与中药免疫增强剂搭配。"
        )
    elif disease_type == "PARASITIC":
        guides.append(
            "**驱虫药定期轮换**：球虫药、驱虫药全年只用同一款，半年～1 年药效会明显下降，"
            "建议不同作用机制产品轮换使用。"
        )

    return "\n\n".join(guides)


def classify_drug_type(drug: "DrugInfo") -> str:
    """根据药物的类别与成分判定其类型

    返回值: "化药" 或 "中兽药"
    判定规则:
      1. 类别属于 CHEMICAL_DRUG_CATEGORIES -> 化药
      2. 类别为"明星产品"时，按主成分关键词判断（命中化药关键词 -> 化药，否则 -> 中兽药）
      3. 其他类别（中药、抗病毒类产品、气管栓塞呼吸道药、营养类、免疫增强剂、微生态、
         酶制剂、维生素、饲料添加剂、保肝类护肾类、腺胃炎产品、气囊炎类产品、
         肠道类产品、特色类产品、增蛋类产品、抗体类产品、防暑降温类产品、营养增料促生长）
         一律判定为中兽药
    """
    category = (drug.category or "").strip()

    if category in CHEMICAL_DRUG_CATEGORIES:
        return "化药"

    # 明星产品需要按成分细分
    if category == "明星产品":
        comp = drug.main_component or ""
        for kw in CHEMICAL_COMPONENT_KEYWORDS:
            if kw in comp:
                return "化药"
        return "中兽药"

    # 其他类别默认为中兽药
    return "中兽药"


def validate_combination_compliance(drugs: List["DrugInfo"]) -> Dict:
    """校验一组药物的类型搭配是否符合业务规则

    规则:
      - 化药 + 中兽药 -> 合规
      - 中兽药 + 中兽药 -> 合规
      - 化药 + 化药 -> 不合规（被禁用）
    返回: dict(compliant, reason, types, chem_count, tcm_count, type_set)
    """
    if not drugs:
        return {
            "compliant": False,
            "reason": "组合为空，无法校验",
            "types": [],
            "type_set": [],
            "chem_count": 0,
            "tcm_count": 0,
        }

    types = [classify_drug_type(d) for d in drugs]
    chem_count = types.count("化药")
    tcm_count = types.count("中兽药")
    type_set = sorted(set(types))

    # 全为化药 -> 不合规
    if chem_count > 0 and tcm_count == 0:
        names = "、".join(d.name for d in drugs)
        return {
            "compliant": False,
            "reason": (
                f"组合中全部为化药产品（{names}），违反业务规则。"
                "必须采用『化药+中兽药』或『中兽药+中兽药』的组合搭配。"
            ),
            "types": types,
            "type_set": type_set,
            "chem_count": chem_count,
            "tcm_count": tcm_count,
        }

    return {
        "compliant": True,
        "reason": "符合业务规则",
        "types": types,
        "type_set": type_set,
        "chem_count": chem_count,
        "tcm_count": tcm_count,
    }


def _has_matching_indication(drug: "DrugInfo", diseases: List[str]) -> bool:
    """检查药物是否有适应症与目标疾病明确匹配

    这是化药展示的核心门槛：化药必须至少有一项适应症与当前病症直接相关。
    """
    if not drug.indications or not diseases:
        return False
    for indication in drug.indications:
        for disease in diseases:
            if disease in indication or indication in disease:
                return True
    return False


def _has_effective_chemical_drug(db: "DrugDatabase", diseases: List[str],
                                 request: RecommendationRequest) -> bool:
    """判断当前病症是否存在具备明确适应症的有效化药产品"""
    for d in db.get_all_drugs():
        if request.egg_period_safe and not d.egg_period_safe:
            continue
        if classify_drug_type(d) != "化药":
            continue
        if not _has_matching_indication(d, diseases):
            continue
        return True
    return False


def _find_tcm_substitute(db: "DrugDatabase", original_drug: "DrugInfo",
                         disease_type: str, used_names: set) -> Optional["DrugInfo"]:
    """为化药寻找一个合适的中兽药替代品

    优先级:
      1. 同疾病类型且类别为中兽药的药物
      2. 主成分含"中药/植物/口服液"等字样的明星产品
      3. 任意蛋鸡产蛋期可用的中兽药
    """
    all_drugs = db.get_all_drugs()
    candidates: List["DrugInfo"] = []

    for d in all_drugs:
        # 跳过名称异常的数据记录
        if not d.name or d.name.strip() in ("", "/"):
            continue
        if d.name in used_names:
            continue
        if d.name == original_drug.name:
            continue
        if classify_drug_type(d) != "中兽药":
            continue
        candidates.append(d)

    # 优先级1：疾病类型匹配
    for d in candidates:
        if disease_type in (d.disease_types or []):
            return d

    # 优先级2：含"中药/植物/口服液"等关键词的明星/中兽药产品
    name_kw = ["中药", "植物", "口服液", "合剂", "清解", "粗提物"]
    for d in candidates:
        comp = d.main_component or ""
        for kw in name_kw:
            if kw in comp or kw in d.name:
                return d

    # 优先级3：任何可用的中兽药
    for d in candidates:
        return d

    return None


def _find_chemical_drug(db: "DrugDatabase", disease_type: str, diseases: List[str],
                        used_names: set, egg_period_safe: bool = False,
                        excluded_drugs: List[str] = None) -> Optional["DrugInfo"]:
    """为中兽药组合寻找一个具备明确适应症的化药产品

    核心约束: 返回的化药必须至少有一项适应症与当前病症明确匹配，
    不允许以"广谱抗菌"等理由引入无治疗依据的化药。

    优先级:
      1. 疾病类型匹配且适应症明确匹配的化药
      2. 适应症明确匹配的化药
    """
    all_drugs = db.get_all_drugs()
    excluded_set = set(excluded_drugs) if excluded_drugs else set()
    candidates: List["DrugInfo"] = []

    for d in all_drugs:
        if d.name in used_names:
            continue
        if d.name in excluded_set or d.brand_name in excluded_set:
            continue
        if classify_drug_type(d) != "化药":
            continue
        if egg_period_safe and not d.egg_period_safe:
            continue
        # 核心门槛：必须有明确适应症匹配
        if not _has_matching_indication(d, diseases):
            continue
        candidates.append(d)

    # 优先级1：疾病类型匹配且适应症匹配
    for d in candidates:
        if disease_type in (d.disease_types or []):
            return d

    # 优先级2：适应症匹配的化药
    for d in candidates:
        return d

    return None


# ===================== 推荐理由详情生成（通俗化、结构化） =====================

def _plain_indications_text(indications: List[str], max_items: int = 3) -> str:
    """将适应症列表转换为通俗语言描述，避免术语堆砌"""
    if not indications:
        return "相关症状"
    items = [i.strip() for i in indications if str(i).strip()][:max_items]
    return "、".join(items)


def _generate_single_drug_reason(drug: DrugInfo, diseases: List[str],
                                 match_score: float,
                                 dosage_recommendation: str) -> DrugRecommendationReason:
    """生成单个药品的详细推荐理由（基于产品说明书及临床信息）"""
    reason = DrugRecommendationReason()

    # 匹配到的适应症
    matched = []
    for ind in drug.indications:
        for disease in diseases:
            if disease in ind or ind in disease:
                if ind not in matched:
                    matched.append(ind)
                    break

    all_indications_text = _plain_indications_text(drug.indications, max_items=4)
    matched_text = _plain_indications_text(matched, max_items=2) if matched else all_indications_text

    # 适用症状
    reason.applicable_symptoms = (
        f"根据您描述的病情，本产品适用于{matched_text}相关症状。"
        f"产品说明书中明确列出的适用范围包括：{all_indications_text}。"
    )

    # 成分优势
    reason.component_advantage = (
        f"主要成分为{drug.main_component}。该成分在兽医临床中应用较广，"
        f"针对当前病症类型具有明确的作用特点，能够帮助改善相关症状。"
    )

    # 用法概要
    reason.usage_summary = dosage_recommendation if dosage_recommendation else drug.usage_info

    return reason


def _generate_combination_rationale(scheme_name: str, description: str,
                                     drug_details: List[Dict], diseases: List[str],
                                     disease_type: str) -> CombinationRationale:
    """生成组合方案的详细推荐理由（通俗化解释）"""
    rationale = CombinationRationale()

    disease_type_cn = {
        "RESPIRATORY": "呼吸道疾病",
        "DIGESTIVE": "消化道疾病",
        "BACTERIAL": "细菌性疾病",
        "VIRAL": "病毒性疾病",
        "PARASITIC": "寄生虫病",
        "NUTRITIONAL": "营养代谢问题",
        "MIXED": "混合感染",
        "REPRODUCTIVE": "生殖系统疾病"
    }.get(disease_type, "当前病症")

    # 组合依据
    rationale.combination_basis = (
        f"针对您当前的{disease_type_cn}情况，本方案根据“标本兼治、协同增效”的原则设计。"
        f"{description}。通过不同作用方向的药物搭配，力求更全面地对患病禽群进行干预。"
    )

    # 各药物作用
    rationale.drug_roles = []
    for drug in drug_details:
        drug_type = drug.get("drug_type", "未知")
        name = drug.get("name", "")
        indications_text = _plain_indications_text(drug.get("indications", []), max_items=3)

        if drug_type == "化药":
            role = (
                f"属于化药，主要负责直接抑制或杀灭病原微生物，"
                f"针对{indications_text}等病症起到快速控制感染的作用。"
            )
        else:
            role = (
                f"属于中兽药/保健类，主要帮助调理机体、缓解症状、增强免疫力，"
                f"对{indications_text}相关表现起到辅助改善作用。"
            )

        rationale.drug_roles.append({
            "name": name,
            "drug_type": drug_type,
            "role": role
        })

    # 协同效应
    if len(drug_details) >= 2:
        names = [d.get("name", "") for d in drug_details]
        has_chem = any(d.get("drug_type") == "化药" for d in drug_details)
        has_tcm = any(d.get("drug_type") == "中兽药" for d in drug_details)
        if has_chem and has_tcm:
            rationale.synergy_effect = (
                f"{'、'.join(names)}联合使用，可以发挥协同作用："
                f"化药类产品快速控制病原，中兽药类产品帮助机体恢复、减少不良反应，"
                f"从而提高整体治疗效果，缩短病程。"
            )
        else:
            rationale.synergy_effect = (
                f"{'、'.join(names)}联合使用，可从多个角度同时改善{disease_type_cn}相关症状，"
                f"相互配合增强整体疗效。"
            )
    else:
        rationale.synergy_effect = "单一药物按推荐方案使用，针对当前病症进行治疗。"

    # 作用机制
    rationale.mechanism = (
        f"本方案通过“直接杀灭/抑制病原 + 调理机体 + 改善症状”的多重机制共同作用："
        f"化药成分针对致病微生物发挥作用，中兽药/保健成分帮助提高机体自身抵抗力，"
        f"两者配合可更全面地应对{disease_type_cn}。"
    )

    # 低耐药风险分析与预防指导
    low_resistance = _analyze_low_resistance(drug_details)
    rationale.low_resistance_analysis = low_resistance["description"]
    has_chemical = any(d.get("drug_type") == "化药" for d in drug_details)
    rationale.resistance_prevention_guide = _generate_resistance_prevention_guide(
        disease_type, has_chemical
    )

    return rationale


class DrugRecommender:
    """药物推荐引擎 - 完整版"""
    
    def __init__(self, database: DrugDatabase):
        self.db = database
        self.symptom_mapper = SymptomDiseaseMapper()
        self.compatibility_checker = DrugCompatibilityChecker()
        self.disease_drug_validator = get_disease_drug_validator()

        self.disease_type_mapping = DISEASE_TYPE_MAPPING
    
    def recommend(self, request: RecommendationRequest) -> Dict:
        """主推荐函数"""
        # 解析症状获取疾病类型
        disease_info = self.symptom_mapper.get_diseases_by_symptom(request.symptom)
        diseases = disease_info["diseases"]
        disease_type = disease_info["type"]
        
        # 如果用户选择了发病类型，优先使用
        if request.disease_type in self.disease_type_mapping:
            disease_type = self.disease_type_mapping[request.disease_type]
        
        # 根据历史用药记录计算需要避免的药物集合（含交叉耐药同类药物）
        request.history_excluded = _get_history_excluded_drugs(
            request.medication_history, self.db.get_all_drugs()
        )
        
        # 获取候选药物
        candidate_drugs = self._get_candidate_drugs(request, diseases, disease_type)

        # 病症-药物关联验证：过滤掉与当前诊断无明确关联的药物
        valid_candidate_drugs, validation_results = self.disease_drug_validator.filter_candidates(
            candidate_drugs, disease_type, diseases
        )

        # 确保至少有3个有效候选药物；补充时也需通过验证
        if len(valid_candidate_drugs) < 3:
            supplemented = self._supplement_drugs(valid_candidate_drugs, request, disease_type, diseases)
            # 对补充的药物再次验证
            revalidated, revalidation_results = self.disease_drug_validator.filter_candidates(
                supplemented, disease_type, diseases
            )
            valid_candidate_drugs = revalidated
            # 合并验证结果：保留原有结果，并追加补充药物的新验证结果
            existing_names = {v.drug_name for v in validation_results}
            for v in revalidation_results:
                if v.drug_name not in existing_names:
                    validation_results.append(v)
                    existing_names.add(v.drug_name)

        # 计算单药推荐
        single_recommendations = self._calculate_single_recommendations(
            valid_candidate_drugs, request, diseases, disease_type
        )
        
        # 获取组合推荐
        combination_recommendations = self._get_combination_recommendations(
            request, diseases, disease_type
        )
        
        # 对组合推荐进行配伍禁忌检测
        compatibility_warnings = []
        for combo in combination_recommendations:
            if 'drugs' in combo and len(combo['drugs']) > 1:
                compatibility_result = self.compatibility_checker.check_compatibility(combo['drugs'])
                combo['compatibility_check'] = {
                    'is_safe': compatibility_result.is_safe,
                    'level': compatibility_result.level.value,
                    'conflicts': compatibility_result.conflicts,
                    'suggestions': compatibility_result.suggestions
                }
                
                # 如果有配伍禁忌，添加到警告列表
                if not compatibility_result.is_safe:
                    compatibility_warnings.append({
                        'scheme_name': combo.get('scheme_name', '未知方案'),
                        'level': compatibility_result.level.value,
                        'conflicts': compatibility_result.conflicts
                    })
        
        # 生成推荐决策审计日志
        final_recommendation_names = []
        for rec in single_recommendations:
            final_recommendation_names.append(rec.drug.name)
        for combo in combination_recommendations:
            for drug in combo.get("drugs", []):
                final_recommendation_names.append(drug.get("name", ""))
        # 去重，保持顺序
        seen = set()
        unique_names = []
        for n in final_recommendation_names:
            if n and n not in seen:
                unique_names.append(n)
                seen.add(n)
        final_recommendation_names = unique_names

        # 确保审计日志包含所有最终推荐药物的验证结果
        # 组合方案中的药物可能未出现在候选药物验证结果中，需要补充
        existing_names = {v.drug_name for v in validation_results}
        for combo in combination_recommendations:
            for drug_detail in combo.get("drugs", []):
                drug_name = drug_detail.get("name", "")
                if drug_name and drug_name not in existing_names:
                    drug_obj = self.db.get_drug_by_name(drug_name)
                    if drug_obj:
                        combo_validation = self.disease_drug_validator.validate_drug(
                            drug_obj, disease_type, diseases
                        )
                        validation_results.append(combo_validation)
                        existing_names.add(drug_name)

        audit_log = self.disease_drug_validator.generate_audit_log(
            request=request,
            disease_type=disease_type,
            diseases=diseases,
            candidates=candidate_drugs,
            valid_candidates=valid_candidate_drugs,
            validations=validation_results,
            final_recommendations=final_recommendation_names,
        )

        # 汇总验证结果（用于前端展示）
        validation_summary = {
            "total_candidates": len(candidate_drugs),
            "valid_candidates": len(valid_candidate_drugs),
            "invalid_candidates": len(candidate_drugs) - len(valid_candidate_drugs),
            "valid_rate": round(len(valid_candidate_drugs) / len(candidate_drugs), 2) if candidate_drugs else 0.0,
            "disease_type_cn": self.disease_drug_validator._disease_type_cn_map.get(
                disease_type, disease_type
            ),
            "check_dimensions": ["适应症匹配", "治疗领域匹配", "作用机制匹配"],
        }

        return {
            "input_analysis": {
                "symptom": request.symptom,
                "possible_diseases": diseases,
                "disease_type": disease_type,
                "animal_type": request.animal_type,
                "age_stage": request.age_stage
            },
            "single_recommendations": [r.to_dict() for r in single_recommendations],
            "combination_recommendations": combination_recommendations,
            "compatibility_warnings": compatibility_warnings,
            "validation_summary": validation_summary,
            "audit_log": audit_log.to_dict(),
        }
    
    def _get_candidate_drugs(self, request: RecommendationRequest,
                             diseases: List[str], disease_type: str) -> List[DrugInfo]:
        """获取候选药物列表"""
        candidates = []

        excluded_drugs_set = set(request.excluded_drugs) if request.excluded_drugs else set()
        history_excluded_set = getattr(request, 'history_excluded', set())

        for drug in self.db.get_all_drugs():
            # 排除用户指定的耐药性药物
            if any(_drug_name_matches(drug, ex) for ex in excluded_drugs_set):
                continue

            # 排除历史用药及易产生交叉耐药的同类药物
            if any(_drug_name_matches(drug, hx) for hx in history_excluded_set):
                continue

            # 产蛋期安全检查
            if request.egg_period_safe and not drug.egg_period_safe:
                continue

            # 疾病类型匹配
            if disease_type in drug.disease_types:
                candidates.append(drug)
                continue

            # 适应症匹配
            for indication in drug.indications:
                for disease in diseases:
                    if disease in indication or indication in disease:
                        if drug not in candidates:
                            candidates.append(drug)
                        break

        return candidates
    
    def _supplement_drugs(self, candidates: List[DrugInfo],
                          request: RecommendationRequest,
                          disease_type: str,
                          diseases: List[str]) -> List[DrugInfo]:
        """补充候选药物 - 只补充适应症真正匹配的药物"""
        existing_names = {d.name for d in candidates}
        excluded_drugs_set = set(request.excluded_drugs) if request.excluded_drugs else set()
        history_excluded_set = getattr(request, 'history_excluded', set())

        # 严格类型优先级 - 只有高度相关的类型才会被补充
        type_priority = {
            "PARASITIC": ["BACTERIAL"],
            "RESPIRATORY": ["BACTERIAL"],
            "DIGESTIVE": ["BACTERIAL"],
            "BACTERIAL": ["MIXED"],
            "VIRAL": ["BACTERIAL"],
            "MIXED": ["BACTERIAL"],
            "NUTRITIONAL": [],
            "REPRODUCTIVE": ["BACTERIAL"]  # 生殖系统疾病可补充细菌性药物
        }
        
        # 先补充同类型药物
        for drug in self.db.get_all_drugs():
            if len(candidates) >= 5:
                break
            if drug.name in existing_names:
                continue
            if any(_drug_name_matches(drug, ex) for ex in excluded_drugs_set):
                continue
            if any(_drug_name_matches(drug, hx) for hx in history_excluded_set):
                continue
            if request.egg_period_safe and not drug.egg_period_safe:
                continue
            if disease_type in drug.disease_types:
                candidates.append(drug)
                existing_names.add(drug.name)

        # 补充相关类型药物 - 但要求适应症必须匹配
        for related_type in type_priority.get(disease_type, []):
            for drug in self.db.get_all_drugs():
                if len(candidates) >= 5:
                    break
                if drug.name in existing_names:
                    continue
                if drug.name in excluded_drugs_set or drug.brand_name in excluded_drugs_set:
                    continue
                if drug.name in history_excluded_set or (drug.brand_name and drug.brand_name in history_excluded_set):
                    continue
                if request.egg_period_safe and not drug.egg_period_safe:
                    continue
                if related_type in drug.disease_types:
                    # 严格检查：适应症必须匹配目标疾病
                    has_matching_indication = False
                    for indication in drug.indications:
                        for disease in diseases:
                            if disease in indication or indication in disease:
                                has_matching_indication = True
                                break
                        if has_matching_indication:
                            break
                    
                    if has_matching_indication:
                        candidates.append(drug)
                        existing_names.add(drug.name)
        
        return candidates
    
    def _calculate_single_recommendations(self, drugs: List[DrugInfo],
                                          request: RecommendationRequest,
                                          diseases: List[str],
                                          disease_type: str = "MIXED") -> List[DrugRecommendation]:
        """计算单药推荐（清理后产品体系）

        仅保留底价目录与产品信息_华英数据，不再对明星产品做特殊兜底。
        推荐结果完全基于匹配分数排序，取前3个不重复产品。
        """
        recommendations = []
        history_excluded_set = getattr(request, 'history_excluded', set())

        for drug in drugs:
            match_score = self._calculate_match_score(drug, diseases, request, disease_type)
            reason = self._generate_reason(drug, diseases, match_score)
            dosage = self._generate_dosage(drug, request)
            reason_detail = _generate_single_drug_reason(drug, diseases, match_score, dosage)

            rec = DrugRecommendation(
                drug=drug,
                match_score=match_score,
                reason=reason,
                dosage_recommendation=dosage,
                reason_detail=reason_detail
            )
            recommendations.append(rec)
        
        # 按匹配分数排序
        recommendations.sort(key=lambda x: x.match_score, reverse=True)
        
        # 确保至少有1个推荐（兜底候选仍需通过病症-药物关联验证）
        if len(recommendations) < 1:
            for drug in self.db.get_all_drugs():
                if request.egg_period_safe and not drug.egg_period_safe:
                    continue
                if drug.name in history_excluded_set or (drug.brand_name and drug.brand_name in history_excluded_set):
                    continue

                # 兜底药物也必须通过关联验证
                validation = self.disease_drug_validator.validate_drug(
                    drug, disease_type, diseases
                )
                if not validation.is_valid:
                    continue

                fallback_dosage = self._generate_dosage(drug, request)
                fallback_reason_detail = _generate_single_drug_reason(
                    drug, diseases, 0.1, fallback_dosage
                )
                rec = DrugRecommendation(
                    drug=drug,
                    match_score=0.1,
                    reason=f"主要成分为{drug.main_component}；{'产蛋期可用' if drug.egg_period_safe else '注意：产蛋期禁用'}",
                    dosage_recommendation=fallback_dosage,
                    reason_detail=fallback_reason_detail
                )
                recommendations.append(rec)
                break

        # 筛选真正匹配的产品
        # 化药必须满足"明确具备治疗相应病症的适应症"这一核心条件；
        # 中兽药等可保留原有宽松逻辑（适应症匹配或综合匹配分数足够高）。
        # 同时复用多维度验证器结果作为最终校验。
        truly_matched_recommendations = []
        for rec in recommendations:
            has_matching_indication = _has_matching_indication(rec.drug, diseases)
            drug_type = classify_drug_type(rec.drug)

            # 最终把关：使用验证器确认关联性
            final_validation = self.disease_drug_validator.validate_drug(
                rec.drug, disease_type, diseases
            )

            if drug_type == "化药":
                # 化药严格门槛：必须有明确适应症匹配且通过验证器
                if has_matching_indication and final_validation.is_valid:
                    truly_matched_recommendations.append(rec)
            else:
                # 中兽药等保留原逻辑，并需通过验证器
                if (has_matching_indication or rec.match_score >= 3.0) and final_validation.is_valid:
                    truly_matched_recommendations.append(rec)

        # 如果没有任何匹配的产品，返回空列表（不再做无明确依据的兜底推荐）
        if not truly_matched_recommendations:
            return []

        # 基于统一匹配分数取前3个不重复产品
        truly_matched_recommendations.sort(key=lambda x: x.match_score, reverse=True)
        final_recommendations = []
        seen_ids = set()
        for rec in truly_matched_recommendations:
            if rec.drug.id not in seen_ids:
                # 额外过滤历史用药及交叉耐药同类药物
                if rec.drug.name in history_excluded_set or (rec.drug.brand_name and rec.drug.brand_name in history_excluded_set):
                    continue
                final_recommendations.append(rec)
                seen_ids.add(rec.drug.id)
            if len(final_recommendations) >= 3:
                break

        return final_recommendations[:3]
    
    def _calculate_match_score(self, drug: DrugInfo, diseases: List[str], 
                               request: RecommendationRequest,
                               disease_type: str = "MIXED") -> float:
        """计算药物与疾病的匹配分数（清理后产品体系）

        权重设计原则：
        - 以适应症匹配为核心（+3.0/命中）
        - 疾病类型直接命中给予稳定加成（+1.0）
        - 用途场景匹配给予适度加成（+0.5）
        - 华英产品信息来源给予少量信息完整度加成（+0.3）
        - 不再对明星产品设置额外加成，确保底价目录与华英产品公平竞争
        """
        score = 1.0
        
        # 适应症匹配（核心权重）
        for indication in drug.indications:
            for disease in diseases:
                if disease in indication or indication in disease:
                    score += 3.0
        
        # 疾病类型直接命中
        if disease_type in (drug.disease_types or []):
            score += 1.0
        
        # 用途匹配
        if request.usage == "预防":
            if drug.category in ['中药', '免疫增强剂', '维生素', '抗病毒类产品']:
                score += 0.5
        else:  # 治疗
            if drug.category in ['抗生素', '化药']:
                score += 0.5
        
        # 来源信息完整度加成：华英产品信息相对完整，给予小幅加成
        if drug.source == "产品信息_华英":
            score += 0.3
        # 底价目录产品不额外加分，依靠适应症和用途匹配
        
        return score
    
    def _generate_reason(self, drug: DrugInfo, diseases: List[str], 
                         match_score: float) -> str:
        """生成推荐理由"""
        reasons = []
        
        # 适应症匹配说明
        matched_indications = []
        for indication in drug.indications:
            for disease in diseases:
                if disease in indication or indication in disease:
                    matched_indications.append(indication)
        
        if matched_indications:
            reasons.append(f"对{', '.join(matched_indications[:2])}有特效")
        
        # 成分和类别
        reasons.append(f"主要成分:{drug.main_component}")
        reasons.append(f"类别:{drug.category}")
        
        # 产蛋期安全性
        if drug.egg_period_safe:
            reasons.append("产蛋期可用")
        else:
            reasons.append("产蛋期禁用")
        
        return "；".join(reasons)
    
    def _generate_dosage(self, drug: DrugInfo, request: RecommendationRequest) -> str:
        """生成用法用量建议"""
        if drug.usage_info:
            return drug.usage_info[:100] + "..." if len(drug.usage_info) > 100 else drug.usage_info
        
        water = drug.water if drug.water else "适量"
        
        if "预防" in request.usage:
            return f"预防：每袋/瓶兑水{water}，连用3-5天"
        else:
            return f"治疗：每袋/瓶兑水{water}，连用3-5天"
    
    def _get_combination_recommendations(self, request: RecommendationRequest,
                                         diseases: List[str],
                                         disease_type: str) -> List[Dict]:
        """获取药物组合推荐"""
        combinations = []
        
        # 定义组合方案库（已根据清理后的产品数据替换明星产品为保留产品）
        combination_schemes = {
            "PARASITIC": [
                {"name": "经典抗球虫方案", "drugs": ["磺胺喹噁啉钠可溶性粉（去球虫病）", "地美硝唑预混剂"], "description": "磺胺类联合抗原虫药，对各类球虫效果显著", "priority": 1, "egg_safe": False},
                {"name": "强化止血方案", "drugs": ["磺胺氯吡嗪钠可溶性粉（去球虫病）", "地美硝唑预混剂"], "description": "针对盲肠球虫特效，快速止血止痢", "priority": 2, "egg_safe": False},
                {"name": "全面抗虫方案", "drugs": ["磺胺喹噁啉钠可溶性粉（去球虫病）", "硫酸新霉素可溶性粉"], "description": "抗球虫同时预防继发细菌感染", "priority": 3, "egg_safe": False},
                {"name": "产蛋期安全抗球方案", "drugs": ["球立欣", "舒感康"], "description": "中药调理肠道、增强免疫力，产蛋期安全", "priority": 4, "egg_safe": True}
            ],
            "RESPIRATORY": [
                {"name": "经典呼吸道方案", "drugs": ["替米考星溶液", "盐酸多西环素可溶性粉"], "description": "大环内酯类联合四环素类，对支原体和细菌双重作用", "priority": 1, "egg_safe": False},
                {"name": "强化呼吸道方案", "drugs": ["80%延胡索酸泰妙菌素（呼吸道）", "盐酸多西环素可溶性粉"], "description": "高含量泰妙菌素，针对顽固性呼吸道病", "priority": 2, "egg_safe": False},
                {"name": "中西结合方案", "drugs": ["盐酸多西环素可溶性粉", "奇美诺250ml"], "description": "抗生素联合中药口服液，标本兼治", "priority": 3, "egg_safe": False},
                {"name": "产蛋期安全方案1", "drugs": ["奇美诺250ml", "感美舒®"], "description": "纯中药组合，产蛋期安全，针对呼吸道症状", "priority": 4, "egg_safe": True},
                {"name": "产蛋期安全方案2", "drugs": ["感美舒®", "欣控"], "description": "中药抗病毒组合，产蛋期可用", "priority": 5, "egg_safe": True},
                {"name": "产蛋期安全方案3", "drugs": ["舒感康", "感美舒®"], "description": "清热解毒组合，全面覆盖呼吸道病原", "priority": 6, "egg_safe": True}
            ],
            "DIGESTIVE": [
                {"name": "经典肠道方案", "drugs": ["硫酸黏菌素预混剂1000g", "阿莫西林可溶性粉"], "description": "黏菌素针对革兰氏阴性菌，阿莫西林广谱抗菌", "priority": 1, "egg_safe": False},
                {"name": "强化杀菌方案", "drugs": ["硫酸新霉素可溶性粉", "地美硝唑预混剂"], "description": "新霉素肠道浓度高，配合抗原虫药", "priority": 2, "egg_safe": False},
                {"name": "微生态调理方案", "drugs": ["杆 福", "益欣康"], "description": "益生菌/中药调理肠道，辅助治疗", "priority": 3, "egg_safe": False},
                {"name": "全面肠道方案", "drugs": ["硫酸黏菌素预混剂1000g", "硫酸新霉素可溶性粉", "地美硝唑预混剂"], "description": "三重杀菌，针对顽固性肠道感染", "priority": 4, "egg_safe": False},
                {"name": "产蛋期安全肠道方案", "drugs": ["杆 福", "益欣康"], "description": "纯中药/微生态调理肠胃，产蛋期安全", "priority": 5, "egg_safe": True}
            ],
            "BACTERIAL": [
                {"name": "广谱杀菌方案", "drugs": ["30%氟苯尼考可溶性粉", "盐酸多西环素可溶性粉"], "description": "广谱抗菌，对大多数细菌性疾病有效", "priority": 1, "egg_safe": False},
                {"name": "肠道细菌方案", "drugs": ["硫酸黏菌素预混剂1000g", "阿莫西林可溶性粉"], "description": "针对肠道细菌感染", "priority": 2, "egg_safe": False},
                {"name": "强化抗菌方案", "drugs": ["盐酸恩诺沙星可溶性粉", "硫酸黏菌素预混剂1000g"], "description": "氟喹诺酮类联合多肽类，杀菌效果强", "priority": 3, "egg_safe": False},
                {"name": "全面抗菌方案", "drugs": ["30%氟苯尼考可溶性粉", "盐酸多西环素可溶性粉", "硫酸黏菌素预混剂1000g"], "description": "三重广谱抗菌，覆盖各类细菌", "priority": 4, "egg_safe": False},
                {"name": "产蛋期安全抗菌方案", "drugs": ["感美舒®", "杆 福"], "description": "中药增强免疫配合抗菌，产蛋期安全", "priority": 5, "egg_safe": True}
            ],
            "VIRAL": [
                {"name": "抗病毒中药方案", "drugs": ["感美舒®", "舒感康"], "description": "中药清热解毒，增强免疫力", "priority": 1, "egg_safe": True},
                {"name": "防继发感染方案", "drugs": ["阿莫西林可溶性粉", "卡巴匹林钙粉"], "description": "预防细菌继发感染，缓解症状", "priority": 2, "egg_safe": False},
                {"name": "综合抗病毒方案", "drugs": ["感美舒®", "舒感康", "阿莫西林可溶性粉"], "description": "中药+抗生素，抗病毒防继发", "priority": 3, "egg_safe": False},
                {"name": "产蛋期安全抗病毒方案", "drugs": ["感美舒®", "欣控"], "description": "纯中药抗病毒，产蛋期安全", "priority": 4, "egg_safe": True}
            ],
            "MIXED": [
                {"name": "全面覆盖方案", "drugs": ["30%氟苯尼考可溶性粉", "盐酸多西环素可溶性粉", "卡巴匹林钙粉"], "description": "广谱抗菌+解热镇痛，应对复杂病情", "priority": 1, "egg_safe": False},
                {"name": "肠道呼吸道混合", "drugs": ["替米考星溶液", "硫酸黏菌素预混剂1000g"], "description": "同时覆盖呼吸道和肠道病原", "priority": 2, "egg_safe": False},
                {"name": "抗菌消炎方案", "drugs": ["阿莫西林可溶性粉", "卡巴匹林钙粉"], "description": "抗菌+消炎，适合混合感染", "priority": 3, "egg_safe": False},
                {"name": "产蛋期安全混合方案", "drugs": ["感美舒®", "传支净", "舒感康"], "description": "中药+保肝护肾支持，产蛋期安全", "priority": 4, "egg_safe": True}
            ],
            "NUTRITIONAL": [
                {"name": "营养支持方案", "drugs": ["传支净", "利美佳康"], "description": "保肝护肾，营养支持", "priority": 1, "egg_safe": True},
                {"name": "全面营养方案", "drugs": ["传支净", "利美佳康", "感美舒®"], "description": "营养+免疫，全面调理", "priority": 2, "egg_safe": True}
            ]
        }
        
        schemes = combination_schemes.get(disease_type, combination_schemes["MIXED"])

        # 历史用药排除集合（包含交叉耐药同类药物）
        history_excluded_set = getattr(request, 'history_excluded', set())

        for scheme in schemes:
            # 产蛋期安全检查 - 如果方案标记为产蛋期不安全且用户要求产蛋期安全，则跳过
            if request.egg_period_safe and scheme.get("egg_safe", True) == False:
                continue

            # 再检查方案中的每个药物
            if request.egg_period_safe:
                has_unsafe = False
                for drug_name in scheme["drugs"]:
                    drug = self.db.get_drug_by_name(drug_name)
                    if drug and not drug.egg_period_safe:
                        has_unsafe = True
                        break
                if has_unsafe:
                    continue

            # 排除耐药性药物检查
            excluded_set = set(request.excluded_drugs) if request.excluded_drugs else set()
            has_excluded = False
            for drug_name in scheme["drugs"]:
                drug = self.db.get_drug_by_name(drug_name)
                if drug and any(_drug_name_matches(drug, ex) for ex in excluded_set):
                    has_excluded = True
                    break
                # 排除历史用药及易产生交叉耐药的同类药物
                if drug and any(_drug_name_matches(drug, hx) for hx in history_excluded_set):
                    has_excluded = True
                    break
            if has_excluded:
                continue
            
            # 检查所有药物是否都存在
            all_drugs_exist = True
            drug_details = []
            total_price = 0
            
            for drug_name in scheme["drugs"]:
                drug = self.db.get_drug_by_name(drug_name)
                if drug:
                    total_price += drug.price
                    drug_details.append({
                        "name": drug.name,
                        "component": drug.main_component,
                        "price": drug.price,
                        "spec": drug.spec,
                        "category": drug.category,
                        "water": drug.water,
                        "content": drug.content,
                        "indications": drug.indications,
                        "egg_period_safe": drug.egg_period_safe,
                        "source": drug.source,
                        "usage_info": drug.usage_info,
                        "timing": drug.timing,
                        "brand_name": drug.brand_name,
                        "product_name": drug.product_name
                    })
                else:
                    all_drugs_exist = False
                    break
            
            if all_drugs_exist and drug_details:
                # ===== 病症-药物关联校验：剔除与当前病症无明确医学关联的药物 =====
                filtered_details = []
                filtered_price = 0
                combo_validations = []
                for dd in drug_details:
                    tmp = self.db.get_drug_by_name(dd.get("name", ""))
                    if tmp is None:
                        continue
                    # 使用多维度验证器判断药物与当前病症的关联性
                    validation = self.disease_drug_validator.validate_drug(
                        tmp, disease_type, diseases
                    )
                    combo_validations.append(validation.to_dict())
                    if not validation.is_valid:
                        continue
                    filtered_details.append(dd)
                    filtered_price += dd.get("price", 0)

                # 如果过滤后没有药物，说明该方案对当前病症无有效产品，跳过
                if not filtered_details:
                    continue

                drug_details = filtered_details
                total_price = filtered_price

                # ===== 类型合规校验：必须为"化药+中兽药"或"中兽药+中兽药" =====
                scheme_drugs = [
                    self.db.get_drug_by_name(dd.get("name", "")) for dd in drug_details
                ]
                scheme_drugs = [d for d in scheme_drugs if d is not None]
                compliance = validate_combination_compliance(scheme_drugs)

                # 若不合规，尝试将其中一款化药自动替换为中兽药
                # 替代品必须通过病症-药物关联验证，确保替换后的药物仍与当前病症相关
                adjusted = False
                if not compliance["compliant"]:
                    used_names = {d.name for d in scheme_drugs}
                    for i, d in enumerate(scheme_drugs):
                        if classify_drug_type(d) != "化药":
                            continue
                        # 对当前化药持续寻找有效替代品
                        while True:
                            substitute = _find_tcm_substitute(
                                self.db, d, disease_type, used_names
                            )
                            if substitute is None:
                                break

                            # 验证替代品与当前病症的关联性
                            sub_validation = self.disease_drug_validator.validate_drug(
                                substitute, disease_type, diseases
                            )
                            if sub_validation.is_valid:
                                break

                            # 该替代品与当前病症无明确关联，跳过并继续寻找下一个
                            used_names.add(substitute.name)

                        if substitute is None:
                            # 当前化药找不到有效中兽药替代品，尝试下一款化药
                            used_names.add(d.name)
                            continue

                        # 在 drug_details 中替换对应记录
                        old_name = d.name
                        new_name = substitute.name
                        for idx, detail in enumerate(drug_details):
                            if detail.get("name") == old_name:
                                drug_details[idx] = {
                                    "name": substitute.name,
                                    "component": substitute.main_component,
                                    "price": substitute.price,
                                    "spec": substitute.spec,
                                    "category": substitute.category,
                                    "water": substitute.water,
                                    "content": substitute.content,
                                    "indications": substitute.indications,
                                    "egg_period_safe": substitute.egg_period_safe,
                                    "source": substitute.source,
                                    "usage_info": substitute.usage_info,
                                    "timing": substitute.timing,
                                    "brand_name": substitute.brand_name,
                                    "product_name": substitute.product_name,
                                }
                                # 价格重新累加
                                total_price = total_price - d.price + substitute.price
                                used_names.add(new_name)
                                adjusted = True
                                break
                        if adjusted:
                            break
                        # 若本轮没找到合适的，跳到下一款化药
                        used_names.add(old_name)

                # 重新校验（若调整成功）
                if adjusted:
                    scheme_drugs = [
                        self.db.get_drug_by_name(dd.get("name", "")) for dd in drug_details
                    ]
                    scheme_drugs = [d for d in scheme_drugs if d is not None]
                    compliance = validate_combination_compliance(scheme_drugs)

                # 构造每个药物的类型标签，便于前端展示
                type_labels = []
                for dd in drug_details:
                    tmp = self.db.get_drug_by_name(dd.get("name", ""))
                    if tmp is not None:
                        type_labels.append({
                            "name": dd.get("name", ""),
                            "drug_type": classify_drug_type(tmp),
                            "category": dd.get("category", ""),
                        })
                    else:
                        type_labels.append({
                            "name": dd.get("name", ""),
                            "drug_type": "未知",
                            "category": dd.get("category", ""),
                        })

                # ===== 中兽药组合规则：两种均为中兽药时，按需添加一种化药 =====
                chem_count = sum(1 for tl in type_labels if tl.get("drug_type") == "化药")
                tcm_count = sum(1 for tl in type_labels if tl.get("drug_type") == "中兽药")

                if len(drug_details) == 2 and tcm_count == 2 and chem_count == 0:
                    # 仅当存在对当前病症具备明确适应症的有效化药时才补充化药；
                    # 否则保留双中兽药组合，不再强制添加无依据化药。
                    if _has_effective_chemical_drug(self.db, diseases, request):
                        used_names = {dd.get("name", "") for dd in drug_details}
                        excluded_drugs = list(set((request.excluded_drugs or []) + list(history_excluded_set)))

                        chemical_drug = _find_chemical_drug(
                            self.db, disease_type, diseases, used_names,
                            egg_period_safe=request.egg_period_safe,
                            excluded_drugs=excluded_drugs
                        )

                        if chemical_drug:
                            drug_details.append({
                                "name": chemical_drug.name,
                                "component": chemical_drug.main_component,
                                "price": chemical_drug.price,
                                "spec": chemical_drug.spec,
                                "category": chemical_drug.category,
                                "water": chemical_drug.water,
                                "content": chemical_drug.content,
                                "indications": chemical_drug.indications,
                                "egg_period_safe": chemical_drug.egg_period_safe,
                                "source": chemical_drug.source,
                                "usage_info": chemical_drug.usage_info,
                                "timing": chemical_drug.timing,
                                "brand_name": chemical_drug.brand_name,
                                "product_name": chemical_drug.product_name
                            })
                            total_price += chemical_drug.price

                            type_labels.append({
                                "name": chemical_drug.name,
                                "drug_type": classify_drug_type(chemical_drug),
                                "category": chemical_drug.category,
                            })

                            adjusted = True
                            compliance["chem_count"] = 1
                            compliance["tcm_count"] = 2
                            compliance["types"] = ["中兽药", "中兽药", "化药"]
                            compliance["type_set"] = ["化药", "中兽药"]

                # 为药品详情补充 drug_type，便于生成推荐理由
                type_label_map = {tl.get("name", ""): tl.get("drug_type", "未知") for tl in type_labels}
                for dd in drug_details:
                    dd["drug_type"] = type_label_map.get(dd.get("name", ""), "未知")

                # ===== 核心用药理念：最终组合药物总数严格不超过4种 =====
                if len(drug_details) > 4:
                    drug_details = drug_details[:4]
                    type_labels = type_labels[:4]
                    total_price = sum(dd.get("price", 0) for dd in drug_details)
                    # 重新统计类型构成
                    chem_count = sum(1 for tl in type_labels if tl.get("drug_type") == "化药")
                    tcm_count = sum(1 for tl in type_labels if tl.get("drug_type") == "中兽药")
                    compliance["chem_count"] = chem_count
                    compliance["tcm_count"] = tcm_count
                    compliance["types"] = [tl.get("drug_type", "未知") for tl in type_labels]
                    compliance["type_set"] = sorted(set(tl.get("drug_type", "未知") for tl in type_labels))

                # 组合药物可能经过替换/补充，重新生成验证结果，确保与展示药物一致
                combo_validations = []
                all_valid = True
                for dd in drug_details:
                    tmp = self.db.get_drug_by_name(dd.get("name", ""))
                    if tmp is None:
                        all_valid = False
                        continue
                    validation = self.disease_drug_validator.validate_drug(
                        tmp, disease_type, diseases
                    )
                    combo_validations.append(validation.to_dict())
                    if not validation.is_valid:
                        all_valid = False

                # 若组合中存在与当前病症无明确关联的药物，则丢弃该组合
                if not all_valid:
                    continue

                # 生成组合方案推荐理由
                combination_rationale = _generate_combination_rationale(
                    scheme_name=scheme["name"],
                    description=scheme["description"],
                    drug_details=drug_details,
                    diseases=diseases,
                    disease_type=disease_type
                )

                combinations.append({
                    "scheme_name": scheme["name"],
                    "description": scheme["description"],
                    "drugs": drug_details,
                    "total_price": round(total_price, 1),
                    "priority": scheme["priority"],
                    "type_compliance": {
                        **compliance,
                        "drug_type_labels": type_labels,
                        "adjusted": adjusted,
                        "rule": "必须为'化药+中兽药'或'中兽药+中兽药'组合，禁止全化药；最终组合药物总数严格不超过4种；两种中兽药组合且存在有效化药时可补充一种化药；所有化药必须对应当前病症具备明确适应症",
                    },
                    "rationale": combination_rationale.to_dict(),
                    "drug_validations": combo_validations,
                })

        # 如果没有找到合适的组合，使用默认组合
        if not combinations:
            combinations = self._get_default_combinations(request, diseases, disease_type)
            # 同样对默认组合做一次合规校验与展示补充
            for combo in combinations:
                scheme_drugs = [
                    self.db.get_drug_by_name(dd.get("name", "")) for dd in combo.get("drugs", [])
                ]
                scheme_drugs = [d for d in scheme_drugs if d is not None]
                compliance = validate_combination_compliance(scheme_drugs)
                type_labels = [
                    {
                        "name": dd.get("name", ""),
                        "drug_type": classify_drug_type(d) if d else "未知",
                        "category": dd.get("category", ""),
                    }
                    for dd, d in zip(combo.get("drugs", []), scheme_drugs)
                ]
                combo["type_compliance"] = {
                    **compliance,
                    "drug_type_labels": type_labels,
                    "adjusted": False,
                    "rule": "必须为'化药+中兽药'或'中兽药+中兽药'组合，禁止全化药；最终组合药物总数严格不超过4种；所有化药必须对应当前病症具备明确适应症",
                }

                # 为默认组合药品补充 drug_type 并生成推荐理由
                type_label_map = {tl.get("name", ""): tl.get("drug_type", "未知") for tl in type_labels}
                for dd in combo.get("drugs", []):
                    dd["drug_type"] = type_label_map.get(dd.get("name", ""), "未知")

                combo["rationale"] = _generate_combination_rationale(
                    scheme_name=combo.get("scheme_name", ""),
                    description=combo.get("description", ""),
                    drug_details=combo.get("drugs", []),
                    diseases=diseases,
                    disease_type=disease_type
                ).to_dict()

        # 按优先级排序，只返回第一个（最优方案）
        combinations.sort(key=lambda x: x["priority"])
        return combinations[:1]
    
    def _get_default_combinations(self, request: RecommendationRequest,
                                   diseases: List[str], disease_type: str = "MIXED") -> List[Dict]:
        """获取默认组合方案（同样执行化药适应症过滤）"""
        default_combos = []
        history_excluded_set = getattr(request, 'history_excluded', set())

        # 根据疾病类型选择不同的默认组合
        if disease_type == "RESPIRATORY":
            safe_combos = [
                {"name": "经典呼吸道方案", "drugs": ["替米考星溶液", "盐酸多西环素可溶性粉"], "description": "大环内酯类联合四环素类，对支原体和细菌双重作用", "priority": 1},
                {"name": "强化呼吸道方案", "drugs": ["80%延胡索酸泰妙菌素（呼吸道）", "盐酸多西环素可溶性粉"], "description": "高含量泰妙菌素，针对顽固性呼吸道病", "priority": 2},
                {"name": "中西结合方案", "drugs": ["盐酸多西环素可溶性粉", "桑仁清肺口服液"], "description": "抗生素联合中药口服液，标本兼治", "priority": 3}
            ]
        elif disease_type == "DIGESTIVE":
            safe_combos = [
                {"name": "经典肠道方案", "drugs": ["硫酸黏菌素预混剂1000g", "阿莫西林可溶性粉"], "description": "黏菌素针对革兰氏阴性菌，阿莫西林广谱抗菌", "priority": 1},
                {"name": "强化杀菌方案", "drugs": ["硫酸新霉素可溶性粉", "地美硝唑预混剂"], "description": "新霉素肠道浓度高，配合抗原虫药", "priority": 2},
                {"name": "微生态调理方案", "drugs": ["严立康", "（中药）畅健"], "description": "益生菌调理肠道，中药辅助治疗", "priority": 3}
            ]
        elif request.egg_period_safe:
            safe_combos = [
                {"name": "安全抗菌方案", "drugs": ["阿莫西林可溶性粉", "双黄连口服液250ml"], "description": "产蛋期安全用药，广谱抗菌", "priority": 1},
                {"name": "中药保健方案", "drugs": ["肽芪剑（蛋鸡）", "海健素"], "description": "中药调理，增强免疫力", "priority": 2},
                {"name": "营养支持方案", "drugs": ["海健素", "甘舒乐"], "description": "营养补充，保肝护肾", "priority": 3}
            ]
        else:
            safe_combos = [
                {"name": "强效抗菌方案", "drugs": ["氟苯尼考粉", "盐酸多西环素可溶性粉"], "description": "广谱强效抗菌组合", "priority": 1},
                {"name": "全面治疗方案", "drugs": ["替米考星溶液", "硫酸黏菌素预混剂1000g"], "description": "呼吸道+肠道全覆盖", "priority": 2},
                {"name": "经典消炎方案", "drugs": ["硫酸新霉素可溶性粉", "地美硝唑预混剂"], "description": "肠道消炎杀菌组合", "priority": 3}
            ]
        
        for combo in safe_combos:
            drug_details = []
            total_price = 0
            all_exist = True
            
            for drug_name in combo["drugs"]:
                drug = self.db.get_drug_by_name(drug_name)
                if drug:
                    if request.egg_period_safe and not drug.egg_period_safe:
                        all_exist = False
                        break
                    # 排除历史用药及交叉耐药同类药物
                    if drug.name in history_excluded_set or (drug.brand_name and drug.brand_name in history_excluded_set):
                        all_exist = False
                        break
                    total_price += drug.price
                    drug_details.append({
                        "name": drug.name,
                        "component": drug.main_component,
                        "price": drug.price,
                        "spec": drug.spec,
                        "category": drug.category,
                        "water": drug.water,
                        "content": drug.content,
                        "indications": drug.indications,
                        "egg_period_safe": drug.egg_period_safe,
                        "source": drug.source,
                        "usage_info": drug.usage_info,
                        "timing": drug.timing,
                        "brand_name": drug.brand_name,
                        "product_name": drug.product_name
                    })
                else:
                    all_exist = False
                    break
            
            if all_exist and drug_details:
                # 对默认组合同样执行化药适应症过滤
                filtered_details = []
                filtered_price = 0
                for dd in drug_details:
                    tmp = self.db.get_drug_by_name(dd.get("name", ""))
                    if tmp is None:
                        continue
                    if classify_drug_type(tmp) == "化药" and not _has_matching_indication(tmp, diseases):
                        continue
                    filtered_details.append(dd)
                    filtered_price += dd.get("price", 0)

                if filtered_details:
                    default_combos.append({
                        "scheme_name": combo["name"],
                        "description": combo["description"],
                        "drugs": filtered_details,
                        "total_price": round(filtered_price, 1),
                        "priority": combo["priority"]
                    })

        return default_combos


# 便捷函数
def create_recommender(data_path: str) -> DrugRecommender:
    """创建推荐器实例
    
    Args:
        data_path: 数据文件路径，支持 .json 或 .xlsx 格式
                  优先使用JSON格式，数据更新更可靠
    """
    db = DrugDatabase(data_path)
    return DrugRecommender(db)


def quick_recommend(recommender: DrugRecommender,
                   animal_type: str,
                   age_stage: str,
                   symptom: str,
                   disease_type: str,
                   usage: str,
                   egg_period_safe: bool,
                   farm_scale: str,
                   excluded_drugs: List[str] = None,
                   medication_history: List[str] = None) -> Dict:
    """快速推荐函数"""
    request = RecommendationRequest(
        animal_type=animal_type,
        age_stage=age_stage,
        symptom=symptom,
        disease_type=disease_type,
        usage=usage,
        egg_period_safe=egg_period_safe,
        farm_scale=farm_scale,
        excluded_drugs=excluded_drugs,
        medication_history=medication_history
    )
    return recommender.recommend(request)
