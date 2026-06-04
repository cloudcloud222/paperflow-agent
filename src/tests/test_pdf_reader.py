from src.input_loader.pdf_reader import PDFReader

reader = PDFReader(max_pages=3)
materials = reader.read_materials("data/input/materials")

print(f"共读取到 {len(materials)} 篇 PDF")

for index, item in enumerate(materials, start=1):
    print(f"\n===== 第 {index} 篇：{item['filename']} =====")
    preview = item["content"][:1000]
    print(preview)
    print("\n------ 预览结束 ------")