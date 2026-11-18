# 🏀 BAHS - Basketball Automation Highlights Suite

Una suite modulare ad alta precisione, **manual-first**, progettata per la creazione di video highlight di pallacanestro. 
Il sistema unisce il controllo umano totale (per un'accuratezza del 100% rispetto ai falsi positivi dell'IA) all'automazione spinta delle fasi di estrazione video e montaggio tramite **FFmpeg**.

Il progetto è suddiviso in due componenti principali:
1. **`01_BAHS_main.py`** : script di governo della suite
2. **`02_BAHS_merge-originals.py`** : script che si occupa di unire eventuali video frammentati ma facenti parte dello stesso match
3. **`03_BAHS_identify-timestamps.py`** : script per il salvataggio del timestamp canestro, salvato nella cartella **IN** nel file **timestamp.txt**
4. **`04_BAHS_split-original.py`** : script relativo allo split del video della partita nelle corrispettive clips derivate dai timestamps
5. **`05_BAHS_merge-clips.py `** : script di merge delle varie clips canestro con effetto di transizione fade in/out
6. **`06_BAHS_add-music-overlay.py`** : script che si occupa di aggiungere lo strato musicale mantenendo audio originale in sottofondo
7. **`07_BAHS_add-text-overlay.py`** : script dedicato alla sovraimpressione dinamica del campionato e delle squadre presenti nelle riprese

Gli script devono avere le seguenti caratteristiche di base:
1. **pulizia console (clear)** : ad avvio script puliza della console di elaborazione
2. **console con intestazione e chiusura elaborazione** : stampare in modo chiaro INIZIO/FINE con indicato il nome dello script elaborato
3. **barra di avanzamento dello stato di elaborazione** : deve sempre essere presente una barra con lo stato di elaborazione delle azioni richieste
4. **logging con data e ora salvati nella cartella LOG** : deve sempre esserci un log relativo alla sessione di elaborazione che inizi con il nome dello script

---

## 📁 Struttura del Progetto

```text
📁 BAHS/
│
├── 📄 01_BAHS_main.py      			# Script generale per la gestione delle varie fasi di elaborazione
├── 📄 02_BAHS_merge-originals.py      	# Motore di unione automatica di eventuali video frammentati
├── 📄 03_BAHS_identify-timestamps.py	# Player interattivo per la registrazione dei canestri (timestamps)
├── 📄 04_BAHS_split-original.py       	# Motore di estrazione clips da video originale
├── 📄 05_BAHS_merge-clips.py     		# Motore dedicato al merge delle clips con effetti di transizione
├── 📄 06_BAHS_add-music-overlay.py    	# Motore di inserimento musica ed effetti
├── 📄 07_BAHS_add-text-overlay.py		# Motore text overlay a video
├── 📄 readme.md		        		# Readme progetto BAHS
├── 📄 requirements.txt         		# Dipendenze e pacchetti necessari
│
├── 📁 EXTRA/                      		# Cartella di input relativa ad oggetti custom da aggiungere
│	├── 📁 MUSIC/						# Cartella di backup musica (da spostare nel folder MUSIC principale)
│	├── 📁 FONT/						# Cartella di backup font (da spostare nel folder EXTRA principale)
│   ├── 📄 copertina_IN.jpg       		# Esempio di copertina IN (inizio video)
│   ├── 📄 copertina_OUT.jpg      		# Esempio di copertina OUT (fine video)
│   ├── 📄 logo_x.jpg      				# Esempio di logo squadra personalizzato
│   └── 📄 font.ttf       				# Font dedicato al testo
│
├── 📁 FINAL/							# Cartella di output montaggio finale
│                    					
├── 📁 IN/                      		# Cartella di input (metti qui i video grezzi e i timestamp)
│   ├── 📄 1.mp4       					# Esempio di video partita primo/secondo quarto
│   ├── 📄 2.mp4      					# Esempio di video partita terzo/quarto quarto
│   └── 📄 timestamps.txt       		# File contenente i timestamps partita
│
├── 📁 LOG/                     		# File di log dettagliati delle sessioni di elaborazione
│
├── 📁 MUSIC/                     		# File MP3 musica dedicata (open source)
│
└── 📁 OUT/                     		# Cartella di output relativamente alle elaborazioni intermedie
```

---

## ⚙️ Prerequisiti e Installazione (Windows 11)

### 1. Python 3.11+
Assicurati di avere Python installato sul sistema (spuntando *Add Python to PATH* durante l'installazione).

### 2. FFmpeg & FFprobe
Gli script si appoggiano a FFmpeg per la manipolazione video:
1. Scarica l'ultima versione di FFmpeg per Windows (build Essentials) da [gyan.dev](https://www.gyan.dev/ffmpeg/builds/).
2. Estrai la cartella (es. in `C:\ffmpeg`).
3. Aggiungi il percorso `C:\ffmpeg\bin` alle **Variabili d'ambiente di sistema (PATH)** di Windows 11.
4. Verifica l'installazione da terminale:
   ```bash
   ffmpeg -version
   ```

### 3. Dipendenze Python
Assicurati di avere un file `requirements.txt` nella cartella principale con questo contenuto:
```text
opencv-python>=4.8.0
tqdm>=4.65.0
```
Installa i pacchetti aprendo il terminale nella cartella del progetto:
```bash
pip install -r requirements.txt
```

---