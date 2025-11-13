from typing import Dict, Any, Union
from base_orchestration import Orchestration
from agents.tutor_agent import TutorAgent

class SingleOrchestration(Orchestration):
    def initialize_agents(self):
        """Initialize only the tutor agent for single-agent orchestration"""
        return {
            'tutor_agent': TutorAgent(self.llm, mode_config = self.mode_config)
        }
    
    def run_workflow(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Implements the run workflow method for the single-agent workflow"""
        state = {
            'user_input': user_input
        }

        #run the tutor agent
        state = self.run_agent('tutor_agent', state)

        return state
    
    def get_agent_input(self, agent_name, state):
        """Override get agent input to return only the user-input for the tutor agent"""
        return {
            'user_input': state.get('user_input', '')
        }