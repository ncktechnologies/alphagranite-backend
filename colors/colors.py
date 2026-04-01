import pandas as pd
from datetime import datetime

# Mappings from Sheet 2 column indices to the Stone Type IDs from Sheet 1
# Note: PC-DELLA TERRA (ID: 12) and SANDSTONE (ID: 18) are skipped as they have no colors listed.
COLUMN_TO_TYPE_ID = {
    0: 2,   # Caesarstone
    1: 11,  # PC-CAESARSTONE
    2: 1,   # Cambria
    3: 16,  # PentalQuartz
    4: 8,   # MSI-Q
    5: 9,   # Neolith
    6: 13,  # PC-PANORAMIC
    7: 14,  # PC-Porcelanosa
    8: 21,  # Silestone
    9: 15,  # PC-STRATUS
    10: 20, # Stratus Quartz
    11: 22, # Terrazzo
    12: 23, # Travertine
    13: 19, # Soapstone
    14: 17, # Quartzite
    15: 10, # Onyx
    16: 7,  # Marble
    17: 6,  # Limestone
    18: 5,  # Granite
    19: 3,  # Della Terra Quartz
    20: 4   # Dekton
}

def generate_color_sql(excel_file_path):
    # Read Sheet 2; header=0 assumes the first row contains the stone type headers
    df_colors = pd.read_excel(excel_file_path, sheet_name="Sheet2", header=0)
    
    sql_statements = []
    sql_statements.append("INSERT INTO stone_colors (stone_type_id, name, status_id, created_by, created_at) VALUES")
    
    values = []
    
    for col_idx, type_id in COLUMN_TO_TYPE_ID.items():
        # Extract the column, drop empty cells (NaN), convert to string, and trim whitespace
        colors = df_colors.iloc[:, col_idx].dropna().astype(str).str.strip().tolist()
        
        for color in colors:
            if not color:
                continue
            # Escape single quotes for SQL (e.g., "Crema D'Orcia" -> "Crema D''Orcia")
            safe_color = color.replace("'", "''")
            
            # Assuming status_id = 1 (Active) and created_by = 1 (Admin)
            values.append(f"({type_id}, '{safe_color}', 1, 1, CURRENT_TIMESTAMP)")
            
    # Join all value tuples with commas and cap off the query with a semicolon
    full_query = ",\n".join(values) + ";"
    sql_statements.append(full_query)
    
    # Write to an SQL file
    output_filename = "insert_stone_colors.sql"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(sql_statements))
        
    print(f"Success! Generated SQL for {len(values)} stone colors and saved to '{output_filename}'.")

if __name__ == "__main__":
    # Replace with your actual filename if different
    generate_color_sql("List of Stone Thickness & Types.xlsx")