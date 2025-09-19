# backend/geo_utils.py
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import json

def build_gdf(df: pd.DataFrame, lat_col="latitude", lon_col="longitude", crs="EPSG:4326"):
    """
    Construct a GeoDataFrame from df. Prioritises geometry column if present (WKT).
    """
    # if geometry column exists
    if "geometry" in df.columns:
        try:
            gdf = gpd.GeoDataFrame(df.copy(), geometry=gpd.GeoSeries.from_wkt(df["geometry"]), crs=crs)
            return gdf
        except Exception:
            # fallthrough to lat/lon
            pass

    if lat_col in df.columns and lon_col in df.columns:
        valid = df[[lat_col, lon_col]].dropna()
        gdf = gpd.GeoDataFrame(df.copy(), geometry=[Point(xy) if not pd.isna(xy[0]) and not pd.isna(xy[1]) else None for xy in zip(df[lon_col], df[lat_col])], crs=crs)
        return gdf
    raise ValueError("No geometry or latitude/longitude columns found.")

def folium_map_from_gdf(gdf, value_col="HMPI", palette=None, popup_fields=None, initial_zoom=5):
    """
    Create a Folium map with marker cluster colored by value_col.
    palette: function or dict mapping category->color
    popup_fields: list of columns to show on popup
    """
    # center map
    center = [gdf.geometry.y.mean(), gdf.geometry.x.mean()] if not gdf.empty else [20,78]
    m = folium.Map(location=center, zoom_start=initial_zoom)
    mc = MarkerCluster().add_to(m)

    for idx, row in gdf.dropna(subset=["geometry"]).iterrows():
        geom = row.geometry
        try:
            val = row.get(value_col, None)
            if palette and val is not None:
                color = palette(val)
            else:
                color = "blue"
            popup_html = ""
            if popup_fields:
                for f in popup_fields:
                    popup_html += f"<b>{f}:</b> {row.get(f, '')}<br>"
            folium.CircleMarker(location=[geom.y, geom.x], radius=6, color=color, fill=True, fill_color=color,
                                popup=folium.Popup(popup_html, max_width=350)).add_to(mc)
        except Exception:
            continue
    return m

def gdf_to_geojson(gdf):
    return json.loads(gdf.to_json())
