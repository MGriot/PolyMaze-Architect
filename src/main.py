# main.py
import arcade
import config
from views import MainMenuView

def main():
    window = arcade.Window(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, config.SCREEN_TITLE)
    menu = MainMenuView()
    window.show_view(menu)
    arcade.run()

if __name__ == "__main__":
    main()