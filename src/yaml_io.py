"""
Carregamento de arquivos YAML e resolução de placeholders ${VARIAVEL}
usando valores de um arquivo de secrets.
"""
import re
from pathlib import Path

import yaml

PLACEHOLDER_RE = re.compile(r"\$\{([A-Z0-9_]+)\}")


def load_yaml(path: Path):
    """Lê um arquivo YAML e devolve um dict (ou {} se o arquivo estiver vazio)."""
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def resolve_placeholders(value, secrets):
    """
    Substitui recursivamente qualquer ${CHAVE} encontrada em strings
    (dentro de dicts, listas ou strings soltas) pelo valor correspondente
    em `secrets`. Chaves sem correspondência em secrets são mantidas como
    estão (ex: "${RESUME_X}" continua "${RESUME_X}" se não existir em secrets).
    """
    if isinstance(value, dict):
        return {k: resolve_placeholders(v, secrets) for k, v in value.items()}

    if isinstance(value, list):
        return [resolve_placeholders(v, secrets) for v in value]

    if isinstance(value, str):
        def repl(match):
            key = match.group(1)
            return str(secrets.get(key, match.group(0)))
        return PLACEHOLDER_RE.sub(repl, value)

    return value