import pathlib
from setuptools import setup, find_packages

HERE = pathlib.Path(__file__).parent

README = (HERE / 'README.md').read_text()

setup(
     name='geophotos',
     version='0.50.1',
     author="Jake Brehm",
     author_email="code@jakebrehm.com",
     license='MIT',
     description="A package to pull, plot, and analyze coordinates from photos.",
     long_description=README,
     long_description_content_type="text/markdown",
     url="https://github.com/jakebrehm/geophotos",
     packages=find_packages(),
     package_data={
        '': ['*.zip', '*.shp', '*.shx', '*.dbf', '*.prj']
     },
     install_requires=[
        'pillow',
        'folium',
        'gdal',
     ],
     extras_require={
        'geopandas': ['geopandas'],
     },
     include_package_data=True,
     classifiers=[
         "Programming Language :: Python :: 3.7",
         "Operating System :: OS Independent",
     ],
 )
