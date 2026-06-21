"""
Phase 2：手写 ReAct Agent —— 真正会"动手"的 AI
=================================================

这个文件是 Agent 开发中最核心的一课。前面 demo.py 你看到了：
  - LLM 返回 tool_calls（"我想调这个函数"）
  - 但你的代码没执行它

现在 —— 你的代码真的去执行，然后把结果喂回去，让 LLM 继续思考。
这就是 Agent 循环。

架构：
  用户输入 → [LLM 思考 → 调工具 → 执行 → 返回结果 → LLM 再思考] → 最终答案
            └──────────────── 这个循环就是 Agent ────────────────┘

运行：python agent_v1.py
"""

import os
import sys
import io
import json
import math as _math
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

from openai import OpenAI

# ============================================================
# 🔧 配置
# ============================================================

API_KEY = os.getenv("DEEPSEEK_API_KEY", "your-api-key-here")
BASE_URL = "https://api.deepseek.com/v1"
MODEL = "deepseek-chat"
MAX_TURNS = 8        # 最多循环 8 轮，防止死循环
TEMPERATURE = 0.3    # Agent 场景建议低温度，决策更稳定

# ============================================================
# 🔨 工具定义 —— Agent 的"手"
# ============================================================

def tool_calculate(expression: str) -> str:
    """
    安全计算数学表达式。
    支持：加减乘除、幂运算、三角函数、sqrt、log 等
    示例：'2 ** 10 + sum([1,2,3])' → '1030'
    """
    try:
        # 只允许安全的内置函数
        allowed = {
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "len": len, "range": range, "list": list,
            "int": int, "float": float, "str": str,
            "sqrt": _math.sqrt, "sin": _math.sin, "cos": _math.cos,
            "log": _math.log, "log10": _math.log10, "pi": _math.pi,
            "e": _math.e, "pow": pow,
        }
        result = eval(expression, {"__builtins__": {}}, allowed)
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"


def tool_generate_sample_data(dataset_type: str, rows: int = 20) -> str:
    """
    生成示例 CSV 数据，供数据分析练习使用。

    dataset_type 可选值：
      - 'sales'    : 销售数据（日期、产品、金额、数量、地区）
      - 'users'    : 用户数据（ID、姓名、年龄、城市、消费额）
      - 'products' : 产品数据（ID、名称、类目、价格、库存、评分）
    """
    import random
    random.seed(42)

    if dataset_type == "sales":
        header = "date,product,amount,quantity,region"
        products = ["手机", "电脑", "耳机", "键盘", "显示器", "平板"]
        regions = ["华东", "华南", "华北", "西南"]
        lines = [header]
        for i in range(rows):
            date = f"2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
            product = random.choice(products)
            amount = round(random.uniform(100, 9999), 2)
            quantity = random.randint(1, 50)
            region = random.choice(regions)
            lines.append(f"{date},{product},{amount},{quantity},{region}")
        return "\n".join(lines)

    elif dataset_type == "users":
        header = "id,name,age,city,total_spent"
        names = ["张三", "李四", "王五", "赵六", "陈七", "周八", "吴九", "郑十"]
        cities = ["北京", "上海", "深圳", "杭州", "成都", "广州"]
        lines = [header]
        for i in range(rows):
            name = random.choice(names)
            age = random.randint(18, 65)
            city = random.choice(cities)
            spent = round(random.uniform(100, 50000), 2)
            lines.append(f"{i+1},{name},{age},{city},{spent}")
        return "\n".join(lines)

    elif dataset_type == "products":
        header = "id,name,category,price,stock,rating"
        categories = ["电子产品", "家居", "服装", "食品", "图书"]
        product_names = [
            "iPhone 15", "MacBook Pro", "无线耳机", "机械键盘",
            "羽绒被", "办公椅", "T恤", "牛仔裤",
            "有机牛奶", "巧克力礼盒", "Python编程", "三体全集"
        ]
        lines = [header]
        for i in range(rows):
            name = random.choice(product_names)
            cat = random.choice(categories)
            price = round(random.uniform(9.9, 9999), 2)
            stock = random.randint(0, 500)
            rating = round(random.uniform(2.0, 5.0), 1)
            lines.append(f"{i+1},{name},{cat},{price},{stock},{rating}")
        return "\n".join(lines)

    else:
        return f"未知数据集类型 '{dataset_type}'，可选：sales / users / products"


def tool_run_python(code: str) -> str:
    """
    执行一段 Python 代码，捕获并返回其标准输出。
    适用于：数据统计、转换计算、文本处理等。

    注意：这是学习用的，生产环境需要沙箱隔离。
    """
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        exec(code, {"__builtins__": __builtins__})
        output = sys.stdout.getvalue()
        if not output:
            output = "(代码执行成功，无输出)"
        return output.strip()
    except Exception as e:
        return f"代码执行错误: {type(e).__name__}: {e}"
    finally:
        sys.stdout = old_stdout


# ── 工具注册表（告诉 LLM 有哪些工具，也告诉你的代码如何执行） ──

TOOL_MAP = {
    "calculate":            tool_calculate,
    "generate_sample_data": tool_generate_sample_data,
    "run_python":           tool_run_python,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "安全计算数学表达式。支持四则运算、幂运算、三角函数、sqrt、log、sum 等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如 '2**10 + sqrt(144)'",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_sample_data",
            "description": "生成示例数据集（CSV 格式）。用于数据分析练习。",
            "parameters": {
                "type": "object",
                "properties": {
                    "dataset_type": {
                        "type": "string",
                        "enum": ["sales", "users", "products"],
                        "description": "数据类型：sales=销售数据, users=用户数据, products=产品数据",
                    },
                    "rows": {
                        "type": "integer",
                        "description": "生成行数，默认 20",
                        "default": 20,
                    },
                },
                "required": ["dataset_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_python",
            "description": "执行 Python 代码并返回输出。可用于数据统计、计算、文本处理等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "要执行的 Python 代码",
                    }
                },
                "required": ["code"],
            },
        },
    },
]

# ============================================================
# 🧠 Agent 循环 —— 整个 Agent 开发里最重要的 30 行代码
# ============================================================

SYSTEM_PROMPT = """你是一个数据分析助手。你可以使用工具来完成用户的任务。

工作方式：
1. 分析用户需求，确定需要什么数据或计算
2. 调用工具获取数据或执行计算
3. 根据工具返回的结果，判断是否需要继续调用更多工具
4. 当你有了足够的信息，给出最终答案

原则：
- 先获取数据，再分析
- 每次工具调用后，仔细检查返回结果再决定下一步
- 最终答案要基于实际数据，不要编造
- 用中文回答，输出可以包含 markdown 格式"""


def agent_loop(user_input: str, verbose: bool = True) -> str:
    """
    Agent 循环 —— 这就是一切 Agent 框架的核心。

    流程：
      LLM 分析输入 → 需要工具？→ 执行 → 结果喂回 → LLM 再分析 → ... → 最终答案
    """
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]

    for turn in range(1, MAX_TURNS + 1):
        if verbose:
            print(f"\n{'─' * 50}")
            print(f"🔄 第 {turn} 轮")
            print(f"{'─' * 50}")

        # ── 调用 LLM ──
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            temperature=TEMPERATURE,
        )

        msg = response.choices[0].message

        # ── 情况 1：LLM 输出文本（没有调工具）→ 任务完成 ──
        if msg.content and not msg.tool_calls:
            if verbose:
                print(f"✅ Agent 给出最终答案")
            return msg.content

        # ── 情况 2：LLM 调用了工具 ──
        if msg.tool_calls:
            # 把 LLM 的 tool_calls 决策加入对话历史
            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            })

            for tc in msg.tool_calls:
                func_name = tc.function.name
                func_args = json.loads(tc.function.arguments)

                if verbose:
                    print(f"🔨 调用工具: {func_name}")
                    print(f"   参数: {json.dumps(func_args, ensure_ascii=False)}")

                # ── 真正执行工具！这就是 Agent 的"手" ──
                tool_func = TOOL_MAP.get(func_name)
                if tool_func:
                    result = tool_func(**func_args)
                else:
                    result = f"错误：未知工具 {func_name}"

                if verbose:
                    preview = result[:200] + "..." if len(result) > 200 else result
                    print(f"📊 结果: {preview}")

                # 把工具执行结果加入对话历史
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

            # 继续循环，让 LLM 处理工具结果
            continue

    # 达到最大轮次
    return "达到最大轮次上限，任务未完成。请简化你的问题。"


# ============================================================
# 🎮 交互式运行
# ============================================================

if __name__ == "__main__":
    # ── 测试用例 ──
    test_cases = [
        # 简单计算（不用工具也能答，但试试看 Agent 会不会主动调 calculate）
        # "帮我算一下，一个圆半径 5.5，面积是多少？同时算一下 sqrt(3^2 + 4^2)",

        # 数据生成 + 分析（必须用工具）
        "生成一份 sales 数据（30 行），然后分析：哪个区域销售额最高？销售额最高的 3 个产品是什么？",

        # 自由探索
        # "用 run_python 生成 100 个正态分布随机数，计算均值和标准差",
    ]

    # print("=" * 60)
    # print("🤖 Phase 2: ReAct Agent — 手写 Agent 循环")
    # print(f"   模型: {MODEL}  |  最大轮次: {MAX_TURNS}  |  温度: {TEMPERATURE}")
    # print("=" * 60)

    # if API_KEY == "your-api-key-here":
    #     print("\n⚠️  请先在 .env 文件中设置 DEEPSEEK_API_KEY")
    #     exit(1)

    for i, question in enumerate(test_cases, 1):
        print(f"\n{'█' * 60}")
        print(f"👤 用户 #{i}: {question}")
        print(f"{'█' * 60}")

        answer = agent_loop(question, verbose=True)

        print(f"\n{'─' * 60}")
        print(f"📝 最终答案:\n{answer}")
        print(f"{'─' * 60}")

        if i < len(test_cases):
            input("\n⏎ 按 Enter 继续下一个测试...")

    # print("\n" + "=" * 60)
    # print("✅ Phase 2 Demo 完成！")
    # print("   你现在看懂了 Agent 循环的全貌。")
    # print("   试试修改 test_cases 里的问题，看 Agent 怎么应对。")
    # print("=" * 60)
