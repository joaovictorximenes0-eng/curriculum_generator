"""
Utilitários para transformar texto cru (vindo do YAML) em estruturas que
o template HTML consome: parágrafos separados ou itens de lista (bullets).
"""


def split_description(text: str):
    """
    Quebra um texto em parágrafos, separando por linha em branco dupla
    (\\n\\n). Se não houver separador, devolve o texto inteiro como um
    único parágrafo.
    """
    text = (text or "").strip()
    if not text:
        return []
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    return parts or [text]


def bullets_from_text(text: str):
    """
    Quebra um texto em bullets, uma linha = um bullet. Remove o prefixo
    "- " de cada linha quando presente (formato usado no YAML para listar
    bullets dentro de um bloco `description: |`).
    """
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    items = []
    for line in lines:
        if line.startswith("- "):
            items.append(line[2:].strip())
        else:
            items.append(line)
    return items