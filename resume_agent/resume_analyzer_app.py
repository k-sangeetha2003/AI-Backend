import os
import re
import csv
import PyPDF2
from docx import Document
from typing import Dict, List, Tuple
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class ResumeShortlistingAgent:
    def __init__(self):
        # Job requirements - customize these for your specific job
        self.required_skills = [
            'python', 'javascript', 'html', 'css', 'react', 'node.js'
        ]
        
        self.preferred_skills = [
            'aws', 'docker', 'git', 'agile', 'sql', 'mongodb', 'express'
        ]
        
        self.must_keywords = [
            'experience', 'development', 'software', 'project'
        ]
        
        self.avoid_keywords = [
            'intern', 'student', 'fresh graduate', 'entry level'
        ]
        
        self.required_years = 3
        
        # Skills keywords for detection
        self.skills_keywords = {
            'programming': ['python', 'java', 'javascript', 'html', 'css', 'sql', 'react', 'node.js', 'git', 'c++', 'c#', 'php', 'ruby', 'go', 'rust'],
            'data_science': ['machine learning', 'data analysis', 'pandas', 'numpy', 'excel', 'statistics', 'tensorflow', 'pytorch', 'scikit-learn'],
            'design': ['ui/ux', 'photoshop', 'figma', 'sketch', 'illustrator', 'adobe xd', 'invision'],
            'business': ['project management', 'leadership', 'marketing', 'sales', 'strategy', 'agile', 'scrum'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'ci/cd'],
            'database': ['mysql', 'postgresql', 'mongodb', 'redis', 'oracle', 'sql server']
        }

    def extract_text(self, file_path: str) -> str:
        """Extract text from PDF, DOCX, or TXT files"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext == '.pdf':
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text()
                    return text.lower()
                    
            elif file_ext == '.docx':
                doc = Document(file_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text.lower()
                
            elif file_ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read().lower()
                    
            else:
                print(f"Unsupported file format: {file_ext}")
                return ""
                
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return ""

    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text"""
        skills = []
        
        # Check for skills in different categories
        for category, skill_list in self.skills_keywords.items():
            for skill in skill_list:
                if skill in text:
                    skills.append(skill)
        
        # Also check for skills mentioned in the required/preferred lists
        for skill in self.required_skills + self.preferred_skills:
            if skill in text:
                skills.append(skill)
        
        return list(set(skills))  # Remove duplicates

    def extract_experience_years(self, text: str) -> int:
        """Extract years of experience from resume text"""
        # Look for patterns like "X years of experience" or "X years"
        patterns = [
            r'(\d+)\s+years?\s+of\s+experience',
            r'(\d+)\s+years?\s+experience',
            r'experience.*?(\d+)\s+years?',
            r'(\d+)\s+years?.*?experience'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return int(matches[0])
        
        # If no specific years found, look for job duration patterns
        duration_patterns = [
            r'(\d{4})\s*-\s*(\d{4})',  # 2020-2023
            r'(\d{4})\s*to\s*(\d{4})',  # 2020 to 2023
        ]
        
        total_years = 0
        for pattern in duration_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    start_year = int(match[0])
                    end_year = int(match[1])
                    total_years += (end_year - start_year)
                except:
                    continue
        
        return total_years if total_years > 0 else 0

    def check_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """Check which keywords are present in the text"""
        found_keywords = []
        for keyword in keywords:
            if keyword in text:
                found_keywords.append(keyword)
        return found_keywords

    def calculate_score(self, required_skills_matched: int, preferred_skills_matched: int, 
                       experience_years: int, must_keywords: List[str], avoid_keywords: List[str]) -> float:
        """Calculate overall score (0-100)"""
        
        # Required skills score (40% weight)
        required_score = (required_skills_matched / len(self.required_skills)) * 40
        
        # Preferred skills score (20% weight)
        preferred_score = (preferred_skills_matched / len(self.preferred_skills)) * 20
        
        # Experience score (30% weight)
        if experience_years >= self.required_years:
            experience_score = 30
        elif experience_years > 0:
            experience_score = (experience_years / self.required_years) * 30
        else:
            experience_score = 0
        
        # Must keywords score (10% weight)
        must_keyword_score = (len(must_keywords) / len(self.must_keywords)) * 10
        
        # Avoid keywords penalty
        avoid_penalty = len(avoid_keywords) * 5
        
        total_score = required_score + preferred_score + experience_score + must_keyword_score - avoid_penalty
        
        return max(0, min(100, total_score))  # Clamp between 0 and 100

    def analyze_resume(self, file_path: str) -> Dict:
        """Analyze a single resume and return results"""
        text = self.extract_text(file_path)
        if not text:
            return None
        
        # Extract information
        skills = self.extract_skills(text)
        experience_years = self.extract_experience_years(text)
        must_keywords = self.check_keywords(text, self.must_keywords)
        avoid_keywords = self.check_keywords(text, self.avoid_keywords)
        
        # Count matched skills
        required_skills_matched = sum(1 for skill in skills if skill in self.required_skills)
        preferred_skills_matched = sum(1 for skill in skills if skill in self.preferred_skills)
        
        # Calculate score
        score = self.calculate_score(required_skills_matched, preferred_skills_matched, 
                                   experience_years, must_keywords, avoid_keywords)
        
        return {
            'filename': os.path.basename(file_path),
            'score': round(score, 2),
            'required_skills_matched': required_skills_matched,
            'preferred_skills_matched': preferred_skills_matched,
            'experience_years': experience_years,
            'must_keywords': must_keywords,
            'avoid_keywords': avoid_keywords,
            'all_skills': skills,
            'total_required_skills': len(self.required_skills),
            'total_preferred_skills': len(self.preferred_skills)
        }

    def analyze_all_resumes(self, folder_path: str) -> List[Dict]:
        """Analyze all resumes in the folder and return results"""
        results = []
        
        if not os.path.exists(folder_path):
            return results
        
        # Get all resume files
        resume_files = []
        for file in os.listdir(folder_path):
            if file.lower().endswith(('.pdf', '.docx', '.txt')):
                resume_files.append(os.path.join(folder_path, file))
        
        # Analyze each resume
        for file_path in resume_files:
            result = self.analyze_resume(file_path)
            if result:
                results.append(result)
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results

# Global agent instance
agent = ResumeShortlistingAgent()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page with upload form and results"""
    # Analyze existing resumes
    results = agent.analyze_all_resumes('resumes')
    
    # Also analyze uploaded resumes
    upload_results = agent.analyze_all_resumes('uploads')
    
    # Combine and sort all results
    all_results = results + upload_results
    all_results.sort(key=lambda x: x['score'], reverse=True)
    
    return render_template('index.html', results=all_results)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        flash(f'File {filename} uploaded successfully!')
    else:
        flash('Invalid file type. Please upload PDF, DOCX, or TXT files.')
    
    return redirect(url_for('index'))

@app.route('/analyze/<filename>')
def analyze_single(filename):
    """Analyze a single resume and return detailed results"""
    # Look for file in both folders
    file_paths = [
        os.path.join('resumes', filename),
        os.path.join('uploads', filename)
    ]
    
    for file_path in file_paths:
        if os.path.exists(file_path):
            result = agent.analyze_resume(file_path)
            if result:
                return jsonify(result)
    
    return jsonify({'error': 'File not found'}), 404

@app.route('/delete/<filename>')
def delete_file(filename):
    """Delete a file"""
    file_paths = [
        os.path.join('uploads', filename),
        os.path.join('resumes', filename)
    ]
    
    for file_path in file_paths:
        if os.path.exists(file_path):
            os.remove(file_path)
            flash(f'File {filename} deleted successfully!')
            break
    
    return redirect(url_for('index'))

@app.route('/export')
def export_results():
    """Export results to CSV"""
    results = agent.analyze_all_resumes('resumes')
    upload_results = agent.analyze_all_resumes('uploads')
    all_results = results + upload_results
    
    if not all_results:
        flash('No results to export')
        return redirect(url_for('index'))
    
    # Save to CSV
    filename = 'shortlisted_resumes.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        fieldnames = ['filename', 'score', 'required_skills_matched', 'preferred_skills_matched', 
                     'experience_years', 'must_keywords', 'avoid_keywords']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in all_results:
            result_copy = {
                'filename': result['filename'],
                'score': result['score'],
                'required_skills_matched': result['required_skills_matched'],
                'preferred_skills_matched': result['preferred_skills_matched'],
                'experience_years': result['experience_years'],
                'must_keywords': ', '.join(result['must_keywords']),
                'avoid_keywords': ', '.join(result['avoid_keywords'])
            }
            writer.writerow(result_copy)
    
    flash(f'Results exported to {filename}')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 