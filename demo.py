"""
Agent 学习 Demo —— 你的第一个 LLM API 调用
============================================
这是一个可修改、可运行的入门 demo。
修改代码 → 运行 → 观察输出变化，是学习最快的方式。

当前使用 DeepSeek API（国内可直接访问，无需翻墙）。
API 格式兼容 OpenAI，后续换 OpenAI/Anthropic 只需改 base_url 和 model。

运行方式：
  1. 复制 .env.example 为 .env，填入你的 DeepSeek API Key
  2. python demo.py
"""

import os
from pathlib import Path
from urllib import response

# 加载 .env 文件（如果存在）
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

from openai import OpenAI

# ============================================================
# 🔧 配置区 —— 改这里看效果
# ============================================================

# DeepSeek API（国内可用，无需翻墙）
# 获取 Key: https://platform.deepseek.com/api_keys
API_KEY = os.getenv("DEEPSEEK_API_KEY", "your-api-key-here")
BASE_URL = "https://api.deepseek.com/v1"
MODEL = "deepseek-chat"  # 可改为 deepseek-reasoner 体验推理模型

# 对话参数 —— 试着改改看
TEMPERATURE = 1   # 0=严谨, 1=创意, 范围 0~2
MAX_TOKENS = 500    # 最大回复长度
SYSTEM_PROMPT = "你是一个帮助学习 Agent 开发的助手，回答简洁、结构化。"

# ============================================================
# 💬 Demo 1: 基础对话 —— 了解 messages 结构
# ============================================================

def demo_basic_chat():
    """最简单的一问一答。重点观察 messages 结构和返回的 JSON。"""
    # print("\n" + "=" * 60)
    # print("📝 Demo 1: 基础对话")
    # print("=" * 60)

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "你是什么ai？"},
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )
    print(response.model_dump_json(indent=2))
    # print(f"💬 回复内容:\n{response}")
    # 打印完整返回（看看结构长什么样）
    # print(f"✅ 模型: {response.model}")
    # print(f"📊 Token 用量: {response.usage}")
    # print(f"💬 回复内容:\n{response.choices[0].message.content}")

    return response


# ============================================================
# 🌊 Demo 2: 流式输出 —— 理解打字机效果
# ============================================================

def demo_streaming():
    """逐字返回，前端 SSE 对接的就是这个。"""
    print("\n" + "=" * 60)
    print("🌊 Demo 2: 流式输出（Streaming）")
    print("=" * 60)

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    from pprint import pprint
    pprint(vars(client))
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "用 markdown 列出 Agent 开发的三个核心概念"},
    ]

    stream = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        stream=True,  # ← 就这一个参数！
    )

    print("💬 实时输出: ", end="", flush=True)
    full_content = ""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            text = chunk.choices[0].delta.content
            print(text, end="", flush=True)  # 逐字打印
            full_content += text

    print(f"\n\n📊 完整内容长度: {len(full_content)} 字符")
    return full_content


# ============================================================
# 🔧 Demo 3: Function Calling —— Agent 的核心能力
# ============================================================

# 定义一个"工具"——就像你给前端组件定义 props 一样
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_database",
            "description": "执行 SQL 查询，返回表格数据。用于数据分析场景。",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "要执行的 SQL 查询语句",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回行数上限，默认 100",
                        "default": 100,
                    },
                },
                "required": ["sql"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_chart",
            "description": "根据数据生成图表配置（ECharts option）",
            "parameters": {
                "type": "object",
                "properties": {
                    "chart_type": {
                        "type": "string",
                        "enum": ["bar", "line", "pie", "scatter"],
                        "description": "图表类型",
                    },
                    "title": {
                        "type": "string",
                        "description": "图表标题",
                    },
                    "data_description": {
                        "type": "string",
                        "description": "数据描述，用于生成示例数据",
                    },
                },
                "required": ["chart_type", "title"],
            },
        },
    },
]


def demo_function_calling():
    """LLM 不会执行工具，它只会返回'要调用哪个工具 + 参数'。
    实际执行由你的代码完成——这就是 Agent 循环的核心。"""
    # print("\n" + "=" * 60)
    # print("🔧 Demo 3: Function Calling（工具调用）")
    # print("=" * 60)

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    # 模拟用户的数据分析请求
    messages = [
        {"role": "system", "content": "你是一个数据分析助手。用户提出分析需求时，"
                                       "你需要调用 query_database 或 generate_chart 工具来完成任务。"},
        {"role": "user", "content": "帮我查询上个月销量前 10 的产品，然后用柱状图展示"},
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,  # ← 把工具列表传给 LLM
        temperature=0.3,  # function calling 建议低温度，更稳定
    )

    choice = response.choices[0]
    msg = choice.message

    print(f"🤔 LLM 决定: finish_reason={choice.finish_reason}")

    if msg.content:
        print(f"💬 文本回复: {msg.content}")

    if msg.tool_calls:
        for i, tc in enumerate(msg.tool_calls):
            print(f"\n🔨 工具调用 #{i+1}:")
            print(f"   函数名: {tc.function.name}")
            print(f"   参数: {tc.function.arguments}")

        # print("\n💡 关键理解:")
        # print("   LLM 没有执行这些函数——它只是返回了要调用什么。")
        # print("   你的代码拿到 tool_calls → 执行对应函数 → 把结果返回给 LLM → 继续循环")
        # print("   这就是 Agent 循环的本质！")

    return response


# ============================================================
# 🧪 实验区 —— 在这里自由修改
# ============================================================

def demo_experiment():
    """修改这里的参数和 prompt，观察输出变化"""
    # print("\n" + "=" * 60)
    # print("🧪 Demo 4: 实验区")
    # print("=" * 60)

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    # 👇 改这里！试试不同的 prompt / temperature
    YOUR_PROMPT = "用 JSON 格式列举 5 个数据分析 Agent 可以使用的工具"
    YOUR_TEMP = 0.3

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": YOUR_PROMPT}],
        temperature=YOUR_TEMP,
        max_tokens=MAX_TOKENS,
    )

    print(f"💬 {response.choices[0].message.content}")


# ============================================================
# 🏃 主入口
# ============================================================

if __name__ == "__main__":
    # print("🚀 Agent 学习 Demo 启动")
    # print(f"🔑 API: {BASE_URL}")
    # print(f"🤖 Model: {MODEL}")
    # print(f"🌡️  Temperature: {TEMPERATURE}")

    if API_KEY == "your-api-key-here":
        print("\n⚠️  请先配置 API Key:")
        print("   1. 复制 .env.example → .env")
        print("   2. 在 .env 中设置 DEEPSEEK_API_KEY=你的key")
        print("   3. 重新运行 python demo.py")
        exit(1)

    # 按顺序运行所有 demo
    # demo_basic_chat()
    # demo_streaming()
    # demo_function_calling()
    demo_experiment()

    # print("\n" + "=" * 60)
    # print("✅ 全部 Demo 完成！现在试试修改源代码看效果吧。")
    # print("=" * 60)
