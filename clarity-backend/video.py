import subprocess
import os
import re
from dotenv import load_dotenv
import json
import time
import logging
from pydantic import BaseModel
import uuid
import shutil
import anthropic
import instructor
from prompts import system_prompt
from datetime import datetime

# Set up logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger('VideoGenerator')

# Load environment variables from .env file
load_dotenv()

# Set up Anthropic client with proper patching for prompt caching
client = instructor.Instructor(
    client=anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY']),
    create=instructor.patch(
        create=anthropic.Anthropic().beta.prompt_caching.messages.create,
        mode=instructor.Mode.ANTHROPIC_TOOLS,
    ),
    mode=instructor.Mode.ANTHROPIC_TOOLS,
)

def post_process_latex(manim_code):
    # Fix common LaTeX errors
    manim_code = manim_code.replace(r'\f\frac', r'\frac')
    manim_code = manim_code.replace(r'\\frac', r'\frac')
    manim_code = manim_code.replace(r'\"', r'"')
    manim_code = re.sub(r'\\\\frac', r'\\frac', manim_code)
    manim_code = re.sub(r'(\w+)\(', r'\1 (', manim_code)
    manim_code = re.sub(r'(\w+)=', r'\1 =', manim_code)
    manim_code = re.sub(
        r'MathTex\((.*?)\)', lambda m: f'MathTex(r"\\text{{{{{m.group(1)}}}}}")', manim_code)
    return manim_code

class ManimVisualization(BaseModel):
    manim_code: str
    description: str

def generate_manim_code(query, max_retries=3):
    """Generate manim code with retries using prompt caching"""
    for attempt in range(max_retries):
        try:
            start_time = time.time()
            logger.info(f"Attempt {attempt + 1} of {max_retries} to generate manim code")
            
            # Use create_with_completion to get both response and completion info
            response, completion = client.chat.completions.create_with_completion(
                model="claude-3-5-sonnet-20241022",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": system_prompt,
                                "cache_control": {"type": "ephemeral"}
                            },
                            {
                                "type": "text",
                                "text": f"Generate a concise but complete Manim visualization for: {query}. Keep the explanation focused and the code efficient to stay within token limits (4000 tokens)."
                            }
                        ]
                    }
                ],
                response_model=ManimVisualization,
                max_tokens=8000,
            )
            
            end_time = time.time()
            logger.info(f"Code generation took {end_time - start_time:.2f} seconds")
            
            # Log cache performance metrics
            logger.info(f"Cache metrics: {completion.usage}")
            
            # Check response validity
            if len(response.manim_code) < 100:
                raise Exception("Generated code is too short to be valid")
            
            if "if __name__ == " not in response.manim_code:
                raise Exception("Generated code appears to be truncated (missing main block)")
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating code on attempt {attempt + 1}: {str(e)}")
            if attempt == max_retries - 1:
                raise Exception("Failed to generate valid manim code after all retries")
            time.sleep(2)
    return None

def test_manim_code(manim_code_filename, output_file):
    """Test if the manim code runs without errors"""
    start_time = time.time()
    try:
        result = subprocess.run(
            ['manim', '-ql', '-o', output_file, manim_code_filename, '--disable_caching', '--write_to_movie'],
            check=True,
            capture_output=True,
            text=True
        )
        end_time = time.time()
        logger.info(f"Manim test took {end_time - start_time:.2f} seconds")
        logger.info("Manim test output:")
        logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        end_time = time.time()
        logger.error(f"Error testing Manim code (took {end_time - start_time:.2f} seconds): {e}")
        logger.error("Manim error output:")
        logger.error(e.stderr)
        return False

def generate_manim_visualization(query, output_folder='./output_videos', max_retries=3):
    total_start_time = time.time()
    logger.info(f"Starting visualization generation at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Delete the media folder if it exists
    media_folder = './media'
    if os.path.exists(media_folder):
        logger.info(f"Deleting existing media folder: {media_folder}")
        shutil.rmtree(media_folder)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    logger.info(f"Starting visualization generation for query: {query}")

    # Copy elepatch.py to output_videos folder
    copy_start_time = time.time()
    src_path = 'elepatch.py'
    dst_path = os.path.join(output_folder, 'elepatch.py')
    shutil.copy2(src_path, dst_path)
    logger.info(f"Copied elepatch.py in {time.time() - copy_start_time:.2f} seconds")

    # Create custom_voiceover_scene.py
    scene_start_time = time.time()
    custom_scene_path = os.path.join(output_folder, 'custom_voiceover_scene.py')
    with open(custom_scene_path, 'w') as f:
        f.write('''
from manim_voiceover import VoiceoverScene
from elepatch import ElevenLabsService

class CustomVoiceoverScene(VoiceoverScene):
    def set_speech_service(self, speech_service, create_subcaption=False):
        super().set_speech_service(speech_service, create_subcaption=create_subcaption)
''')
    logger.info(f"Created custom scene in {time.time() - scene_start_time:.2f} seconds")

    # Generate and test code with retries
    for attempt in range(max_retries):
        try:
            attempt_start_time = time.time()
            logger.info(f"Attempt {attempt + 1} of {max_retries}")
            
            # Generate code
            claude_start_time = time.time()
            claude_response = generate_manim_code(query)
            claude_end_time = time.time()
            logger.info(f"Code generation completed in {claude_end_time - claude_start_time:.2f} seconds")

            manim_code = claude_response.manim_code
            description = claude_response.description
            manim_code = post_process_latex(manim_code)

            # Save the code
            save_start_time = time.time()
            manim_code_filename = os.path.join(output_folder, 'generated_manim_code.py')
            with open(manim_code_filename, 'w') as f:
                f.write(manim_code)
            logger.info(f"Code saved in {time.time() - save_start_time:.2f} seconds")

            # Test the code
            test_start_time = time.time()
            logger.info("Testing Manim code...")
            random_id = str(uuid.uuid4())[:8]
            output_file = f'output_{random_id}'
            
            if test_manim_code(manim_code_filename, output_file):
                logger.info(f"Manim test successful in {time.time() - test_start_time:.2f} seconds")
                
                # Find the generated video
                video_quality = "480p15"
                video_dir = os.path.join("media", "videos", "generated_manim_code", video_quality)
                
                output_video_path = None
                for file in os.listdir(video_dir):
                    if file.endswith(".mp4"):
                        output_video_path = os.path.join(video_dir, file)
                        logger.info(f"Video file found at {output_video_path}")
                        break
                
                if output_video_path is None:
                    logger.warning("No video file found in the expected directory.")
                    continue

                # Save the description
                description_filename = os.path.join(output_folder, 'visualization_description.txt')
                with open(description_filename, 'w') as f:
                    f.write(description)
                logger.info(f"Description saved to {description_filename}")

                total_end_time = time.time()
                total_duration = total_end_time - total_start_time
                logger.info(f"Total visualization process completed in {total_duration:.2f} seconds")
                logger.info(f"Process completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                return output_video_path

            logger.error(f"Manim code test failed after {time.time() - test_start_time:.2f} seconds, retrying...")
            
        except Exception as e:
            attempt_duration = time.time() - attempt_start_time
            logger.error(f"Error on attempt {attempt + 1} (took {attempt_duration:.2f} seconds): {str(e)}")
            if attempt == max_retries - 1:
                logger.error("All attempts failed")
                return None
            logger.info("Retrying...")

    total_duration = time.time() - total_start_time
    logger.info(f"Process failed after {total_duration:.2f} seconds")
    return None

if __name__ == "__main__":
    start_time = time.time()
    output_path = generate_manim_visualization("demonstrate me how the ruy lopez chess opening works with both mine and the opponent's perspective.")
    end_time = time.time()
    
    if output_path:
        logger.info(f"Successfully generated video at: {output_path}")
    else:
        logger.error("Failed to generate visualization")
    
    logger.info(f"Total execution time: {end_time - start_time:.2f} seconds")
