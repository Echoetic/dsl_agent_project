"""
DSL语法分析器 (Parser)
将Token序列转换为AST
"""

from typing import List, Optional, Any
from .lexer import Token, TokenType, Lexer, LexerError
from .ast_nodes import (
    Script, Step, Statement, Expression,
    SpeakStatement, ListenStatement, BranchStatement, BranchCase,
    SilenceStatement, DefaultStatement, ExitStatement, GotoStatement,
    SetStatement, IfStatement, WhileStatement, CallStatement,
    StringLiteral, NumberLiteral, Variable, BinaryOp, UnaryOp, FunctionCall,
    ParseError
)


class ParserError(Exception):
    """语法分析错误"""
    def __init__(self, message: str, token: Token):
        self.message = message
        self.token = token
        super().__init__(f"语法错误 (行 {token.line}, 列 {token.column}): {message}")


class Parser:
    """语法分析器"""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.errors: List[ParseError] = []
    
    def current_token(self) -> Token:
        """获取当前Token"""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]  # 返回EOF
    
    def peek(self, offset: int = 0) -> Token:
        """查看偏移位置的Token"""
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return self.tokens[-1]
    
    def advance(self) -> Token:
        """前进一个Token"""
        token = self.current_token()
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return token
    
    def match(self, *types: TokenType) -> bool:
        """检查当前Token是否匹配指定类型"""
        return self.current_token().type in types
    
    def expect(self, token_type: TokenType, message: str = None) -> Token:
        """期望当前Token为指定类型"""
        if self.match(token_type):
            return self.advance()
        msg = message or f"期望 {token_type.name}，实际为 {self.current_token().type.name}"
        raise ParserError(msg, self.current_token())
    
    def skip_newlines(self):
        """跳过换行"""
        while self.match(TokenType.NEWLINE):
            self.advance()
    
    def parse(self) -> Script:
        """解析整个脚本"""
        script = Script()
        self.skip_newlines()
        
        while not self.match(TokenType.EOF):
            try:
                if self.match(TokenType.STEP):
                    step = self.parse_step()
                    script.steps[step.name] = step
                    if script.entry_step is None:
                        script.entry_step = step.name
                else:
                    raise ParserError(f"期望 Step 关键字，实际为 {self.current_token().value}", 
                                     self.current_token())
            except ParserError as e:
                self.errors.append(ParseError(e.message, e.token.line, e.token.column))
                # 尝试恢复：跳到下一个Step
                while not self.match(TokenType.STEP, TokenType.EOF):
                    self.advance()
            
            self.skip_newlines()
        
        return script
    
    def parse_step(self) -> Step:
        """解析Step"""
        self.expect(TokenType.STEP)
        name_token = self.expect(TokenType.IDENTIFIER, "期望步骤名称")
        step = Step(name=name_token.value)
        
        self.skip_newlines()
        
        # 解析步骤内的语句
        while not self.match(TokenType.STEP, TokenType.EOF):
            self.skip_newlines()
            if self.match(TokenType.STEP, TokenType.EOF):
                break
                
            stmt = self.parse_statement()
            if stmt:
                if isinstance(stmt, BranchStatement):
                    step.branches.append(BranchCase(stmt.intent, stmt.target_step))
                elif isinstance(stmt, SilenceStatement):
                    step.silence_handler = stmt.target_step
                elif isinstance(stmt, DefaultStatement):
                    step.default_handler = stmt.target_step
                elif isinstance(stmt, ExitStatement):
                    step.is_exit = True
                    step.statements.append(stmt)
                else:
                    step.statements.append(stmt)
            
            self.skip_newlines()
        
        return step
    
    def parse_statement(self) -> Optional[Statement]:
        """解析语句"""
        if self.match(TokenType.SPEAK):
            return self.parse_speak()
        elif self.match(TokenType.LISTEN):
            return self.parse_listen()
        elif self.match(TokenType.BRANCH):
            return self.parse_branch()
        elif self.match(TokenType.SILENCE):
            return self.parse_silence()
        elif self.match(TokenType.DEFAULT):
            return self.parse_default()
        elif self.match(TokenType.EXIT):
            return self.parse_exit()
        elif self.match(TokenType.GOTO):
            return self.parse_goto()
        elif self.match(TokenType.SET):
            return self.parse_set()
        elif self.match(TokenType.IF):
            return self.parse_if()
        elif self.match(TokenType.WHILE):
            return self.parse_while()
        elif self.match(TokenType.CALL):
            return self.parse_call()
        elif self.match(TokenType.NEWLINE):
            self.advance()
            return None
        else:
            raise ParserError(f"未知语句类型: {self.current_token().value}", 
                            self.current_token())
    
    def parse_speak(self) -> SpeakStatement:
        """解析Speak语句"""
        self.expect(TokenType.SPEAK)
        expr = self.parse_expression()
        return SpeakStatement(expression=expr)
    
    def parse_listen(self) -> ListenStatement:
        """解析Listen语句"""
        self.expect(TokenType.LISTEN)
        begin_timeout = None
        end_timeout = None
        
        if self.match(TokenType.NUMBER):
            begin_timeout = NumberLiteral(self.advance().value)
            if self.match(TokenType.COMMA):
                self.advance()
                if self.match(TokenType.NUMBER):
                    end_timeout = NumberLiteral(self.advance().value)
        
        return ListenStatement(begin_timeout=begin_timeout, end_timeout=end_timeout)
    
    def parse_branch(self) -> BranchStatement:
        """解析Branch语句"""
        self.expect(TokenType.BRANCH)
        intent = self.expect(TokenType.STRING, "期望意图字符串").value
        if self.match(TokenType.COMMA):
            self.advance()
        target = self.expect(TokenType.IDENTIFIER, "期望目标步骤名").value
        return BranchStatement(intent=intent, target_step=target)
    
    def parse_silence(self) -> SilenceStatement:
        """解析Silence语句"""
        self.expect(TokenType.SILENCE)
        target = self.expect(TokenType.IDENTIFIER, "期望目标步骤名").value
        return SilenceStatement(target_step=target)
    
    def parse_default(self) -> DefaultStatement:
        """解析Default语句"""
        self.expect(TokenType.DEFAULT)
        target = self.expect(TokenType.IDENTIFIER, "期望目标步骤名").value
        return DefaultStatement(target_step=target)
    
    def parse_exit(self) -> ExitStatement:
        """解析Exit语句"""
        self.expect(TokenType.EXIT)
        return ExitStatement()
    
    def parse_goto(self) -> GotoStatement:
        """解析Goto语句"""
        self.expect(TokenType.GOTO)
        target = self.expect(TokenType.IDENTIFIER, "期望目标步骤名").value
        return GotoStatement(target_step=target)
    
    def parse_set(self) -> SetStatement:
        """解析Set语句"""
        self.expect(TokenType.SET)
        var_token = self.expect(TokenType.VARIABLE, "期望变量名")
        self.expect(TokenType.ASSIGN, "期望赋值符号 =")
        expr = self.parse_expression()
        return SetStatement(variable=var_token.value, expression=expr)
    
    def parse_if(self) -> IfStatement:
        """解析If语句"""
        self.expect(TokenType.IF)
        condition = self.parse_expression()
        self.skip_newlines()
        
        then_block = []
        while not self.match(TokenType.ELSE, TokenType.ENDIF, TokenType.EOF):
            stmt = self.parse_statement()
            if stmt:
                then_block.append(stmt)
            self.skip_newlines()
        
        else_block = None
        if self.match(TokenType.ELSE):
            self.advance()
            self.skip_newlines()
            else_block = []
            while not self.match(TokenType.ENDIF, TokenType.EOF):
                stmt = self.parse_statement()
                if stmt:
                    else_block.append(stmt)
                self.skip_newlines()
        
        self.expect(TokenType.ENDIF, "期望 EndIf")
        return IfStatement(condition=condition, then_block=then_block, else_block=else_block)
    
    def parse_while(self) -> WhileStatement:
        """解析While语句"""
        self.expect(TokenType.WHILE)
        condition = self.parse_expression()
        self.skip_newlines()
        
        body = []
        while not self.match(TokenType.ENDWHILE, TokenType.EOF):
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
            self.skip_newlines()
        
        self.expect(TokenType.ENDWHILE, "期望 EndWhile")
        return WhileStatement(condition=condition, body=body)
    
    def parse_call(self) -> CallStatement:
        """解析Call语句"""
        self.expect(TokenType.CALL)
        service = self.expect(TokenType.IDENTIFIER, "期望服务名").value
        
        arguments = []
        if self.match(TokenType.LPAREN):
            self.advance()
            if not self.match(TokenType.RPAREN):
                arguments.append(self.parse_expression())
                while self.match(TokenType.COMMA):
                    self.advance()
                    arguments.append(self.parse_expression())
            self.expect(TokenType.RPAREN, "期望右括号")
        
        result_var = None
        if self.match(TokenType.ASSIGN):
            self.advance()
            result_var = self.expect(TokenType.VARIABLE, "期望结果变量").value
        
        return CallStatement(service_name=service, arguments=arguments, result_var=result_var)
    
    def parse_expression(self) -> Expression:
        """解析表达式"""
        return self.parse_or_expr()
    
    def parse_or_expr(self) -> Expression:
        """解析or表达式"""
        left = self.parse_and_expr()
        while self.match(TokenType.OR):
            op = self.advance().value
            right = self.parse_and_expr()
            left = BinaryOp(left=left, operator=op, right=right)
        return left
    
    def parse_and_expr(self) -> Expression:
        """解析and表达式"""
        left = self.parse_equality_expr()
        while self.match(TokenType.AND):
            op = self.advance().value
            right = self.parse_equality_expr()
            left = BinaryOp(left=left, operator=op, right=right)
        return left
    
    def parse_equality_expr(self) -> Expression:
        """解析相等性表达式"""
        left = self.parse_comparison_expr()
        while self.match(TokenType.EQUALS, TokenType.NOT_EQUALS):
            op = self.advance().value
            right = self.parse_comparison_expr()
            left = BinaryOp(left=left, operator=op, right=right)
        return left
    
    def parse_comparison_expr(self) -> Expression:
        """解析比较表达式"""
        left = self.parse_additive_expr()
        while self.match(TokenType.GREATER, TokenType.LESS, 
                        TokenType.GREATER_EQUALS, TokenType.LESS_EQUALS):
            op = self.advance().value
            right = self.parse_additive_expr()
            left = BinaryOp(left=left, operator=op, right=right)
        return left
    
    def parse_additive_expr(self) -> Expression:
        """解析加减表达式"""
        left = self.parse_multiplicative_expr()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            op = self.advance().value
            right = self.parse_multiplicative_expr()
            left = BinaryOp(left=left, operator=op, right=right)
        return left
    
    def parse_multiplicative_expr(self) -> Expression:
        """解析乘除表达式"""
        left = self.parse_unary_expr()
        while self.match(TokenType.MULTIPLY, TokenType.DIVIDE):
            op = self.advance().value
            right = self.parse_unary_expr()
            left = BinaryOp(left=left, operator=op, right=right)
        return left
    
    def parse_unary_expr(self) -> Expression:
        """解析一元表达式"""
        if self.match(TokenType.NOT, TokenType.MINUS):
            op = self.advance().value
            operand = self.parse_unary_expr()
            return UnaryOp(operator=op, operand=operand)
        return self.parse_primary_expr()
    
    def parse_primary_expr(self) -> Expression:
        """解析基本表达式"""
        if self.match(TokenType.STRING):
            return StringLiteral(self.advance().value)
        elif self.match(TokenType.NUMBER):
            return NumberLiteral(self.advance().value)
        elif self.match(TokenType.VARIABLE):
            return Variable(self.advance().value)
        elif self.match(TokenType.IDENTIFIER):
            name = self.advance().value
            # 检查是否是函数调用
            if self.match(TokenType.LPAREN):
                self.advance()
                args = []
                if not self.match(TokenType.RPAREN):
                    args.append(self.parse_expression())
                    while self.match(TokenType.COMMA):
                        self.advance()
                        args.append(self.parse_expression())
                self.expect(TokenType.RPAREN, "期望右括号")
                return FunctionCall(name=name, arguments=args)
            return Variable(name)
        elif self.match(TokenType.LPAREN):
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN, "期望右括号")
            return expr
        else:
            raise ParserError(f"无效的表达式: {self.current_token().value}", 
                            self.current_token())


def parse(source: str) -> Script:
    """便捷函数：解析源代码为AST"""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()
