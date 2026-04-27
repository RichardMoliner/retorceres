"""
Setup do bot de runemaking.
Rode este script UMA VEZ para configurar as coordenadas dos elementos na tela.

Uso:
    python3 setup.py

Requisitos:
    pip3 install pyautogui pynput mss pillow
"""

import json
import sys
from pynput import keyboard
import pyautogui

CONFIG_FILE = "config.json"

# Cada BP tem 20 slots (a capacidade padrão). Esse valor é usado depois
# pelo bot para calcular o total de runas a criar.
RUNES_PER_BP = 20


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
            return False
        elif key == keyboard.Key.esc:
            print("    Setup cancelado pelo usuário.")
            sys.exit(0)

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

    return [captured["x"], captured["y"]]


def capture_input(instruction, _type=None):
    """Aguarda o usuário digitar um valor. Converte para int/float se pedido."""
    print(f"\n>>> {instruction}")
    while True:
        value = input("    Valor: ").strip()
        if _type is None:
            return value
        try:
            return _type(value)
        except ValueError:
            print(f"    ❌ Valor inválido. Esperado: {_type.__name__}")


def section(title):
    print("\n" + "─" * 60)
    print(f"  {title}")
    print("─" * 60)


def main():
    print("=" * 60)
    print("  SETUP DO BOT DE RUNEMAKING")
    print("=" * 60)
    print("\nEste setup vai capturar as posições na sua tela.")
    print("Tenha o jogo aberto e visível antes de continuar.")
    print("Pressione ESC a qualquer momento para cancelar.\n")
    input("Pressione ENTER para começar...")

    config = {}

    # ---------- Barra de mana ----------
    section("1. BARRA DE MANA")
    config["mana_bar_start"] = capture_mouse_position(
        "Posicione o mouse no INÍCIO (extremidade esquerda) da barra AZUL de mana e pressione ESPAÇO."
    )
    config["mana_bar_end"] = capture_mouse_position(
        "Posicione o mouse no FINAL (extremidade direita) da barra AZUL de mana e pressione ESPAÇO."
    )
    config["mana_max"] = capture_input(
        "Digite o valor MÁXIMO de mana do seu personagem (ex: 1500):", int
    )
    config["mana_threshold"] = capture_input(
        "Digite o valor de mana que dispara a criação de uma runa (ex: 120):", int
    )

    # ---------- Barra de HP ----------
    section("2. BARRA DE HEALTH (HP)")
    config["hp_bar_start"] = capture_mouse_position(
        "Posicione o mouse no INÍCIO (extremidade esquerda) da barra VERMELHA de HP e pressione ESPAÇO."
    )
    config["hp_bar_end"] = capture_mouse_position(
        "Posicione o mouse no FINAL (extremidade direita) da barra VERMELHA de HP e pressione ESPAÇO."
    )
    config["hp_max"] = capture_input(
        "Digite o valor MÁXIMO de HP do seu personagem (ex: 800):", int
    )
    config["hp_threshold"] = capture_input(
        "Digite o HP MÍNIMO que dispara o alerta (ex: 300, ou seja, HP <= 300 aciona):",
        int,
    )
    config["hp_hotkey"] = capture_input(
        "Digite a hotkey a ser apertada quando HP estiver baixo (ex: shift+2):"
    )

    # ---------- Backpacks de blank rune ----------
    section("3. BACKPACKS DE BLANK RUNE")
    print(f"\nCada BP tem {RUNES_PER_BP} blank runes (slots).")
    num_bps = capture_input(
        "Quantas BPs de blank rune você vai usar (ex: 3):", int
    )
    if num_bps < 1:
        print("❌ Número de BPs deve ser pelo menos 1. Abortando.")
        sys.exit(1)

    bp_positions = []
    for i in range(1, num_bps + 1):
        pos = capture_mouse_position(
            f"Posicione o mouse no ÚLTIMO SLOT da BP #{i} de blank rune "
            f"(de onde pegar e onde devolver a runa feita) e pressione ESPAÇO."
        )
        bp_positions.append(pos)

    config["num_bps"] = num_bps
    config["bp_positions"] = bp_positions
    config["runes_per_bp"] = RUNES_PER_BP
    config["total_runes"] = num_bps * RUNES_PER_BP

    # ---------- Slot da mão ----------
    section("4. SLOT DA MÃO")
    config["hand_slot"] = capture_mouse_position(
        "Posicione o mouse no SLOT DA MÃO (onde a blank rune vai para usar a hotkey) e pressione ESPAÇO."
    )

    # ---------- Comida ----------
    section("5. COMIDA")
    config["food_position"] = capture_mouse_position(
        "Posicione o mouse em cima da COMIDA (será clicada com botão direito) e pressione ESPAÇO."
    )
    config["food_interval_seconds"] = capture_input(
        "A cada quantos segundos clicar na comida (ex: 180 = 3 minutos):", int
    )

    # ---------- Parâmetros de runa ----------
    section("6. PARÂMETROS DA RUNA")
    config["hotkey"] = capture_input(
        "Digite a hotkey da spell da runa (ex: shift+5):"
    )
    config["wait_after_hotkey"] = capture_input(
        "Quantos segundos esperar depois da hotkey (ex: 2):", float
    )

    # ---------- Salva ----------
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

    print("\n" + "=" * 60)
    print(f"  ✓ Configuração salva em {CONFIG_FILE}")
    print("=" * 60)
    print(f"\n  Total de runas a criar: {config['total_runes']} "
          f"({num_bps} BPs × {RUNES_PER_BP} runas)")
    print("\nAgora você pode rodar o bot com:  python3 bot.py\n")


if __name__ == "__main__":
    main()