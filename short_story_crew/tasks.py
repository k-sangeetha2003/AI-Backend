from crewai import Task

from utils.logger import log_task_progress


class StoryCrewTasks:
    def create_creative_direction_task(self, agent, user_idea: str, genre: str):
        """Task for the Director to establish creative direction and genre vision."""
        log_task_progress(
            "Creative Direction",
            "started",
            f"Genre: {genre}, Idea: {user_idea[:30]}...",
        )
        return Task(
            description=f"""
            Based on the user's story idea: "{user_idea}" and the selected genre: "{genre.upper()}",
            establish the creative direction and vision for this 15-second short story.

            Your responsibilities:
            - Analyze how this story idea can best be adapted for the {genre} genre
            - Define the genre-specific tone, style, and approach
            - Establish key genre conventions that must be followed
            - Determine the target audience and emotional goal
            - Set visual style guidelines that match the genre
            - Define character archetypes appropriate for this genre
            - Outline pacing and structure suitable for both the genre and 15-second format

            Consider genre-specific elements:
            - If ANIME/MANGA: Dynamic expressions, character tropes, visual metaphors, dramatic reactions
            - If HORROR: Building tension, atmospheric dread, jump scares, dark imagery
            - If ROMANCE: Emotional beats, intimate moments, soft lighting, character chemistry
            - If COMEDY: Timing, visual gags, character reactions, lighthearted tone
            - If KIDS: Simple language, bright visuals, positive messages, age-appropriate content
            - If MOTIVATIONAL: Inspiring tone, overcoming challenges, uplifting message
            - And so on for other genres...

            Output a comprehensive creative direction document that will guide all other team members.
            """,
            agent=agent,
            expected_output="A detailed creative direction document with genre-specific guidelines, tone, style requirements, and vision for the 15-second story",
        )

    def create_story_task(self, agent, user_idea: str, genre: str):
        log_task_progress(
            "Story Writing", "started", f"Genre: {genre}, Idea: {user_idea[:30]}..."
        )
        return Task(
            description=f"""
            Create a compelling {genre} short story based on the user idea: "{user_idea}"
            and following the creative direction provided by the Director.

            Genre-Specific Requirements for {genre.upper()}:
            - Follow all genre conventions and creative direction guidelines
            - Adapt storytelling style to match {genre} expectations
            - Use appropriate language, tone, and pacing for {genre}
            - Include genre-specific story elements and character types

            General Requirements:
            - The story must be suitable for a 15-second duration (approximately 30-40 words when spoken)
            - Include a clear beginning, middle, and end that works for {genre}
            - Create engaging characters appropriate for {genre} conventions
            - Ensure the story has emotional impact suitable for {genre}
            - Focus on one main plot point or revelation that fits {genre}
            - Write in a script-like format with brief scene descriptions

            Output should include:
            - Genre-appropriate story title
            - Character descriptions fitting {genre} archetypes
            - Scene-by-scene breakdown with {genre}-specific elements
            - Estimated reading time
            - Genre-specific mood and tone indicators
            """,
            agent=agent,
            expected_output=f"A complete {genre} short story with title, characters, and scene breakdown optimized for 15-second delivery and genre authenticity",
        )

    def proofread_story_task(self, agent, genre: str):
        log_task_progress("Proofreading", "started", f"Genre-aware editing for {genre}")
        return Task(
            description=f"""
            Review and refine the {genre} story created by the Story Writer, ensuring both quality and genre authenticity.

            Genre-Specific Focus for {genre.upper()}:
            - Verify adherence to {genre} conventions and style guidelines
            - Ensure language and tone are appropriate for {genre}
            - Check that character dialogue matches {genre} expectations
            - Confirm visual descriptions align with {genre} aesthetics
            - Validate that pacing works for {genre} storytelling

            General Editorial Focus:
            - Grammar, spelling, and punctuation
            - Clarity and flow of the narrative
            - Ensuring the story fits within 15-second constraint
            - Maintaining emotional impact while improving readability
            - Checking that all scenes contribute to the main story
            - Verifying character consistency within {genre} archetypes
            - Optimizing word choice for maximum {genre}-appropriate impact

            Provide:
            - Edited version of the story with genre consistency maintained
            - List of changes made and genre-specific reasons
            - Confirmed timing estimate for {genre} delivery style
            - Suggestions for {genre}-appropriate delivery/pacing
            - Genre authenticity verification
            """,
            agent=agent,
            expected_output=f"A polished, refined {genre} story with editorial notes, genre authenticity confirmation, and timing within 15-second constraint",
        )

    def design_visuals_task(self, agent, genre: str):
        log_task_progress(
            "Visual Design", "started", f"Genre-specific visuals for {genre}"
        )
        return Task(
            description=f"""
            Create detailed, {genre}-specific visual descriptions for all story elements that will be used for image generation.

            Genre-Specific Visual Requirements for {genre.upper()}:
            - Follow {genre} visual conventions and aesthetics
            - Use appropriate {genre} color palettes and lighting styles
            - Include {genre}-specific character design elements
            - Apply {genre} environmental and atmospheric standards
            - Consider {genre} visual metaphors and symbolic elements

            For each scene, provide:
            - Detailed character appearance matching {genre} style (clothing, facial features, posture, expressions)
            - Background/setting descriptions appropriate for {genre} (environment, lighting, atmosphere)
            - {genre}-appropriate color palette and mood
            - Camera angle/composition suggestions suitable for {genre}
            - Props and environmental details that enhance {genre} storytelling
            - Style direction (e.g., anime-style, noir cinematography, kids-friendly bright colors)

            Format descriptions to be compatible with Stable Diffusion prompts:
            - Use {genre}-specific descriptive adjectives and details
            - Include {genre} artistic style references (e.g., "anime style", "film noir", "Disney-like")
            - Consider {genre}-appropriate lighting and composition
            - Ensure visual consistency across scenes within {genre} aesthetic
            - Add genre tags for better AI generation (e.g., "anime", "horror", "romantic")
            """,
            agent=agent,
            expected_output=f"Comprehensive {genre}-specific visual design package with detailed scene descriptions optimized for AI image generation",
        )

    def coordinate_script_task(self, agent, genre: str):
        log_task_progress(
            "Script Coordination", "started", f"Final {genre} script assembly"
        )
        return Task(
            description=f"""
            Compile all elements from the team into a final, production-ready {genre} script.

            Genre-Specific Script Requirements for {genre.upper()}:
            - Format the script according to {genre} conventions
            - Include {genre}-specific production notes and directorial guidance
            - Add {genre}-appropriate delivery instructions
            - Ensure all elements maintain {genre} consistency

            Create a comprehensive script that includes:
            - Final story text with {genre}-appropriate formatting
            - Scene-by-scene breakdown with {genre}-specific timing
            - Character descriptions and casting notes suitable for {genre}
            - Visual descriptions for each scene matching {genre} aesthetic
            - Technical notes for {genre}-appropriate production
            - Genre-specific image generation prompts for each scene
            - Delivery notes and pacing guidance for {genre} style
            - Genre authenticity verification checklist

            Format as a professional {genre} script with:
            - Clear scene headers with {genre} context
            - Dialogue and action lines appropriate for {genre}
            - Visual cues and camera directions suitable for {genre}
            - Timing markers considering {genre} pacing
            - {genre}-specific production notes section
            - Image generation prompt collection with {genre} tags
            """,
            agent=agent,
            expected_output=f"A complete, production-ready {genre} script with all visual and narrative elements integrated, professionally formatted, and genre-authentic",
        )
