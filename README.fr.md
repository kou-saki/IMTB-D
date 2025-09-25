# Interactive Multilingual Translator BOT for Discord(IMTB-D)

Un **Bot de traduction relais** qui permet de lire et d'écrire des messages Discord dans la langue de votre choix, un **UI de bureau (Tkinter)** pour le contrôler depuis votre appareil, et un **Console** utilisable depuis le terminal. (Support actuel au 2025/09/08 : en, ja, zh, ko, es, fr, de, it, pt, ru, id, vi, th) Les journaux de traduction peuvent être sauvegardés au format **JSONL**, et un chemin de partage UNC (ex : `\\raspberrypi\IMTB-D\messages.jsonl`) peut également être spécifié.

- **Relay** : Bot Discord et API HTTP locale (`/bind`, `/send`, `/send_image`, `/stats`).
- **UI** : Édition de .env, enregistrement et envoi de destinations, consultation des journaux, **traduction de fichiers (aperçu en direct)**, démarrage automatique de Relay en mode local.
- **Console** : Liaison et envoi depuis le terminal. Affichage en temps réel des journaux.

> Ce dont vous avez besoin : **Token de Bot Discord** et **Clé API OpenAI**.

---

## Structure (fichiers principaux)

```
IMTB-D_relay.py      # Bot Discord + API HTTP
IMTB-D_ui.py         # UI de bureau (Tkinter)
IMTB-D_console.py    # Console pour terminal
console_routes.json      # Sauvegarde des destinations (écrit par l'UI)
log/messages.jsonl       # Journal de traduction (JSON Lines)
```

---

## Exigences

- Télécharger les fichiers principaux
- Python 3.10+ (environnement avec Tkinter)
- `pip install -r requirements.txt` 

```bash
pip install -r requirements.txt
```

---

## .env (exemple minimal)

Créez un fichier `.env` à la racine de ce dépôt.

```ini
DISCORD_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-********************************

# Pour une utilisation locale, il est recommandé d'utiliser localhost (l'UI démarre Relay automatiquement)
IMTBD_API_BASE=http://127.0.0.1:8765

# (optionnel) Chemin de sauvegarde des journaux. Windows utilise UNC, Linux/mac peut utiliser un chemin normal
IMTBD_JSONL_PATH=\\\\raspberrypi\\IMTB-D\\messages.jsonl

# (optionnel) Paramètres de traduction
OPENAI_MODEL=gpt-4o-mini
PREFERRED_LANG=ja
DEFAULT_REPLY_LANG=en
```

> Lors de l'utilisation d'UNC sur Linux/mac, il est préférable de le monter au préalable et de spécifier un chemin normal. ※IMTBD_JSONL_PATH est **sensible à la casse** (Linux)

---

## Utilisation

### A. Utiliser l'UI + Relay localement (le plus court)

```bash
python IMTB-D_ui.py
```

- Si `IMTBD_API_BASE` est `http://127.0.0.1:8765` ou `localhost`,  
  l'UI **aide automatiquement au démarrage de Relay** (après le démarrage, "API ready" s'affiche).
  
  ![setup.png](docs/images/setup.png)
  
  Éditez le fichier `.env` depuis l'onglet « Setup » et **enregistrez .env**.

- Dans l'onglet « Destinations », **Liez** une destination (DM/Channel) → saisissez le texte → **Envoyer**.
  
  ![destinations.png](docs/images/destinations.png)

- Les envois et réceptions seront reflétés dans le journal en bas.
  
  - Cliquez sur « Open Window » tout en ayant une destination (DM/Channel) sélectionnée → une fenêtre de chat individuelle s'ouvrira.
    
    ![chat_window2.png](docs/images/chat_window2.png)
  
  - Traduction de texte
    
    - Saisissez le texte dans la boîte en bas de la fenêtre et appuyez sur send ou Enter pour l'envoyer.
    
    - Si plusieurs lignes sont nécessaires, vous pouvez faire un retour à la ligne avec Ctrl+Enter.
  
  - Traduction d'image (Inpaint)
    
    - En faisant glisser et déposer une image, vous pouvez effectuer une traduction d'image par inpainting.
    
    - Actuellement, ce n'est pas très propre, mais cela peut servir de référence.
      
      Avant traduction
      
      ![origin.png](docs/images/origin.png)
      
      Après traduction
      
      ![translated.png](docs/images/translated.png)

### B. Se connecter à un Relay distant (ex : Raspberry Pi)

- Démarrez `IMTB-D_relay.py` sur le serveur (Pi, etc.),
- Modifiez le `.env` de l'UI pour que `IMTBD_API_BASE` soit `http://<server-ip>:8765`.  
- Dans ce cas, les options Démarrer/Arrêter de l'UI seront désactivées et fonctionnera en **mode distant**.

### C. Console (terminal)

```bash
# Vers un canal
python IMTB-D_console.py --name general --channel 123456789012345678 --lang en

# Vers un DM
python IMTB-D_console.py --name bob --dm 987654321098765432 --lang en

# Tapez directement dans l'entrée standard pour envoyer (les journaux sont affichés en temps réel).
```

---

## API (Relay)

- `POST /bind` — Enregistre le nom de la console et la destination (dm/channel, id, lang)  
- `POST /send` — Envoie du texte à la console spécifiée (peut être temporairement écrasé par `lang`)  
- `POST /send_image` — OCR d'image → traduction → inpainting & dessin → envoi  
- `GET  /stats` — État de démarrage et liste des liaisons

---

## Journal (JSONL)

- Par défaut : `log/messages.jsonl`. Vous pouvez changer le chemin de sauvegarde avec `IMTBD_JSONL_PATH` dans le fichier `.env`.  
- L'UI suit ce fichier et l'affiche à l'écran. Il est également possible de le consulter via un partage UNC.

---

## Questions Fréquemment Posées (FAQ)

**Q : Comment écrire un chemin UNC sous Windows ?**  
R : Dans le fichier `.env`, écrivez `\\raspberrypi\IMTB-D\messages.jsonl` avec **deux barres obliques inverses**.  
   En raison de l'échappement dans `.env`, il est préférable d'écrire `\\\\raspberrypi\\IMTB-D\\messages.jsonl`.

---

## Licence

Licence MIT