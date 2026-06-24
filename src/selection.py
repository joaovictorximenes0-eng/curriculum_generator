"""
Camada de seleção inteligente: analisa o banco completo do master_resume.yaml
contra o texto de uma vaga de emprego (vaga.txt). 

Aplica uma pontuação combinada de relevância técnica (Tiers) e correspondência 
de palavras-chave (Match), limitando os resultados ao "número mágico" físico
para garantir um layout A4 perfeito.
"""
import sys

# --- CONFIGURAÇÃO GLOBAL DE PESOS TÉCNICOS (TIERS) ---
# Evita que ferramentas mundanas como Word roubem o lugar de Java/Python
TIER_WEIGHTS = {
    # Tier 1: Peso Máximo (Core Tech, Engenharia de Dados, Backend)
    "java": 50, "python": 50, "mysql": 50, "pandas": 50, "powerbi": 50, 
    "sql": 50, "backend": 50, "dados": 50, "bi": 50,
    
    # Tier 2: Peso Alto (Infraestrutura, DevOps, Automações e Core Web)
    "docker": 35, "git": 35, "github": 35, "linux": 35, "n8n": 35, 
    "arduino": 35, "esp32": 35, "html": 35, "css": 35, "javascript": 35, 
    "js": 35, "selenium": 35, "pyautogui": 35, "rpa": 35, "automação": 35,
    
    # Tier 3: Peso Médio (Design Gráfico e UI/UX)
    "photoshop": 20, "illustrator": 20, "indesign": 20, "design": 20, "ui/ux": 20,
    
    # Tier 4: Peso Baixo (Utilitários de escritório gerais)
    "word": 5, "powerpoint": 5, "office": 5
}

# --- LIMITES RÍGIDOS PARA O LAYOUT A4 PERFEITO ---
MAX_EXPERIENCES = 3
MAX_SKILLS = 15
MAX_EXTRA_EDUCATION = 2


def get_item_tier_weight(name, tags):
    """Descobre o maior peso em nível associado ao nome ou às tags do elemento."""
    max_w = 5  # Fallback padrão (Tier mais baixo)
    tokens = [name.lower()] + [t.lower() for t in (tags or [])]
    
    for token in tokens:
        for key, weight in TIER_WEIGHTS.items():
            if key in token and weight > max_w:
                max_w = weight
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
    """Seleciona as melhores competências, ordena por relevância e agrupa por seção."""
    bank = master.get("skills_bank") or []
    scored_skills = []
    
    for skill in bank:
        name = skill.get("name", "")
        tags = skill.get("tags", [])
        
        tier_weight = get_item_tier_weight(name, tags)
        match_score = calculate_match_score(vaga_lower, name, tags)
        
        # Pontuação Final: O match tem precedência absoluta, mas o Tier desempata
        final_score = match_score + tier_weight
        
        scored_skills.append({
            "skill": skill,
            "score": final_score,
            "group": skill.get("group", "Outros")
        })
        
    # Ordena do maior score para o menor
    scored_skills.sort(key=lambda x: x["score"], reverse=True)
    
    # Aplica a trava de segurança física de quantidade
    top_skills = scored_skills[:MAX_SKILLS]
    
    # Agrupa mantendo a ordem de relevância dos grupos detectados
    groups_order = []
    groups = {}
    
    for item in top_skills:
        g_title = item["group"]
        if g_title not in groups:
            groups[g_title] = []
            groups_order.append(g_title)
        groups[g_title].append(item["skill"].get("name", ""))
        
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
        
        scored_exps.append({
            "score": exp_score,
            "data": {
                "start": exp.get("start", ""),
                "end": exp.get("end", ""),
                "title": title,
                "company": company,
                "description": description_text,
            }
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
        score = calculate_match_score(vaga_lower, title, tags) + get_item_tier_weight(title, tags)
        
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
        "Education": [
            {
                "start": edu.get("start", ""),
                "end": edu.get("end", ""),
                "title": edu.get("title", ""),
                "company": edu.get("company", ""),
                "description": edu.get("description", ""),
            } for edu in (master.get("education_bank") or [])
        ],
    }
    resolved["extra_education"] = resolve_extra_education(master, vaga_lower)

    # Limpeza de memória dos bancos brutos
    for key in ("description_bank", "skills_bank", "experience_bank", "education_bank", "extra_education_bank"):
        resolved.pop(key, None)

    return resolved