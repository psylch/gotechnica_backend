# 数据处理流程文档 (Data Pipeline)

## 概述
本系统是一个基于视觉的智能学习卡片生成工作流，通过分析用户拍摄的照片，自动生成带有知识点讲解的学习卡片，并支持语音播报和后续问答。

在进入工作流之前，需要上传到 cloudflare r2存储桶的 original_image目录 参考 [cloudflare_r2_api.md](docs/cloudfare_r2_api.md

进入pipeline之后。
其中文本输出的节点 由 DIFY 定义，参考 [dify_api.md](docs/dify_api.md) [不同的流程/节点通过不同的APIkey区分]
文本输出的节点使用gemini-flash-image 参考 [gemini_api.md](docs/gemini_api.md)
需要转语音的节点使用eleven-lab模型 eleven-flash-2.5 参考 [elevenlabs_api.md](docs/elevenlabs_api.md)

---

## 完整数据流

### 1. 用户输入
**输入数据：**
- `image_input`: 照片（URL，已预先上传到对象存储）
- `user_preference`: 学习主题标签（Subject Tag，如 "biology", "computer science" 等）

---

### 2. 照片预处理与分析
**功能：** 判断照片质量和相关性

**输入：**
- `image_input`: 照片
- `user_preference`: 学习主题标签

**输出：**
- `image_status`: "clear" 或 "unclear"
- `central_object`: 照片中心物体的名称（仅当状态为 "clear" 时）

**流程控制：**
- 如果 `image_status` 为 "unclear" → **终止流程**
- 如果 `image_status` 为 "clear" → 继续后续步骤

---

### 3. 分支处理（并行执行）

当照片分析成功后，系统同时执行以下两个任务：

#### 3.1 学习卡片生成
**功能：** 生成知识点卡片内容

**输入：**
- `image_input`: 照片
- `user_preference`: 学习主题标签
- `item_name`: 照片中心物体名称（来自步骤2的 central_object）

**输出（JSON）：**
```json
{
  "title": "知识点名称",
  "desc": "知识点详细说明（2-4句话）"
}
```

#### 3.2 图片高亮处理
**功能：** 生成视觉突出中心物体的图片

**输入：**
- `image_input`: 原始照片

**输出：**
- 高亮处理后的照片（中心物体被强调，周围有光晕效果）

---

### 4. 语音生成
**功能：** 将卡片文字内容转换为语音

**前置条件：** 步骤 3.1（卡片生成）成功完成

**输入：**
- 卡片的 `title` 和 `desc` 文本内容

**输出：**
- 语音文件（通过 ElevenLabs API 生成）

---

## 附加功能：多轮问答

### 后续问题处理
**功能：** 支持用户对生成的卡片内容进行追问

**输入：**
- `card_context`: 学习卡片的所有信息拼接成的字符串（包含 title 和 desc）
- `image_input`: 原始照片
- 用户的问题
- 对话历史（用于多轮对话）

**输出：**
- 口语化的自然语言回答（2-4句话，适合语音播报）

**特点：**
- 支持多轮对话上下文
- 输出适合转换为语音的口语化文本

---

## 数据流图示

```
用户输入（image_input + user_preference）
         ↓
   照片预处理分析
         ↓
    [判断清晰度]
         ↓
    unclear → 终止流程 ❌
         ↓
      clear
         ↓
    ┌────┴────┐
    ↓         ↓
卡片生成   图片高亮
 (JSON)    (Image)
    ↓
语音生成
(Audio)

[额外] 多轮问答 ← 用户追问
```

---

## 关键设计说明

1. **失败快速终止：** 照片不清晰时立即停止，避免无效计算
2. **并行处理：** 卡片生成和图片高亮同时进行，提升效率
3. **语音优先：** 所有文本输出都考虑了语音播报的需求，使用口语化表达
4. **可扩展性：** 多轮问答模块独立，可按需启用

---

## 技术实现方式
- 所有节点通过 API 形式封装为 workflow
- 各节点之间通过标准化的 JSON 数据格式通信
- 后端统一调度整个工作流的执行顺序和数据传递