# -*- coding: utf-8 -*-
"""
环境调整建议模块
根据动物病症、个体档案信息和棚舍环境信息，生成科学、具体且可操作的环境调整建议
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class EnvironmentAdjustment:
    """环境调整建议"""
    category: str
    title: str
    current_value: str
    target_value: str
    adjustment_steps: List[str]
    expected_effect: str
    precautions: List[str]


@dataclass
class AnimalProfile:
    """动物个体档案信息"""
    age_days: int
    breed: str
    health_history: List[str]
    previous_medications: List[str]
    weight: Optional[float] = None
    gender: Optional[str] = None


@dataclass
class ShedEnvironment:
    """棚舍环境信息"""
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    ventilation_status: Optional[str] = None
    stocking_density: Optional[str] = None
    cleanliness_level: Optional[str] = None
    ammonia_level: Optional[str] = None
    lighting_hours: Optional[int] = None


class EnvironmentAdjustmentEngine:
    """环境调整建议引擎"""
    
    def __init__(self):
        self.disease_environment_rules = self._init_disease_environment_rules()
    
    def _init_disease_environment_rules(self) -> Dict:
        return {
            "球虫病": {
                "temperature": {
                    "target_range": "24-28",
                    "adjustment": "保持温暖干燥，避免低温高湿环境",
                    "steps": ["提高舍温1-2℃", "加强保温措施", "避免冷风直吹"],
                    "effect": "降低球虫卵囊活力，减少感染风险",
                    "precautions": ["避免高温闷热", "注意通风降温平衡"]
                },
                "humidity": {
                    "target_range": "50-60",
                    "adjustment": "降低湿度，保持垫料干燥",
                    "steps": ["加强通风排湿", "及时更换潮湿垫料", "使用干燥剂"],
                    "effect": "破坏球虫卵囊生存环境",
                    "precautions": ["避免过度干燥导致呼吸道问题"]
                },
                "cleanliness": {
                    "target_level": "高",
                    "adjustment": "加强清洁消毒",
                    "steps": ["每日清理粪便", "定期带禽消毒", "清理饮水器和料槽"],
                    "effect": "减少环境中卵囊数量",
                    "precautions": ["消毒剂选择对球虫有效的产品"]
                },
                "density": {
                    "target": "降低",
                    "adjustment": "降低饲养密度",
                    "steps": ["分群饲养", "增加活动空间", "避免拥挤"],
                    "effect": "减少接触传播，降低感染压力",
                    "precautions": ["保证每只动物有足够采食空间"]
                }
            },
            "盲肠球虫": {
                "temperature": {
                    "target_range": "25-28",
                    "adjustment": "保持舍温稳定",
                    "steps": ["提高舍温1-2℃", "避免温差过大", "加强保温"],
                    "effect": "减少应激，提高抵抗力",
                    "precautions": ["发病期避免高温"]
                },
                "humidity": {
                    "target_range": "45-55",
                    "adjustment": "严格控制湿度",
                    "steps": ["加强机械通风", "更换潮湿垫料", "防止漏水"],
                    "effect": "抑制卵囊发育",
                    "precautions": ["监测湿度变化"]
                },
                "cleanliness": {
                    "target_level": "极高",
                    "adjustment": "强化消毒",
                    "steps": ["每日多次清理", "使用火焰消毒", "彻底清洁饮水系统"],
                    "effect": "快速降低卵囊污染",
                    "precautions": ["注意消毒频率，避免应激"]
                }
            },
            "小肠球虫": {
                "temperature": {
                    "target_range": "24-27",
                    "adjustment": "保持适宜温度",
                    "steps": ["稳定舍温", "避免骤冷骤热", "保证温度均匀"],
                    "effect": "促进肠道功能恢复",
                    "precautions": ["避免温度过高"]
                },
                "humidity": {
                    "target_range": "50-60",
                    "adjustment": "适度降低湿度",
                    "steps": ["加强通风", "更换垫料", "控制饮水泄漏"],
                    "effect": "减少卵囊繁殖",
                    "precautions": ["维持适宜湿度范围"]
                },
                "cleanliness": {
                    "target_level": "高",
                    "adjustment": "定期清洁",
                    "steps": ["每周深度清洁", "消毒料槽", "清理死角"],
                    "effect": "减少感染源",
                    "precautions": ["清洁后彻底干燥"]
                }
            },
            "慢性呼吸道病": {
                "temperature": {
                    "target_range": "22-26",
                    "adjustment": "保持温度稳定",
                    "steps": ["避免温差超过3℃", "夜间适当加温", "防止冷风"],
                    "effect": "减少呼吸道刺激",
                    "precautions": ["避免高温高湿"]
                },
                "humidity": {
                    "target_range": "55-65",
                    "adjustment": "保持适宜湿度",
                    "steps": ["干燥季节加湿", "潮湿季节通风", "避免极端湿度"],
                    "effect": "保护呼吸道黏膜",
                    "precautions": ["避免湿度过高导致霉菌"]
                },
                "ventilation": {
                    "target_level": "良好",
                    "adjustment": "加强通风管理",
                    "steps": ["定时通风", "降低氨气浓度", "增加空气流动"],
                    "effect": "减少有害气体和粉尘",
                    "precautions": ["避免穿堂风直吹"]
                },
                "ammonia": {
                    "target_level": "<20",
                    "adjustment": "降低氨气浓度",
                    "steps": ["及时清理粪便", "加强通风", "使用垫料添加剂"],
                    "effect": "减轻呼吸道黏膜损伤",
                    "precautions": ["监测氨气浓度"]
                }
            },
            "大肠杆菌病": {
                "temperature": {
                    "target_range": "24-28",
                    "adjustment": "保持温暖环境",
                    "steps": ["提高舍温1-2℃", "避免低温应激", "加强保温"],
                    "effect": "增强抵抗力，减少继发感染",
                    "precautions": ["避免高温"]
                },
                "humidity": {
                    "target_range": "50-60",
                    "adjustment": "控制湿度",
                    "steps": ["加强通风", "保持垫料干燥", "防止饮水溢出"],
                    "effect": "减少细菌滋生",
                    "precautions": ["避免过度干燥"]
                },
                "cleanliness": {
                    "target_level": "高",
                    "adjustment": "强化卫生管理",
                    "steps": ["每日清洁", "定期消毒", "清理料槽和饮水器"],
                    "effect": "减少环境中大肠杆菌数量",
                    "precautions": ["交替使用不同消毒剂"]
                },
                "density": {
                    "target": "降低",
                    "adjustment": "降低饲养密度",
                    "steps": ["分群", "增加空间", "避免过度拥挤"],
                    "effect": "减少接触传播",
                    "precautions": ["保证足够采食饮水位置"]
                }
            },
            "沙门氏菌病": {
                "temperature": {
                    "target_range": "26-30",
                    "adjustment": "保持较高温度",
                    "steps": ["提高舍温2-3℃", "加强保温", "避免低温"],
                    "effect": "减少雏鸡发病，提高抵抗力",
                    "precautions": ["避免高温应激"]
                },
                "cleanliness": {
                    "target_level": "极高",
                    "adjustment": "严格消毒",
                    "steps": ["彻底清洗消毒", "火焰消毒地面", "更换新垫料"],
                    "effect": "杀灭环境中沙门氏菌",
                    "precautions": ["消毒后充分干燥"]
                },
                "ventilation": {
                    "target_level": "良好",
                    "adjustment": "加强通风",
                    "steps": ["定时通风换气", "保持空气新鲜", "降低氨气"],
                    "effect": "减少病原体传播",
                    "precautions": ["避免冷风直吹"]
                }
            },
            "鸡白痢": {
                "temperature": {
                    "target_range": "30-35",
                    "adjustment": "保持育雏温度",
                    "steps": ["提高温度2-3℃", "保证温度均匀", "避免温度波动"],
                    "effect": "减少雏鸡死亡",
                    "precautions": ["注意通风"]
                },
                "humidity": {
                    "target_range": "60-70",
                    "adjustment": "保持较高湿度",
                    "steps": ["加湿", "避免干燥", "保证饮水"],
                    "effect": "保护呼吸道，减少应激",
                    "precautions": ["避免湿度过高"]
                },
                "cleanliness": {
                    "target_level": "极高",
                    "adjustment": "严格卫生",
                    "steps": ["每日清理粪便", "定期消毒", "更换垫料"],
                    "effect": "控制传染源",
                    "precautions": ["注意消毒频率"]
                }
            },
            "禽霍乱": {
                "temperature": {
                    "target_range": "22-26",
                    "adjustment": "保持温度稳定",
                    "steps": ["避免温差过大", "加强保温", "防止冷风"],
                    "effect": "减少应激，提高抵抗力",
                    "precautions": ["避免高温闷热"]
                },
                "humidity": {
                    "target_range": "50-60",
                    "adjustment": "控制湿度",
                    "steps": ["加强通风", "保持干燥", "清理积水"],
                    "effect": "减少细菌繁殖",
                    "precautions": ["避免过度干燥"]
                },
                "cleanliness": {
                    "target_level": "高",
                    "adjustment": "加强消毒",
                    "steps": ["带禽消毒", "器具消毒", "环境消毒"],
                    "effect": "杀灭病原体",
                    "precautions": ["交替使用消毒剂"]
                },
                "density": {
                    "target": "降低",
                    "adjustment": "降低密度",
                    "steps": ["分群隔离", "增加空间", "避免拥挤"],
                    "effect": "减少传播风险",
                    "precautions": ["注意观察病禽"]
                }
            },
            "传染性鼻炎": {
                "temperature": {
                    "target_range": "22-25",
                    "adjustment": "保持适宜温度",
                    "steps": ["稳定温度", "避免骤冷骤热", "保证温度均匀"],
                    "effect": "减少呼吸道应激",
                    "precautions": ["避免高温"]
                },
                "humidity": {
                    "target_range": "55-65",
                    "adjustment": "保持适宜湿度",
                    "steps": ["加湿或通风", "避免极端湿度", "保持垫料干燥"],
                    "effect": "保护鼻腔黏膜",
                    "precautions": ["避免湿度过高"]
                },
                "ventilation": {
                    "target_level": "良好",
                    "adjustment": "加强通风",
                    "steps": ["定时通风", "降低氨气", "增加空气流动"],
                    "effect": "减少飞沫传播",
                    "precautions": ["避免穿堂风"]
                },
                "cleanliness": {
                    "target_level": "高",
                    "adjustment": "定期消毒",
                    "steps": ["带禽消毒", "器具消毒", "环境消毒"],
                    "effect": "减少病原体",
                    "precautions": ["注意消毒时间"]
                }
            },
            "坏死性肠炎": {
                "temperature": {
                    "target_range": "24-28",
                    "adjustment": "保持适宜温度",
                    "steps": ["稳定温度", "避免温度波动", "保证温度均匀"],
                    "effect": "促进肠道恢复",
                    "precautions": ["避免高温"]
                },
                "humidity": {
                    "target_range": "50-60",
                    "adjustment": "控制湿度",
                    "steps": ["加强通风", "保持垫料干燥", "防止漏水"],
                    "effect": "减少梭菌繁殖",
                    "precautions": ["避免过度干燥"]
                },
                "cleanliness": {
                    "target_level": "高",
                    "adjustment": "加强清洁",
                    "steps": ["每日清理粪便", "定期消毒", "清理料槽"],
                    "effect": "减少环境中病原体",
                    "precautions": ["清洁后干燥"]
                },
                "density": {
                    "target": "降低",
                    "adjustment": "降低密度",
                    "steps": ["分群", "增加空间", "避免拥挤"],
                    "effect": "减少接触传播",
                    "precautions": ["保证足够饮水"]
                }
            },
            "滑液囊支原体": {
                "temperature": {
                    "target_range": "24-27",
                    "adjustment": "保持温暖环境",
                    "steps": ["提高舍温1-2℃", "避免低温", "加强保温"],
                    "effect": "减少关节应激，促进恢复",
                    "precautions": ["避免高温"]
                },
                "density": {
                    "target": "降低",
                    "adjustment": "降低饲养密度",
                    "steps": ["分群隔离", "增加活动空间", "避免拥挤"],
                    "effect": "减少接触传播，降低感染压力",
                    "precautions": ["保证足够采食空间"]
                },
                "cleanliness": {
                    "target_level": "高",
                    "adjustment": "定期消毒",
                    "steps": ["带禽消毒", "环境消毒", "器具消毒"],
                    "effect": "减少病原体传播",
                    "precautions": ["交替使用消毒剂"]
                }
            },
            "新城疫": {
                "temperature": {
                    "target_range": "24-28",
                    "adjustment": "保持温暖稳定",
                    "steps": ["提高舍温2-3℃", "避免温差过大", "加强保温"],
                    "effect": "减少应激，提高抵抗力",
                    "precautions": ["避免高温"]
                },
                "humidity": {
                    "target_range": "55-65",
                    "adjustment": "保持适宜湿度",
                    "steps": ["加湿或通风", "避免极端湿度"],
                    "effect": "保护呼吸道黏膜",
                    "precautions": ["避免湿度过高"]
                },
                "cleanliness": {
                    "target_level": "极高",
                    "adjustment": "严格消毒隔离",
                    "steps": ["彻底消毒", "隔离病禽", "禁止人员流动"],
                    "effect": "阻断传播途径",
                    "precautions": ["注意生物安全"]
                },
                "ventilation": {
                    "target_level": "良好",
                    "adjustment": "加强通风",
                    "steps": ["定时通风", "保持空气新鲜", "降低氨气"],
                    "effect": "减少病毒传播",
                    "precautions": ["避免冷风直吹"]
                }
            },
            "传染性支气管炎": {
                "temperature": {
                    "target_range": "26-30",
                    "adjustment": "保持较高温度",
                    "steps": ["提高舍温2-3℃", "加强保温", "避免低温"],
                    "effect": "减少呼吸道刺激，提高抵抗力",
                    "precautions": ["避免高温"]
                },
                "humidity": {
                    "target_range": "55-65",
                    "adjustment": "保持适宜湿度",
                    "steps": ["加湿", "避免干燥", "控制湿度"],
                    "effect": "保护呼吸道黏膜",
                    "precautions": ["避免湿度过高"]
                },
                "ventilation": {
                    "target_level": "良好",
                    "adjustment": "加强通风",
                    "steps": ["定时通风", "保持空气新鲜", "降低氨气"],
                    "effect": "减少病毒传播",
                    "precautions": ["避免穿堂风"]
                },
                "cleanliness": {
                    "target_level": "高",
                    "adjustment": "定期消毒",
                    "steps": ["带禽消毒", "环境消毒", "器具消毒"],
                    "effect": "减少病毒数量",
                    "precautions": ["注意消毒频率"]
                }
            },
            "组织滴虫病": {
                "temperature": {
                    "target_range": "24-28",
                    "adjustment": "保持适宜温度",
                    "steps": ["稳定温度", "避免温度波动", "保证温度均匀"],
                    "effect": "减少应激，提高抵抗力",
                    "precautions": ["避免高温"]
                },
                "humidity": {
                    "target_range": "45-55",
                    "adjustment": "降低湿度",
                    "steps": ["加强通风", "保持垫料干燥", "防止漏水"],
                    "effect": "减少虫卵发育",
                    "precautions": ["避免过度干燥"]
                },
                "cleanliness": {
                    "target_level": "高",
                    "adjustment": "加强清洁",
                    "steps": ["每日清理粪便", "定期消毒", "更换垫料"],
                    "effect": "减少虫卵污染",
                    "precautions": ["注意消毒效果"]
                }
            },
            "蛔虫病": {
                "temperature": {
                    "target_range": "24-28",
                    "adjustment": "保持适宜温度",
                    "steps": ["稳定温度", "避免温度波动"],
                    "effect": "减少应激，提高驱虫效果",
                    "precautions": ["避免极端温度"]
                },
                "humidity": {
                    "target_range": "50-60",
                    "adjustment": "控制湿度",
                    "steps": ["加强通风", "保持干燥", "防止潮湿"],
                    "effect": "减少虫卵存活",
                    "precautions": ["避免过度干燥"]
                },
                "cleanliness": {
                    "target_level": "高",
                    "adjustment": "加强清洁消毒",
                    "steps": ["每日清理粪便", "定期消毒", "清理料槽"],
                    "effect": "减少环境中虫卵",
                    "precautions": ["粪便需发酵处理"]
                }
            },
            "绦虫病": {
                "temperature": {
                    "target_range": "24-28",
                    "adjustment": "保持适宜温度",
                    "steps": ["稳定温度", "避免温度波动"],
                    "effect": "减少应激，提高驱虫效果",
                    "precautions": ["避免极端温度"]
                },
                "cleanliness": {
                    "target_level": "高",
                    "adjustment": "加强清洁",
                    "steps": ["每日清理粪便", "定期消毒", "清理环境"],
                    "effect": "减少中间宿主滋生",
                    "precautions": ["注意消灭昆虫宿主"]
                }
            }
        }
    
    def _adjust_temperature_by_age(self, target_range: str, age_stage: str) -> str:
        """根据养殖阶段调整温度目标范围"""
        base_low, base_high = map(int, target_range.split("-"))
        
        age_adjustments = {
            "育雏期(0-14日龄)": (4, 8),
            "育成期(15-35日龄)": (2, 4),
            "育肥期(36日龄-出栏)": (0, 2),
            "产蛋前期": (-1, 1),
            "产蛋高峰期": (-2, 0),
            "产蛋后期": (-2, 0)
        }
        
        adjustment = age_adjustments.get(age_stage, (0, 0))
        new_low = base_low + adjustment[0]
        new_high = base_high + adjustment[1]
        
        return f"{new_low}-{new_high}"
    
    def _adjust_humidity_by_age(self, target_range: str, age_stage: str) -> str:
        """根据养殖阶段调整湿度目标范围"""
        base_low, base_high = map(int, target_range.split("-"))
        
        age_adjustments = {
            "育雏期(0-14日龄)": (5, 10),
            "育成期(15-35日龄)": (0, 0),
            "育肥期(36日龄-出栏)": (-5, 0),
            "产蛋前期": (0, 0),
            "产蛋高峰期": (0, 0),
            "产蛋后期": (0, 0)
        }
        
        adjustment = age_adjustments.get(age_stage, (0, 0))
        new_low = max(40, base_low + adjustment[0])
        new_high = min(80, base_high + adjustment[1])
        
        return f"{new_low}-{new_high}"
    
    def generate_adjustments(self, disease_name: str, animal_profile: AnimalProfile = None, 
                              shed_env: ShedEnvironment = None, age_stage: str = "") -> List[EnvironmentAdjustment]:
        """根据疾病名称生成环境调整建议"""
        adjustments = []
        
        rules = self.disease_environment_rules.get(disease_name, {})
        
        if "temperature" in rules:
            rule = rules["temperature"]
            current_temp = str(shed_env.temperature) + "℃" if shed_env and shed_env.temperature else "未知"
            target_range = self._adjust_temperature_by_age(rule["target_range"], age_stage)
            adjustments.append(EnvironmentAdjustment(
                category="温度控制",
                title=rule["adjustment"],
                current_value=current_temp,
                target_value=f"{target_range}℃",
                adjustment_steps=rule["steps"],
                expected_effect=rule["effect"],
                precautions=rule["precautions"]
            ))
        
        if "humidity" in rules:
            rule = rules["humidity"]
            current_humidity = str(shed_env.humidity) + "%" if shed_env and shed_env.humidity else "未知"
            target_range = self._adjust_humidity_by_age(rule["target_range"], age_stage)
            adjustments.append(EnvironmentAdjustment(
                category="湿度控制",
                title=rule["adjustment"],
                current_value=current_humidity,
                target_value=f"{target_range}%",
                adjustment_steps=rule["steps"],
                expected_effect=rule["effect"],
                precautions=rule["precautions"]
            ))
        
        if "ventilation" in rules:
            rule = rules["ventilation"]
            current_vent = shed_env.ventilation_status if shed_env and shed_env.ventilation_status else "未知"
            adjustments.append(EnvironmentAdjustment(
                category="通风管理",
                title=rule["adjustment"],
                current_value=current_vent,
                target_value=rule["target_level"],
                adjustment_steps=rule["steps"],
                expected_effect=rule["effect"],
                precautions=rule["precautions"]
            ))
        
        if "cleanliness" in rules:
            rule = rules["cleanliness"]
            current_clean = shed_env.cleanliness_level if shed_env and shed_env.cleanliness_level else "未知"
            adjustments.append(EnvironmentAdjustment(
                category="清洁消毒",
                title=rule["adjustment"],
                current_value=current_clean,
                target_value=rule["target_level"],
                adjustment_steps=rule["steps"],
                expected_effect=rule["effect"],
                precautions=rule["precautions"]
            ))
        
        if "density" in rules:
            rule = rules["density"]
            current_density = shed_env.stocking_density if shed_env and shed_env.stocking_density else "未知"
            adjustments.append(EnvironmentAdjustment(
                category="饲养密度",
                title=rule["adjustment"],
                current_value=current_density,
                target_value=rule["target"],
                adjustment_steps=rule["steps"],
                expected_effect=rule["effect"],
                precautions=rule["precautions"]
            ))
        
        if "ammonia" in rules:
            rule = rules["ammonia"]
            current_ammonia = shed_env.ammonia_level if shed_env and shed_env.ammonia_level else "未知"
            adjustments.append(EnvironmentAdjustment(
                category="氨气控制",
                title=rule["adjustment"],
                current_value=current_ammonia,
                target_value=f"{rule['target_level']}ppm",
                adjustment_steps=rule["steps"],
                expected_effect=rule["effect"],
                precautions=rule["precautions"]
            ))
        
        return adjustments
    
    def _merge_range_values(self, range1: str, range2: str) -> str:
        """合并两个范围值，取交集（更严格的值）"""
        try:
            if "℃" in range1:
                range1 = range1.replace("℃", "")
            if "%" in range1:
                range1 = range1.replace("%", "")
            if "ppm" in range1:
                range1 = range1.replace("ppm", "")
                
            if "℃" in range2:
                range2 = range2.replace("℃", "")
            if "%" in range2:
                range2 = range2.replace("%", "")
            if "ppm" in range2:
                range2 = range2.replace("ppm", "")
            
            if "-" in range1 and "-" in range2:
                low1, high1 = map(int, range1.split("-"))
                low2, high2 = map(int, range2.split("-"))
                
                new_low = max(low1, low2)
                new_high = min(high1, high2)
                
                if new_low <= new_high:
                    return f"{new_low}-{new_high}"
                else:
                    return f"{low1}-{high1}"
            else:
                return range1
        except:
            return range1
    
    def generate_comprehensive_adjustments(self, diseases: List[str], 
                                           animal_profile: AnimalProfile = None,
                                           shed_env: ShedEnvironment = None,
                                           age_stage: str = "") -> List[EnvironmentAdjustment]:
        """根据多个疾病生成综合环境调整建议，同类别取交集或更严格值"""
        category_adjustments = {}
        
        for disease in diseases:
            adjustments = self.generate_adjustments(disease, animal_profile, shed_env, age_stage)
            for adj in adjustments:
                if adj.category not in category_adjustments:
                    category_adjustments[adj.category] = adj
                else:
                    existing = category_adjustments[adj.category]
                    
                    if "-" in existing.target_value and "-" in adj.target_value:
                        new_target = self._merge_range_values(existing.target_value, adj.target_value)
                        
                        combined_steps = []
                        for step in existing.adjustment_steps:
                            if step not in combined_steps:
                                combined_steps.append(step)
                        for step in adj.adjustment_steps:
                            if step not in combined_steps:
                                combined_steps.append(step)
                        
                        combined_precautions = []
                        for p in existing.precautions:
                            if p not in combined_precautions:
                                combined_precautions.append(p)
                        for p in adj.precautions:
                            if p not in combined_precautions:
                                combined_precautions.append(p)
                        
                        category_adjustments[adj.category] = EnvironmentAdjustment(
                            category=adj.category,
                            title=existing.title if "严格" in existing.title else adj.title,
                            current_value=existing.current_value,
                            target_value=new_target + ("℃" if "温度" in adj.category else "%"),
                            adjustment_steps=combined_steps,
                            expected_effect=f"{existing.expected_effect}；{adj.expected_effect}",
                            precautions=combined_precautions
                        )
        
        return list(category_adjustments.values())


def get_environment_adjustment_engine() -> EnvironmentAdjustmentEngine:
    """获取环境调整建议引擎实例"""
    return EnvironmentAdjustmentEngine()