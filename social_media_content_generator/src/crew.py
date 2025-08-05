from crewai import Crew, Process, Task, Agent
import os
import logging
import time
import uuid
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from datetime import datetime
import requests
from src.agents.content_writer import ContentWriter
from src.agents.content_strategist import ContentStrategist
from src.agents.hashtag_specialist import HashtagSpecialist
from src.agents.visual_designer import VisualDesigner
from src.config.config import Config
from src.utils.simple_db_logger import SimpleDatabaseLogger
import re

class SocialMediaCrew:
    def __init__(self, logger):
        """Initialize the Social Media Crew."""
        self.logger = logger
        self.logger.info("Initializing SocialMediaCrew")
        
        # Initialize database logger
        try:
            self.db_logger = SimpleDatabaseLogger(logger)
            self.logger.info("Database logger initialized in crew")
        except Exception as e:
            self.logger.error(f"Failed to initialize database logger in crew: {str(e)}")
            self.db_logger = None
        
        # Initialize config
        self.config = Config()
        
        # Validate API keys
        if not self.config.validate_api_keys():
            raise ValueError("API key validation failed")
            
        # Set up the language model with OpenRouter
        try:
            # Get default model settings from config
            default_settings = self.config.get_agent_settings("content_writer")
            
            self.llm: BaseChatModel = ChatOpenAI(
                model_name=default_settings["model"],
                openai_api_key=self.config.openrouter_api_key,
                openai_api_base="https://openrouter.ai/api/v1",
                max_tokens=2000,
                temperature=default_settings["temperature"]
            )
            self.logger.info(f"Language model (OpenRouter) configured successfully with model: {default_settings['model']}")
            
            # Log all model configurations from config
            self.logger.info("Model configurations from config:")
            for agent_name, settings in self.config.agent_settings.items():
                self.logger.info(f"  {agent_name}: {settings['model']} (temp: {settings['temperature']})")
        except Exception as e:
            self.logger.error(f"Failed to configure language model: {str(e)}")
            raise

        # Define available tones and audiences
        self.available_tones = [
            "professional", "casual", "elegant", "romantic", "humorous", 
            "inspirational", "educational", "friendly", "formal", "persuasive",
            "enthusiastic", "mysterious", "dramatic", "minimalist", "authentic"
        ]
        self.logger.debug(f"Available tones: {', '.join(self.available_tones)}")
        
        self.target_audiences = [
            # Age Groups
            "teens (13-19)", "young adults (20-29)", "adults (30-45)", 
            "middle-aged (46-60)", "seniors (60+)",
            "children (0-12)",
            # Professional Groups
            "professionals", "students", "entrepreneurs", "executives",
            # Interest Groups
            "tech enthusiasts", "creatives", "health enthusiasts",
            "luxury consumers", "budget-conscious",
            # Skill Levels
            "beginners", "experts",
            # General
            "general audience"
        ]
        self.logger.debug(f"Available audiences: {', '.join(self.target_audiences)}")

    def get_available_tones(self):
        """Return list of available tones."""
        self.logger.debug("Returning available tones")
        return self.available_tones

    def get_target_audiences(self):
        """Return list of target audiences."""
        self.logger.debug("Returning target audiences")
        return self.target_audiences

    def generate_image(self, prompt: str, request_id: str = None) -> str:
        """Generate an image based on the content."""
        self.logger.info("Starting image generation")
        self.logger.debug(f"Image prompt: {prompt}")
        
        try:
            # Using OpenRouter's Dall-E 3 endpoint
            headers = {
                "Authorization": f"Bearer {self.config.openrouter_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "openai/dall-e-3",
                "prompt": prompt,
                "quality": "standard",
                "style": "natural",
                "size": "1024x1024"
            }
            
            self.logger.info("Sending request to OpenRouter DALL-E endpoint")
            response = requests.post(
                "https://openrouter.ai/api/v1/images/generations",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                image_url = response.json()["data"][0]["url"]
                self.logger.info("Image generated successfully")
                self.logger.debug(f"Generated image URL: {image_url}")
                return image_url
            else:
                error_msg = f"Image generation failed with status code {response.status_code}: {response.text}"
                self.logger.error(error_msg)
                
                # Log user-facing error
                if self.db_logger:
                    self.db_logger.log_user_facing_error(
                        error_type='generation_error',
                        error_category='social_content',
                        error_message=error_msg,
                        request_id=request_id
                    )
                return None
        except Exception as e:
            error_msg = f"Image generation failed with error: {str(e)}"
            self.logger.error(error_msg)
            
            # Log user-facing error
            if self.db_logger:
                self.db_logger.log_user_facing_error(
                    error_type='generation_error',
                    error_category='social_content',
                    error_message=error_msg,
                    request_id=request_id
                )
            return None

    def run(self, idea: str, platform: str, tones: list = None, audiences: list = None):
        """Execute the content generation process with specified tones and target audiences."""
        crew_id = datetime.now().strftime('%Y%m%d-%H%M%S')
        request_id = str(uuid.uuid4())
        
        # Terminal output
        print("\n" + "="*80)
        print("Crew Execution Started")
        print("Name: Social Media Content Generation Crew")
        print(f"ID: {crew_id}")
        print("="*80 + "\n")

        # Log crew start
        self.logger.info("="*50)
        self.logger.info("Crew Execution Started")
        self.logger.info(f"Crew ID: {crew_id}")
        self.logger.info("="*50)
        
        start_time = time.time()  # Start timing

        # Set defaults if not provided
        tones = tones or ["casual"]
        audiences = audiences or ["general audience"]

        # Validate inputs (platform, tones, audiences)
        try:
            self._validate_inputs(platform, tones, audiences)
        except Exception as e:
            error_msg = f"Input validation failed: {str(e)}"
            self.logger.error(error_msg)
            
            # Log error to database
            if self.db_logger:
                self.db_logger.log_user_facing_error(
                    error_type='generation_error',
                    error_category='social_content',
                    error_message=error_msg,
                    request_id=request_id
                )
            raise Exception(error_msg)

        try:
            # 1. Content Strategist
            # Terminal output
            print("\n📋 Crew: Content Strategy")
            print("└── 📝 Task: Content Analysis and Strategy Development")
            print("    Status: Executing Task...")
            print("\n🤖 Agent Started")
            print("Agent: Content Strategist")
            print(f"Task: Analyze content idea: \"{idea}\"")
            print("      Content Style:")
            print(f"      - Tones to blend: {', '.join(tones)}")
            print(f"      - Target Audiences: {', '.join(audiences)}\n")
            
            # Log agent start
            self.logger.info("Content Strategist Agent: Started")
            
            # Database logging for Content Strategist
            strategist_execution_id = None
            if self.db_logger:
                strategist_execution_id = self.db_logger.log_agent_execution(
                    agent_name="content_strategist",
                    execution_order=1,
                    input_data={
                        "idea": idea,
                        "platform": platform,
                        "tones": tones,
                        "audiences": audiences
                    },
                    model_used=self.config.get_agent_settings("content_strategist")["model"],
                    temperature=self.config.get_agent_settings("content_strategist")["temperature"]
                )
            
            strategy_start = time.time()
            try:
                strategy_result = self._execute_strategist_task(idea, platform, tones, audiences)
                strategy_time = time.time() - strategy_start
            except Exception as e:
                strategy_time = time.time() - strategy_start
                error_msg = f"Content strategist failed: {str(e)}"
                self.logger.error(error_msg)
                
                # Log error to database
                if self.db_logger:
                    self.db_logger.log_user_facing_error(
                        error_type='generation_error',
                        error_category='social_content',
                        error_message=error_msg,
                        request_id=request_id
                    )
                raise Exception(error_msg)
            
            # Update database with completion data
            if self.db_logger and strategist_execution_id:
                self.db_logger.update_agent_execution(
                    execution_uuid=strategist_execution_id,
                    status="completed",
                    output_data={"strategy_result": strategy_result},
                    execution_time_ms=int(strategy_time * 1000)
                )
            
            # Terminal output
            print(f"✅ Content Strategist completed in {strategy_time:.2f} seconds\n")
            # Log completion
            self.logger.info(f"Content Strategist Agent: Completed in {strategy_time:.2f} seconds")

            # 2. Content Writer
            # Terminal output
            print("\n📋 Crew: Content Creation")
            print("└── 📝 Task: Content Writing and Formatting")
            print("    Status: Executing Task...")
            print("\n🤖 Agent Started")
            print("Agent: Content Writer")
            print(f"Task: Generate content for platform: {platform}")
            print("      Following content strategy and guidelines\n")
            
            # Log agent start
            self.logger.info("Content Writer Agent: Started")
            
            # Database logging for Content Writer
            writer_execution_id = None
            if self.db_logger:
                writer_execution_id = self.db_logger.log_agent_execution(
                    agent_name="content_writer",
                    execution_order=2,
                    input_data={
                        "strategy_result": strategy_result,
                        "platform": platform,
                        "tones": tones,
                        "audiences": audiences
                    },
                    model_used=self.config.get_agent_settings("content_writer")["model"],
                    temperature=self.config.get_agent_settings("content_writer")["temperature"]
                )
            
            writer_start = time.time()
            try:
                writer_result = self._execute_writer_task(strategy_result, platform, tones, audiences)
                writer_time = time.time() - writer_start
            except Exception as e:
                writer_time = time.time() - writer_start
                error_msg = f"Content writer failed: {str(e)}"
                self.logger.error(error_msg)
                
                # Log error to database
                if self.db_logger:
                    self.db_logger.log_user_facing_error(
                        error_type='generation_error',
                        error_category='social_content',
                        error_message=error_msg,
                        request_id=request_id
                    )
                raise Exception(error_msg)
            
            # Update database with completion data
            if self.db_logger and writer_execution_id:
                self.db_logger.update_agent_execution(
                    execution_uuid=writer_execution_id,
                    status="completed",
                    output_data={"writer_result": writer_result},
                    execution_time_ms=int(writer_time * 1000)
                )
            
            # Terminal output
            print(f"✅ Content Writer completed in {writer_time:.2f} seconds\n")
            # Log completion
            self.logger.info(f"Content Writer Agent: Completed in {writer_time:.2f} seconds")

            # 3. Hashtag Specialist
            # Terminal output
            print("\n📋 Crew: Hashtag Optimization")
            print("└── 📝 Task: Hashtag Research and Selection")
            print("    Status: Executing Task...")
            print("\n🤖 Agent Started")
            print("Agent: Hashtag Specialist")
            print("Task: Generate and optimize hashtags")
            print(f"      Platform: {platform}")
            print(f"      Target Audiences: {', '.join(audiences)}\n")
            
            # Log agent start
            self.logger.info("Hashtag Specialist Agent: Started")
            
            # Database logging for Hashtag Specialist
            hashtag_execution_id = None
            if self.db_logger:
                hashtag_execution_id = self.db_logger.log_agent_execution(
                    agent_name="hashtag_specialist",
                    execution_order=3,
                    input_data={
                        "writer_result": writer_result,
                        "platform": platform,
                        "audiences": audiences
                    },
                    model_used=self.config.get_agent_settings("hashtag_specialist")["model"],
                    temperature=self.config.get_agent_settings("hashtag_specialist")["temperature"]
                )
            
            hashtag_start = time.time()
            try:
                hashtag_result = self._execute_hashtag_task(writer_result, platform, audiences)
                hashtag_time = time.time() - hashtag_start
            except Exception as e:
                hashtag_time = time.time() - hashtag_start
                error_msg = f"Hashtag specialist failed: {str(e)}"
                self.logger.error(error_msg)
                
                # Log error to database
                if self.db_logger:
                    self.db_logger.log_user_facing_error(
                        error_type='generation_error',
                        error_category='social_content',
                        error_message=error_msg,
                        request_id=request_id
                    )
                raise Exception(error_msg)
            
            # Update database with completion data
            if self.db_logger and hashtag_execution_id:
                self.db_logger.update_agent_execution(
                    execution_uuid=hashtag_execution_id,
                    status="completed",
                    output_data={"hashtag_result": hashtag_result},
                    execution_time_ms=int(hashtag_time * 1000)
                )
            
            # Terminal output
            print(f"✅ Hashtag Specialist completed in {hashtag_time:.2f} seconds\n")
            # Log completion
            self.logger.info(f"Hashtag Specialist Agent: Completed in {hashtag_time:.2f} seconds")

            # 4. Visual Designer
            # Terminal output
            print("\n📋 Crew: Visual Design")
            print("└── 📝 Task: Image Prompt Creation")
            print("    Status: Executing Task...")
            print("\n🤖 Agent Started")
            print("Agent: Visual Designer")
            print("Task: Create image generation prompt")
            print(f"      Platform: {platform}")
            print(f"      Tones: {', '.join(tones)}\n")
            
            # Log agent start
            self.logger.info("Visual Designer Agent: Started")
            
            # Database logging for Visual Designer
            visual_execution_id = None
            if self.db_logger:
                visual_execution_id = self.db_logger.log_agent_execution(
                    agent_name="visual_designer",
                    execution_order=4,
                    input_data={
                        "writer_result": writer_result,
                        "platform": platform,
                        "tones": tones
                    },
                    model_used=self.config.get_agent_settings("visual_designer")["model"],
                    temperature=self.config.get_agent_settings("visual_designer")["temperature"]
                )
            
            visual_start = time.time()
            try:
                visual_result = self._execute_visual_task(writer_result, platform, tones)
                visual_time = time.time() - visual_start
            except Exception as e:
                visual_time = time.time() - visual_start
                error_msg = f"Visual designer failed: {str(e)}"
                self.logger.error(error_msg)
                
                # Log error to database
                if self.db_logger:
                    self.db_logger.log_user_facing_error(
                        error_type='generation_error',
                        error_category='social_content',
                        error_message=error_msg,
                        request_id=request_id
                    )
                raise Exception(error_msg)
            
            # Update database with completion data
            if self.db_logger and visual_execution_id:
                self.db_logger.update_agent_execution(
                    execution_uuid=visual_execution_id,
                    status="completed",
                    output_data={"visual_result": visual_result},
                    execution_time_ms=int(visual_time * 1000)
                )
            
            # Terminal output
            print(f"✅ Visual Designer completed in {visual_time:.2f} seconds\n")
            # Log completion
            self.logger.info(f"Visual Designer Agent: Completed in {visual_time:.2f} seconds")
            # Log the image prompt
            self.logger.info(f"Generated Image Prompt: {visual_result}")

            # Generate image
            # Terminal output
            print("\n📋 Crew: Image Generation")
            print("└── 📝 Task: AI Image Creation")
            print("    Status: Executing Task...")
            
            # Log image generation start
            self.logger.info("Image Generation: Started")
            
            # Database logging for image generation
            if self.db_logger and visual_execution_id:
                self.db_logger.log_image_generation(
                    agent_execution_uuid=visual_execution_id,
                    prompt=visual_result,
                    model_used="openai/dall-e-3",
                    status="started"
                )
            
            image_start = time.time()
            try:
                image_url = self.generate_image(visual_result, request_id)
                image_time = time.time() - image_start
                
                # Update image generation with success
                if self.db_logger and visual_execution_id:
                    self.db_logger.log_image_generation(
                        agent_execution_uuid=visual_execution_id,
                        prompt=visual_result,
                        generated_image_url=image_url,
                        image_size="1024x1024",
                        model_used="openai/dall-e-3",
                        cost_usd=0.040,  # DALL-E 3 cost
                        status="completed"
                    )
                
                # Terminal output
                print(f"✅ Image Generation completed in {image_time:.2f} seconds\n")
                # Log completion
                self.logger.info(f"Image Generation: Completed in {image_time:.2f} seconds")
                
            except Exception as e:
                image_time = time.time() - image_start
                error_msg = f"Image generation failed: {str(e)}"
                
                # Log error to database
                if self.db_logger:
                    self.db_logger.log_user_facing_error(
                        error_type='generation_error',
                        error_category='social_content',
                        error_message=error_msg,
                        request_id=request_id
                    )
                
                # Update image generation with error
                if self.db_logger and visual_execution_id:
                    self.db_logger.log_image_generation(
                        agent_execution_uuid=visual_execution_id,
                        prompt=visual_result,
                        model_used="openai/dall-e-3",
                        status="failed",
                        error_message=error_msg
                    )
                
                self.logger.error(error_msg)
                image_url = None

            # Prepare final content package
            content_package = self._prepare_content_package(
                platform, tones, audiences,
                writer_result, hashtag_result, visual_result, image_url,
                {
                    'total': time.time() - start_time,
                    'strategy': strategy_time,
                    'writing': writer_time,
                    'hashtags': hashtag_time,
                    'visual': visual_time,
                    'image': image_time
                }
            )

            # Terminal output
            print("\n" + "="*80)
            print("Content Generation Complete")
            print(f"Total Execution Time: {content_package['generation_time']}")
            print("="*80 + "\n")
            
            # Log completion
            self.logger.info("="*50)
            self.logger.info("Content Generation Complete")
            self.logger.info(f"Total Execution Time: {content_package['generation_time']}")
            self.logger.info("="*50)
            
            return content_package

        except Exception as e:
            # Terminal output
            print("\n❌ Error occurred during content generation")
            print(f"Error details: {str(e)}\n")
            # Log error
            self.logger.error("Content Generation Error")
            self.logger.error(f"Error details: {str(e)}", exc_info=True)
            
            # Log user-facing error to database
            if hasattr(self, 'db_logger') and self.db_logger:
                self.db_logger.log_user_facing_error(
                    error_type='generation_error',
                    error_category='social_content',
                    error_message=f"Content generation failed: {str(e)}",
                    request_id=request_id
                )
            
            raise Exception(f"Content generation failed: {str(e)}")

    def _validate_inputs(self, platform, tones, audiences):
        """Validate input parameters."""
        # Validate platform
        valid_platforms = ['instagram', 'twitter', 'linkedin', 'facebook', 'tiktok', 'youtube']
        if platform.lower() not in valid_platforms:
            error_msg = f"Unsupported platform. Choose from: {', '.join(valid_platforms)}"
            self.logger.error(f"Invalid platform: {platform}")
            
            # Log user-facing error
            if self.db_logger:
                self.db_logger.log_user_facing_error(
                    error_type='ValidationError',
                    error_category='social_media',
                    error_message=error_msg
                )
            raise ValueError(error_msg)

        # Validate tones and audiences
        for tone in tones:
            if tone.lower() not in [t.lower() for t in self.available_tones]:
                error_msg = f"Unsupported tone '{tone}'. Choose from: {', '.join(self.available_tones)}"
                self.logger.error(f"Invalid tone: {tone}")
                
                # Log user-facing error
                if self.db_logger:
                    self.db_logger.log_user_facing_error(
                        error_type='generation_error',
                        error_category='social_content',
                        error_message=error_msg
                    )
                raise ValueError(error_msg)
                
        for audience in audiences:
            if audience.lower() not in [a.lower() for a in self.target_audiences]:
                error_msg = f"Unsupported audience '{audience}'. Choose from: {', '.join(self.target_audiences)}"
                self.logger.error(f"Invalid audience: {audience}")
                
                # Log user-facing error
                if self.db_logger:
                    self.db_logger.log_user_facing_error(
                        error_type='generation_error',
                        error_category='social_content',
                        error_message=error_msg
                    )
                raise ValueError(error_msg)

    def _prepare_content_package(self, platform, tones, audiences, writer_result, hashtag_result, visual_result, image_url, times):
        """Prepare the final content package with all components."""
        return {
            "platform": platform,
            "tones": tones,
            "audiences": audiences,
            "timestamp": datetime.now().isoformat(),
            "generation_time": f"{times['total']:.2f} seconds",
            "phase_times": {
                "strategy": f"{times['strategy']:.2f} seconds",
                "writing": f"{times['writing']:.2f} seconds",
                "hashtags": f"{times['hashtags']:.2f} seconds",
                "visual": f"{times['visual']:.2f} seconds",
                "image": f"{times['image']:.2f} seconds"
            },
            "content": self._parse_writer_result(writer_result),
            "hashtags": self._parse_hashtag_result(hashtag_result),
            "image_url": image_url
        }

    def _parse_writer_result(self, result):
        """Parse the writer's result into structured content."""
        def remove_hashtags(text):
            return re.sub(r'#\w+', '', text).replace('  ', ' ').strip()
        
        # Parse the new format with Title, Introduction, Main Points, etc.
        sections = {}
        current_section = None
        lines = []
        
        for line in result.split('\n'):
            line = line.strip()
            if line.upper().startswith('TITLE:'):
                if current_section:
                    sections[current_section] = '\n'.join(lines).strip()
                current_section = 'title'
                lines = []
            elif line.upper().startswith('INTRODUCTION:'):
                if current_section:
                    sections[current_section] = '\n'.join(lines).strip()
                current_section = 'introduction'
                lines = []
            elif line.upper().startswith('MAIN POINTS:'):
                if current_section:
                    sections[current_section] = '\n'.join(lines).strip()
                current_section = 'main_points'
                lines = []
            elif line.upper().startswith('CONCLUSION:'):
                if current_section:
                    sections[current_section] = '\n'.join(lines).strip()
                current_section = 'conclusion'
                lines = []
            elif line.upper().startswith('CAPTION:'):
                if current_section:
                    sections[current_section] = '\n'.join(lines).strip()
                current_section = 'caption'
                lines = []
            elif line.upper().startswith('HASHTAGS:'):
                if current_section:
                    sections[current_section] = '\n'.join(lines).strip()
                current_section = 'hashtags'
                lines = []
            elif line.upper().startswith('RESOURCES:'):
                if current_section:
                    sections[current_section] = '\n'.join(lines).strip()
                current_section = None  # Ignore resources section
                lines = []
            elif line and current_section:
                lines.append(line)
        
        if current_section:
            sections[current_section] = '\n'.join(lines).strip()
        
        # Remove hashtags from caption
        caption = remove_hashtags(sections.get('caption', ''))
        
        # Combine all content sections
        main_content_parts = []
        if sections.get('title'):
            main_content_parts.append(f"Title: {sections['title']}")
        if sections.get('introduction'):
            main_content_parts.append(f"Introduction: {sections['introduction']}")
        if sections.get('main_points'):
            main_content_parts.append(f"Main Points: {sections['main_points']}")
        if sections.get('conclusion'):
            main_content_parts.append(f"Conclusion: {sections['conclusion']}")
        
        main_content = '\n\n'.join(main_content_parts)
        
        return {
            "main_content": main_content,
            "captions": {"primary": caption},
            "hashtags": sections.get('hashtags', ''),
            "title": sections.get('title', ''),
            "introduction": sections.get('introduction', ''),
            "main_points": sections.get('main_points', ''),
            "conclusion": sections.get('conclusion', '')
        }
        # Default parsing for other platforms
        sections = {}
        current_section = None
        lines = []
        for line in result.split('\n'):
            line = line.strip()
            if line.upper().startswith('MAIN POST:'):
                current_section = 'main_post'
                lines = []
            elif line.upper().startswith('CAPTION:'):
                if current_section == 'main_post':
                    sections['main_post'] = '\n'.join(lines).strip()
                current_section = 'caption'
                lines = []
            elif line.upper().startswith('HASHTAGS:'):
                if current_section == 'caption':
                    sections['caption'] = '\n'.join(lines).strip()
                break
            elif line and current_section:
                lines.append(line)
        # Remove hashtags from caption
        caption = remove_hashtags(sections.get('caption', ''))
        return {
            "main_content": sections.get('main_post', ''),
            "captions": {"primary": caption}
        }

    def _parse_hashtag_result(self, result):
        """Parse the hashtag specialist's result into structured hashtags."""
        hashtags = []
        for line in result.split('\n'):
            line = line.strip()
            if line.startswith('#'):
                hashtags.extend(tag.strip() for tag in line.split() if tag.strip().startswith('#'))
        return {"trending": hashtags}

    def _execute_strategist_task(self, idea, platform, tones, audiences):
        """Execute Content Strategist task."""
        # Get model settings from config
        agent_settings = self.config.get_agent_settings("content_strategist")
        
        strategist_llm = ChatOpenAI(
            model_name=agent_settings["model"],
            openai_api_key=self.config.openrouter_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            max_tokens=2000,
            temperature=agent_settings["temperature"]
        )
        
        content_strategist = ContentStrategist.create(strategist_llm)
        strategy_task = Task(
            description=f"""Analyze this content idea and create a detailed content strategy:
            Idea: {idea}
            Platform: {platform}
            Tones: {', '.join(tones)}
            Target Audiences: {', '.join(audiences)}
            
            Provide a clear content strategy including:
            1. Key themes and messages
            2. Content structure
            3. Engagement hooks
            4. Platform-specific optimization tips""",
            agent=content_strategist
        )
        
        strategy_crew = Crew(
            agents=[content_strategist],
            tasks=[strategy_task],
            process=Process.sequential,
            verbose=True
        )
        return strategy_crew.kickoff()

    def _execute_writer_task(self, strategy_result, platform, tones, audiences):
        """Execute Content Writer task."""
        # Get model settings from config
        agent_settings = self.config.get_agent_settings("content_writer")
        
        writer_llm = ChatOpenAI(
            model_name=agent_settings["model"],
            openai_api_key=self.config.openrouter_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            max_tokens=2000,
            temperature=agent_settings["temperature"]
        )
        
        content_writer = ContentWriter.create(writer_llm)
        writer_task_description = f"""Using the content strategy, create engaging social media content:
Strategy: {strategy_result}
Platform: {platform}
"""
        if platform.lower() == "youtube":
            writer_task_description += """
Format: Follow this structure exactly:

TITLE:
[Engaging title for the video]

INTRODUCTION:
[Compelling introduction that hooks the viewer]

MAIN POINTS:
1. [Main Point Title] ([timestamp])
- [Bullet points for this section]
2. [Main Point Title] ([timestamp])
- [Bullet points for this section]
... (continue with as many points as needed)

CONCLUSION:
[Strong conclusion that wraps up the content]

CAPTION:
[Engaging caption with emojis that summarizes the video]
Use real Unicode emojis directly in the text (e.g., 🏔️, 🍵, 📷). Do NOT use placeholders like [mountain emoji].
(Do NOT include hashtags in the caption. Only include hashtags in the HASHTAGS section.)

HASHTAGS:
[#hashtags separated by space]

RESOURCES:
[List of resources, links, or further reading]
"""
        elif platform.lower() in ["instagram", "tiktok"]:
            writer_task_description += """
Format: Follow this structure exactly:

MAIN POST:
Write the main content as a natural, engaging post. Do NOT use brackets or scene/image descriptions. Use real Unicode emojis directly in the text (e.g., 🏔️, 🍵, 📷). Do NOT use placeholders like [mountain emoji]. Do not use hashtags in the main post.

CAPTION:
[Caption with emojis]
Use real Unicode emojis directly in the text (e.g., 🏔️, 🍵, 📷). Do NOT use placeholders like [mountain emoji].
(Do NOT include hashtags in the caption. Only include hashtags in the HASHTAGS section.)

HASHTAGS:
[8 relevant hashtags]
"""
        else:
            writer_task_description += """
Format: Follow this structure exactly:

MAIN POST:
[Main content]
(Do NOT include hashtags in the main post. Only include hashtags in the HASHTAGS section.)

CAPTION:
[Caption with emojis]
Use real Unicode emojis directly in the text (e.g., 🏔️, 🍵, 📷). Do NOT use placeholders like [mountain emoji].
(Do NOT include hashtags in the caption. Only include hashtags in the HASHTAGS section.)

HASHTAGS:
[8 relevant hashtags]
"""
        writer_task = Task(
            description=writer_task_description,
            agent=content_writer
        )
        
        writer_crew = Crew(
            agents=[content_writer],
            tasks=[writer_task],
            process=Process.sequential,
            verbose=True
        )
        return writer_crew.kickoff()

    def _execute_hashtag_task(self, writer_result, platform, audiences):
        """Execute Hashtag Specialist task."""
        # Get model settings from config
        agent_settings = self.config.get_agent_settings("hashtag_specialist")
        
        hashtag_llm = ChatOpenAI(
            model_name=agent_settings["model"],
            openai_api_key=self.config.openrouter_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            max_tokens=2000,
            temperature=agent_settings["temperature"]
        )
        
        hashtag_specialist = HashtagSpecialist.create(hashtag_llm)
        hashtag_task = Task(
            description=f"""Optimize and expand the hashtags for maximum reach:
            Content: {writer_result}
            Platform: {platform}
            Target Audiences: {', '.join(audiences)}
            
            Provide:
            1. Trending hashtags
            2. Niche hashtags
            3. Branded hashtags""",
            agent=hashtag_specialist
        )
        
        hashtag_crew = Crew(
            agents=[hashtag_specialist],
            tasks=[hashtag_task],
            process=Process.sequential,
            verbose=True
        )
        return hashtag_crew.kickoff()

    def _execute_visual_task(self, writer_result, platform, tones):
        """Execute Visual Designer task."""
        # Get model settings from config
        agent_settings = self.config.get_agent_settings("visual_designer")
        
        visual_llm = ChatOpenAI(
            model_name=agent_settings["model"],
            openai_api_key=self.config.openrouter_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            max_tokens=2000,
            temperature=agent_settings["temperature"]
        )
        
        visual_designer = VisualDesigner.create(visual_llm)
        visual_task = Task(
            description=f"""Create a detailed image generation prompt based on:
            Content: {writer_result}
            Platform: {platform}
            Tone: {', '.join(tones)}
            
            The prompt should:
            1. Match the content's message
            2. Follow platform best practices
            3. Include specific visual details
            4. Consider the target audience""",
            agent=visual_designer
        )
        
        visual_crew = Crew(
            agents=[visual_designer],
            tasks=[visual_task],
            process=Process.sequential,
            verbose=True
        )
        return visual_crew.kickoff()

    def validate_setup(self) -> bool:
        """Validate the setup."""
        self.logger.info("Validating setup")
        try:
            return self.config.validate_api_keys()
        except Exception as e:
            self.logger.error(f"Setup validation failed: {str(e)}", exc_info=True)
            return False 