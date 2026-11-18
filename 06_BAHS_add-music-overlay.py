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
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "video_finale_merged_music.mp4")
TMP_DIR = "TMP"
LOG_DIR = "LOG"

MUSIC_VOLUME = 0.6
ORIGINAL_AUDIO_VOLUME = 0.4

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

def setup_directories():
    for directory in [INPUT_DIR, MUSIC_DIR, TMP_DIR, LOG_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)

def setup_logging():
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
    os.system('cls' if os.name == 'nt' else 'clear')

def check_ffmpeg():
    if shutil.which("ffmpeg") is None:
        print("\n[X] Errore: FFmpeg non è installato o non è presente nel PATH.")
        sys.exit(1)

def cleanup_tmp():
    if os.path.exists(TMP_DIR):
        try:
            shutil.rmtree(TMP_DIR)
        except Exception:
            pass

def main():
    clear_console()
    log_file = setup_logging()
    
    print("=" * 70)
    print(f" INIZIO ELABORAZIONE (Mix Audio): {SCRIPT_NAME}")
    print(f" [Hardware Rilevato] Thread logici: {TOTAL_THREADS} | Worker: {MAX_WORKERS} | Thread/Worker: {THREADS_PER_WORKER}")
    print(f" Video Input: '{INPUT_VIDEO}' | Cartella Musica: '{MUSIC_DIR}'")
    print(f" Bilanciamento -> Musica: {int(MUSIC_VOLUME*100)}% | Pubblico: {int(ORIGINAL_AUDIO_VOLUME*100)}%")
    print("=" * 70)
    
    logging.info(f"INIZIO elaborazione script {SCRIPT_NAME} (Thread CPU: {TOTAL_THREADS})")
    check_ffmpeg()
    setup_directories()

    try:
        if not os.path.exists(INPUT_VIDEO):
            print(f"\n[!] Errore: File video '{INPUT_VIDEO}' non trovato.")
            return

        supported_audio_exts = ('.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg')
        music_files = sorted([f for f in os.listdir(MUSIC_DIR) if f.lower().endswith(supported_audio_exts)])
        
        if not music_files:
            print(f"\n[!] Nessun file musicale trovato nella cartella '{MUSIC_DIR}'.")
            return

        selected_music = music_files[0]
        music_path = os.path.join(MUSIC_DIR, selected_music)
        print(f"\nTraccia musicale selezionata: '{selected_music}'")

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
            "-threads", str(TOTAL_THREADS),
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
            print(f"\n\n[✔] Elaborazione completata! File: {OUTPUT_FILE}")
        else:
            print(f"\n\n[X] Errore durante l'esecuzione di FFmpeg.")

    except Exception as e:
        print(f"\n[X] Errore critico: {e}")
    finally:
        cleanup_tmp()

    print("\n" + "=" * 70)
    print(f" FINE ELABORAZIONE: {SCRIPT_NAME}")
    print(f" Report salvato in: {log_file}")
    print("=" * 70)

if __name__ == "__main__":
    main()