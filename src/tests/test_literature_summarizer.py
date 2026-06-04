from src.input_loader.input_service import InputService
from src.workflow.literature_summarizer import LiteratureSummarizer

service = InputService()
input_data = service.load_all_inputs()

materials = input_data["materials"]

if not materials:
    raise ValueError("materials 为空，没有可摘要的 PDF")

first_paper = materials[0]

summarizer = LiteratureSummarizer()

result = summarizer.summarize_stream(
    filename=first_paper["filename"],
    content=first_paper["content"]
)

print("\n\n===== 文献摘要完成 =====")
print(result)