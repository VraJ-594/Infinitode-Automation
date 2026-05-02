import pyautogui
import pygetwindow as gw
import keyboard
import time
import os
import logging
import sys
import datetime # Added for logging timestamps

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)

class BotError(Exception):
    pass


class VisionController:
    def __init__(self, window_name="Infinitode 2", image_dir="images"):
        self.window_name = window_name
        self.image_dir = image_dir
        self.game_window = None
        self.region = None

    def _require_window(self):
        if not self.game_window or not self.region:
            raise BotError("Game window is not focused. Call focus_window() first.")

    def focus_window(self):
        logging.info("Searching for game window: %s", self.window_name)
        windows = gw.getWindowsWithTitle(self.window_name)
        if not windows:
            raise BotError(f"Window '{self.window_name}' not found.")

        self.game_window = windows[0]
        if self.game_window.isMinimized:
            logging.info("Restoring minimized window.")
            self.game_window.restore()

        self.game_window.activate()
        time.sleep(1.0)

        self.region = (
            self.game_window.left,
            self.game_window.top,
            self.game_window.width,
            self.game_window.height
        )
        logging.info("Game window focused.")
        return True

    def _click_point(self, x, y):
        x = int(x)
        y = int(y)
        logging.info("Clicking at (%d, %d)", x, y)
        pyautogui.moveTo(x, y, duration=0.08)
        pyautogui.click()

    def find_and_click(self, image_name, confidence=0.8, wait_after=1.0, timeout=6.0, required=False):
        self._require_window()

        path = os.path.join(self.image_dir, image_name)
        deadline = time.monotonic() + timeout
        last_error = None

        logging.info("Searching for image: %s (confidence=%.2f, timeout=%.1fs)", image_name, confidence, timeout)

        while time.monotonic() < deadline:
            try:
                location = pyautogui.locateCenterOnScreen(
                    path,
                    confidence=confidence,
                    region=self.region
                )
                if location:
                    logging.info("Found %s at %s", image_name, location)
                    self._click_point(location.x, location.y)
                    time.sleep(wait_after)
                    logging.info("Clicked %s successfully.", image_name)
                    return True

            except pyautogui.ImageNotFoundException as e:
                last_error = e
            except Exception as e:
                logging.exception("Unexpected error while searching for %s", image_name)
                raise BotError(f"Image search crashed for {image_name}: {e}") from e

            time.sleep(0.35)

        msg = f"Timed out waiting for {image_name}"
        if required:
            raise BotError(msg) from last_error
        logging.warning(msg)
        return False

    def scroll_and_find(self, target_image, anchor_x, anchor_y, max_attempts=15, confidence=0.9):
        self._require_window()

        base_x = self.game_window.left + anchor_x
        base_y = self.game_window.top + anchor_y

        logging.info("Scrolling to find %s", target_image)

        for attempt in range(1, max_attempts + 1):
            logging.info("Scroll attempt %d/%d", attempt, max_attempts)

            if self.find_and_click(target_image, confidence=confidence, wait_after=0.8, timeout=0.6):
                logging.info("Target found: %s", target_image)
                return True

            self._click_point(base_x, base_y)
            time.sleep(0.15)

            logging.info("Scrolling down.")
            pyautogui.scroll(-300)
            time.sleep(0.45)

        raise BotError(f"Failed to find {target_image} after {max_attempts} scroll attempts.")
    
    def speedupgame(self, relx, rely):
        abs_x = self.game_window.left + relx
        abs_y = self.game_window.top + rely
        logging.info("Clicking speed-up at (%d, %d)", abs_x, abs_y)
        pyautogui.moveTo(abs_x, abs_y, duration=0.15)
        pyautogui.click()
        time.sleep(1)
        pyautogui.click()
        time.sleep(1)
        pyautogui.click()
        time.sleep(1)

    def clickOnScreen(self, rel_x, rel_y):
        abs_x = self.game_window.left + rel_x
        abs_y = self.game_window.top + rel_y
        logging.info("Clicking on screen at (%d, %d)", abs_x, abs_y)
        pyautogui.moveTo(abs_x, abs_y, duration=0.15)
        time.sleep(0.5)
        pyautogui.click()
        time.sleep(1)


class FastEntity:
    """A heavily optimized entity that uses exact coordinates and hotkeys."""
    def __init__(self, name, vision_controller, rel_x, rel_y, hotkey='n'):
        self.name = name
        self.vision = vision_controller
        self.rel_x = rel_x
        self.rel_y = rel_y
        self.hotkey = hotkey # default hotkey for building this entity

    def _get_absolute_coords(self):
        win = self.vision.game_window
        return (win.left + self.rel_x, win.top + self.rel_y)


    def get_hotkey(self, action_name):
        if action_name == "upgrade_tower":
            return 'l'
        if action_name == "delete_build":
            return '.'
        if action_name == "update_tower_level_1":
            return 'num1'
        if action_name == "upgrade_tower_level_2":
            return 'num2'
        if action_name == "upgrade_tower_level_3":
            return 'num3'
        if action_name == "upgrade_tower_level_5":
            return 'num5'
        return self.hotkey # default hotkey for building this entity
    
    def interact(self, action_name="initial_build"):
        abs_x, abs_y = self._get_absolute_coords()
        hotkeyForAction = self.get_hotkey(action_name)
        
        logging.info("[%s] %s at (%s, %s)", self.name, action_name, abs_x, abs_y)

        pyautogui.moveTo(abs_x, abs_y, duration=0.15)
        pyautogui.click()
        time.sleep(0.3)

        pyautogui.click()   # second click ensures selection
        time.sleep(0.5)

        pyautogui.keyDown(hotkeyForAction)
        time.sleep(0.08)
        pyautogui.keyUp(hotkeyForAction)

        logging.info("[%s] Hotkey '%s' pressed. for action %s", self.name, self.hotkey, action_name)



    def upgradeUptoPossibleLevels(self, action_name="upgrade_tower", levelsOrder=[2,3,5]):
        self.interact(action_name=action_name)

        for level in levelsOrder:
                self.interact(action_name=action_name+"_level_"+str(level))

        return True


class GameManager:
    """Orchestrates the continuous game lifecycle."""
    def __init__(self):
        self.vision = VisionController()
        self.crusher = FastEntity("Crusher", self.vision, rel_x=959, rel_y=560,hotkey='n')
        self.expCard = FastEntity("Exp Card", self.vision, rel_x=957, rel_y=607,hotkey='[')
        self.green_miner = FastEntity("Green Miner", self.vision, rel_x=718, rel_y=468, hotkey='3')
        self.green_speedCard = FastEntity("Green Speed Card", self.vision, rel_x=768, rel_y=508, hotkey=']')
        self.blue_miner = FastEntity("Blue Miner", self.vision, rel_x=771, rel_y=378, hotkey='4')
        self.blue_speedCard = FastEntity("Blue Speed Card", self.vision, rel_x=817, rel_y=370, hotkey=']')
        self.yellow_miner = FastEntity("Yellow Miner", self.vision, rel_x=863, rel_y=515)
        self.cyan_miner = FastEntity("Cyan Miner", self.vision, rel_x=718, rel_y=468, hotkey='e')
        self.crusher2 = FastEntity("Crusher2", self.vision, rel_x=861, rel_y=608,hotkey='n')
        self.freezer = FastEntity("Freezer", self.vision, rel_x=1054, rel_y=606,hotkey='6')
    def _check_abort(self):
        if keyboard.is_pressed('q'):
            raise BotError("Manual kill switch pressed.")
            
    def log_game_count(self, cycle_count):
        """Appends the completed game count to a dedicated log file."""
        log_filename = "games_played.log"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(log_filename, "a") as f:
                f.write(f"[{timestamp}] Successfully finished game #{cycle_count}\n")
            logging.info("Logged game #%d completion to %s", cycle_count, log_filename)
        except Exception as e:
            logging.error("Failed to write to %s: %s", log_filename, e)

    def phase_start_round_setup(self):
        logging.info("PHASE 1: Start Round Setup")
        self._check_abort()

        time.sleep(2)

        self.vision.find_and_click("select_level.png", wait_after=1.5, timeout=6.0, required=True)

        time.sleep(1.5)

        self.vision.scroll_and_find(
            "level_6_3.png",
            anchor_x=1898,
            anchor_y=728,
            max_attempts=20,
            confidence=0.9
        )

        time.sleep(1.5)

        self.vision.find_and_click("continue.png", wait_after=1.5, timeout=10.0, confidence=0.75, required=True)

        time.sleep(1.5)

        self.vision.find_and_click("play.png", wait_after=5.0, timeout=10.0, confidence=0.75, required=True)

        logging.info("Round setup complete.")

    def phase_game_init_setup(self):
        logging.info("PHASE 2: Game Init Setup")
        self._check_abort()

        logging.info("Waiting for map to fully load.")
        time.sleep(1)

        self.crusher.interact("initial_build")
        time.sleep(1)
        self.expCard.interact("initial_build")
        time.sleep(1)
        self.yellow_miner.interact("delete_build")
        time.sleep(1)
        self.green_miner.interact("delete_build")
        time.sleep(1)
        self.cyan_miner.interact("initial_build")
        time.sleep(1)
        self.isCyanMinerBuilt = True

        self.vision.speedupgame(relx=242, rely=1004)
        time.sleep(2)
        logging.info("Clicking Start Wave.")
        self.vision.find_and_click("start_wave.png", wait_after=1.0, required=True)

        logging.info("Initial game setup complete.")

    def phase_gameplay_loop(self, total_duration_seconds=500): # Modify accordingly
        logging.info("PHASE 3: Gameplay Loop (%s seconds)", total_duration_seconds)

        start_time = time.monotonic()
        early_game_end = start_time + min(250, total_duration_seconds)  # First 200 seconds or total duration, whichever is shorter
        end_time = start_time + total_duration_seconds

        logging.info("Early game phase started.")
        while time.monotonic() < early_game_end:
            self._check_abort()
            self.crusher.upgradeUptoPossibleLevels("upgrade_tower")
            time.sleep(4)

        logging.info("Mid/Late game phase started.")

        greenMinerBuildTries = 0;
        blueMinerBuildTries = 0;
        greenSpeedCardBuildTries = 0;
        blueSpeedCardBuildTries = 0;
        blueTime = start_time + 600;

        while time.monotonic() < end_time:
            self._check_abort()
            if (self.isCyanMinerBuilt):
                self.cyan_miner.interact("delete_build")
                time.sleep(1)
                self.green_miner.interact("initial_build")
                time.sleep(1)
                self.isCyanMinerBuilt = False


            if(greenMinerBuildTries < 3):
                self.green_miner.interact("initial_build")
                greenMinerBuildTries += 1

            self.green_miner.interact("upgrade_tower")
            
            if(greenSpeedCardBuildTries < 3):
                 self.green_speedCard.interact("initial_build")
                 greenSpeedCardBuildTries += 1
            

            if time.monotonic() > blueTime:  # After 5 minutes, be more aggressive with blue miner upgrades
                if(blueMinerBuildTries < 3):
                    self.blue_miner.interact("initial_build")
                    blueMinerBuildTries += 1
                self.blue_miner.interact("upgrade_tower")
                 
                if (blueSpeedCardBuildTries < 3):
                    self.blue_speedCard.interact("initial_build")
                    blueSpeedCardBuildTries += 1

            self.crusher.upgradeUptoPossibleLevels("upgrade_tower")
            logging.info("Upgrade cycle completed. Sleeping 3 seconds.")
            time.sleep(3)

        logging.info("Gameplay loop finished normally.")
        return True

    def phase_game_end_setup(self):
        logging.info("PHASE 4: Game End Setup")
        logging.info("Waiting for end screen.")

        # INCREASED DELAYS: Give the game UI more time to catch up and render completely.
        self.vision.clickOnScreen(rel_x=65, rel_y=80) # Click top-left to open pause menu
        time.sleep(2) # Increased from 1s to 2s
        
        self.vision.clickOnScreen(rel_x=1611, rel_y=886) # End Game Click
        time.sleep(2) # Increased from 1s to 2s
        
        self.vision.clickOnScreen(rel_x=1512, rel_y=750) # Consent Click
        time.sleep(5) # Increased from 3s to 5s
        
        self.vision.clickOnScreen(rel_x=654, rel_y=791) # Another Consent Click to go back to ensure it registers
        time.sleep(12) # Increased from 8s to 12s - longer delay for resource screen to load
        
        self.vision.clickOnScreen(rel_x=394, rel_y=65) # Click on anywhere here rel_x=394, rel_y=65 screen to get past the gained resource screen
        time.sleep(8) # Increased from 5s to 8s - wait for main menu to fully load
        
        self.vision.clickOnScreen(rel_x=82, rel_y=1021) # Click back button to get back to main menu
        time.sleep(5) # Increased from 3s to 5s - ready to restart loop

    def run_infinite_bot(self):
        logging.info("Starting bot.")
        self.vision.focus_window()

        cycle_count = 1
        while True:
            try:
                self._check_abort()

                logging.info("==================================")
                logging.info("STARTING BOT CYCLE #%d", cycle_count)
                logging.info("==================================")

                self.phase_start_round_setup()
                self.phase_game_init_setup()

                if not self.phase_gameplay_loop(total_duration_seconds=700): # Adjust the total duration of the gameplay loop as needed
                    logging.warning("Gameplay loop stopped early.")
                    break

                self.phase_game_end_setup()
                
                # Log the completed cycle to the external text file
                self.log_game_count(cycle_count)
                
                cycle_count += 1

            except BotError as e:
                logging.exception("Bot stopped because of an error: %s", e)
                sys.exit(1)
            except pyautogui.FailSafeException:
                logging.exception("PyAutoGUI fail-safe triggered.")
                sys.exit(1)
            except KeyboardInterrupt:
                logging.exception("Keyboard interrupt received.")
                sys.exit(1)
            except Exception as e:
                logging.exception("Unexpected crash: %s", e)
                sys.exit(1)


if __name__ == "__main__":
    logging.info("Welcome to the Infinitode Hybrid Auto-Bot.")
    logging.info("Ensure the game is open and images are in the 'images/' folder.")
    logging.info("Press and hold 'q' at any time to safely stop the bot.")

    bot = GameManager()
    bot.run_infinite_bot()