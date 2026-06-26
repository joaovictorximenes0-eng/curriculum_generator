"""
Geração do PDF a partir do HTML final (output/resume.html), usando
Playwright com o Chrome/Brave já instalado no sistema — sem precisar
baixar o Chromium separado do Playwright.

Ordem de tentativa:
  1. Google Chrome (caminho padrão no Linux/Mac/Windows)
  2. Brave Browser
  3. Chromium do sistema
  4. Chromium do Playwright como último recurso
     (só nesse caso precisaria: playwright install chromium)

Por que Playwright e não weasyprint: o template usa CSS Grid pesado e
o objetivo é PDF pixel-idêntico ao HTML. Weasyprint não suporta Grid.
"""
from pathlib import Path
from shutil import which


# Caminhos comuns de Chrome/Brave por sistema operacional.
# O Playwright aceita um `executable_path` para usar qualquer binário
# compatível com o protocolo Chrome DevTools (CDP).
_BROWSER_CANDIDATES = [
        "google-chrome",
        "chrome",
        "msedge",
        "brave",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/brave-browser",
        "/usr/bin/brave",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


def _find_system_browser():
    """Retorna o primeiro executável de browser encontrado no sistema."""
    for path in _BROWSER_CANDIDATES:
        p = Path(path)
        if p.exists():
            return str(p)
        
        found = which(path)
        if found:
            return found
    
    return None


def export_pdf(html_path: Path, pdf_path: Path) -> bool:
    """
    Renderiza o HTML em html_path e salva como PDF em pdf_path.
    Usa o Chrome/Brave já instalado no sistema quando disponível.

    Devolve True se o PDF foi gerado com sucesso.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "[pdf_export] Playwright não está instalado — PDF não foi gerado.\n"
            "             Instale com:  pip install playwright\n"
            "             (Não precisa rodar 'playwright install' se você\n"
            "             já tem Chrome ou Brave instalado no sistema.)"
        )
        return False

    file_url = html_path.resolve().as_uri()
    browser_path = _find_system_browser()

    if browser_path:
        print(f"[pdf_export] Usando browser do sistema: {browser_path}")
    else:
        print(
            "[pdf_export] Chrome/Brave não encontrado — tentando Chromium do Playwright.\n"
            "             Se falhar, rode:  playwright install chromium"
        )

    try:
        with sync_playwright() as p:
            launch_kwargs = {"args": ["--no-sandbox"]}
            if browser_path:
                launch_kwargs["executable_path"] = browser_path

            browser = p.chromium.launch(**launch_kwargs)
            page = browser.new_page()
            page.goto(file_url, wait_until="load")
            page.emulate_media(media="print")
            page.wait_for_load_state("networkidle")
            
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                prefer_css_page_size=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            browser.close()
        return True

    except Exception as exc:
        print(
            f"[pdf_export] Falha ao gerar o PDF: {exc}\n"
            f"             Tente:  playwright install chromium"
        )
        return False