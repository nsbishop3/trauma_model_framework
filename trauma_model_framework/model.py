"""
Sugarscape Constant Growback model adjusted for a trauma model framework
================================

"""

import mesa
import numpy as np
# import random

from .agents import SsAgent, Sugar


class SugarscapeTMF(mesa.Model):
    """
    Sugarscape 2 Constant Growback
    """

    @staticmethod
    def reporter_trauma(m):
        '''
        Creating the average trauma reporter had a bit of complexity, so instead of
        making it all on one line, it was made into its own function.
        
        Calculates the average trauma of all the non-sugar agents in the simulation
        at each time step.

        Parameters
        ----------
        m : model object (this is handled by MESA automatically)
            MESA passes the model object as the arg to this function by default
            because this function is registered as a reporter calculation function.

        Returns
        -------
        avg_trauma : float
            average trauma of all non-sugar agents

        '''
        # this obtains counts of all non-sugar agents
        # if all non-sugar agents die out, then it will cause
        # an error without testing for it
        ag_count = m.schedule.get_type_count(SsAgent)
        
        # testing if there is a population of non-sugar agents
        if ag_count > 0:
            # loop over and sum all trauma levels
            traumas = sum([ag.trauma for ag in m.schedule.agents_by_type[SsAgent].values()])
            # divide by number of agents to get the average
            avg_trauma = traumas/m.schedule.get_type_count(SsAgent)
        else:
            avg_trauma = 0
        
        return avg_trauma

    def __init__(self, width=50, height=50, initial_population=100, seed=None):
        """
        Create a new Collective Trauma model based on Constant Growback model with the given parameters.

        Args:
            initial_population: Number of population to start with
            seed: Random seed value for MESA to use
        """
        
        self.verbose = False # Print-monitoring
        
        self.trauma_recovery = False
        self.te_end = self.te_start = -1

        # Set parameters
        self.end = False
        self.width = width
        self.height = height
        self.initial_population = initial_population

        self.schedule = mesa.time.RandomActivationByType(self)
        self.grid = mesa.space.MultiGrid(self.width, self.height, torus=False)
        self.datacollector = mesa.DataCollector(
            model_reporters={"SsAgent": lambda m: m.schedule.get_type_count(SsAgent),
                             "Trauma": self.reporter_trauma,
            },
            agent_reporters = {"test": lambda agent: agent.sugar if isinstance(agent, SsAgent) else None}
        )

        # Create sugar
        sugar_distribution = np.genfromtxt("trauma_model_framework/sugar-map.txt")
        self.agent_id = 0
        for _, (x, y) in self.grid.coord_iter():
            max_sugar = sugar_distribution[x, y]
            sugar = Sugar(self.agent_id, (x, y), self, max_sugar)
            self.agent_id += 1
            self.grid.place_agent(sugar, (x, y))
            self.schedule.add(sugar)

        # Create agent:
        for i in range(self.initial_population):
            ssa = SsAgent(self.agent_id, self, False, family=i)
            x,y = ssa.pos
            self.agent_id += 1
            self.grid.place_agent(ssa, (x, y))
            self.schedule.add(ssa)

        # logistics vars
        self.running = True
        self.datacollector.collect(self)
        

    def step(self):
        self.schedule.step()
        # collect data
        self.datacollector.collect(self)
        if self.verbose:
            print([self.schedule.time, self.schedule.get_type_count(SsAgent)])
        
        # calculations used for marking milestones
        avg_trauma = self.datacollector.model_vars['Trauma'][-1]
        
        # instances of each type of agent for easy type checking
        sugar_agent = self.schedule.agents[0]
        reg_agent = self.schedule.agents[-1]
        
        sn = self.schedule.steps
        
        # check for famine start marker and record or print 
        # in addition to resetting family identifiers for easy tracking of 
        # agent descendents in famine
        if sugar_agent.famine == sugar_agent.step_num:
            if self.verbose:
                print('Famine start:',sn,round(sugar_agent.avg_baseline_trauma,3))
            # set famine start marker
            self.te_start = sn
            # reset all family IDs
            for uid,ssag in self.schedule.agents_by_type[SsAgent].items():
                ssag.reset_family()
        # check if famine has stopped
        elif sn == self.te_start+100:
            if self.verbose:
                print('Famine end:',sn,round(avg_trauma,3))
            # record famine stop marker
            self.te_end = sn
        # check if trauma levels drop to below pre-trauma event level
        elif avg_trauma < sugar_agent.avg_baseline_trauma and (not self.trauma_recovery) and sn > self.te_end:
            if self.verbose:
                print('Trauma recovery:',sn,round(avg_trauma,3))
            self.trauma_recovery = True
            # record marker
            self.t_recovery = sn
        # check if it is time to end simulation;
        # this model framework uses a very simple method of determining end time
        # but it might be worth trying methods of steady state detection
        # of trauma levels after the trauma event to decide an end time 
        # for the simulation
        if sn >= self.te_end + 800:
            # turn on "end" flag to stop simulation
            self.end = True
            

    def run_model(self, step_count=2000):
        # sim mile markers (useful for debugging or plotting important sim events)
        self.te_start = step_count # traumatic event start
        self.te_end = step_count # traumatic event end
        self.t_recovery = step_count # trauma response full recovery
        
        if self.verbose:
            print(
                "Initial number Sugarscape Agent: ",
                self.schedule.get_type_count(SsAgent),
            )
        
        # run simulation at each stop
        for i in range(step_count):
            self.step()
            if self.end:
                break

        if self.verbose:
            print("")
            print(
                "Final number Sugarscape Agent: ",
                self.schedule.get_type_count(SsAgent),
            )
