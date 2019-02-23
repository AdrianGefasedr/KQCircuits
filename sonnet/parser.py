import pya
from string import Template

def apply_template(filename_template, filename_output, rules):
  filein = open(filename_template)
  src = Template( filein.read() )
  filein.close()
  results = src.substitute(rules)
  fileout = open(filename_output, "w")
  fileout.write(results)
  fileout.close()  
  
def polygon_head(
      nvertices,# number of vertices of the polygon
      debugid, # unique number for sonnet internal debugging 
      ilevel= 0, # sonnet layer number
      mtype= -1, # metallization type index, -1 for lossless
      filltype="N", # N for staircase, T for diagonal, V for conformal
      xmin= 1, # minimum subsection size
      ymin= 1, # minimum subsection size
      xmax= 100, # maximum subsection size
      ymax= 100, # maximum subsection size
      conmax= 0, # maximum length for conformal mesh subsection, 0 for auto
      res= 0, # reserved for sonnet future
      edge_mesh= "Y" # edge mesh on (Y) or off (N)
    ):
  
  return "{ilevel} {nvertices} {mtype} {filltype} {debugid} {xmin} {ymin} {xmax} {ymax} {conmax} {res} {res} {edge_mesh}\n".format(**locals())

def symmetry(sym: bool = False):
  sonnet_str = ""
  if (sym):
    sonnet_str = "SYM"
  return sonnet_str

def box_from_cell(cell: pya.Cell, cell_size : float):
  bbox = cell.dbbox()  
  print("box of cell")
  return box(
    xwidth = bbox.width(),
    ywidth = bbox.height(),
    xcells = int(bbox.width()/cell_size),
    ycells = int(bbox.height()/cell_size),
  )

def box(
      xwidth : float = 8000.,
      ywidth : float = 8000.,
      xcells : int = 8000,
      ycells : int = 8000,
      materials_type : str = "SiOx+Si"
    ):

  xcells2 = 2*xcells
  ycells2 = 2*ycells
  nsubs = 20 # placeholder for depricated parameter
  eeff = 0 # placeholder for depricated parameter
  
  materials = {
    "Si": "3000 1 1 0 0 0 0 \"vacuum\"\n500 11.7 1 0 0 0 0 \"Silicon (intrinsic)\"",
    "SiOx+Si": "3000 1 1 0 0 0 0 \"vacuum\"\n0.55 3.78 11.7 1 0 0 0 0 \"SiOx (10mK)\"\n525 11.45 1 1e-06 0 0 0 \"Si (10mK)\"",
  }[materials_type]
  
  nlev = {
    "Si": 1,
    "SiOx+Si": 2
  }[materials_type]
  
  return "BOX {nlev} {xwidth} {ywidth} {xcells2} {ycells2} {nsubs} {eeff}\n{materials}".format(**locals())
  
def refplane(
    position : str, # "LEFT" | "RIGHT" | "TOP" | "BOTTOM",
    length : int = 0
  ):
  return "DRP1 {position} FIX {length}\n".format(**locals())
  
  
def refplanes(postitions, length):  
  sonnet_str = ""
  for side in postitions:
    sonnet_str += refplane(side, length)
  return sonnet_str 

  
def port(
    portnum,
    ipolygon,
    ivertex,
    port_type = "STD", # STD for standard | AGND autogrounded | CUP cocalibrated
    xcord = 0,
    ycord = 0
  ):
  return "POR1 {port_type}\nPOLY {ipolygon} 1\n{ivertex}\n{portnum} 50 0 0 0\n".format(**locals()) # {xcord} {ycord} [reftype rpcallen]

def ports(shapes):
  sonnet_str = ""
  polygons = 0
  
  # FIXME Maybe the shapes will not have the same indexes as polygons in the region!
  for shape in shapes.each():
    if shape:
      polygons += 1
      ivertex = shape.property("sonnet_port_edge")
      portnum = shape.property("sonnet_port_nr")
      if ivertex!=None and portnum!=None:
        sonnet_str += port(ipolygon=polygons-1, portnum=portnum, ivertex=ivertex)
  
  return sonnet_str

def control(control_type):
  return {
  "Simple": "SIMPLE", # Linear frequency sweep
  "ABS": "ABS" # Sonnet guesses the resonances, simulates about 5 points around the resonance and interpolates the rest
  }[control_type]


def polygons(shapes, v):
  
  reg = pya.Region(shapes)
  #bbox = reg.bbox()
  
  #v = pya.Vector(-bbox.p1.x, -bbox.p1.y) # TODO
  
  #cell.shapes(0).insert(reg)
  
  sonnet_str = 'NUM {}\n'.format(reg.size())
  for i, shape in enumerate(shapes.each()):
    if shape.is_polygon:
      poly = shape.dpolygon
      if poly.holes():
        raise NotImplementedError    
      sonnet_str += polygon_head(nvertices=poly.num_points_hull()+1, debugid=i)
      for j, point in enumerate(poly.each_point_hull()):
        sonnet_str += "{} {}\n".format(point.x+v.x, point.y+v.y)
      point = next(poly.each_point_hull()) # first point again to close the polygon
      sonnet_str += "{} {}\nEND\n".format(point.x+v.x, point.y+v.y)
    
  return sonnet_str