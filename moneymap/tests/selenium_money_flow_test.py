import os
from dotenv import load_dotenv
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()


class Browser:
    """Provide access to an instance of a Selenium web driver."""

    @classmethod
    def get_browser(cls):
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless")
        return webdriver.Chrome(options=options)


class TestMoneyFlowPage(unittest.TestCase):
    def setUp(self):
        """Set up the Selenium WebDriver."""
        self.browser = Browser.get_browser()
        print("Navigated to login page.")
        self.base_url = "http://127.0.0.1:8000/accounts/login/"
        self.money_flow_url = "http://127.0.0.1:8000/income-and-expenses/money-flow/"
        self.browser.get(self.base_url)

    def tearDown(self):
        """Close the browser after the test."""
        self.browser.quit()
        print("Browser closed.")

    def login(self):
        """Log in with valid credentials."""
        browser = self.browser

        username = os.getenv("TEST_USERNAME")
        password = os.getenv("TEST_PASSWORD")
        if not username or not password:
            raise EnvironmentError("Environment variables TEST_USERNAME and TEST_PASSWORD are not set.")

        username_input = WebDriverWait(browser, 20).until(
            EC.visibility_of_element_located((By.ID, "id_login"))
        )
        username_input.send_keys(username)

        password_input = browser.find_element(By.ID, "id_password")
        password_input.send_keys(password)

        login_button = browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        login_button.click()

        # Wait for successful redirection
        WebDriverWait(browser, 20).until(
            EC.url_to_be("http://127.0.0.1:8000/")
        )

    def test_money_flow(self):
        """Test adding a money flow entry."""
        browser = self.browser

        try:
            # Log in first
            self.login()

            # Navigate to the money flow page
            browser.get(self.money_flow_url)

            # Fill in the money flow form
            description_input = WebDriverWait(browser, 10).until(
                EC.visibility_of_element_located((By.NAME, "description"))
            )
            description_input.send_keys("Test Income")

            amount_input = browser.find_element(By.NAME, "amount")
            amount_input.send_keys("5000")

            money_type = browser.find_element(By.XPATH, '//*[@id="money-flow-form"]/div/div/div[1]/div[2]/div[3]/div['
                                                        '1]/div')
            money_type.click()

            tag_open_overlay = browser.find_element(By.ID, "add-more-tag")
            tag_open_overlay.click()
            tag_add = browser.find_element(By.ID, "new-tag-input")
            tag_add.send_keys("Tag 1")
            tag_submit = browser.find_element(By.ID, "add-button")
            tag_submit.click()
            tag_option = browser.find_element(By.XPATH,
                                              '//*[@id="money-flow-form"]/div/div/div[1]/div[2]/div[2]/div[1]')
            tag_option.click()

            # Submit the form
            submit_button = browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            submit_button.click()

        except Exception as e:
            self.fail(f"Money flow test failed: {e}")

    def test_same_tag_name(self):
        """Test adding a money flow entry with the same tag name."""
        browser = self.browser

        try:
            # Log in first
            self.login()

            # Navigate to the money flow page
            browser.get(self.money_flow_url)

            # Fill in the money flow form
            description_input = WebDriverWait(browser, 10).until(
                EC.visibility_of_element_located((By.NAME, "description"))
            )
            description_input.send_keys("Test Expense")

            amount_input = browser.find_element(By.NAME, "amount")
            amount_input.send_keys("1000")

            money_type = browser.find_element(By.XPATH, '//*[@id="money-flow-form"]/div/div/div[1]/div[2]/div[3]/div['
                                                        '1]/div')
            money_type.click()

            tag_open_overlay = browser.find_element(By.ID, "add-more-tag")
            tag_open_overlay.click()
            tag_add = browser.find_element(By.ID, "new-tag-input")
            tag_add.send_keys("Tag 1")
            tag_submit = browser.find_element(By.ID, "add-button")
            tag_submit.click()
            tag_option = browser.find_element(By.XPATH,
                                              '//*[@id="money-flow-form"]/div/div/div[1]/div[2]/div[2]/div[1]')
            tag_option.click()

            tag_open_overlay2 = browser.find_element(By.ID, "add-more-tag")
            tag_open_overlay2.click()
            tag_add2 = browser.find_element(By.ID, "new-tag-input")
            tag_add2.send_keys("Tag 1")
            tag_submit2 = browser.find_element(By.ID, "add-button")
            tag_submit2.click()

            error_message = browser.find_element(By.ID, "messages-container")
            normalized_message = " ".join(
                error_message.text.split())
            expected_message = "Error Tag name already exists."
            self.assertEqual(normalized_message, expected_message, f"Unexpected error message: {normalized_message}")

            submit_button = browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            submit_button.click()

        except Exception as e:
            self.fail(f"Money flow test failed: {e}")

    def test_no_description(self):
        """Test adding a money flow entry with no description."""
        browser = self.browser

        try:
            # Log in first
            self.login()

            # Navigate to the money flow page
            browser.get(self.money_flow_url)

            # Fill in the money flow form
            amount_input = browser.find_element(By.NAME, "amount")
            amount_input.send_keys("5000")

            money_type = browser.find_element(By.XPATH, '//*[@id="money-flow-form"]/div/div/div[1]/div[2]/div[3]/div['
                                                        '1]/div')
            money_type.click()

            tag_open_overlay = browser.find_element(By.ID, "add-more-tag")
            tag_open_overlay.click()
            tag_add = browser.find_element(By.ID, "new-tag-input")
            tag_add.send_keys("Tag 1")
            tag_submit = browser.find_element(By.ID, "add-button")
            tag_submit.click()
            tag_option = browser.find_element(By.XPATH,
                                              '//*[@id="money-flow-form"]/div/div/div[1]/div[2]/div[2]/div[1]')
            tag_option.click()

            submit_button = browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            submit_button.click()

            self.assertEqual(browser.current_url, self.money_flow_url)

        except Exception as e:
            self.fail(f"Money flow test failed: {e}")

    def test_no_amount(self):
        """Test adding a money flow entry with no amount."""
        browser = self.browser

        try:
            # Log in first
            self.login()

            # Navigate to the money flow page
            browser.get(self.money_flow_url)

            # Fill in the money flow form
            description_input = WebDriverWait(browser, 10).until(
                EC.visibility_of_element_located((By.NAME, "description"))
            )
            description_input.send_keys("Test Expense")

            money_type = browser.find_element(By.XPATH, '//*[@id="money-flow-form"]/div/div/div[1]/div[2]/div[3]/div['
                                                        '1]/div')
            money_type.click()

            tag_open_overlay = browser.find_element(By.ID, "add-more-tag")
            tag_open_overlay.click()
            tag_add = browser.find_element(By.ID, "new-tag-input")
            tag_add.send_keys("Tag 1")
            tag_submit = browser.find_element(By.ID, "add-button")
            tag_submit.click()
            tag_option = browser.find_element(By.XPATH,
                                              '//*[@id="money-flow-form"]/div/div/div[1]/div[2]/div[2]/div[1]')
            tag_option.click()

            submit_button = browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            submit_button.click()

            self.assertEqual(browser.current_url, self.money_flow_url)

        except Exception as e:
            self.fail(f"Money flow test failed: {e}")


if __name__ == "__main__":
    unittest.main()
