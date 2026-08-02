# Validação manual e critérios de aceite

Os testes automatizados cobrem a lógica local. Os itens abaixo dependem do Alexa Developer Console, rede, contas de provedores ou um Echo físico.

| ID | Procedimento | Resultado esperado | Evidência a registrar |
|---|---|---|---|
| T-01 | Construir o modelo no console | Sem erro de carrier phrase | Captura de tela/data do build |
| T-02 | Invocar com “pergunte ...” | Slot recebe toda a pergunta | Transcript do simulador |
| T-03 | Responder com nova carrier phrase depois do primeiro turno | Próxima fala entra no slot sem erro de resposta inválida | Transcript de três turnos |
| T-04 | Fazer pergunta e “e por quê?” | Resposta considera o turno anterior | Transcript da sessão |
| T-05 | Realizar seis turnos | Histórico fica limitado e o diálogo continua | Log sem conteúdo da pergunta |
| T-06 | Invalidar temporariamente a chave primária | Provedor seguinte responde; WARNING sem segredo | Log com provedor/status |
| T-07 | Invalidar todas as chaves | Mensagem compreensível de indisponibilidade | Transcript e log |
| T-08 | Esperar 30 min e invocar | Resposta chega antes de 8 s | Três medições de duração |
| T-09 | Pedir resposta longa | Corte não termina no meio de frase quando houver pontuação | Transcript |
| T-10 | Pedir itens | Não lê Markdown, URLs ou numeração | Áudio/Transcript |
| T-11 | Dizer “para” | Despedida e fim da sessão, sem inferência | Transcript/log |
| T-12 | Não responder ao reprompt | Alexa encerra normalmente | Transcript |
| T-13 | Chamar proxy sem header | HTTP 401 | Código HTTP |
| T-14 | Chamar proxy com token válido | Resposta do Ollama | Código HTTP e duração |

## Critérios de aceite que dependem de operação real

- CA-01 e CA-02: resposta aberta e contexto no simulador/Echo.
- CA-03: vinte interações consecutivas no dispositivo físico sem exceder oito segundos.
- CA-04: fallback com chave primária temporariamente inválida.
- CA-05: verificação dos painéis de uso após 30 dias.
- CA-06 a CA-09: encerramento, erro compreensível, ausência de marcação em fala e Echo físico.

Registre datas, provedor ativo, duração e resultado; não registre perguntas, respostas integrais, chaves ou tokens.
