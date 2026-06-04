import json
from pathlib import Path

from src.input_loader.input_service import InputService
from src.workflow.literature_pipeline import LiteraturePipeline
from src.workflow.outline_schema_planner import OutlineSchemaPlanner

service = InputService()
input_data = service.load_all_inputs()

topic = input_data["topic"]
goal = input_data["goal"]
materials = input_data["materials"]

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

output_dir = Path("data/output/outline_schemas")
output_dir.mkdir(parents=True, exist_ok=True)

safe_topic = topic.replace("/", "_").replace("\\", "_").replace(":", "_")
output_path = output_dir / f"{safe_topic}_outline_schema.json"

output_path.write_text(
    json.dumps(schema, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("===== 结构化总纲生成完成 =====")
print("输出文件：", output_path)
print(json.dumps(schema, ensure_ascii=False, indent=2))