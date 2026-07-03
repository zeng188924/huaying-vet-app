# -*- coding: utf-8 -*-
"""
内容提取模块
- 图片OCR识别（JPG、PNG等）：优先 Tesseract，未安装时自动回退 RapidOCR
- PDF文本提取
- 语音转文字（MP3、WAV等）
- 智能字段解析，将提取内容映射到产品信息表单

注意：需要安装系统依赖才能使用完整功能
- Tesseract OCR（可选）: https://github.com/tesseract-ocr/tesseract
- RapidOCR（可选，Python 包）: pip install rapidocr-onnxruntime
- FFmpeg: https://ffmpeg.org/
- Poppler: https://poppler.freedesktop.org/
"""

import os
import re
import tempfile
from typing import Dict, Optional, Any

_PIL_OK = False
_TESSERACT_OK = False
_RAPIDOCR_OK = False
_SPEECH_OK = False
_PYDUB_OK = False
_PDF2IMAGE_OK = False

try:
    from PIL import Image
    _PIL_OK = True
except ImportError:
    pass

try:
    import pytesseract
    _TESSERACT_OK = True
except ImportError:
    pass

try:
    from rapidocr_onnxruntime import RapidOCR
    _RAPIDOCR_OK = True
except ImportError:
    pass

try:
    import speech_recognition as sr
    _SPEECH_OK = True
except ImportError:
    pass

try:
    from pydub import AudioSegment
    _PYDUB_OK = True
except ImportError:
    pass
try:
    from pdf2image import convert_from_path
    _PDF2IMAGE_OK = True
except ImportError:
    _PDF2IMAGE_OK = False

try:
    import numpy as np
    _NUMPY_OK = True
except ImportError:
    _NUMPY_OK = False


IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "bmp", "webp"}
PDF_EXTENSIONS = {"pdf"}
AUDIO_EXTENSIONS = {"mp3", "wav", "flac", "ogg", "aac", "m4a"}


class ContentExtractor:
    def __init__(self):
        self.supported_formats = {
            "image": IMAGE_EXTENSIONS,
            "pdf": PDF_EXTENSIONS,
            "audio": AUDIO_EXTENSIONS,
        }

    def extract_from_file(self, file_path: str, file_ext: str = "") -> Dict[str, Any]:
        if not file_ext:
            file_ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""

        result = {
            "success": False,
            "raw_text": "",
            "parsed_fields": {},
            "error": "",
            "file_type": "",
            "available": False,
        }

        try:
            if file_ext in IMAGE_EXTENSIONS:
                result["file_type"] = "image"
                if _PIL_OK and (_TESSERACT_OK or _RAPIDOCR_OK):
                    result["available"] = True
                    raw_text = self._extract_from_image(file_path)
                else:
                    result["error"] = "图片识别依赖未安装（PIL/pytesseract/rapidocr-onnxruntime）"
                    return result

            elif file_ext in PDF_EXTENSIONS:
                result["file_type"] = "pdf"
                if _PDF2IMAGE_OK and (_TESSERACT_OK or _RAPIDOCR_OK):
                    result["available"] = True
                    raw_text = self._extract_from_pdf(file_path)
                else:
                    result["error"] = "PDF识别依赖未安装（pdf2image/pytesseract/rapidocr-onnxruntime）"
                    return result

            elif file_ext in AUDIO_EXTENSIONS:
                result["file_type"] = "audio"
                if _SPEECH_OK:
                    result["available"] = True
                    raw_text = self._extract_from_audio(file_path)
                else:
                    result["error"] = "语音识别依赖未安装（speech_recognition）"
                    return result

            else:
                result["error"] = f"不支持的文件格式: .{file_ext}"
                return result

            result["raw_text"] = raw_text
            result["parsed_fields"] = self._parse_text_to_fields(raw_text)
            result["success"] = True

        except Exception as e:
            result["error"] = str(e)

        return result

    def _ocr_image_to_text(self, image_input) -> str:
        """优先使用 Tesseract，失败或未安装时回退 RapidOCR。"""
        if _TESSERACT_OK:
            try:
                return pytesseract.image_to_string(image_input, lang='chi_sim').strip()
            except Exception:
                pass

        if _RAPIDOCR_OK:
            try:
                engine = RapidOCR()
                # RapidOCR 不支持 PIL.Image，转换为 numpy array
                if _PIL_OK and isinstance(image_input, Image.Image) and _NUMPY_OK:
                    ocr_input = np.array(image_input)
                else:
                    ocr_input = image_input
                result, _ = engine(ocr_input)
                if result:
                    # RapidOCR 返回 [(box, text, score), ...]
                    lines = [item[1] for item in result if item[1]]
                    return "\n".join(lines)
            except Exception:
                pass

        raise RuntimeError("没有可用的 OCR 引擎（Tesseract 或 RapidOCR）")

    def _extract_from_image(self, file_path: str) -> str:
        try:
            img = Image.open(file_path)
            return self._ocr_image_to_text(img)
        except Exception as e:
            try:
                img = Image.open(file_path).convert('RGB')
                return self._ocr_image_to_text(img)
            except Exception:
                raise e

    def _extract_from_pdf(self, file_path: str) -> str:
        pages = convert_from_path(file_path)
        texts = []
        for page in pages:
            text = self._ocr_image_to_text(page)
            texts.append(text.strip())
        return "\n".join(texts)

    def _extract_from_audio(self, file_path: str) -> str:
        recognizer = sr.Recognizer()

        wav_path = file_path
        ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""

        if ext != "wav" and _PYDUB_OK:
            try:
                audio = AudioSegment.from_file(file_path)
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    wav_path = f.name
                audio.export(wav_path, format="wav")
            except Exception as e:
                raise ValueError(f"音频格式转换失败: {e}")

        try:
            with sr.AudioFile(wav_path) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data, language='zh-CN')
                return text.strip()
        except sr.UnknownValueError:
            raise ValueError("无法识别音频内容")
        except sr.RequestError as e:
            raise ValueError(f"语音识别服务请求失败: {e}")
        finally:
            if wav_path != file_path and os.path.exists(wav_path):
                os.remove(wav_path)

    def _parse_text_to_fields(self, text: str) -> Dict[str, Any]:
        fields = {}
        if not text:
            return fields

        # 统一全角/半角冒号、方括号，方便正则匹配
        normalized = text.replace("【", "[").replace("】", "]")

        patterns = {
            "name": [
                # 标签：值
                r"(?:产品名称|商品名|名称|药品名|药名)\s*[：:]\s*(.+?)(?:\n|$)",
                # 【标签】值 或 【标签】\n值
                r"\[(?:产品名称|商品名|名称|药品名|药名)\]\s*(.+?)(?:\n|【|\[|$)",
                # 标签 值（无标点）
                r"(?:产品名称|商品名|名称|药品名|药名)\s+(.+?)(?:\n|$)",
            ],
            "main_component": [
                r"(?:主要成分|成分|有效成分|含量)\s*[：:]\s*(.+?)(?:\n|$)",
                r"\[(?:主要成分|成分|有效成分|含量)\]\s*(.+?)(?:\n|【|\[|$)",
                r"(?:主要成分|成分|有效成分|含量)\s+(.+?)(?:\n|$)",
            ],
            "spec": [
                r"(?:规格|包装规格|剂型|包装)\s*[：:]\s*(.+?)(?:\n|$)",
                r"\[(?:规格|包装规格|剂型|包装)\]\s*(.+?)(?:\n|【|\[|$)",
                r"(?:规格|包装规格|剂型|包装)\s+(.+?)(?:\n|$)",
            ],
            "price": [
                r"(?:价格|售价|单价)\s*[：:]\s*([\d.]+)",
                r"[¥￥]\s*([\d.]+)",
            ],
            "category": [
                r"(?:类别|分类|类型)\s*[：:]\s*(.+?)(?:\n|$)",
                r"\[(?:类别|分类|类型)\]\s*(.+?)(?:\n|【|\[|$)",
                # 仅在行首/行尾/空白处出现分类关键词时才匹配，避免正文中的“卵黄抗体”被误识别
                r"(?:^|\n|\s)(化药|中药|抗生素|营养类|微生态|免疫增强剂|消毒剂类|消毒剂|抗病毒类产品|抗病毒|抗支原体药|抗支原体|抗球虫类|抗球虫|驱霉菌类产品|驱霉菌|解热镇痛|保肝类护肾类|保肝护肾|特色类产品|特色类|腺胃炎产品|腺胃炎|气囊炎类产品|气囊炎|气管栓塞呼吸道药|呼吸道|肠道类产品|肠道|饲料添加剂|维生素|抗体类产品|抗体|增蛋类产品|增蛋|防暑降温类产品|防暑降温|营养增料促生长)(?:\s|\n|$)",
            ],
            "usage_info": [
                r"(?:用法用量|用法|用量|使用方法)\s*[：:]\s*(.+?)(?:\n\n|【|\[|$)",
                r"\[(?:用法用量|用法|用量|使用方法)\]\s*(.+?)(?:\n\n|【|\[|$)",
            ],
            "water": [
                r"(?:兑水|稀释|溶解)\s*[：:]\s*(.+?)(?:\n|$)",
                r"\[(?:兑水|稀释|溶解|兑水量|稀释比例)\]\s*(.+?)(?:\n|【|\[|$)",
                r"(?:兑水量|稀释比例)\s*[：:]\s*(.+?)(?:\n|$)",
            ],
            "indications": [
                r"(?:适应症|适用症|功能主治|主治|用途|作用用途|作用与用途|适应证)\s*[：:]\s*(.+?)(?:\n\n|【|\[|$)",
                r"\[(?:适应症|适用症|功能主治|主治|用途|作用用途|作用与用途|适应证)\]\s*(.+?)(?:\n\n|【|\[|$)",
            ],
            "timing": [
                r"(?:时机|使用时机|适用阶段)\s*[：:]\s*(.+?)(?:\n|$)",
                r"\[(?:时机|使用时机|适用阶段)\]\s*(.+?)(?:\n|【|\[|$)",
            ],
        }

        for field_name, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, normalized, re.MULTILINE)
                if match:
                    # category 的某些模式只有 1 个捕获组
                    if field_name == "category":
                        value = match.group(2) if len(match.groups()) >= 2 else match.group(1)
                    else:
                        value = match.group(1)
                    value = value.strip()
                    # 清理末尾标点
                    value = re.sub(r"[。\.\s]+$", "", value)
                    if value and value not in ["：", ":", "-", "—"]:
                        fields[field_name] = value
                        break

        # 若未识别到产品名称，尝试从文本开头提取显眼的商品名
        if not fields.get("name"):
            fallback_name = self._extract_prominent_name(normalized)
            if fallback_name:
                fields["name"] = fallback_name

        if "price" in fields:
            try:
                fields["price"] = float(fields["price"])
            except ValueError:
                pass

        if "indications" in fields:
            fields["indications"] = self._split_list_field(fields["indications"])

        return fields

    def _extract_prominent_name(self, text: str) -> Optional[str]:
        """从文本顶部提取显眼的商品名（常见于华英产品图片）。"""
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        # 过滤掉明显不是名称的行
        ignore = {"华英", "HUAYING", "TAIQIJIAN", "当天使用", "第二天见效"}
        for ln in lines[:8]:
            # 忽略纯标题/章节行（含【】、[] 或常见标题词）
            if re.search(r"[\[【\]】]", ln):
                continue
            if re.match(r"^(主要成分|作用用途|用法用量|包装规格|治病机理|制备过程|适应症|规格|类别|产品名称|商品名)", ln):
                continue
            # 保留中文字符长度 >= 2 且 <= 10 的行
            chinese_chars = re.sub(r"[^\u4e00-\u9fff]", "", ln)
            if 2 <= len(chinese_chars) <= 10 and ln not in ignore:
                return ln
        return None

    def _split_list_field(self, value: str) -> list:
        if not value:
            return []
        text = str(value)
        parts = []
        current = []
        depth_paren = 0  # 小括号深度（含全角/半角）
        depth_bracket = 0  # 中括号深度
        for ch in text:
            if ch in "(（":
                depth_paren += 1
            elif ch in ")）":
                depth_paren = max(0, depth_paren - 1)
            elif ch == "[":
                depth_bracket += 1
            elif ch == "]":
                depth_bracket = max(0, depth_bracket - 1)

            if depth_paren == 0 and depth_bracket == 0 and ch in "、,，;；/":
                part = "".join(current).strip()
                if part:
                    parts.append(part)
                current = []
            else:
                current.append(ch)

        if current:
            part = "".join(current).strip()
            if part:
                parts.append(part)
        return parts


def extract_product_info(file_path: str, file_ext: str = "") -> Dict[str, Any]:
    extractor = ContentExtractor()
    return extractor.extract_from_file(file_path, file_ext)


def parse_product_text(text: str) -> Dict[str, Any]:
    """直接解析产品 OCR/说明文本，返回结构化字段（用于手动粘贴回填）。"""
    extractor = ContentExtractor()
    return {
        "success": bool(text and text.strip()),
        "raw_text": text or "",
        "parsed_fields": extractor._parse_text_to_fields(text or ""),
        "error": "" if (text and text.strip()) else "文本为空",
        "file_type": "manual_text",
        "available": True,
    }


def is_format_supported(file_ext: str) -> bool:
    file_ext = file_ext.lower()
    for formats in get_supported_formats().values():
        if file_ext in formats:
            return True
    return False


def get_supported_formats() -> Dict[str, list]:
    extractor = ContentExtractor()
    return extractor.supported_formats


def is_extraction_available() -> bool:
    return _PIL_OK and (_TESSERACT_OK or _RAPIDOCR_OK)