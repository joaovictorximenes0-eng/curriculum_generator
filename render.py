"""
Ponto de entrada: lê os YAMLs de entrada, aplica a seleção, monta o
contexto e renderiza o template HTML final.

Toda a lógica fica modularizada em src/ — este arquivo só orquestra a
ordem das chamadas. Veja:
    src/yaml_io.py    -> carregar YAML e resolver ${PLACEHOLDERS}
    src/selection.py  -> filtrar o banco (master_resume.yaml) pela seleção
    src/context.py    -> montar o contexto final para o template
    src/contacts.py   -> lista de contatos (usa src/icons.py)
    src/icons.py      -> registro de ícones SVG por tipo de contato
    src/text_utils.py -> utilitários de texto (parágrafos/bullets)
"""
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input"
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
SRC_DIR = BASE_DIR / "src"

sys.path.insert(0, str(SRC_DIR))

from yaml_io import load_yaml, resolve_placeholders  # noqa: E402
from selection import apply_selection  # noqa: E402
from context import prepare_context  # noqa: E402

MASTER_RESUME = INPUT_DIR / "master_resume.yaml"
SELECTION = INPUT_DIR / "selection.yaml"
SECRETS = INPUT_DIR / "secrets.yaml"
OUTPUT_HTML = OUTPUT_DIR / "resume.html"
TEMPLATE_NAME = "template.html"


def main():
    master_raw = load_yaml(MASTER_RESUME)
    selection_raw = load_yaml(SELECTION)
    secrets = load_yaml(SECRETS)

    master = resolve_placeholders(master_raw, secrets)
    selection = resolve_placeholders(selection_raw, secrets)

    filtered = apply_selection(master, selection)
    context = prepare_context(filtered)

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template = env.get_template(TEMPLATE_NAME)
    html = template.render(**context)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"HTML gerado em: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()