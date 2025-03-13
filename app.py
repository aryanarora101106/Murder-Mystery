from flask import Flask, render_template, request, jsonify
from google import genai
import os
import json

api_key = "AIzaSyAF0_D4EZVNFUQ8icwlOUNXvcd4WEiv5yE"

client = genai.Client(api_key=api_key)

app = Flask(__name__)

# Global variable to store the generated murder mystery
murder_mystery = None

def generate_murder_mystery():
    """Uses Gemini to generate a fully randomized murder mystery and parses JSON correctly."""
    prompt = """
    Generate a unique murder mystery scenario with:
    - A detailed crime scene description.
    - The name and background of the victim.
    - 3-5 suspects, each with unique motives.
    - The actual murderer (must be one of the suspects).
    - Clues available for investigation.

    Format the response as valid JSON without any additional explanations:
    {
      "crime_scene": "Description of the crime scene.",
      "victim": "Name and details of the victim.",
      "suspects": [
        {"name": "Suspect 1", "motive": "Motive description", "is_murderer": false},
        {"name": "Suspect 2", "motive": "Motive description", "is_murderer": true}
      ],
      "clues": ["Clue 1", "Clue 2", "Clue 3"]
    }
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )


    prompt2 =f'''you have this murder mystery : {response.text}, please use it to fill stuff in this json format and final output should be a structutred json, from this response remove backticks (''' ''') and json word, only formatted json should be output, 
    format:
        {
      "crime_scene": "Description of the crime scene.",
      "victim": "Name and details of the victim.",
      "suspects": [
        {"name": "Suspect 1", "motive": "Motive description", "is_murderer": false},
        {"name": "Suspect 2", "motive": "Motive description", "is_murderer": true}
      ],
      "clues": ["Clue 1", "Clue 2", "Clue 3"]
    } 
     
    '''

    response2 = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt2
    )

    cleaned_text = response2.text.split("```json")[1].split("```")[0].strip()
    # Extract JSON from Gemini's response
    try:
        print(cleaned_text)
        parsed_mystery = json.loads(cleaned_text)  # Ensure valid JSON parsing
        return parsed_mystery
    except json.JSONDecodeError:
        return {"error": "Failed to parse AI-generated mystery."}  # Handle invalid JSON case

@app.route("/")
def index():
    """Main game page with a new murder mystery case."""
    global murder_mystery
    murder_mystery = generate_murder_mystery()
    return render_template("index.html", mystery=murder_mystery)

@app.route("/interrogate", methods=["POST"])
def interrogate():
    """Handles interrogation of a selected suspect."""
    global murder_mystery
    suspect_name = request.json.get("suspect", "")
    user_question = request.json.get("question", "")

    # Find the suspect
    suspect = next((s for s in murder_mystery["suspects"] if s["name"] == suspect_name), None)
    if not suspect:
        return jsonify({"response": "That suspect is not part of this case."})

    prompt = f"""
    You are {suspect["name"]}, a suspect in a murder case. You must answer truthfully but avoid directly admitting guilt.
    If you are innocent, defend yourself while revealing important details.
    If you are guilty, provide misleading but plausible responses without outright lying.

    Crime Scene: {murder_mystery["crime_scene"]}
    Victim: {murder_mystery["victim"]}
    Your Motive: {suspect["motive"]}

    Detective asks: "{user_question}"
    Respond in a natural way, like a real suspect under interrogation.
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    return jsonify({"response": response.text})

@app.route("/vote", methods=["POST"])
def vote():
    """Handles the player's vote and reveals the answer."""
    global murder_mystery
    guessed_murderer = request.json.get("suspect", "")

    real_murderer = next((s["name"] for s in murder_mystery["suspects"] if s["is_murderer"]), None)

    if guessed_murderer == real_murderer:
        return jsonify({"result": f"Correct! The murderer was {real_murderer}."})
    else:
        return jsonify({"result": f"Wrong! The real murderer was {real_murderer}."})

if __name__ == "__main__":
    app.run(debug=True)
