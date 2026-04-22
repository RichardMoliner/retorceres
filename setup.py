"""
Setup do bot de runemaking.
Rode este script UMA VEZ para configurar as coordenadas dos elementos na tela.

Uso:
    python3 setup.py

Requisitos:
    pip3 install pyautogui pynput mss pillow
"""

import json
import time
from pynput import mouse, keyboard
import pyautogui

CONFIG_FILE = "config.json"

# Etapas que vamos capturar, na ordem
STEPS = [
    {
        "key": "mana_bar_start",
        "instruction": "Posicione o mouse no INÍCIO (extremidade esquerda) da barra azul de mana e pressione ESPAÇO.",
    },
    {
        "key": "mana_bar_end",
        "instruction": "Posicione o mouse no FINAL (extremidade direita, onde fica 100%) da barra azul de mana e pressione ESPAÇO.",
    },
    {
        "key": "mana_max",
        "instruction": "Digite o valor MÁXIMO de mana do seu personagem (ex: 1500) e pressione ENTER.",
        "type": "input",
    },
    {
        "key": "mana_threshold",
        "instruction": "Digite o valor de mana que dispara a criação de uma runa (ex: 120) e pressione ENTER.",
        "type": "input",
    },
    {
        "key": "blank_rune_position",
        "instruction": "Posicione o mouse em cima da BLANK RUNE na mochila e pressione ESPAÇO.",
    },
    {
        "key": "hand_slot",
        "instruction": "Posicione o mouse no SLOT DA MÃO (onde a blank rune precisa ir para usar a hotkey) e pressione ESPAÇO.",
    },
    {
        "key": "backpack_position",
        "instruction": "Posicione o mouse em um SLOT VAZIO da backpack (onde a runa pronta será guardada) e pressione ESPAÇO.",
    },
    {
        "key": "food_position",
        "instruction": "Posicione o mouse em cima da COMIDA (que será clicada com o botão direito periodicamente) e pressione ESPAÇO.",
    },
    {
        "key": "hotkey",
        "instruction": "Digite a hotkey a ser pressionada (ex: shift+5) e pressione ENTER.",
        "type": "input",
    },
    {
        "key": "wait_after_hotkey",
        "instruction": "Digite quantos segundos esperar depois da hotkey (ex: 2) e pressione ENTER.",
        "type": "input",
    },
    {
        "key": "food_interval_seconds",
        "instruction": "Digite a cada quantos segundos clicar na comida (ex: 180 = 3 minutos) e pressione ENTER.",
        "type": "input",
    },
    {
        "key": "total_runes",
        "instruction": "Digite quantas RUNAS serão criadas por execução (ex: 20) e pressione ENTER.",
        "type": "input",
    },
]


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
            exit(0)

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

    return [captured["x"], captured["y"]]


def capture_input(instruction):
    """Aguarda o usuário digitar um valor."""
    print(f"\n>>> {instruction}")
    value = input("    Valor: ").strip()
    return value


def main():
    print("=" * 60)
    print("  SETUP DO BOT DE RUNEMAKING")
    print("=" * 60)
    print("\nEste setup vai capturar as posições na sua tela.")
    print("Tenha o jogo aberto e visível antes de continuar.")
    print("Pressione ESC a qualquer momento para cancelar.\n")
    input("Pressione ENTER para começar...")

    config = {}

    for step in STEPS:
        if step.get("type") == "input":
            value = capture_input(step["instruction"])
            # converte para número se for numérico
            try:
                if "." in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass  # mantém como string (ex: hotkey)
            config[step["key"]] = value
        else:
            config[step["key"]] = capture_mouse_position(step["instruction"])

    # salva a config
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

    print("\n" + "=" * 60)
    print(f"  ✓ Configuração salva em {CONFIG_FILE}")
    print("=" * 60)
    print("\nAgora você pode rodar o bot com:  python3 bot.py\n")


if __name__ == "__main__":
    main()