# PaperFlow Agent

PaperFlow Agent 是一个面向科研论文写作流程的轻量级 LLM 工作流工具。它将论文写作拆解为文献摘要、大纲规划、节点卡片、节点写作、一致性检查、自动修订和 DOCX 组装等步骤，帮助用户以更清晰、可追踪的方式完成论文初稿准备。

本项目并不是“一键生成论文”的工具，也不建议将模型生成内容直接作为最终稿使用。它更适合作为科研写作辅助工作台：将重复性、结构化的写作环节交给工具辅助完成，而选题判断、方法设计、实验分析和最终修改仍由研究者负责。

## 项目背景

在实际论文写作中，直接让大模型一次性生成整篇文章，通常会遇到几个问题：

* 文章结构容易偏离原始研究目标；
* 不同章节之间可能重复、断裂或相互矛盾；
* 术语、引用和论证逻辑难以保持一致；
* 长文档难以放入一次 Prompt 中处理；
* 中间结果不便保存、检查和复用。

PaperFlow Agent 的思路是：不直接生成整篇论文，而是将写作过程拆成多个可管理的节点。每个节点可以单独生成、检查、修改和组装，从而降低长文本生成中的结构漂移和上下文割裂问题。

## 主要功能

* 以项目目录管理论文写作任务；
* 支持读取 PDF、DOCX、TXT 文献材料；
* 支持 DeepSeek 和 OpenAI-compatible API；
* 支持模型连接测试；
* 支持短文本快速测试，避免直接触发完整生成流程；
* 支持文献摘要生成；
* 支持结构化大纲生成；
* 支持节点卡片生成；
* 支持按节点生成章节草稿；
* 支持可选的节点润色、一致性检查和自动修订；
* 支持 DOCX 草稿组装；
* 支持 Web 页面进行项目编辑、材料上传、流程运行和结果下载。

## 项目结构

```text
paperflow-agent/
├── paper_agent.py
├── quick_test.py
├── requirements.txt
├── .env.example
├── config/
├── docs/
├── examples/
│   └── demo_project/
│       ├── topic.txt
│       ├── goal.txt
│       └── materials/
└── src/
```

一个典型的论文项目目录如下：

```text
my_project/
├── topic.txt
├── goal.txt
├── materials/
│   ├── paper_1.pdf
│   ├── paper_2.docx
│   └── notes.txt
└── outputs/
```

其中：

* `topic.txt` 用于描述论文主题；
* `goal.txt` 用于描述写作目标；
* `materials/` 用于放置参考文献、笔记或其他材料；
* `outputs/` 用于保存生成结果。

## 安装方法

克隆项目：

```bash
git clone https://github.com/cloudcloud222/paperflow-agent.git
cd paperflow-agent
```

创建虚拟环境：

```bash
python -m venv .venv
```

Windows PowerShell 下激活虚拟环境：

```powershell
.venv\Scripts\Activate.ps1
```

安装依赖：

```bash
pip install -r requirements.txt
```

## 配置 API Key

复制环境变量模板：

```bash
copy .env.example .env
```

打开 `.env` 文件，填入自己的 API Key：

```text
DEEPSEEK_API_KEY=your_api_key_here
```

请不要将 `.env` 上传到 GitHub。

如果你的网络环境需要代理，可以在当前终端中设置代理，例如：

```powershell
$env:HTTP_PROXY="http://127.0.0.1:7897"
$env:HTTPS_PROXY="http://127.0.0.1:7897"
```

默认模型和接口配置可在 `config/` 目录中调整。

## 快速开始

项目中已经提供了一个示例项目：

```text
examples/demo_project
```

先检查项目配置：

```bash
python paper_agent.py check --project examples/demo_project
```

测试模型连接：

```bash
python paper_agent.py ping --project examples/demo_project
```

运行最小摘要测试：

```bash
python paper_agent.py quicktest --project examples/demo_project --max-chars 800
```

这个命令只读取第一份材料的一小段内容，并生成简短摘要。它适合用于检查环境、API、文件读取和输出目录是否正常，不会生成完整论文。

## 常用命令

只生成大纲和节点卡片：

```bash
python paper_agent.py run --project examples/demo_project --mode outline
```

只生成一个节点，不进行润色、检查和修订：

```bash
python paper_agent.py run --project examples/demo_project --mode node --max-nodes 1 --no-polish --no-review --no-revision
```

生成一个节点，并进行润色和一致性检查：

```bash
python paper_agent.py run --project examples/demo_project --mode node --max-nodes 1
```

运行完整工作流：

```bash
python paper_agent.py run --project examples/demo_project --mode full --full --yes
```

完整工作流会多次调用大模型，耗时和调用成本都更高。建议先运行 `check`、`ping`、`quicktest` 和单节点测试，确认流程正常后再运行完整流程。

清理生成结果：

```bash
python paper_agent.py clean --project examples/demo_project --yes
```

## Web 页面

启动 Web 页面：

```bash
python paper_agent.py web --host 127.0.0.1 --port 8501
```

浏览器打开：

```text
http://127.0.0.1:8501
```

Web 页面支持：

* 选择或创建论文项目；
* 编辑论文主题和写作目标；
* 上传 PDF、DOCX、TXT 材料；
* 配置模型服务和 API 参数；
* 执行配置检查、模型连接测试和快速摘要测试；
* 运行大纲生成、单节点生成和完整工作流；
* 浏览生成文件；
* 将输出结果打包下载。

## 输出目录

生成文件会保存在对应项目的 `outputs/` 目录下：

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

不同命令会生成不同类型的文件。例如，`quicktest` 只生成短摘要和测试报告；完整工作流会生成文献摘要、大纲、节点卡片、节点正文、修订结果和最终 DOCX 草稿。

## 设计思路

PaperFlow Agent 采用节点化写作流程。它不会直接要求大模型一次性生成整篇论文，而是将写作任务拆分为多个阶段：

1. 读取论文主题和写作目标；
2. 读取并摘要整理参考材料；
3. 生成结构化大纲；
4. 将大纲拆解为节点卡片；
5. 为每个节点选择相关材料；
6. 按节点生成章节草稿；
7. 可选地进行润色、一致性检查和自动修订；
8. 将节点内容组装为 DOCX 草稿。

这种方式使生成过程更容易检查、暂停、调试和修改，也便于用户在不同阶段进行人工干预。

## 使用边界

生成内容必须经过人工审核和修改。本项目适合用于科研写作流程辅助、文献整理、初稿准备和个人效率工具探索，不应用于直接提交未经验证的机器生成论文。

同时，请不要将 API Key、私人文献、未公开论文、生成稿件或个人数据上传到公开仓库。

## 当前限制

* PDF 解析主要适用于文本型 PDF，扫描件、复杂表格、公式和双栏排版可能无法完整处理；
* 生成质量依赖模型能力、材料质量、Prompt 设计和人工修改；
* 参考文献处理仍较基础，正式投稿前需要人工校对；
* 当前更适合个人写作辅助，不是多人协作平台。

## 适用场景

PaperFlow Agent 适合用于：

* 文献摘要整理；
* 论文大纲规划；
* 章节初稿生成；
* 长文档写作流程拆解；
* LLM Agent 工作流实验；
* AI 应用开发项目展示；
* 科研写作辅助工具原型验证。

## License

本项目主要用于学习、科研写作流程探索和个人效率工具开发。
