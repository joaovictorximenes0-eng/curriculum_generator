from pathlib import Path
import re
import sys
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
OUTPUT_DIR = BASE_DIR / "output"

MASTER_RESUME = INPUT_DIR / "master_resume.yaml"
SELECTION = INPUT_DIR / "selection.yaml"
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


# =============================================================================
# CAMADA DE SELEÇÃO (banco de dados -> currículo filtrado)
# =============================================================================
# Estas funções pegam o "banco" completo (skills_bank, experience_bank,
# education_bank, description_bank) e o arquivo selection.yaml, e devolvem
# exatamente a mesma estrutura `keyskills` / `body` que o código antigo
# já sabia consumir — então o resto do pipeline (build_competency_blocks,
# build_body_sections, etc.) não precisa mudar nada.
# =============================================================================

def index_by_id(items):
    """Transforma uma lista de dicts com `id` num dicionário id -> item."""
    return {item["id"]: item for item in (items or []) if item.get("id")}


def warn_missing(kind, item_id):
    print(f"[selection] aviso: {kind} com id '{item_id}' não encontrado no master_resume.yaml — ignorado.", file=sys.stderr)


def resolve_description(master, selection):
    bank = index_by_id(master.get("description_bank"))
    desc_id = selection.get("description_id")

    if desc_id and desc_id in bank:
        return bank[desc_id].get("text", "")

    if desc_id:
        warn_missing("description", desc_id)

    # Fallback: primeira descrição do banco, se existir.
    if bank:
        return next(iter(bank.values())).get("text", "")
    return ""


def resolve_skills(master, selection):
    """
    Devolve no formato `keyskills` (lista de grupos {title, items}) que
    build_competency_blocks já consome, mas só com as skills selecionadas,
    agrupadas na ordem em que cada grupo aparece pela primeira vez na
    seleção.
    """
    bank = index_by_id(master.get("skills_bank"))
    selected_ids = selection.get("skills") or []

    groups_order = []
    groups = {}

    for skill_id in selected_ids:
        skill = bank.get(skill_id)
        if not skill:
            warn_missing("skill", skill_id)
            continue
        group_title = skill.get("group", "Outros")
        if group_title not in groups:
            groups[group_title] = []
            groups_order.append(group_title)
        groups[group_title].append(skill.get("name", ""))

    return [{"title": title, "items": groups[title]} for title in groups_order]


def resolve_experiences(master, selection):
    """
    Devolve a lista de entries no formato que build_body_sections espera
    dentro de body['Experience']: cada item com title/company/start/end/
    description (texto com bullets unidos por linha, no formato "- texto"
    para reaproveitar bullets_from_text).
    """
    bank = index_by_id(master.get("experience_bank"))
    selected = selection.get("experiences") or []

    entries = []
    for item in selected:
        exp_id = item.get("id") if isinstance(item, dict) else item
        exp = bank.get(exp_id)
        if not exp:
            warn_missing("experience", exp_id)
            continue

        bullets_bank = {b["id"]: b for b in (exp.get("bullets") or []) if b.get("id")}
        wanted = item.get("bullets") if isinstance(item, dict) else "all"

        if wanted == "all" or wanted is None:
            chosen_bullets = [b.get("text", "") for b in (exp.get("bullets") or [])]
        else:
            chosen_bullets = []
            for bullet_id in wanted:
                bullet = bullets_bank.get(bullet_id)
                if not bullet:
                    warn_missing(f"bullet (em {exp_id})", bullet_id)
                    continue
                chosen_bullets.append(bullet.get("text", ""))

        description_text = "\n".join(f"- {t}" for t in chosen_bullets if t)

        entries.append({
            "start": exp.get("start", ""),
            "end": exp.get("end", ""),
            "title": exp.get("title", ""),
            "company": exp.get("company", ""),
            "description": description_text,
        })

    return entries


def resolve_education(master, selection):
    bank = index_by_id(master.get("education_bank"))
    selected_ids = selection.get("education") or []

    entries = []
    for edu_id in selected_ids:
        edu = bank.get(edu_id)
        if not edu:
            warn_missing("education", edu_id)
            continue
        entries.append({
            "start": edu.get("start", ""),
            "end": edu.get("end", ""),
            "title": edu.get("title", ""),
            "company": edu.get("company", ""),
            "description": edu.get("description", ""),
        })

    return entries


def apply_selection(master, selection):
    """
    Recebe o banco completo (master_resume.yaml) e a seleção (selection.yaml)
    já resolvidos (placeholders aplicados), e devolve um dict no MESMO
    formato que o pipeline antigo usava (description, keyskills, body),
    para que build_competency_blocks/build_body_sections funcionem sem
    alteração.
    """
    resolved = dict(master)

    resolved["description"] = resolve_description(master, selection)
    resolved["keyskills"] = resolve_skills(master, selection)
    resolved["body"] = {
        "Experience": resolve_experiences(master, selection),
        "Education": resolve_education(master, selection),
    }

    # Os bancos não são mais necessários no contexto final do template.
    for key in ("description_bank", "skills_bank", "experience_bank", "education_bank"):
        resolved.pop(key, None)

    return resolved


# =============================================================================
# PIPELINE PRÉ-EXISTENTE (sem alterações de comportamento)
# =============================================================================

def build_competency_blocks(data):
    """
    Lê os grupos de competências já filtrados pela seleção (chave
    `keyskills`, no formato lista de {title, items}).
    """
    raw = data.get("keyskills", []) or []
    blocks = []
    for group in raw:
        if not isinstance(group, dict):
            continue
        title = (group.get("title") or "").strip()
        items = [item for item in (group.get("items") or []) if item]
        if title and items:
            blocks.append({"title": title, "items": items})
    return blocks


# Ícones SVG monocromáticos (herdam a cor do texto via fill="currentColor"),
# estilo outline simples, viewBox 24x24.
CONTACT_ICONS = {
    "address": '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 21s-7-7.2-7-12a7 7 0 1 1 14 0c0 4.8-7 12-7 12Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><circle cx="12" cy="9" r="2.4" stroke="currentColor" stroke-width="1.6"/></svg>',
    "phone": '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M6.6 10.8c1.3 2.6 3.4 4.7 6 6l2-2c.3-.3.7-.4 1.1-.3 1.2.4 2.5.6 3.8.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.6 21 3 13.4 3 4c0-.6.4-1 1-1h3.9c.6 0 1 .4 1 1 0 1.3.2 2.6.6 3.8.1.4 0 .8-.3 1.1l-2 2Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>',
    "email": '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="5" width="18" height="14" rx="2" stroke="currentColor" stroke-width="1.6"/><path d="m4 7 8 6 8-6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "linkedin": '<svg viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg"><path d="M6.94 5a2 2 0 1 1-4 0 2 2 0 0 1 4 0ZM3.2 8.75h3.5V21H3.2V8.75ZM9.5 8.75h3.35v1.68h.05c.47-.88 1.6-1.8 3.3-1.8 3.53 0 4.18 2.32 4.18 5.35V21h-3.5v-5.66c0-1.35-.02-3.08-1.88-3.08-1.88 0-2.17 1.47-2.17 2.98V21H9.5V8.75Z"/></svg>',
    "github": '<svg viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.48 2 2 6.58 2 12.2c0 4.49 2.87 8.3 6.84 9.64.5.1.68-.22.68-.49 0-.24-.01-1.04-.01-1.88-2.78.61-3.37-1.21-3.37-1.21-.46-1.18-1.11-1.5-1.11-1.5-.91-.63.07-.62.07-.62 1 .07 1.53 1.04 1.53 1.04.89 1.55 2.34 1.1 2.91.84.09-.66.35-1.1.63-1.36-2.22-.26-4.56-1.13-4.56-5.03 0-1.11.39-2.02 1.03-2.73-.1-.26-.45-1.3.1-2.71 0 0 .84-.27 2.75 1.04a9.3 9.3 0 0 1 5 0c1.91-1.31 2.75-1.04 2.75-1.04.55 1.41.2 2.45.1 2.71.64.71 1.03 1.62 1.03 2.73 0 3.91-2.34 4.77-4.57 5.02.36.32.68.94.68 1.9 0 1.37-.01 2.47-.01 2.81 0 .27.18.6.69.49A10.02 10.02 0 0 0 22 12.2C22 6.58 17.52 2 12 2Z"/></svg>',
}


def build_contacts(ctx):
    """
    Monta a lista de itens de contato exibidos na barra superior, cada um
    com {key, icon (svg), text, href (opcional)}.

    Apenas LinkedIn e GitHub viram hyperlink, e a URL é sempre exibida por
    extenso (nunca abreviada). Os demais mostram só ícone + texto.
    Itens sem valor no YAML são omitidos automaticamente.
    """
    contacts = []

    address = ctx.get("address")
    if isinstance(address, list):
        address_text = ", ".join(a for a in address if a)
    else:
        address_text = address or ""
    if address_text:
        contacts.append({"key": "address", "icon": CONTACT_ICONS["address"], "text": address_text, "href": None})

    phone = ctx.get("phone")
    if phone:
        contacts.append({"key": "phone", "icon": CONTACT_ICONS["phone"], "text": phone, "href": None})

    email = ctx.get("email")
    if email:
        contacts.append({"key": "email", "icon": CONTACT_ICONS["email"], "text": email, "href": None})

    linkedin = ctx.get("linkedin")
    if linkedin:
        href = linkedin if linkedin.startswith("http") else f"https://www.linkedin.com/{linkedin.lstrip('/')}"
        contacts.append({"key": "linkedin", "icon": CONTACT_ICONS["linkedin"], "text": href, "href": href})

    github = ctx.get("github")
    if github:
        href = github if github.startswith("http") else f"https://github.com/{github.lstrip('/')}"
        contacts.append({"key": "github", "icon": CONTACT_ICONS["github"], "text": href, "href": href})

    return contacts


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
    ctx["contacts"] = build_contacts(ctx)

    return ctx


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