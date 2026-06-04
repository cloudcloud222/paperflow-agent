from src.input_loader.input_service import InputService
from src.workflow.section_pipeline import SectionPipeline
from src.workflow.paper_assembler import PaperAssembler
from src.utils.logger import get_logger


def main():
    logger = get_logger("run_section_pipeline")

    try:
        logger.info("章节化正式入口启动，开始读取输入数据")
        input_service = InputService()
        input_data = input_service.load_all_inputs()

        topic = input_data["topic"]
        goal = input_data["goal"]
        materials = input_data["materials"]

        logger.info(
            f"输入读取完成 | 论文主题={topic} | 当前目标={goal} | 参考文献数量={len(materials)}"
        )

        print("===== 正在读取输入数据 =====")
        print(f"论文主题：{topic}")
        print(f"当前目标：{goal}")
        print(f"参考文献数量：{len(materials)}")

        # 1. 运行章节化流水线（内部已包含 consistency_checker）
        logger.info("开始执行 SectionPipeline（含全文一致性检查）")
        section_pipeline = SectionPipeline()
        section_result = section_pipeline.run(
            topic=topic,
            goal=goal,
            materials=materials
        )
        logger.info(
            f"SectionPipeline 执行完成 | 输出目录={section_result['run_dir']} | 成本报告={section_result['cost_report_path']}"
        )

        consistency_report_path = f"{section_result['run_dir']}/13_consistency_report.docx"

        # 2. 组装全文
        logger.info("开始执行 PaperAssembler")
        assembler = PaperAssembler()
        assemble_result = assembler.assemble_from_latest_sections(topic=topic)
        logger.info(
            f"PaperAssembler 执行完成 | 输出目录={assemble_result['run_dir']} | final_docx={assemble_result['final_docx_path']}"
        )

        print("\n\n===== 章节化流水线执行完成 =====")
        print("章节输出目录：", section_result["run_dir"])
        print("章节成本报告：", section_result["cost_report_path"])
        print("一致性检查报告：", consistency_report_path)

        print("\n===== 全文组装完成 =====")
        print("全文输出目录：", assemble_result["run_dir"])
        print("全文 docx：", assemble_result["final_docx_path"])
        print(
            "全文 RuleDoc docx：",
            assemble_result["final_ruledoc_path"] if assemble_result["final_ruledoc_path"] else "未启用"
        )
        print("全文章节来源：", assemble_result["source_paths"])

        logger.info(
            f"章节化正式入口全部完成 | section_dir={section_result['run_dir']} | final_dir={assemble_result['run_dir']}"
        )

    except Exception as e:
        logger.exception(f"章节化正式入口运行失败: {e}")
        raise


if __name__ == "__main__":
    main()