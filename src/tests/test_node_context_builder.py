import json
from pathlib import Path

from src.input_loader.input_service import InputService
from src.workflow.node_card_builder import NodeCardBuilder
from src.workflow.outline_schema_planner import OutlineSchemaPlanner
from src.workflow.literature_pipeline import LiteraturePipeline
from src.workflow.node_context_builder import NodeContextBuilder


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
    # 优先选一个非顶层、最好有父节点的叶子节点
    leaf_cards = [c for c in cards if not c.get("has_children", False) and c.get("level", 1) >= 2]
    if leaf_cards:
        return leaf_cards[0]
    return cards[0]


service = InputService()
input_data = service.load_all_inputs()

topic = input_data["topic"]
goal = input_data["goal"]
materials = input_data["materials"]

# 1. 准备 schema
schema_path = find_latest_file("data/output/outline_schemas", ".json", topic=topic)

if schema_path is None or schema_path.suffix.lower() != ".json":
    literature_pipeline = LiteraturePipeline()
    literature_result = literature_pipeline.run(topic=topic, materials=materials)
    literature_pack_text = literature_result["merged_summary_text"]

    planner = OutlineSchemaPlanner()
    schema = planner.plan_schema(
        topic=topic,
        goal=goal,
        literature_pack_text=literature_pack_text,
        organized_material=""
    )
else:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

# 2. 构造 node cards
builder = NodeCardBuilder()
build_result = builder.build_from_schema(schema)
cards = build_result["cards"]

target_node = choose_target_node(cards)

# 3. 伪造一个已完成内容映射，模拟父节点/兄弟节点已写
polished_map = {}
for card in cards[:5]:
    polished_map[card["id"]] = f"这是节点 {card['display_title']} 的已完成正文示例，用于测试上下文构造。"

# 4. 构造上下文
context_builder = NodeContextBuilder()
result = context_builder.build_context_package(
    topic=topic,
    goal=goal,
    node_card=target_node,
    all_cards=cards,
    polished_map=polished_map
)

output_dir = Path("data/output/node_context_tests")
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / "node_context_preview.txt"
output_path.write_text(result["context_text"], encoding="utf-8")

print("===== Node Context Builder 测试完成 =====")
print("目标节点：", target_node["display_title"])
print("上下文长度：", result["context_chars"])
print("输出文件：", output_path)
print(result["context_text"])