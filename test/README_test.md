# Git Commit Patch Data 到 Teams Notification 转换测试工具

这个测试工具允许你指定特定的commit URL来测试整个git commit patch data到Teams notification的转换流程。

## 功能特性

- 🔍 **完整流程测试**: 测试从git commit patch获取到Teams消息生成的每个步骤
- 📊 **详细输出**: 显示每个步骤的处理结果和token使用情况
- 🌐 **多语言支持**: 支持中文和英文输出
- 🔗 **URL映射**: 支持自定义URL映射规则
- 📤 **Teams集成**: 可选择实际发送消息到Teams频道
- ⚡ **快速测试**: 提供命令行快速测试模式

## 使用方法

### 方式1: 交互式测试 (推荐)

#### 1. 环境准备

确保你已经设置了必要的环境变量：

```bash
# 在项目根目录的 .env 文件中设置
PERSONAL_TOKEN=your_github_personal_access_token
```

#### 2. 运行测试工具

```bash
cd test
python test_prompt.py
```

#### 3. 交互式使用

运行后会看到菜单：

```
Git Commit Patch Data 到 Teams Notification 转换测试工具
============================================================

请选择测试模式:
1. 测试处理流程 (不发送到Teams)
2. 测试并发送到Teams
3. 退出
```

### 方式2: 命令行快速测试

对于快速测试单个commit，可以使用命令行模式：

```bash
cd test

# 基本测试
python quick_test.py "https://github.com/MicrosoftDocs/azure-docs/commit/abc123"

# 指定语言
python quick_test.py "https://github.com/MicrosoftDocs/azure-docs/commit/abc123" --language English

# 使用URL映射
python quick_test.py "https://github.com/MicrosoftDocs/azure-docs/commit/abc123" \
  --url-mapping "articles/->https://learn.microsoft.com/zh-cn/azure/"

# 测试并发送到Teams
python quick_test.py "https://github.com/MicrosoftDocs/azure-docs/commit/abc123" \
  --send-teams "https://outlook.office.com/webhook/your-webhook-url"

# 完整示例
python quick_test.py "https://github.com/MicrosoftDocs/azure-docs/commit/abc123" \
  --language Chinese \
  --url-mapping "articles/->https://learn.microsoft.com/zh-cn/azure/,includes/->https://learn.microsoft.com/zh-cn/azure/includes/" \
  --send-teams "https://outlook.office.com/webhook/your-webhook-url"
```

#### 命令行参数说明

- `commit_url`: GitHub commit URL (必需)
- `--language, -l`: 输出语言 (Chinese/English，默认Chinese)
- `--send-teams, -t`: Teams webhook URL (可选，如果提供将实际发送消息)
- `--url-mapping, -m`: URL映射规则 (可选，格式: old1->new1,old2->new2)

### 4. 输入参数详解

#### Commit URL
支持两种格式：
- **HTML格式**: `https://github.com/MicrosoftDocs/azure-docs/commit/abc123def456`
- **API格式**: `https://api.github.com/repos/MicrosoftDocs/azure-docs/commits/abc123def456`

#### 语言设置
- `Chinese` (默认)
- `English`

#### URL映射 (可选)
用于修正生成摘要中的链接，格式：
```
old_path1->new_url1,old_path2->new_url2
```

示例：
```
articles/->https://learn.microsoft.com/zh-cn/azure/,includes/->https://learn.microsoft.com/zh-cn/azure/includes/
```

## 测试流程说明

### 步骤1: 获取 Commit Patch 数据
- 从GitHub API获取commit的详细信息
- 提取patch数据（文件变更内容）
- 显示patch数据的长度和预览

### 步骤2: GPT 生成摘要
- 使用GPT分析patch数据
- 生成人类可读的变更摘要
- 应用URL映射规则修正链接
- 显示token使用情况

### 步骤3: GPT 生成标题
- 基于摘要生成标题
- 格式：`0/1 [标签] 标题`
- 显示token使用情况

### 步骤4: 判断重要性
- 根据标题开头的数字判断重要性
- `0`: 不重要的更改（如拼写错误、格式调整）
- `1`: 重要更改（需要发送通知）

### 步骤5: 生成 Teams 消息格式
- 将处理结果转换为Teams MessageCard格式
- 包含标题、摘要、时间戳和commit链接
- 显示完整的JSON格式

### 步骤6: 发送到 Teams (可选)
- 实际发送消息到指定的Teams webhook
- 需要用户确认才会执行

## 示例输出

```
================================================================================
开始测试 Commit URL: https://github.com/MicrosoftDocs/azure-docs/commit/abc123
================================================================================
API URL: https://api.github.com/repos/MicrosoftDocs/azure-docs/commits/abc123
HTML URL: https://github.com/MicrosoftDocs/azure-docs/commit/abc123

步骤1: 获取 Commit Patch 数据
----------------------------------------
✅ 成功获取patch数据 (长度: 1234 字符)
Patch数据预览:
Original Path:articles/ai-services/openai/concepts/models.md
@@ -10,7 +10,7 @@ ms.date: 11/06/2024
 
 # Azure OpenAI Service models
 
-Azure OpenAI Service is powered by a diverse set of models with different capabilities and price points.
+Azure OpenAI Service is powered by a diverse set of models with different capabilities and pricing options.
...

步骤2: GPT 生成摘要
----------------------------------------
✅ GPT摘要生成成功
Token使用情况: {'prompt': 156, 'completion': 89, 'total': 245}
生成的摘要:
https://learn.microsoft.com/zh-cn/azure/ai-services/openai/concepts/models

更新了Azure OpenAI服务模型概述页面，将"price points"改为"pricing options"，使表述更加准确和专业。

步骤3: GPT 生成标题
----------------------------------------
✅ GPT标题生成成功
Token使用情况: {'prompt': 234, 'completion': 23, 'total': 257}
生成的标题: 1 [文本] 更新Azure OpenAI模型定价描述

步骤4: 判断重要性
----------------------------------------
✅ 判断结果: 发送通知 (重要更改)
清理后的标题: [文本] 更新Azure OpenAI模型定价描述

步骤5: 生成 Teams 消息格式
----------------------------------------
✅ Teams消息格式生成成功
Teams消息JSON:
{
  "@type": "MessageCard",
  "themeColor": "0076D7",
  "title": "[文本] 更新Azure OpenAI模型定价描述",
  "text": "2024-01-15 10:30:45.123456\n\nhttps://learn.microsoft.com/zh-cn/azure/ai-services/openai/concepts/models\n\n更新了Azure OpenAI服务模型概述页面，将\"price points\"改为\"pricing options\"，使表述更加准确和专业。",
  "potentialAction": [
    {
      "@type": "OpenUri",
      "name": "Go to commit page",
      "targets": [
        {
          "os": "default",
          "uri": "https://github.com/MicrosoftDocs/azure-docs/commit/abc123"
        }
      ]
    }
  ]
}

================================================================================
测试完成
================================================================================
```

## 注意事项

1. **GitHub Token**: 确保设置了有效的GitHub Personal Access Token
2. **网络连接**: 需要能够访问GitHub API和OpenAI API
3. **Teams Webhook**: 如果要测试实际发送，需要有效的Teams webhook URL
4. **API限制**: 注意GitHub API和OpenAI API的调用限制

## 故障排除

### 常见错误

1. **获取patch数据失败**
   - 检查GitHub token是否有效
   - 确认commit URL是否正确
   - 检查网络连接

2. **GPT响应失败**
   - 检查OpenAI API配置
   - 确认API密钥是否有效
   - 检查网络连接

3. **Teams发送失败**
   - 确认webhook URL是否正确
   - 检查Teams频道权限
   - 验证消息格式是否正确

### 调试技巧

- 查看日志文件获取详细错误信息
- 使用模式1先测试处理流程，确认无误后再使用模式2发送到Teams
- 检查环境变量设置是否正确 