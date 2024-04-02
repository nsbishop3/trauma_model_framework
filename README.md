# Trauma Model Framework

This version of the repo is designed for the double-blind review of the paper "INCORPORATING TRAUMA PROPAGATION AND TRANSMISSION IN AGENT BASED MODELS: A PRELIMINARY FRAMEWORK" for the ANNSIM 2024 conference.

This framework requires the use of Anaconda (https://www.anaconda.com/download)

This framework runs on:
- Conda 23.7.3
- Python 3.9.17
- mesa 2.1.1
  
All other packages are found in the base environment of Anaconda.

This framework was designed and tested using the Spyder IDE, version 5.15.7 on Windows 10.

# Run with visualization
To run this framework with visualization in the browser:
1. Open an anaconda prompt
2. Navigate to the directory that contains run.py
3. Type the command "mesa runserver"

This command will open your default internet browser to show a visualization of the simulated agents on the Sugarscape canvas. This is the same Sugarscape canvas as seen in the Sugarscape Constant Growth Model in the official MESA examples repo (https://github.com/projectmesa/mesa-examples/tree/main/examples/sugarscape_cg). The middle graphic on the webpage visualization shows the population of agents over time and the bottom graphic shows the average trauma level of the agents over time.

# Run without visualization
Running the framework (or any ABM) without visualization is faster and opens the door to parallelization of runs. This framework does not have any example code for running an ABM in parallel, but more information on that can be found here: https://mesa.readthedocs.io/en/stable/tutorials/intro_tutorial.html. This framework is designed for researchers with little knowledge of Python and no knowledge of designing an ABM, so the code is designed for single-thread usage that can easily be debugged.

To run the model framework without visualization, simply open run_and_analyze.py in a Python IDE and run the script.
