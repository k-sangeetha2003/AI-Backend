import os
import re
import csv
import PyPDF2
from docx import Document
from typing import Dict, List, Tuple
from datetime import datetime
import json

class EnhancedResumeAnalyzer:
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
                
            elif file_ext == '.txt' or file_ext == '':  # Handle files without extensions
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read().lower()
                    
            else:
                print(f"Unsupported file format: {file_ext}")
                return ""
                
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return ""

    def extract_personal_info(self, text: str) -> Dict:
        """Extract personal information from resume text"""
        personal_info = {
            'name': '',
            'email': '',
            'phone': '',
            'location': '',
            'linkedin': '',
            'github': '',
            'website': '',
            'summary': ''
        }
        
        # Extract name (look for patterns like "Name:" or at the beginning)
        name_patterns = [
            r'name[:\s]+([a-zA-Z\s]+)',
            r'^([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*resume',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*cv'
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                personal_info['name'] = matches[0].strip().replace('\n', ' ').replace('\r', ' ').title()
                break
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_pattern, text)
        if email_matches:
            personal_info['email'] = email_matches[0]
        
        # Extract phone
        phone_patterns = [
            r'(\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})',
            r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',
            r'phone[:\s]+([0-9\-\+\(\)\s]+)'
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                personal_info['phone'] = matches[0].strip()
                break
        
        # Extract location
        location_patterns = [
            r'location[:\s]+([^,\n]+)',
            r'address[:\s]+([^,\n]+)',
            r'([A-Z][a-z]+,\s*[A-Z]{2})',
            r'([A-Z][a-z]+,\s*[A-Z][a-z]+)'
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text)
            if matches:
                personal_info['location'] = matches[0].strip()
                break
        
        # Extract LinkedIn
        linkedin_pattern = r'linkedin\.com/in/[a-zA-Z0-9-]+'
        linkedin_matches = re.findall(linkedin_pattern, text)
        if linkedin_matches:
            personal_info['linkedin'] = linkedin_matches[0]
        
        # Extract GitHub
        github_pattern = r'github\.com/[a-zA-Z0-9-]+'
        github_matches = re.findall(github_pattern, text)
        if github_matches:
            personal_info['github'] = github_matches[0]
        
        # Extract website
        website_pattern = r'https?://[^\s]+'
        website_matches = re.findall(website_pattern, text)
        if website_matches:
            personal_info['website'] = website_matches[0]
        
        # Extract summary (first few sentences)
        lines = text.split('\n')
        summary_lines = []
        for line in lines[:10]:  # Check first 10 lines
            if len(line.strip()) > 20 and not any(keyword in line.lower() for keyword in ['experience', 'education', 'skills']):
                summary_lines.append(line.strip())
        if summary_lines:
            personal_info['summary'] = ' '.join(summary_lines[:3])  # First 3 lines
        
        return personal_info

    def extract_education(self, text: str) -> List[Dict]:
        """Extract education information"""
        education = []
        
        # Look for education section
        education_patterns = [
            r'education[:\s]*(.*?)(?=experience|skills|work|employment)',
            r'degree[:\s]*(.*?)(?=experience|skills|work|employment)',
            r'university[:\s]*(.*?)(?=experience|skills|work|employment)',
            r'college[:\s]*(.*?)(?=experience|skills|work|employment)'
        ]
        
        for pattern in education_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                education_text = matches[0]
                # Extract degree and institution
                degree_pattern = r'([A-Z][a-z\s]+(?:Bachelor|Master|PhD|B\.?S\.?|M\.?S\.?|Ph\.?D\.?)[A-Za-z\s]*)'
                institution_pattern = r'([A-Z][a-zA-Z\s&]+(?:University|College|Institute|School))'
                
                degrees = re.findall(degree_pattern, education_text, re.IGNORECASE)
                institutions = re.findall(institution_pattern, education_text, re.IGNORECASE)
                
                for i, degree in enumerate(degrees):
                    edu_info = {
                        'degree': degree.strip(),
                        'institution': institutions[i].strip() if i < len(institutions) else '',
                        'year': '',
                        'gpa': ''
                    }
                    education.append(edu_info)
                break
        
        return education

    def extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience information"""
        experience = []
        
        # Look for experience section
        experience_patterns = [
            r'experience[:\s]*(.*?)(?=education|skills|projects)',
            r'work[:\s]*(.*?)(?=education|skills|projects)',
            r'employment[:\s]*(.*?)(?=education|skills|projects)'
        ]
        
        for pattern in experience_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                experience_text = matches[0]
                
                # Extract job titles and companies
                job_pattern = r'([A-Z][a-zA-Z\s]+(?:Developer|Engineer|Manager|Analyst|Consultant|Specialist|Lead|Senior|Junior))'
                company_pattern = r'([A-Z][a-zA-Z\s&]+(?:Inc|Corp|LLC|Ltd|Company|Technologies|Solutions))'
                
                jobs = re.findall(job_pattern, experience_text, re.IGNORECASE)
                companies = re.findall(company_pattern, experience_text, re.IGNORECASE)
                
                for i, job in enumerate(jobs):
                    exp_info = {
                        'title': job.strip(),
                        'company': companies[i].strip() if i < len(companies) else '',
                        'duration': '',
                        'description': ''
                    }
                    experience.append(exp_info)
                break
        
        return experience

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
        """Analyze a single resume and return comprehensive results"""
        text = self.extract_text(file_path)
        if not text:
            return None
        
        # Extract all information
        personal_info = self.extract_personal_info(text)
        education = self.extract_education(text)
        experience = self.extract_experience(text)
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
        
        # Generate candidate name from filename if not found
        if not personal_info['name']:
            filename = os.path.basename(file_path)
            name_from_file = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title()
            personal_info['name'] = name_from_file
        
        return {
            'filename': os.path.basename(file_path),
            'personal_info': personal_info,
            'education': education,
            'experience': experience,
            'score': round(score, 2),
            'required_skills_matched': required_skills_matched,
            'preferred_skills_matched': preferred_skills_matched,
            'experience_years': experience_years,
            'must_keywords': must_keywords,
            'avoid_keywords': avoid_keywords,
            'all_skills': skills,
            'total_required_skills': len(self.required_skills),
            'total_preferred_skills': len(self.preferred_skills),
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def analyze_all_resumes(self, folder_path: str) -> List[Dict]:
        """Analyze all resumes in the folder and return results"""
        results = []
        
        if not os.path.exists(folder_path):
            return results
        
        # Get all resume files
        resume_files = []
        for file in os.listdir(folder_path):
            # Check for files with extensions
            if file.lower().endswith(('.pdf', '.docx', '.txt')):
                resume_files.append(os.path.join(folder_path, file))
            # Also check for files without extensions (like 'jane', 'priya', 'john')
            elif not '.' in file and os.path.isfile(os.path.join(folder_path, file)):
                resume_files.append(os.path.join(folder_path, file))
        
        # Analyze each resume
        for file_path in resume_files:
            result = self.analyze_resume(file_path)
            if result:
                results.append(result)
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results

    def save_detailed_results(self, results: List[Dict], shortlisted: List[Dict], rejected: List[Dict], base_filename: str = 'detailed_resume_results'):
        """Save detailed results to multiple files with shortlisting focus"""
        if not results:
            print("No results to save")
            return
        
        # Create results directory
        results_dir = 'resume_results'
        os.makedirs(results_dir, exist_ok=True)
        
        # Save comprehensive CSV
        csv_filename = os.path.join(results_dir, f'{base_filename}.csv')
        with open(csv_filename, 'w', newline='', encoding='utf-8') as file:
            fieldnames = [
                'name', 'email', 'phone', 'location', 'linkedin', 'github', 'website',
                'score', 'required_skills_matched', 'preferred_skills_matched',
                'experience_years', 'must_keywords', 'avoid_keywords', 'all_skills',
                'education', 'experience', 'filename', 'analysis_date', 'status'
            ]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in results:
                # Determine status
                status = "SHORTLISTED" if result in shortlisted else "REJECTED"
                
                row = {
                    'name': result['personal_info']['name'],
                    'email': result['personal_info']['email'],
                    'phone': result['personal_info']['phone'],
                    'location': result['personal_info']['location'],
                    'linkedin': result['personal_info']['linkedin'],
                    'github': result['personal_info']['github'],
                    'website': result['personal_info']['website'],
                    'score': result['score'],
                    'required_skills_matched': result['required_skills_matched'],
                    'preferred_skills_matched': result['preferred_skills_matched'],
                    'experience_years': result['experience_years'],
                    'must_keywords': ', '.join(result['must_keywords']),
                    'avoid_keywords': ', '.join(result['avoid_keywords']),
                    'all_skills': ', '.join(result['all_skills']),
                    'education': json.dumps(result['education']),
                    'experience': json.dumps(result['experience']),
                    'filename': result['filename'],
                    'analysis_date': result['analysis_date'],
                    'status': status
                }
                writer.writerow(row)
        
        # Save shortlisted candidates CSV
        if shortlisted:
            shortlisted_csv = os.path.join(results_dir, 'shortlisted_candidates.csv')
            with open(shortlisted_csv, 'w', newline='', encoding='utf-8') as file:
                fieldnames = [
                    'name', 'email', 'phone', 'location', 'linkedin', 'github', 'website',
                    'score', 'required_skills_matched', 'preferred_skills_matched',
                    'experience_years', 'all_skills', 'filename'
                ]
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                
                writer.writeheader()
                for result in shortlisted:
                    row = {
                        'name': result['personal_info']['name'],
                        'email': result['personal_info']['email'],
                        'phone': result['personal_info']['phone'],
                        'location': result['personal_info']['location'],
                        'linkedin': result['personal_info']['linkedin'],
                        'github': result['personal_info']['github'],
                        'website': result['personal_info']['website'],
                        'score': result['score'],
                        'required_skills_matched': result['required_skills_matched'],
                        'preferred_skills_matched': result['preferred_skills_matched'],
                        'experience_years': result['experience_years'],
                        'all_skills': ', '.join(result['all_skills']),
                        'filename': result['filename']
                    }
                    writer.writerow(row)
        
        # Save individual JSON files for each candidate
        for result in results:
            # Clean the candidate name for filename (remove newlines, special chars)
            candidate_name = result['personal_info']['name'].replace('\n', ' ').replace('\r', ' ').strip()
            candidate_name = re.sub(r'[^\w\s-]', '', candidate_name)  # Remove special characters
            candidate_name = candidate_name.replace(' ', '_').lower()
            json_filename = os.path.join(results_dir, f'{candidate_name}_detailed.json')
            with open(json_filename, 'w', encoding='utf-8') as file:
                json.dump(result, file, indent=2, ensure_ascii=False)
        
        # Save shortlisting summary report
        summary_filename = os.path.join(results_dir, f'{base_filename}_shortlisting_summary.txt')
        with open(summary_filename, 'w', encoding='utf-8') as file:
            file.write("SHORTLISTING SUMMARY REPORT\n")
            file.write("=" * 50 + "\n\n")
            file.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            file.write(f"Total Candidates: {len(results)}\n")
            file.write(f"Shortlisted: {len(shortlisted)}\n")
            file.write(f"Rejected: {len(rejected)}\n")
            file.write(f"Shortlisting Rate: {(len(shortlisted)/len(results))*100:.1f}%\n\n")
            
            if shortlisted:
                file.write("🏆 SHORTLISTED CANDIDATES:\n")
                file.write("-" * 30 + "\n")
                for i, result in enumerate(shortlisted, 1):
                    file.write(f"{i}. {result['personal_info']['name']}\n")
                    file.write(f"   Score: {result['score']}%\n")
                    file.write(f"   Email: {result['personal_info']['email']}\n")
                    file.write(f"   Phone: {result['personal_info']['phone']}\n")
                    file.write(f"   Experience: {result['experience_years']} years\n")
                    file.write(f"   Skills: {', '.join(result['all_skills'][:5])}...\n\n")
            
            if rejected:
                file.write("❌ REJECTED CANDIDATES:\n")
                file.write("-" * 30 + "\n")
                for i, result in enumerate(rejected, 1):
                    file.write(f"{i}. {result['personal_info']['name']} - Score: {result['score']}%\n")
                    reasons = []
                    if result['required_skills_matched'] < len(self.required_skills) * 0.5:
                        reasons.append("Missing required skills")
                    if result['experience_years'] < self.required_years * 0.5:
                        reasons.append("Insufficient experience")
                    if result['score'] < 60:
                        reasons.append("Low overall score")
                    if result['avoid_keywords']:
                        reasons.append("Contains avoid keywords")
                    file.write(f"   Reason: {', '.join(reasons)}\n\n")
        
        print(f"✅ Detailed results saved to '{results_dir}/' directory")
        print(f"🎯 Shortlisted candidates saved to '{results_dir}/shortlisted_candidates.csv'")
        return results_dir

def display_comprehensive_results(results: List[Dict], agent_instance):
    """Display comprehensive results for all resumes with shortlisting focus"""
    if not results:
        print("❌ No resumes found to analyze!")
        return
    
    print("\n" + "="*100)
    print("🎯 SHORTLISTED CANDIDATES - RESUME ANALYSIS RESULTS")
    print("="*100)
    
    # Filter shortlisted candidates (score >= 60% and meet minimum requirements)
    shortlisted = []
    rejected = []
    
    for result in results:
        # Check if candidate meets minimum requirements
        meets_skills = result['required_skills_matched'] >= len(agent_instance.required_skills) * 0.5  # At least 50% of required skills
        meets_experience = result['experience_years'] >= agent_instance.required_years * 0.5  # At least 50% of required experience
        good_score = result['score'] >= 60
        no_avoid_keywords = len(result['avoid_keywords']) == 0
        
        if meets_skills and meets_experience and good_score and no_avoid_keywords:
            shortlisted.append(result)
        else:
            rejected.append(result)
    
    # Summary Statistics
    total_resumes = len(results)
    shortlisted_count = len(shortlisted)
    rejected_count = len(rejected)
    
    print(f"\n📊 SHORTLISTING SUMMARY:")
    print(f"   • Total Candidates Analyzed: {total_resumes}")
    print(f"   • ✅ SHORTLISTED Candidates: {shortlisted_count}")
    print(f"   • ❌ Rejected Candidates: {rejected_count}")
    print(f"   • 📈 Shortlisting Rate: {(shortlisted_count/total_resumes)*100:.1f}%")
    
    # Display shortlisted candidates first
    if shortlisted:
        print(f"\n🏆 SHORTLISTED CANDIDATES ({len(shortlisted)}):")
        print("=" * 100)
        
        for i, result in enumerate(shortlisted, 1):
            print(f"\n{'🎯'*20} SHORTLISTED #{i} {'🎯'*20}")
            print(f"👤 CANDIDATE: {result['personal_info']['name'].upper()}")
            print(f"{'='*80}")
            
            # Personal Information
            print(f"📄 PERSONAL INFORMATION:")
            print(f"   Name: {result['personal_info']['name']}")
            print(f"   Email: {result['personal_info']['email'] or 'Not provided'}")
            print(f"   Phone: {result['personal_info']['phone'] or 'Not provided'}")
            print(f"   Location: {result['personal_info']['location'] or 'Not provided'}")
            if result['personal_info']['linkedin']:
                print(f"   LinkedIn: {result['personal_info']['linkedin']}")
            if result['personal_info']['github']:
                print(f"   GitHub: {result['personal_info']['github']}")
            if result['personal_info']['website']:
                print(f"   Website: {result['personal_info']['website']}")
            
            # Score and Analysis
            print(f"\n📊 ANALYSIS RESULTS:")
            if result['score'] >= 80:
                print(f"   🏆 Overall Score: {result['score']}% (EXCELLENT)")
            elif result['score'] >= 60:
                print(f"   ⭐ Overall Score: {result['score']}% (GOOD)")
            
            print(f"   📚 Required Skills: {result['required_skills_matched']}/{result['total_required_skills']}")
            print(f"   🌟 Preferred Skills: {result['preferred_skills_matched']}/{result['total_preferred_skills']}")
            print(f"   ⏰ Experience: {result['experience_years']} years")
            
            # Education
            if result['education']:
                print(f"\n🎓 EDUCATION:")
                for edu in result['education']:
                    print(f"   • {edu['degree']} - {edu['institution']}")
            
            # Experience
            if result['experience']:
                print(f"\n💼 WORK EXPERIENCE:")
                for exp in result['experience']:
                    print(f"   • {exp['title']} at {exp['company']}")
            
            # Skills
            if result['all_skills']:
                print(f"\n🛠️  DETECTED SKILLS ({len(result['all_skills'])}):")
                skills_str = ", ".join(result['all_skills'])
                print(f"   {skills_str}")
            
            # Keywords
            if result['must_keywords']:
                print(f"\n✅ MUST KEYWORDS FOUND:")
                print(f"   {', '.join(result['must_keywords'])}")
            
            # Recommendations
            print(f"\n💡 RECOMMENDATIONS:")
            if result['score'] >= 80:
                print(f"   • 🎯 STRONG CANDIDATE - RECOMMENDED FOR INTERVIEW")
            elif result['score'] >= 60:
                print(f"   • ✅ QUALIFIED CANDIDATE - CONSIDER FOR NEXT ROUND")
            
            print(f"\n📁 File: {result['filename']}")
            print(f"📅 Analyzed: {result['analysis_date']}")
    
    # Display rejected candidates (brief summary)
    if rejected:
        print(f"\n❌ REJECTED CANDIDATES ({len(rejected)}):")
        print("-" * 100)
        for i, result in enumerate(rejected, 1):
            print(f"{i}. {result['personal_info']['name']} - Score: {result['score']}%")
            print(f"   Reason: ", end="")
            reasons = []
            if result['required_skills_matched'] < len(agent_instance.required_skills) * 0.5:
                reasons.append("Missing required skills")
            if result['experience_years'] < agent_instance.required_years * 0.5:
                reasons.append("Insufficient experience")
            if result['score'] < 60:
                reasons.append("Low overall score")
            if result['avoid_keywords']:
                reasons.append("Contains avoid keywords")
            print(", ".join(reasons))
    
    # Final recommendation
    print(f"\n🎯 FINAL RECOMMENDATION:")
    if shortlisted:
        print(f"   ✅ RECOMMENDED: {len(shortlisted)} candidates are shortlisted for interview")
        print(f"   📋 Top candidates to prioritize:")
        for i, result in enumerate(shortlisted[:3], 1):
            print(f"      {i}. {result['personal_info']['name']} ({result['score']}%)")
    else:
        print(f"   ❌ NO CANDIDATES SHORTLISTED - Consider adjusting requirements or expanding search")
    
    return shortlisted, rejected

def main():
    agent = EnhancedResumeAnalyzer()
    
    # Analyze resumes from both folders
    print("🔍 Analyzing resumes with enhanced detail extraction...")
    results = agent.analyze_all_resumes('resumes')
    upload_results = agent.analyze_all_resumes('uploads')
    
    # Combine all results
    all_results = results + upload_results
    all_results.sort(key=lambda x: x['score'], reverse=True)
    
    # Display comprehensive results with shortlisting
    shortlisted, rejected = display_comprehensive_results(all_results, agent)
    
    # Save detailed results
    if all_results:
        results_dir = agent.save_detailed_results(all_results, shortlisted, rejected)
        print(f"\n💾 All detailed results saved to: {results_dir}/")
    
    print(f"\n✅ Analysis complete! {len(shortlisted)} candidates shortlisted out of {len(all_results)} total candidates.")

if __name__ == "__main__":
    main() 