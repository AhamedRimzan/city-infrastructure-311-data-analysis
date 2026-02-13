# imports
import pandas as pd
from datetime import datetime
from tkinter import *
from tkinter import ttk
from tkinter import messagebox

# load data set into pandas dataframe
df = pd.read_csv("311_Service_Requests.csv")

# trim unnecessary columns
columns_to_drop = ["service_request_id", "source", "address", "comm_code",
                   "location_type", "longitude", "latitude", "point", "updated_date"]
df.drop(columns_to_drop, axis=1, inplace=True)

# extract years
years = df["requested_date"].str[:4].unique()
years = sorted([str(year) for year in years])

# convert dates to usable format and remove the time stamps
df["requested_date"] = pd.to_datetime(df["requested_date"], format="%Y/%m/%d %I:%M:%S %p")
df["closed_date"] = pd.to_datetime(df["closed_date"], format="%Y/%m/%d %I:%M:%S %p")

# extract list of community names
comm_names = df["comm_name"].unique()
comm_names = sorted([str(comm) for comm in comm_names])

# extract list of service names
service_names = df["service_name"].unique()
service_names = sorted([str(service) for service in service_names])

# extract list of agency names
agencies = df["agency_responsible"].unique()
agencies = sorted([str(agency) for agency in agencies])

# create a list of months and days
MONTHS = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
DAYS = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16",
        "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31"]

# I manually went through the list of service names to combine useful ones under relevant headings
# import the csv of service names into a pandas data frame
useful_service_names_df = pd.read_csv("useful_service_names.csv")

# trim unnecessary rows
# print(len(df))
# useful_service_names_list = useful_service_names_df.stack().tolist()
# df = df[df["service_name"].isin(useful_service_names_list)]
# print(len(df))

# make a list of the heading names in data frame to be used in tkinter menu
useful_service_groups = useful_service_names_df.columns.to_list()

# a function to search dataset for user entered parameters
def look_up():
    # create a dictionary of parameters based on what is entered in the tkinter fields
    params = {}
    # check that a community was entered or else don't use that parameter
    if comm_entry.get(): params["comm_name"] = comm_entry.get()
    else: params["comm"] = None
    # check that a service was entered or else don't use that parameter
    if service_entry.get(): params["service_name"] = useful_service_names_df[service_entry.get()].tolist()
    else: params["service"] = None
    # call the create_dates function to create the date parameters
    params["requested_date"] = create_dates()

    # remove all unused parameters
    mask_params = {}
    for key, value in params.items():
        if value is not None:
            mask_params[key] = value

    # print the mask to show what is being searched
    print(mask_params)

    # call the count function and pass in the mask parameters
    # the function returns the number of rows in the datat set that meet the parameters passed in
    request_count = count(mask_params)

    # call the completion_times function to calculate the average, shortest and longest times to complete issues
    # function returns a tuple with 3 values - [0] = median, [1] = shortest, [2] = longest
    completion_times = time_to_close()

    # display searched info in a message box
    messagebox.showinfo(title=comm_entry.get(), message=f"There has been {request_count} requests for "
                                                        f"{service_entry.get()} services in {comm_entry.get()}. "
                                                        f"With an average completion time of {completion_times[0]} days, "
                                                        f"quickest time of {completion_times[1]} days, and "
                                                        f"the longest time of {completion_times[2]} days.")

# function that returns the number of rows in the datat set that meet the parameters passed in
def count(mask_params):
    # creates a pandas series with the same number of items as there are rows in the data frame and sets them all to true
    mask = pd.Series(True, index=df.index)

    # for loop removes items in series for each row in data frame that don't meet parameters
    for column, value in mask_params.items():
        if column in df.columns:
            # first it removes all items not in the list of service names
            if isinstance(value, (list, set)):
                mask &= df[column].isin(value)
            # next it removes all items not between the entered dates
            elif isinstance(value, tuple) and len(value) == 2:
                start_date, end_date = value
                mask &= pd.to_datetime(df[column]).between(pd.to_datetime(start_date), pd.to_datetime(end_date))
            # last it removes items that don't contain the community name
            else: mask &= df[column].eq(value)

    # returns the number of items left in mask after removing ones not in parameters
    return mask.sum()

# a function to calculate the average, shortest and longest times to complete issues
# returns a tuple with 3 values - [0] = median, [1] = shortest, [2] = longest
def time_to_close():
    # creates a pandas series with the same number of items as there are rows in the data frame and sets them all to true
    mask = pd.Series(True, index=df.index)

    #
    if comm_entry.get():
        mask &= df["comm_name"].eq(comm_entry.get())
        print(df)

    mask &= df["status_description"].eq("Closed")

    filtered_df = df.loc[mask, ["requested_date", "closed_date"]]
    filtered_df["days_to_close"] = (df["closed_date"] - df["requested_date"]).dt.days
    print(filtered_df["days_to_close"])
    print(filtered_df["days_to_close"].value_counts().sort_index())

    return (filtered_df["days_to_close"].median(),
            filtered_df["days_to_close"].min(),
            filtered_df["days_to_close"].max())

# function to clear tkinter fields
def clear_fields():
    comm_entry.set("")
    service_entry.set("")
    start_year_entry.set("")
    start_month_entry.set("")
    start_day_entry.set("")
    end_year_entry.set("")
    end_month_entry.set("")
    end_day_entry.set("")


def create_dates():

    if not start_year_entry.get():
        return (pd.to_datetime("2000/01/01", format="%Y/%m/%d"),
                pd.to_datetime("2050/12/31", format="%Y/%m/%d"))

    else:
        start_date = f"{start_year_entry.get()}"
        if start_month_entry.get():
            start_date += f"/{start_month_entry.get()}"
            if start_day_entry.get():
                start_date += f"/{start_day_entry.get()}"
            else: start_date += "/01"
        else: start_date += "/01/01"
        if not end_year_entry.get():
            return (pd.to_datetime(start_date, format="%Y/%m/%d"),
                    pd.to_datetime("2050/12/31", format="%Y/%m/%d"))
        else:
            end_date = f"{end_year_entry.get()}"
            if end_month_entry.get():
                end_date += f"/{end_month_entry.get()}"
                if end_day_entry.get():
                    end_date += f"/{end_day_entry.get()}"
                else: end_date += "/31"
            else: end_date += "/12/31"
            return (pd.to_datetime(start_date, format="%Y/%m/%d"),
                    pd.to_datetime(end_date, format="%Y/%m/%d"))

# tkinter window for user to select parameters to search for in dataset
window = Tk()
window.title("311 Service Requests")
window.config(padx= 50, pady= 50)

# Labels
comm_label = Label(text= "Community:", width= 18)
comm_label.grid(row= 2, column= 1)
service_label = Label(text= "Service:")
service_label.grid(row= 3, column= 1)
start_date_label = Label(text= "Start date (YYYY/MM/DD):")
start_date_label.grid(row= 4, column= 1)
end_date_label = Label(text= "End date (YYYY/MM/DD):")
end_date_label.grid(row= 5, column= 1)

# Entries
comm_entry = ttk.Combobox(window, values=comm_names, state="readonly", width= 29)
comm_entry.grid(row= 2, column= 2, columnspan= 3)
service_entry = ttk.Combobox(window, values=useful_service_groups, state="readonly", width= 29)
service_entry.grid(row= 3, column= 2, columnspan= 3)
start_year_entry = ttk.Combobox(window, values=years, state="readonly", width= 8)
start_year_entry.grid(row= 4, column= 2)
start_month_entry = ttk.Combobox(window, values=MONTHS, width= 8)
start_month_entry.grid(row= 4, column= 3)
start_day_entry = ttk.Combobox(window, values=DAYS, width= 8)
start_day_entry.grid(row= 4, column= 4)
end_year_entry = ttk.Combobox(window, values=years, state="readonly", width= 8)
end_year_entry.grid(row= 5, column= 2)
end_month_entry = ttk.Combobox(window, values=MONTHS, width= 8)
end_month_entry.grid(row= 5, column= 3)
end_day_entry = ttk.Combobox(window, values=DAYS, width= 8)
end_day_entry.grid(row= 5, column= 4)

# Buttons
clear_button = Button(text= "Clear", width= 14, command= clear_fields)
clear_button.grid(row= 6, column= 1, columnspan= 1)
lookup_button = Button(text= "Look up", width= 29, command= look_up)
lookup_button.grid(row= 6, column= 2, columnspan= 3)




window.mainloop()

