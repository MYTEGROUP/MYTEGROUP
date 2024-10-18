import json
import os
from flask import Flask, request, jsonify
from helpers.helper import load_json_data, thread_safe_operation

app = Flask(__name__)

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'storage', 'CanadaBillsEnhanced.json')

# Load bill data at startup for performance optimization
@thread_safe_operation
def get_bill_data():
    return load_json_data(DATA_PATH)

@app.route('/api/bills', methods=['GET'])
def get_bills():
    """
    Endpoint to fetch aggregated and filtered bill data for the dashboard.
    Supports filtering by status, sponsor, and topic.
    """
    status = request.args.get('status')
    sponsor = request.args.get('sponsor')
    topic = request.args.get('topic')

    bills = get_bill_data()

    # Apply filters based on query parameters
    if status:
        bills = [bill for bill in bills if bill.get('status') == status]
    if sponsor:
        bills = [bill for bill in bills if bill.get('sponsor') == sponsor]
    if topic:
        bills = [bill for bill in bills if topic.lower() in [t.lower() for t in bill.get('topics', [])]]

    # Aggregate data for visualization
    aggregated_data = {
        'total_bills': len(bills),
        'bills_by_status': {},
        'bills_by_sponsor': {},
        'bills_by_topic': {}
    }

    for bill in bills:
        # Aggregate by status
        bill_status = bill.get('status', 'Unknown')
        aggregated_data['bills_by_status'][bill_status] = aggregated_data['bills_by_status'].get(bill_status, 0) + 1

        # Aggregate by sponsor
        bill_sponsor = bill.get('sponsor', 'Unknown')
        aggregated_data['bills_by_sponsor'][bill_sponsor] = aggregated_data['bills_by_sponsor'].get(bill_sponsor, 0) + 1

        # Aggregate by topic
        for t in bill.get('topics', []):
            topic_lower = t.lower()
            aggregated_data['bills_by_topic'][topic_lower] = aggregated_data['bills_by_topic'].get(topic_lower, 0) + 1

    return jsonify(aggregated_data)

@app.route('/api/bills/summary', methods=['GET'])
def get_bills_summary():
    """
    Endpoint to fetch a summary of all active bills for the dashboard overview.
    """
    status = 'active'
    bills = get_bill_data()
    active_bills = [bill for bill in bills if bill.get('status') == status]

    summary = {
        'total_active_bills': len(active_bills),
        'active_bills_by_sponsor': {},
        'active_bills_by_topic': {}
    }

    for bill in active_bills:
        sponsor = bill.get('sponsor', 'Unknown')
        summary['active_bills_by_sponsor'][sponsor] = summary['active_bills_by_sponsor'].get(sponsor, 0) + 1

        for t in bill.get('topics', []):
            topic_lower = t.lower()
            summary['active_bills_by_topic'][topic_lower] = summary['active_bills_by_topic'].get(topic_lower, 0) + 1

    return jsonify(summary)

if __name__ == '__main__':
    app.run(debug=True)

# End of Backend/bill_dashboard.py