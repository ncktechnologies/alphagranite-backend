import sys
import pandas as pd
import requests

# --- CONFIGURATION ---
URL = "https://api.staging.odysseytracker.com/employees"
EXCEL_FILE_PATH = "scripts/data.xlsx"

# Replace this with a valid admin/authorized user token
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInVzZXJfaWQiOjEsInJvbGVfaWQiOjM1LCJpc19zdXBlcl9hZG1pbiI6dHJ1ZSwiaWF0IjoxNzgyODU1NTU0LCJ0eXBlIjoiYWNjZXNzIn0.eQH7_SJETEDe6MItuuCuOu9Fw0cMdcO04_IDKSsXNxg"

# Exact mapping matching your database production IDs
DEPARTMENT_MAP = {
    "CAD": 1,
    "FABRICATION": 2,
    "INSTALL": 3,
    "OFFICE": 4,
    "SALES": 5,
    "TEMPLATE": 6,
    "WAREHOUSE": 7,
    # Fallback mapping for specific CSV exceptions
    "OWNER": 4, 
}

HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}


def upload_employees():
    try:
        # Read Excel, skipping the decorative title row
        df = pd.read_excel(EXCEL_FILE_PATH, sheet_name="report", skiprows=1)

        success_count = 0
        fail_count = 0

        print(f"Starting batch upload to {URL}...\n")

        for index, row in df.iterrows():
            first_name = str(row.get("First Name", "")).strip()
            last_name = str(row.get("Last Name", "")).strip()
            email = str(row.get("Emails", "")).strip()
            dept_name = str(row.get("Default Cost Center", "")).strip()
            hcp_employee_id = str(row.get("Employee Id", "")).strip()

            # Skip empty rows
            if not first_name or first_name == "nan":
                continue

            # Normalize to uppercase for accurate dictionary lookup
            dept_key = dept_name.upper()
            dept_id = DEPARTMENT_MAP.get(dept_key)

            if not dept_id:
                print(f"❌ Skipped {first_name} {last_name}: Unmapped department '{dept_name}'")
                fail_count += 1
                continue

            # Multipart/form-data payload structure
            payload = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "department": dept_id,
                "hcp_employee_id": hcp_employee_id,
            }

            print(f"[{hcp_employee_id}] Sending: {first_name} {last_name} -> DB Dept ID: {dept_id}... ", end="")

            # POST request
            response = requests.post(URL, headers=HEADERS, data=payload)

            if response.status_code in [200, 201]:
                print("✅ Success!")
                success_count += 1
            else:
                print(f"❌ Failed! Code {response.status_code}")
                print(f"   Response: {response.text}")
                fail_count += 1

        print("\n" + "=" * 40)
        print("Batch processing complete.")
        print(f"Successfully created: {success_count}")
        print(f"Failed: {fail_count}")

    except FileNotFoundError:
        print(f"Error: The file '{EXCEL_FILE_PATH}' was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    if AUTH_TOKEN == "YOUR_BEARER_TOKEN_HERE":
        print("Please replace 'YOUR_BEARER_TOKEN_HERE' with a valid token.")
        sys.exit(1)

    upload_employees()