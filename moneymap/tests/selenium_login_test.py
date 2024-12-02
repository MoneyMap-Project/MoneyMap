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
        options.add_argument("--headless")
        return webdriver.Chrome(options=options)


class TestLoginPage(unittest.TestCase):
    def setUp(self):
        """Set up the Selenium WebDriver."""
        self.browser = Browser.get_browser()
        self.browser.get("http://127.0.0.1:8000/accounts/login/")
        print("Navigated to login page.")

    def tearDown(self):
        """Close the browser after the test."""
        self.browser.quit()
        print("Browser closed.")

    def test_login(self):
        """Test the login functionality."""
        browser = self.browser

        try:
            if not os.getenv("TEST_USERNAME") or not os.getenv("TEST_PASSWORD"):
                raise EnvironmentError("Environment variables TEST_USERNAME and TEST_PASSWORD are not set.")

            username = os.getenv("TEST_USERNAME")
            password = os.getenv("TEST_PASSWORD")

            # Locate and interact with username and password fields
            username_input = WebDriverWait(browser, 20).until(
                EC.visibility_of_element_located((By.ID, "id_login"))
            )
            username_input.send_keys(username)
            print("Entered username.")

            password_input = browser.find_element(By.ID, "id_password")
            password_input.send_keys(password)
            print("Entered password.")

            login_button = browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            login_button.click()
            print("Clicked login button.")

            # Wait for successful redirection to the home page
            WebDriverWait(browser, 20).until(
                EC.url_to_be("http://127.0.0.1:8000/")
            )
            print("Successfully logged in and redirected to the home page.")

        except Exception as e:
            # Save a screenshot for debugging
            print("Screenshot saved as 'login_page_failure.png'")

            # Fail the test and print the error
            self.fail(f"Login test failed: {e}")

    def test_login_failure(self):
        """Test login with invalid credentials."""
        browser = self.browser

        try:
            # Enter invalid username and password
            username_input = WebDriverWait(browser, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="login"]'))
            )
            username_input.send_keys("invaliduser@example.com")
            print("Entered invalid username.")

            password_input = browser.find_element(By.CSS_SELECTOR, 'input[name="password"]')
            password_input.send_keys("wrongpassword")
            print("Entered invalid password.")

            # Click the login button
            login_button = browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            login_button.click()
            print("Clicked login button.")

        except Exception as e:
            self.fail(f"Login failure test failed: {e}")


if __name__ == "__main__":
    unittest.main()
