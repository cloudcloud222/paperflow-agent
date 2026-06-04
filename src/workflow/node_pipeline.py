import json
import time
from pathlib import Path
from datetime import datetime

from src.input_loader.file_reader import FileReader
from src.workflow.literature_pipeline import LiteraturePipeline
from src.workflow.outline_schema_planner import OutlineSchemaPlanner
from src.workflow.node_card_builder import NodeCardBuilder
from src.workflow.node_context_builder import NodeContextBuilder
from src.workflow.node_scheduler import NodeScheduler
from src.workflow.node_reference_selector import NodeReferenceSelector
from src.workflow.node_writer import NodeWriter
from src.workflow.node_polisher import NodePolisher
from src.workflow.node_consistency_checker import NodeConsistencyChecker
from src.workflow.node_reviser import NodeReviser
from src.workflow.node_assembler import NodeAssembler

from src.utils.config_loader import ConfigLoader
from src.utils.logger import get_logger
from src.utils.cost_tracker import CostTracker


class NodePipeline:
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.logger = get_logger("NodePipeline")
        self.cost_tracker = CostTracker()
        self.file_reader = FileReader()

        paths_config = self.config_loader.load_paths_config()
        self.paths_config = paths_config
        output_config = paths_config["output"]

        self.node_pipeline_dir = Path(output_config["node_pipeline_dir"])
        self.literature_dir = Path(output_config.get("literature_dir", "data/output/literature_summaries"))
        self.outline_schema_dir = Path(output_config.get("outline_schema_dir", "data/output/outline_schemas"))
        self.outline_review_dir = Path(output_config.get("outline_review_dir", "data/output/outlines"))

        self.node_pipeline_dir.mkdir(parents=True, exist_ok=True)
        self.literature_dir.mkdir(parents=True, exist_ok=True)
        self.outline_schema_dir.mkdir(parents=True, exist_ok=True)
        self.outline_review_dir.mkdir(parents=True, exist_ok=True)

        self.literature_pipeline = LiteraturePipeline()
        self.outline_schema_planner = OutlineSchemaPlanner()
        self.node_card_builder = NodeCardBuilder()
        self.node_context_builder = NodeContextBuilder()
        self.node_scheduler = NodeScheduler()
        self.node_reference_selector = NodeReferenceSelector()
        self.node_writer = NodeWriter()
        self.node_polisher = NodePolisher()
        self.node_consistency_checker = NodeConsistencyChecker()
        self.node_reviser = NodeReviser()
        self.node_assembler = NodeAssembler()

    def _sanitize_name(self, name: str) -> str:
        invalid_chars = '<>:"/\\|?*'
        sanitized = name
        for ch in invalid_chars:
            sanitized = sanitized.replace(ch, "_")
        sanitized = sanitized.strip()
        return sanitized[:50] if len(sanitized) > 50 else sanitized

    def _create_run_folder(self, topic: str) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = self._sanitize_name(topic) if topic else "untitled"
        run_dir = self.node_pipeline_dir / f"{timestamp}_{safe_topic}"
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def _find_latest_file(
        self,
        base_dir: str | Path,
        filename: str | None = None,
        suffix: str | None = None,
        topic: str = ""
    ) -> Path | None:
        base_path = Path(base_dir)
        if not base_path.exists():
            return None

        matched_files = list(base_path.rglob("*"))

        if filename:
            matched_files = [p for p in matched_files if p.is_file() and p.name == filename]
        elif suffix:
            matched_files = [p for p in matched_files if p.is_file() and p.suffix.lower() == suffix.lower()]
        else:
            matched_files = [p for p in matched_files if p.is_file()]

        if topic:
            topic_matched = [p for p in matched_files if topic in str(p)]
            if topic_matched:
                topic_matched.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                return topic_matched[0]

        if not matched_files:
            return None

        matched_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return matched_files[0]

    def _load_literature_summaries(self, topic: str) -> list[dict]:
        summaries = []
        base_dir = self.literature_dir
        if not base_dir.exists():
            return summaries

        matched_dirs = [p for p in base_dir.iterdir() if p.is_dir() and topic in p.name]
        matched_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        candidate_dirs = matched_dirs if matched_dirs else sorted(
            [p for p in base_dir.iterdir() if p.is_dir()],
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        for run_dir in candidate_dirs[:3]:
            summary_files = sorted(run_dir.glob("*_summary.docx"))
            if not summary_files:
                continue

            current_summaries = []
            for f in summary_files:
                try:
                    content = self.file_reader.read_input(str(f))
                    current_summaries.append({
                        "source_filename": f.name,
                        "summary_text": content
                    })
                except Exception:
                    pass

            if current_summaries:
                summaries = current_summaries
                break

        return summaries

    def _prepare_literature_resources(
        self,
        topic: str,
        materials: list[dict]
    ) -> tuple[str, str, list[dict]]:
        literature_pack_path = self._find_latest_file(
            self.literature_dir,
            filename="literature_review_pack.docx",
            topic=topic
        )

        if literature_pack_path is None:
            self.logger.info("未找到已有文献整理总文档，开始自动生成")
            literature_result = self.literature_pipeline.run(topic=topic, materials=materials)
            literature_pack_text = literature_result["merged_summary_text"]
            literature_pack_path = Path(literature_result["merged_docx_path"])

            literature_summaries = []
            for item in literature_result.get("summaries", []):
                literature_summaries.append({
                    "source_filename": item.get("filename", ""),
                    "summary_text": item.get("summary", "")
                })
        else:
            self.logger.info(f"复用已有文献整理总文档 | path={literature_pack_path}")
            literature_pack_text = self.file_reader.read_input(str(literature_pack_path))
            literature_summaries = self._load_literature_summaries(topic)

        if not literature_summaries:
            literature_summaries = [{
                "source_filename": Path(literature_pack_path).name,
                "summary_text": literature_pack_text
            }]

        return literature_pack_text, str(literature_pack_path), literature_summaries

    def _prepare_schema(self, topic: str, goal: str, literature_pack_text: str) -> tuple[dict, str]:
        schema_path = self._find_latest_file(
            self.outline_schema_dir,
            suffix=".json",
            topic=topic
        )

        schema = None
        if schema_path is not None:
            try:
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                self.logger.info(f"复用已有结构化总纲 | path={schema_path}")
                return schema, str(schema_path)
            except Exception:
                self.logger.warning(f"已有结构化总纲解析失败，重新生成 | path={schema_path}")

        self.logger.info("未找到可用结构化总纲，开始自动生成")
        schema = self.outline_schema_planner.plan_schema(
            topic=topic,
            goal=goal,
            literature_pack_text=literature_pack_text,
            organized_material=""
        )

        output_dir = self.outline_schema_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_topic = self._sanitize_name(topic)
        schema_path = output_dir / f"{safe_topic}_outline_schema.json"
        schema_path.write_text(
            json.dumps(schema, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        self.logger.info(f"结构化总纲已保存 | path={schema_path}")

        return schema, str(schema_path)

    def _prepare_node_cards(self, schema: dict) -> tuple[list[dict], str]:
        build_result = self.node_card_builder.build_from_schema(schema)
        cards_path = build_result["cards_json_path"]
        cards = build_result["cards"]
        self.logger.info(f"节点卡片已构建 | count={len(cards)} | path={cards_path}")
        return cards, cards_path

    def _load_outline_review_text(self, topic: str) -> tuple[str, str]:
        outline_review_path = self._find_latest_file(
            self.outline_review_dir,
            filename="02_outline_review.docx",
            topic=topic
        )

        if outline_review_path is None:
            self.logger.info("未找到总纲审查文件，本次以空审查意见继续")
            return "", ""

        outline_review_text = self.file_reader.read_input(str(outline_review_path))
        self.logger.info(f"复用总纲审查 | path={outline_review_path}")
        return outline_review_text, str(outline_review_path)

    def _build_reference_context_text(self, selection_result: dict) -> str:
        if not selection_result:
            return ""

        lines = []
        summary = selection_result.get("selection_summary", "")
        writing_hint = selection_result.get("writing_hint", "")
        selected_refs = selection_result.get("selected_references", [])

        if summary:
            lines.append("【参考文献选择说明】")
            lines.append(summary)

        if selected_refs:
            lines.append("")
            lines.append("【当前节点推荐参考文献】")
            for idx, ref in enumerate(selected_refs, start=1):
                source_filename = ref.get("source_filename", "")
                relevance_score = ref.get("relevance_score", 0.0)
                relevance_reason = ref.get("relevance_reason", "")
                suggested_use = ref.get("suggested_use", "")
                key_evidence = ref.get("key_evidence", [])

                lines.append(f"{idx}. 来源：{source_filename}")
                lines.append(f"   相关度：{relevance_score}")
                if relevance_reason:
                    lines.append(f"   相关原因：{relevance_reason}")
                if suggested_use:
                    lines.append(f"   建议用途：{suggested_use}")
                if key_evidence:
                    lines.append("   关键证据点：")
                    for evidence in key_evidence:
                        lines.append(f"   - {evidence}")

        if writing_hint:
            lines.append("")
            lines.append("【写作提示】")
            lines.append(writing_hint)

        return "\n".join(lines).strip()

    def _build_card_index(self, cards: list[dict]) -> dict[str, dict]:
        return {card.get("id", ""): card for card in cards if card.get("id")}

    def _get_parent_card(self, card: dict, card_index: dict[str, dict]) -> dict | None:
        parent_id = card.get("parent_id")
        if not parent_id:
            return None
        return card_index.get(parent_id)

    def _get_sibling_cards(self, card: dict, all_cards: list[dict]) -> list[dict]:
        parent_id = card.get("parent_id")
        node_id = card.get("id")
        return [
            c for c in all_cards
            if c.get("parent_id") == parent_id and c.get("id") != node_id
        ]

    def _get_child_cards(self, card: dict, all_cards: list[dict]) -> list[dict]:
        node_id = card.get("id")
        return [
            c for c in all_cards
            if c.get("parent_id") == node_id
        ]

    def _build_text_map_for_cards(self, cards: list[dict], polished_map: dict[str, str]) -> dict[str, str]:
        result = {}
        for card in cards:
            node_id = card.get("id", "")
            if node_id:
                result[node_id] = polished_map.get(node_id, "")
        return result

    def _should_trigger_revision(self, consistency_result: dict | None) -> bool:
        if not consistency_result or not isinstance(consistency_result, dict):
            return False

        if consistency_result.get("revision_required") is True:
            return True

        if consistency_result.get("pass_for_assembly") is False:
            return True

        if consistency_result.get("revision_priority") == "high":
            return True

        fail_keys = [
            "goal_alignment",
            "parent_alignment",
            "sibling_boundary",
            "child_hierarchy",
            "terminology_consistency"
        ]
        for key in fail_keys:
            part = consistency_result.get(key, {})
            if isinstance(part, dict) and part.get("status") == "fail":
                return True

        return False

    def run(
        self,
        topic: str,
        goal: str,
        materials: list[dict],
        strategy: str = "hybrid",
        leaf_only: bool = False,
        write_internal_nodes: bool | None = None,
        enable_consistency_revision: bool = True,
        max_nodes: int | None = None,
        enable_polish: bool = True,
        enable_review: bool = True,
        assemble: bool = True
    ) -> dict:
        if write_internal_nodes is False:
            leaf_only = True

        total_start = time.perf_counter()
        self.logger.info(
            f"NodePipeline 开始 | topic={topic} | goal={goal} | strategy={strategy} | "
            f"leaf_only={leaf_only} | enable_consistency_revision={enable_consistency_revision} | "
            f"max_nodes={max_nodes} | enable_polish={enable_polish} | "
            f"enable_review={enable_review} | assemble={assemble}"
        )

        run_dir = self._create_run_folder(topic)
        nodes_dir = run_dir / "nodes"
        nodes_dir.mkdir(parents=True, exist_ok=True)

        literature_pack_text, literature_pack_path, literature_summaries = self._prepare_literature_resources(
            topic, materials
        )
        schema, schema_path = self._prepare_schema(topic, goal, literature_pack_text)
        cards, cards_path = self._prepare_node_cards(schema)
        outline_review_text, outline_review_path = self._load_outline_review_text(topic)

        schema_used_path = run_dir / "outline_schema_used.json"
        schema_used_path.write_text(
            json.dumps(schema, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        cards_used_path = run_dir / "node_cards_used.json"
        cards_used_path.write_text(
            json.dumps(cards, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        literature_summaries_used_path = run_dir / "literature_summaries_used.json"
        literature_summaries_used_path.write_text(
            json.dumps(literature_summaries, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        scheduled_cards = self.node_scheduler.schedule(
            cards=cards,
            strategy=strategy,
            leaf_only=leaf_only
        )

        scheduled_cards_path = run_dir / "scheduled_cards_used.json"
        scheduled_cards_path.write_text(
            json.dumps(scheduled_cards, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        if max_nodes is not None and max_nodes > 0:
            original_count = len(scheduled_cards)
            scheduled_cards = scheduled_cards[:max_nodes]
            self.logger.info(
                f"节点数量限制已启用 | max_nodes={max_nodes} | original_count={original_count} | "
                f"scheduled_count={len(scheduled_cards)}"
            )

        self.logger.info(
            f"节点调度完成 | strategy={strategy} | leaf_only={leaf_only} | scheduled_count={len(scheduled_cards)}"
        )

        card_index = self._build_card_index(cards)

        node_raw_map = {}
        node_polished_map = {}
        node_reference_map = {}
        node_consistency_map = {}

        for idx, card in enumerate(scheduled_cards, start=1):
            display_title = card.get("display_title", "")
            node_id = card.get("id", f"node_{idx}")
            self.logger.info(f"开始处理节点 | index={idx} | id={node_id} | title={display_title}")

            # 1. 基础上下文
            context_package = self.node_context_builder.build_context_package(
                topic=topic,
                goal=goal,
                node_card=card,
                all_cards=cards,
                polished_map=node_polished_map
            )
            base_context_text = context_package["context_text"]

            base_context_output_path = nodes_dir / f"{idx:03d}_{self._sanitize_name(node_id)}_base_context.txt"
            base_context_output_path.write_text(base_context_text, encoding="utf-8")

            # 2. 节点参考文献选择
            step_start = time.perf_counter()
            print(f"\n===== 节点参考文献选择：{display_title} =====\n")
            reference_selection = self.node_reference_selector.select_references(
                topic=topic,
                goal=goal,
                node_card=card,
                literature_summaries=literature_summaries,
                outline_review_text=outline_review_text,
                previous_context_text=base_context_text
            )
            elapsed = time.perf_counter() - step_start

            node_reference_map[node_id] = reference_selection

            reference_output_path = nodes_dir / f"{idx:03d}_{self._sanitize_name(node_id)}_references.json"
            reference_output_path.write_text(
                json.dumps(reference_selection, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

            self.cost_tracker.record(
                component=f"node_reference_selector:{node_id}",
                model=self.node_reference_selector.get_model_name(),
                input_text=json.dumps(card, ensure_ascii=False) + json.dumps(literature_summaries, ensure_ascii=False) + outline_review_text + base_context_text,
                output_text=json.dumps(reference_selection, ensure_ascii=False),
                elapsed_seconds=elapsed
            )

            # 3. 组合最终上下文
            reference_context_text = self._build_reference_context_text(reference_selection)
            final_context_parts = [base_context_text]
            if reference_context_text:
                final_context_parts.append(reference_context_text)
            final_context_text = "\n\n".join([p for p in final_context_parts if p.strip()]).strip()

            context_output_path = nodes_dir / f"{idx:03d}_{self._sanitize_name(node_id)}_context.txt"
            context_output_path.write_text(final_context_text, encoding="utf-8")

            # 4. 节点初稿
            step_start = time.perf_counter()
            print(f"\n===== 节点写作：{display_title} =====\n")
            node_raw_text = self.node_writer.write_node_stream(
                topic=topic,
                goal=goal,
                node_card=card,
                literature_pack_text=literature_pack_text,
                outline_review_text=outline_review_text,
                previous_context_text=final_context_text
            )
            elapsed = time.perf_counter() - step_start

            node_raw_map[node_id] = node_raw_text
            raw_output_path = nodes_dir / f"{idx:03d}_{self._sanitize_name(node_id)}_raw.txt"
            raw_output_path.write_text(node_raw_text, encoding="utf-8")

            self.cost_tracker.record(
                component=f"node_writer:{node_id}",
                model=self.node_writer.get_model_name(),
                input_text=json.dumps(card, ensure_ascii=False) + literature_pack_text + outline_review_text + final_context_text,
                output_text=node_raw_text,
                elapsed_seconds=elapsed
            )

            # 5. 节点润色（可选）
            if enable_polish:
                step_start = time.perf_counter()
                print(f"\n===== 节点润色：{display_title} =====\n")
                node_polished_text = self.node_polisher.polish_node_stream(
                    topic=topic,
                    goal=goal,
                    node_card=card,
                    node_text=node_raw_text,
                    literature_pack_text=literature_pack_text,
                    outline_review_text=outline_review_text,
                    previous_context_text=final_context_text
                )
                elapsed = time.perf_counter() - step_start

                self.cost_tracker.record(
                    component=f"node_polisher:{node_id}",
                    model=self.node_polisher.get_model_name(),
                    input_text=json.dumps(card, ensure_ascii=False) + node_raw_text + literature_pack_text + outline_review_text + final_context_text,
                    output_text=node_polished_text,
                    elapsed_seconds=elapsed
                )
            else:
                self.logger.info(f"跳过节点润色 | id={node_id} | title={display_title}")
                node_polished_text = node_raw_text

            polished_before_revision_path = nodes_dir / f"{idx:03d}_{self._sanitize_name(node_id)}_polished_before_revision.txt"
            polished_before_revision_path.write_text(node_polished_text, encoding="utf-8")

            # 6. 节点局部一致性检查（可选）
            parent_card = self._get_parent_card(card, card_index)
            parent_text = ""
            if parent_card is not None:
                parent_text = node_polished_map.get(parent_card.get("id", ""), "")

            sibling_cards = self._get_sibling_cards(card, cards)
            sibling_text_map = self._build_text_map_for_cards(sibling_cards, node_polished_map)

            child_cards = self._get_child_cards(card, cards)
            child_text_map = self._build_text_map_for_cards(child_cards, node_polished_map)

            if enable_review:
                step_start = time.perf_counter()
                print(f"\n===== 节点一致性检查：{display_title} =====\n")
                consistency_result_before = self.node_consistency_checker.check_node(
                    topic=topic,
                    goal=goal,
                    target_node_card=card,
                    target_node_text=node_polished_text,
                    parent_card=parent_card,
                    parent_text=parent_text,
                    sibling_cards=sibling_cards,
                    sibling_text_map=sibling_text_map,
                    child_cards=child_cards,
                    child_text_map=child_text_map,
                    outline_review_text=outline_review_text
                )
                elapsed = time.perf_counter() - step_start

                self.cost_tracker.record(
                    component=f"node_consistency_checker_before:{node_id}",
                    model=self.node_consistency_checker.get_model_name(),
                    input_text=json.dumps(card, ensure_ascii=False) + node_polished_text + outline_review_text,
                    output_text=json.dumps(consistency_result_before, ensure_ascii=False),
                    elapsed_seconds=elapsed
                )
            else:
                self.logger.info(f"跳过节点一致性检查 | id={node_id} | title={display_title}")
                consistency_result_before = {"skipped": True, "reason": "enable_review=False"}

            consistency_before_path = nodes_dir / f"{idx:03d}_{self._sanitize_name(node_id)}_consistency_before.json"
            consistency_before_path.write_text(
                json.dumps(consistency_result_before, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

            final_node_text = node_polished_text
            consistency_result_after = {}
            revision_triggered = False

            # 7. 自动修订回流
            if enable_review and enable_consistency_revision and self._should_trigger_revision(consistency_result_before):
                revision_triggered = True
                self.logger.info(f"一致性检查触发自动修订 | id={node_id} | title={display_title}")

                reviser_context = (
                    final_context_text
                    + "\n\n【节点一致性检查报告(JSON)】\n"
                    + json.dumps(consistency_result_before, ensure_ascii=False, indent=2)
                )

                step_start = time.perf_counter()
                print(f"\n===== 节点自动修订：{display_title} =====\n")
                revised_text = self.node_reviser.revise_node_stream(
                    topic=topic,
                    goal=goal,
                    node_card=card,
                    node_text=node_polished_text,
                    consistency_report=json.dumps(consistency_result_before, ensure_ascii=False, indent=2),
                    literature_pack_text=literature_pack_text,
                    outline_review_text=outline_review_text,
                    previous_context_text=reviser_context
                )
                elapsed = time.perf_counter() - step_start

                revised_output_path = nodes_dir / f"{idx:03d}_{self._sanitize_name(node_id)}_revised.txt"
                revised_output_path.write_text(revised_text, encoding="utf-8")

                self.cost_tracker.record(
                    component=f"node_reviser:{node_id}",
                    model=self.node_reviser.get_model_name(),
                    input_text=json.dumps(card, ensure_ascii=False) + node_polished_text + json.dumps(consistency_result_before, ensure_ascii=False) + literature_pack_text + outline_review_text + reviser_context,
                    output_text=revised_text,
                    elapsed_seconds=elapsed
                )

                final_node_text = revised_text

                # 修订后再检查一次
                step_start = time.perf_counter()
                print(f"\n===== 节点一致性复检：{display_title} =====\n")
                consistency_result_after = self.node_consistency_checker.check_node(
                    topic=topic,
                    goal=goal,
                    target_node_card=card,
                    target_node_text=final_node_text,
                    parent_card=parent_card,
                    parent_text=parent_text,
                    sibling_cards=sibling_cards,
                    sibling_text_map=sibling_text_map,
                    child_cards=child_cards,
                    child_text_map=child_text_map,
                    outline_review_text=outline_review_text
                )
                elapsed = time.perf_counter() - step_start

                consistency_after_path = nodes_dir / f"{idx:03d}_{self._sanitize_name(node_id)}_consistency_after.json"
                consistency_after_path.write_text(
                    json.dumps(consistency_result_after, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )

                self.cost_tracker.record(
                    component=f"node_consistency_checker_after:{node_id}",
                    model=self.node_consistency_checker.get_model_name(),
                    input_text=json.dumps(card, ensure_ascii=False) + final_node_text + outline_review_text,
                    output_text=json.dumps(consistency_result_after, ensure_ascii=False),
                    elapsed_seconds=elapsed
                )

            # 8. 保存最终版本
            final_output_path = nodes_dir / f"{idx:03d}_{self._sanitize_name(node_id)}_final.txt"
            final_output_path.write_text(final_node_text, encoding="utf-8")

            node_polished_map[node_id] = final_node_text
            node_consistency_map[node_id] = {
                "revision_triggered": revision_triggered,
                "before": consistency_result_before,
                "after": consistency_result_after
            }

            card_output_path = nodes_dir / f"{idx:03d}_{self._sanitize_name(node_id)}_card.json"
            card_output_path.write_text(
                json.dumps(card, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

            self.logger.info(
                f"节点处理完成 | index={idx} | id={node_id} | title={display_title} | "
                f"references={reference_output_path} | raw={raw_output_path} | "
                f"final={final_output_path} | revision_triggered={revision_triggered}"
            )

        raw_map_path = run_dir / "node_raw_map.json"
        raw_map_path.write_text(
            json.dumps(node_raw_map, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        polished_map_path = run_dir / "node_polished_map.json"
        polished_map_path.write_text(
            json.dumps(node_polished_map, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        reference_map_path = run_dir / "node_reference_map.json"
        reference_map_path.write_text(
            json.dumps(node_reference_map, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        consistency_map_path = run_dir / "node_consistency_map.json"
        consistency_map_path.write_text(
            json.dumps(node_consistency_map, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        if assemble:
            self.logger.info("开始调用 NodeAssembler 进行递归组装")
            assembled_result = self.node_assembler.assemble_from_schema_dict(
                schema=schema,
                node_text_map=node_polished_map,
                include_empty_placeholder=True
            )
        else:
            self.logger.info("跳过 NodeAssembler 组装 | assemble=False")
            assembled_result = {"skipped": True, "reason": "assemble=False"}

        cost_report_path = run_dir / "node_pipeline_cost_report.json"
        self.cost_tracker.save_json(str(cost_report_path))

        total_elapsed = time.perf_counter() - total_start
        self.logger.info(
            f"NodePipeline 完成 | topic={topic} | elapsed={total_elapsed:.2f}s | run_dir={run_dir}"
        )

        return {
            "topic": topic,
            "run_dir": str(run_dir),
            "nodes_dir": str(nodes_dir),
            "literature_pack_path": literature_pack_path,
            "schema_path": schema_path,
            "cards_path": cards_path,
            "outline_review_path": outline_review_path,
            "schema_used_path": str(schema_used_path),
            "cards_used_path": str(cards_used_path),
            "literature_summaries_used_path": str(literature_summaries_used_path),
            "scheduled_cards_path": str(scheduled_cards_path),
            "raw_map_path": str(raw_map_path),
            "polished_map_path": str(polished_map_path),
            "reference_map_path": str(reference_map_path),
            "consistency_map_path": str(consistency_map_path),
            "cost_report_path": str(cost_report_path),
            "assembled_result": assembled_result,
            "cost_records": self.cost_tracker.to_dict(),
            "processed_nodes_count": len(node_polished_map)
        }