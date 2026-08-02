# Assistente Conversacional Alexa com LLM

Skill Alexa-hosted, em pt-BR, que usa a Alexa para voz e um LLM para gerar respostas conversacionais. O backend foi desenhado para operar sem custo recorrente, usando provedores configuráveis de free tier e fallback em cadeia.

## Estado da versão

A versão atual é `0.1.0` (MVP implementado e testado localmente). O deploy no Alexa Developer Console, a criação das contas dos provedores e a validação em um Echo são etapas manuais e ainda não podem ser confirmadas sem as respectivas credenciais e dispositivo.

## Arquitetura

```mermaid
flowchart LR
    Echo["Echo"] --> Alexa["Alexa: ASR, NLU e TTS"]
    Alexa --> Skill["Skill Alexa-hosted"]
    Skill --> Router["Roteador com prazo"]
    Router --> Groq["Groq"]
    Router --> Gemini["Gemini"]
    Router --> Proxy["Proxy autenticado opcional"]
    Proxy --> Ollama["Ollama local"]
    Skill --> Session["Atributos de sessao"]
    Skill --> S3["Configuracao no S3"]
```

## Estrutura

```text
lambda/                 Backend a ser enviado para a Alexa-hosted skill
models/                 Modelo de interação pt-BR para importar no console
local_proxy/            Proxy FastAPI opcional para Ollama local
config/                 Exemplo seguro da configuração externa
tests/                  Testes unitários e de integração local
docs/                   Guia de implantação, testes manuais e releases
```

## Desenvolvimento local

Requer Python 3.11 ou superior.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
pytest
ruff check .
```

O código em `lambda/` é carregado pelo runtime Alexa-hosted. Os testes adicionam esse diretório ao `sys.path` apenas para execução local.

## Configuração e segredos

1. Crie uma skill **Alexa-hosted (Python)** no Alexa Developer Console, locale pt-BR.
2. Importe `models/pt-BR.json` na aba **Build > Interaction Model > JSON Editor** e construa o modelo.
3. Copie os arquivos de `lambda/` para o repositório hospedado da skill, preservando os nomes na raiz do código Lambda.
4. Copie `config/llm.example.json`, preencha as chaves e envie o resultado como `config/llm.json` para o bucket S3 provisionado pela skill.

O arquivo real `config/llm.json` é ignorado pelo Git. Nunca coloque chaves em `lambda/`, no histórico Git ou em logs. Veja o procedimento completo em [docs/implantacao.md](docs/implantacao.md).

## Uso

Após invocar a skill, diga uma das frases iniciais, por exemplo: “pergunte qual a capital de Minas Gerais”. Nos turnos seguintes, a diretiva de elicitação captura a próxima fala livremente. Diga “para” ou “cancela” para encerrar.

## Limitações conhecidas

- A Alexa exige uma frase portadora no primeiro turno; captura totalmente livre só ocorre após a elicitação do slot.
- O orçamento rígido de oito segundos é externo à aplicação. Provedores lentos, cold start ou rede podem levar à mensagem controlada de indisponibilidade.
- A memória é apenas da sessão atual; não há retenção entre sessões nesta versão.
- Free tiers, políticas de provedores e compatibilidade de modelos mudam. Revise limites antes do deploy.
- A trilha Ollama é opcional, pode exceder o prazo e exige proxy autenticado mais Tailscale Funnel. Nunca exponha a porta 11434 diretamente.
- O teste no simulador e no Echo, bem como o envio do objeto S3 com segredos, exigem ações no console e não foram automatizados por segurança.

## Versionamento local

O fluxo local usa `main` para versões estáveis e `develop` para integração. As versões estão registradas em `VERSION`, `CHANGELOG.md` e `docs/releases/`. Nenhum remoto é configurado ou recebe push nesta etapa.

## Documentos de referência

- [PDD](Memory/PDD-assistente-alexa-llm.md)
- [SDD](Memory/SDD-assistente-alexa-llm.md)
- [Implantação](docs/implantacao.md)
- [Validação manual](docs/validacao-manual.md)
