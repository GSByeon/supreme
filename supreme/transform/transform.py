"""Image warping algorithms, e.g. log-polar transform."""

import numpy as N
from scipy.ndimage import interpolation as ndii

__all__ = ['logpolar','matrix']

import supreme
import supreme.config as SC
from supreme.ext import interp_bilinear

def stackcopy(a,b):
    """a[:,:,0] = a[:,:,1] = ... = b"""
    if a.ndim == 3:
        a.transpose().swapaxes(1,2)[:] = b
    else:
        a[:] = b

def _lpcoords(ishape, w, angles=None):
    """Calculate the reverse coordinates for the log-polar transform.

    Return array is of shape (len(angles), w)

    """

    ishape = N.array(ishape)
    bands = ishape[2]

    oshape = ishape.copy()
    centre = (ishape[:2]-1)/2.

    d = N.hypot(*(ishape[:2]-centre)) # maximum radius
    log_base = N.log(d)/w

    if angles is None:
        angles =  -N.linspace(0, 2*N.pi, 4*w + 1)[:-1]
    theta = N.empty((len(angles),w),dtype=SC.ftype)
    # Use broadcasting to replicate angles
    theta.transpose()[:] = angles

    L = N.empty_like(theta)
    # Use broadcasting to replicate distances
    L[:] = N.arange(w).astype(SC.ftype)

    r = N.exp(L*log_base)

    return r*N.sin(theta) + centre[0], r*N.cos(theta) + centre[1], \
           angles, log_base

def logpolar(image, angles=None, Rs=None, mode='M', cval=0, output=None,
             _coords_r=None, _coords_c=None, extra_info=False):
    """Perform the log polar transform on an image.

    Input:
    ------
    image : MxNxC array
        An MxN image with C colour bands.
    Rs : int
        Number of samples in the radial direction.
    angles : 1D array of floats
        Angles at which to evaluate. Defaults to 0..2*Pi in 4*Rs steps
        ([1] below suggests 8*Rs, but that causes too much oversampling).
    mode : string
        How values outside borders are handled. 'C' for constant, 'M'
        for mirror and 'W' for wrap.
    cval : int or float
        Used in conjunction with mode 'C', the value outside the border.
    extra_info : bool
        Whether to return the angles and log base in addition
        to the transform.  False by default.

    Returns
    -------
    lpt : ndarray of uint8
        Log polar transform of the input image.
    angles : ndarray of float
        Angles used.  Only returned if `extra_info` is set
        to True.
    log_base : int
        Log base used.  Only returned if `extra_info` is set
        to True.

    Optimisation parameters:
    ------------------------
    _coords_r, _coords_c : 2D array
        Pre-calculated coords, as given by _lpcoords.

    References
    ----------
    .. [1] Matungka, Zheng and Ewing, "Image Registration Using Adaptive
           Polar Transform". IEEE Transactions on Image Processing, Vol. 18,
           No. 10, October 2009.

    """
    if image.ndim < 2 or image.ndim > 3:
        raise ValueError("Input image must be 2 or 3 dimensional.")

    image = N.atleast_3d(image)

    if Rs is None:
        Rs = max(image.shape[:2])

    if _coords_r is None or _coords_c is None:
        _coords_r, _coords_c, angles, log_base = \
                   _lpcoords(image.shape, Rs, angles)

    bands = image.shape[2]
    if output is None:
        output = N.empty(_coords_r.shape + (bands,),dtype=N.uint8)
    else:
        output = N.atleast_3d(N.ascontiguousarray(output))
    for band in range(bands):
        output[...,band] = interp_bilinear(image[...,band],
                                           _coords_r,_coords_c,mode=mode,
                                           cval=cval,output=output[...,band])

    output = output.squeeze()

    if extra_info:
        return output, angles, log_base
    else:
        return output

def matrix(image,matrix,output_shape=None,order=1,mode='constant',
           cval=0.):
    """Perform a matrix transform on an image.

    Each coordinate (x,y,1) is multiplied by matrix to find its
    new position.  E.g., to rotate by theta degrees clockwise,
    the matrix should be

    [[cos(theta) -sin(theta) 0]
     [sin(theta)  cos(theta) 0]
     [0            0         1]]

    or to translate x by 10 and y by 20,

    [[1 0 10]
     [0 1 20]
     [0 0 1 ]].

    Input:
    ------
    order : int
        Order of splines used in interpolation.
    mode : string
        How to handle values outside the image borders.  Passed as-is to ndimage.
    cval : string
        Used in conjunction with mode 'constant', the value outside the image boundaries.

    """

    if image.ndim < 2:
        raise ValueError("Input must have more than 1 dimension.")

    image = N.atleast_3d(image)
    ishape = N.array(image.shape)
    bands = ishape[2]

    if output_shape is None:
        output_shape = ishape

    coords = N.empty(N.r_[3,output_shape],dtype=SC.ftype)
    tf_coords = supreme.geometry.Grid(*output_shape[:2]).coords
    tf_coords = N.dot(tf_coords,N.linalg.inv(matrix).transpose())
    tf_coords[N.absolute(tf_coords) < SC.eps] = 0.

    # normalize coordinates
    tf_coords[...,:2] /= tf_coords[...,2,N.newaxis]

    # y-coordinate mapping
    stackcopy(coords[0,...], tf_coords[...,1])

    # x-coordinate mapping
    stackcopy(coords[1,...], tf_coords[...,0])

    # colour-coordinate mapping
    coords[2,...] = range(bands)

    # Prefilter not necessary for order 1 interpolation
    prefilter = order > 1
    mapped = ndii.map_coordinates(image,coords,prefilter=prefilter,
                                  mode=mode,order=order,cval=cval)

    return mapped.squeeze()
