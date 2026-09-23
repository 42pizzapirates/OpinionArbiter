"""Markdown → HTML 渲染 + HTML 页面模板。"""

import mistune

_HTML_CSS = """
body { font-family: 'Segoe UI', system-ui, sans-serif; max-width: 900px; margin: 0 auto; padding: 2em; line-height: 1.8; color: #333; }
h1 { color: #1a1a2e; border-bottom: 3px solid #e94560; padding-bottom: 0.3em; }
h2 { color: #16213e; border-bottom: 1px solid #ddd; padding-bottom: 0.2em; margin-top: 1.5em; }
h3 { color: #0f3460; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; }
th, td { border: 1px solid #ddd; padding: 0.6em 1em; text-align: left; }
th { background: #16213e; color: #fff; }
blockquote { border-left: 4px solid #e94560; padding-left: 1em; color: #555; margin-left: 0; }
code { background: #f4f4f4; padding: 0.2em 0.4em; border-radius: 3px; }
pre { background: #1a1a2e; color: #eee; padding: 1em; border-radius: 6px; overflow-x: auto; }
"""

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>{style}</style>
</head>
<body>
{body}
</body>
</html>"""


def render_markdown(text: str) -> str:
    """Markdown → HTML(mistune 硬依赖)。"""
    return mistune.html(text)


def render_html(body_html: str, title: str = "研究报告") -> str:
    """包裹 HTML body 为完整样式页面。"""
    return _HTML_TEMPLATE.format(title=title, body=body_html, style=_HTML_CSS)
