import os
from anthropic import Anthropic  # uses 2cents per pull
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment automatically


def get_player_news(name, team, position):
    """Search fantasy outlets and return a summary plus its source links."""
    prompt = (
        f"Search for the latest fantasy football news on {name}, "
        f"{position} for {team}. In 2-3 sentences, summarize the most important "
        f"recent updates that matter for fantasy: injuries, depth-chart or role "
        f"changes, or usage trends. If there's no notable recent news, say so "
        f"briefly. Finish with a one-line bold fantasy takeaway."
    )

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
    )

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
):
    """Answer a fantasy question with real draft-strategy reasoning."""
    from collections import Counter

    # Summarize roster construction by position
    roster_text = "nobody yet"
    pos_counts = {}
    if my_roster:
        pos_counts = dict(Counter(p["position"] for p in my_roster))
        roster_text = ", ".join(f"{p['name']} ({p['position']})" for p in my_roster)

    construction = ", ".join(f"{n} {pos}" for pos, n in pos_counts.items()) or "empty"

    where = ""
    if round_num and pick_in_round:
        where = f"You are at Round {round_num}, Pick {pick_in_round}. "

    picks_gone = f"{len(taken)} players have been drafted overall. " if taken else ""

    prompt = (
        f"You're a sharp, energetic fantasy draft analyst — confident, opinionated, "
        f"but grounded in real strategy. Setting: a {league_size}-team {scoring} draft.\n\n"
        f"DRAFT SITUATION:\n"
        f"- {where}{picks_gone}\n"
        f"- The person's roster so far: {roster_text}\n"
        f"- Positional construction: {construction}\n\n"
        f"Use real draft-strategy frameworks in your reasoning and name them when "
        f"relevant: Zero RB (load WRs early, running backs late), Hero RB (one elite "
        f"RB then hammer WR), Robust RB (RBs early), late-round QB, and streaming/"
        f"early TE approaches. Consider positional scarcity, roster balance, what's "
        f"likely to fall to their next pick, and value at {scoring} scoring. "
        f"Given their current construction and draft position, tell them which "
        f"position to prioritize NOW and why — with a clear, decisive take. "
        f"If they should wait on a position (like QB or TE), say so and explain. "
        f"Answer in 4-6 sentences. Search the web only if you need current player info.\n\n"
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
    """Top stories — general if no roster, personalized to your players if you have one."""
    if my_players:
        # Personalized: news about the user's rostered players
        names = ", ".join(my_players[:15])  # cap the list length
        prompt = (
            f"Search for the latest fantasy football news specifically about these "
            f"players on my roster: {names}. Give me the 5 most important updates "
            f"among THESE players — injuries, role or usage changes, notable news. "
            f"For each, respond with ONLY:\nPLAYER | headline\n"
            f"(headline under 10 words). One per line, no numbering, no other text. "
            f"If a player has no notable recent news, skip them."
        )
    else:
        # General: top NFL/fantasy stories
        prompt = (
            "Search for the most important fantasy football news right now. "
            "Give me the top 5 stories that matter most for fantasy managers — "
            "injuries, role changes, big news. For each, respond with ONLY:\n"
            "PLAYER | headline\n"
            "(headline under 10 words). One per line, no numbering, no other text."
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


if __name__ == "__main__":
    print(get_player_news("Christian McCaffrey", "SF", "RB"))
