import json
import time
from pathlib import Path
from datetime import datetime

from src.input_loader.input_service import InputService
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
from src.workflow.node_assembler import NodeAssembler


def sanitize_name(name: str) -> str:
    invalid_chars = '<>:"/\\|?*'
    sanitized = name
    for ch in invalid_chars:
        sanitized = sanitized.replace(ch, "_")
    sanitized = sanitized.strip()
    return sanitized[:50] if len(sanitized) > 50 else sanitized


def create_run_folder(topic: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = sanitize_name(topic) if topic else "untitled"
    run_dir = Path("data/output/node_pipeline_smoke") / f"{timestamp}_{safe_topic}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def find_latest_file(
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


def load_literature_summaries(reader: FileReader, topic: str) -> list[dict]:
    summaries = []
    base_dir = Path("data/output/literature_summaries")
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
                content = reader.read_input(str(f))
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


def prepare_literature_resources(topic: str, materials: list[dict], reader: FileReader):
    literature_pack_path = find_latest_file(
        "data/output/literature_summaries",
        filename="literature_review_pack.docx",
        topic=topic
    )

    if literature_pack_path is None:
        print("未找到已有文献整理总文档，开始自动生成...")
        literature_pipeline = LiteraturePipeline()
        literature_result = literature_pipeline.run(topic=topic, materials=materials)
        literature_pack_text = literature_result["merged_summary_text"]
        literature_pack_path = Path(literature_result["merged_docx_path"])

        literature_summaries = []
        for item in literature_result.get("summaries", []):
            literature_summaries.append({
                "source_filename": item.get("filename", ""),
                "summary_text": item.get("summary", "")
            })
    else:
        print("复用已有文献整理总文档：", literature_pack_path)
        literature_pack_text = reader.read_input(str(literature_pack_path))
        literature_summaries = load_literature_summaries(reader, topic)

    if not literature_summaries:
        literature_summaries = [{
            "source_filename": Path(literature_pack_path).name,
            "summary_text": literature_pack_text
        }]

    return literature_pack_text, str(literature_pack_path), literature_summaries


def prepare_schema(topic: str, goal: str, literature_pack_text: str):
    schema_path = find_latest_file(
        "data/output/outline_schemas",
        suffix=".json",
        topic=topic
    )

    if schema_path is not None:
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            print("复用已有结构化总纲：", schema_path)
            return schema, str(schema_path)
        except Exception:
            pass

    print("未找到可用结构化总纲，开始自动生成...")
    planner = OutlineSchemaPlanner()
    schema = planner.plan_schema(
        topic=topic,
        goal=goal,
        literature_pack_text=literature_pack_text,
        organized_material=""
    )

    output_dir = Path("data/output/outline_schemas")
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_topic = sanitize_name(topic)
    schema_path = output_dir / f"{safe_topic}_outline_schema.json"
    schema_path.write_text(
        json.dumps(schema, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    return schema, str(schema_path)


def prepare_cards(schema: dict):
    builder = NodeCardBuilder()
    result = builder.build_from_schema(schema)
    return result["cards"], result["cards_json_path"]


def load_outline_review_text(topic: str, reader: FileReader) -> tuple[str, str]:
    outline_review_path = find_latest_file(
        "data/output/outlines",
        filename="02_outline_review.docx",
        topic=topic
    )

    if outline_review_path is None:
        return "", ""

    return reader.read_input(str(outline_review_path)), str(outline_review_path)


def build_card_index(cards: list[dict]) -> dict[str, dict]:
    return {card.get("id", ""): card for card in cards if card.get("id")}


def get_parent_card(card: dict, card_index: dict[str, dict]) -> dict | None:
    parent_id = card.get("parent_id")
    if not parent_id:
        return None
    return card_index.get(parent_id)


def get_sibling_cards(card: dict, all_cards: list[dict]) -> list[dict]:
    parent_id = card.get("parent_id")
    node_id = card.get("id")
    return [
        c for c in all_cards
        if c.get("parent_id") == parent_id and c.get("id") != node_id
    ]


def get_child_cards(card: dict, all_cards: list[dict]) -> list[dict]:
    node_id = card.get("id")
    return [
        c for c in all_cards
        if c.get("parent_id") == node_id
    ]


def build_text_map_for_cards(cards: list[dict], polished_map: dict[str, str]) -> dict[str, str]:
    result = {}
    for card in cards:
        node_id = card.get("id", "")
        if node_id:
            result[node_id] = polished_map.get(node_id, "")
    return result


def main():
    # ========= 可调参数（先用这个小测试） =========
    strategy = "hybrid"
    leaf_only = True
    max_nodes = 1
    enable_reference_selection = True
    enable_consistency_check = True
    enable_revision = False   # smoke test 默认关掉，省时间
    include_empty_placeholder = True
    # ============================================

    reader = FileReader()

    service = InputService()
    input_data = service.load_all_inputs()

    topic = input_data["topic"]
    goal = input_data["goal"]
    materials = input_data["materials"]

    print("===== Node Pipeline Smoke Test =====")
    print("论文主题：", topic)
    print("当前目标：", goal)
    print("参考文献数量：", len(materials))
    print("调度策略：", strategy)
    print("仅叶子节点：", leaf_only)
    print("最大节点数：", max_nodes)
    print("启用参考文献选择：", enable_reference_selection)
    print("启用一致性检查：", enable_consistency_check)
    print("启用自动修订：", enable_revision)

    run_dir = create_run_folder(topic)
    nodes_dir = run_dir / "nodes"
    nodes_dir.mkdir(parents=True, exist_ok=True)

    total_start = time.perf_counter()

    # 1. 准备文献资源
    literature_pack_text, literature_pack_path, literature_summaries = prepare_literature_resources(
        topic, materials, reader
    )

    # 2. 准备 schema
    schema, schema_path = prepare_schema(topic, goal, literature_pack_text)

    # 3. 准备 cards
    cards, cards_path = prepare_cards(schema)

    # 4. 调度
    scheduler = NodeScheduler()
    scheduled_cards = scheduler.schedule(
        cards=cards,
        strategy=strategy,
        leaf_only=leaf_only
    )
    scheduled_cards = scheduled_cards[:max_nodes]

    # 5. 总纲审查（可选）
    outline_review_text, outline_review_path = load_outline_review_text(topic, reader)

    # 保存本次使用的中间件
    (run_dir / "schema_used.json").write_text(
        json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (run_dir / "cards_used.json").write_text(
        json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (run_dir / "scheduled_cards_used.json").write_text(
        json.dumps(scheduled_cards, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 6. 初始化组件
    context_builder = NodeContextBuilder()
    reference_selector = NodeReferenceSelector()
    writer = NodeWriter()
    polisher = NodePolisher()
    consistency_checker = NodeConsistencyChecker()
    assembler = NodeAssembler()

    card_index = build_card_index(cards)

    node_raw_map = {}
    node_polished_map = {}
    node_reference_map = {}
    node_consistency_map = {}

    for idx, card in enumerate(scheduled_cards, start=1):
        node_id = card.get("id", f"node_{idx}")
        display_title = card.get("display_title", node_id)

        print(f"\n===== 处理节点 {idx}/{len(scheduled_cards)}：{display_title} =====")

        # 基础上下文
        context_package = context_builder.build_context_package(
            topic=topic,
            goal=goal,
            node_card=card,
            all_cards=cards,
            polished_map=node_polished_map
        )
        base_context_text = context_package["context_text"]

        (nodes_dir / f"{idx:03d}_{sanitize_name(node_id)}_base_context.txt").write_text(
            base_context_text, encoding="utf-8"
        )

        final_context_text = base_context_text
        reference_selection = {}

        # 参考文献选择
        if enable_reference_selection:
            print("  -> 参考文献选择")
            reference_selection = reference_selector.select_references(
                topic=topic,
                goal=goal,
                node_card=card,
                literature_summaries=literature_summaries,
                outline_review_text=outline_review_text,
                previous_context_text=base_context_text
            )
            node_reference_map[node_id] = reference_selection

            (nodes_dir / f"{idx:03d}_{sanitize_name(node_id)}_references.json").write_text(
                json.dumps(reference_selection, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

            summary = reference_selection.get("selection_summary", "")
            writing_hint = reference_selection.get("writing_hint", "")
            selected_refs = reference_selection.get("selected_references", [])

            ref_lines = []
            if summary:
                ref_lines.append("【参考文献选择说明】")
                ref_lines.append(summary)
            if selected_refs:
                ref_lines.append("")
                ref_lines.append("【当前节点推荐参考文献】")
                for i, ref in enumerate(selected_refs, start=1):
                    ref_lines.append(f"{i}. 来源：{ref.get('source_filename', '')}")
                    if ref.get("relevance_reason"):
                        ref_lines.append(f"   相关原因：{ref.get('relevance_reason')}")
                    if ref.get("suggested_use"):
                        ref_lines.append(f"   建议用途：{ref.get('suggested_use')}")
            if writing_hint:
                ref_lines.append("")
                ref_lines.append("【写作提示】")
                ref_lines.append(writing_hint)

            reference_context_text = "\n".join(ref_lines).strip()
            if reference_context_text:
                final_context_text = base_context_text + "\n\n" + reference_context_text

        (nodes_dir / f"{idx:03d}_{sanitize_name(node_id)}_context.txt").write_text(
            final_context_text, encoding="utf-8"
        )

        # 节点写作
        print("  -> 节点写作")
        node_raw_text = writer.write_node(
            topic=topic,
            goal=goal,
            node_card=card,
            literature_pack_text=literature_pack_text,
            outline_review_text=outline_review_text,
            previous_context_text=final_context_text
        )
        node_raw_map[node_id] = node_raw_text
        (nodes_dir / f"{idx:03d}_{sanitize_name(node_id)}_raw.txt").write_text(
            node_raw_text, encoding="utf-8"
        )

        # 节点润色
        print("  -> 节点润色")
        node_polished_text = polisher.polish_node(
            topic=topic,
            goal=goal,
            node_card=card,
            node_text=node_raw_text,
            literature_pack_text=literature_pack_text,
            outline_review_text=outline_review_text,
            previous_context_text=final_context_text
        )
        (nodes_dir / f"{idx:03d}_{sanitize_name(node_id)}_polished_before_revision.txt").write_text(
            node_polished_text, encoding="utf-8"
        )

        final_node_text = node_polished_text
        consistency_before = {}
        consistency_after = {}
        revision_triggered = False

        # 一致性检查
        if enable_consistency_check:
            print("  -> 节点一致性检查")
            parent_card = get_parent_card(card, card_index)
            parent_text = ""
            if parent_card is not None:
                parent_text = node_polished_map.get(parent_card.get("id", ""), "")

            sibling_cards = get_sibling_cards(card, cards)
            sibling_text_map = build_text_map_for_cards(sibling_cards, node_polished_map)

            child_cards = get_child_cards(card, cards)
            child_text_map = build_text_map_for_cards(child_cards, node_polished_map)

            consistency_before = consistency_checker.check_node(
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

            (nodes_dir / f"{idx:03d}_{sanitize_name(node_id)}_consistency_before.json").write_text(
                json.dumps(consistency_before, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

            if enable_revision and consistency_before.get("revision_required") is True:
                revision_triggered = True
                print("  -> 节点自动修订")
                from src.workflow.node_reviser import NodeReviser
                reviser = NodeReviser()

                revised_text = reviser.revise_node(
                    topic=topic,
                    goal=goal,
                    node_card=card,
                    node_text=node_polished_text,
                    consistency_report=json.dumps(consistency_before, ensure_ascii=False, indent=2),
                    literature_pack_text=literature_pack_text,
                    outline_review_text=outline_review_text,
                    previous_context_text=final_context_text
                )

                final_node_text = revised_text
                (nodes_dir / f"{idx:03d}_{sanitize_name(node_id)}_revised.txt").write_text(
                    revised_text, encoding="utf-8"
                )

                consistency_after = consistency_checker.check_node(
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

                (nodes_dir / f"{idx:03d}_{sanitize_name(node_id)}_consistency_after.json").write_text(
                    json.dumps(consistency_after, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )

        # 保存最终文本
        node_polished_map[node_id] = final_node_text
        node_consistency_map[node_id] = {
            "revision_triggered": revision_triggered,
            "before": consistency_before,
            "after": consistency_after
        }

        (nodes_dir / f"{idx:03d}_{sanitize_name(node_id)}_final.txt").write_text(
            final_node_text, encoding="utf-8"
        )
        (nodes_dir / f"{idx:03d}_{sanitize_name(node_id)}_card.json").write_text(
            json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # 汇总
    (run_dir / "node_raw_map.json").write_text(
        json.dumps(node_raw_map, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (run_dir / "node_polished_map.json").write_text(
        json.dumps(node_polished_map, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (run_dir / "node_reference_map.json").write_text(
        json.dumps(node_reference_map, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (run_dir / "node_consistency_map.json").write_text(
        json.dumps(node_consistency_map, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 组装
    print("\n===== 递归组装测试 =====")
    assembled_result = assembler.assemble_from_schema_dict(
        schema=schema,
        node_text_map=node_polished_map,
        include_empty_placeholder=include_empty_placeholder
    )

    elapsed = time.perf_counter() - total_start

    print("\n===== Smoke Test 完成 =====")
    print("运行目录：", run_dir)
    print("文献整理：", literature_pack_path)
    print("结构化总纲：", schema_path)
    print("节点卡片：", cards_path)
    print("总纲审查：", outline_review_path if outline_review_path else "无")
    print("实际处理节点数：", len(node_polished_map))
    print("全文输出目录：", assembled_result["run_dir"])
    print("全文 docx：", assembled_result["final_docx_path"])
    print("总耗时（秒）：", round(elapsed, 2))


if __name__ == "__main__":
    main()