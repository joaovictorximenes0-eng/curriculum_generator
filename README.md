
🚀 Smart Resume Generator (AI-Driven ATS Optimizer)

Este é um ecossistema automatizado em Python para geração e otimização de currículos baseado em dados. O projeto evoluiu de um gerador estático para um  **motor de triagem analítico orientado a requisitos ( *Data-Driven* )** .

Em vez de gerenciar manualmente quais experiências e competências entram no currículo, o pipeline analisa o texto bruto de uma vaga de emprego (`vaga.txt`), calcula o nível de relevância técnica dos seus projetos utilizando um sistema inteligente de  *Scoring* , e renderiza um PDF A4 perfeito, totalmente personalizado para a oportunidade em segundos.

## 🧠 Como o Motor Funciona

O projeto resolve de forma automatizada o problema do limite físico do papel (A4) e dos filtros dos sistemas automáticos de recrutamento (ATS):

1. **Leitura de Contexto (`vaga.txt`):** O script lê os requisitos, as responsabilidades e a descrição de uma vaga real colada no arquivo.
2. **Algoritmo de Scoring:** O sistema varre o banco de dados modular (`input/`) buscando correspondências exatas e semânticas entre o texto da vaga, os nomes das tecnologias e as tags associadas a cada projeto.
3. **Hierarquia Quântica de Pesos (Tiers):** Caso haja empate ou para priorizar competências cruciais, o motor utiliza uma configuração de pesos para destacar habilidades de maior impacto de engenharia (ex: Java, Python, Docker) em detrimento de ferramentas utilitárias comuns (Word, PowerPoint).
4. **Corte Rígido (O Número Mágico):** Para garantir o *Page-Budget* perfeito de 1 página A4, o script ordena as experiências pelo score e renderiza apenas o "Top 3" projetos mais compatíveis, aplicando um teto limite para exibição de competências.
5. **Nomenclatura Dinâmica Baseada em Stack:** O arquivo de saída é batizado automaticamente com base no foco tecnológico detectado na vaga (ex: `joao_victor_backend_java.pdf`).

## 🚀 Principais Funcionalidades Extras

* **Agnóstico e de Baixa Manutenção:** Arquitetura flexível baseada em clonagem dinâmica de dicionários (`.copy()`). Alterações ou adições de chaves nos arquivos YAML são refletidas no layout sem necessidade de alterar o código Python.
* **Algoritmo de Densidade Visual (Page-Budget):** Monitora a ocupação física das seções (`page_check.py`) para alertar desvios de layout no terminal.
* **Linter Integrado de Consistência (`validate_tags.py`):** Validador estático que garante que todas as competências citadas nas experiências estão devidamente cadastradas no banco global de skills.
* **Micro-interações de UI/UX:** Links dinâmicos injetados no PDF utilizando o indicador de hyperlink unicode (`↗`) com transições em CSS, além de automação nativa para cópia de dados sensíveis para a área de transferência.

## 📁 Estrutura de Pastas

**Plaintext**

```
├── input/                          # Dados de entrada (Modulares YAML)
│   ├── description.yaml            # Resumos profissionais e objetivos
│   ├── education.yaml              # Formações acadêmicas principais
│   ├── experience.yaml             # Banco de experiências e projetos com tags
│   ├── secrets.yaml                # Variáveis sensíveis e dados de contato
│   ├── skills.yaml                 # Catálogo global de tecnologias
│   └── vaga.txt                    # Requisitos brutos copiados da vaga alvo
├── output/                         # PDFs e HTMLs customizados gerados
├── src/                            # Módulos core da aplicação
│   ├── contacts.py                 # Processamento de contatos e ícones
│   ├── context.py                  # Pipeline de contexto para o template
│   ├── icons.py                    # Repositório de paths SVG inline
│   ├── page_check.py               # Monitor de densidade física do layout
│   ├── pdf_export.py               # Automação de renderização para PDF
│   ├── selection.py                # Motor de Tiers, classificação e match
│   ├── text_utils.py               # Limpeza de strings e normalização
│   └── yaml_io.py                  # Resolvedor de placeholders ${VAR}
├── static/                         # Estilização do currículo
│   ├── css/                        # Arquitetura modular (Layout, Print)
│   ├── script.js                   # Interações do cliente (Clipboard)
│   └── style.css                   # Unificador de folhas de estilo
├── templates/
│   └── template.html               # Estrutura base em Jinja2
├── render.py                       # Orquestrador principal (Maestro)
├── requirements.txt                # Dependências declarativas do projeto
└── validate_tags.py                # Linter estático para integridade de tags
```

## 🛠️ Portabilidade e Renderização Multiplataforma

O motor de exportação de PDF (`src/pdf_export.py`) foi desenhado para ser totalmente  *Cross-Platform* , eliminando a necessidade de dependências pesadas de terceiros.

Ele varre de forma inteligente uma lista de candidatos a executáveis (`_BROWSER_CANDIDATES`) para encontrar instâncias nativas do **Google Chrome, Brave ou Chromium** instaladas no sistema operacional do usuário (suportando  **Windows, Linux e macOS** ), disparando o browser em modo *headless* para gerar um PDF milimetricamente idêntico ao design do HTML.

## ⚙️ Instalação e Execução

### 1. Clonar o Repositório e Instalar Dependências

Certifique-se de ter o Python 3.12+ e o Google Chrome (ou Brave/Chromium) instalados.

**Bash**

```
git clone https://github.com/joaovictorximenes0-eng/curriculum_generator.git
cd curriculum_generator
pip install -r requirements.txt
```

### 2. Validar a Integridade das Tags

Antes de renderizar, execute o linter estático para garantir que nenhuma tag de tecnologia foi digitada incorretamente:

**Bash**

```
python validate_tags.py
```

### 3. Compilar o Currículo Otimizado

Cole a descrição da vaga em `input/vaga.txt` e execute o orquestrador:

**Bash**

```
python render.py
```

## 🛠️ Tecnologias Utilizadas

* **Linguagem Core:** Python 3.12
* **Template Engine:** Jinja2
* **Data Serialization:** PyYAML
* **Design & Layout:** HTML5 / CSS3 Avançado (Flexbox, Grid, CSS Variables, `@media print`)
* **Automação de Render:** Google Chrome CLI Interface (`--headless`)
