import json
from pathlib import Path
from datetime import datetime

from src.input_loader.input_service import InputService
from src.input_loader.file_reader import FileReader
from src.workflow.node_consistency_checker import NodeConsistencyChecker
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
    candidates = [
        c for c in cards
        if c.get("parent_id") and not c.get("has_children", False)
    ]
    if candidates:
        return candidates[0]
    return cards[0]


def build_card_index(cards: list[dict]) -> dict:
    return {card["id"]: card for card in cards if card.get("id")}


service = InputService()
input_data = service.load_all_inputs()

topic = input_data["topic"]
goal = input_data["goal"]
materials = input_data["materials"]

reader = FileReader()

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
        leaf_only=False,
        enable_consistency_revision=True
    )
    cards_path = Path(run_result["cards_used_path"])
    polished_map_path = Path(run_result["polished_map_path"])

cards = json.loads(cards_path.read_text(encoding="utf-8"))
polished_map = json.loads(polished_map_path.read_text(encoding="utf-8"))
card_index = build_card_index(cards)

target_node = choose_target_node(cards)
target_node_id = target_node["id"]
target_node_text = polished_map.get(target_node_id, "")

parent_card = None
parent_text = ""
parent_id = target_node.get("parent_id")
if parent_id and parent_id in card_index:
    parent_card = card_index[parent_id]
    parent_text = polished_map.get(parent_id, "")

sibling_cards = [
    c for c in cards
    if c.get("parent_id") == target_node.get("parent_id") and c.get("id") != target_node_id
]
sibling_text_map = {c["id"]: polished_map.get(c["id"], "") for c in sibling_cards}

child_cards = [
    c for c in cards
    if c.get("parent_id") == target_node_id
]
child_text_map = {c["id"]: polished_map.get(c["id"], "") for c in child_cards}

outline_review_path = find_latest_file("data/output/outlines", "02_outline_review.docx", topic=topic)
outline_review_text = ""
if outline_review_path is not None:
    outline_review_text = reader.read_input(str(outline_review_path))

checker = NodeConsistencyChecker()
report_result = checker.check_node(
    topic=topic,
    goal=goal,
    target_node_card=target_node,
    target_node_text=target_node_text,
    parent_card=parent_card,
    parent_text=parent_text,
    sibling_cards=sibling_cards,
    sibling_text_map=sibling_text_map,
    child_cards=child_cards,
    child_text_map=child_text_map,
    outline_review_text=outline_review_text
)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
safe_topic = sanitize_name(topic)
output_dir = Path("data/output/node_consistency_checks") / f"{timestamp}_{safe_topic}"
output_dir.mkdir(parents=True, exist_ok=True)

report_path = output_dir / "node_consistency_report.json"
report_path.write_text(
    json.dumps(report_result, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

target_card_path = output_dir / "target_node_card.json"
target_card_path.write_text(
    json.dumps(target_node, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("\n\n===== Node Consistency Checker 完成 =====")
print("目标节点：", target_node["display_title"])
print("目标节点类型：", target_node["node_type"])
print("是否需要修订：", report_result.get("revision_required"))
print("是否可进入组装：", report_result.get("pass_for_assembly"))
print("修订优先级：", report_result.get("revision_priority"))
print("报告文件：", report_path)
print("节点卡片：", target_card_path)
print(json.dumps(report_result, ensure_ascii=False, indent=2))