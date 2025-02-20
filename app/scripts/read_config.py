import yaml

def get_config():
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
        chainlit_config = config['configs'][0]['chainlit_config']
        host = chainlit_config[0]['host']
        port = chainlit_config[1]['port']
        return host, port

if __name__ == "__main__":
    host, port = get_config()
    print(f"export CHAINLIT_HOST={host}")
    print(f"export CHAINLIT_PORT={port}")
