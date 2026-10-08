import re

DEFAULT_KEYWORDS = {
    "Food": {"coffee", "cafe", "restaurant", "grocery", "food", "pizza", "starbucks"},
    "Transport": {"uber", "lyft", "fuel", "petrol", "metro", "train", "parking"},
    "Bills": {"electric", "internet", "phone", "utility", "rent", "insurance"},
    "Shopping": {"amazon", "store", "shop", "clothing", "walmart", "target"},
    "Entertainment": {"netflix", "spotify", "cinema", "movie", "game"},
    "Healthcare": {"pharmacy", "doctor", "hospital", "medical"},
    "Education": {"course", "tuition", "book", "university"},
}


def categorize(description: str, categories: list[dict[str, object]], rules: list[dict[str, object]]) -> dict[str, object]:
    text = description.lower()
    for rule in rules:
        if str(rule["keyword"]).lower() in text:
            return {"category_id": rule["category_id"], "category": rule["category_name"], "confidence": 1.0, "source": "merchant_rule"}
    candidates = {str(category["name"]): category for category in categories}
    best_name, best_score = "Other", 0
    for name, keywords in DEFAULT_KEYWORDS.items():
        if name not in candidates: continue
        score = sum(1 for keyword in keywords if re.search(rf"\b{re.escape(keyword)}\b", text))
        if score > best_score: best_name, best_score = name, score
    for name in candidates:
        if name.lower() in text and best_score == 0:
            best_name, best_score = name, 1
    confidence = min(0.95, 0.55 + (best_score * 0.15)) if best_score else 0.2
    category = candidates.get(best_name)
    return {"category_id": category["id"] if category else None, "category": best_name, "confidence": confidence, "source": "keyword_fallback"}
