import time
import logging
import json
from datetime import datetime, date
from app.services.chat_service import ask_question
from app.core.constants import DEFAULT_ORG_ID, DEFAULT_DATA_TYPE_ID, DEFAULT_REPORTED_DATA_END

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)

# Configure logging to see where time is spent
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

QUESTIONS = [
    "What is the average price of TUNA in Goody?",
    "Between 200 GRAM and 400 GRAM, which pack size is growing the most in 'CANNED MUSHROOMS' in goody?",
    "How is TIM HORTONS performing in INSTANT COFFEE volume across different retailers in Jeddah?",
    "What is the monthly trend of Goody’s Tuna sales over the last 12 months?",
    "What is Goody’s volume share in the TUNA category?",
    "Compare volume sales of COFIQUE, and TIM HORTONS in the INSTANT COFFEE category",
    "What are the top 5 brands by volume sales in the CANNED VEGETABLE category?",
    "Compare Goody’s volume sales in TUNA between Riyadh and Jeddah.",
    "What is the year-over-year growth in volume sales for COFIQUE in the INSTANT COFFEE category?",
    "What is Goody’s volume share in the 80 GRAM pack size within the TUNA category?"
]

def run_test_suite():
    print("="*80)
    print(f"FMCG CHAT API - INTEGRATION TEST SUITE")
    print(f"Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Defaults: Org={DEFAULT_ORG_ID}, DataType={DEFAULT_DATA_TYPE_ID}, Date={DEFAULT_REPORTED_DATA_END}")
    print("="*80)
    print("\nStarting execution of 10 questions...\n")

    results = []
    
    for i, question in enumerate(QUESTIONS, 1):
        print(f"\n[{i}/10] Question: {question}")
        start_time = time.time()
        
        try:
            # We use the full service layer to test SQL generation + Calculation
            response = ask_question(
                question=question,
                org_id=DEFAULT_ORG_ID,
                data_type_id=DEFAULT_DATA_TYPE_ID,
                reported_data_end=DEFAULT_REPORTED_DATA_END
            )
            
            duration = time.time() - start_time
            
            if "error" in response:
                results.append({
                    "id": i,
                    "question": question,
                    "status": "FAIL",
                    "metric": "ERROR",
                    "value": response.get("error"),
                    "time": f"{duration:.2f}s"
                })
                print(f"      Result: FAILED with error ({duration:.2f}s)")
                print(f"      Details: {response.get('details', 'No details provided')}")
                continue

            # Print the generated SQL
            num_sql = response.get("numerator_sql", "")
            denom_sql = response.get("denominator_sql", "")
            
            print(f"\n      --- GENERATED SQL ---")
            print(f"      Numerator SQL:\n{num_sql}")
            if denom_sql:
                print(f"\n      Denominator SQL:\n{denom_sql}")
            
            # Print calculated results
            calc_results = response.get("calculated_results", [])
            print(f"\n      --- CALCULATED RESULTS ---")
            print(f"      {json.dumps(calc_results, indent=2, default=json_serial)}")
            print(f"      --------------------------\n")
            
            # Extract data for the summary report
            if calc_results and len(calc_results) > 0:
                primary_result = calc_results[0]
                metric_label = primary_result.get("metric_label", "N/A")
                metric_value = primary_result.get("metric_value", "N/A")
                
                if isinstance(metric_value, (int, float)):
                    metric_value = f"{metric_value:,.2f}"
                
                results.append({
                    "id": i,
                    "question": question,
                    "status": "PASS",
                    "metric": metric_label,
                    "value": metric_value,
                    "time": f"{duration:.2f}s"
                })
            else:
                results.append({
                    "id": i,
                    "question": question,
                    "status": "EMPTY [WARN]",
                    "metric": "N/A",
                    "value": "No Data",
                    "time": f"{duration:.2f}s"
                })

        except Exception as e:
            duration = time.time() - start_time
            results.append({
                "id": i,
                "question": question,
                "status": "CRASH [FAIL]",
                "metric": "ERROR",
                "value": str(e)[:50] + "...",
                "time": f"{duration:.2f}s"
            })
            print(f"      Result: CRASHED with error ({duration:.2f}s)")

    # Print Final Summary Table
    print("\n" + "="*110)
    print(f"{'ID':<4} | {'Status':<8} | {'Time':<6} | {'Question'}")
    print("-" * 110)
    
    passes = 0
    for r in results:
        if "PASS" in r["status"]: passes += 1
        print(f"{r['id']:<4} | {r['status']:<8} | {r['time']:<6} | {r['question']}")
    
    print("="*110)
    print(f"SUMMARY: {passes}/{len(QUESTIONS)} Questions Returned Data Successfully")
    print("="*110 + "\n")

if __name__ == "__main__":
    run_test_suite()
