from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import pathlib
import parse


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
    properties: Optional[AnnotationProperties] = None


def read_fdf_file(file_path: pathlib.Path) -> List[str]:
    """
    Reads the FDF file and returns a list of strings.
    """
    with open(file_path, "r") as file:
        return list(file.readlines())

    
def extract_annotation(annotation_data: List[str]) -> Annotation:
    """
    Returns an Annotation object from a list of FDF annotation data.
    """
    main_object = annotation_data[0]
    
    

def extract_wkt_objects(fdf_data: List[str]) -> List[str]:
    """
    Returns a list of WKT strings extracted from 'fdf_data'.
    """
    wkt_objects = []
    for line in fdf_data:
        fd
        wkt_object = convert_line_to_wkt(line)
        if wkt_object is not None:
            wkt_objects.append(wkt_object)
    return wkt_objects
    
    
def separate_fdf_objects(fdf_str: str) -> List[str]:
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
        opacity_data = extract_object_opacity(line)
        
        if annot_type and vertices and stream_properties:
            annotation_properties.update(stream_properties)
            properties = AnnotationProperties(**annotation_properties)
            annotation = Annotation(annot_type, vertices, properties)
            stream_properties = {}
            type_and_vertices = None
            annotations.append(annotation)
        elif type_and_vertices:
            annot_type, vertices = type_and_vertices
            annotation_properties.update(opacity_data)
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
        if annot_type != "Rectangle":
            vertices = parse.search("/Vertices[{}]", line)[0]
        else:
            bbox = parse.search("/Rect[{}]", line)[0]
            x1, y1, x2, y2 = bbox.split()
            vertices = " ".join([x1,y1, x1, y2, x2, y2, x2, y1])
        return (annot_type, vertices)
            
        
def extract_object_opacity(line: str) -> Optional[dict]:
    fill_opacity = parse.search("/FillOpacity {:g}/", line)
    line_opacity = parse.search("/LineOpacity {:g}/", line)
    if fill_opacity: fill_opacity = fill_opacity[0]
    if line_opacity: line_opacity = line_opacity[0]
    return {"fill_opacity": fill_opacity, "line_opacity": line_opacity}

        
def extract_stream_properties(stream_line: str) -> dict:
    """
    Returns a dict of properties which are available from the stream data:
    'line_color', 'fill_color', 'line_weight'.
    """
    line_color = parse.search("{:g} {:g} {:g} RG", stream_line, case_sensitive=True)
    fill_color = parse.search("{:g} {:g} {:g} rg", stream_line, case_sensitive=True)
    line_weight = parse.search(" {:g} w", stream_line, case_sensitive=True)
    line_type = parse.search(" [{}] {:g} d", stream_line)
    if line_color: line_color = tuple(line_color)
    if fill_color: fill_color = tuple(fill_color)
    if line_weight: line_weight = line_weight[0]
    if line_type: line_type = tuple(line_type)
    return {
        "line_color": line_color, 
        "fill_color": fill_color, 
        "line_weight": line_weight,
        "line_type": line_type
    }


def result_to_value(result: parse.Result, cast_type: type) -> Any:
    """
    Returns the value of result cast to 'cast_type'. Returns None if 'result' is None
    """
    try:
        return cast_type(result)
    except TypeError:
        return None


def extract_object_properties(object_line: str) -> dict:
    """
    Returns a dict of properties which are available from the object data:
    'opacity', 
    """
    pass
    
def convert_line_to_wkt(fdf_line: str) -> str:
    """
    Converts 'fdf_line' to a wkt object if applicable.
    """
    conversion_funcs = [
        convert_line_object,
    ]
    wkt_object = None
    for conversion_func in conversion_funcs:
        wkt_object = convert_line_object(fdf_line)
        if wkt_object is not None:
            return wkt_object
    return wkt_object
    
    
def convert_line_object(fdf_line: str) -> str:
    """
    If 'fdf_line' includes a Line object, returns the line
    object convert to a WKT Line object. Returns None otherwise.
    """
    if "/Subj(Line)" in fdf_line:
        beg_index = fdf_line.find("/L[")
        end_index = fdf_line[beg_index:].find("]")
        coords = fdf_line[beg_index + 3: beg_index + end_index].split(" ")
        x1, y1, x2, y2 = coords
        return f"LINESTRING({x1} {y1}, {x2} {y2})"
    
    
def create_wkt_string(wkt_obj_type: str, *params):
    """
    Constructs a string describing a WKT geometrical object.
    'wkt_obj_type' - One of "linestring", ""
    """
    pass
    
    
def scale_object(wkt_object: str, scale: float) -> str:
    """
    Scale a wkt_object by 'scale'. Returns the scaled WKT string.
    """
    return

def read_wkt_objects(fdf_file: pathlib.Path) -> List[str]:
    """
    Returns the list of wkt_objects that may be contained in 'fdf_file'
    """
    fdf_data = read_fdf_file(fdf_file)
    return extract_wkt_objects(fdf_data)
    

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
    
def group_vertices(vertices: str, close = False) -> List[Tuple[float, float]]:
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
            