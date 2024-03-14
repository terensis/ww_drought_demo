"""
Generate a folium map of the data in the data directory to
visualize the impact of drough conditions on wheat growth
in a HTML file.

Author: Lukas Graf (lukas.graf@terensis.io)
"""

import branca.colormap as cm
import folium
import geopandas as gpd

from branca.element import Element, MacroElement, Template
from pathlib import Path


class BindColormap(MacroElement):
    """Binds a colormap to a given layer.

    Parameters
    ----------
    colormap : branca.colormap.ColorMap
        The colormap to bind.
    """
    def __init__(self, layer, colormap):
        super(BindColormap, self).__init__()
        self.layer = layer
        self.colormap = colormap
        self._template = Template(u"""
        {% macro script(this, kwargs) %}
            {{this.colormap.get_name()}}.svg[0][0].style.display = 'block';
            {{this._parent.get_name()}}.on('overlayadd', function (eventLayer) {
                if (eventLayer.layer == {{this.layer.get_name()}}) {
                    {{this.colormap.get_name()}}.svg[0][0].style.display = 'block';
                }});
            {{this._parent.get_name()}}.on('overlayremove', function (eventLayer) {
                if (eventLayer.layer == {{this.layer.get_name()}}) {
                    {{this.colormap.get_name()}}.svg[0][0].style.display = 'none';
                }});
        {% endmacro %}
        """)  # noqa


def get_textbox_css():
    return """
    {% macro html(this, kwargs) %}
    <!doctype html>
    <html lang="de">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Trockenheit Demo Terensis</title>
        <link rel="stylesheet" href="//code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.2.1/css/all.min.css" integrity="sha512-MV7K8+y+gLIBoVD59lQIYicR65iaqukzvf/nwasF0nqhPay5w/9lJmVM2hMDcnK1OnMGCdVK+iQrJ7lzPJQd1w==" crossorigin="anonymous" referrerpolicy="no-referrer"/>
        <script src="https://code.jquery.com/jquery-1.12.4.js"></script>
        <script src="https://code.jquery.com/ui/1.12.1/jquery-ui.js"></script>

        <script>
        $( function() {
            $( "#textbox" ).draggable({
            start: function (event, ui) {
                $(this).css({
                right: "auto",
                top: "auto",
                bottom: "auto"
                });
            }
            });
        });
        </script>
    </head>

    <body>
        <div id="textbox" class="textbox">
        <div class="textbox-title">Auswirkung von Dürre auf Winterweizenerträge</div>
        <div class="textbox-content">
            <pre>
            Die Karte zeigt modellierte Winterweizenerträge von Parzellen, auf
            denen sowohl in 2019 (nasses Jahr) als auch in 2022 (extrem trockenes
            Jahr) Winterweizen im Kanton Schaffhausen angebaut wurde. Zudem ist
            der Unterschied im Ertrag (2022 - 2019) dargestellt. Die räumliche
            Auflösung des Modells beträgt 10 Meter.</pre>
        </div>
        </div>
        <div style="position: fixed; 
                top: 10px; 
                left: 50px; 
                width: 250px; 
                height: 80px; 
                z-index:9999; 
                font-size:14px;
                text-align: center;">
        <img src="https://github.com/terensis/ww_drought_demo/raw/main/resources/terensis_logo.png" alt="Terensis" style="width: 250px; height: auto;">
    </div>
    </body>
    </html>

    <style type='text/css'>
    .textbox {
        position: absolute;
        z-index:9999;
        border-radius:4px;
        background: rgba( 90, 114, 71, 0.25 );
        box-shadow: 0 8px 32px 0 rgba( 90, 114, 71, 0.37 );
        backdrop-filter: blur( 4px );
        -webkit-backdrop-filter: blur( 4px );
        border: 4px solid rgba( 90, 114, 71, 0.2 );
        padding: 10px;
        font-size: 14px;
        right: 20px;
        bottom: 20px;
        color: #5a7247;
    }
    .textbox .textbox-title {
        color: black;
        text-align: center;
        margin-bottom: 5px;
        font-weight: bold;
        font-size: 22px;
        }
    .textbox .textbox-content {
        color: black;
        text-align: left;
        margin-bottom: 5px;
        font-size: 14px;
        }
    </style>
    {% endmacro %}
    """


def generate_folium_map(
    data_dir: Path,
    output_dir: Path,
    output_name: str = 'index.html',
) -> None:
    """
    Generate a folium map of the data in the data directory to
    visualize the results of the phenology model in a HTML file.

    :param data_dir: directory with the data (geojson files).
    :param output_dir: directory for writing outputs to.
    :param output_name: name of the output file.
    """
    # create map
    m = folium.Map(
        location=[47.7, 8.6],
        zoom_start=11,
        tiles='cartodbpositron',
        attr='© Terensis (2024). Basemap data © CartoDB'
    )

    # Add custom Terensis style
    textbox_css = get_textbox_css()
    my_custom_style = MacroElement()
    my_custom_style._template = Template(textbox_css)
    # Adding to the map
    m.get_root().add_child(my_custom_style)

    # add data
    fpath_grain_yield_2019 = data_dir.joinpath('grain_yield_2019_sh.gpkg')
    grain_yield_2019 = gpd.read_file(fpath_grain_yield_2019)
    # filter where trait_name is grain_yield
    grain_yield_2019 = grain_yield_2019[
        grain_yield_2019['trait_name'] == 'Grain Yield [t/ha]'].copy()
    # rename trait_value to grain_yield
    grain_yield_2019.rename(
        columns={'trait_value': 'grain_yield'}, inplace=True)
    # round grain_yield to 2 decimal places
    grain_yield_2019['grain_yield'] = grain_yield_2019['grain_yield'].round(2)

    # clip grain yield between 0 and 10 t/ha
    grain_yield_2019['grain_yield'] = grain_yield_2019['grain_yield'].clip(0, 11)
    # add a column
    grain_yield_2019['Ertrag 2019 t/ha'] = grain_yield_2019['grain_yield']

    # add choropleth to map
    cl219 = folium.Choropleth(
        geo_data=grain_yield_2019,
        name='Ertrag 2019',
        data=grain_yield_2019,
        columns=['_uid0_', 'grain_yield'],
        fill_color='viridis',
        fill_opacity=0.9,
        line_opacity=0.2,
        legend_name='Winterweizen Ertrag 2019 [t/ha]',
        show=True,
        lazy=True,
        key_on='feature.properties._uid0_',
    )
    # and finally adding a tooltip/hover to the choropleth's geojson
    folium.GeoJsonTooltip(['Ertrag 2019 t/ha']).add_to(
        cl219.geojson)

    # handle colormap
    for key in cl219._children:
        if key.startswith('color_map'):
            branca_color_map = cl219._children[key]
            del (cl219._children[key])

    m.add_child(cl219)
    m.add_child(branca_color_map)
    m.add_child(BindColormap(cl219, branca_color_map))

    # add 2022 grain yield
    fpath_grain_yield_2022 = data_dir.joinpath('grain_yield_2022_sh.gpkg')
    grain_yield_2022 = gpd.read_file(fpath_grain_yield_2022)
    # filter where trait_name is grain_yield
    grain_yield_2022 = grain_yield_2022[
        grain_yield_2022['trait_name'] == 'Grain Yield [t/ha]'].copy()
    # rename trait_value to grain_yield
    grain_yield_2022.rename(
        columns={'trait_value': 'grain_yield'}, inplace=True)
    # round grain_yield to 2 decimal places
    grain_yield_2022['grain_yield'] = grain_yield_2022['grain_yield'].round(2)

    # clip grain yield between 0 and 10 t/ha
    grain_yield_2022['grain_yield'] = grain_yield_2022['grain_yield'].clip(0, 11)

    # add a column
    grain_yield_2022['Ertrag 2022 t/ha'] = grain_yield_2022['grain_yield']

    # add choropleth to map
    cl2022 = folium.Choropleth(
        geo_data=grain_yield_2022,
        name='Ertrag 2022',
        data=grain_yield_2022,
        columns=['_uid0_', 'grain_yield'],
        legend_name='Winterweizen Ertrag 2022 [t/ha]',
        fill_color='viridis',
        fill_opacity=0.9,
        line_opacity=0.2,
        show=False,
        lazy=True,
        key_on='feature.properties._uid0_',
    )

    # and finally adding a tooltip/hover to the choropleth's geojson
    folium.GeoJsonTooltip(['Ertrag 2022 t/ha']).add_to(
        cl2022.geojson)
    # handle colormap
    for key in cl2022._children:
        if key.startswith('color_map'):
            branca_color_map = cl2022._children[key]
            del (cl2022._children[key])

    m.add_child(cl2022)
    m.add_child(branca_color_map)
    m.add_child(BindColormap(cl2022, branca_color_map))

    # calculate difference between 2022 and 2019 and add as new layer
    grain_yield_diff = grain_yield_2022.copy()
    grain_yield_diff['grain_yield'] = grain_yield_diff['grain_yield'] - \
        grain_yield_2019['grain_yield']

    # round grain_yield to 2 decimal places
    grain_yield_diff['grain_yield'] = grain_yield_diff['grain_yield'].round(2)

    # add a column
    grain_yield_diff['Ertragsdifferenz (2022-2019) [t/ha]'] = grain_yield_diff['grain_yield']

    # add choropleth to map
    cl_diff = folium.Choropleth(
        geo_data=grain_yield_diff,
        name='Ertragsdifferenz (2022-2019)',
        data=grain_yield_diff,
        columns=['_uid0_', 'grain_yield'],
        fill_color='PRGn',
        fill_opacity=0.9,
        line_opacity=0.2,
        legend_name='Winterweizen Ertrag Differenz [t/ha]',
        show=False,
        lazy=True,
        key_on='feature.properties._uid0_',
    )

    # and finally adding a tooltip/hover to the choropleth's geojson
    folium.GeoJsonTooltip(['Ertragsdifferenz (2022-2019) [t/ha]']).add_to(
        cl_diff.geojson)

    # handle colormap
    for key in cl_diff._children:
        if key.startswith('color_map'):
            branca_color_map = cl_diff._children[key]
            del (cl_diff._children[key])

    m.add_child(cl_diff)
    m.add_child(branca_color_map)
    m.add_child(BindColormap(cl_diff, branca_color_map))   

    # save map
    m.add_child(folium.map.LayerControl(collapsed=False))
    m.save(output_dir.joinpath(output_name))


if __name__ == '__main__':

    import os
    os.chdir(Path(__file__).parents[1])

    data_dir = Path('data')
    output_dir = Path('.')
    output_dir.mkdir(exist_ok=True)
    generate_folium_map(data_dir, output_dir)
