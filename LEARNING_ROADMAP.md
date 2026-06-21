# Agent 开发学习路线图（Python 后端）

> **学习者背景**：前端工程师，有 JS/TS 经验，无 Agent 开发经验
> **目标**：掌握 Python Agent 开发，能在简历中增加相关项目经历
> **创建日期**：2026-06-20

---

## 目录

- [Phase 1：基础地基（第 1-2 周）](#phase-1基础地基第-1-2-周)
- [Phase 2：Agent 核心模式（第 3-4 周）](#phase-2agent-核心模式第-3-4-周)
- [Phase 3：框架与工程化（第 5-6 周）](#phase-3框架与工程化第-5-6-周)
- [Phase 4：进阶主题（第 7-8 周）](#phase-4进阶主题第-7-8-周)
- [Phase 5：简历项目实战（第 9-10 周）](#phase-5简历项目实战第-9-10-周)
- [学习记录](#学习记录)
- [资源索引](#资源索引)

---

## Phase 1：基础地基（第 1-2 周）

> **目标**：能用 Python 调通 LLM API，理解最基本的调用模式

### 1.1 Python 速成（前端视角）

作为前端工程师，你只需要掌握这些 Python 特性即可上路：

| JS/TS 概念 | Python 等价 |
|------------|-------------|
| `const/let` | 直接赋值（无声明关键字） |
| `async/await` | `async def` / `await`（语法几乎一样） |
| `{...}` 对象 | `dict` 字典 |
| `[...]` 数组 | `list` 列表 |
| `?.` 可选链 | 无，用 `if x is not None` |
| `...spread` | `**dict` / `*list` |
| `import { x } from '...'` | `from module import x` |
| TypeScript 类型 | 类型注解 `: str` / Pydantic |

**必学库**：
- `requests` / `httpx` — HTTP 请求（对标 `fetch`/`axios`）
- `pydantic` — 数据模型 & 验证（对标 TS 的 `interface` + `zod`）
- `asyncio` — 异步编程（对标 JS 的 event loop）
- `fastapi` — Web 框架（对标 Express/Koa）

### 1.2 LLM API 初体验

**实践任务**：用 Python 调用一次 LLM API

```python
# 最小可运行示例
import requests
import os

API_KEY = os.getenv("OPENAI_API_KEY")  # 或用 Anthropic/DeepSeek

response = requests.post(
    "https://api.openai.com/v1/chat/completions",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "你是一个有用的助手"},
            {"role": "user", "content": "解释什么是 AI Agent"}
        ]
    }
)
print(response.json()["choices"][0]["message"]["content"])
```

**关键理解**：
- `messages` 数组就是"对话历史"——这是 Agent 记忆的基础
- `system` prompt 定义 Agent 的行为边界
- 返回的 `message` 需要追加到 messages 里才能实现多轮对话

### 1.3 三种 API 调用模式

| 模式 | 特点 | 适用场景 |
|------|------|----------|
| **Chat Completion** | 一问一答 | 简单对话 |
| **Streaming** | 逐字返回，`stream=True` | 打字机效果，提升 UX |
| **Function Calling** | LLM 返回结构化 JSON，指定要调用的函数 | **Agent 的核心能力** |

**实践任务**：实现一个带 function calling 的调用

```python
# LLM 决定"调用哪个函数 + 传什么参数"
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"}
                },
                "required": ["city"]
            }
        }
    }
]
# ... 在请求中传入 tools 参数，LLM 会返回 tool_calls
```

---

## Phase 2：Agent 核心模式（第 3-4 周）

> **目标**：理解 Agent 的本质，能手写一个 ReAct Agent

### 2.1 Agent 的本质是什么？

```
Agent = LLM + 工具(Tools) + 循环(Loop) + 记忆(Memory)
```

```
┌─────────────────────────────────────────┐
│                  Agent                   │
│  ┌─────────┐   ┌──────────┐             │
│  │   LLM   │◄──│  Memory  │             │
│  │  (大脑)  │   │  (记忆)   │             │
│  └────┬────┘   └──────────┘             │
│       │                                  │
│  ┌────▼─────────────────────────┐       │
│  │        Tool Executor          │       │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ │       │
│  │  │Tool 1│ │Tool 2│ │Tool 3│ │       │
│  │  └──────┘ └──────┘ └──────┘ │       │
│  └──────────────────────────────┘       │
└─────────────────────────────────────────┘
```

Agent 做的事情就是循环：
1. LLM 分析当前状态 → 决定"思考"还是"行动"
2. 如果是行动 → 调用工具 → 把结果反馈给 LLM
3. 如果是思考 → 输出最终答案
4. 重复直到任务完成

### 2.2 ReAct 模式（Reasoning + Acting）

这是最经典的 Agent 模式，**强烈建议手写一遍**：

```
Thought: 我需要知道北京的天气才能回答用户
Action: get_weather
Action Input: {"city": "北京"}
Observation: 北京今天晴，25°C
Thought: 我现在有足够信息回答用户了
Final Answer: 北京今天晴天，气温 25°C
```

**核心实现伪代码**：

```python
async def agent_loop(user_input: str, tools: list, max_turns: int = 10):
    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}]

    for _ in range(max_turns):
        response = await call_llm(messages, tools)

        if response.has_final_answer():
            return response.content

        if response.has_tool_calls():
            for tool_call in response.tool_calls:
                result = await execute_tool(tool_call)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                })
            continue  # 回到循环开始，让 LLM 分析结果

    return "达到最大轮次上限"
```

### 2.3 手写 Agent 项目

**任务**：实现一个「代码助手 Agent」，具备以下工具：

| 工具 | 功能 |
|------|------|
| `read_file` | 读取文件内容 |
| `write_file` | 写入文件 |
| `search_code` | 在项目中搜索代码（grep） |
| `run_command` | 执行 shell 命令 |
| `web_search` | 联网搜索 |

**这个项目就是你的第一个 Agent Demo。**

---

## Phase 3：框架与工程化（第 5-6 周）

> **目标**：掌握主流框架，能快速搭建生产级 Agent

### 3.1 框架对比

| 框架 | 定位 | 学习曲线 | 适用场景 |
|------|------|----------|----------|
| **OpenAI Agents SDK** | OpenAI 官方，轻量 | ⭐ 低 | 简单 Agent，快速原型 |
| **LangChain** | 最全面，生态最大 | ⭐⭐⭐ 高 | 复杂链路，RAG，企业级 |
| **LangGraph** | 有状态图编排 | ⭐⭐⭐ 高 | 多步骤工作流，状态管理 |
| **AutoGen** | 微软出品，多 Agent 对话 | ⭐⭐ 中 | 多 Agent 协作 |
| **CrewAI** | 角色化多 Agent | ⭐ 低 | 快速搭建多 Agent 团队 |
| **Agno** | 轻量级 Agent 框架 | ⭐ 低 | 简单 Agent + 工具 |

**学习建议路径**：
1. 先用 **OpenAI Agents SDK** 把 Phase 2 的手写 Agent 重写一遍（理解框架做了什么）
2. 再用 **LangChain + LangGraph** 做一个带状态的 Agent
3. 用 **CrewAI** 体验多 Agent 协作

### 3.2 OpenAI Agents SDK 示例

```python
from agents import Agent, Runner, function_tool

@function_tool
def get_weather(city: str) -> str:
    """获取城市天气"""
    return f"{city}：晴天，25°C"

agent = Agent(
    name="助手",
    instructions="你是一个有帮助的助手",
    tools=[get_weather],
)

result = await Runner.run(agent, "北京天气怎么样？")
print(result.final_output)
```

### 3.3 FastAPI + Agent = 后端服务

```python
# 将 Agent 包装成 API，前端可以调用
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from agents import Agent, Runner

app = FastAPI()
agent = Agent(name="API-Agent", tools=[...])

@app.post("/chat")
async def chat(message: str):
    result = await Runner.run(agent, message)
    return {"reply": result.final_output}

@app.post("/chat/stream")
async def chat_stream(message: str):
    async def generate():
        result = Runner.run_streamed(agent, message)
        async for event in result.stream_events():
            if event.type == "raw_response_event":
                yield f"data: {event.data.delta}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

## Phase 4：进阶主题（第 7-8 周）

> **目标**：掌握让 Agent 更"聪明"的关键技术

### 4.1 RAG（检索增强生成）

解决 LLM 知识过时 / 私有知识问题：

```
用户问题 → Embedding → 向量检索 → 相关文档 → 拼入 Prompt → LLM 回答
```

**技术栈**：`text-embedding-3-small` + `ChromaDB/Pinecone` + LangChain

### 4.2 Agent 记忆系统

| 记忆类型 | 存储内容 | 实现方式 |
|----------|----------|----------|
| **短期记忆** | 当前对话的 messages | 直接拼在上下文 |
| **长期记忆** | 历史对话摘要 | 向量数据库 + 检索 |
| **工作记忆** | 当前任务的状态/中间结果 | 结构化 JSON 存储 |

### 4.3 多 Agent 协作

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│ Planner  │───►│ Coder    │───►│ Reviewer │
│ Agent    │    │ Agent    │    │ Agent    │
└──────────┘    └──────────┘    └──────────┘
```

### 4.4 安全与防护

- **Prompt Injection**：用户输入包含越狱指令
- **工具权限控制**：限制 Agent 能执行的操作
- **Human-in-the-loop**：关键操作需要人工确认

### 4.5 评估与观测

- **LangSmith / LangFuse**：Agent 执行追踪
- **评估指标**：任务完成率、工具调用准确率、响应延迟

---

## Phase 5：简历项目实战（第 9-10 周）

> **目标**：完成一个可以写进简历的 Full-Stack Agent 项目

### 推荐项目方向（选一个）

| 项目 | 描述 | 亮点 |
|------|------|------|
| **智能代码审查助手** | Agent 自动 Review PR，给出建议 | 实用 + 工具调用 |
| **数据分析 Agent** | 自然语言 → SQL → 图表 | RAG + 多步骤推理 |
| **客服 Agent 系统** | 多 Agent 协作处理工单 | 多 Agent + 人工介入 |
| **个人知识库助手** | 接入自己的笔记/文档，智能问答 | RAG + 记忆 |

### 技术栈建议

```
前端（你的舒适区）          后端 Agent
┌──────────────┐         ┌──────────────┐
│  React / Vue  │◄──SSE──►│   FastAPI    │
│  对话 UI      │         │  Agent Core  │
│  流式渲染     │         │  LangChain   │
│  工具结果展示  │         │  RAG Pipeline │
└──────────────┘         └──────────────┘
```

---

## 学习记录

> 每次学习交互的记录会追加在此，形成知识沉淀。

<!-- 学习记录将追加在下方 -->

### 2026-06-20｜Session 1：学习路线搭建

**交互内容**：

- 明确学习目标：前端工程师转型 Full-Stack Agent 开发，简历增项
- 背景确认：JS/TS 熟练，Python 需补齐，Agent 开发零基础
- 制定了 5 阶段、10 周学习路线图

**关键决策**：

1. **先手写后框架**：Phase 2 手写 ReAct Agent，Phase 3 才引入框架。这样理解底层原理，面试有深度
2. **框架选择路线**：OpenAI Agents SDK（入门）→ LangChain+LangGraph（企业级）→ CrewAI（多 Agent）
3. **后端选型**：FastAPI + SSE Streaming，前端用你熟悉的 React/Vue 对接
4. **简历项目**：从 4 个方向中选一个做 Full-Stack Agent 应用

**下一步行动**：

- [x] 确认 Python 环境就绪（Python 3.11.9 已安装）
- [x] 确认 LLM API：**DeepSeek**（国内可用，无需翻墙，OpenAI 兼容格式）
- [x] 选择简历项目方向：**数据分析 Agent**
- [x] 开始 Phase 1：Demo 代码已创建（`demo.py`）

---

### 2026-06-20｜Session 2：环境搭建 + API 选型 + Demo

**API 推荐结论**：

| API | 需要翻墙 | 价格（每百万 token） | 推荐度 |
|-----|----------|------|--------|
| **DeepSeek** | ❌ 不需要 | ~¥1 | ⭐⭐⭐ 首选 |
| 阿里通义千问 | ❌ 不需要 | ~¥0.8 | ⭐⭐ 备选 |
| 智谱 GLM | ❌ 不需要 | ~¥1 | ⭐⭐ 备选 |
| OpenAI | ✅ 需要 | ~$15 | ⭐ 备选 |
| Anthropic Claude | ✅ 需要 | ~$15 | ⭐ 备选 |

> **推荐 DeepSeek**：① 国内直接访问 ② API 100% 兼容 OpenAI，后续换模型只改 `base_url` ③ 性价比极高 ④ 代码和中文能力强 ⑤ 新用户有免费额度

**Python 环境**：
- Python 3.11.9 通过 winget 安装于 `C:\Users\admin\AppData\Local\Programs\Python\Python311\`
- ⚠️ **PATH 问题待修复**：Windows App Execution Aliases 拦截了 `python` 命令（见下方"下一步行动"）
- 已安装依赖：`openai`, `python-dotenv`, `httpx`

**当前文件结构**：
```
D:\front\agent\
├── LEARNING_ROADMAP.md   ← 学习主文档
├── demo.py               ← 核心 Demo（4 个子 Demo）
├── .env.example          ← API Key 配置模板
├── requirements.txt      ← Python 依赖
└── run_demo.bat          ← Windows 双击运行
```

**`demo.py` 4 个子 Demo**：

| Demo | 学什么 | 前端对应 |
|------|--------|----------|
| `demo_basic_chat()` | messages 结构、API 调用、Token 用量 | `fetch` 请求 |
| `demo_streaming()` | 流式输出 `stream=True` | SSE / EventSource |
| `demo_function_calling()` | 工具定义 + LLM 返回 tool_calls | Agent 核心能力 |
| `demo_experiment()` | 自由修改 prompt/参数 观察变化 | 实验区 |

**关键知识点 — Function Calling**：
```python
# LLM 不会执行工具！它只是返回：
# → "我应该调用 query_database(sql="SELECT ...")"
# 你的代码负责：
# 1. 收到 tool_calls → 执行 sql → 拿到结果
# 2. 把结果拼回 messages → 再次调用 LLM
# 3. 循环直到 LLM 认为任务完成
# 这就是 Agent 循环的本质！
```

**下一步行动**：
- [ ] **修复 PATH**：Windows 设置 → 搜索「管理应用执行别名」→ 关闭 Python 的别名
- [ ] **获取 API Key**：https://platform.deepseek.com 注册并创建 Key（新用户有免费额度）
- [x] **运行 Demo**：`demo.py` 已跑通 ✅
- [x] **动手修改**：已修改 Demo 1-4，理解数据结构
- [ ] **运行 agent_v1.py**：体验真正的 Agent 循环

---

### 2026-06-20｜Session 3：Python 基础补齐（前端对照）

**Python vs JS 基础对照**：

| 概念 | JS | Python |
|------|-----|--------|
| 函数定义 | `function foo() {}` | `def foo():` + 缩进 |
| 打印对象属性 | `console.log(obj)` | `pprint(vars(obj))` 或 `obj.__dict__` |
| 看有哪些 key | `Object.keys(obj)` | `dir(obj)` |
| 看类型 | `typeof obj` | `type(obj)` |
| 热更新 | HMR（Vite/Webpack） | 手动 `↑` + `Enter` 重跑 |

**Python 的 `print(obj)` 为什么不像 JS console.log**：
Python 默认只显示 `<ClassName at 0x内存地址>`，不像 JS 展开所有属性。这是 Python 的保守哲学——你不说我就不猜。想看内部用 `pprint(vars(obj))`。

**单线程对比**：
- JS：Event Loop + Promise（你熟的）
- Python：`asyncio` + `async/await`（语法一模一样）
- Python 有 GIL，多线程不加速 CPU 密集任务，但 Agent 开发 99% 是 IO 密集型（LLM API 调用），碰不到这个坑

**VS Code Python 插件**：
- 必装：Python + Python Debugger + Pylance
- 推荐：Black Formatter / Ruff

---

### 2026-06-20｜Session 4：Agent 概念——它解决了什么问题

**三层递进**：普通对话 → Skill → Agent

| | 普通对话 | Skill/预设指令 | Agent |
|---|---|---|---|
| 工作方式 | 一问一答 | 预置路线，按路线走 | 自己做一步看一步 |
| 路线 | 无 | 死的，你写好的 | 活的，LLM 自己决策 |
| 前端类比 | 静态 HTML | 表单向导（固定步骤） | SPA + 动态路由 |

**Agent 解决的核心问题**：AI 能"动手"了——不只是回答问题，而是调用工具、查询数据、执行代码，根据每一步的结果自主决定下一步该做什么。

**用 Agent ≠ 能造 Agent**：Claude Code 是别人造的写代码专用 Agent，你学的是给任何业务场景造定制 Agent 的能力。

---

### 2026-06-20｜Session 5：Phase 2 启动——手写 ReAct Agent

**创建文件**：`agent_v1.py`

**什么是 ReAct Agent**：
```
用户输入
   │
   ▼
┌──────────────────────────────────────┐
│  🔄 Agent 循环（最多 MAX_TURNS 轮）   │
│                                      │
│  ① LLM 分析 messages + 可用工具列表   │
│  ② LLM 决定：直接回答 还是 调用工具？  │
│     ├─ 直接回答 → 输出最终答案 ✅      │
│     └─ 调用工具 → ③ 你的代码执行工具   │
│                  ④ 结果追加到 messages │
│                  ⑤ 回到 ① 继续循环     │
└──────────────────────────────────────┘
```

**agent_v1.py 的 3 个真实工具**：

| 工具 | 功能 | 注释 |
|------|------|------|
| `calculate(expression)` | 安全计算数学表达式 | 用 `eval` 限制白名单 |
| `generate_sample_data(type, rows)` | 生成 sales/users/products 示例 CSV | 模拟真实数据源 |
| `run_python(code)` | 执行任意 Python 代码并捕获输出 | **最强工具**——Agent 能自己做数据分析 |

**核心代码——agent_loop() 的 4 种情况**：

```python
for turn in range(MAX_TURNS):
    response = llm.chat(messages, tools)

    msg = response.choices[0].message

    # 情况 1: LLM 直接回答 → 结束
    if msg.content and not msg.tool_calls:
        return msg.content

    # 情况 2: LLM 要调工具
    if msg.tool_calls:
        messages.append(msg)           # 记录 LLM 的决策
        for tc in msg.tool_calls:
            result = TOOL_MAP[tc.name](**tc.args)  # 真正执行！
            messages.append(result)     # 结果喂回去
        continue  # ← 回到循环开头，让 LLM 处理结果
```

**前端对照理解**：
```javascript
// Agent 循环 ≈ 这个 JS 伪代码
while (turn < maxTurns) {
    const response = await llm.chat(messages, tools);
    if (response.finishReason === 'stop') return response.content;
    if (response.toolCalls) {
        const results = response.toolCalls.map(tc => executeTool(tc));
        messages.push(...results);  // 结果喂回去
        // 继续循环
    }
}
```

**下一步行动**：
- [ ] 运行 `python agent_v1.py`，观察 Agent 如何自主决定调用哪些工具、调用顺序、以及它如何处理工具返回的数据
- [ ] 修改 `test_cases` 列表，加入你自己想测试的问题
- [ ] 观察：Agent 在第几轮调用工具？每轮调了什么？最终答案是否基于实际数据？

---

## 资源索引

### 必读
- [Anthropic Agent 开发指南](https://docs.anthropic.com/en/docs/build-with-claude/agent-patterns)
- [OpenAI Agents SDK 文档](https://platform.openai.com/docs/guides/agents)
- [LangChain 官方教程](https://python.langchain.com/docs/tutorials/)

### 推荐
- Lilian Weng 博客：[LLM Powered Autonomous Agents](https://lilianweng.github.io/posts/2023-06-23-agent/)
- Chip Huyen：《Building LLM Apps》
- Anthropic Cookbook：[Building Effective Agents](https://github.com/anthropics/anthropic-cookbook)

### 视频
- Andrew Ng《AI Agentic Design Patterns》
- DeepLearning.AI 的 LangChain 系列课程

---

> 📝 **本文档会随着学习进度持续更新。每次交互的关键知识点、代码示例、踩坑记录都会沉淀到这里。**
