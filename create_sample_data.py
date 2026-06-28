"""
Run this script once to generate a sample contacts Excel file.
Usage: python create_sample_data.py
"""

import pandas as pd
from pathlib import Path

sample_data = [
    {"name": "Ali Hassan",     "email": "ali.hassan@example.com",    "department": "Engineering",  "domain": "Software Development", "position": "Intern",        "joining_date": "July 15, 2026",  "company": "TechCorp",    "location": "Lahore"},
    {"name": "Sara Khan",      "email": "sara.khan@example.com",     "department": "Design",       "domain": "UI/UX Design",         "position": "Intern",        "joining_date": "July 15, 2026",  "company": "TechCorp",    "location": "Karachi"},
    {"name": "Ahmed Raza",     "email": "ahmed.raza@example.com",    "department": "Data Science", "domain": "Machine Learning",     "position": "Intern",        "joining_date": "August 1, 2026", "company": "DataLab",     "location": "Islamabad"},
    {"name": "Fatima Malik",   "email": "fatima.malik@example.com",  "department": "Marketing",    "domain": "Digital Marketing",    "position": "Intern",        "joining_date": "August 1, 2026", "company": "BrandX",      "location": "Karachi"},
    {"name": "Usman Tariq",    "email": "usman.tariq@example.com",   "department": "Engineering",  "domain": "Mobile Development",   "position": "Junior Dev",    "joining_date": "July 20, 2026",  "company": "AppStudio",   "location": "Lahore"},
    {"name": "Ayesha Siddiqui","email": "ayesha.siddiqui@example.com","department": "HR",          "domain": "HR Management",        "position": "HR Intern",     "joining_date": "July 10, 2026",  "company": "PeopleFirst", "location": "Multan"},
    {"name": "Bilal Ahmed",    "email": "bilal.ahmed@example.com",   "department": "Finance",      "domain": "Financial Analysis",   "position": "Finance Intern","joining_date": "August 5, 2026", "company": "FinGroup",    "location": "Karachi"},
    {"name": "Zara Iqbal",     "email": "zara.iqbal@example.com",    "department": "Engineering",  "domain": "Backend Development",  "position": "Intern",        "joining_date": "July 15, 2026",  "company": "TechCorp",    "location": "Lahore"},
]

df = pd.DataFrame(sample_data)

output_path = Path("uploads/sample_contacts.xlsx")
output_path.parent.mkdir(exist_ok=True)
df.to_excel(output_path, index=False)
print(f"✅ Sample Excel file created: {output_path}")
print(f"   {len(df)} sample contacts included.")

# Also create CSV version
csv_path = Path("uploads/sample_contacts.csv")
df.to_csv(csv_path, index=False)
print(f"✅ Sample CSV file created: {csv_path}")
