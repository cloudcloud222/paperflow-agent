import json
from pathlib import Path

from src.input_loader.input_service import InputService
from src.workflow.node_card_builder import NodeCardBuilder
from src.workflow.outline_schema_planner import OutlineSchemaPlanner
from src.workflow.literature_pipeline import LiteraturePipeline
from src.workflow.node_assembler import NodeAssembler


def choose_some_nodes(cards: list[dict], max_count: int = 6) -> list[dict]:
    """
    选取一部分节点，构造演示用 node_text_map。
    优先选叶子节点。
    """
    leaf_cards = [c for c in cards if not c.get("has_children", False)]
    if leaf_cards:
        return leaf_cards[:max_count]
    return cards[:max_count]


service = InputService()
input_data = service.load_all_inputs()

topic = input_data["topic"]
goal = input_data["goal"]
materials = input_data["materials"]

# 1. 先确保 schema 存在
literature_pipeline = LiteraturePipeline()
literature_result = literature_pipeline.run(topic=topic, materials=materials)
literature_pack_text = literature_result["merged_summary_text"]

schema_planner = OutlineSchemaPlanner()
schema = schema_planner.plan_schema(
    topic=topic,
    goal=goal,
    literature_pack_text=literature_pack_text,
    organized_material=""
)

# 2. 构造节点卡片
builder = NodeCardBuilder()
build_result = builder.build_from_schema(schema)
cards = build_result["cards"]

# 3. 这里只做演示：手工构造一部分节点正文映射
selected_cards = choose_some_nodes(cards, max_count=6)

node_text_map = {}
for card in selected_cards:
    node_text_map[card["id"]] = (
        f"这是节点“{card['display_title']}”的演示正文。"
        f"本段用于测试 node_assembler 的递归组装能力。"
        f"节点目标为：{card.get('goal', '')}"
    )

# 4. 递归组装
assembler = NodeAssembler()
result = assembler.assemble_from_schema_dict(
    schema=schema,
    node_text_map=node_text_map,
    include_empty_placeholder=True
)

print("===== Node Assembler 测试完成 =====")
print("论文主题：", result["topic"])
print("输出目录：", result["run_dir"])
print("全文 docx：", result["final_docx_path"])
print("全文 RuleDoc docx：", result["final_ruledoc_path"] if result["final_ruledoc_path"] else "未启用")
print("节点正文映射：", result["node_text_map_path"])