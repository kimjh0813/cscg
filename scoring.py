PRIMARY_GENRE_WEIGHT = 3.0
SECONDARY_GENRE_WEIGHT = 1.0
RATING_WEIGHT = 0.5


def calculate_recommendation_score(anime, primary_genre, secondary_genres):
    genre_affinity = anime.get("genre_affinity", {})
    secondary_genres = secondary_genres or []

    primary_score = genre_affinity.get(primary_genre, 0) * PRIMARY_GENRE_WEIGHT
    secondary_score = sum(
        genre_affinity.get(genre, 0) * SECONDARY_GENRE_WEIGHT
        for genre in secondary_genres
        if genre != primary_genre
    )
    rating_score = anime["rating"] * RATING_WEIGHT

    total_score = primary_score + secondary_score + rating_score

    return {
        "score": total_score,
        "primary_affinity": genre_affinity.get(primary_genre, 0),
        "secondary_affinity": {
            genre: genre_affinity.get(genre, 0)
            for genre in secondary_genres
            if genre != primary_genre and genre_affinity.get(genre, 0) > 0
        },
    }
