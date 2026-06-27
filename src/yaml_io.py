"""
Carregamento de arquivos YAML, suporte a múltiplos bancos modulares
e resolução de placeholders ${VARIAVEL} usando valores de um arquivo de secrets.
"""
import re
from pathlib import Path
import yaml

PLACEHOLDER_RE = re.compile(r"\$\{([A-Z0-9_]+)\}")


def load_yaml(path: Path):
    """
    Lê um arquivo YAML.

    Se ele não existir, tenta automaticamente a versão em input/sample/,
    permitindo que o projeto funcione logo após o clone.
    """
    if not path.exists():
        sample_path = path.parent / "sample" / path.name
        if sample_path.exists():
            path = sample_path
        else:
            return {}

    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def find_and_load_yaml(input_dir: Path, possible_names: list, target_key: str = None) -> dict | list:
    """
    Função utilitária para evitar repetição de código (DRY).
    Procura por uma lista de nomes possíveis no diretório e extrai a chave desejada.
    """
    for name in possible_names:
        file_path = input_dir / name
        if file_path.exists():
            data = load_yaml(file_path)
            # Se pedirmos uma chave específica (ex: 'skills_bank'), retorna ela ou []
            if target_key:
                return data.get(target_key, [])
            return data
            
    # Fallback caso nenhum arquivo da lista exista
    return [] if target_key else {}


def load_modular_resume(input_dir: Path) -> dict:
    """
    Lê os arquivos YAML modulares da pasta input/ e os combina em um único
    dicionário 'master' unificado na memória de forma modular e limpa.
    """
    master = {}

    # 1. Carrega dados estruturais e introduções (Retorna o dict inteiro)
    descriptions = find_and_load_yaml(input_dir, ["description.yaml", "descriptions.yaml"])
    master.update(descriptions)

    # 2. Carrega as competências técnicas
    master["skills_bank"] = find_and_load_yaml(
        input_dir, ["skills.yaml", "competence.yaml", "competences.yaml"], "skills_bank"
    )

    # 3. Carrega o histórico de experiências
    master["experience_bank"] = find_and_load_yaml(
        input_dir, ["experience.yaml", "experiences.yaml"], "experience_bank"
    )

    # 4. Carrega as formações principais e complementares do mesmo arquivo
    education_data = find_and_load_yaml(input_dir, ["education.yaml", "educations.yaml"])
    master["education_bank"] = education_data.get("education_bank", [])
    master["extra_education_bank"] = education_data.get("extra_education_bank", [])

    return master

def resolve_placeholders(value, secrets):
    """
    Substitui recursivamente qualquer ${CHAVE} encontrada em strings
    (dentro de dicts, listas os strings soltas) pelo valor correspondente
    em `secrets`.
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