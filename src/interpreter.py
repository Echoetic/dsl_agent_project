"""
DSL脚本解释器
负责执行解析后的AST
"""

import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from .ast_nodes import (
    Script, Step, Statement, Expression,
    SpeakStatement, ListenStatement, BranchStatement, BranchCase,
    SilenceStatement, DefaultStatement, ExitStatement, GotoStatement,
    SetStatement, IfStatement, WhileStatement, CallStatement,
    StringLiteral, NumberLiteral, Variable, BinaryOp, UnaryOp, FunctionCall
)
from .intent_recognizer import GeminiIntentRecognizer, IntentResult, create_intent_recognizer


class InterpreterState(Enum):
    """解释器状态"""
    IDLE = auto()          # 空闲
    RUNNING = auto()       # 运行中
    WAITING_INPUT = auto() # 等待输入
    FINISHED = auto()      # 已结束
    ERROR = auto()         # 错误


@dataclass
class ExecutionContext:
    """执行上下文 - 每个对话会话一个"""
    variables: Dict[str, Any] = field(default_factory=dict)
    current_step: Optional[str] = None
    state: InterpreterState = InterpreterState.IDLE
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    last_speak_output: str = ""
    available_intents: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    session_id: str = ""
    
    def set_variable(self, name: str, value: Any):
        """设置变量"""
        self.variables[name] = value
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量"""
        return self.variables.get(name, default)
    
    def add_to_history(self, role: str, content: str):
        """添加到对话历史"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })


@dataclass
class InterpreterOutput:
    """解释器输出"""
    message: str                          # 输出消息
    state: InterpreterState               # 当前状态
    waiting_for_input: bool = False       # 是否等待输入
    available_intents: List[str] = field(default_factory=list)  # 可用意图
    context: Dict[str, Any] = field(default_factory=dict)       # 上下文数据


class ExternalServiceHandler:
    """外部服务处理器基类"""
    
    def handle(self, service_name: str, arguments: List[Any], context: ExecutionContext) -> Any:
        """处理服务调用"""
        raise NotImplementedError


class DefaultServiceHandler(ExternalServiceHandler):
    """默认外部服务处理器"""
    
    def __init__(self):
        self.services: Dict[str, Callable] = {}
        self._register_default_services()
    
    def _register_default_services(self):
        """注册默认服务"""
        # 医院挂号相关
        self.services["查询科室"] = lambda *args: ["内科", "外科", "儿科", "妇产科", "眼科", "口腔科"]
        self.services["查询医生"] = lambda dept: f"{dept}专家：张医生、李医生、王医生"
        self.services["创建挂号"] = lambda dept, doc: {"挂号单号": "H" + str(int(time.time()) % 10000), "科室": dept, "医生": doc}
        self.services["查询费用"] = lambda order_id: {"挂号费": 50, "检查费": 200, "药费": 150}
        self.services["处理缴费"] = lambda order_id, amount: {"状态": "成功", "交易号": "T" + str(int(time.time()) % 10000)}
        self.services["获取取药信息"] = lambda order_id: {"窗口": "3号窗口", "等待人数": 5}
        
        # 餐厅点餐相关
        self.services["获取菜单"] = lambda: [
            {"名称": "红烧肉", "价格": 48},
            {"名称": "清蒸鱼", "价格": 68},
            {"名称": "宫保鸡丁", "价格": 38},
            {"名称": "米饭", "价格": 3}
        ]
        self.services["添加菜品"] = lambda name, qty: {"菜品": name, "数量": qty, "状态": "已添加"}
        self.services["计算总价"] = lambda items: sum(item.get("价格", 0) * item.get("数量", 1) for item in items)
        self.services["确认订单"] = lambda items: {"订单号": "D" + str(int(time.time()) % 10000), "状态": "已确认"}
        self.services["处理支付"] = lambda order_id, method: {"状态": "支付成功", "支付方式": method}
        
        # 剧院售票相关
        self.services["查询演出"] = lambda: [
            {"名称": "天鹅湖", "时间": "周六 19:00", "价格": 280},
            {"名称": "茶馆", "时间": "周日 14:00", "价格": 180},
            {"名称": "猫", "时间": "周日 19:00", "价格": 380}
        ]
        self.services["查询座位"] = lambda show: ["A区", "B区", "C区"]
        self.services["购票"] = lambda show, seat, qty: {"票号": "P" + str(int(time.time()) % 10000), "演出": show, "座位": seat, "数量": qty}
        self.services["支付票款"] = lambda ticket_id, amount: {"状态": "支付成功", "票号": ticket_id}
        self.services["获取取票码"] = lambda ticket_id: {"取票码": str(int(time.time()) % 1000000).zfill(6), "取票点": "自助取票机"}
    
    def register_service(self, name: str, handler: Callable):
        """注册服务"""
        self.services[name] = handler
    
    def handle(self, service_name: str, arguments: List[Any], context: ExecutionContext) -> Any:
        """处理服务调用"""
        if service_name in self.services:
            try:
                return self.services[service_name](*arguments)
            except Exception as e:
                return {"error": str(e)}
        return {"error": f"未知服务: {service_name}"}


class Interpreter:
    """DSL解释器"""
    
    def __init__(self, 
                 script: Script, 
                 intent_recognizer = None,
                 service_handler: Optional[ExternalServiceHandler] = None):
        self.script = script
        self.intent_recognizer = intent_recognizer
        self.service_handler = service_handler or DefaultServiceHandler()
        self.contexts: Dict[str, ExecutionContext] = {}
    
    def create_session(self, session_id: str, initial_variables: Optional[Dict[str, Any]] = None) -> ExecutionContext:
        """创建新的执行会话"""
        context = ExecutionContext(session_id=session_id)
        if initial_variables:
            context.variables.update(initial_variables)
        
        entry_step = self.script.get_entry_step()
        if entry_step:
            context.current_step = entry_step.name
        context.state = InterpreterState.IDLE
        
        self.contexts[session_id] = context
        return context
    
    def get_session(self, session_id: str) -> Optional[ExecutionContext]:
        """获取会话上下文"""
        return self.contexts.get(session_id)
    
    def remove_session(self, session_id: str):
        """移除会话"""
        if session_id in self.contexts:
            del self.contexts[session_id]
    
    def start(self, session_id: str) -> InterpreterOutput:
        """启动解释器"""
        context = self.get_session(session_id)
        if not context:
            return InterpreterOutput(
                message="会话不存在",
                state=InterpreterState.ERROR
            )
        
        context.state = InterpreterState.RUNNING
        return self._execute_current_step(context)
    
    def process_input(self, session_id: str, user_input: str) -> InterpreterOutput:
        """处理用户输入"""
        context = self.get_session(session_id)
        if not context:
            return InterpreterOutput(
                message="会话不存在",
                state=InterpreterState.ERROR
            )
        
        if context.state != InterpreterState.WAITING_INPUT:
            return InterpreterOutput(
                message="当前不在等待输入状态",
                state=context.state
            )
        
        # 记录用户输入
        context.add_to_history("user", user_input)
        
        # 进行意图识别
        intent_result = self._recognize_intent(user_input, context.available_intents, context)
        
        # 根据意图决定下一步
        current_step = self.script.get_step(context.current_step)
        if not current_step:
            return InterpreterOutput(
                message="步骤不存在",
                state=InterpreterState.ERROR
            )
        
        next_step_name = self._determine_next_step(intent_result, current_step, context)
        
        if next_step_name:
            context.current_step = next_step_name
            context.state = InterpreterState.RUNNING
            return self._execute_current_step(context)
        else:
            # 没有匹配的分支，检查默认处理
            if current_step.default_handler:
                context.current_step = current_step.default_handler
                context.state = InterpreterState.RUNNING
                return self._execute_current_step(context)
            else:
                return InterpreterOutput(
                    message="抱歉，我没有理解您的意思。请重新输入。",
                    state=InterpreterState.WAITING_INPUT,
                    waiting_for_input=True,
                    available_intents=context.available_intents
                )
    
    def _execute_current_step(self, context: ExecutionContext) -> InterpreterOutput:
        """执行当前步骤"""
        step = self.script.get_step(context.current_step)
        if not step:
            context.state = InterpreterState.ERROR
            context.error_message = f"步骤不存在: {context.current_step}"
            return InterpreterOutput(
                message=f"错误: 步骤 '{context.current_step}' 不存在",
                state=InterpreterState.ERROR
            )
        
        output_messages = []
        
        for stmt in step.statements:
            result = self._execute_statement(stmt, context)
            
            if isinstance(result, InterpreterOutput):
                return result
            
            if result:
                output_messages.append(str(result))
        
        # 收集可用意图
        context.available_intents = [branch.intent for branch in step.branches]
        
        # 检查是否是退出步骤
        if step.is_exit:
            context.state = InterpreterState.FINISHED
            message = "\n".join(output_messages) if output_messages else "对话结束"
            context.add_to_history("assistant", message)
            return InterpreterOutput(
                message=message,
                state=InterpreterState.FINISHED
            )
        
        # 检查是否需要等待输入
        has_listen = any(isinstance(s, ListenStatement) for s in step.statements)
        has_branches = bool(step.branches) or step.silence_handler or step.default_handler
        
        if has_listen or has_branches:
            context.state = InterpreterState.WAITING_INPUT
            message = "\n".join(output_messages) if output_messages else ""
            if message:
                context.add_to_history("assistant", message)
            return InterpreterOutput(
                message=message,
                state=InterpreterState.WAITING_INPUT,
                waiting_for_input=True,
                available_intents=context.available_intents
            )
        
        # 没有分支，继续执行
        message = "\n".join(output_messages) if output_messages else ""
        context.state = InterpreterState.FINISHED
        return InterpreterOutput(
            message=message,
            state=InterpreterState.FINISHED
        )
    
    def _execute_statement(self, stmt: Statement, context: ExecutionContext) -> Any:
        """执行单个语句"""
        if isinstance(stmt, SpeakStatement):
            return self._execute_speak(stmt, context)
        elif isinstance(stmt, ListenStatement):
            return self._execute_listen(stmt, context)
        elif isinstance(stmt, SetStatement):
            return self._execute_set(stmt, context)
        elif isinstance(stmt, GotoStatement):
            return self._execute_goto(stmt, context)
        elif isinstance(stmt, IfStatement):
            return self._execute_if(stmt, context)
        elif isinstance(stmt, WhileStatement):
            return self._execute_while(stmt, context)
        elif isinstance(stmt, CallStatement):
            return self._execute_call(stmt, context)
        elif isinstance(stmt, ExitStatement):
            return None
        return None
    
    def _execute_speak(self, stmt: SpeakStatement, context: ExecutionContext) -> str:
        """执行Speak语句"""
        message = self._evaluate_expression(stmt.expression, context)
        context.last_speak_output = str(message)
        return str(message)
    
    def _execute_listen(self, stmt: ListenStatement, context: ExecutionContext):
        """执行Listen语句"""
        # Listen主要是标记需要等待输入，实际等待在step级别处理
        return None
    
    def _execute_set(self, stmt: SetStatement, context: ExecutionContext):
        """执行Set语句"""
        value = self._evaluate_expression(stmt.expression, context)
        context.set_variable(stmt.variable, value)
        return None
    
    def _execute_goto(self, stmt: GotoStatement, context: ExecutionContext) -> InterpreterOutput:
        """执行Goto语句"""
        context.current_step = stmt.target_step
        return self._execute_current_step(context)
    
    def _execute_if(self, stmt: IfStatement, context: ExecutionContext):
        """执行If语句"""
        condition_result = self._evaluate_expression(stmt.condition, context)
        
        if condition_result:
            for s in stmt.then_block:
                result = self._execute_statement(s, context)
                if isinstance(result, InterpreterOutput):
                    return result
        elif stmt.else_block:
            for s in stmt.else_block:
                result = self._execute_statement(s, context)
                if isinstance(result, InterpreterOutput):
                    return result
        return None
    
    def _execute_while(self, stmt: WhileStatement, context: ExecutionContext):
        """执行While语句"""
        max_iterations = 1000  # 防止无限循环
        iterations = 0
        
        while self._evaluate_expression(stmt.condition, context):
            iterations += 1
            if iterations > max_iterations:
                raise RuntimeError("循环超过最大迭代次数")
            
            for s in stmt.body:
                result = self._execute_statement(s, context)
                if isinstance(result, InterpreterOutput):
                    return result
        return None
    
    def _execute_call(self, stmt: CallStatement, context: ExecutionContext):
        """执行Call语句"""
        args = [self._evaluate_expression(arg, context) for arg in stmt.arguments]
        result = self.service_handler.handle(stmt.service_name, args, context)
        
        if stmt.result_var:
            context.set_variable(stmt.result_var, result)
        
        return None
    
    def _evaluate_expression(self, expr: Expression, context: ExecutionContext) -> Any:
        """计算表达式的值"""
        if isinstance(expr, StringLiteral):
            return expr.value
        
        elif isinstance(expr, NumberLiteral):
            return expr.value
        
        elif isinstance(expr, Variable):
            return context.get_variable(expr.name, "")
        
        elif isinstance(expr, BinaryOp):
            left = self._evaluate_expression(expr.left, context)
            right = self._evaluate_expression(expr.right, context)
            
            if expr.operator == '+':
                # 字符串拼接或数字加法
                if isinstance(left, str) or isinstance(right, str):
                    return str(left) + str(right)
                return left + right
            elif expr.operator == '-':
                return left - right
            elif expr.operator == '*':
                return left * right
            elif expr.operator == '/':
                return left / right if right != 0 else 0
            elif expr.operator == '==':
                return left == right
            elif expr.operator == '!=':
                return left != right
            elif expr.operator == '>':
                return left > right
            elif expr.operator == '<':
                return left < right
            elif expr.operator == '>=':
                return left >= right
            elif expr.operator == '<=':
                return left <= right
            elif expr.operator == 'and':
                return bool(left) and bool(right)
            elif expr.operator == 'or':
                return bool(left) or bool(right)
        
        elif isinstance(expr, UnaryOp):
            operand = self._evaluate_expression(expr.operand, context)
            if expr.operator == '-':
                return -operand
            elif expr.operator == 'not':
                return not bool(operand)
        
        elif isinstance(expr, FunctionCall):
            # 内置函数
            args = [self._evaluate_expression(arg, context) for arg in expr.arguments]
            return self._call_builtin_function(expr.name, args, context)
        
        return None
    
    def _call_builtin_function(self, name: str, args: List[Any], context: ExecutionContext) -> Any:
        """调用内置函数"""
        if name == "len":
            return len(args[0]) if args else 0
        elif name == "str":
            return str(args[0]) if args else ""
        elif name == "int":
            return int(args[0]) if args else 0
        elif name == "float":
            return float(args[0]) if args else 0.0
        return None
    
    def _recognize_intent(self, 
                         user_input: str, 
                         available_intents: List[str],
                         context: ExecutionContext) -> IntentResult:
        """识别用户意图"""
        if not user_input.strip():
            return IntentResult(
                intent="",
                confidence=0.0,
                entities={},
                raw_response="",
                is_silence=True
            )
        
        if self.intent_recognizer:
            return self.intent_recognizer.recognize_intent(
                user_input, 
                available_intents,
                {"variables": context.variables, "history": context.conversation_history[-5:]}
            )
        
        # 如果没有意图识别器，使用简单的关键词匹配
        user_input_lower = user_input.lower()
        for intent in available_intents:
            if intent.lower() in user_input_lower:
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
    
    def _determine_next_step(self, 
                            intent_result: IntentResult, 
                            current_step: Step,
                            context: ExecutionContext) -> Optional[str]:
        """根据意图确定下一步"""
        # 检查静默
        if intent_result.is_silence and current_step.silence_handler:
            return current_step.silence_handler
        
        # 检查意图分支
        if intent_result.intent:
            for branch in current_step.branches:
                if branch.intent == intent_result.intent:
                    # 保存识别的实体
                    if intent_result.entities:
                        for key, value in intent_result.entities.items():
                            context.set_variable(key, value)
                    return branch.target_step
        
        # 没有匹配，返回默认处理
        return current_step.default_handler
