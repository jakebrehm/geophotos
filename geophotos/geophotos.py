# -*- coding: utf-8 -*-

#    ____            ____  _           _            
#   / ___| ___  ___ |  _ \| |__   ___ | |_ ___  ___ 
#  | |  _ / _ \/ _ \| |_) | '_ \ / _ \| __/ _ \/ __|
#  | |_| |  __| (_) |  __/| | | | (_) | || (_) \__ \
#   \____|\___|\___/|_|   |_| |_|\___/ \__\___/|___/

'''
GeoPhotos Library
~~~~~~~~~~~~~~~~~

A Python library designed to make it easy to pull coordinates from
photos, analyze them in order to obtain useful information, and plot
them on a map.
'''

import csv
import glob
import os
import sys
import webbrowser
from datetime import datetime

import folium
import pandas as pd
import requests
from folium.plugins import HeatMap
from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS

# Geopandas is an optional dependency
try:
    import geopandas as gpd
except ImportError:
    pass


def requires_geopandas(original):
    '''This function is a decorator that will raise an ImportError
    if geopandas has not been imported due to it being an optional
    dependency.'''
    
    def wrapper(*args, **kwargs):
        # Call the function if geopandas has been imported
        if 'geopandas' in sys.modules:
            return original(*args, **kwargs)
        # Otherwise, raise an ImportError
        else:
            name = original.__name__
            raise ImportError(f'GeoPandas is required to use {name}.')
    return wrapper


class GeoPhotos:
    """"""

    def __init__(self, images=None):
        """"""

        self._images = set()

        if images: self.feed(images)

    @property
    def images(self):
        """"""

        return self._images

    @images.setter
    def images(self, filepaths):
        """"""

        self.feed(filepaths)

    def clear(self):
        """"""

        self._images = set()

    def feed(self, images):
        """"""

        if isinstance(images, str):
            if os.path.isfile(images):
                self._images.add(images)
            elif os.path.isdir(images):
                pass # use glob
        elif isinstance(images, list) or isinstance(images, tuple):
            for item in images:
                if os.path.isfile(item):
                    self._images.add(item)

    def find(self, pathname, recursive=None, feed=False):
        """"""

        if recursive is None:
            if '**' in pathname:
                recursive = True
            else:
                recursive = False
        filepaths = glob.glob(f'{pathname}', recursive=recursive)
        if feed:
            self.feed(filepaths)
        else:
            return filepaths

    def _grasp(self, data, key):
        """"""

        return data[key] if key in data else None
    
    def _convert_to_degrees(self, value):
        """"""

        degrees = float(value[0][0]) / float(value[0][1])
        minutes = float(value[1][0]) / float(value[1][1])
        seconds = float(value[2][0]) / float(value[2][1])
        return degrees + (minutes/60) + (seconds/3600)

    def pull_metadata(self):
        """"""

        return [self.pull_exif(filepath) for filepath in self._images]

    def pull_exif(self, location):
        """"""

        image = Image.open(location)
        
        exif_data = dict()
        info = image._getexif()
        if info:
            for key, value in info.items():
                name = TAGS.get(key, key)
                if name == 'GPSInfo':
                    gps = dict()
                    for subvalue in value:
                        nested = GPSTAGS.get(subvalue, subvalue)
                        gps[nested] = value[subvalue]
                    exif_data[name] = gps
                else:
                    exif_data[name] = value
        return exif_data

    def pull_coordinates(self, metadata=None, include_timestamp=True,
                         as_list=False, sort=True):
        """"""

        if metadata is None:
            metadata = self.pull_metadata()

        coordinates = [self.get_coordinates(datum, as_list=as_list)
                       for datum in metadata]
        
        if not include_timestamp:
            return coordinates
        else:
            datetimes = [[self.get_datetime(datum)] if as_list else
                         (self.get_datetime(datum),) for datum in metadata]
            result = [datetimes[i]+coordinates[i] for i in range(len(datetimes))]
            return sorted(result) if sort else result

    def get_datetime(self, exif_data, as_string=False):
        """"""

        data = exif_data['DateTime']
        date, time = data.split()
        date = date.replace(':', '-')
        result = f'{date} {time}'
        if as_string:
            return result
        else:
            return datetime.strptime(result, r'%Y-%m-%d %H:%M:%S')

    def get_coordinates(self, exif_data, as_list=False):
        """"""

        latitude, longitude = None, None

        if 'GPSInfo' in exif_data:
            gps = exif_data['GPSInfo']
            
            info = {
                'Latitude Degrees': self._grasp(gps, 'GPSLatitude'),
                'Latitude Reference': self._grasp(gps, 'GPSLatitudeRef'),
                'Longitude Degrees': self._grasp(gps, 'GPSLongitude'),
                'Longitude Reference': self._grasp(gps, 'GPSLongitudeRef'),
            }
            
            if all([value for value in info.values()]):
                latitude = self._convert_to_degrees(info['Latitude Degrees'])
                if info['Latitude Reference'] != 'N':
                    latitude *= -1
                    
                longitude = self._convert_to_degrees(info['Longitude Degrees'])
                if info['Longitude Reference'] != 'E':
                    longitude *= -1

        return [latitude, longitude] if as_list else (latitude, longitude)

    def get_latitudes(self, exif_data):
        """"""

        return [latitude for _, latitude, _ in self.pull_coordinates()]

    def get_longitudes(self, exif_data):
        """"""

        return [longitude for _, _, longitude in self.pull_coordinates()]

    def write_csv(self, filepath, data, labels=None, filter_none=True):
        """"""

        if filter_none:
            data = [datum for datum in data if None not in datum]

        with open(filepath, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            if labels:
                writer.writerow(labels)
            for row in data:
                writer.writerow(row)

    def generate_heatmap(self, source='internal', coordinate_data=None,
                         latitude_column=None, longitude_column=None,
                         output='heatmap.html', open_html=False):
        """"""

        if source == 'internal':
            data = self.pull_coordinates(include_timestamp=False)
            latitudes = [datum[0] for datum in data if None not in datum]
            longitudes = [datum[1] for datum in data if None not in datum]

        elif source == 'data':
            latitudes = [datum[latitude_column-1] for datum in coordinate_data]
            longitudes = [datum[longitude_column-1] for datum in coordinate_data]

        elif source == 'csv':
            data = pd.read_csv(coordinate_data)
            latitudes = data.iloc[:, latitude_column-1]
            longitudes = data.iloc[:, longitude_column-1]

        # Need to find a better way to make the heatmap more customizable
        # when being generated through the GeoPhotos class

        heatmap = folium.Map(location=[43.1065, -76.2177], zoom_start=14)

        heatmap_wide = HeatMap(
            list(zip(latitudes, longitudes)),
        )

        heatmap_wide.add_to(heatmap)

        heatmap.save(output)

        if open_html:
            webbrowser.open(output)

    def __str__(self):
        """"""
        
        return '\n'.join(sorted(self._images))


class Map(folium.Map):
    """Stores coordinate information and can generate maps."""

    def __init__(self, *args, **kwargs):
        """Initializes the object.
        
        Takes the same arguments as the folium.Map object. Please refer
        to its own documentation.
        """

        folium.Map.__init__(self, *args, **kwargs)

        self._coordinates = None
        self._latitudes = None
        self._longitudes = None

    def _combine(self):
        """Combines the stored latitudes list with the stored
        longitudes list into a list of tuples."""

        self._coordinates = list(zip(self._latitudes, self._longitudes))

    @property
    def coordinates(self):
        """Returns the stored list of coordinates."""

        return self._coordinates

    @coordinates.setter
    def coordinates(self, data):
        """Sets the stored list of coordinates."""

        self._coordinates = data

    @property
    def latitudes(self):
        """Returns the stored list of latitudes."""

        return self._latitudes

    @latitudes.setter
    def latitudes(self, data):
        """Sets the stored list of latitudes."""

        self._latitudes = data
        # Combines the stored latitude and longitude lists if they have
        # both been initialized
        if self._latitudes and self._longitudes:
            self._combine()

    @property
    def longitudes(self):
        """Returns the stored list of longitudes."""

        return self._longitudes

    @longitudes.setter
    def longitudes(self, data):
        """Sets the stores list of longitudes."""

        self._longitudes = data
        # Combines the stored latitude and longitude lists if they have
        # both been initialized
        if self._latitudes and self._longitudes:
            self._combine()

    def feed(self, latitudes, longitudes):
        """Sets the stored latitude and longitude lists, then combines
        them into a combined coordinates list.
        
        Args:
            latitudes (list):
                A list containing latitude information.
            longitudes (list):
                A list containing longitude information.
        """

        self._latitudes = latitudes
        self._longitudes = longitudes
        self._combine()

    def create_heatmap(self, **kwargs):
        """Create a heatmap using the instance's coordinates.

        The following parameter description were taken directly from
        the folium.plugins.HeatMap documentation.
        
        Kwargs:
            name (str) --> None:
                The name of the Layer, as it will appear in
                LayerControls.
            min_opacity (int) --> 1;
                The minimum opacity the heat will start at.
            max_zoom (int) --> 18:
                Zoom level where the points reach maximum intensity (as
                intensity scales with zoom), equals maxZoom of the map
                by default.
            max_val (float) --> 1:
                Maximum point intensity.
            radius (int) --> 25:
                Radius of each "point" of the heatmap.
            blur (int) --> 15:
                Amount of blur.
            gradient (dict) --> None:
                Color gradient config.
                e.g. {0.4: 'blue', 0.65: 'lime', 1: 'red'}
            overlay (bool) -- True:
                Adds the layer as an optional overlay (True) or the
                base layer (False).
            control (bool) --> True:
                Whether the Layer will be included in LayerControls.
            show (bool) --> True:
                Whether the layer will be shown on opening (only for
                overlays).
        """

        # Raise an error if any invalid arguments are detected
        valid = ['name', 'min_opacity', 'max_zoom', 'max_val', 'radius',
                 'blur', 'gradient', 'overlay', 'control', 'show']
        for kwarg in kwargs:
            if kwarg not in valid:
                raise ValueError('Invalid keyword argument.')

        # Instantiate a heatmap object
        heatmap = HeatMap(self._coordinates, **kwargs)
        heatmap.add_to(self)

    def add_marker(self, location, popup=None, tooltip=None):
        """Add a marker to the Map instance.
        
        Args:
            location (tuple/list):
                Coordinates to place the marker at, passed in as either
                a tuple or a list in the form: (latitude, longitude).
        
        Kwargs:
            popup (dict/folium.Popup) [None]:
                Add a popup to the marker. This can be passed in the
                form of a dictionary containing the relevant
                information, or as a folium.Popup object directly.
                The default value of None will not add a popup.
            tooltip (str) [None]:
                Add a tooltip to the marker. HTML tags are accepted.
                The default value of None will not add a tooltop to the
                marker.
        """

        # Create a folium.Popup object if a dictionary was passed in
        # via the popup argument, otherwise it is assumed that a
        # folium.Popup object was passed in directly.
        if isinstance(popup, dict):
            valid = ['html', 'parse_html', 'max_width', 'show', 'sticky']
            for kwarg in popup:
                if kwarg not in valid:
                    raise ValueError('Invalid keyword argument.')
            popup = folium.Popup(**popup)

        # Create a marker object and add it to the map
        marker = folium.Marker(location=location, popup=popup, tooltip=tooltip)
        marker.add_to(self)

    def save_html(self, filepath, open_html=False):
        """Save the Map instance to an interactive html file, and
        optionally open it in a browser.
        
        Args:
            filepath (str):
                Path to save the html file to.
        
        Kwargs:
            open_html (bool) [False]:
                Whether or not to open the file in a browser after
                saving.
        """

        self.save(filepath)
        if open_html:
            self.open_html(filepath)

    def open_html(self, filepath):
        """Open the specified html file in a browser.
        
        Args:
            filepath (str):
                Path to the html file.
        """

        webbrowser.open(f'file://{filepath}')

    def add_layer_control(self):
        """Add layer controls to the map.
        
        This method is an extremely thin wrapper around
        folium.LayerControl, and is meant to instantiate it and then
        add it to the map object immediately.
        """

        folium.LayerControl().add_to(self)


@requires_geopandas
class CountryLayer(folium.GeoJson):
    '''Wrapper around the folium.GeoJson class. Adds a layer on top of
    a Map instance which highlights the specified countries.
    
    This wrapper mainly exists to make it easier for a user to specify
    which countries they want highlighted and to also initialize a
    folium.GeoJson object with this information -- all in one step.
    
    This class is only available if geopandas has been successfully
    imported, otherwise an ImportError will be raised when called.
    '''

    def __init__(self, countries='all', name=None):
        '''Initializes the object. Takes a list of countries and gets
        their relevant polygons/shapes.
        
        Kwargs:
            countries (str/list) --> 'all':
                A list of countries to be highlighted. The default
                value of 'all' will plot all countries.
            name (str) --> None:
                The name of the layer, which will be displayed if
                layer control is enabled on the Map instance.
        '''

        # Get the world borders/shapes information
        self.borders = gpd.read_file('zip://data/world_borders.zip')
        # Generate a geopandas dataframe of the specified countries' info
        if isinstance(countries, str) and countries == 'all':
            self.countries = self.borders
        elif isinstance(countries, str):
            self.countries = self.borders[self.borders['NAME'] == countries]
        else:
            self.countries = self.borders[self.borders['NAME'].isin(countries)]
        # Initialize the folium.GeoJson object
        folium.GeoJson.__init__(self, self.countries, name=name)
        
    def add_to(self, map_object):
        '''Extremely thin wrapper around the inherited add_to method,
        simply to expose it.'''
        
        super().add_to(map_object)


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


if __name__ == '__main__':

    help(folium.Map)

#     import pickle

#     # Read coordinate data from csv
#     data_path = os.path.join('data', 'testing', 'coordinates.csv')
#     data = coordinates_from_csv(data_path, 2, 3)
#     # Initialize the Map object
#     nys_center = [42.965000, -76.016667]
#     heatmap = Map(location=nys_center, zoom_start=7)
#     # Feed the Heatmap object the coordinates
#     heatmap.coordinates = data
#     # Create the heatmap
#     heatmap.create_heatmap(max_zoom=10, min_opacity=0.05, radius=13, blur=25,
#                            name='Photo Heatmap')
#     # Add a marker to the heatmap
#     hamburg_ny = [42.715746, -78.829416]
#     heatmap.add_marker(location=hamburg_ny,
#                        tooltip='<strong>Hamburg, NY</strong><br>Hometown')
#     # Analyze the data
#     pickle_path = os.path.join('data', 'testing', 'coordinates.pickle')
#     with open(pickle_path, 'rb') as pickle_file:
#         analyzer = pickle.load(pickle_file)
#     results = {
#         'Unique Countries': analyzer.unique_countries(),
#         'Count': analyzer.number_of_countries(),
#         'Frequency': analyzer.country_frequency(),
#         'Most Common': analyzer.most_common(5),
#     }
#     # Use the data to determine which countries to highlight
#     border_layer = CountryLayer(results['Unique Countries'],
#                                name='Countries Visited')
#     border_layer.add_to(heatmap)
#     # Add layer control functionality to the map
#     heatmap.add_layer_control()
#     # Save the heatmap and open it in a browser
#     main_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#     html_name = 'testing.html'
#     path = os.path.join(main_directory, 'tests', 'sample_results', html_name)
#     heatmap.save_html(path, open_html=True)
