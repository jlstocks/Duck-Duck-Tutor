from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

"""
abstract base agent class inherited by other agents
"""
class Agent(ABC):
    def __init__(self, llm, mode_config: Optional[Dict[str, Any]] = None):
        """Initialize the agent"""
        self.llm = llm
        #declare mode config ("debug", "test", )
        self.mode_config = mode_config

        #extract mode settings from mode_config
        self.debug_mode = self.mode_config.get('debug_mode', False)

        #build prompts for each agent
        self.prompt_template = self.build_prompt()

    @abstractmethod
    def build_prompt(self):
        """Abstract method, builds agent's prompt from template"""
        pass

    @abstractmethod
    def get_agent_name(self) -> str:
        """getter method used to return an agent's key for state reference"""
        pass

    def __call__(self, agent_input: Dict[str, Any]) -> Dict[str, Any]:
        """Call method"""
        response = self._invoke_llm(agent_input)

        return {self.get_agent_name(): response}
    
    def _invoke_llm(self, agent_input: Dict[str, Any]):
        """Helper method to invoke the LLM with provided input"""
        #create the agent from the prompt template
        chain = self.prompt_template | self.llm

        #return the invocation of the agent
        return chain.invoke(agent_input)
    