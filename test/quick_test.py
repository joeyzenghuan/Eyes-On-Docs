#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试脚本：用于命令行快速测试特定commit的处理流程
用法: python quick_test.py <commit_url> [language] [--send-teams webhook_url]
"""

import sys
import os
import argparse

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_prompt import CommitTester

def main():
    parser = argparse.ArgumentParser(description='快速测试git commit处理流程')
    parser.add_argument('commit_url', help='GitHub commit URL')
    parser.add_argument('--language', '-l', default='Chinese', choices=['Chinese', 'English'], 
                       help='输出语言 (默认: Chinese)')
    parser.add_argument('--send-teams', '-t', metavar='WEBHOOK_URL', 
                       help='Teams webhook URL (如果提供，将实际发送消息到Teams)')
    parser.add_argument('--url-mapping', '-m', 
                       help='URL映射，格式: old1->new1,old2->new2')
    
    args = parser.parse_args()
    
    # 解析URL映射
    url_mapping = None
    if args.url_mapping:
        try:
            url_mapping = {}
            for mapping in args.url_mapping.split(','):
                old, new = mapping.split('->')
                url_mapping[old.strip()] = new.strip()
        except:
            print("❌ URL映射格式错误，将忽略")
            url_mapping = None
    
    # 创建测试器
    tester = CommitTester()
    
    print(f"🚀 快速测试 Commit: {args.commit_url}")
    print(f"📝 语言: {args.language}")
    if url_mapping:
        print(f"🔗 URL映射: {url_mapping}")
    print()
    
    if args.send_teams:
        print("⚠️  将发送消息到Teams!")
        tester.test_with_teams_webhook(args.commit_url, args.send_teams, args.language, url_mapping)
    else:
        tester.test_commit_processing(args.commit_url, args.language, url_mapping)

if __name__ == "__main__":
    main() 