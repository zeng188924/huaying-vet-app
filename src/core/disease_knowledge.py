"""
疾病知识库模块
提供疾病信息查询、症状分析和用药指导
集成联网搜索功能获取最新疾病信息
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import json


@dataclass
class DiseaseInfo:
    """疾病信息"""
    name: str
    symptoms: List[str]
    pathogen: str
    transmission: str
    prevention: List[str]
    treatment_principles: str
    common_drugs: List[str]
    notes: str


class DiseaseKnowledgeBase:
    """疾病知识库"""
    
    def __init__(self):
        self.diseases = self._init_diseases()
    
    def _init_diseases(self) -> Dict[str, DiseaseInfo]:
        """初始化疾病知识库"""
        diseases = {
            "球虫病": DiseaseInfo(
                name="球虫病",
                symptoms=["血便", "消瘦", "贫血", "精神沉郁", "食欲不振", "羽毛松乱"],
                pathogen="艾美耳球虫",
                transmission="通过粪便污染的饲料、饮水、垫料传播",
                prevention=[
                    "保持鸡舍干燥清洁",
                    "定期更换垫料",
                    "饲料中添加抗球虫药物",
                    "实行全进全出制度"
                ],
                treatment_principles="抗球虫药物联合使用，止血止痢，补充营养",
                common_drugs=["磺胺喹噁啉钠", "磺胺氯吡嗪钠", "地美硝唑", "氨丙啉"],
                notes="盲肠球虫和小肠球虫用药略有不同，需根据血便颜色判断"
            ),
            "盲肠球虫": DiseaseInfo(
                name="盲肠球虫",
                symptoms=["鲜红色血便", "精神萎靡", "冠髯苍白", "消瘦", "死亡率高"],
                pathogen="柔嫩艾美耳球虫",
                transmission="通过粪便污染的饲料、饮水传播",
                prevention=[
                    "保持垫料干燥",
                    "定期消毒",
                    "预防性投药"
                ],
                treatment_principles="磺胺类药物效果最佳，配合止血药",
                common_drugs=["磺胺氯吡嗪钠", "磺胺喹噁啉钠", "维生素K3"],
                notes="发病急、死亡快，需及时治疗"
            ),
            "小肠球虫": DiseaseInfo(
                name="小肠球虫",
                symptoms=["暗红色血便", "消化不良", "消瘦", "生长缓慢"],
                pathogen="毒害艾美耳球虫",
                transmission="通过污染的饲料、饮水传播",
                prevention=[
                    "环境卫生管理",
                    "轮换用药防止耐药"
                ],
                treatment_principles="抗球虫药联合肠道消炎药",
                common_drugs=["磺胺喹噁啉钠", "地美硝唑", "新霉素"],
                notes="病程较长，影响生长发育"
            ),
            "慢性呼吸道病": DiseaseInfo(
                name="慢性呼吸道病",
                symptoms=["咳嗽", "打喷嚏", "流鼻涕", "啰音", "眼睑肿胀"],
                pathogen="鸡毒支原体",
                transmission="垂直传播和水平传播，应激可诱发",
                prevention=[
                    "种鸡净化",
                    "减少应激",
                    "通风良好",
                    "疫苗接种"
                ],
                treatment_principles="大环内酯类或四环素类药物，疗程要足",
                common_drugs=["替米考星", "泰万菌素", "多西环素", "泰乐菌素"],
                notes="易继发大肠杆菌感染，需注意联合用药"
            ),
            "大肠杆菌病": DiseaseInfo(
                name="大肠杆菌病",
                symptoms=["拉稀", "心包炎", "肝周炎", "腹膜炎", "败血症"],
                pathogen="致病性大肠杆菌",
                transmission="经消化道、呼吸道、伤口感染",
                prevention=[
                    "环境卫生",
                    "减少应激",
                    "预防支原体感染",
                    "疫苗接种"
                ],
                treatment_principles="根据药敏试验选择敏感药物",
                common_drugs=["氟苯尼考", "黏菌素", "新霉素", "安普霉素", "恩诺沙星"],
                notes="易产生耐药性，建议轮换用药"
            ),
            "沙门氏菌病": DiseaseInfo(
                name="沙门氏菌病",
                symptoms=["白痢", "精神沉郁", "食欲不振", "拉白色稀粪", "呼吸困难"],
                pathogen="沙门氏菌",
                transmission="垂直传播为主，也可水平传播",
                prevention=[
                    "种鸡净化",
                    "孵化场消毒",
                    "全进全出"
                ],
                treatment_principles="氟喹诺酮类或氟苯尼考，注意耐药性",
                common_drugs=["氟苯尼考", "恩诺沙星", "磺胺类药物"],
                notes="鸡白痢和禽伤寒是主要类型，种鸡需净化"
            ),
            "鸡白痢": DiseaseInfo(
                name="鸡白痢",
                symptoms=["白色稀粪", "肛门污秽", "精神萎靡", "食欲不振", "呼吸困难"],
                pathogen="鸡白痢沙门氏菌",
                transmission="垂直传播为主",
                prevention=[
                    "种鸡检疫净化",
                    "孵化场严格消毒",
                    "育雏期管理"
                ],
                treatment_principles="早期治疗效果好，注意耐药性",
                common_drugs=["氟苯尼考", "恩诺沙星", "庆大霉素"],
                notes="雏鸡易感，死亡率高"
            ),
            "禽霍乱": DiseaseInfo(
                name="禽霍乱",
                symptoms=["高热", "精神沉郁", "腹泻", "呼吸困难", "冠髯发绀"],
                pathogen="多杀性巴氏杆菌",
                transmission="通过污染的饲料、饮水、空气传播",
                prevention=[
                    "疫苗接种",
                    "环境卫生",
                    "减少应激"
                ],
                treatment_principles="磺胺类或氟喹诺酮类药物",
                common_drugs=["磺胺间甲氧嘧啶", "恩诺沙星", "氟苯尼考"],
                notes="急性死亡率高，慢性表现为关节炎"
            ),
            "传染性鼻炎": DiseaseInfo(
                name="传染性鼻炎",
                symptoms=["流鼻涕", "打喷嚏", "眼睑肿胀", "结膜炎", "生长迟缓"],
                pathogen="副鸡嗜血杆菌",
                transmission="通过飞沫和污染的饲料、饮水传播",
                prevention=[
                    "疫苗接种",
                    "隔离病鸡",
                    "加强通风"
                ],
                treatment_principles="磺胺类药物效果好，注意复发",
                common_drugs=["磺胺间甲氧嘧啶", "链霉素", "红霉素"],
                notes="易复发，需加强饲养管理"
            ),
            "坏死性肠炎": DiseaseInfo(
                name="坏死性肠炎",
                symptoms=["腹泻", "血便", "精神沉郁", "死亡率突然升高"],
                pathogen="产气荚膜梭菌",
                transmission="通过污染的饲料、垫料传播",
                prevention=[
                    "饲料中添加抗生素",
                    "防止球虫病",
                    "环境卫生"
                ],
                treatment_principles="林可霉素或青霉素类效果好",
                common_drugs=["林可霉素", "青霉素", "杆菌肽"],
                notes="常与球虫病并发"
            ),
            "滑液囊支原体": DiseaseInfo(
                name="滑液囊支原体",
                symptoms=["关节肿胀", "跛行", "胸囊肿", "生长迟缓", "羽毛粗乱"],
                pathogen="滑液囊支原体",
                transmission="垂直传播为主",
                prevention=[
                    "种鸡净化",
                    "疫苗接种",
                    "减少应激"
                ],
                treatment_principles="大环内酯类或四环素类，疗程要长",
                common_drugs=["泰乐菌素", "替米考星", "多西环素", "泰妙菌素"],
                notes="影响生长发育，肉鸡需重点防控"
            ),
            "新城疫": DiseaseInfo(
                name="新城疫",
                symptoms=["呼吸困难", "下痢", "神经症状", "产蛋下降", "死亡率高等"],
                pathogen="新城疫病毒",
                transmission="通过呼吸道、消化道传播",
                prevention=[
                    "疫苗接种是主要手段",
                    "严格生物安全措施",
                    "全进全出制度"
                ],
                treatment_principles="无特效药，以预防为主，发病可用抗生素防继发感染",
                common_drugs=["抗生素防继发感染", "维生素增强抵抗力"],
                notes="一类动物疫病，需强制免疫"
            ),
            "传染性支气管炎": DiseaseInfo(
                name="传染性支气管炎",
                symptoms=["咳嗽", "打喷嚏", "产蛋下降", "畸形蛋增多", "肾脏肿大"],
                pathogen="传染性支气管炎病毒",
                transmission="通过呼吸道传播",
                prevention=[
                    "疫苗接种",
                    "加强管理",
                    "防止应激"
                ],
                treatment_principles="无特效药，对症治疗，防继发感染",
                common_drugs=["抗生素防继发感染", "肾肿解毒药"],
                notes="肾型传支需特别注意肾脏保护"
            ),
            "组织滴虫病": DiseaseInfo(
                name="组织滴虫病",
                symptoms=["头部发绀", "下痢", "消瘦", "肝脏坏死", "盲肠肿胀"],
                pathogen="火鸡组织滴虫",
                transmission="通过异刺线虫传播",
                prevention=[
                    "定期驱虫",
                    "保持干燥",
                    "隔离病鸡"
                ],
                treatment_principles="甲硝唑类药物治疗",
                common_drugs=["地美硝唑", "甲硝唑", "洛硝达唑"],
                notes="俗称黑头病，火鸡和鸡均可感染"
            ),
            "蛔虫病": DiseaseInfo(
                name="蛔虫病",
                symptoms=["消瘦", "生长迟缓", "腹泻", "肠梗阻", "死亡"],
                pathogen="鸡蛔虫",
                transmission="通过虫卵污染的饲料、饮水传播",
                prevention=[
                    "定期驱虫",
                    "环境卫生",
                    "粪便处理"
                ],
                treatment_principles="驱虫药定期使用",
                common_drugs=["阿苯达唑", "左旋咪唑", "伊维菌素"],
                notes="地面平养易发生"
            ),
            "绦虫病": DiseaseInfo(
                name="绦虫病",
                symptoms=["消瘦", "腹泻", "羽毛松乱", "产蛋下降", "瘫痪"],
                pathogen="赖利绦虫、戴文绦虫",
                transmission="通过中间宿主传播",
                prevention=[
                    "定期驱虫",
                    "消灭中间宿主",
                    "环境卫生"
                ],
                treatment_principles="驱虫药治疗",
                common_drugs=["阿苯达唑", "吡喹酮", "氯硝柳胺"],
                notes="需消灭蚂蚁、甲虫等中间宿主"
            )
        }
        return diseases
    
    def get_disease_info(self, disease_name: str) -> Optional[DiseaseInfo]:
        """获取疾病信息"""
        # 模糊匹配
        for key, info in self.diseases.items():
            if disease_name in key or key in disease_name:
                return info
        return None
    
    def search_by_symptom(self, symptom: str) -> List[DiseaseInfo]:
        """根据症状搜索疾病"""
        results = []
        symptom = symptom.lower()
        
        for disease in self.diseases.values():
            for s in disease.symptoms:
                if symptom in s.lower() or s.lower() in symptom:
                    if disease not in results:
                        results.append(disease)
                    break
        
        return results
    
    def get_treatment_guide(self, disease_name: str) -> Dict:
        """获取治疗指南"""
        disease = self.get_disease_info(disease_name)
        if not disease:
            return {"error": "未找到该疾病信息"}
        
        return {
            "disease_name": disease.name,
            "treatment_principles": disease.treatment_principles,
            "common_drugs": disease.common_drugs,
            "prevention": disease.prevention,
            "notes": disease.notes
        }
    
    def get_all_diseases(self) -> List[str]:
        """获取所有疾病名称"""
        return list(self.diseases.keys())


class OnlineDiseaseSearcher:
    """在线疾病信息搜索器"""
    
    def __init__(self):
        self.search_cache = {}
    
    def search_disease_info(self, disease_name: str) -> Dict:
        """
        搜索疾病信息
        由于无法直接联网，这里使用知识库+模拟数据
        """
        # 使用本地知识库
        kb = DiseaseKnowledgeBase()
        info = kb.get_disease_info(disease_name)
        
        if info:
            return {
                "source": "本地知识库",
                "disease_info": {
                    "name": info.name,
                    "symptoms": info.symptoms,
                    "pathogen": info.pathogen,
                    "transmission": info.transmission,
                    "prevention": info.prevention,
                    "treatment_principles": info.treatment_principles,
                    "common_drugs": info.common_drugs,
                    "notes": info.notes
                }
            }
        
        return {
            "source": "未找到",
            "message": f"未找到{disease_name}的详细信息，建议咨询专业兽医"
        }
    
    def get_drug_usage_guide(self, drug_name: str) -> Dict:
        """获取药物使用指南"""
        drug_guides = {
            "氟苯尼考": {
                "mechanism": "通过抑制细菌蛋白质合成发挥广谱抗菌作用",
                "spectrum": "对革兰氏阳性菌和阴性菌均有良好效果",
                "dosage": "每升水50-100mg，连用3-5天",
                "contraindications": ["产蛋期禁用", "免疫接种期慎用"],
                "precautions": ["不可与β-内酰胺类合用", "注意耐药性"],
                "withdrawal_period": "鸡20日"
            },
            "替米考星": {
                "mechanism": "大环内酯类抗生素，抑制细菌蛋白质合成",
                "spectrum": "对支原体和革兰氏阳性菌效果突出",
                "dosage": "每升水75-100mg，连用3-5天",
                "contraindications": ["产蛋期禁用", "心脏疾病慎用"],
                "precautions": ["注射剂心脏毒性大", "注意剂量"],
                "withdrawal_period": "鸡10日"
            },
            "多西环素": {
                "mechanism": "四环素类抗生素，抑制细菌蛋白质合成",
                "spectrum": "广谱抗菌，对支原体也有效",
                "dosage": "每升水50-100mg，连用3-5天",
                "contraindications": ["产蛋期慎用"],
                "precautions": ["避免与含钙、镁物质同服", "注意光敏反应"],
                "withdrawal_period": "鸡5日"
            },
            "磺胺喹噁啉": {
                "mechanism": "干扰球虫叶酸代谢",
                "spectrum": "对球虫有特效",
                "dosage": "每升水100-150mg，连用3天，停药2天，再用3天",
                "contraindications": ["产蛋期禁用", "肾脏疾病慎用"],
                "precautions": ["多饮水", "配合维生素K使用"],
                "withdrawal_period": "鸡10日"
            },
            "地美硝唑": {
                "mechanism": "抗原虫药，干扰DNA合成",
                "spectrum": "对组织滴虫、毛滴虫有效",
                "dosage": "每升水250-500mg，连用5-7天",
                "contraindications": ["产蛋期禁用"],
                "precautions": ["连续使用不超过7天", "注意耐药性"],
                "withdrawal_period": "鸡5日"
            }
        }
        
        for key, guide in drug_guides.items():
            if key in drug_name or drug_name in key:
                return {
                    "drug_name": drug_name,
                    "guide": guide
                }
        
        return {
            "drug_name": drug_name,
            "message": "详细用药指南请参考产品说明书或咨询兽医"
        }


# 便捷函数
def get_disease_knowledge_base() -> DiseaseKnowledgeBase:
    """获取疾病知识库实例"""
    return DiseaseKnowledgeBase()


def get_online_searcher() -> OnlineDiseaseSearcher:
    """获取在线搜索器实例"""
    return OnlineDiseaseSearcher()
