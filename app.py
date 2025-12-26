"""
Flask Web应用
基于DSL的多业务场景Agent
包含用户认证功能和动态场景管理
"""

import os
import uuid
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from src.lexer import Lexer
from src.parser import Parser
from src.interpreter import Interpreter, InterpreterState
from src.intent_recognizer import GeminiIntentRecognizer, create_intent_recognizer
from src.auth import get_auth_service, AuthService
from src.scenario_manager import get_scenario_manager, init_scenario_manager

app = Flask(__name__)
app.secret_key = 'dsl_agent_secret_key_2024_secure'

# 配置
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyDQJo3RmKSiAfj_CtVqFRCNPzLA-wCVLd0')
BASE_DIR = os.path.dirname(__file__)
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')
CONFIG_DIR = os.path.join(BASE_DIR, 'config')

# 初始化场景管理器
scenario_manager = init_scenario_manager(
    config_path=os.path.join(CONFIG_DIR, 'scenarios.json'),
    scripts_dir=SCRIPTS_DIR
)

# 全局存储
scripts_cache = {}  # 缓存解析后的脚本
interpreters = {}   # 存储解释器实例

# 认证服务
auth_service = get_auth_service()


# ==================== 认证装饰器 ====================

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_session_id = session.get('auth_session_id')
        if not auth_session_id:
            # API请求返回JSON
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': '请先登录',
                    'require_login': True
                }), 401
            # 页面请求重定向到登录页
            return redirect(url_for('login_page'))
        
        # 验证会话
        is_valid, user = auth_service.validate_session(auth_session_id)
        if not is_valid:
            session.pop('auth_session_id', None)
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': '会话已过期，请重新登录',
                    'require_login': True
                }), 401
            return redirect(url_for('login_page'))
        
        # 将用户信息存入请求上下文
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function


def get_current_user():
    """获取当前登录用户"""
    auth_session_id = session.get('auth_session_id')
    if auth_session_id:
        return auth_service.get_current_user(auth_session_id)
    return None


# ==================== 脚本相关函数 ====================

def load_script(scenario: str):
    """加载并解析脚本"""
    if scenario in scripts_cache:
        return scripts_cache[scenario]
    
    # 使用场景管理器获取脚本路径
    script_path = scenario_manager.get_script_path(scenario)
    if not script_path or not os.path.exists(script_path):
        raise FileNotFoundError(f"脚本文件不存在: {scenario}")
    
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


# ==================== 认证页面路由 ====================

@app.route('/login')
def login_page():
    """登录页面"""
    # 如果已登录，重定向到首页
    if get_current_user():
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/register')
def register_page():
    """注册页面"""
    # 如果已登录，重定向到首页
    if get_current_user():
        return redirect(url_for('index'))
    return render_template('register.html')


@app.route('/profile')
@login_required
def profile_page():
    """个人资料页面"""
    return render_template('profile.html', user=request.current_user)


# ==================== 认证API路由 ====================

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """用户注册API"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        
        success, message, user = auth_service.register(username, password, email)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'user': user.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'注册失败: {str(e)}'
        }), 500


@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """用户登录API"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # 获取客户端信息
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        success, message, auth_session_id, user = auth_service.login(
            username, password, ip_address, user_agent
        )
        
        if success:
            # 将认证会话ID存入Flask session
            session['auth_session_id'] = auth_session_id
            
            return jsonify({
                'success': True,
                'message': message,
                'user': user.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 401
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'登录失败: {str(e)}'
        }), 500


@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """用户登出API"""
    try:
        auth_session_id = session.get('auth_session_id')
        if auth_session_id:
            auth_service.logout(auth_session_id)
        
        # 清除Flask session
        session.pop('auth_session_id', None)
        
        return jsonify({
            'success': True,
            'message': '登出成功'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'登出失败: {str(e)}'
        }), 500


@app.route('/api/auth/status')
def api_auth_status():
    """获取当前登录状态"""
    user = get_current_user()
    if user:
        return jsonify({
            'logged_in': True,
            'user': user.to_dict()
        })
    else:
        return jsonify({
            'logged_in': False,
            'user': None
        })


@app.route('/api/auth/change-password', methods=['POST'])
@login_required
def api_change_password():
    """修改密码API"""
    try:
        data = request.json
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        
        user = request.current_user
        success, message = auth_service.change_password(
            user.user_id, old_password, new_password
        )
        
        if success:
            # 清除当前会话
            session.pop('auth_session_id', None)
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'修改密码失败: {str(e)}'
        }), 500


# ==================== 主页面路由 ====================

@app.route('/')
def index():
    """首页"""
    user = get_current_user()
    scenarios = scenario_manager.get_enabled_scenarios()
    site_config = scenario_manager.get_site_config()
    
    return render_template('index.html', 
                         user=user, 
                         scenarios=scenarios,
                         site=site_config)


@app.route('/chat/<scenario>')
@login_required
def chat_page(scenario):
    """聊天页面（需要登录）"""
    # 检查场景是否存在
    if not scenario_manager.scenario_exists(scenario):
        return "场景不存在", 404
    
    scenario_config = scenario_manager.get_scenario(scenario)
    
    return render_template('chat.html', 
                         scenario=scenario, 
                         scenario_info=scenario_config,
                         user=request.current_user)


# ==================== 场景API路由 ====================

@app.route('/api/scenarios')
def api_scenarios():
    """获取所有可用场景"""
    scenarios = scenario_manager.get_scenarios_for_api()
    return jsonify({
        'success': True,
        'scenarios': scenarios
    })


@app.route('/api/scenario/<scenario_id>')
def api_scenario_detail(scenario_id):
    """获取场景详情"""
    scenario = scenario_manager.get_scenario(scenario_id)
    if scenario:
        return jsonify({
            'success': True,
            'scenario': scenario.to_dict()
        })
    else:
        return jsonify({
            'success': False,
            'error': '场景不存在'
        }), 404


# ==================== 聊天API路由 ====================

@app.route('/api/start', methods=['POST'])
@login_required
def start_session():
    """启动新会话"""
    try:
        data = request.json
        scenario = data.get('scenario', 'hospital')
        
        # 验证场景是否存在
        if not scenario_manager.scenario_exists(scenario):
            return jsonify({
                'success': False,
                'error': f'场景不存在: {scenario}'
            }), 404
        
        # 生成会话ID（包含用户ID以便追踪）
        user = request.current_user
        session_id = f"{user.user_id}_{str(uuid.uuid4())}"
        
        # 获取解释器
        interpreter = get_interpreter(scenario, session_id)
        
        # 创建会话上下文，传入用户名
        context = interpreter.create_session(session_id, {'name': user.username})
        
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
@login_required
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
        
        # 验证场景是否存在
        if not scenario_manager.scenario_exists(scenario):
            return jsonify({
                'success': False,
                'error': f'场景不存在: {scenario}'
            }), 404
        
        # 获取解释器
        interpreter = get_interpreter(scenario, session_id)
        
        # 检查会话是否存在
        context = interpreter.get_session(session_id)
        if not context:
            # 会话不存在，创建新会话并启动
            user = request.current_user
            context = interpreter.create_session(session_id, {'name': user.username})
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
@login_required
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


# ==================== 其他API路由 ====================

@app.route('/api/scripts')
@login_required
def list_scripts():
    """列出所有可用脚本"""
    scripts = []
    for filename in os.listdir(SCRIPTS_DIR):
        if filename.endswith('.dsl'):
            name = filename[:-4]
            scenario = scenario_manager.get_scenario(name)
            scripts.append({
                'name': name,
                'filename': filename,
                'display_name': scenario.name if scenario else name,
                'enabled': scenario.enabled if scenario else True
            })
    return jsonify(scripts)


@app.route('/api/script/<n>')
@login_required
def get_script(name):
    """获取脚本内容"""
    try:
        script_path = scenario_manager.get_script_path(name)
        if not script_path:
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
@login_required
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


@app.route('/api/site-config')
def api_site_config():
    """获取站点配置"""
    site_config = scenario_manager.get_site_config()
    return jsonify({
        'success': True,
        'config': site_config.to_dict()
    })


if __name__ == '__main__':
    # 确保目录存在
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    
    # 启动应用
    app.run(host='0.0.0.0', port=5000, debug=True)