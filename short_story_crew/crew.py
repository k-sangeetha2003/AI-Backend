from crewai import Crew, Process

from agents import StoryCrewAgents
from config import Config
from tasks import StoryCrewTasks
from utils.logger import (
    get_logger,
    log_crew_action,
    log_error,
    log_info,
    log_story_generation,
    log_warning,
)

logger = get_logger("crew")


class ShortStoryCrew:
    def __init__(self):
        """Initialize the Short Story Crew with all agents and tasks."""
        log_info(
            "Initializing Short Story Crew with enhanced logging and genre support"
        )

        # Validate configuration
        try:
            Config.validate()
            log_info("Configuration validation successful")
        except Exception as e:
            log_error(f"Configuration validation failed: {str(e)}", exc_info=True)
            raise

        # Initialize agents and tasks
        self.agents = StoryCrewAgents()
        self.tasks = StoryCrewTasks()

        # Create agent instances
        self.director = self.agents.director()
        self.story_writer = self.agents.story_writer()
        self.proofreader = self.agents.proofreader()
        self.art_designer = self.agents.art_designer()
        self.script_coordinator = self.agents.script_coordinator()

        log_info("All crew members initialized successfully")
        log_crew_action(
            "System",
            "Crew initialization complete",
            "5 agents ready: Director, Writer, Proofreader, Art Designer, Coordinator",
        )

    def create_story(self, user_idea: str, genre: str) -> str:
        """
        Create a complete short story script based on user's idea and genre.

        Args:
            user_idea (str): The user's base idea for the story
            genre (str): The genre for the story (e.g., 'anime', 'horror', 'romance')

        Returns:
            str: Complete script with all elements
        """
        try:
            # Validate genre
            if genre.lower() not in Config.SUPPORTED_GENRES:
                log_warning(f"Genre '{genre}' not in supported list, proceeding anyway")

            log_story_generation(
                "START", genre, user_idea, "Beginning crew collaboration"
            )

            # Create tasks with the user's idea and genre
            direction_task = self.tasks.create_creative_direction_task(
                self.director, user_idea, genre
            )
            story_task = self.tasks.create_story_task(
                self.story_writer, user_idea, genre
            )
            proofread_task = self.tasks.proofread_story_task(self.proofreader, genre)
            visual_task = self.tasks.design_visuals_task(self.art_designer, genre)
            script_task = self.tasks.coordinate_script_task(
                self.script_coordinator, genre
            )

            # Set up task dependencies
            story_task.context = [direction_task]
            proofread_task.context = [direction_task, story_task]
            visual_task.context = [direction_task, proofread_task]
            script_task.context = [direction_task, proofread_task, visual_task]

            log_info(f"Task dependencies established for {genre} story")

            # Create and run the crew
            crew = Crew(
                agents=[
                    self.director,
                    self.story_writer,
                    self.proofreader,
                    self.art_designer,
                    self.script_coordinator,
                ],
                tasks=[
                    direction_task,
                    story_task,
                    proofread_task,
                    visual_task,
                    script_task,
                ],
                process=Process.sequential,
                verbose=True,
            )

            log_crew_action(
                "System",
                "Starting crew execution",
                f"5 agents working on {genre} story",
            )

            result = crew.kickoff()

            log_story_generation(
                "COMPLETE", genre, user_idea, "All crew members completed their tasks"
            )

            return result

        except Exception as e:
            log_error(f"Error creating {genre} story: {str(e)}", exc_info=True)
            raise

    def get_crew_info(self) -> dict:
        """Get information about the crew members and their roles."""
        log_info("Retrieving crew information")
        return {
            "crew_members": {
                "director": {
                    "role": "Creative Director & Genre Specialist",
                    "responsibility": "Sets overall creative vision and genre-specific direction",
                },
                "story_writer": {
                    "role": "Genre-Aware Story Writer",
                    "responsibility": "Creates genre-appropriate narratives and story structure",
                },
                "proofreader": {
                    "role": "Professional Proofreader & Genre Editor",
                    "responsibility": "Reviews and refines story for clarity, timing, and genre consistency",
                },
                "art_designer": {
                    "role": "Genre-Specific Visual Art & Scene Designer",
                    "responsibility": "Creates genre-appropriate visual descriptions for image generation",
                },
                "script_coordinator": {
                    "role": "Script Coordinator & Production Format Specialist",
                    "responsibility": "Compiles everything into a genre-consistent production-ready script",
                },
            },
            "supported_genres": Config.SUPPORTED_GENRES,
            "llm_models": {
                crew_member: Config.get_model_for_crew(crew_member)
                for crew_member in Config.CREW_MODELS.keys()
            },
            "process": "Sequential workflow with Director establishing vision, then each stage building upon the previous",
            "output": "Complete genre-specific script with narrative, visual descriptions, and production notes",
        }
