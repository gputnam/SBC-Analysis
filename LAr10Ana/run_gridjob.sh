tar -cvf LAr10ana.tar *.py init.sh requirements.txt ../DataHandling/*.py
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
jobsub_submit --disk=25GB --expected-lifetime=1h --memory=2GB -G coupp --resource-provides=usage_model=OPPORTUNISTIC,OFFSITE,DEDICATED \
	--tar_file_name dropbox:///${SCRIPT_DIR}/LAr10ana.tar \
	-N 1 \
        --singularity-image /cvmfs/singularity.opensciencegrid.org/fermilab/fnal-wn-sl7:latest \
	file://${SCRIPT_DIR}/gridjob.sh \
	/pnfs/coupp/scratch/gputnam/SBC-17-data/20171007_6 \
	/pnfs/coupp/scratch/users/gputnam/test-acoustic-grid
