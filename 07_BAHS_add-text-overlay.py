import os
import sys
import logging
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

SCRIPT_NAME = "07_BAHS_add-text-overlay.py"
INPUT_DIR = "FINAL"
DEFAULT_INPUT_VIDEO = os.path.join(INPUT_DIR, "video_finale_merged_music.mp4")
OUTPUT_FILE = os.path.join(INPUT_DIR, "video_finale_merged_music_text.mp4")
EXTRA_DIR = "EXTRA"
LOG_DIR = "LOG"
TMP_DIR = "TMP"

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
    for directory in [INPUT_DIR, EXTRA_DIR, TMP_DIR, LOG_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)

def setup_logging():
    setup_directories()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(LOG_DIR, f"07_BAHS_add-text-overlay_{timestamp}.log")
    
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
        print("\n[X] Errore: FFmpeg o ffprobe non sono installati nel PATH.")
        sys.exit(1)

def cleanup_tmp():
    if os.path.exists(TMP_DIR):
        try:
            shutil.rmtree(TMP_DIR)
        except Exception:
            pass

def apply_text_overlay(video_path, output_path, dynamic_text, duration=5.0, logger=None):
    setup_directories()
    extra_font = Path(EXTRA_DIR) / "font.ttf"
    tmp_font = Path(TMP_DIR) / "font.ttf"
    
    if extra_font.exists():
        shutil.copy(extra_font, tmp_font)
        if logger: logger.info("Copiato EXTRA/font.ttf in TMP.")
    else:
        print(f"\n[!] Attenzione: File font '{extra_font}' non trovato!")

    font_path = str(tmp_font).replace('\\', '/')
    base_x, base_y = 60, 810
    trans_time = 1.5
    start_x = -1600
    target_x = base_x

    x_expr = (
        f"if(lt(t\\,{trans_time})\\, "
        f"({start_x} + ({target_x} - ({start_x})) * (sin((t/{trans_time}) * 1.570796))) \\, "
        f"if(lt(t\\,{duration}-{trans_time})\\, "
        f"{target_x}\\, "
        f"({target_x} + ({start_x} - {target_x}) * sin(((t - ({duration}-{trans_time}))/{trans_time}) * 1.570796))"
        f")"
        f")"
    )

    alpha_expr = (
        f"if(lt(t\\,{trans_time})\\, t/{trans_time}\\, "
        f"if(lt(t\\,{duration}-{trans_time})\\, 1\\, "
        f"({duration}-t)/{trans_time}"
        f"))"
    )

    filter_complex = (
        f"[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
        f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p[v_norm];"
        f"[v_norm]drawtext=fontfile='{font_path}':text='HIGHLIGHTS':"
        f"fontcolor=white:fontsize=64:borderw=3:bordercolor=black:"
        f"x={base_x}:y={base_y}:alpha='{alpha_expr}':"
        f"enable='between(t,0,{duration})'[txt_top];"
        f"[txt_top]drawbox=x={base_x}:y={base_y}+72:w=750:h=4:color=0x00FF66:t=fill:"
        f"enable='between(t,0,{duration})'[line_green];"
        f"[line_green]drawtext=fontfile='{font_path}':text='{dynamic_text}':"
        f"fontcolor=white:fontsize=64:borderw=3:bordercolor=black:"
        f"x='{x_expr}':y={base_y}+96:alpha='{alpha_expr}':"
        f"enable='between(t,0,{duration})'[v_final]"
    )

    cmd = [
        'ffmpeg',
        '-i', str(video_path),
        '-filter_complex', filter_complex,
        '-map', '[v_final]',
        '-map', '0:a',
        '-c:v', 'libx264',
        '-crf', '18',
        '-pix_fmt', 'yuv420p',
        '-threads', str(TOTAL_THREADS),
        '-c:a', 'copy',
        '-y',
        str(output_path)
    ]

    try:
        if logger: logger.info("Avvio elaborazione overlay FFmpeg...")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode == 0
    except Exception as e:
        if logger: logger.critical(f"Eccezione overlay: {str(e)}")
        return False

def main():
    clear_console()
    setup_directories()
    log_file = setup_logging()
    
    print("=" * 70)
    print(f" TEXT OVERLAY: {SCRIPT_NAME}")
    print(f" [Hardware Rilevato] Thread logici: {TOTAL_THREADS} | Worker: {MAX_WORKERS} | Thread/Worker: {THREADS_PER_WORKER}")
    print(f" Output previsto: '{OUTPUT_FILE}'")
    print(f" Data e ora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    logging.info(f"INIZIO elaborazione script {SCRIPT_NAME} (Thread CPU: {TOTAL_THREADS})")
    check_ffmpeg()

    try:
        video_input = input(f"\n📁 Inserisci il percorso del video MP4 [Default: {DEFAULT_INPUT_VIDEO}]: ").strip()
        if not video_input: video_input = DEFAULT_INPUT_VIDEO
            
        if not os.path.exists(video_input):
            print(f"\n[!] Errore: File video '{video_input}' non trovato.")
            return

        dynamic_input = input("📝 Inserisci il testo dinamico inferiore [Default: CAMPIONATO - TEAM vs TEAM]: ").strip()
        if not dynamic_input: dynamic_input = "CAMPIONATO - TEAM vs TEAM"
        
        print(f"\n🎬 Elaborazione video in corso...")
        if apply_text_overlay(video_input, OUTPUT_FILE, dynamic_input, duration=5.0):
            print(f"\n\n[✔] Elaborazione completata! File: {OUTPUT_FILE}")
        else:
            print(f"\n\n[X] Errore durante l'elaborazione con FFmpeg.")

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