from draft_board import build_board

board = build_board("pts_ppr", 10)
for p in board[:5]:
    print(
        f"{p['name']}: espn_rank={p.get('espn_rank')}, "
        f"consensus={p.get('consensus')}, disagreement={p.get('disagreement')}"
    )
