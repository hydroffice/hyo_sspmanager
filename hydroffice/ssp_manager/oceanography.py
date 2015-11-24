from __future__ import absolute_import, division, print_function, unicode_literals

import numpy as np
import math
import logging

log = logging.getLogger(__name__)


def _adtg(S, T, P):
    a0 = 3.5803E-5
    a1 = 8.5258E-6
    a2 = -6.836E-8
    a3 = 6.6228E-10

    b0 = 1.8932E-6
    b1 = -4.2393E-8

    c0 = 1.8741E-8
    c1 = -6.7795E-10
    c2 = 8.733E-12
    c3 = -5.4481E-14

    d0 = -1.1351E-10
    d1 = 2.7759E-12

    e0 = -4.6206E-13
    e1 = 1.8676E-14
    e2 = -2.1687E-16

    return a0 + (a1 + (a2 + a3 * T) * T) * T + (b0 + b1 * T) * (S - 35) + \
        ((c0 + (c1 + (c2 + c3 * T) * T) * T) + (d0 + d1 * T) * (S - 35)) * P + (e0 + (e1 + e2 * T) * T) * P * P


def potential_temperature(T, S, P, PR):
    delP = PR - P
    delth = delP * _adtg(S, T, P)
    th = T + 0.5 * delth
    q = delth

    delth = delP * _adtg(S, th, P + 0.5 * delP)
    th += (1 - 1 / np.sqrt(2)) * (delth - q)
    q = (2 - np.sqrt(2)) * delth + (-2 + 3 / np.sqrt(2)) * q

    delth = delP * _adtg(S, th, P + 0.5 * delP)
    th += (1 + 1 / np.sqrt(2)) * (delth - q)
    q = (2 + np.sqrt(2)) * delth + (-2 - 3 / np.sqrt(2)) * q

    delth = delP * _adtg(S, th, P + delP)
    pottemp = th + (delth - 2 * q) / 6

    return pottemp


def insitu_temperature(T, S, P, P_ref):
    # Temperature in degrees C
    # Salinity in practical salinity units (ppt)
    # Pressures in decibar

    if P == P_ref:
        return (T)

        # Potential temperature function takes pressure in units of 10*kPa so multiply MPa * 1000 to get kPa, divide by 10 to them in 10*kPa, net result: multiply by 100
        P *= 100
        P_ref *= 100

    temperature = T

    new_pot_t = potential_temperature(T, S, P, P_ref)

    if new_pot_t < T:
        sign = 1
    else:
        sign = -1

    dT = new_pot_t - temperature

    while np.abs(dT) > 0.001:
        temperature += sign * 0.001
        new_pot_t = potential_temperature(temperature, S, P, P_ref)
        dT = new_pot_t - T

    return temperature


def depth2press(depth, lat):
    # depth in metres
    # lat in decimal degrees
    # pressure in decibars

    if lat == None:
        lat = 30

    rlat = lat * np.pi / 180.0
    rlat = np.sin(rlat)

    g = 9.7803 * (1 + 5.3e-3 * rlat ** 2)
    k = (g - 2e-5 * depth) / (9.80612 - 2e-5 * depth)

    h45 = 1.00818e-2 * depth + 2.465e-8 * depth ** 2 - 1.25e-13 * depth ** 3 + 2.8e-19 * depth ** 4
    press = 100 * h45 * k

    return (press)


def press2depth(press, lat):
    # pressure in decibars
    # latitude in decimal degrees
    # depth in metres

    if lat is None:
        lat = 30

    press /= 100

    rlat = lat * np.pi / 180
    rlat = np.sin(rlat)

    g = 9.780318 * (1 + 5.2788e-3 * rlat ** 2 + 2.36e-5 * rlat ** 4)

    depth = (9.72659e2 * press - 2.512e-1 * press ** 2 + 2.279e-4 * press ** 3 - 1.82e-7 * press ** 4) / \
            (g + 1.092e-4 * press)

    return depth


def salinity(depth, speed, temp, lat):
    # Depth in meters
    # temp in degrees Celsius
    # latitude in decimal degrees
    high_value = 50.0
    low_value = 0.0
    num_iterations = 0
    salinity = 0

    if lat == None:
        lat = 30

    speed_calc = 0

    while np.abs(speed_calc - speed) > 0.001:
        salinity = (high_value + low_value) / 2.0
        speed_calc = soundspeed(depth, temp, salinity, lat)
        if speed_calc > speed:
            high_value = salinity
        else:
            low_value = salinity

        num_iterations = num_iterations + 1

        # In case we get a wonky sound speed measurement 
        if high_value == low_value:
            break

    return salinity


def soundspeed(depth, temp, sal, lat):
    # Depth in metres
    # Temp in degrees celcius
    # Salinity in practical salinity units (ppt)
    # Latitude in decimal degrees
    # Sound speed in m/s
    # range of validity 0 - 40 Deg C
    # 0 - 40 ppt
    # 0 - 1000 bars (~1000m)

    if lat == None:
        lat = 30

    press = depth2press(depth, lat) / 10

    c00 = 1402.388
    c01 = 5.03830
    c02 = -5.81090e-2
    c03 = 3.3432e-4
    c04 = -1.47797e-6
    c05 = 3.1419e-9
    c10 = 0.153563
    c11 = 6.8999e-4
    c12 = -8.1829e-6
    c13 = 1.3632e-7
    c14 = -6.1260e-10
    c20 = 3.1260e-5
    c21 = -1.7111e-6
    c22 = 2.5986e-8
    c23 = -2.5353e-10
    c24 = 1.0415e-12
    c30 = -9.7729e-9
    c31 = 3.8513e-10
    c32 = -2.3654e-12

    a00 = 1.389
    a01 = -1.262e-2
    a02 = 7.166e-5
    a03 = 2.008e-6
    a04 = -3.21e-8
    a10 = 9.4742e-5
    a11 = -1.2583e-5
    a12 = -6.4928e-8
    a13 = 1.0515e-8
    a14 = -2.0142e-10
    a20 = -3.9064e-7
    a21 = 9.1061e-9
    a22 = -1.6009e-10
    a23 = 7.994e-12
    a30 = 1.100e-10
    a31 = 6.651e-12
    a32 = -3.391e-13

    b00 = -1.922e-2
    b01 = -4.42e-5
    b10 = 7.3637e-5
    b11 = 1.7950e-7

    d00 = 1.727e-3
    d10 = -7.9836e-6

    D = d00 + (d10 * press)

    B = b00 + b01 * temp + (b10 + b11 * temp) * press

    A = (a00 + a01 * temp + a02 * temp ** 2 + a03 * temp ** 3 + a04 * temp ** 4) + (
                                                                                   a10 + a11 * temp + a12 * temp ** 2 + a13 * temp ** 3 + a14 * temp ** 4) * press + (
                                                                                                                                                                     a20 + a21 * temp + a22 * temp ** 2 + a23 * temp ** 3) * press ** 2 + (
                                                                                                                                                                                                                                          a30 + a31 * temp + a32 * temp ** 2) * press ** 3

    Cw = (c00 + c01 * temp + c02 * temp ** 2 + c03 * temp ** 3 + c04 * temp ** 4 + c05 * temp ** 5) + (
                                                                                                      c10 + c11 * temp + c12 * temp ** 2 + c13 * temp ** 3 + c14 * temp ** 4) * press + (
                                                                                                                                                                                        c20 + c21 * temp + c22 * temp ** 2 + c23 * temp ** 3 + c24 * temp ** 4) * press ** 2 + (
                                                                                                                                                                                                                                                                               c30 + c31 * temp + c32 * temp ** 2) * press ** 3

    SV = Cw + A * sal + B * sal ** 1.5 + D * sal ** 2

    return SV


def salinity2conductivity(sal, pressure, temp):
    # Input units are salinity in psu, pressure in dBar and temperature in deg. C.

    conductivity = 0
    conductivity_step = 0.1
    max_conductivity = 100

    calc_salinity = -1
    last_conductivity = conductivity
    last_salinity = calc_salinity

    while conductivity < max_conductivity:
        calc_salinity = conductivity2salinity(conductivity, pressure, temp)
        # log.debug("%f %f %f %f" % (count, conductivity, calc_salinity, salinity))

        if calc_salinity > sal:
            break

        last_conductivity = conductivity
        last_salinity = calc_salinity

        conductivity += conductivity_step

    delta_cond = conductivity - last_conductivity
    delta_sal = calc_salinity - last_salinity

    conductivity = last_conductivity + delta_cond / delta_sal * (sal - last_salinity)

    # log.debug("Interpolated conductivity: %f" % conductivity)
    # calc_salinity = conductivity2salinity( conductivity, P, T)
    # log.debug("Check new calc'd salinity against desired %f %f" % (calc_salinity, S))

    return conductivity


def conductivity2salinity(C, P, T):
    # From M. Tomczak little javascript on his website: http://www.es.flinders.edu.au/~mattom/Utilities/salcon.html
    # It's based on Fofonoff and Millard (1983)
    # Input units are conductivity in mmho/cm, pressure in dBar and temperature in deg. C.

    e1 = 2.07e-5
    e2 = -6.37e-10
    e3 = 3.989e-15

    d1 = 3.426e-2
    d2 = 4.464e-4
    d3 = 4.215e-1
    d4 = -3.107e-3

    R = C / 42.914
    R1 = P * (e1 + (e2 + e3 * P) * P)
    R2 = 1 + (d1 + d2 * T) * T + (d3 + d4 * T) * R
    Rp = 1 + R1 / R2

    c0 = 0.6766097
    c1 = 2.00564e-2
    c2 = 1.104259e-4
    c3 = -6.9698e-7
    c4 = 1.0031e-9

    rt = c0 + (c1 + (c2 + (c3 + c4 * T) * T) * T) * T

    a0 = 0.0080
    a1 = -0.1692
    a2 = 25.3851
    a3 = 14.0941
    a4 = -7.0261
    a5 = 2.7081

    b0 = 0.0005
    b1 = -0.0056
    b2 = -0.0066
    b3 = -0.0375
    b4 = 0.0636
    b5 = -0.0144

    k = 0.0162
    CR = R / (Rp * rt)
    Rtx = math.sqrt(CR)
    delT = T - 15
    delS = (delT / (1 + k * delT)) * (b0 + (b1 + (b2 + (b3 + (b4 + b5 * Rtx) * Rtx) * Rtx) * Rtx) * Rtx)

    S = a0 + (a1 + (a2 + (a3 + (a4 + a5 * Rtx) * Rtx) * Rtx) * Rtx) * Rtx + delS

    return S


def attenuation(f, T, S, D, pH):
    # Francois & Garrison, J. Acoust. Soc. Am., Vol. 72, No. 6, December 1982
    # f frequency (kHz)
    # T Temperature (degC)
    # S Salinity (ppt)
    # D Depth (m)
    # pH Acidity
    abs_temp = 273.0 + T

    # sound speed calculation
    c = 1412.0 + 3.21 * T + 1.19 * S + 0.0167 * D

    # Boric Acid Contribution
    A1 = (8.86 / c) * math.pow(10.0, (0.78 * pH - 5.0))
    P1 = 1.0

    f1 = 2.8 * math.pow((S / 35.0), 0.5) * math.pow(10.0, 4.0 - (1245.0 / abs_temp))

    # MgSO4 Contribution 
    A2 = (21.44 * S / c) * (1.0 + 0.025 * T)
    P2 = (1.0 - 1.37E-4 * D) + (6.2E-9 * D * D)
    f2 = (8.17 * math.pow(10.0, 8.0 - 1990.0 / abs_temp)) / (1.0 + 0.0018 * (S - 35.0))

    # Pure Water Contribution
    if T <= 20.0:
        A3 = 4.937E-4 - 2.59E-5 * T + 9.11E-7 * T * T - 1.50E-8 * T * T * T
    else:
        A3 = 3.964E-4 - 1.146E-5 * T + 1.45E-7 * T * T - 6.5E-10 * T * T * T

    P3 = 1.0 - 3.83E-5 * D + 4.9E-10 * D * D

    boric = (A1 * P1 * f1 * f * f) / (f * f + f1 * f1)
    magnes = (A2 * P2 * f2 * f * f) / (f * f + f2 * f2)
    purewat = A3 * P3 * f * f

    atten = boric + magnes + purewat

    return atten



