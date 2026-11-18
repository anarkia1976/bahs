import os
import sys
import logging
import subprocess
import shutil
from datetime import datetime
from tqdm import tqdm

SCRIPT_NAME = "05_BAHS_merge-clips.py"
INPUT_DIR = "OUT"
OUTPUT_DIR = "FINAL"
TMP_DIR = "TMP"
LOG_DIR = "LOG"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "video_finale_merged.mp4")
FILE_PREFIX = "canestro_"
FADE_DURATION = 1.0

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
    for directory in [INPUT_DIR, OUTPUT_DIR, TMP_DIR, LOG_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)

def setup_logging():
    setup_directories()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(LOG_DIR, f"05_BAHS_merge-clips_{timestamp}.log")
    
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
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        print("\n[X] Errore: FFmpeg o FFprobe non sono installati o non sono presenti nel PATH.")
        logging.error("FFmpeg o FFprobe non trovati nel sistema.")
        sys.exit(1)

def cleanup_tmp():
    if os.path.exists(TMP_DIR):
        try:
            shutil.rmtree(TMP_DIR)
            logging.info(f"Cartella temporanea '{TMP_DIR}' pulita ed eliminata con successo.")
        except Exception as e:
            logging.warning(f"Impossibile rimuovere completamente la cartella '{TMP_DIR}': {e}")

def get_video_duration(file_path):
    cmd = [
        "ffprobe", "-v", "error", 
        "-show_entries", "format=duration", 
        "-of", "default=noprint_wrappers=1:nokey=1", 
        file_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0

def normalize_clip(input_path, output_path, is_first=False, is_last=False, duration=0.0):
    vf_filters = "fps=30,format=yuv420p"
    af_filters = "aresample=48000,aformat=channel_layouts=stereo"
    
    if is_first and duration > FADE_DURATION:
        vf_filters += f",fade=t=in:st=0:d={FADE_DURATION}"
        af_filters += f",afade=t=in:st=0:d={FADE_DURATION}"
        
    if is_last and duration > FADE_DURATION:
        start_fade_out = max(0, duration - FADE_DURATION)
        vf_filters += f",fade=t=out:st={start_fade_out}:d={FADE_DURATION}"
        af_filters += f",afade=t=out:st={start_fade_out}:d={FADE_DURATION}"

    cmd = [
        "ffmpeg", "-i", input_path,
        "-vf", vf_filters,
        "-af", af_filters,
        "-c:v", "libx264", "-crf", "18", "-preset", "slow",
        "-threads", str(TOTAL_THREADS),
        "-c:a", "aac", "-b:a", "192k",
        "-y", output_path
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.returncode == 0

def main():
    clear_console()
    log_file = setup_logging()
    
    print("=" * 70)
    print(f" INIZIO ELABORAZIONE (Fade In/Out + Transizioni): {SCRIPT_NAME}")
    print(f" [Hardware Rilevato] Thread logici: {TOTAL_THREADS} | Worker: {MAX_WORKERS} | Thread/Worker: {THREADS_PER_WORKER}")
    print(f" Input: '{INPUT_DIR}' | Output: '{OUTPUT_DIR}' | Durata Fade: {FADE_DURATION}s")
    print(f" Data e ora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    logging.info(f"INIZIO elaborazione script {SCRIPT_NAME} (Modalità Fade In/Out Completo - Thread CPU: {TOTAL_THREADS})")
    check_ffmpeg()

    try:
        setup_directories()
        mp4_files = sorted([
            f for f in os.listdir(INPUT_DIR) 
            if f.lower().startswith(FILE_PREFIX) and f.lower().endswith('.mp4')
        ])
        
        if not mp4_files:
            print(f"\n[!] Nessun file video trovato in '{INPUT_DIR}' che inizia con '{FILE_PREFIX}'.")
            return

        print(f"\nTrovati {len(mp4_files)} file validi in '{INPUT_DIR}'.")
        print("\n[Fase 1/2] Normalizzazione e applicazione Fade In/Out...")
        
        normalized_files = []
        total_files = len(mp4_files)
        
        for idx, file in enumerate(tqdm(mp4_files, desc="Normalizzazione", unit="file", colour="blue")):
            src_path = os.path.join(INPUT_DIR, file)
            dst_path = os.path.join(TMP_DIR, f"norm_{idx:03d}.mp4")
            orig_duration = get_video_duration(src_path)
            
            is_first = (idx == 0)
            is_last = (idx == total_files - 1)
            
            success = normalize_clip(src_path, dst_path, is_first=is_first, is_last=is_last, duration=orig_duration)
            if success:
                dur = get_video_duration(dst_path)
                normalized_files.append({"path": dst_path, "duration": dur})
            else:
                print(f"\n[X] Errore di normalizzazione per il file: {file}")
                return

        if len(normalized_files) == 1:
            shutil.copy(normalized_files[0]["path"], OUTPUT_FILE)
            print(f"\n[✔] Elaborazione completata! File generato: {OUTPUT_FILE}")
            return

        print("\n[Fase 2/2] Unione ad alta precisione con transizioni intermedie...")
        cmd = ["ffmpeg"]
        for info in normalized_files:
            cmd.extend(["-i", info["path"]])

        filter_complex = ""
        current_duration = normalized_files[0]["duration"]

        for i in range(len(normalized_files) - 1):
            next_duration = normalized_files[i + 1]["duration"]
            offset = max(0, current_duration - FADE_DURATION)

            v_in1 = f"[{i:d}:v]" if i == 0 else f"[v{i}]"
            v_in2 = f"[{i+1}:v]"
            v_out = f"[v{i+1}]" if i < len(normalized_files) - 2 else "[vout]"

            a_in1 = f"[{i:d}:a]" if i == 0 else f"[a{i}]"
            a_in2 = f"[{i+1}:a]"
            a_out = f"[a{i+1}]" if i < len(normalized_files) - 2 else "[aout]"

            filter_complex += f"{v_in1}{v_in2}xfade=transition=fade:duration={FADE_DURATION}:offset={offset}{v_out};"
            filter_complex += f"{a_in1}{a_in2}acrossfade=d={FADE_DURATION}{a_out};"
            current_duration = offset + next_duration

        cmd.extend([
            "-filter_complex", filter_complex.rstrip(";"),
            "-map", "[vout]",
            "-map", "[aout]",
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "slow",
            "-threads", str(TOTAL_THREADS),
            "-c:a", "aac",
            "-b:a", "192k",
            "-y",
            OUTPUT_FILE
        ])

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8')
        for line in process.stdout:
            if "frame=" in line or "time=" in line:
                sys.stdout.write(f"\rRendering Preciso: {line.strip()[-60:]} ")
                sys.stdout.flush()

        process.wait()

        if process.returncode == 0:
            print(f"\n\n[✔] Elaborazione completata con successo! File: {OUTPUT_FILE}")
        else:
            print(f"\n\n[X] Errore durante il rendering finale di FFmpeg.")

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