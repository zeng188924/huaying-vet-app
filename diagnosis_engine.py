# -*- coding: utf-8 -*-
"""
诊断引擎模块
提供多症状组合诊断、引导式问诊和用药安全分级功能
解决养殖户无法准确判断疾病时的用药难题
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json


class ConfidenceLevel(Enum):
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"


class DiagnosisStatus(Enum):
    CONFIRMED = "确诊"
    SUSPECTED = "疑似"
    UNCERTAIN = "不确定"


@dataclass
class SymptomItem:
    """症状项"""
    id: str
    name: str
    category: str
    weight: float
    description: str = ""


@dataclass
class DiseaseCandidate:
    """疾病候选"""
    name: str
    score: float
    confidence: str
    matched_symptoms: List[str]
    unmatched_symptoms: List[str]
    differentiation_points: List[str]
    treatment_principle: str
    common_drugs: List[str]


@dataclass
class DiagnosisResult:
    """诊断结果"""
    status: str
    primary_disease: Optional[DiseaseCandidate]
    secondary_diseases: List[DiseaseCandidate]
    all_symptoms: List[str]
    confidence_level: str
    safety_level: str
    recommendations: Dict


@dataclass
class QuestionnaireStep:
    """问诊步骤"""
    step_id: str
    title: str
    category: str
    description: str
    symptoms: List[SymptomItem]


class SymptomBasedDiagnosisEngine:
    """多症状组合诊断引擎"""
    
    def __init__(self):
        self.symptom_database = self._init_symptom_database()
        self.disease_diagnosis_rules = self._init_disease_diagnosis_rules()
    
    def _init_symptom_database(self) -> Dict[str, SymptomItem]:
        """初始化症状数据库"""
        symptoms = {}
        
        # 外观症状
        appearance_symptoms = [
            ("feather_ruffled", "羽毛松乱", "外观", 2.0, "羽毛蓬松、杂乱无光泽"),
            ("comb_pale", "冠髯苍白", "外观", 3.0, "鸡冠和肉髯颜色变浅、发白"),
            ("comb_cyanosis", "冠髯发绀", "外观", 3.0, "鸡冠和肉髯呈青紫色"),
            ("eyes_closed", "闭眼缩颈", "外观", 2.5, "闭眼、颈部收缩、不愿活动"),
            ("body_weak", "身体虚弱", "外观", 2.0, "站立不稳、行走无力"),
            ("wings_drooped", "翅膀下垂", "外观", 2.0, "翅膀下垂、不愿拍打"),
            ("head_shaking", "摇头", "外观", 1.5, "频繁摇头"),
            ("neck_twisting", "扭颈", "外观", 4.0, "颈部扭曲、呈S形或反向弯曲"),
        ]
        
        # 粪便症状
        feces_symptoms = [
            ("feces_blood_red", "血便(鲜红)", "粪便", 4.0, "排出鲜红色血液粪便，常见于盲肠球虫"),
            ("feces_blood_dark", "血便(暗红)", "粪便", 3.5, "排出暗红色血液粪便，常见于小肠球虫"),
            ("feces_white", "白色稀粪", "粪便", 3.0, "白色米汤样或石灰样稀粪"),
            ("feces_green", "绿色粪便", "粪便", 3.0, "绿色稀粪，常见于病毒感染"),
            ("feces_yellow", "黄色稀粪", "粪便", 2.0, "黄色稀粪，常见于肠道细菌感染"),
            ("feces_watery", "水样腹泻", "粪便", 2.5, "大量水样粪便，严重脱水"),
            ("feces_unformed", "粪便不成形", "粪便", 1.5, "粪便稀薄、不成形"),
            ("feces_bloody_mucus", "黏液血便", "粪便", 3.5, "粪便中带有黏液和血液"),
        ]
        
        # 呼吸道症状
        respiratory_symptoms = [
            ("resp_cough", "咳嗽", "呼吸道", 2.5, "发出咳嗽声"),
            ("resp_sneeze", "打喷嚏", "呼吸道", 2.0, "频繁打喷嚏"),
            ("resp_nasal_discharge", "流鼻涕", "呼吸道", 2.5, "鼻腔流出分泌物"),
            ("resp_rhonchus", "啰音", "呼吸道", 3.0, "呼吸时发出啰音、喘鸣声"),
            ("resp_open_mouth", "张口呼吸", "呼吸道", 3.5, "张口呼吸、伸颈喘"),
            ("resp_dyspnea", "呼吸困难", "呼吸道", 4.0, "呼吸急促、困难"),
            ("resp_gasping", "喘鸣", "呼吸道", 3.0, "呼吸时有喘息声"),
        ]
        
        # 全身症状
        systemic_symptoms = [
            ("sys_depression", "精神沉郁", "全身", 3.0, "精神不振、反应迟钝"),
            ("sys_anorexia", "食欲不振", "全身", 2.5, "采食量明显下降或不吃"),
            ("sys_fever", "发热", "全身", 3.0, "体温升高"),
            ("sys_weight_loss", "消瘦", "全身", 2.5, "体重明显下降"),
            ("sys_death", "死亡", "全身", 5.0, "出现死亡病例"),
            ("sys_tremor", "抽搐", "全身", 4.0, "身体抽搐、痉挛"),
            ("sys_paralysis", "瘫痪", "全身", 4.0, "肢体瘫痪、无法站立"),
            ("sys_drowsy", "嗜睡", "全身", 2.0, "昏睡、不愿活动"),
        ]
        
        # 其他症状
        other_symptoms = [
            ("other_diarrhea", "拉稀", "其他", 2.0, "腹泻、拉稀"),
            ("other_egg_drop", "产蛋下降", "其他", 2.5, "产蛋率明显下降"),
            ("other_deformed_egg", "畸形蛋", "其他", 2.0, "产出畸形蛋"),
            ("other_sand_egg", "沙壳蛋", "其他", 2.0, "产出沙壳蛋"),
            ("other_blood_spot", "血斑蛋", "其他", 2.0, "蛋内有血斑"),
            ("other_joint_swelling", "关节肿胀", "其他", 3.0, "关节肿大、跛行"),
            ("other_skin_lesion", "皮肤病变", "其他", 2.0, "皮肤出现病变"),
            ("other_abdominal_distension", "腹部膨大", "其他", 2.0, "腹部膨胀"),
        ]
        
        for sym_id, name, category, weight, desc in (
            appearance_symptoms + feces_symptoms + respiratory_symptoms + 
            systemic_symptoms + other_symptoms
        ):
            symptoms[sym_id] = SymptomItem(sym_id, name, category, weight, desc)
        
        return symptoms
    
    def _init_disease_diagnosis_rules(self) -> Dict:
        """初始化疾病诊断规则库"""
        return {
            "球虫病": {
                "key_symptoms": ["feces_blood_red", "feces_blood_dark", "feces_bloody_mucus"],
                "important_symptoms": ["sys_depression", "sys_anorexia", "sys_weight_loss", "feather_ruffled"],
                "supporting_symptoms": ["feces_unformed", "comb_pale"],
                "exclude_symptoms": ["resp_dyspnea", "resp_open_mouth"],
                "differentiation": {
                    "盲肠球虫": ["feces_blood_red", "sys_death"],
                    "小肠球虫": ["feces_blood_dark", "sys_weight_loss"]
                },
                "treatment_principle": "抗球虫药物联合使用，止血止痢，补充营养",
                "common_drugs": ["磺胺喹噁啉钠", "磺胺氯吡嗪钠", "地美硝唑"]
            },
            "盲肠球虫": {
                "key_symptoms": ["feces_blood_red"],
                "important_symptoms": ["sys_depression", "sys_death", "comb_pale"],
                "supporting_symptoms": ["sys_anorexia", "feather_ruffled"],
                "exclude_symptoms": ["feces_blood_dark", "resp_dyspnea"],
                "differentiation": {},
                "treatment_principle": "磺胺类药物效果最佳，配合止血药",
                "common_drugs": ["磺胺氯吡嗪钠", "磺胺喹噁啉钠", "维生素K3"]
            },
            "小肠球虫": {
                "key_symptoms": ["feces_blood_dark"],
                "important_symptoms": ["sys_weight_loss", "sys_depression"],
                "supporting_symptoms": ["feces_unformed", "sys_anorexia"],
                "exclude_symptoms": ["feces_blood_red"],
                "differentiation": {},
                "treatment_principle": "抗球虫药联合肠道消炎药",
                "common_drugs": ["磺胺喹噁啉钠", "地美硝唑", "新霉素"]
            },
            "慢性呼吸道病": {
                "key_symptoms": ["resp_cough", "resp_rhonchus"],
                "important_symptoms": ["resp_sneeze", "resp_nasal_discharge"],
                "supporting_symptoms": ["sys_depression", "feather_ruffled"],
                "exclude_symptoms": ["feces_blood_red", "sys_death"],
                "differentiation": {},
                "treatment_principle": "大环内酯类或四环素类药物，疗程要足",
                "common_drugs": ["替米考星", "泰万菌素", "多西环素"]
            },
            "大肠杆菌病": {
                "key_symptoms": ["feces_yellow", "feces_watery"],
                "important_symptoms": ["sys_depression", "sys_anorexia"],
                "supporting_symptoms": ["feather_ruffled", "resp_dyspnea"],
                "exclude_symptoms": ["feces_blood_red", "neck_twisting"],
                "differentiation": {},
                "treatment_principle": "根据药敏试验选择敏感药物",
                "common_drugs": ["氟苯尼考", "黏菌素", "新霉素", "恩诺沙星"]
            },
            "沙门氏菌病": {
                "key_symptoms": ["feces_white"],
                "important_symptoms": ["sys_depression", "sys_anorexia"],
                "supporting_symptoms": ["comb_pale", "resp_dyspnea"],
                "exclude_symptoms": ["feces_blood_red", "neck_twisting"],
                "differentiation": {},
                "treatment_principle": "氟喹诺酮类或氟苯尼考，注意耐药性",
                "common_drugs": ["氟苯尼考", "恩诺沙星"]
            },
            "鸡白痢": {
                "key_symptoms": ["feces_white"],
                "important_symptoms": ["sys_depression", "sys_anorexia", "resp_dyspnea"],
                "supporting_symptoms": ["comb_pale", "body_weak"],
                "exclude_symptoms": ["feces_blood_red", "neck_twisting"],
                "differentiation": {},
                "treatment_principle": "早期治疗效果好，注意耐药性",
                "common_drugs": ["氟苯尼考", "恩诺沙星", "庆大霉素"]
            },
            "禽霍乱": {
                "key_symptoms": ["sys_death", "comb_cyanosis"],
                "important_symptoms": ["sys_fever", "sys_depression", "feces_green"],
                "supporting_symptoms": ["sys_anorexia", "resp_dyspnea"],
                "exclude_symptoms": ["neck_twisting"],
                "differentiation": {},
                "treatment_principle": "磺胺类或氟喹诺酮类药物",
                "common_drugs": ["磺胺间甲氧嘧啶", "恩诺沙星", "氟苯尼考"]
            },
            "传染性鼻炎": {
                "key_symptoms": ["resp_nasal_discharge", "resp_sneeze"],
                "important_symptoms": ["resp_cough"],
                "supporting_symptoms": ["sys_depression", "feather_ruffled"],
                "exclude_symptoms": ["feces_blood_red", "sys_death"],
                "differentiation": {},
                "treatment_principle": "磺胺类药物效果好，注意复发",
                "common_drugs": ["磺胺间甲氧嘧啶", "链霉素"]
            },
            "坏死性肠炎": {
                "key_symptoms": ["feces_bloody_mucus", "sys_death"],
                "important_symptoms": ["sys_depression", "sys_anorexia"],
                "supporting_symptoms": ["feces_unformed"],
                "exclude_symptoms": ["resp_dyspnea"],
                "differentiation": {},
                "treatment_principle": "林可霉素或青霉素类效果好",
                "common_drugs": ["林可霉素", "青霉素"]
            },
            "滑液囊支原体": {
                "key_symptoms": ["other_joint_swelling"],
                "important_symptoms": ["sys_weight_loss", "feather_ruffled"],
                "supporting_symptoms": ["sys_depression"],
                "exclude_symptoms": ["feces_blood_red", "resp_dyspnea"],
                "differentiation": {},
                "treatment_principle": "大环内酯类或四环素类，疗程要长",
                "common_drugs": ["泰乐菌素", "替米考星", "多西环素"]
            },
            "新城疫": {
                "key_symptoms": ["neck_twisting", "sys_death"],
                "important_symptoms": ["resp_dyspnea", "feces_green", "sys_depression"],
                "supporting_symptoms": ["sys_anorexia", "other_egg_drop"],
                "exclude_symptoms": [],
                "differentiation": {},
                "treatment_principle": "无特效药，以预防为主，发病可用抗生素防继发感染",
                "common_drugs": ["抗生素防继发感染", "维生素增强抵抗力"]
            },
            "传染性支气管炎": {
                "key_symptoms": ["resp_dyspnea", "resp_cough"],
                "important_symptoms": ["resp_rhonchus", "other_egg_drop"],
                "supporting_symptoms": ["sys_depression", "feces_green"],
                "exclude_symptoms": ["neck_twisting"],
                "differentiation": {},
                "treatment_principle": "无特效药，对症治疗，防继发感染",
                "common_drugs": ["抗生素防继发感染", "肾肿解毒药"]
            },
            "组织滴虫病": {
                "key_symptoms": ["comb_cyanosis", "feces_bloody_mucus"],
                "important_symptoms": ["sys_weight_loss", "sys_depression"],
                "supporting_symptoms": ["sys_anorexia"],
                "exclude_symptoms": ["neck_twisting"],
                "differentiation": {},
                "treatment_principle": "甲硝唑类药物治疗",
                "common_drugs": ["地美硝唑", "甲硝唑"]
            },
            "蛔虫病": {
                "key_symptoms": ["sys_weight_loss"],
                "important_symptoms": ["sys_depression", "feces_unformed"],
                "supporting_symptoms": ["feather_ruffled"],
                "exclude_symptoms": ["feces_blood_red", "resp_dyspnea"],
                "differentiation": {},
                "treatment_principle": "驱虫药定期使用",
                "common_drugs": ["阿苯达唑", "左旋咪唑"]
            },
            "绦虫病": {
                "key_symptoms": ["sys_weight_loss"],
                "important_symptoms": ["sys_depression", "feces_unformed"],
                "supporting_symptoms": ["feather_ruffled", "other_paralysis"],
                "exclude_symptoms": ["feces_blood_red"],
                "differentiation": {},
                "treatment_principle": "驱虫药治疗",
                "common_drugs": ["阿苯达唑", "吡喹酮"]
            }
        }
    
    def _calculate_disease_score(self, disease_name: str, selected_symptoms: List[str]) -> Tuple[float, List[str], List[str]]:
        """计算疾病匹配分数"""
        rules = self.disease_diagnosis_rules.get(disease_name, {})
        if not rules:
            return 0.0, [], []
        
        score = 0.0
        matched = []
        unmatched = []
        
        key_weight = 5.0
        important_weight = 3.0
        supporting_weight = 1.5
        exclude_penalty = 10.0
        
        for sym_id in rules.get("key_symptoms", []):
            if sym_id in selected_symptoms:
                score += key_weight * self.symptom_database[sym_id].weight
                matched.append(self.symptom_database[sym_id].name)
            else:
                unmatched.append(f"缺少关键症状: {self.symptom_database[sym_id].name}")
        
        for sym_id in rules.get("important_symptoms", []):
            if sym_id in selected_symptoms:
                score += important_weight * self.symptom_database[sym_id].weight
                matched.append(self.symptom_database[sym_id].name)
        
        for sym_id in rules.get("supporting_symptoms", []):
            if sym_id in selected_symptoms:
                score += supporting_weight * self.symptom_database[sym_id].weight
                matched.append(self.symptom_database[sym_id].name)
        
        for sym_id in rules.get("exclude_symptoms", []):
            if sym_id in selected_symptoms:
                score -= exclude_penalty
        
        return score, matched, unmatched
    
    def _determine_confidence(self, score: float, max_score: float, symptom_count: int) -> str:
        """确定诊断置信度"""
        if max_score == 0:
            return ConfidenceLevel.LOW.value
        
        ratio = score / max_score
        
        if symptom_count == 1:
            if ratio >= 0.7 and score >= 10.0:
                return ConfidenceLevel.MEDIUM.value
            else:
                return ConfidenceLevel.LOW.value
        elif symptom_count == 2:
            if ratio >= 0.6:
                return ConfidenceLevel.MEDIUM.value
            else:
                return ConfidenceLevel.LOW.value
        else:
            if ratio >= 0.7:
                return ConfidenceLevel.HIGH.value
            elif ratio >= 0.4:
                return ConfidenceLevel.MEDIUM.value
            else:
                return ConfidenceLevel.LOW.value
    
    def diagnose(self, selected_symptom_ids: List[str]) -> DiagnosisResult:
        """执行多症状组合诊断"""
        if not selected_symptom_ids:
            return DiagnosisResult(
                status=DiagnosisStatus.UNCERTAIN.value,
                primary_disease=None,
                secondary_diseases=[],
                all_symptoms=[],
                confidence_level=ConfidenceLevel.LOW.value,
                safety_level="谨慎用药",
                recommendations={"error": "未选择任何症状"}
            )
        
        candidates = []
        max_score = 0.0
        
        for disease_name in self.disease_diagnosis_rules:
            score, matched, unmatched = self._calculate_disease_score(disease_name, selected_symptom_ids)
            if score > 0:
                rules = self.disease_diagnosis_rules[disease_name]
                differentiation_points = []
                
                for diff_disease, diff_symptoms in rules.get("differentiation", {}).items():
                    has_diff = any(s in selected_symptom_ids for s in diff_symptoms)
                    if has_diff:
                        diff_names = [self.symptom_database[s].name for s in diff_symptoms if s in self.symptom_database]
                        differentiation_points.append(f"出现{','.join(diff_names)}，更可能是{diff_disease}")
                
                candidate = DiseaseCandidate(
                    name=disease_name,
                    score=score,
                    confidence="",
                    matched_symptoms=matched,
                    unmatched_symptoms=unmatched,
                    differentiation_points=differentiation_points,
                    treatment_principle=rules.get("treatment_principle", ""),
                    common_drugs=rules.get("common_drugs", [])
                )
                candidates.append(candidate)
                if score > max_score:
                    max_score = score
        
        candidates.sort(key=lambda x: x.score, reverse=True)
        
        for candidate in candidates:
            candidate.confidence = self._determine_confidence(candidate.score, max_score, len(selected_symptom_ids))
        
        primary_disease = candidates[0] if candidates else None
        secondary_diseases = candidates[1:3] if len(candidates) > 1 else []
        
        confidence_level = primary_disease.confidence if primary_disease else ConfidenceLevel.LOW.value
        
        safety_level = self._get_safety_level(confidence_level, len(selected_symptom_ids))
        
        all_symptoms = [self.symptom_database[s].name for s in selected_symptom_ids if s in self.symptom_database]
        
        recommendations = self._generate_diagnosis_recommendations(primary_disease, secondary_diseases, confidence_level)
        
        return DiagnosisResult(
            status=self._get_status(confidence_level),
            primary_disease=primary_disease,
            secondary_diseases=secondary_diseases,
            all_symptoms=all_symptoms,
            confidence_level=confidence_level,
            safety_level=safety_level,
            recommendations=recommendations
        )
    
    def _get_status(self, confidence_level: str) -> str:
        """获取诊断状态"""
        if confidence_level == ConfidenceLevel.HIGH.value:
            return DiagnosisStatus.CONFIRMED.value
        elif confidence_level == ConfidenceLevel.MEDIUM.value:
            return DiagnosisStatus.SUSPECTED.value
        else:
            return DiagnosisStatus.UNCERTAIN.value
    
    def _get_safety_level(self, confidence_level: str, symptom_count: int) -> str:
        """获取用药安全等级"""
        if confidence_level == ConfidenceLevel.HIGH.value and symptom_count >= 3:
            return "常规用药"
        elif confidence_level == ConfidenceLevel.HIGH.value:
            return "谨慎用药"
        elif confidence_level == ConfidenceLevel.MEDIUM.value:
            return "谨慎用药"
        else:
            return "严格谨慎"
    
    def _generate_diagnosis_recommendations(self, primary: Optional[DiseaseCandidate], 
                                           secondary: List[DiseaseCandidate], 
                                           confidence: str) -> Dict:
        """生成诊断推荐"""
        recommendations = {
            "advice": "",
            "action_items": [],
            "follow_up": "",
            "consult_veterinarian": False
        }
        
        if confidence == ConfidenceLevel.HIGH.value:
            recommendations["advice"] = f"诊断置信度高，初步判断为{primary.name if primary else '未知疾病'}。建议按推荐方案用药，同时加强观察。"
            recommendations["action_items"] = [
                "立即按推荐药物治疗",
                "加强饲养管理，改善环境",
                "密切观察病情变化",
                "记录用药情况"
            ]
            recommendations["follow_up"] = "用药48小时后观察疗效，若无改善需复诊或送检"
            recommendations["consult_veterinarian"] = False
        
        elif confidence == ConfidenceLevel.MEDIUM.value:
            primary_name = primary.name if primary else "未知疾病"
            recommendations["advice"] = f"诊断置信度中等，最可能为{primary_name}。建议先按推荐方案用药，同时考虑送检确认。"
            recommendations["action_items"] = [
                "按推荐药物进行治疗",
                "建议采集病料送检确诊",
                "加强消毒隔离",
                "密切观察，准备备选方案"
            ]
            recommendations["follow_up"] = "用药24小时后评估疗效，3天无改善必须更换方案或咨询兽医"
            recommendations["consult_veterinarian"] = True
        
        else:
            recommendations["advice"] = "症状信息不足，无法准确判断疾病类型。建议优先咨询专业兽医，或选择安全性高的药物进行试探性治疗。"
            recommendations["action_items"] = [
                "立即联系专业兽医出诊",
                "或选择中兽药进行温和调理",
                "加强环境管理减少应激",
                "准备送检病料"
            ]
            recommendations["follow_up"] = "尽快获得明确诊断"
            recommendations["consult_veterinarian"] = True
        
        return recommendations
    
    def get_all_symptoms_by_category(self) -> Dict[str, List[SymptomItem]]:
        """按类别获取所有症状"""
        categories = {}
        for symptom in self.symptom_database.values():
            if symptom.category not in categories:
                categories[symptom.category] = []
            categories[symptom.category].append(symptom)
        return categories


class SymptomQuestionnaire:
    """引导式问诊流程"""
    
    def __init__(self):
        self.diagnosis_engine = SymptomBasedDiagnosisEngine()
        self.steps = self._init_steps()
    
    def _init_steps(self) -> List[QuestionnaireStep]:
        """初始化问诊步骤"""
        symptoms = self.diagnosis_engine.symptom_database
        
        steps = [
            QuestionnaireStep(
                step_id="step1",
                title="第一步：外观观察",
                category="外观",
                description="请仔细观察家禽的外观表现，选择符合的症状：",
                symptoms=[symptoms[s] for s in ["feather_ruffled", "comb_pale", "comb_cyanosis", "eyes_closed", "body_weak", "wings_drooped", "head_shaking", "neck_twisting"]]
            ),
            QuestionnaireStep(
                step_id="step2",
                title="第二步：粪便检查",
                category="粪便",
                description="请观察家禽的粪便状态，选择符合的症状：",
                symptoms=[symptoms[s] for s in ["feces_blood_red", "feces_blood_dark", "feces_white", "feces_green", "feces_yellow", "feces_watery", "feces_unformed", "feces_bloody_mucus"]]
            ),
            QuestionnaireStep(
                step_id="step3",
                title="第三步：呼吸表现",
                category="呼吸道",
                description="请观察家禽的呼吸情况，选择符合的症状：",
                symptoms=[symptoms[s] for s in ["resp_cough", "resp_sneeze", "resp_nasal_discharge", "resp_rhonchus", "resp_open_mouth", "resp_dyspnea", "resp_gasping"]]
            ),
            QuestionnaireStep(
                step_id="step4",
                title="第四步：全身状况",
                category="全身",
                description="请观察家禽的整体状态，选择符合的症状：",
                symptoms=[symptoms[s] for s in ["sys_depression", "sys_anorexia", "sys_fever", "sys_weight_loss", "sys_death", "sys_tremor", "sys_paralysis", "sys_drowsy"]]
            ),
            QuestionnaireStep(
                step_id="step5",
                title="第五步：其他症状",
                category="其他",
                description="请选择其他可能存在的症状：",
                symptoms=[symptoms[s] for s in ["other_diarrhea", "other_egg_drop", "other_deformed_egg", "other_sand_egg", "other_blood_spot", "other_joint_swelling", "other_skin_lesion", "other_abdominal_distension"]]
            )
        ]
        
        return steps
    
    def get_step(self, step_index: int) -> Optional[QuestionnaireStep]:
        """获取指定步骤"""
        if 0 <= step_index < len(self.steps):
            return self.steps[step_index]
        return None
    
    def get_total_steps(self) -> int:
        """获取总步骤数"""
        return len(self.steps)
    
    def complete_questionnaire(self, all_selected_symptoms: List[str]) -> DiagnosisResult:
        """完成问诊，获取诊断结果"""
        return self.diagnosis_engine.diagnose(all_selected_symptoms)


class MedicationSafetyGuardian:
    """用药安全分级与对症保障机制"""
    
    def __init__(self):
        self.confidence_strategies = {
            ConfidenceLevel.HIGH.value: {
                "strategy": "targeted",
                "description": "诊断明确，可直接推荐对症药物",
                "drug_types": ["化药", "中兽药"],
                "max_drugs": 3,
                "warning": "",
                "follow_up_required": False,
                "follow_up_time": "48小时"
            },
            ConfidenceLevel.MEDIUM.value: {
                "strategy": "broad_spectrum",
                "description": "诊断不确定，推荐广谱药物+中兽药组合",
                "drug_types": ["中兽药", "化药"],
                "max_drugs": 2,
                "warning": "⚠️ 建议送检确认诊断",
                "follow_up_required": True,
                "follow_up_time": "24小时"
            },
            ConfidenceLevel.LOW.value: {
                "strategy": "safety_first",
                "description": "诊断高度不确定，仅推荐安全性高的中兽药",
                "drug_types": ["中兽药"],
                "max_drugs": 1,
                "warning": "❌ 强烈建议咨询兽医，当前仅提供辅助建议",
                "follow_up_required": True,
                "follow_up_time": "立即"
            }
        }
        
        self.treatment_rules = {
            "PARASITIC": {
                "high_confidence": ["磺胺喹噁啉钠", "磺胺氯吡嗪钠"],
                "medium_confidence": ["地美硝唑"],
                "low_confidence": ["益生菌"]
            },
            "RESPIRATORY": {
                "high_confidence": ["替米考星", "多西环素"],
                "medium_confidence": ["氟苯尼考"],
                "low_confidence": ["中药呼吸道药"]
            },
            "DIGESTIVE": {
                "high_confidence": ["黏菌素", "阿莫西林"],
                "medium_confidence": ["新霉素"],
                "low_confidence": ["益生菌", "中药肠道药"]
            },
            "BACTERIAL": {
                "high_confidence": ["氟苯尼考", "恩诺沙星"],
                "medium_confidence": ["多西环素"],
                "low_confidence": ["中药抗菌"]
            },
            "VIRAL": {
                "high_confidence": ["抗生素防继发", "中药抗病毒"],
                "medium_confidence": ["中药抗病毒"],
                "low_confidence": ["中药免疫增强"]
            }
        }
    
    def get_recommendation_strategy(self, confidence_level: str) -> Dict:
        """根据置信度获取推荐策略"""
        return self.confidence_strategies.get(confidence_level, 
                                             self.confidence_strategies[ConfidenceLevel.LOW.value])
    
    def validate_recommendation(self, confidence_level: str, drug_types: List[str]) -> Dict:
        """验证推荐方案是否符合安全策略"""
        strategy = self.get_recommendation_strategy(confidence_level)
        
        if confidence_level == ConfidenceLevel.LOW.value:
            if any(dt == "化药" for dt in drug_types):
                return {
                    "valid": False,
                    "reason": "低置信度下禁止推荐化药，仅允许中兽药",
                    "suggestion": "请更换为中兽药或咨询兽医"
                }
        
        if confidence_level == ConfidenceLevel.MEDIUM.value:
            chem_count = drug_types.count("化药")
            if chem_count > 1:
                return {
                    "valid": False,
                    "reason": "中置信度下化药数量不能超过1种",
                    "suggestion": "建议减少化药种类，增加中兽药"
                }
        
        return {
            "valid": True,
            "reason": "符合安全策略",
            "suggestion": ""
        }
    
    def generate_follow_up_plan(self, confidence_level: str, diagnosis_result: DiagnosisResult) -> Dict:
        """生成随访计划"""
        strategy = self.get_recommendation_strategy(confidence_level)
        
        follow_up = {
            "time": strategy["follow_up_time"],
            "required": strategy["follow_up_required"],
            "indicators": [
                "采食量变化",
                "粪便形态",
                "呼吸道声音",
                "精神状态",
                "伤亡数量"
            ],
            "action_if_no_improvement": "",
            "action_if_improvement": ""
        }
        
        if confidence_level == ConfidenceLevel.HIGH.value:
            follow_up["action_if_no_improvement"] = "用药48小时无改善，考虑更换药物或复诊"
            follow_up["action_if_improvement"] = "继续按疗程用药，巩固疗效"
        
        elif confidence_level == ConfidenceLevel.MEDIUM.value:
            follow_up["action_if_no_improvement"] = "用药24小时无改善，必须更换方案或立即咨询兽医"
            follow_up["action_if_improvement"] = "继续用药，同时建议送检确认"
        
        else:
            follow_up["action_if_no_improvement"] = "立即联系兽医，不要自行调整用药"
            follow_up["action_if_improvement"] = "继续观察，尽快获得明确诊断"
        
        return follow_up


def get_diagnosis_engine() -> SymptomBasedDiagnosisEngine:
    """获取诊断引擎实例"""
    return SymptomBasedDiagnosisEngine()


def get_questionnaire() -> SymptomQuestionnaire:
    """获取问诊流程实例"""
    return SymptomQuestionnaire()


def get_safety_guardian() -> MedicationSafetyGuardian:
    """获取用药安全保障实例"""
    return MedicationSafetyGuardian()