# Paper-Agent

Paper-Agent 是一个面向科研论文写作流程的 LLM 辅助工具。它不是“一键生成论文”的工具，而是把论文写作拆解为文献摘要、大纲规划、节点卡片、节点写作、一致性检查、自动修订和 DOCX 组装等阶段，让用户可以在每个阶段进行人工审核和调整。

V0.3 版本增加了更安全的命令行运行模式和一个轻量 Web UI，重点解决两个问题：

- 最小测试不再误触完整论文生成；
- 用户可以通过网页完成项目创建、文献导入、Agent/模型配置、流程运行和结果导出。

## 主要功能

- 项目目录管理：`topic.txt`、`goal.txt`、`materials/`、`outputs/`
- 支持 PDF / DOCX / TXT 文献读取
- 支持 DeepSeek / OpenAI-compatible API
- 支持 Check / Ping / QuickTest
- 支持文献摘要、结构化大纲、节点卡片生成
- 支持限制节点数量的调试模式
- 支持跳过润色、一致性检查和自动修订，降低测试成本
- 支持完整节点化论文草稿生成和 DOCX 组装
- 支持 Streamlit Web UI 和 outputs.zip 下载

## 安装

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

复制环境变量模板：

```bash
copy .env.example .env
```

在 `.env` 中填入自己的 API Key。不要把 `.env` 上传到 GitHub。

```text
DEEPSEEK_API_KEY=your_api_key_here
```

如果使用代理，例如 Clash / Mihomo 的 7897 端口：

```powershell
$env:HTTP_PROXY="http://127.0.0.1:7897"
$env:HTTPS_PROXY="http://127.0.0.1:7897"
```

## 命令行使用

### 初始化项目

```bash
python paper_agent.py init examples/demo_project --force
```

项目结构：

```text
examples/demo_project/
├── topic.txt
├── goal.txt
├── materials/
└── outputs/
```

### 检查配置

```bash
python paper_agent.py check --project examples/demo_project
```

### 测试模型连接

```bash
python paper_agent.py ping --project examples/demo_project
```

### 最小摘要测试

只读取第一份材料的一小段内容，不生成完整论文。

```bash
python paper_agent.py quicktest --project examples/demo_project --max-chars 800
```

### 只生成大纲和节点卡片

```bash
python paper_agent.py run --project examples/demo_project --mode outline
```

### 只写一个节点

适合调试 Prompt、材料读取和节点写作链路。

```bash
python paper_agent.py run --project examples/demo_project --mode node --max-nodes 1 --no-polish --no-review --no-revision
```

如果希望单节点也做润色和检查：

```bash
python paper_agent.py run --project examples/demo_project --mode node --max-nodes 1
```

### 完整运行

完整工作流会多次调用 LLM，耗时和成本较高，必须显式确认：

```bash
python paper_agent.py run --project examples/demo_project --mode full --full --yes
```

## Web UI

启动网页界面：

```bash
python paper_agent.py web --host 127.0.0.1 --port 8501
```

浏览器打开：

```text
http://127.0.0.1:8501
```

Web UI 支持：

- 创建/选择项目；
- 编辑 topic 和 goal；
- 上传 PDF / DOCX / TXT 文献；
- 配置 Provider、Model、Base URL、API Key 和代理；
- 执行 Check、Ping、QuickTest、Outline、Node Test、Full Run；
- 查看输出文件；
- 打包下载 outputs.zip。

界面风格以淡蓝色、淡灰色和白色为主，卡片与按钮采用圆角设计，更适合项目演示和面试展示。

## 输出目录

```text
outputs/
├── quicktest/
├── literature_summaries/
├── outline_schemas/
├── node_cards/
├── node_pipeline/
├── node_assembled_papers/
└── reports/
```

## 项目定位

Paper-Agent 的重点不是替代研究者写论文，而是把科研写作中重复性强、结构化程度高的环节工具化。它更适合作为科研写作辅助工作台、LLM Agent 工作流原型和 AI 应用开发项目来理解。

## 注意事项

- 生成内容必须经过人工审核和修改。
- 不要把 API Key、真实论文材料、输出论文或个人数据上传到公开仓库。
- PDF 复杂版式、扫描件、公式和表格的解析能力仍有限。
- 完整运行前建议先使用 `quicktest`、`outline` 和 `node --max-nodes 1` 逐步验证。
