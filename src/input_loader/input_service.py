from src.input_loader.file_reader import FileReader
from src.input_loader.pdf_reader import PDFReader
from src.utils.config_loader import ConfigLoader


class InputService:
    def __init__(self):
        self.file_reader = FileReader()
        self.config_loader = ConfigLoader()

        runtime_config = self.config_loader.load_runtime_config()
        paths_config = self.config_loader.load_paths_config()

        max_pages = runtime_config["pdf"]["max_pages"]

        self.topic_dir = paths_config["input"]["topic_dir"]
        self.goal_dir = paths_config["input"]["goal_dir"]
        self.materials_dir = paths_config["input"]["materials_dir"]

        self.pdf_reader = PDFReader(max_pages=max_pages)

    def load_all_inputs(self) -> dict:
        topic = self.file_reader.read_input(self.topic_dir)
        goal = self.file_reader.read_input(self.goal_dir)
        materials = self.pdf_reader.read_materials(self.materials_dir)

        return {
            "topic": topic,
            "goal": goal,
            "materials": materials
        }