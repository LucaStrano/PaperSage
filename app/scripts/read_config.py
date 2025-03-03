import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
from app.config_loader import ConfigLoader

configs = ConfigLoader().get_config()
try:
    print(f"OLLAMA_EMB_MODEL='{configs['embedding_config']['model']}'")
    print(f"CHAINLIT_HOST='{configs['chainlit_config']['host']}'")
    print(f"CHAINLIT_PORT='{configs['chainlit_config']['port']}'")
except Exception as e:
    print(f"Error reading configs: {e}", file=sys.stderr)
    sys.exit(1)
