###################################################### APPLICATION INPUTS ######################################################


# >>>>>>>>>>> Easy Apply Questions & Inputs <<<<<<<<<<<

# Give an relative path of your default resume to be uploaded. If file in not found, will continue using your previously uploaded resume in LinkedIn.
default_resume_path =  "all resumes/default/220456_himanshu_yadav_bt_ce_sde.pdf"  # (In Development)

# What do you want to answer for questions that ask about years of experience you have, this is different from current_experience?
years_of_experience = "1"  # A number in quotes Eg: "0","1","2","3","4", etc.

# Do you need visa sponsorship now or in future?
require_visa = "No"  # "Yes" or "No"

# What is the link to your portfolio website, leave it empty as "", if you want to leave this question unanswered
website = "https://portfolio-blond-eight-63.vercel.app"  # "www.example.bio" or "" and so on....

# Please provide the link to your LinkedIn profile.
linkedIn = "https://www.linkedin.com/in/yhimanshu22045/"  # "https://www.linkedin.com/in/example" or "" and so on...

# What is the status of your citizenship? # If left empty as "", tool will not answer the question. However, note that some companies make it compulsory to be answered
# Valid options are: "U.S. Citizen/Permanent Resident", "Non-citizen allowed to work for any employer", "Non-citizen allowed to work for current employer", "Non-citizen seeking work authorization", "Canadian Citizen/Permanent Resident" or "Other"
us_citizenship = "Other"


## SOME ANNOYING QUESTIONS BY COMPANIES 🫠 ##

# What to enter in your desired salary question (American and European), What is your expected CTC (South Asian and others)?, only enter in numbers as some companies only allow numbers,
desired_salary = 2000000  # 80000, 90000, 100000 or 120000 and so on... Do NOT use quotes

"""
Note: If question has the word "lakhs" in it (Example: What is your expected CTC in lakhs), 
then it will add '.' before last 5 digits and answer. Examples: 
* 2400000 will be answered as "24.00"
* 850000 will be answered as "8.50"
And if asked in months, then it will divide by 12 and answer. Examples:
* 2400000 will be answered as "200000"
* 850000 will be answered as "70833"
"""

# What is your current CTC? Some companies make it compulsory to be answered in numbers...
current_ctc =     1600000  # 800000, 900000, 1000000 or 1200000 and so on... Do NOT use quotes


"""
Note: If question has the word "lakhs" in it (Example: What is your current CTC in lakhs), 
then it will add '.' before last 5 digits and answer. Examples: 
* 2400000 will be answered as "24.00"
* 850000 will be answered as "8.50"
# And if asked in months, then it will divide by 12 and answer. Examples:
# * 2400000 will be answered as "200000"
# * 850000 will be answered as "70833"
"""

# (In Development) # Currency of salaries you mentioned. Companies that allow string inputs will add this tag to the end of numbers. Eg:
currency = "INR"  # "USD", "INR", "EUR", etc.

# What is your notice period in days?
notice_period = 20  # Any number >= 0 without quotes. Eg: 0, 7, 15, 30, 45, etc.
"""
Note: If question has 'month' or 'week' in it (Example: What is your notice period in months), 
then it will divide by 30 or 7 and answer respectively. Examples:
* For notice_period = 20:
  - "66" OR "2" if asked in months OR "9" if asked in weeks
* For notice_period = 20:"
  - "15" OR "0" if asked in months OR "2" if asked in weeks
* For notice_period = 20:
  - "0" OR "0" if asked in months OR "0" if asked in weeks
"""

# Your LinkedIn headline in quotes Eg: "Software Engineer @ Google, Masters in Computer Science", "Recent Grad Student @ MIT, Computer Science"
linkedin_headline = "Full Stack Developer and Former intern in GIVA Jewellery"  # "Headline" or "" to leave this question unanswered

# Your summary in quotes, use \n to add line breaks if using single quotes "Summary".You can skip \n if using triple quotes """Summary"""
linkedin_summary = """Final year Civil Engineering student at IIT Kanpur with a passion for building end-to-end data solutions that drive business results. I thrive on translating complex datasets into actionable insights, a skill I honed during my technical internship at GIVA.

At GIVA, I developed and deployed an automated sales forecasting and inventory optimization pipeline using AutoML. This system improved forecast accuracy by over 15% and was instrumental in reducing stockouts by 25%. I also built interactive Streamlit dashboards to provide real-time insights to the supply chain team.

Beyond my internship, I'm passionate about exploring cutting-edge AI:

Agentic AI: I built a stock screening agent using LangGraph and LLMs that can interpret user queries and utilize tools like the YFinance API to provide financial analysis.

Credit Risk: I developed a complete credit risk model, using K-means for customer segmentation and techniques like WOE/IV for feature engineering to build a robust scoring system.

NLP: I've fine-tuned LLMs like Llama2 for language translation, achieving a 15% improvement in BLEU score.

I'm now seeking full-time Data Scientist or ML Engineer opportunities where I can apply my skills in Python, SQL, machine learning, and data visualization to solve challenging problems.

Feel free to connect or reach out at yhimanshu22@iitk.ac.in

I'm a Software Engineer with 1 year of experience in Full Stack Web applications and cloud solutions. 
Specialized in React, Node.js, and Python.
"""

""" 
Note: If left empty as "", the tool will not answer the question. However, note that some companies make it compulsory to be answered. Use \n to add line breaks.
"""

# Your cover letter in quotes, use \n to add line breaks if using single quotes "Cover Letter".You can skip \n if using triple quotes """Cover Letter""" (This question makes sense though)
cover_letter = """
Dear Hiring Manager, 
I am writing to express my interest in the Software Development / Data Engineering role at 
your organization. I am a final-year B.Tech undergraduate in Civil Engineering at IIT Kanpur, 
with strong hands-on experience in software development, data science, and scalable 
system design. 
During my internship at GIVA Indiejewel Pvt. Ltd., I worked on both product engineering and 
data-driven decision systems. I developed Angular-based admin modules for SKU and 
category management and built an end-to-end sales forecasting and inventory optimization 
pipeline using AutoGluon, which improved forecast accuracy by over 15% and reduced 
stockout risks by 25%. I also delivered a Streamlit dashboard that translated complex analytics 
into actionable insights for business stakeholders. 
Beyond internships, I have built multiple production-grade full-stack projects using Next.js, 
MERN, Prisma, Firebase, Cloudflare, and Vercel. My projects include an AI-powered blogging 
platform using Gemini API, a secure blood bank management system with analytics, and 
several backend systems focused on authentication, scalability, and clean API design. These 
projects strengthened my understanding of system design, RESTful architectures, databases, 
and modern deployment workflows. 
I bring a strong foundation in programming (Java, Python, JavaScript, SQL, C++), practical 
exposure to machine learning and data analysis, and leadership experience from managing 
web development initiatives at IIT Kanpur student bodies. I enjoy working in fast-paced 
environments where engineering decisions directly impact users and business outcomes. 
I am highly motivated to contribute as a developer who can build reliable systems, learn 
quickly, and collaborate eAectively. I would welcome the opportunity to discuss how my skills 
and experiences align with your team’s goals. 
Thank you for your time and consideration. 
Sincerely, 
Himanshu Yadav 
College Name : IIT Kanpur 
email id :  yhimanshu22@iitk.ac.in  
Phone No: +91 8114245060 

"""
##> ------ Dheeraj Deshwal : dheeraj9811 Email:dheeraj20194@iiitd.ac.in/dheerajdeshwal9811@gmail.com - Feature ------

# Your user_information_all letter in quotes, use \n to add line breaks if using single quotes "user_information_all".You can skip \n if using triple quotes """user_information_all""" (This question makes sense though)
# We use this to pass to AI to generate answer from information , Assuing Information contians eg: resume  all the information like name, experience, skills, Country, any illness etc.
user_information_all = """
Himanshu Yadav : yhimanshu22@iitk.ac.in/yhimanshu220456@gmail.com +91 8114245060 IIT Kanpur B.Tech 2025
"""
##<
"""
Note: If left empty as "", the tool will not answer the question. However, note that some companies make it compulsory to be answered. Use \n to add line breaks.
"""

# Name of your most recent employer
recent_employer = "Not Applicable"  # "", "Lala Company", "Google", "Snowflake", "Databricks"

# Example question: "On a scale of 1-10 how much experience do you have building web or mobile applications? 1 being very little or only in school, 10 being that you have built and launched applications to real users"
confidence_level = "10"  # Any number between "1" to "10" including 1 and 10, put it in quotes ""

##


# >>>>>>>>>>> RELATED SETTINGS <<<<<<<<<<<

## Allow Manual Inputs
# Should the tool pause before every submit application during easy apply to let you check the information?
pause_before_submit = False  # True or False, Note: True or False are case-sensitive
"""
Note: Will be treated as False if `run_in_background = True`
"""

# Should the tool pause if it needs help in answering questions during easy apply?
# Note: If set as False will answer randomly...
pause_at_failed_question = False  # True or False, Note: True or False are case-sensitive

"""
Note: Will be treated as False if `run_in_background = True`
"""
##

# Do you want to overwrite previous answers?
overwrite_previous_answers = False  # True or False, Note: True or False are case-sensitive


############################################################################################################
