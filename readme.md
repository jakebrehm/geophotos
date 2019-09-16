**GeoPhotos** is a package to pull, analyze, and plot coordinates from photos.

---
# What is **GeoPhotos**?

**GeoPhotos** is a Python library designed to make it easy to pull coordinates
from photos, analyze them in order to obtain useful information, and plot them
on a map.

## Main features

An overview of some of the major features of **GeoPhotos** are as follows:

* Extract metadata (timestamp, coordinates, etc.) from one or more files, and
  write to a csv file if desired
* Plot coordinate data on a fully customizable heatmap, including markers,
  tooltips, layer control, and more
* Analyze coordinate data to determine unique countries, most common countries,
  and more
* Highlight certain countries on the heatmap easily and painlessly
* Save the map to an html file for reference or for use with web development
  frameworks such as *flask*
* Open the html file directly from the code for debugging

# How to get it

## Dependencies

Currently, the following packages are required:

* [pillow](https://github.com/python-pillow/Pillow)
* webbrowser
* [folium](https://github.com/python-visualization/folium)
* osgeo
* [geopandas](https://github.com/geopandas/geopandas)

There are plans to make certain packages, such as *geopandas*, optional due to
how difficult they are to install properly.

## Installation

Assuming you've already got the dependencies covered, you can use pip to install
this package:

```
pip install geophotos
```

However, you will most likely run into problems doing it this way.
Unfortunately, I have tried and failed to overcome these obstacles myself.
My recommendation is to install geopandas using Anaconda/conda, and then pip
install it into your current environment:

```
conda install geopandas
pip install geophotos
```

This should handle all of the dependencies for you, although you still might run
into some issues (I sure did!).

## Updating

To update *geophotos* to the latest version, simple use the command:

```
pip install --upgrade geophotos
```

# Example usage

One of the main reasons I made this package was to pull GPS information from the
pictures in my iCloud library, then plot them on a map. Skipping the pulling of
the coordinates for simplicity's sake, the following code does the following:

1. Read latitudes and longitudes from a csv file
2. Generate a heatmap using this coordinate data
3. Add a marker that marks my hometown
4. Analyze the data and determine which countries I've visited
5. Highlight only the countries I've been to on a separate layer
6. Save the map as an html file and open it in a web browser

The html file is completely interactive, and I hope to eventually use it on my
personal website! Unfortunately, I had to post a still image of the map because
Github doesn't like cool things.

```python
import geophotos as gp

# Read coordinate data from csv
data = gp.coordinates_from_csv(r'coordinates.csv', 2, 3)
# Initialize the Map object
nys_center = [42.965000, -76.016667]
heatmap = gp.Map(location=nys_center, zoom_start=7)
# Feed the Heatmap object the coordinates
heatmap.coordinates = data
# Create the heatmap
heatmap.create_heatmap(max_zoom=10, min_opacity=0.05, radius=13, blur=25,
                       name='Photo Heatmap')
# Add a marker to the heatmap
hamburg_ny = [42.715746, -78.829416]
heatmap.add_marker(location=hamburg_ny,
                   tooltip='<strong>Hamburg, NY</strong><br>Hometown')
# Analyze the data to determine which countries are unique
analyzer = gp.Analyzer(data)
unique_countries = analyzer.unique_countries(),
# Use the data to determine which countries to highlight
border_layer = gp.BorderLayer(unique_countries, name='Countries Visited')
border_layer.add_to(heatmap)
# Add layer control functionality to the map
heatmap.add_layer_control()
# Save the heatmap and open it in a browser
heatmap.save_html('sample.html', open_html=True)
```

<p align="center">
  <img src="https://raw.githubusercontent.com/jakebrehm/geophotos/master/img/sample.JPG"
  alt="Sample geophotos output map"/>
</p>

---

# Authors
- **Jake Brehm** - *Initial Work* - [Email](mailto:jbrehm@tactair.com) | [Github](http://github.com/jakebrehm) | [LinkedIn](http://linkedin.com/in/jacobbrehm)