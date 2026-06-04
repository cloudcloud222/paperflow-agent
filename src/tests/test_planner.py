from src.workflow.planner import TaskPlanner

planner = TaskPlanner()

result = planner.plan("我要搭建一个用于辅助论文写作的agent平台，先完成文献整理和论文初稿生成。")
print(result)