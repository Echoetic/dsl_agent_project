"""
DSL词法分析器 (Lexer)
负责将脚本文本转换为Token序列
"""

import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional, Any


class TokenType(Enum):
    """Token类型枚举"""
    # 关键字
    STEP = auto()
    SPEAK = auto()
    LISTEN = auto()
    BRANCH = auto()
    SILENCE = auto()
    DEFAULT = auto()
    EXIT = auto()
    GOTO = auto()
    SET = auto()
    IF = auto()
    ELSE = auto()
    ENDIF = auto()
    WHILE = auto()
    ENDWHILE = auto()
    CALL = auto()  # 调用外部服务
    
    # 字面量
    STRING = auto()
    NUMBER = auto()
    IDENTIFIER = auto()
    VARIABLE = auto()  # $开头的变量
    
    # 操作符
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    EQUALS = auto()
    NOT_EQUALS = auto()
    GREATER = auto()
    LESS = auto()
    GREATER_EQUALS = auto()
    LESS_EQUALS = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    ASSIGN = auto()
    
    # 分隔符
    COMMA = auto()
    COLON = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LBRACE = auto()
    RBRACE = auto()
    
    # 特殊
    NEWLINE = auto()
    EOF = auto()
    COMMENT = auto()


@dataclass
class Token:
    """Token数据类"""
    type: TokenType
    value: Any
    line: int
    column: int
    
    def __repr__(self):
        return f"Token({self.type.name}, {repr(self.value)}, L{self.line}:C{self.column})"


class LexerError(Exception):
    """词法分析错误"""
    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"词法错误 (行 {line}, 列 {column}): {message}")


class Lexer:
    """词法分析器"""
    
    # 关键字映射
    KEYWORDS = {
        'Step': TokenType.STEP,
        'Speak': TokenType.SPEAK,
        'Listen': TokenType.LISTEN,
        'Branch': TokenType.BRANCH,
        'Silence': TokenType.SILENCE,
        'Default': TokenType.DEFAULT,
        'Exit': TokenType.EXIT,
        'Goto': TokenType.GOTO,
        'Set': TokenType.SET,
        'If': TokenType.IF,
        'Else': TokenType.ELSE,
        'EndIf': TokenType.ENDIF,
        'While': TokenType.WHILE,
        'EndWhile': TokenType.ENDWHILE,
        'Call': TokenType.CALL,
        'and': TokenType.AND,
        'or': TokenType.OR,
        'not': TokenType.NOT,
    }
    
    # 操作符映射
    OPERATORS = {
        '+': TokenType.PLUS,
        '-': TokenType.MINUS,
        '*': TokenType.MULTIPLY,
        '/': TokenType.DIVIDE,
        '==': TokenType.EQUALS,
        '!=': TokenType.NOT_EQUALS,
        '>': TokenType.GREATER,
        '<': TokenType.LESS,
        '>=': TokenType.GREATER_EQUALS,
        '<=': TokenType.LESS_EQUALS,
        '=': TokenType.ASSIGN,
    }
    
    # 分隔符映射
    DELIMITERS = {
        ',': TokenType.COMMA,
        ':': TokenType.COLON,
        '(': TokenType.LPAREN,
        ')': TokenType.RPAREN,
        '[': TokenType.LBRACKET,
        ']': TokenType.RBRACKET,
        '{': TokenType.LBRACE,
        '}': TokenType.RBRACE,
    }
    
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
    
    def peek(self, offset: int = 0) -> Optional[str]:
        """查看当前或偏移位置的字符"""
        pos = self.pos + offset
        if pos < len(self.source):
            return self.source[pos]
        return None
    
    def advance(self) -> Optional[str]:
        """前进一个字符"""
        if self.pos < len(self.source):
            char = self.source[self.pos]
            self.pos += 1
            if char == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            return char
        return None
    
    def skip_whitespace(self):
        """跳过空白字符（不包括换行）"""
        while self.peek() and self.peek() in ' \t\r':
            self.advance()
    
    def skip_comment(self):
        """跳过注释"""
        if self.peek() == '#':
            while self.peek() and self.peek() != '\n':
                self.advance()
    
    def read_string(self) -> str:
        """读取字符串"""
        start_line = self.line
        start_col = self.column
        quote = self.advance()  # 消费开始引号
        result = []
        
        while self.peek() and self.peek() != quote:
            if self.peek() == '\\':
                self.advance()
                escaped = self.advance()
                if escaped == 'n':
                    result.append('\n')
                elif escaped == 't':
                    result.append('\t')
                elif escaped == '\\':
                    result.append('\\')
                elif escaped == quote:
                    result.append(quote)
                else:
                    result.append(escaped)
            elif self.peek() == '\n':
                raise LexerError("字符串未闭合", start_line, start_col)
            else:
                result.append(self.advance())
        
        if not self.peek():
            raise LexerError("字符串未闭合", start_line, start_col)
        
        self.advance()  # 消费结束引号
        return ''.join(result)
    
    def read_number(self) -> float:
        """读取数字"""
        result = []
        has_dot = False
        
        while self.peek() and (self.peek().isdigit() or self.peek() == '.'):
            if self.peek() == '.':
                if has_dot:
                    break
                has_dot = True
            result.append(self.advance())
        
        return float(''.join(result)) if has_dot else int(''.join(result))
    
    def read_identifier(self) -> str:
        """读取标识符"""
        result = []
        while self.peek() and (self.peek().isalnum() or self.peek() in '_'):
            result.append(self.advance())
        return ''.join(result)
    
    def read_variable(self) -> str:
        """读取变量（$开头）"""
        self.advance()  # 消费 $
        return self.read_identifier()
    
    def tokenize(self) -> List[Token]:
        """执行词法分析"""
        self.tokens = []
        
        while self.pos < len(self.source):
            start_line = self.line
            start_col = self.column
            char = self.peek()
            
            # 跳过空白
            if char in ' \t\r':
                self.skip_whitespace()
                continue
            
            # 处理换行
            if char == '\n':
                self.advance()
                self.tokens.append(Token(TokenType.NEWLINE, '\\n', start_line, start_col))
                continue
            
            # 跳过注释
            if char == '#':
                self.skip_comment()
                continue
            
            # 读取字符串
            if char in '"\'':
                value = self.read_string()
                self.tokens.append(Token(TokenType.STRING, value, start_line, start_col))
                continue
            
            # 读取数字
            if char.isdigit():
                value = self.read_number()
                self.tokens.append(Token(TokenType.NUMBER, value, start_line, start_col))
                continue
            
            # 读取变量
            if char == '$':
                value = self.read_variable()
                self.tokens.append(Token(TokenType.VARIABLE, value, start_line, start_col))
                continue
            
            # 读取标识符或关键字
            if char.isalpha() or char == '_':
                value = self.read_identifier()
                token_type = self.KEYWORDS.get(value, TokenType.IDENTIFIER)
                self.tokens.append(Token(token_type, value, start_line, start_col))
                continue
            
            # 处理双字符操作符
            two_char = char + (self.peek(1) or '')
            if two_char in self.OPERATORS:
                self.advance()
                self.advance()
                self.tokens.append(Token(self.OPERATORS[two_char], two_char, start_line, start_col))
                continue
            
            # 处理单字符操作符
            if char in self.OPERATORS:
                self.advance()
                self.tokens.append(Token(self.OPERATORS[char], char, start_line, start_col))
                continue
            
            # 处理分隔符
            if char in self.DELIMITERS:
                self.advance()
                self.tokens.append(Token(self.DELIMITERS[char], char, start_line, start_col))
                continue
            
            # 未知字符
            raise LexerError(f"未知字符: {char}", start_line, start_col)
        
        # 添加EOF
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        
        return self.tokens


def tokenize(source: str) -> List[Token]:
    """便捷函数：对源代码进行词法分析"""
    lexer = Lexer(source)
    return lexer.tokenize()
