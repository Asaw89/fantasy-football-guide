import os
from anthropic import Anthropic  # uses 2cents per pull
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment automatically


def get_player_news(name, team, position):
    """Search for current, in-season fantasy news on a player."""
    prompt = (
        f"Search for the latest fantasy football news on {name}, "
        f"{position} for {team}, RIGHT NOW during the season. In 2-3 sentences, "
        f"summarize the most important CURRENT updates for fantasy managers this week: "
        f"injury status, whether they're playing this week, this week's matchup, "
        f"recent usage or role changes, and start/sit outlook. Focus on what matters "
        f"THIS WEEK, not season-long or draft outlook. Finish with a one-line bold "
        f"start/sit or waiver takeaway."
    )

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
    )

    text_parts = [block.text for block in response.content if block.type == "text"]
    summary = "\n".join(text_parts).strip()

    sources = {}
    for block in response.content:
        if block.type == "text" and getattr(block, "citations", None):
            for cite in block.citations:
                url = getattr(cite, "url", None)
                title = getattr(cite, "title", None) or url
                if url:
                    sources[url] = title

    return {"summary": summary, "sources": sources}

    # Pull the summary text
    text_parts = [block.text for block in response.content if block.type == "text"]
    summary = "\n".join(text_parts).strip()

    # Pull the source links from citations on the text blocks
    sources = {}
    for block in response.content:
        if block.type == "text" and getattr(block, "citations", None):
            for cite in block.citations:
                url = getattr(cite, "url", None)
                title = getattr(cite, "title", None) or url
                if url:
                    sources[url] = title  # dict dedupes repeated URLs

    return {"summary": summary, "sources": sources}


def ask_question(
    question,
    league_size=10,
    scoring="PPR",
    my_roster=None,
    taken=None,
    round_num=None,
    pick_in_round=None,
    mode="Draft",
):
    """Answer a fantasy question — draft strategy or in-season management
    depending on mode."""
    from collections import Counter

    roster_text = "nobody yet"
    pos_counts = {}
    if my_roster:
        pos_counts = dict(Counter(p["position"] for p in my_roster))
        roster_text = ", ".join(f"{p['name']} ({p['position']})" for p in my_roster)
    construction = ", ".join(f"{n} {pos}" for pos, n in pos_counts.items()) or "empty"

    if mode == "In-Season":
        prompt = (
            "You're a sharp, energetic fantasy football analyst helping someone manage "
            "their team DURING the season — confident, opinionated, grounded in real "
            f"reasoning. Setting: a {league_size}-team {scoring} league.\n\n"
            f"Their current roster: {roster_text}\n"
            f"Positional makeup: {construction}\n\n"
            "Give in-season management advice: start/sit calls, waiver-wire targets, "
            "trade ideas, matchup exploitation, and roster streaming. Consider weekly "
            "matchups, injuries, and rest-of-season value. Be decisive and specific to "
            "their roster. Answer in 4-6 sentences. Search the web if you need current "
            "player news, injuries, or matchup info.\n\n"
            f"Question: {question}"
        )
    else:  # Draft mode
        where = ""
        if round_num and pick_in_round:
            where = f"They're at Round {round_num}, Pick {pick_in_round}. "
        picks_gone = f"{len(taken)} players drafted overall. " if taken else ""
        prompt = (
            "You're a sharp, energetic fantasy draft analyst — confident, opinionated, "
            f"grounded in real strategy. Setting: a {league_size}-team {scoring} draft.\n\n"
            f"DRAFT SITUATION:\n- {where}{picks_gone}\n"
            f"- Their roster so far: {roster_text}\n"
            f"- Positional construction: {construction}\n\n"
            "Use real draft-strategy frameworks and name them when relevant: Zero RB, "
            "Hero RB, Robust RB, late-round QB, streaming/early TE. Consider positional "
            "scarcity, roster balance, and value. Tell them which position to prioritize "
            "and why, with a decisive take. Answer in 4-6 sentences. Search the web only "
            "if you need current player info.\n\n"
            f"Question: {question}"
        )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
    )
    text_parts = [block.text for block in response.content if block.type == "text"]
    return "\n".join(text_parts).strip()


def get_top_stories(my_players=None):
    """Top fantasy news — in-season focused (injuries, starts, waiver-relevant)."""
    if my_players:
        names = ", ".join(my_players[:15])
        prompt = (
            f"Search for the latest fantasy football news this week about these players "
            f"on my roster: {names}. Focus on CURRENT, in-season updates — injuries, "
            f"this week's status, snap/target trends, or role changes. Give the 5 most "
            f"important. For each, respond with ONLY:\nPLAYER | headline\n"
            f"(headline under 10 words). One per line, no numbering. Skip players with no news."
        )
    else:
        prompt = (
            "Search for the most important fantasy football news RIGHT NOW, in-season. "
            "Focus on current-week developments: injuries, players who are in/out this "
            "week, breakout performances, and waiver-wire risers. Give the top 5 stories "
            "that matter most to fantasy managers this week. For each, respond with ONLY:\n"
            "PLAYER | headline\n(headline under 10 words). One per line, no numbering, no other text."
        )

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
    )
    text = "\n".join(b.text for b in response.content if b.type == "text").strip()

    stories = []
    for line in text.split("\n"):
        if "|" in line:
            name, headline = line.split("|", 1)
            stories.append({"player": name.strip(), "headline": headline.strip()})
    return stories

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
    )
    text = "\n".join(b.text for b in response.content if b.type == "text").strip()

    stories = []
    for line in text.split("\n"):
        if "|" in line:
            name, headline = line.split("|", 1)
            stories.append({"player": name.strip(), "headline": headline.strip()})
    return stories


def matchup_preview(team_a_name, team_a_players, team_b_name, team_b_players):
    """Generate a WWE-style hype preview of two fantasy teams facing off."""

    def summarize(name, players):
        starters = [p for p in players if p.get("slot") not in ("BE", "IR", "")]
        if not starters:
            starters = players
        ranked = sorted(starters, key=lambda p: p.get("proj", 0), reverse=True)
        total = round(sum(p.get("proj", 0) for p in starters), 1)  # team total
        stars = ranked[:3]
        # Only flag weak spots among skill positions — D/ST and K always project
        # low and shouldn't be judged as "weak" by raw projection
        weak = [
            p
            for p in ranked
            if p["position"] not in ("D/ST", "K", "DEF")
            and (p.get("proj", 0) < 6 or p.get("status", "ACTIVE") != "ACTIVE")
        ]
        star_txt = ", ".join(
            f"{p['name']} ({p['position']}, proj {p.get('proj', 0)})" for p in stars
        )
        weak_txt = (
            ", ".join(f"{p['name']} ({p['position']})" for p in weak[:3])
            or "no glaring weaknesses"
        )
        return f"{name} (projected total {total}) — Superstars: {star_txt}. Vulnerabilities: {weak_txt}."

    a_summary = summarize(team_a_name, team_a_players)
    b_summary = summarize(team_b_name, team_b_players)

    prompt = (
        "You're a WWE ring announcer hyping a championship showdown between two fantasy "
        "football teams. Write a short, theatrical, over-the-top preview (4-6 sentences). "
        "Use the REAL players, projections, and TEAM TOTALS given — name the superstars, "
        "hype their matchup, and call out each team's weakness dramatically. When you "
        "predict a winner, base the margin on the actual projected totals given (don't "
        "invent a different margin). Bombastic wrestling-promo energy, grounded in these facts:\n\n"
        f"TEAM A — {a_summary}\n"
        f"TEAM B — {b_summary}\n\n"
        "Make it fun and specific. End with a dramatic prediction using the real projected margin."
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return "\n".join(b.text for b in response.content if b.type == "text").strip()


if __name__ == "__main__":
    print(get_player_news("Christian McCaffrey", "SF", "RB"))
