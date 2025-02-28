import yaml

def get_config():
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
        chainlit_config = config['configs'][0]['chainlit_config']
        host = chainlit_config[0]['host']
        port = chainlit_config[1]['port']
        ollama_emb_model = config['configs'][2]['embedding_config'][0]['model']
        return host, port, ollama_emb_model

if __name__ == "__main__":
    host, port, olama_emb_model = get_config()
    print(f"export CHAINLIT_HOST={host}")
    print(f"export CHAINLIT_PORT={port}")
    print(f"export OLLAMA_EMB_MODEL={olama_emb_model}")
