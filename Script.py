import concurrent.futures
import logging
import time
from itertools import count
import requests

# Configuration Variables
API_URL = "https://reqres.in/api/users?page=2"  # Replace with your API URL
MAX_THREADS = 100  # Maximum number of concurrent threads
LOOP_COUNT = 50  # Number of loops (set to float('inf') for infinite loops)
REQUEST_TYPE = "GET"  # HTTP method: GET, POST, PUT, PATCH, DELETE
SEND_PARAMS = False  # True if sending parameters, False otherwise
BODY_DATA = False  # True if sending body data
SEND_AUTH_TOKEN = False  # Set to True to include Bearer Auth Token in the request header
SEND_SXS_TOKEN = False  # Set to True to include SxSrf Token in the request header
SEND_ORIGIN = False  # Set to True to include Origin header in the request
PARAMS = {"key": "value"}  # Parameters to send if SEND_PARAMS is True
BODY_CONTENT = {
    "name": "morpheus"
}  # JSON body data to send if BODY_DATA is True
AUTH_TOKEN = "your_bearer_auth_token"  # Your Bearer Auth token
SXS_TOKEN = "your_sxsrf_token"  # Your SxSrf token
HEADERS = {"Content-Type": "application/json"}  # Basic headers, modify as needed
RAMP_UP_PERIOD = 1  # Ramp-up period in seconds
ORIGIN_URL = " "  # Origin URL (adjust as needed)

# Configure Logging
log_file_name = f"thread_{MAX_THREADS}_loop_{LOOP_COUNT}.log"
logging.basicConfig(
    filename=log_file_name,
    level=logging.INFO,
    format="%(asctime)s [Thread %(thread)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# Function to send a request
def send_request(thread_id):
    headers = HEADERS.copy()  # Copy headers to modify them per request

    # Add Bearer Auth Token if enabled
    if SEND_AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"

    # Add SxSrf Token if enabled
    if SEND_SXS_TOKEN:
        headers["Sxsrf"] = SXS_TOKEN

    # Add Origin header if enabled
    if SEND_ORIGIN:
        headers["Origin"] = ORIGIN_URL

    try:
        start_time = time.time()

        # Choose the HTTP method dynamically
        if SEND_PARAMS:
            response = getattr(requests, REQUEST_TYPE.lower())(
                API_URL,
                params=PARAMS if REQUEST_TYPE == "GET" else None,
                json=BODY_CONTENT if BODY_DATA else None,
                headers=headers,
            )
        else:
            response = getattr(requests, REQUEST_TYPE.lower())(
                API_URL,
                json=BODY_CONTENT if BODY_DATA else None,
                headers=headers,
            )

        end_time = time.time()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds

        # Log successful request
        response_text = response.text.strip()[:500]  # Limit response output to 500 characters
        logging.info(
            f"[Thread {thread_id}] Success - Execution Time: {execution_time:.2f} ms, "
            f"Status Code: {response.status_code}, Response: {response_text}"
        )
        print(f"[Thread {thread_id}] Response Code: {response.status_code}, Response: {response_text}")
        return response.status_code, execution_time, response_text

    except Exception as e:
        # Log failed request
        logging.error(f"[Thread {thread_id}] Failed - Error: {str(e)}")
        print(f"[Thread {thread_id}] Error: {str(e)}")
        return None, None, str(e)


# Function to calculate ramp-up sleep intervals
def get_ramp_up_interval():
    if RAMP_UP_PERIOD <= 0 or MAX_THREADS <= 1:
        return 0
    return RAMP_UP_PERIOD / (MAX_THREADS - 1)


# Load Testing Function
def perform_load_test():
    passed = 0
    failed = 0
    execution_times = []
    total_requests = 0

    print(f"Starting load test with ramp-up period of {RAMP_UP_PERIOD} seconds...")
    print(f"Max Threads: {MAX_THREADS}, Loop Count: {'Infinity' if LOOP_COUNT == float('inf') else LOOP_COUNT}")
    print(f"Logging results to: {log_file_name}")

    ramp_up_interval = get_ramp_up_interval()

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        loop = count(1) if LOOP_COUNT == float('inf') else range(LOOP_COUNT)
        futures = []

        for _ in loop:  # Iterate through loops
            # Submit all requests concurrently for this loop
            for thread_id in range(MAX_THREADS):
                futures.append(executor.submit(send_request, thread_id))
                total_requests += 1

            # Ramp-up logic: Gradually increase threads
            if ramp_up_interval > 0:
                time.sleep(ramp_up_interval)

            if LOOP_COUNT != float('inf') and total_requests >= MAX_THREADS * LOOP_COUNT:
                break

        for future in concurrent.futures.as_completed(futures):
            status_code, execution_time, _ = future.result()
            # Check for success status codes (200 and 201 are typically successful in API responses)
            if status_code in [200, 201] and execution_time is not None:
                passed += 1
                execution_times.append(execution_time)
            else:
                failed += 1

    # Calculate metrics only if there are valid execution times
    if execution_times:
        min_time = min(execution_times)
        max_time = max(execution_times)
        avg_time = sum(execution_times) / len(execution_times)
    else:
        min_time = max_time = avg_time = None

    error_percentage = (failed / total_requests) * 100 if total_requests > 0 else 0

    # Print results
    print("\n--- Load Test Results ---")
    print(f"API URL: {API_URL}")
    print(f"HTTP Method: {REQUEST_TYPE}")
    print(f"Max Threads: {MAX_THREADS}")
    print(f"Ramp-Up Period: {RAMP_UP_PERIOD} seconds")
    print(f"Loop Count: {'Infinity' if LOOP_COUNT == float('inf') else LOOP_COUNT}")
    print(f"Total Executions: {total_requests}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Error Percentage: {error_percentage:.2f}%")
    print(f"Min Execution Time: {min_time:.2f} ms" if min_time is not None else "Min Execution Time: N/A")
    print(f"Max Execution Time: {max_time:.2f} ms" if max_time is not None else "Max Execution Time: N/A")
    print(f"Average Execution Time: {avg_time:.2f} ms" if avg_time is not None else "Average Execution Time: N/A")

    # Log summary to the file
    logging.info("\n--- Load Test Results ---")
    logging.info(f"API URL: {API_URL}")
    logging.info(f"HTTP Method: {REQUEST_TYPE}")
    logging.info(f"Max Threads: {MAX_THREADS}")
    logging.info(f"Ramp-Up Period: {RAMP_UP_PERIOD} seconds")
    logging.info(f"Loop Count: {'Infinity' if LOOP_COUNT == float('inf') else LOOP_COUNT}")
    logging.info(f"Total Executions: {total_requests}")
    logging.info(f"Passed: {passed}")
    logging.info(f"Failed: {failed}")
    logging.info(f"Error Percentage: {error_percentage:.2f}%")
    logging.info(f"Min Execution Time: {min_time:.2f} ms" if min_time is not None else "Min Execution Time: N/A")
    logging.info(f"Max Execution Time: {max_time:.2f} ms" if max_time is not None else "Max Execution Time: N/A")
    logging.info(
        f"Average Execution Time: {avg_time:.2f} ms" if avg_time is not None else "Average Execution Time: N/A")


if __name__ == "__main__":
    perform_load_test()
