# Implantação

## Pré-requisitos externos

- Conta Amazon Developer e Echo vinculados à mesma conta.
- Conta Groq e/ou Google AI Studio com chaves emitidas sem cartão de crédito.
- Para a trilha local: Ollama, Tailscale e uma máquina acessível durante o uso.

Essas contas, chaves e qualquer console externo não são criados por este repositório. Não há credenciais de exemplo funcionais.

## Skill hospedada

1. No Alexa Developer Console, crie uma skill do tipo **Custom** e **Alexa-hosted (Python)**, em pt-BR.
2. Use um nome de invocação de duas ou mais palavras que seja aceito pelo console. Se necessário, altere `models/pt-BR.json` e documente a alteração em uma nova release.
3. Importe `models/pt-BR.json` pelo JSON Editor. Caso `AMAZON.FallbackIntent` não esteja disponível no locale, remova apenas essa intent e seu handler correspondente.
4. Faça o build do modelo. A utterance de primeiro turno sempre contém uma carrier phrase; o slot sozinho existe somente dentro da configuração de diálogo.
5. No editor Code da skill hospedada, copie os quatro arquivos de `lambda/` e o conteúdo de `requirements.txt` para a raiz do projeto Lambda.
6. Faça o deploy pelo próprio console.

## Configuração no bucket da skill

1. Copie `config/llm.example.json` para um arquivo temporário fora do Git.
2. Preencha ao menos um provedor e mantenha em `ordem` apenas provedores completos.
3. Envie o arquivo para `config/llm.json` no bucket S3 provisionado para a skill.
4. Não registre ou imprima o conteúdo. A aplicação mantém o objeto em cache por container; uma rotação de chave pode exigir aguardar novo container ou redeploy para invalidar o cache imediatamente.

## Proxy Ollama opcional

No Windows, em um ambiente virtual independente:

```powershell
py -3.11 -m venv local_proxy\.venv
.\local_proxy\.venv\Scripts\Activate.ps1
pip install -r local_proxy\requirements.txt
$env:PROXY_TOKEN = '<token-longo-aleatorio>'
uvicorn proxy:app --host 127.0.0.1 --port 8080
```

Execute o comando a partir de `local_proxy/`. O proxy só escuta em loopback. Publique-o com Tailscale Funnel e registre a URL HTTPS e o mesmo token no objeto S3. Não exponha `11434` diretamente e não suba o token para o Git.

## Rollback

- Código: selecione a versão anterior no repositório Git hospedado da skill e faça deploy.
- Configuração: restaure a versão anterior do objeto `config/llm.json` no bucket.
- Modelo: restaure o JSON da release anterior e reconstrua o interaction model.

O rollback não é automático. Valide sempre o caminho de voz após uma alteração no console.
