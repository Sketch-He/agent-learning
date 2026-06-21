# Agent 学习项目

## 用户身份
前端工程师（JS/TS 熟练），零 Agent 开发经验，正在学习 Python Agent 开发以增加简历项目经历。

## 学习目标
完成 5 阶段学习路线，最终做一个 **数据分析 Agent** 的 Full-Stack 简历项目。

## 技术选型（已确认）
- **LLM API**：DeepSeek（国内可用，OpenAI 兼容格式，¥1/百万 token）
- **后端**：Python 3.11.9 + FastAPI（已安装）
- **前端**：React/Vue + SSE Streaming
- **框架路线**：手写 Agent → OpenAI Agents SDK → LangChain+LangGraph

## 当前进度
- [x] Python 环境安装
- [x] API 选型（DeepSeek）
- [x] Demo 跑通（demo.py 四个子 Demo）
- [x] VS Code 插件配置
- [x] **Phase 2 进行中：手写 ReAct Agent（agent_v1.py）**
- [ ] 简历项目开发

## 关键文件
- `LEARNING_ROADMAP.md` — 完整学习路线图 + 所有 Session 记录（**必读**）
- `demo.py` — Phase 1：LLM API 调用的 4 个 Demo
- `agent_v1.py` — Phase 2：手写 ReAct Agent 循环（核心学习文件）
- `.env` — API Key 配置（已配置）

## 每次交互规则
1. 将新知识沉淀到 `LEARNING_ROADMAP.md` 的「学习记录」部分
2. 将关键上下文更新到项目 memory 文件
3. 保持"前端工程师视角"的教学方式
