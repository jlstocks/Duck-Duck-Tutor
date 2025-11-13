from typing import Dict, Any, Union, Optional, Tuple
from abc import ABC, abstractmethod
from resources.logger import Logger
from resources.parser import Parser

from agents.expert_agent import ExpertAgent
from agents.teacher_agent import TeacherAgent
from agents.tutor_agent import TutorAgent

class Orchestration(ABC):
    def __init__(self, llm, mode_config: Optional[Dict[str, Any]] = None, log_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the orchestrator using the chain architecture.

        Handles user-defined configurations for execution mode and local logging.

        Args
            llm: user-defined language model
            mode_config: determines mode of execution for agents
            log_config: local logging technique, optional
        """
        #declare the llm
        self.llm = llm

        #handle mode configurations
        self.mode_config = mode_config or {}

        #handle logging configurations
        self.log_config = log_config or {}
        self.logger = Logger.from_config(self.log_config.get('log_config', None))

        #initialize the parser object
        self.parser = Parser()

        #initialize agents in the workflow
        self.agents = self.initialize_agents()

    @abstractmethod
    def initialize_agents(self) -> Dict[str, Any]:
        """
        Initializes all of the agents in the workflow.

        Each orchestration must implement this to initialize agents as needed.
        """
        pass

    @abstractmethod
    def run_workflow(self, state: Union[str, Any]) -> Dict[str, Any]:
        """Executes the workflow"""
        pass

    @abstractmethod
    def get_agent_input(self, agent_name:str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Gets the input for specific agent based on workflow position"""
        pass

    def run_agent(self, agent_name: str, state: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Method to run an agent"""
        #retrieve the agent input
        agent_input = self.get_agent_input(agent_name, state)

        #execute agent and retrieve raw response
        agent_response = self.agents[agent_name](agent_input)

        #log if enabled
        self._log_agent(agent_name, agent_input, agent_response)

        #update the state to contain the agent response
        response_key = f"{agent_name}_result"
        state.update({response_key: agent_response})

        return state
    
    def _log_agent(self, agent_name: str, agent_input: Dict[str, Any], agent_response: Dict[str, Any]):
        """Log an agent's input and output if the logging is enabled"""
        if self.logger:
            self.logger.log_agent(agent_name, agent_input, agent_response)

