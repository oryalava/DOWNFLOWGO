import fiona
import shapely
import rasterio
import os
import numpy as np
from rasterio.transform import Affine
from rasterio.crs import CRS
#import downflowgo.astar as astar
import pandas as pd
import math
import csv
import downflowgo.txt_to_shape as txt_to_shape
import downflowgo.check_files as check_files
import heapq
from shapely.geometry import Point, LineString

def grid_maker_reader(data: dict, config: object) -> np.ndarray:
    """
    Create a vent grid around a UTM coordinate.
    """

    print(f"Csv file used : {config.csv_vent_file}")

    flow_id = str(data['flow_id'])

    data['lon'] = float(data.pop('X'))
    data['lat'] = float(data.pop('Y'))

    check_files.check_vent_in_dem(data['lon'],  data['lat'],config.dem)

    grid = coordinate_maker(vent_grid_size=config.ventgrid_size, resolution=config.ventgrid_resolution,
        csv_file=False, coord_dict=True,coords=data)

    path_to_grid_folder = os.path.join(config.path_to_grid_folder,flow_id)

    check_files.overwrite_check_files(config.delete_existing,path_to_grid_folder)

    grid_csv = grid_to_csv(grid,path_to_grid_folder, flow_id)

    print(f"Grid created : {grid_csv}")

    config.csv_vent_file = grid_csv

    return grid


def coordinate_maker(vent_grid_size: float, resolution: float, csv_file=True, csv_vent_file='', coord_dict=False,
                     coords=None) -> np.ndarray:
    """
    Generate a square grid of vents centered on a UTM coordinate.

    Parameters
    ----------
    vent_grid_size : float
        Total size of the square grid (m).

    resolution : float
        Distance between vents (m).

    Returns
    -------
    grid : np.ndarray
        Array of shape (n_vents, 2)
        [:,0] = Easting (X)
        [:,1] = Northing (Y)
    """

    if csv_file and not coord_dict:
        with open(csv_vent_file, 'r') as csvfile:
            csvreader = csv.DictReader(csvfile, delimiter=';')
            row = next(csvreader)

            long = float(row['X'])
            lat = float(row['Y'])

    elif coord_dict and not csv_file:
        long = float(coords['lon'])
        lat = float(coords['lat'])

    else:
        raise ValueError('csv_file and coord_dict must be opposite boolean values.')

    half_size = vent_grid_size / 2.0

    x_array = np.arange(long - half_size, long + half_size + resolution / 2, resolution)

    y_array = np.arange(lat - half_size, lat + half_size + resolution / 2, resolution)

    X, Y = np.meshgrid(x_array, y_array, indexing='ij')

    grid = np.column_stack([X.ravel(),Y.ravel()])

    return grid

def grid_to_csv(grid: np.ndarray, path_to_results: str, flow_id: str) -> str:
    """ SAve vent grid to csv """
    os.makedirs(path_to_results, exist_ok=True)
    grid_csv = os.path.join(path_to_results, f'{flow_id}_ventgrid_coordinates.csv')

    df = pd.DataFrame({
        "flow_id": [f"{int(x)}_{int(y)}"
            for x, y in grid], "X": grid[:, 0], "Y": grid[:, 1]})

    df.to_csv(grid_csv,sep=';',index=False)

    return grid_csv

def path_stacker_helper(grid: dict, flow_id: str, path_to_results: str,resolution: float, epsg_code: str):
    """
    Builds both stacking products:
    - n1 mode: occurrence count
    - multi_n mode: probability sum
    """

    # ------------------------------------------------------------
    # 1. Multi-n (probability-weighted stack)
    # ------------------------------------------------------------
    sim_mastergrid, lon_X, lat_Y, sim_dict = path_stacker(
        grid=grid,
        flow_id=flow_id,
        path_to_results=path_to_results,
        resolution=resolution,
        epsg_code=epsg_code,
        n=True,
        helper=True
    )

    # ------------------------------------------------------------
    # 2. N1 (occurrence stack)
    # ------------------------------------------------------------
    n1_mastergrid, _, _, n1_dict = path_stacker(
        grid=grid,
        flow_id=flow_id,
        path_to_results=path_to_results,
        resolution=resolution,
        epsg_code=epsg_code,
        n=False,
        helper=True
    )

    # ------------------------------------------------------------
    # 3. Return everything consistently
    # ------------------------------------------------------------
    return {
        "sim": {
            "mastergrid": sim_mastergrid,
            "lon_X": lon_X,
            "lat_Y": lat_Y,
            "grid_dict": sim_dict
        },
        "n1": {
            "mastergrid": n1_mastergrid,
            "lon_X": lon_X,
            "lat_Y": lat_Y,
            "grid_dict": n1_dict
        }
    }

def path_stacker(grid: np.ndarray, flow_id: str, path_to_results: str, resolution: float, epsg_code: str, n=False,
                 helper=False):
    path_to_folder = path_to_results
    files = []
    lats = []
    lons = []
    grid_dict = {}

    grid_array = np.asarray(grid)

    # Accept both:
    # (N, M, 2) -> old grid format
    # (N, 2)    -> flattened grid format

    if grid_array.ndim == 3:
        coords = grid_array.reshape(-1, 2)

    elif grid_array.ndim == 2 and grid_array.shape[1] == 2:
        coords = grid_array

    else:
        raise ValueError(f"Unexpected grid format: {grid_array.shape}")
    for coord in coords:

        lon = int(coord[0])
        lat = int(coord[1])

        profile_tif = os.path.join(path_to_folder, f'profile_{lon}_{lat}_dH001_n1_sim.tif')
        sim_file = os.path.join(path_to_folder, f'sim_{lon}_{lat}.tif')
        if helper and not n:
            file = profile_tif
        else:
            file = sim_file

        files.append(file)
        lats.append(lat)
        lons.append(lon)

    # get corner coordinates and size of first raster and initialize master grid
    first_grid = rasterio.open(files[0])
    current_size = first_grid.shape
    first_grid_topleft = first_grid.transform * (0, 0)
    first_grid_topleft_X = first_grid_topleft[0]
    first_grid_topleft_Y = first_grid_topleft[1]
    first_grid_bottomright = first_grid.transform * (first_grid.width, first_grid.height)
    first_grid_bottomright_X = first_grid_bottomright[0]
    first_grid_bottomright_Y = first_grid_bottomright[1]
    # mastergrid_ncol = int((first_grid_bottomright_X - first_grid_topleft_X)/resolution) # this is redunant since we already have the size of the first grid
    # mastergrid_nrow = int((first_grid_topleft_Y - first_grid_bottomright_Y)/resolution)
    mastergrid_topleft = first_grid_topleft
    mastergrid_topleft_X = first_grid_topleft_X
    mastergrid_topleft_Y = first_grid_topleft_Y
    mastergrid_bottomright = first_grid_bottomright
    mastergrid_bottomright_X = first_grid_bottomright_X
    mastergrid_bottomright_Y = first_grid_bottomright_Y
    mastergrid = np.zeros((current_size))

    # begin path stacking
    first_path = first_grid.read(1)  # reads the probabilities from band 1 (which is the only band)
    for i, row in enumerate(first_path):
        for j, prob in enumerate(row):
            if prob > 0:
                if n:
                    mastergrid[i, j] += prob
                else:
                    mastergrid[i, j] += 1

    # the 0.5 multiplier is to center the coordinates in the pixel, as currently the coordinates represent top left
    # EDIT JUNE 3RD 2025: commented out the two below lines. The current_x and current_y arrays were larger than
    # their respective dimensions in the raster
    # current_x = np.arange(first_grid_topleft_X + 0.5*resolution, first_grid_bottomright_X+1.5*resolution, resolution)
    # current_y = np.arange(first_grid_topleft_Y-0.5*resolution, first_grid_bottomright_Y-1.5*resolution, -resolution)
    current_x = np.arange(first_grid_topleft_X + 0.5 * resolution, first_grid_bottomright_X + 0.5 * resolution,
                          resolution)
    current_y = np.arange(first_grid_topleft_Y - 0.5 * resolution, first_grid_bottomright_Y - 0.5 * resolution,
                          -resolution)
    grid_dict[str((lats[0], lons[0]))] = {'Coords': (lats[0], lons[0]),
                                          "Raster": first_path,
                                          'Longitude': np.round(current_x, decimals=6),
                                          'Latitude': np.round(current_y, decimals=6)}
    first_grid.close()
    # os.remove(files[0])

    # path stacking with adaptive master grid for remaining files
    for count, file in enumerate(files[1:], start=1):
        # get the corners of the current raster
        current_grid = rasterio.open(file)
        current_grid_topleft = current_grid.transform * (0, 0)
        current_grid_topleft_X = current_grid_topleft[0]
        current_grid_topleft_Y = current_grid_topleft[1]
        current_grid_bottomright = current_grid.transform * (current_grid.width, current_grid.height)
        current_grid_bottomright_X = current_grid_bottomright[0]
        current_grid_bottomright_Y = current_grid_bottomright[1]
        # JUNE 3RD 2025 EDIT: see above
        # current_x = np.arange(current_grid_topleft_X + 0.5*resolution, current_grid_bottomright_X+1.5*resolution, resolution)
        # current_y = np.arange(current_grid_topleft_Y - 0.5*resolution, current_grid_bottomright_Y-1.5*resolution, -resolution)
        current_x = np.arange(current_grid_topleft_X + 0.5 * resolution, current_grid_bottomright_X + 0.5 * resolution,
                              resolution)
        current_y = np.arange(current_grid_topleft_Y - 0.5 * resolution, current_grid_bottomright_Y - 0.5 * resolution,
                              -resolution)

        # compare w/ coordinates of current master grid
        x_coords = [current_grid_topleft_X, current_grid_bottomright_X, mastergrid_topleft_X, mastergrid_bottomright_X]
        max_X = max(x_coords)
        min_X = min(x_coords)

        y_coords = [current_grid_topleft_Y, current_grid_bottomright_Y, mastergrid_topleft_Y, mastergrid_bottomright_Y]
        max_Y = max(y_coords)
        min_Y = min(y_coords)

        # get new dimensions of mastergrid
        ncol = (max_X - min_X) / resolution
        nrow = (max_Y - min_Y) / resolution

        # get new mastergrid corner coordinates
        new_mastergrid_topleft = (min_X, max_Y)
        new_mastergrid_topleft_X = new_mastergrid_topleft[0]
        new_mastergrid_topleft_Y = new_mastergrid_topleft[1]

        new_mastergrid_bottomright = (max_X, min_Y)
        new_mastergrid_bottomright_X = new_mastergrid_bottomright[0]
        new_mastergrid_bottomright_Y = new_mastergrid_bottomright[1]

        # expand the mastergrid as needed
        # rows above
        add_to_top = round((new_mastergrid_topleft_Y - mastergrid_topleft_Y) / resolution)

        # rows below
        add_to_bottom = round((mastergrid_bottomright_Y - new_mastergrid_bottomright_Y) / resolution)

        # columns left
        add_to_left = round((mastergrid_topleft_X - new_mastergrid_topleft_X) / resolution)

        # columns right
        add_to_right = round((new_mastergrid_bottomright_X - mastergrid_bottomright_X) / resolution)

        mastergrid = np.pad(mastergrid, pad_width=((add_to_top, add_to_bottom), (add_to_left, add_to_right)))

        # reset mastergrid corner coordinates
        mastergrid_topleft = new_mastergrid_topleft
        mastergrid_topleft_X = new_mastergrid_topleft_X
        mastergrid_topleft_Y = new_mastergrid_topleft_Y
        mastergrid_bottomright = new_mastergrid_bottomright
        mastergrid_bottomright_X = new_mastergrid_bottomright_X
        mastergrid_bottomright_Y = new_mastergrid_bottomright_Y

        # get offsets between the current grid and the mastergrid
        row_offset = int((mastergrid_topleft_Y - current_grid_topleft_Y) / resolution)
        col_offset = int((current_grid_topleft_X - mastergrid_topleft_X) / resolution)

        # path stacking
        current_path = current_grid.read(1)
        for i, row in enumerate(current_path):
            for j, prob in enumerate(row):
                if prob > 0:
                    if n:
                        mastergrid[i + row_offset, j + col_offset] += prob  # Add the actual raster value
                    else:
                        mastergrid[i + row_offset, j + col_offset] += 1  # Count occurrences

        grid_dict[str((lats[count], lons[count]))] = {'Coords': (lats[count], lons[count]),
                                                      'Raster': current_path,
                                                      'Longitude': np.round(current_x, decimals=6),
                                                      'Latitude': np.round(current_y, decimals=6)}
        current_grid.close()
        # os.remove(file)

    # normalize the mastergrid
    mastergrid = mastergrid / np.amax(mastergrid)

    # create a geospatial raster from the mastergrid
    # generate array of x (longitude) values
    lon = np.arange(mastergrid_topleft_X, mastergrid_bottomright_X + resolution, resolution)

    # generate array of y (latitude) values
    lat = np.arange(mastergrid_topleft_Y, mastergrid_bottomright_Y - resolution, -resolution)

    # make them into grids
    lon_X, lat_Y = np.meshgrid(lon, lat)

    # Affine transform
    # transform = Affine.translation(lon_X[0][0]-resolution/2, lat_Y[0][0]-resolution/2)*Affine.scale(resolution, -resolution)
    transform = Affine.translation(lon_X[0][0], lat_Y[0][0]) * Affine.scale(resolution, -resolution)

    # get CRS
    crs = CRS.from_epsg(int(epsg_code))

    # export to geotiff
    if helper and n:
        # simfile = f'{path_to_results}/{flow_id}_ventgrid_sim_multi_n.tif'
        geotiff_name = "mastergrid_multi_n.tif"
    elif helper and not n:
        # simfile = f'{path_to_results}/{flow_id}_ventgrid_sim_n1.tif'
        geotiff_name = 'mastergrid_n1.tif'
    else:
        # simfile = f'{path_to_results}/{flow_id}_ventgrid_sim.tif'
        geotiff_name = 'mastergrid_sim.tif'
    simfile = os.path.join(path_to_folder, f'{flow_id}_{geotiff_name}')

    raster = rasterio.open(simfile, 'w', driver='GTiff', height=mastergrid.shape[0],
                           width=mastergrid.shape[1], count=1, dtype=mastergrid.dtype,
                           crs=crs, transform=transform)
    raster.write(mastergrid, 1)
    raster.close()

    return mastergrid, lon_X, lat_Y, grid_dict


def get_bounds(ds):
    """Return raster bounds in UTM"""
    t = ds.transform
    w, h = ds.width, ds.height

    x_min, y_max = t * (0, 0)
    x_max, y_min = t * (w, h)

    return x_min, x_max, y_min, y_max

def open_mastergrid(filename):
    # load in everything and extract data
    mastergrid_raster = rasterio.open(filename)
    mastergrid = mastergrid_raster.read(1)

    height, width = mastergrid.shape[0], mastergrid.shape[1]
    cols, rows = np.meshgrid(np.arange(width), np.arange(height))
    xs, ys = rasterio.transform.xy(mastergrid_raster.transform, rows, cols)
    lon, lat = np.round(np.array(xs), decimals=6), np.round(np.array(ys), decimals=6)

    mastergrid_raster_topleft_X, mastergrid_raster_topleft_Y = lon[0, 0], lat[0, 0]
    mastergrid_raster_bottomright_X, mastergrid_raster_bottomright_Y = lon[-1, -1], lat[-1, -1]
    mastergrid_raster.close()
    return mastergrid, lon, lat, mastergrid_raster_topleft_X, mastergrid_raster_topleft_Y, mastergrid_raster_bottomright_X, mastergrid_raster_bottomright_Y

def open_dem(dem, mastergrid_raster_topleft_X, mastergrid_raster_topleft_Y, mastergrid_raster_bottomright_X,
             mastergrid_raster_bottomright_Y):
    # load in the DEM and 'trim' it to be the size of the matergrid
    dem = rasterio.open(dem)
    elevations = dem.read(1)

    # get indicies where coordinates match mastergrid's top left and bottom right coordinates
    dem_top_x, dem_top_y = dem.index(mastergrid_raster_topleft_X, mastergrid_raster_topleft_Y)
    dem_bottom_x, dem_bottom_y = dem.index(mastergrid_raster_bottomright_X, mastergrid_raster_bottomright_Y)
    elevations = elevations[dem_top_x:dem_bottom_x + 1, dem_top_y:dem_bottom_y + 1]

    dem.close()
    return elevations

# -------------------------------------------------------------------------
# Dijkstra until reaching any cell on a target "edge" set (8-connected)
# -------------------------------------------------------------------------
def dijkstra_until_edge(cost, start, edge_cells, cell_size):
    """
    Run Dijkstra's algorithm on a regular grid until the first cell belonging
    to `edge_cells` is reached. Returns the path as a list of (row, col).

    Parameters
    ----------
    cost : np.ndarray (H x W, float)
        Per-cell traversal cost surrogate. Cells with cost >= 9999 are treated as blocked.
        NOTE: The actual edge cost is cost[next_cell] * step_length.
    start : Tuple[int, int]
        Starting (row, col).
    edge_cells : Iterable[Tuple[int, int]]
        Set (or list) of boundary cells where we want to stop.
    cell_size : float
        Cell size in map units (meters).

    Returns
    -------
    path : List[Tuple[int, int]]
        Sequence of (row, col) from start to the first reached edge cell,
        or empty list if no path exists.
    """
    rows, cols = cost.shape
    edge_cells = set(map(tuple, edge_cells))  # fast lookup

    # 8-connected neighborhood with geometric length factors
    neighbors = [
        (-1,  0, 1.0),
        ( 1,  0, 1.0),
        ( 0, -1, 1.0),
        ( 0,  1, 1.0),
        (-1, -1, math.sqrt(2)),
        (-1,  1, math.sqrt(2)),
        ( 1, -1, math.sqrt(2)),
        ( 1,  1, math.sqrt(2)),
    ]

    INF = 1e30
    dist = np.full((rows, cols), INF, dtype=float)
    prev = {}  # (r,c) -> (r_parent, c_parent)

    sr, sc = int(start[0]), int(start[1])
    dist[sr, sc] = 0.0

    pq = [(0.0, (sr, sc))]  # (distance, (r,c))

    while pq:
        d, (r, c) = heapq.heappop(pq)
        if d > dist[r, c]:
            continue

        # Stop immediately upon reaching any edge cell
        if (r, c) in edge_cells:
            path = [(r, c)]
            while (r, c) in prev:
                r, c = prev[(r, c)]
                path.append((r, c))
            return path[::-1]

        # Explore 8 neighbors
        for dr, dc, step_factor in neighbors:
            rr, cc = r + dr, c + dc
            if rr < 0 or rr >= rows or cc < 0 or cc >= cols:
                continue

            # Treat very large cost as blocked
            if cost[rr, cc] >= 9999:
                continue

            step_len = step_factor * cell_size
            nd = d + cost[rr, cc] * step_len

            if nd < dist[rr, cc]:
                dist[rr, cc] = nd
                prev[(rr, cc)] = (r, c)
                heapq.heappush(pq, (nd, (rr, cc)))

    # No path found
    return []

# -------------------------------------------------------------------------
# Main function: robust pathfinding with vectorized trimming + Dijkstra
# -------------------------------------------------------------------------
def pathfinder(dem_resolution,grid,path_to_results,flow_id,dem,epsg_code,filename,edge=True,flowgo=False):
    """
    Compute an optimal path from a source cell (derived from the probability grid)
    to the vent-grid boundary using Dijkstra on a raster cost surface.

    Steps:
    - Read single-payj mastergrid (probability) and DEM cropped to the master extent.
    - Normalize probabilities and perform a safe vectorized trim of all-zero margins.
    - Robustly determine a source cell on left/right edges of the non-zero rows.
    - Identify the vent-grid rectangle inside the mastergrid and homogenize inner probs.
    - Run Dijkstra until the vent-grid boundary is reached.
    - Extract X/Y/Z, compute cumulative distance L and slope, write TXT and SHP.

    Parameters
    ----------
    dem_resolution : float
        Cell size in meters (used for neighbor step lengths in Dijkstra).
    grid : np.ndarray
        Vent grid coordinates. grid[0,0] is near top-left; grid[-1,-1] near bottom-right (x,y).
    path_to_results : str
        Output directory.
    flow_id : str
        Identifier used in output filenames.
    dem : str
        Path to DEM raster.
    epsg_code : int
        EPSG code for the output shapefile.
    filename : str
        Path to the probability master grid raster (read by open_mastergrid).
    edge : bool, default=True
        If True, stop at the vent-grid boundary (this function assumes True).
    flowgo : bool, default=False
        If True, write a CSV with the vent-grid intersection point.

    Returns
    -------
    (lon_ventgrid_intersection, lat_ventgrid_intersection, pathfinder_slope_file_shp) : Tuple[float, float, str]
    """

    grid = np.asarray(grid)

    if grid.ndim == 2 and grid.shape[1] == 2:
        # reconstruct square grid
        n = int(np.sqrt(len(grid)))
        grid = grid.reshape(n, n, 2)

    elif grid.ndim != 3:
        raise ValueError(
            f"Unexpected grid format: {grid.shape}"
        )
    # ---------------------------------------------------------------------
    # Load data (user-provided helpers)
    # mastergrid: 2D probability array; lon/lat: 2D coordinates matching mastergrid
    # mrtX/mrtY, mrbX/mrbY: bounding coords used to crop DEM accordingly
    # ---------------------------------------------------------------------
    (mastergrid, lon, lat, mrtX, mrtY, mrbX, mrbY) = open_mastergrid(filename)
    elevations = open_dem(dem, mrtX, mrtY, mrbX, mrbY)

    # ---------------------------------------------------------------------
    # Check normalization [0,1]
    # ---------------------------------------------------------------------
    if np.amax(mastergrid) <= 0:
        raise ValueError("Probability grid is entirely zero (or invalid).")
    probabilities = mastergrid

    # ---------------------------------------------------------------------
    # Vectorized trim: remove rows/cols that are all zeros
    # (apply the same slicing to probabilities, elevations, lon, lat)
    # ---------------------------------------------------------------------
    row_keep = (probabilities > 0).any(axis=1)
    col_keep = (probabilities > 0).any(axis=0)

    probabilities = probabilities[row_keep][:, col_keep]
    elevations = elevations[row_keep][:, col_keep]
    lon = lon[row_keep][:, col_keep]
    lat = lat[row_keep][:, col_keep]

    # Safety: ensure not empty after trim
    if probabilities.size == 0:
        raise ValueError("After trimming, probability grid is empty (all-zero input).")

    # Safety: shapes alignment (crop to min common shape if needed)
    H = min(probabilities.shape[0], elevations.shape[0], lon.shape[0], lat.shape[0])
    W = min(probabilities.shape[1], elevations.shape[1], lon.shape[1], lat.shape[1])
    probabilities = probabilities[:H, :W]
    elevations = elevations[:H, :W]
    lon = lon[:H, :W]
    lat = lat[:H, :W]

    # ---------------------------------------------------------------------
    # Find a robust source cell:
    # For each non-zero row, take leftmost/rightmost non-zero and choose
    # the side with higher probability. Then break ties by local 3x3 max,
    # then by minimal elevation.
    # ---------------------------------------------------------------------
    intersections_cols = [None] * H
    for i in range(H):
        nz = np.flatnonzero(probabilities[i] > 0)
        if nz.size == 0:
            continue
        left, right = int(nz[0]), int(nz[-1])
        intersections_cols[i] = right if probabilities[i, right] > probabilities[i, left] else left

    valid_rows = [i for i, c in enumerate(intersections_cols) if c is not None]
    if not valid_rows:
        raise ValueError("Unable to determine a source cell: all rows are zero.")

    inter_probs = np.array([probabilities[i, intersections_cols[i]] for i in valid_rows])
    best_prob = inter_probs.max()
    candidate_rows = [valid_rows[k] for k in np.where(inter_probs == best_prob)[0]]

    if len(candidate_rows) == 1:
        start_row = candidate_rows[0]
        start_col = intersections_cols[start_row]
    else:
        # tie-breaker 1: local 3x3 maximum probability around the candidate
        def local_max(i, j):
            r0, r1 = max(0, i-1), min(H, i+2)
            c0, c1 = max(0, j-1), min(W, j+2)
            return probabilities[r0:r1, c0:c1].max()
        scores = np.array([local_max(i, intersections_cols[i]) for i in candidate_rows])
        best = scores.max()
        chosen_rows = [candidate_rows[k] for k in np.where(scores == best)[0]]

        if len(chosen_rows) == 1:
            start_row = chosen_rows[0]
            start_col = intersections_cols[start_row]
        else:
            # tie-breaker 2: minimal elevation at the candidate
            elevs = np.array([elevations[i, intersections_cols[i]] for i in chosen_rows])
            kmin = int(np.nanargmin(elevs))
            start_row = chosen_rows[kmin]
            start_col = intersections_cols[start_row]

    start = (int(start_row), int(start_col))

    # ---------------------------------------------------------------------
    # Identify vent-grid bounding rectangle inside the master grid
    # (using closest columns/rows to the given grid corner coordinates)
    # ---------------------------------------------------------------------
    lon_diff_topleft = np.abs(lon - grid[0, 0][0])
    lat_diff_topleft = np.abs(lat - grid[0, 0][1])
    col_left   = int(np.argmin(lon_diff_topleft[0, :]))   # column for top-left x
    row_bottom = int(np.argmin(lat_diff_topleft[:, 0]))   # row    for top-left y

    lon_diff_bottomright = np.abs(lon - grid[-1, -1][0])
    lat_diff_bottomright = np.abs(lat - grid[-1, -1][1])
    col_right = int(np.argmin(lon_diff_bottomright[0, :])) # column for bottom-right x
    row_top   = int(np.argmin(lat_diff_bottomright[:, 0])) # row    for bottom-right y

    # Sort to ensure (rmin, rmax), (cmin, cmax)
    rmin, rmax = sorted([row_top, row_bottom])
    cmin, cmax = sorted([col_left, col_right])

    # Keep indices inside bounds (just in case)
    rmin = max(0, min(rmin, H-1))
    rmax = max(0, min(rmax, H-1))
    cmin = max(0, min(cmin, W-1))
    cmax = max(0, min(cmax, W-1))

    # ---------------------------------------------------------------------
    # Homogenize probabilities inside the vent-grid interior so that the
    # shortest path aims for the boundary, not biased by inner variations.
    # ---------------------------------------------------------------------
    probabilities_copy = probabilities.copy()
    if (rmax - rmin >= 2) and (cmax - cmin >= 2):
        probabilities_copy[rmin+1:rmax, cmin+1:cmax] = 0.001  # inner area
    # otherwise, 1-cell-thick rectangle has no interior to homogenize

    # Vent-grid rows/cols for boundary (stop set for Dijkstra)
    ventgrid_toprow    = [(rmin, j) for j in range(cmin, cmax+1)]
    ventgrid_bottomrow = [(rmax, j) for j in range(cmin, cmax+1)]
    ventgrid_leftcol   = [(i, cmin) for i in range(rmin, rmax+1)]
    ventgrid_rightcol  = [(i, cmax) for i in range(rmin, rmax+1)]
    edge_cells = set(ventgrid_toprow + ventgrid_bottomrow + ventgrid_leftcol + ventgrid_rightcol)

    # ---------------------------------------------------------------------
    # Dijkstra on a simple per-cell cost surface:
    # - low cost = high probability
    # - cost == 9999 => blocked
    # You can later replace this by a combined cost (prob + slope penalty)
    # ---------------------------------------------------------------------
    cost = np.where(probabilities_copy == 0, 9999.0, 1.0 - probabilities_copy)

    path = dijkstra_until_edge(
        cost=cost,
        start=start,
        edge_cells=edge_cells,
        cell_size=dem_resolution)

    if not path:
        raise RuntimeError("Dijkstra failed: no path from source to the vent-grid boundary.")

    # ---------------------------------------------------------------------
    # Extract coordinates and elevations along the path
    # NOTE: path is in order source -> boundary (no reverse)
    # ---------------------------------------------------------------------
    X, Y, Z = [], [], []
    for (ri, ci) in path:
        X.append(float(lon[ri, ci]))
        Y.append(float(lat[ri, ci]))
        Z.append(float(elevations[ri, ci]))

    # Optional: enforce monotonic "upflow" to avoid negative slopes (simple fix)
    for k in range(1, len(Z)):
        if Z[k] <= Z[k-1]:
            Z[k] = Z[k-1] + 0.01  # small epsilon in elevation units

    # Vent-grid intersection: last point (boundary hit)
    lat_ventgrid_intersection = Y[-1]
    lon_ventgrid_intersection = X[-1]

    # ---------------------------------------------------------------------
    # Compute cumulative distance L and slope profile (degrees)
    # Distances are Euclidean in meters (CRS is metric)
    # ---------------------------------------------------------------------
    distances_between_points = [0.0]
    for r in range(1, len(Y)):
        dx = X[r] - X[r - 1]
        dy = Y[r] - Y[r - 1]
        distances_between_points.append(math.hypot(dx, dy))

    L = [0.0]
    for r in range(1, len(Y)):
        L.append(L[-1] + distances_between_points[r])

    slope = []
    for r in range(1, len(L)):
        dZ = Z[r - 1] - Z[r]
        dL = L[r] - L[r - 1]
        angle = math.degrees(math.atan2(dZ, dL)) if dL != 0 else 0.0
        slope.append(angle)
    slope.append(0.0)  # pad last value

    # ---------------------------------------------------------------------
    # Outputs: TXT + SHP
    # ---------------------------------------------------------------------
    os.makedirs(path_to_results, exist_ok=True)

    df = pd.DataFrame({
        'x': X,
        'y': Y,
        'z': Z,
        'L': L,
        'slope': slope
    })

    pathfinder_slope_file = os.path.join(path_to_results, f'map/pathfinder_{flow_id}.txt')
    pathfinder_slope_file_shp = os.path.join(path_to_results, f'map/pathfinder_{flow_id}.shp')

    df.to_csv(pathfinder_slope_file, sep='\t', index=False)
    # Convert TXT to shapefile
    txt_to_shape.get_path_shp(pathfinder_slope_file, pathfinder_slope_file_shp, epsg_code)

    # Optional CSV with the intersection point
    if flowgo:
        csv_vent_file = os.path.join(path_to_results, f'{flow_id}_edge_vent.csv')
        pd.DataFrame(
            {'flow_id': [flow_id], 'X': [lon_ventgrid_intersection], 'Y': [lat_ventgrid_intersection]}
        ).to_csv(csv_vent_file, sep=';', index=False)

    return lon_ventgrid_intersection, lat_ventgrid_intersection, pathfinder_slope_file_shp

def get_average_run_outs(path_to_results: str, flow_id: str, start: float, stop: float, step: float,
                         pathfinder_slope_file_shp: str):
    ##############################################################################

    # path_to_flowgo_results = os.path.join(path_to_results, f"vent_{flow_id}")
    output_csv = os.path.join(path_to_results, 'run_outs.csv')
    df = pd.read_csv(output_csv)
    # get the pathfinder from the piel ?
    colxn = fiona.open(pathfinder_slope_file_shp)
    # colxn = fiona.open(os.path.join(path_to_results, f'{flow_id}_pathfinder.shp'))
    feat = next(iter(colxn))
    geom = feat.geometry['coordinates']
    colxn.close()
    linestring = shapely.LineString(geom)

    means_x = []
    means_y = []
    medians_x = []
    medians_y = []
    p25_x = []
    p25_y = []
    p75_x = []
    p75_y = []
    xs_2sig = []
    ys_2sig = []
    xs_2sig_minus = []
    ys_2sig_minus = []

    effusion_rate_array = np.arange(start, stop + step, step)

    # Calculates statistics for each effusion rate
    for eff in effusion_rate_array:
        eff_string_x = f'X_run_out_{eff:.1f}'
        eff_string_y = f'Y_run_out_{eff:.1f}'
        run_outs_x = df[eff_string_x]
        run_outs_y = df[eff_string_y]

        points_on_profile = []
        dist_error = []
        distance_from_edge = []

        for (x, y) in zip(run_outs_x, run_outs_y):
            point = shapely.Point(x, y)
            shortest_line = shapely.shortest_line(point, linestring)
            xi = shortest_line.bounds[2]
            yi = shortest_line.bounds[3]
            points_on_profile.append((xi, yi))
            error = np.sqrt((yi - y) ** 2 + (xi - x) ** 2)
            dist_error.append(error)
            dist_from = shapely.line_locate_point(linestring, point)
            distance_from_edge.append(dist_from)

        # Statistics
        average_distance = np.mean(distance_from_edge)
        stdev = np.std(distance_from_edge)
        sig_x2 = average_distance + 2 * stdev
        sig_x2_minus = average_distance - 2 * stdev
        average_point = shapely.line_interpolate_point(linestring, average_distance)
        average_x = average_point.x
        means_x.append(average_x)
        average_y = average_point.y
        means_y.append(average_y)
        point_2sig = shapely.line_interpolate_point(linestring, sig_x2)
        x_2sig = point_2sig.x
        xs_2sig.append(x_2sig)
        y_2sig = point_2sig.y
        ys_2sig.append(y_2sig)
        point_2sig_minus = shapely.line_interpolate_point(linestring, sig_x2_minus)
        x_2sig_minus = point_2sig_minus.x
        xs_2sig_minus.append(x_2sig_minus)
        y_2sig_minus = point_2sig_minus.y
        ys_2sig_minus.append(y_2sig_minus)

        med_distance = np.median(distance_from_edge)
        p25_distance = np.quantile(distance_from_edge, 0.25)
        p75_distance = np.quantile(distance_from_edge, 0.75)
        med_point = shapely.line_interpolate_point(linestring, med_distance)
        med_point_x = med_point.x
        medians_x.append(med_point_x)
        med_point_y = med_point.y
        medians_y.append(med_point_y)
        p25_point = shapely.line_interpolate_point(linestring, p25_distance)
        p25_point_x = p25_point.x
        p25_x.append(p25_point_x)
        p25_point_y = p25_point.y
        p25_y.append(p25_point_y)
        p75_point = shapely.line_interpolate_point(linestring, p75_distance)
        p75_point_x = p75_point.x
        p75_x.append(p75_point_x)
        p75_point_y = p75_point.y
        p75_y.append(p75_point_y)

    new_df = pd.DataFrame({'Effusion Rate': effusion_rate_array,
                           'Median X': medians_x,
                           'Median Y': medians_y,
                           '25th Percentile X': p25_x,
                           '25th Percentile Y': p25_y,
                           '75th Percentile X': p75_x,
                           '75th Percentile Y': p75_y,
                           'Average X': means_x,
                           'Average Y': means_y,
                           '+2sigma X': xs_2sig,
                           '+2sigma Y': ys_2sig,
                           '-2sigma X': xs_2sig_minus,
                           '-2sigma Y': ys_2sig_minus})

    # writes statistics to a CSV file
    average_run_outs = os.path.join(path_to_results, 'average_run_outs.csv')
    new_df.to_csv(average_run_outs)
    return average_run_outs

def losd_passes_near_point(latitude, longitude,lat_intersect, lon_intersect,tol):
    coords = list(zip(longitude, latitude))
    line = LineString(coords)
    p = Point(lon_intersect, lat_intersect)
    return line.distance(p) <= tol

def export_contributing_vents(contributing_vents, path_to_results, flow_id, epsg_code):
    """
    Export contributing vents coordinates as CSV and shapefile.

    Parameters
    ----------
    contributing_vents : dict
        Dictionary returned by find_contributing_vents().
        Each entry must contain:
            - "Coords": (lat, lon)

    path_to_results : str
        Output directory.

    flow_id : str
        Flow identifier.

    epsg_code : int
        EPSG code of the coordinates.

    Returns
    -------
    csv_file, shp_file
    """

    vents = []

    for vent_key, vent_data in contributing_vents.items():

        # path_stacker stores coordinates as (lat, lon)
        lat, lon = vent_data["Coords"]

        vents.append({
            "vent_id": str(vent_key),
            "X": float(lon),
            "Y": float(lat)
        })

    if len(vents) == 0:
        raise ValueError("No contributing vents to export.")

    # ------------------------------------------------------------
    # CSV export
    # ------------------------------------------------------------
    df = pd.DataFrame(vents)

    csv_file = os.path.join(
        path_to_results,
        f"{flow_id}_contributing_vents.csv"
    )

    df.to_csv(
        csv_file,
        sep=";",
        index=False
    )

    # ------------------------------------------------------------
    # Convert CSV to shapefile
    # ------------------------------------------------------------
    shp_file = os.path.join(
        path_to_results,
        f"{flow_id}_contributing_vents.shp"
    )

    schema = {
        "geometry": "Point",
        "properties": {
            "vent_id": "str",
            "X": "float",
            "Y": "float"
        }
    }

    with fiona.open(
        shp_file,
        "w",
        driver="ESRI Shapefile",
        crs=CRS.from_epsg(int(epsg_code)).to_wkt(),
        schema=schema
    ) as shp:

        for _, row in df.iterrows():

            point = Point(
                row["X"],
                row["Y"]
            )

            shp.write({
                "geometry": {
                    "type": "Point",
                    "coordinates": point.coords[0]
                },
                "properties": {
                    "vent_id": row["vent_id"],
                    "X": row["X"],
                    "Y": row["Y"]
                }
            })

    print("Contributing vents exported:")
    print(f"  CSV: {csv_file}")
    print(f"  SHP: {shp_file}")

    return csv_file, shp_file