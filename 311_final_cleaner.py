# imports
import pandas as pd
pd.set_option('display.max_columns', None)
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

# create a csv with a summary of the input dataset
input_summary_df = pd.DataFrame({"column name": df.columns,
                           "input unique values": df.nunique(dropna=True).values,
                           "input null values": df.isna().sum().values,
                           "input data type": df.dtypes.astype(str).values})

# print info on dataset
print("This dataset contains: ")
print(f"{len(df.columns)} columns")
print(f"{len(df)} rows")
print(input_summary_df)

# remove rows that contain "Inquiry" or "Request"
print("Removing inquiries...")
df = df[~df["service_name"].str.contains("Inquiry", na=False)]
print("Removing requests...")
df = df[~df["service_name"].str.contains("Request", na=False)]

# remove duplicate and to be deleted items
print("Removing duplicates...")
removable_statuses = ["Duplicate (Closed)", "Duplicate (Open)", "TO BE DELETED"]
df = df[~df["status_description"].isin(removable_statuses)]

# remove unnecessary columns
print("Removing address, location_type, point and updated_date columns...")
columns_to_drop = ["address", "location_type", "point", "updated_date"]
df.drop(columns_to_drop, axis=1, inplace=True)

# convert dates to usable format and remove the time stamps
print("Removing timestamps...")
df["requested_date"] = pd.to_datetime(df["requested_date"], format="%Y/%m/%d %I:%M:%S %p").dt.date
df["closed_date"] = pd.to_datetime(df["closed_date"], format="%Y/%m/%d %I:%M:%S %p").dt.date

# remove rows with blank community names, service name
print("Removing some blank data...")
df = df[df["comm_name"].notna()]
df = df[df["service_name"].notna()]

# fill in blanks in comm_code and long/lat using values from other rows with the same comm_name
# fill in blanks in agency_responsible using values from other rows with the same service_name
print("Filling other blank data...")
df["comm_code"] = df["comm_code"].fillna(df.groupby("comm_name")["comm_code"].transform("first"))
df["longitude"] = df["longitude"].fillna(df.groupby("comm_name")["longitude"].transform("first"))
df["latitude"] = df["latitude"].fillna(df.groupby("comm_name")["latitude"].transform("first"))
df["agency_responsible"] = (df["agency_responsible"]
                            .fillna(df.groupby("service_name")["agency_responsible"].transform("first")))
agency_free_to_keep = ["CPI - Water and Sewer Main Condition Inquiries", "CPI - Bridge - Tunnel - Underpass Concern"]
mask = df["service_name"].isin(agency_free_to_keep) & df["agency_responsible"].isna()
df.loc[mask, "agency_responsible"] = "Unknown"

# remove all remaining blanks except closed_dates that are still open
print("Removing more blank data...")
df = df[(df["status_description"] == "Open") | ~df.isna().any(axis=1)]

# add to the summary csv with a summary of the output dataset
output_summary_df = pd.DataFrame({"column name": df.columns,
                           "output unique values": df.nunique(dropna=True).values,
                           "output null values": df.isna().sum().values,
                           "output data type": df.dtypes.astype(str).values})

# print info for exported file
print("This exported dataset contains: ")
print(f"{len(df.columns)} columns")
print(f"{len(df)} rows")
print(output_summary_df)

# export a summary csv
summary_df = pd.merge(input_summary_df, output_summary_df, on="column name", how="left")
summary_df = summary_df[["column name", "input unique values", "output unique values", "input null values",
                         "output null values", "input data type", "output data type"]]
summary_df.to_csv(os.path.join(download_folder, "311_service_requests_summary.csv"), index=False)

# export csv from cleaned dataframe
print("Exporting cleansed CSV...")
df.to_csv(os.path.join(download_folder, "311_clean_service_requests.csv"), index=False)
print(f"Successful, your cleansed CSV and summary CSV have been exported to \n "
      f"{os.path.join(download_folder, "311_clean_service_requests.csv")} and \n"
      f"{os.path.join(download_folder, "311_service_requests_summary.csv")}")
