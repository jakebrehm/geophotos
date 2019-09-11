from osgeo import ogr
import fiona
from collections import Counter
import pickle

class ReverseGeolocator:

    def __init__(self, shapefile):
        self.shapefile = shapefile
        driver = ogr.GetDriverByName('ESRI Shapefile')
        self.map_file = driver.Open(shapefile)
        self.layer = self.map_file.GetLayer()

    def get_country(self, coordinates):

        self.shapes = fiona.open(self.shapefile)

        latitude, longitude = coordinates
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(longitude, latitude)

        for s, shape in enumerate(self.shapes):
            country = self.layer.GetFeature(s)
            if country.geometry().Contains(point):
                return shape['properties']['NAME']


class Analyzer:

    def __init__(self, data, save_pickle=None):
        self.data = data
        self.countries = self._get_countries()

        if save_pickle is not None:
            with open(save_pickle, 'wb') as output:
                pickle.dump(self, output)

    def _get_countries(self):
        locator = ReverseGeolocator(r'data\world_borders.shp')
        return [locator.get_country(datum) for datum in self.data]

    def unique_countries(self, include_none=False):
        if include_none:
            return set(self.countries)
        else:
            return set(country for country in self.countries if country)
        # return set(self.countries)

    def count_countries(self, include_none=False):
        if include_none:
            return len(set(self.countries))
        else:
            return len([country for country in set(self.countries) if country])

    def country_frequency(self, include_none=False, sort=True):
        if include_none:
            counter = Counter(self.countries)
        else:
            counter = Counter(country for country in self.countries if country)
        
        if sort:
            return sorted(dict(counter).items(), key=lambda kv: kv[1], reverse=True)
        else:
            return dict(counter)

    def most_common(self, n, include_none=False):
        if include_none:
            counter = Counter(self.countries)
        else:
            counter = Counter(country for country in self.countries if country)
        return counter.most_common(n)


def count_countries(data):
    pass


def unique_countries(data):

    # locator = ReverseGeolocator(r'data\world_borders.shp')
    # countries = [locator.get_country(datum) for datum in data]
    # return set(countries)
    
    locator = ReverseGeolocator(r'data\world_borders.shp')

    total = len(data)

    # countries = set()
    countries = list()

    for d, datum in enumerate(data):
        # countries.add(locator.get_country(datum))
        countries.append(locator.get_country(datum))

        percent = (d+1)/total * 100
        print(f'{percent:.2f}% finished.')

    # from collections import Counter
    # print(Counter(countries))

    # return set(countries)
    return set(countries)


if __name__ == '__main__':
    cc = ReverseGeolocator(r'data\world_borders.shp')
    coordinates = [42.715746, -78.829416] # hamburg
    print(cc.get_country(coordinates))
    coordinates = [55.644904, 12.576965] # amager
    print(cc.get_country(coordinates))
