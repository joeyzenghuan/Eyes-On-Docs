#!/usr/bin/env python3
"""
单独测试脚本：复现JSON截断问题

此脚本用于复现特定commit导致的JSON解析错误：
- Commit: e126b9c4ee254b4ecaf72b12603bd34ea5bc1644
- 问题：GPT返回的JSON响应被截断，导致JSON解析失败
"""

import os
import sys
import json
import datetime
import toml
from dotenv import load_dotenv

# 添加父目录到路径，以便导入本地模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logs import logger
from commit_fetch import CommitFetcher
from call_gpt import CallGPT

# 加载环境变量
load_dotenv(override=True)
PERSONAL_TOKEN = os.getenv("PERSONAL_TOKEN")

class JsonTruncationTester(CommitFetcher, CallGPT):
    """
    JSON截断问题复现测试器
    """
    
    def __init__(self):
        self.headers = {"Authorization": "token " + PERSONAL_TOKEN}
        self.topic_path = "articles/ai-foundry"  # 设置主题路径过滤
        self.max_input_token = 30000
        self.language = "Chinese"
        
        # 加载生产环境使用的system prompts
        self.system_prompts = self.load_production_prompts()
    
    def load_production_prompts(self):
        """加载生产环境使用的system prompts"""
        try:
            # 获取父目录中的prompts.toml文件路径
            prompts_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'prompts.toml')
            with open(prompts_file, 'r') as f:  
                data = toml.load(f)
                
            # 生产环境使用的默认prompt配置（来自eyes_on_docs.py）
            default_prompt = {
                "GPT_SUMMARY_PROMPT": "gpt_summary_prompt_v2",  
                "GPT_TITLE_PROMPT": "gpt_title_prompt_v4",  
                "GPT_SIMILARITY_PROMPT": "gpt_similarity_prompt_v1",  
                "GPT_WEEKLY_SUMMARY_PROMPT": "gpt_weekly_summary_prompt_v1",
                "GPT_STRUCTURED_PROMPT": "gpt_structured_prompt_v1"  # 结构化输出prompt
            }
            
            # 将prompt键名映射到实际的prompt内容
            system_prompt = {}
            for k, v in default_prompt.items():
                system_prompt[k] = data[v]['prompt']
            
            logger.info("✅ 成功加载生产环境system prompts")
            logger.info(f"包含的prompt类型: {list(system_prompt.keys())}")
            
            return system_prompt
            
        except Exception as e:
            logger.error(f"❌ 加载生产环境prompts失败: {e}")
            # 回退到简化版本
            return {
                "GPT_STRUCTURED_PROMPT": """Analyze the contents from a git commit patch data and summarize the contents of the commit.
If the commit contains multiple files, please separate them into different items.
Please reply in the requested language."""
            }
    
    def test_problematic_commit(self, max_tokens=1000):
        """
        测试导致JSON截断的特定commit
        
        Args:
            max_tokens (int): GPT响应的最大token数，默认1000（原始出错值）
        """
        # 出问题的commit URL
        commit_url = "https://api.github.com/repos/MicrosoftDocs/azure-ai-docs/commits/e126b9c4ee254b4ecaf72b12603bd34ea5bc1644"
        commit_time = datetime.datetime(2025, 9, 5, 14, 46, 11)  # 从日志中获取的时间
        
        logger.info(f"Testing commit: {commit_url}")
        logger.info(f"Testing with max_tokens: {max_tokens}")
        logger.info("=" * 80)
        
        try:
            # 1. 获取commit的patch数据
            logger.info("Step 1: 获取commit patch数据...")
            commit_patch_data = self.get_change_from_each_url(
                commit_time, 
                commit_url, 
                self.max_input_token, 
                self.headers
            )
            
            logger.info(f"Patch数据长度: {len(commit_patch_data)} 字符")
            logger.info(f"Patch数据预览:\n{commit_patch_data[:500]}...")
            logger.info("=" * 80)
            
            # 2. 调用GPT进行结构化分析（使用原始的max_tokens值来复现问题）
            logger.info("Step 2: 调用GPT进行结构化分析...")
            result = self.test_gpt_structured_response(commit_patch_data, max_tokens)
            
            if result:
                logger.info("✅ 测试成功完成！")
                return result
            else:
                logger.error("❌ 测试失败 - 复现了JSON截断问题")
                return None
                
        except Exception as e:
            logger.exception(f"❌ 测试过程中发生异常: {e}")
            return None
    
    def test_gpt_structured_response(self, commit_patch_data, max_tokens):
        """
        测试GPT结构化响应，模拟原始的调用方式
        
        Args:
            commit_patch_data (str): commit的patch数据
            max_tokens (int): GPT响应的最大token数
            
        Returns:
            dict or None: 解析成功返回结构化数据，失败返回None
        """
        try:
            # 构建结构化响应格式（与原始代码相同）
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "commit_analysis",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "summary": {"type": "string"},
                            "title": {"type": "string"},
                            "importance_score": {"type": "integer"},
                            "importance_score_reasoning": {"type": "string"}
                        },
                        "required": ["summary", "title", "importance_score", "importance_score_reasoning"],
                        "additionalProperties": False
                    }
                }
            }
            
            # 构建消息（与原始代码相同）
            system_message = f"{self.system_prompts['GPT_STRUCTURED_PROMPT']} Reply in {self.language}."
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Here are the commit patch data. #####{commit_patch_data} ##### Reply in {self.language}"},
            ]
            
            logger.debug(f"GPT请求消息: {messages}")
            
            # 调用GPT（使用指定的max_tokens来复现问题）
            from gpt_reply import get_gpt_structured_response
            structured_response, prompt_tokens, completion_tokens, total_tokens = get_gpt_structured_response(
                messages, response_format, max_tokens=max_tokens
            )
            
            if structured_response is None:
                logger.error("❌ GPT返回了None - 复现了JSON截断问题！")
                return None
            
            # 如果成功，记录结果
            logger.info("✅ GPT结构化响应成功解析:")
            logger.info(f"Summary: {structured_response.get('summary', 'N/A')}")
            logger.info(f"Title: {structured_response.get('title', 'N/A')}")
            logger.info(f"Importance Score: {structured_response.get('importance_score', 'N/A')}")
            logger.info(f"Token使用: Prompt {prompt_tokens}, Completion {completion_tokens}, Total {total_tokens}")
            
            return structured_response
            
        except Exception as e:
            logger.exception(f"❌ GPT结构化响应失败: {e}")
            return None
    
    def run_comparison_test(self):
        """
        运行对比测试：使用不同的max_tokens值进行测试
        """
        logger.info("🧪 开始JSON截断问题对比测试")
        logger.info("=" * 80)
        
        # 测试不同的max_tokens值
        test_cases = [
            ("原始值（会导致截断）", 1000),
            ("修复值1", 2000),
            ("修复值2", 3000),
        ]
        
        results = {}
        
        for test_name, max_tokens in test_cases:
            logger.info(f"\n🔍 测试案例: {test_name} (max_tokens={max_tokens})")
            logger.info("-" * 60)
            
            result = self.test_problematic_commit(max_tokens)
            results[test_name] = {
                "max_tokens": max_tokens,
                "success": result is not None,
                "result": result
            }
            
            if result:
                logger.info(f"✅ {test_name}: 成功")
            else:
                logger.info(f"❌ {test_name}: 失败（JSON截断）")
        
        # 总结测试结果
        logger.info("\n" + "=" * 80)
        logger.info("📊 测试结果总结:")
        for test_name, result_info in results.items():
            status = "✅ 成功" if result_info["success"] else "❌ 失败"
            logger.info(f"{test_name} (max_tokens={result_info['max_tokens']}): {status}")
        
        return results


def main():
    """
    主函数：运行JSON截断问题复现测试
    """
    logger.info("🚀 启动JSON截断问题复现测试")
    
    try:
        tester = JsonTruncationTester()
        
        # 直接运行对比测试（不需要用户输入）
        logger.info("📝 运行对比测试模式")
        results = tester.run_comparison_test()
        
        # 显示简洁的结果
        print("\n📊 测试结果:")
        for test_name, info in results.items():
            status = "✅" if info["success"] else "❌"
            print(f"{status} {test_name}: max_tokens={info['max_tokens']}")
            
    except KeyboardInterrupt:
        logger.info("⏹️  用户中断测试")
    except Exception as e:
        logger.exception(f"❌ 测试过程中发生未预期的错误: {e}")


if __name__ == "__main__":
    main()
