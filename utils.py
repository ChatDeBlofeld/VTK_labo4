from pyproj import Transformer
import numpy as np
import math
import vtk

# Trial and error, this CRS fits our case
# https://epsg.org/crs_3021/RT90-2-5-gon-V.html
RT90_TO_WGS84 = Transformer.from_crs(3021, 4326)

def RT90ToWGS84(yy, xx):
    '''
    Transform a point or a set of points from RT90 to WGS84 coords
    '''
    return RT90_TO_WGS84.transform(xx, yy)

def RT90ListToWGS84(coords):
    '''
    Transform a list of RT90 coords to WGS84
    '''
    a = np.array(coords)
    a = a.T
    return np.vstack(RT90ToWGS84(a[0], a[1])).T

def toCartesian(inclination: float, azimuth: float, elevation):
    '''
    Transform spherical coord to cartesian coords.
    Uses physics' world conventions about what azimuth and inclination mean
    
    Assuming this disposition for world axis
    https://raw.githubusercontent.com/Kitware/vtk-examples/gh-pages/src/VTKBook/Figures/Figure3-15.png?raw=true
    '''

    cartesian = vtk.vtkTransform()
    cartesian.RotateY(azimuth)
    cartesian.RotateX(-inclination)
    cartesian.Translate(0, 0, elevation)

    return cartesian.TransformPoint(0,0,0)

def quadInterpolation(x, y, a, b):
    '''
    Compute quad interpolation from physical world to logical world
    https://www.particleincell.com/2012/quad-interpolation/
    '''
    # quadratic equation coeffs, aa*mm^2+bb*m+cc=0
    aa = a[3]*b[2] - a[2]*b[3]
    bb = a[3]*b[0] - a[0]*b[3] + a[1]*b[2] - a[2]*b[1] + x*b[3] - y*a[3]
    cc = a[1]*b[0] - a[0]*b[1] + x*b[1] - y*a[1]

    # compute m = (-b+sqrt(b^2-4ac))/(2a)
    det = math.sqrt(bb**2 - 4*aa*cc)
    m = (-bb-det) / (2*aa)

    # compute l
    l = (x-a[0]-a[2]*m) / (a[1]+a[3]*m)

    return l, m