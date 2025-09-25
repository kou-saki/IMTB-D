# Interactive Multilingual Translator BOT for Discord(IMTB-D)

Um **Bot de Tradução Relay** que permite ler e escrever mensagens do Discord em “qualquer idioma”,
com uma **UI de Desktop (Tkinter)** para operação local e um **Console** utilizável a partir do terminal. (Suporte atual em 2025/09/08: en, ja, zh, ko, es, fr, de, it, pt, ru, id, vi, th)
Os logs de tradução podem ser salvos em **JSONL**, e um caminho de compartilhamento UNC (ex: `\\raspberrypi\IMTB-D\messages.jsonl`) também pode ser especificado.

- **Relay**: Bot do Discord e API HTTP local (`/bind`, `/send`, `/send_image`, `/stats`).
- **UI**: Edição do .env, registro e envio de destinos, visualização de logs, **tradução de arquivos (visualização ao vivo)**, iniciação automática do Relay quando em modo local.
- **Console**: Vinculação e envio a partir do terminal. Exibição de logs em tempo real.

> Requisitos: **Token do Bot do Discord** e **Chave da API do OpenAI**.

---

## Estrutura (Arquivos principais)

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
- Python 3.10+ (Ambiente que suporte Tkinter)
- `pip install -r requirements.txt` 

```bash
pip install -r requirements.txt
```

---

## .env (Exemplo mínimo)

Crie um arquivo `.env` na raiz deste repositório.

```ini
DISCORD_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-********************************

# Para uso local, recomenda-se localhost (a UI inicia o Relay automaticamente)
IMTBD_API_BASE=http://127.0.0.1:8765

# (Opcional) Caminho para salvar logs. Windows usa UNC, Linux/mac pode usar caminho normal
IMTBD_JSONL_PATH=\\\\raspberrypi\\IMTB-D\\messages.jsonl

# (Opcional) Configurações de tradução
OPENAI_MODEL=gpt-4o-mini
PREFERRED_LANG=ja
DEFAULT_REPLY_LANG=en
```

> Ao usar UNC no Linux/mac, é mais seguro montar previamente e especificar o caminho normal. *IMTBD_JSONL_PATH é **case-sensitive** (Linux)*

---

## Como usar

### A. Usar UI + Relay localmente (mais rápido)

```bash
python IMTB-D_ui.py
```

- Se `IMTBD_API_BASE` for `http://127.0.0.1:8765` ou `localhost`,  
  a UI **ajudará automaticamente a iniciar o Relay** (após a inicialização, exibirá "API ready").
  
  ![setup.png](docs/images/setup.png)
  
  Edite o `.env` na aba "Setup" e **Salve .env**.

- Na aba "Destinations", **Bind** o destino (DM/Canal) → insira o texto → **Send**.
  
  ![destinations.png](docs/images/destinations.png)

- O log na parte inferior refletirá o envio e recebimento.
  
  - Com o destino (DM/Canal) selecionado, clique em "Open Window" → uma tela de chat individual será aberta.
    
    ![chat_window2.png](docs/images/chat_window2.png)
  
  - Tradução de texto
    
    - Insira o texto na caixa na parte inferior da janela e pressione send ou Enter para enviar.
    
    - Para inserir várias linhas, use Ctrl+Enter para nova linha.
  
  - Tradução de Imagem (Inpaint)
    
    - Arraste e solte uma imagem para realizar a tradução de imagem via inpainting.
    
    - Neste estágio, a qualidade não é muito boa, mas serve como referência.
      
      Antes da tradução
      
      ![origin.png](docs/images/origin.png)
      
      Após a tradução
      
      ![translated.png](docs/images/translated.png)

### B. Conectar ao Relay remoto (ex: Raspberry Pi)

- Inicie `IMTB-D_relay.py` no servidor (Pi, etc.),
- Configure o `.env` da UI com `IMTBD_API_BASE` para `http://<server-ip>:8765`.  
- Nesse caso, o Start/Stop da UI será desativado, funcionando em **modo remoto**.

### C. Console (terminal)

```bash
# Para canal
python IMTB-D_console.py --name general --channel 123456789012345678 --lang en

# Para DM
python IMTB-D_console.py --name bob --dm 987654321098765432 --lang en

# Digite diretamente na entrada padrão para enviar (logs são exibidos em tempo real).
```

---

## API (Relay)

- `POST /bind` — Registra o nome do console e o destino (dm/canal, id, lang)  
- `POST /send` — Envia texto para o console especificado (pode ser temporariamente sobrescrito com `lang`)  
- `POST /send_image` — OCR da imagem → tradução → inpainting e desenho → envio  
- `GET  /stats` — Estado de inicialização e lista de vinculações

---

## Logs (JSONL)

- Padrão: `log/messages.jsonl`. O caminho de salvamento pode ser alterado em `IMTBD_JSONL_PATH` no `.env`.  
- A UI faz tail deste arquivo para exibição na tela. Também é acessível através de compartilhamento UNC.

---

## Perguntas Frequentes (FAQ)

**Q: Como escrever o caminho UNC no Windows?**  
A: No `.env`, escreva `\\raspberrypi\IMTB-D\messages.jsonl` com **duas barras invertidas**.  
   Devido à necessidade de escape no `.env`, é mais seguro escrever `\\\\raspberrypi\\IMTB-D\\messages.jsonl`.

---

## Licença

Licença MIT