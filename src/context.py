"""
Monta o contexto final (dict) que é passado ao template Jinja: transforma
os dados já filtrados pela seleção (description, keyskills, body) nas
estruturas que o template.html espera (competency_blocks, body_sections,
contacts, description_paragraphs). Suporta tradução automática para o Inglês.
"""
from contacts import build_contacts
from text_utils import bullets_from_text, split_description
from deep_translator import GoogleTranslator

# Mapeamento de títulos de seções comuns para manter uma tradução perfeita e padronizada
SECTION_NAMES_MAP = {
    "Experiência": "Experience",
    "Educação": "Education",
    "Formação": "Education",
    "Certificações": "Certifications",
    "Cursos": "Courses",
    "Habilidades": "Skills",
    "Competências": "Skills"
}

def translate_text(text, target="en"):
    """Auxiliar para traduzir textos simples de forma segura."""
    if not text or not isinstance(text, str):
        return text
    try:
        return GoogleTranslator(source='auto', target=target).translate(text)
    except Exception as e:
        print(f"Erro ao traduzir '{text[:20]}...': {e}")
        return text


def build_competency_blocks(data, to_eng=False):
    """
    Lê os grupos de competências e opcionalmente traduz seus títulos.
    """
    raw = data.get("keyskills", []) or []
    blocks = []
    for group in raw:
        if not isinstance(group, dict):
            continue
        title = (group.get("title") or "").strip()
        items = [item for item in (group.get("items") or []) if item]
        
        if title and items:
            if to_eng:
                title = translate_text(title, "en")
                # Traduz itens de competência apenas se não forem termos puramente técnicos
                # Geralmente nomes de ferramentas (Python, SQL) não mudam, mas "Excel Avançado" vira "Advanced Excel"
                items = [translate_text(item, "en") for item in items]
                
            blocks.append({"title": title, "items": items})
    return blocks


def build_body_sections(body, to_eng=False):
    """
    Transforma o dict `body` e opcionalmente traduz cargos, nomes de empresas/projetos,
    e as descrições em formato de texto antes do parser rodar.
    """
    sections = []

    for section_name, entries in (body or {}).items():
        if not entries:
            continue

        # Traduz o nome da Seção (ex: Experiência -> Experience)
        if to_eng:
            section_name = SECTION_NAMES_MAP.get(section_name, translate_text(section_name, "en"))

        normalized_entries = []
        for entry in entries:
            entry = dict(entry)
            
            if to_eng:
                if "title" in entry:
                    entry["title"] = translate_text(entry["title"], "en")
                if "company" in entry:
                    # Traduz termos como "Projeto de Extensão" mas evita traduzir nomes próprios como "UERJ"
                    entry["company"] = translate_text(entry["company"], "en")
                if "description" in entry:
                    entry["description"] = translate_text(entry["description"], "en")

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


def prepare_context(data, to_eng=False):
    """
    Ponto de entrada do módulo: recebe o dict filtrado e opcionalmente traduz 
    todos os textos dinâmicos para o inglês antes de montar o contexto do Jinja.
    """
    ctx = dict(data)

    if to_eng:
        # Traduz o cargo principal (ex: Engenheiro de Dados -> Data Engineer)
        if "title" in ctx:
            ctx["title"] = translate_text(ctx["title"], "en")
        # Traduz o resumo profissional
        if "description" in ctx:
            ctx["description"] = translate_text(ctx["description"], "en")

    ctx["description_paragraphs"] = split_description(ctx.get("description", ""))
    ctx["competency_blocks"] = build_competency_blocks(ctx, to_eng=to_eng)
    ctx["body_sections"] = build_body_sections(ctx.get("body", {}), to_eng=to_eng)
    ctx["contacts"] = build_contacts(ctx)

    return ctx