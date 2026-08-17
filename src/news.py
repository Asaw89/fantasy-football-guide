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


def ask_question(question, league_size=10, scoring="PPR", my_roster=None, taken=None):
    """Answer a fantasy question, aware of the user's draft situation."""
    roster_text = "nobody yet"
    if my_roster:
        roster_text = ", ".join(f"{p['name']} ({p['position']})" for p in my_roster)

    taken_text = ""
    if taken:
        # Just the count and a sample — the full list can be long
        taken_text = f" So far {len(taken)} players have been drafted overall. "

    prompt = (
        f"You're a sharp, energetic fantasy football analyst with a lively "
        f"podcast-style voice — confident, fun, opinionated, but grounded in real "
        f"reasoning. The person is drafting in a {league_size}-team {scoring} league. "
        f"Their current roster is: {roster_text}.{taken_text}"
        f"Give advice tailored to their roster and format — what positions they still "
        f"need, who to target. Answer in 3-5 sentences with a clear take. "
        f"Search the web if you need current information.\n\n"
        f"Question: {question}"
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
    )
    text_parts = [block.text for block in response.content if block.type == "text"]
    return "\n".join(text_parts).strip()


if __name__ == "__main__":
    print(get_player_news("Christian McCaffrey", "SF", "RB"))
