import redis
from redis.commands.search.query import Query
from shapely import wkt, area, difference
from shapely.geometry import Polygon, LineString
from shapely.ops import split
import math
import os
from dotenv import load_dotenv 

load_dotenv() 
SIGNIFICANT_INTERSECTION = .33
SIGNIFICANT_TOTAL_INTERSECTION = .66
INDEX = os.getenv("INDEX")

load_dotenv() 

r = redis.Redis(
    host=os.getenv("HOST"),
    port=os.getenv("PORT"),
    decode_responses=True,
    username=os.getenv("USER"),
    password=os.getenv("PASSWORD")
)

def get_nonintersecting_tiles(polygon):
    polygon_area = area(polygon)

    # query redis cache
    ft = r.ft(INDEX)
    q = Query("@region:[INTERSECTS $regionContainer]").dialect(3)

    # query all regions that overlap
    res = ft.search(q, query_params={"regionContainer": 
                   f"{polygon.wkt}"})

    total_intersection = Polygon()

    for doc in res.docs:
        overlapping_region = eval(doc.json)[0]['region']
        overlapping_poly = Polygon(wkt.loads(overlapping_region)) # convert wkt string of overlapping region to shapely polygon
        
        intersection = overlapping_poly.intersection(polygon) # get polygon of intersection

        if (area(intersection)/polygon_area >= SIGNIFICANT_INTERSECTION):
            total_intersection = total_intersection.union(intersection) # add intersection to total 

    if (area(total_intersection)/polygon_area >= SIGNIFICANT_TOTAL_INTERSECTION):
        return _slice_region_difference(polygon, total_intersection) # return array of sliced tiles in nonintersecting area/difference
    else:
        return [polygon]
    
def _slice_region_difference(polygon, intersection):
    diff = difference(polygon, intersection) # get nonintersecting region

    if diff.is_empty:
        return [polygon] # no intersection, return original shape
    
    edges = get_extended_edges(diff) # get extended edges to cut region with
    
    # slice difference polygon into rectangular tiles using the extended edges
    tiles = []
    if diff.geom_type == 'Polygon':
        _get_polygon_tiles(diff, edges, 0, tiles) 
    
    elif diff.geom_type == 'MultiPolygon':
        for poly in diff.geoms:
            _get_polygon_tiles(poly, edges, 0, tiles)
    return tiles

def _get_polygon_tiles(polygon, cuts, cut_index, tiles):
    if (is_rectangle(polygon)):
        # it is a tile - we are done
        tiles.append(polygon)
    else:
        partitions = []
        partition_area = 0

        # while slicing on edge does not produce two distinct polygons, try next edge
        while partition_area == 0 or partition_area == area(polygon): 
            partitions = split(polygon, cuts[cut_index])
            partition_area = area(partitions.geoms[0])

            cut_index += 1
        
        for partition in partitions.geoms: 
            # continue slicing current partitions into rectangles
            _get_polygon_tiles(partition, cuts, cut_index + 1, tiles)

def get_extended_edges(polygon):
    coords = polygon.boundary.coords

    extended_edges = []

    for i in range(len(coords) - 1):
        # Polygon coordinates must be defined in a LinearRing, so we can connect adjacent points in the list
        start_point = coords[i]
        end_point = coords[i + 1]

        # compute direction vector of line
        dx = end_point[0] - start_point[0]
        dy = end_point[1] - start_point[1]
        line_length = (dx**2 + dy**2)**0.5  # line length

        # calculate unit vector of line
        unit_dx = dx / line_length
        unit_dy = dy / line_length

        x_extension = area(polygon) * unit_dx
        y_extension = area(polygon) * unit_dy

        # extend start, end points, preserving the slope
        extended_start = (start_point[0] - x_extension, start_point[1] - y_extension)
        extended_end = (end_point[0] + x_extension * unit_dx, end_point[1] + y_extension)

        extended_edges.append(LineString([extended_start, extended_end]))
        
    return extended_edges

def is_rectangle(polygon):
    return  math.isclose(polygon.minimum_rotated_rectangle.area, polygon.area)
