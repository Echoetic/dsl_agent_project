"""
LLM意图识别模块
使用Google Gemini API进行自然语言理解和意图识别
"""

import json
import re
import requests
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import time


@dataclass
class IntentResult:
    """意图识别结果"""
    intent: str                    # 识别出的意图
    confidence: float              # 置信度 0-1
    entities: Dict[str, Any]       # 提取的实体
    raw_response: str              # 原始响应
    is_silence: bool = False       # 是否为静默


class LLMError(Exception):
    """LLM调用错误"""
    pass


class GeminiIntentRecognizer:
    """使用Gemini进行意图识别"""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.session = requests.Session()
    
    def _make_request(self, prompt: str, max_retries: int = 3) -> str:
        """发送请求到Gemini API"""
        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 500,
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        for attempt in range(max_retries):
            try:
                response = self.session.post(url, json=payload, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    if "candidates" in result and result["candidates"]:
                        content = result["candidates"][0].get("content", {})
                        parts = content.get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                    return ""
                elif response.status_code == 429:
                    # 速率限制，等待后重试
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise LLMError(f"API请求失败: {response.status_code} - {response.text}")
            
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                raise LLMError("API请求超时")
            except requests.exceptions.RequestException as e:
                raise LLMError(f"网络错误: {str(e)}")
        
        raise LLMError("达到最大重试次数")
    
    def recognize_intent(self, 
                        user_input: str, 
                        available_intents: List[str],
                        context: Optional[Dict[str, Any]] = None) -> IntentResult:
        """
        识别用户意图
        
        Args:
            user_input: 用户输入的文本
            available_intents: 可用的意图列表
            context: 上下文信息（可选）
        
        Returns:
            IntentResult: 意图识别结果
        """
        if not user_input or user_input.strip() == "":
            return IntentResult(
                intent="",
                confidence=0.0,
                entities={},
                raw_response="",
                is_silence=True
            )
        
        # 构建提示词
        prompt = self._build_intent_prompt(user_input, available_intents, context)
        
        try:
            response = self._make_request(prompt)
            return self._parse_intent_response(response, available_intents)
        except LLMError as e:
            # 如果LLM调用失败，尝试使用简单的关键词匹配
            return self._fallback_intent_match(user_input, available_intents)
    
    def _build_intent_prompt(self, 
                            user_input: str, 
                            available_intents: List[str],
                            context: Optional[Dict[str, Any]] = None) -> str:
        """构建意图识别提示词"""
        
        intent_list = "\n".join([f"- {intent}" for intent in available_intents])
        
        context_str = ""
        if context:
            context_str = f"\n当前对话上下文:\n{json.dumps(context, ensure_ascii=False, indent=2)}\n"
        
        prompt = f"""你是一个智能客服意图识别系统。请分析用户的输入，识别其意图。

可用的意图类别:
{intent_list}
{context_str}
用户输入: "{user_input}"

请以JSON格式返回识别结果，格式如下:
{{
    "intent": "识别出的意图（必须是上述意图列表中的一个，如果都不匹配则返回空字符串）",
    "confidence": 0.0到1.0之间的置信度,
    "entities": {{提取的相关实体，如数量、名称等}}
}}

注意：
1. intent必须完全匹配上述意图列表中的某一项
2. 如果用户输入与任何意图都不相关，intent返回空字符串
3. 只返回JSON，不要有其他文字"""
        
        return prompt
    
    def _parse_intent_response(self, 
                              response: str, 
                              available_intents: List[str]) -> IntentResult:
        """解析意图识别响应"""
        try:
            # 尝试提取JSON
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                intent = result.get("intent", "")
                confidence = float(result.get("confidence", 0.0))
                entities = result.get("entities", {})
                
                # 验证意图是否在可用列表中
                if intent and intent not in available_intents:
                    # 尝试模糊匹配
                    for available in available_intents:
                        if intent.lower() in available.lower() or available.lower() in intent.lower():
                            intent = available
                            break
                    else:
                        intent = ""
                        confidence = 0.0
                
                return IntentResult(
                    intent=intent,
                    confidence=min(max(confidence, 0.0), 1.0),
                    entities=entities if isinstance(entities, dict) else {},
                    raw_response=response
                )
        except (json.JSONDecodeError, ValueError, KeyError):
            pass
        
        # 解析失败，使用回退方法
        return self._fallback_intent_match(response, available_intents)
    
    def _fallback_intent_match(self, 
                              text: str, 
                              available_intents: List[str]) -> IntentResult:
        """回退的关键词匹配方法"""
        text_lower = text.lower()
        
        for intent in available_intents:
            intent_lower = intent.lower()
            # 检查意图关键词是否在文本中
            if intent_lower in text_lower:
                return IntentResult(
                    intent=intent,
                    confidence=0.6,
                    entities={},
                    raw_response=f"fallback_match: {intent}"
                )
            
            # 检查文本关键词是否在意图中
            words = text_lower.split()
            for word in words:
                if len(word) > 1 and word in intent_lower:
                    return IntentResult(
                        intent=intent,
                        confidence=0.4,
                        entities={},
                        raw_response=f"fallback_match: {intent}"
                    )
        
        return IntentResult(
            intent="",
            confidence=0.0,
            entities={},
            raw_response="no_match"
        )
    
    def extract_entities(self, 
                        user_input: str, 
                        entity_types: List[str]) -> Dict[str, Any]:
        """
        提取实体信息
        
        Args:
            user_input: 用户输入
            entity_types: 要提取的实体类型列表
        
        Returns:
            提取的实体字典
        """
        entity_list = ", ".join(entity_types)
        
        prompt = f"""从以下用户输入中提取信息。

用户输入: "{user_input}"

请提取以下类型的信息: {entity_list}

以JSON格式返回，例如:
{{"数量": 2, "菜品": "红烧肉"}}

只返回JSON，不要有其他文字。如果某类信息不存在，不要包含该字段。"""
        
        try:
            response = self._make_request(prompt)
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {}
    
    def generate_response(self, 
                         template: str, 
                         context: Dict[str, Any]) -> str:
        """
        生成自然语言响应
        
        Args:
            template: 响应模板
            context: 上下文信息
        
        Returns:
            生成的响应文本
        """
        prompt = f"""请根据以下模板和上下文信息，生成自然流畅的回复。

模板: {template}
上下文: {json.dumps(context, ensure_ascii=False)}

生成一句自然、友好的回复，直接返回回复内容，不要有其他文字。"""
        
        try:
            return self._make_request(prompt)
        except:
            # 如果生成失败，简单地进行模板替换
            result = template
            for key, value in context.items():
                result = result.replace(f"${key}", str(value))
            return result


class MockIntentRecognizer:
    """模拟的意图识别器（用于测试）"""
    
    def __init__(self):
        self.responses = {}
    
    def set_response(self, user_input: str, intent: str, confidence: float = 0.9):
        """设置模拟响应"""
        self.responses[user_input.lower()] = IntentResult(
            intent=intent,
            confidence=confidence,
            entities={},
            raw_response="mock"
        )
    
    def recognize_intent(self, 
                        user_input: str, 
                        available_intents: List[str],
                        context: Optional[Dict[str, Any]] = None) -> IntentResult:
        """模拟意图识别"""
        if not user_input or user_input.strip() == "":
            return IntentResult(
                intent="",
                confidence=0.0,
                entities={},
                raw_response="",
                is_silence=True
            )
        
        # 检查是否有预设响应
        lower_input = user_input.lower()
        if lower_input in self.responses:
            return self.responses[lower_input]
        
        # 简单的关键词匹配
        for intent in available_intents:
            if intent.lower() in lower_input:
                return IntentResult(
                    intent=intent,
                    confidence=0.8,
                    entities={},
                    raw_response="keyword_match"
                )
        
        return IntentResult(
            intent="",
            confidence=0.0,
            entities={},
            raw_response="no_match"
        )


def create_intent_recognizer(api_key: Optional[str] = None, 
                            use_mock: bool = False) -> 'GeminiIntentRecognizer | MockIntentRecognizer':
    """
    创建意图识别器
    
    Args:
        api_key: Gemini API密钥
        use_mock: 是否使用模拟识别器
    
    Returns:
        意图识别器实例
    """
    if use_mock or not api_key:
        return MockIntentRecognizer()
    return GeminiIntentRecognizer(api_key)
