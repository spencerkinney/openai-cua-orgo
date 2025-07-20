import time
from openai import OpenAI
from orgo import Computer
from dotenv import load_dotenv

load_dotenv()


def run_computer_task(task, project_id=None):
    client = OpenAI()
    computer = Computer(project_id=project_id)
    print(f"🖥️  Computer ID: {computer.project_id}")
    
    response = client.responses.create(
        model="computer-use-preview",
        tools=[{
            "type": "computer_use_preview",
            "display_width": 1024,
            "display_height": 768,
            "environment": "linux"
        }],
        input=[{
            "role": "user",
            "content": [{
                "type": "input_text", 
                "text": f"""IMPORTANT: You are controlling a Linux desktop. 
- Always double-click desktop icons to open applications
- Use keyboard shortcuts as single commands (e.g., 'ctrl+c' not separate keys)

Task: {task}"""
            }]
        }],
        reasoning={"summary": "concise"},
        truncation="auto"
    )
    
    while True:
        for item in response.output:
            if item.type == "reasoning" and hasattr(item, "summary"):
                for summary in item.summary:
                    if hasattr(summary, "text"):
                        print(f"💭 {summary.text}")
            elif item.type == "text" and hasattr(item, "text"):
                print(f"💬 {item.text}")
        
        actions = [item for item in response.output if item.type == "computer_call"]
        if not actions:
            print("✓ Task completed")
            break
            
        action = actions[0]
        print(f"→ {action.action.type}")
        
        execute_action(computer, action.action)
        time.sleep(1)
        
        screenshot = computer.screenshot_base64()
        response = client.responses.create(
            model="computer-use-preview",
            previous_response_id=response.id,
            tools=[{
                "type": "computer_use_preview",
                "display_width": 1024,
                "display_height": 768,
                "environment": "linux"
            }],
            input=[{
                "call_id": action.call_id,
                "type": "computer_call_output",
                "output": {
                    "type": "input_image",
                    "image_url": f"data:image/png;base64,{screenshot}"
                }
            }],
            reasoning={"summary": "concise"},
            truncation="auto"
        )
    
    return computer


def execute_action(computer, action):
    match action.type:
        case "click":
            if getattr(action, 'button', 'left') == "right":
                computer.right_click(action.x, action.y)
            else:
                computer.left_click(action.x, action.y)
                
        case "double_click":
            computer.double_click(action.x, action.y)
            
        case "type":
            computer.type(action.text)
            
        case "key" | "keypress":
            keys = getattr(action, 'keys', [getattr(action, 'key', [])])
            if len(keys) > 1:
                computer.key('+'.join(keys).lower())
            else:
                for key in keys:
                    computer.key(key)
                    
        case "scroll":
            scroll_y = getattr(action, 'scroll_y', 0)
            direction = "down" if scroll_y > 0 else "up"
            computer.scroll(direction, abs(scroll_y) // 100)
            
        case "wait":
            computer.wait(getattr(action, 'seconds', 2))
            
        case "screenshot":
            pass


if __name__ == "__main__":
    computer = run_computer_task("open a terminal and run 'ls -l'")
    computer.destroy()