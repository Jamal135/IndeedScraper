''' Created: 10/09/2023 '''

# External Dependencies
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver, WebElement
from bs4 import BeautifulSoup
import re

# Internal Dependencies
from utilities.handle_exceptions import ScraperExceptions as SE

WEBDRIVER_TIMEOUT = 20

class Constants:
    ''' Purpose: Stores commonly used scraper specific constants. '''
    # Verify that URL and year meet expected formats.
    year_pattern = re.compile(r"\d{4}")
    # Expected challenge/good text strings in review data block.
    good_text = 'The good things'
    challenge_text = 'The challenges'
    # Expected index of 'The challenges' text in data block.
    data_challenge_idx = 7
    # Distance of 'The good things' text index from start of data block.
    data_start_offset =  5
    # Expected index of data point that contains 4 digit year.
    data_year_idx = 1
    # Length of list data block per set of review data.
    data_length = 9 

class Validators:
    ''' Purpose: Contains all scraper specific validation logic. '''
    url_pattern = r'https?://www\.seek\.com\.au/companies/.+/reviews'
    @staticmethod
    def validate_data_block(block: list):
        ''' Purpose: Validates the given data block. '''
        try:
            if not Constants.year_pattern.match((block[Constants.data_year_idx].split()[1])):
                raise SE.UnexpectedData(f'Expected year at second block index:\n{block}')
            if not block[Constants.data_challenge_idx] == Constants.challenge_text:
                raise SE.UnexpectedData(f'Expected challenge text at second last block index:\n{block}')
        except (IndexError, AttributeError):
            raise SE.UnexpectedData(f'Unexpected data format encountered:\n{block}')

class Parsers:
    ''' Purpose: Stores all scraper logic for processing review data. '''
    @staticmethod
    def extract_total_reviews(driver: WebDriver) -> int:
        ''' Returns: Total number of reviews for particular organisation. '''
        total_element = driver.find_element(By.XPATH, '//strong[following-sibling::text()[contains(., "reviews sorted by")]]')
        total_str = total_element.text
        return int(total_str.strip())
    @staticmethod
    def extract_page_text(soup: BeautifulSoup) -> list[str]:
        ''' Returns: List of review element text extracted from page soup. '''
        return [element.get_text() for element in soup.find_all(['span', 'h3'])]
    @staticmethod
    def extract_data_indices(texts: list[list]) -> list[int]:
        ''' Returns: List of indices of relevant review data blocks in list. '''
        return [i for i, x in enumerate(texts) if x == Constants.good_text]
    @staticmethod
    def extract_data_bounds(idx: int) -> dict[str, int]:
        ''' Returns: Dict of start and end indexs for relevant review data in list. '''
        start_idx = idx - Constants.data_start_offset
        end_idx = idx + Constants.data_length - Constants.data_start_offset
        return {"start_idx": start_idx, "end_idx": end_idx}
    @staticmethod
    def extract_data_block(texts: list[list], data_bounds: dict[str, int]) -> list[str]:
        ''' Returns: List block of review data from full list of text. '''
        return texts[data_bounds['start_idx']:data_bounds['end_idx']]

class Navigators:
    ''' Purpose: Stores all logic for navigating and loading webpages. '''
    @staticmethod
    def grab_next_button(driver: WebDriver) -> WebElement:
        ''' Returns: Next review page button element. '''
        return driver.find_element(By.XPATH, '//a[@aria-label="Next"]')
    @staticmethod
    def check_next_page(next_button: WebElement) -> bool:
        ''' Returns: Boolean True or False if there is a next review page. '''
        return next_button.get_attribute('tabindex') != '-1'
    @staticmethod
    def wait_for_url(driver: WebDriver):
        ''' Purpose: Waits for the webpage contents to load. '''
        wait = WebDriverWait(driver, WEBDRIVER_TIMEOUT)
        wait.until(EC.presence_of_element_located((By.XPATH, "//a[@aria-label='Next']")))
    @staticmethod
    def wait_for_next_page(driver: WebDriver):
        ''' Waits for the review contents of the page to update. '''
        old_texts = [elem.text for elem in driver.find_elements(By.TAG_NAME, 'h3')]
        def page_has_changed(driver: webdriver.Chrome) -> bool:
            try:
                current_texts = [elem.text for elem in driver.find_elements(By.TAG_NAME, 'h3')]
                return current_texts != old_texts
            except StaleElementReferenceException:
                return False
        wait = WebDriverWait(driver, WEBDRIVER_TIMEOUT)
        wait.until(page_has_changed)
