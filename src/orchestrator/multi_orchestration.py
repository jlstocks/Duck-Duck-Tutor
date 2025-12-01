from typing import Dict, Any
from base_orchestration import Orchestration

from agents.expert_agent import ExpertAgent
from agents.teacher_agent import TeacherAgent
from agents.tutor_agent import TutorAgent

class MultiOrchestration(Orchestration):
    def __init__(self, llm, mode_config = None, log_config = None, revision_enabled = True):
        """Override init method for multi-agent orchestration"""
        #call parent initialization method with base configurations
        super().__init__(llm, mode_config, log_config)
        #define revision status for tutor based on agent feedback
        self.revision = revision_enabled
        
    def initialize_agents(self) -> Dict[str, Any]:
        """Implement agent initialization to handle multiple agents"""
        return {
            'expert_agent': ExpertAgent(self.llm, mode_config = self.mode_config),
            'tutor_agent': TutorAgent(self.llm, mode_config = self.mode_config),
            'teacher_agent': TeacherAgent(self.llm, mode_config = self.mode_config)
        }
    
    def run_workflow(self, user_input: str) -> Dict[str, Any]:
        """Override the workflow method"""
        #initialize the state
        state = {
            'user_input': user_input,
            'stage': 'initial'
        }
        
        #run the tutor agent
        state = self.run_agent('tutor_agent', state)
        
        #run the expert agent given the tutor's analysis
        state = self.run_agent('expert_agent', state)

        #run the teacher agent provided other agent analyses
        state = self.run_agent('teacher_agent', state)

        #optional stage for tutor revision using teacher feedback
        if self.revision:
            state['stage'] = 'revision'
            state = self.run_agent('tutor_agent', state)

        return state
    
    def get_agent_input(self, agent_name: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Gets the agent input for specific agent based on workflow position"""
        #declare base input
        agent_input = {
            'user_input': state.get('user_input', '')
        }
        
        #add context for session handling
        if 'context' in state:
            agent_input['context'] = state['context']

        #tutor agent
        if agent_name == 'tutor_agent':
            return self._get_tutor_input(agent_input, state)
        elif agent_name == 'expert_agent':
            return self._get_expert_input(agent_input, state)
        elif agent_name == 'teacher_agent':
            return self._get_teacher_input(agent_input, state)
        else:
            return agent_input

    def _get_output(self, agent_response: Dict[str, Any]) -> str:
        """Helper method to extract text content from an agent's response"""
        if isinstance(agent_response, dict):
            for key in agent_response:
                output = agent_response[key]
                if hasattr(output, 'output'):
                    return output.output
                elif isinstance(output, str):
                    return output
                
        if hasattr(agent_response, 'content'):
            return agent_response.content
        
        return str(agent_response)
    

    def _get_tutor_input(self, base_input: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare input for the tutor agent"""
        stage = state.get('stage', 'initial')

        #handle initial stage after user input
        if stage == 'initial':
            return base_input
        
        #handle revision stage after teacher feedback
        elif stage == 'revision':
            base_input['teacher_agent_result'] = state.get('teacher_agent_result', '')
            return base_input
        
        #fallback
        return base_input
    
    def _get_expert_input(self, base_input: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare input for expert agent"""
        #get tutor's initial response for expert
        tutor_output = state.get('tutor_agent_result', {})
        tutor_response = self._get_output(tutor_output)
        
        #update input to include tutor response
        base_input['tutor_response'] = tutor_response
        return base_input
    
    def _get_teacher_input(self, base_input: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare input for teacher agent"""
        #get tutor's response and expert's analysis for teacher
        tutor_output = state.get('tutor_agent_result', {})
        tutor_response = self._get_output(tutor_output)
        expert_output = state.get('expert_agent_result', {})
        expert_response = self._get_output(expert_output)
        
        #update input to include other responses
        base_input['tutor_response'] = tutor_response
        base_input['expert_analysis'] = expert_response
        return base_input