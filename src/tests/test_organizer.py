from src.workflow.organizer import MaterialOrganizer

organizer = MaterialOrganizer()

raw_text = """
我想做一个辅助论文写作的agent平台。
第一阶段希望它先完成两件事：文献整理和论文初稿生成。
我现在已经完成了DeepSeek API调用、client封装、planner模块。
后面希望继续加入写作模块和审阅模块。
"""

result = organizer.organize(raw_text)
print(result)