**GeoPhotos** is a package to pull, plot, and analyze coordinates from photos.

```
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
# Analyze the data
analyzer = gp.Analyzer(data)
results = {
    'Unique Countries': analyzer.unique_countries(),
    'Count': analyzer.count_countries(),
    'Frequency': analyzer.country_frequency(),
    'Most Common': analyzer.most_common(5),
}
# Use the data to determine which countries to highlight
border_layer = gp.BorderLayer(results['Unique Countries'], name='Countries Visited')
border_layer.add_to(heatmap)
# Add layer control functionality to the map
heatmap.add_layer_control()
# Save the heatmap and open it in a browser
heatmap.save_html('sample.html', open_html=True)
```

<iframe src="img\sample.html" style="border: 0; width:100%; height:500px;"></iframe>