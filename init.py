from flask import Flask, render_template
from flask_frozen import Freezer
import shutil
import json
import os

app = Flask(__name__)

# Create a Freezer instance
freezer = Freezer(app)

data = []
id_to_question = {}

def load_data():
    global data, id_to_question
    data_folder = 'data'

    # Loop through every file in the data folder
    for filename in os.listdir(data_folder):
        file_path = os.path.join(data_folder, filename)
        # Check if the path is a file and if the file is a JSON file
        if os.path.isfile(file_path) and filename.endswith('.json'):
            try:
                with open(file_path) as json_file:
                    # Load the JSON data from the file and add it to the data list
                    item = json.load(json_file)
                    data.append(item)
                    # Add the question to the id_to_question dictionary
                    id_to_question[item['id']] = item['question']
            except json.JSONDecodeError:
                print(f"Error: Could not decode the JSON file {filename}")

    # Add the related questions to each item in the data
    for item in data:
        related_questions = [id_to_question.get(related_id, 'None') for related_id in item.get('related_id', [])]
        item['related_questions'] = ', '.join(related_questions) if related_questions else 'None'

@app.route('/')
def home():
    return render_template('index.html', data=data)

# Add a route for the home page for tags
@app.route('/tags/index.html')
def tags_index():
    tags = set(tag for item in data for tag in item.get('tags', []))
    return render_template('tags.html', tags=tags)

# Add a route for each item in the data
@app.route('/tags/<tag>.html')
def tags(tag):
    filtered_data = [item for item in data if tag in item.get('tags', [])]
    return render_template('index.html', data=filtered_data)

@app.route('/tags.html')
def tag_list():
    tags = set(tag for item in data for tag in item.get('tags', []))
    return render_template('tags.html', tags=tags)

if __name__ == '__main__':
    load_data()
    # Delete the build directory if it exists
    if os.path.exists('build'):
        shutil.rmtree('build')
    # app.run(debug=True)
    freezer.freeze()

