"""
HP Monitor — monitora a barra de Health do personagem e dispara ação
quando o HP cai abaixo de um threshold configurado.

Roda em uma thread separada do bot principal.
"""

import os
import sys
import time
import threading

import pyautogui
import mss


def is_red_pixel(r, g, b):
    """
    Detecta se um pixel pertence à barra de HP (vermelho).
    A barra cheia é bem vermelha; a parte vazia fica escura/cinza.
    """
    return r > 100 and r > g + 30 and r > b + 20


def read_hp_percentage(config, sct):
    """
    Lê a porcentagem de preenchimento da barra de HP
    escaneando pixels da esquerda para a direita.
    """
    x_start, y = config["hp_bar_start"]
    x_end, _ = config["hp_bar_end"]

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
        if is_red_pixel(r, g, b):
            filled += 1
        else:
            break

    return filled / bar_width


def read_hp_value(config, sct):
    """Retorna o valor atual de HP em números inteiros."""
    pct = read_hp_percentage(config, sct)
    return int(pct * config["hp_max"])


def play_hp_alert():
    """Toca um som mais urgente para alerta de HP baixo."""
    try:
        if sys.platform == "darwin":
            # Sosumi é o clássico "alô" urgente do Mac. Toca 4 vezes rápido.
            for _ in range(4):
                os.system("afplay /System/Library/Sounds/Sosumi.aiff &")
                time.sleep(0.2)
        else:
            # fallback bell do terminal
            for _ in range(4):
                print("\a", end="", flush=True)
                time.sleep(0.2)
    except Exception:
        pass


def press_hotkey(hotkey_str):
    """Aperta uma hotkey tipo 'shift+2' ou 'f1'."""
    keys = [k.strip().lower() for k in hotkey_str.split("+")]
    pyautogui.hotkey(*keys)


class HPMonitor:
    """
    Monitor de HP que roda em thread paralela.
    Dispara a hotkey UMA vez quando HP cai abaixo do threshold.
    Só dispara de novo se o HP subir acima do threshold e cair de novo.
    """

    def __init__(self, config, log_callback=None):
        self.config = config
        self.log = log_callback or (lambda msg: print(msg))
        self._stop = threading.Event()
        self._pause = threading.Event()
        self.thread = None

        # estado: já foi alertado neste "ciclo de queda"?
        self.already_triggered = False

        self.hp_threshold = config["hp_threshold"]
        self.hp_hotkey = config["hp_hotkey"]
        # intervalo entre leituras (não precisa ser tão frequente)
        self.check_interval = 0.3

    def start(self):
        self._stop.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self._stop.set()

    def pause(self):
        self._pause.set()

    def resume(self):
        self._pause.clear()

    def _run(self):
        try:
            with mss.mss() as sct:
                while not self._stop.is_set():
                    if self._pause.is_set():
                        time.sleep(0.2)
                        continue

                    try:
                        hp = read_hp_value(self.config, sct)
                    except Exception:
                        time.sleep(self.check_interval)
                        continue

                    if hp <= self.hp_threshold:
                        if not self.already_triggered:
                            self.log(
                                f"\n⚠️  HP BAIXO! ({hp} ≤ {self.hp_threshold}) "
                                f"— apertando {self.hp_hotkey}"
                            )
                            try:
                                press_hotkey(self.hp_hotkey)
                                play_hp_alert()
                            except Exception as e:
                                self.log(f"   Erro ao executar ação de HP: {e}")
                            self.already_triggered = True
                    else:
                        # HP voltou acima do threshold — rearma o trigger
                        if self.already_triggered:
                            self.log(f"   ✓ HP recuperou ({hp}). Monitor rearmado.")
                            self.already_triggered = False

                    time.sleep(self.check_interval)
        except Exception as e:
            self.log(f"❌ HP Monitor crashou: {e}")