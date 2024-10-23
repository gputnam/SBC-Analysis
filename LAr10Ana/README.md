# Getting started on FNAL servers

1. Send a ticket requesting access to the coupp organization with the [Fermilab Service Desk](https://fermi.servicenowservices.com/wp)
2. Once you have access, ssh into the general purpose virtual machine (GPVM)
   ```
   kinit <username>@FNAL.GOV
   ssh -KYX <username>@couppsbcgpvm01.fnal.gov
   ```
3. The servers use the Alma9 OS. It's easier to get stuff setup with Scientific Linux 7, so setup a container on login:
   ```
   sh /exp/e961/app/users/gputnam/sl7/start_SL7.sh
   ```
4. Navigate to the app directory area, then make a new directory for yourself
   ```
   cd /exp/e961/app/users
   mkdir <username>
   cd <username>
   ```
6. Get the code! Setup an [SSH key for github](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)
   if you do not already have one (follow the "Generating a new SSH key" steps), and then [add it to you github account](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account).
   Then clone the directory into you app users area:
   ```
   git clone git@github.com:gputnam/SBC-Analysis.git
   ```
Now you have access to the code on the Fermilab servers! See below for instructions on other things you may want to do next: 
how to setup a python virtual environment, how to log back into the fermilab servers, how to submit grid jobs, and others.

# Logging back into the Fermilab servers
Once you have your account setup, to get back to your app area from your laptop, run:
```
ssh -KYX <username>@couppsbcgpvm01.fnal.gov
cd /exp/e961/app/users/<username>
sh /exp/e961/app/users/gputnam/sl7/start_SL7.sh
```
You may get an authentication error if you have not run `kinit` in about a day. In that case, before `ssh`-ing, run:
```
kinit <username>@FNAL.GOV
```
# Making a python Virtual Environment

SBC analysis mostly relies on python code, with a few external dependencies. It's useful to have your own python virtual environment to store those dependencies. 
Once you have the SBC-Analysis repository downloaded, navigate to `SBC-Analysis/`. Then run:
```
source LAr10Ana/init.sh
```
This will iniatialize the virtual environment. Once you have created it, to activate from a new terminal, navigate to `SBC-Analysis/` and run:
```
source LAr10Ana/setup.sh
```

# Running jupyter notebooks

To run a jupyter notebook, you'll want to start a server from your terminal and then open it in a browser. First, login to the Fermilab server and forward port `8888`:
```
ssh -KYX <username>@couppsbcgpvm01.fnal.gov -L 8888:localhost:8888
```
If you see an error in the login that port 8888 is taken, then try again with a different port (8889, for example). Then navigate to your python virtual environment and activate it. Then, run:
```
jupyter notebook --no-browser --port <port>
```
Where `<port>` is the port you selected in the ssh. A link will print in the terminal. Open it in the browser to access the jupyter notebook. For some example notebooks for 
accessing SBC-LAr10 data, navigate to `UserCode/gputnam/nb/`

# Running Grid Jobs
TODO
