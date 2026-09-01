import json
import time

from selenium import webdriver  # pyrefly: ignore [missing-import]
from selenium.webdriver.common.by import By  # pyrefly: ignore [missing-import]
# pyrefly: ignore [missing-import]
from selenium.webdriver.support import expected_conditions as EC
# pyrefly: ignore [missing-import]
from selenium.webdriver.support.ui import WebDriverWait

# Start the Edge browser
driver = webdriver.Edge()

driver.get("https://web-scraping.dev/login?cookies=")

wait = WebDriverWait(driver, 10)

# Accept the cookie popup
ok_button = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(text(), 'OK')]")
    )
)
ok_button.click()

# Find the login fields and enter credentials
username_input = wait.until(
    EC.presence_of_element_located(
        (By.NAME, "username")
    )
)

password_input = wait.until(
    EC.presence_of_element_located(
        (By.NAME, "password")
    )
)

username_input.send_keys("user123")
password_input.send_keys("password")

# Submit the login form
submit_button = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(text(), 'Submit')]")
    )
)
submit_button.click()

driver.get("https://web-scraping.dev/testimonials")

# Scroll until no more content is loaded
last_height = driver.execute_script(
    "return document.body.scrollHeight"
)

while True:
    driver.execute_script(
        "window.scrollTo(0, document.body.scrollHeight);"
    )

    time.sleep(2)

    new_height = driver.execute_script(
        "return document.body.scrollHeight"
    )

    if new_height == last_height:
        break

    last_height = new_height

# Find all testimonial elements
testimonials = driver.find_elements(
    By.CSS_SELECTOR,
    "div.testimonial"
)

print("Number of testimonials:", len(testimonials))

# Extract rating and comment from each testimonial
data = []

for testimonial in testimonials:

    rating = len(
        testimonial.find_elements(
            By.CSS_SELECTOR,
            "span.rating > svg"
        )
    )

    text = testimonial.find_element(
        By.CSS_SELECTOR,
        "p"
    ).text

    data.append({
        "rating": rating,
        "comment": text
    })

# Save the scraped testimonials as JSON
with open("data/testimonials.json", "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=4)

print("Data saved to data/testimonials.json")

# Close the browser
driver.quit()
