# -*- coding: utf-8 -*-
"""
兽药智能推荐系统 - 完整版
整合所有产品数据：
- 底价目录：22个产品
- 明星产品：23个产品
- 产品信息_华英：66个产品
总计：111个产品

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


@dataclass
class DrugRecommendation:
    """药物推荐结果"""
    drug: DrugInfo
    match_score: float
    reason: str
    dosage_recommendation: str
    
    def to_dict(self):
        return {
            'drug': self.drug.to_dict(),
            'match_score': self.match_score,
            'reason': self.reason,
            'dosage_recommendation': self.dosage_recommendation
        }


class DrugDatabase:
    """药物数据库 - 包含所有111个产品"""
    
    def __init__(self, excel_path: str):
        self.drugs: List[DrugInfo] = []
        self.load_all_products(excel_path)
    
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
        """加载所有产品数据"""
        excel_file = pd.ExcelFile(excel_path)
        
        # 1. 加载底价目录产品
        self._load_base_products(excel_file)
        
        # 2. 加载明星产品
        self._load_star_products(excel_file)
        
        # 3. 加载产品信息_华英
        self._load_info_products(excel_file)
        
        print(f"[数据库] 共加载 {len(self.drugs)} 个产品")
    
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
    
    def _load_star_products(self, excel_file):
        """加载明星产品（23个）"""
        df = pd.read_excel(excel_file, sheet_name='明星产品_20260512')
        
        # 加载"产品信息_华英" sheet 用于匹配详细信息
        info_df = pd.read_excel(excel_file, sheet_name='产品信息_华英')
        
        # 创建列名映射函数（处理特殊字符如不间断空格）
        def get_column_value(row, target_name, default=None):
            """根据目标列名模糊匹配获取值"""
            for col in row.index:
                if target_name in str(col):
                    val = row[col]
                    if pd.notna(val):
                        return val
            return default
        
        info_products = {}
        for _, info_row in info_df.iterrows():
            # 通过商品名匹配
            brand = get_column_value(info_row, '商品名')
            if brand and str(brand) != '/':
                info_products[str(brand)] = info_row
            # 通过产品名称匹配
            product = get_column_value(info_row, '产品名称')
            if product and str(product) != '/':
                info_products[str(product)] = info_row
        
        # 明星产品知识库
        star_knowledge = {
            "浆小白(水禽)": {"component": "中药提取物", "indications": ["水禽浆膜炎", "大肠杆菌病", "沙门氏菌病"], "types": ["BACTERIAL", "RESPIRATORY"], "egg_safe": True, "category": "中药", "timing": "发病期间治疗使用", "usage": "混饮：每袋兑水1000斤，连用3-5日"},
            "控孤": {"component": "混合型饲料添加剂L-抗坏血酸", "indications": ["弧菌感染", "肠道疾病", "免疫增强"], "types": ["BACTERIAL", "DIGESTIVE"], "egg_safe": True, "category": "饲料添加剂", "timing": "发病期间治疗使用", "usage": "混饮：每袋兑水2000斤，连用3-5日"},
            "抚风": {"component": "混合型饲料添加剂牛磺酸", "indications": ["抗应激", "保肝护肾", "提高免疫力"], "types": ["MIXED"], "egg_safe": True, "category": "饲料添加剂", "timing": "日常保健使用", "usage": "混饮：每袋兑水2000斤，连用5-7日"},
            "浆小白(清解合剂)": {"component": "中药提取物", "indications": ["清热解毒", "病毒感染", "免疫增强"], "types": ["VIRAL", "MIXED"], "egg_safe": True, "category": "中药", "timing": "发病期间治疗使用", "usage": "混饮：每袋兑水1000斤，连用3-5日"},
            "海健素": {"component": "黄芪多糖口服液(β防御素、干扰素β、γ）", "indications": ["维生素缺乏", "营养补充", "抗应激"], "types": ["NUTRITIONAL"], "egg_safe": True, "category": "维生素", "timing": "日常保健使用", "usage": "混饮：每袋兑水2000斤，连用5-7日"},
            "（中药）金舒利（小柴胡）500g": {"component": "混合型饲料添加剂 牛磺酸", "indications": ["退烧", "抗炎", "增料", "抗病毒"], "types": ["NUTRITIONAL", "MIXED"], "egg_safe": True, "category": "饲料添加剂", "timing": "增免抗病毒类产品", "usage": "本品500g/袋兑水6000斤，建议不低于5000斤水使用，全天量集中饮用7-8小时，连用3-5天"},
            "（中药）金舒利（小柴胡）100g": {"component": "混合型饲料添加剂 牛磺酸", "indications": ["退烧", "抗炎", "增料", "抗病毒"], "types": ["NUTRITIONAL", "MIXED"], "egg_safe": True, "category": "饲料添加剂", "timing": "增免抗病毒类产品", "usage": "本品100g/袋兑水1200斤，建议不低于1000斤水使用，全天量集中饮用7-8小时，连用3-5天"},
            "严立康": {"component": "盐酸大观霉素盐酸林可霉素可溶性粉", "indications": ["肠道菌群失调", "腹泻", "消化不良"], "types": ["DIGESTIVE"], "egg_safe": False, "category": "微生态", "timing": "日常保健使用", "usage": "混饮：每袋兑水2000斤，连用5-7日"},
            "超吉拍档": {"component": "盐酸大观霉素盐酸林可霉素可溶性粉", "indications": ["促进消化", "提高饲料利用率", "肠道健康"], "types": ["NUTRITIONAL", "DIGESTIVE"], "egg_safe": False, "category": "酶制剂", "timing": "日常保健使用", "usage": "混饲：每袋拌料1000斤，连用5-7日"},
            "新达罗": {"component": "硫酸庆大霉素可溶性粉", "indications": ["细菌感染", "呼吸道感染", "肠道感染"], "types": ["BACTERIAL", "RESPIRATORY", "DIGESTIVE"], "egg_safe": False, "category": "抗生素", "timing": "发病期间治疗使用", "usage": "混饮：每袋兑水1000斤，连用3-5日"},
            "菲清": {"component": "液态甘草鱼腥草粗提物(复配型)", "indications": ["清肺止咳", "呼吸道感染", "痰多"], "types": ["RESPIRATORY"], "egg_safe": True, "category": "中药", "timing": "发病期间治疗使用", "usage": "混饮：每瓶兑水2000斤，连用3-5日"},
            "热感清100ml": {"component": "鱼腥草提取液", "indications": ["退热", "感冒", "发热"], "types": ["MIXED", "VIRAL"], "egg_safe": True, "category": "中药", "timing": "增免抗病毒类产品", "usage": "本品100ml/瓶饮水400-600斤，全天量集中饮用4-5小时，连用3天"},
            "热感清250ml": {"component": "鱼腥草提取液", "indications": ["退热", "感冒", "发热"], "types": ["MIXED", "VIRAL"], "egg_safe": True, "category": "中药", "timing": "增免抗病毒类产品", "usage": "本品250ml/瓶饮水1000-1500斤，全天量集中饮用4-5小时，连用3天"},
            "肽芪剑（蛋鸡）": {"component": "液态低聚壳聚糖", "indications": ["免疫增强", "抗病毒", "提高产蛋率"], "types": ["VIRAL", "MIXED"], "egg_safe": True, "category": "免疫增强剂", "timing": "日常保健使用", "usage": "混饮：每袋兑水2000斤，连用5-7日"},
            "卡迪欧100ml": {"component": "鸡传染性法氏囊病精制蛋黄抗体", "indications": ["退热", "止痛", "消炎"], "types": ["MIXED"], "egg_safe": True, "category": "解热镇痛", "timing": "发热时使用", "usage": "混饮：每瓶兑水1000斤，连用3日"},
            "卡迪欧250ml": {"component": "鸡传染性法氏囊病精制蛋黄抗体", "indications": ["退热", "止痛", "消炎"], "types": ["MIXED"], "egg_safe": True, "category": "解热镇痛", "timing": "发热时使用", "usage": "混饮：每瓶兑水2000斤，连用3日"},
            "甘舒乐": {"component": "甘露寡糖", "indications": ["保肝护肾", "解毒", "抗应激"], "types": ["NUTRITIONAL", "MIXED"], "egg_safe": True, "category": "中药", "timing": "日常保健使用", "usage": "混饮：每袋兑水2000斤，连用5-7日"},
            "（中药）温炎消": {"component": "混合型饲料添加剂液态牛磺酸", "indications": ["消炎", "肠道疾病", "腹泻"], "types": ["DIGESTIVE", "BACTERIAL"], "egg_safe": True, "category": "中药", "timing": "发病期间治疗使用", "usage": "混饮：每袋兑水1000斤，连用3-5日"},
            "（中药）双胃康": {"component": "液态苍术木香粗提物(复配型)", "indications": ["腺胃炎", "肌胃炎", "消化不良"], "types": ["DIGESTIVE"], "egg_safe": True, "category": "中药", "timing": "发病期间治疗使用", "usage": "混饮：每袋兑水1000斤，连用3-5日"},
            "（中药）羡康100g": {"component": "天然植物饲料原料、干姜粗提物", "indications": ["腺胃炎", "肌胃炎", "采食量低", "鸡大小不均"], "types": ["DIGESTIVE"], "egg_safe": True, "category": "腺胃炎产品", "timing": "发病期间治疗使用", "usage": "混饮：每袋兑水1000斤，连用3-5日"},
            "（中药）羡康500g": {"component": "天然植物饲料原料、干姜粗提物", "indications": ["腺胃炎", "肌胃炎", "采食量低", "鸡大小不均"], "types": ["DIGESTIVE"], "egg_safe": True, "category": "腺胃炎产品", "timing": "发病期间治疗使用", "usage": "混饮：每袋兑水5000斤，连用3-5日"},
            "（中药）畅健": {"component": "混合型饲料添加剂液态甘露寡糖", "indications": ["肠道健康", "腹泻", "消化不良"], "types": ["DIGESTIVE"], "egg_safe": True, "category": "中药", "timing": "发病期间治疗使用", "usage": "混饮：每袋兑水1000斤，连用3-5日"},
        }
        
        for idx, row in df.iterrows():
            if pd.notna(row['商品名']) and row['商品名'] != '/':
                name = str(row['商品名'])  # 商品名（显示用）
                knowledge = star_knowledge.get(name, {})
                
                # 获取产品名称（原来的通用名称），如果为 "/" 则使用商品名
                generic_name = str(row['产品名称']) if pd.notna(row['产品名称']) else ""
                if generic_name == "/" or not generic_name:
                    generic_name = name
                
                # 从"产品信息_华英" sheet 获取更完整的信息
                # 尝试多种匹配方式：1. 商品名 2. 产品名称
                info_product = None
                
                # 方式1：通过商品名匹配
                if name in info_products:
                    info_product = info_products[name]
                
                # 方式2：通过产品名称匹配
                if info_product is None and generic_name in info_products:
                    info_product = info_products[generic_name]
                
                # 方式3：通过规格+商品名联合匹配
                if info_product is None:
                    spec = str(row['规格型号']) if pd.notna(row['规格型号']) else ""
                    if spec:
                        for key, product in info_products.items():
                            if pd.notna(product['包装规格']) and str(product['包装规格']) == spec:
                                info_product = product
                                break
                
                # 方式4：通过知识库中的 component 匹配
                if info_product is None:
                    component = knowledge.get("component", "")
                    if component:
                        for key, product in info_products.items():
                            if pd.notna(product['产品名称']) and component in str(product['产品名称']):
                                info_product = product
                                break
                
                # 获取时机（只从 Excel 获取，找不到保持空缺）
                timing = ""
                if info_product is not None:
                    val = get_column_value(info_product, '时机')
                    if val and str(val) != '/':
                        timing = str(val)
                
                # 获取商品名（优先从 Excel 获取）
                if info_product is not None:
                    brand_val = get_column_value(info_product, '商品名')
                    if brand_val and str(brand_val) != '/':
                        brand_name = str(brand_val)
                    else:
                        brand_name = name
                else:
                    brand_name = name
                
                # 获取用法用量（只从 Excel 获取，找不到保持空缺）
                usage_info = ""
                if info_product is not None:
                    val = get_column_value(info_product, '用法用量')
                    if val and str(val) != '/':
                        usage_info = str(val)
                
                # 获取兑水量（只从 Excel 获取，找不到保持空缺）
                water = ""
                if info_product is not None:
                    val = get_column_value(info_product, '兑水量')
                    if val and str(val) != '/':
                        water = str(val)
                
                # 获取适应症状（只从 Excel 获取，找不到保持空缺）
                indications = []
                if info_product is not None:
                    val = get_column_value(info_product, '适应症状或产品功效')
                    if val and str(val) != '/':
                        indications_str = str(val)
                        indications = [i.strip() for i in indications_str.split('、')] if '、' in indications_str else [indications_str]
                
                drug = DrugInfo(
                    id=f"S{idx+1}",
                    name=name,
                    content=generic_name,
                    spec=str(row['规格型号']) if pd.notna(row['规格型号']) else "",
                    water=water,
                    price=self._parse_price(row['经销商单价']),
                    indications=indications,
                    main_component=knowledge.get("component", name),
                    category=knowledge.get("category", "其他"),
                    egg_period_safe=knowledge.get("egg_safe", True),
                    disease_types=knowledge.get("types", ["MIXED"]),
                    usage_info=usage_info,
                    source="明星产品",
                    timing=timing,
                    brand_name=brand_name,
                    product_name=name
                )
                self.drugs.append(drug)
    
    def _load_info_products(self, excel_file):
        """加载产品信息_华英（66个）"""
        df = pd.read_excel(excel_file, sheet_name='产品信息_华英')
        
        # 产蛋期禁用药物清单（根据GB 31650-2019和兽药质量标准）
        # 包含所有变体名称和商品名
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
        
        for idx, row in df.iterrows():
            if pd.notna(row['产品名称']) and row['产品名称'] != '/':
                name = str(row['产品名称'])
                category = str(row['类别']) if pd.notna(row['类别']) else "其他"
                
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
                
                # 根据类别判断疾病类型
                if category == '抗生素':
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
                
                indications_str = str(row['适应症状或产品功效']) if pd.notna(row['适应症状或产品功效']) else ""
                indications = [i.strip() for i in indications_str.split('、')] if indications_str else ["详见产品说明"]
                
                # 获取商品名，如果为空则使用产品名称
                brand_name = str(row['商品名']) if pd.notna(row['商品名']) else ""
                if not brand_name or brand_name == "/":
                    brand_name = name
                
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
                
                # 获取价格（产品信息_华英的价格更准确，处理列名中的不间断空格）
                price = 0
                for col in df.columns:
                    if '价' in str(col) or '价格' in str(col):
                        price = self._parse_price(row[col])
                        break
                
                # 检查产品是否已存在（从明星产品加载的）
                # 注意：为了保持三个类别的独立性，不更新已存在的产品
                # 而是跳过重复项，保持原有分类
                existing_drug = None
                for drug in self.drugs:
                    if drug.name == name:
                        existing_drug = drug
                        break
                
                if existing_drug:
                    # 产品已存在，跳过以保持分类独立性
                    # 不更新 source 字段，保持原有分类（底价目录/明星产品）
                    continue
                else:
                    # 添加新产品（仅产品信息_华英独有的产品）
                    drug = DrugInfo(
                        id=f"H{idx+1}",
                        name=name,
                        content=brand_name,
                        spec=str(row['包装规格']) if pd.notna(row['包装规格']) else "",
                        water=water_amount,
                        price=price,
                        indications=indications,
                        main_component=name,
                        category=category,
                        egg_period_safe=egg_safe,
                        disease_types=disease_types,
                        usage_info=str(row['用法用量']) if pd.notna(row['用法用量']) else "",
                        source="产品信息_华英",
                        timing=timing,
                        brand_name=brand_name,
                        product_name=name
                    )
                    self.drugs.append(drug)
    
    def get_drug_by_name(self, name: str) -> Optional[DrugInfo]:
        """根据名称获取药物"""
        for drug in self.drugs:
            if drug.name == name:
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
        }
    
    def get_diseases_by_symptom(self, symptom: str) -> Dict:
        """根据症状获取可能的疾病"""
        symptom_lower = symptom.lower()
        for key, value in self.symptom_disease_map.items():
            if key in symptom_lower or symptom_lower in key:
                return value
        return {"diseases": [symptom], "type": "MIXED"}


class DrugRecommender:
    """药物推荐引擎 - 完整版"""
    
    def __init__(self, database: DrugDatabase):
        self.db = database
        self.symptom_mapper = SymptomDiseaseMapper()
        self.compatibility_checker = DrugCompatibilityChecker()
        
        self.disease_type_mapping = {
            "寄生虫病": "PARASITIC",
            "呼吸道疾病": "RESPIRATORY",
            "消化道疾病": "DIGESTIVE",
            "细菌性疾病": "BACTERIAL",
            "病毒性疾病": "VIRAL",
            "营养代谢病": "NUTRITIONAL",
            "混合感染": "MIXED"
        }
    
    def recommend(self, request: RecommendationRequest) -> Dict:
        """主推荐函数"""
        # 解析症状获取疾病类型
        disease_info = self.symptom_mapper.get_diseases_by_symptom(request.symptom)
        diseases = disease_info["diseases"]
        disease_type = disease_info["type"]
        
        # 如果用户选择了发病类型，优先使用
        if request.disease_type in self.disease_type_mapping:
            disease_type = self.disease_type_mapping[request.disease_type]
        
        # 获取候选药物
        candidate_drugs = self._get_candidate_drugs(request, diseases, disease_type)
        
        # 确保至少有3个候选药物
        if len(candidate_drugs) < 3:
            candidate_drugs = self._supplement_drugs(candidate_drugs, request, disease_type)
        
        # 计算单药推荐
        single_recommendations = self._calculate_single_recommendations(
            candidate_drugs, request, diseases
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
            "compatibility_warnings": compatibility_warnings
        }
    
    def _get_candidate_drugs(self, request: RecommendationRequest, 
                             diseases: List[str], disease_type: str) -> List[DrugInfo]:
        """获取候选药物列表"""
        candidates = []
        
        for drug in self.db.get_all_drugs():
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
                          disease_type: str) -> List[DrugInfo]:
        """补充候选药物"""
        existing_names = {d.name for d in candidates}
        
        type_priority = {
            "PARASITIC": ["BACTERIAL", "DIGESTIVE"],
            "RESPIRATORY": ["BACTERIAL", "MIXED"],
            "DIGESTIVE": ["BACTERIAL", "PARASITIC"],
            "BACTERIAL": ["MIXED", "DIGESTIVE", "RESPIRATORY"],
            "VIRAL": ["MIXED", "BACTERIAL"],
            "MIXED": ["BACTERIAL", "RESPIRATORY", "DIGESTIVE"],
            "NUTRITIONAL": ["MIXED", "BACTERIAL"]
        }
        
        # 先补充同类型药物
        for drug in self.db.get_all_drugs():
            if len(candidates) >= 5:
                break
            if drug.name in existing_names:
                continue
            if request.egg_period_safe and not drug.egg_period_safe:
                continue
            if disease_type in drug.disease_types:
                candidates.append(drug)
                existing_names.add(drug.name)
        
        # 补充相关类型药物
        for related_type in type_priority.get(disease_type, ["BACTERIAL"]):
            for drug in self.db.get_all_drugs():
                if len(candidates) >= 5:
                    break
                if drug.name in existing_names:
                    continue
                if request.egg_period_safe and not drug.egg_period_safe:
                    continue
                if related_type in drug.disease_types:
                    candidates.append(drug)
                    existing_names.add(drug.name)
        
        return candidates
    
    def _calculate_single_recommendations(self, drugs: List[DrugInfo], 
                                          request: RecommendationRequest,
                                          diseases: List[str]) -> List[DrugRecommendation]:
        """计算单药推荐，确保包含明星产品和华英产品"""
        recommendations = []
        
        for drug in drugs:
            match_score = self._calculate_match_score(drug, diseases, request)
            reason = self._generate_reason(drug, diseases, match_score)
            dosage = self._generate_dosage(drug, request)
            
            rec = DrugRecommendation(
                drug=drug,
                match_score=match_score,
                reason=reason,
                dosage_recommendation=dosage
            )
            recommendations.append(rec)
        
        # 按匹配分数排序
        recommendations.sort(key=lambda x: x.match_score, reverse=True)
        
        # 确保至少有1个推荐
        if len(recommendations) < 1:
            for drug in self.db.get_all_drugs():
                if request.egg_period_safe and not drug.egg_period_safe:
                    continue
                
                rec = DrugRecommendation(
                    drug=drug,
                    match_score=0.1,
                    reason=f"主要成分为{drug.main_component}；{'产蛋期可用' if drug.egg_period_safe else '注意：产蛋期禁用'}",
                    dosage_recommendation=self._generate_dosage(drug, request)
                )
                recommendations.append(rec)
                break
        
        # 确保推荐结果包含明星产品和华英产品（非底价目录产品）
        final_recommendations = []
        base_recommendations = []  # 底价目录产品
        star_huaying_recommendations = []  # 明星产品和华英产品
        
        for rec in recommendations:
            if rec.drug.source == "底价目录":
                base_recommendations.append(rec)
            else:
                star_huaying_recommendations.append(rec)
        
        # 优先添加明星产品和华英产品，确保至少包含2个
        final_recommendations.extend(star_huaying_recommendations[:2])
        
        # 如果明星/华英产品不足2个，从底价目录补充
        if len(final_recommendations) < 2:
            needed = 2 - len(final_recommendations)
            final_recommendations.extend(base_recommendations[:needed])
        
        # 如果还有空间，再添加1个（优先明星/华英产品）
        existing_ids = {r.drug.id for r in final_recommendations}
        for rec in star_huaying_recommendations[2:]:
            if len(final_recommendations) >= 3:
                break
            if rec.drug.id not in existing_ids:
                final_recommendations.append(rec)
                existing_ids.add(rec.drug.id)
        
        # 如果仍然不足3个，从底价目录补充
        for rec in base_recommendations:
            if len(final_recommendations) >= 3:
                break
            if rec.drug.id not in existing_ids:
                final_recommendations.append(rec)
                existing_ids.add(rec.drug.id)
        
        return final_recommendations[:3]
    
    def _calculate_match_score(self, drug: DrugInfo, diseases: List[str], 
                               request: RecommendationRequest) -> float:
        """计算药物与疾病的匹配分数"""
        score = 1.0
        
        # 适应症匹配
        for indication in drug.indications:
            for disease in diseases:
                if disease in indication or indication in disease:
                    score += 3.0
        
        # 用途匹配
        if request.usage == "预防":
            if drug.category in ['中药', '免疫增强剂', '维生素']:
                score += 0.5
        else:  # 治疗
            if drug.category in ['抗生素', '化药']:
                score += 0.5
        
        # 产品来源优先级加成：明星产品和华英产品获得额外分数
        if drug.source == "明星产品":
            score += 2.0  # 明星产品加2分
        elif drug.source == "产品信息_华英":
            score += 1.5  # 华英产品加1.5分
        # 底价目录产品不加分
        
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
        
        # 定义组合方案库
        combination_schemes = {
            "PARASITIC": [
                {"name": "经典抗球虫方案", "drugs": ["磺胺喹噁啉钠可溶性粉（去球虫）", "地美硝唑预混剂"], "description": "磺胺类联合抗原虫药，对各类球虫效果显著", "priority": 1, "egg_safe": False},
                {"name": "强化止血方案", "drugs": ["磺胺氯吡嗪钠可溶性粉（去球虫）", "地美硝唑预混剂"], "description": "针对盲肠球虫特效，快速止血止痢", "priority": 2, "egg_safe": False},
                {"name": "全面抗虫方案", "drugs": ["磺胺喹噁啉钠可溶性粉（去球虫）", "硫酸新霉素可溶性粉"], "description": "抗球虫同时预防继发细菌感染", "priority": 3, "egg_safe": False},
                {"name": "产蛋期安全抗球方案", "drugs": ["（中药）畅健", "海健素"], "description": "中药调理肠道，增强免疫力，产蛋期安全", "priority": 4, "egg_safe": True}
            ],
            "RESPIRATORY": [
                {"name": "经典呼吸道方案", "drugs": ["替米考星溶液", "盐酸多西环素可溶性粉"], "description": "大环内酯类联合四环素类，对支原体和细菌双重作用", "priority": 1, "egg_safe": False},
                {"name": "强化呼吸道方案", "drugs": ["80%延胡索酸泰妙菌素（呼吸道）", "盐酸多西环素可溶性粉"], "description": "高含量泰妙菌素，针对顽固性呼吸道病", "priority": 2, "egg_safe": False},
                {"name": "中西结合方案", "drugs": ["盐酸多西环素可溶性粉", "桑仁清肺口服液"], "description": "抗生素联合中药口服液，标本兼治", "priority": 3, "egg_safe": False},
                {"name": "产蛋期安全方案1", "drugs": ["桑仁清肺口服液", "麻杏石甘口服液"], "description": "纯中药组合，产蛋期安全，针对呼吸道症状", "priority": 4, "egg_safe": True},
                {"name": "产蛋期安全方案2", "drugs": ["双黄连口服液250ml", "银黄口服液"], "description": "中药抗病毒组合，产蛋期可用", "priority": 5, "egg_safe": True},
                {"name": "产蛋期安全方案3", "drugs": ["清解合剂", "双黄连口服液250ml"], "description": "清热解毒组合，全面覆盖呼吸道病原", "priority": 6, "egg_safe": True}
            ],
            "DIGESTIVE": [
                {"name": "经典肠道方案", "drugs": ["硫酸黏菌素预混剂1000g", "阿莫西林可溶性粉"], "description": "黏菌素针对革兰氏阴性菌，阿莫西林广谱抗菌", "priority": 1, "egg_safe": False},
                {"name": "强化杀菌方案", "drugs": ["硫酸新霉素可溶性粉", "地美硝唑预混剂"], "description": "新霉素肠道浓度高，配合抗原虫药", "priority": 2, "egg_safe": False},
                {"name": "微生态调理方案", "drugs": ["严立康", "（中药）畅健"], "description": "益生菌调理肠道，中药辅助治疗", "priority": 3, "egg_safe": False},
                {"name": "全面肠道方案", "drugs": ["硫酸黏菌素预混剂1000g", "硫酸新霉素可溶性粉", "地美硝唑预混剂"], "description": "三重杀菌，针对顽固性肠道感染", "priority": 4, "egg_safe": False},
                {"name": "产蛋期安全肠道方案", "drugs": ["（中药）双胃康", "（中药）羡康100g"], "description": "纯中药调理肠胃，产蛋期安全", "priority": 5, "egg_safe": True}
            ],
            "BACTERIAL": [
                {"name": "广谱杀菌方案", "drugs": ["氟苯尼考粉", "盐酸多西环素可溶性粉"], "description": "广谱抗菌，对大多数细菌性疾病有效", "priority": 1, "egg_safe": False},
                {"name": "肠道细菌方案", "drugs": ["硫酸黏菌素预混剂1000g", "阿莫西林可溶性粉"], "description": "针对肠道细菌感染", "priority": 2, "egg_safe": False},
                {"name": "强化抗菌方案", "drugs": ["盐酸恩诺沙星可溶性粉", "硫酸黏菌素预混剂1000g"], "description": "氟喹诺酮类联合多肽类，杀菌效果强", "priority": 3, "egg_safe": False},
                {"name": "全面抗菌方案", "drugs": ["氟苯尼考粉", "盐酸多西环素可溶性粉", "硫酸黏菌素预混剂1000g"], "description": "三重广谱抗菌，覆盖各类细菌", "priority": 4, "egg_safe": False},
                {"name": "产蛋期安全抗菌方案", "drugs": ["（中药）金舒利（小柴胡）100g", "肽芪剑（蛋鸡）"], "description": "中药抗菌增强免疫，产蛋期安全", "priority": 5, "egg_safe": True}
            ],
            "VIRAL": [
                {"name": "抗病毒中药方案", "drugs": ["（中药）金舒利（小柴胡）100g", "肽芪剑（蛋鸡）"], "description": "中药清热解毒，增强免疫力", "priority": 1, "egg_safe": True},
                {"name": "防继发感染方案", "drugs": ["阿莫西林可溶性粉", "卡巴匹林钙粉"], "description": "预防细菌继发感染，缓解症状", "priority": 2, "egg_safe": False},
                {"name": "综合抗病毒方案", "drugs": ["（中药）金舒利（小柴胡）100g", "肽芪剑（蛋鸡）", "阿莫西林可溶性粉"], "description": "中药+抗生素，抗病毒防继发", "priority": 3, "egg_safe": False},
                {"name": "产蛋期安全抗病毒方案", "drugs": ["（中药）金舒利（小柴胡）100g", "双黄连口服液250ml"], "description": "纯中药抗病毒，产蛋期安全", "priority": 4, "egg_safe": True}
            ],
            "MIXED": [
                {"name": "全面覆盖方案", "drugs": ["氟苯尼考粉", "盐酸多西环素可溶性粉", "卡巴匹林钙粉"], "description": "广谱抗菌+解热镇痛，应对复杂病情", "priority": 1, "egg_safe": False},
                {"name": "肠道呼吸道混合", "drugs": ["替米考星溶液", "硫酸黏菌素预混剂1000g"], "description": "同时覆盖呼吸道和肠道病原", "priority": 2, "egg_safe": False},
                {"name": "抗菌消炎方案", "drugs": ["阿莫西林可溶性粉", "卡巴匹林钙粉"], "description": "抗菌+消炎，适合混合感染", "priority": 3, "egg_safe": False},
                {"name": "产蛋期安全混合方案", "drugs": ["（中药）金舒利（小柴胡）100g", "甘舒乐", "海健素"], "description": "中药+营养支持，产蛋期安全", "priority": 4, "egg_safe": True}
            ],
            "NUTRITIONAL": [
                {"name": "营养支持方案", "drugs": ["海健素", "甘舒乐"], "description": "补充营养，保肝护肾", "priority": 1, "egg_safe": True},
                {"name": "全面营养方案", "drugs": ["海健素", "甘舒乐", "肽芪剑（蛋鸡）"], "description": "营养+免疫，全面调理", "priority": 2, "egg_safe": True}
            ]
        }
        
        schemes = combination_schemes.get(disease_type, combination_schemes["MIXED"])
        
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
                combinations.append({
                    "scheme_name": scheme["name"],
                    "description": scheme["description"],
                    "drugs": drug_details,
                    "total_price": round(total_price, 1),
                    "priority": scheme["priority"]
                })
        
        # 如果没有找到合适的组合，使用默认组合
        if not combinations:
            combinations = self._get_default_combinations(request, disease_type)
        
        # 按优先级排序，只返回第一个（最优方案）
        combinations.sort(key=lambda x: x["priority"])
        return combinations[:1]
    
    def _get_default_combinations(self, request: RecommendationRequest, disease_type: str = "MIXED") -> List[Dict]:
        """获取默认组合方案"""
        default_combos = []
        
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
                default_combos.append({
                    "scheme_name": combo["name"],
                    "description": combo["description"],
                    "drugs": drug_details,
                    "total_price": round(total_price, 1),
                    "priority": combo["priority"]
                })
        
        return default_combos


# 便捷函数
def create_recommender(excel_path: str) -> DrugRecommender:
    """创建推荐器实例"""
    db = DrugDatabase(excel_path)
    return DrugRecommender(db)


def quick_recommend(recommender: DrugRecommender, 
                   animal_type: str,
                   age_stage: str,
                   symptom: str,
                   disease_type: str,
                   usage: str,
                   egg_period_safe: bool,
                   farm_scale: str) -> Dict:
    """快速推荐函数"""
    request = RecommendationRequest(
        animal_type=animal_type,
        age_stage=age_stage,
        symptom=symptom,
        disease_type=disease_type,
        usage=usage,
        egg_period_safe=egg_period_safe,
        farm_scale=farm_scale
    )
    return recommender.recommend(request)
