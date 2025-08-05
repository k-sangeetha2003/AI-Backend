import os
import sys
import time
from datetime import datetime
import logging
from dotenv import load_dotenv

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Add Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.crew import SocialMediaCrew
from src.utils.simple_db_logger import SimpleDatabaseLogger

class SocialMediaContentGenerator:
    def __init__(self, logger):
        self.logger = logger
        self.logger.info("Initializing SocialMediaContentGenerator")
        
        # Initialize database logger
        try:
            self.db_logger = SimpleDatabaseLogger(logger)
            self.logger.info("Database logger initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize database logger: {str(e)}")
            self.db_logger = None
        
        self.crew = SocialMediaCrew(self.logger)
        if not self.crew.validate_setup():
            self.logger.error("Invalid setup detected")
            raise ValueError("Invalid setup. Please check your .env file and configurations.")
        self.logger.info("SocialMediaContentGenerator initialized successfully")

    def generate_content(self, idea: str, platform: str, tones: list = None, audiences: list = None):
        session_id = None
        total_tokens_used = 0
        total_cost_usd = 0.0
        start_time = time.time()
        
        try:
            # Start database logging session
            if self.db_logger:
                session_id = self.db_logger.start_generation_session(
                    idea=idea,
                    platform=platform,
                    tones=tones,
                    audiences=audiences
                )
                self.logger.info(f"Started database logging session: {session_id}")
            
            self.logger.info(f"Generating content for platform: {platform}")
            self.logger.debug(f"Idea: {idea}")
            self.logger.debug(f"Tones: {tones}")
            self.logger.debug(f"Audiences: {audiences}")
            
            result = self.crew.run(idea, platform, tones, audiences)
            
            # Calculate total tokens and cost from result
            if 'total_tokens' in result:
                total_tokens_used = result['total_tokens']
            if 'total_cost' in result:
                total_cost_usd = result['total_cost']
            
            self._save_result(result, idea)
            
            # Log performance metrics
            generation_time = time.time() - start_time
            if self.db_logger:
                self.db_logger.log_performance_metric('total_generation_time', generation_time, 'seconds')
                self.db_logger.complete_generation_session(
                    status='completed',
                    total_tokens_used=total_tokens_used,
                    total_cost_usd=total_cost_usd
                )
            
            self.logger.info("Content generation completed successfully")
            return result
            
        except Exception as e:
            error_message = f"Content generation failed: {str(e)}"
            self.logger.error(error_message, exc_info=True)
            # Log user-facing error to database
            if self.db_logger:
                self.db_logger.log_user_facing_error(
                    error_type='generation_error',
                    error_category='social_content',
                    error_message=error_message,
                        session_id=session_id
                    )
                self.db_logger.complete_generation_session(
                    status='failed',
                    total_tokens_used=total_tokens_used,
                    total_cost_usd=total_cost_usd,
                    error_message=error_message
                )
            
            raise Exception(error_message)

    def _save_result(self, result, original_idea):
        try:
            self.logger.info("Saving generated content")
            # Create outputs directory if it doesn't exist
            os.makedirs("outputs", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            platform = result["platform"]

            # Save content as TXT
            txt_filename = f"outputs/content_{platform}_{timestamp}.txt"
            self.logger.debug(f"Saving to file: {txt_filename}")
            
            with open(txt_filename, 'w', encoding='utf-8') as f:
                # Write the original idea and style information
                f.write("Original Idea:\n")
                f.write(f"{original_idea}\n\n")
                f.write("Style Settings:\n")
                f.write(f"Tones: {', '.join(result['tones'])}\n")
                f.write(f"Target Audiences: {', '.join(result['audiences'])}\n\n")

                # Write generated content
                if "content" in result:
                    content = result["content"]
                    if isinstance(content, dict):
                        # Write title
                        if "title" in content and content["title"]:
                            f.write("Title:\n")
                            f.write(content["title"] + "\n\n")
                        
                        # Write introduction
                        if "introduction" in content and content["introduction"]:
                            f.write("Introduction:\n")
                            f.write(content["introduction"] + "\n\n")
                        
                        # Write main points
                        if "main_points" in content and content["main_points"]:
                            f.write("Main Points:\n")
                            f.write(content["main_points"] + "\n\n")
                        
                        # Write conclusion
                        if "conclusion" in content and content["conclusion"]:
                            f.write("Conclusion:\n")
                            f.write(content["conclusion"] + "\n\n")
                        
                        # Write caption
                        if "captions" in content:
                            if isinstance(content["captions"], dict):
                                if "primary" in content["captions"]:
                                    f.write("Caption:\n")
                                    f.write(f'"{content["captions"]["primary"]}"\n\n')

                # Write hashtags
                if "hashtags" in result:
                    hashtags = result["hashtags"]
                    if isinstance(hashtags, dict):
                        # Combine all hashtag categories
                        all_hashtags = []
                        categories = ["trending", "niche", "branded"]
                        for category in categories:
                            if category in hashtags and isinstance(hashtags[category], list):
                                all_hashtags.extend(hashtags[category])
                        
                        if all_hashtags:
                            f.write("Suggested Hashtags:\n")
                            f.write(" ".join(all_hashtags) + "\n\n")

                # Write image URL if available
                if "image_url" in result and result["image_url"]:
                    f.write("Image:\n")
                    f.write(f"{result['image_url']}\n\n")

            self.logger.info(f"Content saved to: {txt_filename}")
            # Log the image prompt if available
            if "image_prompt" in result:
                self.logger.info(f"Image Prompt: {result['image_prompt']}")
            return txt_filename
            
        except Exception as e:
            self.logger.error(f"Failed to save content: {str(e)}", exc_info=True)
            raise Exception(f"Failed to save content: {str(e)}")

def setup_logging(idea):
    """Setup logging with a unique file for each idea."""
    # Create a timestamp and sanitize idea for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Remove invalid filename characters and limit length
    sanitized_idea = "".join(x for x in idea if x.isalnum() or x in (' ', '-', '_'))[:30]
    sanitized_idea = sanitized_idea.replace(' ', '_')
    
    # Create log filename
    log_filename = f"logs/content_generation_{timestamp}_{sanitized_idea}.log"
    
    # Create a logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # Remove any existing handlers
    logger.handlers = []
    
    # Create file handler
    file_handler = logging.FileHandler(log_filename, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Initial log entries
    logger.info(f"Log file created: {log_filename}")
    logger.info(f"Original idea: {idea}")
    
    return logger, log_filename

def main():
    try:
        print("\n=== Social Media Content Generator ===")
        print("\nShare your idea or text, and I'll help you create engaging social media content!")
        idea = input("\nEnter your idea or text: ")
        
        # Setup logging for this idea
        logger, log_filename = setup_logging(idea)
        
        # Add system information to log
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info("Loading environment variables...")
        load_dotenv(verbose=True)
        
        logger.info("Environment variables loaded:")
        logger.info(f"OPENAI_API_KEY present: {bool(os.getenv('OPENAI_API_KEY'))}")
        logger.info(f"OPENROUTER_API_KEY present: {bool(os.getenv('OPENROUTER_API_KEY'))}")
        
        logger.info("Starting Social Media Content Generator")
        generator = SocialMediaContentGenerator(logger)
        
        # Define available platforms
        platforms = ['instagram', 'twitter', 'linkedin', 'facebook', 'tiktok', 'youtube']
        print("\nWhich platforms would you like to create content for?")
        print("Available platforms:", ', '.join(platforms))
        print("You can select multiple platforms by separating them with commas")
        print("Example: instagram, twitter, linkedin")
        platform_input = input("Choose platforms: ").lower()
        selected_platforms = [p.strip() for p in platform_input.split(',')]
        
        # Validate selected platforms
        invalid_platforms = [p for p in selected_platforms if p not in platforms]
        if invalid_platforms:
            error_msg = f"Invalid platform(s): {', '.join(invalid_platforms)}. Please choose from: {', '.join(platforms)}"
            print(f"\n❌ {error_msg}")
            
            # Log user-facing error if generator is available
            if 'generator' in locals() and generator.db_logger:
                generator.db_logger.log_user_facing_error(
                    error_type='generation_error',
                    error_category='social_content',
                    error_message=error_msg
                )
            return
        
        logger.info(f"Selected platforms: {', '.join(selected_platforms)}")

        # Get available tones and audiences
        available_tones = generator.crew.get_available_tones()
        available_audiences = generator.crew.get_target_audiences()
        
        print("\nChoose your content tones (comma-separated):")
        print(f"Available tones: {', '.join(available_tones)}")
        tones_input = input("Enter tones (default: casual): ").lower() or "casual"
        tones = [t.strip() for t in tones_input.split(',')]
        logger.info(f"Selected tones: {tones}")
        
        print("\nChoose your target audiences (comma-separated):")
        print(f"Available audiences: {', '.join(available_audiences)}")
        audiences_input = input("Enter target audiences (default: general audience): ").lower() or "general audience"
        audiences = [a.strip() for a in audiences_input.split(',')]
        logger.info(f"Selected audiences: {audiences}")
        
        print("\nGenerating engaging content for your idea...")
        print(f"📝 Logging details to: {log_filename}")
        
        # Generate content for each selected platform
        results = {}
        for platform in selected_platforms:
            print(f"\n🎯 Generating content for {platform.upper()}")
            print("-" * 50)
            
            try:
                result = generator.generate_content(idea, platform, tones, audiences)
                results[platform] = result
                
                print(f"\n✨ Generation Times for {platform.upper()}:")
                print(f"📝 Content: {result['generation_time']}")
                if 'image_generation_time' in result:
                    print(f"🖼️ Image: {result['image_generation_time']}")
                
                print(f"\n📄 Output saved to: outputs/content_{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                
                # Display the content for this platform
                if "content" in result and isinstance(result["content"], dict):
                    content = result["content"]
                    print(f"\n=== Generated Content for {platform.upper()} ===")
                    
                    # Display Title
                    if "title" in content and content["title"]:
                        print(f"\n📋 Title:")
                        print(content["title"])
                    
                    # Display Introduction
                    if "introduction" in content and content["introduction"]:
                        print(f"\n🎬 Introduction:")
                        print(content["introduction"])
                    
                    # Display Main Points
                    if "main_points" in content and content["main_points"]:
                        print(f"\n📝 Main Points:")
                        print(content["main_points"])
                    
                    # Display Conclusion
                    if "conclusion" in content and content["conclusion"]:
                        print(f"\n🎯 Conclusion:")
                        print(content["conclusion"])
                    
                    # Display Caption
                    if "captions" in content and isinstance(content["captions"], dict):
                        if "primary" in content["captions"]:
                            print(f"\n💭 Caption:")
                            print(f'"{content["captions"]["primary"]}"')
                    
                    # Display Hashtags
                    if "hashtags" in result and isinstance(result["hashtags"], dict):
                        all_hashtags = []
                        for category in ["trending", "niche", "branded"]:
                            if category in result["hashtags"] and isinstance(result["hashtags"][category], list):
                                all_hashtags.extend(result["hashtags"][category])
                        if all_hashtags:
                            print(f"\n🏷️ Suggested Hashtags:")
                            print(" ".join(all_hashtags))
                    
                    # Display Image URL
                    if "image_url" in result and result["image_url"]:
                        print(f"\n🖼️ Generated Image:")
                        print(result["image_url"])
                
            except Exception as e:
                error_msg = f"Error generating content for {platform}: {str(e)}"
                print(f"\n❌ {error_msg}")
                logger.error(f"Failed to generate content for {platform}: {str(e)}")
                
                # Log user-facing error if generator is available
                if 'generator' in locals() and generator.db_logger:
                    generator.db_logger.log_user_facing_error(
                        error_type='generation_error',
                        error_category='social_content',
                        error_message=error_msg
                    )
                continue
        
        # Display summary
        print("\n=== Content Generation Summary ===")
        successful_platforms = [p for p in selected_platforms if p in results]
        failed_platforms = [p for p in selected_platforms if p not in results]
        
        if successful_platforms:
            print(f"\n✅ Successfully generated content for: {', '.join(successful_platforms)}")
        if failed_platforms:
            print(f"\n❌ Failed to generate content for: {', '.join(failed_platforms)}")
            
        logger.info("Content generation and display completed successfully")
        print(f"\n📋 Detailed logs available at: {log_filename}")
            
    except Exception as e:
        error_msg = f"Application error: {str(e)}"
        if 'logger' in locals():
            logger.error(error_msg, exc_info=True)
        print(f"\n❌ {error_msg}")
        
        # Log user-facing error if generator is available
        if 'generator' in locals() and generator.db_logger:
            generator.db_logger.log_user_facing_error(
                error_type='generation_error',
                error_category='social_content',
                error_message=error_msg
            )

if __name__ == "__main__":
    main() 