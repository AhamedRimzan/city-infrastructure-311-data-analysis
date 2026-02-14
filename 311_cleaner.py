# imports
import pandas as pd

# load data set into pandas dataframe
df = pd.read_csv("311_Service_Requests.csv")

# !! ALREADY EXPORTED SO NO NEEDED TO RUN
# extract unique service names and export to a txt file
# service_names = sorted(df["service_name"].dropna().unique())
# with open("service_names.txt", "w") as file:
#     for name in service_names:
#         file.write(f"{name}\n")

# !! ALREADY CHECKED SO NO NEEDED TO RUN
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
                   "location_type", "point", "updated_date"]
df.drop(columns_to_drop, axis=1, inplace=True)

# convert dates to usable format and remove the time stamps
df["requested_date"] = pd.to_datetime(df["requested_date"], format="%Y/%m/%d %I:%M:%S %p").dt.date
df["closed_date"] = pd.to_datetime(df["closed_date"], format="%Y/%m/%d %I:%M:%S %p").dt.date

# !! LONGITUDE AND LATITUDE VALUES ARE FLOATS NO NEED TO CHANGE
# check data type for longitude and latitude
# print(df["longitude"].apply(type).value_counts())
# print(df["latitude"].apply(type).value_counts())

# I manually went through the list of service names to combine useful ones under relevant headings
# import the csv of service names into a pandas data frame
useful_service_names_df = pd.read_csv("useful_service_names.csv")

# trim unnecessary rows
print(len(df))
useful_service_names_list = useful_service_names_df.stack().tolist()
df = df[df["service_name"].isin(useful_service_names_list)]
print(len(df))

# check each column for blanks
for column in df.columns:
    blanks = (df[column].isna()).sum()
    print(f"{column}: {blanks}")
# requested_date: 0
# closed_date: 13992

# ?? WHAT VALUES TO PUT IN CLOSED DATE? THESE ARE STILL VALID DATA POINTS THEY JUST AREN'T CLOSED YET
# ?? JUST IN MY SELECTION SO FAR OF 1734023 SERVICE REQUESTS 13992 ARE STILL OPEN, THAT'S .8% -- SMALL ENOUGH TO IGNORE?

# status_description: 0
# service_name: 0
# agency_responsible: 0
# comm_name: 2038
# longitude: 2078
# latitude: 2078

# trim rows with blank community names
df = df[df["comm_name"].notna()]
# checking if blank long/lat have community names
# for column in df.columns:
#     blanks = (df[column].isna()).sum()
#     print(f"{column}: {blanks}")
# blank_lat_long = (df["longitude"].isna())
# df[blank_lat_long].to_csv("blank_lat_long.csv")

# ?? ALL BLANK COMMUNITY NAMES ALSO HAD NO LONG/LAT
# ?? THE REMAINING 40 BLANK LONG/LAT HAVE COMMUNITY NAMES SO MAYBE STILL USEFUL?

# checking to see if the long/lat is a specific coordinate or just the coordinate for the community
# comm_coordinates_df = df[["comm_name", "longitude", "latitude"]].drop_duplicates().reset_index(drop=True)
# comm_coordinates_df = comm_coordinates_df.sort_values(by="comm_name").reset_index(drop=True)
# comm_coordinates_df.to_csv("comm_coordinates.csv")

# ?? THERE ARE ~3-7 UNIQUE COORDINATES PER COMMUNITY
# ?? MAYBE RANDOMLY CHOOSE ONE OF THE COORDINATES TO ADD TO BLANK LONG/LAT?

# make a category column in the data frame based on the columns in the useful names df
category = {}
for column in useful_service_names_df.columns:
    for value in useful_service_names_df[column].dropna():
        category[value] = column
df["category"] = df["service_name"].map(category)

# export csv from cleaned dataframe
# df.to_csv("311_clean_service_requests.csv")
