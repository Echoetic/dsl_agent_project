"""
测试桩 (Test Stubs)
提供模拟的外部依赖，用于隔离测试
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class StubResponse:
    """桩响应"""
    data: Any
    delay: float = 0  # 模拟延迟（秒）
    error: Optional[str] = None


class LLMStub:
    """
    LLM服务桩
    模拟Gemini API的行为
    """
    
    def __init__(self):
        self.responses: Dict[str, StubResponse] = {}
        self.call_history: List[Dict] = []
        self.default_response = StubResponse(
            data={
                "intent": "",
                "confidence": 0.0,
                "entities": {}
            }
        )
    
    def set_response(self, input_pattern: str, response: StubResponse):
        """设置特定输入的响应"""
        self.responses[input_pattern.lower()] = response
    
    def set_intent_response(self, input_text: str, intent: str, 
                           confidence: float = 0.9, entities: Dict = None):
        """设置意图识别响应"""
        self.responses[input_text.lower()] = StubResponse(
            data={
                "intent": intent,
                "confidence": confidence,
                "entities": entities or {}
            }
        )
    
    def recognize_intent(self, user_input: str, 
                        available_intents: List[str]) -> Dict:
        """模拟意图识别"""
        self.call_history.append({
            "method": "recognize_intent",
            "input": user_input,
            "intents": available_intents
        })
        
        # 检查预设响应
        input_lower = user_input.lower()
        if input_lower in self.responses:
            return self.responses[input_lower].data
        
        # 简单关键词匹配
        for intent in available_intents:
            if intent.lower() in input_lower:
                return {
                    "intent": intent,
                    "confidence": 0.8,
                    "entities": {}
                }
        
        return self.default_response.data
    
    def get_call_count(self) -> int:
        """获取调用次数"""
        return len(self.call_history)
    
    def clear_history(self):
        """清除调用历史"""
        self.call_history = []


class ExternalServiceStub:
    """
    外部服务桩
    模拟医院、餐厅、剧院等外部服务
    """
    
    def __init__(self):
        self.services: Dict[str, StubResponse] = {}
        self.call_history: List[Dict] = []
        self._setup_default_services()
    
    def _setup_default_services(self):
        """设置默认服务响应"""
        # 医院服务
        self.services["创建挂号"] = StubResponse(
            data={"挂号单号": "H20241225001", "状态": "成功"}
        )
        self.services["查询费用"] = StubResponse(
            data={"挂号费": 50, "检查费": 200, "药费": 150}
        )
        self.services["处理缴费"] = StubResponse(
            data={"状态": "成功", "交易号": "T20241225001"}
        )
        
        # 餐厅服务
        self.services["获取菜单"] = StubResponse(
            data=[
                {"名称": "红烧肉", "价格": 48},
                {"名称": "清蒸鱼", "价格": 68}
            ]
        )
        self.services["确认订单"] = StubResponse(
            data={"订单号": "D20241225001", "状态": "已确认"}
        )
        
        # 剧院服务
        self.services["查询演出"] = StubResponse(
            data=[
                {"名称": "天鹅湖", "时间": "周六19:00", "价格": 280}
            ]
        )
        self.services["购票"] = StubResponse(
            data={"票号": "P20241225001", "状态": "成功"}
        )
    
    def set_service_response(self, service_name: str, response: StubResponse):
        """设置服务响应"""
        self.services[service_name] = response
    
    def call_service(self, service_name: str, *args) -> Any:
        """调用服务"""
        self.call_history.append({
            "service": service_name,
            "args": args
        })
        
        if service_name in self.services:
            stub = self.services[service_name]
            if stub.error:
                raise Exception(stub.error)
            return stub.data
        
        return {"error": f"未知服务: {service_name}"}
    
    def get_service_call_count(self, service_name: str = None) -> int:
        """获取服务调用次数"""
        if service_name:
            return sum(1 for c in self.call_history if c["service"] == service_name)
        return len(self.call_history)


class UserInputStub:
    """
    用户输入桩
    模拟用户输入序列
    """
    
    def __init__(self):
        self.inputs: List[str] = []
        self.current_index = 0
    
    def set_inputs(self, inputs: List[str]):
        """设置输入序列"""
        self.inputs = inputs
        self.current_index = 0
    
    def get_next_input(self) -> str:
        """获取下一个输入"""
        if self.current_index < len(self.inputs):
            result = self.inputs[self.current_index]
            self.current_index += 1
            return result
        return ""
    
    def has_more_inputs(self) -> bool:
        """是否还有更多输入"""
        return self.current_index < len(self.inputs)
    
    def reset(self):
        """重置索引"""
        self.current_index = 0


class OutputCapture:
    """
    输出捕获器
    捕获系统输出用于验证
    """
    
    def __init__(self):
        self.outputs: List[str] = []
    
    def capture(self, message: str):
        """捕获输出"""
        self.outputs.append(message)
    
    def get_all_outputs(self) -> List[str]:
        """获取所有输出"""
        return self.outputs
    
    def get_last_output(self) -> str:
        """获取最后一条输出"""
        return self.outputs[-1] if self.outputs else ""
    
    def contains(self, text: str) -> bool:
        """检查输出是否包含特定文本"""
        return any(text in output for output in self.outputs)
    
    def clear(self):
        """清除输出"""
        self.outputs = []


# 预配置的测试场景
class TestScenarios:
    """预配置的测试场景"""
    
    @staticmethod
    def hospital_registration():
        """医院挂号场景"""
        llm = LLMStub()
        llm.set_intent_response("挂号", "挂号", 0.95)
        llm.set_intent_response("内科", "内科", 0.9)
        llm.set_intent_response("张医生", "张医生", 0.85)
        llm.set_intent_response("确认", "确认", 0.9)
        
        user = UserInputStub()
        user.set_inputs(["挂号", "内科", "张医生", "确认"])
        
        return llm, user
    
    @staticmethod
    def restaurant_ordering():
        """餐厅点餐场景"""
        llm = LLMStub()
        llm.set_intent_response("点餐", "点餐", 0.95)
        llm.set_intent_response("红烧肉", "红烧肉", 0.9)
        llm.set_intent_response("米饭", "米饭", 0.9)
        llm.set_intent_response("完成", "完成", 0.9)
        llm.set_intent_response("微信", "微信", 0.85)
        
        user = UserInputStub()
        user.set_inputs(["点餐", "红烧肉", "米饭", "完成", "确认", "微信"])
        
        return llm, user
    
    @staticmethod
    def theater_ticketing():
        """剧院购票场景"""
        llm = LLMStub()
        llm.set_intent_response("查询", "查询", 0.95)
        llm.set_intent_response("天鹅湖", "天鹅湖", 0.9)
        llm.set_intent_response("购买", "购买", 0.9)
        llm.set_intent_response("A区", "A区", 0.85)
        llm.set_intent_response("2", "2", 0.9)
        
        user = UserInputStub()
        user.set_inputs(["查询", "天鹅湖", "购买", "A区", "2", "确认"])
        
        return llm, user


if __name__ == '__main__':
    # 测试桩示例
    print("=== LLM桩测试 ===")
    llm = LLMStub()
    llm.set_intent_response("我要挂号", "挂号", 0.95)
    result = llm.recognize_intent("我要挂号", ["挂号", "缴费", "取药"])
    print(f"识别结果: {result}")
    print(f"调用次数: {llm.get_call_count()}")
    
    print("\n=== 外部服务桩测试 ===")
    service = ExternalServiceStub()
    result = service.call_service("创建挂号", "内科", "张医生")
    print(f"服务响应: {result}")
    print(f"调用次数: {service.get_service_call_count()}")
    
    print("\n=== 用户输入桩测试 ===")
    user = UserInputStub()
    user.set_inputs(["挂号", "内科", "确认"])
    while user.has_more_inputs():
        print(f"用户输入: {user.get_next_input()}")
