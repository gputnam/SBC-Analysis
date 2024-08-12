from EventDealer import ProcessSingleRun2
import sys

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ProcessSingleRun2(
            rundir=sys.argv[1],
            recondir=sys.argv[2],
            process_list = ["acoustic", "event", "exposure"])
    else:
        ProcessSingleRun2(
            # rundir="/exp/e961/data/SBC-17-data/20171007_3",
            rundir="/exp/e961/data/SBC-17-data/20171007_6",
            recondir="/exp/e961/data/users/gputnam/test-acoustic", # Use your own directory for testing~
            process_list = ["acoustic", "event", "exposure"])
