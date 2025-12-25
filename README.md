# DSL智能Agent系统

## 项目简介

本项目是2025年程序设计实践课程大作业，实现了一个基于领域特定语言(DSL)的多业务场景智能客服机器人系统。

### 核心功能

- **自定义DSL脚本语言**：设计了专门用于描述客服机器人应答逻辑的脚本语言
- **通用脚本解释器**：实现了完整的词法分析、语法分析和解释执行
- **LLM意图识别**：集成Google Gemini API进行自然语言理解
- **三个业务场景**：医院挂号缴费取药、餐厅点餐付账、剧院售票领票
- **美观Web界面**：基于Flask的响应式前端界面

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Flask Web Application                   │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐    ┌──────────┐    ┌──────────────────────┐  │
│  │  Lexer   │ -> │  Parser  │ -> │     Interpreter      │  │
│  │ (词法分析)│    │(语法分析) │    │      (解释器)        │  │
│  └──────────┘    └──────────┘    └──────────────────────┘  │
│                                            │                 │
│                                            v                 │
│                               ┌──────────────────────┐      │
│                               │   Intent Recognizer  │      │
│                               │    (Gemini API)      │      │
│                               └──────────────────────┘      │
├─────────────────────────────────────────────────────────────┤
│                        DSL Scripts                           │
│   hospital.dsl    │    restaurant.dsl    │    theater.dsl   │
└─────────────────────────────────────────────────────────────┘
```

## 项目结构

```
dsl_agent_project/
├── app.py                 # Flask Web应用主入口
├── requirements.txt       # Python依赖
├── README.md             # 项目说明
├── src/                  # 源代码
│   ├── __init__.py
│   ├── lexer.py          # 词法分析器
│   ├── parser.py         # 语法分析器
│   ├── ast_nodes.py      # AST节点定义
│   ├── interpreter.py    # 解释器
│   └── intent_recognizer.py  # 意图识别器
├── scripts/              # DSL脚本文件
│   ├── hospital.dsl      # 医院场景脚本
│   ├── restaurant.dsl    # 餐厅场景脚本
│   └── theater.dsl       # 剧院场景脚本
├── templates/            # HTML模板
│   ├── index.html        # 首页
│   └── chat.html         # 聊天页面
├── static/               # 静态资源
│   └── css/
│       └── style.css     # 样式文件
├── tests/                # 测试文件
│   ├── __init__.py
│   ├── test_dsl.py       # 单元测试
│   ├── stubs.py          # 测试桩
│   └── run_tests.py      # 测试驱动
└── data/                 # 测试数据
    └── test_data.json
```

## DSL语法说明

### 关键字

| 关键字 | 说明 | 示例 |
|--------|------|------|
| Step | 定义步骤 | `Step welcome` |
| Speak | 输出文本 | `Speak "您好"` |
| Listen | 等待输入 | `Listen 5, 30` |
| Branch | 意图分支 | `Branch "挂号", registration` |
| Silence | 静默处理 | `Silence silenceHandler` |
| Default | 默认处理 | `Default defaultHandler` |
| Exit | 结束对话 | `Exit` |
| Set | 变量赋值 | `Set $name = "张三"` |
| Goto | 跳转步骤 | `Goto welcome` |
| Call | 调用服务 | `Call 创建挂号($dept) = $result` |
| If/Else/EndIf | 条件判断 | `If $count > 0 ... EndIf` |

### 脚本示例

```
Step welcome
    Speak "欢迎您，" + $name + "！请问有什么可以帮您？"
    Listen 5, 30
    Branch "挂号", registration
    Branch "缴费", payment
    Default defaultHandler

Step registration
    Set $department = "内科"
    Speak "您选择了" + $department
    Call 创建挂号($department) = $result
    Speak "挂号成功，单号：" + $result
    Exit
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行应用

```bash
python app.py
```

访问 http://localhost:5000 即可使用。

### 运行测试

```bash
python tests/run_tests.py
```

## API接口

### 启动会话
```
POST /api/start
Content-Type: application/json

{
    "scenario": "hospital"
}
```

### 发送消息
```
POST /api/chat
Content-Type: application/json

{
    "scenario": "hospital",
    "session_id": "xxx",
    "message": "我要挂号"
}
```

### 结束会话
```
POST /api/end
Content-Type: application/json

{
    "scenario": "hospital",
    "session_id": "xxx"
}
```

## 业务场景说明

### 1. 医院智能客服 (hospital.dsl)
- 科室选择与挂号
- 费用查询与缴纳
- 取药进度查询
- 人工服务转接

### 2. 餐厅点餐助手 (restaurant.dsl)
- 菜单浏览与推荐
- 点餐与订单管理
- 多种支付方式
- 服务员呼叫

### 3. 剧院售票服务 (theater.dsl)
- 演出信息查询
- 座位选择购票
- 取票码获取
- 会员服务管理

## 意图识别

系统使用Google Gemini 2.0 Flash模型进行意图识别：

1. 用户输入自然语言
2. 调用Gemini API进行意图分析
3. 返回匹配的意图和置信度
4. 根据意图执行相应的脚本分支

如果API调用失败，系统会自动使用关键词匹配作为后备方案。

## 测试说明

### 测试类型
- 单元测试：测试各组件功能
- 集成测试：测试完整流程
- 桩测试：使用测试桩隔离外部依赖

### 测试桩
- LLMStub: 模拟LLM服务
- ExternalServiceStub: 模拟外部服务
- UserInputStub: 模拟用户输入序列

## 作者信息

- 课程：程序设计实践
- 学校：北京邮电大学
- 专业：数据科学与大数据技术

