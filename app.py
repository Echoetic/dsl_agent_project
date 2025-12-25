"""
Flask Web应用
基于DSL的多业务场景Agent
"""

import os
import uuid
from flask import Flask, render_template, request, jsonify, session
from src.lexer import Lexer
from src.parser import Parser
from src.interpreter import Interpreter, InterpreterState
from src.intent_recognizer import GeminiIntentRecognizer, create_intent_recognizer

app = Flask(__name__)
app.secret_key = 'dsl_agent_secret_key_2024'

# 配置
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyDQJo3RmKSiAfj_CtVqFRCNPzLA-wCVLd0')
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), 'scripts')

# 全局存储
scripts_cache = {}  # 缓存解析后的脚本
interpreters = {}   # 存储解释器实例


def load_script(scenario: str):
    """加载并解析脚本"""
    if scenario in scripts_cache:
        return scripts_cache[scenario]
    
    script_path = os.path.join(SCRIPTS_DIR, f'{scenario}.dsl')
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"脚本文件不存在: {script_path}")
    
    with open(script_path, 'r', encoding='utf-8') as f:
        source = f.read()
    
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    script = parser.parse()
    
    scripts_cache[scenario] = script
    return script


def get_interpreter(scenario: str, session_id: str):
    """获取或创建解释器"""
    key = f"{scenario}_{session_id}"
    
    if key not in interpreters:
        script = load_script(scenario)
        intent_recognizer = create_intent_recognizer(GEMINI_API_KEY)
        interpreter = Interpreter(script, intent_recognizer)
        interpreters[key] = interpreter
    
    return interpreters[key]


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/chat/<scenario>')
def chat_page(scenario):
    """聊天页面"""
    scenarios = {
        'hospital': {'name': '医院智能客服', 'icon': '🏥', 'description': '看病挂号、缴费、取药'},
        'restaurant': {'name': '餐厅点餐助手', 'icon': '🍽️', 'description': '点餐、查看菜单、付账'},
        'theater': {'name': '剧院售票服务', 'icon': '🎭', 'description': '查询演出、购票、取票'}
    }
    
    if scenario not in scenarios:
        return "场景不存在", 404
    
    return render_template('chat.html', 
                         scenario=scenario, 
                         scenario_info=scenarios[scenario])


@app.route('/api/start', methods=['POST'])
def start_session():
    """启动新会话"""
    try:
        data = request.json
        scenario = data.get('scenario', 'hospital')
        
        # 生成会话ID
        session_id = str(uuid.uuid4())
        
        # 获取解释器
        interpreter = get_interpreter(scenario, session_id)
        
        # 创建会话上下文
        context = interpreter.create_session(session_id)
        
        # 启动解释器
        output = interpreter.start(session_id)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': output.message,
            'state': output.state.name,
            'waiting_for_input': output.waiting_for_input,
            'available_intents': output.available_intents
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """处理用户输入"""
    try:
        data = request.json
        scenario = data.get('scenario', 'hospital')
        session_id = data.get('session_id')
        user_input = data.get('message', '')
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': '会话ID不能为空'
            }), 400
        
        # 获取解释器
        interpreter = get_interpreter(scenario, session_id)
        
        # 检查会话是否存在
        context = interpreter.get_session(session_id)
        if not context:
            # 会话不存在，创建新会话并启动
            context = interpreter.create_session(session_id)
            output = interpreter.start(session_id)
            return jsonify({
                'success': True,
                'message': output.message,
                'state': output.state.name,
                'waiting_for_input': output.waiting_for_input,
                'available_intents': output.available_intents,
                'session_restarted': True
            })
        
        # 处理用户输入
        output = interpreter.process_input(session_id, user_input)
        
        return jsonify({
            'success': True,
            'message': output.message,
            'state': output.state.name,
            'waiting_for_input': output.waiting_for_input,
            'available_intents': output.available_intents
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/end', methods=['POST'])
def end_session():
    """结束会话"""
    try:
        data = request.json
        scenario = data.get('scenario', 'hospital')
        session_id = data.get('session_id')
        
        if session_id:
            key = f"{scenario}_{session_id}"
            if key in interpreters:
                interpreter = interpreters[key]
                interpreter.remove_session(session_id)
        
        return jsonify({
            'success': True,
            'message': '会话已结束'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/scripts')
def list_scripts():
    """列出所有可用脚本"""
    scripts = []
    for filename in os.listdir(SCRIPTS_DIR):
        if filename.endswith('.dsl'):
            name = filename[:-4]
            scripts.append({
                'name': name,
                'filename': filename
            })
    return jsonify(scripts)


@app.route('/api/script/<name>')
def get_script(name):
    """获取脚本内容"""
    try:
        script_path = os.path.join(SCRIPTS_DIR, f'{name}.dsl')
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({
            'success': True,
            'content': content
        })
    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': '脚本不存在'
        }), 404


@app.route('/api/parse', methods=['POST'])
def parse_script():
    """解析脚本（用于调试）"""
    try:
        data = request.json
        source = data.get('source', '')
        
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        script = parser.parse()
        
        # 返回脚本结构
        steps = []
        for name, step in script.steps.items():
            steps.append({
                'name': name,
                'statements': len(step.statements),
                'branches': [{'intent': b.intent, 'target': b.target_step} for b in step.branches],
                'silence_handler': step.silence_handler,
                'default_handler': step.default_handler,
                'is_exit': step.is_exit
            })
        
        return jsonify({
            'success': True,
            'entry_step': script.entry_step,
            'steps': steps,
            'errors': [str(e) for e in parser.errors]
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # 确保脚本目录存在
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    
    # 启动应用
    app.run(host='0.0.0.0', port=5000, debug=True)
