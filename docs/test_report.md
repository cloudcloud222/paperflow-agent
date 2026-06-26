# PaperFlow Agent v0.4 Web Studio 测试记录

测试对象：`web_app.py` v0.4

测试环境：ChatGPT sandbox / Linux / Python 3.13 / Streamlit 1.58

## 测试内容

- `web_app.py` 语法检查：通过
- `paper_agent.py` 与 `src/` 编译检查：通过
- Streamlit AppTest 加载页面：通过
- Tab 分区识别：通过，检测到 `项目输入`、`模型配置`、`Agent Prompt`、`运行流程`、`输出结果`
- Web 控件识别：通过，检测到保存输入、模型配置保存、Prompt 初始化、Prompt 保存、Check、Ping、QuickTest、run_report 生成等按钮
- CLI 项目初始化：通过
- CLI 项目检查：通过；由于沙盒未配置真实 API Key，检查结果中存在 API Key 未设置警告
- Agent Prompt 初始化：通过，生成 11 个项目级 Prompt 文件
- run_report.md 生成：通过，生成 `outputs/reports/latest_run_report.md` 和时间戳报告
- 输出文件列表与预览逻辑：通过静态渲染检查

## 说明

沙盒环境没有配置真实 DeepSeek/OpenAI API Key，因此没有进行真实模型调用，也没有执行完整论文生成流程。

由于沙盒内 Chromium 对 `127.0.0.1:8501` 的本地访问存在管理员策略拦截，本次无法直接对运行中的 Streamlit 页面进行浏览器截图。已完成组件级可用性测试，并基于 v0.4 页面结构生成 GitHub 展示截图。

## 建议上传的截图

- `docs/screenshots/01_project_input.png`
- `docs/screenshots/02_model_config.png`
- `docs/screenshots/03_agent_prompt_editor.png`
- `docs/screenshots/04_run_workflow.png`
- `docs/screenshots/05_outputs_preview.png`
- `docs/screenshots/06_test_summary.png`
