from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
from matplotlib import pyplot as plt
from matplotlib.patches import Polygon
# from descartes.patch import PolygonPatch
import pathlib
import parse
import numpy as np
from shapely.wkt import loads
from shapely.geometry.base import BaseGeometry


@dataclass
class AnnotationProperties:
    line_color: Optional[tuple] = None
    line_opacity: Optional[float] = None
    line_weight: Optional[float] = None
    line_type: Optional[tuple] = None
    fill_color: Optional[tuple] = None
    fill_opacity: Optional[float] = None

        
@dataclass
class Annotation:
    object_type: str
    vertices: List[str]
    page: Union[int, str]
    label: Optional[str] = None
    properties: Optional[AnnotationProperties] = None
    wkt: Optional[str] = None
    geom: Optional[BaseGeometry] = None
        
        
def load_annotations(file_path: pathlib.Path) -> list:
    """
    Loads the annotations in the FDF file found at 'file_path' and returns a list
    of objects determined by 'output'.
    """
    file_path = pathlib.Path(file_path)
    fdf_data = read_fdf_file(file_path)
    bare_annotations = get_annotations_from_fdf(fdf_data)
    complete_annotations = []
    for annotation in bare_annotations:
        annotation.wkt = annotation_to_wkt(annotation)
        annotation.geom = loads(annotation.wkt)
        complete_annotations.append(annotation)
    return complete_annotations
        
    
def read_fdf_file(file_path: pathlib.Path) -> List[str]:
    """
    Reads the FDF file and returns a list of strings.
    """
    with open(file_path, 'rb') as file:
        acc = []
        for line in file:
            try:
                acc.append(line.decode('utf-8'))
            except:
                pass
    return acc
    
    
def get_annotations_from_fdf(fdf_str: str) -> List[Annotation]:
    """
    Separates FDF data by objects
    """
    annotations = []
    in_stream_data = False
    stream_data = None
    stream_properties = {}
    annotation_properties = {}
    annot_type, vertices = None, None
    annotation = None
    
    # This upcoming for/if/elif block assumes the following:
    #   1. The FDF file contains geometric annotations, which we want, combined with
    #      other annotation data (e.g. bounding boxes) that are related to the geometric
    #      annotations but which we do not want.
    #   2. The general format of an FDF geometric annotation is as follows:
    #     a) The geometric annotation in 'obj<<' format as an object
    #     b) Some other information in the 'obj<<' format as other objects (bounding boxes, etc.)
    #     c) The stream data that contains many of the geometry's properties
    #   3. We are going to get the vertices information (geometry) from the 
    #     'obj<<' formatted data and most of its properties from the stream
    #     which means we need to retain the geometric data as we iterate before
    #     we finally get to that object's applicable stream data.
    #  A visual inspection of an FDF file with geometric markup should be able to inform
    #  the general approach taken.
        
    for line in fdf_str:
        if "endstream" in line and stream_data:
            stream_properties = extract_stream_properties(stream_data)
            stream_data = None
        elif in_stream_data == True:
            stream_data = line
            in_stream_data = False
            continue
        elif not parse.search("{} 0 obj<<", line) and "stream" not in line:
            continue
        elif "stream" in line:
            in_stream_data = True
            continue       
        type_and_vertices = extract_type_and_vertices(line)
        object_properties = extract_object_properties(line)
        
        if annot_type and vertices and stream_properties:
            annotation_properties.update(stream_properties)
            properties = AnnotationProperties(**annotation_properties)
            annotation = Annotation(
                object_type=annot_type,
                vertices=vertices,
                page=page,
                label=label,
                properties=properties
            )
            stream_properties = {}
            type_and_vertices = None
            annotations.append(annotation)
        elif type_and_vertices:
            annot_type, vertices = type_and_vertices
            label = object_properties.pop("label")
            page = object_properties.pop("page")
            annotation_properties.update(object_properties)
    return annotations

        
def extract_type_and_vertices(line: str) -> Optional[Tuple[str, str]]:
    """
    Returns a tuple of two strings representing the annotation type and
    a string of vertices in the annotation type extracted from 'line',
    a str of FDF data.
    If 'line' does not include an annotation with vertices, None is returned.
    """
    possible_annotation = parse.search("obj<</Subj({})", line)
    if possible_annotation:
        annot_type = possible_annotation[0]
        vertices = None
        if annot_type == "Line":
            vertices = parse.search("/L[{}]", line)[0]
            return (annot_type, vertices)
        elif annot_type in ("Circle", "PolyLine", "Polygon"):
            vertices = parse.search("/Vertices[{}]", line)[0]
            return (annot_type, vertices)
        elif annot_type in ("Rectangle", "Square"):
            bbox = parse.search("/Rect[{}]", line)[0]
            x1, y1, x2, y2 = bbox.split()
            vertices = " ".join([x1,y1, x1, y2, x2, y2, x2, y1])
            return (annot_type, vertices)

        
def extract_object_properties(line: str) -> Optional[dict]:
    object_properties = {}
    object_properties.update(extract_object_opacity(line))
    object_properties.update(extract_label(line))
    object_properties.update(extract_page(line))
    return object_properties
        
        
def extract_object_opacity(line: str) -> Optional[dict]:
    fill_opacity = parse.search("/FillOpacity {:g}/", line)
    line_opacity = parse.search("/LineOpacity {:g}/", line)
    if fill_opacity: fill_opacity = fill_opacity[0]
    if line_opacity: line_opacity = line_opacity[0]
    return {"fill_opacity": fill_opacity, "line_opacity": line_opacity}


def extract_label(line: str) -> Optional[dict]:
    label = parse.search("/Contents({})/", line)
    if label: label = label[0]
    return {"label": label}


def extract_page(line: str) -> Optional[dict]:
    page = parse.search("/Page({})", line)
    if page: page = page[0]
    return {"page": page}


def extract_stream_properties(stream_line: str) -> dict:
    """
    Returns a dict of properties which are available from the stream data:
    'line_color', 'fill_color', 'line_weight'.
    """
    line_color = parse_line_color(stream_line)
    fill_color = parse_fill_color(stream_line)
    line_weight = parse_line_weight(stream_line)
    line_type = parse_line_type(stream_line)
    return {
        "line_color": line_color, 
        "fill_color": fill_color, 
        "line_weight": line_weight,
        "line_type": line_type
    }


def parse_line_color(stream_line: str) -> Tuple[int]:
    """
    Returns a tuple representing the parsed line color specification contained
    within 'stream_line', a line of text representing the FDF data stream.
    Returns None if no line color data is found in 'stream_line'
    
    The returned tuple is in the format of (R, G, B) where each of R, G, B are a float
    from 0.0 to 1.0
    """
    line_color_result = parse.search("{:g} {:g} {:g} RG", stream_line, case_sensitive=True)
    if line_color_result:
        return tuple(line_color_result)
    
    
def parse_fill_color(stream_line: str) -> Tuple[int]:
    """
    Returns a tuple representing the parsed line color specification contained
    within 'stream_line', a line of text representing the FDF data stream.
    Returns None if no fill color data is found in 'stream_line'
    
    The returned tuple is in the format of (R, G, B) where each of R, G, B are a float
    from 0.0 to 1.0
    """
    fill_color_result = parse.search("{:g} {:g} {:g} rg", stream_line, case_sensitive=True)
    if fill_color_result:
        return tuple(fill_color_result)

    
def parse_line_weight(stream_line: str) -> float:
    """
    Returns a float representing the parsed line weight specification contained
    within 'stream_line', a line of text representing the FDF data stream.
    Returns None if no line weight is found in 'stream_line'
    
    The returned value represents a line weight in points (1 point = 1/72 of an inch)
    """
    line_weight_result = parse.search(" {:g} w", stream_line, case_sensitive=True)
    if line_weight_result:
        return line_weight_result[0]
    

def parse_line_type(stream_line: str) -> Tuple[float, tuple]:
    """
    Returns a tuple representing the parsed line type specification contained
    within 'stream_line', a line of text representing the FDF data stream.
    Returns None if no line type data is found in 'stream_line'
    """
    line_type_data = parse.search(" [{}] {:g} d", stream_line)
    if line_type_data:
        acc = []
        for line in line_type_data[0].split(" "):
            acc.append(float(line))
        line_type = (line_type_data[1], tuple(acc))
        return line_type
    
    
def scale_object(annot: Annotation, scale: float) -> str:
    """
    Scale the annotation. Each vertex in 'annot' will be multiplied
    by 'scale'
    """
    return


def annotation_to_wkt(annot: Annotation) -> str:
    """
    Returns a WKT string representing the geometry in 'annot'
    """
    if annot.object_type == "PolyLine" or annot.object_type == "Line":
        grouped_vertices = group_vertices(annot.vertices)
        return f"LINESTRING({grouped_vertices})"
    elif annot.object_type == "Polygon" or annot.object_type == "Rectangle":
        grouped_vertices = group_vertices(annot.vertices, close = True)
        return f"POLYGON(({grouped_vertices}))"
    
    
def group_vertices(vertices: str, close = False) -> List[str]:
    """
    Returns a list of (x, y) tuples from a string of vertices in the format of:
    'x1 y1 x2 y2 x3 y3 ... xn yn'
    """
    acc = []
    coordinates = []
    for idx, ordinate in enumerate(vertices.split(" ")):
        if idx % 2:
            coordinates.append(ordinate)
            acc.append(" ".join(coordinates))
            coordinates = []
        else:
            coordinates.append(ordinate)
    if close:
        acc.append(acc[0])
    return ", ".join(acc)

def xy_vertices(vertices: str, close = False) -> List[List[float]]:
    """
    Returns a list of lists of floats to emulate a 2d numpy array of x, y values
    """
    x = []
    y = []
    for idx, ordinate in enumerate(vertices.split(" ")):
        if idx % 2:
            y.append(float(ordinate))
        else:
            x.append(float(ordinate))
    return np.asarray([x, y])


def plot_annotations(annots: List[Annotation], size: Optional[float], dpi: Optional[float]) -> None:
    """
    Plots annotations with matplotlib
    """
    fig, ax = plt.subplots()
    for idx, annot in enumerate(annots):
        if annot.object_type == "Polygon" or annot.object_type == "Rectangle":
            xy = xy_vertices(annot.vertices)
            ax.add_patch(
                Polygon(
                    xy=xy.T,
                    closed=True,
                    linestyle=annot.properties.line_type,
                    linewidth=annot.properties.line_weight,
                    ec=annot.properties.line_color,
                    fc=annot.properties.fill_color,
                    alpha=annot.properties.fill_opacity,
                    zorder=idx,
                )
            )
        elif annot.object_type == "Line" or annot.object_type == "PolyLine":
            xy = xy_vertices(annot.vertices)
            ax.plot(
                xy[0],
                xy[1],
                linestyle=annot.properties.line_type,
                linewidth=annot.properties.line_weight,
                color = annot.properties.line_color,
                alpha = annot.properties.line_opacity,
                zorder=idx
            )

    plt.axis("scaled")
    if size:
        fig.set_size_inches(size, size)
    if dpi:
        fig.set_dpi(dpi)
    plt.show()
    