# Troubleshooting operacional

## Abertura funciona, mas a pergunta retorna indisponibilidade

Quando a Alexa abre a skill e responde "não consegui falar com o modelo agora", o roteamento de voz e o handler estão ativos. Investigue o caminho de inferência, nesta ordem:

1. Abra **Code > CloudWatch Logs** no Alexa Developer Console.
2. Localize o evento da mesma hora da pergunta.
3. Procure o motivo seguro registrado pelo roteador, por exemplo `gemini:http_403`, `gemini:URLError` ou `gemini:prazo_esgotado`.
4. Corrija a credencial, a restrição de rede ou o provedor indicado; não copie chaves para logs, issues ou commits.

O alerta `cloudwatch:GetMetricData` não é a causa. Ele representa falta de permissão para o painel de métricas e não bloqueia os eventos do grupo de logs.

## Erro de importação no runtime

O runtime hospedado desta skill é Python 3.8. A mensagem `TypeError: 'ABCMeta' object is not subscriptable` indica um alias de tipo avaliado na importação com genéricos de `collections.abc`. Use `typing.Mapping`, `typing.Sequence` e `typing.Callable` em aliases de tipo; mantenha `collections.abc` apenas onde for necessário para `isinstance`.

## O Echo não executa a revisão publicada

O botão **Deploy** atualiza o ambiente Development. Para testar sem publicação pública, o Echo deve usar a mesma conta Amazon do console e a skill deve estar habilitada em **Suas skills > Dev Skills**. A promoção para Live exige que a skill tenha sido publicada e aprovada pelo fluxo de certificação.

## Provedores ativos

Gemini é o provedor ativo atual. A Groq foi retirada da fila depois de responder HTTP 403. Só reative Groq após rotacionar a chave e validar uma resposta fora e dentro da Lambda hospedada.
