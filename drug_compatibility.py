# -*- coding: utf-8 -*-
"""
药物配伍禁忌检测模块
用于检测药物组合中是否存在配伍禁忌
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class CompatibilityLevel(Enum):
    """配伍禁忌等级"""
    SAFE = "安全"           # 可以配伍
    CAUTION = "慎用"        # 需谨慎，可能需要调整剂量
    INCOMPATIBLE = "禁忌"   # 禁止配伍


@dataclass
class CompatibilityRule:
    """配伍规则"""
    drug_a: str              # 药物A（成分或类别）
    drug_b: str              # 药物B（成分或类别）
    level: CompatibilityLevel
    reason: str              # 禁忌原因说明
    suggestion: str          # 建议替代方案


@dataclass
class CompatibilityResult:
    """配伍检测结果"""
    is_safe: bool
    level: CompatibilityLevel
    conflicts: List[Dict]
    suggestions: List[str]


class DrugCompatibilityChecker:
    """药物配伍禁忌检测器"""
    
    def __init__(self):
        self.rules: List[CompatibilityRule] = []
        self._init_compatibility_rules()
    
    def _init_compatibility_rules(self):
        """初始化配伍禁忌规则库"""
        
        # ========== 抗生素类配伍禁忌 ==========
        
        # 氟苯尼考相关禁忌
        self.rules.append(CompatibilityRule(
            drug_a="氟苯尼考",
            drug_b="β-内酰胺类",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="氟苯尼考为速效抑菌剂，β-内酰胺类（如青霉素、阿莫西林）为繁殖期杀菌剂，两者合用会产生拮抗作用，降低疗效",
            suggestion="如需联合使用，应先用β-内酰胺类，间隔2-3小时后再用氟苯尼考，或选择其他抗菌药物替代"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="氟苯尼考",
            drug_b="大环内酯类",
            level=CompatibilityLevel.CAUTION,
            reason="两者均为抑菌剂，合用可能增强抑菌效果但不一定增强杀菌效果",
            suggestion="可以合用，但需注意剂量控制，避免过量"
        ))
        
        # 氨基糖苷类相关禁忌
        self.rules.append(CompatibilityRule(
            drug_a="氨基糖苷类",
            drug_b="头孢类",
            level=CompatibilityLevel.CAUTION,
            reason="两者合用可能增加肾毒性",
            suggestion="肾功能不全患畜慎用，需监测肾功能，或选择肾毒性较小的替代药物"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="硫酸庆大霉素",
            drug_b="利尿剂",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="利尿剂可增强氨基糖苷类的耳肾毒性",
            suggestion="避免合用，如需利尿可选择其他类型利尿剂或减少氨基糖苷类剂量"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="硫酸新霉素",
            drug_b="肌肉松弛剂",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="氨基糖苷类可增强肌肉松弛剂的神经肌肉阻滞作用",
            suggestion="避免合用，如需使用需准备钙剂和新斯的明作为解救药"
        ))
        
        # 四环素类相关禁忌
        self.rules.append(CompatibilityRule(
            drug_a="多西环素",
            drug_b="含钙药物",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="钙离子与四环素类形成络合物，影响吸收，降低疗效",
            suggestion="避免同时服用，如需补钙应间隔2-3小时，或选择其他抗菌药物"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="多西环素",
            drug_b="含铝药物",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="铝离子与四环素类形成络合物，影响吸收",
            suggestion="避免同时服用，间隔2-3小时使用"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="多西环素",
            drug_b="含镁药物",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="镁离子与四环素类形成络合物，影响吸收",
            suggestion="避免同时服用，间隔2-3小时使用"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="多西环素",
            drug_b="铁剂",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="铁离子与四环素类形成络合物，相互影响吸收",
            suggestion="如需合用应间隔2-3小时，或选择其他抗菌药物"
        ))
        
        # 氟喹诺酮类相关禁忌
        self.rules.append(CompatibilityRule(
            drug_a="恩诺沙星",
            drug_b="含金属离子药物",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="金属离子（钙、铝、镁、铁等）与氟喹诺酮类形成络合物，影响吸收",
            suggestion="避免同时服用，间隔2-3小时使用"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="恩诺沙星",
            drug_b="茶碱类",
            level=CompatibilityLevel.CAUTION,
            reason="氟喹诺酮类可抑制茶碱代谢，升高血药浓度",
            suggestion="如需合用应减少茶碱剂量，并监测血药浓度"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="恩诺沙星",
            drug_b="非甾体抗炎药",
            level=CompatibilityLevel.CAUTION,
            reason="合用可能增加中枢神经系统兴奋性和惊厥风险",
            suggestion="癫痫患畜禁用，其他患畜需慎用并观察"
        ))
        
        # 磺胺类相关禁忌
        self.rules.append(CompatibilityRule(
            drug_a="磺胺类",
            drug_b="酸性药物",
            level=CompatibilityLevel.CAUTION,
            reason="酸性环境可能增加磺胺类药物的肾毒性",
            suggestion="使用磺胺类时应碱化尿液，多饮水，避免与酸性药物合用"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="磺胺类",
            drug_b="普鲁卡因",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="普鲁卡因代谢产物PABA可拮抗磺胺类的抗菌作用",
            suggestion="避免合用，选择利多卡因等其他局麻药"
        ))
        
        # 林可霉素相关禁忌
        self.rules.append(CompatibilityRule(
            drug_a="林可霉素",
            drug_b="大环内酯类",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="两者作用靶点相同，竞争结合位点，产生拮抗作用",
            suggestion="避免合用，选择其他类型抗菌药物"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="林可霉素",
            drug_b="氯霉素",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="两者作用机制相似，合用产生拮抗作用",
            suggestion="避免合用"
        ))
        
        # 大环内酯类相关禁忌
        self.rules.append(CompatibilityRule(
            drug_a="替米考星",
            drug_b="肾上腺素",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="替米考星可能增强肾上腺素的致心律失常作用",
            suggestion="避免合用，或严密监测心脏功能"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="泰万菌素",
            drug_b="聚醚类抗生素",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="合用可能增强毒性反应",
            suggestion="避免合用"
        ))
        
        # 多黏菌素相关禁忌
        self.rules.append(CompatibilityRule(
            drug_a="黏菌素",
            drug_b="氨基糖苷类",
            level=CompatibilityLevel.CAUTION,
            reason="两者均有肾毒性和神经肌肉阻滞作用，合用毒性增强",
            suggestion="如需合用应减量并严密监测肾功能和神经肌肉功能"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="黏菌素",
            drug_b="肌松药",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="增强神经肌肉阻滞作用，可能导致呼吸麻痹",
            suggestion="避免合用"
        ))
        
        # 硝基咪唑类相关禁忌
        self.rules.append(CompatibilityRule(
            drug_a="地美硝唑",
            drug_b="乙醇",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="可引起双硫仑样反应（面红、头痛、恶心、呕吐等）",
            suggestion="用药期间及停药后3天内禁止饮酒或使用含乙醇的药物"
        ))
        
        # ========== 解热镇痛类配伍禁忌 ==========
        
        self.rules.append(CompatibilityRule(
            drug_a="卡巴匹林钙",
            drug_b="抗凝药",
            level=CompatibilityLevel.CAUTION,
            reason="水杨酸类可增强抗凝作用，增加出血风险",
            suggestion="如需合用应减少抗凝药剂量并监测凝血功能"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="卡巴匹林钙",
            drug_b="糖皮质激素",
            level=CompatibilityLevel.CAUTION,
            reason="合用增加胃肠道溃疡和出血风险",
            suggestion="如需合用应加用胃黏膜保护剂，或选择其他解热镇痛药"
        ))
        
        # ========== 抗寄生虫类配伍禁忌 ==========
        
        self.rules.append(CompatibilityRule(
            drug_a="磺胺喹噁啉钠",
            drug_b="维生素B1",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="磺胺喹噁啉可拮抗维生素B1的作用",
            suggestion="避免同时大量使用，如需补充B族维生素应间隔使用"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="球虫药",
            drug_b="其他球虫药",
            level=CompatibilityLevel.CAUTION,
            reason="不同作用机制的球虫药合用可能增强效果，但也可能增加毒性",
            suggestion="轮换用药优于联合用药，如需联合应咨询兽医"
        ))
        
        # ========== 维生素与矿物质配伍禁忌 ==========
        
        self.rules.append(CompatibilityRule(
            drug_a="维生素C",
            drug_b="维生素B12",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="维生素C可破坏维生素B12的活性",
            suggestion="避免在同一溶液中混合，分开使用"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="维生素C",
            drug_b="铁剂",
            level=CompatibilityLevel.SAFE,
            reason="维生素C可促进铁的吸收",
            suggestion="可以合用，有利于铁剂吸收"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="钙剂",
            drug_b="磷剂",
            level=CompatibilityLevel.CAUTION,
            reason="钙磷比例不当影响吸收，理想比例为2:1",
            suggestion="注意钙磷比例，保持适当比例有利于吸收"
        ))
        
        # ========== 中药配伍禁忌（十八反、十九畏） ==========
        
        self.rules.append(CompatibilityRule(
            drug_a="乌头",
            drug_b="半夏",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="十八反：半蒌贝蔹及攻乌",
            suggestion="禁止配伍"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="甘草",
            drug_b="甘遂",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="十八反：藻戟遂芫俱战草",
            suggestion="禁止配伍"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="藜芦",
            drug_b="人参",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="十八反：诸参辛芍叛藜芦",
            suggestion="禁止配伍"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="硫黄",
            drug_b="朴硝",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="十九畏：硫黄原是火中精，朴硝一见便相争",
            suggestion="禁止配伍"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="水银",
            drug_b="砒霜",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="十九畏：水银莫与砒霜见",
            suggestion="禁止配伍"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="狼毒",
            drug_b="密陀僧",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="十九畏：狼毒最怕密陀僧",
            suggestion="禁止配伍"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="巴豆",
            drug_b="牵牛",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="十九畏：巴豆性烈最为上，偏与牵牛不顺情",
            suggestion="禁止配伍"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="丁香",
            drug_b="郁金",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="十九畏：丁香莫与郁金见",
            suggestion="禁止配伍"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="川乌草乌",
            drug_b="犀角",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="十九畏：川乌草乌不顺犀",
            suggestion="禁止配伍"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="人参",
            drug_b="五灵脂",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="十九畏：人参最怕五灵脂",
            suggestion="禁止配伍"
        ))
        
        self.rules.append(CompatibilityRule(
            drug_a="官桂",
            drug_b="赤石脂",
            level=CompatibilityLevel.INCOMPATIBLE,
            reason="十九畏：官桂善能调冷气，若逢石脂便相欺",
            suggestion="禁止配伍"
        ))
    
    def check_compatibility(self, drugs: List[Dict]) -> CompatibilityResult:
        """
        检查药物组合的配伍禁忌
        
        Args:
            drugs: 药物列表，每个药物为包含name、component等信息的字典
            
        Returns:
            CompatibilityResult: 配伍检测结果
        """
        conflicts = []
        suggestions = []
        max_level = CompatibilityLevel.SAFE
        
        # 两两检查所有药物组合
        for i in range(len(drugs)):
            for j in range(i + 1, len(drugs)):
                drug_a = drugs[i]
                drug_b = drugs[j]
                
                # 检查这对药物是否有配伍禁忌
                conflict = self._check_pair(drug_a, drug_b)
                if conflict:
                    conflicts.append(conflict)
                    if conflict['level'] == CompatibilityLevel.INCOMPATIBLE:
                        max_level = CompatibilityLevel.INCOMPATIBLE
                    elif conflict['level'] == CompatibilityLevel.CAUTION and max_level != CompatibilityLevel.INCOMPATIBLE:
                        max_level = CompatibilityLevel.CAUTION
                    
                    if conflict['suggestion'] not in suggestions:
                        suggestions.append(conflict['suggestion'])
        
        return CompatibilityResult(
            is_safe=(max_level == CompatibilityLevel.SAFE),
            level=max_level,
            conflicts=conflicts,
            suggestions=suggestions
        )
    
    def _check_pair(self, drug_a: Dict, drug_b: Dict) -> Optional[Dict]:
        """检查一对药物是否有配伍禁忌"""
        
        # 获取药物的成分和名称
        components_a = self._get_components(drug_a)
        components_b = self._get_components(drug_b)
        
        # 检查所有规则
        for rule in self.rules:
            # 检查是否匹配规则
            match_a = self._matches(components_a, rule.drug_a)
            match_b = self._matches(components_b, rule.drug_b)
            
            # 双向检查（A+B 或 B+A）
            if (match_a and match_b) or (self._matches(components_b, rule.drug_a) and self._matches(components_a, rule.drug_b)):
                return {
                    'drug_a': drug_a.get('name', '未知药物'),
                    'drug_b': drug_b.get('name', '未知药物'),
                    'component_a': rule.drug_a,
                    'component_b': rule.drug_b,
                    'level': rule.level,
                    'reason': rule.reason,
                    'suggestion': rule.suggestion
                }
        
        return None
    
    def _get_components(self, drug: Dict) -> List[str]:
        """获取药物的所有标识（名称、成分、类别）"""
        components = []
        
        if 'name' in drug and drug['name']:
            components.append(drug['name'])
        if 'component' in drug and drug['component']:
            components.append(drug['component'])
        if 'main_component' in drug and drug['main_component']:
            components.append(drug['main_component'])
        if 'content' in drug and drug['content']:
            components.append(drug['content'])
        if 'category' in drug and drug['category']:
            components.append(drug['category'])
            
        return components
    
    def _matches(self, components: List[str], rule_term: str) -> bool:
        """检查药物成分是否匹配规则中的术语"""
        rule_term_lower = rule_term.lower()
        
        for component in components:
            component_lower = component.lower()
            # 完全匹配或包含关系
            if rule_term_lower in component_lower or component_lower in rule_term_lower:
                return True
            
            # 特殊匹配逻辑
            if self._special_match(component_lower, rule_term_lower):
                return True
        
        return False
    
    def _special_match(self, component: str, rule_term: str) -> bool:
        """特殊匹配逻辑，处理同义词和类别匹配"""
        
        # 氨基糖苷类包含的药物
        aminoglycosides = ['庆大霉素', '新霉素', '卡那霉素', '安普霉素', '链霉素', '阿米卡星']
        if rule_term == '氨基糖苷类':
            return any(drug in component for drug in aminoglycosides)
        
        # β-内酰胺类包含的药物
        beta_lactams = ['青霉素', '阿莫西林', '头孢', '氨苄西林']
        if rule_term == 'β-内酰胺类':
            return any(drug in component for drug in beta_lactams)
        
        # 大环内酯类包含的药物
        macrolides = ['替米考星', '泰万菌素', '泰乐菌素', '红霉素', '阿奇霉素']
        if rule_term == '大环内酯类':
            return any(drug in component for drug in macrolides)
        
        # 四环素类包含的药物
        tetracyclines = ['多西环素', '四环素', '土霉素', '金霉素']
        if rule_term == '四环素类' or rule_term == '多西环素':
            return any(drug in component for drug in tetracyclines)
        
        # 氟喹诺酮类包含的药物
        fluoroquinolones = ['恩诺沙星', '环丙沙星', '氧氟沙星', '诺氟沙星']
        if rule_term == '氟喹诺酮类' or rule_term == '恩诺沙星':
            return any(drug in component for drug in fluoroquinolones)
        
        # 磺胺类包含的药物
        sulfonamides = ['磺胺', '磺胺嘧啶', '磺胺甲噁唑', '磺胺间甲氧嘧啶', '磺胺氯吡嗪', '磺胺喹噁啉']
        if rule_term == '磺胺类':
            return any(drug in component for drug in sulfonamides)
        
        # 头孢类包含的药物
        cephalosporins = ['头孢', '头孢噻呋', '头孢唑林', '头孢氨苄']
        if rule_term == '头孢类':
            return any(drug in component for drug in cephalosporins)
        
        # 聚醚类抗生素
        polyethers = ['莫能菌素', '盐霉素', '马杜霉素', '拉沙洛菌素']
        if rule_term == '聚醚类抗生素':
            return any(drug in component for drug in polyethers)
        
        # 球虫药类别
        coccidiostats = ['磺胺喹噁啉', '磺胺氯吡嗪', '地克珠利', '妥曲珠利', '莫能菌素', '盐霉素']
        if rule_term == '球虫药':
            return any(drug in component for drug in coccidiostats)
        
        # 含金属离子药物
        metal_ions = ['钙', '铝', '镁', '铁', '锌', '铜']
        if rule_term == '含钙药物' or rule_term == '含金属离子药物':
            return any(ion in component for ion in metal_ions)
        
        # 林可霉素
        if rule_term == '林可霉素':
            return '林可霉素' in component
        
        # 黏菌素
        if rule_term == '黏菌素':
            return '黏菌素' in component or '多黏菌素' in component
        
        # 地美硝唑
        if rule_term == '地美硝唑':
            return '地美硝唑' in component or '甲硝唑' in component
        
        # 卡巴匹林钙
        if rule_term == '卡巴匹林钙':
            return '卡巴匹林' in component or '阿司匹林' in component
        
        return False
    
    def get_all_rules(self) -> List[Dict]:
        """获取所有配伍规则（用于展示）"""
        return [
            {
                'drug_a': rule.drug_a,
                'drug_b': rule.drug_b,
                'level': rule.level.value,
                'reason': rule.reason,
                'suggestion': rule.suggestion
            }
            for rule in self.rules
        ]


# 全局配伍检测器实例
_compatibility_checker = None

def get_compatibility_checker() -> DrugCompatibilityChecker:
    """获取配伍检测器单例"""
    global _compatibility_checker
    if _compatibility_checker is None:
        _compatibility_checker = DrugCompatibilityChecker()
    return _compatibility_checker


def check_drug_compatibility(drugs: List[Dict]) -> CompatibilityResult:
    """
    便捷函数：检查药物配伍禁忌
    
    使用示例:
        drugs = [
            {'name': '氟苯尼考粉', 'component': '氟苯尼考'},
            {'name': '阿莫西林可溶性粉', 'component': '阿莫西林'}
        ]
        result = check_drug_compatibility(drugs)
    """
    checker = get_compatibility_checker()
    return checker.check_compatibility(drugs)


if __name__ == "__main__":
    # 测试配伍检测功能
    print("=" * 60)
    print("药物配伍禁忌检测系统测试")
    print("=" * 60)
    
    # 测试案例1：氟苯尼考 + 阿莫西林（禁忌）
    print("\n【测试案例1】氟苯尼考 + 阿莫西林")
    drugs1 = [
        {'name': '氟苯尼考粉', 'component': '氟苯尼考'},
        {'name': '阿莫西林可溶性粉', 'component': '阿莫西林'}
    ]
    result1 = check_drug_compatibility(drugs1)
    print(f"安全性: {result1.level.value}")
    print(f"是否安全: {'是' if result1.is_safe else '否'}")
    if result1.conflicts:
        for conflict in result1.conflicts:
            print(f"\n[!] 配伍问题: {conflict['drug_a']} + {conflict['drug_b']}")
            print(f"原因: {conflict['reason']}")
            print(f"建议: {conflict['suggestion']}")
    
    # 测试案例2：多西环素 + 含钙药物（禁忌）
    print("\n" + "=" * 60)
    print("【测试案例2】多西环素 + 含钙药物")
    drugs2 = [
        {'name': '盐酸多西环素可溶性粉', 'component': '盐酸多西环素'},
        {'name': '葡萄糖酸钙', 'component': '葡萄糖酸钙'}
    ]
    result2 = check_drug_compatibility(drugs2)
    print(f"安全性: {result2.level.value}")
    if result2.conflicts:
        for conflict in result2.conflicts:
            print(f"\n[!] 配伍问题: {conflict['drug_a']} + {conflict['drug_b']}")
            print(f"原因: {conflict['reason']}")
            print(f"建议: {conflict['suggestion']}")
    
    # 测试案例3：安全组合
    print("\n" + "=" * 60)
    print("【测试案例3】替米考星 + 多西环素（慎用）")
    drugs3 = [
        {'name': '替米考星溶液', 'component': '替米考星'},
        {'name': '盐酸多西环素可溶性粉', 'component': '盐酸多西环素'}
    ]
    result3 = check_drug_compatibility(drugs3)
    print(f"安全性: {result3.level.value}")
    if result3.conflicts:
        for conflict in result3.conflicts:
            print(f"\n[!] 配伍问题: {conflict['drug_a']} + {conflict['drug_b']}")
            print(f"原因: {conflict['reason']}")
            print(f"建议: {conflict['suggestion']}")
    else:
        print("[OK] 未发现配伍禁忌")
    
    print("\n" + "=" * 60)
    print("测试完成！")
