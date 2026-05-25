ANIME_LIST = [
    {
        "title": "귀멸의 칼날",
        "genres": ["액션", "판타지", "모험"],
        "year": 2019,
        "rating": 4.7,
        "description": "가족을 잃은 소년이 동생을 구하기 위해 귀살대가 되어 싸우는 이야기.",
    },
    {
        "title": "주술회전",
        "genres": ["액션", "판타지", "학원"],
        "year": 2020,
        "rating": 4.6,
        "description": "저주와 싸우는 주술사들의 빠른 전개와 화려한 전투가 매력인 작품.",
    },
    {
        "title": "하이큐!!",
        "genres": ["스포츠", "성장", "학원"],
        "year": 2014,
        "rating": 4.8,
        "description": "작은 키의 소년이 배구를 통해 팀워크와 성장을 배워가는 스포츠 애니.",
    },
    {
        "title": "스파이 패밀리",
        "genres": ["코미디", "일상", "액션"],
        "year": 2022,
        "rating": 4.5,
        "description": "스파이, 암살자, 초능력자가 가짜 가족이 되며 벌어지는 따뜻한 코미디.",
    },
    {
        "title": "너의 이름은.",
        "genres": ["로맨스", "판타지", "드라마"],
        "year": 2016,
        "rating": 4.8,
        "description": "서로 몸이 바뀌는 두 학생이 시간과 운명을 넘어 이어지는 극장판 애니.",
    },
    {
        "title": "바이올렛 에버가든",
        "genres": ["드라마", "감동", "일상"],
        "year": 2018,
        "rating": 4.7,
        "description": "감정을 몰랐던 소녀가 편지를 대필하며 사랑의 의미를 배워가는 작품.",
    },
    {
        "title": "소드 아트 온라인",
        "genres": ["판타지", "액션", "모험"],
        "year": 2012,
        "rating": 4.2,
        "description": "가상현실 게임에 갇힌 플레이어들이 생존을 위해 싸우는 이야기.",
    },
    {
        "title": "약속의 네버랜드",
        "genres": ["스릴러", "미스터리", "드라마"],
        "year": 2019,
        "rating": 4.4,
        "description": "고아원에 숨겨진 진실을 알게 된 아이들이 탈출을 계획하는 긴장감 있는 작품.",
    },
    {
        "title": "데스노트",
        "genres": ["스릴러", "미스터리", "두뇌전"],
        "year": 2006,
        "rating": 4.8,
        "description": "이름을 쓰면 사람이 죽는 노트를 둘러싼 천재들의 심리전.",
    },
    {
        "title": "케이온!",
        "genres": ["일상", "코미디", "음악"],
        "year": 2009,
        "rating": 4.3,
        "description": "방과 후 밴드부 학생들의 귀엽고 편안한 일상을 그린 음악 애니.",
    },
    {
        "title": "4월은 너의 거짓말",
        "genres": ["음악", "로맨스", "드라마"],
        "year": 2014,
        "rating": 4.7,
        "description": "피아노를 치지 못하게 된 소년이 바이올린 소녀를 만나 다시 음악과 마주한다.",
    },
    {
        "title": "원펀맨",
        "genres": ["액션", "코미디", "히어로"],
        "year": 2015,
        "rating": 4.6,
        "description": "너무 강해서 모든 적을 한 방에 쓰러뜨리는 히어로의 유쾌한 이야기.",
    },
    {
        "title": "나의 히어로 아카데미아",
        "genres": ["히어로", "액션", "학원"],
        "year": 2016,
        "rating": 4.4,
        "description": "개성이 없는 소년이 최고의 히어로를 꿈꾸며 성장하는 학원 액션물.",
    },
    {
        "title": "빙과",
        "genres": ["미스터리", "일상", "학원"],
        "year": 2012,
        "rating": 4.4,
        "description": "고전부 학생들이 일상 속 작은 수수께끼를 풀어가는 잔잔한 미스터리.",
    },
    {
        "title": "슬램덩크",
        "genres": ["스포츠", "성장", "코미디"],
        "year": 1993,
        "rating": 4.9,
        "description": "농구 초보 강백호가 팀원들과 함께 성장하는 전설적인 스포츠 애니.",
    },
]


def get_all_genres():
    genres = set()

    for anime in ANIME_LIST:
        genres.update(anime["genres"])

    return sorted(genres)
