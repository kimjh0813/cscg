from pathlib import Path

from kivy.app import App
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import ListProperty, NumericProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget

from data import ANIME_LIST, get_all_genres
from recommender import recommend_anime
from theme import BLACK, CARD, MUTED, PANEL, RED, SOFT, WHITE


BASE_DIR = Path(__file__).resolve().parent
FONT_DIR = BASE_DIR / "assets" / "fonts"
APP_FONT_PATH = FONT_DIR / "NotoSansKR-Regular.ttf"


def _register_korean_font():
    if not APP_FONT_PATH.exists():
        raise FileNotFoundError(f"프로젝트 폰트 파일을 찾을 수 없습니다: {APP_FONT_PATH}")

    LabelBase.register(name="AppFont", fn_regular=str(APP_FONT_PATH))
    return "AppFont"


FONT_NAME = _register_korean_font()


class GenreSpinnerOption(SpinnerOption):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_name = FONT_NAME
        self.font_size = sp(14)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = SOFT
        self.color = WHITE
        self.size_hint_y = None
        self.height = dp(40)


def _poster_path(anime):
    poster = anime.get("poster")

    if not poster:
        return ""

    path = BASE_DIR / poster
    return str(path) if path.exists() else ""


def _genre_summary(genres):
    return ", ".join(genres) if genres else "추가 장르 없음"


def _featured_anime():
    return max(ANIME_LIST, key=lambda anime: (anime["rating"], anime["year"]))


def _label(
    text,
    font_size=14,
    color=WHITE,
    bold=False,
    height=None,
    halign="left",
    valign="middle",
):
    label = Label(
        text=text,
        font_name=FONT_NAME,
        font_size=sp(font_size),
        color=color,
        bold=bold,
        halign=halign,
        valign=valign,
        markup=True,
        size_hint_y=None,
    )

    def update_text_size(instance, width):
        text_height = instance.height if height is not None else None
        instance.text_size = (width, text_height)

    label.bind(width=update_text_size)

    if height is not None:
        label.height = dp(height)
        label.bind(height=lambda instance, value: setattr(instance, "text_size", (instance.width, value)))
    else:
        label.bind(
            texture_size=lambda instance, value: setattr(instance, "height", value[1] + dp(4)),
        )

    label.text_size = (label.width, label.height if height is not None else None)
    return label


class RoundedPanel(BoxLayout):
    background_color = ListProperty(PANEL)
    radius = NumericProperty(dp(8))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            self._panel_color = Color(*self.background_color)
            self._panel_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[self.radius],
            )

        self.bind(
            pos=self._update_canvas,
            size=self._update_canvas,
            background_color=self._update_canvas,
            radius=self._update_canvas,
        )

    def _update_canvas(self, *args):
        self._panel_color.rgba = self.background_color
        self._panel_rect.pos = self.pos
        self._panel_rect.size = self.size
        self._panel_rect.radius = [self.radius]


def _tag(text, background=SOFT, color=WHITE):
    tag = RoundedPanel(
        orientation="vertical",
        size_hint=(None, None),
        width=max(dp(52), dp(24 + len(text) * 12)),
        height=dp(30),
        padding=(dp(8), 0, dp(8), 0),
        background_color=background,
        radius=dp(15),
    )
    tag.add_widget(_label(text, font_size=12, color=color, bold=True, height=30, halign="center"))
    return tag


class GenreToggle(ToggleButton):
    def __init__(self, genre, **kwargs):
        super().__init__(**kwargs)
        self.genre = genre
        self.font_name = FONT_NAME
        self.font_size = sp(14)
        self.markup = True
        self.halign = "left"
        self.valign = "middle"
        self.padding = (dp(12), 0)
        self.size_hint_y = None
        self.height = dp(38)
        self.background_normal = ""
        self.background_down = ""
        self.color = WHITE
        self.bind(state=self._update_state_style, width=self._update_text_size)
        self._update_state_style()

    @property
    def active(self):
        return self.state == "down"

    def _update_text_size(self, *args):
        self.text_size = (self.width - dp(24), self.height)

    def _update_state_style(self, *args):
        self.text = self.genre
        if self.active:
            self.background_color = RED
        else:
            self.background_color = SOFT
        self._update_text_size()


class PosterCard(ButtonBehavior, RoundedPanel):
    def __init__(self, index, anime, open_detail, **kwargs):
        super().__init__(
            orientation="vertical",
            spacing=0,
            padding=0,
            background_color=CARD,
            radius=dp(8),
            size_hint=(None, None),
            size=(dp(168), dp(326)),
            **kwargs,
        )
        self.anime = anime
        self.open_detail = open_detail

        poster = _poster_path(anime)
        if poster:
            self.add_widget(
                Image(
                    source=poster,
                    fit_mode="cover",
                    size_hint=(1, None),
                    height=dp(238),
                )
            )
        else:
            placeholder = RoundedPanel(
                orientation="vertical",
                background_color=SOFT,
                size_hint=(1, None),
                height=dp(238),
                radius=dp(8),
            )
            placeholder.add_widget(_label("No Image", color=MUTED, halign="center", height=238))
            self.add_widget(placeholder)

        text_area = BoxLayout(
            orientation="vertical",
            spacing=dp(6),
            padding=(dp(10), dp(8), dp(10), dp(8)),
            size_hint=(1, None),
            height=dp(88),
        )
        text_area.add_widget(
            _label(
                f"[color=e50914][b]{index}[/b][/color]  {anime['title']}",
                bold=True,
                height=42,
                valign="top",
            )
        )
        text_area.add_widget(_label(f"{anime['year']} · 평점 {anime['rating']}", font_size=12, color=MUTED, height=24))
        self.add_widget(text_area)

    def on_release(self):
        self.open_detail(self.anime)


class AnimeRecommenderKivyApp(App):
    title = "ANIFLIX 애니 추천"

    def build(self):
        Window.clearcolor = BLACK
        Window.size = (1180, 760)
        self.genres = get_all_genres()
        self.secondary_toggles = {}

        root = BoxLayout(orientation="vertical", spacing=0)
        root.add_widget(self._create_header())

        content = BoxLayout(orientation="horizontal", spacing=dp(18), padding=dp(20))
        content.add_widget(self._create_filter_panel())

        self.result_area = BoxLayout(orientation="vertical", spacing=dp(18), size_hint=(1, 1))
        content.add_widget(self.result_area)

        root.add_widget(content)
        self.reset_selection()
        return root

    def _create_header(self):
        header = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(72),
            padding=(dp(28), 0, dp(28), 0),
        )

        brand = _label("ANIFLIX", font_size=28, color=RED, bold=True, height=72)
        header.add_widget(brand)

        header.add_widget(Widget())
        return header

    def _create_filter_panel(self):
        panel = RoundedPanel(
            orientation="vertical",
            spacing=dp(12),
            padding=dp(18),
            size_hint=(None, 1),
            width=dp(310),
            background_color=PANEL,
            radius=dp(8),
        )

        panel.add_widget(_label("취향 선택", font_size=20, bold=True))
        panel.add_widget(_label("가장 중요한 장르를 먼저 고른 뒤, 함께 보고 싶은 분위기를 추가하세요.", color=MUTED))

        self.primary_spinner = Spinner(
            text="1순위 장르",
            values=self.genres,
            option_cls=GenreSpinnerOption,
            font_name=FONT_NAME,
            font_size=sp(14),
            size_hint=(1, None),
            height=dp(44),
            background_normal="",
            background_down="",
            background_color=SOFT,
            color=WHITE,
        )
        panel.add_widget(self.primary_spinner)
        panel.add_widget(_label("추가 장르", color=MUTED, height=24))

        scroll = ScrollView(size_hint=(1, 1))
        genre_box = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        genre_box.bind(minimum_height=genre_box.setter("height"))

        for genre in self.genres:
            toggle = GenreToggle(genre)
            genre_box.add_widget(toggle)
            self.secondary_toggles[genre] = toggle

        scroll.add_widget(genre_box)
        panel.add_widget(scroll)

        button_row = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint=(1, None), height=dp(48))
        button_row.add_widget(self._button("추천받기", self.show_recommendations, background=RED))
        button_row.add_widget(self._button("초기화", self.reset_selection, width=dp(86), background=SOFT))
        panel.add_widget(button_row)
        return panel

    def _button(self, text, callback, width=None, background=SOFT):
        button = Button(
            text=text,
            font_name=FONT_NAME,
            bold=True,
            background_normal="",
            background_down="",
            background_color=background,
            color=WHITE,
            size_hint=(None, 1) if width else (1, 1),
            width=width or dp(120),
        )
        button.bind(on_release=lambda instance: callback())
        return button

    def _render_default(self):
        self._render_hero(_featured_anime())
        popular = sorted(ANIME_LIST, key=lambda anime: anime["rating"], reverse=True)[:10]
        self._render_results("오늘의 인기 애니", "처음이라면 평점이 높은 작품부터 둘러보세요.", popular)

    def _render_hero(self, anime, primary_genre=None, secondary_genres=None):
        hero = RoundedPanel(
            orientation="horizontal",
            spacing=dp(22),
            padding=dp(18),
            size_hint=(1, None),
            height=dp(280),
            background_color=CARD,
            radius=dp(8),
        )

        poster = _poster_path(anime)
        if poster:
            hero.add_widget(
                Image(
                    source=poster,
                    fit_mode="cover",
                    size_hint=(None, 1),
                    width=dp(170),
                )
            )

        copy = BoxLayout(orientation="vertical", spacing=dp(8), size_hint=(1, 1))
        copy.add_widget(_label("ANIME PICKS", font_size=13, color=RED, bold=True, height=28))
        copy.add_widget(_label(anime["title"], font_size=40, bold=True))

        if primary_genre:
            meta = f"{anime['year']} · 평점 {anime['rating']} · {primary_genre} 추천"
        else:
            meta = f"{anime['year']} · 평점 {anime['rating']} · 오늘의 대표 작품"

        copy.add_widget(_label(meta, font_size=16, bold=True, height=30))
        copy.add_widget(_label(anime["description"], font_size=15, color=MUTED))

        if primary_genre:
            copy.add_widget(_label(f"1순위 {primary_genre} · {_genre_summary(secondary_genres)}", color=WHITE))

        hero.add_widget(copy)
        self.result_area.add_widget(hero)

    def _render_results(self, title, subtitle, anime_list):
        result_scroll = ScrollView(size_hint=(1, 1))
        result_box = BoxLayout(orientation="vertical", spacing=dp(14), size_hint_y=None)
        result_box.bind(minimum_height=result_box.setter("height"))

        result_box.add_widget(_label(title, font_size=22, bold=True))
        result_box.add_widget(_label(subtitle, color=MUTED))

        if not anime_list:
            empty = RoundedPanel(
                orientation="vertical",
                background_color=CARD,
                padding=dp(18),
                size_hint=(1, None),
                height=dp(80),
            )
            empty.add_widget(_label("조건에 맞는 추천 결과가 없습니다. 장르를 다르게 선택해보세요."))
            result_box.add_widget(empty)
        else:
            grid = GridLayout(cols=4, spacing=dp(14), size_hint_y=None)
            grid.bind(minimum_height=grid.setter("height"))

            for index, anime in enumerate(anime_list, start=1):
                grid.add_widget(PosterCard(index, anime, self.open_detail))

            result_box.add_widget(grid)

        result_scroll.add_widget(result_box)
        self.result_area.add_widget(result_scroll)

    def show_recommendations(self):
        primary_genre = self.primary_spinner.text

        if primary_genre == "1순위 장르":
            self._show_message("1순위 장르 선택 필요", "가장 중요하게 볼 1순위 장르를 선택해주세요.")
            return

        secondary_genres = [
            genre
            for genre, toggle in self.secondary_toggles.items()
            if toggle.active and genre != primary_genre
        ]
        recommendations = recommend_anime(primary_genre, secondary_genres)

        self.result_area.clear_widgets()
        self._render_hero(recommendations[0] if recommendations else _featured_anime(), primary_genre, secondary_genres)
        self._render_results("추천 결과", f"1순위 {primary_genre} · {_genre_summary(secondary_genres)}", recommendations)

    def reset_selection(self):
        self.primary_spinner.text = "1순위 장르"

        for toggle in self.secondary_toggles.values():
            toggle.state = "normal"

        if hasattr(self, "result_area"):
            self.result_area.clear_widgets()
            self._render_default()

    def open_detail(self, anime):
        content = RoundedPanel(
            orientation="vertical",
            spacing=dp(16),
            padding=dp(18),
            background_color=PANEL,
            radius=dp(8),
        )
        body = BoxLayout(orientation="horizontal", spacing=dp(20), size_hint=(1, 1))
        poster = _poster_path(anime)

        if poster:
            poster_panel = RoundedPanel(
                orientation="vertical",
                padding=0,
                background_color=CARD,
                radius=dp(8),
                size_hint=(None, 1),
                width=dp(230),
            )
            poster_panel.add_widget(
                Image(
                    source=poster,
                    fit_mode="cover",
                    size_hint=(1, 1),
                )
            )
            body.add_widget(poster_panel)

        details = BoxLayout(orientation="vertical", spacing=dp(8), size_hint=(1, 1))
        details.add_widget(_label("작품 상세", font_size=13, color=RED, bold=True, height=24))
        details.add_widget(_label(anime["title"], font_size=30, bold=True, height=48))
        details.add_widget(
            _label(
                f"{anime['year']} · 평점 {anime['rating']} · 추천 점수 {anime.get('score', 0):.2f}",
                color=MUTED,
                height=28,
            )
        )

        genre_row = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(34))
        for genre in anime["genres"]:
            genre_row.add_widget(_tag(genre, background=SOFT))
        genre_row.add_widget(Widget())
        details.add_widget(genre_row)

        details.add_widget(_label("소개", font_size=14, color=WHITE, bold=True, height=28))

        description_box = BoxLayout(orientation="vertical", size_hint_y=None)
        description_box.bind(minimum_height=description_box.setter("height"))
        description_box.add_widget(
            _label(
                anime["description"],
                font_size=15,
                color=MUTED,
                valign="top",
            )
        )

        if anime.get("primary_affinity") is not None:
            secondary = _genre_summary(anime.get("secondary_affinity", {}).keys())
            description_box.add_widget(
                _label(
                    f"1순위 장르 가까움 {anime['primary_affinity']:.2f} · 추가 반영 {secondary}",
                    color=MUTED,
                )
            )

        description_scroll = ScrollView(size_hint=(1, 1))
        description_scroll.add_widget(description_box)
        details.add_widget(description_scroll)

        body.add_widget(details)
        content.add_widget(body)

        button_row = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint=(1, None), height=dp(44))
        button_row.add_widget(Widget())
        close_button = Button(
            text="닫기",
            font_name=FONT_NAME,
            bold=True,
            background_normal="",
            background_down="",
            background_color=RED,
            color=WHITE,
            size_hint=(None, 1),
            width=dp(96),
        )
        button_row.add_widget(close_button)
        content.add_widget(button_row)

        popup = Popup(
            title="",
            content=content,
            size_hint=(None, None),
            size=(dp(820), dp(500)),
            title_font=FONT_NAME,
            title_color=WHITE,
            title_size=0,
            separator_height=0,
            background_color=BLACK,
        )
        close_button.bind(on_release=popup.dismiss)
        popup.open()

    def _show_message(self, title, message):
        content = BoxLayout(orientation="vertical", spacing=dp(16), padding=dp(16))
        content.add_widget(_label(message, color=WHITE))

        popup = Popup(
            title=title,
            content=content,
            size_hint=(None, None),
            size=(dp(420), dp(200)),
            title_font=FONT_NAME,
            title_color=WHITE,
            background_color=BLACK,
        )
        content.add_widget(self._button("확인", popup.dismiss, background=RED))
        popup.open()


def run_app():
    AnimeRecommenderKivyApp().run()
