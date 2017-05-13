import imaplib 
import smtplib
import subprocess
import email
import time
import re
import threading
import base64
import sys
from random import randint


allowedEmails = ["a@b.c","d@e.f]
usingFile = False
gmailEmail = "a@b.c"
gmailPassword = "pswd"
errorMessage = "That's an error!"

def saveAndRunCode(code):
    global usingFile
    output = ""
    while usingFile:
        time.sleep(randint(0, 100) / 100)
    
    usingFile = True
    try:
        with open("code.sh", "w+") as codeFile:
            codeFile.write(code)
    except:
        print("There was an error with saving code to file!!!!")
        exceptionHandler(sys.exc_info()[1])
        output += errorMessage
    else:
      try:
          output += subprocess.check_output(["./code.sh"], shell=True).decode("utf-8").strip()
      except:
          print("There was an error with running code!!!!!")
          output += errorMessage
          exceptionHandler(sys.exc_info()[1])
        
    usingFile = False
    return output


def sendEmail(toAddress, subject, body):
    try:
        smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        smtp.login(gmailEmail, gmailPassword)
        smtp.sendmail(gmailEmail, toAddress, "Subject: " + subject + "\n\n" + body)
        smtp.quit()
    except:
        exceptionHandler(sys.exc_info()[1])


def exceptionHandler(exception):
    with open("errorLog.txt", "a") as errorFile:
        errorFile.write(str(exception) + "\n")


class startRunCodeThread(threading.Thread):
    def __init__(self, sender, body, sendExecutionEmail):
        threading.Thread.__init__(self)
        self.sender = sender
        self.body = body
        self.sendExecutionEmail = sendExecutionEmail
         
    def run(self):
        processEmail(self.sender, self.body, self.sendExecutionEmail)


def processEmail(sender, body, sendExecutionEmail):
    if sendExecutionEmail:
      sendEmail(sender,"Executing Your code...", "Your code is being executed...")
    output = saveAndRunCode(body)
    sendEmail(sender, "Code Output", "Your code output is:\n" + output)
    
    
def getFirstTextBlock(self, emailMessageInstance):
    maintype = emailMessageInstance.get_content_maintype()
    if maintype == 'multipart':
        for part in emailMessageInstance.get_payload():
            if part.get_content_maintype() == 'text':
                if email.message_from_string(str(part))['Content-Transfer-Encoding'] == "base64":
                    return base64.b64decode(part.get_payload())
                return part.get_payload()
    elif maintype == 'text':
        if email.message_from_string(str(emailMessageInstance.get_payload()))['Content-Transfer-Encoding'] == "base64":
            return base64.b64decode(emailMessageInstance.get_payload())
        return emailMessageInstance.get_payload()


def loopCode():
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(gmailEmail, gmailPassword)
    imap.select("INBOX")

    result, data = imap.search(None, "(UNSEEN)")
    idList = data[0].split()

    for unreadEmail in idList:
        imap.store(unreadEmail,'+FLAGS','\Seen')
        result, data = imap.fetch(unreadEmail, "(RFC822)")
        imap.store(unreadEmail, '+FLAGS', '\Deleted')
        imap.expunge()
        emailMessage = email.message_from_string(data[0][1])
        
        try:
            sender = re.findall("<(.+:?)>", emailMessage["From"])[0]
        except:
            sender = emailMessage["From"]
            
        subject = emailMessage["Subject"]
        
        fullBody = getFirstTextBlock(" ", emailMessage).strip()
        if "*****************" in fullBody:
            body = fullBody[:fullBody.find("****************")].strip()
        else:
            body = fullBody
            
        americanDate = time.strftime("%x").split("/")
        date = "/".join([americanDate[1], americanDate[0], americanDate[2]])
        
        if "RPI Email Control" in subject and date in subject and sender in allowedEmails:
            executeEmail = startRunCodeThread(sender, body, "sendExeEmail" in subject)
            executeEmail.start()
    imap.close()
    imap.logout()

    time.sleep(2)


while True:
    loopCode()
