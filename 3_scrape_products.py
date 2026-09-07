import os
import json
from dotenv import load_dotenv
from scrapling.spiders import Spider, Response
from scrapling.fetchers import FetcherSession, ProxyRotator

load_dotenv()

OUTPUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data",
    "goldone_products.json"
)

CATEGORIES = {
    "Laptop", "Desktop", "Monitor", "Tablet and Handheld",
    "PC Components", "Gaming Gear", "Accessories",
    "Digital Storage", "Audio Device", "Laptop Sqare Parts",
    "Network", "Printer and Scanner", "Projector", "UPS",
    "Software", "Security System"
}


class GoldOneSpider(Spider):
    name = "goldone"
    start_urls = ["https://www.goldonecomputer.com/"]

    custom_settings = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._products = []
        os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

    def _flush(self):
        """Write all buffered products to disk."""
        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump(self._products, f, ensure_ascii=False, indent=4)

    def configure_sessions(self, manager):
        proxies = [
            os.getenv(f"PROXY_{i}")
            for i in range(1, 11)
        ]
        proxies = [p for p in proxies if p]

        print(f"Loaded {len(proxies)} proxies")

        manager.add(
            "default",
            FetcherSession(
                proxy_rotator=ProxyRotator(proxies)
            ),
            default=True
        )

    async def parse(self, response: Response):
        for link in response.css('a[href*="route=product/category"]'):
            href = link.attrib.get("href")

            if (
                href
                and "_" not in href.split("path=")[-1]
                and link.text.strip() in CATEGORIES
            ):
                yield response.follow(
                    href.strip(),
                    callback=self.parse_category
                )

    async def parse_category(self, response: Response):
        # Scrape all products on this page
        for href in response.css(
            'a[href*="route=product/product"]::attr(href)'
        ).getall():
            yield response.follow(
                href.strip(),
                callback=self.parse_product
            )

        # Follow ONLY the next page
        next_href = response.css(
            "ul.pagination li.active + li a::attr(href)"
        ).get()

        if next_href:
            yield response.follow(
                next_href.strip(),
                callback=self.parse_category
            )

    async def parse_product(self, response: Response):
        title = response.css(
            "h3.product-title::text"
        ).get("").strip()

        price = response.css(
            "ul.list-unstyled.price h3::text"
        ).get("").strip()

        if not title or not price:
            return

        code = [
            x.strip()
            for x in response.css(
                "div.product-right ul.list-unstyled > "
                "li:nth-child(2)::text"
            ).getall()
            if x.strip() and x.strip() != "Product Code:"
        ]

        image = (
            response.css(
                "img#tmzoom::attr(data-zoom-image)"
            ).get("")
            or response.css(
                "img#tmzoom::attr(src)"
            ).get("")
        )

        product = {
            "product_code": code[0] if code else "",
            "title": title,
            "brand": response.css(
                "div.product-right ul.list-unstyled > "
                "li:nth-child(1) a::text"
            ).get("").strip(),
            "price": price,
            "review_count": response.css(
                "a.review-count::text"
            ).get("").strip(),
            "image": image,
            "url": response.url
        }

        self._products.append(product)

        if len(self._products) % 10 == 0:
            self._flush()
            print(f"[{len(self._products)}] Batch saved to file...")
        else:
            print(f"[{len(self._products)}] Scraped: {title}")

        yield product


spider = GoldOneSpider()
spider.start()
spider._flush()  # final flush for any remaining items

print(f"\nFinished! {len(spider._products)} products saved to: {OUTPUT}")
