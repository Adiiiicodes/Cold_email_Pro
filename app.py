from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    if request.method == 'POST':
        # Here, you can process the form data and generate an email
        # For simplicity, I'm just passing a placeholder response
        generated_email = "This is a generated email content."
        skills_match = 85  # Placeholder value
        experience_match = 90  # Placeholder value
        suggestions = ["Improve your experience section", "Add more skills"]
        return render_template('response.html', generated_email=generated_email, skills_match=skills_match, 
                               experience_match=experience_match, suggestions=suggestions)
    return render_template('generate.html')

@app.route('/guidelines')
def guidelines():
    return render_template('guidelines.html')

@app.route('/docs')
def docs():
    return render_template('docs.html')

@app.route('/features')
def features():
    return render_template('features.html')

if __name__ == '__main__':
    app.run(debug=True)
