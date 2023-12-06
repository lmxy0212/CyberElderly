import keyboard

print("Listening for key presses (press ESC to exit)...")

while True:
    if keyboard.is_pressed('enter'):
        print("You pressed Enter!")
    elif keyboard.is_pressed('esc'):
        print("Exiting...")
        break

print("Script ended.")