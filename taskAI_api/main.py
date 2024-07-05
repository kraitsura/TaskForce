from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import os
import json
import re
import tiktoken
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allows the Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Constants for token limits
MAX_INPUT_TOKENS = 100  # Adjust as needed
MAX_OUTPUT_TOKENS = 200  # Adjust as needed
MODEL = "gpt-3.5-turbo"  # Specify the model you're using

class Task(BaseModel):
    description: str

class SubTask(BaseModel):
    description: str
    time_estimate: str

class StructureStep(BaseModel):
    step: str
    details: List[str]
    time_estimate: str

class SubTaskSelection(BaseModel):
    selected_subtasks: List[SubTask]

def num_tokens_from_string(string: str, model: str = MODEL) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def clean_json_string(json_string):
    # Remove any leading/trailing whitespace
    json_string = json_string.strip()
    
    # If the string is wrapped in ```, remove them
    json_string = re.sub(r'^```json\s*|\s*```$', '', json_string)
    
    # If the string starts with 'json', remove it
    json_string = re.sub(r'^json\s*', '', json_string)
    
    return json_string

def get_subtasks(task_description: str) -> List[SubTask]:
    if num_tokens_from_string(task_description) > MAX_INPUT_TOKENS:
        raise HTTPException(status_code=400, detail=f"Input exceeds maximum token limit of {MAX_INPUT_TOKENS}")
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an expert assistant with a talent for deconstructing complex tasks into clear, manageable subtasks. You generate multiple options for each step, allowing users to select the best approach and create a personalized task list to achieve their goals efficiently. Provide your response in JSON format."},
                {"role": "user", "content": f"""Break down the following task into subtasks, including an estimated time for each subtask in minutes. 
                Respond with a JSON array of objects, each with 'description' and 'time_estimate' fields. 
                For example: 
                [
                    {{"description": "Research venues", "time_estimate": "30 minutes"}},
                    {{"description": "Create guest list", "time_estimate": "20 minutes"}}
                ]
                Task: {task_description}"""}
            ],
            max_tokens=MAX_OUTPUT_TOKENS
        )
        json_string = clean_json_string(response.choices[0].message.content)
        subtasks_json = json.loads(json_string)
        return [SubTask(**subtask) for subtask in subtasks_json]
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing subtasks: {str(e)}")

def get_overall_structure(selected_subtasks: List[SubTask]) -> List[StructureStep]:
    subtasks_str = "\n".join([f"{task.description} - {task.time_estimate}" for task in selected_subtasks])
    if num_tokens_from_string(subtasks_str) > MAX_INPUT_TOKENS:
        raise HTTPException(status_code=400, detail=f"Input exceeds maximum token limit of {MAX_INPUT_TOKENS}")

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates structured plans. Provide your response in JSON format."},
                {"role": "user", "content": f"""You are an expert planner with the ability to create a cohesive overall structure and detailed plan for completing subtasks. 
                You generate multiple strategies for organizing and executing these steps, giving users the most effective approach to achieve their objectives smoothly and efficiently.
                Respond with a JSON array of objects, each with 'step', 'details' (an array of strings), and 'time_estimate' fields. Be elaborate in 'details' to provide a clear plan.
                For example:
                [
                    {{
                        "step": "Prepare venue",
                        "details": ["Book location", "Arrange seating", "Set up decorations"],
                        "time_estimate": "2 hours"
                    }},
                    {{
                        "step": "Organize catering",
                        "details": ["Choose menu", "Place order", "Arrange delivery"],
                        "time_estimate": "1 hour"
                    }}
                ]
                Subtasks:
                {subtasks_str}"""}
            ]
        )
        print(response.choices[0].message.content)
        json_string = clean_json_string(response.choices[0].message.content)
        structure_json = json.loads(json_string)
        return [StructureStep(**step) for step in structure_json]
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing overall structure: {str(e)}")

@app.post("/get_subtasks")
async def api_get_subtasks(task: Task):
    try:
        return get_subtasks(task.description)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"msg": str(e)}
        )

@app.post("/get_overall_structure")
async def api_get_overall_structure(selection: SubTaskSelection):
    try:
        return get_overall_structure(selection.selected_subtasks)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"msg": str(e)}
        )

def main():
    print("Welcome to the Task Breakdown Tool!")
    while True:
        task = input("\nEnter a task description (or 'quit' to exit): ")
        if task.lower() == 'quit':
            break
        
        try:
            subtasks = get_subtasks(task)
            
            print("\nHere are the subtasks with time estimates:")
            for i, subtask in enumerate(subtasks, 1):
                print(f"{i}. {subtask.description} - {subtask.time_estimate}")
            
            print("\nSelect subtasks to complete (enter numbers separated by commas, or 'all'):")
            selection = input()
            if selection.lower() == 'all':
                selected_subtasks = subtasks
                print("You've chosen to complete all subtasks.")
            else:
                selected_indices = [int(num.strip()) - 1 for num in selection.split(',')]
                selected_subtasks = [subtasks[i] for i in selected_indices]
                print(f"You've chosen to complete subtasks: {[i+1 for i in selected_indices]}")
            
            overall_structure = get_overall_structure(selected_subtasks)
            
            print("\nHere's your overall plan and structure:")
            for step in overall_structure:
                print(f"\n{step.step} - {step.time_estimate}")
                for detail in step.details:
                    print(f"  - {detail}")
        except HTTPException as e:
            print(f"An error occurred: {e.detail}")
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        main()