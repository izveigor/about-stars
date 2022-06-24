# About stars [![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/izveigor/about-stars/blob/main/LICENSE) ![Tests](https://github.com/izveigor/about-stars/actions/workflows/tests.yml/badge.svg)
Flask-powered application about stars.
![1](https://user-images.githubusercontent.com/68601180/162478863-d5af577d-a51b-4167-93df-a80234873971.JPG)
![2](https://user-images.githubusercontent.com/68601180/162478864-c71c5a66-1392-4c58-ab7f-4f22d25d0a04.JPG)
![3 1](https://user-images.githubusercontent.com/68601180/162478856-c4992d11-18ba-447f-a834-baace650112d.JPG)
![4](https://user-images.githubusercontent.com/68601180/162478860-fb0e5448-ca3f-4888-bfbc-30c4587e357c.JPG)
![5](https://user-images.githubusercontent.com/68601180/162478862-98f906dd-623d-4190-9bcb-69511befd246.JPG)
## How to use
You can start the application with docker-compose:
```
$ docker-compose up
```
Application takes information from file ("data/hygdata_v3.csv").
It downloads data from that file with special command ("flask api download_stars"). After that, user visit site 127.0.0.1:5000.
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
