import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

### MAKE SURE TO MERGE THE DATA NOT APPEND THE DATA TO cANAFAbILLSeNHANCED.JSON - CURRENT YDOUBLE THE NUMBER OF BILLS.

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--start-maximized")
chrome_options.add_experimental_option("detach", True)

# Define the path to your new ChromeDriver location
chromedriver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../assets', 'chromedriver.exe')

# Initialize the Chrome driver
service = Service(chromedriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Function to enhance bill information
def enhance_bill_info(bill):
    driver.get(bill['href'])
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'attribute')))

    # Extract the sponsor
    try:
        sponsor_element = driver.find_element(By.XPATH, "//div[div[@class='label' and contains(text(),'Sponsor')]]/div[not(@class='label')]")
        bill['sponsor'] = sponsor_element.text
    except:
        bill['sponsor'] = 'Not Available'

    # Extract the bill type
    try:
        bill_type_element = driver.find_element(By.XPATH, "//div[div[@class='label' and contains(text(),'Bill type')]]/div[not(@class='label')]")
        bill['bill_type'] = bill_type_element.text
    except:
        bill['bill_type'] = 'Not Available'

    # Attempt to click the "Text of the bill" button
    try:
        WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.publication.btn.btn-primary')))
        text_button = driver.find_element(By.CSS_SELECTOR, 'a.publication.btn.btn-primary')

        # Click using JavaScript
        driver.execute_script("arguments[0].click();", text_button)

        # Wait for the text to be visible
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.TAG_NAME, 'body')))
        time.sleep(2)  # Wait a bit more for safety

        # Extract all visible text as the bill content
        bill_text = driver.find_element(By.TAG_NAME, 'body').text
        bill['bill_content'] = bill_text
    except TimeoutException:
        bill['bill_content'] = 'No Text Available Yet'

    # Extract the contact email
    try:
        contact_email_element = driver.find_element(By.XPATH, "//a[contains(@href, 'mailto:')]")
        bill['contact_email'] = contact_email_element.get_attribute('href').split(':')[1]
    except:
        bill['contact_email'] = 'Not Available'

    return bill

# Load the existing data
input_file_path = os.path.join('../../../storage', 'CanadaBills.json')
with open(input_file_path, 'r') as file:
    bills_data = json.load(file)

# Define the output file path
output_file_path = os.path.join('../../../storage', 'CanadaBillsEnhanced.json')

# Check if the enhanced file already exists, if not, create an empty list
if not os.path.exists(output_file_path):
    with open(output_file_path, 'w') as file:
        json.dump([], file)

# Load the current state of the enhanced file
with open(output_file_path, 'r') as file:
    enhanced_bills_data = json.load(file)

# Create a set of bill numbers from the enhanced data for quick lookup
enhanced_bill_numbers = {bill['bill_number'] for bill in enhanced_bills_data}

for bill in bills_data:
    # Check if the bill number is already in the enhanced data
    if bill['bill_number'] not in enhanced_bill_numbers:
        enhanced_bill = enhance_bill_info(bill)
        enhanced_bills_data.append(enhanced_bill)

        # Save the updated data back to the file after each successful enhancement
        with open(output_file_path, 'w') as file:
            json.dump(enhanced_bills_data, file, indent=4)

driver.quit()
