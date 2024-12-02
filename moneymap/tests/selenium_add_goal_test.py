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


class TestAddMoneyGoal(unittest.TestCase):
    def setUp(self):
        """Set up the Selenium WebDriver."""
        self.browser = Browser.get_browser()
        self.browser.get("http://127.0.0.1:8000/accounts/login/")
        print("Navigated to the login page.")

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

    def test_add_money_goal(self):
        """Test adding a money goal after logging in."""
        browser = self.browser

        # Perform login
        self.login()

        # Navigate to Add Money Goal page
        browser.get("http://127.0.0.1:8000/goals/add-money")
        print("Navigated to 'Add Money Goal' page.")

        try:
            # Locate and fill in the amount field
            amount_input = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, "goal-amount"))
            )
            amount_input.clear()
            amount_input.send_keys('500')

            # Click the "Distribute Evenly" checkbox
            distribute_checkbox = browser.find_element(By.ID, "distribute-evenly")
            if not distribute_checkbox.is_selected():
                distribute_checkbox.click()
            print("Selected 'Distribute Evenly' option.")

            # Submit the form
            submit_button = browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            submit_button.click()
            print("Clicked 'Add New Money Flow' button.")

        except Exception as e:
            self.fail(f"Add Money Goal test failed: {e}")


if __name__ == "__main__":
    unittest.main()
