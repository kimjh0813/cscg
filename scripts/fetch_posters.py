"""Jikan API로 애니 포스터를 다운로드합니다. (python3 scripts/fetch_posters.py)"""

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

# 프로젝트 루트 디렉토리와 포스터가 저장될 폴더 경로를 객체 지향적(Pathlib)으로 정의
ROOT = Path(__file__).resolve().parent.parent
POSTERS_DIR = ROOT / "assets" / "posters"

# 검색용 마스터 데이터 맵 (한국어 제목 : (API 검색어/MAL_ID, 저장할 파일명 슬러그))
ANIME_POSTERS = {
    "귀멸의 칼날": ("Kimetsu no Yaiba", "kimetsu_no_yaiba"),
    "주술회전": ("Jujutsu Kaisen", "jujutsu_kaisen"),
    "하이큐!!": ("Haikyuu!!", "haikyuu"),
    "스파이 패밀리": ("Spy x Family", "spy_x_family"),
    "너의 이름은.": ("Kimi no Na wa", "kimi_no_na_wa"),
    "바이올렛 에버가든": ("Violet Evergarden", "violet_evergarden"),
    "소드 아트 온라인": ("Sword Art Online", "sword_art_online"),
    "약속의 네버랜드": ("Yakusoku no Neverland", "neverland"),
    "데스노트": ("Death Note", "death_note"),  # [수정] "Death Death Note" 오타 에러 수정
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
    "그 비스크 돌은 사랑을 한다": ("My Dress-Up Darling", "sono_bisque_doll"),
    "강철의 연금술사": ("Fullmetal Alchemist: Brotherhood", "fma"),
    "나루토": ("Naruto", "naruto"),
    # 검색어 쿼리 시 동명 극장판이나 스핀오프가 먼저 잡히는 에러를 방지하기 위해, MyAnimeList 고유 ID(mal:21)를 직접 지정하여 족집게 호출
    "원피스": ("mal:21", "one_piece"),
    "헌터×헌터": ("Hunter x Hunter", "hunter_x_hunter"),
    "진격의 거인": ("Shingeki no Kyojin", "attack_on_titan"),
    "닥터 스톤": ("Dr. Stone", "dr_stone"),
}


def jikan_search(query: str):
    """Jikan API를 통해 애니메이션 메타데이터를 검색하는 함수"""
    # 쿼리가 'mal:'로 시작하는 경우 ID 단건 조회 API 엔드포인트 분기 처리
    if query.startswith("mal:"):
        mal_id = query.split(":", 1)[1]
        url = f"https://api.jikan.moe/v4/anime/{mal_id}"
    # 일반 문자열일 경우, 공백이나 특수문자를 URL Safe하게 인코딩(quote)하여 검색 API 호출 (결과는 상위 1개만 제한)
    else:
        url = f"https://api.jikan.moe/v4/anime?q={urllib.parse.quote(query)}&limit=1"

    # API 봇 차단을 우회하기 위해 HTTP 헤더에 커스텀 User-Agent를 삽입하여 리퀘스트 패킷 송신
    req = urllib.request.Request(url, headers={"User-Agent": "cscg-anime-recommender/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)

    # ID 검색일 경우 단일 데이터 객체('data')를 바로 반환
    if query.startswith("mal:"):
        return data.get("data")

    # 텍스트 검색일 경우 배열 형태의 결과 중 가장 검색 매칭 확률이 높은 첫 번째 요소([0])를 반환
    items = data.get("data") or []
    return items[0] if items else None


def download_image(url: str, dest: Path) -> None:
    """전달받은 이미지 URL 주소에서 바이너리 데이터를 읽어와 로컬 파일로 저장하는 함수"""
    req = urllib.request.Request(url, headers={"User-Agent": "cscg-anime-recommender/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        # 별도의 파일 스트림 오픈 없이 path 객체에 직접 바이트 배열을 Write하는 최적화 기법 사용
        dest.write_bytes(resp.read())


def main():
    # 포스터 저장 폴더가 없을 경우 부모 폴더까지 자동으로 일괄 생성(mkdir)
    POSTERS_DIR.mkdir(parents=True, exist_ok=True)
    results = {}

    for title, (query, slug) in ANIME_POSTERS.items():
        dest = POSTERS_DIR / f"{slug}.jpg"
        
        # 성능 최적화(Caching): 이미 파일이 존재하고 파일 크기가 정상(1KB 이상)인 경우, 중복 API 요청을 생략(skip)하여 실행 속도 향상
        if dest.exists() and dest.stat().st_size > 1000:
            results[title] = f"assets/posters/{slug}.jpg"
            print(f"[skip] {title}")
            continue

        # 네트워크 통신 장애나 API 스로틀링으로 인해 스크립트 전체가 뻗는 것을 방지하는 예외 처리 루프
        try:
            anime = jikan_search(query)
            # Jikan 무료 API의 Rate Limit(초당 요청 제한) 정책을 준수하여 429 Too Many Requests 에러를 차단하기 위한 0.4초 딜레이(Sleep) 셋업
            time.sleep(0.4)
            if not anime:
                print(f"[fail] {title}: 검색 결과 없음 ({query})")
                continue

            # 고화질 이미지(large_image_url)가 있으면 우선 선택하고, 없으면 일반 이미지 URL을 폴백(Fallback) 데이터로 채택
            image_url = anime["images"]["jpg"].get("large_image_url") or anime["images"]["jpg"]["image_url"]
            download_image(image_url, dest)
            results[title] = f"assets/posters/{slug}.jpg"
            print(f"[ok]   {title} -> {dest.name} ({anime['title']})")
            
            # 다운로드 완료 후 다음 루프 진입 전 통신 안정성을 위해 추가 딜레이 부여
            time.sleep(0.4)
        except Exception as exc:
            # 특정 작품 다운로드 중 에러가 나더라도 트래킹 로그만 남기고 다음 작품으로 루프를 계속 진행(방어적 코딩)
            print(f"[fail] {title}: {exc}")

    # 다운로드가 정상 완료된 작품들의 로컬 상대 경로 목록을 최종 로그 포맷으로 덤프
    print("\n--- poster paths ---")
    for title, path in results.items():
        print(f"{title!r}: {path!r}")


if __name__ == "__main__":
    main()