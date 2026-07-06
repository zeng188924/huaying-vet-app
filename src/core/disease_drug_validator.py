# -*- coding: utf-8 -*-
"""
病症-药物关联验证模块

提供严格的疾病-药物关联验证机制，确保推荐药物与当前诊断病症存在明确医学关联。
核心能力：
- 建立病症与药物的多维度关联数据库
- 对候选药物进行适应症、治疗领域、作用机制匹配度检查
- 记录推荐决策过程的审计日志
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Any


class AssociationLevel(Enum):
    """关联强度等级"""
    STRONG = "强关联"
    MEDIUM = "中等关联"
    WEAK = "弱关联"
    NONE = "无关联"


class DrugTypeCategory(Enum):
    """药物类型分类"""
    CHEMICAL = "化药"
    TCM = "中兽药"


# 疾病类型中文映射
DISEASE_TYPE_CN = {
    "RESPIRATORY": "呼吸道疾病",
    "DIGESTIVE": "消化道疾病",
    "PARASITIC": "寄生虫病",
    "BACTERIAL": "细菌性疾病",
    "VIRAL": "病毒性疾病",
    "NUTRITIONAL": "营养代谢病",
    "MIXED": "混合感染",
    "REPRODUCTIVE": "生殖系统疾病",
}


# 化药类别关键词（命中任一即判定为化药）
CHEMICAL_CATEGORIES = {
    "化药", "抗生素", "抗支原体药", "抗球虫类",
    "驱霉菌类产品", "消毒剂类", "解热镇痛",
}

# 化药成分关键词
CHEMICAL_COMPONENT_KEYWORDS = [
    "氟苯尼考", "多西环素", "卡巴匹林", "阿莫西林", "黏菌素",
    "新霉素", "恩诺沙星", "庆大霉素", "林可霉素", "地美硝唑",
    "卡那霉素", "替米考星", "安普霉素", "磺胺", "泰万菌素",
    "泰妙菌素", "大观霉素", "土霉素", "金霉素", "头孢",
    "喹诺酮", "红霉素", "青霉素", "链霉素", "壮观霉素",
]

# 交叉耐药性分组（即作用机制分类）
MECHANISM_GROUPS = {
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


# 疾病-典型作用机制映射：用于判断某类药物是否适合某类疾病
DISEASE_MECHANISM_PREFERENCES = {
    "RESPIRATORY": ["大环内酯类", "四环素类", "截短侧耳素/林可胺类", "氟喹诺酮类", "β-内酰胺类", "酰胺醇类"],
    "DIGESTIVE": ["氨基糖苷类", "多肽类", "硝基咪唑类", "β-内酰胺类", "磺胺类", "酰胺醇类", "四环素类"],
    "PARASITIC": ["磺胺类", "硝基咪唑类"],
    "BACTERIAL": ["β-内酰胺类", "酰胺醇类", "氟喹诺酮类", "氨基糖苷类", "四环素类", "大环内酯类", "磺胺类", "多肽类"],
    "VIRAL": ["解热镇痛类"],  # 病毒性以中药/支持疗法为主，化药仅用于防继发
    "NUTRITIONAL": [],
    "MIXED": ["β-内酰胺类", "酰胺醇类", "氟喹诺酮类", "四环素类", "大环内酯类", "氨基糖苷类", "多肽类"],
    "REPRODUCTIVE": ["β-内酰胺类", "四环素类", "大环内酯类", "氟喹诺酮类"],
}


# 疾病类型 -> 典型适应症关键词映射（用于强化适应症匹配）
DISEASE_INDICATION_KEYWORDS = {
    "RESPIRATORY": ["呼吸道", "慢性呼吸道病", "支原体", "传染性鼻炎", "咳嗽", "呼吸困难", "啰音", "气囊炎", "肺炎", "支气管炎", "喉气管炎"],
    "DIGESTIVE": ["肠道", "肠炎", "腹泻", "拉稀", "消化不良", "大肠杆菌", "沙门氏菌", "白痢", "霍乱", "坏死性肠炎", "腺胃炎", "肌胃炎"],
    "PARASITIC": ["球虫", "组织滴虫", "毛滴虫", "蛔虫", "绦虫", "吸虫", "寄生虫"],
    "BACTERIAL": ["细菌", "大肠杆菌", "沙门氏菌", "巴氏杆菌", "霍乱", "白痢", "葡萄球菌", "链球菌", "支原体", "浆膜炎"],
    "VIRAL": ["病毒", "流感", "新城疫", "传支", "传喉", "法氏囊", "鸭瘟", "肝炎", "坦布苏"],
    "NUTRITIONAL": ["维生素", "营养", "应激", "保肝", "护肾", "解毒", "免疫增强"],
    "MIXED": ["混合感染", "继发", "并发症"],
    "REPRODUCTIVE": ["输卵管", "卵巢", "产蛋", "畸形蛋", "血斑蛋", "沙壳蛋", "薄壳蛋"],
}


@dataclass
class DiseaseDrugAssociation:
    """单个药物与疾病的关联评估结果"""
    drug_name: str
    drug_component: str
    drug_category: str
    drug_type: str  # 化药 / 中兽药
    disease_type: str
    diseases: List[str]

    indication_match: bool = False
    indication_score: float = 0.0
    indication_matched_terms: List[str] = field(default_factory=list)

    therapeutic_match: bool = False
    therapeutic_score: float = 0.0

    mechanism_match: bool = False
    mechanism_score: float = 0.0
    mechanism_groups: List[str] = field(default_factory=list)

    overall_score: float = 0.0
    association_level: str = AssociationLevel.NONE.value
    is_valid: bool = False
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationAuditLog:
    """推荐决策审计日志条目"""
    timestamp: str
    request_id: str
    animal_type: str
    age_stage: str
    symptom: str
    disease_type: str
    diseases: List[str]
    excluded_drugs: List[str]
    medication_history: List[str]
    candidate_count: int
    valid_count: int
    invalid_count: int
    validation_details: List[Dict[str, Any]]
    filtering_decisions: List[Dict[str, Any]]
    final_recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DiseaseDrugValidator:
    """病症-药物关联验证器

    对候选药物进行多维度关联验证：
    1. 适应症匹配：药物适应症是否与当前疾病/症状直接相关
    2. 治疗领域匹配：药物疾病类型是否覆盖当前疾病大类
    3. 作用机制匹配：药物作用机制是否适用于当前疾病大类
    """

    def __init__(self):
        self._disease_type_cn_map = DISEASE_TYPE_CN
        self._init_disease_drug_maps()

    def _init_disease_drug_maps(self):
        """初始化病症-药物关联映射"""
        # 症状到疾病类型的快速映射（复用并简化 SymptomDiseaseMapper 的语义）
        self.symptom_disease_map = {
            # 呼吸道
            "咳嗽": "RESPIRATORY",
            "打喷嚏": "RESPIRATORY",
            "流鼻涕": "RESPIRATORY",
            "呼吸困难": "RESPIRATORY",
            "啰音": "RESPIRATORY",
            "喘": "RESPIRATORY",
            "呼吸": "RESPIRATORY",
            "气囊炎": "RESPIRATORY",
            "肺炎": "RESPIRATORY",
            "支气管炎": "RESPIRATORY",
            "喉气管炎": "RESPIRATORY",
            "传染性鼻炎": "RESPIRATORY",
            "支原体": "RESPIRATORY",
            "慢呼": "RESPIRATORY",
            # 消化道
            "拉稀": "DIGESTIVE",
            "腹泻": "DIGESTIVE",
            "血便": "DIGESTIVE",
            "绿色粪便": "DIGESTIVE",
            "白色粪便": "DIGESTIVE",
            "食欲不振": "DIGESTIVE",
            "不吃": "DIGESTIVE",
            "肠炎": "DIGESTIVE",
            "肠道": "DIGESTIVE",
            "腺胃炎": "DIGESTIVE",
            "肌胃炎": "DIGESTIVE",
            "嗉囊炎": "DIGESTIVE",
            "过料": "DIGESTIVE",
            "饲料便": "DIGESTIVE",
            # 寄生虫
            "球虫": "PARASITIC",
            "盲肠球虫": "PARASITIC",
            "小肠球虫": "PARASITIC",
            "蛔虫": "PARASITIC",
            "绦虫": "PARASITIC",
            "羽虱": "PARASITIC",
            "螨虫": "PARASITIC",
            "组织滴虫": "PARASITIC",
            "毛滴虫": "PARASITIC",
            "前殖吸虫": "PARASITIC",
            "消瘦": "PARASITIC",
            "贫血": "PARASITIC",
            # 细菌
            "大肠杆菌": "BACTERIAL",
            "沙门氏菌": "BACTERIAL",
            "白痢": "BACTERIAL",
            "霍乱": "BACTERIAL",
            "伤寒": "BACTERIAL",
            "巴氏杆菌": "BACTERIAL",
            "葡萄球菌": "BACTERIAL",
            "链球菌": "BACTERIAL",
            "浆膜炎": "BACTERIAL",
            "里默氏杆菌": "BACTERIAL",
            # 病毒
            "流感": "VIRAL",
            "禽流感": "VIRAL",
            "新城疫": "VIRAL",
            "传支": "VIRAL",
            "传喉": "VIRAL",
            "法氏囊": "VIRAL",
            "鸭瘟": "VIRAL",
            "鸭肝炎": "VIRAL",
            "坦布苏": "VIRAL",
            "病毒": "VIRAL",
            # 生殖
            "输卵管炎": "REPRODUCTIVE",
            "卵巢炎": "REPRODUCTIVE",
            "产蛋下降": "REPRODUCTIVE",
            "畸形蛋": "REPRODUCTIVE",
            "沙壳蛋": "REPRODUCTIVE",
            "血斑蛋": "REPRODUCTIVE",
            "薄壳蛋": "REPRODUCTIVE",
            "软壳蛋": "REPRODUCTIVE",
            # 营养代谢
            "维生素": "NUTRITIONAL",
            "营养": "NUTRITIONAL",
            "应激": "NUTRITIONAL",
            "保肝": "NUTRITIONAL",
            "护肾": "NUTRITIONAL",
            "解毒": "NUTRITIONAL",
            "中暑": "NUTRITIONAL",
            "冷应激": "NUTRITIONAL",
            "热应激": "NUTRITIONAL",
            "痛风": "NUTRITIONAL",
            "脂肪肝": "NUTRITIONAL",
            "腹水": "NUTRITIONAL",
        }

    def classify_drug_type(self, drug: Any) -> str:
        """判断药物类型：化药 / 中兽药"""
        category = (getattr(drug, "category", None) or "").strip()
        if category in CHEMICAL_CATEGORIES:
            return DrugTypeCategory.CHEMICAL.value
        if category == "明星产品":
            comp = (getattr(drug, "main_component", None) or "").strip()
            for kw in CHEMICAL_COMPONENT_KEYWORDS:
                if kw in comp:
                    return DrugTypeCategory.CHEMICAL.value
            return DrugTypeCategory.TCM.value
        return DrugTypeCategory.TCM.value

    def _get_mechanism_groups(self, drug: Any) -> List[str]:
        """获取药物涉及的作用机制类别"""
        component = (getattr(drug, "main_component", None) or "").strip()
        name = (getattr(drug, "name", None) or "").strip()
        text = component + " " + name
        groups = []
        for group_name, keywords in MECHANISM_GROUPS.items():
            for kw in keywords:
                if kw in text:
                    groups.append(group_name)
                    break
        return groups

    def _check_indication_match(self, drug: Any, diseases: List[str], disease_type: str) -> tuple:
        """检查适应症匹配情况

        返回: (是否匹配, 匹配分数, 匹配到的术语列表)
        """
        indications = getattr(drug, "indications", []) or []
        if not indications:
            return False, 0.0, []

        matched_terms = []
        score = 0.0

        # 1. 与具体疾病名称匹配
        for indication in indications:
            ind_lower = str(indication).lower()
            for disease in diseases:
                if disease in indication or indication in disease:
                    if disease not in matched_terms:
                        matched_terms.append(disease)
                    score += 3.0

        # 2. 与疾病类型关键词匹配
        keywords = DISEASE_INDICATION_KEYWORDS.get(disease_type, [])
        for indication in indications:
            ind_lower = str(indication).lower()
            for kw in keywords:
                if kw in indication:
                    if kw not in matched_terms:
                        matched_terms.append(kw)
                    score += 1.0

        return score > 0, min(score, 10.0), matched_terms

    def _check_therapeutic_match(self, drug: Any, disease_type: str) -> tuple:
        """检查治疗领域（疾病类型）匹配"""
        drug_types = getattr(drug, "disease_types", []) or []
        if disease_type in drug_types:
            return True, 2.0
        if "MIXED" in drug_types:
            return True, 0.5
        return False, 0.0

    def _check_mechanism_match(self, drug: Any, disease_type: str) -> tuple:
        """检查作用机制是否适合当前疾病大类"""
        groups = self._get_mechanism_groups(drug)
        if not groups:
            # 中兽药等无明确化药机制的，默认不以此维度扣分
            return False, 0.0
        preferred = DISEASE_MECHANISM_PREFERENCES.get(disease_type, [])
        matched = [g for g in groups if g in preferred]
        if matched:
            return True, 1.5 + 0.5 * len(matched)
        return False, -0.5  # 化药机制与疾病不匹配时扣分

    def validate_drug(self, drug: Any, disease_type: str, diseases: List[str]) -> DiseaseDrugAssociation:
        """对单个药物进行多维关联验证"""
        drug_type = self.classify_drug_type(drug)

        indication_match, indication_score, indication_matched_terms = self._check_indication_match(
            drug, diseases, disease_type
        )
        therapeutic_match, therapeutic_score = self._check_therapeutic_match(drug, disease_type)
        mechanism_match, mechanism_score = self._check_mechanism_match(drug, disease_type)

        # 计算综合得分
        overall_score = indication_score + therapeutic_score + max(mechanism_score, 0.0)

        # 根据得分判定关联等级
        if overall_score >= 4.0:
            level = AssociationLevel.STRONG.value
        elif overall_score >= 2.0:
            level = AssociationLevel.MEDIUM.value
        elif overall_score > 0.0:
            level = AssociationLevel.WEAK.value
        else:
            level = AssociationLevel.NONE.value

        # 判定是否有效：所有药物必须以"适应症匹配"作为核心依据，
        # 确保推荐药物与当前诊断病症存在明确医学关联。
        # 化药额外要求治疗领域或作用机制至少一项匹配；
        # 非化药至少要有明确的适应症匹配。
        if drug_type == DrugTypeCategory.CHEMICAL.value:
            is_valid = indication_match and (therapeutic_match or mechanism_match)
        else:
            is_valid = indication_match

        # 生成原因说明
        reasons = []
        if indication_match:
            reasons.append(f"适应症匹配：{', '.join(indication_matched_terms[:3])}")
        if therapeutic_match:
            reasons.append(f"治疗领域匹配：{DISEASE_TYPE_CN.get(disease_type, disease_type)}")
        if mechanism_match:
            reasons.append(f"作用机制匹配：{', '.join(self._get_mechanism_groups(drug)[:2])}")
        if not reasons:
            reasons.append("未找到明确关联依据")

        return DiseaseDrugAssociation(
            drug_name=getattr(drug, "name", "未知"),
            drug_component=getattr(drug, "main_component", ""),
            drug_category=getattr(drug, "category", ""),
            drug_type=drug_type,
            disease_type=disease_type,
            diseases=diseases,
            indication_match=indication_match,
            indication_score=indication_score,
            indication_matched_terms=indication_matched_terms,
            therapeutic_match=therapeutic_match,
            therapeutic_score=therapeutic_score,
            mechanism_match=mechanism_match,
            mechanism_score=mechanism_score,
            mechanism_groups=self._get_mechanism_groups(drug),
            overall_score=round(overall_score, 2),
            association_level=level,
            is_valid=is_valid,
            reason="；".join(reasons),
        )

    def validate_candidates(self, candidates: List[Any], disease_type: str,
                            diseases: List[str]) -> List[DiseaseDrugAssociation]:
        """批量验证候选药物"""
        return [self.validate_drug(d, disease_type, diseases) for d in candidates]

    def filter_candidates(self, candidates: List[Any], disease_type: str,
                          diseases: List[str]) -> tuple:
        """过滤候选药物并返回验证结果

        返回: (有效候选药物列表, 完整验证结果列表)
        """
        validations = self.validate_candidates(candidates, disease_type, diseases)
        valid_candidates = []
        for drug, validation in zip(candidates, validations):
            if validation.is_valid:
                valid_candidates.append(drug)
        return valid_candidates, validations

    def generate_audit_log(self,
                           request: Any,
                           disease_type: str,
                           diseases: List[str],
                           candidates: List[Any],
                           valid_candidates: List[Any],
                           validations: List[DiseaseDrugAssociation],
                           final_recommendations: List[str]) -> ValidationAuditLog:
        """生成推荐决策审计日志"""
        filtering_decisions = []
        for v in validations:
            if not v.is_valid:
                filtering_decisions.append({
                    "drug_name": v.drug_name,
                    "drug_type": v.drug_type,
                    "decision": "排除",
                    "association_level": v.association_level,
                    "score": v.overall_score,
                    "reason": v.reason,
                })
            else:
                filtering_decisions.append({
                    "drug_name": v.drug_name,
                    "drug_type": v.drug_type,
                    "decision": "保留",
                    "association_level": v.association_level,
                    "score": v.overall_score,
                    "reason": v.reason,
                })

        return ValidationAuditLog(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            request_id=datetime.now().strftime("%Y%m%d%H%M%S%f"),
            animal_type=getattr(request, "animal_type", ""),
            age_stage=getattr(request, "age_stage", ""),
            symptom=getattr(request, "symptom", ""),
            disease_type=getattr(request, "disease_type", ""),
            diseases=diseases,
            excluded_drugs=list(getattr(request, "excluded_drugs", []) or []),
            medication_history=list(getattr(request, "medication_history", []) or []),
            candidate_count=len(candidates),
            valid_count=len(valid_candidates),
            invalid_count=len(candidates) - len(valid_candidates),
            validation_details=[v.to_dict() for v in validations],
            filtering_decisions=filtering_decisions,
            final_recommendations=final_recommendations,
        )


def get_disease_drug_validator() -> DiseaseDrugValidator:
    """获取验证器实例"""
    return DiseaseDrugValidator()
