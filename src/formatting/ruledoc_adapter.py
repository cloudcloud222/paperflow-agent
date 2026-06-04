from ruledoc.formatter import Formatter
from ruledoc.rules import load_rule


class RuleDocAdapter:
    def __init__(self, rule_name: str = "yzu_thesis"):
        self.rule_name = rule_name

    def format_docx(self, input_path: str, output_path: str):
        rule = load_rule(self.rule_name)

        formatter = Formatter(
            input_path=input_path,
            rule=rule,
            output_path=output_path
        )

        formatter.process()