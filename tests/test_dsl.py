"""
DSL Agent 测试套件
包含词法分析、语法分析、解释器和意图识别的测试
"""

import sys
import os
import unittest
from io import StringIO

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.lexer import Lexer, Token, TokenType, LexerError
from src.parser import Parser, ParserError, parse
from src.ast_nodes import (
    Script, Step, SpeakStatement, ListenStatement, BranchStatement,
    StringLiteral, Variable, BinaryOp
)
from src.interpreter import Interpreter, InterpreterState, ExecutionContext
from src.intent_recognizer import MockIntentRecognizer, IntentResult


class TestLexer(unittest.TestCase):
    """词法分析器测试"""
    
    def test_basic_tokens(self):
        """测试基本Token识别"""
        source = 'Step welcome'
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        self.assertEqual(tokens[0].type, TokenType.STEP)
        self.assertEqual(tokens[1].type, TokenType.IDENTIFIER)
        self.assertEqual(tokens[1].value, 'welcome')
    
    def test_string_literal(self):
        """测试字符串字面量"""
        source = 'Speak "Hello World"'
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        self.assertEqual(tokens[0].type, TokenType.SPEAK)
        self.assertEqual(tokens[1].type, TokenType.STRING)
        self.assertEqual(tokens[1].value, 'Hello World')
    
    def test_number_literal(self):
        """测试数字字面量"""
        source = 'Listen 5, 30'
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        self.assertEqual(tokens[0].type, TokenType.LISTEN)
        self.assertEqual(tokens[1].type, TokenType.NUMBER)
        self.assertEqual(tokens[1].value, 5)
        self.assertEqual(tokens[2].type, TokenType.COMMA)
        self.assertEqual(tokens[3].type, TokenType.NUMBER)
        self.assertEqual(tokens[3].value, 30)
    
    def test_variable(self):
        """测试变量识别"""
        source = 'Speak $name + "您好"'
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        self.assertEqual(tokens[1].type, TokenType.VARIABLE)
        self.assertEqual(tokens[1].value, 'name')
        self.assertEqual(tokens[2].type, TokenType.PLUS)
    
    def test_operators(self):
        """测试操作符识别"""
        source = '$a == $b != $c'
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        self.assertEqual(tokens[1].type, TokenType.EQUALS)
        self.assertEqual(tokens[3].type, TokenType.NOT_EQUALS)
    
    def test_comments(self):
        """测试注释处理"""
        source = '''Step test # 这是注释
Speak "Hello"'''
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        # 注释应该被忽略
        self.assertNotIn('#', [t.value for t in tokens])
    
    def test_multiline(self):
        """测试多行处理"""
        source = '''Step welcome
    Speak "Hello"
    Exit'''
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        # 检查换行符被正确识别
        newline_count = sum(1 for t in tokens if t.type == TokenType.NEWLINE)
        self.assertGreaterEqual(newline_count, 2)


class TestParser(unittest.TestCase):
    """语法分析器测试"""
    
    def test_simple_step(self):
        """测试简单Step解析"""
        source = '''Step welcome
    Speak "Hello"
    Exit'''
        script = parse(source)
        
        self.assertEqual(script.entry_step, 'welcome')
        self.assertIn('welcome', script.steps)
        
        step = script.steps['welcome']
        self.assertEqual(len(step.statements), 2)
    
    def test_speak_expression(self):
        """测试Speak表达式解析"""
        source = '''Step test
    Speak "Hello" + $name + "!"'''
        script = parse(source)
        
        step = script.steps['test']
        stmt = step.statements[0]
        
        self.assertIsInstance(stmt, SpeakStatement)
        self.assertIsInstance(stmt.expression, BinaryOp)
    
    def test_branch_statement(self):
        """测试Branch语句解析"""
        source = '''Step welcome
    Branch "挂号", registration
    Branch "缴费", payment
    Default defaultHandler'''
        script = parse(source)
        
        step = script.steps['welcome']
        self.assertEqual(len(step.branches), 2)
        self.assertEqual(step.branches[0].intent, '挂号')
        self.assertEqual(step.branches[0].target_step, 'registration')
        self.assertEqual(step.default_handler, 'defaultHandler')
    
    def test_listen_statement(self):
        """测试Listen语句解析"""
        source = '''Step test
    Listen 5, 30'''
        script = parse(source)
        
        step = script.steps['test']
        stmt = step.statements[0]
        
        self.assertIsInstance(stmt, ListenStatement)
        self.assertEqual(stmt.begin_timeout.value, 5)
        self.assertEqual(stmt.end_timeout.value, 30)
    
    def test_multiple_steps(self):
        """测试多个Step解析"""
        source = '''Step welcome
    Speak "Hello"
    
Step goodbye
    Speak "Bye"
    Exit'''
        script = parse(source)
        
        self.assertEqual(len(script.steps), 2)
        self.assertIn('welcome', script.steps)
        self.assertIn('goodbye', script.steps)


class TestInterpreter(unittest.TestCase):
    """解释器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.simple_script = '''Step welcome
    Speak "欢迎您，" + $name + "！"
    Listen 5, 30
    Branch "帮助", help
    Branch "退出", goodbye
    Default defaultHandler

Step help
    Speak "这是帮助信息"
    Exit

Step goodbye
    Speak "再见！"
    Exit

Step defaultHandler
    Speak "没有理解您的意思"
    Exit'''
    
    def test_start_session(self):
        """测试启动会话"""
        script = parse(self.simple_script)
        interpreter = Interpreter(script)
        
        context = interpreter.create_session('test_session', {'name': '张三'})
        output = interpreter.start('test_session')
        
        self.assertEqual(output.state, InterpreterState.WAITING_INPUT)
        self.assertIn('欢迎您，张三', output.message)
    
    def test_intent_matching(self):
        """测试意图匹配"""
        script = parse(self.simple_script)
        mock_recognizer = MockIntentRecognizer()
        interpreter = Interpreter(script, mock_recognizer)
        
        context = interpreter.create_session('test_session', {'name': '张三'})
        interpreter.start('test_session')
        
        # 处理用户输入
        output = interpreter.process_input('test_session', '帮助')
        
        self.assertIn('帮助信息', output.message)
    
    def test_variable_substitution(self):
        """测试变量替换"""
        script = parse(self.simple_script)
        interpreter = Interpreter(script)
        
        context = interpreter.create_session('test_session', {'name': '李四'})
        output = interpreter.start('test_session')
        
        self.assertIn('李四', output.message)
    
    def test_exit_state(self):
        """测试退出状态"""
        script = parse(self.simple_script)
        mock_recognizer = MockIntentRecognizer()
        interpreter = Interpreter(script, mock_recognizer)
        
        context = interpreter.create_session('test_session', {'name': '用户'})
        interpreter.start('test_session')
        output = interpreter.process_input('test_session', '退出')
        
        self.assertEqual(output.state, InterpreterState.FINISHED)


class TestMockIntentRecognizer(unittest.TestCase):
    """模拟意图识别器测试"""
    
    def test_keyword_matching(self):
        """测试关键词匹配"""
        recognizer = MockIntentRecognizer()
        result = recognizer.recognize_intent(
            '我想挂号',
            ['挂号', '缴费', '取药']
        )
        
        self.assertEqual(result.intent, '挂号')
        self.assertGreater(result.confidence, 0)
    
    def test_silence_detection(self):
        """测试静默检测"""
        recognizer = MockIntentRecognizer()
        result = recognizer.recognize_intent(
            '',
            ['挂号', '缴费']
        )
        
        self.assertTrue(result.is_silence)
        self.assertEqual(result.intent, '')
    
    def test_preset_response(self):
        """测试预设响应"""
        recognizer = MockIntentRecognizer()
        recognizer.set_response('测试输入', '测试意图', 0.95)
        
        result = recognizer.recognize_intent(
            '测试输入',
            ['测试意图', '其他意图']
        )
        
        self.assertEqual(result.intent, '测试意图')
        self.assertEqual(result.confidence, 0.95)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_hospital_script(self):
        """测试医院脚本"""
        script_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 'scripts', 'hospital.dsl'
        )
        
        if os.path.exists(script_path):
            with open(script_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            script = parse(source)
            
            self.assertIsNotNone(script.entry_step)
            self.assertGreater(len(script.steps), 0)
    
    def test_restaurant_script(self):
        """测试餐厅脚本"""
        script_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 'scripts', 'restaurant.dsl'
        )
        
        if os.path.exists(script_path):
            with open(script_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            script = parse(source)
            
            self.assertIsNotNone(script.entry_step)
            self.assertGreater(len(script.steps), 0)
    
    def test_theater_script(self):
        """测试剧院脚本"""
        script_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 'scripts', 'theater.dsl'
        )
        
        if os.path.exists(script_path):
            with open(script_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            script = parse(source)
            
            self.assertIsNotNone(script.entry_step)
            self.assertGreater(len(script.steps), 0)


class TestExpressionEvaluation(unittest.TestCase):
    """表达式计算测试"""
    
    def test_string_concatenation(self):
        """测试字符串拼接"""
        source = '''Step test
    Set $result = "Hello" + " " + "World"
    Speak $result
    Exit'''
        
        script = parse(source)
        interpreter = Interpreter(script)
        context = interpreter.create_session('test')
        output = interpreter.start('test')
        
        self.assertIn('Hello World', output.message)
    
    def test_arithmetic(self):
        """测试算术运算"""
        source = '''Step test
    Set $a = 10
    Set $b = 5
    Set $sum = $a + $b
    Speak "结果是" + $sum
    Exit'''
        
        script = parse(source)
        interpreter = Interpreter(script)
        context = interpreter.create_session('test')
        output = interpreter.start('test')
        
        self.assertIn('15', output.message)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestLexer))
    suite.addTests(loader.loadTestsFromTestCase(TestParser))
    suite.addTests(loader.loadTestsFromTestCase(TestInterpreter))
    suite.addTests(loader.loadTestsFromTestCase(TestMockIntentRecognizer))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestExpressionEvaluation))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
