from src.input_loader.input_service import InputService
from src.workflow.literature_pipeline import LiteraturePipeline

service = InputService()
input_data = service.load_all_inputs()

topic = input_data["topic"]

pipeline = LiteraturePipeline()
result = pipeline.run(topic=topic)

print("\n\n===== 文献批量摘要完成 =====")
print("结果保存目录：", result["run_dir"])
print("共生成摘要数量：", len(result["summaries"]))
print("文献整理总文档：", result["merged_docx_path"])