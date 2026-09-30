import pyautogui
pyautogui.FAILSAFE = True
pyautogui.moveTo(100, 100, duration=1)  
print("PyAutoGUI has moved the mouse to (100, 100) over 1 second.")
pyautogui.click()
print("PyAutoGUI has clicked at the current mouse position.")
pyautogui.typewrite("Hello, World!", interval=0.1)
pyautogui.press('enter')
pyautogui.hotkey('ctrl', 's')
pyautogui.alert("This is an alert box!")
pyautogui.confirm("Do you want to continue?")
pyautogui.PAUSE = 1