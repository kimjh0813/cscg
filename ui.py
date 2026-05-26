import tkinter as tk
import subprocess
import tempfile
from pathlib import Path
from tkinter import messagebox, ttk

from data import get_all_genres
from recommender import recommend_anime


BASE_DIR = Path(__file__).resolve().parent
POSTER_CACHE_DIR = Path(tempfile.gettempdir()) / "anime_recommender_posters"


class AnimeRecommenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("애니 추천 프로그램")
        self.root.geometry("780x560")
        self.root.minsize(680, 500)

        self.primary_genre_var = tk.StringVar()
        self.genre_vars = {}
        self.poster_images = []

        self._configure_style()
        self._create_layout()

    def _configure_style(self):
        self.root.configure(bg="#f5f7fb")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Title.TLabel", font=("맑은 고딕", 20, "bold"), background="#f5f7fb", foreground="#1f2937")
        style.configure("Subtitle.TLabel", font=("맑은 고딕", 10), background="#f5f7fb", foreground="#4b5563")
        style.configure("Card.TFrame", background="#ffffff", relief="flat")
        style.configure("Result.TFrame", background="#ffffff")
        style.configure("ResultTitle.TLabel", font=("맑은 고딕", 12, "bold"), background="#ffffff", foreground="#111827")
        style.configure("ResultText.TLabel", font=("맑은 고딕", 10), background="#ffffff", foreground="#374151")
        style.configure("Genre.TCheckbutton", font=("맑은 고딕", 10), background="#ffffff", foreground="#1f2937")
        style.configure("Primary.TButton", font=("맑은 고딕", 11, "bold"), padding=(14, 8))
        style.configure("Secondary.TButton", font=("맑은 고딕", 10), padding=(10, 6))

    def _create_layout(self):
        main_frame = ttk.Frame(self.root, padding=24, style="Card.TFrame")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        title = ttk.Label(main_frame, text="애니 추천 프로그램", style="Title.TLabel")
        title.pack(anchor="w")

        subtitle = ttk.Label(
            main_frame,
            text="좋아하는 장르를 여러 개 선택하면 어울리는 애니를 추천합니다.",
            style="Subtitle.TLabel",
        )
        subtitle.pack(anchor="w", pady=(4, 18))

        content_frame = ttk.Frame(main_frame, style="Card.TFrame")
        content_frame.pack(fill="both", expand=True)
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=2)
        content_frame.rowconfigure(0, weight=1)

        self._create_genre_panel(content_frame)
        self._create_result_panel(content_frame)

    def _create_genre_panel(self, parent):
        genre_frame = ttk.LabelFrame(parent, text="장르 선택", padding=14)
        genre_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        genre_frame.rowconfigure(3, weight=1)
        genre_frame.columnconfigure(0, weight=1)

        genres = get_all_genres()

        primary_label = ttk.Label(genre_frame, text="1순위 장르", background="#ffffff")
        primary_label.grid(row=0, column=0, columnspan=2, sticky="w")

        primary_combo = ttk.Combobox(
            genre_frame,
            textvariable=self.primary_genre_var,
            values=genres,
            state="readonly",
        )
        primary_combo.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 14))

        secondary_label = ttk.Label(genre_frame, text="추가 장르", background="#ffffff")
        secondary_label.grid(row=2, column=0, columnspan=2, sticky="nw", pady=(0, 6))

        genre_canvas = tk.Canvas(
            genre_frame,
            bg="#ffffff",
            highlightthickness=0,
            width=120,
        )
        genre_canvas.grid(row=3, column=0, sticky="nsew")

        genre_scrollbar = ttk.Scrollbar(genre_frame, orient="vertical", command=genre_canvas.yview)
        genre_scrollbar.grid(row=3, column=1, sticky="ns")
        genre_canvas.configure(yscrollcommand=genre_scrollbar.set)

        checkbox_frame = ttk.Frame(genre_canvas, style="Card.TFrame")
        canvas_window = genre_canvas.create_window((0, 0), window=checkbox_frame, anchor="nw")

        def update_scroll_region(event):
            genre_canvas.configure(scrollregion=genre_canvas.bbox("all"))

        def update_canvas_width(event):
            genre_canvas.itemconfigure(canvas_window, width=event.width)

        checkbox_frame.bind("<Configure>", update_scroll_region)
        genre_canvas.bind("<Configure>", update_canvas_width)

        for index, genre in enumerate(genres):
            var = tk.BooleanVar()
            checkbox = ttk.Checkbutton(checkbox_frame, text=genre, variable=var, style="Genre.TCheckbutton")
            checkbox.grid(row=index, column=0, sticky="w", pady=3)
            self.genre_vars[genre] = var

        button_frame = ttk.Frame(genre_frame)
        button_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(12, 0))

        recommend_button = ttk.Button(
            button_frame,
            text="추천받기",
            command=self.show_recommendations,
            style="Primary.TButton",
        )
        recommend_button.pack(fill="x", pady=(0, 8))

        reset_button = ttk.Button(
            button_frame,
            text="초기화",
            command=self.reset_selection,
            style="Secondary.TButton",
        )
        reset_button.pack(fill="x")

    def _create_result_panel(self, parent):
        result_frame = ttk.LabelFrame(parent, text="추천 결과", padding=14)
        result_frame.grid(row=0, column=1, sticky="nsew")
        result_frame.rowconfigure(0, weight=1)
        result_frame.columnconfigure(0, weight=1)

        self.result_canvas = tk.Canvas(
            result_frame,
            bg="#ffffff",
            highlightthickness=0,
        )
        self.result_canvas.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.result_canvas.configure(yscrollcommand=scrollbar.set)

        self.result_container = ttk.Frame(self.result_canvas, style="Result.TFrame")
        container_window = self.result_canvas.create_window((0, 0), window=self.result_container, anchor="nw")

        def update_scroll_region(event):
            self.result_canvas.configure(scrollregion=self.result_canvas.bbox("all"))

        def update_container_width(event):
            self.result_canvas.itemconfigure(container_window, width=event.width)

        self.result_container.bind("<Configure>", update_scroll_region)
        self.result_canvas.bind("<Configure>", update_container_width)
        self._show_placeholder()

    def show_recommendations(self):
        primary_genre = self.primary_genre_var.get()
        secondary_genres = [
            genre for genre, var in self.genre_vars.items()
            if var.get() and genre != primary_genre
        ]

        if not primary_genre:
            messagebox.showwarning("1순위 장르 선택 필요", "가장 중요하게 볼 1순위 장르를 선택해주세요.")
            return

        recommendations = recommend_anime(primary_genre, secondary_genres)
        self._render_recommendations(primary_genre, secondary_genres, recommendations)

    def _clear_results(self):
        self.poster_images.clear()

        for widget in self.result_container.winfo_children():
            widget.destroy()

    def _show_placeholder(self):
        self._clear_results()
        label = ttk.Label(
            self.result_container,
            text="왼쪽에서 장르를 선택하고 추천받기 버튼을 눌러보세요.",
            style="ResultText.TLabel",
        )
        label.pack(anchor="w", padx=12, pady=12)

    def _render_recommendations(self, primary_genre, secondary_genres, recommendations):
        self._clear_results()

        summary = ttk.Label(
            self.result_container,
            text=f"1순위 장르: {primary_genre}\n추가 장르: {', '.join(secondary_genres) if secondary_genres else '없음'}",
            style="ResultText.TLabel",
        )
        summary.pack(anchor="w", fill="x", padx=12, pady=(8, 12))

        if not recommendations:
            empty_label = ttk.Label(
                self.result_container,
                text="조건에 맞는 추천 결과가 없습니다.",
                style="ResultText.TLabel",
            )
            empty_label.pack(anchor="w", padx=12, pady=12)
            return

        for index, anime in enumerate(recommendations, start=1):
            self._create_result_card(index, anime)

    def _create_result_card(self, index, anime):
        card = ttk.Frame(self.result_container, style="Result.TFrame", padding=10)
        card.pack(fill="x", padx=8, pady=(0, 10))
        card.columnconfigure(1, weight=1)

        poster_image = self._load_poster_image(anime.get("poster"))
        if poster_image:
            poster_label = ttk.Label(card, image=poster_image, background="#ffffff")
            poster_label.grid(row=0, column=0, rowspan=2, sticky="nw", padx=(0, 12))
            self.poster_images.append(poster_image)
        else:
            poster_placeholder = tk.Label(
                card,
                text="No Image",
                width=12,
                height=8,
                bg="#e5e7eb",
                fg="#6b7280",
            )
            poster_placeholder.grid(row=0, column=0, rowspan=2, sticky="nw", padx=(0, 12))

        title = ttk.Label(
            card,
            text=f"{index}. {anime['title']} ({anime['year']})",
            style="ResultTitle.TLabel",
        )
        title.grid(row=0, column=1, sticky="ew")

        secondary_matches = ", ".join(anime["secondary_affinity"].keys()) or "없음"
        detail = ttk.Label(
            card,
            text=(
                f"평점: {anime['rating']} | 추천 점수: {anime['score']:.2f}\n"
                f"장르: {', '.join(anime['genres'])}\n"
                f"1순위 장르 가까움: {anime['primary_affinity']:.2f} | 추가 장르 반영: {secondary_matches}\n"
                f"소개: {anime['description']}"
            ),
            style="ResultText.TLabel",
            wraplength=390,
            justify="left",
        )
        detail.grid(row=1, column=1, sticky="new", pady=(6, 0))

    def _load_poster_image(self, poster_path):
        image_path = self._get_displayable_poster_path(poster_path)

        if not image_path:
            return None

        try:
            image = tk.PhotoImage(file=image_path)
        except tk.TclError:
            return None

        width_scale = max(1, image.width() // 95)
        height_scale = max(1, image.height() // 135)
        return image.subsample(width_scale, height_scale)

    def _get_displayable_poster_path(self, poster_path):
        if not poster_path:
            return None

        path = BASE_DIR / poster_path

        if not path.exists():
            return None

        if path.suffix.lower() == ".png":
            return path

        POSTER_CACHE_DIR.mkdir(exist_ok=True)
        cache_path = POSTER_CACHE_DIR / path.with_suffix(".png").name

        if cache_path.exists() and cache_path.stat().st_mtime >= path.stat().st_mtime:
            return cache_path

        try:
            subprocess.run(
                ["sips", "-s", "format", "png", str(path), "--out", str(cache_path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            return None

        return cache_path

    def reset_selection(self):
        self.primary_genre_var.set("")

        for var in self.genre_vars.values():
            var.set(False)

        self._show_placeholder()
