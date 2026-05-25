import tkinter as tk
from tkinter import messagebox, ttk

from data import get_all_genres
from recommender import recommend_anime


class AnimeRecommenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("애니 추천 프로그램")
        self.root.geometry("780x560")
        self.root.minsize(680, 500)

        self.genre_vars = {}

        self._configure_style()
        self._create_layout()

    def _configure_style(self):
        self.root.configure(bg="#f5f7fb")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Title.TLabel", font=("맑은 고딕", 20, "bold"), background="#f5f7fb", foreground="#1f2937")
        style.configure("Subtitle.TLabel", font=("맑은 고딕", 10), background="#f5f7fb", foreground="#4b5563")
        style.configure("Card.TFrame", background="#ffffff", relief="flat")
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
        genre_frame.rowconfigure(0, weight=1)
        genre_frame.columnconfigure(0, weight=1)

        genre_canvas = tk.Canvas(
            genre_frame,
            bg="#ffffff",
            highlightthickness=0,
            width=120,
        )
        genre_canvas.grid(row=0, column=0, sticky="nsew")

        genre_scrollbar = ttk.Scrollbar(genre_frame, orient="vertical", command=genre_canvas.yview)
        genre_scrollbar.grid(row=0, column=1, sticky="ns")
        genre_canvas.configure(yscrollcommand=genre_scrollbar.set)

        checkbox_frame = ttk.Frame(genre_canvas, style="Card.TFrame")
        canvas_window = genre_canvas.create_window((0, 0), window=checkbox_frame, anchor="nw")

        def update_scroll_region(event):
            genre_canvas.configure(scrollregion=genre_canvas.bbox("all"))

        def update_canvas_width(event):
            genre_canvas.itemconfigure(canvas_window, width=event.width)

        checkbox_frame.bind("<Configure>", update_scroll_region)
        genre_canvas.bind("<Configure>", update_canvas_width)

        for index, genre in enumerate(get_all_genres()):
            var = tk.BooleanVar()
            checkbox = ttk.Checkbutton(checkbox_frame, text=genre, variable=var, style="Genre.TCheckbutton")
            checkbox.grid(row=index, column=0, sticky="w", pady=3)
            self.genre_vars[genre] = var

        button_frame = ttk.Frame(genre_frame)
        button_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))

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

        self.result_text = tk.Text(
            result_frame,
            wrap="word",
            font=("맑은 고딕", 10),
            bg="#ffffff",
            fg="#111827",
            padx=12,
            pady=12,
            relief="solid",
            borderwidth=1,
        )
        self.result_text.grid(row=0, column=0, sticky="nsew")
        self.result_text.insert("1.0", "왼쪽에서 장르를 선택하고 추천받기 버튼을 눌러보세요.")
        self.result_text.configure(state="disabled")

        scrollbar = ttk.Scrollbar(result_frame, command=self.result_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.result_text.configure(yscrollcommand=scrollbar.set)

    def show_recommendations(self):
        selected_genres = [
            genre for genre, var in self.genre_vars.items()
            if var.get()
        ]

        if not selected_genres:
            messagebox.showwarning("장르 선택 필요", "추천받을 장르를 하나 이상 선택해주세요.")
            return

        recommendations = recommend_anime(selected_genres)
        result = self._format_recommendations(selected_genres, recommendations)

        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", result)
        self.result_text.configure(state="disabled")

    def _format_recommendations(self, selected_genres, recommendations):
        lines = [
            f"선택한 장르: {', '.join(selected_genres)}",
            "",
            "추천 애니 TOP 5",
            "-" * 34,
        ]

        for index, anime in enumerate(recommendations, start=1):
            lines.extend(
                [
                    f"{index}. {anime['title']} ({anime['year']})",
                    f"   평점: {anime['rating']}",
                    f"   장르: {', '.join(anime['genres'])}",
                    f"   선택 장르와 일치: {', '.join(anime['matched_genres'])}",
                    f"   소개: {anime['description']}",
                    "",
                ]
            )

        return "\n".join(lines)

    def reset_selection(self):
        for var in self.genre_vars.values():
            var.set(False)

        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", "왼쪽에서 장르를 선택하고 추천받기 버튼을 눌러보세요.")
        self.result_text.configure(state="disabled")
