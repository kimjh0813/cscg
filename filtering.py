from dataclasses import dataclass
from recommender import recommend_anime

# 1순위 장르를 아직 고르지 않았을 때 Spinner에 표시되는 기본 문구
DEFAULT_PRIMARY_GENRE = "1순위 장르"

# 1순위 장르를 선택하지 않고 추천받기를 눌렀을 때 보여줄 안내 문구
PRIMARY_GENRE_REQUIRED_TITLE = "1순위 장르 선택 필요"
PRIMARY_GENRE_REQUIRED_MESSAGE = "가장 중요하게 볼 1순위 장르를 선택해주세요."


@dataclass(frozen=True)
class RecommendationRequest:
    # 추천 알고리즘에 전달할 사용자 선택 조건
    primary_genre: str
    secondary_genres: list[str]


@dataclass(frozen=True)
class RecommendationResult:
    # 추천 요청 처리 결과를 UI에서 사용하기 쉽게 묶어 반환한다.
    request: RecommendationRequest
    recommendations: list[dict]
    error_title: str | None = None
    error_message: str | None = None

    @property
    def is_valid(self):
        # 오류 메시지가 없으면 정상 추천 요청으로 판단한다.
        return self.error_message is None


def genre_summary(genres):
    # 추가 장르 목록을 화면 표시용 문자열로 변환한다.
    return ", ".join(genres) if genres else "추가 장르 없음"


def is_primary_genre_selected(primary_genre):
    # 기본 문구가 그대로 남아 있으면 아직 1순위 장르를 선택하지 않은 상태이다.
    return bool(primary_genre and primary_genre != DEFAULT_PRIMARY_GENRE)


def collect_secondary_genres(primary_genre, secondary_toggles):
    # 선택된 추가 장르만 모으되, 1순위 장르와 중복되는 장르는 제외한다.
    return [
        genre
        for genre, toggle in secondary_toggles.items()
        if toggle.active and genre != primary_genre
    ]


def create_recommendation_request(primary_genre, secondary_toggles):
    # UI에서 선택한 값을 추천 알고리즘이 사용할 요청 객체로 정리한다.
    secondary_genres = collect_secondary_genres(primary_genre, secondary_toggles)
    return RecommendationRequest(
        primary_genre=primary_genre,
        secondary_genres=secondary_genres,
    )


def request_recommendations(primary_genre, secondary_toggles):
    # 추천 실행 전 1순위 장르가 선택되었는지 먼저 검사한다.
    if not is_primary_genre_selected(primary_genre):
        return RecommendationResult(
            request=RecommendationRequest(primary_genre="", secondary_genres=[]),
            recommendations=[],
            error_title=PRIMARY_GENRE_REQUIRED_TITLE,
            error_message=PRIMARY_GENRE_REQUIRED_MESSAGE,
        )

    # 검증을 통과하면 추천 요청 객체를 만들고 실제 추천 함수에 전달한다.
    request = create_recommendation_request(primary_genre, secondary_toggles)
    recommendations = recommend_anime(request.primary_genre, request.secondary_genres)

    return RecommendationResult(
        request=request,
        recommendations=recommendations,
    )
