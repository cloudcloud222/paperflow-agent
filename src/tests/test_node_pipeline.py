from src.input_loader.input_service import InputService
from src.workflow.node_pipeline import NodePipeline

service = InputService()
input_data = service.load_all_inputs()

topic = input_data["topic"]
goal = input_data["goal"]
materials = input_data["materials"]

pipeline = NodePipeline()
result = pipeline.run(
    topic=topic,
    goal=goal,
    materials=materials,
    strategy="hybrid",
    leaf_only=False,
    enable_consistency_revision=True
)

print("\n\n===== Node Pipeline 执行完成 =====")
print("论文主题：", result["topic"])
print("NodePipeline 输出目录：", result["run_dir"])
print("节点输出目录：", result["nodes_dir"])
print("已处理节点数：", result["processed_nodes_count"])
print("调度结果：", result["scheduled_cards_path"])
print("参考文献映射：", result["reference_map_path"])
print("一致性检查映射：", result["consistency_map_path"])
print("成本报告：", result["cost_report_path"])

assembled = result["assembled_result"]
print("\n===== Node Assembler 输出 =====")
print("全文输出目录：", assembled["run_dir"])
print("全文 docx：", assembled["final_docx_path"])
print("全文 RuleDoc docx：", assembled["final_ruledoc_path"] if assembled["final_ruledoc_path"] else "未启用")