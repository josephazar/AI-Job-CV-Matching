cv_review_prompt = """
I will give you an anonymized Resume. The personal information, dates, and emails are incorrect and fake. The rest of the information is real.

This is the resume: 
--------
{resume}
--------


Using the above resume, generate a professional profile containing only five categories: Work Experience, Education, Skills, Certifications, and Languages. Each category should be detailed, but concise. Below are the specific instructions for each category:

Work Experience:
- Include only job title, company, and dates. Do not include responsibilities or achievements.

Education:
- List only the degree name, institution, and year. Exclude other details like GPA, honors, activities, etc.

Skills, Certifications, Languages:
- List them concisely. 

If information for a category is not provided, include that category with the statement "Not Mentioned."

For example:
Work Experience:
- Job title, Company, Dates 

Education:
- Degree, Institution, Year

Skills:
- Specific skills

Certifications:
- Certifications earned

Languages:
- Languages spoken, proficiency level

Ensure no specific personal names or identifiers are included – focus on the global information about professional experience, educational background, skills, certifications, and languages spoken. Stick strictly to these instructions and categories, keeping the information concise and anonymous.
"""

cv_review_prompt_confidence = """
Extract all data in Work experience and Education.
in Education output this format 'Major,Degree,University,start date-end date' only, and  if major  or degree or university are not mentioned write Not Mentioned.
the month in dates should be Letters only , and year should be YYYY.

This is the resume: 
-------------------------------------------------------
{resume}
-------------------------------------------------------

Using the above resume, generate a professional profile containing only five categories: Work Experience, Education, Skills, Certifications, and Languages. Each category should be detailed, but concise, and include a confidence percentage for the accuracy of the extracted information. Below are the specific instructions for each category, including the request for a confidence level and follow the rules:

Work Experience:
- Include only job title, company, and dates. Do not include responsibilities,city ,country or achievements.
- Provide a confidence percentage regarding the extracted information.

Education:
- List only in order the Major ,degree type, institution, and start year - end year . this one should be always Major,degree type, institution, start year - end year. Exclude other details like GPA, honors, activities, etc.
- Provide a confidence percentage regarding the extracted information.

Skills, Certifications, Languages, Personnel info:
- List them concisely.
- Provide a confidence percentage regarding the extracted information for each category.

If information for a category is not provided, include that category with the statement "Not Mentioned" and a confidence percentage that reflects the certainty of the absence of data.
in Wokr Experience i want this format only job title , company name (without country or city) , dates.
"""

cv_job_review_prompt_confidence2 = """
I will give you an anonymized Resume. The rest of the information is real.also extract as much as you can data.

This is the resume: 
-------------------------------------------------------
{resume}
-------------------------------------------------------
These are the Jobs Positions:
-------------------------------------------------------
{Positions}
-------------------------------------------------------

Using the above resume and jobs positions, generate a professional profile for each job and  and include a confidence percentage for the accuracy of the matching job on the resume. Below are the specific instructions for each category, including the request for a confidence level:


------------------------------------------------------------------
the output should be like this for example if there are 3 positions

positon 1:
-name of the position 1
-confidence 90%

position 2:
-name of the position 2
-confidence 10%

position 3:
-name of the position 3
-confidence 50%


------------------------------------------------------------------------------
the confidence value should be based on the percentage of the given resume matching the jobs positions take into account the required experience,degree,certificates and skills.
"""

cv_job_review_prompt_confidence = """
Task: You are an AI HR system responsible for analyzing resumes and job positions. 
Your goal is to provide a confidence for a given job position based on the provided resume. 
Follow the rules outlined below to determine the confidence value.
-------------------------------------------------------
Rules for confidence:

If the job description doesn't match the experience in the resume, the confidence value should be lower than 10%.
if the job description moderate match the experience in the resume the confidence should be between 10% and 50%.
if the job description highly match the experience in the resume the confidence should be between 50% and 100%.

-------------------------------------------------------------
Job Position:

Name: {name} , {recruitment_id}
Requirements:
{Positions}
-------------------------------------------------------
resume:

{resume}
-------------------------------------------------------
Output Format:

Position:
-Name: {name} , {recruitment_id}
-confidence: Percentage of matching position requirements%
-------------------------------------------------------
"""

job_description_prompt = """
Write an interesting job descriptions for the following job: {job_title}.
Job description: {job_description}.
Company Information: {company}.
Experience:{experience} years.
Degree:{degree}.
Generate content in the following language: {language}.
Tone of voice of the intro must be: {writing_tone}.
the certifications should be professional.
i will give you an example :
--------------------------------------
        example : 
        Title:
        Machine Learning Engineer


        Information:
        CM is a leading technology company that specializes in developing innovative solutions for businesses across various industries. We are committed to providing our clients with cutting-edge technologies that help them stay ahead of the competition. As a Machine Learning Engineer at CM, you will have the opportunity to work on exciting projects that leverage the latest advancements in machine learning and artificial intelligence.

        Description:
        We are seeking a highly skilled Machine Learning Engineer to join our team. The ideal candidate will have experience in developing and implementing machine learning models using Azure ML and MLops. In this role, you will be responsible for designing, developing, and deploying machine learning models that can be used to solve complex business problems. You will work closely with our data scientists, software engineers, and product managers to ensure that our machine learning models are accurate, scalable, and reliable.

        Responsibilities:
        - Design and develop machine learning models using Azure ML and MLops
        - Collaborate with data scientists, software engineers, and product managers to identify business problems that can be solved using machine learning
        - Develop and deploy machine learning models that are accurate, scalable, and reliable
        - Monitor and maintain machine learning models to ensure they are performing optimally
        - Continuously improve machine learning models by incorporating new data and feedback from users



        Requirements:
        - Bachelor's or Master's degree in Computer Science, Mathematics, or related field
        - 3+ years of experience in developing and implementing machine learning models
        - Strong programming skills in Python and experience with Azure ML and MLops
        - Experience with data visualization tools such as Tableau or Power BI
        - Strong problem-solving skills and ability to work independently
        - Excellent communication and collaboration skills

        Certifications:
        -Microsoft DP-100
        -Microsoft DP-103
        -Microsoft AI-900

        Remaining:
        If you are passionate about machine learning and want to work on exciting projects that have a real impact on businesses, then we want to hear from you. Apply now to join our team at CM!
        ---------------------------------------------
        """

salary_range = """   what is the salary range for {job_title} in {country} , the currency should be in {currency} """
min_salary = """  what is the minimum salary for {job_title} in {country} per year , the currency should be in {currency} , source:indeed  """
max_salary = """what is the maximum salary for {job_title} in {country} per year , the currency should be in {currency} , source:indeed """
extract_salary_range = """ your task is to extract the salary range with currency only , from a given text and you should return json format only.
for example the given input is : the minimum salary for this job in this country is 500$, and the maximum salary for this job is 1000$, the output should be :
                {{"minsalary":"500",maxsalary:"1000","currency":"US-Dollar"}}
----------------------------------------------------
extract from this phrase : {minmaxsalary}  """

extract_salary = """ your task is to extract the salary with currency only , from a given text and you should return json format only.
for example the given input is : the salary in this country is 500$ the output should be :
                {{"salary":500,"currency":"US-Dollar"}}
----------------------------------------------------
extract from this phrase : {salary}
"""

highlights = """  
write highlight points this given text {text} , the highlights should be maximum 3 words

----------------------------------------------------------
for example :
the highlights points for this text :
- Design and develop web applications using Angular, React, MongoDB, Octa, and MySQL
- Collaborate with designers and project managers to understand client requirements and translate them into technical solutions
- Write clean, efficient, and well-documented code
- Troubleshoot and debug issues in a timely manner
- Stay updated on industry trends and best practices to continuously improve our development processes
Result Needed :
-Develop web applications.
-collaborate with designers and managers.
-write well documented code.

-----------------------------------------------------------


"""
extract_experience = """
I want to extract experience as points example: - Worked a software engineer for 2 yrs.\n- Worked a full stack dev for 1 yr.
"""
extract_degree = """
I want to extract degree only summarize the degree in 2 words only ,field only summarize it with 1 words at the most and years as number only 0 if not availble without writing description. For example response by json needed like: - Level: MB\n- Field: Software Engineering\n- Years: 1
---------------------------------------- 
Extract the degree from the following: {text}
"""
policy = """You are an AI HR Manager that helps the company to write Attendance & Leave Policy.
generate a report for a campany called {company} that has {prompt}

------------------------------------------------------------------
here is a sample example to follow and dont copy the exact information just use it to help you write the report , the info change depends on the company:
A-	Scope
This policy applies to all regular fulltime team members of EXQUITECH and should be fairly enforced by all management and supervisory personnel.
B-	Objectives
Through implementation of this policy, Exquitech expects to:

•	Ensure timely reporting and accurate recording of absences.
•	Manage absences in line with contractual entitlements and operational requirements.
•	Reduce the current level of unexcused absences, tardiness, and early departures.
•	Identify patterns of employee absences and develop effective intervention strategies to improve team member’s attendance.
•	Provide a framework for the granting and administration of leave.
•	Use the vacation days as tools to ensure that sick leaves and unjustified leaves are to improve team member’s attendance.

C-	Attendance

1.	Attendance
The operating hours of the head office are from 7:00 am till 4:00pm or 8am till 5pm from Monday to Friday.

All Exquitech team members are granted paid days off on the official holidays as per the internal policies and regulations, and the Labor Law.

a-	Absence
The absence of a team member will either be accepted or not by his manager. In case the absence is justified and agreed upon by the manager, a leave request should be filled on the platform.
All absences and tardiness should be applied on the company’s platform otherwise appropriate disciplinary action will result. 
In case the absence is unjustified, it will be deducted as per the internal policy.
b-	Duty on Holidays       
When a team member is requested by his manager to work on a holiday or a day off, the team member is entitled for alternative days and will be added to his annual leaves.

c-	  Tardiness
The team member should inform his direct manager.
If justified a justification email or text message should be sent.
If the lateness is unjustified, the deduction will be done as per the internal policy.

d-	Leaves

2.	Sick Leave

a.	Absence Reporting
When a team member is absent because of the need for sick leave, he should ensure that his manager is informed at the earliest practicable time, normally no later than 30min after his scheduled start time, and should be also applied on the company platform.
Responsible notice is also required for pre-arranged sick leave, example: a surgical procedure.
If the period of leave extends over 2 days or longer, the team member will keep the manager informed at regular intervals of the situation concerning the absence from work. A medical certificate giving the reason in the likely period of expected absence is required, and it must be submitted to the company within 48 hours of the team member’s absence. Sickness during preapproved annual leave will be considered as annual leave.

b.	Work Accident
All personal work-related accidents must be reported and recorded on an accident/incident report form (insurance).
All lost time resulting from the non-work injury must also be documented.

c.	Leave Management
Each Manager will monitor and manage sick leave in a fair and equitable manner that takes account of individual circumstances. The most difficult problems to manage are often those concerning short term but persistent patterns of absenteeism, or long-term illness.
If the pattern of unsupported absence continues, the situation will be reviewed, and disciplinary action may be considered. Where the period of absence extends over a significant period and the continued ill health of an employee prevents them from carrying out their duties.
The situation will be reviewed at regular intervals and where necessary medical advice will be sought on the long-term prediction.
If the absence continues to extend over a prolonged period and is affecting operational needs, other options may need to be explored with the team member. Each case will be treated on its merits and with due regard to the medical information that is received.





3.	Annual Leave
a.	Entitlement to Annual Leave
Entitlement to Annual Leaves is prescribed in employment contracts. The annual leave balance is earned based on each country’s Labor Law.
The annual leave is also subjected to the manager’s approval. During probation period, special approval is required.

For each year of service, the team member is entitled for:

In Lebanon:
•	15 days of paid annual vacation (1.25 days per month)
In UAE:
•	30 days, if they have completed one year of service and 2 days per month, if they have completed six months of service, but not one year. 
•	1.8 days per month 
In KSA: 
•	Less than 5 years of service: 15 working days of annual leave.
•	5 to 10 years of service: 20 working days of annual leave.
•	More than 10 years of service: 30 working days of annual leave

b.	Accumulated Leave
A team member may only carry forward 8 days as annual leaves at the beginning of each year. The carried over leaves need 31-Aug
When a team member resigns, the company  will not refund the balance of annual leaves earned during the employment period, they can be deducted from the notice period if seen appropriate by the management.

c.	Timing of Leave
Annual leave should be taken each year at times mutually agreed between the manager and the team member concerned; taking into account the operational needs that apply.
The leave request is to be presented 24 hours prior from the assigned leave date if the period doesn’t exceed 1 day.
- Annual leaves exceeding 2 days should be applied for 1 week ahead
- Annual leaves for 1 week should be applied for 1 month ahead    
- Annual leaves for 2 weeks should be applied for 2 months ahead    
- Annual leaves for 3 weeks should be applied for 4 months ahead 

If the request leave was not approved due to operational needs, an alternative date is to be scheduled accordingly with the consent of the team member.

d.	Leaves Platform
All team members must apply for annual leave using the company’s leave request form and submit it to the manager at least 24 hours ahead of time. The manager in turn is responsible for checking the balance of leaves of the employee in question. 

4.	Work from Home
In special cases and for a valid reason you can work from home, but as well you are requested to fill and submit a Work from home request on the company’s designated platform in advance with a pre-approval from your direct manager and HR and you should always be available on Microsoft teams.
5.	Bereavement Leave
Paid bereavement leave is available to team member to pay respects to someone who has died within his close family. The number of leave days for such occurrences is per the company’s internal regulations.

a.	Entitlement
A team member will be granted special bereavement leave on full pay to discharge their obligation and/or pay their respect to a deceased person within his close family. 

b.	Applications
Application for bereavement leave must be specified on the leave request form, and the team member must submit a certification of this unfortunate event upon his return to the company.

6.	Maternity Leave (the law)
The Lebanese Labor Law article 28 prescribes parental leave entitlement for female team member who are pregnant and intent to assume the primary care of the child and protects the rights of team members during pregnancy and parental leave, the duration of the maternity leave is set at 70 days at the moment.

a.	Job Protection
The company will normally hold a team member’s position open (this includes filling it temporarily). Where the company needs to fill a key position permanently, there are provisions for offering the team member on parental leave a comparable position, or, if this is not possible, approving an extension of leave until a team member previous position or similar position 
becomes vacant. The job protection applies to all leaves that are for more than 1 month and especially for senior positions.

b.	Applications 
A team member intending to take parental leave associated with the birth of a child is required to give at least 3 months’ notice in writing using the leave request form. The form is to be accompanied by medical certificate stating the expected date of delivery. 

7.	Paternity Leave
A team member is entitled for 3 days paternity leave associated with the birth of a child is required.

8.	Marriage Leave
Any team member who intends to get married has the right to apply for a leave request; the number of days the team member is entitled for is stated in the company’s internal regulations to a fully paid marriage leave for 1 week. 
The team member must submit documentation of the marriage upon his return; otherwise the leave is treated as unpaid leave.

e-	DEDUCTION
Excessive Absence & Tardiness
Team members that are frequently absent without the prior approval of their direct supervisors will face a 1-day deduction for each absence and a written warning will be handed to them if deemed necessary.
If a team member doesn’t show up for 7 consecutive days or 15 days a year, without prior approval or a documented justification, then his actions will result in the termination of his employment with the company.


------------------------------------------------------------------

"""

cv_review_prompt_confidence2 = """
I will give you an anonymized Resume. The rest of the information is real.also extract as much as you can data.

This is the resume: 
--------
{resume}
--------

Using the above resume, generate a professional profile containing only five categories: Work Experience, Education, Skills, Certifications, and Languages. Each category should be detailed, but concise, and include a confidence percentage for the accuracy of the extracted information. Below are the specific instructions for each category, including the request for a confidence level:

Work Experience:
- Include only job title, company, and dates. Do not include responsibilities or achievements.
- Provide a confidence percentage regarding the extracted information.

Education:
- List only the degree name, institution, and year. Exclude other details like GPA, honors, activities, etc.
- Provide a confidence percentage regarding the extracted information.

Skills, Certifications, Languages:
- List them concisely.
- Provide a confidence percentage regarding the extracted information for each category.

If information for a category is not provided, include that category with the statement "Not Mentioned" and a confidence percentage that reflects the certainty of the absence of data.

For example:
Work Experience:
- Job title, Company, Dates 
- Confidence: 90%

Education:
- Degree, Institution, Year
- Confidence: 95%

Skills:
- Specific skills
- Confidence: 85%

Certifications:
- Certifications earned
- Confidence: 80%

Languages:
- Languages spoken, proficiency level
- Confidence: 90%

Personnel info:
-full name,address,phone number, linkedin
-Confidence:90%


 focus on the global information about professional experience and include personnel information, educational background, skills, certifications, and languages spoken. Stick strictly to these instructions and categories, keeping the information concise and anonymous. The confidence percentages should reflect how certain you are that the extracted data match the categories correctly and do not include any of the fake or incorrect details.
"""