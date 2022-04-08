# About stars [![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/izveigor/about-stars/blob/main/LICENSE)
Flask-powered application about stars.
## How to use
Application takes information from file ("data/hygdata_v3.csv").
It downloads data from that file with special command ("flask db download_stars"). After that, user visit site 127.0.0.1:5000.
User has two options to input data for searching stars:
1. Input tag of a constellation
2. Input points
---
If you input points, the application finds all stars in polygon, building by convex set by these points.
After that you will see next information about stars:
1. Catalogs
2. Constellations
3. Spects
---
Next window allows you for searching these data by segment. You can search by next parameters:
1. Distance
2. Apparent magnitude
3. Absolute magnitude
---
Segment finds all stars, which were contained by it.
You can also sort all data (ascending or descending), which were contained by segment
## About file "hygdata_v3.csv"
All data were taken from https://github.com/astronexus/HYG-Database
by Attribution-ShareAlike 2.5 Generic (CC BY-SA 2.5).