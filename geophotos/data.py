# -*- coding: utf-8 -*-

"""
geophotos.gather
~~~~~~~~~~~~~~~~~

"""

import csv
import json
from datetime import datetime

import pandas as pd


def coordinates_from_csv(filepath, latitude_column, longitude_column,
                         delimiter=','):
    '''Takes a path to a data file, and with it, pulls out the
    specified latitude and longitude columns. This data is then
    returned as a list of tuples.
    
    Args:
        filepath (str):
            Path to the data/csv file.
        latitude_column (int):
            Column of the data file that holds latitude information.
        longitude_column (int):
            Column of the data file that holds longitude information.
    
    Kwargs:
        delimiter (str) --> ',':
            The delimiter that the csv file values are split by.

    Returns:
        A list of tuples which contain coordinate information in the
        form of: (latitude, longitude).
    '''

    # Read the data file into a pandas dataframe
    data = pd.read_csv(filepath, delimiter=delimiter)
    # Grab the specified columns and return as a list of tuples
    latitudes = data.iloc[:, latitude_column-1]
    longitudes = data.iloc[:, longitude_column-1]
    return list(zip(latitudes, longitudes))


def csv_from_google_takeout_json(filepath, destination=None):
    """Converts the information stored in a Google Takeout JSON file to
    a csv file with three columns: timestamp, latitude, and longitude.
    
    Args:
        filepath (str):
            The location of the Google Takeout JSON file.

    Kwargs:
        destination (str) --> None:
            Where to save the output csv file. If no filepath is
            specified, a list of coordinates will be returned.
    """

    # Load the json file and parse the location information
    with open(filepath, 'r') as takeout_json:
        data = json.load(takeout_json)
    locations = data['locations']

    # Iteratate through each location to get coordinate information
    information = []
    for _, location in enumerate(locations):
        # Convert time in milliseconds to seconds, then to a UTC timestamp
        seconds = int(location['timestampMs']) / 1000
        timestamp = datetime.utcfromtimestamp(seconds)
        # Convert the latitude and longitudes to a readable format
        latitude = float(location['latitudeE7']) / 10e7
        longitude = float(location['longitudeE7']) / 10e7
        # Write the coordinates to the information list
        row = [latitude, longitude]
        if destination:
            # If saving to a file, include a timestamp column
            row.insert(0, timestamp)
        information.append(tuple(row))

    if destination:
        # If a filepath was specified, instantiate the csv writer
        with open(destination, 'w') as output:
            writer = csv.writer(output, delimiter=',')
            # Write a header row to the csv file
            writer.writerow(['timestamp', 'latitude', 'longitude'])
            # Write the rest of the information to the csv file
            writer.writerows(information)
    else:
        # Otherwise, return the information list
        return information


if __name__ == '__main__':
    data = csv_from_google_takeout_json(
        r"/Users/jake/OneDrive/Python/_Miscellaneous/Google Location History/Early 2020/Location History.json",
        r"/Users/jake/OneDrive/Python/_Miscellaneous/Google Location History/Early 2020/test.csv",
    )
    print(data)