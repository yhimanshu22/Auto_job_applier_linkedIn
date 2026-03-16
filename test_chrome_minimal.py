
import undetected_chromedriver as uc
import time
from selenium.common.exceptions import WebDriverException

def test_chrome():
    print("Testing Undetected Chromedriver start...")
    options = uc.ChromeOptions()
    # options.add_argument("--headless") # Try headless first to see if it's a display issue
    try:
        driver = uc.Chrome(options=options, version_main=145)
        print("Successfully opened Chrome!")
        driver.get("https://www.google.com")
        print(f"Page title: {driver.title}")
        time.sleep(5)
        driver.quit()
        print("Successfully closed Chrome!")
    except Exception as e:
        print(f"Failed to open Chrome: {e}")

if __name__ == "__main__":
    test_chrome()
