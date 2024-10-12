import pyautogui
import time

try:
    while True:
        x, y = pyautogui.position()
        position_str = f'Posición del mouse: ({x}, {y})'
        print(position_str, end='')
        print('\b' * len(position_str), end='', flush=True)
        time.sleep(0.1)
except KeyboardInterrupt:
    print('\nFinalizado.')
