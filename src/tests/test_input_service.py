from src.input_loader.input_service import InputService

service = InputService()
result = service.load_all_inputs()

print("===== topic =====")
print(result["topic"])

print("\n===== goal =====")
print(result["goal"])

print(f"\n===== materials 共 {len(result['materials'])} 篇 =====")

for index, item in enumerate(result["materials"], start=1):
    print(f"\n第 {index} 篇：{item['filename']}")
    preview = item["content"][:500]
    print(preview)
    print("------")