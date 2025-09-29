## Tradutor Multilíngue Interativo BOT para Discord (IMTB-D)

Uma ferramenta que combina um **Bot de Tradução Relay** que traduz mensagens do Discord para o “idioma desejado”, uma **UI de Desktop (Tkinter)** para controle local e um **Console** que pode ser usado a partir do terminal.  
Os logs de tradução podem ser salvos em **JSONL** e um caminho de compartilhamento UNC (ex: `\\raspberrypi\IMTB-D\messages.jsonl`) também pode ser especificado.

- **Relay**: Bot do Discord e API HTTP local (`/bind`, `/send`, `/send_image`, `/stats`)

- **Adição do Relay r3**: **`/translate`** (recebe texto via HTTP e retorna **tradução via HTTP**)

- **UI**: Edição do .env, registro e envio de destinos, visualização de logs, **tradução de arquivos (pré-visualização ao vivo)**, inicia automaticamente o Relay quando em operação local

- **Console**: Vinculação e envio a partir do terminal. Exibição de logs em tempo real

> Requisitos: **Token do Bot do Discord** e **Chave da API do OpenAI** (configuração que não faz chamadas diretas para o OpenAI também é aceitável)

---

## Índice

- [Configuração](#configura%C3%A7%C3%A3o)

- [Requisitos](#requisitos)

- [.env (exemplo mínimo)](#env-exemplo-m%C3%ADnimo)

- [Como usar](#como-usar)
  
  - [A. Usando UI + Relay localmente](#a-usando-ui--relay-localmente)
  
  - [B. Conectando ao Relay remoto](#b-conectando-ao-relay-remoto)
  
  - [C. Console (terminal)](#c-console-terminal)

- [API (Relay)](#api-relay)
  
  - [/translate (nova r3)](#translate-nova-r3)
  
  - [/bind, /send, /send_image, /stats](#bind-send-send_image-stats)

- [Logs (JSONL)](#logs-jsonl)

- [Exemplo de integração com VS Code Wrapper](#exemplo-de-integra%C3%A7%C3%A3o-com-vs-code-wrapper)

- [Perguntas frequentes](#perguntas-frequentes)

- [Dicas de desenvolvimento/operacionais](#dicas-de-desenvolvimentooperacionais)

- [Licença](#licen%C3%A7a)

---

## Configuração (principais arquivos)

```
IMTB-D_relay.py      # Bot do Discord + API HTTP
IMTB-D_ui.py         # UI de Desktop (Tkinter)
IMTB-D_console.py    # Console para terminal
console_routes.json      # Armazenamento de destinos (escrita pela UI)
log/messages.jsonl       # Logs de tradução (JSON Lines)
```

---

## Requisitos

- Baixar os arquivos principais
- Python 3.10+ (ambiente que suporta Tkinter)
- `pip install -r requirements.txt` 

```bash
pip install -r requirements.txt
```

---

## .env (exemplo mínimo)

Crie um arquivo `.env` na raiz deste repositório.

```ini
DISCORD_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-********************************

# URL base do Relay (recomendado usar 127.0.0.1 durante a operação local da UI)
IMTBD_API_BASE=http://127.0.0.1:8765

# Configuração de vinculação (Listen) do Relay (padrão: 127.0.0.1:8765 se não configurado)
RELAY_HOST=127.0.0.1
RELAY_PORT=8765

# (opcional) Local de armazenamento do log de tradução
IMTBD_JSONL_PATH=\\\\raspberrypi\\IMTB-D\\messages.jsonl

# (opcional) Configurações relacionadas à tradução
OPENAI_MODEL=gpt-4o-mini
PREFERRED_LANG=ja
DEFAULT_REPLY_LANG=en
```

> Ao usar UNC no Linux/mac, é recomendável montar previamente e especificar o caminho normalmente. *IMTBD_JSONL_PATH é **case-sensitive** (Linux)*

---

## Como usar

### A. Usando UI + Relay localmente (mais rápido)

```bash
python IMTB-D_ui.py
```

- Se `IMTBD_API_BASE` for `http://127.0.0.1:8765` ou `localhost`,  
  a UI **ajudará automaticamente a iniciar o Relay** (após a inicialização, será exibido "API ready").
  
  ![setup.png](docs/images/setup.png)
  
  Edite o `.env` na aba "Setup" e **Salve .env**.

- Na aba "Destinations", vincule o destino (DM/Canal) → insira o texto → **Envie**.
  
  ![destinations.png](docs/images/destinations.png)

- O log na parte inferior refletirá o envio e recebimento.
  
  - Com o destino (DM/Canal) selecionado, clique em "Open Window" → uma tela de chat individual será aberta.
    
    ![chat_window2.png](docs/images/chat_window2.png)
  
  - Tradução de texto
    
    - Insira o texto na caixa na parte inferior da janela e pressione send ou Enter para enviar.
    
    - Para inserir várias linhas, use Ctrl+Enter para quebrar a linha.
  
  - Tradução de Imagem (Inpaint)
    
    - Arraste e solte uma imagem para realizar a tradução de imagem via inpainting.
    
    - Neste estágio, a qualidade não é muito boa, mas serve como referência.
      
      Antes da tradução
      
      ![origin.png](docs/images/origin.png)
      
      Após a tradução
      
      ![translated.png](docs/images/translated.png)

### B. Conectando ao Relay remoto (ex: Raspberry Pi)

- Inicie `IMTB-D_relay.py` no servidor (Pi, etc.),
- Configure `IMTBD_API_BASE` no `.env` da UI para `http://<server-ip>:8765`.  
- Neste caso, o Start/Stop da UI será desativado e funcionará em **modo remoto**.

### C. Console (terminal)

```bash
# Para canal
python IMTB-D_console.py --name general --channel 123456789012345678 --lang en

# Para DM
python IMTB-D_console.py --name bob --dm 987654321098765432 --lang en

# Digite diretamente na entrada padrão para enviar (logs serão exibidos em tempo real).
```

---

## API (Relay)

### `/translate` (nova r3)

**API genérica que traduz texto recebido via HTTP e retorna a tradução via HTTP**. Não passa pelo Discord.

- **POST** `/translate`

- **Request (JSON)**:
  
  `{ "text": "Hello world", "source": "en", "target": "ja" }`
  
  - `source`: `"en" | "ja" | "auto" | ""` (não especificado/auto/vazio será determinado automaticamente internamente)
  
  - `target`: padrão é `DEFAULT_REPLY_LANG` no `.env` (ex: `"ja"`)

- **Response (JSON)**:
  
  `{ "ok": true, "translated": "こんにちは世界", "source": "en", "target": "ja" }`

- **Exemplo: curl**
  
  `curl -sS -X POST "http://<server-ip>:8765/translate" \   -H "Content-Type: application/json" \   -d '{"text":"Hello","source":"en","target":"ja"}'`

- **Exemplo: PowerShell**
  
  `$b = @{ text="Hello"; source="en"; target="ja" } | ConvertTo-Json Invoke-RestMethod -Uri "http://<server-ip>:8765/translate" -Method Post -ContentType "application/json" -Body $b`

#### Promessa de retorno

- Quando `ok` é `true`, `translated` contém a tradução

- Em caso de falha, retorna `{ "ok": false, "error": "<message>" }` (HTTP 4xx/5xx)

---

### `/bind`, `/send`, `/send_image`, `/stats`

- `POST /bind` — Registra o nome do console e o destino (dm/canal, id, lang, etc.)

- `POST /send` — Envia texto para o console especificado (entrega ao Discord)

- `POST /send_image` — OCR de imagem → tradução → inpainting → envio

- `GET /stats` — Estado de inicialização e lista de vinculações> `/translate` é **ideal para responder diretamente ao cliente HTTP**, tornando-se a melhor opção para integração com ferramentas externas como o VS Code. O fluxo tradicional via Discord utiliza `/bind` e `/send`.

---

## Log (JSONL)

- Padrão: `log/messages.jsonl`. O local de salvamento pode ser alterado na variável `IMTBD_JSONL_PATH` do arquivo `.env`.  
- A interface do usuário faz o tail deste arquivo para exibição na tela. É possível visualizá-lo através de compartilhamento UNC.

---

## Exemplo de Integração com Wrapper do VS Code

- Configuração do lado da extensão: `mikeWrapper.endpoint = http://<server-ip>:8765/translate`

- Selecionar → **Substituir Seleção por Japonês** (ex: `Ctrl+Alt+K`) para **substituição imediata**

- Tradução da área de transferência (`Ctrl+Alt+J`), tradução ao passar o mouse, etc., seguem as configurações do lado da extensão.

---

## Perguntas Frequentes (FAQ)

**Q: Como escrever o caminho UNC no Windows?**  
A: No arquivo `.env`, deve-se escrever `\\raspberrypi\IMTB-D\messages.jsonl` com **duas barras invertidas**.  
   Devido à necessidade de escape no `.env`, o ideal é escrever `\\\\raspberrypi\\IMTB-D\\messages.jsonl`.

**Q: Aparece `fetch failed`**  
A: Pode ser que `localhost` esteja resolvendo em IPv6 e não consiga se conectar. Tente com **`127.0.0.1`**. Para conexões remotas, utilize `<server-ip>`.

**Q: Permission denied (escrita em `console_routes.json`)**  
A: Isso pode ocorrer se o editor mantiver o arquivo aberto (exclusivo) ou devido ao Acesso Controlado a Pastas do Windows. Altere o local de salvamento para o diretório do usuário ou feche o editor e execute novamente.

---

## Dicas de Desenvolvimento/Operação

- **Hot Reload do r3** (reinício ao salvar)
  
  `pip install watchdog watchmedo auto-restart -p "*.py" -d . -- python IMTB-D_relay_r3.py`

- **Execução em segundo plano (Linux, systemd)**
  
  `# /etc/systemd/system/imtb-relay.service [Unit] Description=IMTB-D Relay r3 After=network-online.target [Service] WorkingDirectory=/home/<user>/IMTB-D ExecStart=/home/<user>/IMTB-D/venv/bin/python IMTB-D_relay_r3.py Restart=always RestartSec=2 Environment=RELAY_HOST=0.0.0.0 RELAY_PORT=8765 [Install] WantedBy=multi-user.target`

- **Uso do Git**
  
  - Comitar a implementação do `/translate`, README e CHANGELOG
  
  - Não comitar o arquivo `.env` (fornecer `.env.example`)
  
  - O diretório `.vscode/` deve ser ignorado na maioria das vezes. Se necessário compartilhar, incluir apenas o mínimo sem informações confidenciais, como `extensions.json`/`tasks.json`, etc.

---

## Licença

Licença MIT