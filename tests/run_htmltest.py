#!/usr/bin/env python3
"""
测试报告生成器 - 生成详细的HTML格式测试报告
"""

import sys
import os
import unittest
import json
import time
import traceback
from datetime import datetime
from io import StringIO
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


@dataclass
class TestCaseResult:
    """单个测试用例结果"""
    name: str
    class_name: str
    method_name: str
    description: str
    status: str  # 'passed', 'failed', 'error', 'skipped'
    duration: float
    message: str = ""
    traceback: str = ""


@dataclass
class TestSuiteResult:
    """测试套件结果"""
    name: str
    test_cases: List[TestCaseResult] = field(default_factory=list)
    
    @property
    def total(self) -> int:
        return len(self.test_cases)
    
    @property
    def passed(self) -> int:
        return sum(1 for tc in self.test_cases if tc.status == 'passed')
    
    @property
    def failed(self) -> int:
        return sum(1 for tc in self.test_cases if tc.status == 'failed')
    
    @property
    def errors(self) -> int:
        return sum(1 for tc in self.test_cases if tc.status == 'error')
    
    @property
    def skipped(self) -> int:
        return sum(1 for tc in self.test_cases if tc.status == 'skipped')
    
    @property
    def duration(self) -> float:
        return sum(tc.duration for tc in self.test_cases)


class HTMLTestResult(unittest.TestResult):
    """自定义测试结果收集器"""
    
    def __init__(self):
        super().__init__()
        self.test_results: List[TestCaseResult] = []
        self.start_time = None
        self.current_test_start = None
        
    def startTest(self, test):
        super().startTest(test)
        self.current_test_start = time.time()
    
    def stopTest(self, test):
        super().stopTest(test)
    
    def _get_test_info(self, test) -> tuple:
        """获取测试信息"""
        class_name = test.__class__.__name__
        method_name = test._testMethodName
        description = test.shortDescription() or method_name
        return class_name, method_name, description
    
    def _get_duration(self) -> float:
        """获取测试耗时"""
        if self.current_test_start:
            return time.time() - self.current_test_start
        return 0.0
    
    def addSuccess(self, test):
        super().addSuccess(test)
        class_name, method_name, description = self._get_test_info(test)
        self.test_results.append(TestCaseResult(
            name=f"{class_name}.{method_name}",
            class_name=class_name,
            method_name=method_name,
            description=description,
            status='passed',
            duration=self._get_duration()
        ))
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        class_name, method_name, description = self._get_test_info(test)
        self.test_results.append(TestCaseResult(
            name=f"{class_name}.{method_name}",
            class_name=class_name,
            method_name=method_name,
            description=description,
            status='failed',
            duration=self._get_duration(),
            message=str(err[1]),
            traceback=''.join(traceback.format_exception(*err))
        ))
    
    def addError(self, test, err):
        super().addError(test, err)
        class_name, method_name, description = self._get_test_info(test)
        self.test_results.append(TestCaseResult(
            name=f"{class_name}.{method_name}",
            class_name=class_name,
            method_name=method_name,
            description=description,
            status='error',
            duration=self._get_duration(),
            message=str(err[1]),
            traceback=''.join(traceback.format_exception(*err))
        ))
    
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        class_name, method_name, description = self._get_test_info(test)
        self.test_results.append(TestCaseResult(
            name=f"{class_name}.{method_name}",
            class_name=class_name,
            method_name=method_name,
            description=description,
            status='skipped',
            duration=self._get_duration(),
            message=reason
        ))


class HTMLReportGenerator:
    """HTML报告生成器"""
    
    def __init__(self, title: str = "DSL Agent 测试报告"):
        self.title = title
        self.start_time = None
        self.end_time = None
        self.test_suites: List[TestSuiteResult] = []
    
    def generate_report(self, result: HTMLTestResult) -> str:
        """生成HTML报告"""
        # 按测试类分组
        suites_dict: Dict[str, TestSuiteResult] = {}
        for tc in result.test_results:
            if tc.class_name not in suites_dict:
                suites_dict[tc.class_name] = TestSuiteResult(name=tc.class_name)
            suites_dict[tc.class_name].test_cases.append(tc)
        
        self.test_suites = list(suites_dict.values())
        
        # 计算总体统计
        total = sum(s.total for s in self.test_suites)
        passed = sum(s.passed for s in self.test_suites)
        failed = sum(s.failed for s in self.test_suites)
        errors = sum(s.errors for s in self.test_suites)
        skipped = sum(s.skipped for s in self.test_suites)
        total_duration = sum(s.duration for s in self.test_suites)
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        return self._render_html(
            total=total,
            passed=passed,
            failed=failed,
            errors=errors,
            skipped=skipped,
            pass_rate=pass_rate,
            total_duration=total_duration
        )
    
    def _render_html(self, total, passed, failed, errors, skipped, pass_rate, total_duration) -> str:
        """渲染HTML"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 生成测试套件HTML
        suites_html = ""
        for suite in self.test_suites:
            suites_html += self._render_suite(suite)
        
        # 生成统计图表数据
        chart_data = {
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'skipped': skipped
        }
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --primary-color: #4A90D9;
            --success-color: #28a745;
            --danger-color: #dc3545;
            --warning-color: #ffc107;
            --info-color: #17a2b8;
            --light-color: #f8f9fa;
            --dark-color: #343a40;
            --border-color: #dee2e6;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: var(--dark-color);
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .report-header {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }}
        
        .report-title {{
            font-size: 2rem;
            color: var(--primary-color);
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .report-title::before {{
            content: '📊';
            font-size: 2.5rem;
        }}
        
        .report-meta {{
            color: #666;
            font-size: 0.95rem;
        }}
        
        .report-meta span {{
            margin-right: 20px;
        }}
        
        .summary-section {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .summary-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        
        .summary-card:hover {{
            transform: translateY(-5px);
        }}
        
        .summary-card.total {{
            border-top: 4px solid var(--primary-color);
        }}
        
        .summary-card.passed {{
            border-top: 4px solid var(--success-color);
        }}
        
        .summary-card.failed {{
            border-top: 4px solid var(--danger-color);
        }}
        
        .summary-card.errors {{
            border-top: 4px solid var(--warning-color);
        }}
        
        .summary-card.skipped {{
            border-top: 4px solid var(--info-color);
        }}
        
        .summary-number {{
            font-size: 3rem;
            font-weight: bold;
            line-height: 1;
            margin-bottom: 10px;
        }}
        
        .summary-card.total .summary-number {{ color: var(--primary-color); }}
        .summary-card.passed .summary-number {{ color: var(--success-color); }}
        .summary-card.failed .summary-number {{ color: var(--danger-color); }}
        .summary-card.errors .summary-number {{ color: var(--warning-color); }}
        .summary-card.skipped .summary-number {{ color: var(--info-color); }}
        
        .summary-label {{
            color: #666;
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .charts-section {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .chart-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .chart-title {{
            font-size: 1.2rem;
            color: var(--dark-color);
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--light-color);
        }}
        
        .progress-section {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .progress-bar-container {{
            background: var(--light-color);
            border-radius: 10px;
            height: 30px;
            overflow: hidden;
            display: flex;
        }}
        
        .progress-bar {{
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 0.85rem;
            transition: width 0.5s ease;
        }}
        
        .progress-bar.passed {{ background: var(--success-color); }}
        .progress-bar.failed {{ background: var(--danger-color); }}
        .progress-bar.errors {{ background: var(--warning-color); }}
        .progress-bar.skipped {{ background: var(--info-color); }}
        
        .progress-legend {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 15px;
            flex-wrap: wrap;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .legend-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}
        
        .legend-dot.passed {{ background: var(--success-color); }}
        .legend-dot.failed {{ background: var(--danger-color); }}
        .legend-dot.errors {{ background: var(--warning-color); }}
        .legend-dot.skipped {{ background: var(--info-color); }}
        
        .suite-section {{
            background: white;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .suite-header {{
            padding: 20px 25px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .suite-header:hover {{
            opacity: 0.95;
        }}
        
        .suite-name {{
            font-size: 1.3rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .suite-name::before {{
            content: '📁';
        }}
        
        .suite-stats {{
            display: flex;
            gap: 15px;
        }}
        
        .suite-stat {{
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
        }}
        
        .suite-stat.passed {{ background: var(--success-color); }}
        .suite-stat.failed {{ background: var(--danger-color); }}
        .suite-stat.errors {{ background: var(--warning-color); color: #333; }}
        
        .suite-content {{
            padding: 0;
        }}
        
        .test-case {{
            padding: 15px 25px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            gap: 15px;
            transition: background 0.2s ease;
        }}
        
        .test-case:last-child {{
            border-bottom: none;
        }}
        
        .test-case:hover {{
            background: var(--light-color);
        }}
        
        .test-status {{
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
            flex-shrink: 0;
        }}
        
        .test-status.passed {{ background: #d4edda; color: var(--success-color); }}
        .test-status.failed {{ background: #f8d7da; color: var(--danger-color); }}
        .test-status.error {{ background: #fff3cd; color: #856404; }}
        .test-status.skipped {{ background: #d1ecf1; color: var(--info-color); }}
        
        .test-info {{
            flex: 1;
        }}
        
        .test-name {{
            font-weight: 600;
            color: var(--dark-color);
            margin-bottom: 3px;
        }}
        
        .test-description {{
            font-size: 0.9rem;
            color: #666;
        }}
        
        .test-duration {{
            font-size: 0.85rem;
            color: #999;
            white-space: nowrap;
        }}
        
        .test-details {{
            margin-top: 10px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid var(--danger-color);
            display: none;
        }}
        
        .test-case.expanded .test-details {{
            display: block;
        }}
        
        .test-details pre {{
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'Consolas', monospace;
            font-size: 0.85rem;
            color: #333;
        }}
        
        .test-details-toggle {{
            background: none;
            border: none;
            color: var(--primary-color);
            cursor: pointer;
            font-size: 0.85rem;
            padding: 5px 10px;
        }}
        
        .test-details-toggle:hover {{
            text-decoration: underline;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: rgba(255,255,255,0.8);
        }}
        
        .footer a {{
            color: white;
        }}
        
        @media (max-width: 768px) {{
            .summary-section {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .charts-section {{
                grid-template-columns: 1fr;
            }}
            
            .suite-header {{
                flex-direction: column;
                gap: 10px;
            }}
            
            .test-case {{
                flex-wrap: wrap;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="report-header">
            <h1 class="report-title">{self.title}</h1>
            <div class="report-meta">
                <span>📅 生成时间: {timestamp}</span>
                <span>⏱️ 总耗时: {total_duration:.3f}秒</span>
                <span>📈 通过率: {pass_rate:.1f}%</span>
            </div>
        </header>
        
        <section class="summary-section">
            <div class="summary-card total">
                <div class="summary-number">{total}</div>
                <div class="summary-label">总测试数</div>
            </div>
            <div class="summary-card passed">
                <div class="summary-number">{passed}</div>
                <div class="summary-label">通过</div>
            </div>
            <div class="summary-card failed">
                <div class="summary-number">{failed}</div>
                <div class="summary-label">失败</div>
            </div>
            <div class="summary-card errors">
                <div class="summary-number">{errors}</div>
                <div class="summary-label">错误</div>
            </div>
            <div class="summary-card skipped">
                <div class="summary-number">{skipped}</div>
                <div class="summary-label">跳过</div>
            </div>
        </section>
        
        <section class="progress-section">
            <h3 class="chart-title">测试执行进度</h3>
            <div class="progress-bar-container">
                {self._render_progress_bars(passed, failed, errors, skipped, total)}
            </div>
            <div class="progress-legend">
                <div class="legend-item"><span class="legend-dot passed"></span>通过 ({passed})</div>
                <div class="legend-item"><span class="legend-dot failed"></span>失败 ({failed})</div>
                <div class="legend-item"><span class="legend-dot errors"></span>错误 ({errors})</div>
                <div class="legend-item"><span class="legend-dot skipped"></span>跳过 ({skipped})</div>
            </div>
        </section>
        
        <section class="charts-section">
            <div class="chart-card">
                <h3 class="chart-title">测试结果分布</h3>
                <canvas id="resultChart"></canvas>
            </div>
            <div class="chart-card">
                <h3 class="chart-title">各模块测试情况</h3>
                <canvas id="suiteChart"></canvas>
            </div>
        </section>
        
        <section class="test-suites">
            <h2 style="color: white; margin-bottom: 20px; font-size: 1.5rem;">📋 详细测试结果</h2>
            {suites_html}
        </section>
        
        <footer class="footer">
            <p>DSL智能Agent系统 - 自动化测试报告</p>
            <p>2025 程序设计实践课程大作业</p>
        </footer>
    </div>
    
    <script>
        // 结果分布饼图
        const resultCtx = document.getElementById('resultChart').getContext('2d');
        new Chart(resultCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['通过', '失败', '错误', '跳过'],
                datasets: [{{
                    data: [{passed}, {failed}, {errors}, {skipped}],
                    backgroundColor: ['#28a745', '#dc3545', '#ffc107', '#17a2b8'],
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }}
                }}
            }}
        }});
        
        // 各模块测试情况柱状图
        const suiteCtx = document.getElementById('suiteChart').getContext('2d');
        new Chart(suiteCtx, {{
            type: 'bar',
            data: {{
                labels: [{self._get_suite_labels()}],
                datasets: [
                    {{
                        label: '通过',
                        data: [{self._get_suite_data('passed')}],
                        backgroundColor: '#28a745'
                    }},
                    {{
                        label: '失败',
                        data: [{self._get_suite_data('failed')}],
                        backgroundColor: '#dc3545'
                    }},
                    {{
                        label: '错误',
                        data: [{self._get_suite_data('errors')}],
                        backgroundColor: '#ffc107'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                scales: {{
                    x: {{ stacked: true }},
                    y: {{ stacked: true, beginAtZero: true }}
                }},
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }}
                }}
            }}
        }});
        
        // 切换测试详情
        function toggleDetails(btn) {{
            const testCase = btn.closest('.test-case');
            testCase.classList.toggle('expanded');
            btn.textContent = testCase.classList.contains('expanded') ? '收起详情' : '查看详情';
        }}
        
        // 切换测试套件展开/折叠
        document.querySelectorAll('.suite-header').forEach(header => {{
            header.addEventListener('click', () => {{
                const content = header.nextElementSibling;
                content.style.display = content.style.display === 'none' ? 'block' : 'none';
            }});
        }});
    </script>
</body>
</html>'''
        return html
    
    def _render_progress_bars(self, passed, failed, errors, skipped, total) -> str:
        """渲染进度条"""
        if total == 0:
            return ''
        
        bars = []
        if passed > 0:
            pct = passed / total * 100
            bars.append(f'<div class="progress-bar passed" style="width: {pct}%">{passed}</div>')
        if failed > 0:
            pct = failed / total * 100
            bars.append(f'<div class="progress-bar failed" style="width: {pct}%">{failed}</div>')
        if errors > 0:
            pct = errors / total * 100
            bars.append(f'<div class="progress-bar errors" style="width: {pct}%">{errors}</div>')
        if skipped > 0:
            pct = skipped / total * 100
            bars.append(f'<div class="progress-bar skipped" style="width: {pct}%">{skipped}</div>')
        
        return ''.join(bars)
    
    def _render_suite(self, suite: TestSuiteResult) -> str:
        """渲染测试套件"""
        test_cases_html = ""
        for tc in suite.test_cases:
            test_cases_html += self._render_test_case(tc)
        
        stats_html = f'<span class="suite-stat passed">✓ {suite.passed}</span>'
        if suite.failed > 0:
            stats_html += f'<span class="suite-stat failed">✗ {suite.failed}</span>'
        if suite.errors > 0:
            stats_html += f'<span class="suite-stat errors">⚠ {suite.errors}</span>'
        
        return f'''
        <div class="suite-section">
            <div class="suite-header">
                <div class="suite-name">{suite.name}</div>
                <div class="suite-stats">{stats_html}</div>
            </div>
            <div class="suite-content">
                {test_cases_html}
            </div>
        </div>
        '''
    
    def _render_test_case(self, tc: TestCaseResult) -> str:
        """渲染测试用例"""
        status_icon = {
            'passed': '✓',
            'failed': '✗',
            'error': '⚠',
            'skipped': '⊘'
        }.get(tc.status, '?')
        
        status_class = tc.status if tc.status != 'error' else 'error'
        
        details_html = ""
        if tc.status in ('failed', 'error') and tc.traceback:
            escaped_tb = tc.traceback.replace('<', '&lt;').replace('>', '&gt;')
            details_html = f'''
            <button class="test-details-toggle" onclick="toggleDetails(this)">查看详情</button>
            <div class="test-details">
                <pre>{escaped_tb}</pre>
            </div>
            '''
        
        return f'''
        <div class="test-case">
            <div class="test-status {status_class}">{status_icon}</div>
            <div class="test-info">
                <div class="test-name">{tc.method_name}</div>
                <div class="test-description">{tc.description}</div>
                {details_html}
            </div>
            <div class="test-duration">{tc.duration*1000:.1f}ms</div>
        </div>
        '''
    
    def _get_suite_labels(self) -> str:
        """获取套件标签"""
        labels = [f"'{s.name.replace('Test', '')}'" for s in self.test_suites]
        return ', '.join(labels)
    
    def _get_suite_data(self, status: str) -> str:
        """获取套件数据"""
        if status == 'passed':
            data = [s.passed for s in self.test_suites]
        elif status == 'failed':
            data = [s.failed for s in self.test_suites]
        elif status == 'errors':
            data = [s.errors for s in self.test_suites]
        else:
            data = [s.skipped for s in self.test_suites]
        return ', '.join(map(str, data))


def run_tests_with_html_report(output_path: str = None):
    """运行测试并生成HTML报告"""
    # 测试目录
    test_dir = os.path.join(project_root, 'tests')
    
    # 发现测试
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern='test_*.py')
    
    # 创建结果收集器
    result = HTMLTestResult()
    
    # 运行测试
    print("正在运行测试...")
    suite.run(result)
    
    # 生成报告
    generator = HTMLReportGenerator()
    html_content = generator.generate_report(result)
    
    # 保存报告
    if output_path is None:
        output_path = os.path.join(project_root, 'tests', 'test_report.html')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # 打印摘要
    total = len(result.test_results)
    passed = sum(1 for r in result.test_results if r.status == 'passed')
    failed = sum(1 for r in result.test_results if r.status == 'failed')
    errors = sum(1 for r in result.test_results if r.status == 'error')
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    print(f"总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"错误: {errors}")
    print(f"通过率: {passed/total*100:.1f}%" if total > 0 else "通过率: N/A")
    print("=" * 60)
    print(f"HTML报告已生成: {output_path}")
    
    return result.wasSuccessful(), output_path


def main():
    """主函数"""
    # 确定输出路径
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    else:
        output_path = None
    
    success, report_path = run_tests_with_html_report(output_path)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())