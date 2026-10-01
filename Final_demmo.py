import pyautogui
import pyscreeze
import time
from datetime import datetime
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5 
print("Step1:Opent Crome browser.")
time.sleep(1)
pyautogui.hotkey('command', 'space', interval=0.5)

time.sleep(1)
pyautogui.typewrite('chrome')
time.sleep(1)
pyautogui.hotkey('command', 't', interval=0.5)
pyautogui.press('enter')
time.sleep(2)
print("Step2:Open Google.com")
pyautogui.typewrite('https://www.accuweather.com/en/in/chennai/206671/weather-forecast/206671')
pyautogui.press('enter')
time.sleep(2)

print("Step3:Take copy the full data and save it in a text file")
pyautogui.hotkey('command', 'a', interval=0.5)
pyautogui.hotkey('command', 'c', interval=0.5)
time.sleep(1)
pyautogui.hotkey('command', 'space', interval=0.5)
time.sleep(1)
pyautogui.typewrite('textedit')
time.sleep(1)
pyautogui.hotkey('command', 't', interval=0.5)
pyautogui.press('enter')
time.sleep(2)
pyautogui.hotkey('command', 'v', interval=0.5)
time.sleep(1)
print("Step4:Save the file in a text file")
pyautogui.hotkey('command', 's', interval=0.5)
time.sleep(1)
current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
pyautogui.typewrite(f'weather_data_{current_time}.txt')
pyautogui.press('enter')
time.sleep(1)       

