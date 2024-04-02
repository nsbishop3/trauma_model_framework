import math
import numpy as np
# import random

import mesa
# import copy


def get_distance(pos_1, pos_2):
    """Get the distance between two point

    Args:
        pos_1, pos_2: Coordinate tuples for both points.
    """
    x1, y1 = pos_1
    x2, y2 = pos_2
    dx = x1 - x2
    dy = y1 - y2
    return math.sqrt(dx**2 + dy**2)


class SsAgent(mesa.Agent):
    def __init__(
        self, unique_id, model, moore=False, sugar=0, trauma=0, trauma_min=0, cortisol=0.05,
        generation=-1, family=-1, sex=None, epigenetic_symptoms=[],
    ):
        super().__init__(unique_id, model)
        
        self.moore = moore
        x = self.random.randrange(self.model.width)
        y = self.random.randrange(self.model.height)
        self.pos = (x,y)
        if sugar == -1:
            sugar = self.random.randrange(6, 25)
        self.sugar = sugar
        self.max_sugar_hold = self.random.randint(20,60)

        metabolism = self.random.randrange(2, 4)
        self.metabolism = metabolism
        vision = self.random.randrange(1, 6)
        self.vision = vision
        
        self.age = 0
        self.starvation = 0
        if sex is None:
            self.sex = self.random.choice(['m','f'])
        else:
            self.sex = sex
        self.next_birth_sex = None
        self.generation = generation + 1
        # if no family is specified, start a new family line identifier
        if family is None:
            self.family = unique_id
        else:
            self.family = family
        self.death = self.random.randint(90,110)
        self.starvaton = 0
        
        # epigenetic_symptoms shoud be a
        # list of lists like [trigger_dict, [function,arg1,arg2,...]] with triggers and triggered function
        try:
            if len(epigenetic_symptoms) > 0:
                self.epigenetic_symptoms = [xx for xx in epigenetic_symptoms if xx[0]['generation'] >= generation]
            else:
                self.epigenetic_symptoms = epigenetic_symptoms
        except:
            raise Exception('All epigenetic symptoms must have a generation designation')
        # self.epigenetic_symptoms_init = copy.deepcopy(self.epigenetic_symptoms)
        
        # set born trauma level as half of their parent
        self.trauma = trauma * 0.5
        self.trauma_min = trauma_min
        self.trauma_capacity = 1
        self.trauma_lifemax = 0
        self.cortisol = cortisol
        
        # reproduction
        self.pregnant = False
        self.pregnancy_time = 5
        self.pregnancy_countdown = self.pregnancy_time
        self.puberty_age = 20
        
        # trauma symptoms - unused in model framework
        # these are here as examples
        self.obesity = 0
        self.cardio_disease = 0
        
        # epigenetic
        self.future_epigenetic_symptoms = dict()
        self.epigenetic_lifespan_decrease_prenatal = 0
        self.epigenetic_lifespan_increase_prepubecent = 0
        
    
    def reset_family(self):
        '''
        This function allows for resetting family identifiers mid-simulation.
        This is useful in an example where a researcher wishes to track individual
        family progress starting at the beginning of a traumatic event.

        Returns
        -------
        None. Object attributes are changed.

        '''
        self.family = self.unique_id
    
    def is_cannibalized(self):
        '''
        This function is called by an external agent trying to cannibalize
        this agent. It removes this agent from the simulation (this agent killed)
        and returns the sugar of this agent + a constant (energy from eating this agent)
        so the external agent can add that value to its sugar.

        Returns
        -------
        self.sugar + c : Integer
            This agent's sugar + a constant (energy of consuming this agent)

        '''
        self.model.grid.remove_agent(self)
        self.model.schedule.remove(self)
        return self.sugar + 5
    
    def is_killed(self):
        '''
        This function is called by an external agent trying to kill this
        agent to steal its sugar.

        Returns
        -------
        self.sugar : Integer
            The amount of sugar this agent is holding at the time of being killed

        '''
        self.model.grid.remove_agent(self)
        self.model.schedule.remove(self)
        return self.sugar
    
    def is_mugged(self):
        '''
        This function is called by an external agent trying to
        steal sugar from this agent. This agent is not killed by
        being mugged. In this model, this agent being mugged does 
        not become more traumatized by the incident, although the 
        option exists in the code of this function where "self.trauma += 0.0"
        
        The sugar and trauma level after being mugged are not returned,
        but are edited in this function.
        
        Returns
        -------
        sugar_give : Integar
            The amount of sugar being stolen from this agent by the external agent

        '''
        sugar_give = int(self.sugar * 1.0)
        self.sugar = int(self.sugar * 0.0)
        self.trauma += 0.0
        return sugar_give
    
    def get_sugar(self, pos):
        '''
        Used by this agent to gather sugar from a sugar tile on the 
        Sugarscape canvas landscape

        Parameters
        ----------
        pos : (int,int)
            attribute of this agent that is changed by the "move" function

        Returns
        -------
        agent : object
            returns the sugar tile (which is instantiated as a stationary agent by MESA)

        '''
        this_cell = self.model.grid.get_cell_list_contents([pos])
        for agent in this_cell:
            if type(agent) is Sugar:
                return agent

    def is_occupied(self, pos):
        '''
        Tests if another non-sugar agent is at a particular pos on the canvas

        Parameters
        ----------
        pos : (int,int)
            pos on the canvas

        Returns
        -------
        agent or None : object or None
            returns a non-sugar agent object instance if there is any;
            if not, it will return None

        '''
        this_cell = self.model.grid.get_cell_list_contents([pos])
        return any(isinstance(agent, SsAgent) for agent in this_cell)

    def move(self):
        '''
        This function handles moving the agent on the canvas to look for food.
        
        There is an if-statement that allows for trauma influenced behavior to 
        be expressed by the agent. In this model, if the agent is starving, there
        is no other viable food options within their vision on the canvas, and a 
        random number draw is less than the current trauma level, the agent will 
        attempt to engage in trauma influence behavior. This includes mugging,
        killing, and cannibalizing other agents depending on this agent's current
        starvation and trauma levels.

        Returns
        -------
        None.

        '''
        # Get neighborhood within vision
        neighborhood = self.model.grid.get_neighborhood(
            self.pos, self.moore, False, radius=self.vision
        )
        # get all non-sugar agents within agent vision
        agent_neighbors = [i for i in neighborhood if self.is_occupied(i)]
        
        # get all sugar agents within agent vision (sugar tiles)
        neighbors = [
            i
            for i in neighborhood
            if not self.is_occupied(i)
        ]
        
        neighbors.append(self.pos)
        # Look for location with the most sugar
        max_sugar = max(self.get_sugar(pos).amount for pos in neighbors)
        
        # enable trauma influenced behavior
        trauma_influenced_behavior = True
        
        # if - 1. other non-sugar agents within vision
        # 2. random.random() < trauma level
        # 3. agent is starving
        # 4. the max sugar on the visible canvas < this agent's metabolism
        # then engage in possible trauma influenced behaviors
        if len(agent_neighbors) > 0 and self.random.random() < self.trauma and self.starvation > -1 \
            and max_sugar < self.metabolism and trauma_influenced_behavior:
            
            # pick random non-sugar agent and move to them
            self.random.shuffle(agent_neighbors)
            pos = agent_neighbors[0]
            
            this_cell = self.model.grid.get_cell_list_contents(pos)
            for agent in this_cell:
                if isinstance(agent,SsAgent):
                    break

            
            # trauma influenced behavior #
            # the starvation level and trauma level affects what the agent is 
            # capable of doing to other agents
            if self.starvation > 15 and self.random.random() < self.trauma * .1:
                self.sugar += agent.is_cannibalized()
                # this agent becomes more traumatized by cannibalizing another
                self.trauma += .05
            elif self.starvation > 5 and self.random.random() < self.trauma * .5:
                self.sugar += agent.is_killed()
            elif self.starvation <= 5 and self.random.random() < self.trauma * 1.0:
                self.sugar += agent.is_mugged()
            
            self.model.grid.move_agent(self,pos)
        # else if there is no sugar on the visible canvas and no non-sugar agents,
        # just move somewhere random within vision
        elif max_sugar == 0:
            self.random.shuffle(neighbors)
            self.model.grid.move_agent(self, neighbors[0])
        
        # else, move to cell with the most sugar that is nearest to consume it
        # when the "eat" function is called
        else:
        
            # Look for location with the most sugar
            candidates = [
                pos for pos in neighbors if self.get_sugar(pos).amount == max_sugar
            ]
            # Narrow down to the nearest ones
            min_dist = min(get_distance(self.pos, pos) for pos in candidates)
            final_candidates = [
                pos for pos in candidates if get_distance(self.pos, pos) == min_dist
            ]
            
            self.random.shuffle(final_candidates)
            self.model.grid.move_agent(self, final_candidates[0])

    def eat(self):
        '''
        This function handles logistics for tracking starvation of this agent,
        making sure the sugar an agent holds does not exceed the max allowed amount,
        processes the metabolism of sugar by the agent, and consumption of sugar 
        of a cell on the canvas by this agent.
        
        While an agent's sugar < an agent's metabolism, the agent's starvation
        increments by one. If the agent obtains enough sugar to stop starvation 
        for one step, then the starvation level is set to zero.

        Returns
        -------
        None.

        '''
        step_metabolism = self.metabolism #min(4,self.metabolism + self.random.randint(-1,1))
        
        # if self.sugar < step_metabolism:
        #     self.starvation += 1
        # else:
        #     self.starvation = 0
        
        if self.sugar < self.max_sugar_hold:
            sugar_patch = self.get_sugar(self.pos)
            self.sugar = max(0,self.sugar - self.metabolism + sugar_patch.amount)
            # if sugar_patch.amount + self.sugar >= step_metabolism:
            #     self.sugar = max(0,self.sugar - step_metabolism + sugar_patch.amount)
            #     self.starvation = 0
            # else:
            #     self.sugar += sugar_patch.amount
            sugar_patch.amount = 0
        else:
            self.sugar = self.sugar - step_metabolism
        
        if self.sugar == 0:
            self.starvation += 1
        else:
            self.starvation = 0
    
    def reproduce(self):
        '''
        This function handles how agents asexually reproduce. To allow for sexual reproduction,
        one could use code from the "move" function that can identify other agents
        within this agent's vision.
        
        This agent will have some probability of reproducing that is a function
        of the amount of sugar it holds as a percentage of its max allowed sugar limit.
        The agent must also have an age that is greater than the pre-defined puberty 
        age in order to reproduce. 
        
        When reproduction is triggered on an agent, it will become pregnant for the 
        number of steps defined by self.pregnant_time. Pregnancy and puberty is 
        implemented in this model to allow for modeling the effects of prenatal 
        and prepubescent trauma on individuals.
        
        This function also handles the logistics of counting down the time for pregnancy
        of an agent and handling what happens when pregnancy ends and a new agent
        is "birthed"

        Returns
        -------
        None.

        '''
        # probability of reproducing (asexual)
        pr = 0.005 + 0.015 * self.sugar/self.max_sugar_hold
        if self.sugar == self.max_sugar_hold:
            pr = pr + 0.01
        
        # if 1. random.random() < probability of reproduction
        # 2. agent age > puberty age
        # 3. agent is currently no pregnant
        # then make agent pregnant
        if self.random.random() < pr and self.age > self.puberty_age and self.pregnant == False:
            self.pregnant = True
        
        # give birth
        if self.pregnancy_countdown == 0:
            
            # get all epigenetic symptoms that have been calculated during
            # this agent's lifetme
            eg_for_birth = self.epigenetic_symptoms + self.get_epigenetics_for_birth()
            # reset pregnancy countdown
            self.pregnancy_countdown = self.pregnancy_time
            self.pregnant = False
            
            # reduce cortisol levels of the offspring of parents that have been
            # extremely traumatized. Often seen in literature about epigenetics
            # and families of Holocaust survivors.
            if self.trauma_lifemax >= 0.5:
                # cortisol_offspring = self.cortisol/2
                cortisol_offspring = self.cortisol * (1-self.trauma_lifemax)
            # if no extreme trauma experienced by an agent, then increase the 
            # cortisol level slightly for offspring
            else:
                cortisol_offspring = min(self.cortisol+0.01,0.1)
            
            # min possible trauma of offspring is equal to half of the 
            # max trauma experienced by this agent over the course of it's life.
            tm_offspring = self.trauma_lifemax/2
            
            # birth new agent #
            # give child agent half of this agent's sugar
            self.sugar = int(self.sugar*.5)
            
            # enable epigenetic effects
            epigenetic_effects = True
            
            if epigenetic_effects:
                ssa = SsAgent(self.model.agent_id, self.model, False, 
                               sugar = int(self.sugar*.5), trauma = self.trauma,
                                trauma_min = tm_offspring, cortisol = cortisol_offspring,
                              generation = self.generation, family = self.family,
                              sex = self.next_birth_sex,
                                epigenetic_symptoms = eg_for_birth
                              )
                self.next_birth_sex = None
            else:
                ssa = SsAgent(self.model.agent_id, self.model, False, 
                               sugar = int(self.sugar*.5), trauma = self.trauma,
                              generation = self.generation, family = self.family,
                              )
            self.model.agent_id += 1
            self.model.grid.place_agent(ssa, (self.pos[0], self.pos[1]))
            self.model.schedule.add(ssa)
        # continue tracking pregnancy timeline
        if self.pregnant:
            self.pregnancy_countdown -= 1
            
    def traumatize(self):
        '''
        This function handles the logistics of increasing this agent's trauma level
        due to starvation, applying that starvation in a prenatal/prepubescent context
        where applicable, and decay of trauma from this agent's cortisol level.

        Returns
        -------
        None.

        '''
        # if agent is starving, add trauma
        if self.starvation > 0:
            self.trauma = max(self.trauma + 0.05, 1)
            # pre-pubecent traumas have transgenerational epigenetic effects
            if self.age <= self.puberty_age:
                self.prepubecent_trauma_create(.01)
            # pre-natal traumas have transgenerational epigenetic effects
            if self.pregnant:
                self.prenatal_trauma_create(.04)
        # trauma decay when not starving
        else:
            self.trauma *= 1 - self.cortisol
        
        self.trauma = max(min(self.trauma, 1),self.trauma_min)
        
        if self.trauma > self.trauma_lifemax:
            self.trauma_lifemax = self.trauma
    
    def trigger_genes(self):
        '''
        This function is used each step to check if an inherited epigenetic
        symptom should be expressed and how it will be expressed. It uses the trigger dictionary
        and runs the specified trigger function to simulate any desired effects. To see an example of 
        creating a transgenerational epigenetic effect, look at "prenatal_trauma_create"
        and "prepubescent_trauma_create" functions.

        Returns
        -------
        None.

        '''
        self_vars = vars(self)
        for epigenetic_expression in self.epigenetic_symptoms:
            triggers, expression = epigenetic_expression
            trigger_expression = 1
            
            for trigger_attr, trigger_val in triggers.items():
                trigger = 0
                if trigger_val == self_vars[trigger_attr]:
                    trigger = 1
                trigger_expression = trigger_expression and trigger
                
            if trigger_expression:
                func = getattr(self,expression[0])
                func(*expression[1:])

    
    
    def step(self):
        '''
        Run all functions affecting agent simulation and determine if 
        agent should die from starvation or old age

        Returns
        -------
        None.

        '''
        self.trigger_genes()
        self.move()
        self.eat()
        self.reproduce()
        self.traumatize()
        self.age += 1
        if self.starvation > 20 or self.age > self.death:
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
    
    # sub functions #
    def get_epigenetics_for_birth(self):
        '''
        Gather all running calculations gathered in the dictionary "self.future_epigenetic_symptoms"
        and append to epigenetic symptoms for this agent's offspring to inherit.
        
        This function is used instead of just appending directly to self.epigenetic_symptoms
        to allow for trauma creation functions to be called multiple times to change specific
        values of a dictionary. If these functions appended to a list every time, then
        it would be more difficult to track exactly what the offspring is inheriting 
        as epigenetic symptoms and verify the intended effects.

        Returns
        -------
        eg_symptoms : list of [trigger dictionary, (function, *args)]
            list of running calculation epigenetic symptoms that change over the
            course of this agent's life

        '''
        eg_symptoms = []
        for key,future_symptoms in self.future_epigenetic_symptoms.items():
            eg_symptoms.append(future_symptoms)
        
        return eg_symptoms
    
    def prenatal_trauma_create(self,eld):
        '''
        Example of prenatal trauma creating transgenerational epigenetic effects
        
        According to the literature, life expectancy decreases
        if the offspring are the same sex 2 generations later, so that is included
        in the trigger criteria dictionary.
        
        The trigger age is 0 so that this effect is present starting at birth

        Parameters
        ----------
        eld (expected life decrease): float (0-1)
            Percentage of the decreased lifespan of the descendant of this agent 
            in 2 generations. 

        Returns
        -------
        None.

        '''
        self.epigenetic_lifespan_decrease_prenatal += eld
        self.epigenetic_lifespan_decrease_prenatal = min(self.epigenetic_lifespan_decrease_prenatal,0.2)
        # trigger is (gen + 3) b/c it is 2 generations after the agent currently about to be birthed (prenatal)
        # also 'sex' of the next child is chosen now, since the epigenetic effects are based on that
        self.next_birth_sex = self.random.choice(['m','f'])
        triggers = {'generation':self.generation+3,'age':0,'sex':self.next_birth_sex}
        expression = ['prenatal_trauma_express',self.epigenetic_lifespan_decrease_prenatal]
        self.future_epigenetic_symptoms['prenatal1'] = [triggers,expression]
        
        return None
    
    def prepubecent_trauma_create(self,eli):
        '''
        Example of prepubescent trauma creating transgenerational epigenetic effects
        
        The trigger age is 0 so that this effect is present starting at birth

        Parameters
        ----------
        eld (expected life increase): float (0-1)
            Percentage of the increased lifespan of the descendant of this agent 
            in 2 generations. This effect is shown in the literature.

        Returns
        -------
        None.

        '''
        self.epigenetic_lifespan_increase_prepubecent += eli
        self.epigenetic_lifespan_increase_prepubecent = min(self.epigenetic_lifespan_increase_prepubecent,0.2)
        triggers = {'generation':self.generation+2,'age':0}
        expression = ['prepubescent_trauma_express',self.epigenetic_lifespan_increase_prepubecent]
        self.future_epigenetic_symptoms['prepubecent1'] = [triggers,expression]
        
        return None
    
    def prenatal_trauma_express(self,dec_perc):
        '''
        Expression of the transgenerational epigentic effects of prenatal trauma.
        
        For every epigenetic symptom, there needs to be a function used to express 
        that effect. This is an example of proper implementation.

        Parameters
        ----------
        dec_perc : float (0-1)
            Percentage that the lifespan of this agent will be decreased by
            (affects only death by old age value)

        Returns
        -------
        None.

        '''
        
        self.death *= 1 - dec_perc
        
        return None
    
    def prepubescent_trauma_express(self,inc_perc):
        '''
        Expression of the transgenerational epigentic effects of prepubescent trauma.
        
        For every epigenetic symptom, there needs to be a function used to express 
        that effect. This is an example of proper implementation.

        Parameters
        ----------
        inc_perc : float (0-1)
            Percentage that the lifespan of this agent will be increased by
            (affects only death by old age value)

        Returns
        -------
        None.

        '''
        
        self.death *= 1 + inc_perc
        
        return None

class Sugar(mesa.Agent):
    def __init__(self, unique_id, pos, model, max_sugar):
        super().__init__(unique_id, model)
        self.amount = max_sugar
        self.max_sugar = max_sugar
        # self.step_num = 0
        self.famine = -1e6
        # conway rule counter
        self.con_counter = 0
        self.avg_baseline_trauma = 0
        self.avg_trauma = -1
        self.end_sim = False # flag for parent model object to end simulation
                            # it isn't used in this framework, but it would allow
                            # triggering an end to the sim at the agent level

    def step(self):
        # step for sugar cell/tile/agent #
        
        self.step_num = self.model.schedule.steps
        
        
        # other example models of simulating famine
        # growth = 3**(-self.step_num/500) + 0.05
        # cyclic_growth = 0.45 * np.cos( (self.step_num) * (2*np.pi/100) ) + 0.5

        constant = 1        
        growback = constant
        
        # conway rule
        steady_state = False
        # number of oldest steps truncated for the conway rule set
        nsteps = 200 
        # number of consecutive steps within the value set of the last nsteps
        # necessary for the conway rule to trigger
        num_conway_steps = 100
        # start famine
        if self.step_num > nsteps and self.step_num > 500 and self.famine < 0:
            last_nsteps = self.model.datacollector.model_vars['Trauma'][-(nsteps+1):]
            truncated_conway_steps = last_nsteps[:-1]
            last_step = last_nsteps[-1]
            if (last_step >= min(truncated_conway_steps)) and \
                (last_step <= max(truncated_conway_steps)):
                self.con_counter += 1
            else:
                self.con_counter = 0
            
            if self.con_counter > num_conway_steps:
                self.con_counter = 0
                steady_state = True
                self.famine = self.step_num
                # recording to have a variable that has the last trauma
                # value before the trauma event starts
                self.avg_baseline_trauma = np.average(last_nsteps)
        
        # For this famine model, sugar is wiped from the board
        # and the growth rate is set to 10% of the initial growth rate
        if self.step_num == self.famine:
            if self.random.random() < 0.9:
                self.amount = 0
        if self.famine <= self.step_num < self.famine+100:
            growback = 0.1 * constant

        
        if self.random.random() < growback:
            self.amount = min([self.max_sugar, self.amount + 1])
        # else:
        #     self.amount = min([self.max_sugar, self.amount])