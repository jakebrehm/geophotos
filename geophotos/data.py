# -*- coding: utf-8 -*-

"""
geophotos.gather
~~~~~~~~~~~~~~~~~

Specializes in reading and writing geographic coordinate data. Intended
to provide a way to pull coordinates from a variety of sources, such as
Google Takeout Location History. This information can then be stored,
either as a csv file or a returned object.
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


def _parse_google_takeout_json(filepath):
    '''Parses the input Google Takeout Location History JSON file.
    
    Args:
        filepath (str):
            The location of the Google Takeout Location History JSON
            file.

    Returns:
        A list of tuples which contain coordinate information in the
        form of: (timestamp, latitude, longitude).
    '''

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
        latitude = float(location['latitudeE7']) / 1e7
        longitude = float(location['longitudeE7']) / 1e7
        # Write the coordinates to the information list
        row = (timestamp, latitude, longitude)
        information.append(row)
    
    return information


def csv_from_google_takeout_json(filepath, destination):
    '''Converts the information stored in a Google Takeout Location
    History JSON file to a csv file with three columns: timestamp,
    latitude, and longitude.
    
    Args:
        filepath (str):
            The location of the Google Takeout Location History JSON
            file.
        destination (str):
            Where to save the output csv file.
    '''

    # Get the coordinate information from the input file
    information = _parse_google_takeout_json(filepath)
    # If a filepath was specified, instantiate the csv writer
    with open(destination, 'w') as output:
        writer = csv.writer(output, delimiter=',')
        # Write a header row to the csv file
        writer.writerow(['timestamp', 'latitude', 'longitude'])
        # Write the rest of the information to the csv file
        writer.writerows(information)


def coordinates_from_google_takeout_json(filepath):
    '''Takes a path to a Google Takeout Location History JSON file,
    and with it, pulls the coordinates. This data is then returned as
    a list of tuples.
    
    Args:
        filepath (str):
            The location of the Google Takeout Location History JSON
            file.

    Returns:
        A list of tuples which contain coordinate information in the
        form of: (latitude, longitude).
    '''

    # Get the coordinate information from the input file
    information = _parse_google_takeout_json(filepath)
    # Remove timestamp column for synergy with other geophotos functions
    return [(info[1], info[2]) for info in information]


if __name__ == '__main__':
    csv_from_google_takeout_json(
        r"/Users/jake/OneDrive/Python/_Miscellaneous/Google Location History/Early 2020/Location History.json",
        r"/Users/jake/OneDrive/Python/_Miscellaneous/Google Location History/Early 2020/test.csv",
    )

    data = coordinates_from_google_takeout_json(
        r"/Users/jake/OneDrive/Python/_Miscellaneous/Google Location History/Early 2020/Location History.json"
    )
    print(data)
