from src.input_loader.input_service import InputService
from src.workflow.pipeline import PaperWorkflow
from src.utils.logger import get_logger


def main():
    logger = get_logger("run_pipeline")

    try:
        logger.info("系统启动，开始读取输入数据")
        input_service = InputService()
        input_data = input_service.load_all_inputs()

        topic = input_data["topic"]
        goal = input_data["goal"]
        materials = input_data["materials"]

        logger.info(f"输入读取完成 | 论文主题={topic} | 当前目标={goal} | 参考文献数量={len(materials)}")

        print("===== 正在读取输入数据 =====")
        print(f"论文主题：{topic}")
        print(f"当前目标：{goal}")
        print(f"参考文献数量：{len(materials)}")

        workflow = PaperWorkflow()
        result = workflow.run(
            user_goal=goal,
            topic=topic,
            materials=materials
        )

        logger.info(
            f"系统运行完成 | 主流程输出目录={result['run_dir']} | 文献摘要输出目录={result['literature_run_dir']}"
        )

        print("\n\n===== 系统运行完成 =====")
        print("论文主题：", result["topic"])
        print("主流程输出目录：", result["run_dir"])
        print("文献摘要输出目录：", result["literature_run_dir"])
        print("文献整理总文档：", result["literature_pack_path"])
        print("成本统计报告：", result["cost_report_path"])

    except Exception as e:
        logger.exception(f"系统运行失败: {e}")
        raise


if __name__ == "__main__":
    main()