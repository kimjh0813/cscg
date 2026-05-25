from data import ANIME_LIST


def recommend_anime(selected_genres, limit=5):
    if not selected_genres:
        return []

    recommendations = []

    for anime in ANIME_LIST:
        matched_genres = set(anime["genres"]) & set(selected_genres)

        if matched_genres:
            score = len(matched_genres) * 10 + anime["rating"]
            recommendations.append(
                {
                    **anime,
                    "matched_genres": sorted(matched_genres),
                    "score": score,
                }
            )

    recommendations.sort(key=lambda item: item["score"], reverse=True)
    return recommendations[:limit]
