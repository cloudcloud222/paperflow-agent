import json
from pathlib import Path
from datetime import datetime

from src.input_loader.input_service import InputService
from src.input_loader.file_reader import FileReader
from src.workflow.node_reference_selector import NodeReferenceSelector
from src.workflow.node_pipeline import NodePipeline


def sanitize_name(name: str) -> str:
    invalid_chars = '<>:"/\\|?*'
    sanitized = name
    for ch in invalid_chars:
        sanitized = sanitized.replace(ch, "_")
    sanitized = sanitized.strip()
    return sanitized[:50] if len(sanitized) > 50 else sanitized


def find_latest_file(base_dir: str, filename: str, topic: str = "") -> Path | None:
    base_path = Path(base_dir)
    if not base_path.exists():
        return None

    matched_files = list(base_path.rglob(filename))

    if topic:
        topic_matched = [p for p in matched_files if topic in str(p)]
        if topic_matched:
            topic_matched.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            return topic_matched[0]

    if not matched_files:
        return None

    matched_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return matched_files[0]


def choose_target_node(cards: list[dict]) -> dict:
    # 优先选一个偏技术细节的叶子节点
    preferred_types = {
        "system_model",
        "problem_formulation",
        "solution_framework",
        "algorithm",
        "mechanism",
        "subsection",
        "custom"
    }

    leaf_cards = [c for c in cards if not c.get("has_children", False)]
    for card in leaf_cards:
        if card.get("node_type") in preferred_types:
            return card

    if leaf_cards:
        return leaf_cards[0]

    return cards[0]


def load_literature_summaries(reader: FileReader, topic: str) -> list[dict]:
    summaries = []

    # 优先读取当前 topic 对应目录下的 *_summary.docx
    base_dir = Path("data/output/literature_summaries")
    if not base_dir.exists():
        return summaries

    matched_dirs = [p for p in base_dir.iterdir() if p.is_dir() and topic in p.name]
    matched_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    candidate_dirs = matched_dirs if matched_dirs else sorted(
        [p for p in base_dir.iterdir() if p.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    for run_dir in candidate_dirs[:3]:
        summary_files = sorted(run_dir.glob("*_summary.docx"))
        if not summary_files:
            continue

        for f in summary_files:
            try:
                content = reader.read_input(str(f))
                summaries.append({
                    "source_filename": f.name,
                    "summary_text": content
                })
            except Exception:
                pass

        if summaries:
            break

    return summaries


service = InputService()
input_data = service.load_all_inputs()

topic = input_data["topic"]
goal = input_data["goal"]
materials = input_data["materials"]

reader = FileReader()

# ---------- 第1步：尽量复用最新 node_pipeline 结果 ----------
cards_path = find_latest_file("data/output/node_pipeline", "node_cards_used.json", topic=topic)
polished_map_path = find_latest_file("data/output/node_pipeline", "node_polished_map.json", topic=topic)

if cards_path is None or polished_map_path is None:
    print("未找到可用 node_pipeline 结果，开始自动执行一次 node_pipeline...")
    pipeline = NodePipeline()
    run_result = pipeline.run(
        topic=topic,
        goal=goal,
        materials=materials,
        strategy="hybrid",
        leaf_only=False
    )
    cards_path = Path(run_result["cards_used_path"])
    polished_map_path = Path(run_result["polished_map_path"])

cards = json.loads(cards_path.read_text(encoding="utf-8"))
polished_map = json.loads(polished_map_path.read_text(encoding="utf-8"))
target_node = choose_target_node(cards)

# ---------- 第2步：读取文献摘要 ----------
literature_summaries = load_literature_summaries(reader, topic)
if not literature_summaries:
    raise FileNotFoundError("未找到可用的文献摘要文件，请先确保 literature_pipeline 已运行成功。")

# ---------- 第3步：读取总纲审查（可选） ----------
outline_review_path = find_latest_file("data/output/outlines", "02_outline_review.docx", topic=topic)
outline_review_text = ""
if outline_review_path is not None:
    outline_review_text = reader.read_input(str(outline_review_path))

# ---------- 第4步：构造前序上下文 ----------
previous_context_text = ""
parent_id = target_node.get("parent_id")
if parent_id and parent_id in polished_map:
    previous_context_text = polished_map[parent_id]

# ---------- 第5步：执行选择 ----------
selector = NodeReferenceSelector()
selection_result = selector.select_references(
    topic=topic,
    goal=goal,
    node_card=target_node,
    literature_summaries=literature_summaries,
    outline_review_text=outline_review_text,
    previous_context_text=previous_context_text
)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
safe_topic = sanitize_name(topic)
output_dir = Path("data/output/node_references") / f"{timestamp}_{safe_topic}"
output_dir.mkdir(parents=True, exist_ok=True)

result_path = output_dir / "node_reference_selection.json"
result_path.write_text(
    json.dumps(selection_result, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

target_card_path = output_dir / "target_node_card.json"
target_card_path.write_text(
    json.dumps(target_node, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("\n\n===== Node Reference Selector 完成 =====")
print("目标节点：", target_node["display_title"])
print("目标节点类型：", target_node["node_type"])
print("结果文件：", result_path)
print("节点卡片：", target_card_path)
print(json.dumps(selection_result, ensure_ascii=False, indent=2))