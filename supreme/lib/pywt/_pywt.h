#ifndef __PYX_HAVE__supreme__lib__pywt___pywt
#define __PYX_HAVE__supreme__lib__pywt___pywt
#ifdef __cplusplus
#define __PYX_EXTERN_C extern "C"
#else
#define __PYX_EXTERN_C extern
#endif

/* "/home/stefan/akad/projekte/supreme/supreme/lib/pywt/_pywt.pyx":147
 *     return __wfamily_list_long[:]
 * 
 * cdef public class Wavelet [type WaveletType, object WaveletObject]:             # <<<<<<<<<<<<<<
 *     """
 *     Wavelet(name, filter_bank=None) object describe properties of
 */

struct WaveletObject {
  PyObject_HEAD
  Wavelet *w;
  PyObject *name;
  PyObject *number;
};

#ifndef __PYX_HAVE_API__supreme__lib__pywt___pywt

__PYX_EXTERN_C DL_IMPORT(PyTypeObject) WaveletType;

#endif

PyMODINIT_FUNC init_pywt(void);

#endif
