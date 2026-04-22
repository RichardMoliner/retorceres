"""
Bot de Fishing.
Clica com botão direito na fishing rod e depois com botão esquerdo em cada um
dos 10 SQMs configurados, em sequência, repetindo até o usuário apertar ESC.

Uso:
    python3 fish.py

Na primeira execução (ou se passar --setup), roda o setup para capturar
as posições da fishing rod e dos 10 SQMs.

Controles durante a execução:
    - ESC : parar o bot
    - Mover o mouse para o canto superior esquerdo : parada de emergência

Requisitos:
    pip3 install pyautogui pynput mss pillow
"""

import json
import os
import sys
import time
from threading import Event

import pyautogui
from pynput import keyboard

CONFIG_FILE = "fish_config.json"
TOTAL_SQMS = 10

# ---------- Estado global ----------
running = Event()
running.set()

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05


# ---------- Setup ----------
def capture_mouse_position(instruction):
    """Aguarda o usuário posicionar o mouse e apertar espaço."""
    print(f"\n>>> {instruction}")
    print("    (Pressione ESPAÇO quando o mouse estiver no lugar certo)")

    captured = {}

    def on_press(key):
        if key == keyboard.Key.space:
            pos = pyautogui.position()
            captured["x"] = pos.x
            captured["y"] = pos.y
            print(f"    ✓ Capturado: x={pos.x}, y={pos.y}")
            return False  # para o listener
        elif key == keyboard.Key.esc:
            print("    Setup cancelado pelo usuário.")
            sys.exit(0)

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

    return [captured["x"], captured["y"]]


def run_setup():
    """Captura todas as posições e salva no config."""
    print("=" * 60)
    print("  SETUP DO BOT DE FISHING")
    print("=" * 60)
    print("\nEste setup vai capturar as posições na sua tela.")
    print("Tenha o jogo aberto e visível antes de continuar.")
    print(f"Serão capturadas: 1 FISHING ROD + {TOTAL_SQMS} SQMs onde pescar.")
    print("Pressione ESC a qualquer momento para cancelar.\n")
    input("Pressione ENTER para começar...")

    config = {}

    # 1. fishing rod
    config["fishing_rod_position"] = capture_mouse_position(
        "Posicione o mouse em cima da FISHING ROD e pressione ESPAÇO."
    )

    # 2. os 10 SQMs
    sqms = []
    for i in range(1, TOTAL_SQMS + 1):
        pos = capture_mouse_position(
            f"Posicione o mouse no SQM #{i} (de {TOTAL_SQMS}) e pressione ESPAÇO."
        )
        sqms.append(pos)

    config["sqms"] = sqms

    # salva
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

    print("\n" + "=" * 60)
    print(f"  ✓ Configuração salva em {CONFIG_FILE}")
    print("=" * 60)

    return config


def load_config():
    """Carrega config existente. Retorna None se não existir."""
    if not os.path.isfile(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        # valida
        if "fishing_rod_position" not in config or "sqms" not in config:
            return None
        if len(config["sqms"]) != TOTAL_SQMS:
            return None
        return config
    except Exception:
        return None


# ---------- Ações ----------
def right_click(pos):
    """Clica com o botão direito em uma posição."""
    pyautogui.moveTo(pos[0], pos[1], duration=0.1)
    time.sleep(0.05)
    pyautogui.rightClick()
    time.sleep(0.15)


def left_click(pos):
    """Clica com o botão esquerdo em uma posição."""
    pyautogui.moveTo(pos[0], pos[1], duration=0.1)
    time.sleep(0.05)
    pyautogui.leftClick()
    time.sleep(0.15)


def fish_at(rod_pos, sqm_pos, index, total):
    """Usa a fishing rod em um SQM específico."""
    print(f"  🎣 SQM {index}/{total} — usando fishing rod...")
    right_click(rod_pos)
    time.sleep(0.1)
    left_click(sqm_pos)


# ---------- Listener de teclado ----------
def on_key_press(key):
    if key == keyboard.Key.esc:
        print("\n🛑 Parando o bot...")
        running.clear()
        return False


# ---------- Loop principal ----------
def run_bot(config):
    rod_pos = config["fishing_rod_position"]
    sqms = config["sqms"]

    print("\n" + "=" * 60)
    print("  BOT DE FISHING")
    print("=" * 60)
    print(f"  Fishing rod: {rod_pos}")
    print(f"  SQMs configurados: {len(sqms)}")
    print("=" * 60)
    print("  ESC = parar")
    print("  (mover o mouse para o canto superior esquerdo também para)")
    print("=" * 60)
    print("\nIniciando em 3 segundos... foque na janela do jogo!")
    time.sleep(3)
    print("🟢 Rodando...\n")

    # inicia listener de teclado em background
    listener = keyboard.Listener(on_press=on_key_press)
    listener.start()

    round_count = 0
    fish_count = 0
    stop_reason = "Parado pelo usuário"

    try:
        while running.is_set():
            round_count += 1
            print(f"\n🔄 Rodada {round_count}")

            for i, sqm_pos in enumerate(sqms, start=1):
                if not running.is_set():
                    break
                fish_at(rod_pos, sqm_pos, i, len(sqms))
                fish_count += 1
                # pequena pausa entre SQMs para o jogo processar
                time.sleep(0.5)

    except pyautogui.FailSafeException:
        print("\n🛑 Failsafe ativado (mouse no canto). Parando.")
        stop_reason = "Failsafe"
    except KeyboardInterrupt:
        print("\n🛑 Interrompido pelo usuário.")
        stop_reason = "Ctrl+C"
    finally:
        listener.stop()
        print(f"\n📊 Motivo da parada: {stop_reason}")
        print(f"📊 Rodadas completas: {round_count - 1}")
        print(f"📊 Total de pescadas: {fish_count}")


# ---------- Entry point ----------
def main():
    force_setup = "--setup" in sys.argv or "-s" in sys.argv

    config = None if force_setup else load_config()

    if config is None:
        # roda o setup
        if not force_setup:
            print("Nenhuma configuração encontrada. Vamos configurar agora.\n")
        config = run_setup()
    else:
        # já tem config — pergunta se quer reconfigurar
        print("=" * 60)
        print("  BOT DE FISHING")
        print("=" * 60)
        print(f"\nConfiguração encontrada em {CONFIG_FILE}:")
        print(f"  Fishing rod: {config['fishing_rod_position']}")
        print(f"  {len(config['sqms'])} SQMs configurados")
        print()
        choice = input("Pressione ENTER para iniciar, ou 'r' + ENTER para reconfigurar: ").strip().lower()
        if choice == "r":
            config = run_setup()

    run_bot(config)


if __name__ == "__main__":
    main()