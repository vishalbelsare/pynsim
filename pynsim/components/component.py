#    (c) Copyright 2014, University of Manchester
#
#    This file is part of PyNSim.
#
#    PyNSim is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    PyNSim is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with PyNSim.  If not, see <http://www.gnu.org/licenses/>.

import logging
import os
import time
import pickle
from copy import deepcopy, copy
import sys
import datetime
from pynsim.history import Map
import json
import jsonpickle

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s:%(name)s:%(lineno)s:%(message)s"
)
logger = logging.getLogger(__name__)

from .component_status import ComponentStatus


class Component(object):
    """
        A top level object, from which Networks, Nodes, Links and Institions
        derive. This object is what a model performs its calculations on.
    """
    name = None
    description = None
    base_type = 'component'

    # This dict contains both the current scenarios properties names and the status properties names
    _properties = dict()
    _history = dict()
    #To avoid exporting the history of every property, property names can
    #be specified here to explictly define which properties are results
    #(and are therefore to be exported).
    _result_properties = []

    # List of fields that will be managed through the scenario manager. They are set at class level. THese are the parameter set for providing the full scenarios
    _scenarios_parameters = dict()

    # List of fields that does not vary through the simulation
    _invariant_parameters = dict()

    # This dictionary contains the fields that represents the internal status.
    # These fields will be managed by the component status object
    # _internal_status_fields = dict()

    #def __init__(self, name, simulator=None, **kwargs):
    def __init__(self, name, **kwargs):
        logger.info(f"Component class {self.__class__.__name__}")
        logger.info(f"Name class {name.__class__.__name__}")

        # Reference to the simulator
        self._simulator = None
        for k, v in kwargs.items():
            logger.warning("k: %s, v: %s", k, v)
            input("Wait")
        input("ok")
        logger.info(f"Simulator class {simulator.__class__.__name__}")

        self.bind_simulator(simulator) # To properly bind the simulator!

        self.component_type = self.__class__.__name__
        if name is None:
            raise Exception("The 'name' of a pynsim component is mandatory and unique inside the same components set!")

        self.name = name
        self._history = dict()

        self._status = ComponentStatus(component_ref = self, properties = deepcopy(self._properties))

        for k, v in self._properties.items():
            logger.warning("k: %s, v: %s", k, v)

            setattr(self, k, deepcopy(v))
            self._history[k] = []

        for k, v in kwargs.items():
            logger.warning("k: %s, v: %s", k, v)
            input("Wait")

            if k == "_scenarios_parameters":
                setattr(self, k, v)
            elif k in self._properties:
                setattr(self, k, v)
            else:
                raise Exception("Invalid property %s. Allowed properties are: %s" % (k, self._properties.keys()))

            # This sets the current status for the property
            # if k in self._internal_status_fields:
            #     self._status.set_property_start_value(k, v)


    def __setattr__(self, name, value):
        logger.info("set attr {}: {}".format(name, value))
        if name is not "_simulator" and self._simulator is None:
            raise Exception("The current Component does not have any simulator assigned!")

        if name == "_scenarios_parameters":
            logger.info("Setting _scenarios_parameters")
            # time.sleep(5)
            pass
            ##self.__class__.__name__
        else:
            if name in self._properties:
                logger.warning("This is a property: %s", name)

                """
                    If the property is valid for status
                """
                #if name in self._internal_status_fields:
                logger.warning("object %s, name: %s, val: %s", self.name, name, value)
                self._status.set_property_value(name, value)

            elif name in self._scenarios_parameters:
                logger.warning("This is a scenario parameter: %s", name)
                self._simulator.get_scenario_manager().add_scenario(
                    object_type=self.__class__.__name__,
                    object_name = self.name,
                    object_reference = self,
                    property_name=name,
                    property_data=value
                )
                #time.sleep(1)
            else:
                logger.error("This is a NOT property: %s", name)

        super().__setattr__(name, value) # This allows to propagate the __setattr__ to the object itself
        # self._attributes[name] = value


    def replace_internal_value(self, name, value):
        """
            This is called explicitly to replace the values without passing from __setattr__
        """
        super().__setattr__(name, value) # This allows to propagate the __setattr__ to the object itself


    def get_status(self):
        return self._status

    def set_current_scenario_index_tuple(self, current_multiscenario_index_tuple):
        self._status.set_current_scenario_index_tuple(current_multiscenario_index_tuple)

    def set_current_timestep(self, timestep):
        self._status.set_current_timestep(timestep)

    def add_scenario(self, name, value):
        logger.error("self.__class__.__name__ %s", self.__class__.__name__)
        logger.error("self.__name__ %s", self.name)
        #time.sleep(2)

    def get_class_name(self):
        return self.__class__.__name__

    def get_object_name(self):
        return self.name

    def bind_simulator(self, simulator=None):
        """
            Command to set the simulator reference
        """
        if self._simulator is None:
            if simulator is not None:
                self._simulator = simulator
                simulator.register_component(self) # Registering the component into the simulator
            else:
                raise Exception("The simulator reference cannot be None")

    def get_simulator(self):
        return self._simulator

    def get_history(self, attr_name=None):
        """
            Return a dictionary, keyed on timestep, with each value of the
            attribute at that timestep.
        """
        if attr_name is None:
            return self._history
        else:
            return self._history.get(attr_name, None)

    def reset_history(self):
        """
            Reset the _history dict. This is useful if a simulator instance is
            used for multiple simulations.
        """
        for k in self._properties:
            self._history[k] = []

    def get_properties(self):
        """
            Get all the properties for this component (as defined in
            _properties)
        """
        properties = dict()
        for k in self._properties:
            properties[k] = getattr(self, k)
        return properties

    def post_process(self):
        for k in self._properties:
            attr = getattr(self, k)
            if isinstance(attr, dict) or isinstance(attr, list):
                self._history[k].append(deepcopy(attr))
            else:
                self._history[k].append(attr)

    def __repr__(self):
        return "Component(name=%s)" % (self.name)

    def setup(self, timestamp):
        """
            Setup function to be overwritten in each component implementation
        """
        pass


    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

    def validate_history(self):
        """
            Check whether this comonent's history can be exported
        """
        try:
            json.dumps(self._history)
        except TypeError:
            logging.warn("History of %s %s is not JSON compatible. Trying to pickle...", self.base_type, self.name)
            pickle.dumps(self._history)
        except TypeError:
            logging.critical("History of %s %s cannot be exported. Skipping.", self.base_type, self.name)
            return False

        return True



    def get_current_property_value(self, property_name):
        if property_name not in self._properties:
            raise Exception("The property '%s' is not valid!", property_name)

        return self._status.get_property_current_value(property_name)
