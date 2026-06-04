from src.input_loader.input_service import InputService
from src.workflow.literature_pipeline import LiteraturePipeline
from src.workflow.outline_planner import OutlinePlanner
from src.utils.file_saver import FileSaver

service = InputService()
input_data = service.load_all_inputs()

topic = input_data["topic"]
goal = input_data["goal"]
materials = input_data["materials"]

literature_pipeline = LiteraturePipeline()
literature_result = literature_pipeline.run(topic=topic, materials=materials)

literature_pack_text = literature_result["merged_summary_text"]

planner = OutlinePlanner()
outline_result = planner.plan_outline_stream(
    topic=topic,
    goal=goal,
    literature_pack_text=literature_pack_text,
    organized_material=""
)

file_saver = FileSaver(base_dir="data/output/outlines")
run_dir = file_saver.create_run_folder(topic)
file_saver.save_docx(
    run_dir,
    "01_outline.docx",
    outline_result,
    f"{topic} - 论文总纲"
)

print("\n\n===== 总纲生成完成 =====")
print("保存目录：", run_dir)
print(outline_result)