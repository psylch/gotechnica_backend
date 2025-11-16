# Snapopedia 后端设计决策文档

> 本文档记录所有待确认和已确认的设计决策

---

## 1. 图片上传与存储

### 1.1 图片上传方式
- **决策**: ✅ 后端中转
- **说明**: 前端 → 后端 → R2

### 1.2 R2 访问权限
- **决策**: ✅ 通过 API 访问
- **说明**: 使用 R2 API，配置访问密钥

### 1.3 文件命名规则
- **决策**: ✅ `{timestamp}_{random_id}.jpg`
- **说明**:
  ```python
  # 示例
  import time
  import uuid

  filename = f"{int(time.time())}_{uuid.uuid4().hex[:8]}.jpg"
  # 例如: 1699999999_a1b2c3d4.jpg
  ```

### 1.4 Pipeline 触发方式
- **决策**: ✅ 前端获得 R2 URL 后调用后端接口
- **流程**:
  ```
  前端上传图片 → 后端接收 → 存到 R2 → 返回 URL 给前端
  → 前端调用 /api/v1/generate-card 接口触发 pipeline
  ```

---

## 2. Pipeline 步骤1：照片预处理与分析

### 2.1 实现方式
- **决策**: ✅ DIFY Workflow
- **配置**:
  - 环境变量名: `DIFY_API_KEY_PREPROCESSING`
  - Workflow 名称: [待补充]

### 2.2 输入格式
- **决策**: ✅ 文本 + 图片 URL
- **参考**: `docs/dify_api.md`
- **请求示例**:
  ```python
  {
      "query": "{user_preference}",  # 例如 "biology"
      "files": [{
          "type": "image",
          "transfer_method": "remote_url",
          "url": "{image_url}"
      }]
  }
  ```

### 2.3 输出格式
- **决策**: ✅ 参考 `docs/dify_schemas.md`（用户将创建此文档）
- **预期字段**:
  ```json
  {
      "image_status": "clear" | "unclear",
      "central_object": "物体名称"  // 仅当 status 为 clear 时
  }
  ```

### 2.4 失败图片处理
- **决策**: ✅ 不存储失败记录
- **说明**: unclear 的图片直接返回错误，不做日志记录

---

## 3. Pipeline 步骤2：并行处理

### 3.1 卡片生成

#### 3.1.1 实现方式
- **决策**: ✅ DIFY Workflow
- **配置**:
  - 环境变量名: `DIFY_API_KEY_CARD_GEN`
  - Workflow 名称: [待补充]

#### 3.1.2 输入参数
- **决策**: ✅ `central_object` 和 `item_name` 是同一个东西
- **输入格式**:
  ```python
  {
      "query": "{user_preference}",
      "inputs": {
          "item_name": "{central_object}"  # 来自步骤1
      },
      "files": [{
          "type": "image",
          "transfer_method": "remote_url",
          "url": "{image_url}"
      }]
  }
  ```

#### 3.1.3 输出格式
- **决策**: ✅ 参考 `docs/dify_schemas.md`
- **预期字段**:
  ```json
  {
      "title": "知识点名称",
      "desc": "知识点详细说明（2-4句话）"
  }
  ```

#### 3.1.4 文本长度限制
- **决策**: ✅ 不用管
- **说明**: DIFY 内部已控制输出长度

### 3.2 图片高亮

#### 3.2.1 高亮 Prompt
- **决策**: ✅ 已确定
- **格式**:
  ```python
  prompt = f"""
  把相片中间的物体{central_object}重点勾勒出来 边框周围散发朦胧的半透明光效
  """
  ```

#### 3.2.2 是否使用 central_object
- **决策**: ✅ 是，需要在 prompt 中使用
- **说明**: 高亮 prompt 需要知道要突出哪个物体

#### 3.2.3 输出图片格式
- **决策**: WEBP(我要控制体积！)
- **选项**:
  - [ ] PNG (无损，文件较大)
  - [ ] JPEG (有损，文件较小)
- **分辨率**: ⏳ 待确认
  - [ ] 保持原图分辨率
  - [ ] 固定尺寸：________

#### 3.2.4 高亮图存储方式
- **决策**: ✅ 存到 R2，返回 URL
- **存储路径**: `highlighted_image/{filename}.webp`
- **说明**: 使用 WebP 格式压缩，控制文件体积

### 3.3 并行执行机制

#### 3.3.1 真正并行吗？
- **决策**: ✅ 是，使用 `asyncio.gather()` 并行调用
- **说明**: 卡片生成和图片高亮同时进行，节省时间

#### 3.3.2 部分失败处理
- **决策**: ⏳ 待确认
- **场景**: 卡片生成成功 ✅，图片高亮失败 ❌
- **选项**:
  - [ ] 等待两个都完成，部分成功也返回（推荐）
  - [ ] 一个失败就整体失败
- **降级策略**:
  ```json
  {
      "card": {"title": "...", "desc": "..."},
      "highlighted_image": null,  // 失败时为 null
      "original_image": "...",     // 总是返回原图
      "highlight_failed": true     // 标记失败
  }
  ```

---

## 4. Pipeline 步骤3：语音生成

### 4.1 输入文本格式
- **决策**: ⏳ 待确认
- **选项**:
  - [ ] 只用 `desc`
  - [ ] 使用 `title + desc` 拼接，格式: `"{title}。{desc}"`
  - [ ] 其他格式: ____________

### 4.2 语音文件存储
- **决策**: ✅ 存到 R2，返回 URL
- **存储路径**: `audio/{filename}.mp3`
- **文件命名**: 与原图使用相同的 timestamp + random_id

### 4.3 音频参数
- **决策**: ⏳ 待补充
- **配置**:
  - 环境变量名: `ELEVENLABS_API_KEY`
  - Voice ID: ____________
  - 模型: `eleven-flash-2.5`（已确定）
  - 格式: `mp3_44100_128` / `mp3_22050_32` / 其他: ____________
  - 语言: ____________ (en / zh / ...)

### 4.4 语音生成失败处理
- **决策**: ⏳ 待确认
- **选项**:
  - [ ] 降级：返回卡片，但 `audio` 字段为 null（推荐）
  - [ ] 必须成功：语音失败则整体失败

---

## 5. 多轮问答功能

### 5.1 实现方式
- **决策**: ✅ DIFY Workflow
- **配置**:
  - 环境变量名: `DIFY_API_KEY_QA`
  - Workflow 名称: [待补充]

### 5.2 card_context 拼接格式
- **决策**: ⏳ 待确认
- **选项**:
  - [ ] 格式: `"{title}\n{desc}"`
  - [ ] 格式: `"标题：{title}\n说明：{desc}"`
  - [ ] JSON 字符串: `json.dumps({"title": ..., "desc": ...})`
  - [ ] 其他: ____________

### 5.3 conversation_id 存储
- **决策**: ⏳ 待确认
- **选项**:
  - [ ] 前端管理（DIFY 返回的 conversation_id 由前端保存）
  - [ ] 后端数据库存储
  - [ ] Redis 缓存
- **如果后端存储，需要关联**: ____________

### 5.4 对话历史上限
- **决策**: ⏳ 待确认
- **限制**:
  - 最多轮数: ________ 轮
  - 超过后: [ ] 清空重新开始 / [ ] 保留最近 N 轮 / [ ] 不限制

### 5.5 问答是否需要语音
- **决策**: ⏳ 待确认
- **选项**:
  - [ ] 是，每个回答都转语音
  - [ ] 否，只返回文本
  - [ ] 可选，前端传参控制

---

## 6. 错误处理策略

### 6.1 照片分析失败（unclear）
- **决策**: ✅ 终止流程
- **返回**:
  ```json
  {
      "success": false,
      "error": "image_unclear",
      "message": "照片不够清晰或与主题不相关，请重新拍摄"
  }
  ```

### 6.2 卡片生成失败
- **决策**: ⏳ 待确认
- **选项**:
  - [ ] 直接失败，返回错误（推荐 demo）
  - [ ] 重试 1 次
  - [ ] 重试 N 次: ________

### 6.3 图片高亮失败
- **决策**: ⏳ 待确认（见 3.3.2）
- **推荐**: 降级使用原图

### 6.4 语音生成失败
- **决策**: ⏳ 待确认（见 4.4）
- **推荐**: 降级返回无语音

### 6.5 API 超时设置
- **决策**: ⏳ 待补充
- **配置**:
  ```python
  TIMEOUT_DIFY_PREPROCESSING = 30  # 秒
  TIMEOUT_DIFY_CARD_GEN = 30
  TIMEOUT_GEMINI_HIGHLIGHT = 30
  TIMEOUT_ELEVENLABS_TTS = 30
  TIMEOUT_DIFY_QA = 20
  ```

### 6.6 API Rate Limit 处理
- **决策**: ⏳ 待确认
- **选项**:
  - [ ] 返回错误，提示稍后重试
  - [ ] 自动重试，使用指数退避
  - [ ] 队列排队

---

## 7. FastAPI 接口设计

### 7.1 主接口：生成学习卡片

#### 接口定义
- **路径**: ⏳ 待确认
  - 建议: `POST /api/v1/cards/generate`
  - 或: ____________

#### 请求格式
```json
{
    "image_url": "https://r2.../original_image/xxx.jpg",
    "user_preference": "biology"
}
```

#### 响应格式（成功）
- **决策**: ⏳ 待确认
- **选项 A - 一次性返回**（用户等待 6-8 秒）:
  ```json
  {
      "success": true,
      "data": {
          "card_id": "uuid-xxx",
          "central_object": "叶绿体",
          "card": {
              "title": "光合作用的场所",
              "desc": "叶绿体是植物细胞中进行光合作用的细胞器..."
          },
          "images": {
              "original": "https://r2.../original.jpg",
              "highlighted": "https://r2.../highlighted.jpg"
          },
          "audio": "https://r2.../audio.mp3",
          "conversation_id": "dify-conv-xxx"
      }
  }
  ```

- **选项 B - 异步返回**（立即返回 task_id，前端轮询）:
  ```json
  // 立即返回
  {
      "success": true,
      "task_id": "task-xxx",
      "status_url": "/api/v1/tasks/task-xxx"
  }

  // 轮询接口返回
  {
      "task_id": "task-xxx",
      "status": "processing" | "completed" | "failed",
      "progress": 60,  // 百分比
      "data": {...}    // 完成后才有
  }
  ```

- **你的选择**: [ ] A / [ ] B / [ ] 其他: ____________

#### 响应格式（失败）
```json
{
    "success": false,
    "error": "error_code",
    "message": "错误描述",
    "details": {}  // 可选的详细信息
}
```

### 7.2 问答接口

#### 接口定义
- **路径**: ⏳ 待确认
  - 建议: `POST /api/v1/cards/chat`
  - 或: ____________

#### 请求格式
- **决策**: ⏳ 待确认
- **选项**:
  ```json
  {
      "conversation_id": "dify-conv-xxx",  // DIFY 返回的 ID
      "question": "用户的问题",
      "need_audio": true  // 可选，是否需要语音
  }
  ```

#### 响应格式
```json
{
    "success": true,
    "data": {
        "answer": "AI 的回答（2-4句话）",
        "audio": "https://r2.../answer.mp3",  // 如果 need_audio=true
        "message_id": "dify-msg-xxx"
    }
}
```

### 7.3 图片上传接口

#### 接口定义
- **路径**: `POST /api/v1/images/upload`

#### 请求格式
- **Content-Type**: `multipart/form-data`
- **字段**:
  ```
  file: <binary>
  ```

#### 响应格式
```json
{
    "success": true,
    "data": {
        "image_url": "https://r2.../original_image/xxx.jpg",
        "filename": "1699999999_a1b2c3d4.jpg"
    }
}
```

### 7.4 其他接口

#### 健康检查
- **路径**: `GET /health`
- **响应**:
  ```json
  {
      "status": "ok",
      "timestamp": 1699999999
  }
  ```

#### 是否需要其他接口？
- **决策**: ⏳ 待确认
- **可选**:
  - [ ] `GET /api/v1/cards/{card_id}` - 查看历史卡片
  - [ ] `GET /api/v1/cards` - 列出用户的所有卡片
  - [ ] `DELETE /api/v1/cards/{card_id}` - 删除卡片
  - [ ] 其他: ____________

---

## 8. 数据持久化

### 8.1 是否需要数据库
- **决策**: ⏳ 待确认
- **选项**:
  - [ ] 不需要，完全无状态（conversation_id 由前端管理）
  - [ ] 需要，存储卡片历史
- **如果需要，类型**:
  - [ ] SQLite（简单，适合 demo）
  - [ ] PostgreSQL
  - [ ] MongoDB
  - [ ] 其他: ____________

### 8.2 卡片数据存储
- **决策**: ⏳ 待确认
- **如果存储，表结构**:
  ```sql
  CREATE TABLE cards (
      id UUID PRIMARY KEY,
      user_id VARCHAR,  -- 如果有用户系统
      image_url TEXT,
      highlighted_image_url TEXT,
      central_object VARCHAR,
      title TEXT,
      description TEXT,
      audio_url TEXT,
      conversation_id VARCHAR,
      created_at TIMESTAMP,
      updated_at TIMESTAMP
  );
  ```

### 8.3 用户系统
- **决策**: ⏳ 待确认
- **选项**:
  - [ ] 不需要，匿名使用
  - [ ] 需要简单的用户标识（如设备 ID）
  - [ ] 需要完整的登录系统
- **如果需要用户标识**: ____________

### 8.4 conversation_id 管理
- **决策**: ⏳ 待确认（见 5.3）
- **推荐**: 前端管理（demo 阶段最简单）

---

## 9. 配置与部署

### 9.1 环境变量清单

```bash
# R2 配置
R2_ACCOUNT_ID=          # [待填写]
R2_ACCESS_KEY_ID=       # [待填写]
R2_SECRET_ACCESS_KEY=   # [待填写]
R2_BUCKET_NAME=         # [待填写]
R2_PUBLIC_URL=          # [待填写] 例如 https://pub-xxx.r2.dev

# DIFY API Keys
DIFY_API_KEY_PREPROCESSING=   # [待填写] 照片预处理
DIFY_API_KEY_CARD_GEN=        # [待填写] 卡片生成
DIFY_API_KEY_QA=              # [待填写] 问答

# Gemini API
GEMINI_API_KEY=         # [待填写]

# ElevenLabs API
ELEVENLABS_API_KEY=     # [待填写]
ELEVENLABS_VOICE_ID=    # [待填写]

# 超时配置（秒）
TIMEOUT_DIFY_PREPROCESSING=30
TIMEOUT_DIFY_CARD_GEN=30
TIMEOUT_GEMINI_HIGHLIGHT=30
TIMEOUT_ELEVENLABS_TTS=30
TIMEOUT_DIFY_QA=20

# 其他
DEBUG=False
LOG_LEVEL=INFO
```

### 9.2 部署方式
- **决策**: ⏳ 待确认
- **选项**:
  - [ ] 本地运行（开发）
  - [ ] Docker 容器
  - [ ] 云平台: ____________

---

## 10. 前后端交互

### 10.1 前端技术栈
- **决策**: ⏳ 待补充
- **技术栈**: ____________
- **影响**: 决定返回数据格式和实时通信方式

### 10.2 实时进度反馈
- **决策**: ⏳ 待确认
- **选项**:
  - [ ] 不需要，简单的 loading 动画
  - [ ] 需要，使用 WebSocket
  - [ ] 需要，使用 SSE（Server-Sent Events）
  - [ ] 需要，使用轮询

### 10.3 CORS 配置
- **决策**: ⏳ 待确认
- **允许的源**:
  ```python
  CORS_ORIGINS = [
      "http://localhost:3000",  # 开发环境
      "https://your-domain.com"  # 生产环境
  ]
  ```

---

## 待办事项清单

### 🔴 高优先级（必须确定才能开始编码）
- [ ] 3.2.1 - 补充图片高亮的 prompt 模板
- [ ] 3.2.3 - 确定高亮图片的格式和分辨率
- [ ] 3.2.4 - 确定高亮图存储方式
- [ ] 4.1 - 确定语音输入文本格式
- [ ] 4.2 - 确定语音文件存储方式
- [ ] 4.3 - 补充 ElevenLabs 音频参数
- [ ] 7.1 - 确定主接口的响应方式（同步/异步）

### 🟡 中优先级（影响用户体验）
- [ ] 3.3.1 - 确定是否并行执行
- [ ] 3.3.2 - 确定部分失败的处理策略
- [ ] 4.4 - 确定语音生成失败的处理
- [ ] 5.2 - 确定 card_context 拼接格式
- [ ] 5.3 - 确定 conversation_id 存储方式
- [ ] 6.2 - 确定卡片生成失败的重试策略
- [ ] 6.5 - 补充各 API 的超时时间

### 🟢 低优先级（可以后续优化）
- [ ] 5.4 - 确定对话历史上限
- [ ] 5.5 - 确定问答是否需要语音
- [ ] 6.6 - 确定 Rate Limit 处理方式
- [ ] 8.1 - 确定是否需要数据库
- [ ] 10.2 - 确定是否需要实时进度反馈

### 📝 需要用户提供的文档
- [ ] `docs/dify_schemas.md` - 各个 DIFY workflow 的返回格式
- [ ] `.env.example` - 环境变量模板
