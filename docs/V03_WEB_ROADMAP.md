# Paper-Agent V0.3 Web Roadmap

V0.3 的目标是把当前 CLI 工具升级为可视化 Web 工具。重点不是增加更复杂的生成能力，而是让用户可以在浏览器中完成项目创建、材料导入、Agent 调整、运行监控和文件导出。

## 1. 推荐技术路线

### 第一阶段：Streamlit 快速原型

适合个人项目展示和简历演示，开发速度快。

- 项目创建：填写 topic、goal，自动生成项目目录
- 文献导入：上传 PDF/TXT/DOCX 到 materials/
- Agent 调整：编辑 Prompt 模板、模型名、温度、max_tokens
- 运行控制：check、ping、quicktest、run、assemble、clean
- 结果展示：显示文献摘要、大纲、节点卡片、运行日志和最终 DOCX 下载

### 第二阶段：FastAPI + React/Vue

适合进一步产品化。

- 后端：FastAPI 管理项目、上传、工作流任务和文件下载
- 前端：React/Vue 展示项目列表、Agent 配置、进度条、日志流
- 任务队列：后台线程 / Celery / RQ
- 数据库：SQLite 管理项目、任务、Agent、运行记录

## 2. Web 页面规划

### Dashboard

- 项目列表
- 新建项目
- 最近运行结果
- 快速打开 outputs

### Project Setup

- 编辑 topic.txt
- 编辑 goal.txt
- 上传 materials
- 检查材料数量和格式

### Agent Config

- Provider / Base URL / Model
- API Key 环境变量提示，不在页面明文保存 Key
- Prompt 模板编辑
- 温度、max_tokens、是否流式输出

### Workflow Runner

- check
- ping
- quicktest
- run
- assemble
- clean
- 实时日志显示
- 阶段状态：literature / outline / node cards / writing / revision / assemble

### Outputs

- literature summaries
- outline schema
- node cards
- node writings
- consistency checks
- final docx
- run_report.json / run_report.md
- 打包下载 outputs.zip

## 3. 优先级

1. Streamlit 单页面 Demo
2. 支持上传材料与修改 topic/goal
3. 支持调用 CLI 的 check/ping/quicktest
4. 支持后台运行 full workflow
5. 支持输出文件下载
6. 再考虑多项目管理、数据库和登录

## 4. 关键风险

- API Key 不应写入公开日志或前端文件
- 长任务不能阻塞 Web 页面
- 生成过程需要可取消、可恢复
- 输出文件可能包含论文内容，上传 GitHub 前必须忽略 outputs/
- 论文写作工具必须强调人工审核，避免宣传为自动代写工具
