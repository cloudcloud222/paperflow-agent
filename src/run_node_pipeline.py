import json
from pathlib import Path

from src.input_loader.input_service import InputService
from src.workflow.node_pipeline import NodePipeline
from src.utils.logger import get_logger


def load_json_file(json_path: str) -> dict:
    path = Path(json_path)
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def analyze_consistency_map(consistency_map_path: str) -> dict:
    data = load_json_file(consistency_map_path)

    revision_triggered_ids = []
    not_pass_for_assembly_ids = []
    high_priority_ids = []

    for node_id, item in data.items():
        if not isinstance(item, dict):
            continue

        if item.get("revision_triggered") is True:
            revision_triggered_ids.append(node_id)

        # 优先看 after，没有 after 再看 before
        final_result = item.get("after") if item.get("after") else item.get("before", {})
        if not isinstance(final_result, dict):
            final_result = {}

        if final_result.get("pass_for_assembly") is False:
            not_pass_for_assembly_ids.append(node_id)

        if final_result.get("revision_priority") == "high":
            high_priority_ids.append(node_id)

    return {
        "revision_triggered_count": len(revision_triggered_ids),
        "revision_triggered_ids": revision_triggered_ids,
        "not_pass_for_assembly_count": len(not_pass_for_assembly_ids),
        "not_pass_for_assembly_ids": not_pass_for_assembly_ids,
        "high_priority_count": len(high_priority_ids),
        "high_priority_ids": high_priority_ids,
    }


def main():
    logger = get_logger("run_node_pipeline")

    try:
        logger.info("Node 主线正式入口启动，开始读取输入数据")
        input_service = InputService()
        input_data = input_service.load_all_inputs()

        topic = input_data["topic"]
        goal = input_data["goal"]
        materials = input_data["materials"]

        # 主入口统一参数
        strategy = "hybrid"                 # 可改成 top_down / bottom_up / hybrid
        leaf_only = False                   # True 表示只写叶子节点
        enable_consistency_revision = True  # 是否启用一致性检查后的自动回流修订

        logger.info(
            f"输入读取完成 | 论文主题={topic} | 当前目标={goal} | 参考文献数量={len(materials)}"
        )

        print("===== 正在读取输入数据 =====")
        print(f"论文主题：{topic}")
        print(f"当前目标：{goal}")
        print(f"参考文献数量：{len(materials)}")
        print(f"调度策略：{strategy}")
        print(f"仅写叶子节点：{leaf_only}")
        print(f"启用一致性回流修订：{enable_consistency_revision}")

        pipeline = NodePipeline()
        result = pipeline.run(
            topic=topic,
            goal=goal,
            materials=materials,
            strategy=strategy,
            leaf_only=leaf_only,
            enable_consistency_revision=enable_consistency_revision
        )

        logger.info(
            f"NodePipeline 执行完成 | 输出目录={result['run_dir']} | 成本报告={result['cost_report_path']} | 节点数={result['processed_nodes_count']}"
        )

        assembled = result["assembled_result"]

        logger.info(
            f"NodeAssembler 执行完成 | 输出目录={assembled['run_dir']} | final_docx={assembled['final_docx_path']}"
        )

        consistency_stats = analyze_consistency_map(result["consistency_map_path"])

        print("\n\n===== Node Pipeline 执行完成 =====")
        print("论文主题：", result["topic"])
        print("NodePipeline 输出目录：", result["run_dir"])
        print("节点输出目录：", result["nodes_dir"])
        print("已处理节点数：", result["processed_nodes_count"])
        print("结构化总纲：", result["schema_used_path"])
        print("节点卡片：", result["cards_used_path"])
        print("文献摘要：", result["literature_summaries_used_path"])
        print("调度结果：", result["scheduled_cards_path"])
        print("节点参考文献映射：", result["reference_map_path"])
        print("节点一致性检查映射：", result["consistency_map_path"])
        print("节点初稿映射：", result["raw_map_path"])
        print("节点最终正文映射：", result["polished_map_path"])
        print("成本报告：", result["cost_report_path"])

        print("\n===== 自动修订统计 =====")
        print("是否启用一致性回流修订：", enable_consistency_revision)
        print("触发自动修订的节点数：", consistency_stats["revision_triggered_count"])
        if consistency_stats["revision_triggered_ids"]:
            print("触发修订的节点ID：", ", ".join(consistency_stats["revision_triggered_ids"]))
        else:
            print("触发修订的节点ID：无")

        print("\n===== 一致性结果统计（按最终结果） =====")
        print("修订后仍不建议进入组装的节点数：", consistency_stats["not_pass_for_assembly_count"])
        if consistency_stats["not_pass_for_assembly_ids"]:
            print("不建议进入组装的节点ID：", ", ".join(consistency_stats["not_pass_for_assembly_ids"]))
        else:
            print("不建议进入组装的节点ID：无")

        print("高优先级问题节点数：", consistency_stats["high_priority_count"])
        if consistency_stats["high_priority_ids"]:
            print("高优先级问题节点ID：", ", ".join(consistency_stats["high_priority_ids"]))
        else:
            print("高优先级问题节点ID：无")

        print("\n===== Node Assembler 输出 =====")
        print("全文输出目录：", assembled["run_dir"])
        print("全文 docx：", assembled["final_docx_path"])
        print(
            "全文 RuleDoc docx：",
            assembled["final_ruledoc_path"] if assembled["final_ruledoc_path"] else "未启用"
        )

        logger.info(
            "Node 主线正式入口全部完成 | "
            f"node_run_dir={result['run_dir']} | "
            f"assembled_dir={assembled['run_dir']} | "
            f"revisions={consistency_stats['revision_triggered_count']} | "
            f"not_pass={consistency_stats['not_pass_for_assembly_count']} | "
            f"high_priority={consistency_stats['high_priority_count']}"
        )

    except Exception as e:
        logger.exception(f"Node 主线正式入口运行失败: {e}")
        raise


if __name__ == "__main__":
    main()