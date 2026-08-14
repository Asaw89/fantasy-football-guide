import os
from anthropic import Anthropic  # uses 2cents per pull
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment automatically


def get_player_news(name, team, position):
    """Search fantasy outlets and return a short, fantasy-focused summary."""
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

    text_parts = [block.text for block in response.content if block.type == "text"]
    return "\n".join(text_parts).strip()


def ask_question(question):
    """Answer an open fantasy football question in an energetic analyst style."""
    prompt = (
        f"You're a sharp, energetic fantasy football analyst with a lively "
        f"podcast-style voice — confident, fun, and opinionated, but grounded in "
        f"real reasoning. Answer this fantasy football question in 3-5 sentences "
        f"with a clear take. Search the web if you need current information.\n\n"
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
