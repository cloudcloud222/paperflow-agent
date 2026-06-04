import logging
from pathlib import Path
from src.utils.config_loader import ConfigLoader


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if getattr(logger, "_custom_configured", False):
        return logger

    config_loader = ConfigLoader()
    paths_config = config_loader.load_paths_config()
    logs_dir = Path(paths_config["output"]["logs_dir"])
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_file = logs_dir / "system.log"

    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger._custom_configured = True
    return logger