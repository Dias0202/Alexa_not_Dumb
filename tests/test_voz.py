from __future__ import annotations

import pytest
import voz


def test_normalizar_remove_marcacao_links_e_listas() -> None:
    texto = "# Título\n1. **Item** [útil](https://exemplo.com)\n- https://nao-falar.com"

    assert voz.normalizar(texto) == "Título Item útil"


def test_normalizar_corta_no_ultimo_fim_de_frase() -> None:
    texto = f"{'a' * 170}. {'b' * 500}"

    assert voz.normalizar(texto, limite=250).endswith(".")


def test_normalizar_rejeita_resposta_sem_conteudo() -> None:
    with pytest.raises(voz.RespostaVazia):
        voz.normalizar("** https://exemplo.com")


def test_escapar_ssml() -> None:
    assert voz.escapar_ssml("a < b & c > d") == "a &lt; b &amp; c &gt; d"
