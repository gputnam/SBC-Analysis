#Author: Trent Cwiok
import pdb
import numpy as np
import math
import SBCcode as sbc

from matplotlib import pyplot as plt
from scipy import signal as sig

def main(event_dict, low_tau=5e-4, high_tau=5e-3, window_width_ms=10, offset_from_t0_ms=2, bin_edges=np.array((500, 10000), dtype=np.float64), show_figures_t0=False, show_figures_loudness=False):
	"""
	A top-level function that makes calls to the FindBubbleStart and FindLoudness helper functions.
	It then parses the output of those functions and returns a dictionary containing that information.
	
	Required inputs:
	event_dict -- an event dictionary generated by SBCcode.get_event()

	Keyword arguments:
	low_tau -- a Float, the time constant used by the low-pass filter applied to the acoustic trace in FindBubbleStart 
	high_tau -- identical to low_tau, but used in the high-pass filter
	window_width_ms -- a Float, the length of each time window slice taken of the FFT, in milliseconds
	offset_from_t0_ms -- a Float, the number of milliseconds before the bubble t0 where the first time window will start
	bin_edges -- a 1-dimensional Ndarray, contains the values of the bin edges in Hz used to partition the FFT
	show_figures-- a Boolean, determines if figures showing the bubble_t0 and FFT plots will be displayed

	Output format:
	Returns a dictionary containing the following keys...
	bubble_t0 -- the time in milliseconds where the bubble appears in the acoustic trace
	bubble_loudness -- an Ndarray, contains the loudness calculated for each time window between each set of bin edges
	bin_edges -- an Ndarray, a copy of the bin edges passed to the function to help with indexing the bubble loudnesses
	time_windows -- an Ndarray, the actual times in milliseconds that were samples from the acoustic trace
	"""
	acoustic_analysis_dict = dict()

	#Calls FindBubbleStart and stores the returned value to its respective dictionary entry
	bubble_start = FindBubbleStart(event_dict, low_tau, high_tau, show_figures_t0)
	#pdb.set_trace()
	acoustic_analysis_dict['bubble_t0'] = bubble_start[1]

	#Calls FindLoudness and stores the returned values of the tuple to their respective dictionary entries
	bubble_loudness = FindLoudness(event_dict, bubble_start[0], window_width_ms, offset_from_t0_ms, bin_edges, show_figures_loudness)
	acoustic_analysis_dict['bubble_loudness'] = bubble_loudness[0]
	acoustic_analysis_dict['ap_time_windows'] = bubble_loudness[1]
	acoustic_analysis_dict['ap_frequency_bins'] = bubble_loudness[2]

	return acoustic_analysis_dict


def FindBubbleStart(event_dict, low_tau, high_tau, show_figures_t0):
	"""
	A helper function to main which finds the time in the acoustic trace at which bubble formation begins.

	Required inputs:
	See main's keyword arguments -- all inputs are optional inputs of main

	Output format:
	Returns a tuple containing both the time of bubble formation and its corresponding index
	"""

	# Checks that the event dictionary was properly loaded and passed
	if not event_dict['fastDAQ']['loaded']:
		print "Failed to load fastDAQ dictionary, process terminated."
		return np.float64(np.NaN), np.float64(np.NaN)

	# Reads and stores information determined by the DAQ
	time_zero = int(event_dict['fastDAQ']['caldata']['pretrigger_samples'][0])
	time_step = event_dict['fastDAQ']['caldata']['dt'][0]

	# Calculates the average and standard deviation of the trace before any bubble formation
	base_sampling = event_dict['fastDAQ']['Piezo1'][:100000]
	base_mean = np.mean(base_sampling, dtype = np.float64)
	base_stdev = np.std(base_sampling, dtype = np.float64)
	# Normalizes the acoustic trace to an average of zero
	event_dict['fastDAQ']['Piezo1'] -= base_mean

	# Uses scipy's low and high pass filters to create a bandwidth filter -- bandwidth is determined by low and high tau and are passed to the function
	filtered_low = sig.lfilter([1-math.exp(-time_step/low_tau)], [1, -math.exp(-time_step/low_tau)], event_dict['fastDAQ']['Piezo1'], axis = 0)
	filtered_both = sig.lfilter([math.exp(-time_step/high_tau),-math.exp(-time_step/high_tau)], [1, -math.exp(-time_step/high_tau)], filtered_low, axis = 0)
	
	# Calculates the average and standard deviation of the filtered trace before bubble formation
	filtered_sampling = filtered_both[:100000]
	filtered_mean = np.mean(filtered_sampling, dtype = np.float64)
	filtered_stdev = np.std(filtered_sampling, dtype = np.float64)
	# Normalizes mean to zero
	filtered_both -= filtered_mean

	# Scales both the filtered and unfiltered traces by their respective standard deviations -- Y-axis is now in units of sigma
	filtered_both = (filtered_both/filtered_stdev)
	event_dict['fastDAQ']['Piezo1'] = (event_dict['fastDAQ']['Piezo1']/base_stdev)

	# Declaration of loop variables
	bubble = False
	low_res_start = None
	spike = False
	index = 0
	# This loop starts from the start of the trace and steps forward until it finds a region where the trace exceeeds a certain
	# absolute value standard deviation threshold.  If the trace remains above this threshold for a certain duration, it records
	# the index where the trace first crossed the threshold as a bubble.
	while (not bubble) and (index < time_zero):
		value = abs(filtered_both[index])
		# If the value is less than 2 sigma, there is no bubble
		if value < 2 and low_res_start != None:
			spike = False
			low_res_start = None

		# Else, a bubble start is labelled
		elif value >= 2 and low_res_start == None:
			low_res_start = index
			spike = True

		# If the bubble label persists, it is confirmed and the loop ends
		if spike and (abs(event_dict['fastDAQ']['time'][index]-event_dict['fastDAQ']['time'][low_res_start]) > .0001):
			bubble = True
		index += 1

	# Declaration of loops variables
	index = low_res_start
	high_res_start = None
	found = False
	# This loop starts from where the previous loop labelled the bubble formation and searches for the start of the bubble with
	# finer resolution.  It then steps BACKWARDS, searching for a point at which the trace has a standard deviation of essentially
	# zero, and if it remains within that range for a certain duration, it stores that value as the t0 of the bubble formation.
	while not found and (index > 0):
		x1 = index
		x2 = index - 100
		y1 = filtered_both[x1]
		y2 = filtered_both[x2]
		slope = GetAbsSlope(y1, y2, x1, x2)

		if (slope < .5) and (filtered_both[x2] < 3):
			high_res_start = x2
			found = True

		index -= 1

	if not found:
		return np.float64(np.NaN), np.float64(np.NaN)

	# Optional function argument for plotting tools
	if show_figures_t0:
		plt.plot(event_dict['fastDAQ']['time'], event_dict['fastDAQ']['Piezo1'], 'b-',event_dict['fastDAQ']['time'], filtered_both, 'r-', event_dict['fastDAQ']['time'][int(high_res_start)], 0, 'r^', markersize = 10.0)
		plt.axis([-.2,.2,-100,100])
		plt.show()

	return high_res_start, event_dict['fastDAQ']['time'][high_res_start]


def FindLoudness(event_dict, bubble_t0_index, window_width_ms, offset_from_t0_ms, bin_edges, show_figures_loudness):
	"""
	
	"""

	# Checks that the event dictionary was properly loaded and passed
	if not event_dict['fastDAQ']['loaded']:
		print "Failed to load fastDAQ dictionary, process terminated."
		return np.float64(np.NaN), np.float64(np.NaN), np.float64(np.NaN)

	if np.isnan(bubble_t0_index):
		return np.float64(np.NaN), np.float64(np.NaN), np.float64(np.NaN)

	# Reads and stores information determined by the DAQ
	time_step = event_dict['fastDAQ']['caldata']['dt'][0]

	# Converts function inputs from milliseconds to seconds
	window_width_sec = window_width_ms*1e-3
	offset_from_t0_sec = offset_from_t0_ms*1e-3

	# Gets the indices of those times
	window_width_index = int(window_width_sec/time_step)
	offset_from_t0_index = int(offset_from_t0_sec/time_step)

	# Generates an n-by-2 Ndarray, where n is the number of time windows (NOT IMPLEMENTED): axis 0 is the start of each window, axis 1 the end
	times_array_sec = np.array([(event_dict['fastDAQ']['time'][bubble_t0_index-(2*offset_from_t0_index)-window_width_index],
		event_dict['fastDAQ']['time'][bubble_t0_index-(2*offset_from_t0_index)]), (event_dict['fastDAQ']['time'][bubble_t0_index-offset_from_t0_index],
		event_dict['fastDAQ']['time'][bubble_t0_index-offset_from_t0_index+window_width_index])], dtype=np.float64)

	# Converts all the times in the times_array to milliseconds
	times_array_ms = times_array_sec*1000
	
	try:
		# Performs a Fast Fourier Transform on the bubble and non-bubble parts of the trace, then calculates the power
		fft_bubble_amp = np.fft.rfft(event_dict['fastDAQ']['Piezo1']
			[bubble_t0_index-offset_from_t0_index:bubble_t0_index-offset_from_t0_index+window_width_index], axis=0)
		fft_bubble_power = (abs(fft_bubble_amp))**2

		fft_sample_amp = np.fft.rfft(event_dict['fastDAQ']['Piezo1']
			[bubble_t0_index-(2*offset_from_t0_index)-window_width_index:bubble_t0_index-(2*offset_from_t0_index)], axis=0)
		fft_sample_power = (abs(fft_sample_amp))**2

	except IndexError:
		print "Index error encountered with the time windows. Process Terminated."
		return np.float64(np.NaN), np.float64(np.NaN), np.float64(np.NaN)

	# Finds the df of the Fourier Transform	
	freq_step = 1/window_width_sec

	# Uses the df to generate the range of Hertz which the FFT spans
	freq_scale = np.linspace(0, freq_step*len(fft_bubble_power), num=len(fft_bubble_power))

	# Creates an empty array to store the loudness of the bubble and non-bubble time windows
	loudness_array = np.zeros((2, len(bin_edges)-1), dtype=np.float64)

	# Finds the corresponding indices of the frequency bin edges and stores them in an array
	bin_edges_indices = np.zeros(len(bin_edges), dtype=np.float64)
	for ii in range(len(bin_edges)):
		masked = freq_scale < bin_edges[ii]
		index = np.nonzero(masked)[0]
		try:
			bin_edges_indices[ii] = index[-1]
		except IndexError:
			print "Index error encountered in finding bin edge indices.  Process terminated."
			return np.float64(np.NaN), np.float64(np.NaN), np.float64(np.NaN)
	
	# Uses the bin edge indices to calculate the loudness of each frequency bin -- the loudness is the sum of all points times df squared
	for ii in range(len(bin_edges_indices)-1):
		bubble_loudness = np.sum((fft_bubble_power*(freq_step**2))[bin_edges_indices[ii]:bin_edges_indices[ii+1]], dtype=np.float64)
		sample_loudness = np.sum((fft_sample_power*(freq_step**2))[bin_edges_indices[ii]:bin_edges_indices[ii+1]], dtype=np.float64)
		loudness_array[0][ii] = sample_loudness
		loudness_array[1][ii] = bubble_loudness

	# Optional function argument for plotting tools
	if show_figures_loudness:
		plt.plot(freq_scale, fft_bubble_power*(freq_scale**2), 'b-', freq_scale, fft_sample_power*(freq_scale**2), 'r--')
		plt.loglog()
		plt.show()

	return loudness_array, times_array_ms, bin_edges


def GetAbsSlope(x1, x2, y1, y2):
	return abs((y1-y2)/(x1-x2))