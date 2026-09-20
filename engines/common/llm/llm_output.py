import re


def clean_markdown_text(text: str) -> str:
    """
    供 SummarizeNode 使用。
    只负责剥离外层的 ```markdown 和 ``` 标记，返回纯净的正文。
    """
    if not text:
        return ""

    match = re.search(r"```[A-Za-z0-9_-]*\s*\n(.*?)```", text, flags=re.DOTALL)
    return match.group(1).strip() if match else text.strip()
