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
from kivy.uix.dropdown import DropDown
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget

from data import ANIME_LIST, get_all_genres
from filtering import DEFAULT_PRIMARY_GENRE, genre_summary, request_recommendations
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


# 장르 선택 Spinner의 드롭다운 항목 스타일을 담당하는 클래스
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
        self.height = dp(34)


# 장르 드롭다운 목록이 화면보다 너무 길어지지 않도록 높이를 제한하는 클래스
class GenreDropDown(DropDown):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.max_height = dp(280)


# 애니 데이터에 저장된 포스터 경로를 실제 파일 경로로 변환한다.
def _poster_path(anime):
    poster = anime.get("poster")

    if not poster:
        return ""

    path = BASE_DIR / poster
    return str(path) if path.exists() else ""


# 앱 시작 시 기본으로 보여줄 대표 애니를 평점과 연도 기준으로 선택한다.
def _featured_anime():
    return max(ANIME_LIST, key=lambda anime: (anime["rating"], anime["year"]))


# 앱에서 반복해서 사용하는 Kivy Label 생성 함수
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
        # 라벨 폭이 바뀔 때 줄바꿈 기준도 함께 갱신한다.
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


# 배경색과 둥근 모서리를 가진 공통 패널 클래스
class RoundedPanel(BoxLayout):
    background_color = ListProperty(PANEL)
    radius = NumericProperty(dp(8))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Kivy 기본 BoxLayout에는 배경이 없으므로 canvas에 직접 사각형을 그린다.
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
        # 패널 위치, 크기, 색상이 바뀔 때 배경 사각형도 함께 갱신한다.
        self._panel_color.rgba = self.background_color
        self._panel_rect.pos = self.pos
        self._panel_rect.size = self.size
        self._panel_rect.radius = [self.radius]


# 상세 팝업에서 장르를 작은 태그 형태로 표시하기 위한 함수
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


# 추가 장르 선택에 사용하는 토글 버튼 클래스
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
        # 선택된 장르는 빨간색, 선택되지 않은 장르는 회색으로 표시한다.
        self.text = self.genre
        if self.active:
            self.background_color = RED
        else:
            self.background_color = SOFT
        self._update_text_size()


# 1순위 장르, 추가 장르, 추천/초기화 버튼을 묶은 필터 UI 클래스
class FilterPanel(RoundedPanel):
    def __init__(self, genres, on_recommend, on_reset, **kwargs):
        super().__init__(
            orientation="vertical",
            spacing=dp(12),
            padding=dp(18),
            size_hint=(None, 1),
            width=dp(310),
            background_color=PANEL,
            radius=dp(8),
            **kwargs,
        )
        self.genres = genres
        self.secondary_toggles = {}

        self.add_widget(_label("취향 선택", font_size=20, bold=True))
        self.add_widget(_label("가장 중요한 장르를 먼저 고른 뒤, 함께 보고 싶은 분위기를 추가하세요.", color=MUTED))

        # 1순위 장르는 하나만 선택할 수 있도록 Spinner를 사용한다.
        self.primary_spinner = Spinner(
            text=DEFAULT_PRIMARY_GENRE,
            values=self.genres,
            option_cls=GenreSpinnerOption,
            dropdown_cls=GenreDropDown,
            font_name=FONT_NAME,
            font_size=sp(14),
            size_hint=(1, None),
            height=dp(44),
            background_normal="",
            background_down="",
            background_color=SOFT,
            color=WHITE,
        )
        self.add_widget(self.primary_spinner)
        self.add_widget(_label("추가 장르", color=MUTED, height=24))

        # 추가 장르는 여러 개 선택할 수 있으므로 스크롤 가능한 토글 목록으로 만든다.
        scroll = ScrollView(size_hint=(1, 1))
        genre_box = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        genre_box.bind(minimum_height=genre_box.setter("height"))

        for genre in self.genres:
            toggle = GenreToggle(genre)
            genre_box.add_widget(toggle)
            self.secondary_toggles[genre] = toggle

        scroll.add_widget(genre_box)
        self.add_widget(scroll)

        # 버튼은 외부에서 전달받은 추천 실행 함수와 초기화 함수를 연결한다.
        button_row = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint=(1, None), height=dp(48))
        button_row.add_widget(self._button("추천받기", on_recommend, background=RED))
        button_row.add_widget(self._button("초기화", on_reset, width=dp(86), background=SOFT))
        self.add_widget(button_row)

    @property
    def primary_genre(self):
        return self.primary_spinner.text

    def reset_selection(self):
        # 필터 초기화 시 1순위 장르와 모든 추가 장르 선택을 원래 상태로 되돌린다.
        self.primary_spinner.text = DEFAULT_PRIMARY_GENRE

        for toggle in self.secondary_toggles.values():
            toggle.state = "normal"

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


# 추천 결과 목록에서 한 작품을 카드 형태로 보여주는 클래스
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
            # 포스터 파일이 있으면 카드 상단에 이미지를 표시한다.
            self.add_widget(
                Image(
                    source=poster,
                    fit_mode="cover",
                    size_hint=(1, None),
                    height=dp(238),
                )
            )
        else:
            # 포스터가 없을 때도 카드 크기가 무너지지 않도록 대체 영역을 보여준다.
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
        # 카드를 클릭하면 해당 애니의 상세 팝업을 연다.
        self.open_detail(self.anime)


# Kivy 앱 전체를 구성하고 화면 전환/렌더링을 관리하는 메인 클래스
class AnimeRecommenderKivyApp(App):
    title = "ANIFLIX 애니 추천"

    def build(self):
        Window.clearcolor = BLACK
        Window.size = (1180, 760)
        self.genres = get_all_genres()

        # 전체 화면은 상단 헤더와 본문 영역으로 구성한다.
        root = BoxLayout(orientation="vertical", spacing=0)
        root.add_widget(self._create_header())

        content = BoxLayout(orientation="horizontal", spacing=dp(18), padding=dp(20))
        # 필터 UI는 FilterPanel 클래스로 분리하여 왼쪽 영역에 배치한다.
        self.filter_panel = FilterPanel(self.genres, self.show_recommendations, self.reset_selection)
        content.add_widget(self.filter_panel)

        # 오른쪽 영역은 기본 화면, 추천 결과, 상세 진입용 카드 목록을 표시한다.
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
        # 아직 추천 조건을 선택하지 않았을 때 보여주는 기본 인기 작품 화면
        self._render_hero(_featured_anime())
        popular = sorted(ANIME_LIST, key=lambda anime: anime["rating"], reverse=True)[:10]
        self._render_results("오늘의 인기 애니", "처음이라면 평점이 높은 작품부터 둘러보세요.", popular)

    def _render_hero(self, anime, primary_genre=None, secondary_genres=None):
        # 추천 결과의 대표 작품을 크게 보여주는 상단 영역
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
            copy.add_widget(_label(f"1순위 {primary_genre} · {genre_summary(secondary_genres)}", color=WHITE))

        hero.add_widget(copy)
        self.result_area.add_widget(hero)

    def _render_results(self, title, subtitle, anime_list):
        # 추천 결과나 인기 작품 목록을 스크롤 가능한 카드 그리드로 출력한다.
        result_scroll = ScrollView(size_hint=(1, 1))
        result_box = BoxLayout(orientation="vertical", spacing=dp(14), size_hint_y=None)
        result_box.bind(minimum_height=result_box.setter("height"))

        result_box.add_widget(_label(title, font_size=22, bold=True))
        result_box.add_widget(_label(subtitle, color=MUTED))

        if not anime_list:
            # 추천 결과가 비어 있을 때는 빈 화면 대신 안내 문구를 보여준다.
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
        # FilterPanel에서 선택한 값을 filtering.py에 넘겨 검증과 추천 요청을 처리한다.
        result = request_recommendations(self.filter_panel.primary_genre, self.filter_panel.secondary_toggles)

        if not result.is_valid:
            self._show_message(result.error_title, result.error_message)
            return

        primary_genre = result.request.primary_genre
        secondary_genres = result.request.secondary_genres
        recommendations = result.recommendations

        # 기존 기본 화면을 지우고 추천 결과 화면으로 다시 렌더링한다.
        self.result_area.clear_widgets()
        self._render_hero(recommendations[0] if recommendations else _featured_anime(), primary_genre, secondary_genres)
        self._render_results("추천 결과", f"1순위 {primary_genre} · {genre_summary(secondary_genres)}", recommendations)

    def reset_selection(self):
        # 필터와 결과 영역을 모두 초기 상태로 되돌린다.
        self.filter_panel.reset_selection()

        if hasattr(self, "result_area"):
            self.result_area.clear_widgets()
            self._render_default()

    def open_detail(self, anime):
        # 카드 클릭 시 작품 정보를 팝업으로 자세히 보여준다.
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
            # 상세 화면 왼쪽에는 작품 포스터를 크게 표시한다.
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
            # 추천 결과에서 열린 상세 화면이면 추천에 반영된 장르 정보도 함께 표시한다.
            secondary = genre_summary(anime.get("secondary_affinity", {}).keys())
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
