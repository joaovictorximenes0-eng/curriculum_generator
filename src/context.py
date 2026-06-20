"""
Monta o contexto final (dict) que é passado ao template Jinja: transforma
os dados já filtrados pela seleção (description, keyskills, body) nas
estruturas que o template.html espera (competency_blocks, body_sections,
contacts, description_paragraphs).
"""
from contacts import build_contacts
from text_utils import bullets_from_text, split_description


def build_competency_blocks(data):
    """
    Lê os grupos de competências já filtrados pela seleção (chave
    `keyskills`, no formato lista de {title, items}) e descarta qualquer
    grupo malformado (sem title ou sem items).
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


def build_body_sections(body):
    """
    Transforma o dict `body` (ex: {"Experience": [...], "Education": [...]})
    numa lista de seções, cada entrada já com `description_items`
    (bullets) e `description_paragraphs` (texto corrido) prontos para o
    template escolher qual usar.
    """
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
    """
    Ponto de entrada do módulo: recebe o dict já filtrado pela seleção
    (description, keyskills, body, + campos de contato) e devolve o
    contexto completo pronto para `template.render(**context)`.
    """
    ctx = dict(data)

    ctx["description_paragraphs"] = split_description(ctx.get("description", ""))
    ctx["competency_blocks"] = build_competency_blocks(ctx)
    ctx["body_sections"] = build_body_sections(ctx.get("body", {}))
    ctx["contacts"] = build_contacts(ctx)

    return ctx