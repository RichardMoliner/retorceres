"""
Bot de runemaking.
Lê a mana da tela e executa a sequência quando atingir o valor configurado.
Clica com botão direito na comida periodicamente.
Para quando atingir a quantidade de runas configurada.

Uso:
    python3 bot.py

Controles:
    - F8  : pausar/despausar
    - ESC : parar o bot

Requisitos:
    pip3 install pyautogui pynput mss pillow
"""

import json
import time
import sys
from threading import Event

import pyautogui
import mss
from pynput import keyboard

CONFIG_FILE = "config.json"

# ---------- Estado global ----------
running = Event()
running.set()
paused = Event()

# Para segurança: mover o mouse pro canto superior esquerdo aborta o pyautogui
pyautogui.FAILSAFE = True
# Pequena pausa entre comandos de mouse (ajuda em jogos)
pyautogui.PAUSE = 0.05


def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"❌ Arquivo {CONFIG_FILE} não encontrado.")
        print("   Rode 'python3 setup.py' primeiro.")
        sys.exit(1)

    # valores padrão para configs antigas
    config.setdefault("total_runes", 20)
    config.setdefault("food_interval_seconds", 180)
    return config


def is_blue_pixel(r, g, b):
    """
    Detecta se um pixel pertence à barra de mana (azul).
    A barra cheia é bem azul; a parte vazia fica escura/cinza.
    Ajuste os limiares se a detecção falhar.
    """
    return b > 100 and b > r + 30 and b > g + 20


def read_mana_percentage(config, sct):
    """
    Lê a porcentagem de preenchimento da barra de mana
    escaneando pixels da esquerda pra direita.
    Retorna float entre 0.0 e 1.0.
    """
    x_start, y = config["mana_bar_start"]
    x_end, _ = config["mana_bar_end"]

    bar_width = x_end - x_start
    if bar_width <= 0:
        return 0.0

    # Captura uma linha fina da barra
    region = {
        "left": x_start,
        "top": y - 1,
        "width": bar_width,
        "height": 3,
    }
    img = sct.grab(region)
    pixels = img.pixels  # lista de linhas, cada linha é lista de (r,g,b)

    # usa a linha do meio
    middle_row = pixels[len(pixels) // 2]

    # conta pixels azuis consecutivos a partir da esquerda
    filled = 0
    for (r, g, b) in middle_row:
        if is_blue_pixel(r, g, b):
            filled += 1
        else:
            # se achar um pixel não-azul, para
            # (tolerância pequena para anti-aliasing)
            break

    return filled / bar_width


def read_mana_value(config, sct):
    """Retorna o valor atual de mana em números inteiros."""
    pct = read_mana_percentage(config, sct)
    return int(pct * config["mana_max"])


def drag(from_pos, to_pos, duration=0.25):
    """Arrasta um item de um ponto para outro."""
    pyautogui.moveTo(from_pos[0], from_pos[1], duration=0.1)
    pyautogui.mouseDown(button="left")
    time.sleep(0.1)
    pyautogui.moveTo(to_pos[0], to_pos[1], duration=duration)
    time.sleep(0.1)
    pyautogui.mouseUp(button="left")
    time.sleep(0.15)


def press_hotkey(hotkey_str):
    """Aperta uma hotkey tipo 'shift+5' ou 'f1'."""
    keys = [k.strip().lower() for k in hotkey_str.split("+")]
    pyautogui.hotkey(*keys)


def right_click(pos):
    """Clica com o botão direito em uma posição."""
    pyautogui.moveTo(pos[0], pos[1], duration=0.1)
    time.sleep(0.05)
    pyautogui.rightClick()
    time.sleep(0.15)


def do_rune_cycle(config):
    """Executa um ciclo completo de criação de runa."""
    print("  → Arrastando blank rune para o slot da mão...")
    drag(config["blank_rune_position"], config["hand_slot"])

    print(f"  → Apertando hotkey: {config['hotkey']}")
    press_hotkey(config["hotkey"])

    wait = config["wait_after_hotkey"]
    print(f"  → Esperando {wait}s...")
    time.sleep(wait)

    print("  → Arrastando runa pronta para a backpack...")
    drag(config["hand_slot"], config["backpack_position"])


def eat_food(config):
    """Clica com botão direito na comida."""
    print("🍖 Comendo...")
    right_click(config["food_position"])


def play_done_sound():
    """Toca 3 beeps para avisar que terminou."""
    try:
        if sys.platform == "darwin":
            import os
            for _ in range(3):
                os.system("afplay /System/Library/Sounds/Glass.aiff &")
                time.sleep(0.4)
        else:
            for _ in range(3):
                print("\a", end="", flush=True)
                time.sleep(0.3)
    except Exception:
        pass


def on_key_press(key):
    """Listener de teclado global para pausar/parar."""
    try:
        if key == keyboard.Key.f8:
            if paused.is_set():
                paused.clear()
                print("\n▶️  Despausado")
            else:
                paused.set()
                print("\n⏸️  Pausado (F8 para retomar)")
        elif key == keyboard.Key.esc:
            print("\n🛑 Parando o bot...")
            running.clear()
            return False
    except AttributeError:
        pass


def main():
    config = load_config()
    total_runes = config["total_runes"]
    food_interval = config["food_interval_seconds"]

    print("=" * 60)
    print("  BOT DE RUNEMAKING")
    print("=" * 60)
    print(f"  Mana máxima:      {config['mana_max']}")
    print(f"  Gatilho:          {config['mana_threshold']}")
    print(f"  Hotkey:           {config['hotkey']}")
    print(f"  Espera:           {config['wait_after_hotkey']}s")
    print(f"  Runas a criar:    {total_runes}")
    print(f"  Intervalo comida: {food_interval}s")
    print("=" * 60)
    print("  F8  = pausar/despausar")
    print("  ESC = parar")
    print("  (mover o mouse para o canto superior esquerdo também para)")
    print("=" * 60)
    print("\nIniciando em 3 segundos... foque na janela do jogo!")
    time.sleep(3)
    print("🟢 Rodando...\n")

    # inicia listener de teclado em background
    listener = keyboard.Listener(on_press=on_key_press)
    listener.start()

    threshold = config["mana_threshold"]
    runes_made = 0
    last_food_time = time.time()
    stop_reason = "Parado pelo usuário"

    try:
        with mss.mss() as sct:
            while running.is_set():
                if paused.is_set():
                    time.sleep(0.2)
                    continue

                # checa se precisa comer
                now = time.time()
                if now - last_food_time >= food_interval:
                    print()  # quebra a linha de status
                    eat_food(config)
                    last_food_time = now

                mana = read_mana_value(config, sct)

                # status no terminal
                elapsed_since_food = int(time.time() - last_food_time)
                next_food_in = max(0, food_interval - elapsed_since_food)
                sys.stdout.write(
                    f"\rMana: {mana:<5} | Runas: {runes_made}/{total_runes} | "
                    f"Próx comida em: {next_food_in}s    "
                )
                sys.stdout.flush()

                if mana >= threshold:
                    runes_made += 1
                    print(f"\n\n⚡ Runa {runes_made}/{total_runes} — mana em {mana}")
                    do_rune_cycle(config)
                    print(f"✓ Runa {runes_made} criada\n")

                    # chegou no limite? para e toca o som
                    if runes_made >= total_runes:
                        print("=" * 60)
                        print(f"🎉 {total_runes} runas criadas!")
                        print("=" * 60)
                        stop_reason = f"{total_runes} runas concluídas"
                        play_done_sound()
                        break

                    # pequena pausa antes de voltar a monitorar
                    time.sleep(0.3)
                else:
                    time.sleep(0.2)

    except pyautogui.FailSafeException:
        print("\n🛑 Failsafe ativado (mouse no canto). Parando.")
        stop_reason = "Failsafe"
    except KeyboardInterrupt:
        print("\n🛑 Interrompido pelo usuário.")
        stop_reason = "Ctrl+C"
    finally:
        listener.stop()
        print(f"\n📊 Motivo da parada: {stop_reason}")
        print(f"📊 Total de runas criadas: {runes_made}")


if __name__ == "__main__":
    main()