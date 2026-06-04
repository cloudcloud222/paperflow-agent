import json
import re
from pathlib import Path
from datetime import datetime

from src.llm.client import DeepSeekClient
from src.utils.prompt_loader import load_prompt
from src.utils.logger import get_logger


class NodeConsistencyChecker:
    def __init__(self):
        self.client = DeepSeekClient(component_name="node_consistency_checker")
        self.system_prompt = load_prompt("node_consistency_checker.txt")
        self.logger = get_logger("NodeConsistencyChecker")

    def get_model_name(self) -> str:
        return self.client.model_name

    def _clean_json_text(self, text: str) -> str:
        text = text.strip()

        if text.startswith("```json"):
            text = text[len("```json"):].strip()
        elif text.startswith("```"):
            text = text[len("```"):].strip()

        if text.endswith("```"):
            text = text[:-3].strip()

        return text

    def _extract_json_object_text(self, text: str) -> str:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start:end + 1]
        return text

    def _repair_invalid_backslashes(self, text: str) -> str:
        return re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text)

    def _remove_trailing_commas(self, text: str) -> str:
        return re.sub(r",(\s*[}\]])", r"\1", text)

    def _normalize_common_issues(self, text: str) -> str:
        text = text.replace("\ufeff", "")
        return text

    def _dump_bad_json(self, raw_text: str, stage: str = "parse_error") -> str:
        debug_dir = Path("data/output/debug/node_consistency_checker")
        debug_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = debug_dir / f"{timestamp}_{stage}.txt"
        file_path.write_text(raw_text, encoding="utf-8")

        self.logger.warning(f"NodeConsistencyChecker 解析失败，已保存原始输出到: {file_path}")
        return str(file_path)

    def _extract_bool_field(self, text: str, field_name: str) -> bool | None:
        pattern = rf'"{re.escape(field_name)}"\s*:\s*(true|false)'
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            return None
        return match.group(1).lower() == "true"

    def _extract_str_field(self, text: str, field_name: str) -> str | None:
        pattern = rf'"{re.escape(field_name)}"\s*:\s*"([^"]*)"'
        match = re.search(pattern, text)
        if not match:
            return None
        return match.group(1)

    def _fallback_result(
        self,
        target_node_card: dict,
        raw_text: str,
        error_message: str,
        debug_path: str
    ) -> dict:
        raw_node_id = self._extract_str_field(raw_text, "node_id")
        raw_display_title = self._extract_str_field(raw_text, "display_title")
        raw_revision_required = self._extract_bool_field(raw_text, "revision_required")
        raw_pass_for_assembly = self._extract_bool_field(raw_text, "pass_for_assembly")
        raw_revision_priority = self._extract_str_field(raw_text, "revision_priority")

        node_id = raw_node_id or target_node_card.get("id", "")
        display_title = raw_display_title or target_node_card.get("display_title", "")

        # 解析失败时采取“不中断主线”的保守策略：
        # - 默认不强制修订
        # - 默认允许进入组装
        # - 但明确标记 parse_failed，方便后处理
        revision_required = raw_revision_required if raw_revision_required is not None else False
        pass_for_assembly = raw_pass_for_assembly if raw_pass_for_assembly is not None else True
        revision_priority = raw_revision_priority if raw_revision_priority in {"low", "medium", "high"} else "low"

        return {
            "node_id": node_id,
            "display_title": display_title,
            "overall_assessment": "一致性检查结果解析失败，已降级处理。请结合调试文件人工复核。",
            "goal_alignment": {
                "status": "unknown",
                "issues": ["一致性检查 JSON 解析失败，无法可靠判断当前节点与目标的一致性。"],
                "suggestions": ["如需严格审查，请查看调试文件并人工复核。"]
            },
            "parent_alignment": {
                "status": "unknown",
                "issues": ["一致性检查 JSON 解析失败，无法可靠判断与父节点承接情况。"],
                "suggestions": []
            },
            "sibling_boundary": {
                "status": "unknown",
                "issues": ["一致性检查 JSON 解析失败，无法可靠判断与兄弟节点的边界关系。"],
                "suggestions": []
            },
            "child_hierarchy": {
                "status": "unknown",
                "issues": ["一致性检查 JSON 解析失败，无法可靠判断与子节点的层级关系。"],
                "suggestions": []
            },
            "terminology_consistency": {
                "status": "unknown",
                "issues": ["一致性检查 JSON 解析失败，无法可靠判断术语是否统一。"],
                "suggestions": []
            },
            "revision_required": revision_required,
            "pass_for_assembly": pass_for_assembly,
            "revision_priority": revision_priority,
            "summary_actions": [
                "查看调试文件，定位模型输出中的非法 JSON 结构。",
                "必要时对当前节点进行人工复核。",
                "后续可优化 prompt 或解析器以提升稳定性。"
            ],
            "parse_failed": True,
            "parse_error_message": error_message,
            "raw_output_debug_path": debug_path
        }

    def _safe_json_loads(self, text: str, target_node_card: dict) -> dict:
        cleaned = self._clean_json_text(text)
        cleaned = self._normalize_common_issues(cleaned)
        cleaned = self._extract_json_object_text(cleaned)

        # 第一次：直接解析
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # 第二次：修复反斜杠
        repaired = self._repair_invalid_backslashes(cleaned)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            pass

        # 第三次：去尾逗号 + 再解析
        repaired2 = self._remove_trailing_commas(repaired)
        try:
            return json.loads(repaired2)
        except json.JSONDecodeError as e:
            debug_path = self._dump_bad_json(text, stage="json_decode_error")
            return self._fallback_result(
                target_node_card=target_node_card,
                raw_text=text,
                error_message=str(e),
                debug_path=debug_path
            )

    def _build_user_message(
        self,
        topic: str,
        goal: str,
        target_node_card: dict,
        target_node_text: str,
        parent_card: dict | None = None,
        parent_text: str = "",
        sibling_cards: list[dict] | None = None,
        sibling_text_map: dict | None = None,
        child_cards: list[dict] | None = None,
        child_text_map: dict | None = None,
        outline_review_text: str = ""
    ) -> str:
        if sibling_cards is None:
            sibling_cards = []
        if sibling_text_map is None:
            sibling_text_map = {}
        if child_cards is None:
            child_cards = []
        if child_text_map is None:
            child_text_map = {}

        sibling_package = []
        for card in sibling_cards:
            sibling_package.append({
                "card": card,
                "text": sibling_text_map.get(card.get("id", ""), "")
            })

        child_package = []
        for card in child_cards:
            child_package.append({
                "card": card,
                "text": child_text_map.get(card.get("id", ""), "")
            })

        return f"""【论文主题】
{topic}

【当前写作目标】
{goal}

【当前节点卡片】
{json.dumps(target_node_card, ensure_ascii=False, indent=2)}

【当前节点正文】
{target_node_text}

【父节点卡片】
{json.dumps(parent_card, ensure_ascii=False, indent=2) if parent_card else ""}

【父节点正文】
{parent_text}

【兄弟节点信息】
{json.dumps(sibling_package, ensure_ascii=False, indent=2)}

【子节点信息】
{json.dumps(child_package, ensure_ascii=False, indent=2)}

【总纲审查意见】
{outline_review_text}
"""

    def check_node_raw(
        self,
        topic: str,
        goal: str,
        target_node_card: dict,
        target_node_text: str,
        parent_card: dict | None = None,
        parent_text: str = "",
        sibling_cards: list[dict] | None = None,
        sibling_text_map: dict | None = None,
        child_cards: list[dict] | None = None,
        child_text_map: dict | None = None,
        outline_review_text: str = ""
    ) -> str:
        user_message = self._build_user_message(
            topic=topic,
            goal=goal,
            target_node_card=target_node_card,
            target_node_text=target_node_text,
            parent_card=parent_card,
            parent_text=parent_text,
            sibling_cards=sibling_cards,
            sibling_text_map=sibling_text_map,
            child_cards=child_cards,
            child_text_map=child_text_map,
            outline_review_text=outline_review_text
        )
        return self.client.chat(
            user_message=user_message,
            system_message=self.system_prompt
        )

    def check_node(
        self,
        topic: str,
        goal: str,
        target_node_card: dict,
        target_node_text: str,
        parent_card: dict | None = None,
        parent_text: str = "",
        sibling_cards: list[dict] | None = None,
        sibling_text_map: dict | None = None,
        child_cards: list[dict] | None = None,
        child_text_map: dict | None = None,
        outline_review_text: str = ""
    ) -> dict:
        raw_text = self.check_node_raw(
            topic=topic,
            goal=goal,
            target_node_card=target_node_card,
            target_node_text=target_node_text,
            parent_card=parent_card,
            parent_text=parent_text,
            sibling_cards=sibling_cards,
            sibling_text_map=sibling_text_map,
            child_cards=child_cards,
            child_text_map=child_text_map,
            outline_review_text=outline_review_text
        )
        return self._safe_json_loads(raw_text, target_node_card=target_node_card)