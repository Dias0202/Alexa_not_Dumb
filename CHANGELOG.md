# Changelog

Este projeto segue [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [0.1.2] - 2026-08-02

### Corrigido

- Removidas as diretivas `Dialog.ElicitSlot`, rejeitadas pelo endpoint Alexa-hosted neste fluxo com `AMAZON.SearchQuery`.
- Fluxo de conversa ajustado para usar a frase portadora `pergunte {pergunta}` em cada turno.
- Carregamento do runtime de LLM adiado para a pergunta, preservando a abertura da skill se uma dependência estiver indisponível.

### Validado

- Resposta de `LaunchRequest` não inclui diretivas de diálogo e mantém a sessão aberta.
- Falhas de configuração ou dependência do LLM retornam uma mensagem controlada, sem resposta Alexa inválida.

## [0.1.1] - 2026-08-02

### Corrigido

- Configuração local privada como contingência para indisponibilidade do painel S3 da Alexa-hosted.
- Documentação de implantação, segredos, versionamento e limitações da validação remota.

### Validado

- Modelo de interação compilado no Alexa Developer Console.
- `LaunchRequest` manual executado com status `SUCCESSFUL` contra a Lambda Alexa-hosted em `us-west-2`.

## [0.1.0] - 2026-08-02

### Adicionado

- Skill Alexa-hosted em Python para conversas em pt-BR.
- Captura livre por `AMAZON.SearchQuery` com elicitação de slot.
- Contexto limitado aos últimos três pares de mensagens da sessão.
- Roteador Groq, Gemini e Ollama local com prazo global e fallback.
- Normalização de texto para fala e resposta progressiva.
- Proxy autenticado opcional para Ollama local.
- Testes automatizados, configuração de qualidade e documentação operacional.
