import time

from src.workflow.literature_pipeline import LiteraturePipeline
from src.workflow.outline_planner import OutlinePlanner
from src.workflow.outline_reviewer import OutlineReviewer
from src.workflow.consistency_checker import ConsistencyChecker

from src.workflow.introduction_writer import IntroductionWriter
from src.workflow.introduction_polisher import IntroductionPolisher

from src.workflow.related_work_writer import RelatedWorkWriter
from src.workflow.related_work_polisher import RelatedWorkPolisher

from src.workflow.methodology_writer import MethodologyWriter
from src.workflow.methodology_polisher import MethodologyPolisher

from src.workflow.experiment_writer import ExperimentWriter
from src.workflow.experiment_polisher import ExperimentPolisher

from src.workflow.conclusion_writer import ConclusionWriter
from src.workflow.conclusion_polisher import ConclusionPolisher

from src.utils.config_loader import ConfigLoader
from src.utils.file_saver import FileSaver
from src.utils.logger import get_logger
from src.utils.cost_tracker import CostTracker


class SectionPipeline:
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.logger = get_logger("SectionPipeline")
        self.cost_tracker = CostTracker()

        paths_config = self.config_loader.load_paths_config()
        sections_dir = paths_config["output"].get("sections_dir", "data/output/sections")
        self.file_saver = FileSaver(base_dir=sections_dir)

        self.literature_pipeline = LiteraturePipeline()
        self.outline_planner = OutlinePlanner()
        self.outline_reviewer = OutlineReviewer()
        self.consistency_checker = ConsistencyChecker()

        self.introduction_writer = IntroductionWriter()
        self.introduction_polisher = IntroductionPolisher()

        self.related_work_writer = RelatedWorkWriter()
        self.related_work_polisher = RelatedWorkPolisher()

        self.methodology_writer = MethodologyWriter()
        self.methodology_polisher = MethodologyPolisher()

        self.experiment_writer = ExperimentWriter()
        self.experiment_polisher = ExperimentPolisher()

        self.conclusion_writer = ConclusionWriter()
        self.conclusion_polisher = ConclusionPolisher()

    def run(self, topic: str, goal: str, materials: list[dict]) -> dict:
        total_start = time.perf_counter()
        self.logger.info(f"章节化流水线开始 | topic={topic} | goal={goal}")

        run_dir = self.file_saver.create_run_folder(topic)
        self.logger.info(f"章节输出目录创建完成 | run_dir={run_dir}")

        # 0. 文献整理
        step_start = time.perf_counter()
        print("\n===== 第0步：文献整理 =====\n")
        literature_result = self.literature_pipeline.run(topic=topic, materials=materials)
        literature_pack_text = literature_result["merged_summary_text"]

        self.file_saver.save_docx(
            run_dir,
            "00_literature_pack.docx",
            literature_pack_text,
            f"{topic} - 文献整理总文档"
        )

        elapsed = time.perf_counter() - step_start
        self.cost_tracker.records.update(literature_result.get("cost_records", {}))
        self.logger.info(f"第0步完成 | 文献整理 | elapsed={elapsed:.2f}s")

        # 1. 总纲生成
        step_start = time.perf_counter()
        print("\n===== 第1步：总纲生成 =====\n")
        outline_text = self.outline_planner.plan_outline_stream(
            topic=topic,
            goal=goal,
            literature_pack_text=literature_pack_text,
            organized_material=""
        )

        self.file_saver.save_docx(
            run_dir,
            "01_outline.docx",
            outline_text,
            f"{topic} - 论文总纲"
        )

        elapsed = time.perf_counter() - step_start
        self.cost_tracker.record(
            component="outline_planner",
            model=self.outline_planner.get_model_name(),
            input_text=f"{topic}\n{goal}\n{literature_pack_text}",
            output_text=outline_text,
            elapsed_seconds=elapsed
        )
        self.logger.info(f"第1步完成 | 总纲生成 | elapsed={elapsed:.2f}s")

        # 2. 总纲审查
        step_start = time.perf_counter()
        print("\n===== 第2步：总纲审查 =====\n")
        outline_review_text = self.outline_reviewer.review_outline_stream(outline_text)

        self.file_saver.save_docx(
            run_dir,
            "02_outline_review.docx",
            outline_review_text,
            f"{topic} - 总纲审查"
        )

        elapsed = time.perf_counter() - step_start
        self.cost_tracker.record(
            component="outline_reviewer",
            model=self.outline_reviewer.get_model_name(),
            input_text=outline_text,
            output_text=outline_review_text,
            elapsed_seconds=elapsed
        )
        self.logger.info(f"第2步完成 | 总纲审查 | elapsed={elapsed:.2f}s")

        # 3. Introduction 初稿
        step_start = time.perf_counter()
        print("\n===== 第3步：Introduction 写作 =====\n")
        introduction_raw = self.introduction_writer.write_introduction_stream(
            topic=topic,
            goal=goal,
            literature_pack_text=literature_pack_text,
            outline_text=outline_text,
            outline_review_text=outline_review_text
        )

        self.file_saver.save_docx(
            run_dir,
            "03_introduction_raw.docx",
            introduction_raw,
            f"{topic} - Introduction 初稿"
        )

        elapsed = time.perf_counter() - step_start
        self.cost_tracker.record(
            component="introduction_writer",
            model=self.introduction_writer.get_model_name(),
            input_text=f"{topic}\n{goal}\n{literature_pack_text}\n{outline_text}\n{outline_review_text}",
            output_text=introduction_raw,
            elapsed_seconds=elapsed
        )
        self.logger.info(f"第3步完成 | Introduction 写作 | elapsed={elapsed:.2f}s")

        # 4. Introduction 润色
        step_start = time.perf_counter()
        print("\n===== 第4步：Introduction 润色 =====\n")
        introduction_polished = self.introduction_polisher.polish_introduction_stream(
            topic=topic,
            goal=goal,
            introduction_text=introduction_raw,
            outline_review_text=outline_review_text
        )

        self.file_saver.save_docx(
            run_dir,
            "04_introduction_polished.docx",
            introduction_polished,
            f"{topic} - Introduction 润色稿"
        )

        elapsed = time.perf_counter() - step_start
        self.cost_tracker.record(
            component="introduction_polisher",
            model=self.introduction_polisher.get_model_name(),
            input_text=f"{topic}\n{goal}\n{introduction_raw}\n{outline_review_text}",
            output_text=introduction_polished,
            elapsed_seconds=elapsed
        )
        self.logger.info(f"第4步完成 | Introduction 润色 | elapsed={elapsed:.2f}s")

        # 5. Related Work 初稿
        step_start = time.perf_counter()
        print("\n===== 第5步：Related Work 写作 =====\n")
        related_work_raw = self.related_work_writer.write_related_work_stream(
            topic=topic,
            goal=goal,
            literature_pack_text=literature_pack_text,
            outline_text=outline_text,
            outline_review_text=outline_review_text,
            introduction_text=introduction_polished
        )

        self.file_saver.save_docx(
            run_dir,
            "05_related_work_raw.docx",
            related_work_raw,
            f"{topic} - Related Work 初稿"
        )

        elapsed = time.perf_counter() - step_start
        self.cost_tracker.record(
            component="related_work_writer",
            model=self.related_work_writer.get_model_name(),
            input_text=f"{topic}\n{goal}\n{literature_pack_text}\n{outline_text}\n{outline_review_text}\n{introduction_polished}",
            output_text=related_work_raw,
            elapsed_seconds=elapsed
        )
        self.logger.info(f"第5步完成 | Related Work 写作 | elapsed={elapsed:.2f}s")

        # 6. Related Work 润色
        step_start = time.perf_counter()
        print("\n===== 第6步：Related Work 润色 =====\n")
        related_work_polished = self.related_work_polisher.polish_related_work_stream(
            topic=topic,
            goal=goal,
            related_work_text=related_work_raw,
            literature_pack_text=literature_pack_text,
            outline_review_text=outline_review_text,
            introduction_text=introduction_polished
        )

        self.file_saver.save_docx(
            run_dir,
            "06_related_work_polished.docx",
            related_work_polished,
            f"{topic} - Related Work 润色稿"
        )

        elapsed = time.perf_counter() - step_start
        self.cost_tracker.record(
            component="related_work_polisher",
            model=self.related_work_polisher.get_model_name(),
            input_text=f"{topic}\n{goal}\n{related_work_raw}\n{literature_pack_text}\n{outline_review_text}\n{introduction_polished}",
            output_text=related_work_polished,
            elapsed_seconds=elapsed
        )
        self.logger.info(f"第6步完成 | Related Work 润色 | elapsed={elapsed:.2f}s")

        # 7. Methodology 初稿
        step_start = time.perf_counter()
        print("\n===== 第7步：Methodology 写作 =====\n")
        methodology_raw = self.methodology_writer.write_methodology_stream(
            topic=topic,
            goal=goal,
            literature_pack_text=literature_pack_text,
            outline_text=outline_text,
            outline_review_text=outline_review_text,
            introduction_text=introduction_polished,
            related_work_text=related_work_polished
        )

        self.file_saver.save_docx(
            run_dir,
            "07_methodology_raw.docx",
            methodology_raw,
            f"{topic} - Methodology 初稿"
        )

        elapsed = time.perf_counter() - step_start
        self.cost_tracker.record(
            component="methodology_writer",
            model=self.methodology_writer.get_model_name(),
            input_text=f"{topic}\n{goal}\n{literature_pack_text}\n{outline_text}\n{outline_review_text}\n{introduction_polished}\n{related_work_polished}",
            output_text=methodology_raw,
            elapsed_seconds=elapsed
        )
        self.logger.info(f"第7步完成 | Methodology 写作 | elapsed={elapsed:.2f}s")

        # 8. Methodology 润色
        step_start = time.perf_counter()
        print("\n===== 第8步：Methodology 润色 =====\n")
        methodology_polished = self.methodology_polisher.polish_methodology_stream(
            topic=topic,
            goal=goal,
            methodology_text=methodology_raw,
            literature_pack_text=literature_pack_text,
            outline_review_text=outline_review_text,
            introduction_text=introduction_polished,
            related_work_text=related_work_polished
        )

        self.file_saver.save_docx(
            run_dir,
            "08_methodology_polished.docx",
            methodology_polished,
            f"{topic} - Methodology 润色稿"
        )

        elapsed = time.perf_counter() - step_start
        self.cost_tracker.record(
            component="methodology_polisher",
            model=self.methodology_polisher.get_model_name(),
            input_text=f"{topic}\n{goal}\n{methodology_raw}\n{literature_pack_text}\n{outline_review_text}\n{introduction_polished}\n{related_work_polished}",
            output_text=methodology_polished,
            elapsed_seconds=elapsed
        )
        self.logger.info(f"第8步完成 | Methodology 润色 | elapsed={elapsed:.2f}s")

        # 9. Experiment 初稿
        step_start = time.perf_counter()
        print("\n===== 第9步：Experiment 写作 =====\n")
        experiment_raw = self.experiment_writer.write_experiment_stream(
            topic=topic,
            goal=goal,
            literature_pack_text=literature_pack_text,
            outline_text=outline_text,
            outline_review_text=outline_review_text,
            introduction_text=introduction_polished,
            related_work_text=related_work_polished,
            methodology_text=methodology_polished
        )

        self.file_saver.save_docx(
            run_dir,
            "09_experiment_raw.docx",
            experiment_raw,
            f"{topic} - Experiment 初稿"
        )

        elapsed = time.perf_counter() - step_start
        self.cost_tracker.record(
            component="experiment_writer",
            model=self.experiment_writer.get_model_name(),
            input_text=f"{topic}\n{goal}\n{literature_pack_text}\n{outline_text}\n{outline_review_text}\n{introduction_polished}\n{related_work_polished}\n{methodology_polished}",
            output_text=experiment_raw,
            elapsed_seconds=elapsed
        )
        self.logger.info(f"第9步完成 | Experiment 写作 | elapsed={elapsed:.2f}s")

        # 10. Experiment 润色
        step_start = time.perf_counter()
        print("\n===== 第10步：Experiment 润色 =====\n")
        experiment_polished = self.experiment_polisher.polish_experiment_stream(
            topic=topic,
            goal=goal,
            experiment_text=experiment_raw,
            literature_pack_text=literature_pack_text,
            outline_review_text=outline_review_text,
            introduction_text=introduction_polished,
            related_work_text=related_work_polished,
            methodology_text=methodology_polished
        )

        self.file_saver.save_docx(
            run_dir,
            "10_experiment_polished.docx",
            experiment_polished,
            f"{topic} - Experiment 润色稿"
        )

        elapsed = time.perf_counter() - step_start
        self.cost_tracker.record(
            component="experiment_polisher",
            model=self.experiment_polisher.get_model_name(),
            input_text=f"{topic}\n{goal}\n{experiment_raw}\n{literature_pack_text}\n{outline_review_text}\n{introduction_polished}\n{related_work_polished}\n{methodology_polished}",
            output_text=experiment_polished,
            elapsed_seconds=elapsed
        )
        self.logger.info(f"第10步完成 | Experiment 润色 | elapsed={elapsed:.2f}s")

        # 11. Conclusion 初稿
        step_start = time.perf_counter()
        print("\n===== 第11步：Conclusion 写作 =====\n")
        conclusion_raw = self.conclusion_writer.write_conclusion_stream(
            topic=topic,
            goal=goal,
            literature_pack_text=literature_pack_text,
            outline_text=outline_text,
            outline_review_text=outline_review_text,
            introduction_text=introduction_polished,
            related_work_text=related_work_polished,
            methodology_text=methodology_polished,
            experiment_text=experiment_polished
        )

        self.file_saver.save_docx(
            run_dir,
            "11_conclusion_raw.docx",
            conclusion_raw,
            f"{topic} - Conclusion 初稿"
        )

        elapsed = time.perf_counter() - step_start
        self.cost_tracker.record(
            component="conclusion_writer",
            model=self.conclusion_writer.get_model_name(),
            input_text=f"{topic}\n{goal}\n{literature_pack_text}\n{outline_text}\n{outline_review_text}\n{introduction_polished}\n{related_work_polished}\n{methodology_polished}\n{experiment_polished}",
            output_text=conclusion_raw,
            elapsed_seconds=elapsed
        )
        self.logger.info(f"第11步完成 | Conclusion 写作 | elapsed={elapsed:.2f}s")

        # 12. Conclusion 润色
        step_start = time.perf_counter()
        print("\n===== 第12步：Conclusion 润色 =====\n")
        conclusion_polished = self.conclusion_polisher.polish_conclusion_stream(
            topic=topic,
            goal=goal,
            conclusion_text=conclusion_raw,
            literature_pack_text=literature_pack_text,
            outline_review_text=outline_review_text,
            introduction_text=introduction_polished,
            related_work_text=related_work_polished,
            methodology_text=methodology_polished,
            experiment_text=experiment_polished
        )

        self.file_saver.save_docx(
            run_dir,
            "12_conclusion_polished.docx",
            conclusion_polished,
            f"{topic} - Conclusion 润色稿"
        )

        elapsed = time.perf_counter() - step_start
        self.cost_tracker.record(
            component="conclusion_polisher",
            model=self.conclusion_polisher.get_model_name(),
            input_text=f"{topic}\n{goal}\n{conclusion_raw}\n{literature_pack_text}\n{outline_review_text}\n{introduction_polished}\n{related_work_polished}\n{methodology_polished}\n{experiment_polished}",
            output_text=conclusion_polished,
            elapsed_seconds=elapsed
        )
        self.logger.info(f"第12步完成 | Conclusion 润色 | elapsed={elapsed:.2f}s")

        # 13. 全文一致性检查
        step_start = time.perf_counter()
        print("\n===== 第13步：全文一致性检查 =====\n")
        consistency_report = self.consistency_checker.check_sections_stream(
            topic=topic,
            goal=goal,
            outline_text=outline_text,
            outline_review_text=outline_review_text,
            introduction_text=introduction_polished,
            related_work_text=related_work_polished,
            methodology_text=methodology_polished,
            experiment_text=experiment_polished,
            conclusion_text=conclusion_polished
        )

        self.file_saver.save_docx(
            run_dir,
            "13_consistency_report.docx",
            consistency_report,
            f"{topic} - 全文一致性检查"
        )

        elapsed = time.perf_counter() - step_start
        self.cost_tracker.record(
            component="consistency_checker",
            model=self.consistency_checker.get_model_name(),
            input_text=f"{topic}\n{goal}\n{outline_text}\n{outline_review_text}\n{introduction_polished}\n{related_work_polished}\n{methodology_polished}\n{experiment_polished}\n{conclusion_polished}",
            output_text=consistency_report,
            elapsed_seconds=elapsed
        )
        self.logger.info(f"第13步完成 | 全文一致性检查 | elapsed={elapsed:.2f}s")

        cost_report_path = run_dir / "section_cost_report.json"
        self.cost_tracker.save_json(str(cost_report_path))
        self.logger.info(f"章节化写作成本报告已保存 | path={cost_report_path}")

        total_elapsed = time.perf_counter() - total_start
        self.logger.info(
            f"章节化流水线完成 | topic={topic} | elapsed={total_elapsed:.2f}s | run_dir={run_dir}"
        )

        return {
            "run_dir": str(run_dir),
            "topic": topic,
            "literature_pack_text": literature_pack_text,
            "outline_text": outline_text,
            "outline_review_text": outline_review_text,
            "introduction_raw": introduction_raw,
            "introduction_polished": introduction_polished,
            "related_work_raw": related_work_raw,
            "related_work_polished": related_work_polished,
            "methodology_raw": methodology_raw,
            "methodology_polished": methodology_polished,
            "experiment_raw": experiment_raw,
            "experiment_polished": experiment_polished,
            "conclusion_raw": conclusion_raw,
            "conclusion_polished": conclusion_polished,
            "consistency_report": consistency_report,
            "cost_report_path": str(cost_report_path),
            "cost_records": self.cost_tracker.to_dict()
        }