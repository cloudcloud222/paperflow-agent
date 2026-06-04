from pathlib import Path
from docx import Document


class FileReader:
    SUPPORTED_EXTENSIONS = {".txt", ".docx"}

    def read_input(self, path_str: str) -> str:
        path = Path(path_str)

        if not path.exists():
            raise FileNotFoundError(f"路径不存在: {path}")

        if path.is_file():
            return self._read_file(path)

        if path.is_dir():
            supported_files = self._find_supported_files(path)

            if len(supported_files) == 0:
                raise FileNotFoundError(f"文件夹中未找到可读取的 txt 或 docx 文件: {path}")

            if len(supported_files) > 1:
                file_names = [file.name for file in supported_files]
                raise ValueError(f"文件夹中存在多个可读取文件，请只保留一个: {file_names}")

            return self._read_file(supported_files[0])

        raise ValueError(f"无法识别的路径类型: {path}")

    def _find_supported_files(self, folder: Path) -> list[Path]:
        files = sorted(folder.iterdir(), key=lambda x: x.name)
        result = []

        for file in files:
            if file.is_file() and file.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                result.append(file)

        return result

    def _read_file(self, file_path: Path) -> str:
        suffix = file_path.suffix.lower()

        if suffix == ".txt":
            return self._read_txt(file_path)

        if suffix == ".docx":
            return self._read_docx(file_path)

        raise ValueError(f"暂不支持的文件类型: {file_path.suffix}")

    def _read_txt(self, file_path: Path) -> str:
        # UTF-8 is the project default. GBK fallback makes Windows-authored
        # Chinese notes easier to load without manual transcoding.
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
