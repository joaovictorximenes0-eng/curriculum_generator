"""
Camada de seleção inteligente: analisa o banco completo do master_resume.yaml
contra o texto de uma vaga de emprego (vaga.txt). 

Aplica uma pontuação combinada de relevância técnica (Tiers) e correspondência 
de palavras-chave (Match), limitando os resultados ao "número mágico" físico
para garantir um layout A4 perfeito.
"""
import sys



# --- LIMITES RÍGIDOS PARA O LAYOUT A4 PERFEITO ---
MAX_EXPERIENCES = 3
MAX_SKILLS = 15
MAX_EXTRA_EDUCATION = 2


def get_item_tier_weight(name, tags, master_data):
    """
    Descobre o peso do item buscando suas tags ou nome dentro do 'tier_config'
    que agora foi movido para o YAML.
    """
    # Busca a configuração que mudamos para o YAML. Se não existir, usa um fallback seguro
    tier_config = master_data.get("tier_config", {})
    
    # Se não houver configuração nenhuma no YAML, mantém os pesos padrão
    t1 = tier_config.get("tier_1", ["java", "python", "mysql", "sql", "dados", "backend"])
    t2 = tier_config.get("tier_2", ["docker", "git", "linux", "html", "automação"])
    t3 = tier_config.get("tier_3", ["photoshop", "design", "ui/ux"])
    
    tokens = [name.lower()] + [t.lower() for t in (tags or [])]
    
    max_w = 5  # Fallback padrão (Tier 4)
    for token in tokens:
        for t_word in t1:
            if t_word in token: return 50
        for t_word in t2:
            if t_word in token: return 35
        for t_word in t3:
            if t_word in token: return 20
            
    return max_w


def calculate_match_score(vaga_lower, name, tags):
    """Calcula quantos pontos o item ganha baseado no texto da vaga."""
    if not vaga_lower:
        return 0
    
    score = 0
    # Match direto no nome (ex: "Power BI" contido no texto da vaga)
    if name.lower() in vaga_lower:
        score += 100
        
    # Match nas tags associadas
    for tag in (tags or []):
        if tag.lower() in vaga_lower:
            score += 40
            
    return score


def resolve_description(master, vaga_lower):
    """Escolhe a melhor introdução profissional baseada no foco da vaga."""
    bank = master.get("description_bank") or []
    if not bank:
        return ""
    
    best_desc = bank[0].get("text", "")
    max_score = -1
    
    for desc in bank:
        # Se o ID da descrição der match com o contexto geral da vaga
        # Ex: desc_dev ganha pontos se a vaga falar em 'dev', 'desenvolvedor', 'software'
        score = calculate_match_score(vaga_lower, desc.get("id", ""), [desc.get("text", "")])
        if score > max_score:
            max_score = score
            best_desc = desc.get("text", "")
            
    return best_desc


def resolve_skills(master, vaga_lower):
    """
    Seleciona as competências. Grupos VIPs (como Idiomas) cortam a fila,
    não consomem o limite do MAX_SKILLS e são jogados para o final do bloco.
    """
    bank = master.get("skills_bank") or []
    always_include = master.get("always_include_groups", ["Idiomas"])
    
    mandatory_skills = []
    pool_skills = []
    
    # 1. Triagem Inicial
    for skill in bank:
        group = skill.get("group", "Outros")
        
        if group in always_include:
            mandatory_skills.append(skill)
        else:
            name = skill.get("name", "")
            tags = skill.get("tags", [])
            
            tier_weight = get_item_tier_weight(name, tags, master)
            match_score = calculate_match_score(vaga_lower, name, tags)
            final_score = match_score + tier_weight
            
            pool_skills.append({
                "skill": skill,
                "score": final_score,
                "group": group
            })
            
    # 2. Ordena o pool técnico restante por relevância
    pool_skills.sort(key=lambda x: x["score"], reverse=True)
    
    # 3. Seleção: Techs entram primeiro e as Mandatórias (Idiomas) fecham a lista!
    selected_pool = [item["skill"] for item in pool_skills[:MAX_SKILLS]]
    final_selection = selected_pool + mandatory_skills  # 👈 Invertido aqui!
    
    print(f"[selection] Total renderizado: {len(final_selection)} (Techs: {len(selected_pool)} | VIPs: {len(mandatory_skills)})")
    
    # 4. Agrupa para o Jinja2 manter a ordem correta dos blocos no HTML
    groups_order = []
    groups = {}
    for skill in final_selection:
        g_title = skill.get("group", "Outros")
        if g_title not in groups:
            groups[g_title] = []
            groups_order.append(g_title)
        groups[g_title].append(skill.get("name", ""))
        
    return [{"title": title, "items": groups[title]} for title in groups_order]

def resolve_experiences(master, vaga_lower):
    """Escolhe as 3 melhores experiências com base nos matches dos sub-bullets e tags."""
    bank = master.get("experience_bank") or []
    scored_exps = []
    
    for exp in bank:
        exp_tags = exp.get("tags", [])
        title = exp.get("title", "")
        company = exp.get("company", "")
        
        # Score base da experiência
        exp_score = calculate_match_score(vaga_lower, f"{title} {company}", exp_tags)
        
        # Analisa os sub-bullets internos para somar pontos na experiência
        bullets_data = exp.get("bullets") or []
        chosen_bullets = []
        
        for b in bullets_data:
            b_text = b.get("text", "")
            b_tags = b.get("tags", [])
            b_score = calculate_match_score(vaga_lower, b_text, b_tags)
            
            # Se não houver vaga especificada, todos os bullets são válidos
            chosen_bullets.append((b_score, b_text))
            exp_score += b_score
            
        # Ordena os bullets internos por relevância com a vaga e limpa pontuações
        chosen_bullets.sort(key=lambda x: x[0], reverse=True)
        final_bullets_text = [b[1] for b in chosen_bullets]
        
        description_text = "\n".join(f"- {t}" for t in final_bullets_text if t)
        
        exp_dinamica = exp.copy() 
        exp_dinamica["description"] = description_text  # Atualiza ou injeta a descrição filtrada
        if "bullets" in exp_dinamica: 
            del exp_dinamica["bullets"] # Limpa os bullets brutos para não inflar o HTML à toa
        
        scored_exps.append({
            "score": exp_score,
            "data": exp_dinamica # Passa o dicionário completo com QUALQUER chave que você criar no YAML
        })
        
    # Ordena as experiências: Matches de vaga primeiro
    scored_exps.sort(key=lambda x: x["score"], reverse=True)
    
    # O CORTADOR MÁGICO: Garante rigorosamente no máximo 3 experiências na folha
    return [item["data"] for item in scored_exps[:MAX_EXPERIENCES]]


def resolve_extra_education(master, vaga_lower):
    """Filtra cursos complementares mais pertinentes para a oportunidade."""
    bank = master.get("extra_education_bank") or []
    scored_courses = []
    
    for item in bank:
        title = item.get("title", "")
        tags = item.get("tags", [])
        score = calculate_match_score(vaga_lower, title, tags) + get_item_tier_weight(title, tags,master)
        
        scored_courses.append({
            "score": score,
            "year": item.get("year", ""),
            "data": {
                "title": title,
                "institution": item.get("institution", ""),
                "year": item.get("year", ""),
            }
        })
        
    # Ordena por score e usa o ano como desempate (mais novos primeiro)
    scored_courses.sort(key=lambda x: (x["score"], x["year"]), reverse=True)
    return [c["data"] for c in scored_courses[:MAX_EXTRA_EDUCATION]]


def apply_selection(master, vaga_text):
    """
    Ponto de entrada do módulo: Substitui o antigo selection.yaml.
    Gera dinamicamente o currículo baseado na análise textual da vaga.
    """
    vaga_lower = vaga_text.lower().strip() if vaga_text else ""
    resolved = dict(master)

    # Processamento Inteligente Automatizado
    resolved["description"] = resolve_description(master, vaga_lower)
    resolved["keyskills"] = resolve_skills(master, vaga_lower)
    
    # Montagem das seções estruturais
    resolved["body"] = {
        "Experience": resolve_experiences(master, vaga_lower),
        # Formação Acadêmica Principal sempre entra completa (visto que são poucas e vitais)
        "Education": [edu.copy() for edu in (master.get("education_bank") or [])],
    }
    resolved["extra_education"] = resolve_extra_education(master, vaga_lower)

    # Limpeza de memória dos bancos brutos
    for key in ("description_bank", "skills_bank", "experience_bank", "education_bank", "extra_education_bank"):
        resolved.pop(key, None)

    return resolved