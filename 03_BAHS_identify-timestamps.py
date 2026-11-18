import os
import cv2
from pathlib import Path
import time
import ctypes
import logging
from datetime import datetime

# Tentativo di importare tqdm per eventuali barre di avanzamento testuali di supporto
try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

# Nome dello script di riferimento (usato per intestazioni e file di log)
NOME_SCRIPT = "03_BAHS_identify-timestamps"

def pulisci_schermo():
    """1. Pulisce la console del terminale ad avvio script."""
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
    
    # Pulisce eventuali handler preesistenti per evitare duplicazioni
    if logger.hasHandlers():
        logger.handlers.clear()

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

def seconds_to_time_str(seconds):
    """Converte i secondi in formato MM:SS o HH:MM:SS."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    if mins >= 60:
        hours = mins // 60
        mins = mins % 60
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"

def put_contrasted_text(frame, text, org, font_scale, color, thickness=2):
    """Scrive un testo con bordo nero di protezione per garantire la massima visibilità su qualsiasi sfondo."""
    cv2.putText(frame, text, org, cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness + 2, cv2.LINE_AA)
    cv2.putText(frame, text, org, cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)

def draw_overlay(frame, current_sec, total_sec, speed, paused, recorded_times, flash_timer, session_label):
    """Disegna l'interfaccia grafica e la barra di avanzamento dello stato di elaborazione."""
    h, w, _ = frame.shape
    
    # 1. Riquadro informativo in alto a sinistra
    put_contrasted_text(frame, f"Sessione: {session_label}", (20, 45), 0.9, (0, 255, 255), 2)
    
    time_str = seconds_to_time_str(current_sec)
    status_text = "PAUSA (Premi P per riprendere)" if paused else f"IN RIPRODUZIONE ({speed}x)"
    status_color = (0, 165, 255) if paused else (0, 255, 0)
    
    put_contrasted_text(frame, f"Tempo: {time_str}", (20, 90), 0.9, (255, 255, 255), 2)
    put_contrasted_text(frame, status_text, (20, 135), 0.7, status_color, 2)
    
    # 2. Elenco degli ultimi timestamp registrati
    put_contrasted_text(frame, f"Canestri registrati: {len(recorded_times)}", (20, 185), 0.7, (0, 255, 255), 2)
    
    start_idx = max(0, len(recorded_times) - 6)
    y_offset = 225
    for i, t in enumerate(recorded_times[start_idx:], start=start_idx + 1):
        text_item = f"[{i}] Canestro: {t}"
        put_contrasted_text(frame, text_item, (20, y_offset), 0.65, (255, 255, 0), 2)
        y_offset += 35
        
    # 3. Effetto lampeggiante
    if time.time() < flash_timer:
        put_contrasted_text(frame, "CANESTRO REGISTRATO!", (w // 2 - 320, h // 2), 1.4, (0, 255, 0), 3)

    # 4. 📊 Barra di avanzamento dello stato di elaborazione video
    bar_x = 30
    bar_y = h - 85
    bar_w = w - 60
    bar_h = 16
    
    progress = min(1.0, max(0.0, current_sec / total_sec)) if total_sec > 0 else 0
    filled_w = int(bar_w * progress)
    
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (50, 50, 50), -1)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + filled_w, bar_y + bar_h), (0, 200, 0), -1)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (255, 255, 255), 1)
    
    total_str = seconds_to_time_str(total_sec)
    progress_text = f"Progresso Elaborazione: {time_str} / {total_str} ({int(progress * 100)}%)"
    put_contrasted_text(frame, progress_text, (bar_x, bar_y - 12), 0.6, (255, 255, 255), 2)
        
    # 5. Legenda comandi rapidi in basso
    help_text = "[BARRA SPAZIO]: Canestro | [P]: Pausa | [F/R]: Avanti/Indietro 5s | [Q]: Salva ed Esci"
    put_contrasted_text(frame, help_text, (30, h - 25), 0.6, (0, 255, 255), 2)
    
    return frame

def record_timestamps():
    # 1. Pulizia console iniziale
    pulisci_schermo()
    
    # 2. Intestazione con nome script
    stampa_intestazione()
    
    # 4. Avvio logging
    configura_logging()
    
    successo_processo = True
    dir_in = Path("OUT")
    dir_in.mkdir(exist_ok=True)
    
    try:
        logging.info("Avvio procedura di identificazione timestamp e analisi video.")
        
        # 0. Inserimento etichetta personalizzata
        session_label = input("🏷️ Inserisci un'etichetta/nome per la sessione [Default: campionato_squadra]: ").strip()
        if not session_label:
            session_label = "campionato_squadra"
        safe_label = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in session_label)
        logging.info(f"Etichetta sessione confermata: {session_label}")
        
        # 1. Selezione video
        video_name = input("📁 Inserisci il nome del video nella cartella 'OUT' [Default: video_finale.mp4]: ").strip()
        if not video_name:
            video_name = "video_finale.mp4"
            logging.warning(f"Nessun nome inserito, uso il predefinito: {video_name}")
            
        video_path = dir_in / video_name
        if not video_path.exists():
            logging.error(f"File video non trovato in: {video_path.absolute()}")
            successo_processo = False
            return
            
        # 2. Selezione velocità di riproduzione
        speed_input = input("🚀 Velocità di riproduzione [Default: 1.5]: ").strip()
        try:
            speed = float(speed_input) if speed_input else 1.5
            if speed <= 0:
                speed = 1.0
        except ValueError:
            speed = 1.5
        logging.info(f"Velocità di elaborazione impostata a: {speed}x")

        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 25.0
            
        total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        total_sec = total_frames / fps if fps > 0 else 0
            
        txt_path = dir_in / "timestamps.txt"
        custom_txt_path = dir_in / f"timestamps_{safe_label}.txt"
        
        print("\n🎮 GUIDA CONTROLLI DA TASTIERA:")
        print("   [BARRA SPAZIATRICE] -> 🎯 Registra e mostra avviso verde")
        print("   [P]                 -> ⏸️ Metti in pausa / Riprendi riproduzione")
        print("   [F]                 -> ⏩ Salta in avanti di 5 secondi")
        print("   [R]                 -> ⏪ Salta all'indietro di 5 secondi")
        print("   [Q]                 -> 💾 Chiudi, salva ed esci")
        print(f"\n📝 I timestamp verranno salvati in: {txt_path.absolute()}\n")
        input("Premi [INVIO] per aprire il video a schermo intero e iniziare subito... ")
        
        recorded_times = []
        paused = False
        flash_timer = 0
        
        window_title = f"Player Analisi - {session_label} ({speed}x)"
        
        cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(window_title, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        ret, current_frame = cap.read()
        if not ret:
            logging.error("Impossibile leggere il fotogramma iniziale del video.")
            successo_processo = False
            return
            
        display_frame = current_frame.copy()
        display_frame = draw_overlay(display_frame, 0.0, total_sec, speed, paused, recorded_times, flash_timer, session_label)
        cv2.imshow(window_title, display_frame)
        
        if os.name == 'nt':
            try:
                hwnd = ctypes.windll.user32.FindWindowW(None, window_title)
                if hwnd:
                    ctypes.windll.user32.SetForegroundWindow(hwnd)
            except Exception:
                pass

        base_delay = int(1000 / fps)
        delay = max(1, int(base_delay / speed))
        
        while cap.isOpened():
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    logging.info("Fine del video raggiunta.")
                    break
                current_frame = frame
            
            current_msec = cap.get(cv2.CAP_PROP_POS_MSEC)
            current_sec = current_msec / 1000.0
            
            display_frame = current_frame.copy()
            display_frame = draw_overlay(display_frame, current_sec, total_sec, speed, paused, recorded_times, flash_timer, session_label)
            
            cv2.imshow(window_title, display_frame)
            
            key = cv2.waitKey(delay if not paused else 30) & 0xFF
            
            if key == ord('q') or key == ord('Q'):
                logging.info("Chiusura sessione interrotta anticipatamente dall'utente.")
                break
            elif key == ord('p') or key == ord('P'):
                paused = not paused
                logging.info(f"Stato riproduzione cambiato. Pausa: {paused}")
            elif key == ord('f') or key == ord('F'):
                new_msec = current_msec + 5000
                cap.set(cv2.CAP_PROP_POS_MSEC, new_msec)
            elif key == ord('r') or key == ord('R'):
                new_msec = max(0, current_msec - 5000)
                cap.set(cv2.CAP_PROP_POS_MSEC, new_msec)
            elif key == 32:
                time_str = seconds_to_time_str(current_sec)
                if time_str not in recorded_times:
                    recorded_times.append(time_str)
                    flash_timer = time.time() + 0.6
                    logging.info(f"Canestro registrato al secondo {current_sec:.1f} -> Timestamp: [{time_str}]")
                
        cap.release()
        cv2.destroyAllWindows()
        
        if recorded_times:
            file_content = f"# --------------------------------------------------\n" \
                           f"# Sessione: {session_label}\n" \
                           f"# Video sorgente: {video_name} (Velocità: {speed}x)\n" \
                           f"# --------------------------------------------------\n"
            for t in recorded_times:
                file_content += f"{t}\n"
                
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(file_content)
                
            with open(custom_txt_path, "w", encoding="utf-8") as f:
                f.write(file_content)
                
            logging.info(f"Salvati con successo {len(recorded_times)} timestamp nei file: {txt_path} e {custom_txt_path}")
        else:
            logging.warning("Nessun timestamp registrato durante la sessione.")

    except Exception as e:
        logging.exception(f"Errore critico durante l'esecuzione: {e}")
        successo_processo = False
        
    finally:
        # 2. Chiusura ufficiale come ultima operazione in assoluto
        stampa_chiusura(successo=successo_processo)

if __name__ == "__main__":
    record_timestamps()