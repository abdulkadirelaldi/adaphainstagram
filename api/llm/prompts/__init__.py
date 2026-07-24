"""Versiyonlu LLM promptları (SPEC §6: koda gömülmez, dosyada durur).

`load_prompt("classify_system_v1.md")` ile okunur. Sürüm dosya adında; yeni sürüm
yeni dosya, eski bozulmaz — prompt caching prefix'i sabit kalsın.
"""

from pathlib import Path

_DIR = Path(__file__).resolve().parent


def load_prompt(name: str) -> str:
    return (_DIR / name).read_text(encoding="utf-8")
