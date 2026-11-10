"""Load the app config from `config.yaml` and the 511 API key from `.env`."""

import os

import dotenv
import yaml

API_KEY_VAR = "API_511_KEY"


def load_config(path: str) -> dict:
    """The parsed YAML config at `path`."""
    with open(path, encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_api_key() -> str:
    """`API_511_KEY` from the environment, after loading `.env`; raises `RuntimeError` when unset."""
    dotenv.load_dotenv()
    api_key = os.environ.get(API_KEY_VAR)
    if not api_key:
        raise RuntimeError(f"{API_KEY_VAR} is not set; copy .env.example to .env and add your 511 API key")
    return api_key
