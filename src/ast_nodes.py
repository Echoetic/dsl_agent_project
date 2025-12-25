"""
AST (抽象语法树) 节点定义
定义DSL的语法树结构
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from abc import ABC, abstractmethod


class ASTNode(ABC):
    """AST节点基类"""
    pass


# ============ 表达式节点 ============

class Expression(ASTNode):
    """表达式基类"""
    pass


@dataclass
class StringLiteral(Expression):
    """字符串字面量"""
    value: str


@dataclass
class NumberLiteral(Expression):
    """数字字面量"""
    value: Union[int, float]


@dataclass
class Variable(Expression):
    """变量引用"""
    name: str


@dataclass
class BinaryOp(Expression):
    """二元操作"""
    left: Expression
    operator: str
    right: Expression


@dataclass
class UnaryOp(Expression):
    """一元操作"""
    operator: str
    operand: Expression


@dataclass
class FunctionCall(Expression):
    """函数调用表达式"""
    name: str
    arguments: List[Expression] = field(default_factory=list)


# ============ 语句节点 ============

class Statement(ASTNode):
    """语句基类"""
    pass


@dataclass
class SpeakStatement(Statement):
    """Speak语句 - 输出文本"""
    expression: Expression


@dataclass
class ListenStatement(Statement):
    """Listen语句 - 等待用户输入"""
    begin_timeout: Optional[Expression] = None  # 开始超时
    end_timeout: Optional[Expression] = None    # 结束超时


@dataclass
class BranchCase:
    """分支条件"""
    intent: str           # 意图关键词
    target_step: str      # 目标步骤


@dataclass
class BranchStatement(Statement):
    """Branch语句 - 意图分支"""
    intent: str
    target_step: str


@dataclass
class SilenceStatement(Statement):
    """Silence语句 - 静默处理"""
    target_step: str


@dataclass
class DefaultStatement(Statement):
    """Default语句 - 默认处理"""
    target_step: str


@dataclass
class ExitStatement(Statement):
    """Exit语句 - 结束对话"""
    pass


@dataclass
class GotoStatement(Statement):
    """Goto语句 - 跳转到指定步骤"""
    target_step: str


@dataclass
class SetStatement(Statement):
    """Set语句 - 变量赋值"""
    variable: str
    expression: Expression


@dataclass
class IfStatement(Statement):
    """If语句 - 条件判断"""
    condition: Expression
    then_block: List[Statement]
    else_block: Optional[List[Statement]] = None


@dataclass
class WhileStatement(Statement):
    """While语句 - 循环"""
    condition: Expression
    body: List[Statement]


@dataclass
class CallStatement(Statement):
    """Call语句 - 调用外部服务"""
    service_name: str
    arguments: List[Expression] = field(default_factory=list)
    result_var: Optional[str] = None  # 存储结果的变量


# ============ 步骤和脚本节点 ============

@dataclass
class Step:
    """步骤定义"""
    name: str
    statements: List[Statement] = field(default_factory=list)
    branches: List[BranchCase] = field(default_factory=list)
    silence_handler: Optional[str] = None
    default_handler: Optional[str] = None
    is_exit: bool = False


@dataclass
class Script:
    """脚本（整个DSL程序）"""
    steps: Dict[str, Step] = field(default_factory=dict)
    entry_step: Optional[str] = None
    variables: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_step(self, name: str) -> Optional[Step]:
        """获取指定名称的步骤"""
        return self.steps.get(name)
    
    def get_entry_step(self) -> Optional[Step]:
        """获取入口步骤"""
        if self.entry_step:
            return self.steps.get(self.entry_step)
        # 如果没有指定入口，返回第一个步骤
        if self.steps:
            return next(iter(self.steps.values()))
        return None


# ============ 辅助类 ============

@dataclass
class ParseError:
    """解析错误"""
    message: str
    line: int
    column: int
    
    def __str__(self):
        return f"解析错误 (行 {self.line}, 列 {self.column}): {self.message}"


class ASTVisitor(ABC):
    """AST访问者基类"""
    
    def visit(self, node: ASTNode):
        """访问节点"""
        method_name = f'visit_{node.__class__.__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)
    
    def generic_visit(self, node: ASTNode):
        """通用访问方法"""
        raise NotImplementedError(f"未实现对 {node.__class__.__name__} 的访问")


class ASTPrinter(ASTVisitor):
    """AST打印器 - 用于调试"""
    
    def __init__(self):
        self.indent = 0
    
    def _print(self, text: str):
        print("  " * self.indent + text)
    
    def visit_Script(self, node: Script):
        self._print(f"Script (入口: {node.entry_step})")
        self.indent += 1
        for step in node.steps.values():
            self.visit(step)
        self.indent -= 1
    
    def visit_Step(self, node: Step):
        self._print(f"Step: {node.name}")
        self.indent += 1
        for stmt in node.statements:
            self.visit(stmt)
        if node.branches:
            self._print("Branches:")
            self.indent += 1
            for branch in node.branches:
                self._print(f"'{branch.intent}' -> {branch.target_step}")
            self.indent -= 1
        if node.silence_handler:
            self._print(f"Silence -> {node.silence_handler}")
        if node.default_handler:
            self._print(f"Default -> {node.default_handler}")
        self.indent -= 1
    
    def visit_SpeakStatement(self, node: SpeakStatement):
        self._print(f"Speak: {node.expression}")
    
    def visit_ListenStatement(self, node: ListenStatement):
        self._print(f"Listen: begin={node.begin_timeout}, end={node.end_timeout}")
    
    def visit_ExitStatement(self, node: ExitStatement):
        self._print("Exit")
    
    def visit_SetStatement(self, node: SetStatement):
        self._print(f"Set: ${node.variable} = {node.expression}")
    
    def visit_GotoStatement(self, node: GotoStatement):
        self._print(f"Goto: {node.target_step}")
    
    def visit_CallStatement(self, node: CallStatement):
        self._print(f"Call: {node.service_name}({node.arguments}) -> ${node.result_var}")
