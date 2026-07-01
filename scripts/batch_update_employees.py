import sys
import pandas as pd
import requests

# --- CONFIGURATION ---
BASE_URL = "https://api.staging.odysseytracker.com/employees"
# Path pointing to your raw Excel file
EXCEL_FILE_PATH = "scripts/data.xlsx"

# Replace this with a valid admin/authorized user token
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInVzZXJfaWQiOjEsInJvbGVfaWQiOjM1LCJpc19zdXBlcl9hZG1pbiI6dHJ1ZSwiaWF0IjoxNzgyODU2NjU2LCJ0eXBlIjoiYWNjZXNzIn0.msozM1YdXCxcRCNQkJdbcJXz08luHX17m2e0kYIj7b0"
HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}


def get_existing_employees():
    """Fetch existing system records and return them as a list for matching."""
    print("Fetching current employee list from database...")
    try:
        response = requests.get(f"{BASE_URL}?limit=500", headers=HEADERS)
        if response.status_code != 200:
            print(f"❌ Failed to fetch employees. Status: {response.status_code}")
            sys.exit(1)
            
        res_json = response.json()
        if isinstance(res_json, dict) and "data" in res_json:
            inner_data = res_json["data"]
            if isinstance(inner_data, dict) and "data" in inner_data:
                return inner_data["data"]
                
        print("❌ Unexpected API response format structure.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error fetching existing directory: {e}")
        sys.exit(1)


def find_matching_employee(db_employees, file_email, file_first, file_last):
    """Finds a matching employee in the database by email and precise name checking."""
    file_email_clean = file_email.strip().lower()
    file_first_clean = file_first.strip().lower()
    file_last_clean = file_last.strip().lower()

    # Shared team emails list
    shared_emails = [
        "odyssey@alphagraniteaustin.com", 
        "install@alphagraniteaustin.com", 
        "templates@alphagraniteaustin.com", 
        "workshop@alphagraniteaustin.com"
    ]

    for emp in db_employees:
        db_email = str(emp.get("email", "")).strip().lower()
        db_first = str(emp.get("first_name", "")).strip().lower()
        db_last = str(emp.get("last_name", "")).strip().lower()

        if db_email == file_email_clean:
            if file_email_clean in shared_emails:
                # Require precise first name match for shared team accounts
                if file_first_clean == db_first or file_first_clean in db_first:
                    return emp["id"]
            else:
                return emp["id"]
    return None


def update_employee_ids():
    db_employees = get_existing_employees()
    print(f"Successfully cached {len(db_employees)} system records.")
    
    try:
        df = pd.read_excel(EXCEL_FILE_PATH, sheet_name="report", skiprows=1)

        success_count = 0
        match_failed_count = 0
        update_failed_count = 0

        print("\nStarting matching and update processing...\n")

        for index, row in df.iterrows():
            first_name = str(row.get("First Name", "")).strip()
            last_name = str(row.get("Last Name", "")).strip()
            email = str(row.get("Emails", "")).strip()
            
            raw_hcp_id = row.get("Employee Id", "")
            if pd.isna(raw_hcp_id):
                continue
                
            if isinstance(raw_hcp_id, float) and raw_hcp_id.is_integer():
                hcp_id = str(int(raw_hcp_id))
            else:
                hcp_id = str(raw_hcp_id).strip()

            if not first_name or first_name == "nan" or not email or email == "nan":
                continue

            system_id = find_matching_employee(db_employees, email, first_name, last_name)

            if not system_id:
                print(f"⚠️ No system match for {first_name} {last_name} ({email}) - Skipped.")
                match_failed_count += 1
                continue

            # CRITICAL: We pass ONLY hcp_employee_id to prevent hitting unsubmitted route fallbacks like 'None'
            payload = {
                "hcp_employee_id": hcp_id
            }

            update_url = f"{BASE_URL}/{system_id}"
            print(f"🔄 Updating {first_name} {last_name} (System ID: {system_id}) with correct HCP ID: {hcp_id}... ", end="")

            response = requests.put(update_url, headers=HEADERS, data=payload)

            if response.status_code in [200, 204]:
                print("✅ Success!")
                success_count += 1
            else:
                print(f"❌ Patch Failed! Code {response.status_code}")
                print(f"   Response: {response.text}")
                update_failed_count += 1

        print("\n" + "=" * 40)
        print("Batch updates complete.")
        print(f"Successfully updated: {success_count}")
        print(f"Skipped (No Match): {match_failed_count}")
        print(f"Failed Updates: {update_failed_count}")

    except FileNotFoundError:
        print(f"Error: The file '{EXCEL_FILE_PATH}' was not found.")
    except Exception as e:
        print(f"An unexpected error occurred during execution: {e}")


if __name__ == "__main__":
    if AUTH_TOKEN == "YOUR_BEARER_TOKEN_HERE":
        print("Please replace 'YOUR_BEARER_TOKEN_HERE' with a valid token.")
        sys.exit(1)

    update_employee_ids()