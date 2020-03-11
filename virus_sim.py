import random
import pandas as pd


class Person(object):
    """
    A person has a position, an age, information about whether they are infected or
    dead, and how long they have spent infected.
    """
    __slots__ = ['x', 'x_max', 'y', 'y_max', 'infected', 'infected_time', 'age', 'dead']

    def __init__(self, x, x_max, y, y_max, age, infected=False):
        self.x = x
        self.x_max = x_max
        self.y = y
        self.y_max = y_max
        self.age = age
        self.infected = infected
        self.infected_time = 0
        self.dead = False

    def run(self):
        """
        Ages the person by a day, based on their current infection status.

        :return: False, if the person is dead, else True
        """
        if self.dead:
            return False

        if self.infected:
            self.infected_time += 1

            if self.recovered_profile():
                self.infected = False
            elif self.death_profile():
                self.dead = True
                return False

        new_x = self.x + self.activity_profile()
        new_x = max(new_x, 0)
        new_x = min(new_x, self.x_max)
        self.x = new_x

        new_y = self.y + self.activity_profile()
        new_y = max(new_y, 0)
        new_y = min(new_y, self.y_max)
        self.y = new_y

        return True

    def recovered_profile(self):
        """
        Simulates whether the person recovers on a given iteration (day) according to
        probabilities based on infection time and age.
        """
        # TODO: probabilistic death/cure rate by time and activity level
        # TODO: check math for cumulative probabilities to equal real death rates
        #  assuming one check per day (infected time measured in days)
        if self.infected_time < 10:
            return False

        elif self.infected_time < 18:
            if self.age < 50:
                if random.random() < 0.5:
                    return True
            else:
                if random.random() < 0.3:
                    return True
            return False

        else:
            if random.random() < 0.3:
                return True
            return False

    def death_profile(self):
        """
        Simulates whether the person dies on a given iteration (day) according to
        probabilities based on infection time and age.
        """
        if self.infected_time < 7:
            return False

        elif self.infected_time < 14:
            if self.age < 50:
                if random.random() < 0.001:
                    return True
                else:
                    return False
            elif self.age < 70:
                if random.random() < 0.006:
                    return True
                else:
                    return False
            else:
                if random.random() < 0.015:
                    return True
            return False

        else:
            if self.age < 50:
                if random.random() < 0.002:
                    return True
                else:
                    return False
            elif self.age < 70:
                if random.random() < 0.015:
                    return True
                else:
                    return False
            else:
                if random.random() < 0.03:
                    return True
            return False

    def activity_profile(self):
        """
        Activity is defined such that it captures both the probability of exposing
        others to any carried pathogens, and the probability of encountering more
        pathogens from others. These probabilities are assumed to be equivalent.
        """
        if self.age < 30:
            movement = 10
        elif self.age < 50:
            movement = 8
        elif self.age < 70:
            movement = 5
        else:
            movement = 3
        return random.randint(-movement, movement)

    def immunity_profile(self):
        """
        Probabilistic profile for a person's immunity, based on their age and previous
        infection history.
        """
        # For now, assume flat 50% exposure rate when exposed with infected,
        #  and 95% immunity rate across the board
        return 0.95

    def infection_profile(self):
        """
        Simulates whether the person is infected on a given day (iteration) if they
        were 'exposed' on this day to an infected person.
        """
        # TODO: immunity profile by age/previous infection resulting in probability of
        #  re-infection

        exposure_rate = 0.05 * self.activity_profile()
        immunity_rate = self.immunity_profile()

        if not self.infected_time:
            return random.random() < exposure_rate
        else:
            return random.random() < (1 - immunity_rate) * exposure_rate


class World(object):
    def __init__(self, num_people, num_initial_infected, contagious,
                 max_x=200, max_y=200, contagious_delay=1):
        self.max_x = max_x
        self.max_y = max_y
        self.contagious = contagious
        self.contagious_delay = contagious_delay

        self.current_people = num_people
        self.current_infected = 0
        self.current_recovered = 0
        self.current_dead = 0

        self.people = []
        self.grid = {}

        assert num_people > num_initial_infected

        for i in range(num_people):
            # TODO: create a more realistic world grid that is larger and contains
            #  clusters of activity (cities)
            self.add_person(random.randint(0, self.max_x),
                            random.randint(0, self.max_y),
                            self.current_infected < num_initial_infected,
                            random.randint(1, 85))

    def add_person(self, x, y, infected, age):
        """
        Adds a person to the World grid.
        :param x: starting x coordinate
        :param y: starting y coordinate
        :param infected: whether the person is infected (boolean)
        :param age: the person's age
        :return:
        """
        person = Person(x, self.max_x, y, self.max_y, age, infected)
        if x in self.grid:
            if y in self.grid[x]:
                self.grid[x][y].append(person)
            else:
                self.grid[x][y] = [person]
        else:
            self.grid[x] = {y: [person]}
        self.people.append(person)
        self.current_infected += 1 if infected else 0

    def update(self):
        """
        Updates the world-grid for the next day. People move according to their
        activity profile, are infected by others according to their infection profile,
        and recover or die according to the respective probability profiles for their
        age and immunity status.
        """
        for person in self.people:
            if person.dead:
                continue
            last_infected = person.infected
            last_x = person.x
            last_y = person.y
            alive = person.run()
            if not alive:
                self.current_dead += 1
                self.current_people -= 1
                self.current_infected -= 1
                continue
            if last_infected and not person.infected:
                self.current_recovered += 1
                self.current_infected -= 1

            # Assume delay between infection and spreading to others
            if person.infected and person.infected_time > self.contagious_delay:
                for x in range(max(0, last_x - self.contagious),
                               min(self.max_x, last_x + self.contagious)):
                    if not x in self.grid:
                        continue
                    for y in range(max(0, last_y - self.contagious),
                                   min(self.max_y, last_y + self.contagious)):
                        if not y in self.grid[x]:
                            continue
                        for other_person in self.grid[x][y]:
                            if (not other_person.infected and
                                    other_person.infection_profile()):
                                other_person.infected = True
                                self.current_infected += 1
                                if other_person.infected_time:
                                    self.current_recovered -= 1

        # Easier to just rebuild the grid each day.
        self.grid = {}
        for person in self.people:
            if person.x in self.grid:
                if person.y in self.grid[person.x]:
                    self.grid[person.x][person.y].append(person)
                else:
                    self.grid[person.x][person.y] = [person]
            else:
                self.grid[person.x] = {person.y: [person]}

    def run_simulation(self, iterations=1000):
        """
        Runs a simulation of the spread of the contagion in the world grid.

        :param iterations: the number of iterations (days) to run the simulation
        :return: df: a dataframe with data from each iteration of the simulation
        """
        i = 0
        index = []
        data = []
        index.append(i)
        data.append([self.current_people, self.current_infected,
                     self.current_recovered, self.current_dead])
        while i < iterations and self.current_people > 0 and self.current_infected > 0:
            self.update()
            i += 1
            index.append(i)
            data.append([self.current_people, self.current_infected,
                         self.current_recovered, self.current_dead])

        field_names = ["Population", "Infected", "Recovered", "Dead"]
        columns = pd.Index(field_names, dtype="object")
        dtype = "object"
        df = pd.DataFrame(data, index, columns, dtype, True)
        return df

