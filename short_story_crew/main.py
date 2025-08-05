#!/usr/bin/env python3
"""
Short Story Crew - AI-powered story generation system
Enhanced with logging and genre-based story generation
"""

import argparse
import os
import sys
from datetime import datetime

from config import Config
from crew import ShortStoryCrew
from utils.logger import log_error, log_info, log_user_interaction, setup_logging


def save_output(result: str, user_idea: str, genre: str) -> str:
    """Save the generated story to a file with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create output directory if it doesn't exist
    os.makedirs("outputs", exist_ok=True)

    # Generate filename based on user idea and genre (sanitized)
    idea_snippet = "".join(
        c if c.isalnum() or c in (" ", "-", "_") else "" for c in user_idea
    )[:40]
    idea_snippet = idea_snippet.strip().replace(" ", "_")
    genre_clean = genre.replace(" ", "_").replace("-", "_")
    filename = f"outputs/story_{genre_clean}_{idea_snippet}_{timestamp}.txt"

    # Save the result
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"Generated {genre.title()} Story Script\n")
            f.write(f"{'=' * 60}\n")
            f.write(f"Original Idea: {user_idea}\n")
            f.write(f"Genre: {genre.title()}\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'=' * 60}\n\n")
            f.write(str(result))

        log_info(f"Story saved successfully to {filename}")
        return filename

    except Exception as e:
        log_error(f"Error saving story to file: {str(e)}", exc_info=True)
        raise


def select_genre() -> str:
    """Interactive genre selection with suggestions."""
    print("\n🎭 Genre Selection")
    print("=" * 30)

    # Group genres for better presentation
    genre_groups = {
        "Popular": ["anime", "romance", "comedy", "horror", "sci-fi", "drama"],
        "Family": ["kids", "family", "motivational", "educational"],
        "Action": ["action", "adventure", "thriller", "mystery"],
        "Creative": ["fantasy", "experimental", "musical", "documentary"],
        "Classic": ["noir", "western", "biographical", "historical"],
    }

    print("Available genres by category:")
    for category, genres in genre_groups.items():
        print(f"\n  {category}: {', '.join(genres)}")

    while True:
        genre_input = (
            input("\n💡 Enter genre (or 'list' for full list): ").strip().lower()
        )

        if genre_input in ["quit", "exit", "q"]:
            return None
        elif genre_input == "list":
            print(
                f"\nAll supported genres: {', '.join(sorted(Config.SUPPORTED_GENRES))}"
            )
            continue
        elif genre_input in Config.SUPPORTED_GENRES:
            log_user_interaction("Genre selected", f"Genre: {genre_input}")
            return genre_input
        elif genre_input:
            # Try to find partial matches
            matches = [
                g
                for g in Config.SUPPORTED_GENRES
                if genre_input in g or g in genre_input
            ]
            if len(matches) == 1:
                print(f"Did you mean '{matches[0]}'? Using that.")
                log_user_interaction(
                    "Genre auto-corrected", f"Input: {genre_input}, Used: {matches[0]}"
                )
                return matches[0]
            elif len(matches) > 1:
                print(f"Multiple matches found: {', '.join(matches)}")
                print("Please be more specific.")
            else:
                print(f"❌ Genre '{genre_input}' not supported.")
                print(f"Supported genres: {', '.join(sorted(Config.SUPPORTED_GENRES))}")
        else:
            print("Please enter a valid genre.")


def interactive_mode():
    """Run the application in interactive mode."""
    print("\n🎬 Welcome to Short Story Crew!")
    print("=" * 60)
    print("Generate compelling 15-second short stories with genre-specific AI agents")
    print("Type 'quit' or 'exit' to end the session\n")

    log_user_interaction("Started interactive mode")

    try:
        crew = ShortStoryCrew()
    except Exception as e:
        log_error(f"Failed to initialize crew: {str(e)}", exc_info=True)
        print(f"❌ Error initializing crew: {str(e)}")
        return

    while True:
        try:
            # Get story idea
            user_idea = input("\n💡 Enter your story idea (1-2 lines): ").strip()

            if user_idea.lower() in ["quit", "exit", "q"]:
                log_user_interaction("User quit from idea input")
                print("\n👋 Thanks for using Short Story Crew!")
                break

            if not user_idea:
                print("❌ Please enter a valid story idea.")
                continue

            log_user_interaction("Story idea entered", f"Idea: {user_idea[:50]}...")

            # Get genre
            genre = select_genre()
            if genre is None:
                log_user_interaction("User quit from genre selection")
                print("\n👋 Thanks for using Short Story Crew!")
                break

            print(f"\n🚀 Creating {genre.title()} story from idea: '{user_idea}'")
            print("🎭 Director is setting creative vision...")
            print("✍️  Writer is crafting the narrative...")
            print("📝 Proofreader is refining the story...")
            print("🎨 Art Designer is creating visual descriptions...")
            print("📋 Coordinator is assembling final script...")
            print("\n⏳ This may take a few minutes...")

            log_info(
                f"Starting story generation: Genre={genre}, Idea={user_idea[:50]}..."
            )

            result = crew.create_story(user_idea, genre)

            # Save output
            filename = save_output(str(result), user_idea, genre)

            print(f"\n📄 {genre.title()} story saved to: {filename}")
            print(f"\n{'='*60}")
            print(f"GENERATED {genre.upper()} STORY SCRIPT:")
            print(f"{'='*60}")
            print(result)
            print(f"{'='*60}")

            log_user_interaction(
                "Story generation completed", f"Genre: {genre}, File: {filename}"
            )

            # Ask if user wants to continue
            continue_choice = (
                input("\n🔄 Generate another story? (y/n): ").strip().lower()
            )
            if continue_choice not in ["y", "yes"]:
                log_user_interaction("User chose to end session")
                print("\n👋 Thanks for using Short Story Crew!")
                break

        except KeyboardInterrupt:
            log_user_interaction("Session interrupted by user")
            print("\n\n👋 Session interrupted. Goodbye!")
            break
        except Exception as e:
            log_error(f"Error during story generation: {str(e)}", exc_info=True)
            print(f"\n❌ Error: {str(e)}")
            print("Please try again with a different idea or genre.")


def single_run_mode(user_idea: str, genre: str = None):
    """Run the application for a single story generation."""
    try:
        print("\n🎬 Short Story Crew - Single Run Mode")
        print("=" * 60)

        log_user_interaction("Single run mode started", f"Idea: {user_idea[:50]}...")

        # Get genre if not provided
        if not genre:
            genre = select_genre()
            if genre is None:
                log_user_interaction("User quit from genre selection in single run")
                print("❌ Genre selection cancelled.")
                return
        else:
            if genre.lower() not in Config.SUPPORTED_GENRES:
                log_error(f"Unsupported genre in single run: {genre}")
                print(f"❌ Unsupported genre: {genre}")
                print(f"Supported genres: {', '.join(sorted(Config.SUPPORTED_GENRES))}")
                sys.exit(1)
            genre = genre.lower()

        log_info(f"Single run generation: Genre={genre}, Idea={user_idea[:50]}...")

        crew = ShortStoryCrew()
        result = crew.create_story(user_idea, genre)

        # Save output
        filename = save_output(str(result), user_idea, genre)

        print(f"\n📄 {genre.title()} story saved to: {filename}")
        print(f"\n{'='*60}")
        print(f"GENERATED {genre.upper()} STORY SCRIPT:")
        print(f"{'='*60}")
        print(result)
        print(f"{'='*60}")

        log_user_interaction(
            "Single run completed successfully", f"Genre: {genre}, File: {filename}"
        )

    except Exception as e:
        log_error(f"Error in single run mode: {str(e)}", exc_info=True)
        print(f"\n❌ Error generating story: {str(e)}")
        sys.exit(1)


def show_crew_info():
    """Display information about the crew members."""
    log_user_interaction("Crew info requested")

    try:
        crew = ShortStoryCrew()
        info = crew.get_crew_info()

        print("\n🎭 Short Story Crew Information")
        print("=" * 60)

        print("\n👥 Crew Members:")
        for member, details in info["crew_members"].items():
            print(f"\n  🎯 {details['role']}")
            print(f"     {details['responsibility']}")

        print(f"\n🎨 Supported Genres ({len(info['supported_genres'])}):")
        # Group genres for better display
        genres = sorted(info["supported_genres"])
        for i in range(0, len(genres), 6):
            genre_line = ", ".join(genres[i : i + 6])
            print(f"     {genre_line}")

        print("\n🤖 AI Models by Crew Member:")
        for member, model in info["llm_models"].items():
            print(f"     {member}: {model}")

        print(f"\n⚙️  Process: {info['process']}")
        print(f"📋 Output: {info['output']}")

        print("\n🔧 Configuration:")
        print(f"     LLM Provider: {Config.LLM_PROVIDER}")
        print(f"     Max Story Duration: {Config.MAX_STORY_DURATION} seconds")
        print(f"     Log Level: {Config.LOG_LEVEL}")
        print()

    except Exception as e:
        log_error(f"Error displaying crew info: {str(e)}", exc_info=True)
        print(f"❌ Error displaying crew information: {str(e)}")


def main():
    """Main entry point of the application."""
    parser = argparse.ArgumentParser(
        description="Generate 15-second genre-specific short stories using AI crew",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                           # Interactive mode
  python main.py --idea "A robot falls in love" --genre romance  # Single run with genre
  python main.py --idea "A time traveler" --genre sci-fi         # Sci-fi story
  python main.py --info                                    # Show crew information
  python main.py --genres                                  # List supported genres

Supported Genres:
  {', '.join(sorted(Config.SUPPORTED_GENRES[:10]))}...
  (Use --genres to see all)
        """,
    )

    parser.add_argument("--idea", type=str, help="Story idea for single run mode")

    parser.add_argument(
        "--genre",
        type=str,
        help="Genre for the story (e.g., anime, horror, romance). Use --genres to see all supported genres",
    )

    parser.add_argument(
        "--info",
        action="store_true",
        help="Show detailed information about the crew members and configuration",
    )

    parser.add_argument(
        "--genres", action="store_true", help="List all supported genres"
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=Config.LOG_LEVEL,
        help="Set logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Set up logging with specified level
    setup_logging(args.log_level)
    log_info(f"Application started with log level: {args.log_level}")

    try:
        # Handle commands that don't require API keys first
        if args.genres:
            print(f"\n🎭 Supported Genres ({len(Config.SUPPORTED_GENRES)}):")
            print("=" * 40)
            for i, genre in enumerate(sorted(Config.SUPPORTED_GENRES), 1):
                print(f"  {i:2d}. {genre}")
            print()
            return

        # Check if required environment variables are set for commands that need them
        api_key = Config.get_api_key()
        if not api_key:
            provider = Config.LLM_PROVIDER.upper()
            key_name = f"{provider}_API_KEY"
            log_error(f"Missing API key: {key_name}")
            print(
                f"❌ Error: {key_name} environment variable is required for {provider} provider"
            )
            print("Please set it in your environment or create a .env file")
            sys.exit(1)

        if args.info:
            show_crew_info()

        elif args.idea:
            if args.genre and args.genre.lower() not in Config.SUPPORTED_GENRES:
                log_error(f"Unsupported genre provided: {args.genre}")
                print(f"❌ Unsupported genre: {args.genre}")
                print("Use --genres to see all supported genres")
                sys.exit(1)
            single_run_mode(args.idea, args.genre)

        else:
            interactive_mode()

    except KeyboardInterrupt:
        log_user_interaction("Application interrupted by user")
        print("\n👋 Application interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        log_error(f"Application error: {str(e)}", exc_info=True)
        print(f"❌ Application error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
