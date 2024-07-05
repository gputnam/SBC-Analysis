import numpy as np

def SiPMPulses(ev):
    # Stuff to save, with defaults
    default_output = dict(
        baseline=np.array([]),
        rms=np.array([]),
        hit_t0=np.array([]),
        hit_area=np.array([]),
        hit_amp=np.array([]),
        wvf_area=np.array([]),
        second_pulse=np.array([]),
        wvf_timestamp=np.array([]),
    )
    out = default_output

    # One event has N SiPMs readout M times, each with T samples
    # Each readout is stored is ev["sipm_traces"], with a shape (M, N, T)

    # For each SiPM, for each readout, obtain the t0 and the voltage

    # Convert inputs into the waveform in (ns, V)
    raw_traces = ev["sipm_traces"].T / 2**12 # 12 bit
    dc_offset = ev["dc_offsets"].T / 2**16 - 1 # overall offset, 16 bit
    ch_offset = ev["dc_corrections"].T / 2**16 # per-channel offset 8-bit to the 16bit
    dc_range = ev["dc_range"].T  # should be 2V

    traces = ((raw_traces + dc_offset + ch_offset) * dc_range)

    sample_rate = ev["sample_rate"].T / 1e9 # GHz

    # obtain the leading baseline and RMS
    N_SAMPLE_BASELINE = 40

    baseline = traces[:N_SAMPLE_BASELINE].mean(axis=0)
    rms = traces[:N_SAMPLE_BASELINE].std(axis=0)

    # flip the trace and correct for baseline
    trace_V = -(traces - baseline)

    # Start time of hit
    N_SIGMA_THRESHOLD = 5
    above_threshold = trace_V > rms*N_SIGMA_THRESHOLD
    t0_ind = np.argmax(above_threshold, axis=0)
    t0 = t0_ind / sample_rate

    # Final time of hit
    tf_ind = np.argmax(np.cumsum(~above_threshold, axis=0) > t0_ind, axis=0)

    # build index into each waveform
    wvf_index = np.zeros(trace_V.shape, dtype=np.int32)
    wvf_index[:, :, :] = np.arange(0, wvf_index.shape[0]).reshape((wvf_index.shape[0], 1, 1))

    # mask area inside hit
    hit_trace_V = trace_V*(wvf_index >= t0_ind)*(wvf_index < tf_ind)

    # voltage values
    hit_area = hit_trace_V.sum(axis=0)
    hit_amplitude = hit_trace_V.max(axis=0)
    wvf_area = (trace_V*(wvf_index >= t0_ind)).sum(axis=0)

    # Are there any secondary hits after the first one?
    N_SECONDPULSE_TICK_DELAY = 10
    second_pulse = (above_threshold*(wvf_index > (tf_ind + N_SECONDPULSE_TICK_DELAY))).any(axis=0)

    # Get the timestamp and correct for the number of wraps 
    TIMESTAMP_PERIOD = 8 # ns
    timestamps = ev["time_stamp"]%(2**31)
    nwrap = np.cumsum(np.diff(timestamps.astype(np.int64), prepend=0) < 0)
    timestamps_corr = timestamps.astype(np.int64) + nwrap*(2**31)
    timestamps_corr = timestamps_corr*TIMESTAMP_PERIOD

    out["baseline"] = baseline
    out["rms"] = rms
    out["hit_t0"] = t0
    out["hit_area"] = hit_area
    out["hit_amp"] = hit_amplitude
    out["wvf_area"] = wvf_area
    out["second_pulse"] = second_pulse
    out["wvf_timestamp"] = timestamps_corr

    # If no hit was found, set relevant values to nan
    out["hit_t0"][t0 == 0] = np.nan
    out["hit_area"][t0 == 0] = np.nan
    out["hit_amp"][t0 == 0] = np.nan
    out["wvf_area"][t0 == 0] = np.nan
    out["second_pulse"][t0 == 0] = False

    return out


if __name__ == "__main__":
    import os
    from DataHandling import ReadBinary, GetSBCEvent

    path = "/bluearc/storage/SBC-22-caendata"
    file = "202206201045.bin"
    
    filename = os.path.join(path, file)
    
    data = ReadBinary.ReadBlock(filename)
    print(SiPMPulses(data))
