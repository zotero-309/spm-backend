import unittest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class SeleniumTest(unittest.TestCase):

    def setUp(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    def test_navigate_month_buttons(self):
        driver = self.driver
        # driver.get("http://192.168.2.166:8080/#/scheduler")
       
        driver.get(" http://localhost:8080/#/scheduler")
        # Navigate 3 months back
        for _ in range(3):
            prev_month_button = driver.find_element(By.CSS_SELECTOR, '.smart-calendar-button[smart-id="previousMonthButton"]')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.smart-calendar-button[smart-id="previousMonthButton"]')))
            prev_month_button.click()
            time.sleep(1)  # Ensure UI catches up

        # Check if previous month button is disabled
        prev_month_button = driver.find_element(By.CSS_SELECTOR, '.smart-calendar-button[smart-id="previousMonthButton"]')
        prev_month_disabled = prev_month_button.get_attribute('aria-disabled')
        is_disabled = prev_month_button.get_attribute('disabled') is not None
        print(f"Previous month button disabled state: {prev_month_disabled}, is disabled: {is_disabled}")
        self.assertTrue(prev_month_disabled == "true" or is_disabled, "Previous month button should be disabled after navigating 3 months back.")

        # Navigate forward 4 months
        for _ in range(6):
            next_month_button = driver.find_element(By.CSS_SELECTOR, '.smart-calendar-button[smart-id="nextMonthButton"]')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.smart-calendar-button[smart-id="nextMonthButton"]')))
            next_month_button.click()
            time.sleep(1)  # Ensure UI catches up

        # Check if next month button is disabled
        next_month_button = driver.find_element(By.CSS_SELECTOR, '.smart-calendar-button[smart-id="nextMonthButton"]')
        next_month_disabled = next_month_button.get_attribute('aria-disabled')
        is_disabled = next_month_button.get_attribute('disabled') is not None
        print(f"Next month button disabled state: {next_month_disabled}, is disabled: {is_disabled}")
        self.assertTrue(next_month_disabled == "true" or is_disabled, "Next month button should be disabled after navigating 4 months forward.")


    
    def test_smart_repeat_button_clicks(self):
        driver = self.driver
        #driver.get("http://192.168.2.166:8080/#/scheduler")
        driver.get(" http://localhost:8080/#/scheduler")
        time.sleep(2)
             # Navigate forward 4 months
        for _ in range(14):
            next_month_button = driver.find_element(By.CSS_SELECTOR, '.smart-repeat-button[smart-id="previousDate"] .smart-button[smart-id="button"]')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.smart-repeat-button[smart-id="previousDate"] .smart-button[smart-id="button"]')))
            next_month_button.click()
            time.sleep(1)  # Ensure UI catches up

        # Check if next month button is disabled
        next_month_button = driver.find_element(By.CSS_SELECTOR, '.smart-repeat-button[smart-id="previousDate"] .smart-button[smart-id="button"]')
        next_month_disabled = next_month_button.get_attribute('aria-disabled')
        is_disabled = next_month_button.get_attribute('disabled') is not None
        print(f"Next month button disabled state: {next_month_disabled}, is disabled: {is_disabled}")
        self.assertTrue(next_month_disabled == "true" or is_disabled, "Next month button should be disabled after navigating 4 months forward.")

         # Navigate forward 4 months
        for _ in range(27):
            next_month_button = driver.find_element(By.CSS_SELECTOR, '.smart-repeat-button[smart-id="nextDate"] .smart-button[smart-id="button"]')
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.smart-repeat-button[smart-id="nextDate"] .smart-button[smart-id="button"]')))
            next_month_button.click()
            time.sleep(1)  # Ensure UI catches up

        # Check if next month button is disabled
        next_month_button = driver.find_element(By.CSS_SELECTOR, '.smart-repeat-button[smart-id="nextDate"] .smart-button[smart-id="button"]')
        next_month_disabled = next_month_button.get_attribute('aria-disabled')
        is_disabled = next_month_button.get_attribute('disabled') is not None
        print(f"Next month button disabled state: {next_month_disabled}, is disabled: {is_disabled}")
        self.assertTrue(next_month_disabled == "true" or is_disabled, "Next month button should be disabled after navigating 4 months forward.")

    def test_value_exists_on_page(self):
        driver = self.driver
        driver.get("http://192.168.2.166:8080/#/scheduler")

        # Wait for an element containing "WFH" to be present
        try:
            # Check for the presence of "WFH"
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//label[contains(text(), 'WFH')]"))
            )
            print("'WFH' is present on the page.")
            
            # Check for the presence of the specific time label
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//label[contains(text(), '8:00 AM - 12:00 PM')]"))
            )
            print("'8:00 AM - 12:00 PM' is present on the page.")
        
        except TimeoutException:
            self.fail("'WFH' or '8:00 AM - 12:00 PM' is not present on the page.")


    def tearDown(self):
        self.driver.quit()

if __name__ == "__main__":
    unittest.main()
