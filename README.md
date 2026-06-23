# 期末复习题库助手

一个使用 Streamlit、JSON 题库和 DeepSeek API 的期末复习小工具。无需 API Key
即可浏览、筛选、随机抽题、查看答案，以及生成可复制的 AI 解析 Prompt。

## 功能

- 按课程、章节和题型联动筛选
- 随机抽题，查看标准答案与解析
- 使用 LaTeX 同时兼容 Streamlit 数学渲染和 AI Prompt
- 生成可复制到 DeepSeek 或 ChatGPT 的解析提示词
- 可选使用自己的 DeepSeek API Key 直接生成讲解
- AI 结果显示在侧边栏

## 项目结构

```text
first_math_question/
├─ main.py
├─ ai_utils.py
├─ question_bank.json
├─ questions/              # 原始试卷图片
├─ requirements.txt
├─ README.md
└─ .gitignore
```

## Windows 本地运行

```powershell
cd D:\project\first_math_question
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run main.py
```

终端显示 Local URL 后，在浏览器打开该地址。停止服务时按 `Ctrl+C`。

## DeepSeek 设置

页面侧边栏提供 API Key 密码输入框。Key 只作为当前页面调用参数传给
`DeepSeekAI`，程序不会打印或写入文件。只有点击“使用 DeepSeek 生成解析”时
才会发出 API 请求。

当前配置：

- `base_url`: `https://api.deepseek.com`
- 默认模型：`deepseek-v4-flash`
- 可选模型：`deepseek-v4-pro`
- 默认 temperature：`0.3`

如果服务端调整了模型名称，可修改 `main.py` 中“DeepSeek 模型”的选项。

## 题库格式

每道题保存课程、章节、题型、题干、选项、答案、解析、标签和原图路径。
数学公式使用 `$...$`（行内）或 `$$...$$`（独立公式）的 LaTeX 格式。

```json
{
  "id": 1,
  "course": "高等数学",
  "chapter": "空间向量",
  "type": "选择题",
  "question": "设向量 $\\vec{r}=(2,3,6)$……",
  "options": ["A. $\\cos \\alpha$"],
  "answer": "A. $\\cos \\alpha$",
  "analysis": "……",
  "tags": ["方向余弦"],
  "source_image": "questions/IMG_5823.jpeg"
}
```
