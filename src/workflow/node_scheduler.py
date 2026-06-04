from collections import defaultdict


class NodeScheduler:
    def __init__(self):
        pass

    def _build_children_map(self, cards: list[dict]) -> dict[str, list[dict]]:
        children_map = defaultdict(list)
        for card in cards:
            parent_id = card.get("parent_id")
            if parent_id:
                children_map[parent_id].append(card)
        return dict(children_map)

    def _build_card_index(self, cards: list[dict]) -> dict[str, dict]:
        return {card.get("id", ""): card for card in cards if card.get("id")}

    def _sort_cards(self, cards: list[dict]) -> list[dict]:
        def sort_key(card: dict):
            return (
                int(card.get("level", 1)),
                card.get("number", ""),
                card.get("display_title", "")
            )
        return sorted(cards, key=sort_key)

    def _top_down_traverse(self, roots: list[dict], children_map: dict[str, list[dict]]) -> list[dict]:
        ordered = []

        def dfs(card: dict):
            ordered.append(card)
            for child in self._sort_cards(children_map.get(card.get("id", ""), [])):
                dfs(child)

        for root in self._sort_cards(roots):
            dfs(root)

        return ordered

    def _bottom_up_traverse(self, roots: list[dict], children_map: dict[str, list[dict]]) -> list[dict]:
        ordered = []

        def dfs(card: dict):
            for child in self._sort_cards(children_map.get(card.get("id", ""), [])):
                dfs(child)
            ordered.append(card)

        for root in self._sort_cards(roots):
            dfs(root)

        return ordered

    def _hybrid_traverse(self, roots: list[dict], children_map: dict[str, list[dict]]) -> list[dict]:
        """
        hybrid 策略：
        - 顶层章、存在子节点的框架性节点先写
        - 再写其子树中的叶子或低层细节
        - 最后回到该节点做一次“总结型回写”的机会，可以由后续 pipeline 决定是否二次写
        当前 V1 先返回一个单序列：
          父节点 -> 子节点们（递归）
        但顺序比纯 top_down 更强调：
          顶层/框架节点优先，其次细节节点
        """
        ordered = []

        def dfs(card: dict):
            ordered.append(card)

            children = self._sort_cards(children_map.get(card.get("id", ""), []))

            # 先递归有子节点的结构节点，再递归叶子节点
            internal_children = [c for c in children if c.get("has_children", False)]
            leaf_children = [c for c in children if not c.get("has_children", False)]

            for child in internal_children:
                dfs(child)
            for child in leaf_children:
                dfs(child)

        for root in self._sort_cards(roots):
            dfs(root)

        return ordered

    def schedule(self, cards: list[dict], strategy: str = "hybrid", leaf_only: bool = False) -> list[dict]:
        if not cards:
            return []

        card_index = self._build_card_index(cards)
        children_map = self._build_children_map(cards)

        roots = [card for card in cards if not card.get("parent_id") or card.get("parent_id") not in card_index]

        strategy = (strategy or "hybrid").lower()

        if strategy == "top_down":
            ordered = self._top_down_traverse(roots, children_map)
        elif strategy == "bottom_up":
            ordered = self._bottom_up_traverse(roots, children_map)
        else:
            ordered = self._hybrid_traverse(roots, children_map)

        if leaf_only:
            ordered = [card for card in ordered if not card.get("has_children", False)]

        # 去重，避免异常结构重复遍历
        seen = set()
        unique_ordered = []
        for card in ordered:
            node_id = card.get("id", "")
            if node_id in seen:
                continue
            seen.add(node_id)
            unique_ordered.append(card)

        return unique_ordered