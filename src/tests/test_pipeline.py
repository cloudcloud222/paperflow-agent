from src.workflow.pipeline import PaperWorkflow

workflow = PaperWorkflow()

topic = "研究生论文写作辅助Agent平台"
user_goal = "我要搭建一个辅助研究生论文写作的agent平台，第一阶段先实现文献整理、初稿生成和初稿审阅。"

result = workflow.run(user_goal=user_goal, topic=topic)

print("\n\n===== 工作流执行完成 =====")
print("论文主题：", result["topic"])
print("结果保存目录：", result["run_dir"])
print("最终返回的字段有：", result.keys())