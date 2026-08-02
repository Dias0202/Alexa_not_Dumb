# PDD - Process Design Document
## Assistente Conversacional na Alexa com LLM

---

### 1. Controle do documento

| Campo | Valor |
|---|---|
| Projeto | Assistente Conversacional na Alexa com LLM |
| Documento | PDD (Process Design Document) |
| Versão | 1.0 |
| Data | 02/08/2026 |
| Autor | Luan Pacheco Cabral |
| Tipo | Projeto pessoal, uso individual |
| Restrição-mãe | Custo recorrente igual a zero |
| Documento relacionado | SDD-assistente-alexa-llm.md |
| Status | Aprovado para execução |

---

### 2. Contexto e justificativa

A Alexa nativa responde a partir de um conjunto fechado de intents. Cada frase precisa ser mapeada previamente para uma intenção, e o dispositivo não mantém raciocínio entre turnos nem lida com perguntas fora do catálogo. O resultado é uma interação por comando, não por conversa.

A proposta é manter da Amazon apenas o que ela faz bem (captura de áudio, reconhecimento de fala e síntese de voz) e substituir a camada de decisão por um LLM. O dispositivo vira interface de voz, o modelo vira o cérebro.

Como o uso é individual e sem qualquer intenção comercial, a restrição de custo zero é tratada como requisito de projeto e não como preferência. Toda decisão de arquitetura que implique cobrança recorrente, mesmo que baixa, está descartada por definição.

---

### 3. Escopo

**3.1 Dentro do escopo**

- Skill customizada em pt-BR, operando em modo desenvolvimento (sem publicação na loja)
- Captura de fala livre, sem necessidade de mapear frases específicas
- Roteamento da fala capturada para um LLM e devolução da resposta em voz
- Conversa contínua dentro da sessão, com memória dos turnos anteriores
- Perfil fixo do usuário injetado no prompt (nome, contexto, preferências de resposta)
- Fallback automático entre provedores de inferência
- Tratamento de erro sempre audível, nunca silêncio ou mensagem genérica da Amazon

**3.2 Fora do escopo**

| Item | Motivo |
|---|---|
| Publicação na Amazon Skills Store | Uso individual, exige certificação e política de privacidade |
| Múltiplos usuários e reconhecimento de voz por pessoa | Um único usuário |
| Controle de dispositivos smart home | Outro tipo de skill, exige modelo de interação pré-definido |
| Streaming de resposta token a token | A Alexa opera em request/response síncrono, não suporta |
| Substituição da Alexa nativa | A skill convive com a assistente padrão, é invocada por nome |
| Memória de longo prazo entre sessões | Adiado para v2, ver seção 15 |
| Wake word própria | Fora do controle do desenvolvedor |

---

### 4. Atores e responsabilidades

| Ator | Tipo | Responsabilidade |
|---|---|---|
| Usuário | Humano | Invocar a skill, formular perguntas, encerrar a conversa |
| Desenvolvedor | Humano | Construir, implantar, monitorar e ajustar prompts e modelos |
| Dispositivo Echo | Sistema | Capturar áudio e reproduzir a resposta sintetizada |
| Serviço Alexa | Sistema | Reconhecimento de fala, resolução de intent, síntese de voz, arbitragem do timeout |
| Backend da skill | Sistema | Extrair o texto, montar o contexto, orquestrar provedores, formatar a resposta |
| Provedor de LLM | Sistema externo | Gerar a resposta em linguagem natural |

Neste projeto os dois papéis humanos são exercidos pela mesma pessoa. A separação é mantida no documento porque as necessidades de cada papel são diferentes: o usuário precisa de resposta rápida e natural, o desenvolvedor precisa de log e previsibilidade.

---

### 5. Processo AS-IS

| Passo | Ator | Ação |
|---|---|---|
| 1 | Usuário | Fala um comando para a Alexa |
| 2 | Serviço Alexa | Transcreve e tenta casar a frase com uma intent conhecida |
| 3 | Serviço Alexa | Se casar, executa a ação; se não casar, responde que não entendeu |
| 4 | Usuário | Reformula a frase até acertar o formato esperado |

**Dores identificadas**

| ID | Dor | Efeito |
|---|---|---|
| D-01 | Vocabulário fechado | O usuário precisa aprender como falar com a máquina |
| D-02 | Ausência de contexto entre turnos | Toda pergunta precisa ser autocontida |
| D-03 | Ausência de raciocínio | Perguntas abertas ou analíticas não têm resposta |
| D-04 | Ausência de personalização | O assistente não sabe nada sobre quem está falando |
| D-05 | Falha silenciosa | Frases não reconhecidas geram resposta padrão sem utilidade |

---

### 6. Processo TO-BE

| Passo | Ator | Ação | Saída |
|---|---|---|---|
| 1 | Usuário | Invoca a skill pelo nome de invocação | Áudio capturado |
| 2 | Serviço Alexa | Transcreve e identifica a skill de destino | Payload JSON com a transcrição |
| 3 | Serviço Alexa | Envia o payload ao backend e inicia a contagem de 8 segundos | Requisição HTTP |
| 4 | Backend | Extrai o texto livre do slot de captura | String da pergunta |
| 5 | Backend | Recupera o histórico da sessão e o perfil do usuário | Lista de mensagens |
| 6 | Backend | Emite resposta progressiva para preencher a espera | Áudio curto de espera |
| 7 | Backend | Chama o provedor primário de LLM com prazo controlado | Texto bruto ou erro |
| 8 | Backend | Em caso de erro, aciona o provedor seguinte da fila | Texto bruto ou erro |
| 9 | Backend | Normaliza o texto para voz (remove marcação, corta no limite) | Texto falável |
| 10 | Backend | Grava o turno no histórico da sessão | Sessão atualizada |
| 11 | Backend | Devolve a resposta e reabre o microfone | JSON de resposta |
| 12 | Serviço Alexa | Sintetiza a voz e escuta o próximo turno | Áudio reproduzido |
| 13 | Usuário | Faz nova pergunta (volta ao passo 4) ou encerra | Fim ou novo ciclo |

O ponto crítico do processo está entre os passos 3 e 11. Todo o trabalho precisa caber na janela de 8 segundos que o serviço Alexa concede ao backend. Ultrapassado esse limite, a Alexa descarta a resposta, informa erro ao usuário e encerra a sessão.

---

### 7. Gatilhos, frequência e volumetria

| Item | Valor |
|---|---|
| Gatilho | Comando de voz do usuário |
| Frequência estimada | 10 a 40 interações por dia |
| Pico estimado | 5 interações em um minuto |
| Volume mensal estimado | 300 a 1.200 requisições |
| Janela de uso | Sem restrição de horário |
| Sazonalidade | Nenhuma |

A volumetria confirma a viabilidade do custo zero: o consumo projetado fica uma ordem de grandeza abaixo dos limites gratuitos de qualquer provedor considerado. O detalhamento dos limites está na seção 3 do SDD.

---

### 8. Regras de negócio

| ID | Regra | Justificativa |
|---|---|---|
| RN-01 | Nenhum componente da solução pode gerar cobrança recorrente | Restrição-mãe do projeto |
| RN-02 | Nenhum serviço que exija cartão de crédito cadastrado deve ser usado como componente obrigatório | Elimina o risco de cobrança por engano ou por estouro de limite |
| RN-03 | O backend deve devolver resposta em até 8 segundos contados do recebimento da requisição | Timeout imposto pelo serviço Alexa |
| RN-04 | O orçamento interno de chamada ao LLM é de 6 segundos, reservando 2 segundos para overhead | Margem de segurança sobre a RN-03 |
| RN-05 | A resposta padrão deve ter no máximo 3 frases ou 600 caracteres | Texto longo demora a gerar e cansa em voz |
| RN-06 | Todo o processo opera em pt-BR | Idioma do usuário e do dispositivo |
| RN-07 | A resposta enviada à Alexa deve ser texto plano, sem marcação markdown | Marcação é lida em voz alta e polui a fala |
| RN-08 | A sessão permanece aberta após cada resposta até comando explícito de encerramento ou silêncio do usuário | Permite conversa contínua |
| RN-09 | O contexto enviado ao modelo é limitado aos últimos 3 pares de pergunta e resposta | Contém a latência e o consumo de tokens |
| RN-10 | Toda falha de provedor deve acionar o provedor seguinte da fila antes de retornar erro | Disponibilidade sobre stack gratuita instável |
| RN-11 | Qualquer erro não recuperado deve virar uma resposta falada e compreensível | Silêncio ou erro genérico da Amazon é falha de processo |
| RN-12 | Dados pessoais sensíveis não devem ser enviados no prompt | Provedores gratuitos podem usar as entradas para treinamento |
| RN-13 | Chaves de API não podem ser versionadas em repositório público nem expostas em log | Higiene mínima de segurança |
| RN-14 | O endpoint de inferência local, quando usado, deve exigir autenticação própria | O Ollama não tem camada de autenticação nativa |

---

### 9. Cenários de uso

**CN-01 Caminho feliz**
Usuário invoca a skill, faz uma pergunta, recebe resposta em menos de 5 segundos, encerra. É o cenário esperado em mais de 90% das interações.

**CN-02 Pergunta de acompanhamento**
Usuário faz uma segunda pergunta que depende da primeira ("e por quê?"). O backend recupera o histórico da sessão e o modelo responde com o contexto correto. Valida a RN-09.

**CN-03 Encerramento explícito**
Usuário diz "para" ou "cancela". A skill se despede e encerra a sessão sem chamar o LLM.

**CN-04 Silêncio do usuário**
O microfone reabre e o usuário não fala. A Alexa emite o reprompt e, persistindo o silêncio, encerra a sessão sozinha. Nenhuma chamada ao LLM é feita.

**CN-05 Fala não capturada**
A transcrição chega vazia ou ilegível. O backend pede repetição sem consumir cota do provedor.

**CN-06 Troca de assunto**
Usuário muda completamente de tema no meio da sessão. O histórico permanece, mas o modelo é instruído no prompt de sistema a priorizar o turno mais recente.

---

### 10. Exceções e tratamento

| ID | Exceção | Causa provável | Tratamento | Resposta ao usuário |
|---|---|---|---|---|
| EX-01 | Slot de captura vazio | Ruído, fala truncada, ASR sem confiança | Reabrir o microfone sem chamar o LLM | "Não peguei. Pode repetir?" |
| EX-02 | Timeout do provedor primário | Latência de rede ou fila do provedor | Acionar o provedor seguinte dentro do prazo restante | Transparente, sem menção ao usuário |
| EX-03 | Todos os provedores falharam | Queda simultânea ou cota diária esgotada | Registrar em log e devolver mensagem controlada | "Não consegui falar com o modelo agora. Tenta de novo?" |
| EX-04 | HTTP 429 do provedor | Limite de requisições por minuto atingido | Pular imediatamente para o provedor seguinte | Transparente |
| EX-05 | HTTP 401 ou 403 | Chave inválida, revogada ou expirada | Pular para o provedor seguinte e registrar alerta no log | Transparente, se houver alternativa |
| EX-06 | Resposta do modelo vazia ou só com marcação | Falha de geração ou filtro de conteúdo | Tratar como falha e acionar o provedor seguinte | Transparente |
| EX-07 | Resposta acima do limite de caracteres | Modelo ignorou a instrução de concisão | Cortar no último ponto final antes do limite | Resposta truncada de forma natural |
| EX-08 | Prazo interno estourado antes da chamada | Cold start somado a leitura de configuração | Abortar a cadeia e responder com mensagem controlada | "Demorei demais aqui. Pergunta de novo?" |
| EX-09 | Endpoint local inacessível | Máquina desligada, túnel caído | Marcar o provedor local como indisponível e seguir a fila | Transparente |
| EX-10 | Falha ao carregar a configuração | Objeto de configuração ausente ou malformado | Abortar com mensagem controlada e registrar erro completo em log | "Estou com um problema de configuração." |

O princípio de tratamento é simples: falha de infraestrutura nunca deve virar falha de conversa. O usuário só percebe o erro quando não há nenhuma alternativa restante.

---

### 11. Entradas e saídas

| Direção | Dado | Origem | Destino | Observação |
|---|---|---|---|---|
| Entrada | Transcrição da fala | Serviço Alexa | Backend | Texto livre, sem estrutura garantida |
| Entrada | Identificador de sessão | Serviço Alexa | Backend | Chave do histórico em memória de sessão |
| Entrada | Perfil do usuário | Configuração | Prompt de sistema | Estático, editado manualmente |
| Entrada | Histórico da sessão | Atributos de sessão | Prompt | Limitado pela RN-09 |
| Saída | Texto da resposta | Backend | Serviço Alexa | Texto plano, limitado pela RN-05 |
| Saída | Resposta progressiva | Backend | Serviço Alexa | Frase curta de espera, opcional |
| Saída | Log de execução | Backend | Log da nuvem | Sem chaves e sem conteúdo sensível |

---

### 12. Requisitos não funcionais

| ID | Requisito | Meta |
|---|---|---|
| RNF-01 | Latência ponta a ponta | Abaixo de 5 segundos em 90% das interações |
| RNF-02 | Latência máxima tolerada | 8 segundos, limite rígido |
| RNF-03 | Custo mensal | R$ 0,00 |
| RNF-04 | Disponibilidade percebida | Acima de 95%, sustentada por fallback e não por SLA |
| RNF-05 | Privacidade | Nenhum dado sensível trafegando para provedores gratuitos |
| RNF-06 | Manutenibilidade | Troca de modelo ou provedor sem alterar a lógica dos handlers |
| RNF-07 | Observabilidade | Log de cada chamada com provedor usado, duração e resultado |
| RNF-08 | Portabilidade | Backend independente do provedor de inferência |
| RNF-09 | Tempo de recuperação | Reimplantação completa em menos de 10 minutos |

---

### 13. Critérios de aceite

| ID | Critério | Como validar |
|---|---|---|
| CA-01 | A skill responde a uma pergunta aberta não prevista no modelo de interação | Perguntar algo arbitrário e obter resposta coerente |
| CA-02 | A skill mantém contexto entre dois turnos consecutivos | Fazer pergunta de acompanhamento com pronome ou referência implícita |
| CA-03 | Nenhuma interação estoura o timeout de 8 segundos em 20 tentativas seguidas | Bateria de teste no dispositivo físico |
| CA-04 | A queda do provedor primário não interrompe a conversa | Invalidar a chave primária e repetir a pergunta |
| CA-05 | Nenhum serviço da solução gera cobrança | Verificar o painel de uso após 30 dias de operação |
| CA-06 | O encerramento por comando de voz funciona | Dizer "para" e confirmar que a sessão fecha |
| CA-07 | Erros aparecem como fala compreensível, nunca como erro genérico da Amazon | Forçar falha em todos os provedores |
| CA-08 | Marcação de texto não é lida em voz alta | Pedir uma lista e conferir a fala resultante |
| CA-09 | A skill funciona no dispositivo físico, não apenas no simulador | Teste no Echo com a mesma conta Amazon |

---

### 14. Riscos e premissas

**14.1 Riscos**

| ID | Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|---|
| R-01 | Provedor gratuito reduz ou encerra a cota | Média | Alto | Fila de provedores configurável, trilha local como último recurso |
| R-02 | Latência do provedor cresce e estoura o timeout | Média | Alto | Prazo por provedor, resposta progressiva, limite de tokens de saída |
| R-03 | Cota diária esgotada no meio do uso | Baixa | Médio | Volumetria muito abaixo do limite, fallback entre provedores |
| R-04 | Chave de API vazada | Baixa | Médio | Chave fora do código versionado, rotação simples |
| R-05 | Provedor gratuito usar as entradas para treinamento | Alta | Baixo | RN-12, nenhum dado sensível no prompt |
| R-06 | Mudança de política da Amazon sobre skills em desenvolvimento | Baixa | Alto | Backend desacoplado, migrável para endpoint HTTPS próprio |
| R-07 | Qualidade da transcrição em pt-BR abaixo do esperado | Média | Médio | Frases de invocação curtas, tolerância a erro no prompt de sistema |
| R-08 | Trilha local indisponível por queda de energia ou rede residencial | Alta | Baixo | Trilha local é opcional e nunca é o provedor primário |

**14.2 Premissas**

| ID | Premissa |
|---|---|
| P-01 | O dispositivo Echo está vinculado à mesma conta Amazon da conta de desenvolvedor |
| P-02 | Existe conexão de internet estável no ambiente do dispositivo |
| P-03 | O usuário aceita que a skill opere em modo desenvolvimento, sem publicação |
| P-04 | O usuário aceita a política de uso de dados dos provedores gratuitos para conteúdo não sensível |
| P-05 | A trilha local, se adotada, roda em máquina do próprio usuário |

---

### 15. Backlog para versões futuras

| ID | Item | Valor esperado | Complexidade |
|---|---|---|---|
| B-01 | Memória de longo prazo entre sessões | Assistente lembra de fatos ditos em dias anteriores | Média |
| B-02 | Ferramentas via chamada de função (agenda, clima, tarefas) | Ações reais e não apenas respostas | Alta |
| B-03 | RAG sobre documentos pessoais | Respostas sobre conteúdo próprio | Alta |
| B-04 | Perfil editável por voz ("lembre que...") | Personalização sem editar arquivo | Média |
| B-05 | Métrica de latência por provedor ao longo do tempo | Escolha do provedor primário baseada em dado | Baixa |
| B-06 | Suporte a dispositivos com tela | Resposta visual complementando a fala | Média |

---

### 16. Glossário

| Termo | Definição |
|---|---|
| ASR | Automatic Speech Recognition, conversão de áudio em texto |
| Carrier phrase | Palavras fixas que precisam acompanhar um slot de texto livre no modelo de interação |
| Cold start | Primeira execução de uma função serverless após período ocioso, com latência extra |
| Intent | Intenção mapeada no modelo de interação da Alexa |
| LLM | Large Language Model |
| Prompt de sistema | Instrução persistente que define o comportamento do modelo |
| Resposta progressiva | Fala curta emitida enquanto o backend ainda processa a resposta final |
| Skill | Aplicação de voz que estende a Alexa |
| Slot | Variável extraída da fala do usuário dentro de uma intent |
| Utterance | Frase de exemplo que o usuário pode dizer para acionar uma intent |
