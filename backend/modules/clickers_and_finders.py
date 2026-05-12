from config.config_bridge import *
from modules.helpers import buffer, print_lg, sleep, random_sleep
from modules.human_actions import human_move_and_click, human_type_text
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime


def _driver_for(root: WebDriver | WebElement) -> WebDriver:
    if isinstance(root, WebDriver):
        return root
    parent = getattr(root, "_parent", None)
    if parent is not None:
        return parent  # type: ignore[return-value]
    raise TypeError("Cannot resolve WebDriver from root")


# Click Functions
def wait_span_click(
    driver: WebDriver,
    text: str,
    time: float = 5.0,
    click: bool = True,
    scroll: bool = True,
    scrollTop: bool = False,
) -> WebElement | bool:
    """
    Finds the span element with the given `text`.
    - Returns `WebElement` if found, else `False` if not found.
    - Clicks on it if `click = True`.
    - Will spend a max of `time` seconds in searching for each element.
    - Will scroll to the element if `scroll = True`.
    - Will scroll to the top if `scrollTop = True`.
    """
    if text:
        try:
            button = WebDriverWait(driver, time).until(
                EC.presence_of_element_located(
                    (By.XPATH, './/span[normalize-space(.)="' + text + '"]')
                )
            )
            if scroll:
                scroll_to_view(driver, button, scrollTop)
            if click:
                human_move_and_click(driver, button)
                buffer(click_gap)
            return button
        except Exception as e:
            print_lg("Click Failed! Didn't find '" + text + "'")
            # print_lg(e)
            return False


def multi_sel(driver: WebDriver, texts: list, time: float = 5.0) -> None:
    """
    - For each text in the `texts`, tries to find and click `span` element with that text.
    - Will spend a max of `time` seconds in searching for each element.
    """
    for text in texts:
        ##> ------ Dheeraj Deshwal : dheeraj20194@iiitd.ac.in/dheerajdeshwal9811@gmail.com - Bug fix ------
        wait_span_click(driver, text, time, False)
        ##<
        try:
            button = WebDriverWait(driver, time).until(
                EC.presence_of_element_located(
                    (By.XPATH, './/span[normalize-space(.)="' + text + '"]')
                )
            )
            scroll_to_view(driver, button)
            human_move_and_click(driver, button)
            buffer(click_gap)
        except Exception as e:
            print_lg("Click Failed! Didn't find '" + text + "'")
            # print_lg(e)


def multi_sel_noWait(
    driver: WebDriver, texts: list, actions: ActionChains = None
) -> None:
    """
    - For each text in the `texts`, tries to find and click `span` element with that class.
    - If `actions` is provided, bot tries to search and Add the `text` to this filters list section.
    - Won't wait to search for each element, assumes that element is rendered.
    """
    for text in texts:
        try:
            button = driver.find_element(
                By.XPATH, './/span[normalize-space(.)="' + text + '"]'
            )
            scroll_to_view(driver, button)
            human_move_and_click(driver, button)
            buffer(click_gap)
        except Exception as e:
            if actions:
                company_search_click(driver, actions, text)
            else:
                print_lg("Click Failed! Didn't find '" + text + "'")
            # print_lg(e)


def boolean_button_click(driver: WebDriver, actions: ActionChains, text: str) -> None:
    """
    Tries to click on the boolean button with the given `text` text.
    """
    try:
        list_container = driver.find_element(
            By.XPATH, './/h3[normalize-space()="' + text + '"]/ancestor::fieldset'
        )
        button = list_container.find_element(By.XPATH, './/input[@role="switch"]')
        scroll_to_view(driver, button)
        human_move_and_click(driver, button)
        buffer(click_gap)
    except Exception as e:
        print_lg("Click Failed! Didn't find '" + text + "'")
        # print_lg(e)


# Find functions
def find_by_class(
    driver: WebDriver, class_name: str, time: float = 5.0
) -> WebElement | Exception:
    """
    Waits for a max of `time` seconds for element to be found, and returns `WebElement` if found, else `Exception` if not found.
    """
    return WebDriverWait(driver, time).until(
        EC.presence_of_element_located((By.CLASS_NAME, class_name))
    )


# Scroll functions
def scroll_to_view(
    driver: WebDriver,
    element: WebElement,
    top: bool = False,
    smooth_scroll: bool = smooth_scroll,
) -> None:
    """
    Scrolls the `element` to view.
    - `smooth_scroll` will scroll with smooth behavior.
    - `top` will scroll to the `element` to top of the view.
    """
    if top:
        return driver.execute_script("arguments[0].scrollIntoView();", element)
    behavior = "smooth" if smooth_scroll else "instant"
    return driver.execute_script(
        'arguments[0].scrollIntoView({block: "center", behavior: "'
        + behavior
        + '" });',
        element,
    )


# Enter input text functions
def text_input_by_ID(
    driver: WebDriver, id: str, value: str, time: float = 5.0
) -> None | Exception:
    """
    Enters `value` into the input field with the given `id` if found, else throws NotFoundException.
    - `time` is the max time to wait for the element to be found.
    """
    username_field = WebDriverWait(driver, time).until(
        EC.presence_of_element_located((By.ID, id))
    )
    username_field.clear()
    human_type_text(username_field, value)


def try_xp(root: WebDriver | WebElement, xpath: str, click: bool = True) -> WebElement | bool:
    try:
        el = root.find_element(By.XPATH, xpath)
        if click:
            human_move_and_click(_driver_for(root), el)
            return True
        return el
    except:
        return False


def try_linkText(driver: WebDriver, linkText: str) -> WebElement | bool:
    try:
        return driver.find_element(By.LINK_TEXT, linkText)
    except:
        return False


def try_find_by_classes(
    driver: WebDriver, classes: list[str]
) -> WebElement | ValueError:
    for cla in classes:
        try:
            return driver.find_element(By.CLASS_NAME, cla)
        except:
            pass
    raise ValueError("Failed to find an element with given classes")


def company_search_click(
    driver: WebDriver, actions: ActionChains, companyName: str
) -> None:
    """
    Tries to search and Add the company to company filters list.
    """
    wait_span_click(driver, "Add a company", 1)
    search = driver.find_element(
        By.XPATH, "(.//input[@placeholder='Add a company'])[1]"
    )
    search.send_keys(Keys.CONTROL + "a")
    human_type_text(search, companyName)
    random_sleep(2, 4)
    actions.send_keys(Keys.DOWN).perform()
    actions.send_keys(Keys.ENTER).perform()
    print_lg(f'Tried searching and adding "{companyName}"')


def text_input(
    driver: WebDriver,
    actions: ActionChains,
    textInputEle: WebElement | bool,
    value: str,
    textFieldName: str = "Text",
) -> None | Exception:
    if textInputEle:
        random_sleep(0.5, 1)
        textInputEle.clear()
        human_type_text(textInputEle, value.strip())
        random_sleep(1, 2)
        actions.send_keys(Keys.ENTER).perform()
    else:
        print_lg(f"{textFieldName} input was not given!")


def robust_click(
    driver: WebDriver, text_variants: list[str], time: float = 5.0
) -> bool:
    """
    Tries to find and click a button using multiple robust strategies.
    Returns True if successful, False otherwise.
    """
    print_lg(f"Trying robust click for: {text_variants}")
    end_time = datetime.now().timestamp() + time

    while datetime.now().timestamp() < end_time:
        try:
            # Strategy 1: aria-label (most robust)
            for text in text_variants:
                try:
                    # Case-insensitive contains for aria-label
                    xpath = f"//button[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]"
                    elem = driver.find_element(By.XPATH, xpath)
                    if elem.is_displayed() and elem.is_enabled():
                        scroll_to_view(driver, elem)
                        human_move_and_click(driver, elem)
                        buffer(click_gap)
                        return True
                except:
                    pass

            # Strategy 2: Button text
            for text in text_variants:
                try:
                    xpath = f"//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]"
                    elem = driver.find_element(By.XPATH, xpath)
                    if elem.is_displayed() and elem.is_enabled():
                        scroll_to_view(driver, elem)
                        human_move_and_click(driver, elem)
                        buffer(click_gap)
                        return True
                except:
                    pass

            # Strategy 3: Span text (common in LinkedIn)
            for text in text_variants:
                try:
                    xpath = f"//span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]"
                    elem = driver.find_element(By.XPATH, xpath)
                    if elem.is_displayed() and elem.is_enabled():
                        scroll_to_view(driver, elem)
                        human_move_and_click(driver, elem)
                        buffer(click_gap)
                        return True
                except:
                    pass

        except Exception as e:
            # print_lg(f"Robust click error: {e}")
            pass

        random_sleep(0.2, 0.5)

    print_lg(f"Robust click failed for {text_variants}")
    return False
