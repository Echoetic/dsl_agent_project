#!/usr/bin/env python3
"""
场景模拟测试脚本
模拟用户与智能客服机器人的完整对话流程
"""

import sys
import os
import time
from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.lexer import Lexer
from src.parser import Parser
from src.interpreter import Interpreter, InterpreterState
from src.intent_recognizer import MockIntentRecognizer


class TestResult(Enum):
    PASSED = "✓ PASSED"
    FAILED = "✗ FAILED"
    ERROR = "⚠ ERROR"


@dataclass
class ConversationStep:
    """对话步骤"""
    user_input: str
    expected_keywords: List[str]  # 期望机器人回复中包含的关键词
    description: str = ""


@dataclass 
class TestScenario:
    """测试场景"""
    name: str
    script_file: str
    initial_vars: dict
    conversation: List[ConversationStep]
    description: str = ""


class ScenarioSimulator:
    """场景模拟器"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.test_results = []
        
    def log(self, message: str, indent: int = 0):
        """输出日志"""
        if self.verbose:
            prefix = "  " * indent
            print(f"{prefix}{message}")
    
    def load_script(self, script_path: str) -> Optional[Interpreter]:
        """加载DSL脚本"""
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            
            parser = Parser(tokens)
            script = parser.parse()
            
            # 使用Mock意图识别器
            intent_recognizer = MockIntentRecognizer()
            interpreter = Interpreter(script, intent_recognizer)
            
            return interpreter
        except Exception as e:
            self.log(f"加载脚本失败: {e}")
            return None
    
    def run_scenario(self, scenario: TestScenario) -> Tuple[TestResult, str]:
        """运行单个测试场景"""
        self.log(f"\n{'='*60}")
        self.log(f"场景: {scenario.name}")
        self.log(f"描述: {scenario.description}")
        self.log(f"{'='*60}")
        
        # 加载脚本
        script_path = os.path.join(project_root, 'scripts', scenario.script_file)
        interpreter = self.load_script(script_path)
        
        if not interpreter:
            return TestResult.ERROR, "脚本加载失败"
        
        # 创建会话
        session_id = f"test_{scenario.name}_{int(time.time())}"
        interpreter.create_session(session_id, scenario.initial_vars)
        
        # 开始对话
        try:
            result = interpreter.start(session_id)
            self.log(f"\n[机器人] {result.message}", indent=1)
            
            # 执行对话步骤
            for i, step in enumerate(scenario.conversation):
                self.log(f"\n--- 步骤 {i+1}: {step.description} ---")
                self.log(f"[用户] {step.user_input}", indent=1)
                
                # 处理用户输入
                result = interpreter.process_input(session_id, step.user_input)
                self.log(f"[机器人] {result.message}", indent=1)
                
                # 验证回复
                missing_keywords = []
                for keyword in step.expected_keywords:
                    if keyword not in result.message:
                        missing_keywords.append(keyword)
                
                if missing_keywords:
                    error_msg = f"步骤{i+1}验证失败，缺少关键词: {missing_keywords}"
                    self.log(f"[验证] {error_msg}", indent=1)
                    return TestResult.FAILED, error_msg
                else:
                    self.log(f"[验证] 通过 ✓", indent=1)
                
                # 检查是否结束
                if result.state == InterpreterState.FINISHED:
                    self.log(f"\n对话正常结束", indent=1)
                    break
            
            return TestResult.PASSED, "所有步骤验证通过"
            
        except Exception as e:
            return TestResult.ERROR, f"执行异常: {str(e)}"
    
    def run_all_scenarios(self, scenarios: List[TestScenario]):
        """运行所有测试场景"""
        print("\n" + "=" * 70)
        print("           智能客服机器人 - 场景模拟测试")
        print("=" * 70)
        
        passed = 0
        failed = 0
        errors = 0
        
        for scenario in scenarios:
            result, message = self.run_scenario(scenario)
            self.test_results.append({
                'scenario': scenario.name,
                'result': result,
                'message': message
            })
            
            if result == TestResult.PASSED:
                passed += 1
            elif result == TestResult.FAILED:
                failed += 1
            else:
                errors += 1
        
        # 输出汇总
        print("\n" + "=" * 70)
        print("                       测试结果汇总")
        print("=" * 70)
        
        for item in self.test_results:
            status = item['result'].value
            print(f"  {status}  {item['scenario']}")
            if item['result'] != TestResult.PASSED:
                print(f"           原因: {item['message']}")
        
        print("-" * 70)
        print(f"  总计: {len(scenarios)} 个场景")
        print(f"  通过: {passed} | 失败: {failed} | 错误: {errors}")
        print(f"  通过率: {passed/len(scenarios)*100:.1f}%")
        print("=" * 70)
        
        return passed == len(scenarios)


def get_hospital_scenarios() -> List[TestScenario]:
    """医院场景测试用例"""
    return [
        TestScenario(
            name="hospital_registration_flow",
            script_file="hospital.dsl",
            initial_vars={"name": "张先生", "phone": "13800138000"},
            description="完整挂号流程测试",
            conversation=[
                ConversationStep(
                    user_input="挂号",
                    expected_keywords=["科室"],
                    description="选择挂号服务"
                ),
                ConversationStep(
                    user_input="内科",
                    expected_keywords=["医生"],
                    description="选择内科"
                ),
                ConversationStep(
                    user_input="张医生",
                    expected_keywords=["挂号", "内科", "张医生"],
                    description="选择张医生"
                ),
                ConversationStep(
                    user_input="确认",
                    expected_keywords=["缴费", "元"],
                    description="确认挂号并缴费"
                ),
            ]
        ),
        TestScenario(
            name="hospital_payment_flow",
            script_file="hospital.dsl",
            initial_vars={"name": "李女士", "balance": "500"},
            description="缴费流程测试",
            conversation=[
                ConversationStep(
                    user_input="缴费",
                    expected_keywords=["缴费"],
                    description="选择缴费服务"
                ),
                ConversationStep(
                    user_input="H12345",
                    expected_keywords=["查询"],
                    description="输入挂号单号"
                ),
            ]
        ),
        TestScenario(
            name="hospital_silence_handling",
            script_file="hospital.dsl",
            initial_vars={"name": "王先生"},
            description="静默处理测试",
            conversation=[
                ConversationStep(
                    user_input="",
                    expected_keywords=["请问"],
                    description="用户静默，触发提示"
                ),
            ]
        ),
    ]


def get_restaurant_scenarios() -> List[TestScenario]:
    """餐厅场景测试用例"""
    return [
        TestScenario(
            name="restaurant_ordering_flow",
            script_file="restaurant.dsl",
            initial_vars={"name": "顾客A", "table": "8号桌"},
            description="完整点餐流程测试",
            conversation=[
                ConversationStep(
                    user_input="点餐",
                    expected_keywords=["菜品", "菜单"],
                    description="开始点餐"
                ),
                ConversationStep(
                    user_input="红烧肉",
                    expected_keywords=["红烧肉"],
                    description="点红烧肉"
                ),
            ]
        ),
        TestScenario(
            name="restaurant_menu_query",
            script_file="restaurant.dsl",
            initial_vars={"name": "顾客B"},
            description="菜单查询测试",
            conversation=[
                ConversationStep(
                    user_input="菜单",
                    expected_keywords=["菜单"],
                    description="查看菜单"
                ),
            ]
        ),
    ]


def get_theater_scenarios() -> List[TestScenario]:
    """剧院场景测试用例"""
    return [
        TestScenario(
            name="theater_ticket_purchase",
            script_file="theater.dsl",
            initial_vars={"name": "观众甲", "member_level": "普通会员"},
            description="购票流程测试",
            conversation=[
                ConversationStep(
                    user_input="购票",
                    expected_keywords=["演出"],
                    description="开始购票"
                ),
            ]
        ),
        TestScenario(
            name="theater_ticket_pickup",
            script_file="theater.dsl",
            initial_vars={"name": "观众乙", "order_id": "T20241225001"},
            description="取票流程测试",
            conversation=[
                ConversationStep(
                    user_input="取票",
                    expected_keywords=["取票"],
                    description="选择取票服务"
                ),
            ]
        ),
        TestScenario(
            name="theater_membership",
            script_file="theater.dsl",
            initial_vars={"name": "观众丙"},
            description="会员服务测试",
            conversation=[
                ConversationStep(
                    user_input="会员",
                    expected_keywords=["会员"],
                    description="查询会员服务"
                ),
            ]
        ),
    ]


def main():
    """主函数"""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "DSL智能Agent自动化测试" + " " * 24 + "║")
    print("║" + " " * 15 + "场景模拟测试 (Scenario Simulation)" + " " * 18 + "║")
    print("╚" + "═" * 68 + "╝")
    
    simulator = ScenarioSimulator(verbose=True)
    
    # 收集所有测试场景
    all_scenarios = []
    all_scenarios.extend(get_hospital_scenarios())
    all_scenarios.extend(get_restaurant_scenarios())
    all_scenarios.extend(get_theater_scenarios())
    
    print(f"\n共 {len(all_scenarios)} 个测试场景待执行...")
    
    # 运行测试
    success = simulator.run_all_scenarios(all_scenarios)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
