import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.properties import StringProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.screenmanager import ScreenManager, Screen
import random
import json
import os
from datetime import datetime
from nba_api.stats.static import players
from nba_api.stats.endpoints import commonplayerinfo, playercareerstats
import requests
from PIL import Image
from io import BytesIO
import tempfile

STREAK_FILE = "nba_streak.json"

class NBAPlayerGuesserGUI(App):
    def build(self):
        from kivy.utils import get_color_from_hex
        self.title = "HoopMind"
        self.session_id = datetime.now().strftime("%Y%m%d")
        self.streak_data = self.load_streak()
        self.max_attempts = 6
        self.guesses = []
        self.all_players = [p for p in players.get_players() if p.get('is_active')]
        self.target_player = None
        self.target_player_info = None
        self.reveal_level = 0
        self.mode = 'original'  # Always original mode
        self.time_left = 60
        self.score = 0
        # --- Custom Font Setup ---
        # Download and use a Google Fonts TTF (Montserrat) for a modern look
        # Place 'Montserrat-Bold.ttf' and 'Montserrat-Regular.ttf' in the same directory as this script
        font_bold = os.path.join(os.path.dirname(__file__), 'Montserrat-Bold.ttf')
        font_regular = os.path.join(os.path.dirname(__file__), 'Montserrat-Regular.ttf')
        # --- Main Layout with Canvas Background ---
        self.root = BoxLayout(orientation='vertical', padding=10, spacing=10)
        from kivy.graphics import Color, Rectangle, RoundedRectangle
        with self.root.canvas.before:
            Color(*get_color_from_hex('#0B162A'))
            self.bg_rect = Rectangle(pos=self.root.pos, size=self.root.size)
        def update_bg_rect(instance, value):
            self.bg_rect.pos = instance.pos
            self.bg_rect.size = instance.size
        self.root.bind(pos=update_bg_rect, size=update_bg_rect)
        # --- Header ---
        self.header = Label(text="[b]HoopMind[/b]", markup=True, font_size=36, size_hint=(1, 0.13), color=get_color_from_hex('#FDB927'))
        self.root.add_widget(self.header)
        # --- Subheader ---
        self.status_label = Label(text="Guess the NBA player in 6 tries!", markup=True, font_size=22, size_hint=(1, 0.08), color=get_color_from_hex('#C9082A'))
        self.root.add_widget(self.status_label)
        # --- Image Frame with Rounded Corners and Drop Shadow ---
        image_frame = BoxLayout(size_hint=(1, 0.45), padding=8)
        with image_frame.canvas.before:
            # Drop shadow
            Color(0, 0, 0, 0.35)
            self.shadow_rect = RoundedRectangle(pos=(image_frame.x+4, image_frame.y-4), size=image_frame.size, radius=[24])
            # Main frame
            Color(*get_color_from_hex('#1D428A'))
            self.image_bg = RoundedRectangle(pos=image_frame.pos, size=image_frame.size, radius=[24])
        def update_image_bg(instance, value):
            self.image_bg.pos = instance.pos
            self.image_bg.size = instance.size
            self.shadow_rect.pos = (instance.x+4, instance.y-4)
            self.shadow_rect.size = instance.size
        image_frame.bind(pos=update_image_bg, size=update_image_bg)
        self.image_widget = AsyncImage(size_hint=(1, 1))
        image_frame.add_widget(self.image_widget)
        self.root.add_widget(image_frame)
        # --- Clue label ---
        self.clue_label = Label(text="", markup=True, font_size=18, size_hint=(1, 0.08), color=get_color_from_hex('#FDB927'))
        self.root.add_widget(self.clue_label)
        # --- Guess input and button row with rounded corners ---
        input_row = BoxLayout(orientation='horizontal', size_hint=(1, 0.09), spacing=8)
        self.guess_input = TextInput(hint_text="Enter player name", multiline=False, font_size=18, background_color=get_color_from_hex('#F5F5F5'), foreground_color=get_color_from_hex('#0B162A'), padding=[12, 8, 12, 8])
        # Add dropdown for player suggestions
        from kivy.uix.dropdown import DropDown
        self.dropdown = DropDown(auto_width=False, width=350, max_height=200)
        self.guess_input.bind(text=self.update_dropdown)
        self.guess_input.bind(focus=self.on_input_focus)
        # Rounded corners for TextInput (fix: use canvas.after instead of canvas.before to avoid blocking input)
        with self.guess_input.canvas.after:
            Color(1, 1, 1, 0)  # Transparent, just for structure
            self.input_bg = RoundedRectangle(pos=self.guess_input.pos, size=self.guess_input.size, radius=[16])
        def update_input_bg(instance, value):
            self.input_bg.pos = instance.pos
            self.input_bg.size = instance.size
        self.guess_input.bind(pos=update_input_bg, size=update_input_bg)
        input_row.add_widget(self.guess_input)
        self.submit_btn = Button(text="Submit Guess", font_size=18, background_color=get_color_from_hex('#C9082A'), color=get_color_from_hex('#FDB927'))
        # Rounded corners and drop shadow for button
        with self.submit_btn.canvas.before:
            Color(0, 0, 0, 0.25)
            self.btn_shadow = RoundedRectangle(pos=(self.submit_btn.x+2, self.submit_btn.y-2), size=self.submit_btn.size, radius=[16])
            Color(*get_color_from_hex('#C9082A'))
            self.btn_bg = RoundedRectangle(pos=self.submit_btn.pos, size=self.submit_btn.size, radius=[16])
        def update_btn_bg(instance, value):
            self.btn_bg.pos = instance.pos
            self.btn_bg.size = instance.size
            self.btn_shadow.pos = (instance.x+2, instance.y-2)
            self.btn_shadow.size = instance.size
        self.submit_btn.bind(pos=update_btn_bg, size=update_btn_bg)
        self.submit_btn.bind(on_press=self.submit_guess)
        input_row.add_widget(self.submit_btn)
        self.root.add_widget(input_row)
        # --- Guess history in a scrollable area ---
        scroll = ScrollView(size_hint=(1, 0.17), bar_color=get_color_from_hex('#FDB927'))
        self.guess_history = Label(text="", markup=True, font_size=16, size_hint=(1, None), color=get_color_from_hex('#F5F5F5'))
        self.guess_history.bind(texture_size=self.guess_history.setter('size'))
        scroll.add_widget(self.guess_history)
        self.root.add_widget(scroll)
        self.start_new_game()
        return self.root

    def load_streak(self):
        try:
            with open(STREAK_FILE, 'r') as f:
                data = json.load(f)
                today = datetime.now().strftime("%Y%m%d")
                if data.get("last_session") != today:
                    data["streak"] = 0
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return {"streak": 0, "last_session": None}

    def save_streak(self):
        with open(STREAK_FILE, 'w') as f:
            json.dump(self.streak_data, f)

    def start_new_game(self):
        self.guesses = []
        self.reveal_level = 0
        self.status_label.text = "[b]HoopMind[/b]\nGuess the NBA player in 6 tries!"
        self.clue_label.text = ""
        self.guess_history.text = ""
        self.guess_input.text = ""
        self.target_player = random.choice(self.all_players)
        info = commonplayerinfo.CommonPlayerInfo(player_id=self.target_player['id']).get_normalized_dict()
        self.target_player_info = info['CommonPlayerInfo'][0] if info['CommonPlayerInfo'] else None
        self.update_image()

    def update_image(self, force_full_res=False, reveal_actual_image=False):
        person_id = self.target_player_info.get('PERSON_ID')
        resolutions = [
            None,  # 0: blank
            '52x40',  # 1: very blurry
            '104x76', # 2: blurry
            '260x190', # 3: low-res
            '520x380', # 4: mid-res
            '1040x760' # 5: full-res
        ]
        if force_full_res or reveal_actual_image:
            res = resolutions[-1]
        else:
            reveal = min(self.reveal_level, len(resolutions) - 1)
            res = resolutions[reveal]
        if res is None:
            self.image_widget.source = ""
            self.image_widget.reload()
            return
        url = f"https://cdn.nba.com/headshots/nba/latest/{res}/{person_id}.png"
        if reveal_actual_image:
            self.image_widget.source = url
            self.image_widget.reload()
            return
        try:
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                try:
                    img = Image.open(BytesIO(resp.content)).convert("RGBA")
                    gray = img.convert("L")
                    mask = gray.point(lambda x: 0 if x > 40 else 255, mode='1')
                    silhouette = Image.new("RGBA", img.size, (255,255,255,0))
                    for y in range(img.size[1]):
                        for x in range(img.size[0]):
                            if mask.getpixel((x, y)) == 255:
                                silhouette.putpixel((x, y), (0,0,0,255))
                            else:
                                silhouette.putpixel((x, y), (255,255,255,0))
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                    silhouette.save(tmp.name)
                    self.image_widget.source = tmp.name
                except Exception:
                    self.image_widget.source = url
            else:
                blank = Image.new("RGBA", (104, 76), (255,255,255,0))
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                blank.save(tmp.name)
                self.image_widget.source = tmp.name
        except Exception:
            blank = Image.new("RGBA", (104, 76), (255,255,255,0))
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            blank.save(tmp.name)
            self.image_widget.source = tmp.name
        self.image_widget.reload()

    def submit_guess(self, instance):
        guess = self.guess_input.text.strip()
        if not guess:
            return
        found = [p for p in self.all_players if guess.lower() in p['full_name'].lower()]
        if not found:
            self.status_label.text = "[color=ff0000][b]Player not found. Try again.[/b][/color]"
            return
        player_info = commonplayerinfo.CommonPlayerInfo(player_id=found[0]['id']).get_normalized_dict()
        if not player_info['CommonPlayerInfo']:
            self.status_label.text = "[color=ff0000][b]Player data not found. Try again.[/b][/color]"
            return
        guessed = player_info['CommonPlayerInfo'][0]
        feedback = self.compare_guess(guessed)
        self.guesses.append(feedback)
        self.update_guess_history()
        if self.check_win(guessed):
            self.reveal_level = len([None, '52x40', '104x76', '260x190', '520x380', '1040x760']) - 1
            self.update_image(force_full_res=True, reveal_actual_image=True)
            self.status_label.text = "[color=00ff00][b]🎉 Correct! You guessed it![/b][/color]"
            self.update_streak(True)
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: self.show_popup(f"Correct! The player was {self.target_player_info['DISPLAY_FIRST_LAST']}\nStreak: {self.streak_data['streak']}", restart=True), 10)
        else:
            self.reveal_level = min(self.reveal_level + 1, 5)
            self.update_image()
            clue = self.get_player_clue(self.target_player_info['PERSON_ID'])
            self.clue_label.text = f"{clue}"
            if len(self.guesses) == self.max_attempts:
                self.reveal_level = 5
                self.update_image(force_full_res=True, reveal_actual_image=True)
                self.status_label.text = f"[color=ff0000][b]❌ Game Over! The player was {self.target_player_info['DISPLAY_FIRST_LAST']}[/b][/color]"
                self.update_streak(False)
                from kivy.clock import Clock
                Clock.schedule_once(lambda dt: self.show_popup(f"Game Over! The player was {self.target_player_info['DISPLAY_FIRST_LAST']}\nStreak: {self.streak_data['streak']}", restart=True), 10)

    def update_guess_history(self):
        text = "[b]Guesses:[/b]\n"
        for i, guess in enumerate(self.guesses, 1):
            # Color feedback for each stat
            team_color = "00ff00" if guess.get('team_match') else "ff0000"
            pos_color = "00ff00" if guess.get('position_match') else "ff0000"
            height_color = "00ff00" if guess.get('height_match') else "ff0000"
            weight_color = "00ff00" if guess.get('weight_match') else "ff0000"
            conf_color = "00ff00" if guess.get('conference_match') else "ff0000"
            div_color = "00ff00" if guess.get('division_match') else "ff0000"
            text += (
                f"{i}. {guess['name']} | "
                f"Team: [color={team_color}]{guess['team']}[/color] | "
                f"Pos: [color={pos_color}]{guess['position']}[/color] | "
                f"Height: [color={height_color}]{guess['height']}[/color] | "
                f"Weight: [color={weight_color}]{guess['weight']}[/color] | "
                f"Conf: [color={conf_color}]{guess['conference']}[/color] | "
                f"Div: [color={div_color}]{guess['division']}[/color]\n"
            )
        self.guess_history.text = text

    def compare_guess(self, guessed_player):
        # Helper to get conference/division from TEAM_ABBREVIATION
        def get_conf_div(team_abbr):
            nba_teams = {
                'ATL': ('East', 'Southeast'), 'BOS': ('East', 'Atlantic'), 'BKN': ('East', 'Atlantic'), 'CHA': ('East', 'Southeast'),
                'CHI': ('East', 'Central'), 'CLE': ('East', 'Central'), 'DAL': ('West', 'Southwest'), 'DEN': ('West', 'Northwest'),
                'DET': ('East', 'Central'), 'GSW': ('West', 'Pacific'), 'HOU': ('West', 'Southwest'), 'IND': ('East', 'Central'),
                'LAC': ('West', 'Pacific'), 'LAL': ('West', 'Pacific'), 'MEM': ('West', 'Southwest'), 'MIA': ('East', 'Southeast'),
                'MIL': ('East', 'Central'), 'MIN': ('West', 'Northwest'), 'NOP': ('West', 'Southwest'), 'NYK': ('East', 'Atlantic'),
                'OKC': ('West', 'Northwest'), 'ORL': ('East', 'Southeast'), 'PHI': ('East', 'Atlantic'), 'PHX': ('West', 'Pacific'),
                'POR': ('West', 'Northwest'), 'SAC': ('West', 'Pacific'), 'SAS': ('West', 'Southwest'), 'TOR': ('East', 'Atlantic'),
                'UTA': ('West', 'Northwest'), 'WAS': ('East', 'Southeast')
            }
            return nba_teams.get(team_abbr, ('N/A', 'N/A'))
        # Get conference/division for guessed and target
        guessed_conf, guessed_div = get_conf_div(guessed_player.get('TEAM_ABBREVIATION'))
        target_conf, target_div = get_conf_div(self.target_player_info.get('TEAM_ABBREVIATION'))
        feedback = {
            'name': guessed_player['DISPLAY_FIRST_LAST'],
            'team': guessed_player['TEAM_ABBREVIATION'] if guessed_player['TEAM_ABBREVIATION'] else 'N/A',
            'position': guessed_player['POSITION'] or 'N/A',
            'height': guessed_player['HEIGHT'] if guessed_player['HEIGHT'] else 'N/A',
            'weight': int(guessed_player['WEIGHT']) if guessed_player['WEIGHT'] else 0,
            'conference': guessed_conf,
            'division': guessed_div,
            'team_match': guessed_player['TEAM_ID'] == self.target_player_info['TEAM_ID'],
            'position_match': guessed_player['POSITION'] and self.target_player_info['POSITION'] and guessed_player['POSITION'].lower() == self.target_player_info['POSITION'].lower(),
            'height_match': guessed_player['HEIGHT'] == self.target_player_info['HEIGHT'],
            'weight_match': abs(int(guessed_player['WEIGHT'] or 0) - int(self.target_player_info['WEIGHT'] or 0)) <= 10 if guessed_player['WEIGHT'] and self.target_player_info['WEIGHT'] else False,
            'conference_match': guessed_conf == target_conf and guessed_conf != 'N/A',
            'division_match': guessed_div == target_div and guessed_div != 'N/A',
        }
        return feedback

    def check_win(self, guessed_player):
        return guessed_player['DISPLAY_FIRST_LAST'].lower() == self.target_player_info['DISPLAY_FIRST_LAST'].lower()

    def update_streak(self, won):
        if won:
            self.streak_data['streak'] += 1
        else:
            self.streak_data['streak'] = 0
        self.streak_data['last_session'] = self.session_id
        self.save_streak()

    def get_player_clue(self, player_id):
        try:
            stats = playercareerstats.PlayerCareerStats(player_id=player_id).get_normalized_dict()
            if 'CareerStats' in stats and stats['CareerStats']:
                career = stats['CareerStats'][0]
            elif 'CareerTotalsRegularSeason' in stats and stats['CareerTotalsRegularSeason']:
                career = stats['CareerTotalsRegularSeason'][0]
            else:
                return "No stats available."
            gp = float(career.get('GP', 0))
            ppg = float(career.get('PTS', 0)) / gp if gp else 0
            rpg = float(career.get('REB', 0)) / gp if gp else 0
            apg = float(career.get('AST', 0)) / gp if gp else 0
            return f"Clue: Career averages - PPG: {ppg:.1f}, RPG: {rpg:.1f}, APG: {apg:.1f}"
        except Exception as e:
            return f"Clue unavailable due to error: {e}"

    def show_popup(self, message, restart=False):
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=message, font_size=18))
        btn = Button(text="Play Again" if restart else "OK", size_hint=(1, 0.3), font_size=18)
        content.add_widget(btn)
        popup = Popup(title="HoopMind", content=content, size_hint=(0.7, 0.4))
        btn.bind(on_press=lambda x: (popup.dismiss(), self.start_new_game() if restart else None))
        popup.open()

    def update_dropdown(self, instance, value):
        from kivy.utils import get_color_from_hex
        text = value.strip().lower()
        if not text or len(text) < 2:
            self.dropdown.dismiss()
            return
        matches = [p['full_name'] for p in self.all_players if text in p['full_name'].lower()][:10]
        if not matches:
            self.dropdown.dismiss()
            return
        current_names = [w.text for w in self.dropdown.container.children]
        if current_names[::-1] == matches:
            if not self.dropdown.attach_to:
                self.dropdown.open(self.guess_input)
            return
        self.dropdown.clear_widgets()
        for i, name in enumerate(matches):
            btn = Button(
                text=name,
                size_hint_y=None,
                height=38,
                font_size=17,
                background_normal='',
                background_color=get_color_from_hex('#F5F5F5') if i % 2 == 0 else get_color_from_hex('#E0E0E0'),
                color=get_color_from_hex('#0B162A'),
                halign='left',
                valign='middle',
                padding=(16, 8)
            )
            btn.text_size = (320, None)
            btn.bind(on_release=lambda btn: self.select_suggestion(btn.text))
            self.dropdown.add_widget(btn)
        if not self.dropdown.attach_to:
            self.dropdown.open(self.guess_input)

    def select_suggestion(self, name):
        self.guess_input.text = name
        self.dropdown.dismiss()
        self.guess_input.focus = True

    def on_input_focus(self, instance, value):
        if not value:
            self.dropdown.dismiss()

if __name__ == "__main__":
    NBAPlayerGuesserGUI().run()
