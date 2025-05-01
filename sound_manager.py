import os
import pygame # Import pygame
import time # Import time for waiting in test

# Initialize pygame mixer (needs to be done once)
try:
    pygame.mixer.init()
    print("[SoundManager] Pygame mixer initialized.")
except pygame.error as init_error:
    print(f"[SoundManager] Error initializing pygame mixer: {init_error}")
    # Consider how to handle this - maybe disable sound?
    pygame = None # Disable pygame if init fails

SOUND_FILE_NAME = "twinkling_sound.mp3" # Updated sound file name

def play_notification_sound(sound_type='default'):
    """Plays the notification sound, falling back to system sound if necessary."""
    try:
        # Construct absolute path relative to this script's location
        script_dir = os.path.dirname(__file__)
        sound_file_path = os.path.abspath(os.path.join(script_dir, SOUND_FILE_NAME))

        if os.path.exists(sound_file_path):
            # Play using pygame.mixer (it plays asynchronously by default)
            if pygame and pygame.mixer.get_init(): # Check if pygame and mixer initialized successfully
                try:
                    sound = pygame.mixer.Sound(sound_file_path)
                    sound.play()
                    # No need to wait here, play() is non-blocking
                except pygame.error as play_error:
                    print(f"[{sound_type}] Error playing sound with pygame: {play_error}")
            else:
                print(f"[{sound_type}] Pygame mixer not initialized, cannot play sound.")
        else:
            # Fallback: Pygame also doesn't play system sounds directly.
            print(f"[{sound_type}] Sound file not found at {sound_file_path}. Cannot play sound.")
    except Exception as e:
        # Error handling is now within the pygame play block.
        print(f"[{sound_type}] Error occurred trying to play sound: {e}") # Keep one error message

if __name__ == '__main__':
    # Simple test when running this file directly
    if pygame and pygame.mixer.get_init():
        print("Testing notification sound with pygame.mixer...")
        play_notification_sound('test')
        # Wait a bit for the sound to play in the background during test
        print("Waiting for sound to finish (approx 5s)...")
        time.sleep(5) 
        print("Test finished.")
        pygame.mixer.quit() # Clean up mixer when test is done
    else:
        print("Pygame mixer not initialized. Cannot run test.")