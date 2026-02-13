# imports
import pandas as pd

# load data set into pandas dataframe
df = pd.read_csv("311_Service_Requests.csv")

# ALREADY EXPORTED SO NO NEEDED TO RUN
# extract unique service names and export to a txt file
# service_names = sorted(df["service_name"].dropna().unique())
# with open("service_names.txt", "w") as file:
#     for name in service_names:
#         file.write(f"{name}\n")

# ALREADY CHECKED SO NO NEEDED TO RUN
# check different types of statuses
# statuses = sorted(df["status_description"].dropna().unique())
# print(statuses)

# remove duplicate and to be deleted items
removable_statuses = ["Duplicate (Closed)", "Duplicate (Open)", "TO BE DELETED"]
print(len(df))
df = df[~df["status_description"].isin(removable_statuses)]
print(len(df))

# trim unnecessary columns
columns_to_drop = ["service_request_id", "source", "address", "comm_code",
                   "location_type", "longitude", "latitude", "point", "updated_date"]
df.drop(columns_to_drop, axis=1, inplace=True)

# convert dates to usable format and remove the time stamps
df["requested_date"] = pd.to_datetime(df["requested_date"], format="%Y/%m/%d %I:%M:%S %p").dt.date
df["closed_date"] = pd.to_datetime(df["closed_date"], format="%Y/%m/%d %I:%M:%S %p").dt.date

# I manually went through the list of service names to combine useful ones under relevant headings
# import the csv of service names into a pandas data frame
useful_service_names_df = pd.read_csv("useful_service_names.csv")

# trim unnecessary rows
print(len(df))
useful_service_names_list = useful_service_names_df.stack().tolist()
df = df[df["service_name"].isin(useful_service_names_list)]
print(len(df))

# make a category column in the data frame based on the columns in the useful names df
category = {}
for column in useful_service_names_df.columns:
    for value in useful_service_names_df[column].dropna():
        category[value] = column
df["category"] = df["service_name"].map(category)

# export csv from cleaned dataframe
# df.to_csv("311_clean_service_requests.csv")
