from pathlib import Path
import re
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
OUTPUT_DIR = BASE_DIR / "output"

MASTER_RESUME = INPUT_DIR / "master_resume.yaml"
SECRETS = INPUT_DIR / "secrets.yaml"
OUTPUT_HTML = OUTPUT_DIR / "resume.html"
TEMPLATE_NAME = "template.html"

PLACEHOLDER_RE = re.compile(r"\$\{([A-Z0-9_]+)\}")


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def resolve_placeholders(value, secrets):
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


def split_description(text: str):
    text = (text or "").strip()
    if not text:
        return []
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    return parts or [text]


def bullets_from_text(text: str):
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    items = []
    for line in lines:
        if line.startswith("- "):
            items.append(line[2:].strip())
        else:
            items.append(line)
    return items


def build_competency_blocks(data):
    """
    Lê os grupos de competências diretamente do YAML (chave `keyskills`),
    no formato:
        keyskills:
          - title: Python
            items: [Selenium, Pandas, ...]
          - title: Web / Automação
            items: [...]

    Não há mais hardcode aqui: para adicionar, remover ou renomear um
    grupo/skill, edite apenas o master_resume.yaml.

    Mantém compatibilidade com o formato antigo (lista simples de strings)
    agrupando tudo em um único bloco "Competências", caso alguém ainda
    use `keyskills: [Python, Excel, ...]`.
    """
    raw = data.get("keyskills", []) or []

    if not raw:
        return []

    # Formato novo: lista de dicts {title, items}
    if isinstance(raw[0], dict):
        blocks = []
        for group in raw:
            title = group.get("title", "").strip()
            items = [item for item in (group.get("items") or []) if item]
            if title and items:
                blocks.append({"title": title, "items": items})
        return blocks

    # Formato antigo: lista simples de strings -> um único bloco
    items = [s for s in raw if s]
    if not items:
        return []
    return [{"title": "Competências", "items": items}]


def build_body_sections(body):
    sections = []

    for section_name, entries in (body or {}).items():
        if not entries:
            continue

        normalized_entries = []
        for entry in entries:
            entry = dict(entry)
            desc = entry.get("description", "")
            normalized_entries.append({
                **entry,
                "description_items": bullets_from_text(desc) if isinstance(desc, str) else [],
                "description_paragraphs": split_description(desc) if isinstance(desc, str) else [],
            })

        sections.append({
            "name": section_name,
            "entries": normalized_entries,
        })

    return sections


def prepare_context(data):
    ctx = dict(data)

    ctx["description_paragraphs"] = split_description(ctx.get("description", ""))
    ctx["competency_blocks"] = build_competency_blocks(ctx)
    ctx["body_sections"] = build_body_sections(ctx.get("body", {}))

    # Garante que campos de contato opcionais nunca cheguem como None
    # ao template (evita "None" literal aparecendo no HTML, já que o
    # template não usa `is defined`/`default` nesses campos).
    for key in ("linkedin", "github", "email", "web"):
        if ctx.get(key) is None:
            ctx[key] = ""

    return ctx


def main():
    master = load_yaml(MASTER_RESUME)
    secrets = load_yaml(SECRETS)
    resolved = resolve_placeholders(master, secrets)
    context = prepare_context(resolved)

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