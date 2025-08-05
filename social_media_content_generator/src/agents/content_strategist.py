from crewai import Agent
from typing import List
import sys
import os
from langchain_core.language_models.chat_models import BaseChatModel

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.tools.web_tools import url_scraper

class ContentStrategist:
    @staticmethod
    def create(llm: BaseChatModel) -> Agent:
        """
        Creates a Content Strategist agent that analyzes topics and references
        to develop content strategy.
        
        Args:
            llm (BaseChatModel): The language model to use for the agent
        """
        return Agent(
            role='Content Strategist',
            goal='Analyze topics and references to develop effective content strategies',
            backstory="""You are an expert content strategist with years of experience in 
            social media marketing. You excel at analyzing topics, identifying trends, and 
            creating effective content strategies that resonate with target audiences.""",
            tools=[url_scraper],
            llm=llm,
            verbose=True
        )

    @staticmethod
    def analyze_topic(topic: str, references: List[str] = None) -> dict:
        """
        Analyzes the given topic and references to create a content strategy.
        
        Args:
            topic (str): The main topic for content creation
            references (List[str], optional): List of reference URLs
            
        Returns:
            dict: Content strategy including key themes, tone, style, etc.
        """
        strategy = {
            "topic": topic,
            "key_themes": [],
            "tone": "",
            "style": "",
            "target_audience": "",
            "content_pillars": [],
            "reference_insights": []
        }
        
        # Strategy will be developed by the agent during execution
        return strategy 