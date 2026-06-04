from src.utils.config_loader import ConfigLoader

loader = ConfigLoader()
config = loader.load_all()

print("===== models =====")
print(config["models"])

print("\n===== runtime =====")
print(config["runtime"])

print("\n===== paths =====")
print(config["paths"])