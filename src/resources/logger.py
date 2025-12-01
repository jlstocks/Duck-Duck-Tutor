from typing import Dict, Any, Optional

class Logger:
    def __init__(self, enabled: bool = True):
        """Initialize the logger"""
        self.enabled = enabled
    
    @classmethod
    def from_config(cls, config: Optional[Dict[str, Any]]):
        """
        Create logger from user-defined config
        
        Args
            config: Optional dict with 'enabled' key
        
        Returns
            Logger object
        """
        if config is None:
            return cls(enabled=False)
        
        return cls(enabled=config.get('enabled', True))
    
    def log_agent(self, agent_name: str, agent_input: Dict[str, Any], agent_response: Dict[str, Any]):
        """
        Log an agent's execution
        
        Args
            agent_name: reference name of the agent
            agent_input: input provided to agent
            agent_response: an agent's analysis
        """
        if not self.enabled:
            return
        
        print(f"\n{'='*60}")
        print(f"Agent: {agent_name}")
        
        #track the inputs that are provided to the agent
        input_keys = list(agent_input.keys())
        print(f"Inputs: {', '.join(input_keys)}")
        
        #display the user input if present in state
        if 'user_input' in agent_input:
            user_msg = agent_input['user_input']
            preview = user_msg[:80] + '...' if len(user_msg) > 80 else user_msg
            print(f"User: {preview}")
        
        print(f"{'='*60}\n")