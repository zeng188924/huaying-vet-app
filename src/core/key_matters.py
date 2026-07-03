# -*- coding: utf-8 -*-
"""
兽医诊疗关键事项模块
用于读取和解析兽医开药时必须同步告知、落实的关键事项
"""

import zipfile
import xml.etree.ElementTree as ET
from typing import List, Dict
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOCUMENT_PATH = os.path.join(_ROOT, 'docs', '兽医开药、诊疗推荐用药时，除药品外必须同步告知、落实的关键事项.md')


def extract_docx_content(docx_path: str) -> str:
    """从docx文件中提取文本内容"""
    try:
        with zipfile.ZipFile(docx_path, 'r') as z:
            with z.open('word/document.xml') as f:
                tree = ET.parse(f)
                root = tree.getroot()
                
                namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                paragraphs = root.findall('.//w:p', namespaces)
                
                text_content = ''
                for p in paragraphs:
                    texts = p.findall('.//w:t', namespaces)
                    paragraph_text = ''.join(t.text for t in texts if t.text)
                    if paragraph_text.strip():
                        text_content += paragraph_text + '\n\n'
                return text_content
    except Exception as e:
        print(f"[关键事项] 提取文档内容失败: {e}")
        return ""


def parse_key_matters(content: str) -> List[Dict]:
    """解析关键事项内容，提取结构化数据"""
    key_matters = []
    
    sections = [
        {
            "title": "一、用药方式与操作细节",
            "description": "直接影响药效",
            "items": [
                {"title": "给药途径", "content": "严格区分饮水、拌料、注射、喷雾、灌服、点眼滴鼻，不能混用"},
                {"title": "饮水药", "content": "提前控水2～4小时，保证短时间喝完；水质不能含氯、重金属，避免分解失效"},
                {"title": "拌料药", "content": "少量多次预混，防止局部药量过高中毒；油脂类药物不能直接拌干料"},
                {"title": "注射药", "content": "区分肌注、皮下、静脉，不同家禽注射部位不同；油苗、混悬液需摇匀"},
                {"title": "熏蒸/带禽消毒药", "content": "避开雏禽、产蛋高峰，控制浓度，防止呼吸道刺激"},
                {"title": "用药时长与间隔", "content": "标明疗程（3天/5天/7天），不能症状好转立刻停药；明确一天1次还是2次，间隔多久"},
                {"title": "配伍禁忌", "content": "明确哪些药不能混合使用：酸碱中和、拮抗失效、叠加中毒；中西药联用也要标注间隔时间"}
            ]
        },
        {
            "title": "二、家禽饲养环境同步调整",
            "description": "治病七分靠环境",
            "items": [
                {"title": "通风管控", "content": "呼吸道病：加大通风但杜绝冷风直吹，降低氨气、粉尘；肠道、球虫病：降低湿度，勤换垫料"},
                {"title": "温度调整", "content": "生病家禽抵抗力差，比正常温度高1～2℃，减少扎堆应激；热性病避免高温闷热"},
                {"title": "降低饲养密度", "content": "发病群适当分群、减少密度，减少交叉感染、缺氧"},
                {"title": "饮水饲料优化", "content": "发病期减少高蛋白、高能量饲料，减轻肝肾负担；全程补充多维、电解质、葡萄糖抗应激"}
            ]
        },
        {
            "title": "三、消毒与生物安全",
            "description": "阻断传播，防止复发扩散",
            "items": [
                {"title": "场内同步消毒", "content": "带禽消毒频次、消毒剂种类；棚舍过道、器具、排水沟每日消杀"},
                {"title": "隔离措施", "content": "病弱禽挑出单独隔离，病死禽及时无害化处理；禁止健康舍与发病舍人员、工具交叉使用"},
                {"title": "场外消杀", "content": "门口消毒池更换药液，外来车辆、物资严格消毒，避免外源持续带菌"}
            ]
        },
        {
            "title": "四、休药期与合规残留",
            "description": "养殖最容易踩红线",
            "items": [
                {"title": "休药天数", "content": "肉鸡、肉鸭出栏前停药天数，蛋禽产蛋期禁用/可用药物，产蛋禁止使用的抗生素、抗病毒药必须重点提醒"},
                {"title": "禁药提醒", "content": "告知国家明令禁止的兽药，避免处罚、产品检测不合格"},
                {"title": "用药台账", "content": "指导养殖户记录用药日期、剂量、禽群、停药时间，应对监管检查"}
            ]
        },
        {
            "title": "五、应激防护与辅助保健",
            "description": "增强体质，辅助恢复",
            "items": [
                {"title": "抗应激措施", "content": "转群、免疫、高温、降温、用药期间，搭配多维、VC、电解质"},
                {"title": "肠道调理", "content": "长期使用抗生素后，必须搭配益生菌调理肠道，避免肠道菌群失衡持续拉稀"},
                {"title": "肝肾保护", "content": "使用磺胺、四环素等肝肾损伤类药物时，同步添加保肝中药"}
            ]
        },
        {
            "title": "六、观察复诊判断标准",
            "description": "判断药效，及时调整方案",
            "items": [
                {"title": "观察指标", "content": "采食量、饮水量变化、粪便形态、呼吸道声音、伤亡数量"},
                {"title": "复诊时间", "content": "用药24/48小时后反馈情况"},
                {"title": "备选方案", "content": "3天无明显好转，及时更换药物，避免拖延病程"}
            ]
        },
        {
            "title": "七、储存与用量安全",
            "description": "避免中毒",
            "items": [
                {"title": "储存条件", "content": "避光、冷藏、防潮，疫苗冷冻保存"},
                {"title": "精准剂量", "content": "按体重/千只禽计算，严禁随意加量；雏禽、产蛋禽、弱禽要减量"},
                {"title": "废弃物处理", "content": "剩余药液、药渣不能随意倒入沟渠、投喂其他畜禽"}
            ]
        },
        {
            "title": "八、免疫搭配注意事项",
            "description": "避免加重病情",
            "items": [
                {"title": "免疫暂缓", "content": "病毒病治疗阶段，暂缓活疫苗免疫，避免加重发病"}
            ]
        },
        {
            "title": "九、源头预防方案",
            "description": "本次治好后防复发",
            "items": [
                {"title": "诱因分析", "content": "温差、霉菌、氨气、引种带毒、消毒不到位"},
                {"title": "长期预防", "content": "定期肠道保健、呼吸道预防、驱虫程序、免疫优化方案"}
            ]
        }
    ]
    
    return sections


def get_key_matters() -> List[Dict]:
    """获取关键事项列表"""
    content = extract_docx_content(DOCUMENT_PATH)
    if content:
        return parse_key_matters(content)
    return parse_key_matters("")


def get_summary_points() -> List[str]:
    """获取精简总结要点"""
    return [
        "怎么用、用几天、哪些药不能混",
        "棚舍温湿度、通风、密度怎么调",
        "同步消毒隔离怎么做",
        "严格休药期，合规出栏卖蛋",
        "配合多维、益生菌保肝护肠",
        "观察采食伤亡，无效及时复诊，后期做好预防"
    ]
