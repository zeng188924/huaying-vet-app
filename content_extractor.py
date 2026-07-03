# -*- coding: utf-8 -*-
"""
内容提取模块
- 图片OCR识别（JPG、PNG等）
- PDF文本提取
- 语音转文字（MP3、WAV等）
- 智能字段解析，将提取内容映射到产品信息表单

注意：需要安装系统依赖才能使用完整功能
- Tesseract OCR: https://github.com/tesseract-ocr/tesseract
- FFmpeg: https://ffmpeg.org/
- Poppler: https://poppler.freedesktop.org/
"""

import os
import re
import tempfile
from typing import Dict, Optional, Any

_PIL_OK = False
_TESSERACT_OK = False
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
    pass


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
                if _PIL_OK and _TESSERACT_OK:
                    result["available"] = True
                    raw_text = self._extract_from_image(file_path)
                else:
                    result["error"] = "图片识别依赖未安装（PIL/pytesseract）"
                    return result

            elif file_ext in PDF_EXTENSIONS:
                result["file_type"] = "pdf"
                if _PDF2IMAGE_OK and _TESSERACT_OK:
                    result["available"] = True
                    raw_text = self._extract_from_pdf(file_path)
                else:
                    result["error"] = "PDF识别依赖未安装（pdf2image/pytesseract）"
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

    def _extract_from_image(self, file_path: str) -> str:
        try:
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img, lang='chi_sim')
            return text.strip()
        except Exception as e:
            try:
                img = Image.open(file_path).convert('RGB')
                text = pytesseract.image_to_string(img, lang='chi_sim')
                return text.strip()
            except Exception:
                raise e

    def _extract_from_pdf(self, file_path: str) -> str:
        pages = convert_from_path(file_path)
        texts = []
        for page in pages:
            text = pytesseract.image_to_string(page, lang='chi_sim')
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

        patterns = {
            "name": [
                r"(产品名称|商品名|名称|药品名|药名)\s*[：:]\s*(.+)",
                r"(产品名称|商品名|名称|药品名|药名)\s*(.+)",
            ],
            "main_component": [
                r"(主要成分|成分|有效成分|含量)\s*[：:]\s*(.+)",
                r"(主要成分|成分|有效成分|含量)\s*(.+)",
            ],
            "spec": [
                r"(规格|包装规格|剂型|包装)\s*[：:]\s*(.+)",
                r"(规格|包装规格|剂型|包装)\s*(.+)",
            ],
            "price": [
                r"(价格|售价|单价)\s*[：:]\s*([\d.]+)",
                r"[¥￥]\s*([\d.]+)",
            ],
            "category": [
                r"(类别|分类|类型)\s*[：:]\s*(.+)",
                r"(化药|中药|抗生素|营养类|微生态|免疫增强剂|消毒剂|抗病毒|抗支原体|抗球虫|驱霉菌|解热镇痛|保肝护肾|特色类|腺胃炎|气囊炎|呼吸道|肠道|饲料添加剂|维生素|抗体|增蛋|防暑降温)",
            ],
            "usage_info": [
                r"(用法用量|用法|用量|使用方法)\s*[：:]\s*(.+)",
                r"(用法用量|用法|用量|使用方法)[\s\S]*?(?=\n\n|\Z)",
            ],
            "water": [
                r"(兑水|稀释|溶解)\s*[：:]\s*(.+)",
                r"(兑水量|稀释比例)\s*[：:]\s*(.+)",
            ],
            "indications": [
                r"(适应症|适用症|功能主治|主治|用途)\s*[：:]\s*(.+)",
                r"(适应症|适用症|功能主治|主治|用途)[\s\S]*?(?=\n\n|\Z)",
            ],
            "timing": [
                r"(时机|使用时机|适用阶段)\s*[：:]\s*(.+)",
            ],
        }

        for field_name, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, text, re.MULTILINE)
                if match:
                    value = match.group(1) if field_name == "category" else match.group(2)
                    value = value.strip()
                    if value and value not in ["：", ":", "-", "—"]:
                        fields[field_name] = value
                        break

        if "price" in fields:
            try:
                fields["price"] = float(fields["price"])
            except ValueError:
                pass

        if "indications" in fields:
            fields["indications"] = self._split_list_field(fields["indications"])

        return fields

    def _split_list_field(self, value: str) -> list:
        if not value:
            return []
        parts = re.split(r"[、,，;；/]+", str(value))
        return [p.strip() for p in parts if p.strip()]


def extract_product_info(file_path: str, file_ext: str = "") -> Dict[str, Any]:
    extractor = ContentExtractor()
    return extractor.extract_from_file(file_path, file_ext)


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
    return _PIL_OK and _TESSERACT_OK