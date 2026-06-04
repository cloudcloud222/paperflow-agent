from src.input_loader.input_service import InputService
from src.workflow.node_card_builder import NodeCardBuilder

service = InputService()
input_data = service.load_all_inputs()
topic = input_data["topic"]

builder = NodeCardBuilder()
result = builder.build_from_latest_schema(topic=topic)

print("===== 节点卡片构建完成 =====")
print("论文主题：", result["topic"])
print("输出目录：", result["run_dir"])
print("节点数量：", result["cards_count"])
print("JSON 文件：", result["cards_json_path"])
print("TXT 文件：", result["cards_txt_path"])