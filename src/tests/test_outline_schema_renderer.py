from src.input_loader.input_service import InputService
from src.workflow.outline_schema_renderer import OutlineSchemaRenderer

service = InputService()
input_data = service.load_all_inputs()
topic = input_data["topic"]

renderer = OutlineSchemaRenderer()
result = renderer.render_latest_schema(topic=topic)

print("===== 结构化总纲渲染完成 =====")
print("论文主题：", result["topic"])
print("输出目录：", result["run_dir"])
print("TXT 文件：", result["txt_path"])
print("DOCX 文件：", result["docx_path"])