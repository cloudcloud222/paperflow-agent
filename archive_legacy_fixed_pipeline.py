from pathlib import Path
import shutil

# =========================
# 一次性归档脚本配置
# =========================

# 第一次运行建议保持 True，只打印将要移动的内容，不真正执行
DRY_RUN = False

# 若目标位置已存在同名文件：
# True  -> 覆盖旧文件
# False -> 跳过该文件
OVERWRITE = False

PROJECT_ROOT = Path(__file__).resolve().parent

SRC_ROOT = PROJECT_ROOT / "src"
ARCHIVE_ROOT = SRC_ROOT / "archive" / "legacy_fixed_pipeline"

WORKFLOW_ARCHIVE = ARCHIVE_ROOT / "workflow"
PROMPTS_ARCHIVE = ARCHIVE_ROOT / "prompts"
TESTS_ARCHIVE = ARCHIVE_ROOT / "tests"
ENTRYPOINTS_ARCHIVE = ARCHIVE_ROOT / "entrypoints"


def ensure_archive_dirs():
    WORKFLOW_ARCHIVE.mkdir(parents=True, exist_ok=True)
    PROMPTS_ARCHIVE.mkdir(parents=True, exist_ok=True)
    TESTS_ARCHIVE.mkdir(parents=True, exist_ok=True)
    ENTRYPOINTS_ARCHIVE.mkdir(parents=True, exist_ok=True)


def move_file(src: Path, dst: Path):
    if not src.exists():
        print(f"[跳过] 源文件不存在: {src}")
        return

    dst.parent.mkdir(parents=True, exist_ok=True)

    if dst.exists():
        if OVERWRITE:
            print(f"[覆盖] {dst}")
            if not DRY_RUN:
                dst.unlink()
        else:
            print(f"[跳过] 目标已存在: {dst}")
            return

    print(f"[归档] {src}  ->  {dst}")
    if not DRY_RUN:
        shutil.move(str(src), str(dst))


def archive_workflow_files():
    files = [
        "planner.py",
        "organizer.py",
        "writer.py",
        "reviewer.py",
        "reviser.py",
        "pipeline.py",
        "introduction_writer.py",
        "introduction_polisher.py",
        "related_work_writer.py",
        "related_work_polisher.py",
        "methodology_writer.py",
        "methodology_polisher.py",
        "experiment_writer.py",
        "experiment_polisher.py",
        "conclusion_writer.py",
        "conclusion_polisher.py",
        "section_pipeline.py",
        "paper_assembler.py",
        "outline_planner.py",
        "outline_reviewer.py",
    ]

    for filename in files:
        src = SRC_ROOT / "workflow" / filename
        dst = WORKFLOW_ARCHIVE / filename
        move_file(src, dst)


def archive_prompt_files():
    files = [
        "planner.txt",
        "organizer.txt",
        "writer.txt",
        "reviewer.txt",
        "reviser.txt",
        "outline_planner.txt",
        "outline_reviewer.txt",
        "introduction_writer.txt",
        "introduction_polisher.txt",
        "related_work_writer.txt",
        "related_work_polisher.txt",
        "methodology_writer.txt",
        "methodology_polisher.txt",
        "experiment_writer.txt",
        "experiment_polisher.txt",
        "conclusion_writer.txt",
        "conclusion_polisher.txt",
    ]

    for filename in files:
        src = SRC_ROOT / "prompts" / filename
        dst = PROMPTS_ARCHIVE / filename
        move_file(src, dst)


def archive_test_files():
    files = [
        "test_outline_planner.py",
        "test_outline_reviewer.py",
        "test_introduction_writer.py",
        "test_introduction_polisher.py",
        "test_section_pipeline.py",
        "test_paper_assembler.py",
    ]

    for filename in files:
        src = SRC_ROOT / "tests" / filename
        dst = TESTS_ARCHIVE / filename
        move_file(src, dst)


def archive_entrypoints():
    files = [
        "run_pipeline.py",
        "run_section_pipeline.py",
    ]

    for filename in files:
        src = SRC_ROOT / filename
        dst = ENTRYPOINTS_ARCHIVE / filename
        move_file(src, dst)


def main():
    print("===== 开始归档旧固定流水线文件 =====")
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"归档根目录: {ARCHIVE_ROOT}")
    print(f"DRY_RUN = {DRY_RUN}")
    print(f"OVERWRITE = {OVERWRITE}")
    print()

    ensure_archive_dirs()

    print("----- 归档 workflow -----")
    archive_workflow_files()
    print()

    print("----- 归档 prompts -----")
    archive_prompt_files()
    print()

    print("----- 归档 tests -----")
    archive_test_files()
    print()

    print("----- 归档 entrypoints -----")
    archive_entrypoints()
    print()

    if DRY_RUN:
        print("===== 预演完成：尚未真正移动文件 =====")
        print("确认无误后，把脚本里的 DRY_RUN 改为 False，再运行一次。")
    else:
        print("===== 归档完成 =====")


if __name__ == "__main__":
    main()