from src.input_loader.file_reader import FileReader

reader = FileReader()

topic_text = reader.read_input("data/input/topic")
goal_text = reader.read_input("data/input/goal")

print("===== topic 内容 =====")
print(topic_text)

print("\n===== goal 内容 =====")
print(goal_text)