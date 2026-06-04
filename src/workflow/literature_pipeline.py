import time
from src.input_loader.input_service import InputService
from src.workflow.literature_summarizer import LiteratureSummarizer
from src.utils.file_saver import FileSaver
from src.utils.config_loader import ConfigLoader
from src.utils.logger import get_logger
from src.utils.cost_tracker import CostTracker


class LiteraturePipeline:
    def __init__(self):
        self.input_service = InputService()
        self.summarizer = LiteratureSummarizer()
        self.config_loader = ConfigLoader()
        self.logger = get_logger("LiteraturePipeline")
        self.cost_tracker = CostTracker()

        paths_config = self.config_loader.load_paths_config()
        runtime_config = self.config_loader.load_runtime_config()

        literature_output_dir = paths_config["output"]["literature_dir"]
        self.file_saver = FileSaver(base_dir=literature_output_dir)

        self.stream_config = runtime_config["stream"]

    def _call_summarizer(self, filename: str, content: str) -> str:
        if self.stream_config.get("literature_summarizer", False):
            return self.summarizer.summarize_stream(filename=filename, content=content)
        return self.summarizer.summarize(filename=filename, content=content)

    def run(self, topic: str, materials: list[dict] | None = None) -> dict:
        total_start = time.perf_counter()
        self.logger.info(f"文献摘要流程开始 | topic={topic}")

        if materials is None:
            input_data = self.input_service.load_all_inputs()
            materials = input_data["materials"]

        if not materials:
            self.logger.error("materials 为空，没有可处理的 PDF")
            raise ValueError("materials 为空，没有可处理的 PDF")

        run_dir = self.file_saver.create_run_folder(topic + "_literature")
        self.logger.info(f"文献摘要输出目录创建完成 | run_dir={run_dir}")

        all_summaries = []
        merged_parts = []

        for index, paper in enumerate(materials, start=1):
            step_start = time.perf_counter()
            filename = paper["filename"]

            print(f"\n===== 正在处理第 {index} 篇：{filename} =====\n")
            self.logger.info(f"开始处理文献 | index={index} | filename={filename}")

            summary = self._call_summarizer(
                filename=filename,
                content=paper["content"]
            )

            all_summaries.append({
                "filename": filename,
                "summary": summary
            })

            merged_parts.append(
                f"【第{index}篇文献：{filename}】\n{summary}"
            )

            safe_name = f"{index:02d}_{filename.replace('.pdf', '')}_summary.docx"
            self.file_saver.save_docx(
                run_dir,
                safe_name,
                summary,
                f"{topic} - {filename} 文献摘要"
            )

            elapsed = time.perf_counter() - step_start

            self.cost_tracker.record(
                component=f"literature_summarizer_{index}",
                model=self.summarizer.get_model_name(),
                input_text=paper["content"],
                output_text=summary,
                elapsed_seconds=elapsed
            )

            self.logger.info(
                f"文献处理完成 | index={index} | filename={filename} | elapsed={elapsed:.2f}s | output={run_dir / safe_name}"
            )

        separator = "\n\n" + ("=" * 50) + "\n\n"
        merged_summary_text = separator.join(merged_parts)

        merged_docx_name = "literature_review_pack.docx"
        self.file_saver.save_docx(
            run_dir,
            merged_docx_name,
            merged_summary_text,
            f"{topic} - 文献整理总文档"
        )

        total_elapsed = time.perf_counter() - total_start
        self.logger.info(
            f"文献摘要流程完成 | topic={topic} | count={len(all_summaries)} | elapsed={total_elapsed:.2f}s | merged_doc={run_dir / merged_docx_name}"
        )

        return {
            "run_dir": str(run_dir),
            "topic": topic,
            "summaries": all_summaries,
            "merged_summary_text": merged_summary_text,
            "merged_docx_path": str(run_dir / merged_docx_name),
            "cost_records": self.cost_tracker.to_dict()
        }