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

# Cartelle soggette a pulizia automatica con l'opzione 0
CLEANUP_DIRECTORIES = ["FINAL", "OUT", "TMP"]

# Estensioni video supportate dai controlli
SUPPORTED_VIDEO_EXTS = ('.mp4', '.mov', '.avi', '.mkv', '.m4v', '.webm')

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
    """Configura la cartella LOG e il file di log associato alla sessione (creato solo su richiesta di elaborazione)."""
    log_dir = "LOG"
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = os.path.join(log_dir, f"{SCRIPT_NAME}_{timestamp}.log")
    
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

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
            except Exception as e:
                print(f"   [X] Errore creazione cartella '{directory}': {e}")

def check_input_videos():
    """Verifica la presenza di file video supportati nella cartella IN e suggerisce di inserirli se assenti."""
    print("\n[Fase 2] Controllo presenza file video nella cartella 'IN'...")
    in_dir = "IN"
    
    if os.name == 'nt':
        os.system('')
        
    if os.path.exists(in_dir):
        video_files = [f for f in os.listdir(in_dir) if f.lower().endswith(SUPPORTED_VIDEO_EXTS)]
        if not video_files:
            messaggio_lampeggiante = f"\033[1m\033[5m\033[91m[!] Attenzione: Nessun file video valido ({', '.join(SUPPORTED_VIDEO_EXTS)}) trovato nella cartella 'IN'.\033[0m"
            print(f"   {messaggio_lampeggiante}")
            print(f"   💡 SUGGERIMENTO: Inserisci i file video (es. .mp4, .mov, ecc.) nella cartella 'IN' prima di avviare le attività.")
        else:
            print(f"   [✔] Trovati {len(video_files)} file video supportati nella cartella 'IN'.")
    else:
        print("   [!] Cartella 'IN' non trovata.")

def check_ffmpeg():
    """Verifica disponibilità di FFmpeg e FFprobe nel sistema."""
    print("\n[Fase 3] Verifica disponibilità di FFmpeg e FFprobe nel sistema...")
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        print("   [!] Attenzione: FFmpeg o FFprobe non sono installati o non sono presenti nel PATH.")
        return False
    else:
        print("   [✔] FFmpeg e FFprobe rilevati correttamente.")
        return True

def pulisci_cartelle_lavoro():
    """Svuota e pulisce in automatico le cartelle di elaborazione (FINAL, OUT, TMP e log vecchi)."""
    print("\n🧹 Avvio pulizia automatica delle cartelle di lavoro...")
    
    for directory in CLEANUP_DIRECTORIES:
        if os.path.exists(directory):
            try:
                for item in os.listdir(directory):
                    item_path = os.path.join(directory, item)
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                print(f"   [✔] Cartella pulita con successo: '{directory}'")
            except Exception as e:
                print(f"   [X] Errore durante la pulizia della cartella '{directory}': {e}")
        else:
            os.makedirs(directory, exist_ok=True)
            print(f"   [+] Cartella ricreata (perché inesistente): '{directory}'")

    log_dir = "LOG"
    if os.path.exists(log_dir):
        try:
            for item in os.listdir(log_dir):
                item_path = os.path.join(log_dir, item)
                try:
                    if os.path.isfile(item_path):
                        os.unlink(item_path)
                except Exception:
                    pass
            print(f"   [✔] Cartella log pulita (file attivi esclusi): '{log_dir}'")
        except Exception as e:
            print(f"   [X] Errore pulizia cartella '{log_dir}': {e}")

    print("✨ Pulizia completata con successo!\n")
    input("Premi [INVIO] per tornare al menu principale... ")

def mostra_menu_principale(ultima_scelta=None):
    """Mostra il menu con opzioni allineate e l'ultima eseguita evidenziata in verde lampeggiante."""
    if os.name == 'nt':
        os.system('')

    verde_lamp = "\033[1m\033[5m\033[92m"
    ciano = "\033[96m"
    giallo = "\033[93m"
    reset = "\033[0m"

    voci = [
        ("1", "Avvia unione video originali (02_BAHS_merge-originals.py)"),
        ("2", "Identifica timestamp dei canestri (03_BAHS_identify-timestamps.py)"),
        ("3", "Taglia e separa le clip dei canestri (04_BAHS_split-original.py)"),
        ("4", "Unisci le clip dei canestri con transizioni (05_BAHS_merge-clips.py)"),
        ("5", "Aggiungi sottofondo musicale (06_BAHS_add-music-overlay.py)"),
        ("6", "Aggiungi sovraimpressione testo/titoli (07_BAHS_add-text-overlay.py)")
    ]

    # Lunghezza fissa per garantire l'allineamento perfetto delle descrizioni
    larghezza_testo = 60

    print("\n" + "=" * 70)
    print(" 🏀 BASKET HIGHLIGHTS AUTOMATION SYSTEM (BHAS) - MENU PRINCIPALE")
    print("=" * 70)
    
    print("")
    print(f" {ciano}0. Vuoi eseguire pulizia delle cartelle (FINAL, OUT, LOG, TMP){reset}")
    print("")
    
    for num, descrizione in voci:
        testo_voce = f"{num}. {descrizione}".ljust(larghezza_testo)
        if ultima_scelta == num:
            print(f" {verde_lamp}{testo_voce} [ULTIMA ESEGUITA]{reset}")
        else:
            print(f" {testo_voce}")
            
    print("")
    print(f" {giallo}99. Esci{reset}")
    print("")
    print("=" * 70)

def main():
    pulisci_schermo()           
    stampa_intestazione()       
    
    successo_processo = True
    ultima_scelta_eseguita = None
    log_file = None

    try:
        setup_directories()
        check_input_videos()    
        check_ffmpeg()

        while True:
            mostra_menu_principale(ultima_scelta=ultima_scelta_eseguita)
            scelta = input("\n👉 Seleziona un'opzione (0-6 o 99): ").strip()

            if scelta == "0":
                pulisci_cartelle_lavoro()
                ultima_scelta_eseguita = None
            elif scelta in ["1", "2", "3", "4", "5", "6"]:
                if not log_file:
                    log_file = setup_logging()
                    logging.info(f"INIZIO script principale {SCRIPT_NAME} (Thread CPU: {TOTAL_THREADS})")

                script_mapping = {
                    "1": "02_BAHS_merge-originals.py",
                    "2": "03_BAHS_identify-timestamps.py",
                    "3": "04_BAHS_split-original.py",
                    "4": "05_BAHS_merge-clips.py",
                    "5": "06_BAHS_add-music-overlay.py",
                    "6": "07_BAHS_add-text-overlay.py"
                }
                nome_script_target = script_mapping[scelta]
                print(f"\n🚀 Avvio di {nome_script_target}...")
                logging.info(f"Lancio sottoscript: {nome_script_target}")
                
                os.system(f"{sys.executable} {nome_script_target}")
                ultima_scelta_eseguita = scelta
                
            elif scelta == "99":
                print("\n👋 Chiusura del programma di controllo. Arrivederci!")
                if log_file:
                    logging.info("Chiusura manuale del sistema da parte dell'utente.")
                break
            else:
                print("\n[!] Scelta non valida. Inserisci un'opzione corretta dal menu.")

    except Exception as e:
        if log_file:
            logging.exception(f"Errore critico nello script principale: {e}")
        else:
            print(f"\n[X] Errore critico: {e}")
        successo_processo = False
    finally:
        if log_file:
            print(f"\n Report salvato in: {log_file}")
            logging.info(f"FINE script principale {SCRIPT_NAME}")
        stampa_chiusura(successo=successo_processo) 

if __name__ == "__main__":
    main()