from src.input_loader.input_service import InputService
from src.workflow.literature_pipeline import LiteraturePipeline
from src.workflow.outline_planner import OutlinePlanner
from src.workflow.outline_reviewer import OutlineReviewer
from src.utils.file_saver import FileSaver

service = InputService()
input_data = service.load_all_inputs()

topic = input_data["topic"]
goal = input_data["goal"]
materials = input_data["materials"]

literature_pipeline = LiteraturePipeline()
literature_result = literature_pipeline.run(topic=topic, materials=materials)
literature_pack_text = literature_result["merged_summary_text"]

outline_planner = OutlinePlanner()
outline_result = outline_planner.plan_outline(
    topic=topic,
    goal=goal,
    literature_pack_text=literature_pack_text,
    organized_material=""
)

outline_reviewer = OutlineReviewer()
review_result = outline_reviewer.review_outline_stream(outline_result)

file_saver = FileSaver(base_dir="data/output/outlines")
run_dir = file_saver.create_run_folder(topic)

file_saver.save_docx(
    run_dir,
    "01_outline.docx",
    outline_result,
    f"{topic} - 论文总纲"
)

file_saver.save_docx(
    run_dir,
    "02_outline_review.docx",
    review_result,
    f"{topic} - 总纲审查"
)

print("\n\n===== 总纲审查完成 =====")
print("保存目录：", run_dir)
print(review_result)