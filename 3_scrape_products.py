from scrapling.fetchers import FetcherSession, ProxyRotator
from dotenv import load_dotenv  # pyrefly: ignore [missing-import]
import sys
import json
import os

load_dotenv()

# Enable UTF-8 output for the terminal
sys.stdout.reconfigure(encoding="utf-8")

# Load proxy addresses from environment variables
proxies = [
    os.getenv("PROXY_1"),
    os.getenv("PROXY_2"),
    os.getenv("PROXY_3"),
    os.getenv("PROXY_4"),
    os.getenv("PROXY_5"),
    os.getenv("PROXY_6"),
    os.getenv("PROXY_7"),
    os.getenv("PROXY_8"),
    os.getenv("PROXY_9"),
]

# Rotate between proxies when making requests
rotator = ProxyRotator(proxies)

URL = "https://www.goldonecomputer.com/"

# Main product categories to scrape
main_categories = [
    "Laptop",
    "Desktop",
    "Monitor",
    "Tablet and Handheld",
    "PC Components",
    "Gaming Gear",
    "Accessories",
    "Digital Storage",
    "Audio Device",
    "Laptop Sqare Parts",
    "Network",
    "Printer and Scanner",
    "Projector",
    "UPS",
    "Software",
    "Security System",
]

# Create the output path relative to this Python file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
output_file = os.path.join(SCRIPT_DIR, "data", "goldone_products.json")

os.makedirs(os.path.dirname(output_file), exist_ok=True)

# Load existing products so the scraper can resume
if os.path.exists(output_file):
    try:
        with open(output_file, "r", encoding="utf-8") as file:
            products = json.load(file)

        if not isinstance(products, list):
            products = []

    except (json.JSONDecodeError, OSError):
        products = []
else:
    products = []


# Keep track of product codes that have already been saved
completed_codes = set()

for product in products:
    code = product.get("product_code", "").strip()

    if code:
        completed_codes.add(code)


# Create an empty JSON array if the output file does not exist
if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
    with open(output_file, "w", encoding="utf-8") as file:
        file.write("[\n]\n")


# Append one product to the existing JSON array
def append_product(product, has_existing_products):

    if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("[\n]\n")

        has_existing_products = False

    with open(output_file, "r+", encoding="utf-8") as file:
        content = file.read().rstrip()

        if not content.endswith("]"):
            raise ValueError("JSON file is not a valid array")

        content = content[:-1].rstrip()

        file.seek(0)
        file.truncate()
        file.write(content)

        if has_existing_products:
            file.write(",\n")

        json.dump(product, file, ensure_ascii=False, indent=4)
        file.write("\n]\n")
        file.flush()
        os.fsync(file.fileno())


with FetcherSession(proxy_rotator=rotator) as session:

    # Open the main website
    response = session.get(URL)

    print("Status:", response.status)
    print("URL:", response.url)

    # Find links for the main product categories
    category_links = []

    for link in response.css('a[href*="route=product/category"]'):

        text = link.text.strip()
        href = link.attrib.get("href")

        if not href:
            continue

        path = href.split("path=")[-1]

        # Ignore subcategories
        if "_" in path:
            continue

        if text in main_categories:
            category_links.append(href.strip())

    # Remove duplicate category links
    category_links = list(dict.fromkeys(category_links))

    print("Number of main categories:", len(category_links))

    all_product_links = []

    # Scrape each main category
    for category_number, category_link in enumerate(
        category_links,
        start=1
    ):

        print(f"\nCategory {category_number}/16")
        print(category_link)

        category_page = session.get(category_link)

        # Determine the total number of pages in the category
        page_numbers = []

        for link in category_page.css("ul.pagination a"):

            text = link.text.strip()

            if text.isdigit():
                page_numbers.append(int(text))

        if page_numbers:
            max_page = max(page_numbers)
        else:
            max_page = 1

        print("Pages:", 1, "to", max_page)

        category_products = []

        # Collect product links from every page
        for page_number in range(1, max_page + 1):

            if page_number == 1:
                page_url = category_link
            else:
                page_url = f"{category_link}&page={page_number}"

            print(f"Page {page_number}/{max_page}")

            page = session.get(page_url)

            product_links = page.css(
                'a[href*="route=product/product"]::attr(href)'
            ).getall()

            product_links = [
                link.strip() for link in product_links if link
            ]

            # Remove duplicate product links from the page
            product_links = list(dict.fromkeys(product_links))

            print("Products:", len(product_links))

            category_products.extend(product_links)

        # Remove duplicates within the category
        category_products = list(dict.fromkeys(category_products))

        print(
            "Total products in category:",
            len(category_products)
        )

        all_product_links.extend(category_products)

    # Remove duplicates across all categories
    all_product_links = list(dict.fromkeys(all_product_links))

    print(
        "\nTotal unique product links:",
        len(all_product_links)
    )

    # Scrape information from each product page
    for i, product_url in enumerate(
        all_product_links,
        start=1
    ):

        try:
            print(
                f"\nScraping product "
                f"{i}/{len(all_product_links)}"
            )

            product_page = session.get(product_url)

            # Extract the main product information
            title = product_page.css(
                "h3.product-title::text"
            ).get("").strip()

            price = product_page.css(
                "ul.list-unstyled.price h3::text"
            ).get("").strip()

            if not title or not price:
                print(
                    "Invalid product page. Skipping:",
                    product_url
                )
                continue

            brand = product_page.css(
                "div.product-right ul.list-unstyled > "
                "li:nth-child(1) a::text"
            ).get("").strip()

            # Extract the product code
            code_parts = product_page.css(
                "div.product-right ul.list-unstyled > "
                "li:nth-child(2)::text"
            ).getall()

            code_parts = [
                text.strip()
                for text in code_parts
                if text.strip()
            ]

            product_code = ""

            for text in code_parts:
                if text != "Product Code:":
                    product_code = text
                    break

            review_count = product_page.css(
                "a.review-count::text"
            ).get("").strip()

            # Try to get the high-resolution image first
            image = product_page.css(
                "img#tmzoom::attr(data-zoom-image)"
            ).get("")

            # Use the normal image as a fallback
            if not image:
                image = product_page.css(
                    "img#tmzoom::attr(src)"
                ).get("")

            # Skip products that were already saved
            if product_code and product_code in completed_codes:
                print("Already saved:", product_code)
                continue

            # Store the extracted product information
            product = {
                "product_code": product_code,
                "title": title,
                "brand": brand,
                "price": price,
                "review_count": review_count,
                "image": image,
            }

            # Save the product immediately
            append_product(
                product,
                len(products) > 0
            )

            products.append(product)

            if product_code:
                completed_codes.add(product_code)

            print("Saved:", title)

        except Exception as error:
            print("Error:", error)
            print("Failed:", product_url)
            continue


print("\nFinished!")
print("Total products:", len(products))
print("Saved to:", output_file)
