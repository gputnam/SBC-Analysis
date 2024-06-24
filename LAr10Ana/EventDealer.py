import os
import re
import shutil
import time

import numpy as np
import copy
import numpy.matlib

from EventAnalysis import EventAnalysis as eva
from AcousticT0 import AcousticAnalysis as aa
from DataHandling.GetSBCEvent import GetEvent as get_event
from DataHandling.WriteBinary import WriteBinaryNtupleFile as wb
from DataHandling.ReadBinary import ReadBlock as rb

def BuildEventList(rundir, first_event=0, last_event=-1):
    # Inputs:
    #   rundir: Directory for the run
    #   first_event: Index of first event
    #   last_event: Index of last_event
    # Outputs: A sorted list of events from rundir
    # Possible Issues: If we ever move to a different naming scheme, this needs to be re-written.
    eventdirlist = os.listdir(rundir)
    eventdirlist = filter(lambda fn: (not re.search('^\d+$', fn) is None) and
                                     os.path.isdir(os.path.join(rundir, fn)),
                          eventdirlist)
    eventdirlist = filter(lambda fn: os.path.exists(os.path.join(rundir,
                                                                 *[fn, 'Event.txt'])), eventdirlist)
    eventlist = np.intp(list(eventdirlist))
    eventlist = eventlist[eventlist >= first_event]
    if last_event >= 0:
        eventlist = eventlist[eventlist <= last_event]
    return np.sort(eventlist)


def ProcessFromReconfile(reconfile, datadir='/exp/e961/data/SBC-17-data',
                         dataset='SBC-2017', recondir='.', process_list=None):
    # Inputs:
    #   reconfile: Location of file that will be used for event list
    #   dataset: Indicator used for filtering which analyses to run
    #   recondir: Location of recon data/where we want to output our binary files
    #   process_list: List of analyses modules to run. example: ["acoustic", "event", ""]
    # Outputs: Nothing. Saves binary files to recondir.
    if process_list is None:
        process_list = []  # This is needed since lists are mutable objects. If you have a default argument
                           # as a mutable object, then the default argument can *change* across multiple
                           # function calls since the argument is created ONCE when the function is defined.
    evlist_source = rb(reconfile)

    if not os.path.isdir(recondir):
        os.mkdir(recondir)

    if dataset == 'SBC-2017':
        loadlist = []
        for process in process_list:
            if process.lower().strip() == 'event':
                loadlist.append('event')
            elif process.lower().strip() == 'images':
                loadlist.append('images')
            elif process.lower().strip() == 'exposure':
                loadlist.append('slowDAQ')
                loadlist.append('event')
            elif process.lower().strip() == 'history':
                loadlist.append('slowDAQ')
            elif any(process.lower().strip() == x for x in ['dytran', 'acoustic']):
                loadlist.append('fastDAQ')
            elif any(process.lower().strip() == x for x in ['pmtfda', 'pmt', 'timing']):
                loadlist.append('fastDAQ')
                loadlist.append('PMTtraces')
        loadlist = list(set(loadlist))
    else:
        loadlist = ['~']

    exposure_out = []

    process_list = [p.lower().strip() for p in process_list]
    eventlist = np.concatenate((evlist_source['runid'], evlist_source['ev'][:,None]), axis=1)

    for ev in eventlist:
        runname = str(ev[0])+'_'+str(ev[1])
        rundir = os.path.join(datadir, runname)
        t0 = time.time()
        print('Starting event ' + runname + '/' + str(ev[2]))
        thisevent = get_event(rundir, ev[2], *loadlist)
        print('Time to load event:  '.rjust(35) +
              str(time.time() - t0) + ' seconds')

    if "exposure" in process_list:
        wb(os.path.join(recondir,
                        'ExposureAnalysis_all.bin'), exposure_out,
           rowdef=1, initialkeys=['runid', 'ev'], drop_first_dim=False)

    return


def ProcessSingleRun2(rundir, dataset='SBC-2017', recondir='.', process_list=None):
    # Inputs:
    #   rundir: Location of raw data
    #   dataset: Indicator used for filtering which analyses to run
    #   recondir: Location of recon data/where we want to output our binary files
    #   process_list: List of analyses modules to run. example: ["acoustic", "event", ""]
    # Outputs: Nothing. Saves binary files to recondir.
    if process_list is None:
        process_list = []  # This is needed since lists are mutable objects. If you have a default argument
                           # as a mutable object, then the default argument can *change* across multiple
                           # function calls since the argument is created ONCE when the function is defined.
    runname = os.path.basename(rundir)
    runid_str = runname.split('_')
    runid = np.int32(runid_str)
    #run_recondir = os.path.join(recondir, runname)
    run_recondir = recondir

    if not os.path.isdir(run_recondir):
        os.mkdir(run_recondir)

    if dataset == 'SBC-2017':
        loadlist = []
        for process in process_list:
            if process.lower().strip() == 'event':
                loadlist.append('event')
            elif any(process.lower().strip() == x for x in ['acoustic']):
                loadlist.append('fastDAQ')
        loadlist = list(set(loadlist))
    else:
        loadlist = ['~']

    event_out = []
    acoustic_out = []

    event_default = eva(None)
    acoustic_default = aa(None, None)
    # image_default = BubbleFinder(None, None, None ,None, None, None)

    process_list = [p.lower().strip() for p in process_list]
    print("Starting run " + rundir)
    eventlist = BuildEventList(rundir)

    for ev in eventlist:
        t0 = time.time()
        print('Starting event ' + runname + '/' + str(ev))
        npev = np.array([ev], dtype=np.int32)
        thisevent = get_event(rundir, ev, *loadlist)
        print('Time to load event:  '.rjust(35) +
              str(time.time() - t0) + ' seconds')

        if "event" in process_list:
            # zeroth order of business:  copy event data
            t1 = time.time()
            if dataset == 'SBC-2017':
                try:
                    event_out.append(eva(thisevent))
                except:
                    event_out.append(copy.deepcopy(event_default))
                event_out[-1]['runid'] = runid
                event_out[-1]['ev'] = npev
            et = time.time() - t1
            print('Event analysis:  '.rjust(35) + str(et) + ' seconds')

        if "acoustic" in process_list:
            # Acoustic analysis
            t1 = time.time()
            if dataset == 'SBC-2017':
                tau_peak = 0.0025884277467056165  # <-- This comes from TauResultAnalysis.py (J.G.)
                tau_average = 0.0038163479219674467  # <-- This also ^^
                # lower_f = 20000 OLD...
                # upper_f = 40000
                lower_f = 1000
                upper_f = 25000
                piezo_fit_type = 0
                try:
                    acoustic_out.append(aa(ev=thisevent, tau=tau_average, piezo_fit_type=piezo_fit_type,
                                           corr_lowerf=lower_f, corr_upperf=upper_f))
                except:
                    raise
                    acoustic_out.append(copy.deepcopy(acoustic_default))
                acoustic_out[-1]['runid'] = runid
                acoustic_out[-1]['ev'] = npev
            et = time.time() - t1
            print('Acoustic analysis:  '.rjust(35) + str(et) + ' seconds')

        print('*** Full event analysis ***  '.rjust(35) +
              str(time.time() - t0) + ' seconds')


    #for process in process_list:
    if "event" in process_list:
        wb(os.path.join(run_recondir,
                        'EventAnalysis_' + runname + '.bin'), event_out,
           rowdef=1, initialkeys=['runid', 'ev'], drop_first_dim=False)

    if "acoustic" in process_list:
        wb(os.path.join(run_recondir,
                        'AcousticAnalysis_' + runname + '.bin'), acoustic_out,
           rowdef=1, initialkeys=['runid', 'ev'], drop_first_dim=False)
    return
