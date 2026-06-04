import json
from pathlib import Path
from datetime import datetime

from src.utils.config_loader import ConfigLoader
from src.utils.logger import get_logger


class NodeCardBuilder:
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.logger = get_logger("NodeCardBuilder")

        paths_config = self.config_loader.load_paths_config()
        self.schema_dir = Path(paths_config["output"]["outline_schema_dir"])
        self.node_cards_dir = Path(paths_config["output"]["node_cards_dir"])
        self.node_cards_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_name(self, name: str) -> str:
        invalid_chars = '<>:"/\\|?*'
        sanitized = name
        for ch in invalid_chars:
            sanitized = sanitized.replace(ch, "_")
        sanitized = sanitized.strip()
        return sanitized[:50] if len(sanitized) > 50 else sanitized

    def _create_run_folder(self, topic: str) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = self._sanitize_name(topic) if topic else "untitled"
        run_dir = self.node_cards_dir / f"{timestamp}_{safe_topic}"
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def _find_latest_schema_file(self, topic: str) -> Path:
        if not self.schema_dir.exists():
            raise FileNotFoundError(f"结构化总纲目录不存在: {self.schema_dir}")

        matched_files = list(self.schema_dir.glob("*.json"))
        matched_files = [p for p in matched_files if topic in p.name]

        if not matched_files:
            raise FileNotFoundError(f"未找到当前主题对应的结构化总纲 JSON: topic={topic}")

        matched_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return matched_files[0]

    def _walk_node(
        self,
        node: dict,
        cards: list[dict],
        parent_id: str | None = None,
        parent_title: str = "",
        ancestor_titles: list[str] | None = None
    ):
        if ancestor_titles is None:
            ancestor_titles = []

        number = node.get("number", "")
        title = node.get("title", "")
        display_title = f"{number} {title}".strip()

        children = node.get("children", [])
        children_ids = [child.get("id", "") for child in children]

        current_ancestors = ancestor_titles.copy()
        path_titles = current_ancestors + [display_title]
        path = " > ".join(path_titles)

        card = {
            "id": node.get("id", ""),
            "number": number,
            "title": title,
            "display_title": display_title,
            "level": int(node.get("level", 1)),
            "node_type": node.get("node_type", "custom"),
            "goal": node.get("goal", ""),
            "key_points": node.get("key_points", []),
            "parent_id": parent_id,
            "parent_title": parent_title,
            "ancestor_titles": current_ancestors,
            "children_ids": children_ids,
            "has_children": len(children_ids) > 0,
            "path": path
        }
        cards.append(card)

        next_ancestors = current_ancestors + [display_title]
        for child in children:
            self._walk_node(
                child,
                cards,
                parent_id=node.get("id", ""),
                parent_title=display_title,
                ancestor_titles=next_ancestors
            )

    def build_from_schema(self, schema: dict) -> dict:
        topic = schema.get("paper_title", "untitled")
        run_dir = self._create_run_folder(topic)

        cards: list[dict] = []
        for chapter in schema.get("chapters", []):
            self._walk_node(chapter, cards)

        cards_json_path = run_dir / "node_cards.json"
        cards_txt_path = run_dir / "node_cards.txt"

        cards_json_path.write_text(
            json.dumps(cards, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        lines = []
        lines.append(f"论文题目：{schema.get('paper_title', '')}")
        lines.append(f"写作总目标：{schema.get('writing_goal', '')}")
        lines.append("")
        lines.append("===== 节点卡片列表 =====")
        lines.append("")

        for idx, card in enumerate(cards, start=1):
            lines.append(f"[节点 {idx}]")
            lines.append(f"id: {card['id']}")
            lines.append(f"display_title: {card['display_title']}")
            lines.append(f"level: {card['level']}")
            lines.append(f"node_type: {card['node_type']}")
            lines.append(f"goal: {card['goal']}")
            lines.append(f"parent_id: {card['parent_id']}")
            lines.append(f"parent_title: {card['parent_title']}")
            lines.append(f"path: {card['path']}")
            lines.append("key_points:")
            for point in card["key_points"]:
                lines.append(f"  - {point}")
            lines.append(f"children_ids: {card['children_ids']}")
            lines.append("")

        cards_txt_path.write_text("\n".join(lines).strip(), encoding="utf-8")

        self.logger.info(
            f"节点卡片构建完成 | topic={topic} | count={len(cards)} | json={cards_json_path} | txt={cards_txt_path}"
        )

        return {
            "topic": topic,
            "run_dir": str(run_dir),
            "cards_count": len(cards),
            "cards_json_path": str(cards_json_path),
            "cards_txt_path": str(cards_txt_path),
            "cards": cards
        }

    def build_from_json_file(self, json_path: str) -> dict:
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"JSON 文件不存在: {path}")

        schema = json.loads(path.read_text(encoding="utf-8"))
        return self.build_from_schema(schema)

    def build_from_latest_schema(self, topic: str) -> dict:
        latest_schema_path = self._find_latest_schema_file(topic)
        self.logger.info(f"开始构建节点卡片 | topic={topic} | source={latest_schema_path}")
        return self.build_from_json_file(str(latest_schema_path))