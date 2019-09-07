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

    def find(self, pathname, recursive=None, internal=False):
        if recursive is None:
            if '**' in pathname:
                recursive = True
            else:
                recursive = False
        filepaths = glob.glob(f'{pathname}', recursive=recursive)
        if internal:
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


if __name__ == '__main__':
    path = r"C:\Users\jakem\OneDrive\Python\Leisure Projects\Geolocation Map"
    app = GeoPhotos()
    # app.find(f'{path}\\**\\*.jpg', internal=True)
    photos = glob.glob(f'{path}\\**\\*.jpg', recursive=True)
    app.images = photos
    # for item in app.images: print(item)
    # print(app)
    # app.generate_heatmap()
    # app.generate_heatmap(source='csv', coordinate_data='coordinates.csv',
    #                      latitude_column=2, longitude_column=3, open_html=True)
    data = [datum for datum in app.pull_coordinates() if None not in datum]
    app.generate_heatmap(source='data', coordinate_data=data,
                         latitude_column=2, longitude_column=3, open_html=True)