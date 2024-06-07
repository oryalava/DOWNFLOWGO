import fiona
import matplotlib.pyplot as plt
from shapely.geometry import shape
import matplotlib.colors as colors
import rasterio
from PIL import Image
from adjustText import adjust_text
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.cm import ScalarMappable
from matplotlib.patches import Polygon
import os
import datetime

#if __name__ == "__main__":

def create_map_downflowgo(path_to_folder, dem, flow_id, map_layers):

    current_datetime = datetime.datetime.now()
    Date = current_datetime.strftime('%d-%m-%y %H:%M')

    losd_path = path_to_folder + '/map/path_' + flow_id + '.shp'
    vent_path = path_to_folder + '/map/vent_' + flow_id + '.shp'
    run_outs_path = path_to_folder + '/map/run_outs_' + flow_id + '.shp'
    sim_tif_file = path_to_folder + '/map/sim_' + flow_id + '.tif'

    tiff_file = map_layers['tiff_file']
    lavaflow_outline_path = map_layers['lava_flow_outline_path']
    station_ovpf_path = map_layers.get('station_ovpf_path')  # Récupérer le chemin d'accès aux stations OVPF
    logo = map_layers['logo']


    # Create the map figure
    fig, ax = plt.subplots(figsize=(8, 7))

    # Load the TIFF image with Pillow, convert it to RGB and read
    tiff_image = Image.open(tiff_file)
    tiff_image_rgb = tiff_image.convert('RGB')
    with rasterio.open(tiff_file) as src:
        tiff_image = src.read(1)
        extent = src.bounds

    # Display the TIFF image as the background
    tif = ax.imshow(tiff_image_rgb, extent=(extent.left, extent.right, extent.bottom, extent.top))

    # ------------ plot simulation .tiff ----------

    # Load the compressed GeoTIFF file and extract the necessary information and data
    with rasterio.open(sim_tif_file) as src:
        data = src.read(1)
        transform = src.transform

    # Define value intervals and associated colors
    intervals = [0, 1, 10, 100, 1000, 10000]  # color intervals
    colors_list = ['none', 'gold', 'orange', 'orangered', 'red']  # associated colors
    colors_list2 = ['gold', 'orange', 'darkorange', 'orangered', 'red']  # colors for colorbar

    # Create a colormap for the legend colorbar
    cmap = colors.LinearSegmentedColormap.from_list('my_colormap', colors_list, N=256)
    bounds = [v - 0.5 for v in intervals]
    norm = colors.BoundaryNorm(bounds, cmap.N)

    # Plot the simulation data on the map
    sim = ax.imshow(data, extent=(transform[2], transform[2] + transform[0] * data.shape[1],
                                  transform[5] + transform[4] * data.shape[0], transform[5]),  # Flip the y-axis
                    cmap=cmap, norm=norm)

    # Set the limit of the figure based on used DEM
    with open(dem) as file:
        header_lines = [next(file) for _ in range(6)]
        ncols_dem = int(header_lines[0].split()[1])
        nrows_dem = int(header_lines[1].split()[1])
        xllcorner_dem = float(header_lines[2].split()[1])
        yllcorner_dem = float(header_lines[3].split()[1])
        cellsize_dem = float(header_lines[4].split()[1])
        nodata_value = float(header_lines[5].split()[1])

    ax.set_xlim(xllcorner_dem, xllcorner_dem + ncols_dem * cellsize_dem)
    ax.set_ylim(yllcorner_dem, yllcorner_dem + nrows_dem * cellsize_dem)

    # ------------ Plot lava flow outline and stations ----------

    if lavaflow_outline_path == str(0):
        pass
    else:
        lavaflow_outline = fiona.open(lavaflow_outline_path)
    # Plot the lavaflow outline layer
        for feature in lavaflow_outline:
            geometry = shape(feature['geometry'])
            if geometry.geom_type == 'Polygon':
                coordinates = geometry.exterior.coords.xy
                x = coordinates[0]
                y = coordinates[1]
                polygon_coords = list(zip(x, y))
                polygon = Polygon(polygon_coords, edgecolor='black', facecolor='none')
                ax.add_patch(polygon)

    if station_ovpf_path == str(0):
        pass
    else:
        station_ovpf = fiona.open(station_ovpf_path)

    # Plot stations ovpf vector layer
        label_station = []
        point_station = []
        for feature in station_ovpf:
            geometry = shape(feature['geometry'])
            properties = feature['properties']
            if geometry.geom_type == 'Point':
                x, y = geometry.x, geometry.y
                point_station.append((x, y))
                label_station.append(properties['Name'])
                ax.plot(x, y, 'k.')
        # sort out the point according their coordinates y
        sorted_points = sorted(zip(point_station, label_station), key=lambda p: p[0][1])
        # Displaying station_ovpf labels with automatic adjustment of label positions to avoid overlapping
        text_station = []
        previous_y = None
        for (x, y), label in sorted_points:
            if previous_y is None or y - previous_y > 5:  #value in UTM between two points
                text_station.append(ax.annotate(label, (x, y), xytext=(-1, 1), color='k', fontsize=7, textcoords='offset points'))
                previous_y = y
        adjust_text(text_station)

    # ------------ Plot vector layers simulation path + vent + run out ----------

    # Load vector layers
    losd = fiona.open(losd_path)
    vent = fiona.open(vent_path)
    run_outs = fiona.open(run_outs_path)


    # Plot the LOSD vector layer
    for feature in losd:
        geometry = shape(feature['geometry'])
        if geometry.geom_type == 'LineString':
            x, y = geometry.xy
            ax.plot(x, y, 'darkred')

    # Plot the vent vector layer
    for feature in vent:
        geometry = shape(feature['geometry'])
        if geometry.geom_type == 'Point':
            x, y = geometry.x, geometry.y
            ax.plot(x, y, 'r^', markersize=10)

    # Plot the run_outs vector layer
    points = []
    labels = []
    for feature in run_outs:
        geometry = shape(feature['geometry'])
        properties = feature['properties']
        if geometry.geom_type == 'Point':
            x, y = geometry.x, geometry.y
            points.append((x, y))
            labels.append(properties['Effusion_r'])
            ax.plot(x, y, 'b', marker=7)

    # Create a dictionary to keep only the smallest label for each unique point
    unique_points = {}
    for (x, y), label in zip(points, labels):
        if (x, y) not in unique_points or label < unique_points[(x, y)]:
            unique_points[(x, y)] = label

    # Convert dictionary back to sorted list of points and labels
    sorted_points = sorted(unique_points.items(), key=lambda p: p[0][1])
    # Displaying runout labels with automatic adjustment and automatic adjustment of label positions
    # to avoid overlapping
    texts = []
    previous_y = None
    for (x, y), label in sorted_points:
        if previous_y is None or y - previous_y > 5:  # Ajuster la valeur selon votre besoin (en utm)
            texts.append(ax.annotate(label, (x, y), xytext=(-3, 5), color='blue', fontsize=10, textcoords='offset points'))
            previous_y = y
        else:
            # If labels are too close, move the label and draw a line
            offset_x, offset_y = 5, 5
            texts.append(ax.annotate(
                label, (x, y), xytext=(x + offset_x, y + offset_y),
                arrowprops=dict(arrowstyle="->", color='b'), color='b', fontsize=10
            ))
    adjust_text(texts)


    # ------------ Add legend and colorbar ------------

    # Add the legend image to the map
    ax.plot([], [], 'r^', markersize=7, label='Bouche éruptive ('+ flow_id+')')
    ax.plot([], [], '-r', label='Trajectoire principale')
    ax.plot([], [], 'bv', markersize=5, label='Distances atteintes \npour un débit donné (m$^{3}$/s)')

    if station_ovpf_path == str(0):
        pass
    else:
        ax.plot([], [], 'k.', markersize=5, label='Stations OVPF')

    if lavaflow_outline_path == str(0):
        pass
    else:
        ax.plot([], [], 'k-', markersize=10, label='Contour de la coulée')

    legend=ax.legend(bbox_to_anchor=(1, 0.7), loc="upper left", fontsize='8')
    legend.get_frame().set_linewidth(0)
    # Adjust the figure size
    fig.subplots_adjust(right=0.7)
    fig.subplots_adjust(left=0.1)
    fig.subplots_adjust(top=0.9)
    fig.subplots_adjust(bottom=0.1)

    # Create a colorbar for the simulation data in raster
    cax = fig.add_axes([0.71, 0.70, 0.2, 0.02])  # Coordinates and size of the axis
    # Create the colorbar with the colors of the intervals
    norm2 = colors.Normalize(vmin=min(intervals), vmax=max(intervals))
    cmap2 = colors.LinearSegmentedColormap.from_list('my_colormap', colors_list2, N=256)
    sm = ScalarMappable(cmap=cmap2, norm=norm2)
    sm.set_array([])  # Set empty array for the colorbar
    cbar = plt.colorbar(sm, cax=cax, orientation='horizontal')
    cbar.ax.set_title("Simulation DOWNFLOWGO \nProbabilité de passage de la coulée\n ", fontsize=8, loc='left')
    cbar.set_label("Basse                        Haute", fontsize=8, loc='left')
    cbar.set_ticks([])
    cbar.set_ticklabels([])
    #cbar.ax.set_position([0.71, 0.71, 0.2, 0.05])

    # Load Logo image
    img = plt.imread(logo)
    logo_box = OffsetImage(img, zoom=0.05)  # size of the logo
    logo_anchor = (1.2, 0.02)  # Define the coordinate of the image anchor
    # Create the annotation of the image (remove frame
    ab = AnnotationBbox(logo_box, logo_anchor, xycoords='axes fraction', frameon=False)
    ax.add_artist(ab)

    # ------------ Final adjustments ------------

    #show label from y axis en completo
    #formatter = ScalarFormatter(useMathText=False)
    #formatter.set_scientific(False)
    #ax.yaxis.set_major_formatter(formatter)

    # Adjust the position of the legend and colorbar
    # Rotate label of Y and orientate vertically
    ax.set_yticks(ax.get_yticks())
    ax.set_yticklabels(ax.get_yticklabels(), rotation='vertical')
    ax.set_title('Carte de simulation DOWNFLOWGO pour l\'éruption en cours\n' + str(Date))

    plt.savefig(path_to_folder+'/map_'+ flow_id+'.png', dpi=300, bbox_inches='tight')
    #plt.savefig('./map.png', dpi=300, bbox_inches='tight')

    # Show the figure
    plt.show()


def create_map_downflow(path_to_folder, dem, flow_id, map_layers):

    current_datetime = datetime.datetime.now()
    Date = current_datetime.strftime('%d-%m-%y %H:%M')

    losd_path = path_to_folder + '/map/path_' + flow_id + '.shp'
    vent_path = path_to_folder + '/map/vent_' + flow_id + '.shp'
    sim_tif_file = path_to_folder + '/map/sim_' + flow_id + '.tif'

    tiff_file = map_layers['tiff_file']
    lavaflow_outline_path = map_layers['lava_flow_outline_path']
    station_ovpf_path = map_layers.get('station_ovpf_path')  # Récupérer le chemin d'accès aux stations OVPF
    logo = map_layers['logo']


    # Create the map figure
    fig, ax = plt.subplots(figsize=(8, 7))

    # Load the TIFF image with Pillow, convert it to RGB and read
    tiff_image = Image.open(tiff_file)
    tiff_image_rgb = tiff_image.convert('RGB')
    with rasterio.open(tiff_file) as src:
        tiff_image = src.read(1)
        extent = src.bounds

    # Display the TIFF image as the background
    tif = ax.imshow(tiff_image_rgb, extent=(extent.left, extent.right, extent.bottom, extent.top))

    # ------------ plot simulation .tiff ----------

    # Load the compressed GeoTIFF file and extract the necessary information and data
    with rasterio.open(sim_tif_file) as src:
        data = src.read(1)
        transform = src.transform

    # Define value intervals and associated colors
    intervals = [0, 1, 10, 100, 1000, 10000]  # color intervals
    colors_list = ['none', 'gold', 'orange', 'orangered', 'red']  # associated colors
    colors_list2 = ['gold', 'orange', 'darkorange', 'orangered', 'red']  # colors for colorbar

    # Create a colormap for the legend colorbar
    cmap = colors.LinearSegmentedColormap.from_list('my_colormap', colors_list, N=256)
    bounds = [v - 0.5 for v in intervals]
    norm = colors.BoundaryNorm(bounds, cmap.N)

    # Plot the simulation data on the map
    sim = ax.imshow(data, extent=(transform[2], transform[2] + transform[0] * data.shape[1],
                                  transform[5] + transform[4] * data.shape[0], transform[5]),  # Flip the y-axis
                    cmap=cmap, norm=norm)

    # Set the limit of the figure based on used DEM
    with open(dem) as file:
        header_lines = [next(file) for _ in range(6)]
        ncols_dem = int(header_lines[0].split()[1])
        nrows_dem = int(header_lines[1].split()[1])
        xllcorner_dem = float(header_lines[2].split()[1])
        yllcorner_dem = float(header_lines[3].split()[1])
        cellsize_dem = float(header_lines[4].split()[1])
        nodata_value = float(header_lines[5].split()[1])

    ax.set_xlim(xllcorner_dem, xllcorner_dem + ncols_dem * cellsize_dem)
    ax.set_ylim(yllcorner_dem, yllcorner_dem + nrows_dem * cellsize_dem)

    # ------------ Plot lava flow outline and stations ----------

    if lavaflow_outline_path == str(0):
        pass
    else:
        lavaflow_outline = fiona.open(lavaflow_outline_path)
    # Plot the lavaflow outline layer
        for feature in lavaflow_outline:
            geometry = shape(feature['geometry'])
            if geometry.geom_type == 'Polygon':
                coordinates = geometry.exterior.coords.xy
                x = coordinates[0]
                y = coordinates[1]
                polygon_coords = list(zip(x, y))
                polygon = Polygon(polygon_coords, edgecolor='black', facecolor='none')
                ax.add_patch(polygon)

    if station_ovpf_path == str(0):
        pass
    else:
        station_ovpf = fiona.open(station_ovpf_path)

    # Plot stations ovpf vector layer
        label_station = []
        point_station = []
        for feature in station_ovpf:
            geometry = shape(feature['geometry'])
            properties = feature['properties']
            if geometry.geom_type == 'Point':
                x, y = geometry.x, geometry.y
                point_station.append((x, y))
                label_station.append(properties['Name'])
                ax.plot(x, y, 'k.')
        # sort out the point according their coordinates y
        sorted_points = sorted(zip(point_station, label_station), key=lambda p: p[0][1])
        # Displaying station_ovpf labels with automatic adjustment of label positions to avoid overlapping
        text_station = []
        previous_y = None
        for (x, y), label in sorted_points:
            if previous_y is None or y - previous_y > 10:  #value in UTM between two points
                text_station.append(ax.annotate(label, (x, y), xytext=(-1, 1), color='k', fontsize=7, textcoords='offset points'))
                previous_y = y
            else:
                # If labels are too close, move the label and draw a line
                offset_x, offset_y = 10, 10
                text_station.append(ax.annotate(
                    label, (x, y), xytext=(x + offset_x, y + offset_y),
                    arrowprops=dict(arrowstyle="->", color='k'), color='k', fontsize=7
                ))
        adjust_text(text_station)

    # ------------ Plot vector layers simulation path + vent ----------

    # Load vector layers
    losd = fiona.open(losd_path)
    vent = fiona.open(vent_path)

    # Plot the LOSD vector layer
    for feature in losd:
        geometry = shape(feature['geometry'])
        if geometry.geom_type == 'LineString':
            x, y = geometry.xy
            ax.plot(x, y, 'darkred')

    # Plot the vent vector layer
    for feature in vent:
        geometry = shape(feature['geometry'])
        if geometry.geom_type == 'Point':
            x, y = geometry.x, geometry.y
            ax.plot(x, y, 'r^', markersize=10)



    # ------------ Add legend and colorbar ------------

    # Add the legend image to the map
    ax.plot([], [], 'r^', markersize=7, label='Bouche éruptive ('+ flow_id+')')
    ax.plot([], [], '-r', label='Trajectoire principale')

    if station_ovpf_path == str(0):
        pass
    else:
        ax.plot([], [], 'k.', markersize=5, label='Stations OVPF')

    if lavaflow_outline_path == str(0):
        pass
    else:
        ax.plot([], [], 'k-', markersize=10, label='Contour de la coulée')

    legend=ax.legend(bbox_to_anchor=(1, 0.7), loc="upper left", fontsize='8')
    legend.get_frame().set_linewidth(0)
    # Adjust the figure size
    fig.subplots_adjust(right=0.7)
    fig.subplots_adjust(left=0.1)
    fig.subplots_adjust(top=0.9)
    fig.subplots_adjust(bottom=0.1)

    # Create a colorbar for the simulation data in raster
    cax = fig.add_axes([0.71, 0.70, 0.2, 0.02])  # Coordinates and size of the axis
    # Create the colorbar with the colors of the intervals
    norm2 = colors.Normalize(vmin=min(intervals), vmax=max(intervals))
    cmap2 = colors.LinearSegmentedColormap.from_list('my_colormap', colors_list2, N=256)
    sm = ScalarMappable(cmap=cmap2, norm=norm2)
    sm.set_array([])  # Set empty array for the colorbar
    cbar = plt.colorbar(sm, cax=cax, orientation='horizontal')
    cbar.ax.set_title("Simulation DOWNFLOWGO \nProbabilité de passage de la coulée\n ", fontsize=8, loc='left')
    cbar.set_label("Basse                        Haute", fontsize=8, loc='left')
    cbar.set_ticks([])
    cbar.set_ticklabels([])
    #cbar.ax.set_position([0.71, 0.71, 0.2, 0.05])

    # Load Logo image
    img = plt.imread(logo)
    logo_box = OffsetImage(img, zoom=0.05)  # size of the logo
    logo_anchor = (1.2, 0.02)  # Define the coordinate of the image anchor
    # Create the annotation of the image (remove frame
    ab = AnnotationBbox(logo_box, logo_anchor, xycoords='axes fraction', frameon=False)
    ax.add_artist(ab)

    # ------------ Final adjustments ------------

    #show label from y axis en completo
    #formatter = ScalarFormatter(useMathText=False)
    #formatter.set_scientific(False)
    #ax.yaxis.set_major_formatter(formatter)

    # Adjust the position of the legend and colorbar
    # Rotate label of Y and orientate vertically
    ax.set_yticks(ax.get_yticks())
    ax.set_yticklabels(ax.get_yticklabels(), rotation='vertical')
    ax.set_title('Carte de simulation DOWNFLOWGO pour l\'éruption en cours\n' + str(Date))

    plt.savefig(path_to_folder+'/map_'+ flow_id+'.png', dpi=300, bbox_inches='tight')
#    plt.savefig('./map_'+ flow_id+'.png', dpi=300, bbox_inches='tight')

    # Show the figure
    plt.show()



