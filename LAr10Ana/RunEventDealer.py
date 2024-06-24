from EventDealer import ProcessSingleRun2

if __name__ == "__main__":
    ProcessSingleRun2(
            # rundir="/exp/e961/data/SBC-17-data/20171007_3",
            rundir="/exp/e961/data/SBC-17-data/20171007_6",
            recondir="/exp/e961/data/users/gputnam/test-acoustic", # Use your own directory for testing~
            process_list = ["acoustic"])
    pass

