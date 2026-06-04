"""Paper-Agent V0.3 Streamlit Web UI.

A lightweight local Web UI for project setup, model checks, quick tests,
limited node runs, and output downloads. It is intentionally simple and
runs the existing CLI commands under the hood.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT / "workspace" / "web_projects"
WORKSPACE.mkdir(parents=True, exist_ok=True)

DEFAULT_MODEL = "deepseek-v4-flash"
DEFAULT_BASE_URL = "https://api.deepseek.com"

st.set_page_config(
    page_title="Paper-Agent",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
:root {
  --pa-blue: #4f8df7;
  --pa-blue-light: #eaf3ff;
  --pa-bg: #f6f8fb;
  --pa-card: #ffffff;
  --pa-border: #dfe7f3;
  --pa-text: #1f2937;
  --pa-muted: #64748b;
}
html, body, [data-testid="stAppViewContainer"] {
  background: linear-gradient(180deg, #f7fbff 0%, #f6f8fb 45%, #f7f9fc 100%);
  color: var(--pa-text);
}
[data-testid="stSidebar"] {
  background: #ffffff;
  border-right: 1px solid var(--pa-border);
}
.block-container {
  padding-top: 2rem;
  padding-bottom: 2rem;
}
.pa-hero {
  background: linear-gradient(135deg, #ffffff 0%, #edf6ff 100%);
  border: 1px solid var(--pa-border);
  border-radius: 26px;
  padding: 28px 30px;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.06);
  margin-bottom: 20px;
}
.pa-title {
  font-size: 34px;
  font-weight: 760;
  letter-spacing: -0.02em;
  margin-bottom: 8px;
}
.pa-subtitle {
  color: var(--pa-muted);
  font-size: 16px;
  line-height: 1.7;
  max-width: 900px;
}
.pa-card {
  background: var(--pa-card);
  border: 1px solid var(--pa-border);
  border-radius: 22px;
  padding: 20px 22px;
  box-shadow: 0 14px 35px rgba(15, 23, 42, 0.045);
  margin-bottom: 16px;
}
.pa-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--pa-blue-light);
  color: #1d4ed8;
  border: 1px solid #c7ddff;
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 13px;
  margin-right: 8px;
  margin-top: 8px;
}
.stButton>button {
  border-radius: 999px !important;
  border: 1px solid #c9d9f2 !important;
  background: #ffffff !important;
  color: #1f2937 !important;
  padding: 0.55rem 1rem !important;
  box-shadow: 0 5px 15px rgba(15, 23, 42, 0.06) !important;
}
.stButton>button:hover {
  border-color: #4f8df7 !important;
  color: #1d4ed8 !important;
}
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {
  border-radius: 14px !important;
}
</style>
""",
    unsafe_allow_html=True,
)


def project_dir(name: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name.strip()) or "demo_project"
    return WORKSPACE / safe


def run_cli(args: list[str], api_key: str = "", key_env: str = "DEEPSEEK_API_KEY", proxy: str = "") -> tuple[int, str]:
    env = os.environ.copy()
    if api_key.strip():
        env[key_env.strip() or "DEEPSEEK_API_KEY"] = api_key.strip()
    if proxy.strip():
        env["HTTP_PROXY"] = proxy.strip()
        env["HTTPS_PROXY"] = proxy.strip()
    cmd = [sys.executable, str(ROOT / "paper_agent.py"), *args]
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    return proc.returncode, output


def save_project_inputs(pdir: Path, topic: str, goal: str, uploads: list) -> None:
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "materials").mkdir(parents=True, exist_ok=True)
    (pdir / "topic.txt").write_text(topic.strip() + "\n", encoding="utf-8")
    (pdir / "goal.txt").write_text(goal.strip() + "\n", encoding="utf-8")
    for file in uploads or []:
        target = pdir / "materials" / file.name
        target.write_bytes(file.getbuffer())


def make_outputs_zip(pdir: Path) -> Path | None:
    outputs = pdir / "outputs"
    if not outputs.exists():
        return None
    zip_path = pdir / f"outputs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in outputs.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(outputs.parent))
    return zip_path


st.markdown(
    """
<div class="pa-hero">
  <div class="pa-title">Paper-Agent</div>
  <div class="pa-subtitle">
    一个面向科研写作流程的轻量 LLM Agent 工具。它不追求“一键生成论文”，而是把文献摘要、
    大纲规划、节点写作、一致性检查和 DOCX 组装拆成可配置、可追踪的工作流。
  </div>
  <span class="pa-chip">🧩 Node Workflow</span>
  <span class="pa-chip">📄 Literature Summary</span>
  <span class="pa-chip">🔎 Quick Test</span>
  <span class="pa-chip">⬇️ Export Outputs</span>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("设置")
    project_name = st.text_input("项目名称", value="demo_project")
    pdir = project_dir(project_name)
    st.caption(f"项目目录：{pdir}")

    st.divider()
    st.subheader("模型")
    provider = st.text_input("Provider", value="deepseek")
    model = st.text_input("Model", value=os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL))
    base_url = st.text_input("Base URL", value=os.getenv("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL))
    key_env = st.text_input("API Key 环境变量名", value="DEEPSEEK_API_KEY")
    api_key = st.text_input("API Key（仅当前会话使用，不保存）", type="password")
    proxy = st.text_input("代理（可选）", value=os.getenv("HTTPS_PROXY", ""), placeholder="http://127.0.0.1:7897")

    st.divider()
    st.subheader("运行参数")
    max_pages = st.number_input("PDF 最大读取页数", min_value=1, max_value=100, value=5, step=1)
    max_chars = st.number_input("QuickTest 截断字符数", min_value=100, max_value=8000, value=800, step=100)
    max_nodes = st.number_input("Node 模式最大节点数", min_value=1, max_value=10, value=1, step=1)
    strategy = st.selectbox("调度策略", ["hybrid", "top_down", "bottom_up"], index=0)
    no_polish = st.checkbox("Node 测试跳过润色", value=True)
    no_review = st.checkbox("Node 测试跳过一致性检查", value=True)
    no_revision = st.checkbox("关闭自动修订", value=True)

left, right = st.columns([1.05, 0.95], gap="large")

with left:
    st.markdown('<div class="pa-card">', unsafe_allow_html=True)
    st.subheader("1. 项目输入")
    topic_default = "面向科研论文写作流程的 LLM Agent 辅助工具研究"
    goal_default = "形成一篇中文论文草稿，说明 Paper-Agent 的研究背景、系统架构、节点化写作流程、工程实现方式、局限性与后续优化方向。"
    if (pdir / "topic.txt").exists():
        topic_default = (pdir / "topic.txt").read_text(encoding="utf-8").strip()
    if (pdir / "goal.txt").exists():
        goal_default = (pdir / "goal.txt").read_text(encoding="utf-8").strip()
    topic = st.text_input("Topic", value=topic_default)
    goal = st.text_area("Goal", value=goal_default, height=120)
    uploads = st.file_uploader("导入文献 / 材料（PDF / DOCX / TXT）", type=["pdf", "docx", "txt"], accept_multiple_files=True)

    c1, c2, c3 = st.columns(3)
    if c1.button("保存输入", use_container_width=True):
        save_project_inputs(pdir, topic, goal, uploads)
        st.success("已保存 topic、goal 和上传材料。")
    if c2.button("初始化示例", use_container_width=True):
        code, out = run_cli(["init", str(pdir), "--force"], api_key, key_env, proxy)
        st.code(out)
    if c3.button("清理输出", use_container_width=True):
        code, out = run_cli(["clean", "--project", str(pdir), "--yes"], api_key, key_env, proxy)
        st.code(out)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="pa-card">', unsafe_allow_html=True)
    st.subheader("2. 运行")
    common = [
        "--project", str(pdir),
        "--provider", provider,
        "--model", model,
        "--base-url", base_url,
        "--api-key-env", key_env,
        "--max-pages", str(max_pages),
    ]

    b1, b2, b3 = st.columns(3)
    if b1.button("Check", use_container_width=True):
        code, out = run_cli(["check", *common], api_key, key_env, proxy)
        st.session_state["last_output"] = out
    if b2.button("Ping", use_container_width=True):
        code, out = run_cli(["ping", *common], api_key, key_env, proxy)
        st.session_state["last_output"] = out
    if b3.button("QuickTest", use_container_width=True):
        save_project_inputs(pdir, topic, goal, uploads)
        code, out = run_cli(["quicktest", *common, "--max-chars", str(max_chars)], api_key, key_env, proxy)
        st.session_state["last_output"] = out

    b4, b5, b6 = st.columns(3)
    if b4.button("只生成大纲", use_container_width=True):
        save_project_inputs(pdir, topic, goal, uploads)
        code, out = run_cli(["run", *common, "--mode", "outline"], api_key, key_env, proxy)
        st.session_state["last_output"] = out
    if b5.button("单节点测试", use_container_width=True):
        save_project_inputs(pdir, topic, goal, uploads)
        args = ["run", *common, "--mode", "node", "--strategy", strategy, "--max-nodes", str(max_nodes)]
        if no_polish:
            args.append("--no-polish")
        if no_review:
            args.append("--no-review")
        if no_revision:
            args.append("--no-revision")
        code, out = run_cli(args, api_key, key_env, proxy)
        st.session_state["last_output"] = out
    full_ok = b6.checkbox("确认完整运行", value=False)
    if b6.button("完整运行", use_container_width=True):
        if not full_ok:
            st.warning("完整运行会多次调用 LLM，请先勾选确认。")
        else:
            save_project_inputs(pdir, topic, goal, uploads)
            code, out = run_cli(["run", *common, "--mode", "full", "--strategy", strategy, "--full", "--yes"], api_key, key_env, proxy)
            st.session_state["last_output"] = out
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="pa-card">', unsafe_allow_html=True)
    st.subheader("运行日志")
    st.code(st.session_state.get("last_output", "等待运行命令..."), language="text")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="pa-card">', unsafe_allow_html=True)
    st.subheader("输出文件")
    outputs = pdir / "outputs"
    if outputs.exists():
        files = sorted([x for x in outputs.rglob("*") if x.is_file()], key=lambda x: x.stat().st_mtime, reverse=True)
        for f in files[:25]:
            rel = f.relative_to(pdir)
            st.write(f"📄 `{rel}`")
        zip_path = make_outputs_zip(pdir)
        if zip_path and zip_path.exists():
            st.download_button("下载 outputs.zip", data=zip_path.read_bytes(), file_name=zip_path.name, mime="application/zip", use_container_width=True)
    else:
        st.caption("暂无输出。先运行 QuickTest、Outline 或 Node 测试。")
    st.markdown('</div>', unsafe_allow_html=True)
