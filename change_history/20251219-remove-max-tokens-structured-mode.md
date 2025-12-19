# Remove max_tokens Limit in Structured Output Mode

**Date**: December 19, 2025  
**Type**: Bug Fix / Optimization  
**Impact**: GPT Structured Output Mode

## Summary

Removed the `max_tokens` parameter limit in Structured Output mode to allow OpenAI API to use its default behavior (full context window minus prompt tokens). This prevents response truncation and JSON parsing errors while legacy mode remains unchanged.

## Problem

Previously, structured output mode had a hard-coded `max_tokens=3000` limit:
- Could cause response truncation for complex commits with multiple files
- Truncated JSON responses lead to parsing errors
- Had to manually tune the value based on content length

## Changes Made

### 1. Modified `gpt_reply.py`

**File**: `gpt_reply.py`

**Before**:
```python
def get_gpt_structured_response(messages, response_format, max_tokens=2000):
    """
    Args:
        max_tokens: 最大 token 数
    """
    try:
        response = chat_completion_with_backoff(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=messages,
            temperature=0,
            max_tokens=max_tokens,
            response_format=response_format
        )
```

**After**:
```python
def get_gpt_structured_response(messages, response_format):
    """
    Note:
        不设置max_tokens，使用OpenAI API默认行为（上下文窗口减去prompt tokens）
    """
    try:
        response = chat_completion_with_backoff(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=messages,
            temperature=0,
            response_format=response_format
        )
```

### 2. Modified `call_gpt.py`

**File**: `call_gpt.py`

**Before**:
```python
# 获取 structured response
structured_response, prompt_tokens, completion_tokens, total_tokens = get_gpt_structured_response(
    messages, response_format, max_tokens=3000  # 增加max_tokens以避免响应被截断
)
```

**After**:
```python
# 获取 structured response (不设置max_tokens，使用API默认值)
structured_response, prompt_tokens, completion_tokens, total_tokens = get_gpt_structured_response(
    messages, response_format
)
```

## Behavior Changes

### Structured Mode (Modified)
- **Before**: Limited to 3000 tokens, could be truncated
- **After**: Uses full available context (model limit - prompt tokens)
- **Benefit**: No truncation, always complete JSON responses
- **Trade-off**: May consume more tokens, but ensures correctness

### Legacy Mode (Unchanged)
- Still uses `max_tokens=1000` for summary and title generation
- No changes to existing behavior

## OpenAI API Default Behavior

When `max_tokens` is not specified:
- API uses: `max_tokens = context_window - prompt_tokens`
- For GPT-4o (128k context): Can generate very long responses
- For GPT-4 (8k context): Can generate up to remaining context

## Benefits

1. **Reliability**: Eliminates JSON truncation errors
2. **Flexibility**: Adapts to response length automatically
3. **Simplicity**: No need to tune max_tokens value
4. **Completeness**: Ensures all 4 fields (summary, title, importance_score, importance_score_reasoning) are fully generated

## Potential Considerations

1. **Token Usage**: May consume more tokens per request
   - Acceptable trade-off for guaranteed complete responses
   - Structured mode already saves 50% API calls vs legacy mode

2. **Cost Monitoring**: 
   - Monitor completion_tokens in logs
   - Can add alerting if tokens exceed expected range

3. **Future Optimization** (if needed):
   - Can make max_tokens configurable per topic in target_config.json
   - Can implement dynamic calculation based on patch size

## Testing Recommendations

1. Monitor logs for completion_tokens values
2. Verify no JSON parsing errors occur
3. Check summary quality hasn't degraded
4. Compare token usage before/after

## Rollback Plan

If issues arise, can easily restore by:
```python
get_gpt_structured_response(messages, response_format, max_tokens=3000)
```

## Related Issues

- Fixes potential JSON truncation issues
- Related to test case in `test/test_json_truncation_reproduce.py`
- Aligns with OpenAI best practices for structured outputs
