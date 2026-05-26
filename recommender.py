from data import ANIME_LIST
from scoring import calculate_recommendation_score


def recommend_anime(primary_genre, secondary_genres=None, limit=5):
    if not primary_genre:
        return []

    secondary_genres = secondary_genres or []
    recommendations = []

    for anime in ANIME_LIST:
        score_info = calculate_recommendation_score(anime, primary_genre, secondary_genres)

        if score_info["primary_affinity"] > 0 or score_info["secondary_affinity"]:
            recommendations.append(
                {
                    **anime,
                    **score_info,
                }
            )

    recommendations.sort(key=lambda item: item["score"], reverse=True)
    return recommendations[:limit]
