from pathlib import Path
from src.input_loader.input_service import InputService
from src.input_loader.file_reader import FileReader
from src.workflow.introduction_polisher import IntroductionPolisher
from src.utils.file_saver import FileSaver


def find_latest_file(base_dir: str, filename: str, topic: str = "") -> Path | None:
    base_path = Path(base_dir)

    if not base_path.exists():
        return None

    matched_files = list(base_path.rglob(filename))

    if topic:
        matched_files = [p for p in matched_files if topic in str(p.parent)]

    if not matched_files:
        return None

    matched_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return matched_files[0]


service = InputService()
input_data = service.load_all_inputs()

topic = input_data["topic"]
goal = input_data["goal"]

reader = FileReader()

# 读取最新的引言初稿
introduction_path = find_latest_file(
    "data/output/sections",
    "01_introduction.docx",
    topic=topic
)

if introduction_path is None:
    raise FileNotFoundError(
        f"未找到当前主题对应的引言初稿，请先运行 test_introduction_writer.py。topic={topic}"
    )

introduction_text = reader.read_input(str(introduction_path))

# 读取最新的总纲审查意见，如果没有则允许为空
outline_review_path = find_latest_file(
    "data/output/outlines",
    "02_outline_review.docx",
    topic=topic
)

outline_review_text = ""
if outline_review_path is not None:
    outline_review_text = reader.read_input(str(outline_review_path))

polisher = IntroductionPolisher()
polished_text = polisher.polish_introduction_stream(
    topic=topic,
    goal=goal,
    introduction_text=introduction_text,
    outline_review_text=outline_review_text
)

file_saver = FileSaver(base_dir="data/output/sections")
run_dir = file_saver.create_run_folder(topic)

file_saver.save_docx(
    run_dir,
    "01_introduction_raw.docx",
    introduction_text,
    f"{topic} - Introduction 初稿"
)

file_saver.save_docx(
    run_dir,
    "02_introduction_polished.docx",
    polished_text,
    f"{topic} - Introduction 润色稿"
)

print("\n\n===== Introduction 润色完成 =====")
print("使用的引言初稿：", introduction_path)
print("使用的总纲审查：", outline_review_path if outline_review_path else "未提供")
print("保存目录：", run_dir)
print(polished_text)