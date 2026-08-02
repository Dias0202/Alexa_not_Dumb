from __future__ import annotations

import lambda_function


def test_elicitacao_limpa_o_slot_da_pergunta() -> None:
    diretiva = lambda_function.elicitar()

    assert diretiva.slot_to_elicit == "pergunta"
    assert diretiva.updated_intent.name == "PerguntaIntent"
    assert diretiva.updated_intent.slots == {}


def test_historico_descarta_itens_malformados_e_limita_tamanho() -> None:
    entrada = [
        {"role": "user", "content": "pergunta"},
        {"role": "system", "content": "não deve viajar"},
        {"role": "assistant", "content": 1},
        {"role": "assistant", "content": "resposta"},
    ]

    assert lambda_function._historico_valido(entrada) == [
        {"role": "user", "content": "pergunta"},
        {"role": "assistant", "content": "resposta"},
    ]
