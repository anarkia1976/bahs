import os
import sys
import logging
import subprocess
import shutil
from datetime import datetime
from tqdm import tqdm

SCRIPT_NAME = "06_BAHS_add-music-overlay.py"
INPUT_DIR = "FINAL"
INPUT_VIDEO = os.path.join(INPUT_DIR, "video_finale_merged.mp4")
MUSIC_DIR = "MUSIC"
OUTPUT_DIR = "FINAL"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "video_finale_merged_music.mp4")  # Nome aggiornato
TMP_DIR = "TMP"
LOG_DIR = "LOG"

# Bilanciamento Audio (60% musica, 40% pubblico/audio originale)
MUSIC_VOLUME = 0.6
ORIGINAL_AUDIO_VOLUME = 0.4

def setup_directories():
    """Crea le cartelle necessarie se non esistono."""
    for directory in [INPUT_DIR, MUSIC_DIR, TMP_DIR, LOG_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)

def setup_logging():
    """Configura il sistema di logging nella cartella LOG."""
    setup_directories()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(LOG_DIR, f"06_BAHS_add-music-overlay_{timestamp}.log")
    
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] - %(message)s",
        encoding="utf-8"
    )
    return log_filename

def clear_console():
    """Pulisce la console a seconda del sistema operativo."""
    os.system('cls' if os.name == 'nt' else 'clear')

def check_ffmpeg():
    """Verifica che FFmpeg sia installato e disponibile nel sistema."""
    if shutil.which("ffmpeg") is None:
        print("\n[X] Errore: FFmpeg non è installato o non è presente nel PATH del sistema.")
        logging.error("FFmpeg non trovato nel sistema.")
        sys.exit(1)

def cleanup_tmp():
    """Pulisce e rimuove la cartella temporanea TMP e il suo contenuto."""
    if os.path.exists(TMP_DIR):
        try:
            shutil.rmtree(TMP_DIR)
            logging.info(f"Cartella temporanea '{TMP_DIR}' pulita ed eliminata con successo.")
        except Exception as e:
            logging.warning(f"Impossibile rimuovere completamente la cartella '{TMP_DIR}': {e}")

def main():
    # 1. Pulizia console all'avvio
    clear_console()
    
    # Setup delle directory e del log
    log_file = setup_logging()
    
    # 2. Console con intestazione di inizio
    print("=" * 65)
    print(f" INIZIO ELABORAZIONE (Mix Audio): {SCRIPT_NAME}")
    print(f" Video Input: '{INPUT_VIDEO}' | Cartella Musica: '{MUSIC_DIR}'")
    print(f" Bilanciamento -> Musica: {int(MUSIC_VOLUME*100)}% | Pubblico: {int(ORIGINAL_AUDIO_VOLUME*100)}%")
    print(f" Data e ora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)
    
    logging.info(f"INIZIO elaborazione script {SCRIPT_NAME}")
    
    check_ffmpeg()
    setup_directories()

    try:
        # Verifica esistenza del video unito in precedenza
        if not os.path.exists(INPUT_VIDEO):
            print(f"\n[!] Errore: File video '{INPUT_VIDEO}' non trovato.")
            print("    Assicurati di aver prima eseguito lo script di merge delle clip.")
            logging.error(f"File video di input non trovato: {INPUT_VIDEO}")
            return

        # Ricerca della traccia musicale nella cartella MUSIC
        supported_audio_exts = ('.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg')
        music_files = sorted([
            f for f in os.listdir(MUSIC_DIR) 
            if f.lower().endswith(supported_audio_exts)
        ])
        
        if not music_files:
            print(f"\n[!] Nessun file musicale trovato nella cartella '{MUSIC_DIR}'.")
            print("    Aggiungi almeno un file audio (es. .mp3 o .wav) nella cartella MUSIC.")
            logging.warning(f"Nessun file audio trovato nella cartella '{MUSIC_DIR}'.")
            return

        selected_music = music_files[0]
        music_path = os.path.join(MUSIC_DIR, selected_music)
        
        print(f"\nTraccia musicale selezionata: '{selected_music}'")
        logging.info(f"Traccia musicale selezionata: {selected_music}")

        print("\nElaborazione e mixaggio tracce audio in corso (con FFmpeg)...")
        logging.info("Avvio mixaggio audio con FFmpeg.")

        cmd = [
            "ffmpeg",
            "-i", INPUT_VIDEO,
            "-stream_loop", "-1",
            "-i", music_path,
            "-filter_complex", 
            f"[0:a]volume={ORIGINAL_AUDIO_VOLUME}[original];[1:a]volume={MUSIC_VOLUME}[music];[original][music]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-y",
            OUTPUT_FILE
        ]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8')
        
        for line in process.stdout:
            if "time=" in line:
                sys.stdout.write(f"\rElaborazione in corso: {line.strip()[-50:]} ")
                sys.stdout.flush()

        process.wait()

        if process.returncode == 0:
            print(f"\n\n[✔] Elaborazione completata con successo!")
            print(f"    File generato: {OUTPUT_FILE}")
            logging.info("Elaborazione e mixaggio audio completati con successo.")
        else:
            print(f"\n\n[X] Errore durante l'esecuzione di FFmpeg.")
            logging.error("Errore durante l'esecuzione del comando FFmpeg per il mixaggio audio.")

    except Exception as e:
        print(f"\n[X] Errore critico durante l'elaborazione: {e}")
        logging.error(f"Errore critico: {e}", exc_info=True)

    finally:
        print("\nPulizia dei file temporanei in corso...")
        cleanup_tmp()

    # 2. Console con chiusura elaborazione
    print("\n" + "=" * 65)
    print(f" FINE ELABORAZIONE: {SCRIPT_NAME}")
    print(f" Report salvato in: {log_file}")
    print("=" * 65)
    logging.info(f"FINE elaborazione script {SCRIPT_NAME}")

if __name__ == "__main__":
    main()