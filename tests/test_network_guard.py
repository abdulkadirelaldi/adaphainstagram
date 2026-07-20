"""Ağ muhafızının gerçekten çalıştığını kanıtlar.

Bu dosya `CLAUDE.md` kural 6'nın regresyon testidir. Muhafız bozulursa veya birisi
`conftest.py` içindeki autouse fixture'ı kaldırırsa burası kırmızıya döner — testlerin
sessizce canlı Instagram/Apify/Places çağrısı yapmaya başlaması bu sayede fark edilir.
"""

from __future__ import annotations

import socket

import pytest

from tests.conftest import NetworkCallBlockedError


def test_disari_giden_baglanti_engellenir() -> None:
    """Dış bir adrese connect() denemesi testi düşürmeli."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with pytest.raises(NetworkCallBlockedError, match="kural 6"):
        sock.connect(("graph.instagram.com", 443))
    sock.close()


def test_create_connection_de_engellenir() -> None:
    """socket.create_connection ayrı bir yol — o da kapalı olmalı."""
    with pytest.raises(NetworkCallBlockedError, match="kural 6"):
        socket.create_connection(("api.apify.com", 443))


def test_connect_ex_de_engellenir() -> None:
    """connect_ex sessizce hata kodu döner, muhafız burada da devrede olmalı."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with pytest.raises(NetworkCallBlockedError, match="kural 6"):
        sock.connect_ex(("places.googleapis.com", 443))
    sock.close()


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1"])
def test_yerel_adresler_serbest(host: str) -> None:
    """CI'daki postgres/redis servisleri ve ASGI taşıması yerelden geçer, engellenmemeli."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.1)
    # Bağlantının başarılı olması gerekmiyor — muhafızın araya girmemesi yeterli.
    with pytest.raises((ConnectionRefusedError, TimeoutError, OSError)):
        sock.connect((host, 1))
    sock.close()


def test_fixtures_dizini_var(fixtures_dir: object) -> None:
    """Fixture dizini yerinde olmalı — sabit JSON'ların adresi burası."""
    from pathlib import Path

    assert isinstance(fixtures_dir, Path)
    assert fixtures_dir.is_dir()
