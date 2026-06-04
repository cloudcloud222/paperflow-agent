import json
from pathlib import Path
from datetime import datetime

from src.input_loader.input_service import InputService
from src.input_loader.file_reader import FileReader
from src.workflow.node_writer import NodeWriter
from src.workflow.node_polisher import NodePolisher
from src.workflow.outline_schema_planner import OutlineSchemaPlanner
from src.workflow.node_card_builder import NodeCardBuilder
from src.workflow.literature_pipeline import LiteraturePipeline


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


service = InputService()
input_data = service.load_all_inputs()

topic = input_data["topic"]
goal = input_data["goal"]
materials = input_data["materials"]

reader = FileReader()

# 文献整理总文档
literature_pack_path = find_latest_file(
    "data/output/literature_summaries",
    "literature_review_pack.docx",
    topic=topic
)

if literature_pack_path is None:
    print("未找到已有文献整理总文档，开始自动生成...")
    literature_pipeline = LiteraturePipeline()
    literature_result = literature_pipeline.run(topic=topic, materials=materials)
    literature_pack_text = literature_result["merged_summary_text"]
else:
    print("复用文献整理总文档：", literature_pack_path)
    literature_pack_text = reader.read_input(str(literature_pack_path))

# 节点卡片
cards_path = find_latest_file(
    "data/output/node_cards",
    "node_cards.json",
    topic=topic
)

if cards_path is None:
    print("未找到已有 node_cards.json，开始自动生成结构化总纲与节点卡片...")
    schema_planner = OutlineSchemaPlanner()
    schema = schema_planner.plan_schema(
        topic=topic,
        goal=goal,
        literature_pack_text=literature_pack_text,
        organized_material=""
    )

    builder = NodeCardBuilder()
    build_result = builder.build_from_schema(schema)
    cards_path = Path(build_result["cards_json_path"])
else:
    print("复用节点卡片文件：", cards_path)

cards = json.loads(cards_path.read_text(encoding="utf-8"))
target_node = choose_target_node(cards)

# 总纲审查（可选）
outline_review_path = find_latest_file(
    "data/output/outlines",
    "02_outline_review.docx",
    topic=topic
)

outline_review_text = ""
if outline_review_path is not None:
    print("复用总纲审查：", outline_review_path)
    outline_review_text = reader.read_input(str(outline_review_path))
else:
    print("未找到总纲审查文件，本次以空审查意见继续。")

# 先写节点初稿
writer = NodeWriter()
node_raw_text = writer.write_node(
    topic=topic,
    goal=goal,
    node_card=target_node,
    literature_pack_text=literature_pack_text,
    outline_review_text=outline_review_text,
    previous_context_text=""
)

# 再润色
polisher = NodePolisher()
node_polished_text = polisher.polish_node_stream(
    topic=topic,
    goal=goal,
    node_card=target_node,
    node_text=node_raw_text,
    literature_pack_text=literature_pack_text,
    outline_review_text=outline_review_text,
    previous_context_text=""
)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
safe_topic = sanitize_name(topic)
output_dir = Path("data/output/node_writings") / f"{timestamp}_{safe_topic}"
output_dir.mkdir(parents=True, exist_ok=True)

raw_output_path = output_dir / "node_raw_output.txt"
raw_output_path.write_text(node_raw_text, encoding="utf-8")

polished_output_path = output_dir / "node_polished_output.txt"
polished_output_path.write_text(node_polished_text, encoding="utf-8")

card_path = output_dir / "node_card_used.json"
card_path.write_text(json.dumps(target_node, ensure_ascii=False, indent=2), encoding="utf-8")

print("\n\n===== Node Polisher 生成完成 =====")
print("使用的节点：", target_node["display_title"])
print("节点类型：", target_node["node_type"])
print("节点路径：", target_node["path"])
print("输出目录：", output_dir)
print("初稿输出：", raw_output_path)
print("润色输出：", polished_output_path)
print("节点卡片：", card_path)