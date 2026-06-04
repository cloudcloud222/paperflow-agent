from src.workflow.writer import DraftWriter

writer = DraftWriter()

material = """
【研究背景】
希望搭建一个面向研究生论文写作的agent平台，用于辅助完成文献整理、论文初稿生成、后续实验支持和审稿修改。

【核心问题】
如何以较低成本先搭建一个最小可用版本，使平台具备任务规划、资料整理和初稿写作能力。

【已有信息】
1. 已完成 DeepSeek API 调用
2. 已完成 client 封装
3. 已完成 planner 模块
4. 已完成 organizer 模块

【仍然缺少的信息】
1. 初稿写作模块
2. 审阅模块
3. 多模块串联流程

【可直接用于写作的要点】
1. 当前目标是先完成平台最小骨架
2. 平台将首先覆盖论文任务规划、资料整理和初稿写作
3. 后续将进一步加入审阅与多节点工作流
"""

result = writer.write_draft(material)
print(result)