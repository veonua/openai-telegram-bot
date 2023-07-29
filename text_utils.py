
def is_markdown(text: str):
    return text.startswith("*") and text.endswith("*")