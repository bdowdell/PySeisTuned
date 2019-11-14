#!/usr/bin/env python

# This is a simple GUI utility to calculate a seismic tuning wedge
# The base code for this comes from Agile Scientific's Synthetic Tuning Wedge nb
# source: https://github.com/agile-geoscience/xlines/blob/master/notebooks/00_Synthetic_wedge_model.ipynb

import numpy as np


def earthmodel(rock_props):
    """
	Input:
	rock_props as a list of len 6 in Vp-Density pairs

	ex: rock_props = [3000, 2.315, 2200, 2.15, 3000, 2.315]

	this function creates the earth model that is used
	to create the wedge model.  First, three layers are defined.
	Second, each layer is populated with a Vp & Density.
	Finally, the Impedance of each layer is populated
	returns rc
	"""

    # define the initial earth model
    duration, depth = 101, 240
    model = 1 + np.tri(depth, duration, -depth // 3, dtype=int)
    model[: depth // 3, :] = 0

    # Populate each layer of the earth model with specific rock properties
    rocks = np.array(rock_props).reshape(3, 2)

    # use fancy indexing to create an earth model where each layer of the model
    # has Vp & Density at each location
    earth = rocks[model]

    # Calculate the acoustic impedance of each layer
    imp = np.apply_along_axis(np.product, -1, earth)

    # Finally, calculate the reflection coefficients for the interfaces between
    # each layer and then return
    rc = (imp[1:, :] - imp[:-1, :]) / (imp[1:, :] + imp[:-1, :])

    return imp, rc


def wavelet(duration=0.100, dt=0.001, f=25):
    """
	This function defines a Ricker wavelet to convolve with the earth model
	reflection coefficients to build the tuning wedge.
	returns w
	"""
    t = np.linspace(-duration / 2, (duration - dt) / 2, duration / dt)
    w = (1.0 - 2.0 * (np.pi ** 2) * (f ** 2) * (t ** 2)) * np.exp(
        -(np.pi ** 2) * (f ** 2) * (t ** 2)
    )
    return w


def get_wavelet_plot_parms(w):
    """Assumes w is numpy array
    Returns a numpy array
    """
    start = int(len(w) / 2 * -1 - 1)
    stop = int(len(w) / 2)
    num = len(w)
    return np.linspace(start, stop, num)


def tuningwedge(rc, w):
    """
	This function takes the reflection coefficients and convolves them with the
	wavelet to produce a synthetic tuning wedge
	returns synth
	"""

    synth = np.apply_along_axis(
        lambda t: np.convolve(t, w, mode="same"), axis=0, arr=rc
    )
    return synth


def mask_rc(rc):
    """Assumes rc is a numpy array
    Returns a masked numpy array for zero values
    """
    return np.ma.masked_equal(rc, 0)


def tuningcurve(rc, synth, rock_props):
    """
	This function calculates the tuning curve
	Returns: z, z_tuning, amp, z_apparent, z_onset
	"""

    depth = 240

    rocks = np.array(rock_props).reshape(3, 2)
    AI = np.apply_along_axis(np.product, -1, rocks)

    # Determine the wedge thickness at each trace
    # Initially we assume that the top RC is a decrease in impedance,
    # negative value (trough) SEG normal polarity
    if AI[1] < AI[0]:
        top = np.apply_along_axis(np.nanargmin, 0, rc) + 1
        base = np.apply_along_axis(np.nanargmax, 0, rc) + 1
    else:
        top = np.apply_along_axis(np.nanargmax, 0, rc) + 1
        base = np.apply_along_axis(np.nanargmin, 0, rc) + 1

    # calculate the wedge thickness, z, in twt, m, & ft.
    z = base - top

    # Determine the thickness at which synth has max amplitude
    # This is the measured tuning thickness in TWT
    z_tuning = np.nanargmax(abs(synth[np.nanmax(top), :]))

    # Determine the apparent thickness at which synth has max amplitude
    # This represents what is seismically resolvable, in TWT
    if AI[1] < AI[0]:
        topApparent = np.apply_along_axis(np.nanargmin, 0, synth) + 1
        baseApparent = np.apply_along_axis(np.nanargmax, 0, synth) + 1

    else:
        topApparent = np.apply_along_axis(np.nanargmax, 0, synth) + 1
        baseApparent = np.apply_along_axis(np.nanargmin, 0, synth) + 1

    z_apparent = baseApparent - topApparent
    z_apparent[0] = z_apparent[1]

    # Extract the amplitude along the top of the wedge model
    # amp = abs(synth[np.nanmax(top),:])
    ampTop = abs(synth[depth // 3, :])
    amp = ampTop
    # ampBase = abs(np.diag(synth, k=-depth//3))

    # calculate the tuning onset thickness
    ampRef = abs(ampTop[-1])  # grabs amplitude "reference" when z >> z_tuning
    ampPC = [
        ((abs(x) - ampRef) / ampRef) for x in ampTop
    ]  # calculates Percent Change in amp along wedge top
    z_onset = (len(ampTop) - np.argwhere(np.flip(ampPC) > 0.01)[0][0]) - 1

    return z, z_tuning, amp, z_apparent, z_onset


def tuningVLine(amp):
    """
    Assumes amp a numpy array
    Returns min and max values
    """
    ampMin = np.nanmin(amp)
    ampMax = np.nanmax(amp)
    return ampMin, ampMax


def results_summary(inArr):
    """
    Assumes inArr a list
    Returns a string
    """
    rock_props = inArr[0]
    f_central = inArr[1]
    z_tuning_meas_TWT = inArr[2] / 1000
    z_onset_meas_TWT = inArr[3] / 1000

    AI1 = rock_props[0] * rock_props[1] / 1000
    AI2 = rock_props[2] * rock_props[3] / 1000
    vp2 = rock_props[2]
    AI3 = rock_props[4] * rock_props[5] / 1000

    rc1 = (AI2 - AI1) / (AI2 + AI1)
    rc2 = (AI3 - AI2) / (AI3 + AI2)

    f_apparent = f_central * (np.pi / np.sqrt(6))
    f_dom_simm = f_central * 1.3

    z_tuning_widess_TWT = 1 / f_apparent / 2
    z_tuning_simm_TWT = 1 / f_dom_simm / 2

    z_tuning_meas_m = z_tuning_meas_TWT / 2 * vp2
    z_tuning_widess_m = z_tuning_widess_TWT / 2 * vp2
    z_tuning_simm_m = z_tuning_simm_TWT / 2 * vp2

    z_onset_widess_TWT = 1 / f_apparent
    z_onset_simm_TWT = 1 / f_dom_simm

    z_onset_meas_m = z_onset_meas_TWT / 2 * vp2
    z_onset_widess_m = z_onset_widess_TWT / 2 * vp2
    z_onset_simm_m = z_onset_simm_TWT / 2 * vp2

    wlength_widess = vp2 / f_apparent
    wlength_simm = vp2 / f_dom_simm

    z_limit_widess_TWT = 1 / f_apparent / 4
    z_limit_widess_m = z_limit_widess_TWT / 2 * vp2

    z_limit_simm_TWT = 1 / (2.31 * f_dom_simm)
    z_limit_simm_m = z_limit_simm_TWT / 2 * vp2

    summary = """Summary of Measured and Theoretical Values\n
Layer 1 Acoustic Impedance: {} (m/s).(g/cm3)\n
Layer 2 Acoustic Impedance: {} (m/s).(g/cm3)\n
Layer 3 Acoustic Impedance: {} (m/s).(g/cm3)\n
Top Layer Reflection Coefficient: {}\n
Bottom Layer Reflection Coefficient: {}\n
Ricker wavelet Central Frequency: {} Hz\n
Ricker wavelet Apparent Frequency (F_central * pi/sqrt(6)): {} Hz\n
Ricker wavelet Dominant Frequency (F_dom*1.3, Simm & Bacon, 2014): {} Hz\n
Measured Tuning Thickness: {} sec TWT, {} m\n
Theoretical Tuning Thickness (Widess, 1973): {} sec TWT, {} m\n
Theoretical Tuning Thickness (Simm & Bacon, 2014): {} sec TWT, {} m\n
Measured Onset of Tuning Thickness: {} sec TWT, {} m\n
Theoretical Onset of Tuning (Widess, 1973, Lambda/2): {} sec TWT, {} m\n
Theoretical Onset of Tuning (Simm & Bacon, 2014): {} sec TWT, {} m\n
Wavelength (F_apparent): {} m\n
Wavelength (F_dom): {} m\n
Theoretical limit of resolution (F_apparent / 8, Widess, 1973): {} sec TWT, {} m\n
Theoretical limit of resolution (1/2.31*Fdom, Simm & Bacon, 2014): {} sec TWT, {}m
	""".format(
        round(AI1, 2),
        round(AI2, 2),
        round(AI3, 2),
        round(rc1, 4),
        round(rc2, 4),
        f_central,
        round(f_apparent, 2),
        f_dom_simm,
        round(z_tuning_meas_TWT, 4),
        round(z_tuning_meas_m, 1),
        round(z_tuning_widess_TWT, 4),
        round(z_tuning_widess_m, 1),
        round(z_tuning_simm_TWT, 4),
        round(z_tuning_simm_m, 1),
        round(z_onset_meas_TWT, 4),
        round(z_onset_meas_m, 1),
        round(z_onset_widess_TWT, 4),
        round(z_onset_widess_m, 1),
        round(z_onset_simm_TWT, 4),
        round(z_onset_simm_m, 1),
        round(wlength_widess, 2),
        round(wlength_simm, 2),
        round(z_limit_widess_TWT, 4),
        round(z_limit_widess_m, 1),
        round(z_limit_simm_TWT, 4),
        round(z_limit_simm_m, 1),
    )
    return summary
