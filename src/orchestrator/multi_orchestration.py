from typing import Dict, Any
from base_orchestration import Orchestration

from agents.expert_agent import ExpertAgent
from agents.teacher_agent import TeacherAgent
from agents.tutor_agent import TutorAgent

class MultiOrchestration(Orchestration):
    def __init__(self, llm, mode_config = None, log_config = None, max_rounds = 3):
        """Override init method for multi-agent orchestration"""
        #call parent initialization method with base configurations
        super().__init__(llm, mode_config, log_config)
        #declare max number of discussion rounds
        self.max_rounds = max_rounds
        
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
            'round_num': 0,
            'consensus': False,
            'history': []
        }

        #conditional for agents to discuss while consensus or max round numbers are not met
        while not state['consensus'] and state['round_num'] < self.max_rounds:
            #update the current round number
            state['round_num'] += 1

            #run expert agent
            state = self.run_agent('expert_agent', state)
            
            #run the tutor agent
            state = self.run_agent('tutor_agent', state)

            #run the teacher agent
            state = self.run_agent('teacher_agent', state)

            #get the raw response from the teacher agent's analysis
            teacher_output = state.get('teacher_agent_result', {})
            teacher_raw_response = self._get_output(teacher_output)

            #get the consensus and the parsed response from the teacher agent
            consensus, parsed_response = self.parser.get_consensus(teacher_raw_response)

            #update the state with consensus information
            state['consensus'] = consensus
            state['teacher_parsed_response'] = parsed_response

            #store conversation round in history
            state['history'].append({
                'round_num': state['round_num'],
                'consensus': consensus,
                'feedback': parsed_response.get('feedback', '')
            })

            #log consensus status if logging is enabled
            if consensus:
                self.logger.log(f"Consensus reached at round #{state['round_num']}")
            #otherwise update revision requested by the teacher agent
            else:
                self.logger.log(f"Revision requested By teacher.")
                state['revision_feedback'] = parsed_response.get('feedback', '')

        if not state['consensus']:
            self.logger.log(f"Max rounds reached without consensus. Returning progress.")

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

        #expert agent only needs user input + context
        if agent_name == 'expert_agent':
            return agent_input
        
        #tutor agent needs expert + base input
        elif agent_name == 'tutor_agent':
            expert_output = state.get('expert_agent_result', {})
            expert_response = self._get_output(expert_output)

            #add expert response to input
            agent_input['expert_response'] = expert_response

            #handle teacher feedback during discussion round
            if 'teacher_feedback' in state:
                agent_input['revision_feedback'] = state['revision_feedback']

            return agent_input
        
        #teacher agent needs access to all information
        elif agent_name == 'teacher_agent':
            #get tutor's output
            tutor_output = state.get('tutor_agent_result', {})
            tutor_response = self._get_output(tutor_output)

            #get expert's output
            expert_output = state.get('expert_agent_result', {})
            expert_response = self._get_output(expert_output)

            #add fields to agent_input
            agent_input['expert_response'] = expert_response
            agent_input['tutor_response'] = tutor_response

            return agent_input
        
        #fallback option to return base input (should never be reached)
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