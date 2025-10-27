import os
import pandas as pd

base_path = "../data/mens"
target_sheets = ["Settings", "Shots", "Points", "Games", "Sets", "Stats"]
def create_combined():
    """
        For each player in data/mens, creates a combined .xlsx of all their matches.
        Prints in terminal which matches + tabs have been analyzed.
    """
    for player in os.listdir(base_path):
        player_folder = os.path.join(base_path, player)
        if os.path.isdir(player_folder):
            combined_sheets = {sheet: [] for sheet in target_sheets}

            # Collect data from each file
            for file in os.listdir(player_folder):
                file_path = os.path.join(player_folder, file)
                missing = []
                combined = []
                empty = []
                if file.endswith(".xlsx") and file != "combined.xlsx":
                    try:
                        print(f"Reading {file_path}...")  # Debugging
                        xls = pd.read_excel(file_path, sheet_name=None)
                        for sheet in target_sheets:
                            if sheet in xls:
                                df = xls[sheet]
                                if not df.empty:  # Check if the sheet has any data
                                    #print(f"Adding data from {file} - {sheet}")  # Debugging
                                    df['__source_file__'] = file  # Optional: source file column
                                    combined_sheets[sheet].append(df)
                                    combined.append(sheet)
                                else:
                                    empty.append(sheet)
                                    #print(f"Sheet {sheet} in {file} is empty")  # Debugging
                            else:
                                missing.append(sheet)
                                #print(f"Sheet {sheet} missing in {file}")  # Debugging
                    except Exception as e:
                        print(f"⚠️ Error with {file_path}: {e}")
                    print('------------------------------------------------------------------------')
                    print(f'Successfully accessed {file}')
                    print(f'Missing: {missing}, Empty: {empty}, Combined: {combined}')
                    print('------------------------------------------------------------------------')

            # Filter out empty lists for each sheet
            sheets_to_write = {
                sheet: pd.concat(dfs, ignore_index=True)
                for sheet, dfs in combined_sheets.items()
                if dfs  # Only include sheets with actual data
            }

            # Only write if there's at least one sheet with data
            if sheets_to_write:
                output_file = os.path.join(player_folder, "combined.xlsx")
                with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                    for sheet, df in sheets_to_write.items():
                        df.to_excel(writer, sheet_name=sheet, index=False)
                print(f"✅ Created combined.xlsx for {player} with sheets: {list(sheets_to_write.keys())}")
            else:
                print(f"⚠️ No valid data found for {player}, skipping combined.xlsx")


create_combined()
