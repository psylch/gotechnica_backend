# Snapopedia 后端项目协作协议

> 本文档定义 Claude、开发者与项目代码库之间的交互协议和开发规范

---

## 📋 项目概述

**Snapopedia** 是一个基于视觉的智能学习卡片生成系统。用户拍摄照片后，系统自动分析图片内容，生成知识点卡片、高亮图片和语音讲解，并支持多轮问答。

**技术栈**：FastAPI + DIFY + Gemini + ElevenLabs + Cloudflare R2

---

## 🗂️ 文档索引

### 核心文档
- **`docs/prd_init.md`** - 项目初始需求文档
- **`docs/pipeline.md`** - 完整数据处理流程说明
- **`docs/decisions.md`** - 设计决策记录（动态更新）
- **`docs/dify_schemas.md`** - DIFY workflows 返回格式定义
- **`docs/tasks.md`** - 开发任务追踪（多窗口协作必读）

### API 参考文档
- **`docs/dify_api.md`** - DIFY API 使用指南
- **`docs/gemini_api.md`** - Gemini 2.5 Flash Image API 指南
- **`docs/elevenlabs_api.md`** - ElevenLabs TTS API 指南
- **`docs/cloudflare_r2_api.md`** - Cloudflare R2 存储 API 指南

### 配置文件
- **`.env.example`** - 环境变量模板
- **`.env`** - 实际配置（由开发者填写，不提交到 git）

---

## 🎯 开发原则

### 1. Spec-Driven Development
- **所有开发必须基于文档规范**
- 实现前先确认 `docs/decisions.md` 中的相关决策
- 如遇未定义的情况，先更新文档再编码

### 2. 模块化设计
- 每个外部服务（R2、DIFY、Gemini、ElevenLabs）独立封装为 client
- Pipeline 逻辑与服务调用分离
- 配置与代码分离

### 3. 错误处理优先
- 所有外部 API 调用必须有超时设置
- 实现降级策略（参考 `docs/decisions.md` 第 6 节）
- 记录详细错误日志

### 4. 渐进式开发
- 按任务拆分逐步实现
- 每个阶段独立可测试
- 优先实现核心功能，再优化体验

---

## 🔄 交互协议

### Claude 的工作流程

1. **接收任务时**
   - 先查阅 `docs/tasks.md` 了解当前阶段和任务状态
   - 查阅相关文档索引
   - 确认 `docs/decisions.md` 中的相关决策
   - 如有未定义的点，询问开发者并更新文档

2. **编写代码时**
   - 遵循项目目录结构（见下方）
   - 引用环境变量使用 `.env.example` 中定义的名称
   - API 调用格式参考 `docs/*_api.md`
   - 返回数据格式参考 `docs/dify_schemas.md`

3. **完成任务后**
   - 更新 `docs/tasks.md` 中的任务状态（⏳ → ✅）
   - 说明实现了什么功能
   - 列出依赖的环境变量（需要开发者填写 .env）
   - 给出测试建议

### 开发者的职责

1. **决策相关**
   - 填写 `docs/decisions.md` 中标记为 ⏳ 的待确认项
   - 提供各个 API 的密钥到 `.env` 文件
   - 测试 DIFY workflows 并更新 `docs/dify_schemas.md`

2. **代码审查**
   - 检查实现是否符合文档规范
   - 验证错误处理是否完善
   - 测试实际 API 调用

---

## 📁 项目结构

```
Technica/
├── CLAUDE.md                 # 本文档（协作协议）
├── .env.example              # 环境变量模板
├── .env                      # 实际配置（开发者填写）
├── requirements.txt          # Python 依赖
├── docs/                     # 文档目录
│   ├── prd_init.md          # PRD
│   ├── pipeline.md          # 流程文档
│   ├── decisions.md         # 设计决策
│   ├── dify_schemas.md      # DIFY 返回格式
│   └── *_api.md             # API 参考
├── src/                      # 源代码
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置管理
│   ├── models/              # 数据模型（Pydantic）
│   │   ├── __init__.py
│   │   ├── request.py       # 请求模型
│   │   └── response.py      # 响应模型
│   ├── services/            # 业务逻辑
│   │   ├── __init__.py
│   │   └── pipeline.py      # 主 pipeline
│   ├── clients/             # 外部服务客户端
│   │   ├── __init__.py
│   │   ├── r2_client.py     # R2 存储
│   │   ├── dify_client.py   # DIFY API
│   │   ├── gemini_client.py # Gemini API
│   │   └── elevenlabs_client.py # ElevenLabs API
│   ├── api/                 # API 路由
│   │   ├── __init__.py
│   │   ├── images.py        # 图片上传接口
│   │   ├── cards.py         # 卡片生成接口
│   │   └── chat.py          # 问答接口
│   └── utils/               # 工具函数
│       ├── __init__.py
│       ├── logger.py        # 日志工具
│       └── errors.py        # 自定义异常
└── tests/                   # 测试（后续添加）
```

---

## 📝 开发任务拆分

### Phase 1: 项目基础 🏗️
- [x] 创建文档体系（CLAUDE.md, decisions.md, etc.）
- [ ] 搭建 FastAPI 项目结构
- [ ] 配置管理（读取 .env）
- [ ] 日志系统
- [ ] 基础数据模型（Request/Response）

### Phase 2: 存储模块 📦
- [ ] R2 客户端封装
- [ ] 图片上传功能
- [ ] 文件命名规则实现
- [ ] 图片上传 API 接口

### Phase 3: AI 服务客户端 🤖
- [ ] DIFY 客户端封装（三个 workflows）
- [ ] Gemini 客户端封装（图片高亮）
- [ ] ElevenLabs 客户端封装（TTS）
- [ ] 统一的错误处理和超时设置

### Phase 4: 核心 Pipeline 🔄
- [ ] 步骤1：照片预处理与分析
- [ ] 步骤2：并行执行（卡片生成 + 图片高亮）
- [ ] 步骤3：语音生成
- [ ] Pipeline 整合与错误处理
- [ ] 卡片生成 API 接口

### Phase 5: 问答功能 💬
- [ ] 问答 DIFY workflow 调用
- [ ] 可选的语音生成
- [ ] 问答 API 接口

### Phase 6: 优化与完善 ✨
- [ ] 错误信息优化
- [ ] 日志完善
- [ ] API 文档（OpenAPI/Swagger）
- [ ] 性能优化

---

## 🚀 当前阶段

**当前**: Phase 1 - 项目基础搭建

**下一步**: 创建 FastAPI 项目结构和配置管理

---

## 🧰 开发环境

- **Python 版本**: 3.12（`pyproject.toml` 已锁定）
- **依赖管理**: 默认使用 `uv`，首次进入项目运行 `uv sync` 即可创建/更新 `.venv`
- **运行服务**: `uv run uvicorn src.main:app --reload`
- **运行测试**: `uv run pytest`
- `.venv` 由 `uv` 自动维护并已加入 `.gitignore`，请勿手动提交本地虚拟环境

---

## ⚠️ 重要约定

### 环境变量命名
- 所有环境变量必须在 `.env.example` 中定义
- 使用大写 + 下划线命名（如 `DIFY_API_KEY_PREPROCESSING`）
- 敏感信息（API keys）绝不提交到代码仓库

### API 超时时间
- 参考 `docs/decisions.md` 第 6.5 节
- 所有外部调用使用环境变量配置超时时间

### 错误返回格式
- 统一使用 `{"success": false, "error": "error_code", "message": "..."}`
- 错误码定义在 `src/utils/errors.py`

### 日志级别
- `DEBUG`: 开发调试信息
- `INFO`: 关键流程节点（如 API 调用开始/结束）
- `WARNING`: 降级处理（如图片高亮失败但继续）
- `ERROR`: 请求失败

---

## 📌 常见问题

### Q: 新窗口如何快速了解项目状态？
**A**: 按以下顺序阅读：
1. **`CLAUDE.md`** - 了解协作协议和项目结构
2. **`docs/tasks.md`** - 查看当前阶段和任务状态
3. **`docs/decisions.md`** - 查看已确定的设计决策

### Q: 如何确定某个功能的实现细节？
**A**: 按以下顺序查找：
1. `docs/decisions.md` - 查看是否有明确决策
2. `docs/pipeline.md` - 查看流程定义
3. `docs/*_api.md` - 查看 API 使用方式
4. 如仍不清楚，询问开发者并更新 `docs/decisions.md`

### Q: DIFY 返回的数据格式不确定怎么办？
**A**: 查看 `docs/dify_schemas.md`，如果未填写，提醒开发者测试并补充

### Q: 某个环境变量找不到怎么办？
**A**: 检查 `.env.example`，如果没有定义，先更新 `.env.example` 再使用

### Q: 遇到文档冲突怎么办？
**A**: `docs/decisions.md` 的优先级最高，这是最新的决策记录

---

## 🔄 文档更新规则

- **Claude**:
  - 更新 `docs/tasks.md` 中的任务状态
  - 必要时更新 `CLAUDE.md` 中的"当前阶段"
- **开发者**:
  - 负责更新 `docs/decisions.md` 和 `docs/dify_schemas.md`
  - 填写 `.env` 文件中的配置
- **双方**: 发现文档问题时及时沟通并更新

---

**最后更新**: 2024-XX-XX
**当前版本**: v0.1 - 项目初始化阶段
