# DIFY Workflows 返回数据格式

> 本文档记录各个 DIFY workflow 的实际返回 JSON 格式

---

## 1. 照片预处理与分析 (Preprocessing)

### API Key
环境变量: `DIFY_API_KEY_PREPROCESSING`

### 输入示例
```json
{
    "query": "biology",
    "files": [{
        "type": "image",
        "transfer_method": "remote_url",
        "url": "https://r2.../original_image/xxx.jpg"
    }],
    "user": "user_id_xxx",
    "response_mode": "blocking"
}
```

### 输出格式
> [请在这里填写实际的 DIFY 返回格式]

**预期字段**:
```json
{
    "answer": "...",  // DIFY 返回的文本，需要解析
    "conversation_id": "...",
    "message_id": "...",

    // 需要从 answer 中解析出以下字段（如果 DIFY 返回的是 JSON 字符串）
    "parsed_data": {
        "image_status": "clear" | "unclear",
        "central_object": "物体名称"  // 仅当 status 为 clear 时
    }
}
```

**实际返回示例**:
```json
OUTPUT FORMAT:
Return a JSON object with the following structure:

If the image is CLEAR:
{
  "image_status": "clear",
  "central_object": "Name of the object in the center of the image"
}

If the image is NOT CLEAR (blurry, no central object, or too ambiguous):
{
  "image_status": "unclear"
}
```

---

## 2. 学习卡片生成 (Card Generation)

### API Key
环境变量: `DIFY_API_KEY_CARD_GEN`

### 输入示例
```json
{
    "query": "biology",
    "inputs": {
        "item_name": "叶绿体"  // 来自预处理步骤的 central_object
    },
    "files": [{
        "type": "image",
        "transfer_method": "remote_url",
        "url": "https://r2.../original_image/xxx.jpg"
    }],
    "user": "user_id_xxx",
    "response_mode": "blocking"
}
```

### 输出格式
> [请在这里填写实际的 DIFY 返回格式]

**预期字段**:
```json
{
    "answer": "...",  // DIFY 返回的文本，需要解析
    "conversation_id": "...",
    "message_id": "...",

    // 需要从 answer 中解析出以下字段
    "parsed_data": {
        "title": "知识点名称",
        "desc": "知识点详细说明（2-4句话）"
    }
}
```

**实际返回示例**:
```json
{
  "title": "A concise name for the knowledge point (max 10 words)",
  "desc": "A detailed explanation of the knowledge point (2-4 sentences, educational and informative)"
}
```

---

## 3. 多轮问答 (Q&A)

### API Key
环境变量: `DIFY_API_KEY_QA`

### 首轮输入示例
```json
{
    "query": "用户的问题",
    "inputs": {
        "card_context": "标题：光合作用的场所\n说明：叶绿体是..."  // 格式待定
    },
    "files": [{
        "type": "image",
        "transfer_method": "remote_url",
        "url": "https://r2.../original_image/xxx.jpg"
    }],
    "user": "user_id_xxx",
    "conversation_id": "",  // 首轮为空
    "response_mode": "blocking"
}
```

### 后续轮次输入
```json
{
    "query": "继续提问",
    "inputs": {},
    "user": "user_id_xxx",
    "conversation_id": "conv-xxx",  // 使用首轮返回的 ID
    "response_mode": "blocking"
}
```

### 输出格式
> [请在这里填写实际的 DIFY 返回格式]

**预期字段**:
```json
{
    "answer": "AI 的回答（2-4句话，口语化）",
    "conversation_id": "conv-xxx",  // 用于后续对话
    "message_id": "msg-xxx"
}
```

**实际返回示例**:
```json
纯文本
```

---

## 解析规则

### 如果 DIFY 返回的是 JSON 字符串
某些 DIFY workflow 可能在 `answer` 字段中返回 JSON 字符串，需要解析：

```python
import json

response = dify_client.send_message(...)
answer = response.get("answer", "")

# 尝试解析 JSON
try:
    parsed_data = json.loads(answer)
    image_status = parsed_data.get("image_status")
    central_object = parsed_data.get("central_object")
except json.JSONDecodeError:
    # 如果不是 JSON，可能需要其他解析方式
    pass
```

### 如果 DIFY 返回的是纯文本
需要根据实际返回格式进行文本解析或正则匹配。

---

## 测试清单

- [ ] 测试照片预处理 workflow，记录返回格式
- [ ] 测试卡片生成 workflow，记录返回格式
- [ ] 测试问答 workflow（首轮），记录返回格式
- [ ] 测试问答 workflow（多轮），记录返回格式
- [ ] 确认各 workflow 是否需要 `inputs` 参数
- [ ] 确认 `conversation_id` 的生命周期

---

## 更新日志

- 2024-XX-XX: 初始创建模板
- [待补充]
