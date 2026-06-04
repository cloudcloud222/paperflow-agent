import time
from src.workflow.planner import TaskPlanner
from src.workflow.organizer import MaterialOrganizer
from src.workflow.writer import DraftWriter
from src.workflow.reviewer import DraftReviewer
from src.workflow.reviser import DraftReviser
from src.workflow.literature_pipeline import LiteraturePipeline
from src.utils.file_saver import FileSaver
from src.utils.config_loader import ConfigLoader
from src.utils.logger import get_logger
from src.utils.cost_tracker import CostTracker
from src.formatting.ruledoc_adapter import RuleDocAdapter


class PaperWorkflow:
    def __init__(self):
        self.planner = TaskPlanner()
        self.organizer = MaterialOrganizer()
        self.writer = DraftWriter()
        self.reviewer = DraftReviewer()
        self.reviser = DraftReviser()
        self.literature_pipeline = LiteraturePipeline()
        self.config_loader = ConfigLoader()
        self.logger = get_logger("PaperWorkflow")
        self.cost_tracker = CostTracker()

        paths_config = self.config_loader.load_paths_config()
        runtime_config = self.config_loader.load_runtime_config()

        paper_output_dir = paths_config["output"]["paper_dir"]
        self.file_saver = FileSaver(base_dir=paper_output_dir)

        self.enable_ruledoc = runtime_config["ruledoc"]["enabled"]
        ruledoc_rule_name = runtime_config["ruledoc"]["rule_name"]
        self.ruledoc_adapter = RuleDocAdapter(rule_name=ruledoc_rule_name)

        self.stream_config = runtime_config["stream"]
        self.pipeline_config = runtime_config["pipeline"]

    def _call_planner(self, plan_input: str) -> str:
        if self.stream_config.get("planner", False):
            return self.planner.plan_stream(plan_input)
        return self.planner.plan(plan_input)

    def _call_organizer(self, organizer_input: str) -> str:
        if self.stream_config.get("organizer", False):
            return self.organizer.organize_stream(organizer_input)
        return self.organizer.organize(organizer_input)

    def _call_writer(self, organize_result: str) -> str:
        if self.stream_config.get("writer", False):
            return self.writer.write_draft_stream(organize_result)
        return self.writer.write_draft(organize_result)

    def _call_reviewer(self, draft_result: str) -> str:
        if self.stream_config.get("reviewer", False):
            return self.reviewer.review_stream(draft_result)
        return self.reviewer.review(draft_result)

    def _call_reviser(self, draft_result: str, review_result: str) -> str:
        if self.stream_config.get("reviser", False):
            return self.reviser.revise_stream(draft_result, review_result)
        return self.reviser.revise(draft_result, review_result)

    def run(self, user_goal: str, topic: str, materials: list[dict] | None = None) -> dict:
        total_start = time.perf_counter()
        self.logger.info(f"主论文流程开始 | topic={topic} | goal={user_goal}")

        run_dir = self.file_saver.create_run_folder(topic)
        self.logger.info(f"主流程输出目录创建完成 | run_dir={run_dir}")

        literature_pack_text = ""
        literature_result = {
            "run_dir": "",
            "merged_docx_path": "",
            "cost_records": {}
        }

        if self.pipeline_config.get("enable_literature_pipeline", True):
            step_start = time.perf_counter()
            print("\n===== 第0步：文献摘要与整理 literature_pipeline =====\n")
            self.logger.info("第0步开始 | literature_pipeline")

            literature_result = self.literature_pipeline.run(topic=topic, materials=materials)
            literature_pack_text = literature_result["merged_summary_text"]

            self.file_saver.save_docx(
                run_dir,
                "00_literature_pack.docx",
                literature_pack_text,
                f"{topic} - 文献整理总文档"
            )

            # 合并 literature pipeline 的成本记录
            self.cost_tracker.records.update(literature_result.get("cost_records", {}))

            elapsed = time.perf_counter() - step_start
            self.logger.info(
                f"第0步完成 | literature_pipeline | elapsed={elapsed:.2f}s | output={run_dir / '00_literature_pack.docx'}"
            )
        else:
            print("\n===== 第0步：文献摘要与整理 literature_pipeline 已跳过 =====\n")
            self.logger.info("第0步跳过 | literature_pipeline")

        step_start = time.perf_counter()
        print("\n===== 第1步：任务规划 planner =====\n")
        self.logger.info("第1步开始 | planner")

        plan_input = f"""论文主题：
{topic}

当前目标：
{user_goal}
"""
        if literature_pack_text:
            plan_input += f"""

文献整理结果：
{literature_pack_text}
"""

        plan_result = self._call_planner(plan_input)
        self.file_saver.save_docx(
            run_dir,
            "01_plan.docx",
            plan_result,
            f"{topic} - 任务规划"
        )

        elapsed = time.perf_counter() - step_start
        self.cost_tracker.record(
            component="planner",
            model=self.planner.get_model_name(),
            input_text=plan_input,
            output_text=plan_result,
            elapsed_seconds=elapsed
        )
        self.logger.info(
            f"第1步完成 | planner | elapsed={elapsed:.2f}s | output={run_dir / '01_plan.docx'}"
        )

        step_start = time.perf_counter()
        print("\n===== 第2步：资料整理 organizer =====\n")
        self.logger.info("第2步开始 | organizer")

        organizer_input = f"""【论文主题】
{topic}

【当前目标】
{user_goal}

【任务规划结果】
{plan_result}
"""

        if literature_pack_text:
            organizer_input += f"""

【文献整理总文档】
{literature_pack_text}
"""

        organize_result = self._call_organizer(organizer_input)
        self.file_saver.save_docx(
            run_dir,
            "02_organized_material.docx",
            organize_result,
            f"{topic} - 资料整理"
        )

        elapsed = time.perf_counter() - step_start
        self.cost_tracker.record(
            component="organizer",
            model=self.organizer.get_model_name(),
            input_text=organizer_input,
            output_text=organize_result,
            elapsed_seconds=elapsed
        )
        self.logger.info(
            f"第2步完成 | organizer | elapsed={elapsed:.2f}s | output={run_dir / '02_organized_material.docx'}"
        )

        step_start = time.perf_counter()
        print("\n===== 第3步：初稿写作 writer =====\n")
        self.logger.info("第3步开始 | writer")

        draft_result = self._call_writer(organize_result)
        self.file_saver.save_docx(
            run_dir,
            "03_draft.docx",
            draft_result,
            f"{topic} - 论文初稿"
        )

        if self.enable_ruledoc:
            self.ruledoc_adapter.format_docx(
                input_path=str(run_dir / "03_draft.docx"),
                output_path=str(run_dir / "03_draft_ruledoc.docx")
            )

        elapsed = time.perf_counter() - step_start
        self.cost_tracker.record(
            component="writer",
            model=self.writer.get_model_name(),
            input_text=organize_result,
            output_text=draft_result,
            elapsed_seconds=elapsed
        )
        self.logger.info(
            f"第3步完成 | writer | elapsed={elapsed:.2f}s | output={run_dir / '03_draft.docx'}"
        )

        review_result = ""
        if self.pipeline_config.get("enable_reviewer", True):
            step_start = time.perf_counter()
            print("\n===== 第4步：初稿审阅 reviewer =====\n")
            self.logger.info("第4步开始 | reviewer")

            review_result = self._call_reviewer(draft_result)
            self.file_saver.save_docx(
                run_dir,
                "04_review.docx",
                review_result,
                f"{topic} - 初稿审阅"
            )

            if self.enable_ruledoc:
                self.ruledoc_adapter.format_docx(
                    input_path=str(run_dir / "04_review.docx"),
                    output_path=str(run_dir / "04_review_ruledoc.docx")
                )

            elapsed = time.perf_counter() - step_start
            self.cost_tracker.record(
                component="reviewer",
                model=self.reviewer.get_model_name(),
                input_text=draft_result,
                output_text=review_result,
                elapsed_seconds=elapsed
            )
            self.logger.info(
                f"第4步完成 | reviewer | elapsed={elapsed:.2f}s | output={run_dir / '04_review.docx'}"
            )
        else:
            print("\n===== 第4步：初稿审阅 reviewer 已跳过 =====\n")
            self.logger.info("第4步跳过 | reviewer")

        revised_draft_result = ""
        if self.pipeline_config.get("enable_reviser", True):
            step_start = time.perf_counter()
            print("\n===== 第5步：修订稿生成 reviser =====\n")
            self.logger.info("第5步开始 | reviser")

            reviser_input_review = review_result if review_result else "未提供审阅意见，请基于初稿进行自我优化修订。"
            revised_draft_result = self._call_reviser(draft_result, reviser_input_review)

            self.file_saver.save_docx(
                run_dir,
                "05_revised_draft.docx",
                revised_draft_result,
                f"{topic} - 修订稿"
            )

            if self.enable_ruledoc:
                self.ruledoc_adapter.format_docx(
                    input_path=str(run_dir / "05_revised_draft.docx"),
                    output_path=str(run_dir / "05_revised_draft_ruledoc.docx")
                )

            elapsed = time.perf_counter() - step_start
            reviser_input_text = f"【原始初稿】\n{draft_result}\n\n【审阅意见】\n{reviser_input_review}"
            self.cost_tracker.record(
                component="reviser",
                model=self.reviser.get_model_name(),
                input_text=reviser_input_text,
                output_text=revised_draft_result,
                elapsed_seconds=elapsed
            )
            self.logger.info(
                f"第5步完成 | reviser | elapsed={elapsed:.2f}s | output={run_dir / '05_revised_draft.docx'}"
            )
        else:
            print("\n===== 第5步：修订稿生成 reviser 已跳过 =====\n")
            self.logger.info("第5步跳过 | reviser")

        cost_report_path = run_dir / "cost_report.json"
        self.cost_tracker.save_json(str(cost_report_path))
        self.logger.info(f"成本统计报告已保存 | path={cost_report_path}")

        total_elapsed = time.perf_counter() - total_start
        self.logger.info(
            f"主论文流程完成 | topic={topic} | elapsed={total_elapsed:.2f}s | run_dir={run_dir}"
        )

        return {
            "run_dir": str(run_dir),
            "topic": topic,
            "literature_run_dir": literature_result["run_dir"],
            "literature_pack_path": literature_result["merged_docx_path"],
            "literature_pack_text": literature_pack_text,
            "plan": plan_result,
            "organized_material": organize_result,
            "draft": draft_result,
            "review": review_result,
            "revised_draft": revised_draft_result,
            "cost_report_path": str(cost_report_path),
            "cost_records": self.cost_tracker.to_dict()
        }