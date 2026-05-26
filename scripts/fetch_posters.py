"""Jikan API로 애니 포스터를 다운로드합니다. (python3 scripts/fetch_posters.py)"""

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTERS_DIR = ROOT / "assets" / "posters"

ANIME_POSTERS = {
    "귀멸의 칼날": ("Kimetsu no Yaiba", "kimetsu_no_yaiba"),
    "주술회전": ("Jujutsu Kaisen", "jujutsu_kaisen"),
    "하이큐!!": ("Haikyuu!!", "haikyuu"),
    "스파이 패밀리": ("Spy x Family", "spy_x_family"),
    "너의 이름은.": ("Kimi no Na wa", "kimi_no_na_wa"),
    "바이올렛 에버가든": ("Violet Evergarden", "violet_evergarden"),
    "소드 아트 온라인": ("Sword Art Online", "sword_art_online"),
    "약속의 네버랜드": ("Yakusoku no Neverland", "neverland"),
    "데스노트": ("Death Note", "death_note"),
    "케이온!": ("K-On!", "k_on"),
    "4월은 너의 거짓말": ("Shigatsu wa Kimi no Uso", "your_lie_in_april"),
    "원펀맨": ("One Punch Man", "one_punch_man"),
    "나의 히어로 아카데미아": ("Boku no Hero Academia", "mha"),
    "빙과": ("Hyouka", "hyouka"),
    "슬램덩크": ("Slam Dunk", "slam_dunk"),
    "체인소 맨": ("Chainsaw Man", "chainsaw_man"),
    "최애의 아이": ("Oshi no Ko", "oshi_no_ko"),
    "장송의 프리렌": ("Sousou no Frieren", "frieren"),
    "괴수 8호": ("Kaiju No. 8", "kaiju_no_8"),
    "블리치": ("Bleach", "bleach"),
    "도쿄 리벤져스": ("Tokyo Revengers", "tokyo_revengers"),
    "그 비스크 돌은 사랑을 한다": ("Bocchi the Rock!", "bocchi_the_rock"),
    "강철의 연금술사": ("Fullmetal Alchemist: Brotherhood", "fma"),
    "나루토": ("Naruto", "naruto"),
    "원피스": ("mal:21", "one_piece"),  # TV 본편 (검색 시 극장판이 잡히는 경우 방지)
    "헌터×헌터": ("Hunter x Hunter", "hunter_x_hunter"),
    "진격의 거인": ("Shingeki no Kyojin", "attack_on_titan"),
    "닥터 스톤": ("Dr. Stone", "dr_stone"),
}


def jikan_search(query: str):
    if query.startswith("mal:"):
        mal_id = query.split(":", 1)[1]
        url = f"https://api.jikan.moe/v4/anime/{mal_id}"
    else:
        url = f"https://api.jikan.moe/v4/anime?q={urllib.parse.quote(query)}&limit=1"

    req = urllib.request.Request(url, headers={"User-Agent": "cscg-anime-recommender/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)

    if query.startswith("mal:"):
        return data.get("data")

    items = data.get("data") or []
    return items[0] if items else None


def download_image(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "cscg-anime-recommender/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        dest.write_bytes(resp.read())


def main():
    POSTERS_DIR.mkdir(parents=True, exist_ok=True)
    results = {}

    for title, (query, slug) in ANIME_POSTERS.items():
        dest = POSTERS_DIR / f"{slug}.jpg"
        if dest.exists() and dest.stat().st_size > 1000:
            results[title] = f"assets/posters/{slug}.jpg"
            print(f"[skip] {title}")
            continue

        try:
            anime = jikan_search(query)
            time.sleep(0.4)
            if not anime:
                print(f"[fail] {title}: 검색 결과 없음 ({query})")
                continue

            image_url = anime["images"]["jpg"].get("large_image_url") or anime["images"]["jpg"]["image_url"]
            download_image(image_url, dest)
            results[title] = f"assets/posters/{slug}.jpg"
            print(f"[ok]   {title} -> {dest.name} ({anime['title']})")
            time.sleep(0.4)
        except Exception as exc:
            print(f"[fail] {title}: {exc}")

    print("\n--- poster paths ---")
    for title, path in results.items():
        print(f"{title!r}: {path!r}")


if __name__ == "__main__":
    main()
