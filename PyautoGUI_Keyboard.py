import pyautogui
import time
pyautogui.FAILSAFE = True
pyautogui.typewrite("Hello, World!", interval=0.1)
pyautogui.hotkey('cmd', 'c')
pyautogui.hotkey('cmd', 'v')
pyautogui.hotkey('cmd', 's')
pyautogui.hotkey('cmd', 'q')
pyautogui.press('enter')
pyautogui.hold('shift')
pyautogui.press('tab')
pyautogui.typewrite("Hello, World!", interval=0.1)
#pyautogui.release('shift')