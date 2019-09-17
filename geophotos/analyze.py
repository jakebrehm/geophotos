# -*- coding: utf-8 -*-

'''
geophotos.analyze
~~~~~~~~~~~~~~~~~

Analyzes coordinate data to determine which countries each datum falls
under. Furthermore, with the list of countries determined, subsequent
analysis can be performed in order to output characteristics of the
dataset such as which countries appeared most frequently.
'''

import fiona
import os
import pickle
from collections import Counter
from osgeo import ogr


class ReverseGeolocator:
    '''Class that has the ability to take a set of coordinates and
    determine which country it lies in.
    
    Primarily intended to only be called by the Analyze class.
    '''

    def __init__(self, shapefile):
        '''Initializes the object.
        
        Args:
            shapefile (str):
                Path to a shapefile that contains world map information
        '''
        
        self.shapefile = shapefile
        driver = ogr.GetDriverByName('ESRI Shapefile')
        self.map_file = driver.Open(shapefile)
        self.layer = self.map_file.GetLayer()

    def get_country(self, coordinates):
        '''Determine which country a set of coordinates lies in.
        
        Example usage:
        >>> locator = ReverseGeolocator(r'data/world_borders.zip')
        >>> locator.get_country([55.644904, 12.576965])
        Denmark
        
        Args:
            coordinates (list/tuple):
                A list of tuple of length two, with the first element
                being latitude and the second being longitude.
        '''

        self.shapes = fiona.open(self.shapefile)

        latitude, longitude = coordinates
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(longitude, latitude)

        for s, shape in enumerate(self.shapes):
            country = self.layer.GetFeature(s)
            if country.geometry().Contains(point):
                return shape['properties']['NAME']


class Analyzer:
    '''Performs analysis of given coordinate data.'''

    def __init__(self, data, save_pickle=None):
        '''Initializes the object. Loops through the data that was
        passed in, which may take a very long time; therefore, an
        option to pickle the resulting object is included.
        
        Args:
            data (list):
                A list of lits/tuples containing coordinates.
                e.g. [(latitude, longitude), ...]
                
        Kwargs:
            save_pickle (str) [None]:
                Path to save the pickled Analyzer object to.
                A value of None will not save a pickle.
        '''
        
        self.data = data
        self.countries = self._get_countries()

        if save_pickle is not None:
            with open(save_pickle, 'wb') as output:
                pickle.dump(self, output)

    def _get_countries(self):
        '''Gathers an exhaustive list of countries that appear in the
        data. This may take awhile for large datasets.
        
        Returns:
            A list of countries.
        '''
        
        shapefile_path = os.path.join('data', 'world_borders.shp')
        locator = ReverseGeolocator(shapefile_path)
        return [locator.get_country(datum) for datum in self.data]

    def unique_countries(self, include_none=False):
        '''Determines the unique countries that appear in the data.
        
        Kwargs:
            include_none (bool) [False]:
                False will remove all None values from the result.

        Returns:
            A set of unique countries (no repeats).
        '''
        
        if include_none:
            return set(self.countries)
        else:
            return set(country for country in self.countries if country)

    def count_countries(self, include_none=False):
        '''Counts the number of unique countries that appear in the
        data.
        
        Kwargs:
            include_none (bool) [False]:
                False will remove all None values from the result.

        Returns:
            Number of unique countries as an integer.
        '''
        
        if include_none:
            return len(set(self.countries))
        else:
            return len([country for country in set(self.countries) if country])

    def country_frequency(self, include_none=False, sort=True):
        '''Counts the number of times that each country appeared in the
        data.

        Kwargs:
            include_none (bool) [False]:
                False will remove all None values from the result.
            sort (bool) [True]:
                True will sort the result from most to least frequent.

        Returns:
            A list of tuples, where each tuple contains the name of the
            country and the number of times it appeared in the data.
        '''
        
        # if include_none:
        #     counter = Counter(self.countries)
        # else:
        #     counter = Counter(country for country in self.countries if country)
        
        # if sort:
        #     return sorted(dict(counter).items(), key=lambda kv: kv[1], reverse=True)
        # else:
        #     return dict(counter)

        if include_none:
            counter = Counter(self.countries)
        else:
            counter = Counter(country for country in self.countries if country)
        
        if sort:
            return sorted(dict(counter).items(), key=lambda kv: kv[1], reverse=True)
        else:
            return dict(counter)
        
    def most_common(self, n, include_none=False):
        '''Determines the countries that appear most commonly in the
        data.
        
        Args:
            n (int):
                The number of top countries to return.
                e.g. an n of 5 gives the top 5 most common countries.
        
        Kwargs:
            include_none (bool) [False]:
                False will remove all None values from the result.

        Returns:
            A list of tuples ordered from most common to least common,
            with each tuple containing the name of the country and the
            number of times it appeared in the data.
        '''
        
        if include_none:
            counter = Counter(self.countries)
        else:
            counter = Counter(country for country in self.countries if country)
        return counter.most_common(n)


if __name__ == '__main__':
    # shapefile_path = os.path.join('data', 'world_borders.shp')
    # cc = ReverseGeolocator(shapefile_path)
    # coordinates = [42.715746, -78.829416] # hamburg
    # print(cc.get_country(coordinates))
    # coordinates = [55.644904, 12.576965] # amager
    # print(cc.get_country(coordinates))
    
    pickle_path = os.path.join('data', 'testing', 'coordinates.pickle')
    with open(pickle_path, 'rb') as pickle_file:
        analyzer = pickle.load(pickle_file)
    results = {
        'Unique Countries': analyzer.unique_countries(),
        'Count': analyzer.count_countries(),
        'Frequency': analyzer.country_frequency(),
        'Most Common': analyzer.most_common(5),
    }
    for k, v in results.items(): print(k, v)