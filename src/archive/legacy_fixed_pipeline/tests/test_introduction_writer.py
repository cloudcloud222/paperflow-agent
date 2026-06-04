from pathlib import Path
from src.input_loader.input_service import InputService
from src.input_loader.file_reader import FileReader
from src.workflow.literature_pipeline import LiteraturePipeline
from src.workflow.outline_planner import OutlinePlanner
from src.workflow.outline_reviewer import OutlineReviewer
from src.workflow.introduction_writer import IntroductionWriter
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
materials = input_data["materials"]

reader = FileReader()

# ---------- 第1步：获取文献整理总文档 ----------
literature_pack_path = find_latest_file(
    "data/output/literature_summaries",
    "literature_review_pack.docx",
    topic=topic
)

if literature_pack_path is None:
    print("未找到已有文献整理总文档，开始自动生成...")
    literature_pipeline = LiteraturePipeline()
    literature_result = literature_pipeline.run(topic=topic, materials=materials)
    literature_pack_text = literature_result["merged_summary_text"]
    literature_pack_path = Path(literature_result["merged_docx_path"])
else:
    print("复用已有文献整理总文档：", literature_pack_path)
    literature_pack_text = reader.read_input(str(literature_pack_path))

# ---------- 第2步：获取总纲和总纲审查，如果没有则自动生成 ----------
outline_path = find_latest_file(
    "data/output/outlines",
    "01_outline.docx",
    topic=topic
)
outline_review_path = find_latest_file(
    "data/output/outlines",
    "02_outline_review.docx",
    topic=topic
)

if outline_path is None or outline_review_path is None:
    print("未找到已有总纲或总纲审查，开始自动生成...")

    outline_planner = OutlinePlanner()
    outline_text = outline_planner.plan_outline(
        topic=topic,
        goal=goal,
        literature_pack_text=literature_pack_text,
        organized_material=""
    )

    outline_reviewer = OutlineReviewer()
    outline_review_text = outline_reviewer.review_outline(
        outline_text
    )

    outline_saver = FileSaver(base_dir="data/output/outlines")
    outline_run_dir = outline_saver.create_run_folder(topic)

    outline_saver.save_docx(
        outline_run_dir,
        "01_outline.docx",
        outline_text,
        f"{topic} - 论文总纲"
    )

    outline_saver.save_docx(
        outline_run_dir,
        "02_outline_review.docx",
        outline_review_text,
        f"{topic} - 总纲审查"
    )

    outline_path = outline_run_dir / "01_outline.docx"
    outline_review_path = outline_run_dir / "02_outline_review.docx"
else:
    print("复用已有总纲：", outline_path)
    print("复用已有总纲审查：", outline_review_path)
    outline_text = reader.read_input(str(outline_path))
    outline_review_text = reader.read_input(str(outline_review_path))

# ---------- 第3步：生成 Introduction ----------
introduction_writer = IntroductionWriter()
introduction_text = introduction_writer.write_introduction_stream(
    topic=topic,
    goal=goal,
    literature_pack_text=literature_pack_text,
    outline_text=outline_text,
    outline_review_text=outline_review_text
)

section_saver = FileSaver(base_dir="data/output/sections")
section_run_dir = section_saver.create_run_folder(topic)

section_saver.save_docx(
    section_run_dir,
    "01_introduction.docx",
    introduction_text,
    f"{topic} - Introduction 初稿"
)

print("\n\n===== Introduction 生成完成 =====")
print("使用的文献整理总文档：", literature_pack_path)
print("使用的总纲：", outline_path)
print("使用的总纲审查：", outline_review_path)
print("保存目录：", section_run_dir)
print(introduction_text)