"""
Ponto de entrada: lê os YAMLs modulares de input/, lê os requisitos da vaga em vaga.txt,
aplica o motor de pontuação inteligente por Tiers/Keywords, monta o
contexto e renderiza o template HTML final.
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

# Trocamos load_yaml por load_modular_resume
from yaml_io import load_modular_resume, load_yaml, resolve_placeholders  # noqa: E402
from selection import apply_selection  # noqa: E402
from context import prepare_context  # noqa: E402
from page_check import check_overflow, print_overflow_warning, compute_density  # noqa: E402
from pdf_export import export_pdf  # noqa: E402

VAGA_TXT = INPUT_DIR / "vaga.txt"
SECRETS = INPUT_DIR / "secrets.yaml"
OUTPUT_HTML = OUTPUT_DIR / "resume.html"
OUTPUT_PDF = OUTPUT_DIR / "resume.pdf"
TEMPLATE_NAME = "template.html"

import re
from unicodedata import normalize

def slugify(text):
    """Transforma qualquer string em um nome de arquivo seguro (sem acentos ou espaços)"""
    text = normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s_-]', '', text)
    text = re.sub(r'[\s_-]+', '_', text)
    return text

def detect_file_focus(vaga_text, default_title):
    """Analisa o texto da vaga e resume o foco em apenas 1 ou 2 palavras para o nome do arquivo."""
    if not vaga_text:
        return default_title
        
    vaga_lower = vaga_text.lower()
    
    # Define grupos simples de palavras-chave para o nome do arquivo
    if any(w in vaga_lower for w in ["java", "backend", "spring", "servlet"]):
        return "Backend_Java"
    elif any(w in vaga_lower for w in ["dados", "power bi", "pandas", "bi", "sql", "analytics","python"]):
        return "Engenharia_de_Dados"
    elif any(w in vaga_lower for w in ["n8n", "selenium", "automação", "rpa"]):
        return "Automacao"
    elif any(w in vaga_lower for w in ["design", "ui", "ux", "photoshop"]):
        return "Design_UI_UX"
        
    return default_title # Fallback caso seja uma vaga genérica

def main():
    # AQUI ESTÁ A MÁGICA: O Python monta o quebra-cabeça dos arquivos para você
    master_raw = load_modular_resume(INPUT_DIR)
    secrets = load_yaml(SECRETS)

    master = resolve_placeholders(master_raw, secrets)

    # Lê a vaga de forma segura
    vaga_text = ""
    if VAGA_TXT.exists():
        vaga_text = VAGA_TXT.read_text(encoding="utf-8")
        print(f"[render] Lendo requisitos e palavras-chave de: {VAGA_TXT}")
    else:
        print("[render] Aviso: vaga.txt não encontrado. Gerando versão genérica por Tiers de peso.")

    # Processamento e montagem do contexto
    filtered = apply_selection(master, vaga_text)
    context = prepare_context(filtered)

    estimated_mm, usable_mm, overflow = check_overflow(
        context["body_sections"], context.get("extra_education")
    )
    if overflow:
        print_overflow_warning(estimated_mm, usable_mm)

    density = compute_density(
        context["body_sections"],
        context.get("extra_education"),
        context["competency_blocks"],
    )
    context["density"] = density
    print(
        f"[page_check] densidade calculada: experience={density['experience']} "
        f"side={density['side']} (1.0 = espaçamento normal)"
    )

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template = env.get_template(TEMPLATE_NAME)
    html = template.render(**context)



    # Nome personalizado 
    user_name = master.get("full_name", "place_holder")
    primeiros_nomes = " ".join(user_name.split()[:2])

    default_title = master.get("headline_title", "Desenvolvedor") 

    foco_vaga = detect_file_focus(vaga_text, default_title)

    # 2. Gera os nomes de arquivos limpos e seguros
    base_name = f"{slugify(primeiros_nomes)}_{slugify(foco_vaga)}"
    
    # 3. Monta os caminhos (Path) finais apontando para a pasta output/
    dinamico_html = OUTPUT_DIR / f"{base_name}.html"
    dinamico_pdf = OUTPUT_DIR / f"{base_name}.pdf"

    # 4. Garante que a pasta output/ exista
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 5. Salva o HTML com o nome dinâmico
    dinamico_html.write_text(html, encoding="utf-8")
    print(f"[render] HTML gerado em: {dinamico_html}")

    # 6. Exporta o PDF passando os caminhos dinâmicos corretos
    if export_pdf(dinamico_html, dinamico_pdf):
        print(f"[render] PDF profissional gerado com sucesso em: {dinamico_pdf}")
    else:
        print("[render] Erro crítico na exportação do PDF.")


if __name__ == "__main__":
    main()