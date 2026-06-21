"""
Camada de seleção: pega o "banco" completo (master_resume.yaml, com
description_bank / skills_bank / experience_bank / education_bank) e o
arquivo selection.yaml (lista de ids escolhidos), e devolve um dict no
formato "currículo pronto" (description, keyskills, body) que o resto do
pipeline (veja context.py) já sabe consumir.

Para montar um currículo diferente, edite apenas selection.yaml — nada
aqui precisa mudar.
"""
import sys


def index_by_id(items):
    """Transforma uma lista de dicts com `id` num dicionário id -> item."""
    return {item["id"]: item for item in (items or []) if item.get("id")}


def warn_missing(kind, item_id):
    print(
        f"[selection] aviso: {kind} com id '{item_id}' não encontrado "
        f"no master_resume.yaml — ignorado.",
        file=sys.stderr,
    )


def resolve_description(master, selection):
    """Escolhe o texto de headline a partir de description_bank + description_id."""
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
    Devolve a lista de grupos de skills (formato {title, items}) já filtrada
    pela seleção, agrupadas na ordem em que cada grupo aparece pela
    primeira vez na lista `skills` de selection.yaml.
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
    Devolve a lista de experiências filtradas, no formato esperado por
    build_body_sections (start/end/title/company/description), onde
    `description` é o texto com bullets já unidos (um por linha, prefixo
    "- ") prontos para bullets_from_text.

    Cada item de selection["experiences"] pode escolher bullets específicos
    (lista de ids) ou usar bullets: "all" para incluir todos.
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
    """Devolve a lista de formações filtradas, na ordem de selection["education"]."""
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


def resolve_extra_education(master, selection):
    """
    Devolve a lista de formações complementares (cursos rápidos, palestras,
    workshops) filtradas pela seleção, na ordem de
    selection["extra_education"]. Cada item já vem pronto no formato
    {title, institution, year} usado diretamente pelo template.
    """
    bank = index_by_id(master.get("extra_education_bank"))
    selected_ids = selection.get("extra_education") or []

    entries = []
    for item_id in selected_ids:
        item = bank.get(item_id)
        if not item:
            warn_missing("extra_education", item_id)
            continue
        entries.append({
            "title": item.get("title", ""),
            "institution": item.get("institution", ""),
            "year": item.get("year", ""),
        })

    return entries


def apply_selection(master, selection):
    """
    Ponto de entrada do módulo: recebe o banco completo e a seleção (ambos
    já com placeholders resolvidos) e devolve um dict no formato "currículo
    pronto" (description, keyskills, body), no mesmo formato que o pipeline
    de contexto (context.py) já sabe consumir.
    """
    resolved = dict(master)

    resolved["description"] = resolve_description(master, selection)
    resolved["keyskills"] = resolve_skills(master, selection)
    resolved["body"] = {
        "Experience": resolve_experiences(master, selection),
        "Education": resolve_education(master, selection),
    }
    resolved["extra_education"] = resolve_extra_education(master, selection)

    # Os bancos não são mais necessários no contexto final do template.
    for key in ("description_bank", "skills_bank", "experience_bank", "education_bank", "extra_education_bank"):
        resolved.pop(key, None)

    return resolved