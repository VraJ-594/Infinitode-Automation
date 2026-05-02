import pyautogui
import pygetwindow as gw
import keyboard
import time

def run_mapper():
    print("=========================================")
    print(" INFINTODE 2 - COORDINATE MAPPER UTILITY ")
    print("=========================================")
    
    window_name = "Infinitode 2"
    windows = gw.getWindowsWithTitle(window_name)
    
    if not windows:
        print(f"[Error] Could not find window '{window_name}'. Open the game first!")
        return
        
    game_window = windows[0]
    print(f"Locked onto '{window_name}'.")
    print("\nINSTRUCTIONS:")
    print("1. Hover your mouse over the base/tile you want to map.")
    print("2. Press 'SPACE' to save the coordinate.")
    print("3. Press 'Q' to quit and close the mapper.")
    print("-----------------------------------------")

    # Open a text file to log the coordinates
    with open("mapped_coordinates.txt", "a") as log_file:
        log_file.write(f"\n--- New Mapping Session ({time.ctime()}) ---\n")
        
        # Debounce variable so holding space doesn't spam saves
        space_pressed = False 
        
        while True:
            # Quit condition
            if keyboard.is_pressed('q'):
                print("\nExiting mapper. Check 'mapped_coordinates.txt' for your data.")
                break
                
            # Check for Spacebar press
            if keyboard.is_pressed('space'):
                if not space_pressed:
                    space_pressed = True
                    
                    # Get current absolute mouse position
                    abs_x, abs_y = pyautogui.position()
                    
                    # Calculate relative coordinates
                    rel_x = abs_x - game_window.left
                    rel_y = abs_y - game_window.top
                    
                    # Print to terminal
                    output = f"Mapped Point -> rel_x: {rel_x}, rel_y: {rel_y}"
                    print(output)
                    
                    # Save to file
                    log_file.write(f"rel_x={rel_x}, rel_y={rel_y}  | (Absolute: {abs_x}, {abs_y})\n")
                    
                    # Small delay to prevent double-logging
                    time.sleep(0.2) 
            else:
                space_pressed = False
            
            time.sleep(0.01) # Keep loop fast but avoid CPU hogging

if __name__ == "__main__":
    run_mapper()