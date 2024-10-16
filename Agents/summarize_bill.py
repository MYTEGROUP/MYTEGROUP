# Agents/summarize_bill.py

import os
from threading import Thread
from openaiconfig.openaiservice import generate_text  # Import generate_text function
from helpers.helper import load_json, save_json  # Import JSON helpers
from config import STORAGE_DIR

# File names
ENHANCED_BILLS_FILE = 'CanadaBillsEnhanced.json'
SUMMARIZED_BILLS_FILE = 'SummarizedBills.json'

# Generate structured HTML summary for each bill
def generate_html_summary(bill):
    system_message = "You are a legal assistant generating HTML summaries for Canadian bills."
    assistant_message = ("Please create a structured HTML summary with headers, paragraphs, bold text, and proper links. "
                         "You must respond only with the HTML strcuture - do not use descriptions before or after the html snipper. "
                         "Do not use ''' in your reponse either.")

    user_prompt = (
        f"Summarize the following bill with structured HTML:\n"
        f"Title: {bill['title']}\n"
        f"Bill Number: {bill['bill_number']}\n"
        f"Current Status: {bill['current_status']}\n"
        f"Last Major Stage Completed: {bill['last_major_stage_completed']}\n"
        f"Parliament Session: {bill['parliament_session']}\n"
        f"Senate Readings: First - {bill['senate_first_reading']}, Second - {bill['senate_second_reading']}, "
        f"Third - {bill['senate_third_reading']}\n"
        f"House Readings: First - {bill['house_first_reading']}, Second - {bill['house_second_reading']}, "
        f"Third - {bill['house_third_reading']}\n"
        f"Royal Assent: {bill['royal_assent']}\n"
        f"Sponsor: {bill['sponsor']}\n"
        f"Bill Type: {bill['bill_type']}\n"
        f"Bill Content: {bill['bill_content'][:1000]}... (truncated)\n"
        f"Contact Email: {bill['contact_email']}\n"
    )

    html_summary = generate_text(system_message, assistant_message, user_prompt)
    return html_summary

# Process a single bill and store the summary
def process_single_bill(bill, summarized_bills):
    print(f"Processing Bill: {bill['bill_number']}...")
    html_summary = generate_html_summary(bill)

    summarized_bills.append({
        "bill_number": bill['bill_number'],
        "bill_summary": html_summary
    })

    # Save the updated summaries
    save_json(SUMMARIZED_BILLS_FILE, summarized_bills)

# Main function to process all bills using threads
def process_bills():
    bills_data = load_json(ENHANCED_BILLS_FILE)

    # Load existing summaries or initialize an empty list
    if os.path.exists(os.path.join(STORAGE_DIR, SUMMARIZED_BILLS_FILE)):
        summarized_bills = load_json(SUMMARIZED_BILLS_FILE)
    else:
        summarized_bills = []

    summarized_bill_numbers = {bill['bill_number'] for bill in summarized_bills}
    threads = []

    for bill in bills_data:
        if bill['bill_number'] not in summarized_bill_numbers:
            thread = Thread(target=process_single_bill, args=(bill, summarized_bills))
            threads.append(thread)
            thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print("All bills processed and summarized.")

# Entry point
if __name__ == "__main__":
    process_bills()
