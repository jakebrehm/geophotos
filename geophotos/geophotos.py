from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import requests

from datetime import datetime
import os
import csv
import glob

import pandas as pd
import folium
from folium.plugins import HeatMap
import webbrowser

try:
    import analyze
except:
    from . import analyze

class GeoPhotos:

    def __init__(self, images=None):
        self._images = set()

        if images: self.feed(images)

    @property
    def images(self):
        return self._images

    @images.setter
    def images(self, filepaths):
        self.feed(filepaths)

    def clear(self):
        self._images = set()

    def feed(self, images):

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
        return data[key] if key in data else None
    
    def _convert_to_degrees(self, value):
        degrees = float(value[0][0]) / float(value[0][1])
        minutes = float(value[1][0]) / float(value[1][1])
        seconds = float(value[2][0]) / float(value[2][1])
        return degrees + (minutes/60) + (seconds/3600)

    def pull_metadata(self):
        return [self.pull_exif(filepath) for filepath in self._images]

    def pull_exif(self, location):
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
        data = exif_data['DateTime']
        date, time = data.split()
        date = date.replace(':', '-')
        result = f'{date} {time}'
        if as_string:
            return result
        else:
            return datetime.strptime(result, r'%Y-%m-%d %H:%M:%S')

    def get_coordinates(self, exif_data, as_list=False):
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
        return [latitude for _, latitude, _ in self.pull_coordinates()]

    def get_longitudes(self, exif_data):
        return [longitude for _, _, longitude in self.pull_coordinates()]

    def write_csv(self, filepath, data, labels=None, filter_none=True):

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

        heatmap = folium.Map(location=[43.1065, -76.2177], zoom_start=14)

        heatmap_wide = HeatMap(
            list(zip(latitudes, longitudes)),
        )

        heatmap_wide.add_to(heatmap)

        heatmap.save(output)

        if open_html:
            webbrowser.open(output)

    def __str__(self):
        return '\n'.join(sorted(self._images))


class Map(folium.Map):

    def __init__(self, *args, **kwargs):

        folium.Map.__init__(self, *args, **kwargs)

        self._coordinates = None
        self._latitudes = None
        self._longitudes = None

    def _combine(self):
        self._coordinates = list(zip(self._latitudes, self._longitudes))

    @property
    def coordinates(self):
        return self._coordinates

    @coordinates.setter
    def coordinates(self, data):
        self._coordinates = data

    @property
    def latitudes(self):
        return self._latitudes

    @latitudes.setter
    def latitudes(self, data):
        self._latitudes = data
        if self._latitudes and self._longitudes:
            self._combine()

    @property
    def longitudes(self):
        return self._longitudes

    @longitudes.setter
    def longitudes(self, data):
        self._longitudes = data
        if self._latitudes and self._longitudes:
            self._combine()

    def feed(self, latitudes, longitudes):
        self._latitudes = latitudes
        self._longitudes = longitudes
        self._combine()

    def create_heatmap(self, **kwargs):

        valid = ['name', 'min_opacity', 'max_zoom', 'max_val', 'radius',
                 'blur', 'gradient', 'overlay', 'control', 'show']
        for kwarg in kwargs:
            if kwarg not in valid:
                raise ValueError('Invalid keyword argument.')

        heatmap = HeatMap(self._coordinates, **kwargs)

        heatmap.add_to(self)

    def add_marker(self, location, popup=None, tooltip=None):

        if isinstance(popup, dict):
            valid = ['html', 'parse_html', 'max_width', 'show', 'sticky']
            for kwarg in popup:
                if kwarg not in valid:
                    raise ValueError('Invalid keyword argument.')
            popup = folium.Popup(**popup)

        marker = folium.Marker(location=location, popup=popup, tooltip=tooltip)
        marker.add_to(self)

    def save_html(self, filepath, open_html=False):
        self.save(filepath)
        if open_html:
            self.open_html(filepath)

    def open_html(self, filepath):
        path = os.path.dirname(os.path.abspath(__file__))
        webbrowser.open(f'file://{path}/{filepath}')

    # @property
    # def countries(self):
    #     locator = analyze.ReverseGeolocator(r'data\world_borders.shp')

    #     countries = [locator.get_country(coordinate) for coordinate in self.coordinates]

    #     print(set(countries))



def coordinates_from_csv(filepath, latitude_column, longitude_column,
                         delimiter=','):

    data = pd.read_csv(filepath, delimiter=delimiter)

    latitudes = data.iloc[:, latitude_column-1]
    longitudes = data.iloc[:, longitude_column-1]

    return list(zip(latitudes, longitudes))


if __name__ == '__main__':
    # # Directory where images are stored
    # path = r"C:\Users\jakem\OneDrive\Python\Leisure Projects\Geolocation Map"

    # # Initialize GeoPhotos object
    # app = GeoPhotos()
    # # Get the filepaths of all jpg files and feed it to the GeoPhotos object
    # app.find(f'{path}\\**\\*.jpg', feed=True)
    # # Pull the coordinates and filter out None values
    # data = [datum for datum in app.pull_coordinates(include_timestamp=False)
    #         if None not in datum]

    # # Read coordinate data from csv
    # data = coordinates_from_csv('coordinates.csv', 2, 3)
    # # Initialize the Map object
    # heatmap = Map(location=data[1], zoom_start=14)
    # # Feed the Heatmap object the coordinates
    # heatmap.coordinates = data
    # # Create the heatmap
    # heatmap.create_heatmap(max_zoom=14, min_opacity=0.05, radius=13, blur=25)
    # # Save the heatmap and open it in a browser
    # heatmap.save_html('test.html', open_html=True)




    # # Read coordinate data from csv
    # data = coordinates_from_csv('coordinates.csv', 2, 3)
    # # Initialize the Map object
    # ny_center = [42.965000, -76.016667]
    # # heatmap = Heatmap(location=ny_center, zoom_start=5, tiles='Mapbox Bright')
    # heatmap = Map(location=ny_center, zoom_start=7)
    # # Feed the Heatmap object the coordinates
    # heatmap.coordinates = data
    # # Create the heatmap
    # heatmap.create_heatmap(max_zoom=10, min_opacity=0.05, radius=13, blur=25)
    # # Add a marker to the heatmap
    # # hamburg = [42.74444, -78.85833]
    # hamburg = [42.715746, -78.829416]
    # # popup = folium.Popup(html='<strong>Hamburg, NY</strong><br>My hometown!',
    # #                      parse_html=False,
    # #                      max_width=14000,
    # #                      show=False,
    # #                      sticky=False)
    # popup = dict(html='<strong>Hamburg, NY</strong><br>My hometown!',
    #              parse_html=False,
    #              max_width=14000,
    #              show=False,
    #              sticky=False)
    # heatmap.add_marker(location=hamburg,
    #                 #    popup=popup,
    #                 #    tooltip='Hometown')
    #                    tooltip='<strong>Hamburg, NY</strong><br>Hometown')
    # # Save the heatmap and open it in a browser
    # heatmap.save_html('test.html', open_html=True)

    


    
    # # Read coordinate data from csv
    # data = coordinates_from_csv(r'data\testing\coordinates.csv', 2, 3)
    # data = data[0:10000]
    # analyzer = analyze.Analyzer(data)
    # print(analyzer.unique_countries())
    # print(analyzer.count_countries())
    # print(analyzer.most_common(5))


    import pickle

    with open(r'data\testing\coordinates.pickle', 'rb') as pickle_file:
        analyzer = pickle.load(pickle_file)

    print(analyzer)
    print(type(analyzer))
    print(analyzer.unique_countries())
    print(analyzer.count_countries())
    print(analyzer.most_common(5))

    # # Read coordinate data from csv
    # data = coordinates_from_csv(r'data\testing\coordinates.csv', 2, 3)
    # analyzer = analyze.Analyzer(data, save_pickle=r'data\testing\coordinates.pickle')

    # pickle_out = open(r'data\testing\coordinates.pickle', 'wb')
    # pickle.dump(analyzer, pickle_out)

    # with open(r'data\testing\coordinates.pickle', 'wb') as pickle_out:
    #     pickle.dump(analyzer, pickle_out)

    # print(analyzer.unique_countries())
    # print(analyzer.count_countries())
    # print(analyzer.most_common(5))





    # # Initialize the Map object
    # ny_center = [42.965000, -76.016667]
    # # heatmap = Heatmap(location=ny_center, zoom_start=5, tiles='Mapbox Bright')
    # heatmap = Map(location=ny_center, zoom_start=7)
    # # Feed the Heatmap object the coordinates
    # heatmap.coordinates = data
    # # Create the heatmap
    # heatmap.create_heatmap(max_zoom=10, min_opacity=0.05, radius=13, blur=25)
    # # Add a marker to the heatmap
    # # hamburg = [42.74444, -78.85833]
    # hamburg = [42.715746, -78.829416]
    # # popup = folium.Popup(html='<strong>Hamburg, NY</strong><br>My hometown!',
    # #                      parse_html=False,
    # #                      max_width=14000,
    # #                      show=False,
    # #                      sticky=False)
    # popup = dict(html='<strong>Hamburg, NY</strong><br>My hometown!',
    #              parse_html=False,
    #              max_width=14000,
    #              show=False,
    #              sticky=False)
    # heatmap.add_marker(location=hamburg,
    #                 #    popup=popup,
    #                 #    tooltip='Hometown')
    #                    tooltip='<strong>Hamburg, NY</strong><br>Hometown')
    # # Save the heatmap and open it in a browser
    # heatmap.save_html('test.html', open_html=True)
