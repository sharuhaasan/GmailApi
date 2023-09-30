# GmailApi
Aim : Standalone Python script that integrates with Gmail API and performs some rule based operations on emails.

INSTALLATION                                                                                                                                                                                                                                                              
Clone the repository: https://github.com/sharuhaasan/GmailApi                                                                     

Navigate to the project directory:  cd GmailApi                                                                              

Create a virtual environment: python3 -m venv venv                                                                               

Activate the virtual environment: venv\Scripts\activate                                                                  

Install the dependencies: pip install -r requirements.txt                                                                                  


DATABASE :   Mysql database............(The table representation of Mysql database is attached below as screenshot)                                                   

Download :   "client_secret_509730660755-rnaj4ujvaun0tvhem1qkoglt7hpgbadn.apps.googleusercontent.com.json" ....(File is attached in mail )                  

Open Gmail_Api.py file... and Add the path of the above downloaded Json file in "CLIENT_SECRET_FILE".....(remove exisiting Json file path)              

RUN the project file : python Gmail_Api.py                                                                                                                     

OUTPUT:                                                                                                                                         

"Email is inserted" ...{(Mails from gmail app is fetched and inserted in Mysql database),                                                                            
In def fetch_and_insert_emails() function : I have used "maxResults=4"....(means latest 4 mails from the gmail app)}                                                    

"Rule Applied for email (shows "mail" details)"......{The fetched emails which matches the specific conditions, mentioned in "Rules.json" file}                                  

"Rule not Applied: (shows "rule"), Conditions not met for email: (shows mail details)"........{The fetched emails which does not matche the specific conditions, mentioned in "Rules.json" file}}                       

"Successfully marked email from (shows "sender" detail) as read."........{If rule is applied,the actions(marked)mentioned in "Rules.json" file is performed}                                             

"Successfully moved email with subject (shows "subject" of the mail) to (folder_name)"...........{If rule is applied,the actions(move message)mentioned in "Rules.json" file is performed} and{"folder_name" is the folder where the mail is moved; and it is mentioned in Rules.json}.....

[folder_name must be "SPAM" , "TRASH" , "STARRED" , "IMPORTANT"]
-
"Failed to mark email as read. API response:(shows "response")"...........{when rule is applied,the actions(marked)mentioned in "Rules.json" file is not performed}

"Failed to move email to '{folder_name}'. API response: {shows "response")"...........{when rule is applied,the actions(move message)mentioned in "Rules.json" file is not performed}

"Exception occurred"...........{shows error if condition/statement(try&except) does not met}

RUN the Unittest cases : Unit_Test.py....................{shows the test cases passed or failed, if passed some statements are printed}    


SCREENSHOT
-
![Screenshot (48)](https://github.com/sharuhaasan/GmailApi/assets/136123240/d9c2be3c-5106-4cb3-93cc-dc5816db7970)

