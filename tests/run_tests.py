#!/usr/bin/env python3
"""
测试驱动 - 自动运行所有测试并生成报告
"""

import sys
import os
import unittest
import json
from datetime import datetime
from io import StringIO

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def discover_and_run_tests():
    """发现并运行所有测试"""
    # 测试目录
    test_dir = os.path.join(project_root, 'tests')
    
    # 发现测试
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern='test_*.py')
    
    # 捕获输出
    output = StringIO()
    
    # 运行测试
    runner = unittest.TextTestRunner(stream=output, verbosity=2)
    result = runner.run(suite)
    
    return result, output.getvalue()


def generate_report(result, output):
    """生成测试报告"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total': result.testsRun,
            'passed': result.testsRun - len(result.failures) - len(result.errors),
            'failed': len(result.failures),
            'errors': len(result.errors),
            'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0
        },
        'success': result.wasSuccessful(),
        'failures': [],
        'errors': []
    }
    
    # 记录失败
    for test, traceback in result.failures:
        report['failures'].append({
            'test': str(test),
            'traceback': traceback
        })
    
    # 记录错误
    for test, traceback in result.errors:
        report['errors'].append({
            'test': str(test),
            'traceback': traceback
        })
    
    return report


def print_summary(report):
    """打印测试摘要"""
    print("\n" + "=" * 60)
    print("测试报告摘要")
    print("=" * 60)
    print(f"时间: {report['timestamp']}")
    print(f"总测试数: {report['summary']['total']}")
    print(f"通过: {report['summary']['passed']}")
    print(f"失败: {report['summary']['failed']}")
    print(f"错误: {report['summary']['errors']}")
    print(f"跳过: {report['summary']['skipped']}")
    print("-" * 60)
    
    if report['success']:
        print("✅ 所有测试通过!")
    else:
        print("❌ 存在失败的测试")
        
        if report['failures']:
            print("\n失败的测试:")
            for failure in report['failures']:
                print(f"  - {failure['test']}")
        
        if report['errors']:
            print("\n出错的测试:")
            for error in report['errors']:
                print(f"  - {error['test']}")
    
    print("=" * 60)


def save_report(report, filename='test_report.json'):
    """保存测试报告到文件"""
    report_path = os.path.join(project_root, 'tests', filename)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n测试报告已保存到: {report_path}")


def main():
    """主函数"""
    print("开始运行测试...")
    print("=" * 60)
    
    # 运行测试
    result, output = discover_and_run_tests()
    
    # 打印详细输出
    print(output)
    
    # 生成报告
    report = generate_report(result, output)
    
    # 打印摘要
    print_summary(report)
    
    # 保存报告
    save_report(report)
    
    # 返回状态码
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
