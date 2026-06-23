import json
import random
import re
from pathlib import Path

import streamlit as st

from ai_utils import (
    build_explanation_prompt,
    generate_explanation,
    normalize_ai_markdown,
)


QUESTION_BANK_PATH = Path(__file__).with_name("question_bank.json")
REQUIRED_FIELDS = {
    "id",
    "course",
    "chapter",
    "type",
    "question",
    "answer",
    "analysis",
    "tags",
}


@st.cache_data
def load_questions(file_path: Path = QUESTION_BANK_PATH) -> list[dict]:
    """读取题库，并尽早报告常见的 JSON 格式问题。"""
    try:
        with file_path.open("r", encoding="utf-8") as file:
            questions = json.load(file)
    except FileNotFoundError as error:
        raise RuntimeError(f"找不到题库文件：{file_path}") from error
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"题库 JSON 格式错误：第 {error.lineno} 行，第 {error.colno} 列"
        ) from error

    if not isinstance(questions, list):
        raise RuntimeError("题库最外层必须是 JSON 数组。")

    for position, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            raise RuntimeError(f"第 {position} 道题必须是 JSON 对象。")
        missing_fields = REQUIRED_FIELDS - question.keys()
        if missing_fields:
            missing = "、".join(sorted(missing_fields))
            raise RuntimeError(f"第 {position} 道题缺少字段：{missing}")
        if not isinstance(question["tags"], list):
            raise RuntimeError(f"第 {position} 道题的 tags 必须是数组。")

    return questions


def filter_questions(
    questions: list[dict], course: str, chapter: str, question_type: str
) -> list[dict]:
    """按照三个筛选条件返回题目；“全部”表示不限制。"""
    return [
        question
        for question in questions
        if (course == "全部" or question["course"] == course)
        and (chapter == "全部" or question["chapter"] == chapter)
        and (question_type == "全部" or question["type"] == question_type)
    ]


def get_option_label(text: str, fallback_index: int | None = None) -> str | None:
    """从“A. 内容”中提取选项字母；没有字母时按位置生成。"""
    match = re.match(r"^\s*([A-Z])(?:[.、。:：]|\s|$)", text)
    if match:
        return match.group(1)
    if fallback_index is not None and 0 <= fallback_index < 26:
        return chr(ord("A") + fallback_index)
    return None


st.set_page_config(page_title="期末复习题库助手", page_icon="📚", layout="centered")
st.title("📚 期末复习题库助手")
st.caption("从试卷图片整理题目，用筛选和随机抽题帮助你复习。")

try:
    questions = load_questions()
except RuntimeError as error:
    st.error(str(error))
    st.stop()

with st.sidebar:
    st.header("复习设置")
    api_key = st.text_input("DeepSeek API Key", type="password")
    st.caption(
        "API Key 只用于本次调用，不会保存；如果担心安全，可以只使用复制 Prompt 功能。"
    )

    course_options = ["全部"] + sorted(
        {question["course"] for question in questions}
    )
    selected_course = st.selectbox("课程", course_options)

    questions_in_course = filter_questions(
        questions, selected_course, "全部", "全部"
    )
    chapter_options = ["全部"] + sorted(
        {question["chapter"] for question in questions_in_course}
    )
    selected_chapter = st.selectbox("章节", chapter_options)

    questions_in_chapter = filter_questions(
        questions, selected_course, selected_chapter, "全部"
    )
    type_options = ["全部"] + sorted(
        {question["type"] for question in questions_in_chapter}
    )
    selected_type = st.selectbox("题型", type_options)
    temperature = st.slider(
        "AI 回答随机性（temperature）",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.1,
    )
    selected_model = st.selectbox(
        "DeepSeek 模型",
        ["deepseek-v4-flash", "deepseek-v4-pro"],
        help="默认使用 flash；需要更强回答时可手动切换为 pro。",
    )

filtered_questions = filter_questions(
    questions, selected_course, selected_chapter, selected_type
)

st.metric("当前筛选后的题目数量", len(filtered_questions))
if not filtered_questions:
    st.warning("当前条件下没有题目，请调整侧边栏筛选条件。")
    st.stop()

filtered_ids = {question["id"] for question in filtered_questions}
if st.session_state.get("current_question_id") not in filtered_ids:
    st.session_state.current_question_id = filtered_questions[0]["id"]
    st.session_state.ai_prompt = ""
    st.session_state.ai_result = ""
    st.session_state.submitted_question_id = None
    st.session_state.submitted_choice = None

if st.button("🎲 随机抽一题", type="primary"):
    candidates = [
        question
        for question in filtered_questions
        if question["id"] != st.session_state.current_question_id
    ]
    chosen_question = random.choice(candidates or filtered_questions)
    st.session_state.current_question_id = chosen_question["id"]
    st.session_state.ai_prompt = ""
    st.session_state.ai_result = ""
    st.session_state.submitted_question_id = None
    st.session_state.submitted_choice = None

current_question = next(
    question
    for question in filtered_questions
    if question["id"] == st.session_state.current_question_id
)

st.subheader(f"题目 {current_question['id']}")
st.markdown(current_question["question"])
question_options = current_question.get("options", [])
for option in question_options:
    st.markdown(option)

if question_options:
    option_labels = [
        get_option_label(option, index) for index, option in enumerate(question_options)
    ]
    selected_choice = st.radio(
        "选择你的答案",
        option_labels,
        index=None,
        horizontal=True,
        key=f"choice_{current_question['id']}",
    )

    if st.button("提交答案", key=f"submit_{current_question['id']}"):
        if selected_choice is None:
            st.warning("请先选择一个选项。")
        else:
            st.session_state.submitted_question_id = current_question["id"]
            st.session_state.submitted_choice = selected_choice

    if st.session_state.get("submitted_question_id") == current_question["id"]:
        correct_label = get_option_label(current_question["answer"])
        submitted_choice = st.session_state.get("submitted_choice")
        if submitted_choice == correct_label:
            st.success(f"回答正确！你选择了 {submitted_choice}。")
        else:
            st.error(
                f"回答错误：你选择了 {submitted_choice}，正确答案是 {correct_label or current_question['answer']}。"
            )

        with st.container(border=True):
            st.markdown("**答案**")
            st.markdown(current_question["answer"])
            st.markdown("**解析**")
            st.markdown(current_question["analysis"])

with st.expander("直接查看答案与解析（放弃作答）"):
    st.markdown("**答案**")
    st.markdown(current_question["answer"])
    st.markdown("**解析**")
    st.markdown(current_question["analysis"])

if st.button("生成 AI 解析提示词"):
    st.session_state.ai_prompt = build_explanation_prompt(current_question)

prompt_text = st.text_area(
    "可复制的 AI 解析提示词",
    value=st.session_state.get("ai_prompt", ""),
    height=320,
    placeholder="点击“生成 AI 解析提示词”后，Prompt 会显示在这里。",
)

if st.button("使用 DeepSeek 生成解析"):
    if not api_key:
        st.info("请先在侧边栏输入 DeepSeek API Key。你也可以只复制上面的 Prompt。")
    else:
        prompt_to_send = prompt_text or build_explanation_prompt(current_question)
        with st.spinner("DeepSeek 正在生成解析……"):
            try:
                st.session_state.ai_result = generate_explanation(
                    prompt=prompt_to_send,
                    api_key=api_key,
                    temperature=temperature,
                    model=selected_model,
                )
            except Exception:
                st.session_state.ai_result = ""
                st.error(
                    "DeepSeek 调用失败，请检查 API Key、网络、base_url 和模型名。"
                )

st.divider()
st.subheader("AI 解析结果")
if st.session_state.get("ai_result"):
    with st.container(border=True):
        st.markdown(normalize_ai_markdown(st.session_state.ai_result))
else:
    st.caption("点击“使用 DeepSeek 生成解析”后，结果会显示在这里。")

with st.sidebar:
    st.divider()
    st.caption("AI 解析结果已移到主页面下方，阅读空间更宽。")
