from src.formatting.ruledoc_adapter import RuleDocAdapter

adapter = RuleDocAdapter(rule_name="yzu_thesis")

input_path = r"data\output\20260422_173952_研究生论文写作辅助Agent平台\03_draft.docx"
output_path = r"data\output\20260422_173952_研究生论文写作辅助Agent平台\03_draft_ruledoc.docx"

adapter.format_docx(input_path=input_path, output_path=output_path)

print("RuleDoc 格式修正完成")
print("输入文件：", input_path)
print("输出文件：", output_path)