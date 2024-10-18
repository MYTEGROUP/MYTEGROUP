import os
import re
import json
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from datetime import datetime, timezone
from openaiconfig.openaiservice import generate_text  # Functional wrapper of OpenAI
from helpers.helper import load_json, save_json  # JSON helpers
from config import STORAGE_DIR

# ============================================================
# ==================== CONFIGURATION ========================
# ============================================================

# File names
ENHANCED_BILLS_FILE = 'CanadaBillsEnhanced.json'
OUTPUT_FILE = 'CanadaBillsEnhanced.json'  # Overwrite the existing file with enhanced data

# Initialize a lock for thread-safe operations
lock = Lock()

# Define JSON_STRUCTURE to ensure controlled data handling
JSON_STRUCTURE = {
    "href": str,
    "bill_number": str,
    "title": str,
    "current_status": str,
    "last_major_stage_completed": str,
    "parliament_session": str,
    "senate_first_reading": str,
    "senate_second_reading": str,
    "senate_third_reading": str,
    "house_first_reading": str,
    "house_second_reading": str,
    "house_third_reading": str,
    "royal_assent": str,
    "sponsor": str,
    "bill_type": str,
    "bill_content": str,
    "contact_email": str,
    # Enhanced Keys
    "summary": str,
    "bill_progress": dict,
    "sponsor_profile": dict,
    "committees": list,
    "amendments": list,
    "related_bills": list,
    "named_entities": list,
    "bill_impact": str,
    "debates": str,
    "public_engagement": str,
    "stakeholder_analysis": list,
    "future_projections": str,
    "ai_enhancement_date": str  # Timestamp for last enhancement
}

# Define Essential and Supplementary Keys
ESSENTIAL_KEYS = ['summary', 'bill_progress', 'sponsor_profile']
SUPPLEMENTARY_KEYS = [
    'committees', 'amendments', 'related_bills',
    'named_entities', 'bill_impact', 'debates',
    'public_engagement', 'stakeholder_analysis', 'future_projections'
]

# ============================================================
# ==================== HELPER FUNCTIONS =====================
# ============================================================

def clean_html_summary(raw_summary):
    """
    Cleans the raw HTML summary by removing any leading text and triple backticks.

    Args:
        raw_summary (str): The raw summary returned by the generate_text function.

    Returns:
        str: Cleaned HTML summary.
    """
    # Regex to capture content between ```html and ```
    html_block = re.search(r'```html\s*(.*?)\s*```', raw_summary, re.DOTALL | re.IGNORECASE)
    if html_block:
        return html_block.group(1).strip()

    # If no backticks, try to find the HTML content starting with <!DOCTYPE html>
    html_start = raw_summary.find('<!DOCTYPE html>')
    if html_start != -1:
        return raw_summary[html_start:].strip()

    # If neither pattern is found, return the raw summary (optional: handle differently)
    return raw_summary.strip()

# ============================================================
# ==================== WRAPPER FUNCTIONS ====================
# ============================================================

def generate_summary(bill_content):
    """
    Generates a concise summary of the bill content.

    Args:
        bill_content (str): The full content of the bill.

    Returns:
        dict: A dictionary containing the structured summary.
    """
    JSONSTRUCTURE = {
        "content": "",
        "format": "HTML",
        "generated_on": ""
    }

    system_message = "You are a legal assistant generating concise summaries for Canadian bills."
    assistant_message = (
        "Please create a clear and unbiased summary of the following bill. "
        "The summary should be concise, approximately 200 words, and highlight the key objectives and provisions."
    )

    user_prompt = f"Bill Content: {bill_content}\n\nPlease structure your summary as follows:\n{json.dumps(JSONSTRUCTURE, indent=4)}"

    raw_summary = generate_text(system_message, assistant_message, user_prompt)
    cleaned_summary = clean_html_summary(raw_summary)

    # Populate the JSONSTRUCTURE
    JSONSTRUCTURE["content"] = cleaned_summary
    JSONSTRUCTURE["generated_on"] = datetime.now(timezone.utc).isoformat()

    return JSONSTRUCTURE

def extract_named_entities(bill_content):
    """
    Extracts named entities from the bill content.

    Args:
        bill_content (str): The full content of the bill.

    Returns:
        dict: A dictionary containing the list of named entities.
    """
    JSONSTRUCTURE = {
        "entities": []
    }

    system_message = "You are an NLP model tasked with extracting named entities from Canadian legislative bills."
    assistant_message = (
        "Identify and list all named entities such as persons, organizations, locations, and legislative bodies mentioned in the following bill content."
    )

    user_prompt = f"Bill Content: {bill_content}\n\nPlease structure your named entities as follows:\n{json.dumps(JSONSTRUCTURE, indent=4)}"

    raw_entities = generate_text(system_message, assistant_message, user_prompt)
    entities = [entity.strip() for entity in raw_entities.split(',') if entity.strip()]

    # Populate the JSONSTRUCTURE
    JSONSTRUCTURE["entities"] = entities

    return JSONSTRUCTURE

def identify_committees(bill_content):
    """
    Identifies parliamentary committees involved with the bill.

    Args:
        bill_content (str): The full content of the bill.

    Returns:
        dict: A dictionary containing the list of committees.
    """
    JSONSTRUCTURE = {
        "committees": []
    }

    system_message = "You are an assistant identifying parliamentary committees involved with Canadian bills."
    assistant_message = (
        "From the following bill content, identify all parliamentary committees that have reviewed or are reviewing this bill."
    )

    user_prompt = f"Bill Content: {bill_content}\n\nPlease structure the committees as follows:\n{json.dumps(JSONSTRUCTURE, indent=4)}"

    raw_committees = generate_text(system_message, assistant_message, user_prompt)
    committees = [committee.strip() for committee in raw_committees.split(',') if committee.strip()]

    # Populate the JSONSTRUCTURE
    JSONSTRUCTURE["committees"] = committees

    return JSONSTRUCTURE

def analyze_bill_impact(bill_content):
    """
    Analyzes the potential impact of the bill.

    Args:
        bill_content (str): The full content of the bill.

    Returns:
        dict: A dictionary containing the analysis of social, economic, and legal impacts.
    """
    JSONSTRUCTURE = {
        "social": "",
        "economic": "",
        "legal": ""
    }

    system_message = "You are an analyst assessing the potential impact of Canadian legislative bills."
    assistant_message = (
        "Provide an analysis of the potential social, economic, and legal impacts of the following bill."
    )

    user_prompt = f"Bill Content: {bill_content}\n\nPlease structure your analysis as follows:\n{json.dumps(JSONSTRUCTURE, indent=4)}"

    raw_impact = generate_text(system_message, assistant_message, user_prompt)

    # Extract the impacts
    for key in JSONSTRUCTURE.keys():
        pattern = f"{key.capitalize()}:"
        match = re.search(rf"{pattern}\s*(.*?)(?={ '|'.join([k.capitalize() for k in JSONSTRUCTURE.keys() if k != key ]) }|$)", raw_impact, re.IGNORECASE | re.DOTALL)
        if match:
            JSONSTRUCTURE[key] = match.group(1).strip()

    return JSONSTRUCTURE

def extract_amendments(bill_content):
    """
    Extracts amendments made to the bill.

    Args:
        bill_content (str): The full content of the bill.

    Returns:
        dict: A dictionary containing the list of amendments.
    """
    JSONSTRUCTURE = {
        "amendments": []
    }

    system_message = "You are a legal assistant identifying amendments in Canadian bills."
    assistant_message = (
        "List all amendments made to the following bill, specifying the section numbers and nature of each amendment."
    )

    user_prompt = f"Bill Content: {bill_content}\n\nPlease structure your amendments as follows:\n{json.dumps(JSONSTRUCTURE, indent=4)}"

    raw_amendments = generate_text(system_message, assistant_message, user_prompt)
    amendments = [amendment.strip() for amendment in raw_amendments.split('\n') if amendment.strip()]

    # Populate the JSONSTRUCTURE
    JSONSTRUCTURE["amendments"] = amendments

    return JSONSTRUCTURE

def find_related_bills(bill_content):
    """
    Finds related bills referenced in the bill content.

    Args:
        bill_content (str): The full content of the bill.

    Returns:
        dict: A dictionary containing the list of related bills.
    """
    JSONSTRUCTURE = {
        "related_bills": []
    }

    system_message = "You are an assistant identifying related Canadian legislative bills."
    assistant_message = (
        "Identify and list any other bills or pieces of legislation that are related to or referenced in the following bill content."
    )

    user_prompt = f"Bill Content: {bill_content}\n\nPlease structure the related bills as follows:\n{json.dumps(JSONSTRUCTURE, indent=4)}"

    raw_related = generate_text(system_message, assistant_message, user_prompt)
    related_bills = [bill.strip() for bill in raw_related.split(',') if bill.strip()]

    # Populate the JSONSTRUCTURE
    JSONSTRUCTURE["related_bills"] = related_bills

    return JSONSTRUCTURE

def summarize_debates(bill_content):
    """
    Summarizes parliamentary debates related to the bill.

    Args:
        bill_content (str): The full content of the bill.

    Returns:
        dict: A dictionary containing the summary, key points, and outcomes of debates.
    """
    JSONSTRUCTURE = {
        "summary": "",
        "key_points": [],
        "outcomes": []
    }

    system_message = "You are an assistant summarizing parliamentary debates on Canadian bills."
    assistant_message = (
        "Summarize the key points and outcomes of parliamentary debates related to the following bill."
    )

    user_prompt = f"Bill Content: {bill_content}\n\nPlease structure your summary as follows:\n{json.dumps(JSONSTRUCTURE, indent=4)}"

    raw_debates = generate_text(system_message, assistant_message, user_prompt)

    # Extract the summaries
    for key in JSONSTRUCTURE.keys():
        pattern = f"{key.capitalize()}:"
        match = re.search(rf"{pattern}\s*(.*?)(?={ '|'.join([k.capitalize() for k in JSONSTRUCTURE.keys() if k != key ]) }|$)", raw_debates, re.IGNORECASE | re.DOTALL)
        if match:
            content = match.group(1).strip()
            if key in ["key_points", "outcomes"]:
                # Assuming these are bullet points
                JSONSTRUCTURE[key] = [point.strip('- ').strip() for point in content.split('\n') if point.strip()]
            else:
                JSONSTRUCTURE[key] = content

    return JSONSTRUCTURE

def analyze_public_engagement(bill_number):
    """
    Analyzes public engagement metrics related to the bill.

    Args:
        bill_number (str): The number of the bill.

    Returns:
        dict: A dictionary containing metrics and sentiments from public interactions.
    """
    JSONSTRUCTURE = {
        "metrics": {
            "social_media_mentions": 0,
            "engagement_rate": "",
            "public_comments": 0
        },
        "sentiments": {
            "positive": "",
            "neutral": "",
            "negative": ""
        },
        "media_coverage": {
            "articles_count": 0,
            "sentiment_analysis": {
                "positive": "",
                "neutral": "",
                "negative": ""
            }
        }
    }

    system_message = "You are an assistant analyzing public engagement data related to Canadian bills."
    assistant_message = (
        f"Provide metrics and sentiments based on public interactions, such as social media mentions and public comments, for bill number {bill_number}."
    )

    user_prompt = f"Bill Number: {bill_number}\n\nPlease structure your public engagement data as follows:\n{json.dumps(JSONSTRUCTURE, indent=4)}"

    raw_engagement = generate_text(system_message, assistant_message, user_prompt)

    # Extracting metrics and sentiments
    for key in JSONSTRUCTURE.keys():
        if key in ["metrics", "sentiments", "media_coverage"]:
            for sub_key in JSONSTRUCTURE[key].keys():
                if isinstance(JSONSTRUCTURE[key][sub_key], dict):
                    for sub_sub_key in JSONSTRUCTURE[key][sub_key].keys():
                        pattern = f"{sub_sub_key.replace('_', ' ').capitalize()}:"
                        match = re.search(rf"{pattern}\s*(.*?)(?={ '|'.join([k.replace('_', ' ').capitalize() for k in JSONSTRUCTURE[key][sub_key].keys() ]) }|$)", raw_engagement, re.IGNORECASE | re.DOTALL)
                        if match:
                            JSONSTRUCTURE[key][sub_key][sub_sub_key] = match.group(1).strip()
                else:
                    pattern = f"{sub_key.replace('_', ' ').capitalize()}:"
                    match = re.search(rf"{pattern}\s*(.*?)(?={ '|'.join([k.replace('_', ' ').capitalize() for k in JSONSTRUCTURE[key].keys() if k != sub_key ]) }|$)", raw_engagement, re.IGNORECASE | re.DOTALL)
                    if match:
                        value = match.group(1).strip()
                        if sub_key in ["social_media_mentions", "public_comments", "articles_count"]:
                            try:
                                JSONSTRUCTURE[key][sub_key] = int(re.findall(r'\d+', value)[0])
                            except (IndexError, ValueError):
                                JSONSTRUCTURE[key][sub_key] = 0
                        else:
                            JSONSTRUCTURE[key][sub_key] = value

    return JSONSTRUCTURE

def stakeholder_analysis(bill_content):
    """
    Identifies and categorizes stakeholders affected by the bill.

    Args:
        bill_content (str): The full content of the bill.

    Returns:
        dict: A dictionary containing the list of stakeholders.
    """
    JSONSTRUCTURE = {
        "stakeholders": []
    }

    system_message = "You are an analyst identifying stakeholders affected by Canadian bills."
    assistant_message = (
        "Identify and categorize key stakeholders impacted by the following bill content, including government bodies, private sectors, and public interest groups."
    )

    user_prompt = f"Bill Content: {bill_content}\n\nPlease structure your stakeholder analysis as follows:\n{json.dumps(JSONSTRUCTURE, indent=4)}"

    raw_stakeholders = generate_text(system_message, assistant_message, user_prompt)
    stakeholders = [stakeholder.strip() for stakeholder in raw_stakeholders.split(',') if stakeholder.strip()]

    # Populate the JSONSTRUCTURE
    JSONSTRUCTURE["stakeholders"] = stakeholders

    return JSONSTRUCTURE

def future_projections(bill_content):
    """
    Predicts potential future amendments or outcomes related to the bill.

    Args:
        bill_content (str): The full content of the bill.

    Returns:
        dict: A dictionary containing potential amendments and predicted outcomes.
    """
    JSONSTRUCTURE = {
        "potential_amendments": [],
        "predicted_outcomes": ""
    }

    system_message = "You are an assistant predicting future outcomes of Canadian legislative bills."
    assistant_message = (
        "Based on the following bill content, predict potential future amendments or outcomes related to this bill."
    )

    user_prompt = f"Bill Content: {bill_content}\n\nPlease structure your future projections as follows:\n{json.dumps(JSONSTRUCTURE, indent=4)}"

    raw_projections = generate_text(system_message, assistant_message, user_prompt)

    # Extracting potential amendments and predicted outcomes
    for key in JSONSTRUCTURE.keys():
        pattern = f"{key.replace('_', ' ').capitalize()}:"
        match = re.search(rf"{pattern}\s*(.*?)(?={ '|'.join([k.replace('_', ' ').capitalize() for k in JSONSTRUCTURE.keys() if k != key ]) }|$)", raw_projections, re.IGNORECASE | re.DOTALL)
        if match:
            content = match.group(1).strip()
            if key == "potential_amendments":
                # Assuming amendments are listed as bullet points
                JSONSTRUCTURE[key] = [amend.strip('- ').strip() for amend in content.split('\n') if amend.strip()]
            elif key == "predicted_outcomes":
                JSONSTRUCTURE[key] = content

    return JSONSTRUCTURE

# ============================================================
# ==================== WRAPPER MAPPING ======================
# ============================================================

# Mapping of keys to their respective wrapper functions
WRAPPER_FUNCTIONS = {
    'summary': generate_summary,
    'named_entities': extract_named_entities,
    'committees': identify_committees,
    'bill_impact': analyze_bill_impact,
    'amendments': extract_amendments,
    'related_bills': find_related_bills,
    'debates': summarize_debates,
    'public_engagement': analyze_public_engagement,
    'stakeholder_analysis': stakeholder_analysis,
    'future_projections': future_projections
}

# ============================================================
# ==================== PROCESSING FUNCTION ==================
# ============================================================

def process_single_bill(bill):
    """
    Processes a single bill to extract and enhance data using concurrent execution of wrapper functions.

    Args:
        bill (dict): The bill data.

    Returns:
        dict: Enhanced bill data.
    """
    enhanced_data = {}
    try:
        bill_number = bill.get('bill_number', 'Unknown')
        bill_content = bill.get('bill_content', '')
        bill_content_length = len(bill_content)

        # Filter bills with bill_content greater than 500 characters
        if bill_content_length <= 500:
            print(f"⚠️ Skipping Bill: {bill_number} due to insufficient bill content length ({bill_content_length} characters).")
            return None

        print(f"🔍 Processing Bill: {bill_number}...")

        # ------------------- Essential Keys -------------------
        # Extract bill progress information
        try:
            enhanced_data['bill_progress'] = {
                'current_status': bill.get('current_status', ''),
                'last_major_stage_completed': bill.get('last_major_stage_completed', ''),
                'senate_readings': {
                    'first_reading': bill.get('senate_first_reading', ''),
                    'second_reading': bill.get('senate_second_reading', ''),
                    'third_reading': bill.get('senate_third_reading', '')
                },
                'house_readings': {
                    'first_reading': bill.get('house_first_reading', ''),
                    'second_reading': bill.get('house_second_reading', ''),
                    'third_reading': bill.get('house_third_reading', '')
                },
                'royal_assent': bill.get('royal_assent', '')
            }
            print(f"✅ Bill progress extracted for Bill: {bill_number}")
        except Exception as e:
            print(f"❌ Error extracting bill progress for {bill_number}: {e}")
            enhanced_data['bill_progress'] = {}

        # Extract sponsor profile information
        try:
            enhanced_data['sponsor_profile'] = {
                'name': bill.get('sponsor', ''),
                'bill_type': bill.get('bill_type', ''),
                'contact_email': bill.get('contact_email', '')
            }
            print(f"✅ Sponsor profile extracted for Bill: {bill_number}")
        except Exception as e:
            print(f"❌ Error extracting sponsor profile for {bill_number}: {e}")
            enhanced_data['sponsor_profile'] = {}

        # ------------------- Concurrent Wrapper Execution -------------------
        with ThreadPoolExecutor(max_workers=len(WRAPPER_FUNCTIONS)) as executor:
            future_to_key = {}
            for key, func in WRAPPER_FUNCTIONS.items():
                if key == 'public_engagement':
                    future = executor.submit(func, bill_number)
                else:
                    future = executor.submit(func, bill_content)
                future_to_key[future] = key

            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    result = future.result()
                    enhanced_data[key] = result
                    print(f"✅ {key.replace('_', ' ').title()} processed for Bill: {bill_number}")
                except Exception as e:
                    print(f"❌ Error processing {key} for Bill {bill_number}: {e}")
                    enhanced_data[key] = {}

        # Add ai_enhancement_date
        enhanced_data['ai_enhancement_date'] = datetime.now(timezone.utc).isoformat()

        # ------------------- Prepare Enhanced Bill -------------------
        enhanced_bill = bill.copy()
        enhanced_bill.update(enhanced_data)

        print(f"🎉 Completed processing Bill: {bill_number}\n")
        return enhanced_bill

    except Exception as e:
        print(f"🚨 Unexpected error processing bill {bill.get('bill_number', 'Unknown')}: {e}\n")
        return None

# ============================================================
# ==================== MAIN PROCESSING ======================
# ============================================================

def process_bills():
    """
    Processes all bills in the ENHANCED_BILLS_FILE to extract additional data and enhance the JSON file.
    Utilizes multithreading for efficient processing.
    """
    try:
        # Load existing bills data
        bills_data = load_json(os.path.join(STORAGE_DIR, ENHANCED_BILLS_FILE))
        print(f"📂 Loaded {len(bills_data)} bills from {ENHANCED_BILLS_FILE}.")

        # Load existing enhanced bills or initialize an empty list
        if os.path.exists(os.path.join(STORAGE_DIR, OUTPUT_FILE)):
            enhanced_bills = load_json(os.path.join(STORAGE_DIR, OUTPUT_FILE))
            print(f"📂 Loaded {len(enhanced_bills)} enhanced bills from {OUTPUT_FILE}.")
        else:
            enhanced_bills = []
            print(f"📂 No existing {OUTPUT_FILE} found. Initializing new enhanced bills list.")

        # Filter bills that are not yet processed
        bills_to_process = [bill for bill in bills_data]

        print(f"🔍 Found {len(bills_to_process)} bills to process.\n")

        if not bills_to_process:
            print("✅ No new bills to process. Enhancement up-to-date.")
            return

        # Determine the number of workers based on CPU cores
        cpu_cores = multiprocessing.cpu_count()
        max_workers = cpu_cores * 2  # Adjust multiplier based on I/O vs CPU-bound tasks
        print(f"⚙️ Starting processing with {max_workers} threads...\n")

        # Initialize a ThreadPoolExecutor for processing bills
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all bills for processing
            future_to_bill = {executor.submit(process_single_bill, bill): bill for bill in bills_to_process}

            for future in as_completed(future_to_bill):
                bill = future_to_bill[future]
                try:
                    enhanced_bill = future.result()
                    if enhanced_bill:
                        with lock:
                            enhanced_bills.append(enhanced_bill)
                except Exception as exc:
                    print(f"🚨 {bill.get('bill_number', 'Unknown')} generated an exception: {exc}")

        # Save all enhanced bills at once to reduce I/O operations
        save_json(OUTPUT_FILE, enhanced_bills)
        print(f"\n💾 {OUTPUT_FILE} saved successfully.")
        print("\n🎉 All bills processed and enhanced successfully.")

    except Exception as e:
        print(f"🚨 Error in processing bills: {e}")

# ============================================================
# ==================== ENTRY POINT ==========================
# ============================================================

if __name__ == "__main__":
    process_bills()
