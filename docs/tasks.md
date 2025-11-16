# Snapopedia 开发任务追踪

> 本文档记录项目开发任务的状态和进度，供多窗口协作使用

**最后更新**: 2024-XX-XX
**当前阶段**: Phase 1 - 项目基础搭建

---

## 任务状态说明

- ✅ **已完成** - 代码已实现并测试通过
- 🔄 **进行中** - 正在开发
- ⏳ **待开始** - 已规划但未开始
- ⏸️ **暂停** - 阻塞或等待其他任务
- ❌ **已取消** - 不再需要

---

## Phase 1: 项目基础 🏗️

**目标**: 搭建 FastAPI 项目基础架构，为后续开发做准备

| 任务 | 状态 | 负责 | 说明 |
|------|------|------|------|

| 创建文档体系 | ✅ | Claude | CLAUDE.md, decisions.md, tasks.md 等 |
| 搭建 FastAPI 项目结构 | ✅ | Claude | 已创建 FastAPI 应用、路由与 /health |
| 实现配置管理模块 | ✅ | Claude | src/config.py - 读取 .env 文件 |
| 实现日志系统 | ✅ | Claude | src/utils/logger.py - 统一日志格式 |
| 定义基础数据模型 | ✅ | Claude | src/models/request.py 和 response.py |
| 实现自定义异常类 | ✅ | Claude | src/utils/errors.py - 错误码定义 |

**完成标准**:
- [x] 项目可以启动（`uvicorn src.main:app --reload`）
- [x] `/health` 接口返回正常
- [x] 日志输出到控制台
- [x] 配置可以从 `.env` 读取

---

## Phase 2: 存储模块 📦

**目标**: 实现 Cloudflare R2 图片上传功能

| 任务 | 状态 | 负责 | 说明 |
|------|------|------|------|
| R2 客户端封装 | ✅ | Claude | src/clients/r2_client.py - boto3 封装 |
| 实现图片上传逻辑 | ✅ | Claude | src/services/storage.py - 统一命名 & 错误处理 |
| 实现文件命名规则 | ✅ | Claude | `original_image/{timestamp}_{random_id}.ext` |
| 图片上传 API 接口 | ✅ | Claude | POST /api/v1/images/upload 返回公开 URL |

**完成标准**:
- [x] 图片可以上传到 R2 的 `original_image/` 目录
- [x] 返回公开访问的 URL
- [x] 支持常见图片格式（jpg, png, webp）
- [x] 有完善的错误处理

**依赖环境变量** (需开发者填写):
- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME`
- `R2_PUBLIC_URL`

---

## Phase 3: AI 服务客户端 🤖

**目标**: 封装所有外部 AI 服务的调用

| 任务 | 状态 | 负责 | 说明 |
|------|------|------|------|
| DIFY 客户端基础封装 | ✅ | Claude | src/clients/dify_client.py - 通用请求方法 |
| DIFY 照片预处理调用 | ✅ | Claude | preprocessing workflow 封装 analyze |
| DIFY 卡片生成调用 | ✅ | Claude | card generation workflow 封装 generate_card |
| DIFY 问答调用 | ✅ | Claude | Q&A workflow 封装 ask |
| Gemini 客户端封装 | ✅ | Claude | src/clients/gemini_client.py - 图片编辑 |
| ElevenLabs 客户端封装 | ✅ | Claude | src/clients/elevenlabs_client.py - TTS |
| 统一错误处理和超时 | ✅ | Claude | ExternalServiceError + 各客户端 timeout |

**完成标准**:
- [x] 所有客户端可以独立调用和测试
- [x] 有完善的超时设置（参考 `docs/decisions.md` 6.5）
- [x] 有统一的错误处理
- [ ] 日志记录所有 API 调用

**依赖环境变量** (需开发者填写):
- `DIFY_API_KEY_PREPROCESSING`
- `DIFY_API_KEY_CARD_GEN`
- `DIFY_API_KEY_QA`
- `GEMINI_API_KEY`
- `ELEVENLABS_API_KEY`
- `ELEVENLABS_VOICE_ID`

**依赖文档** (需开发者补充):
- `docs/dify_schemas.md` - DIFY 实际返回格式（这里不写完整的响应格式了 只写了Agent所返回的JSON string的格式 用来解析）
- `docs/dify_api.md` - DIFY API docs （这里定义了相对完整的响应格式）

---

## Phase 4: 核心 Pipeline 🔄

**目标**: 实现学习卡片生成的完整流程

| 任务 | 状态 | 负责 | 说明 |
|------|------|------|------|
| Pipeline 服务基础框架 | ✅ | Claude | src/services/pipeline.py |
| 步骤1：照片预处理 | ✅ | Claude | 调用 DIFY，判断 clear/unclear |
| 步骤2a：卡片生成 | ✅ | Claude | 调用 DIFY，解析 title 和 desc |
| 步骤2b：图片高亮 | ✅ | Claude | 调用 Gemini（OpenRouter），生成高亮图并上传 R2 |
| 步骤2：并行执行 | ✅ | Claude | asyncio.gather 并行卡片/高亮 |
| 步骤3：语音生成 | ✅ | Claude | 调用 ElevenLabs，上传音频到 R2 |
| Pipeline 整合与错误处理 | ✅ | Claude | 高亮/语音失败自动降级 |
| 卡片生成 API 接口 | ✅ | Claude | POST /api/v1/cards/generate 已接入 Pipeline |

**完成标准**:
- [x] 完整 pipeline 可以运行
- [x] 正常情况返回：卡片 + 高亮图 + 语音
- [x] 部分失败时有降级策略（参考 `docs/decisions.md` 3.3.2）
- [x] 响应时间 < 10 秒（并行执行）

**关键决策参考**:
- `docs/decisions.md` 第 2、3、4 节
- `docs/pipeline.md` 完整流程

---

## Phase 5: 问答功能 💬

**目标**: 实现基于学习卡片的多轮问答

| 任务 | 状态 | 负责 | 说明 |
|------|------|------|------|
| 问答服务实现 | ✅ | Claude | src/services/chat.py 调用 DIFY Q&A |
| card_context 拼接 | ✅ | Claude | 请求体传入 card_context，转发至 DIFY |
| 可选语音生成 | ✅ | Claude | need_audio 参数控制 ElevenLabs 降级 |
| 问答 API 接口 | ✅ | Claude | POST /api/v1/chat/ 返回 answer/audio |

**完成标准**:
- [x] 支持多轮对话（conversation_id 由前端管理）
- [x] 回答文本口语化（2-4 句话）
- [x] 可选返回语音

**关键决策参考**:
- `docs/decisions.md` 第 5 节

---

## Phase 6: 优化与完善 ✨

**目标**: 提升代码质量和用户体验

| 任务 | 状态 | 负责 | 说明 |
|------|------|------|------|
| 优化错误信息 | ⏳ | Claude | 用户友好的错误提示 |
| 完善日志系统 | ⏳ | Claude | 结构化日志、关键节点记录 |
| 生成 API 文档 | ⏳ | Claude | Swagger/OpenAPI 自动生成 |
| 性能优化 | ⏳ | Claude | 减少不必要的等待时间 |
| 添加单元测试 | ⏳ | 待定 | 核心逻辑测试覆盖 |

---

## 阻塞问题追踪

> 记录当前阻塞开发的问题，需要开发者解决

| 问题 | 影响任务 | 状态 | 说明 |
|------|----------|------|------|
| 无 | - | - | 当前无阻塞问题 |

---

## 技术债务

> 记录已知的技术债务，后续需要重构

| 问题 | 优先级 | 说明 |
|------|--------|------|
| 暂无 | - | 初始开发阶段 |

---

## 更新日志

- **2024-XX-XX**: 创建任务追踪文档，定义 Phase 1-6
- [待补充]

---

## 使用说明

### 给 Claude（新窗口）
1. 查看"当前阶段"了解项目进度
2. 查看对应 Phase 的任务状态
3. 选择状态为 ⏳ 的任务开始实现
4. 完成后更新状态为 ✅ 并记录说明

### 给开发者
1. 查看"依赖环境变量"填写 `.env` 文件
2. 查看"依赖文档"补充相关文档
3. 查看"阻塞问题"解决阻塞项
4. 测试完成的功能并反馈

### 协作约定
- **Claude** 负责更新任务状态（⏳ → 🔄 → ✅）
- **开发者** 负责填写依赖的配置和文档
- 发现新问题时记录到"阻塞问题追踪"或"技术债务"
