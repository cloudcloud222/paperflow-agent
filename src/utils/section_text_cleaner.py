import re


class SectionTextCleaner:
    def __init__(self):
        self.markdown_heading_pattern = re.compile(r"^\s*#{1,6}\s*")
        self.chapter_title_pattern = re.compile(r"^\s*第[一二三四五六七八九十0-9]+章")
        self.short_number_heading_pattern = re.compile(r"^\s*\d+(\.\d+){0,3}\s+")
        self.process_label_keywords = [
            "Introduction 初稿",
            "Introduction 润色稿",
            "Related Work 初稿",
            "Related Work 润色稿",
            "Methodology 初稿",
            "Methodology 润色稿",
            "Experiment 初稿",
            "Experiment 润色稿",
            "Conclusion 初稿",
            "Conclusion 润色稿",
            "润色稿",
            "初稿"
        ]

    def clean(self, text: str) -> str:
        if not text:
            return ""

        lines = text.replace("\r\n", "\n").split("\n")
        cleaned = []

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue

            if self.markdown_heading_pattern.match(line):
                continue

            if self.chapter_title_pattern.match(line):
                continue

            if len(line) < 50 and self.short_number_heading_pattern.match(line):
                continue

            if any(keyword in line for keyword in self.process_label_keywords) and len(line) < 80:
                continue

            line = re.sub(r"^\s*[-*]\s+", "", line)
            cleaned.append(line)

        return "\n".join(cleaned).strip()