# -*- coding: utf-8 -*-
"""
蛋鸡产蛋期禁用药物拦截模块

功能：
1. 提供药物产蛋期禁用状态查询
2. 提供拦截提示功能
3. 可与现有系统集成使用

使用方法：
    from egg_laying_banned_drugs_checker import BannedDrugsChecker
    
    checker = BannedDrugsChecker()
    
    # 检查单个药物
    result = checker.check_drug("恩诺沙星溶液")
    print(result)
    
    # 检查多个药物
    results = checker.check_drugs(["恩诺沙星溶液", "玉屏风口服液"])
    print(results)
    
    # 获取所有禁用药物清单
    banned_list = checker.get_all_banned_drugs()
    print(banned_list)
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class DrugStatus(Enum):
    """药物状态"""
    BANNED = "产蛋期禁用"
    ALLOWED = "产蛋期可用"
    UNKNOWN = "未知"


@dataclass
class DrugCheckResult:
    """药物检查结果"""
    drug_name: str
    status: DrugStatus
    is_banned: bool
    active_ingredient: str
    ban_reason: str
    legal_basis: str
    suggestion: str


class BannedDrugsChecker:
    """蛋鸡产蛋期禁用药物检查器"""
    
    def __init__(self):
        self.banned_drugs_87 = [
            "二硝托胺预混剂", "马杜米星铵预混剂", "磷酸泰乐菌素预混剂",
            "磺胺喹噁啉钠可溶性粉", "磺胺喹噁啉钠溶液", "复方磺胺喹噁啉溶液",
            "复方磺胺喹噁啉钠可溶性粉", "磺胺喹噁啉二甲氧苄啶预混剂",
            "磺胺氯吡嗪钠可溶性粉", "复方磺胺氯吡嗪钠预混剂", "复方磺胺氯哒嗪钠粉",
            "磺胺对甲氧嘧啶二甲氧苄啶预混剂", "复方磺胺二甲嘧啶钠可溶性粉",
            "复方磺胺间甲氧嘧啶可溶性粉", "磺胺间甲氧嘧啶预混剂",
            "复方磺胺间甲氧嘧啶钠可溶性粉", "复方磺胺间甲氧嘧啶预混剂",
            "盐酸氨丙啉磺胺喹噁啉钠可溶性粉", "氯羟吡啶预混剂",
            "硫酸黏菌素可溶性粉", "硫酸黏菌素预混剂",
            "硫酸新霉素可溶性粉", "硫酸新霉素溶液", "硫酸安普霉素可溶性粉",
            "硫氰酸红霉素可溶性粉", "替米考星溶液",
            "酒石酸泰乐菌素可溶性粉", "酒石酸泰乐菌素磺胺二甲嘧啶可溶性粉",
            "酒石酸吉他霉素可溶性粉",
            "恩诺沙星溶液", "恩诺沙星片", "恩诺沙星可溶性粉",
            "盐霉素钠预混剂", "盐酸氯苯胍预混剂",
            "盐酸氨丙啉乙氧酰胺苯甲酯磺胺喹噁啉预混剂",
            "盐酸氨丙啉乙氧酰胺苯甲酯预混剂",
            "盐酸多西环素片", "盐酸多西环素可溶性粉", "盐酸大观霉素可溶性粉",
            "氟苯尼考粉", "氟苯尼考预混剂", "氟苯尼考溶液", "氟苯尼考注射液", "氟苯尼考可溶性粉",
            "阿莫西林可溶性粉", "阿莫西林片", "复方阿莫西林粉",
            "氨苄西林可溶性粉", "氨苄西林钠可溶性粉", "复方氨苄西林粉",
            "杆菌肽锌预混剂",
            "地克珠利预混剂", "地克珠利溶液", "地克珠利颗粒",
            "吉他霉素预混剂", "吉他霉素片",
            "马杜米星铵尼卡巴嗪预混剂", "复方马度米星铵预混剂",
            "三苯氯达唑片", "三苯氯达唑颗粒",
            "甲磺酸达氟沙星粉", "甲磺酸达氟沙星溶液",
            "甲磺酸培氟沙星可溶性粉", "甲磺酸培氟沙星注射液",
            "地美硝唑预混剂", "那西肽预混剂",
            "乳酸环丙沙星可溶性粉", "乳酸诺氟沙星可溶性粉",
            "金霉素预混剂", "盐酸金霉素可溶性粉",
            "洛克沙胂预混剂",
            "盐酸沙拉沙星片", "盐酸沙拉沙星可溶性粉", "盐酸沙拉沙星注射液", "盐酸沙拉沙星溶液",
            "盐酸环丙沙星可溶性粉", "盐酸环丙沙星注射液",
            "氨苯砷酸预混剂",
            "烟酸诺氟沙星可溶性粉", "烟酸诺氟沙星溶液",
            "酒石酸泰万菌素可溶性粉", "酒石酸泰万菌素预混剂",
            "海南霉素钠预混剂", "越霉素A预混剂",
            "硫酸庆大霉素可溶性粉", "甲砜霉素可溶性粉", "氯霉素可溶性粉"
        ]
        
        self.banned_reasons = {
            "恩诺沙星": {
                "reason": "喹诺酮类合成抗菌药，GB 31650-2019规定产蛋期禁用",
                "basis": "GB 31650-2019",
                "suggestion": "产蛋期请使用允许使用的抗菌药物，如泰妙菌素、土霉素等"
            },
            "氟苯尼考": {
                "reason": "酰胺醇类抗菌药，GB 31650-2019规定蛋鸡产蛋期不得使用",
                "basis": "GB 31650-2019",
                "suggestion": "产蛋期请使用允许使用的抗菌药物，或停用该药物后再进入产蛋期"
            },
            "阿莫西林": {
                "reason": "β-内酰胺类抗菌药，GB 31650-2019规定蛋鸡产蛋期不得使用",
                "basis": "GB 31650-2019",
                "suggestion": "产蛋期请使用允许使用的抗菌药物"
            },
            "氨苄西林": {
                "reason": "β-内酰胺类抗菌药，GB 31650-2019规定蛋鸡产蛋期不得使用",
                "basis": "GB 31650-2019",
                "suggestion": "产蛋期请使用允许使用的抗菌药物"
            },
            "多西环素": {
                "reason": "四环素类抗菌药，GB 31650-2019规定产蛋期禁用",
                "basis": "GB 31650-2019",
                "suggestion": "产蛋期请使用允许使用的抗菌药物，如土霉素"
            },
            "金霉素": {
                "reason": "四环素类抗菌药，GB 31650-2019规定产蛋期禁用",
                "basis": "GB 31650-2019",
                "suggestion": "产蛋期请使用允许使用的抗菌药物，如土霉素"
            },
            "沙拉沙星": {
                "reason": "氟喹诺酮类抗菌药，GB 31650-2019规定产蛋期禁用",
                "basis": "GB 31650-2019",
                "suggestion": "产蛋期请使用允许使用的抗菌药物"
            },
            "替米考星": {
                "reason": "大环内酯类抗菌药，GB 31650-2019规定产蛋期禁用",
                "basis": "GB 31650-2019",
                "suggestion": "产蛋期请使用允许使用的抗菌药物"
            },
            "庆大霉素": {
                "reason": "氨基糖苷类抗菌药，兽药质量标准规定产蛋期禁用",
                "basis": "兽药质量标准",
                "suggestion": "产蛋期请使用允许使用的抗菌药物"
            },
            "地美硝唑": {
                "reason": "硝基咪唑类，GB 31650-2019规定产蛋期禁用",
                "basis": "GB 31650-2019",
                "suggestion": "产蛋期禁止使用硝基咪唑类药物"
            },
            "达氟沙星": {
                "reason": "氟喹诺酮类抗菌药，GB 31650-2019规定产蛋期禁用",
                "basis": "GB 31650-2019",
                "suggestion": "产蛋期请使用允许使用的抗菌药物"
            },
            "培氟沙星": {
                "reason": "氟喹诺酮类，农业农村部公告第2292号停用药物",
                "basis": "农业农村部公告第2292号",
                "suggestion": "该药物已停用，所有食品动物不得使用"
            },
            "环丙沙星": {
                "reason": "氟喹诺酮类抗菌药，GB 31650-2019规定产蛋期禁用",
                "basis": "GB 31650-2019",
                "suggestion": "产蛋期请使用允许使用的抗菌药物"
            },
            "诺氟沙星": {
                "reason": "氟喹诺酮类，农业农村部公告第2292号停用药物",
                "basis": "农业农村部公告第2292号",
                "suggestion": "该药物已停用，所有食品动物不得使用"
            },
            "泰乐菌素": {
                "reason": "大环内酯类抗菌药，兽药质量标准规定产蛋期禁用",
                "basis": "兽药质量标准",
                "suggestion": "产蛋期请使用允许使用的抗菌药物"
            },
            "泰万菌素": {
                "reason": "大环内酯类抗菌药，兽药质量标准规定产蛋期禁用",
                "basis": "兽药质量标准",
                "suggestion": "产蛋期请使用允许使用的抗菌药物"
            },
            "磺胺": {
                "reason": "磺胺类抗菌药，GB 31650-2019规定产蛋期禁用",
                "basis": "GB 31650-2019",
                "suggestion": "产蛋期禁止使用磺胺类药物"
            },
            "地克珠利": {
                "reason": "抗球虫药，GB 31650-2019规定产蛋期禁用",
                "basis": "GB 31650-2019",
                "suggestion": "产蛋期请使用允许使用的抗球虫药物"
            },
            "二硝托胺": {
                "reason": "抗球虫药，兽药典2000版规定产蛋期禁用",
                "basis": "兽药典2000版",
                "suggestion": "产蛋期请使用允许使用的抗球虫药物"
            },
            "马杜米星": {
                "reason": "聚醚类抗球虫药，部颁标准规定产蛋期禁用",
                "basis": "部颁标准",
                "suggestion": "产蛋期请使用允许使用的抗球虫药物"
            },
            "氯羟吡啶": {
                "reason": "抗球虫药，兽药质量标准规定产蛋期禁用",
                "basis": "兽药质量标准",
                "suggestion": "产蛋期请使用允许使用的抗球虫药物"
            },
            "盐酸氯苯胍": {
                "reason": "抗球虫药，兽药质量标准规定产蛋期禁用",
                "basis": "兽药质量标准",
                "suggestion": "产蛋期请使用允许使用的抗球虫药物"
            },
            "盐霉素": {
                "reason": "聚醚类抗球虫药，兽药质量标准规定产蛋期禁用",
                "basis": "兽药质量标准",
                "suggestion": "产蛋期请使用允许使用的抗球虫药物"
            },
            "黏菌素": {
                "reason": "多肽类抗菌药，兽药质量标准规定产蛋期禁用",
                "basis": "兽药质量标准",
                "suggestion": "产蛋期请使用允许使用的抗菌药物"
            },
            "新霉素": {
                "reason": "氨基糖苷类抗菌药，兽药质量标准规定产蛋期禁用",
                "basis": "兽药质量标准",
                "suggestion": "产蛋期请使用允许使用的抗菌药物"
            },
            "安普霉素": {
                "reason": "氨基糖苷类抗菌药，兽药质量标准规定产蛋期禁用",
                "basis": "兽药质量标准",
                "suggestion": "产蛋期请使用允许使用的抗菌药物"
            },
            "红霉素": {
                "reason": "大环内酯类抗菌药，兽药质量标准规定产蛋期禁用",
                "basis": "兽药质量标准",
                "suggestion": "产蛋期请使用允许使用的抗菌药物"
            },
            "吉他霉素": {
                "reason": "大环内酯类抗菌药，兽药质量标准规定产蛋期禁用",
                "basis": "兽药质量标准",
                "suggestion": "产蛋期请使用允许使用的抗菌药物"
            },
            "大观霉素": {
                "reason": "氨基糖苷类抗菌药，兽药质量标准规定产蛋期禁用",
                "basis": "兽药质量标准",
                "suggestion": "产蛋期请使用允许使用的抗菌药物"
            },
            "杆菌肽": {
                "reason": "多肽类抗菌药，兽药质量标准规定产蛋期禁用",
                "basis": "兽药质量标准",
                "suggestion": "产蛋期请使用允许使用的抗菌药物"
            },
            "那西肽": {
                "reason": "大环内酯类抗菌药，已禁止作为饲料添加剂使用",
                "basis": "农业农村部公告",
                "suggestion": "该药物已禁止作为饲料添加剂使用"
            },
            "甲砜霉素": {
                "reason": "酰胺醇类抗菌药，GB 31650-2019规定产蛋期禁用",
                "basis": "GB 31650-2019",
                "suggestion": "产蛋期请使用允许使用的抗菌药物"
            },
            "氯霉素": {
                "reason": "酰胺醇类，农业农村部公告第250号禁止使用药品",
                "basis": "农业农村部公告第250号",
                "suggestion": "该药物为食品动物禁用药品，严禁使用"
            },
            "氨苯砷酸": {
                "reason": "砷制剂，已停止使用",
                "basis": "农业农村部公告",
                "suggestion": "该药物已停止使用"
            },
            "洛克沙胂": {
                "reason": "砷制剂，已停止使用",
                "basis": "农业农村部公告",
                "suggestion": "该药物已停止使用"
            },
            "三苯氯达唑": {
                "reason": "抗寄生虫药，兽药质量标准规定产蛋期禁用",
                "basis": "兽药质量标准",
                "suggestion": "产蛋期请使用允许使用的抗寄生虫药物"
            },
            "海南霉素": {
                "reason": "聚醚类抗球虫药，兽药质量标准规定产蛋期禁用",
                "basis": "兽药质量标准",
                "suggestion": "产蛋期请使用允许使用的抗球虫药物"
            },
            "越霉素": {
                "reason": "氨基糖苷类抗球虫药，兽药质量标准规定产蛋期禁用",
                "basis": "兽药质量标准",
                "suggestion": "产蛋期请使用允许使用的抗球虫药物"
            },
            "氨丙啉": {
                "reason": "抗球虫药，兽药质量标准规定产蛋期禁用",
                "basis": "兽药质量标准",
                "suggestion": "产蛋期请使用允许使用的抗球虫药物"
            },
        }
    
    def check_drug(self, drug_name: str) -> DrugCheckResult:
        """
        检查单个药物是否为产蛋期禁用
        
        Args:
            drug_name: 药物名称
            
        Returns:
            DrugCheckResult: 检查结果
        """
        for banned_name in self.banned_drugs_87:
            if banned_name in drug_name or drug_name in banned_name:
                active_ingredient = None
                for ingredient, info in self.banned_reasons.items():
                    if ingredient in drug_name or ingredient in banned_name:
                        active_ingredient = ingredient
                        break
                
                if active_ingredient:
                    reason_info = self.banned_reasons[active_ingredient]
                else:
                    reason_info = {
                        "reason": "列入87种蛋鸡产蛋期禁用兽药清单",
                        "basis": "GB 31650-2019/兽药质量标准",
                        "suggestion": "产蛋期禁止使用该药物"
                    }
                
                return DrugCheckResult(
                    drug_name=drug_name,
                    status=DrugStatus.BANNED,
                    is_banned=True,
                    active_ingredient=active_ingredient or "未知",
                    ban_reason=reason_info["reason"],
                    legal_basis=reason_info["basis"],
                    suggestion=reason_info["suggestion"]
                )
        
        return DrugCheckResult(
            drug_name=drug_name,
            status=DrugStatus.ALLOWED,
            is_banned=False,
            active_ingredient="",
            ban_reason="",
            legal_basis="",
            suggestion="该药物未在产蛋期禁用清单中"
        )
    
    def check_drugs(self, drug_names: List[str]) -> List[DrugCheckResult]:
        """
        检查多个药物是否为产蛋期禁用
        
        Args:
            drug_names: 药物名称列表
            
        Returns:
            List[DrugCheckResult]: 检查结果列表
        """
        return [self.check_drug(name) for name in drug_names]
    
    def get_all_banned_drugs(self) -> List[str]:
        """
        获取所有产蛋期禁用药物清单
        
        Returns:
            List[str]: 禁用药物名称列表
        """
        return self.banned_drugs_87.copy()
    
    def get_banned_drugs_with_reasons(self) -> Dict[str, Dict]:
        """
        获取所有产蛋期禁用药物及其禁用原因
        
        Returns:
            Dict[str, Dict]: 禁用药物名称及其原因字典
        """
        result = {}
        for banned_name in self.banned_drugs_87:
            active_ingredient = None
            for ingredient, info in self.banned_reasons.items():
                if ingredient in banned_name:
                    active_ingredient = ingredient
                    break
            
            if active_ingredient:
                result[banned_name] = self.banned_reasons[active_ingredient]
            else:
                result[banned_name] = {
                    "reason": "列入87种蛋鸡产蛋期禁用兽药清单",
                    "basis": "GB 31650-2019/兽药质量标准",
                    "suggestion": "产蛋期禁止使用该药物"
                }
        return result
    
    def generate_warning_message(self, drug_name: str) -> str:
        """
        生成禁用药物警告消息
        
        Args:
            drug_name: 药物名称
            
        Returns:
            str: 警告消息
        """
        result = self.check_drug(drug_name)
        
        if result.is_banned:
            return f"""警告：该产品为蛋鸡产蛋期禁用药物！

产品名称：{result.drug_name}
有效成分：{result.active_ingredient}
禁用原因：{result.ban_reason}
法规依据：{result.legal_basis}

根据GB 31650-2019及相关法规规定，该产品在蛋鸡产蛋期禁止使用。
违规使用将导致鸡蛋中兽药残留超标，可能面临以下法律后果：
1. 依照《兽药管理条例》第六十二条，处1万元以上5万元以下罚款
2. 给他人造成损失的，依法承担赔偿责任
3. 情节严重的，依据《刑法》第一百四十四条追究刑事责任

建议：{result.suggestion}"""
        else:
            return f"提示：{drug_name} 未在产蛋期禁用清单中。"


def main():
    """测试函数"""
    checker = BannedDrugsChecker()
    
    # 测试已知禁用药物
    test_drugs = [
        "恩诺沙星溶液",
        "10%氟苯尼考溶液",
        "10%阿莫西林可溶性粉",
        "复方阿莫西林粉",
        "5%盐酸沙拉沙星溶液",
        "盐酸多西环素可溶性粉",
        "盐酸金霉素可溶性粉",
        "20%酒石酸泰万菌素预混剂",
        "替米考星溶液",
        "硫酸庆大霉素可溶性粉",
        "玉屏风口服液（蛋鸡可用）",
        "双黄连口服液250ml（蛋鸡可用）"
    ]
    
    print("=" * 60)
    print("蛋鸡产蛋期禁用药物检查测试")
    print("=" * 60)
    
    for drug in test_drugs:
        result = checker.check_drug(drug)
        status = "禁用" if result.is_banned else "可用"
        print(f"\n{drug}: {status}")
        if result.is_banned:
            print(f"  成分: {result.active_ingredient}")
            print(f"  原因: {result.ban_reason}")
            print(f"  依据: {result.legal_basis}")
    
    print("\n" + "=" * 60)
    print(f"总计测试 {len(test_drugs)} 种药物")
    banned_count = sum(1 for d in test_drugs if checker.check_drug(d).is_banned)
    print(f"禁用药物: {banned_count} 种")
    print(f"可用药物: {len(test_drugs) - banned_count} 种")
    print("=" * 60)


if __name__ == "__main__":
    main()
