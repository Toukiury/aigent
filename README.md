---
title: 通用问题优化智能体
emoji: 🔍
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: "4.44.0"
app_file: app.py
pinned: false
license: mit
---

# 通用问题优化智能体

基于公开大模型 API，通过**提示词工程**与**轻量工具调用**，将模糊问题优化为高质量 Prompt。

## 如何调用智能体

### 方式一：Web 网站（推荐，适合作业演示）

```powershell
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key
copy .env.example .env
# 编辑 .env，填写 LLM_API_KEY

# 3. 启动网站
python app.py
```

浏览器打开 **http://localhost:7860**，输入问题后点击「开始优化」。

**界面会逐步实时显示：**
- 每个工具调用卡片（诊断 → 追问 → 重写 → 评估 → System Prompt → 对比）
- 右侧最终输出区随步骤推进逐步填充
- 全部完成后可下载 PDF

临时公网链接（录视频用）：`.env` 中设置 `GRADIO_SHARE=true` 后启动。

### 方式二：Python 代码调用

```python
from agent.optimizer import QuestionOptimizer

optimizer = QuestionOptimizer()

# 一次性获取最终结果
result = optimizer.run("帮我写个爬虫", template="CO-STAR")
print(result.optimized_question)

# 流式逐步获取（适合自定义界面）
for state in optimizer.run_stream("帮我写个爬虫"):
    print(state.status, state.steps[-1] if state.steps else "")
    if state.done:
        print("完成:", state.result.optimized_question)
```

### 方式三：公网永久部署

上传项目到 [Hugging Face Spaces](https://huggingface.co/spaces)（Gradio），在 Secrets 中配置 `LLM_API_KEY`，即可获得公网 URL。

## 使用模型

**默认：DeepSeek Chat (`deepseek-chat`)**，通过 OpenAI 兼容 API 调用。

在 `.env` 中可切换（见 `.env.example`）：

| 预设 | 模型 | 说明 |
|------|------|------|
| `deepseek`（默认） | deepseek-chat | 性价比高，推荐 |
| `qwen` | qwen-plus | 通义千问，国内稳定 |
| `doubao` | 你的 endpoint_id | 火山方舟豆包 |

## 功能

- **问题诊断** (`analyze_question`)：识别意图、缺失信息、歧义点
- **追问建议** (`suggest_clarifications`)：生成 2-4 个追问，帮助用户补全信息
- **问题重写** (`rewrite_question`)：支持 CO-STAR / CRISPE / RISEN 三种模板
- **质量评估** (`evaluate_quality`)：多维度打分，不达标自动迭代优化
- **System Prompt 生成** (`generate_system_prompt`)：为优化后问题推荐系统提示词
- **优化前后对比** (`compare_answers`)：同一模型下对比模糊问题 vs 优化问题的回答质量
- **PDF 报告**：自动记录完整 6 步工具调用过程，可下载提交作业

## 演示案例

主案例：**「帮我写个爬虫」** → 优化为含技术栈、约束、输出格式的完整 Prompt

## 本地运行

```bash
pip install -r requirements.txt
cp .env.example .env   # 填写 LLM_API_KEY
python app.py
```

浏览器打开 http://localhost:7860

## 公网部署

### 方式一：Hugging Face Spaces（推荐，永久公网链接）

1. 在 [huggingface.co/spaces](https://huggingface.co/spaces) 创建 Gradio Space
2. 上传本项目全部文件
3. 在 Space Settings → Repository secrets 中添加 `LLM_API_KEY` 等环境变量
4. 获得公网链接，如 `https://huggingface.co/spaces/用户名/question-optimizer`

### 方式二：Gradio 临时分享链接

```bash
# .env 中设置 GRADIO_SHARE=true
python app.py
```

启动后会打印 `https://xxxxx.gradio.live` 临时链接（约 72 小时有效）。

## 作业提交清单

| 交付物 | 说明 |
|--------|------|
| 可访问链接 | HF Spaces 或 Gradio share 链接 |
| MP4 视频 | 录屏演示：输入模糊问题 → 查看优化过程 → 下载 PDF |
| PDF 文档 | 点击界面「下载求解过程 PDF 报告」 |

## 录屏建议脚本（约 3 分钟）

1. 打开公网链接，介绍智能体功能（15 秒）
2. 输入「帮我写个爬虫」，点击「开始优化」（30 秒）
3. 展示工具调用过程：诊断 → 重写 → 评估（60 秒）
4. 展示优化后 Prompt 与质量评分（30 秒）
5. 下载并打开 PDF，展示求解过程记录（45 秒）

## 技术栈

- Python 3.10+
- Gradio（Web 界面）
- OpenAI 兼容 API（DeepSeek / 通义千问 / 豆包等）
- ReportLab（PDF 生成）

## 项目结构

```
homework/
├── app.py              # Gradio 主应用
├── agent/
│   ├── optimizer.py    # 智能体主逻辑
│   ├── tools.py        # 轻量工具（分析/重写/评估）
│   ├── prompts.py      # 提示词模板
│   └── llm_client.py   # 大模型 API 客户端
├── pdf_generator.py    # PDF 报告生成
├── requirements.txt
└── outputs/            # 生成的 PDF 存放目录
```
