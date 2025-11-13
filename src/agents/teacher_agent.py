from langchain_core.prompts import ChatPromptTemplate
from base_agent import Agent

class TeacherAgent(Agent):
    def build_prompt(self):
        if not self.debug_mode:
            system_message = """


"""
        else:
            system_message = """
"""

        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("user", """


""")
        ])
    
    def get_agent_name(self) -> str:
        return "teacher_agent_result"