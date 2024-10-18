import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime

def scrape_canada_bills():
    """
    Scrapes Canadian law bill information from the Parliament of Canada website,
    updates the existing JSON data, and records changes with timestamps.

    This function is designed to be run as a cron job or called via an API.
    """

    # ### Once upon a time, there was a scraper that had to visit a website with Canadian law-bill information.
    # To achieve its mission, it set up the necessary tools to make its journey a success.

    # Set up Chrome options
    # #### Our scraper needed a vehicle to traverse the web - a Chrome browser with specific configurations to keep it running smoothly.
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_experimental_option("detach", True)  # Optional: Detach Chrome for debugging

    # #### The scraper found the exact location of its ChromeDriver, a loyal companion that would help it on this adventure.
    chromedriver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../assets', 'chromedriver.exe')

    # Initialize the Chrome driver
    # #### With everything set, the scraper called upon ChromeDriver and got ready to begin the mission.
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # ### Our scraper's main goal was to collect information about bills in Canada.
    # It had to carefully navigate through pages, pick up pieces of data, and return with a full basket of information.

    # Function to scrape bill information
    # #### First, it defined a strategy - a function to gather all the bill details it could find on a given page.
    def scrape_bills_info(driver):
        # #### The scraper had to wait for the right elements to appear before collecting the information, ensuring no detail was missed.
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.bill"))
        )
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.progress-bar-wrapper'))
        )

        # Get the page source and parse it with BeautifulSoup
        # #### Once ready, it gathered all the HTML data and asked BeautifulSoup to help it read through.
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Initialize an empty list to hold the bill information
        bills_info = []

        # Find all bill card containers
        # #### The scraper discovered several bill cards, each containing valuable information.
        bill_cards = soup.find_all('div', class_='bill')

        # Loop through each bill card and extract information
        # #### For each card, it carefully extracted details such as the title, bill number, and progress.
        for card in bill_cards:
            bill_info = {}
            bill_info['href'] = "https://www.parl.ca" + card.find('a', class_='bill-tile-container')['href']
            bill_info['bill_number'] = card.find('h4', class_='bill-number').text.strip()
            bill_info['title'] = card.find('h5').text.strip()
            bill_info['current_status'] = card.find_all('dl')[0].find('dd').text.strip()
            bill_info['last_major_stage_completed'] = card.find_all('dl')[1].find('dd').text.strip()
            bill_info['parliament_session'] = card.find('div', class_='parliament-session').text.strip()

            # #### The scraper needed to understand if the bill was a House bill (C) or a Senate bill (S).
            is_c_bill = 'c-' in bill_info['href'].lower()

            # Process the progress bars
            # #### It then moved on to analyze the bill's progress, carefully examining the House and Senate readings.
            progress_bar_wrapper = card.find('div', class_='progress-bar-wrapper')
            if is_c_bill:
                house_progress = progress_bar_wrapper.find('div', class_='progress-bar-group first-group house')
                senate_progress = progress_bar_wrapper.find('div', class_='progress-bar-group second-group senate')
            else:
                senate_progress = progress_bar_wrapper.find('div', class_='progress-bar-group first-group senate')
                house_progress = progress_bar_wrapper.find('div', class_='progress-bar-group second-group house')

            royal_assent_progress = progress_bar_wrapper.find('div', class_='royal-assent-group')

            # Senate progress
            # #### The scraper documented the status of each reading in the Senate - whether it was completed or not.
            for reading, stage in [('first_reading', 'first-reading'), ('second_reading', 'second-reading'),
                                   ('third_reading', 'third-reading')]:
                if senate_progress and senate_progress.find('div', class_=stage):
                    bill_info['senate_' + reading] = 'Completed' if 'stage-completed' in \
                                                                    senate_progress.find('div', class_=stage)[
                                                                        'class'] else 'Not Completed'
                else:
                    bill_info['senate_' + reading] = 'Not Applicable'

            # House progress
            # #### Similarly, it checked the House progress for each reading.
            for reading, stage in [('first_reading', 'first-reading'), ('second_reading', 'second-reading'),
                                   ('third_reading', 'third-reading')]:
                if house_progress and house_progress.find('div', class_=stage):
                    bill_info['house_' + reading] = 'Completed' if 'stage-completed' in \
                                                                   house_progress.find('div', class_=stage)[
                                                                       'class'] else 'Not Completed'
                else:
                    bill_info['house_' + reading] = 'Not Applicable'

            # Royal Assent
            # #### The final step was to determine if the bill had received Royal Assent.
            if royal_assent_progress:
                royal_assent_div = royal_assent_progress.find('div', class_='royal-assent')
                bill_info['royal_assent'] = 'Completed' if royal_assent_div and 'stage-completed' in royal_assent_div[
                    'class'] else 'Not Completed'
            else:
                bill_info['royal_assent'] = 'Not Applicable'

            # #### Add the current timestamp to the bill information
            bill_info['last_updated_at'] = datetime.now().isoformat()

            # #### With all the gathered details, it added this bill's information to its collection.
            bills_info.append(bill_info)

        return bills_info

    try:
        # ### The adventure begins - the scraper visited the website, gathering information from page to page.

        # Define the URL
        url = "https://www.parl.ca/LegisInfo/en/bills?advancedview=true"

        # Navigate to the URL
        driver.get(url)
        time.sleep(5)  # Wait for the page to load

        # Initialize an empty list to hold all bill information
        all_bills_info = []

        # Loop to scrape information from each page
        # #### The scraper wasn't satisfied with just one page - it kept exploring the next pages until there were none left.
        while True:
            try:
                # Call the function to scrape bills information and append to the list
                current_page_bills_info = scrape_bills_info(driver)
                all_bills_info.extend(current_page_bills_info)

                # Scroll to the bottom of the page
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                # Click on the "Next" button using JavaScript
                next_button = driver.find_element(By.XPATH, '//a[contains(@aria-label, "Next page")]')
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(5)  # Wait for the next page to load

            except NoSuchElementException:
                # #### At last, the scraper realized there were no more pages to explore.
                print("No more pages available. Exiting...")
                break

        # ### After gathering all this valuable information, it was time for the scraper to store it safely.

        # Define the output file path
        output_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../storage', 'CanadaBills.json')

        # Load existing data if the JSON file exists
        if os.path.exists(output_file_path):
            with open(output_file_path, 'r') as json_file:
                try:
                    existing_data = json.load(json_file)
                    # Convert the list to a dictionary keyed by 'href' for easy updating
                    existing_data_dict = {bill['href']: bill for bill in existing_data}
                except json.JSONDecodeError:
                    print("Existing JSON file is empty or corrupted. Starting fresh.")
                    existing_data_dict = {}
        else:
            existing_data_dict = {}

        # Initialize counters for summary statistics
        total_scraped = len(all_bills_info)
        new_bills_added = 0
        existing_bills_changed = 0

        # Update the existing data with the newly scraped data
        for bill in all_bills_info:
            href = bill['href']
            if href in existing_data_dict:
                # Compare existing bill data with the new bill data
                existing_bill = existing_data_dict[href]
                # Define the fields to compare
                fields_to_compare = [
                    'bill_number',
                    'title',
                    'current_status',
                    'last_major_stage_completed',
                    'parliament_session',
                    'senate_first_reading',
                    'senate_second_reading',
                    'senate_third_reading',
                    'house_first_reading',
                    'house_second_reading',
                    'house_third_reading',
                    'royal_assent'
                ]

                # Check if any field has changed
                change_detected = False
                for field in fields_to_compare:
                    if existing_bill.get(field) != bill.get(field):
                        change_detected = True
                        break

                # Set the change_status based on whether a change was detected
                bill['change_status'] = change_detected

                if change_detected:
                    existing_bills_changed += 1

                # Update the bill information in the existing data
                existing_data_dict[href] = bill
            else:
                # New bill entry
                bill['change_status'] = True  # Since it's a new entry
                existing_data_dict[href] = bill
                new_bills_added += 1

        # Convert the dictionary back to a list
        updated_data = list(existing_data_dict.values())

        # Write the updated bill information to the JSON file
        with open(output_file_path, 'w') as json_file:
            json.dump(updated_data, json_file, indent=4)

        # ### And so, after completing its mission, our scraper closed its browser window and rested.

        # Print summary statistics
        print(f"Total bills scraped: {total_scraped}")
        print(f"New bills added: {new_bills_added}")
        print(f"Existing bills changed: {existing_bills_changed}")
        print(f"Scraped bill information has been written to {output_file_path}")

    except Exception as e:
        print(f"An error occurred during scraping: {e}")

    finally:
        # Close the browser window
        driver.quit()

if __name__ == "__main__":
    scrape_canada_bills()
