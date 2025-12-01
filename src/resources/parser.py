from typing import Dict, Any

class Parser:
    def extract_final_response(self, state: Dict[str, Any]) -> str:
        """
        Extract the response shown to the user from the workflow state.
        
        Args
            state: The final state from the orchestration
            
        Returns:
            The tutor's response (revised or original in multi-agent system)
        """
        #get tutor result from state
        tutor_result = state.get('tutor_agent_result', {})
        
        #extract text from the tutor result
        if isinstance(tutor_result, dict):
            for key, value in tutor_result.items():
                if hasattr(value, 'content'):
                    return value.content
                elif hasattr(value, 'output'):
                    return value.output
                elif isinstance(value, str):
                    return value
        
        if hasattr(tutor_result, 'content'):
            return tutor_result.content
        
        return str(tutor_result)
    
    def extract_code_blocks(self, text: str) -> list:
        """
        Extract code blocks from agent responses.
        Uses markdown-formatted text to indicate code block locations.
        """
        import re
        pattern = r'```(?:python)?\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        return matches