#!/usr/bin/env python3
"""
Example usage of Short Story Crew
Demonstrates the enhanced system with genre-based story generation.
"""

import os
import sys

from config import Config
from crew import ShortStoryCrew
from utils.logger import log_error, log_info, log_user_interaction, setup_logging


def run_example():
    """Run the example with predefined story ideas and genres."""

    # Example story ideas paired with suggested genres
    example_combinations = [
        (
            "A lonely robot discovers an abandoned garden and learns to grow flowers",
            "sci-fi",
        ),
        (
            "Two strangers get stuck in an elevator and share their deepest fears",
            "romance",
        ),
        ("A time traveler accidentally prevents their parents from meeting", "sci-fi"),
        ("An AI tries to understand human love by reading poetry", "romance"),
        ("A child's drawing comes to life for exactly 15 seconds", "kids"),
        ("A detective finds a clue in their own reflection", "mystery"),
        ("A vampire learns to bake cupcakes", "comedy"),
        ("A dragon discovers they're afraid of heights", "fantasy"),
        ("Two ninjas compete in a cooking contest", "anime"),
        ("A ghost helps someone overcome their fear of death", "horror"),
    ]

    print("🎬 Short Story Crew - Example Demo")
    print("=" * 60)
    print("\nAvailable example combinations (idea + genre):")

    for i, (idea, genre) in enumerate(example_combinations, 1):
        print(f"  {i:2d}. [{genre.upper()}] {idea}")

    print(f"  {len(example_combinations) + 1:2d}. Enter your own idea and genre")

    try:
        choice = input(
            f"\nSelect a combination (1-{len(example_combinations) + 1}): "
        ).strip()

        if choice.isdigit():
            choice_num = int(choice)
            if 1 <= choice_num <= len(example_combinations):
                selected_idea, selected_genre = example_combinations[choice_num - 1]
            elif choice_num == len(example_combinations) + 1:
                selected_idea = input("Enter your story idea: ").strip()
                if not selected_idea:
                    print("❌ No idea provided. Using default.")
                    selected_idea, selected_genre = example_combinations[0]
                else:
                    print(
                        "\nAvailable genres:",
                        ", ".join(sorted(Config.SUPPORTED_GENRES)),
                    )
                    selected_genre = input("Enter genre: ").strip().lower()
                    if selected_genre not in Config.SUPPORTED_GENRES:
                        print("❌ Invalid genre. Using 'drama' as default.")
                        selected_genre = "drama"
            else:
                print("❌ Invalid choice. Using default combination.")
                selected_idea, selected_genre = example_combinations[0]
        else:
            print("❌ Invalid input. Using default combination.")
            selected_idea, selected_genre = example_combinations[0]

        log_user_interaction(
            "Example started", f"Idea: {selected_idea[:30]}..., Genre: {selected_genre}"
        )

        print(f"\n🚀 Generating {selected_genre.upper()} story for: '{selected_idea}'")
        print("🎭 Director is setting creative vision...")
        print("✍️  Writer is crafting the narrative...")
        print("📝 Proofreader is refining the story...")
        print("🎨 Art Designer is creating visual descriptions...")
        print("📋 Coordinator is assembling final script...")
        print("\n⏳ This may take a few minutes...")
        print("-" * 60)

        # Create and run the crew
        crew = ShortStoryCrew()
        result = crew.create_story(selected_idea, selected_genre)

        # Display results
        print("\n" + "=" * 70)
        print(f"🎭 GENERATED {selected_genre.upper()} STORY SCRIPT")
        print("=" * 70)
        print(f"Original Idea: {selected_idea}")
        print(f"Genre: {selected_genre.title()}")
        print("-" * 70)
        print(result)
        print("=" * 70)

        # Save to file
        timestamp = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("outputs", exist_ok=True)

        # Generate filename with genre
        genre_clean = selected_genre.replace(" ", "_").replace("-", "_")
        filename = f"outputs/example_{genre_clean}_{timestamp}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"Example {selected_genre.title()} Story Script\n")
            f.write(f"{'=' * 60}\n")
            f.write(f"Original Idea: {selected_idea}\n")
            f.write(f"Genre: {selected_genre.title()}\n")
            f.write(
                f"Generated on: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            f.write(f"{'=' * 60}\n\n")
            f.write(str(result))

        log_info(f"Example completed successfully: {filename}")

        print(f"\n📄 {selected_genre.title()} story saved to: {filename}")
        print("\n✨ Example completed successfully!")

    except KeyboardInterrupt:
        print("\n\n👋 Example interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error running example: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Make sure you've set your OPENAI_API_KEY")
        print("2. Check your internet connection")
        print("3. Ensure all dependencies are installed")
        sys.exit(1)


def main():
    """Main function."""
    # Set up logging
    setup_logging()
    log_info("Example script started")

    try:
        # Check if API key is set
        api_key = Config.get_api_key()
        if not api_key:
            provider = Config.LLM_PROVIDER.upper()
            key_name = f"{provider}_API_KEY"
            print(
                f"❌ Error: {key_name} environment variable is required for {provider} provider"
            )
            print("\n💡 To set it up:")
            print(f"   1. Create a .env file with: {key_name}=your_key_here")
            print(f"   2. Or run: export {key_name}=your_key_here")
            print("   3. Or use the setup script: python setup.py")
            sys.exit(1)

        log_info(f"Using {Config.LLM_PROVIDER} provider for example")
        run_example()

    except ImportError as e:
        log_error(f"Import error: {e}", exc_info=True)
        print(f"❌ Import error: {e}")
        print("\n💡 Try running: pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        log_user_interaction("Example interrupted by user")
        print("\n\n👋 Example interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        log_error(f"Unexpected error in example: {e}", exc_info=True)
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
