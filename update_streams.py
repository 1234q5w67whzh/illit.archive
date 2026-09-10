import json
import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup


STREAMS_FILE = "streams.json"

KWORB_URL = (
    "https://www.kworb.net/spotify/artist/"
    "36cgvBn0aadzOijnjjwqMN_songs.html"
)


def normalize(text):
    text = text.lower().strip()
    text = text.replace("’", "'")
    text = re.sub(r"\s+", " ", text)
    return text


def get_kworb_data():
    response = requests.get(
        KWORB_URL,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table")

    if table is None:
        raise RuntimeError("Tabela do Kworb não foi encontrada.")

    data = {}

    for row in table.find_all("tr"):
        cells = row.find_all("td")

        if len(cells) < 3:
            continue

        title = cells[0].get_text(" ", strip=True)
        streams_text = cells[1].get_text(" ", strip=True)
        daily_text = cells[2].get_text(" ", strip=True)

        if not title:
            continue

        title = title.lstrip("*").strip()

        streams_text = streams_text.replace(",", "").strip()
        daily_text = daily_text.replace(",", "").strip()

        if not streams_text.isdigit():
            continue

        if not daily_text.isdigit():
            continue

        key = normalize(title)

        data[key] = {
            "total": int(streams_text),
            "daily": int(daily_text)
        }

    if not data:
        raise RuntimeError("Nenhuma música foi encontrada no Kworb.")

    return data


def main():
    with open(STREAMS_FILE, "r", encoding="utf-8") as file:
        streams = json.load(file)

    spotify_data = get_kworb_data()

    if "spotify" not in streams:
        streams["spotify"] = {}

    if "total" not in streams["spotify"]:
        streams["spotify"]["total"] = {}

    if "daily" not in streams["spotify"]:
        streams["spotify"]["daily"] = {}

    updated = 0

    for song, values in spotify_data.items():
        streams["spotify"]["total"][song] = values["total"]
        streams["spotify"]["daily"][song] = values["daily"]
        updated += 1

    streams["updated_at"] = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d")

    with open(STREAMS_FILE, "w", encoding="utf-8") as file:
        json.dump(
            streams,
            file,
            ensure_ascii=False,
            indent=2
        )
        file.write("\n")

    print(f"Spotify atualizado: {updated} músicas.")
    print(f"Data: {streams['updated_at']}")


if __name__ == "__main__":
    main()
