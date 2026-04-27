"""
Bot de runemaking.
Lê a mana da tela e executa a sequência quando atingir o valor configurado.
Clica com botão direito na comida periodicamente.
Suporta múltiplas BPs de blank rune — avança para a próxima quando termina a atual.
Monitora HP em paralelo e dispara hotkey de defesa quando HP baixa.

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
import os
from threading import Event

import pyautogui
import mss
from pynput import keyboard

from hp_monitor import HPMonitor

CONFIG_FILE = "config.json"

# ---------- Estado global ----------
running = Event()
running.set()
paused = Event()

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05


def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"❌ Arquivo {CONFIG_FILE} não encontrado.")
        print("   Rode 'python3 setup.py' primeiro.")
        sys.exit(1)

    # validação básica das chaves necessárias
    required = [
        "mana_bar_start", "mana_bar_end", "mana_max", "mana_threshold",
        "hp_bar_start", "hp_bar_end", "hp_max", "hp_threshold", "hp_hotkey",
        "bp_positions", "hand_slot", "food_position",
        "hotkey", "wait_after_hotkey",
    ]
    missing = [k for k in required if k not in config]
    if missing:
        print(f"❌ Config incompleta. Faltam: {', '.join(missing)}")
        print("   Rode 'python3 setup.py' novamente para reconfigurar.")
        sys.exit(1)

    config.setdefault("food_interval_seconds", 180)
    config.setdefault("runes_per_bp", 20)
    config.setdefault("num_bps", len(config["bp_positions"]))
    config.setdefault("total_runes", config["num_bps"] * config["runes_per_bp"])

    return config


# ---------- Leitura de mana ----------
def is_blue_pixel(r, g, b):
    return b > 100 and b > r + 30 and b > g + 20


def read_mana_percentage(config, sct):
    x_start, y = config["mana_bar_start"]
    x_end, _ = config["mana_bar_end"]

    bar_width = x_end - x_start
    if bar_width <= 0:
        return 0.0

    region = {
        "left": x_start,
        "top": y - 1,
        "width": bar_width,
        "height": 3,
    }
    img = sct.grab(region)
    pixels = img.pixels
    middle_row = pixels[len(pixels) // 2]

    filled = 0
    for (r, g, b) in middle_row:
        if is_blue_pixel(r, g, b):
            filled += 1
        else:
            break

    return filled / bar_width


def read_mana_value(config, sct):
    pct = read_mana_percentage(config, sct)
    return int(pct * config["mana_max"])


# ---------- Ações ----------
def drag(from_pos, to_pos, duration=0.25):
    pyautogui.moveTo(from_pos[0], from_pos[1], duration=0.1)
    pyautogui.mouseDown(button="left")
    time.sleep(0.1)
    pyautogui.moveTo(to_pos[0], to_pos[1], duration=duration)
    time.sleep(0.1)
    pyautogui.mouseUp(button="left")
    time.sleep(0.15)


def press_hotkey(hotkey_str):
    keys = [k.strip().lower() for k in hotkey_str.split("+")]
    pyautogui.hotkey(*keys)


def right_click(pos):
    pyautogui.moveTo(pos[0], pos[1], duration=0.1)
    time.sleep(0.05)
    pyautogui.rightClick()
    time.sleep(0.15)


def do_rune_cycle(config, current_bp_pos):
    """
    Executa um ciclo completo de criação de runa usando a BP atual.
    Pega a blank rune do último slot da BP, cria a runa, devolve no mesmo slot.
    """
    print(f"  → Pegando blank rune da BP em {current_bp_pos}...")
    drag(current_bp_pos, config["hand_slot"])

    print(f"  → Apertando hotkey: {config['hotkey']}")
    press_hotkey(config["hotkey"])

    wait = config["wait_after_hotkey"]
    print(f"  → Esperando {wait}s...")
    time.sleep(wait)

    print(f"  → Devolvendo runa pronta para a BP em {current_bp_pos}...")
    drag(config["hand_slot"], current_bp_pos)


def eat_food(config):
    print("🍖 Comendo...")
    right_click(config["food_position"])


def play_done_sound():
    """Som de conclusão: Glass 3 vezes."""
    try:
        if sys.platform == "darwin":
            for _ in range(3):
                os.system("afplay /System/Library/Sounds/Glass.aiff &")
                time.sleep(0.4)
        else:
            for _ in range(3):
                print("\a", end="", flush=True)
                time.sleep(0.3)
    except Exception:
        pass


# ---------- Listener de teclado ----------
def on_key_press(key):
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


# ---------- Main ----------
def main():
    config = load_config()

    total_runes = config["total_runes"]
    food_interval = config["food_interval_seconds"]
    num_bps = config["num_bps"]
    runes_per_bp = config["runes_per_bp"]
    bp_positions = config["bp_positions"]

    print("=" * 60)
    print("  BOT DE RUNEMAKING")
    print("=" * 60)
    print(f"  Mana máxima:      {config['mana_max']}")
    print(f"  Mana gatilho:     {config['mana_threshold']}")
    print(f"  HP máximo:        {config['hp_max']}")
    print(f"  HP threshold:     {config['hp_threshold']}")
    print(f"  HP hotkey:        {config['hp_hotkey']}")
    print(f"  Runa hotkey:      {config['hotkey']}")
    print(f"  Espera runa:      {config['wait_after_hotkey']}s")
    print(f"  BPs de blank:     {num_bps} × {runes_per_bp} = {total_runes} runas")
    print(f"  Intervalo comida: {food_interval}s")
    print("=" * 60)
    print("  F8  = pausar/despausar")
    print("  ESC = parar")
    print("  (mover o mouse para o canto superior esquerdo também para)")
    print("=" * 60)
    print("\nIniciando em 3 segundos... foque na janela do jogo!")
    time.sleep(3)
    print("🟢 Rodando...\n")

    # listener de teclado
    listener = keyboard.Listener(on_press=on_key_press)
    listener.start()

    # inicia monitor de HP em thread paralela
    hp_monitor = HPMonitor(config, log_callback=lambda msg: print(msg))
    hp_monitor.start()

    threshold = config["mana_threshold"]
    runes_made = 0
    last_food_time = time.time()
    stop_reason = "Parado pelo usuário"
    current_bp_index = 0  # qual BP estamos usando (0-indexed)
    runes_this_bp = 0     # quantas runas já foram feitas com a BP atual

    try:
        with mss.mss() as sct:
            while running.is_set():
                if paused.is_set():
                    time.sleep(0.2)
                    continue

                # comida
                now = time.time()
                if now - last_food_time >= food_interval:
                    print()
                    eat_food(config)
                    last_food_time = now

                mana = read_mana_value(config, sct)

                # status no terminal
                elapsed_food = int(time.time() - last_food_time)
                next_food_in = max(0, food_interval - elapsed_food)
                sys.stdout.write(
                    f"\rMana: {mana:<5} | Runas: {runes_made}/{total_runes} | "
                    f"BP: {current_bp_index + 1}/{num_bps} "
                    f"({runes_this_bp}/{runes_per_bp}) | "
                    f"Próx comida: {next_food_in}s   "
                )
                sys.stdout.flush()

                if mana >= threshold:
                    current_bp_pos = bp_positions[current_bp_index]
                    runes_made += 1
                    runes_this_bp += 1

                    print(
                        f"\n\n⚡ Runa {runes_made}/{total_runes} "
                        f"(BP {current_bp_index + 1}, slot {runes_this_bp}/{runes_per_bp}) "
                        f"— mana em {mana}"
                    )
                    do_rune_cycle(config, current_bp_pos)
                    print(f"✓ Runa {runes_made} criada\n")

                    # terminou esta BP? avança para a próxima
                    if runes_this_bp >= runes_per_bp:
                        current_bp_index += 1
                        runes_this_bp = 0
                        if current_bp_index < num_bps:
                            print(
                                f"📦 BP {current_bp_index} esgotada. "
                                f"Avançando para BP {current_bp_index + 1}.\n"
                            )

                    # chegou no total de runas? fim
                    if runes_made >= total_runes:
                        print("=" * 60)
                        print(f"🎉 {total_runes} runas criadas!")
                        print("=" * 60)
                        stop_reason = f"{total_runes} runas concluídas"
                        play_done_sound()
                        break

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
        hp_monitor.stop()
        listener.stop()
        print(f"\n📊 Motivo da parada: {stop_reason}")
        print(f"📊 Total de runas criadas: {runes_made}")
        print(f"📊 BPs usadas: {current_bp_index + (1 if runes_this_bp > 0 else 0)}/{num_bps}")


if __name__ == "__main__":
    main()