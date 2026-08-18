def grade_draft(my_roster, starters, bench_spots):
    """Grade a drafted roster on value, completeness, and balance."""
    if not my_roster:
        return None

    # --- 1. Total value: sum of VOR across the roster ---
    total_vor = sum(p.get("vor", 0) for p in my_roster)

    # --- 2. Completeness: did you fill every starting slot? ---
    from collections import Counter

    counts = Counter(p["position"] for p in my_roster)
    slots_filled = sum(min(counts.get(pos, 0), need) for pos, need in starters.items())
    slots_total = sum(starters.values())
    completeness = slots_filled / slots_total  # 0.0 to 1.0

    # --- 3. Balance: penalize missing positions ---
    missing_positions = [pos for pos in starters if counts.get(pos, 0) < starters[pos]]
    balance = 1.0 - (len(missing_positions) / len(starters))

    # --- 4. Efficiency: average VOR per pick (value density) ---
    avg_vor = total_vor / len(my_roster)

    # --- Combine into a 0-100 score ---
    # Weighted: value density 40%, completeness 35%, balance 25%
    value_score = min(avg_vor / 3, 1.0) * 40  # ~4 avg VOR = full marks
    complete_score = completeness * 35
    balance_score = balance * 25
    total_score = value_score + complete_score + balance_score

    # --- Convert to letter grade ---
    if total_score >= 90:
        letter = "A"
    elif total_score >= 80:
        letter = "B"
    elif total_score >= 70:
        letter = "C"
    elif total_score >= 60:
        letter = "D"
    else:
        letter = "F"

    return {
        "score": round(total_score),
        "letter": letter,
        "total_vor": round(total_vor, 1),
        "avg_vor": round(avg_vor, 1),
        "slots_filled": slots_filled,
        "slots_total": slots_total,
        "missing": missing_positions,
    }
