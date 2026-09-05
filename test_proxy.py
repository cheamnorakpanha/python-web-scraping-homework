import os
import requests
from dotenv import load_dotenv

load_dotenv()

for i in range(1, 11):
    proxy = os.getenv(f"PROXY_{i}")

    print(f"\nTesting PROXY_{i}...")

    if not proxy:
        print("MISSING")
        continue

    try:
        response = requests.get(
            "https://httpbin.org/ip",
            proxies={
                "http": proxy,
                "https": proxy,
            },
            timeout=10,
        )

        print(f"SUCCESS: {response.status_code}")
        print(f"IP: {response.json()['origin']}")

    except requests.exceptions.ProxyError as e:
        print(f"PROXY ERROR: {e}")

    except requests.exceptions.ConnectTimeout:
        print("TIMEOUT")

    except requests.exceptions.SSLError:
        print("SSL ERROR")

    except requests.exceptions.RequestException as e:
        print(f"ERROR: {type(e).__name__}")
