# Resume Analyzer - Comprehensive Results System

This system provides comprehensive analysis and shortlisting of all resumes that users can provide. It includes both a web interface and command-line tools to display detailed results for all resumes.

## Features

- **All Resumes Shortlisted**: Every resume is analyzed and included in the results
- **Comprehensive Analysis**: Detailed scoring based on skills, experience, and keywords
- **Multiple File Formats**: Supports PDF, DOCX, and TXT files
- **Web Interface**: Modern, responsive web application for easy interaction
- **Command Line**: Quick command-line tool for batch processing
- **Export Capabilities**: Save results to CSV for further analysis

## Quick Start

### Option 1: Web Interface (Recommended)

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Web Application**:
   ```bash
   python resume_analyzer_app.py
   ```

3. **Open Browser**: Navigate to `http://localhost:5000`

4. **Upload Resumes**: Use the web interface to upload and analyze resumes

### Option 2: Command Line

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Place Resumes**: Put resume files in the `resumes/` folder

3. **Run Analysis**:
   ```bash
   python show_all_results.py
   ```

## File Structure

```
resume_agent/
├── resumes/                    # Place resume files here
│   ├── sample_resume.txt
│   └── john
├── uploads/                    # Web-uploaded files (auto-created)
├── templates/                  # Web interface templates
│   └── index.html
├── resume_analyzer_app.py      # Web application
├── show_all_results.py         # Command-line tool
├── shortlisting_agent.py       # Original script
├── requirements.txt            # Dependencies
└── README.md                  # This file
```

## Web Interface Features

### Dashboard Overview
- **Upload Section**: Drag-and-drop or click to upload resumes
- **Statistics Cards**: Total resumes, average score, high performers, qualified candidates
- **All Results Display**: Every resume shown with detailed analysis

### Resume Cards
Each resume card shows:
- **Overall Score**: Color-coded (Green: 80%+, Yellow: 60-79%, Red: <60%)
- **Skills Progress**: Visual progress bars for required and preferred skills
- **Experience**: Years of experience detected
- **Keywords**: Must-have and avoid keywords found
- **All Skills**: Complete list of detected skills
- **Actions**: Detailed analysis and delete options

### Export Functionality
- **CSV Export**: Download all results as a CSV file
- **Comprehensive Data**: Includes all analysis metrics

## Command Line Features

### Comprehensive Display
- **Summary Statistics**: Total resumes, average scores, performance categories
- **Detailed Table**: All resumes in a formatted table
- **Individual Reports**: Detailed analysis for each resume
- **Recommendations**: Specific suggestions for each candidate

### Output Files
- `all_resume_results.csv`: Complete analysis results
- `shortlisted_resumes.csv`: Original format results

## Analysis Criteria

### Scoring System (0-100%)
- **Required Skills (40%)**: Python, JavaScript, HTML, CSS, React, Node.js
- **Preferred Skills (20%)**: AWS, Docker, Git, Agile, SQL, MongoDB, Express
- **Experience (30%)**: Years of experience (target: 3+ years)
- **Must Keywords (10%)**: Experience, development, software, project
- **Avoid Keywords**: Penalty for intern, student, fresh graduate, entry level

### Skills Detection
The system detects skills across multiple categories:
- **Programming**: Python, Java, JavaScript, HTML, CSS, SQL, React, Node.js, Git, C++, C#, PHP, Ruby, Go, Rust
- **Data Science**: Machine Learning, Data Analysis, Pandas, NumPy, Excel, Statistics, TensorFlow, PyTorch, Scikit-learn
- **Design**: UI/UX, Photoshop, Figma, Sketch, Illustrator, Adobe XD, InVision
- **Business**: Project Management, Leadership, Marketing, Sales, Strategy, Agile, Scrum
- **Cloud**: AWS, Azure, GCP, Docker, Kubernetes, Jenkins, CI/CD
- **Database**: MySQL, PostgreSQL, MongoDB, Redis, Oracle, SQL Server

## Customization

### Modify Job Requirements
Edit the `ResumeShortlistingAgent` class in any script:

```python
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
```

### Add New Skills
Update the `skills_keywords` dictionary to include new skill categories:

```python
self.skills_keywords = {
    'your_category': ['skill1', 'skill2', 'skill3'],
    # ... existing categories
}
```

## Usage Examples

### Web Interface
1. Start the application: `python resume_analyzer_app.py`
2. Open browser to `http://localhost:5000`
3. Upload resumes using the web interface
4. View all results in the dashboard
5. Export results to CSV

### Command Line
1. Place resumes in `resumes/` folder
2. Run: `python show_all_results.py`
3. View comprehensive analysis in terminal
4. Check generated CSV files

### Batch Processing
```bash
# Analyze existing resumes
python show_all_results.py

# Run web interface for interactive use
python resume_analyzer_app.py

# Export results
# (Results are automatically saved to CSV files)
```

## Output Files

### all_resume_results.csv
Complete analysis including all detected skills:
- filename, score, required_skills_matched, preferred_skills_matched
- experience_years, must_keywords, avoid_keywords, all_skills

### shortlisted_resumes.csv
Original format results:
- filename, score, required_skills_matched, preferred_skills_matched
- experience_years, must_keywords, avoid_keywords

## Troubleshooting

### Common Issues
1. **No resumes found**: Ensure files are in `resumes/` folder with correct extensions (.pdf, .docx, .txt)
2. **Import errors**: Run `pip install -r requirements.txt`
3. **Web interface not loading**: Check if port 5000 is available
4. **File reading errors**: Ensure files are not corrupted and have proper permissions

### File Format Support
- **PDF**: Requires PyPDF2
- **DOCX**: Requires python-docx
- **TXT**: Plain text files

## Performance Notes

- **Large Files**: PDF files with many pages may take longer to process
- **Multiple Files**: System processes all files in parallel for efficiency
- **Memory Usage**: Large resume collections may require more memory

## Security Considerations

- **File Uploads**: Web interface validates file types and uses secure filenames
- **Data Privacy**: Resume content is processed locally, not sent to external services
- **File Storage**: Uploaded files are stored in the `uploads/` directory

## Contributing

To extend the system:
1. Modify the `ResumeShortlistingAgent` class for different analysis criteria
2. Update the web interface templates for new features
3. Add new file format support in the `extract_text` method
4. Enhance the scoring algorithm in `calculate_score` method

## License

This project is open source and available under the MIT License. 