from src.input_loader.input_service import InputService
from src.workflow.paper_assembler import PaperAssembler

service = InputService()
input_data = service.load_all_inputs()
topic = input_data["topic"]

assembler = PaperAssembler()
result = assembler.assemble_from_latest_sections(topic=topic)

print("\n\n===== 全文组装完成 =====")
print("论文主题：", result["topic"])
print("输出目录：", result["run_dir"])
print("全文 docx：", result["final_docx_path"])
print("全文 RuleDoc docx：", result["final_ruledoc_path"] if result["final_ruledoc_path"] else "未启用")
print("使用的章节来源：", result["source_paths"])