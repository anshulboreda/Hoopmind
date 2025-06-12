# Hoopmind


Hoopmind is an NBA player guessing game with a modern GUI, built in Python using Kivy and the NBA API. Try to guess the randomly selected NBA player in 6 tries or less! The game provides feedback for each guess, including stats and clues, and features silhouette image reveals as you progress.

---

## Features

- **NBA Player Guessing Game:** Guess the NBA player based on silhouette images and stat clues.
- **Modern Kivy GUI:** Responsive, colorful interface using Kivy, with custom fonts and advanced layouts.
- **NBA API Integration:** Live NBA player data (name, team, position, stats, etc) powered by the [nba_api](https://github.com/swar/nba_api) package.
- **Image Reveal:** Silhouette and gradual reveal of player headshots.
- **Stat Feedback:** Each guess shows feedback on team, position, height, weight, conference, and division.
- **Guess History:** Scrollable history of your guesses with color-coded feedback.
- **Streak Tracking:** Keeps track of your winning streaks across sessions.

---

## Requirements

- Python 3.7+
- [Kivy](https://kivy.org/#download) (GUI framework)
- [nba_api](https://github.com/swar/nba_api) (NBA data)
- [Pillow](https://python-pillow.org/) (image processing)
- [requests](https://docs.python-requests.org/) (HTTP requests)

### Python Dependencies

You can install all requirements with:

```bash
pip install kivy nba_api pillow requests
```

---

## Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/anshulboreda/Hoopmind.git
   cd Hoopmind
   ```

2. **(Optional) Download Fonts:**

   The game uses Montserrat fonts. Place `Montserrat-Bold.ttf` and `Montserrat-Regular.ttf` in the project directory for best appearance. You can download them from [Google Fonts](https://fonts.google.com/specimen/Montserrat).

3. **Run the game:**

   ```bash
   python nba_player_guesser_gui.py
   ```

---

## How to Play

- On launch, an active NBA player is chosen at random.
- Type your guess (player name) in the input box.
- Submit your guess. The app will provide feedback on each stat with color coding:
  - **Green:** Exact match
  - **Red:** Not a match
- With each incorrect guess, the player image is slowly revealed.
- You have 6 attempts to guess the player.
- Keep your streak alive by playing daily!

---

## Project Structure

- `nba_player_guesser_gui.py`: Main Kivy GUI application and game logic.
- `nba_streak.json`: Stores your current streak (auto-generated).
- `README.md`: Project documentation.

---

## Notes

- Requires an internet connection for NBA API data and player images.
- Data and headshots are sourced from [nba.com](https://www.nba.com/) and the [nba_api](https://github.com/swar/nba_api) library.
- For troubleshooting Kivy installations or OS-specific dependencies, see the [Kivy installation docs](https://kivy.org/doc/stable/gettingstarted/installation.html).

---

## License

MIT License

---

## Credits

- [nba_api](https://github.com/swar/nba_api)
- [Kivy](https://kivy.org/)
- NBA data © NBA.com

---

Enjoy guessing!
