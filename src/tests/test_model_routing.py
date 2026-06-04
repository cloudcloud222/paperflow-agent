from src.llm.client import DeepSeekClient

components = [
    "planner",
    "organizer",
    "writer",
    "reviewer",
    "reviser",
    "literature_summarizer"
]

for name in components:
    client = DeepSeekClient(component_name=name)
    print(f"{name} -> provider={client.provider_name}, model={client.model_name}, base_url={client.base_url}")