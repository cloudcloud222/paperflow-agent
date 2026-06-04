from src.workflow.reviewer import DraftReviewer

reviewer = DraftReviewer()

draft_text = """
本研究拟搭建一个面向研究生论文写作场景的 agent 平台，以辅助完成论文任务规划、资料整理与初稿生成等关键环节。考虑到平台开发初期的成本控制需求，系统首先采用低成本大模型接口完成整体流程打通，在此基础上逐步扩展更高性能模型，以支持复杂写作与审阅任务。当前阶段，平台已经完成 DeepSeek API 调用、基础客户端封装、任务规划模块以及资料整理模块，并进一步实现了论文初稿生成功能。后续研究将继续补充审阅模块和多节点串联流程，以形成更加完整的论文辅助写作闭环。
"""

result = reviewer.review_stream(draft_text)

print("\n\n=== 最终完整结果 ===")
print(result)