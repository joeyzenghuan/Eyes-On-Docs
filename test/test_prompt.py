#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试文件：测试git commit patch data到Teams notification的转换流程
用户可以指定特定的commit_url来测试每个步骤的生成内容
"""

import sys
import os
import json
import datetime
from dotenv import load_dotenv

# 添加父目录到路径，以便导入项目模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from commit_fetch import CommitFetcher
from call_gpt import CallGPT
from teams_notifier import TeamsNotifier
from logs import logger
import toml

load_dotenv(override=True)  # 允许覆盖环境变量

class CommitTester(CommitFetcher, CallGPT, TeamsNotifier):
    def __init__(self):
        self.headers = {"Authorization": "token " + os.getenv("PERSONAL_TOKEN", "")}
        self.max_input_token = 30000
        
        # 加载系统提示词
        self.system_prompts = self.load_system_prompts()
        
    def load_system_prompts(self):
        """加载系统提示词"""
        try:
            # 获取项目根目录路径
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            prompts_path = os.path.join(project_root, 'prompts.toml')
            
            with open(prompts_path, 'r', encoding='utf-8') as f:
                data = toml.load(f)
            
            default_prompt = {
                "GPT_SUMMARY_PROMPT": "gpt_summary_prompt_v2",
                "GPT_TITLE_PROMPT": "gpt_title_prompt_v4",
                "GPT_SIMILARITY_PROMPT": "gpt_similarity_prompt_v1",
                "GPT_WEEKLY_SUMMARY_PROMPT": "gpt_weekly_summary_prompt_v1"
            }
            
            system_prompt = {}
            for k, v in default_prompt.items():
                system_prompt[k] = data[v]['prompt']
                
            return system_prompt
        except Exception as e:
            logger.error(f"Failed to load prompts: {e}")
            return {}

    def test_commit_processing(self, commit_url, language="Chinese", url_mapping=None):
        """
        测试完整的commit处理流程
        
        Args:
            commit_url: GitHub commit URL (支持两种格式)
                       - HTML格式: https://github.com/MicrosoftDocs/azure-docs/commit/abc123
                       - API格式: https://api.github.com/repos/MicrosoftDocs/azure-docs/commits/abc123
            language: 输出语言，默认为中文
            url_mapping: URL映射字典，用于链接修正
        """
        print("=" * 80)
        print(f"开始测试 Commit URL: {commit_url}")
        print("=" * 80)
        
        # 转换URL格式（如果是HTML格式，转换为API格式）
        if "github.com" in commit_url and "/commit/" in commit_url:
            api_url = commit_url.replace("https://github.com", "https://api.github.com/repos").replace("/commit/", "/commits/")
        else:
            api_url = commit_url
            
        # 转换为HTML格式用于显示
        html_url = api_url.replace("https://api.github.com/repos", "https://github.com").replace("/commits/", "/commit/")
        
        print(f"API URL: {api_url}")
        print(f"HTML URL: {html_url}")
        print()
        
        try:
            # 步骤1: 获取patch数据
            print("步骤1: 获取 Commit Patch 数据")
            print("-" * 40)
            
            current_time = datetime.datetime.now()
            commit_patch_data = self.get_change_from_each_url(current_time, api_url, self.max_input_token, self.headers)
            
            if commit_patch_data == "Error":
                print("❌ 获取patch数据失败")
                return
                
            print(f"✅ 成功获取patch数据 (长度: {len(commit_patch_data)} 字符)")
            print(f"Patch数据预览:\n{commit_patch_data[:500]}...")
            print()
            
            # 步骤2: GPT生成摘要
            print("步骤2: GPT 生成摘要")
            print("-" * 40)
            
            gpt_summary, gpt_summary_tokens, processed_patch_data = self.gpt_summary(
                commit_patch_data, language, self.system_prompts["GPT_SUMMARY_PROMPT"], url_mapping
            )
            
            if gpt_summary:
                print(f"✅ GPT摘要生成成功")
                print(f"Token使用情况: {gpt_summary_tokens}")
                print(f"生成的摘要:\n{gpt_summary}")
            else:
                print("❌ GPT摘要生成失败")
                return
            print()
            
            # 步骤3: GPT生成标题
            print("步骤3: GPT 生成标题")
            print("-" * 40)
            
            gpt_title, gpt_title_tokens = self.gpt_title(
                gpt_summary, language, self.system_prompts["GPT_TITLE_PROMPT"]
            )
            
            if gpt_title:
                print(f"✅ GPT标题生成成功")
                print(f"Token使用情况: {gpt_title_tokens}")
                print(f"生成的标题: {gpt_title}")
                
                # 步骤4: 判断重要性
                print("\n步骤4: 判断重要性")
                print("-" * 40)
                
                if gpt_title.startswith('0 '):
                    status = 'skip'
                    print(f"⚠️  判断结果: 跳过 (不重要的更改)")
                    print(f"原因: 标题以'0'开头，表示这是一个不重要的更改")
                else:
                    status = 'post'
                    print(f"✅ 判断结果: 发送通知 (重要更改)")
                    clean_title = gpt_title[2:] if gpt_title.startswith(('0 ', '1 ')) else gpt_title
                    print(f"清理后的标题: {clean_title}")
                    
                    # 步骤5: 生成Teams消息格式
                    print("\n步骤5: 生成 Teams 消息格式")
                    print("-" * 40)
                    
                    teams_message_data = {
                        "@type": "MessageCard",
                        "themeColor": "0076D7",
                        "title": clean_title,
                        "text": str(current_time) + "\n\n" + str(gpt_summary),
                        "potentialAction": [{
                            "@type": "OpenUri",
                            "name": "Go to commit page",
                            "targets": [{"os": "default", "uri": html_url}],
                        }],
                    }
                    
                    print("✅ Teams消息格式生成成功")
                    print("Teams消息JSON:")
                    print(json.dumps(teams_message_data, indent=2, ensure_ascii=False))
                    
            else:
                print("❌ GPT标题生成失败")
                return
                
        except Exception as e:
            logger.exception(f"测试过程中发生错误: {e}")
            print(f"❌ 测试失败: {e}")
            
        print("\n" + "=" * 80)
        print("测试完成")
        print("=" * 80)

    def test_with_teams_webhook(self, commit_url, teams_webhook_url, language="Chinese", url_mapping=None):
        """
        测试完整流程并实际发送到Teams
        
        Args:
            commit_url: GitHub commit URL
            teams_webhook_url: Teams webhook URL
            language: 输出语言
            url_mapping: URL映射字典
        """
        print("⚠️  警告: 这将实际发送消息到Teams频道!")
        confirm = input("确认继续? (y/N): ")
        if confirm.lower() != 'y':
            print("已取消")
            return
            
        # 先运行测试流程
        self.test_commit_processing(commit_url, language, url_mapping)
        
        # 然后实际发送到Teams
        print("\n步骤6: 发送到 Teams")
        print("-" * 40)
        
        try:
            # 重新获取数据（简化版）
            api_url = commit_url.replace("https://github.com", "https://api.github.com/repos").replace("/commit/", "/commits/") if "github.com" in commit_url else commit_url
            html_url = api_url.replace("https://api.github.com/repos", "https://github.com").replace("/commits/", "/commit/")
            
            current_time = datetime.datetime.now()
            commit_patch_data = self.get_change_from_each_url(current_time, api_url, self.max_input_token, self.headers)
            gpt_summary, _, _ = self.gpt_summary(commit_patch_data, language, self.system_prompts["GPT_SUMMARY_PROMPT"], url_mapping)
            gpt_title, _ = self.gpt_title(gpt_summary, language, self.system_prompts["GPT_TITLE_PROMPT"])
            
            if gpt_title and not gpt_title.startswith('0 '):
                clean_title = gpt_title[2:] if gpt_title.startswith(('0 ', '1 ')) else gpt_title
                teams_message_jsondata, post_status, error_message = self.post_teams_message(
                    clean_title, current_time, gpt_summary, teams_webhook_url, html_url
                )
                
                if post_status == "success":
                    print("✅ 成功发送到Teams!")
                else:
                    print(f"❌ 发送失败: {error_message}")
            else:
                print("⚠️  根据重要性判断，此commit不会发送通知")
                
        except Exception as e:
            print(f"❌ 发送到Teams时发生错误: {e}")


def main():
    """主函数：提供交互式测试界面"""
    tester = CommitTester()
    
    print("Git Commit Patch Data 到 Teams Notification 转换测试工具")
    print("=" * 60)
    
    while True:
        print("\n请选择测试模式:")
        print("1. 测试处理流程 (不发送到Teams)")
        print("2. 测试并发送到Teams")
        print("3. 退出")
        
        choice = input("\n请输入选择 (1-3): ").strip()
        
        if choice == '3':
            print("再见!")
            break
            
        if choice not in ['1', '2']:
            print("无效选择，请重新输入")
            continue
            
        # 获取commit URL
        print("\n请输入commit URL (支持两种格式):")
        print("- HTML格式: https://github.com/MicrosoftDocs/azure-docs/commit/abc123")
        print("- API格式: https://api.github.com/repos/MicrosoftDocs/azure-docs/commits/abc123")
        
        commit_url = input("Commit URL: ").strip()
        if not commit_url:
            print("URL不能为空")
            continue
            
        # 获取语言设置
        language = input("输出语言 (Chinese/English, 默认Chinese): ").strip() or "Chinese"
        
        # 获取URL映射（可选）
        print("\nURL映射设置 (可选，用于链接修正):")
        print("格式: old_path1->new_url1,old_path2->new_url2")
        print("示例: articles/->https://learn.microsoft.com/zh-cn/azure/")
        url_mapping_input = input("URL映射 (留空跳过): ").strip()
        
        url_mapping = None
        if url_mapping_input:
            try:
                url_mapping = {}
                for mapping in url_mapping_input.split(','):
                    old, new = mapping.split('->')
                    url_mapping[old.strip()] = new.strip()
            except:
                print("URL映射格式错误，将忽略")
                url_mapping = None
        
        if choice == '1':
            # 仅测试处理流程
            tester.test_commit_processing(commit_url, language, url_mapping)
            
        elif choice == '2':
            # 测试并发送到Teams
            teams_webhook_url = input("\nTeams Webhook URL: ").strip()
            if not teams_webhook_url:
                print("Teams Webhook URL不能为空")
                continue
            tester.test_with_teams_webhook(commit_url, teams_webhook_url, language, url_mapping)


if __name__ == "__main__":
    main()
