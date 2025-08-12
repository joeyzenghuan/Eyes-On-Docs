# GPT分析模式功能说明

## 概述

项目现在支持两种GPT分析模式：
- **Legacy模式**：传统的两次API调用模式（生成摘要 → 生成标题）
- **Structured模式**：新的一次API调用模式（使用OpenAI structured output同时生成摘要和标题）

## 配置方式

在 `target_config.json` 中添加 `gpt_analysis_mode` 字段：

```json
{
  "topic_name": "Azure OpenAI",
  "root_commits_url": "https://api.github.com/repos/MicrosoftDocs/azure-docs/commits?path=articles/ai-services/openai/",
  "language": "Chinese",
  "teams_webhook_url": "https://microsoft.webhook.office.com/webhookb2/***",
  "gpt_analysis_mode": "structured",  // "legacy" 或 "structured"
  "GPT_STRUCTURED_PROMPT": "gpt_structured_prompt_v1"  // 仅在structured模式下需要
}
```

## 模式对比

### Legacy模式（默认）
- **API调用次数**：2次（摘要 + 标题）
- **优点**：经过验证的稳定逻辑
- **缺点**：调用次数多，成本较高，摘要和标题可能不够一致

### Structured模式（新增）
- **API调用次数**：1次（同时生成摘要、标题、重要性判断）
- **优点**：
  - 50%的API调用减少
  - 更低的成本和延迟
  - 摘要和标题在同一上下文中生成，逻辑更一致
  - 结构化输出，更容易扩展新字段
- **缺点**：依赖较新的OpenAI功能

## 兼容性保证

1. **向后兼容**：不配置 `gpt_analysis_mode` 时默认使用legacy模式
2. **无缝切换**：两种模式的输出格式完全一致
3. **自动降级**：structured模式失败时自动fallback到legacy模式
4. **混合部署**：不同topic可以使用不同模式

## Structured Output Schema

新模式返回的JSON结构：

```json
{
  "summary": "详细的更新内容摘要...",
  "title": "[功能更新] Azure OpenAI 新增GPT-4o模型支持",  // 不包含数字前缀
  "importance_score": 1,  // 1=重要需通知, 0=不重要跳过
  "importance_score_reasoning": "新增重要功能，影响用户使用体验"
}
```

### 数据库存储

在 CosmosDB 中，structured 模式会额外保存以下字段：
- `importance_score`: 重要性评分 (0 或 1)
- `importance_score_reasoning`: 重要性判断的详细理由

这些额外信息有助于：
- 分析模型的判断准确性
- 调优 AI 模型的判断逻辑
- 提供决策过程的可追溯性

### 设计优势

- **更清晰的分离**：标题专注于内容描述，重要性判断通过 `importance_score` 字段
- **更高效的处理**：直接使用 `importance_score` 判断状态，无需额外的字符串解析
- **更好的扩展性**：JSON结构化数据便于添加更多字段

## 提示词配置

在 `prompts.toml` 中配置structured模式的提示词：

```toml
[gpt_structured_prompt_v1]
prompt = """
You are a professional technical documentation analyst...
[详细的提示词内容]
"""
```

## 使用建议

1. **新部署**：建议使用structured模式获得更好的性能
2. **现有部署**：可以逐步迁移，先在测试环境验证
3. **A/B测试**：可以为同一主题配置两个entry分别使用不同模式进行对比
4. **监控指标**：注意观察两种模式的token消耗和响应质量

## 故障排查

1. **Structured模式失败**：会自动fallback到legacy模式，检查日志中的异常信息
2. **JSON解析错误**：检查OpenAI API版本是否支持structured output
3. **提示词问题**：确保提示词符合structured output的要求

## 迁移示例

### 当前配置（Legacy）
```json
{
  "topic_name": "Azure OpenAI",
  "gpt_analysis_mode": "legacy"  // 或不配置此字段
}
```

### 迁移到Structured
```json
{
  "topic_name": "Azure OpenAI", 
  "gpt_analysis_mode": "structured",
  "GPT_STRUCTURED_PROMPT": "gpt_structured_prompt_v1"
}
```

这种设计确保了系统的稳定性和灵活性，用户可以根据自己的需求选择合适的模式。
