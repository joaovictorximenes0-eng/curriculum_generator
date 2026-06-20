"""
Registro de tipos de contato exibidos na barra superior do currículo.

Cada tipo tem: um ícone SVG monocromático (herda cor via `currentColor`,
fácil de colorir no CSS) e uma função `make_href` que decide se o item
vira link clicável e qual URL usar (None = não é link, só ícone + texto).

Para adicionar um novo tipo de contato no futuro (ex: site pessoal,
WhatsApp), basta adicionar uma entrada nova em CONTACT_TYPES — nenhum
outro módulo precisa mudar.
"""

# Ícones SVG simples, estilo outline, viewBox 24x24.
_ICON_ADDRESS = '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 21s-7-7.2-7-12a7 7 0 1 1 14 0c0 4.8-7 12-7 12Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><circle cx="12" cy="9" r="2.4" stroke="currentColor" stroke-width="1.6"/></svg>'
_ICON_PHONE = '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M6.6 10.8c1.3 2.6 3.4 4.7 6 6l2-2c.3-.3.7-.4 1.1-.3 1.2.4 2.5.6 3.8.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.6 21 3 13.4 3 4c0-.6.4-1 1-1h3.9c.6 0 1 .4 1 1 0 1.3.2 2.6.6 3.8.1.4 0 .8-.3 1.1l-2 2Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>'
_ICON_EMAIL = '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="5" width="18" height="14" rx="2" stroke="currentColor" stroke-width="1.6"/><path d="m4 7 8 6 8-6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
_ICON_LINKEDIN = '<svg viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg"><path d="M6.94 5a2 2 0 1 1-4 0 2 2 0 0 1 4 0ZM3.2 8.75h3.5V21H3.2V8.75ZM9.5 8.75h3.35v1.68h.05c.47-.88 1.6-1.8 3.3-1.8 3.53 0 4.18 2.32 4.18 5.35V21h-3.5v-5.66c0-1.35-.02-3.08-1.88-3.08-1.88 0-2.17 1.47-2.17 2.98V21H9.5V8.75Z"/></svg>'
_ICON_GITHUB = '<svg viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.48 2 2 6.58 2 12.2c0 4.49 2.87 8.3 6.84 9.64.5.1.68-.22.68-.49 0-.24-.01-1.04-.01-1.88-2.78.61-3.37-1.21-3.37-1.21-.46-1.18-1.11-1.5-1.11-1.5-.91-.63.07-.62.07-.62 1 .07 1.53 1.04 1.53 1.04.89 1.55 2.34 1.1 2.91.84.09-.66.35-1.1.63-1.36-2.22-.26-4.56-1.13-4.56-5.03 0-1.11.39-2.02 1.03-2.73-.1-.26-.45-1.3.1-2.71 0 0 .84-.27 2.75 1.04a9.3 9.3 0 0 1 5 0c1.91-1.31 2.75-1.04 2.75-1.04.55 1.41.2 2.45.1 2.71.64.71 1.03 1.62 1.03 2.73 0 3.91-2.34 4.77-4.57 5.02.36.32.68.94.68 1.9 0 1.37-.01 2.47-.01 2.81 0 .27.18.6.69.49A10.02 10.02 0 0 0 22 12.2C22 6.58 17.52 2 12 2Z"/></svg>'


def _no_link(value: str):
    """Tipo de contato que nunca vira link (só ícone + texto)."""
    return None


def _linkedin_href(value: str):
    """Aceita tanto 'in/usuario' quanto a URL completa já pronta no YAML."""
    if value.startswith("http"):
        return value
    return f"https://www.linkedin.com/{value.lstrip('/')}"


def _github_href(value: str):
    """Aceita tanto 'usuario' quanto a URL completa já pronta no YAML."""
    if value.startswith("http"):
        return value
    return f"https://github.com/{value.lstrip('/')}"


# Registro de tipos de contato. Ordem de exibição = ordem desta lista.
# `key`: nome do campo correspondente no YAML (address, phone, email, ...)
# `icon`: SVG monocromático
# `make_href`: função texto -> URL ou None (None = não vira link)
CONTACT_TYPES = [
    {"key": "address", "icon": _ICON_ADDRESS, "make_href": _no_link},
    {"key": "phone", "icon": _ICON_PHONE, "make_href": _no_link},
    {"key": "email", "icon": _ICON_EMAIL, "make_href": _no_link},
    {"key": "linkedin", "icon": _ICON_LINKEDIN, "make_href": _linkedin_href},
    {"key": "github", "icon": _ICON_GITHUB, "make_href": _github_href},
]