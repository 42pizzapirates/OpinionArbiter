import re


def sanitize_markdown(text: str) -> str:
    """清洗 LLM 输出：剥离代码块与多余空白"""
    if not text:
        return ""
    match = re.search(r"```[A-Za-z0-9_-]*\s*\n(.*?)```", text, flags=re.DOTALL)
    cleaned = match.group(1).strip() if match else text.strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip(" \n\r\t\"'“”‘’")
