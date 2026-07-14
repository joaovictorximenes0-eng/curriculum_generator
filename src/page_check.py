"""
Estimativa (não pixel-perfect) de quanto espaço vertical o conteúdo de
cada coluna vai ocupar, comparado à altura útil de uma página A4. Não
depende de navegador/Playwright — só conta linhas e bullets e usa alturas
aproximadas em milímetros por linha, calibradas a partir do
static/style.css (fontes em pt convertidas para mm de linha impressa).

Além de avisar sobre overflow, este módulo calcula um "fator de
densidade" por coluna (1.0 = espaçamento normal do CSS), usado para
ajustar dinamicamente o espaçamento via CSS custom properties:

  - Se sobrar pouco espaço (dentro de uma margem de tolerância), nada
    muda — um rodapé em branco discreto é aceitável.
  - Se sobrar MUITO espaço (acima da tolerância), o espaçamento da
    coluna aumenta para preencher melhor a página.
  - Se faltar espaço, a coluna de Experiências NUNCA comprime (até 3
    experiências é prioridade máxima); Competências e Cursos &
    Aperfeiçoamentos comprimem primeiro.

Isso NÃO substitui conferir visualmente o HTML gerado — é uma estimativa
para guiar o ajuste automático e avisar no terminal quando o conteúdo
realmente não cabe de jeito nenhum.
"""

# Altura útil da página A4 (297mm) menos o que já é ocupado pelo header
# escuro + linha de resumo (headline) + paddings, estimado a partir do
# layout atual do template.html / style.css.
PAGE_HEIGHT_MM = 297
HEADER_AND_SUMMARY_MM = 78  # topbar + headline, aproximado
PAGE_PADDING_MM = 12        # padding inferior da página
USABLE_COLUMN_HEIGHT_MM = PAGE_HEIGHT_MM - HEADER_AND_SUMMARY_MM - PAGE_PADDING_MM

# Alturas aproximadas por elemento, em mm, calibradas para a fonte
# 'Poppins' nos tamanhos usados em .entry-header h3 (11.5pt), .entry-date
# (10pt) e .entry-description li (9.4pt) com a largura da experience-column.
MM_PER_ENTRY_TITLE_LINE = 5.2     # título da vaga, pode quebrar em 2 linhas
MM_PER_ENTRY_DATE_LINE = 4.2
MM_PER_BULLET_LINE = 4.0          # 1 bullet ~1 linha; bullets longos quebram em 2
CHARS_PER_TITLE_LINE = 48         # experience-column é mais larga
CHARS_PER_BULLET_LINE = 62
ENTRY_MARGIN_MM = 6.4             # margin-bottom: 18px (.entry) ≈ 6.4mm
EDUCATION_ENTRY_MM = 11           # título + meta de cada formação
EDUCATION_TITLE_HEADER_MM = 8     # "Formações Acadêmicas" + margem
EXTRA_EDUCATION_BLOCK_MM = 10     # label + 1 linha de tags (estimado)

# Coluna de competências: título do grupo + N skills, calibrado para
# .competency-block h3 (12pt) e .competency-block li (10pt).
COMPETENCY_HEADER_MM = 8.5        # "Competências Técnicas" (h2) + margem
COMPETENCY_GROUP_TITLE_MM = 5.5   # h3 do grupo (ex: "Python")
COMPETENCY_SKILL_LINE_MM = 4.3    # cada skill ~1 linha

# Regras de negócio da densidade (ajuste dinâmico de espaçamento):
# - até esta fração do espaço sobrando, fica em branco mesmo (tolerância)
EMPTY_TOLERANCE_FRACTION = 0.08
# - fator máximo de "esticar" espaçamento quando sobra espaço de verdade
MAX_STRETCH_FACTOR = 1.7
# - fator mínimo de "comprimir" espaçamento quando falta espaço
MIN_SHRINK_FACTOR = 0.72

LIMIT_TO_ONE_PAGE = False


def _estimate_lines(text: str, chars_per_line: int) -> int:
    length = len(text or "")
    if length == 0:
        return 1
    return max(1, -(-length // chars_per_line))  # ceil division


def estimate_experience_height_mm(entries) -> float:
    """Soma a altura estimada de todas as experiências (coluna esquerda)."""
    total = 0.0
    for entry in entries:
        title = f"{entry.get('title', '')} — {entry.get('company', '')}".strip(" —")
        total += _estimate_lines(title, CHARS_PER_TITLE_LINE) * MM_PER_ENTRY_TITLE_LINE
        total += MM_PER_ENTRY_DATE_LINE

        bullets = entry.get("description_items") or []
        if bullets:
            for bullet in bullets:
                total += _estimate_lines(bullet, CHARS_PER_BULLET_LINE) * MM_PER_BULLET_LINE
        else:
            for para in entry.get("description_paragraphs") or []:
                total += _estimate_lines(para, CHARS_PER_BULLET_LINE) * MM_PER_BULLET_LINE

        total += ENTRY_MARGIN_MM

    return total


def estimate_education_height_mm(education_entries, extra_education) -> float:
    total = EDUCATION_TITLE_HEADER_MM
    total += len(education_entries) * EDUCATION_ENTRY_MM
    if extra_education:
        total += EXTRA_EDUCATION_BLOCK_MM
    return total


def estimate_competency_height_mm(competency_blocks) -> float:
    """Soma a altura estimada da coluna de competências (coluna direita)."""
    total = COMPETENCY_HEADER_MM
    for group in competency_blocks or []:
        total += COMPETENCY_GROUP_TITLE_MM
        total += len(group.get("items") or []) * COMPETENCY_SKILL_LINE_MM
    return total


def check_overflow(body_sections, extra_education):
    """
    Recebe `body_sections` (já no formato de context.py) e `extra_education`,
    e devolve (estimated_mm, usable_mm, overflow: bool) considerando apenas
    a coluna de Experiências — que é a prioridade máxima e nunca deve ser
    cortada silenciosamente.
    """
    experience_entries = []
    education_entries = []

    for section in body_sections:
        if section["name"] == "Experience":
            experience_entries = section["entries"]
        elif section["name"] == "Education":
            education_entries = section["entries"]

    estimated = (
        estimate_experience_height_mm(experience_entries)
        + estimate_education_height_mm(education_entries, extra_education)
    )

    return estimated, USABLE_COLUMN_HEIGHT_MM, estimated > USABLE_COLUMN_HEIGHT_MM


def print_overflow_warning(estimated_mm, usable_mm):
    over_by = estimated_mm - usable_mm
    print(
        f"[page_check] AVISO: o conteúdo da coluna de Experiências está "
        f"estimado em ~{estimated_mm:.0f}mm, mas a página A4 tem espaço "
        f"para ~{usable_mm:.0f}mm (~{over_by:.0f}mm acima do limite).\n"
        f"             Como Experiências tem prioridade máxima, ela NÃO "
        f"encolhe — considere remover um bullet, encurtar uma experiência\n"
        f"             ou ajustar a seleção em input/selection.yaml.\n"
        f"             (Estimativa aproximada — confira sempre o "
        f"output/resume.html para o resultado real.)"
    )


def _clamp(value, low, high):
    return max(low, min(high, value))


def compute_density(body_sections, extra_education, competency_blocks):
    """
    Calcula os fatores de densidade (multiplicadores de espaçamento) para
    cada coluna, seguindo a regra de negócio:

      1. Experiências (até 3) é prioridade máxima: o fator dela só ESTICA
         (nunca comprime) — se sobrar espaço de verdade, ela "respira"
         mais; se faltar espaço, ela permanece em 1.0 e quem cede é o
         lado de Competências/Cursos.
      2. Um vazio de até EMPTY_TOLERANCE_FRACTION da altura útil é
         aceitável e não dispara nenhum ajuste (fica em branco mesmo).
      3. Acima da tolerância, o fator de esticar cresce proporcionalmente
         ao espaço sobrando, até MAX_STRETCH_FACTOR.
      4. Se o conteúdo total (Experiências + Competências) ultrapassa a
         altura útil, o fator de Competências/Cursos comprime
         proporcionalmente ao excesso, até MIN_SHRINK_FACTOR — protegendo
         Experiências de qualquer corte.

    Devolve um dict com {"experience": float, "side": float} prontos para
    virar CSS custom properties (--density-experience / --density-side).
    """

    if not LIMIT_TO_ONE_PAGE:
        return {
        "experience": 1.0,
        "side": 1.0,
    }
    
    experience_entries = []
    education_entries = []

    for section in body_sections:
        if section["name"] == "Experience":
            experience_entries = section["entries"]
        elif section["name"] == "Education":
            education_entries = section["entries"]

    experience_mm = estimate_experience_height_mm(experience_entries) + \
        estimate_education_height_mm(education_entries, extra_education)
    competency_mm = estimate_competency_height_mm(competency_blocks)

    # A coluna que efetivamente determina o "preenchimento" da página é a
    # mais alta das duas (já que ambas compartilham a mesma altura útil
    # disponível verticalmente).
    tallest_mm = max(experience_mm, competency_mm)
    leftover_mm = USABLE_COLUMN_HEIGHT_MM - tallest_mm
    tolerance_mm = USABLE_COLUMN_HEIGHT_MM * EMPTY_TOLERANCE_FRACTION

    experience_factor = 1.0
    side_factor = 1.0

    if leftover_mm > tolerance_mm:
        # Sobra espaço de verdade (além da tolerância): estica os dois
        # lados proporcionalmente, para preencher melhor a página.
        extra_fraction = (leftover_mm - tolerance_mm) / USABLE_COLUMN_HEIGHT_MM
        stretch = 1.0 + extra_fraction
        factor = _clamp(stretch, 1.0, MAX_STRETCH_FACTOR)
        experience_factor = factor
        side_factor = factor

    elif leftover_mm < 0:
        # Falta espaço: Experiências mantém 1.0 (prioridade máxima);
        # Competências/Cursos comprimem proporcionalmente ao excesso.
        deficit_fraction = abs(leftover_mm) / USABLE_COLUMN_HEIGHT_MM
        shrink = 1.0 - deficit_fraction
        side_factor = _clamp(shrink, MIN_SHRINK_FACTOR, 1.0)
        experience_factor = 1.0

    return {"experience": round(experience_factor, 3), "side": round(side_factor, 3)}