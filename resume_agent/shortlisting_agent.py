import os
import re
import csv
import PyPDF2
from docx import Document
from typing import Dict, List, Tuple

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
            'all_skills': skills
        }

    def shortlist_resumes(self, resumes_folder: str) -> List[Dict]:
        """Analyze all resumes in the folder and return sorted results"""
        results = []
        
        if not os.path.exists(resumes_folder):
            print(f"❌ Resumes folder '{resumes_folder}' not found!")
            return results
        
        # Get all resume files
        resume_files = []
        for file in os.listdir(resumes_folder):
            if file.lower().endswith(('.pdf', '.docx', '.txt')):
                resume_files.append(os.path.join(resumes_folder, file))
        
        if not resume_files:
            print(f"❌ No resume files found in '{resumes_folder}'!")
            return results
        
        print(f"📄 Found {len(resume_files)} resume files to analyze...")
        
        # Analyze each resume
        for file_path in resume_files:
            print(f"🔍 Analyzing: {os.path.basename(file_path)}")
            result = self.analyze_resume(file_path)
            if result:
                results.append(result)
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results

    def save_to_csv(self, results: List[Dict], filename: str = 'shortlisted_resumes.csv'):
        """Save results to CSV file"""
        if not results:
            print("No results to save")
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            fieldnames = ['filename', 'score', 'required_skills_matched', 'preferred_skills_matched', 
                         'experience_years', 'must_keywords', 'avoid_keywords']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in results:
                # Convert lists to strings for CSV and remove extra fields
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
        
        print(f"✅ Results saved to '{filename}'")

def main():
    agent = ResumeShortlistingAgent()
    
    # Analyze resumes
    results = agent.shortlist_resumes('resumes')
    
    if results:
        # Save results
        agent.save_to_csv(results)
        
        # Display summary
        print("\n📊 SHORTLISTING RESULTS")
        print("=" * 50)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['filename']}")
            print(f"   📈 Score: {result['score']}%")
            print(f"   ✅ Required Skills: {result['required_skills_matched']}/{len(agent.required_skills)}")
            print(f"   ⭐ Preferred Skills: {result['preferred_skills_matched']}/{len(agent.preferred_skills)}")
            print(f"   📅 Experience: {result['experience_years']} years")
            
            if result['must_keywords']:
                print(f"   🔍 Must Keywords: {', '.join(result['must_keywords'])}")
            
            if result['avoid_keywords']:
                print(f"   ⚠️  Avoid Keywords: {', '.join(result['avoid_keywords'])}")
        
        print(f"\n📁 Results saved to: shortlisted_resumes.csv")
        
    else:
        print("❌ No results generated. Please check your resume files.")

if __name__ == "__main__":
    main() 