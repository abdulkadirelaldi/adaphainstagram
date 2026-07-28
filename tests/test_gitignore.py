"""`.gitignore` regresyon testi (SEC-2, SEC-1-B3'ün kapanışı).

Sır sızıntısının en olası yolu izlenmeye açık bir `.env*` dosyasıdır. Bu test o
yolu makineye devreder: `.gitignore`'dan bir env deseni sessizce düşerse burası
kırmızıya döner.

`git check-ignore` gerçek git kararını verir — desen eşleşmesini elle taklit etmeyiz,
git'in kendisine sorarız. Test canlı ağ değil, yalnızca yerel repoyu kullanır
(CLAUDE.md kural 6'ya aykırı değil).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# İzlenmesi ASLA istenmeyen yollar. Kök .gitignore bunların hepsini yok saymalı.
IGNORED_PATHS = [
    ".env",
    ".env.local",
    ".env.production.local",
    ".env.development.local",
    "api/.env",  # kök desen alt dizinde de tutmalı
    "secret.pem",
    "server.key",
    ".DS_Store",
    "test-results/report.xml",  # Playwright, Faz 6
    ".coverage",
    "var/audit_pdfs/audit_1.pdf",  # üretilen PDF çıktısı, Faz 5 (BE-18-N1)
]


@pytest.fixture(scope="module")
def git_available() -> str:
    git = shutil.which("git")
    if git is None:
        pytest.skip("git bulunamadı — bu testin çalışması için gerekli")
    return git


def _is_ignored(git: str, path: str) -> bool:
    """git'e sorar: bu yol .gitignore tarafından yok sayılıyor mu?

    `check-ignore` yok sayılan yolda 0, sayılmayanda 1 döner. Dosyanın diskte
    var olması gerekmez — sadece desen eşleşmesi sorgulanır.
    """
    result = subprocess.run(  # noqa: S603  # git yolu which'ten, argümanlar sabit — güvenilir
        [git, "check-ignore", "-q", path],
        cwd=REPO_ROOT,
        capture_output=True,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(
            f"git check-ignore beklenmedik çıkış {result.returncode}: "
            f"{result.stderr.decode(errors='replace')}"
        )
    return result.returncode == 0


@pytest.mark.parametrize("path", IGNORED_PATHS)
def test_yol_gitignore_tarafindan_yok_sayilir(git_available: str, path: str) -> None:
    assert _is_ignored(git_available, path), (
        f"{path!r} .gitignore tarafından yok sayılmıyor — izlenmeye açık. "
        "Bu bir sızıntı yoludur (SEC-1-B3). Kök .gitignore'a ilgili deseni ekle."
    )


def test_env_ornegi_yok_sayilmaz() -> None:
    """`.env.example` şablondur, izlenmeli — yanlışlıkla yok sayılmadığını doğrula.

    `.env` deseni fazla geniş yazılırsa `.env.example`'ı da yutabilir; o zaman
    sözleşme dosyası repodan kaybolur. Bu testin ters yönü korur.
    """
    git = shutil.which("git")
    if git is None:
        pytest.skip("git bulunamadı")
    assert not _is_ignored(git, ".env.example"), (
        ".env.example yok sayılıyor — bu şablon dosyası izlenmeli. "
        ".gitignore'daki .env deseni fazla geniş."
    )
