from threading import Thread
from telebot import types, TeleBot
from parser import Parser
from dbconnection import DBConnection
from event import Event
from Gcalendar import Gcalendar
from datetime import datetime, timedelta
from telebot import types
from os import environ
import flask

bot = TeleBot(environ["API_KEY"])

server = flask.Flask(__name__)

@server.route('/', methods=["GET"])
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=environ['SERVER_URL'], certificate=open('webhook_cert.pem'))
    return "ok", 200

@server.route('/', methods=['POST'])
def get_message():
    bot.process_new_updates([types.Update.de_json(flask.request.stream.read().decode("utf-8"))])
    return "ok", 200

@bot.message_handler(commands=['start'])
def start(message):
    db = DBConnection()
    db.connect()
    if not db.record_exists('user_data', 'chat_id', chat_id=message.from_user.id):
        db.insert('user_data', ['chat_id', 'last_events_refresh', 'is_auto_refreshed'], [message.from_user.id, str(datetime.now().date()), False])
    db.disconnect()
    bot.send_message(message.from_user.id, "Welcome! I'll help you in managing your events from dou.ua")

@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(chat_id=message.from_user.id,
                     text='/choose_tags to choose preferred event topics\n' +
                     '/choose_event_interval to choose time interval from display date\n' +
                     '/choose_display_interval to choose events refresh frequency\n' +
                     '/choose_location to choose events location\n' +
                     '/show_events to show events according to chosen parameters\n' +
                     '/turn_on_autorefresh - to enable autorefresh events\n' +
                     '/turn_off_autorefresh - to disable autorefresh events\n' +
                     '/set_refresh_time - set autorefresh time\n'+
                     'reply event and type \'add to gcalendar\' to add event to gcalendar\n' +
                     'reply event and type \'remove from gcalendar\' to remove event from gcalendar')

@bot.message_handler(commands=['choose_tags'])
def choose_tags(message):
    db = DBConnection()
    db.connect()
    if db.record_exists('user_tags', 'tag', chat_id=message.from_user.id):
        db.delete('user_tags', chat_id=message.from_user.id)
    db.disconnect()
    available_tags = Parser().parse_tags()
    reply_markup = types.ReplyKeyboardMarkup()
    buttons = [types.KeyboardButton(tag) for tag in available_tags]
    end_button = types.KeyboardButton('Done')
    row_width = 3
    for i in range(0, len(buttons), row_width):
        reply_markup.row(*buttons[i:i+row_width])
    reply_markup.add(end_button)
    reply_markup.resize_keyboard = True
    bot.send_message(chat_id=message.from_user.id, text='Please choose preferred topics:', reply_markup=reply_markup)
    bot.register_next_step_handler(message,  read_tag)

def read_tag(message):
    db = DBConnection()
    db.connect()
    available_tags = Parser().parse_tags()
    new_tag = message.text
    if new_tag in available_tags:
        saved_tags = [rec[0] for rec in db.select('user_tags', ['tag'], chat_id=message.from_user.id)]
        if saved_tags and new_tag in saved_tags:
            bot.send_message(message.from_user.id, text='This tag is already chosen!')
        else:
            db.insert('user_tags', ['chat_id', 'tag'], [message.from_user.id, new_tag])
        bot.register_next_step_handler(message,  read_tag)
    elif new_tag == 'Done':
        if not db.record_exists('user_tags', 'chat_id', chat_id=message.from_user.id):
            bot.send_message(message.from_user.id, text='Please choose a tag before quit!')
            bot.register_next_step_handler(message,  read_tag)
        else:
            markup = types.ReplyKeyboardRemove()
            bot.send_message(message.from_user.id, text='Topics chosen, thanks!', reply_markup=markup)
    else:
        bot.send_message(chat_id=message.from_user.id, text='Please, pick a tag from the list!')
        bot.register_next_step_handler(message, read_tag)

@bot.message_handler(commands=['choose_event_interval'])
def event_interval(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        text='a day ahead', callback_data='1 days'))
    markup.add(types.InlineKeyboardButton(
        text='a week ahead', callback_data='7 days'))
    markup.add(types.InlineKeyboardButton(
        text='4 weeks ahead', callback_data='28 days'))
    markup.add(types.InlineKeyboardButton(
        text='a year ahead', callback_data='356 days'))
    bot.send_message(chat_id=message.from_user.id,
                     text='Please choose for what time ahead events should be shown:', reply_markup=markup)

@bot.callback_query_handler(lambda call: call.data.endswith('days'))
def callback_event_interval(query):
    data = int(query.data.split(' ')[0])
    db = DBConnection()
    db.connect()
    db.update('user_data', 'event_interval_days', data, chat_id=query.from_user.id)
    db.disconnect()
    bot.edit_message_reply_markup(chat_id=query.from_user.id, message_id=query.message.id, reply_markup=None)
    bot.send_message(chat_id=query.from_user.id, text='Event interval chosen, thanks!')

@bot.message_handler(commands=['choose_display_interval'])
def choose_display_interval(message):
    bot.send_message(chat_id=message.from_user.id,
                     text='Please type events refresh frequency (in days, > 0):')
    bot.register_next_step_handler(message, read_display_interval)

def read_display_interval(message):
    try:
        days = int(message.text)
        if days <= 0:
            bot.send_message(chat_id=message.from_user.id, text='Please type events refresh frequency (in days, > 0):')
            bot.register_next_step_handler(message, read_display_interval)
            return
        db = DBConnection()
        db.connect()
        db.update('user_data', 'display_interval_days', days, chat_id=message.from_user.id)
        db.disconnect()
        bot.send_message(chat_id=message.from_user.id, text='Display interval chosen, thanks!')
    except ValueError:
        bot.send_message(chat_id=message.from_user.id, text='Please send a message conaining number of days only!')
        bot.register_next_step_handler(message, read_display_interval)

@bot.message_handler(commands=['choose_location'])
def choose_location(message):
    locations = Parser().parse_locations()
    markup = types.ReplyKeyboardMarkup()
    buttons = [types.KeyboardButton(text=location) for location in locations]
    row_width = 3
    for i in range(0, len(buttons), row_width):
        markup.row(*buttons[i:i+row_width])
    bot.send_message(chat_id=message.from_user.id, text='Please choose desired location:', reply_markup=markup)
    bot.register_next_step_handler(message, read_location, Parser().parse_locations())


def read_location(message, locations):
    if message.text not in locations:
        bot.send_message(chat_id=message.from_user.id, text='Please choose desired location(hit the buttons):')
        bot.register_next_step_handler(message, read_location, locations)
    else:
        db = DBConnection()
        db.connect()
        db.update('user_data', 'location', message.text, chat_id=message.from_user.id)
        db.disconnect()
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.from_user.id, text='Location chosen, thanks!', reply_markup=markup)

@bot.message_handler(commands=['set_refresh_time'])
def set_refresh_time(message):
    bot.send_message(chat_id=message.from_user.id, text='Please type tyme in format \'HH:MM\'')
    bot.register_next_step_handler(message, read_time)

def read_time(message):
    try:
        time = datetime.strptime(message.text, "%H:%M").time()
        db = DBConnection()
        db.connect()
        db.update('user_data', 'refresh_time', time, chat_id=message.from_user.id)
        db.disconnect()
        bot.send_message(chat_id=message.from_user.id, text='Refresh time set!')
    except ValueError:
        bot.send_message(chat_id=message.from_user.id, text='Wrong input! Please type tyme in format \'HH:MM\'')
        bot.register_next_step_handler(message, read_time)

@bot.message_handler(commands=['show_events'])
def show_events(message):
    db = DBConnection()
    db.connect()
    event_interval = db.select('user_data', ['event_interval_days'], chat_id=message.from_user.id)[0][0]
    if not event_interval:
        bot.send_message(chat_id=message.from_user.id, text='Please choose event interval first - /choose_event_interval')
        db.disconnect()
        return
    location = db.select('user_data', ['location'], chat_id=message.from_user.id)[0][0]
    if not location:
        bot.send_message(chat_id=message.from_user.id, text='Please choose location first - /choose_location')
        db.disconnect()
        return
    tags = [rec[0] for rec in db.select('user_tags', ['tag'], chat_id=message.from_user.id)]
    if not tags:
        bot.send_message(chat_id=message.from_user.id, text='Please choose topics first - /choose_tags')
        db.disconnect()
        return
    bot.send_message(chat_id=message.from_user.id, text='Your events were refreshed!')
    db.update('user_data', 'last_events_refresh', str(datetime.now().date()), chat_id=message.from_user.id)
    db.disconnect()
    for event in Parser().parse_events(location, tags, event_interval):
        bot.send_photo(chat_id=message.from_user.id, photo=event.img, caption=event.to_user(), disable_notification=True)

@bot.message_handler(content_types=['text'],  func=lambda message: message.text == 'add to gcalendar')
def add_to_gcalendar(message):
    if not message.reply_to_message:
        bot.send_message(chat_id=message.from_user.id, text='You should reply event message with \'add to gcalendar\' text to add event!')
    else:
        db = DBConnection()
        db.connect()
        event = Event.from_text_to_gcalendar(message.reply_to_message.text)
        event_in_gcalendar = db.record_exists('events_in_gcalendar', 'name', chat_id=message.from_user.id, name=event["summary"],
        location=event["location"], description=event["description"], start_date_time=event["start"]["dateTime"], end_date_time=event["end"]["dateTime"])
        if event_in_gcalendar:
            bot.send_message(chat_id=message.from_user.id, text='Event is in your gcalendar already!')
        else:
            event_id = Gcalendar.set_event(event)
            db.insert('events_in_gcalendar', ['name', 'location', 'description', 'start_date_time', 'end_date_time', 'chat_id', 'event_id'],
            [event["summary"], event["summary"], event["description"], event["start"]["dateTime"], event["end"]["dateTime"], message.from_user.id, event_id])
            bot.send_message(chat_id=message.from_user.id, text='Event succesfully added')
        db.disconnect()


@bot.message_handler(content_types=['text'], func=lambda message: message.text == 'remove from gcalendar')
def remove_from_gcalendar(message):
    if not message.reply_to_message:
        bot.send_message(chat_id=message.from_user.id, text='You should reply event message with \'remove from gcalendar\' text to remove event!')
    else:
        db = DBConnection()
        db.connect()
        event = Event.from_text_to_gcalendar(message.reply_to_message.text)
        start = datetime.strptime(event["start"]["dateTime"], "%Y-%m-%dT%H:%M:%S")
        end = datetime.strptime(event["end"]["dateTime"], "%Y-%m-%dT%H:%M:%S")
        event_in_gcalendar = db.select('events_in_gcalendar', ['event_id'], chat_id=message.from_user.id)
        if db.record_exists('events_in_gcalendar', 'name', chat_id=message.from_user.id, name=event["summary"], start_date_time=start,
        end_date_time=end):
            Gcalendar.delete_event(event_in_gcalendar[0][0])
            db.delete('events_in_gcalendar', event_id=event_in_gcalendar[0][0])
            bot.send_message(chat_id=message.from_user.id, text='Event succesfully removed')
        else:
            bot.send_message(chat_id=message.from_user.id, text='Event is not in gcalendar!')
        db.disconnect()

@bot.message_handler(commands=['turn_on_autorefresh'])
def events_autorefresh(message):
    db = DBConnection()
    db.connect()
    if not db.record_exists('user_data', 'refresh_time', chat_id=message.from_user.id):
        bot.send_message(chat_id=message.from_user.id, text='autorefresh turned off\nplease choose autorefresh time first - /set_refresh_time')
        db.disconnect()
        return
    if not db.record_exists('user_tags', 'tag', chat_id=message.from_user.id):
        bot.send_message(chat_id=message.from_user.id, text='autorefresh turned off\ntags must be chosen first - /choose_tags')
        db.disconnect()
        return
    if not db.record_exists('user_data', 'event_interval_days'):
        bot.send_message(chat_id=message.from_user.id,
                         text='autorefresh turned off\nevent_interval must be chosen first - /choose_event_interval')
        db.disconnect()
        return
    if not db.record_exists('user_data', 'display_interval_days', chat_id=message.from_user.id):
        bot.send_message(chat_id=message.from_user.id,
                         text='autorefresh turned off\ndisplay_interval must be chosen first - /choose_display_interval')
        db.disconnect()
        return
    if not db.record_exists('user_data', 'location'):
        bot.send_message(chat_id=message.from_user.id,
                         text='autorefresh turned off\nlocation must be chosen first - /choose_location')
        db.disconnect()
        return

    db.update('user_data', 'is_auto_refreshed', True, chat_id=message.from_user.id)
    db.disconnect()
    notifications_thread = Thread(target=refresher, args=[message])
    notifications_thread.daemon = True
    notifications_thread.start()

def refresher(message):
    db = DBConnection()
    db.connect()
    bot.send_message(chat_id=message.from_user.id, text='autorefresh turned on')
    time = datetime.strptime(db.select('user_data', ['refresh_time'], chat_id=message.from_user.id)[0][0], "%H:%M:%S").time() 
    while True:
        if not db.record_exists('user_data', 'is_auto_refreshed', chat_id=message.from_user.id):
            db.disconnect()
            return
        last_refresh_date = str(db.select('user_data', ['last_events_refresh'], chat_id=message.from_user.id)[0][0])
        display_interval = db.select('user_data', ['display_interval_days'], chat_id=message.from_user.id)[0][0]
        if datetime.now().date() - datetime.fromisoformat(last_refresh_date).date() >= timedelta(days=display_interval) and datetime.now().time() >= time:
            show_events(message)  

@bot.message_handler(commands=['turn_off_autorefresh'])
def turn_off_autorefresh(message):
    db = DBConnection()
    db.connect()
    db.update('user_data', 'is_auto_refreshed', False, chat_id=message.from_user.id)
    db.disconnect()
    bot.send_message(chat_id=message.from_user.id, text='autorefresh turned off')

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8443, ssl_context=('webhook_cert.pem', 'webhook_key.key'))
