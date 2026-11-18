import os
import sys
import logging
import shutil
from datetime import datetime

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

SCRIPT_NAME = "01_BHAS_main"

# Elenco di tutte le cartelle standard utilizzate dai vari moduli della suite
REQUIRED_DIRECTORIES = ["IN", "OUT", "FINAL", "TMP", "LOG", "MUSIC", "EXTRA"]

# ==========================================
# CONFIGURAZIONE DINAMICA DELLA CPU
# ==========================================
def calcola_parametri_cpu():
    total_threads = os.cpu_count() or 4
    physical_cores = max(2, total_threads // 2)
    if total_threads <= 4:
        max_workers, threads_per_worker = 2, max(1, total_threads // 2)
    elif total_threads <= 8:
        max_workers, threads_per_worker = 4, 2
    else:
        max_workers, threads_per_worker = physical_cores, 4
    return total_threads, max_workers, threads_per_worker

TOTAL_THREADS, MAX_WORKERS, THREADS_PER_WORKER = calcola_parametri_cpu()

def pulisci_schermo():
    """Pulisce la console del terminale ad avvio script."""
    os.system('cls' if os.name == 'nt' else 'clear')

def setup_logging():
    """Configura la cartella LOG e il file di log associato alla sessione."""
    log_dir = "LOG"
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = os.path.join(log_dir, f"{SCRIPT_NAME}_{timestamp}.log")
    
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        encoding="utf-8"
    )
    return log_filename

def stampa_intestazione():
    """Stampa in modo chiaro l'INIZIO con il nome dello script e l'hardware rilevato."""
    print("=" * 70)
    print(f" INIZIO ELABORAZIONE - SCRIPT: {SCRIPT_NAME}")
    print(f" [Hardware Rilevato] Thread logici: {TOTAL_THREADS} | Worker: {MAX_WORKERS} | Thread/Worker: {THREADS_PER_WORKER}")
    print("=" * 70)

def stampa_chiusura(successo=True):
    """Stampa in modo chiaro la FINE con il nome dello script e l'esito."""
    print("=" * 70)
    stato = "PROCESSO COMPLETATO CON SUCCESSO" if successo else "PROCESSO TERMINATO CON ERRORI"
    print(f" FINE ELABORAZIONE [{SCRIPT_NAME}] - {stato}")
    print("=" * 70)

def setup_directories():
    """Verifica la presenza delle cartelle nella dir root e le crea se non esistenti con barra di avanzamento."""
    print("\n[Fase 1] Controllo e creazione cartelle di sistema nella directory root...")
    
    iterabile = REQUIRED_DIRECTORIES
    if tqdm is not None:
        iterabile = tqdm(REQUIRED_DIRECTORIES, desc="Verifica Cartelle", ncols=65, ascii=" #")

    for directory in iterabile:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                logging.info(f"Cartella creata: '{directory}'")
            except Exception as e:
                logging.error(f"Impossibile creare la cartella '{directory}': {e}")
        else:
            logging.info(f"Cartella già esistente: '{directory}'")
    print("   [✔] Controllo e configurazione cartelle completato.")

def check_input_videos():
    """Verifica la presenza di file .mp4 nella cartella IN e suggerisce di inserirli se assenti."""
    print("\n[Fase 2] Controllo presenza file video nella cartella 'IN'...")
    in_dir = "IN"
    
    # Abilita i codici ANSI su Windows se necessario
    if os.name == 'nt':
        os.system('')
        
    if os.path.exists(in_dir):
        mp4_files = [f for f in os.listdir(in_dir) if f.lower().endswith('.mp4')]
        if not mp4_files:
            # Codici ANSI: \033[1m (Grassetto), \033[5m (Lampeggiante), \033[91m (Rosso acceso), \033[0m (Reset)
            messaggio_lampeggiante = "\033[1m\033[5m\033[91m[!] Attenzione: Nessun file '.mp4' trovato nella cartella 'IN'.\033[0m"
            
            print(f"   {messaggio_lampeggiante}")
            print("   💡 SUGGERIMENTO: Inserisci i file video MP4 nella cartella 'IN' prima di avviare le attività di elaborazione.")
            logging.warning("Cartella 'IN' vuota: nessun file MP4 trovato.")
        else:
            print(f"   [✔] Trovati {len(mp4_files)} file video MP4 nella cartella 'IN'.")
            logging.info(f"Trovati {len(mp4_files)} file MP4 in 'IN'.")
    else:
        print("   [!] Cartella 'IN' non trovata.")
        logging.error("Cartella 'IN' inesistente.")

def check_ffmpeg():
    """Verifica disponibilità di FFmpeg e FFprobe nel sistema."""
    print("\n[Fase 3] Verifica disponibilità di FFmpeg e FFprobe nel sistema...")
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        print("   [!] Attenzione: FFmpeg o FFprobe non sono installati o non sono presenti nel PATH.")
        logging.warning("FFmpeg o FFprobe non trovati nel PATH di sistema.")
        return False
    else:
        print("   [✔] FFmpeg e FFprobe rilevati correttamente.")
        logging.info("FFmpeg e FFprobe verificati con successo.")
        return True

def mostra_menu_principale():
    print("\n" + "=" * 70)
    print(" 🏀 BASKET HIGHLIGHTS AUTOMATION SYSTEM (BHAS) - MENU PRINCIPALE")
    print("=" * 70)
    print(" 1. Avvia unione video originali (02_BAHS_merge-originals.py)")
    print(" 2. Identifica timestamp dei canestri (03_BAHS_identify-timestamps.py)")
    print(" 3. Taglia e separa le clip dei canestri (04_BAHS_split-original.py)")
    print(" 4. Unisci le clip dei canestri con transizioni (05_BAHS_merge-clips.py)")
    print(" 5. Aggiungi sottofondo musicale (06_BAHS_add-music-overlay.py)")
    print(" 6. Aggiungi sovraimpressione testo/titoli (07_BAHS_add-text-overlay.py)")
    print(" 0. Esci")
    print("=" * 70)

def main():
    pulisci_schermo()           # 1. Pulizia console (clear) ad avvio script
    stampa_intestazione()       # 2. Console con intestazione chiara e nome script
    log_file = setup_logging()  # 4. Logging con data e ora salvati nella cartella LOG con nome script
    
    logging.info(f"INIZIO script principale {SCRIPT_NAME} (Thread CPU: {TOTAL_THREADS})")
    successo_processo = True

    try:
        # 3. Barra di avanzamento per le cartelle + controlli iniziali
        setup_directories()
        check_input_videos()    # Controllo file mp4 in IN con avviso lampeggiante e suggerimento
        check_ffmpeg()

        # Interfaccia di lancio rapido degli altri script
        while True:
            mostra_menu_principale()
            scelta = input("\n👉 Seleziona un'opzione (0-6): ").strip()

            if scelta == "1":
                print("\n🚀 Avvio di 02_BAHS_merge-originals.py...")
                os.system(f"{sys.executable} 02_BAHS_merge-originals.py")
            elif scelta == "2":
                print("\n🚀 Avvio di 03_BAHS_identify-timestamps.py...")
                os.system(f"{sys.executable} 03_BAHS_identify-timestamps.py")
            elif scelta == "3":
                print("\n🚀 Avvio di 04_BAHS_split-original.py...")
                os.system(f"{sys.executable} 04_BAHS_split-original.py")
            elif scelta == "4":
                print("\n🚀 Avvio di 05_BAHS_merge-clips.py...")
                os.system(f"{sys.executable} 05_BAHS_merge-clips.py")
            elif scelta == "5":
                print("\n🚀 Avvio di 06_BAHS_add-music-overlay.py...")
                os.system(f"{sys.executable} 06_BAHS_add-music-overlay.py")
            elif scelta == "6":
                print("\n🚀 Avvio di 07_BAHS_add-text-overlay.py...")
                os.system(f"{sys.executable} 07_BAHS_add-text-overlay.py")
            elif scelta == "0":
                print("\n👋 Chiusura del programma di controllo. Arrivederci!")
                logging.info("Chiusura manuale del sistema da parte dell'utente.")
                break
            else:
                print("\n[!] Scelta non valida. Inserisci un numero compreso tra 0 e 6.")

    except Exception as e:
        logging.exception(f"Errore critico nello script principale: {e}")
        successo_processo = False
    finally:
        stampa_chiusura(successo=successo_processo) # 2. Chiusura elaborazione stampata in modo chiaro
        print(f" Report salvato in: {log_file}")

if __name__ == "__main__":
    main()