import logging
from agents.utils.agent_utils import AgentUtils

# Configure logging
logger = logging.getLogger(__name__)

class ChatbotAgent:
    """
    Agent responsible for General Chat, Greetings, and Capabilities explanations.
    It acts as the 'Face' of the system when no specific data/search is needed.
    """

    def __init__(self):
        self.utils = AgentUtils()
        
    def run(self, user_query: str) -> str:
        """
        Generates a conversational response based on the user's input.
        """
        logger.info(f"--- General Chat Started: '{user_query}' ---")

        # 1. Quick check for specific "Help" or "Capabilities" keywords
        #    to provide a deterministic, high-quality menu.
        if self._is_help_request(user_query):
            return self._get_capabilities_message()

        # 2. Construct Persona-based Prompt
        system_prompt = (
            "You are QGenie, an advanced Financial & Operational Data Assistant.\n"
            "Your purpose is to help users query Opex data, search policies, and analyze financial reports.\n\n"
            
            "**Guidelines:**\n"
            "1. Be professional, concise, and helpful.\n"
            "2. If the user greets you, greet them back warmly and ask how you can help with their data.\n"
            "3. If the user asks a question you cannot answer (e.g., about sports, weather, or coding unrelated to this context), "
            "politely decline and remind them of your financial focus.\n"
            "4. Do NOT make up data. If you don't know, ask the user to clarify.\n\n"
            "5. stick to finance related topics and provide sufficient details as the audience are financial experts. \n\n"
            
            f"**User Input:** {user_query}\n\n"
            "**Response:**"
        )

        # 3. Generate Response
        try:
            response = self.utils.llm_call(system_prompt)
            return response
        except Exception as e:
            logger.error(f"Chatbot LLM call failed: {e}")
            return "I'm having trouble processing that right now. How else can I assist you with your data?"

    def _is_help_request(self, query: str) -> bool:
        """
        Simple heuristic to detect if the user is asking what the bot can do.
        """
        keywords = ["help", "what can you do", "capabilities", "features", "menu", "assist"]
        q_lower = query.lower()
        return any(k in q_lower for k in keywords)

    def _get_capabilities_message(self) -> str:
        """
        Returns a formatted string of capabilities.
        """
        return (
            "**I can assist you with the following:**\n\n"
            "📊 **Data Analysis (SQL)**\n"
            "- \"What is the total spend for Project X?\"\n"
            "- \"List the top 5 vendors by cost in Q1.\"\n"
            "- \"Compare actuals vs. budget for Dept 123.\"\n\n"
            "📚 **Knowledge Search (Semantic)**\n"
            "- \"What is the travel reimbursement policy?\"\n"
            "- \"How do I submit a variance report?\"\n"
            "- \"Summarize the FY24 strategic goals.\"\n\n"
            "Just ask me a question in plain English!"
        )

if __name__ == "__main__":
    print("\n=== Initializing Chatbot Agent ===")
    try:
        bot = ChatbotAgent()
        
        test_inputs = [
            "Hello, who are you?",
            "Can you help me?",
            "What is the capital of France?", # Out of scope test
            "I need to analyze some variance data."
        ]

        print(f"\nRunning {len(test_inputs)} test cases...\n")

        for inp in test_inputs:
            print(f"👤 User: {inp}")
            resp = bot.run(inp)
            print(f"🤖 Bot:  {resp}\n")
            print("-" * 50)

    except Exception as e:
        logger.error(f"Initialization Failed: {e}")