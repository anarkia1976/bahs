import os
import logging
from datetime import datetime
import subprocess

# Tentativo di importare tqdm per una barra di avanzamento grafica professionale
try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

# Nome dello script di riferimento
NOME_SCRIPT = "02_BAHS_merge-originals"

def pulisci_schermo():
    """1. Pulisce la console di elaborazione all'avvio."""
    os.system('cls' if os.name == 'nt' else 'clear')

def configura_logging():
    """4. Configura il logging con data e ora salvato nella cartella LOG,
    iniziando con il nome dello script."""
    cartella_log = "LOG"
    os.makedirs(cartella_log, exist_ok=True)
    timestamp_file = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    percorso_file_log = os.path.join(cartella_log, f"{NOME_SCRIPT}_{timestamp_file}.log")

    formato_log = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Evita la duplicazione degli handler se la funzione viene richiamata più volte
    if not logger.handlers:
        handler_console = logging.StreamHandler()
        handler_console.setFormatter(formato_log)
        logger.addHandler(handler_console)

        handler_file = logging.FileHandler(percorso_file_log, encoding='utf-8')
        handler_file.setFormatter(formato_log)
        logger.addHandler(handler_file)

    logging.info(f"Sistema di log inizializzato. File salvato in: {percorso_file_log}")

def stampa_intestazione():
    """2. Stampa in modo chiaro l'INIZIO con il nome dello script."""
    print("=" * 65)
    print(f" INIZIO ELABORAZIONE - SCRIPT: {NOME_SCRIPT}")
    print("=" * 65)

def stampa_chiusura(successo=True):
    """2. Stampa in modo chiaro la FINE con il nome dello script e l'esito."""
    print("=" * 65)
    stato = "PROCESSO COMPLETATO CON SUCCESSO" if successo else "PROCESSO TERMINATO CON ERRORI"
    print(f" FINE ELABORAZIONE [{NOME_SCRIPT}] - {stato}")
    print("=" * 65)

def mostra_barra_avanzamento(iterabile, descrizione="Elaborazione"):
    """3. Gestisce la barra di avanzamento dello stato di elaborazione."""
    if tqdm is not None:
        return tqdm(iterabile, desc=descrizione, ncols=65, ascii=" #")
    else:
        # Fallback nel caso in cui la libreria tqdm non sia installata
        print(f"[{descrizione}] In corso...")
        return iterabile

def rimuovi_file_temporanei(cartelle_da_controllare, file_lista_temp="filelist.txt"):
    """Rimuove i file temporanei e la cartella TMP se vuota."""
    logging.info("Pulizia dei file temporanei residui...")
    
    if os.path.exists(file_lista_temp):
        try:
            os.remove(file_lista_temp)
            logging.info(f"Rimosso file temporaneo: {file_lista_temp}")
        except Exception:
            pass

    for cartella in cartelle_da_controllare:
        if os.path.exists(cartella):
            for file in os.listdir(cartella):
                try:
                    os.remove(os.path.join(cartella, file))
                except Exception:
                    pass
            try:
                if not os.listdir(cartella):
                    os.rmdir(cartella)
                    logging.info(f"Cartella temporanea '{cartella}' rimossa.")
            except Exception:
                pass

def unisci_video_ffmpeg(cartella_input="IN", cartella_output="OUT", cartella_tmp="TMP", nome_file_output="video_finale.mp4"):
    # 1. Pulizia console iniziale
    pulisci_schermo()
    
    # 2. Intestazione con nome script
    stampa_intestazione()
    
    # 4. Avvio logging
    configura_logging()
    
    successo_processo = True
    file_lista_temp = "filelist.txt"

    try:
        logging.info(f"Avvio procedura di unione rapida FFmpeg dalla cartella '{cartella_input}'.")

        if not os.path.exists(cartella_input):
            logging.error(f"La cartella '{cartella_input}' non esiste.")
            successo_processo = False
            return

        os.makedirs(cartella_output, exist_ok=True)
        os.makedirs(cartella_tmp, exist_ok=True)
        
        percorso_output = os.path.join(cartella_output, nome_file_output)

        file_video = sorted([
            f for f in os.listdir(cartella_input) 
            if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))
        ])

        if not file_video:
            logging.warning(f"Nessun file video trovato in '{cartella_input}'.")
            successo_processo = False
            return

        logging.info(f"Trovati {len(file_video)} video da unire in sequenza.")
        
        # 3. Barra di avanzamento per la scansione e scrittura della lista file
        with open(file_lista_temp, "w", encoding="utf-8") as f:
            for file in mostra_barra_avanzamento(file_video, descrizione="Scansione Video"):
                percorso_completo = os.path.abspath(os.path.join(cartella_input, file))
                f.write(f"file '{percorso_completo.replace(os.sep, '/')}'\n")
                logging.info(f" - Aggiunto alla sequenza: {file}")

        logging.info("Esecuzione unione istantanea tramite FFmpeg (Stream Copy)...")
        
        comando = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", file_lista_temp,
            "-c", "copy",
            percorso_output
        ]

        # Esecuzione del processo FFmpeg
        processo = subprocess.run(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if processo.returncode != 0:
            logging.error(f"Errore durante l'esecuzione di FFmpeg:\n{processo.stderr}")
            successo_processo = False
        else:
            logging.info(f"Video unito ed esportato con successo in: {percorso_output}")

    except Exception as e:
        logging.exception(f"Errore critico: {e}")
        successo_processo = False
        
    finally:
        # Pulizia file temporanei
        rimuovi_file_temporanei([cartella_tmp], file_lista_temp)
        
        # 2. Chiusura ufficiale come ultima operazione
        stampa_chiusura(successo=successo_processo)

if __name__ == "__main__":
    unisci_video_ffmpeg(
        cartella_input="IN", 
        cartella_output="OUT",
        cartella_tmp="TMP",
        nome_file_output="video_finale.mp4"
    )