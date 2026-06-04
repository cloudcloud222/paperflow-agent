from src.input_loader.input_service import InputService
from src.workflow.section_pipeline import SectionPipeline

service = InputService()
input_data = service.load_all_inputs()

topic = input_data["topic"]
goal = input_data["goal"]
materials = input_data["materials"]

pipeline = SectionPipeline()
result = pipeline.run(
    topic=topic,
    goal=goal,
    materials=materials
)

print("\n\n===== Section Pipeline 执行完成 =====")
print("论文主题：", result["topic"])
print("输出目录：", result["run_dir"])
print("成本报告：", result["cost_report_path"])