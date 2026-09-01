from bs4 import BeautifulSoup as bs
import requests
import re
import json

# URL of the webpage to scrape
URL = "https://www.womansday.com/relationships/dating-marriage/a41055149/best-pickup-lines/"

# Request and parse the webpage
page = requests.get(URL)
page.encoding = "utf-8"
soup = bs(page.text, "html.parser")

# Find all category headings
titles = soup.find_all("h2", class_="body-h2 css-1pdbjaa emevuu60")

# Store pickup lines by category
pickup_data = {}

for title in titles:

    title_text = title.get_text(strip=True)
    print("\n" + title_text)

    # Find the list following each category heading
    ul = title.find_next("ul")

    if ul:
        lines = ul.find_all("li")
        pickup_lines = []

        for line in lines:

            # Remove image captions and clean the extracted text
            for caption in line.find_all("figcaption"):
                caption.decompose()

            text = line.get_text(" ", strip=True)

            # Clean spacing around punctuation and brackets
            text = re.sub(r"\s+([,.!?;:])", r"\1", text)
            text = re.sub(r"([\[(])\s+", r"\1", text)
            text = re.sub(r"\s+([\])])", r"\1", text)

            # Remove related-content text
            text = re.split(r"RELATED\s*:", text, maxsplit=1)[0]

            text = text.strip()

            # Add to list if text is not empty
            if text:
                pickup_lines.append(text)
                print("-", text)

        # Add the cleaned lines to the dictionary
        pickup_data[title_text] = pickup_lines

# Save the scraped data as a JSON file
with open("data/pickup_lines.json", "w", encoding="utf-8") as file:
    json.dump(pickup_data, file, indent=4, ensure_ascii=False)
