import pdfplumber
import re
import json
import sys

record_re = re.compile(
    r"(\d+)\.\s*\(([A-Z]+)(\d+)\)\s+(.+?),\s*([A-Z]{2,3})\s+\$(\d+)\s+(\d+)"
)


def extract(pdf_path):
    rows = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.split("\n"):
                for m in record_re.finditer(line):
                    overall = int(m.group(1))
                    if overall in rows:
                        continue
                    rows[overall] = {
                        "espn_rank": overall,
                        "position": m.group(2),
                        "pos_rank": int(m.group(3)),
                        "name": m.group(4).strip(),
                        "team": m.group(5),
                    }
    return [rows[k] for k in sorted(rows)]


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "NFL26_CS_PPR300.pdf"
    players = extract(path)
    print(
        f"Extracted {len(players)} players (ranks {players[0]['espn_rank']}-{players[-1]['espn_rank']})"
    )
    with open("src/espn_rankings.json", "w") as f:
        json.dump(players, f, indent=2)
    print("Saved src/espn_rankings.json")
