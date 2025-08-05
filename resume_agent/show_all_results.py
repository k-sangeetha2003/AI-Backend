import os
import re
import csv
import PyPDF2
from docx import Document
from typing import Dict, List, Tuple
from tabulate import tabulate

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

def display_comprehensive_results(results: List[Dict]):
    """Display comprehensive results for all resumes"""
    if not results:
        print("❌ No resumes found to analyze!")
        return
    
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE RESUME ANALYSIS RESULTS")
    print("="*80)
    
    # Summary Statistics
    total_resumes = len(results)
    avg_score = sum(r['score'] for r in results) / total_resumes
    high_performers = len([r for r in results if r['score'] >= 80])
    qualified = len([r for r in results if r['score'] >= 60])
    
    print(f"\n📈 SUMMARY STATISTICS:")
    print(f"   • Total Resumes Analyzed: {total_resumes}")
    print(f"   • Average Score: {avg_score:.1f}%")
    print(f"   • High Performers (80%+): {high_performers}")
    print(f"   • Qualified Candidates (60%+): {qualified}")
    
    # Detailed Results Table
    print(f"\n📋 DETAILED RESULTS (All {total_resumes} Resumes):")
    print("-" * 80)
    
    table_data = []
    for i, result in enumerate(results, 1):
        # Determine score category
        if result['score'] >= 80:
            score_category = "🟢 Excellent"
        elif result['score'] >= 60:
            score_category = "🟡 Good"
        else:
            score_category = "🔴 Needs Improvement"
        
        # Format keywords
        must_kw = ", ".join(result['must_keywords']) if result['must_keywords'] else "None"
        avoid_kw = ", ".join(result['avoid_keywords']) if result['avoid_keywords'] else "None"
        
        table_data.append([
            i,
            result['filename'],
            f"{result['score']}%",
            score_category,
            f"{result['required_skills_matched']}/{result['total_required_skills']}",
            f"{result['preferred_skills_matched']}/{result['total_preferred_skills']}",
            f"{result['experience_years']} years",
            must_kw,
            avoid_kw
        ])
    
    headers = [
        "#", "Filename", "Score", "Category", "Required Skills", 
        "Preferred Skills", "Experience", "Must Keywords", "Avoid Keywords"
    ]
    
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Individual Detailed Reports
    print(f"\n🔍 DETAILED INDIVIDUAL REPORTS:")
    print("="*80)
    
    for i, result in enumerate(results, 1):
        print(f"\n📄 {i}. {result['filename']}")
        print(f"   {'─' * (len(result['filename']) + 4)}")
        
        # Score and category
        if result['score'] >= 80:
            print(f"   🏆 Score: {result['score']}% (Excellent)")
        elif result['score'] >= 60:
            print(f"   ⭐ Score: {result['score']}% (Good)")
        else:
            print(f"   ⚠️  Score: {result['score']}% (Needs Improvement)")
        
        # Skills breakdown
        print(f"   📚 Required Skills: {result['required_skills_matched']}/{result['total_required_skills']}")
        print(f"   🌟 Preferred Skills: {result['preferred_skills_matched']}/{result['total_preferred_skills']}")
        print(f"   ⏰ Experience: {result['experience_years']} years")
        
        # Keywords
        if result['must_keywords']:
            print(f"   ✅ Must Keywords Found: {', '.join(result['must_keywords'])}")
        else:
            print(f"   ❌ Must Keywords: None found")
            
        if result['avoid_keywords']:
            print(f"   ⚠️  Avoid Keywords Found: {', '.join(result['avoid_keywords'])}")
        else:
            print(f"   ✅ Avoid Keywords: None found")
        
        # All detected skills
        if result['all_skills']:
            print(f"   🛠️  All Detected Skills ({len(result['all_skills'])}):")
            skills_str = ", ".join(result['all_skills'][:10])  # Show first 10
            if len(result['all_skills']) > 10:
                skills_str += f" ... and {len(result['all_skills']) - 10} more"
            print(f"      {skills_str}")
        
        # Recommendations
        print(f"   💡 Recommendations:")
        if result['score'] >= 80:
            print(f"      • Strong candidate - Consider for interview")
        elif result['score'] >= 60:
            print(f"      • Qualified candidate - Review further")
        else:
            print(f"      • May need additional screening")
        
        if result['required_skills_matched'] < len(agent.required_skills) * 0.5:
            print(f"      • Missing many required skills")
        if result['experience_years'] < agent.required_years:
            print(f"      • Below required experience level")
        if result['avoid_keywords']:
            print(f"      • Contains avoid keywords - review carefully")

def main():
    agent = ResumeShortlistingAgent()
    
    # Analyze resumes from both folders
    print("🔍 Analyzing resumes...")
    results = agent.analyze_all_resumes('resumes')
    upload_results = agent.analyze_all_resumes('uploads')
    
    # Combine all results
    all_results = results + upload_results
    all_results.sort(key=lambda x: x['score'], reverse=True)
    
    # Display comprehensive results
    display_comprehensive_results(all_results)
    
    # Save to CSV
    if all_results:
        filename = 'all_resume_results.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            fieldnames = ['filename', 'score', 'required_skills_matched', 'preferred_skills_matched', 
                         'experience_years', 'must_keywords', 'avoid_keywords', 'all_skills']
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
                    'avoid_keywords': ', '.join(result['avoid_keywords']),
                    'all_skills': ', '.join(result['all_skills'])
                }
                writer.writerow(result_copy)
        
        print(f"\n💾 Results saved to: {filename}")
    
    print(f"\n✅ Analysis complete! All {len(all_results)} resumes have been analyzed and shortlisted.")

if __name__ == "__main__":
    main() 