import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "config"
DEFAULT_MODEL = "deepseek-v4-flash"
DEFAULT_BASE_URL = "https://api.deepseek.com"


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def _normalize_bool_values(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _normalize_bool_values(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_bool_values(v) for v in value]
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "ture"}:
            return True
        if lowered == "false":
            return False
    return value


def _abs(path: str | Path) -> str:
    return str(Path(path).resolve())


def _project_layout(project: Path) -> dict[str, Path]:
    outputs = project / "outputs"
    return {
        "project": project,
        "topic": project / "topic.txt",
        "goal": project / "goal.txt",
        "materials": project / "materials",
        "outputs": outputs,
        "runtime_config": project / ".paper_agent_runtime" / "config",
    }


def _material_files(materials_dir: Path) -> list[Path]:
    if not materials_dir.exists():
        return []
    return sorted(
        [p for p in materials_dir.iterdir() if p.is_file() and p.suffix.lower() in {".pdf", ".txt", ".docx"}],
        key=lambda p: p.name,
    )


def _mask_key(value: str) -> str:
    value = value.strip()
    if not value:
        return "<empty>"
    if len(value) <= 10:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]} (len={len(value)})"


def _proxy_info() -> dict[str, str]:
    return {
        "HTTP_PROXY": os.getenv("HTTP_PROXY") or os.getenv("http_proxy") or "",
        "HTTPS_PROXY": os.getenv("HTTPS_PROXY") or os.getenv("https_proxy") or "",
    }


def init_project(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    layout = _project_layout(project)
    project.mkdir(parents=True, exist_ok=True)
    layout["materials"].mkdir(parents=True, exist_ok=True)
    layout["outputs"].mkdir(parents=True, exist_ok=True)

    files_to_write = {
        layout["topic"]: "面向大模型应用的科研论文写作辅助工具研究\n",
        layout["goal"]: (
            "形成一篇关于科研写作 Agent 工作流的中文论文草稿，重点说明研究背景、"
            "系统架构、关键模块、工程实现和局限性。\n"
        ),
        layout["materials"] / "sample_material.txt": (
            "This is a sanitized demo material. It describes LLM-based writing workflows, "
            "literature summarization, outline planning, section drafting, consistency checking, "
            "and DOCX assembly. Replace this file with your own PDF/TXT/DOCX references.\n"
        ),
    }

    for path, content in files_to_write.items():
        if path.exists() and not args.force:
            print(f"跳过已存在文件：{path}")
            continue
        path.write_text(content, encoding="utf-8")
        print(f"已创建：{path}")

    print("\n项目初始化完成。下一步：")
    print(f"  python paper_agent.py check --project {project}")
    print(f"  python paper_agent.py quicktest --project {project}")
    print(f"  python paper_agent.py run --project {project}")
    return 0


def prepare_runtime_config(args: argparse.Namespace) -> Path:
    project = Path(args.project).resolve()
    layout = _project_layout(project)
    runtime_config_dir = layout["runtime_config"]
    runtime_config_dir.mkdir(parents=True, exist_ok=True)

    models = _read_yaml(DEFAULT_CONFIG_DIR / "models.yaml")
    runtime = _normalize_bool_values(_read_yaml(DEFAULT_CONFIG_DIR / "runtime.yaml"))

    if not models:
        models = {
            "default_provider": "deepseek",
            "providers": {
                "deepseek": {
                    "base_url": DEFAULT_BASE_URL,
                    "api_key_env": "DEEPSEEK_API_KEY",
                    "chat_model": DEFAULT_MODEL,
                    "timeout": 60,
                    "max_retries": 1,
                }
            },
            "routing": {},
        }

    provider = (getattr(args, "provider", None) or models.get("default_provider") or "deepseek").strip()
    models["default_provider"] = provider
    models.setdefault("providers", {})
    models.setdefault("routing", {})
    models["providers"].setdefault(provider, {})

    provider_config = models["providers"][provider]
    if getattr(args, "base_url", None):
        provider_config["base_url"] = args.base_url.strip()
    provider_config["base_url"] = (provider_config.get("base_url") or DEFAULT_BASE_URL).strip()

    if getattr(args, "api_key_env", None):
        provider_config["api_key_env"] = args.api_key_env.strip()
    provider_config["api_key_env"] = (provider_config.get("api_key_env") or "DEEPSEEK_API_KEY").strip()

    if getattr(args, "model", None):
        provider_config["chat_model"] = args.model.strip()
    provider_config["chat_model"] = (provider_config.get("chat_model") or DEFAULT_MODEL).strip()
    if provider_config["chat_model"] == "deepseek-chat":
        provider_config["chat_model"] = DEFAULT_MODEL

    provider_config["timeout"] = int(provider_config.get("timeout", 60) or 60)
    provider_config["max_retries"] = int(provider_config.get("max_retries", 1) or 1)

    known_components = [
        "planner", "organizer", "reviewer", "reviser", "literature_summarizer",
        "outline_planner", "outline_reviewer", "introduction_writer", "introduction_polisher",
        "related_work_writer", "related_work_polisher", "methodology_writer", "methodology_polisher",
        "experiment_writer", "experiment_polisher", "conclusion_writer", "conclusion_polisher",
        "consistency_checker", "outline_schema_planner", "node_writer", "node_polisher",
        "node_consistency_checker", "node_reference_selector", "node_reviser",
    ]
    for component in known_components:
        models["routing"][component] = provider

    runtime.setdefault("stream", {})
    runtime.setdefault("pdf", {})
    runtime.setdefault("ruledoc", {"enabled": False, "rule_name": "yzu_thesis"})
    runtime.setdefault("pipeline", {})
    if getattr(args, "max_pages", None) is not None:
        runtime["pdf"]["max_pages"] = args.max_pages
    runtime["pdf"].setdefault("max_pages", 5)
    runtime["pipeline"]["enable_reviser"] = not getattr(args, "no_revision", False)

    outputs = layout["outputs"]
    paths = {
        "input": {
            "base_dir": _abs(project),
            "topic_dir": _abs(layout["topic"]),
            "goal_dir": _abs(layout["goal"]),
            "materials_dir": _abs(layout["materials"]),
        },
        "output": {
            "base_dir": _abs(outputs),
            "literature_dir": _abs(outputs / "literature_summaries"),
            "paper_dir": _abs(outputs / "paper_pipeline"),
            "sections_dir": _abs(outputs / "sections"),
            "assembled_dir": _abs(outputs / "final_papers"),
            "outline_schema_dir": _abs(outputs / "outline_schemas"),
            "outline_schema_rendered_dir": _abs(outputs / "outline_schemas_rendered"),
            "outline_review_dir": _abs(outputs / "outlines"),
            "node_cards_dir": _abs(outputs / "node_cards"),
            "node_writing_dir": _abs(outputs / "node_writings"),
            "node_pipeline_dir": _abs(outputs / "node_pipeline"),
            "node_assembled_dir": _abs(outputs / "node_assembled_papers"),
            "node_reference_dir": _abs(outputs / "node_references"),
            "logs_dir": _abs(outputs / "logs"),
        },
    }

    _write_yaml(runtime_config_dir / "models.yaml", models)
    _write_yaml(runtime_config_dir / "runtime.yaml", runtime)
    _write_yaml(runtime_config_dir / "paths.yaml", paths)
    os.environ["PAPER_AGENT_CONFIG_DIR"] = str(runtime_config_dir)
    return runtime_config_dir


def _get_provider_config(runtime_config_dir: Path) -> tuple[str, dict]:
    models = _read_yaml(runtime_config_dir / "models.yaml")
    provider = models.get("default_provider", "deepseek")
    provider_config = models.get("providers", {}).get(provider, {})
    return provider, provider_config


def check_project(args: argparse.Namespace) -> int:
    load_dotenv(override=False)
    project = Path(args.project).resolve()
    layout = _project_layout(project)
    errors = []
    warnings = []

    if not project.exists():
        errors.append(f"项目目录不存在：{project}")
    if not layout["topic"].exists():
        errors.append(f"缺少 topic.txt：{layout['topic']}")
    if not layout["goal"].exists():
        errors.append(f"缺少 goal.txt：{layout['goal']}")
    if not layout["materials"].exists():
        errors.append(f"缺少 materials 目录：{layout['materials']}")
    elif not _material_files(layout["materials"]):
        errors.append("materials 目录中没有 .pdf/.txt/.docx 材料")

    runtime_config_dir = prepare_runtime_config(args)
    provider, provider_config = _get_provider_config(runtime_config_dir)
    api_key_env = (provider_config.get("api_key_env") or "DEEPSEEK_API_KEY").strip()
    api_key = os.getenv(api_key_env)
    if not api_key:
        warnings.append(f"环境变量 {api_key_env} 未设置。run 时会在调用模型前失败。")
    elif api_key != api_key.strip():
        errors.append(f"环境变量 {api_key_env} 前后包含空格或换行，请重新设置或在 .env 中修正。")

    print("===== Paper-Agent 项目检查 =====")
    print(f"项目目录：{project}")
    print(f"运行配置：{runtime_config_dir}")
    print(f"材料数量：{len(_material_files(layout['materials'])) if layout['materials'].exists() else 0}")
    print(f"Provider：{provider}")
    print(f"Base URL：{provider_config.get('base_url', '')}")
    print(f"Model：{provider_config.get('chat_model', '')}")
    print(f"API Key Env：{api_key_env} = {_mask_key(api_key or '')}")
    proxies = _proxy_info()
    if proxies["HTTP_PROXY"] or proxies["HTTPS_PROXY"]:
        print(f"Proxy：HTTP={proxies['HTTP_PROXY'] or '<empty>'} | HTTPS={proxies['HTTPS_PROXY'] or '<empty>'}")

    if warnings:
        print("\n警告：")
        for item in warnings:
            print(f"  - {item}")

    if errors:
        print("\n错误：")
        for item in errors:
            print(f"  - {item}")
        return 1

    print("\n检查通过。")
    return 0


def ping_project(args: argparse.Namespace) -> int:
    if check_project(args) != 0:
        return 1
    prepare_runtime_config(args)
    from src.llm.client import DeepSeekClient

    print("\n===== LLM 连接测试 =====")
    client = DeepSeekClient(component_name="literature_summarizer")
    info = client.get_model_info()
    print(f"Provider：{info['provider']}")
    print(f"Base URL：{info['base_url']}")
    print(f"Model：{info['model']}")
    print(f"Proxy：{info['proxy'] or '<none>'}")

    message = getattr(args, "message", None) or "请回复：Paper-Agent 连接测试成功。"
    start = time.perf_counter()
    response = client.chat(message, system_message="你是一个简洁的连接测试助手，只需要按要求简短回复。")
    elapsed = time.perf_counter() - start
    print("\n连接成功：")
    print(response)
    print(f"耗时：{elapsed:.2f}s")
    return 0


def quicktest_project(args: argparse.Namespace) -> int:
    """A fast end-to-end smoke test.

    This runs: input loading -> first material truncation -> LLM summary -> output files.
    It intentionally skips outline planning, node writing, revision and DOCX assembly.
    """
    if check_project(args) != 0:
        return 1
    prepare_runtime_config(args)

    from src.input_loader.input_service import InputService
    from src.workflow.literature_summarizer import LiteratureSummarizer

    input_service = InputService()
    input_data = input_service.load_all_inputs()
    topic = input_data["topic"]
    goal = input_data["goal"]
    materials = input_data["materials"]
    if not materials:
        print("quicktest 失败：没有可用材料。")
        return 1

    first = materials[0]
    max_chars = max(100, int(args.max_chars or 1000))
    content = (first.get("content") or "")[:max_chars]
    filename = first.get("filename", "material")

    print("\n===== QuickTest：最小链路测试 =====")
    print(f"主题：{topic}")
    print(f"目标：{goal[:80]}{'...' if len(goal) > 80 else ''}")
    print(f"材料：{filename}")
    print(f"截断长度：{len(content)} chars")

    summarizer = LiteratureSummarizer()
    start = time.perf_counter()
    summary = summarizer.summarize(filename=f"quicktest_{filename}", content=content)
    elapsed = time.perf_counter() - start

    project = Path(args.project).resolve()
    out_dir = project / "outputs" / "quicktest"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / "quick_summary.md"
    report_path = out_dir / "quick_report.json"
    summary_path.write_text(summary, encoding="utf-8")
    report = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "project": str(project),
        "topic": topic,
        "material": filename,
        "input_chars": len(content),
        "output_chars": len(summary),
        "elapsed_seconds": round(elapsed, 2),
        "summary_path": str(summary_path),
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nQuickTest 完成。")
    print(f"摘要文件：{summary_path}")
    print(f"报告文件：{report_path}")
    print(f"耗时：{elapsed:.2f}s")
    return 0


def _write_run_report_md(report_path: Path, report: dict) -> Path:
    result = report.get("result", {}) or {}
    assembled = result.get("assembled_result", {}) or {}
    lines = [
        "# Paper-Agent Run Report",
        "",
        f"- Created at: {report.get('created_at', '')}",
        f"- Project: `{report.get('project', '')}`",
        f"- Strategy: `{report.get('strategy', '')}`",
        f"- Leaf only: `{report.get('leaf_only', False)}`",
        f"- Consistency revision: `{report.get('enable_consistency_revision', False)}`",
        f"- Run dir: `{result.get('run_dir', '')}`",
        f"- Final DOCX: `{assembled.get('final_docx_path', '')}`",
        "",
        "## Main Outputs",
        "",
        f"- Literature pack: `{result.get('literature_pack_path', '')}`",
        f"- Outline schema: `{result.get('schema_path', '')}`",
        f"- Node cards: `{result.get('cards_path', '')}`",
        "",
    ]
    md_path = report_path.with_suffix(".md")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


def _print_full_run_safety(args: argparse.Namespace, topic: str, materials_count: int) -> None:
    print("\n===== Full Run Safety Notice =====")
    print("你正在请求完整节点化论文写作流程。该流程会多次调用 LLM，可能耗时较长并产生较多费用。")
    print(f"主题：{topic}")
    print(f"材料数量：{materials_count}")
    print(f"调度策略：{args.strategy}")
    print(f"仅写叶子节点：{args.leaf_only}")
    print(f"最大节点数：{args.max_nodes if args.max_nodes else '不限制'}")
    print(f"润色：{not args.no_polish} | 一致性检查：{not args.no_review} | 自动修订：{not args.no_revision}")
    print("\n如只想做最小测试，请使用：")
    print("  python paper_agent.py ping --project examples/demo_project")
    print("  python paper_agent.py quicktest --project examples/demo_project --max-chars 800")
    print("  python paper_agent.py run --project examples/demo_project --mode node --max-nodes 1 --no-polish --no-review --no-revision")


def _run_literature_only(args: argparse.Namespace, input_data: dict) -> dict:
    from src.workflow.literature_pipeline import LiteraturePipeline

    topic = input_data["topic"]
    materials = input_data["materials"]
    start = time.perf_counter()
    result = LiteraturePipeline().run(topic=topic, materials=materials)
    elapsed = time.perf_counter() - start
    return {
        "mode": "literature",
        "elapsed_seconds": round(elapsed, 2),
        "result": result,
    }


def _run_outline_only(args: argparse.Namespace, input_data: dict) -> dict:
    from src.workflow.node_pipeline import NodePipeline

    topic = input_data["topic"]
    goal = input_data["goal"]
    materials = input_data["materials"]
    start = time.perf_counter()
    pipeline = NodePipeline()
    literature_pack_text, literature_pack_path, literature_summaries = pipeline._prepare_literature_resources(topic, materials)
    schema, schema_path = pipeline._prepare_schema(topic, goal, literature_pack_text)
    cards, cards_path = pipeline._prepare_node_cards(schema)
    elapsed = time.perf_counter() - start
    return {
        "mode": "outline",
        "elapsed_seconds": round(elapsed, 2),
        "result": {
            "literature_pack_path": literature_pack_path,
            "schema_path": schema_path,
            "cards_path": cards_path,
            "cards_count": len(cards),
            "literature_summaries_count": len(literature_summaries),
        },
    }


def _write_mode_report(project: Path, mode: str, payload: dict) -> tuple[Path, Path]:
    report_dir = project / "outputs" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_json = report_dir / f"{timestamp}_{mode}_report.json"
    report_md = report_dir / f"{timestamp}_{mode}_report.md"
    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "project": str(project),
        **payload,
    }
    report_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        f"# Paper-Agent {mode} Report",
        "",
        f"- Created at: {payload.get('created_at')}",
        f"- Project: `{project}`",
        f"- Mode: `{mode}`",
        f"- Elapsed: `{payload.get('elapsed_seconds', '')}s`",
        "",
        "## Result",
        "",
        "```json",
        json.dumps(payload.get("result", {}), ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    report_md.write_text("\n".join(lines), encoding="utf-8")
    return report_json, report_md


def run_project(args: argparse.Namespace) -> int:
    mode = (args.mode or "").strip().lower()
    if not mode:
        print("run 命令在 V0.3 中已改为安全模式，不再默认执行完整论文生成。")
        print("请选择明确模式：")
        print("  --mode quick       只做最小摘要测试")
        print("  --mode literature  只做文献摘要")
        print("  --mode outline     只生成大纲与节点卡片")
        print("  --mode node        只处理少量节点，默认 1 个")
        print("  --mode full        完整工作流，必须额外加 --full")
        return 2

    if mode == "quick":
        return quicktest_project(args)

    if check_project(args) != 0:
        return 1

    runtime_config_dir = prepare_runtime_config(args)
    print(f"\n使用运行配置：{runtime_config_dir}")

    from src.input_loader.input_service import InputService
    from src.workflow.node_pipeline import NodePipeline

    input_service = InputService()
    input_data = input_service.load_all_inputs()

    topic = input_data["topic"]
    goal = input_data["goal"]
    materials = input_data["materials"]
    project = Path(args.project).resolve()

    if mode == "literature":
        print("\n===== Literature Mode：仅生成文献摘要 =====")
        payload = _run_literature_only(args, input_data)
        report_json, report_md = _write_mode_report(project, "literature", payload)
        print("\nLiterature mode 完成。")
        print(f"报告 JSON：{report_json}")
        print(f"报告 Markdown：{report_md}")
        return 0

    if mode == "outline":
        print("\n===== Outline Mode：生成文献摘要、结构化总纲和节点卡片 =====")
        payload = _run_outline_only(args, input_data)
        report_json, report_md = _write_mode_report(project, "outline", payload)
        result = payload.get("result", {})
        print("\nOutline mode 完成。")
        print(f"结构化总纲：{result.get('schema_path')}")
        print(f"节点卡片：{result.get('cards_path')}")
        print(f"报告 JSON：{report_json}")
        print(f"报告 Markdown：{report_md}")
        return 0

    if mode == "node":
        if args.max_nodes is None or args.max_nodes <= 0:
            args.max_nodes = 1
        if args.max_nodes > 3 and not args.yes:
            print("node 模式建议 max_nodes <= 3。若确认要处理更多节点，请添加 --yes。")
            return 2
        print("\n===== Node Mode：只处理指定数量节点 =====")

    elif mode == "full":
        if not args.full:
            _print_full_run_safety(args, topic, len(materials))
            print("\n已阻止完整运行。若确认执行完整流程，请添加：--full --yes")
            return 2
        if not args.yes:
            _print_full_run_safety(args, topic, len(materials))
            confirm = input("确认执行完整流程？输入 yes 继续：")
            if confirm.strip().lower() != "yes":
                print("已取消完整运行。")
                return 0
        print("\n===== Full Mode：完整节点化论文写作工作流 =====")
    else:
        print(f"未知 mode：{mode}")
        return 2

    print(f"主题：{topic}")
    print(f"目标：{goal}")
    print(f"材料数量：{len(materials)}")
    print(f"调度策略：{args.strategy}")
    print(f"最大节点数：{args.max_nodes if args.max_nodes else '不限制'}")
    print(f"润色：{not args.no_polish} | 一致性检查：{not args.no_review} | 自动修订：{not args.no_revision}")
    print(f"组装 DOCX：{args.assemble or mode == 'full'}")

    start = time.perf_counter()
    pipeline = NodePipeline()
    result = pipeline.run(
        topic=topic,
        goal=goal,
        materials=materials,
        strategy=args.strategy,
        leaf_only=args.leaf_only,
        enable_consistency_revision=not args.no_revision,
        max_nodes=args.max_nodes,
        enable_polish=not args.no_polish,
        enable_review=not args.no_review,
        assemble=(args.assemble or mode == "full"),
    )
    elapsed = time.perf_counter() - start

    report_path = project / "outputs" / "run_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "project": str(project),
        "mode": mode,
        "strategy": args.strategy,
        "leaf_only": args.leaf_only,
        "max_nodes": args.max_nodes,
        "enable_polish": not args.no_polish,
        "enable_review": not args.no_review,
        "enable_consistency_revision": not args.no_revision,
        "assemble": (args.assemble or mode == "full"),
        "elapsed_seconds": round(elapsed, 2),
        "result": result,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md_path = _write_run_report_md(report_path, report)

    final_docx = result.get("assembled_result", {}).get("final_docx_path", "")
    print("\n===== 运行完成 =====")
    print(f"Mode：{mode}")
    print(f"处理节点数：{result.get('processed_nodes_count')}")
    print(f"NodePipeline 输出：{result.get('run_dir')}")
    print(f"最终 DOCX：{final_docx if final_docx else '<未组装>'}")
    print(f"运行报告 JSON：{report_path}")
    print(f"运行报告 Markdown：{report_md_path}")
    print(f"总耗时：{elapsed:.2f}s")
    return 0

def _latest_dir(base_dir: Path) -> Path | None:
    if not base_dir.exists():
        return None
    dirs = [p for p in base_dir.iterdir() if p.is_dir()]
    if not dirs:
        return None
    dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return dirs[0]


def assemble_project(args: argparse.Namespace) -> int:
    prepare_runtime_config(args)
    project = Path(args.project).resolve()
    run_dir = Path(args.run_dir).resolve() if args.run_dir else _latest_dir(project / "outputs" / "node_pipeline")
    if run_dir is None:
        print("未找到 node_pipeline 运行目录。请先执行 run，或用 --run-dir 指定。")
        return 1

    schema_path = run_dir / "outline_schema_used.json"
    node_map_path = run_dir / "node_polished_map.json"
    if not schema_path.exists() or not node_map_path.exists():
        print(f"运行目录缺少必要文件：{run_dir}")
        print("需要 outline_schema_used.json 和 node_polished_map.json")
        return 1

    from src.workflow.node_assembler import NodeAssembler

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    node_map = json.loads(node_map_path.read_text(encoding="utf-8"))
    result = NodeAssembler().assemble_from_schema_dict(
        schema=schema,
        node_text_map=node_map,
        include_empty_placeholder=True,
    )
    print("组装完成：", result.get("final_docx_path"))
    return 0


def clean_project(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    targets = [project / "outputs", project / ".paper_agent_runtime"]
    if not args.yes:
        print("将删除以下目录：")
        for target in targets:
            print(f"  - {target}")
        confirm = input("确认删除？输入 yes 继续：")
        if confirm.strip().lower() != "yes":
            print("已取消。")
            return 0
    for target in targets:
        if target.exists():
            shutil.rmtree(target)
            print(f"已删除：{target}")
    return 0



def web_project(args: argparse.Namespace) -> int:
    import subprocess

    app_path = PROJECT_ROOT / "web_app.py"
    if not app_path.exists():
        print(f"Web UI 文件不存在：{app_path}")
        return 1
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.address",
        args.host,
        "--server.port",
        str(args.port),
    ]
    print("启动 Web UI：")
    print(" ".join(cmd))
    return subprocess.call(cmd, cwd=str(PROJECT_ROOT))

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="paper-agent",
        description="Paper-Agent V0.3 CLI: safe modes for quick testing, outline generation, limited node writing, full workflow and Web UI support.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="初始化一个论文项目目录")
    p_init.add_argument("project", help="项目目录，例如 examples/demo_project")
    p_init.add_argument("--force", action="store_true", help="覆盖已存在的 topic/goal/demo material")
    p_init.set_defaults(func=init_project)

    def add_common_options(p: argparse.ArgumentParser) -> None:
        p.add_argument("--project", required=True, help="论文项目目录，包含 topic.txt、goal.txt、materials/")
        p.add_argument("--provider", default=None, help="Provider 名称，默认读取 config/models.yaml")
        p.add_argument("--model", default=None, help=f"覆盖聊天模型名称，例如 {DEFAULT_MODEL}")
        p.add_argument("--base-url", default=None, help="覆盖 Provider Base URL")
        p.add_argument("--api-key-env", default=None, help="API Key 环境变量名，例如 DEEPSEEK_API_KEY")
        p.add_argument("--max-pages", type=int, default=None, help="每个 PDF 最多读取页数")
        p.add_argument("--no-revision", action="store_true", help="关闭一致性检查后的自动修订回流")

    p_check = sub.add_parser("check", help="检查项目输入、配置和 API Key 环境变量")
    add_common_options(p_check)
    p_check.set_defaults(func=check_project)

    p_ping = sub.add_parser("ping", help="最小 LLM 连接测试，不运行论文工作流")
    add_common_options(p_ping)
    p_ping.add_argument("--message", default=None, help="自定义测试消息")
    p_ping.set_defaults(func=ping_project)

    p_quick = sub.add_parser("quicktest", help="最小端到端测试：读取材料并摘要，不生成整篇论文")
    add_common_options(p_quick)
    p_quick.add_argument("--max-chars", type=int, default=1000, help="只截取第一份材料的前 N 个字符用于测试")
    p_quick.set_defaults(func=quicktest_project)

    p_run = sub.add_parser("run", help="安全执行工作流。默认不完整生成，必须显式指定 --mode")
    add_common_options(p_run)
    p_run.add_argument("--mode", choices=["quick", "literature", "outline", "node", "full"], default=None, help="运行模式：quick/literature/outline/node/full")
    p_run.add_argument("--strategy", choices=["top_down", "bottom_up", "hybrid"], default="hybrid")
    p_run.add_argument("--leaf-only", action="store_true", help="只生成叶子节点正文")
    p_run.add_argument("--max-nodes", type=int, default=None, help="node/full 模式最多处理多少个节点；node 模式默认 1")
    p_run.add_argument("--no-polish", action="store_true", help="跳过节点润色，调试时可显著减少调用次数")
    p_run.add_argument("--no-review", action="store_true", help="跳过节点一致性检查，调试时可显著减少调用次数")
    p_run.add_argument("--assemble", action="store_true", help="node 模式下也组装 DOCX；默认不组装")
    p_run.add_argument("--full", action="store_true", help="确认执行完整工作流。仅 --mode full 需要")
    p_run.add_argument("--yes", action="store_true", help="跳过完整运行确认提示")
    p_run.set_defaults(func=run_project)

    p_assemble = sub.add_parser("assemble", help="用已有 node_polished_map 重新组装 DOCX")
    add_common_options(p_assemble)
    p_assemble.add_argument("--run-dir", default=None, help="指定 node_pipeline 运行目录；默认使用最新目录")
    p_assemble.set_defaults(func=assemble_project)

    p_web = sub.add_parser("web", help="启动 V0.3 Streamlit Web UI")
    p_web.add_argument("--host", default="127.0.0.1", help="Web UI host")
    p_web.add_argument("--port", type=int, default=8501, help="Web UI port")
    p_web.set_defaults(func=web_project)

    p_clean = sub.add_parser("clean", help="清理项目 outputs 和临时运行配置")
    p_clean.add_argument("--project", required=True)
    p_clean.add_argument("--yes", action="store_true", help="不询问直接删除")
    p_clean.set_defaults(func=clean_project)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n用户中断。")
        return 130
    except Exception as exc:
        print(f"运行失败：{type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
