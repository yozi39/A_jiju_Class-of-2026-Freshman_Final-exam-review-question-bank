import re

from langchain_openai import ChatOpenAI


DEEPSEEK_BASE_URL = "https://api.deepseek.com"


def normalize_ai_markdown(content: str) -> str:
    """将模型常用的数学分隔符转换为 Streamlit 兼容格式。"""
    text = content.strip()

    # 有些模型会把整篇 Markdown 包在代码块中，代码块内公式不会渲染。
    fenced_markdown = re.fullmatch(
        r"```(?:markdown|md)?\s*\n?(.*?)\n?```", text, flags=re.DOTALL | re.IGNORECASE
    )
    if fenced_markdown:
        text = fenced_markdown.group(1).strip()

    # Streamlit 对美元符号形式的 KaTeX 分隔符支持更稳定。
    text = re.sub(r"\\\[(.*?)\\\]", r"$$\1$$", text, flags=re.DOTALL)
    text = re.sub(r"\\\((.*?)\\\)", r"$\1$", text, flags=re.DOTALL)
    return text


def build_explanation_prompt(question: dict) -> str:
    """把一道题整理成可复制、也可直接交给模型的提示词。"""
    options = question.get("options", [])
    option_text = "\n".join(options) if options else "无（本题不是选择题）"

    return f"""你是一位耐心、严谨的大学数学老师，请讲解下面这道期末复习题。

课程：{question["course"]}
章节：{question["chapter"]}
题型：{question["type"]}

题目：
{question["question"]}

选项：
{option_text}

题库参考答案：
{question["answer"]}

题库参考解析：
{question["analysis"]}

请完成以下任务：
1. 先独立验算，不要盲从参考答案；如果参考答案有误，请明确指出。
2. 分步骤解释解题思路，说明每一步为什么这样做。
3. 总结本题考查的知识点和容易犯的错误。
4. 最后给出一道简短的同类练习题，但不要立即给练习题答案。

请使用中文 Markdown。数学表达式统一使用 LaTeX：行内公式放在 $...$ 中，独立公式放在 $$...$$ 中，以便 Streamlit 正确渲染。"""


def generate_explanation(
    prompt: str,
    api_key: str,
    temperature: float = 0.3,
    model: str = "deepseek-v4-flash",
) -> str:
    """仅在页面按钮触发时调用 DeepSeek，不保存 API Key。"""
    if not api_key:
        raise ValueError("缺少 DeepSeek API Key")

    chat_model = ChatOpenAI(
        api_key=api_key,
        base_url=DEEPSEEK_BASE_URL,
        model=model,
        temperature=temperature,
        timeout=60,
        max_retries=1,
    )
    response = chat_model.invoke(prompt)
    if isinstance(response.content, str):
        return normalize_ai_markdown(response.content)
    return normalize_ai_markdown(str(response.content))
