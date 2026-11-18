import os
import sys
import logging
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

SCRIPT_NAME = "07_BAHS_text-overlay.py"
INPUT_DIR = "FINAL"
DEFAULT_INPUT_VIDEO = os.path.join(INPUT_DIR, "video_finale_merged_music.mp4")
OUTPUT_FILE = os.path.join(INPUT_DIR, "video_finale_merged_music_text.mp4")
EXTRA_DIR = "EXTRA"
LOG_DIR = "LOG"
TMP_DIR = "TMP"

def setup_directories():
    """Crea le cartelle necessarie se non esistono."""
    for directory in [INPUT_DIR, EXTRA_DIR, TMP_DIR, LOG_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)

def setup_logging():
    """Configura il sistema di logging nella cartella LOG."""
    setup_directories()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(LOG_DIR, f"07_BAHS_text-overlay_{timestamp}.log")
    
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
    """Verifica che FFmpeg e ffprobe siano installati e disponibili nel sistema."""
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        print("\n[X] Errore: FFmpeg o ffprobe non sono installati o non sono presenti nel PATH del sistema.")
        logging.error("FFmpeg o ffprobe non trovati nel sistema.")
        sys.exit(1)

def cleanup_tmp():
    """Pulisce e rimuove la cartella temporanea TMP e il suo contenuto."""
    if os.path.exists(TMP_DIR):
        try:
            shutil.rmtree(TMP_DIR)
            logging.info(f"Cartella temporanea '{TMP_DIR}' pulita ed eliminata con successo.")
        except Exception as e:
            logging.warning(f"Impossibile rimuovere completamente la cartella '{TMP_DIR}': {e}")

def apply_text_overlay(video_path, output_path, dynamic_text, duration=5.0, logger=None):
    """Normalizza il video e applica l'overlay gestendo il font temporaneamente in TMP."""
    
    setup_directories()
    
    # Copia il font nella cartella TMP per evitare di inquinare la directory principale
    extra_font = Path(EXTRA_DIR) / "font.ttf"
    tmp_font = Path(TMP_DIR) / "font.ttf"
    
    if extra_font.exists():
        shutil.copy(extra_font, tmp_font)
        if logger:
            logger.info("Copiato EXTRA/font.ttf nella cartella temporanea TMP.")
    else:
        print(f"\n[!] Attenzione: File font '{extra_font}' non trovato nella cartella {EXTRA_DIR}!")
        if logger:
            logger.warning(f"File font {extra_font} non trovato.")

    # Percorso relativo pulito all'interno della cartella TMP per FFmpeg
    font_path = str(tmp_font).replace('\\', '/')

    # Posizione di base in basso a sinistra
    base_x = 60
    base_y = 810
    
    trans_time = 1.5  # Durata della transizione
    start_x = -1600   # Partenza a sinistra fuori schermo
    target_x = base_x # Posizione fissa di arrivo allineata

    # Formula matematica di easing (decelerazione fluida in entrata e uscita simmetrica)
    x_expr = (
        f"if(lt(t\\,{trans_time})\\, "
        f"({start_x} + ({target_x} - ({start_x})) * (sin((t/{trans_time}) * 1.570796))) \\, "
        f"if(lt(t\\,{duration}-{trans_time})\\, "
        f"{target_x}\\, "
        f"({target_x} + ({start_x} - {target_x}) * sin(((t - ({duration}-{trans_time}))/{trans_time}) * 1.570796))"
        f")"
        f")"
    )

    # Effetto dissolvenza (Fade In e Fade Out sincronizzato)
    alpha_expr = (
        f"if(lt(t\\,{trans_time})\\, t/{trans_time}\\, "
        f"if(lt(t\\,{duration}-{trans_time})\\, 1\\, "
        f"({duration}-t)/{trans_time}"
        f"))"
    )

    # Filtro complesso con font in TMP
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
        '-c:a', 'copy',
        '-y',
        str(output_path)
    ]

    try:
        if logger:
            logger.info("Avvio elaborazione overlay FFmpeg con font in TMP...")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            if logger:
                logger.info("Overlay completato con successo.")
            return True
        else:
            print(f"❌ Errore dettagliato FFmpeg:\n{result.stderr}")
            if logger:
                logger.error(f"Errore FFmpeg overlay: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ Eccezione Python: {str(e)}")
        if logger:
            logger.critical(f"Eccezione overlay: {str(e)}")
        return False

def main():
    clear_console()
    setup_directories()
    log_file = setup_logging()
    
    print("=" * 65)
    print(f" TEXT OVERLAY CLEAN TMP: {SCRIPT_NAME}")
    print(f" Output previsto: '{OUTPUT_FILE}'")
    print(f" Data e ora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)
    
    logging.info(f"INIZIO elaborazione script {SCRIPT_NAME}")
    check_ffmpeg()

    try:
        video_input = input(f"\n📁 Inserisci il percorso del video MP4 [Default: {DEFAULT_INPUT_VIDEO}]: ").strip()
        if not video_input:
            video_input = DEFAULT_INPUT_VIDEO
            
        if not os.path.exists(video_input):
            print(f"\n[!] Errore: File video '{video_input}' non trovato.")
            logging.error(f"File video non trovato: {video_input}")
            return

        dynamic_input = input("📝 Inserisci il testo dinamico inferiore [Default: CAMPIONATO - TEAM vs TEAM]: ").strip()
        if not dynamic_input:
            dynamic_input = "CAMPIONATO - TEAM vs TEAM"
        
        print(f"\n✅ Testo dinamico selezionato: \"{dynamic_input}\"")
        logging.info(f"Testo dinamico impostato: '{dynamic_input}'")

        print("\n🎬 Elaborazione video in corso...")
        if apply_text_overlay(video_input, OUTPUT_FILE, dynamic_input, duration=5.0):
            print(f"\n\n[✔] Elaborazione completata con successo!")
            print(f"    File generato: {OUTPUT_FILE}")
            logging.info(f"Video generato con successo: {OUTPUT_FILE}")
        else:
            print(f"\n\n[X] Errore durante l'elaborazione con FFmpeg.")
            logging.error("Errore durante l'applicazione dell'overlay.")

    except Exception as e:
        print(f"\n[X] Errore critico: {e}")
        logging.error(f"Errore critico: {e}", exc_info=True)

    finally:
        print("\nPulizia dei file temporanei in corso...")
        cleanup_tmp()

    print("\n" + "=" * 65)
    print(f" FINE ELABORAZIONE: {SCRIPT_NAME}")
    print(f" Report salvato in: {log_file}")
    print("=" * 65)
    logging.info(f"FINE elaborazione script {SCRIPT_NAME}")

if __name__ == "__main__":
    main()