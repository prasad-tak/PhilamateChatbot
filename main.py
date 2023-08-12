#importing packages

import threading
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import  ContextTypes, ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import pandas
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import random
import time
from datetime import date, datetime, timedelta, time
import mysql.connector
import concurrent.futures
from telegram import Bot




intake = ''
output = ''
intake_ready = threading.Event()
output_ready = threading.Event()



mydb = mysql.connector.connect(
  host="project.mysql.database.azure.com",
  user="project",
  password="Prasad@7744",
  database='hospital'

)
sql = mydb.cursor()

Stopwords = stopwords.words('english')

def get_keywords(text):
    tokens = word_tokenize(text)
   
    stemmer = PorterStemmer()
    tokens = [stemmer.stem(token) for token in tokens if token.lower() not in Stopwords or token in ['no']]
    
    return tokens
    
def greet():
    return "Hello, I am Ryzen, virtual assistant for the Philimate Hospital.\nI am here to help you with your appointments."
    
    

def err():
    choices = ["Please enter a valid response\n", "Sorry, I am not able to understand your response. Please try again.\n"]
    return str(random.choice(choices))


date_available = date(2023,8,9)
datetime_available = datetime(date_available.year,date_available.month,date_available.day,10,0,0)
future_appointments = []


async def dates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dates = []
    dates.append(str(datetime_available.date() + timedelta(days = 1)))
    dates.append(str(datetime_available.date() + timedelta(days = 2)))
    dates.append(str(datetime_available.date() + timedelta(days = 3)))
    
    
    keyboard = []
    for date in dates:
        keyboard.append([InlineKeyboardButton(date, callback_data=date)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please select a date for appointment: ", reply_markup=reply_markup)
    
async def handle_date_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
   
    global intake
    query = update.callback_query
    selected_date = query.data
    intake = selected_date
    intake_ready.set()
    output_ready.wait()
    await query.edit_message_text(output)
    output_ready.clear()
    
   



def get_datetime():
    global datetime_available,date_available, future_appointments
    if datetime.now() > datetime_available:
        if datetime.now() < datetime(date_available.year,date_available.month,date_available.day,12,0,0):
            datetime_available = datetime(date_available.year,date_available.month,date_available.day,13,0,0)
        elif datetime.now() < datetime(date_available.year,date_available.month,date_available.day,17,0,0):
            datetime_available = datetime(date_available.year,date_available.month,date_available.day,17,0,0)
        else:
            date_available = date.today() + timedelta(days=1)
            datetime_available = datetime(date_available.year,date_available.month,date_available.day,10,0,0)
        if datetime_available in future_appointments:
            datetime_available = datetime_available + timedelta(minutes = 20)
        return datetime_available
    else:       
    
        datetime_available = datetime_available + timedelta(minutes = 20)
        if datetime_available in future_appointments:
            datetime_available = datetime_available + timedelta(minutes = 20)
        if datetime_available.time() >= time(14,0,0) and datetime_available.time() <= time(17,0,0):
            datetime_available = datetime(date_available.year,date_available.month,date_available.day,17,0,0)
        elif datetime_available.time() >= time(21,0,0):
            date_available = date.today() + timedelta(days=1)
            datetime_available = datetime(date_available.year,date_available.month,date_available.day,10,0,0)
        return datetime_available

def set_datetime():
    global future_appointments, output
    datetime_ = get_datetime()
    if datetime_.date() == datetime.now().date():
        output = 'Earliest possible appointment is today at {} \n'.format(datetime_.time()) + 'Are you okay with it?'
        output_ready.set()
    else:
        output = 'Earliest possible appointment is on {} at {} \n'.format(datetime_.date(),datetime_.time()) + 'Are you okay with it?'
        output_ready.set()
    intake_ready.wait()
    intake_ready.clear()
    choice = intake
    reply = get_keywords(choice.lower())
    if 'ye' in reply or 'alright' in reply:
        return datetime_
    elif 'no' in reply:
        output = f"Type '/dates' or select 'Choose a date' option from menu"
        output_ready.set()
        intake_ready.wait()
        intake_ready.clear()
        date_ = intake
        combined_str = f"{date_} {'10:00:00'}"
        datetime_ = datetime.strptime(combined_str, "%Y-%m-%d %H:%M:%S")
        while True:
            if datetime_ not in future_appointments:
                future_appointments.append(datetime_)
                break
            else:
                datetime_ += timedelta(minutes = 20)
        print('We reach here')
        return datetime_



def new_patient():
    global output
    output = "Please enter your name\n"
    output_ready.set()
    intake_ready.wait()
    name = intake
    intake_ready.clear()     
    
    output = "Please enter your mobile number\n"
    output_ready.set()
    intake_ready.wait()
    mobile = intake
    intake_ready.clear()    
    
    output = "Please enter your city of residence\n"
    output_ready.set()
    intake_ready.wait()
    city = intake
    intake_ready.clear()    
   
    sql.execute("INSERT INTO patients (Name, Mobile, City) VALUES (%s,%s,%s)",(name,mobile,city))
    mydb.commit()
    sql.execute("SELECT Id FROM patients WHERE Name = %s",(name,))
    id = sql.fetchone()
    return id
    

def book():
    global output
    output = "May I know if you are a new patient\n"
    output_ready.set()
    intake_ready.wait()
    reply = intake.lower()
    intake_ready.clear()
    while True:
        reply = get_keywords(reply)
        
        if 'ye' in reply or 'new' in reply:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(new_patient)
                id = future.result()          
            break
        elif 'no' in reply or 'old' in reply:
            output = "Please enter your name\n"
            while True:
                output_ready.set()
                intake_ready.wait()
                name = intake
                intake_ready.clear()    
                sql.execute("SELECT Id FROM patients WHERE Name = %s",(name,))
                id = sql.fetchone()
                if id is not None:
                    break
                else:
                    output = "The name you have entered is not in the data base."
            break
        else:
            output = err()
            output_ready.set()
            intake_ready.wait()
            reply = intake
            intake_ready.clear()    
    output = 'What is the problem you are dealing with?\n'
    output_ready.set()
    intake_ready.wait()
    problem = intake
    intake_ready.clear()   
    with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(set_datetime)
                dtime = future.result()       
    
    sql.execute("INSERT INTO appointments VALUES (%s, %s, %s, %s);", (int(id[0]),problem,dtime.date(),dtime.time()))
    mydb.commit()
    sql.execute("SELECT * FROM appointments WHERE Id = %s",(int(id[0]), ))
    data = sql.fetchone()
    
    output = "Your appointment has been booked!\nPlease visit on {} at {}".format(data[2],data[3])
    output_ready.set()
   
def cancel():
     
    global output
    output = "Please enter your name\n"
    while True:
        output_ready.set()
        intake_ready.wait()
        name = intake
        intake_ready.clear()    
        sql.execute("SELECT Id FROM patients WHERE Name = %s",(name,))
        id = sql.fetchone()
        if id is not None:
            break
        else:
            output = "The name you have entered is not in the data base."
    sql.execute("DELETE FROM  appointments WHERE Id = %s",(int(id[0]),))
    mydb.commit()
    output = "Your appointment has been deleted succesfully"
    output_ready.set()
    
    
def reschedule():
    global output
    output = "Surely, I can reschedule the appointment\nCan you tell me your name?\n"
    while True:
        output_ready.set()
        intake_ready.wait()
        name = intake
        intake_ready.clear()    
        sql.execute("SELECT Id FROM patients WHERE Name = %s",(name,))
        id = sql.fetchone()
        if id is not None:
            break
        else:
            output = "The name you have entered is not in the data base."
    sql.execute("DELETE FROM  appointments WHERE Id = %s",(int(id[0]),))
    mydb.commit()
    output = 'What is the problem you are dealing with?\n'
    output_ready.set()
    intake_ready.wait()
    problem = intake
    intake_ready.clear()    
    with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(set_datetime)
                dtime = future.result()       
    
    sql.execute("INSERT INTO appointments VALUES (%s, %s, %s, %s);", (int(id[0]),problem,dtime.date(),dtime.time()))
    mydb.commit()
    sql.execute("SELECT * FROM appointments WHERE Id = %s",(int(id[0]),))
    data = sql.fetchone()
    output = "Your appointment has been resheduled!\nPlease visit on {} at {}".format(data[2],data[3])
    output_ready.set()












def chat():
    global intake, output,i
    
    while True:
        intake_ready.wait()
        intake_ready.clear()         
        reply = get_keywords(intake.lower())
        if 'hi' in reply:
            output = "Hello!, I am Ryzen.\nI can help you book, cancle or reschedule appointments.\nHow can I help you?"
            output_ready.set()
        elif 'book' in reply or 'visit' in reply:
            book_thread = threading.Thread(target=book)
            book_thread.start()
            book_thread.join()
        elif 'cancel'in reply or 'cancle' in reply:
            cancel_thread = threading.Thread(target=cancel)
            cancel_thread.start()
            cancel_thread.join()
        elif 'reschedul' in reply:
            resced_thread = threading.Thread(target=reschedule)
            resced_thread.start()
            resced_thread.join()
        else:
            output = err()
            output_ready.set()
      
    
     
        
    
loop = asyncio.get_event_loop()

   
   


chat_thread = threading.Thread(target=chat)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(greet())

async def exit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global chat_thread
    await update.message.reply_text(greet())
    



async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type = update.message.chat.type
    global intake,intake_ready,i
    
    text = update.message.text
    print(f'User ({update.message.chat.id}) in {message_type} : "{text}"')
    intake = text
    
    intake_ready.set()
   
    output_ready.wait()
    output_ready.clear()
    print("Bot: ",output)
    await update.message.reply_text(output)
    
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):   
    await update.message.reply_text("An error has occured.")
    await update.message.reply_text("Please try again")



if __name__ == '__main__':
    chat_thread.start()
    webhook_url = "https://philamate.azurewebsites.net/"

    bot = Bot(token='6472535326:AAGRCql7rCoBOJPVNZ5WkasuS8t_8XDpdRQ')
    bot.setWebhook(url=webhook_url)
    application = ApplicationBuilder().token('6472535326:AAGRCql7rCoBOJPVNZ5WkasuS8t_8XDpdRQ').build()
    application.add_handler(CallbackQueryHandler(handle_date_button))
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('dates', dates))
    application.add_error_handler(error)
    application.add_handler(MessageHandler(filters.ALL,handle_message))
    print('Polling')
    loop.run_until_complete(application.run_polling())
    chat_thread.join()

