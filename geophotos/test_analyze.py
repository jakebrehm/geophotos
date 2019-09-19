# -*- coding: utf-8 -*-

'''
geophotos.analyze unit test
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unit test of the analyze module of GeoPhotos.
'''

import analyze
import os
import pickle
import unittest


class TestAnalyze(unittest.TestCase):
    '''Unit test the analyze module.'''

    def test_reverse_geolocator(self):
        '''Test the ReverseGeolocator class.'''
        
        # Initialize a ReverseGeolocator object
        shapefile_path = os.path.join('data', 'world_borders.shp')
        cc = analyze.ReverseGeolocator(shapefile_path)
        # Hamburg, NY, USA --> United States
        coordinates = [42.715746, -78.829416]
        country = cc.get_country(coordinates)
        self.assertEqual(country, 'United States')
        # Amager, Denmark --> Denmark
        coordinates = [55.644904, 12.576965]
        country = cc.get_country(coordinates)
        self.assertEqual(country, 'Denmark')
        # Pacific Ocean --> None
        coordinates = [-1.311849, -122.934390]
        country = cc.get_country(coordinates)
        self.assertEqual(country, None)
    
    def test_analyzer(self):
        '''Test the Analyzer class.'''
        
        # Load the pickled Analyzer object
        pickle_path = os.path.join('data', 'testing', 'coordinates.pickle')
        with open(pickle_path, 'rb') as pickle_file:
            analyzer = pickle.load(pickle_file)
        # Perform the analysis
        results = {
            'Unique Countries': analyzer.unique_countries(),
            'Count': analyzer.number_of_countries(),
            'Frequency': analyzer.country_frequency(),
            'Most Common': analyzer.most_common(5),
        }

        # List of expected results
        expected = [
            ('United States', 11413),
            ('United Kingdom', 2194),
            ('Denmark', 1803),
            ('Australia', 1437),
            ('Iceland', 1176),
            ('France', 896),
            ('New Zealand', 776),
            ('Germany', 507),
            ('Italy', 300),
            ('Canada', 273),
            ('Switzerland', 256),
            ('Spain', 222),
            ('Latvia', 142),
            ('Norway', 98),
            ('Portugal', 94),
            ('Ireland', 65),
            ('Saint Lucia', 62),
            ('Barbados', 57),
            ('Fiji', 48),
            ('United States Virgin Islands', 36),
            ('Antigua and Barbuda', 32),
            ('Saint Martin', 18),
            ('Sweden', 16),
            ('British Virgin Islands', 13),
            ('Saint Barthelemy', 10),
            ('Netherlands', 2),
            ('Greenland', 2)
        ]
        # Expected set of countries
        countries = set(item[0] for item in expected)

        # Make assertions
        self.assertEqual(results['Unique Countries'], countries)
        self.assertEqual(results['Count'], 27)
        self.assertEqual(results['Frequency'], expected)
        self.assertEqual(results['Most Common'], expected[0:4+1])


if __name__ == '__main__':
    unittest.main()