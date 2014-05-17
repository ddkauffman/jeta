"""
Derived parameter MSIDs related to vehicle Keplerian orbital elements.

Based on http://www.castor2.ca/05_OD/01_Gauss/14_Kepler/index.html
"""
import numpy as np

from . import base

from Chandra.Time import DateTime

ELEMENTS_CACHE = {}
R_E = 6378.137  # Earth Equatorial Radius (km)
M_G = 398600.44  # Gravitational parameter (km**3 / s**2)


def calc_orbital_elements(x, y, z, vx, vy, vz):
    from numpy import sin, cos, arccos, sqrt, degrees, pi

    def arccos_2pi(arg, reflect):
        """
        Return arccos(arg) where reflect is False, 2 * pi - arccos(arg) where reflect is True
        """
        np_err_handling = np.geterr()
        np.seterr(all='raise')
        try:
            out = arccos(arg)
        except FloatingPointError:
            print('Bad argccos arg={}'.format(arg))
            raise
        np.seterr(**np_err_handling)

        try:
            # Check if arg is a non-scalar numpy array
            len(arg) and isinstance(arg, np.ndarray)
        except:
            if reflect:
                out = 2 * pi - out
            if abs(arg) > 1:
                raise ValueError('arrcos arg = {}'.format(arg))
        else:
            out[reflect] = 2 * pi - out[reflect]
            if np.any(np.abs(arg)) > 1.0:
                bad = np.abs(arg) > 1.0
                raise ValueError('arrcos args = {}'.format(arg[bad]))

        return out

    # Semi major axis
    r = np.sqrt(x ** 2 + y ** 2 + z ** 2)
    v2 = vx ** 2 + vy ** 2 + vz ** 2
    a = 1 / (2 / r - v2 / M_G)
    # a_alt = a - R_E

    # Period
    T = 2 * pi * sqrt(a ** 3 / M_G)
    # n = 1 / T

    # Eccentricity
    f1 = (1 / r - 1 / a)
    f2 = (x * vx + y * vy + z * vz) / M_G
    ei = f1 * x - f2 * vx
    ej = f1 * y - f2 * vy
    ek = f1 * z - f2 * vz
    e = sqrt(ei * ei + ej * ej + ek * ek)

    # Orbit inclination
    hi = y * vz - z * vy
    hj = z * vx - x * vz
    hk = x * vy - y * vx
    h = sqrt(hi ** 2 + hj ** 2 + hk ** 2)
    i = arccos(hk / h)  # radians

    # Ascending node
    Wi = -hj
    Wj = hi
    W = sqrt(Wi ** 2 + Wj ** 2)
    aw = arccos_2pi(Wi / W, Wj < 0)

    # Argument of perigee
    w = arccos_2pi((Wi * ei + Wj * ej) / (W * e), ek < 0)

    # Mean Anomaly
    n = arccos_2pi((x * ei + y * ej + z * ek) / (e * r), f2 < 0)

    # Eccentric Anomaly
    E = arccos_2pi((e + cos(n)) / (1 + e * cos(n)), n > pi)

    # Mean Anomaly
    M = E - e * sin(E)

    i = degrees(i)
    aw = degrees(aw)
    w = degrees(w)
    M = degrees(M)

    return {'semi_major_axis': a,
            'orbit_period': T,
            'eccentricity': e,
            'inclination': i,
            'ascending_node': aw,
            'argument_perigee': w,
            'mean_anomaly': M}


class DerivedParameterOrbit(base.DerivedParameter):
    content_root = 'orbit'
    rootparams = ['orbitephem0_x', 'orbitephem0_y', 'orbitephem0_z',
                  'orbitephem0_vx', 'orbitephem0_vy', 'orbitephem0_vz']
    time_step = 328.0
    max_gap = 1000.0

    def get_orbital_element(self, data):
        # Lower case and chop off the initial "DP_"
        param = self.__class__.__name__.lower()[3:]

        start = DateTime(data.times[0]).date
        stop = DateTime(data.times[-1]).date
        if (start, stop) in ELEMENTS_CACHE:
            return ELEMENTS_CACHE[start, stop][param]

        # Get values in km and km/sec
        x = data['orbitephem0_x'].vals / 1000.
        y = data['orbitephem0_y'].vals / 1000.
        z = data['orbitephem0_z'].vals / 1000.
        vx = data['orbitephem0_vx'].vals / 1000.
        vy = data['orbitephem0_vy'].vals / 1000.
        vz = data['orbitephem0_vz'].vals / 1000.

        elements = calc_orbital_elements(x, y, z, vx, vy, vz)
        ELEMENTS_CACHE[start, stop] = elements
        return elements[param]

    def calc(self, data):
        return self.get_orbital_element(data)


class DP_SEMI_MAJOR_AXIS(DerivedParameterOrbit):
    """
    Orbital element: semi-major axis (km)
    """


class DP_ORBIT_PERIOD(DerivedParameterOrbit):
    """
    Orbital element: period (sec)
    """


class DP_ECCENTRICITY(DerivedParameterOrbit):
    """
    Orbital element: eccentricity
    """


class DP_INCLINATION(DerivedParameterOrbit):
    """
    Orbital element: inclination (degrees)
    """


class DP_ASCENDING_NODE(DerivedParameterOrbit):
    """
    Orbital element: right ascension of ascending node (degrees)
    """


class DP_ARGUMENT_PERIGEE(DerivedParameterOrbit):
    """
    Orbital element: argument of perigee (degrees)
    """


class DP_MEAN_ANOMALY(DerivedParameterOrbit):
    """
    Orbital element: mean anomaly (degrees)
    """
