# imports
import pandas as pd
import os
import glob

# load data set into pandas dataframe
download_folder = os.path.join(os.path.expanduser("~"), "Downloads")
file_string = os.path.join(download_folder, "*311_Service_Requests*")
possible_files = glob.glob(file_string)
if len(possible_files) == 1:
    print("Importing CSV...")
    df = pd.read_csv(possible_files[0])
elif len(possible_files) > 1:
    for _, file in enumerate(possible_files, start=1):
        print(f"{_}. {file}")
    while True:
        try:
            choice = int(input("Select a file by entering a number: "))
            if 1 <= choice <= len(possible_files):
                print(f"You selected: {possible_files[choice - 1]}")
                print("Importing CSV...")
                df = pd.read_csv(possible_files[choice - 1])
                break
            else:
                print("Please enter a valid number")
        except ValueError:
            print("Please enter a valid number")
else: print("No valid file found")

# remove rows that contain "Inquiry" or "Request"
print("Removing inquiries...")
df = df[~df["service_name"].str.contains("Inquiry", na=False)]
print("Removing requests...")
df = df[~df["service_name"].str.contains("Request", na=False)]

# remove duplicate and to be deleted items
print("Removing duplicates...")
removable_statuses = ["Duplicate (Closed)", "Duplicate (Open)", "TO BE DELETED"]
df = df[~df["status_description"].isin(removable_statuses)]

# trim unnecessary columns
print("Removing address, location_type, point and updated_date columns...")
columns_to_drop = ["address", "location_type", "point", "updated_date"]
df.drop(columns_to_drop, axis=1, inplace=True)

# convert dates to usable format and remove the time stamps
print("Removing timestamps...")
df["requested_date"] = pd.to_datetime(df["requested_date"], format="%Y/%m/%d %I:%M:%S %p").dt.date
df["closed_date"] = pd.to_datetime(df["closed_date"], format="%Y/%m/%d %I:%M:%S %p").dt.date

# trim rows with blank community names, service name
print("Removing blank data...")
df = df[df["comm_name"].notna()]
df = df[df["service_name"].notna()]

# export csv from cleaned dataframe
print("Exporting cleansed CSV...")
df.to_csv(os.path.join(download_folder, "311_clean_service_requests.csv"), index=False)
print(f"Successful, your cleansed CSV has been exported to "
      f"{os.path.join(download_folder, "311_clean_service_requests.csv")}")
