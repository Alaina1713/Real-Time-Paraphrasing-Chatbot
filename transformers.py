import random
import re
import nltk
from nltk.corpus import wordnet
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
import os
import pdfplumber

# Initialize NLTK
nltk.download('wordnet')
nltk.download('omw-1.4')

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max file size 16MB
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf'}

# Your stopwords list
stop_words = set([
    'the', 'and', 'to', 'of', 'a', 'in', 'that', 'it', 'for', 'on', 'with', 'as', 'by', 'an', 'be', 'at', 'this', 'from',
    'was', 'is', 'were', 'are', 'have', 'has', 'had', 'will', 'shall', 'should', 'may', 'might', 'could', 'can', 'i', 'you',
    'he', 'she', 'they', 'we', 'which', 'who', 'what', 'where', 'when', 'why', 'how', 'not', 'up', 'down', 'all', 'any',
    'each', 'few', 'more', 'most', 'some', 'these', 'those', 'here', 'there', 'too', 'very', 'much', 'so', 'just', 'like',
    'than', 'about', 'into', 'after', 'before', 'during', 'while', 'such', 'no', 'yes', 'or', 'nor', 'but'
])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "".join(page.extract_text() or "" for page in pdf.pages)
        return text.strip()
    except Exception as e:
        print(f"Error during PDF extraction: {e}")
        return None

def clean_word(word):
    """Remove punctuation from words for processing."""
    return re.sub(r'[^\w\s]', '', word)

def get_synonym(word, level='easy'):
    """Fetch a synonym from WordNet based on the complexity level."""
    clean = clean_word(word)
    
    if clean.lower() in stop_words or not clean:
        return word  # Skip stopwords and empty words
    
    # Get synonyms using WordNet
    synonyms = wordnet.synsets(clean)
    if not synonyms:
        return word  # If no synonyms found, return the original word

    # Easy Level: Use the first synonym
    if level == 'easy':
        return synonyms[0].lemmas()[0].name() if synonyms else word

    # Medium Level: Use a less common synonym
    elif level == 'medium' and len(synonyms) > 1:
        return random.choice(synonyms[1:]).lemmas()[0].name()

    # Hard Level: Use the least common or complex synonym
    elif level == 'hard' and len(synonyms) > 2:
        return random.choice(synonyms[2:]).lemmas()[0].name()

    return word  # Fallback

def paraphrase_text_with_synonyms(text, level='easy'):
    """Paraphrase text using synonyms based on the given level."""
    words = text.split()  # Split by whitespace
    paraphrased_words = [get_synonym(word, level) for word in words]
    return ' '.join(paraphrased_words)

@app.route('/')
def home():
    return render_template('main.html', original_text="", easy_paraphrased_text="", medium_paraphrased_text="", 
                           hard_paraphrased_text="")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files or not request.files['file'].filename:
        return render_template('main.html', error="No file uploaded.")
    
    file = request.files['file']
    
    if file.filename == '':
        return render_template('main.html', error="No file selected.")
    
    if not allowed_file(file.filename):
        return render_template('main.html', error="Invalid file format. Please upload a PDF.")
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Extract text from the uploaded PDF
        original_text = extract_text_from_pdf(file_path)

        if not original_text:
            return render_template('main.html', error="No text found in the uploaded PDF.")
        
        # Generate paraphrased versions
        easy_paraphrased_text = paraphrase_text_with_synonyms(original_text, 'easy')
        medium_paraphrased_text = paraphrase_text_with_synonyms(original_text, 'medium')
        hard_paraphrased_text = paraphrase_text_with_synonyms(original_text, 'hard')

        return render_template('main.html',
                               original_text=original_text,
                               easy_paraphrased_text=easy_paraphrased_text,
                               medium_paraphrased_text=medium_paraphrased_text,
                               hard_paraphrased_text=hard_paraphrased_text)

@app.route('/help')
def help_page():
    return render_template('help.html')

@app.route('/settings')
def settings_page():
    return render_template('settings.html')

@app.route('/chatbot')
def chatbot_page():
    return render_template('chatbot.html')

@app.route('/history')
def history_page():
    return render_template('history.html')

if __name__ == '__main__':
    app.run(debug=True)
