from typing import List, Dict, Any


class NodeContextBuilder:
    def __init__(
        self,
        max_parent_chars: int = 1200,
        max_sibling_chars: int = 1800,
        max_ancestor_chars: int = 800,
        max_total_chars: int = 3200,
        max_previous_siblings: int = 2
    ):
        self.max_parent_chars = max_parent_chars
        self.max_sibling_chars = max_sibling_chars
        self.max_ancestor_chars = max_ancestor_chars
        self.max_total_chars = max_total_chars
        self.max_previous_siblings = max_previous_siblings

    def _truncate(self, text: str, max_chars: int) -> str:
        if not text:
            return ""
        text = text.strip()
        if len(text) <= max_chars:
            return text
        return text[:max_chars].rstrip() + "……"

    def _build_card_index(self, all_cards: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        return {card.get("id", ""): card for card in all_cards if card.get("id")}

    def _get_ancestors(
        self,
        node_card: Dict[str, Any],
        card_index: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        ancestors = []
        current_parent_id = node_card.get("parent_id")

        while current_parent_id:
            parent_card = card_index.get(current_parent_id)
            if not parent_card:
                break
            ancestors.append(parent_card)
            current_parent_id = parent_card.get("parent_id")

        ancestors.reverse()
        return ancestors

    def _get_previous_siblings(
        self,
        node_card: Dict[str, Any],
        all_cards: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        parent_id = node_card.get("parent_id")
        node_id = node_card.get("id")

        same_level_cards = [c for c in all_cards if c.get("parent_id") == parent_id]

        previous = []
        for c in same_level_cards:
            if c.get("id") == node_id:
                break
            previous.append(c)

        if not previous:
            return []

        return previous[-self.max_previous_siblings:]

    def build_context_text(
        self,
        topic: str,
        goal: str,
        node_card: Dict[str, Any],
        all_cards: List[Dict[str, Any]],
        polished_map: Dict[str, str]
    ) -> str:
        card_index = self._build_card_index(all_cards)
        ancestors = self._get_ancestors(node_card, card_index)
        previous_siblings = self._get_previous_siblings(node_card, all_cards)

        parts = []

        parts.append(f"【当前论文主题】\n{topic}")
        parts.append(f"【当前写作目标】\n{goal}")

        display_title = node_card.get("display_title", "")
        node_goal = node_card.get("goal", "")
        node_type = node_card.get("node_type", "")
        node_path = node_card.get("path", "")
        key_points = node_card.get("key_points", [])

        current_info_lines = [
            f"节点标题：{display_title}",
            f"节点类型：{node_type}",
            f"节点路径：{node_path}",
            f"节点目标：{node_goal}",
        ]
        if key_points:
            current_info_lines.append("核心要点：")
            current_info_lines.extend([f"- {kp}" for kp in key_points])

        parts.append("【当前节点信息】\n" + "\n".join(current_info_lines))

        if ancestors:
            ancestor_titles = " > ".join([a.get("display_title", "") for a in ancestors])
            parts.append(
                "【祖先节点链】\n" +
                self._truncate(ancestor_titles, self.max_ancestor_chars)
            )

            parent_card = ancestors[-1]
            parent_title = parent_card.get("display_title", "")
            parent_goal = parent_card.get("goal", "")
            parent_text = polished_map.get(parent_card.get("id", ""), "")

            parent_lines = [f"父节点：{parent_title}"]
            if parent_goal:
                parent_lines.append(f"父节点目标：{parent_goal}")
            if parent_text:
                parent_lines.append("父节点已写正文：")
                parent_lines.append(self._truncate(parent_text, self.max_parent_chars))

            parts.append("【父节点上下文】\n" + "\n".join(parent_lines))

        if previous_siblings:
            sibling_lines = []
            for sibling in previous_siblings:
                sibling_title = sibling.get("display_title", "")
                sibling_text = polished_map.get(sibling.get("id", ""), "")
                sibling_lines.append(f"兄弟节点：{sibling_title}")
                if sibling_text:
                    sibling_lines.append(self._truncate(sibling_text, self.max_sibling_chars // max(len(previous_siblings), 1)))
                sibling_lines.append("")

            parts.append("【前序兄弟节点上下文】\n" + "\n".join(sibling_lines).strip())

        child_ids = node_card.get("children_ids", [])
        if child_ids:
            parts.append("【子节点提示】\n该节点存在下级节点，当前正文应偏向总述、框架说明与承接，不宜过早写死所有细节。")

        context_text = "\n\n".join([p for p in parts if p.strip()])

        return self._truncate(context_text, self.max_total_chars)

    def build_context_package(
        self,
        topic: str,
        goal: str,
        node_card: Dict[str, Any],
        all_cards: List[Dict[str, Any]],
        polished_map: Dict[str, str]
    ) -> Dict[str, Any]:
        context_text = self.build_context_text(
            topic=topic,
            goal=goal,
            node_card=node_card,
            all_cards=all_cards,
            polished_map=polished_map
        )

        return {
            "node_id": node_card.get("id", ""),
            "display_title": node_card.get("display_title", ""),
            "context_text": context_text,
            "context_chars": len(context_text)
        }