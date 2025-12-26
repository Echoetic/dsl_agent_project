#!/usr/bin/env python3
"""
自动化交互测试脚本
包含：压力测试、边界测试、异常输入测试、并发会话测试
"""

import sys
import os
import time
import random
import string
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.lexer import Lexer
from src.parser import Parser
from src.interpreter import Interpreter, InterpreterState
from src.intent_recognizer import MockIntentRecognizer


@dataclass
class TestMetrics:
    """测试指标"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    
    @property
    def avg_response_time(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_time / self.total_requests
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests * 100


class AutomatedTester:
    """自动化测试器"""
    
    def __init__(self):
        self.scripts_dir = os.path.join(project_root, 'scripts')
        self.interpreters: Dict[str, Interpreter] = {}
        self._load_all_scripts()
    
    def _load_all_scripts(self):
        """加载所有脚本"""
        scripts = ['hospital.dsl', 'restaurant.dsl', 'theater.dsl']
        for script_name in scripts:
            script_path = os.path.join(self.scripts_dir, script_name)
            if os.path.exists(script_path):
                try:
                    with open(script_path, 'r', encoding='utf-8') as f:
                        source = f.read()
                    lexer = Lexer(source)
                    tokens = lexer.tokenize()
                    parser = Parser(tokens)
                    script = parser.parse()
                    intent_recognizer = MockIntentRecognizer()
                    self.interpreters[script_name] = Interpreter(script, intent_recognizer)
                    print(f"  ✓ 加载脚本: {script_name}")
                except Exception as e:
                    print(f"  ✗ 加载失败: {script_name} - {e}")
    
    def get_interpreter(self, script_name: str) -> Interpreter:
        """获取解释器实例"""
        return self.interpreters.get(script_name)


class BoundaryTester:
    """边界测试"""
    
    def __init__(self, tester: AutomatedTester):
        self.tester = tester
        self.results = []
    
    def test_empty_input(self) -> Tuple[bool, str]:
        """测试空输入"""
        interpreter = self.tester.get_interpreter('hospital.dsl')
        if not interpreter:
            return False, "解释器未加载"
        
        session_id = f"boundary_empty_{int(time.time())}"
        interpreter.create_session(session_id, {"name": "测试用户"})
        interpreter.start(session_id)
        
        try:
            result = interpreter.process_input(session_id, "")
            # 空输入应该触发静默处理
            return True, f"空输入处理正常: {result.message[:50]}..."
        except Exception as e:
            return False, f"空输入处理异常: {e}"
    
    def test_very_long_input(self) -> Tuple[bool, str]:
        """测试超长输入"""
        interpreter = self.tester.get_interpreter('hospital.dsl')
        if not interpreter:
            return False, "解释器未加载"
        
        session_id = f"boundary_long_{int(time.time())}"
        interpreter.create_session(session_id, {"name": "测试用户"})
        interpreter.start(session_id)
        
        # 生成超长输入（1000个字符）
        long_input = "我想" + "挂号" * 200
        
        try:
            result = interpreter.process_input(session_id, long_input)
            return True, f"超长输入处理正常: {result.message[:50]}..."
        except Exception as e:
            return False, f"超长输入处理异常: {e}"
    
    def test_special_characters(self) -> Tuple[bool, str]:
        """测试特殊字符输入"""
        interpreter = self.tester.get_interpreter('hospital.dsl')
        if not interpreter:
            return False, "解释器未加载"
        
        session_id = f"boundary_special_{int(time.time())}"
        interpreter.create_session(session_id, {"name": "测试用户"})
        interpreter.start(session_id)
        
        special_inputs = [
            "!@#$%^&*()",
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "🎉🎊🎁",
            "\n\r\t",
            "null",
            "undefined",
        ]
        
        for special_input in special_inputs:
            try:
                result = interpreter.process_input(session_id, special_input)
            except Exception as e:
                return False, f"特殊字符'{special_input}'处理异常: {e}"
        
        return True, "所有特殊字符输入处理正常"
    
    def test_unicode_input(self) -> Tuple[bool, str]:
        """测试Unicode输入"""
        interpreter = self.tester.get_interpreter('restaurant.dsl')
        if not interpreter:
            return False, "解释器未加载"
        
        session_id = f"boundary_unicode_{int(time.time())}"
        interpreter.create_session(session_id, {"name": "テストユーザー"})
        interpreter.start(session_id)
        
        unicode_inputs = [
            "日本語テスト",
            "한국어 테스트",
            "العربية",
            "עברית",
            "Ελληνικά",
        ]
        
        for unicode_input in unicode_inputs:
            try:
                result = interpreter.process_input(session_id, unicode_input)
            except Exception as e:
                return False, f"Unicode'{unicode_input}'处理异常: {e}"
        
        return True, "所有Unicode输入处理正常"
    
    def test_numeric_input(self) -> Tuple[bool, str]:
        """测试纯数字输入"""
        interpreter = self.tester.get_interpreter('hospital.dsl')
        if not interpreter:
            return False, "解释器未加载"
        
        session_id = f"boundary_numeric_{int(time.time())}"
        interpreter.create_session(session_id, {"name": "测试用户"})
        interpreter.start(session_id)
        
        numeric_inputs = ["123", "0", "-1", "99999999999", "3.14159"]
        
        for num_input in numeric_inputs:
            try:
                result = interpreter.process_input(session_id, num_input)
            except Exception as e:
                return False, f"数字'{num_input}'处理异常: {e}"
        
        return True, "所有数字输入处理正常"
    
    def run_all_tests(self) -> List[Dict[str, Any]]:
        """运行所有边界测试"""
        tests = [
            ("空输入测试", self.test_empty_input),
            ("超长输入测试", self.test_very_long_input),
            ("特殊字符测试", self.test_special_characters),
            ("Unicode测试", self.test_unicode_input),
            ("纯数字测试", self.test_numeric_input),
        ]
        
        results = []
        for name, test_func in tests:
            success, message = test_func()
            results.append({
                'name': name,
                'success': success,
                'message': message
            })
        
        return results


class StressTester:
    """压力测试"""
    
    def __init__(self, tester: AutomatedTester):
        self.tester = tester
        self.metrics = TestMetrics()
    
    def _single_conversation(self, thread_id: int) -> Tuple[bool, float, str]:
        """执行单次对话"""
        scripts = ['hospital.dsl', 'restaurant.dsl', 'theater.dsl']
        script_name = random.choice(scripts)
        interpreter = self.tester.get_interpreter(script_name)
        
        if not interpreter:
            return False, 0.0, "解释器未加载"
        
        session_id = f"stress_{thread_id}_{int(time.time()*1000)}"
        
        # 随机用户输入
        inputs = ["挂号", "点餐", "购票", "查询", "确认", "取消", "帮助", ""]
        
        start_time = time.time()
        
        try:
            interpreter.create_session(session_id, {"name": f"用户{thread_id}"})
            interpreter.start(session_id)
            
            # 执行3-5轮对话
            rounds = random.randint(3, 5)
            for _ in range(rounds):
                user_input = random.choice(inputs)
                result = interpreter.process_input(session_id, user_input)
                
                if result.state == InterpreterState.FINISHED:
                    break
            
            elapsed = time.time() - start_time
            return True, elapsed, "成功"
            
        except Exception as e:
            elapsed = time.time() - start_time
            return False, elapsed, str(e)
    
    def run_stress_test(self, num_requests: int = 100, max_workers: int = 10) -> TestMetrics:
        """运行压力测试"""
        self.metrics = TestMetrics()
        
        print(f"\n  开始压力测试: {num_requests} 次请求, {max_workers} 并发线程")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self._single_conversation, i) 
                for i in range(num_requests)
            ]
            
            for future in as_completed(futures):
                success, elapsed, message = future.result()
                
                self.metrics.total_requests += 1
                self.metrics.total_time += elapsed
                
                if success:
                    self.metrics.successful_requests += 1
                else:
                    self.metrics.failed_requests += 1
                    self.metrics.errors.append(message)
                
                self.metrics.min_response_time = min(self.metrics.min_response_time, elapsed)
                self.metrics.max_response_time = max(self.metrics.max_response_time, elapsed)
                
                # 进度显示
                progress = self.metrics.total_requests / num_requests * 100
                if self.metrics.total_requests % 10 == 0:
                    print(f"  进度: {progress:.0f}% ({self.metrics.total_requests}/{num_requests})")
        
        return self.metrics


class ConcurrencyTester:
    """并发会话测试"""
    
    def __init__(self, tester: AutomatedTester):
        self.tester = tester
        self.active_sessions = {}
        self.lock = threading.Lock()
    
    def _run_session(self, session_num: int) -> Dict[str, Any]:
        """运行单个会话"""
        script_name = 'hospital.dsl'
        interpreter = self.tester.get_interpreter(script_name)
        
        session_id = f"concurrent_{session_num}_{int(time.time()*1000)}"
        
        result = {
            'session_id': session_id,
            'session_num': session_num,
            'success': False,
            'rounds': 0,
            'messages': []
        }
        
        try:
            interpreter.create_session(session_id, {"name": f"并发用户{session_num}"})
            
            with self.lock:
                self.active_sessions[session_id] = True
            
            # 开始对话
            output = interpreter.start(session_id)
            result['messages'].append(output.message[:50])
            
            # 模拟多轮对话
            conversation = ["挂号", "内科", "张医生", "确认"]
            for user_input in conversation:
                # 随机延迟，模拟真实用户
                time.sleep(random.uniform(0.01, 0.05))
                
                output = interpreter.process_input(session_id, user_input)
                result['messages'].append(output.message[:50])
                result['rounds'] += 1
                
                if output.state == InterpreterState.FINISHED:
                    break
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
        
        finally:
            with self.lock:
                if session_id in self.active_sessions:
                    del self.active_sessions[session_id]
        
        return result
    
    def run_concurrency_test(self, num_sessions: int = 20) -> List[Dict[str, Any]]:
        """运行并发测试"""
        print(f"\n  开始并发测试: {num_sessions} 个并发会话")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=num_sessions) as executor:
            futures = [
                executor.submit(self._run_session, i) 
                for i in range(num_sessions)
            ]
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                
                status = "✓" if result['success'] else "✗"
                print(f"  {status} 会话 {result['session_num']}: {result['rounds']} 轮对话")
        
        return results


class RandomInputTester:
    """随机输入测试"""
    
    def __init__(self, tester: AutomatedTester):
        self.tester = tester
    
    def _generate_random_input(self) -> str:
        """生成随机输入"""
        input_types = [
            # 随机中文词语
            lambda: random.choice(["你好", "帮助", "退出", "什么", "怎么", "为什么", "在哪", "多少钱"]),
            # 随机英文
            lambda: ''.join(random.choices(string.ascii_letters, k=random.randint(3, 10))),
            # 随机数字
            lambda: str(random.randint(0, 9999)),
            # 混合输入
            lambda: f"我要{random.choice(['挂号', '点餐', '买票'])}{random.randint(1, 10)}个",
            # 空白
            lambda: " " * random.randint(0, 5),
            # 重复字符
            lambda: random.choice(["哈", "嗯", "啊", "呃"]) * random.randint(1, 10),
        ]
        
        return random.choice(input_types)()
    
    def run_random_test(self, num_iterations: int = 50) -> Dict[str, Any]:
        """运行随机输入测试"""
        print(f"\n  开始随机输入测试: {num_iterations} 次迭代")
        
        results = {
            'total': num_iterations,
            'success': 0,
            'errors': [],
            'crash': False
        }
        
        scripts = ['hospital.dsl', 'restaurant.dsl', 'theater.dsl']
        
        for i in range(num_iterations):
            script_name = random.choice(scripts)
            interpreter = self.tester.get_interpreter(script_name)
            
            session_id = f"random_{i}_{int(time.time()*1000)}"
            
            try:
                interpreter.create_session(session_id, {"name": "随机测试"})
                interpreter.start(session_id)
                
                # 执行5-10轮随机输入
                rounds = random.randint(5, 10)
                for _ in range(rounds):
                    random_input = self._generate_random_input()
                    result = interpreter.process_input(session_id, random_input)
                    
                    if result.state == InterpreterState.FINISHED:
                        break
                
                results['success'] += 1
                
            except Exception as e:
                results['errors'].append({
                    'iteration': i,
                    'script': script_name,
                    'error': str(e)
                })
            
            # 进度
            if (i + 1) % 10 == 0:
                print(f"  进度: {(i+1)/num_iterations*100:.0f}%")
        
        return results


def print_section(title: str):
    """打印分节标题"""
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print(f"{'─' * 70}")


def main():
    """主函数"""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "DSL智能Agent自动化测试" + " " * 20 + "║")
    print("║" + " " * 12 + "压力测试 / 边界测试 / 并发测试 / 随机测试" + " " * 11 + "║")
    print("╚" + "═" * 68 + "╝")
    
    print(f"\n测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 初始化测试器
    print_section("初始化")
    tester = AutomatedTester()
    
    all_passed = True
    
    # 1. 边界测试
    print_section("1. 边界测试 (Boundary Testing)")
    boundary_tester = BoundaryTester(tester)
    boundary_results = boundary_tester.run_all_tests()
    
    for result in boundary_results:
        status = "✓" if result['success'] else "✗"
        print(f"  {status} {result['name']}: {result['message']}")
        if not result['success']:
            all_passed = False
    
    # 2. 压力测试
    print_section("2. 压力测试 (Stress Testing)")
    stress_tester = StressTester(tester)
    metrics = stress_tester.run_stress_test(num_requests=50, max_workers=5)
    
    print(f"\n  测试结果:")
    print(f"    总请求数: {metrics.total_requests}")
    print(f"    成功: {metrics.successful_requests}")
    print(f"    失败: {metrics.failed_requests}")
    print(f"    成功率: {metrics.success_rate:.1f}%")
    print(f"    平均响应时间: {metrics.avg_response_time*1000:.2f}ms")
    print(f"    最小响应时间: {metrics.min_response_time*1000:.2f}ms")
    print(f"    最大响应时间: {metrics.max_response_time*1000:.2f}ms")
    
    if metrics.success_rate < 95:
        all_passed = False
    
    # 3. 并发测试
    print_section("3. 并发测试 (Concurrency Testing)")
    concurrency_tester = ConcurrencyTester(tester)
    concurrent_results = concurrency_tester.run_concurrency_test(num_sessions=10)
    
    success_count = sum(1 for r in concurrent_results if r['success'])
    print(f"\n  并发会话成功率: {success_count}/{len(concurrent_results)}")
    
    if success_count < len(concurrent_results):
        all_passed = False
    
    # 4. 随机输入测试
    print_section("4. 随机输入测试 (Random Input Testing)")
    random_tester = RandomInputTester(tester)
    random_results = random_tester.run_random_test(num_iterations=30)
    
    print(f"\n  测试结果:")
    print(f"    总迭代数: {random_results['total']}")
    print(f"    成功: {random_results['success']}")
    print(f"    错误数: {len(random_results['errors'])}")
    print(f"    系统崩溃: {'否' if not random_results['crash'] else '是'}")
    
    if random_results['errors']:
        print(f"    错误详情:")
        for err in random_results['errors'][:3]:
            print(f"      - 迭代{err['iteration']}: {err['error'][:50]}")
    
    # 总结
    print("\n" + "═" * 70)
    print("                         测试总结")
    print("═" * 70)
    
    print(f"\n  测试结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if all_passed:
        print(f"\n  ✓ 所有测试通过!")
        return 0
    else:
        print(f"\n  ✗ 部分测试未通过，请检查上述结果")
        return 1


if __name__ == '__main__':
    sys.exit(main())
