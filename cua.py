import os
import time
from openai import OpenAI
from orgo import Computer
from dotenv import load_dotenv

load_dotenv()

def execute_action(computer_environment, action):
    """Map OpenAI computer actions to Orgo commands"""
    match action.type:
        case "click":
            x, y = action.x, action.y
            button = getattr(action, 'button', 'left')
            if button == "right":
                computer_environment.right_click(x, y)
            else:
                computer_environment.left_click(x, y)
                
        case "double_click":
            computer_environment.double_click(action.x, action.y)
            
        case "type":
            computer_environment.type(action.text)
            
        case "key" | "keypress":
            keys = action.keys if hasattr(action, 'keys') else [action.key]
            # Combine modifier keys into single command
            if len(keys) > 1:
                # Join keys with '+' for shortcuts like 'ctrl+c' or 'shift+p'
                key_combo = '+'.join(keys).lower()
                computer_environment.key(key_combo)
            else:
                for key in keys:
                    computer_environment.key(key)
                
        case "scroll":
            x, y = action.x, action.y
            scroll_y = getattr(action, 'scroll_y', 0)
            direction = "down" if scroll_y > 0 else "up"
            amount = abs(scroll_y) // 100
            computer_environment.scroll(direction, amount)
            
        case "wait":
            seconds = getattr(action, 'seconds', 2)
            computer_environment.wait(seconds)
            
        case "screenshot":
            pass  # Screenshot taken after each action

def run_computer_task(task, project_id=None):
    # Initialize OpenAI client and Orgo computer
    openai_client = OpenAI()
    computer_environment = Computer(project_id=project_id)
    
    # Configure computer tool
    tool_config = {
        "type": "computer_use_preview",
        "display_width": 1024,
        "display_height": 768,
        "environment": "linux"
    }
    
    # Enhanced task with double-click instructions (removed wait instruction)
    enhanced_task = f"""IMPORTANT: You are controlling a Linux desktop. 
- Always double-click desktop icons to open applications
- Use keyboard shortcuts as single commands (e.g., 'ctrl+c' not separate keys)

Task: {task}"""
    
    # Send task to OpenAI
    response = openai_client.responses.create(
        model="computer-use-preview",
        tools=[tool_config],
        input=[{
            "role": "user",
            "content": [{"type": "input_text", "text": enhanced_task}]
        }],
        reasoning={"summary": "concise"},
        truncation="auto"
    )
    
    # Execute actions until complete
    while True:
        actions = [item for item in response.output if item.type == "computer_call"]
        
        if not actions:
            print("✓ Task completed")
            break
        
        action = actions[0]
        print(f"→ {action.action.type}")
        execute_action(computer_environment, action.action)
        
        # Wait 1 second before taking screenshot (for UI to update)
        import time
        time.sleep(1)
        
        # Send screenshot back to OpenAI
        screenshot = computer_environment.screenshot_base64()
        response = openai_client.responses.create(
            model="computer-use-preview",
            previous_response_id=response.id,
            tools=[tool_config],
            input=[{
                "call_id": action.call_id,
                "type": "computer_call_output",
                "output": {
                    "type": "input_image",
                    "image_url": f"data:image/png;base64,{screenshot}"
                }
            }],
            truncation="auto"
        )
    
    return computer_environment

if __name__ == "__main__":
    computer_environment = run_computer_task(
        "can you open up libreoffice and insert some random data into a spreadsheet",
        project_id="computer-pvhvll"
    )
    # computer_environment.shutdown()  # Optional cleanup