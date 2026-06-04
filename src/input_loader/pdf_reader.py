from pathlib import Path

import fitz
from docx import Document


class PDFReader:
    """Read reference materials for the paper workflow.

    The original implementation only accepted PDFs.  For a tool-style project it
    is useful to support sanitized TXT/DOCX examples as well, so demos can be
    shipped without private PDF papers.
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx"}

    def __init__(self, max_pages: int = 5):
        self.max_pages = max_pages

    def read_materials(self, folder_path: str) -> list[dict]:
        folder = Path(folder_path)

        if not folder.exists():
            raise FileNotFoundError(f"materials 路径不存在: {folder}")

        if not folder.is_dir():
            raise ValueError(f"materials 必须是文件夹: {folder}")

        material_files = sorted(
            [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in self.SUPPORTED_EXTENSIONS],
            key=lambda x: x.name
        )

        if not material_files:
            raise FileNotFoundError(
                f"materials 文件夹中未找到可读取材料: {folder}。支持 .pdf/.txt/.docx"
            )

        results = []
        for material_file in material_files:
            content = self._read_material(material_file)
            if not content:
                content = "[空材料或未能提取文本]"
            results.append({
                "filename": material_file.name,
                "content": content
            })

        return results

    def _read_material(self, file_path: Path) -> str:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            return self._read_pdf(file_path)
        if suffix == ".txt":
            return self._read_txt(file_path)
        if suffix == ".docx":
            return self._read_docx(file_path)
        raise ValueError(f"暂不支持的材料类型: {file_path.suffix}")

    def _read_pdf(self, pdf_path: Path) -> str:
        doc = fitz.open(pdf_path)
        texts = []

        try:
            page_count = min(len(doc), self.max_pages)
            for page_index in range(page_count):
                page = doc[page_index]
                text = page.get_text().strip()
                if text:
                    texts.append(text)
        finally:
            doc.close()

        return "\n".join(texts).strip()

    def _read_txt(self, file_path: Path) -> str:
        for encoding in ("utf-8", "utf-8-sig", "gbk"):
            try:
                return file_path.read_text(encoding=encoding).strip()
            except UnicodeDecodeError:
                continue
        return file_path.read_text(encoding="utf-8", errors="ignore").strip()

    def _read_docx(self, file_path: Path) -> str:
        document = Document(file_path)
        paragraphs = []
        for para in document.paragraphs:
            text = para.text.strip()
            if text:
                paragraphs.append(text)
        return "\n".join(paragraphs).strip()
