from draft_board import build_board

board = build_board("pts_ppr", 10)
with_adp = [p for p in board if p.get("adp")]
print(f"Players with ADP: {len(with_adp)} / {len(board)}")
for p in board[:8]:
    print(
        f"  {p['name']}: vor={p.get('vor')}, adp={p.get('adp')}, sleeper_rank={p.get('sleeper_rank')}"
    )
