from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime
import json, os, string, sys, threading, logging, time, re, random
import openai

#OpenAI API key
aienv = os.getenv('OPENAI_KEY')
if aienv == None:
    openai.api_key = "ENTER YOUR API KEY HERE"
else:
    openai.api_key = aienv
print(aienv)

#Telegram bot key
tgenv = os.getenv('TELEGRAM_KEY')
if tgenv == None:
    tgkey = "ENTER YOUR TELEGRAM TOKEN HERE"
else:
    tgkey = tgenv
print(tgenv)



# Lots of console output
debug = True

# User Session timeout
timstart = 300
tim = 1

#Defaults
user = ""
running = False
cache = None
qcache = None
chat_log = None
botname = 'Harshit ethic'
username = 'harshitethic_bot'
# Max chat log length (A token is about 4 letters and max tokens is 2048)
max = int(3000)


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


completion = openai.Completion()


##################
#Command handlers#
##################
def start(bot, update):
    """Send a message when the command /start is issued."""
    global chat_log
    global qcache
    global cache
    global tim
    global botname
    global username
    left = str(tim)
    if tim == 1:
        chat_log = None
        cache = None
        qcache = None
        botname = 'chatGPT'
        username = 'chatgpttaherbot'
        update.message.reply_text('مرحبا')
        return 
    else:
        update.message.reply_text('أتحدث حاليا إلى شخص آخر. هل يمكنك الانتظار من فضلك؟ ' + left + ' ثواني?')
        return


def help(bot, update):
    """ارسل رسالة عند استخدام امر /help  """
    update.message.reply_text('[/reset] إعادة تعيين المحادثة,\n [/retry] أعد النظر في الناتج الأخير,\n [/username name] تعيين اسمك على الروبوت، الافتراضي هو "إنسان",\n [/botname name] تعيين اسم حرف برامج الروبوت، الافتراضي هو "AI"')


def reset(bot, update):
    """ارسل رسالة عند استخدام  /reset """
    global chat_log
    global cache
    global qcache
    global tim
    global botname
    global username
    left = str(tim)
    if user == update.message.from_user.id:
        chat_log = None
        cache = None
        qcache = None
        botname = 'chatGPT'
        username = 'chatgpttaherbot'
        update.message.reply_text('تمت إعادة تعيين البوت، أرسل رسالة!')
        return
    if tim == 1:
        chat_log = None
        cache = None
        qcache = None
        botname = 'chatGPT'
        username = 'chatgpttaherbot'
        update.message.reply_text('تمت إعادة تعيين البوت، أرسل رسالة!')
        return 
    else:
        update.message.reply_text('أتحدث حاليا إلى شخص آخر. هل يمكنك الانتظار من فضلك؟ ' + left + ' ثواني?')
        return


def retry(bot, update):
    """ارسل امر /retry """
    global chat_log
    global cache
    global qcache
    global tim
    global botname
    global username
    left = str(tim)
    if user == update.message.from_user.id:
        new = True
        comput = threading.Thread(target=wait, args=(bot, update, botname, username, new,))
        comput.start()
        return
    if tim == 1:
        chat_log = None
        cache = None
        qcache = None
        botname = 'chatGPT'
        username = 'chatgpttaherbot'
        update.message.reply_text('أرسل رسالة!')
        return 
    else:
        update.message.reply_text('أتحدث حاليا إلى شخص آخر. هل يمكنك الانتظار من فضلك؟ ' + left + ' ثواني?')
        return

def runn(bot, update):
    """أرسل رسالة عند استلام رسالة."""
    new = False
    global botname
    global username
    if "/botname " in update.message.text:
        try:
            string = update.message.text
            charout = string.split("/botname ",1)[1]
            botname = charout
            response = "تم تعيين اسم حرف الروبوت على: " + botname
            update.message.reply_text(response)
        except Exception as e:
            update.message.reply_text(e)
        return
    if "/username " in update.message.text:
        try:
            string = update.message.text
            userout = string.split("/username ",1)[1]
            username = userout
            response = "تم تعيين اسم شخصيتك على: " + username
            update.message.reply_text(response)
        except Exception as e:
            update.message.reply_text(e)
        return
    else:
        comput = threading.Thread(target=interact, args=(bot, update, botname, username, new,))
        comput.start()


def wait(bot, update, botname, username, new):
    global user
    global chat_log
    global cache
    global qcache
    global tim
    global running
    if user == "":
        user = update.message.from_user.id
    if user == update.message.from_user.id:
        tim = timstart
        compute = threading.Thread(target=interact, args=(bot, update, botname, username, new,))
        compute.start()
        if running == False:
            while tim > 1:
                running = True
                time.sleep(1)
                tim = tim - 1
            if running == True:
                chat_log = None
                cache = None
                qcache = None
                user = ""
                username = 'chatgpttaherbot'
                botname = 'chatGPT'
                update.message.reply_text('تم تشغيل المؤقت، وتمت إعادة تعيين الروبوت إلى الإعدادات الافتراضية.')
                running = False
    else:
        left = str(tim)
        update.message.reply_text('أتحدث حاليا إلى شخص آخر. هل يمكنك الانتظار من فضلك؟ ' + left + ' ثواني?')


################
#Main functions#
################
def limit(text, max):
    if (len(text) >= max):
        inv = max * 10
        print("تقليل مدة سجل الدردشة... يمكن أن يكون هذا عربات التي تجرها الدواب بعض الشيء.")
        nl = text[inv:]
        text = re.search(r'(?<=\n)[\s\S]*', nl).group(0)
        return text
    else:
        return text


def ask(username, botname, question, chat_log=None):
    if chat_log is None:
        chat_log = 'فيما يلي محادثة بين مستخدمين اثنين:\n\n'
    now = datetime.now()
    ampm = now.strftime("%I:%M %p")
    t = '[' + ampm + '] '
    prompt = f'{chat_log}{t}{username}: {question}\n{t}{botname}:'
    response = completion.create(
        prompt=prompt, engine="text-curie-001", stop=['\n'], temperature=0.7,
        top_p=1, frequency_penalty=0, presence_penalty=0.6, best_of=3,
        max_tokens=500)
    answer = response.choices[0].text.strip()
    return answer
    # fp = 15 pp= 1 top_p = 1 temp = 0.9

def append_interaction_to_chat_log(username, botname, question, answer, chat_log=None):
    if chat_log is None:
        chat_log = 'فيما يلي محادثة بين مستخدمين اثنين:\n\n'
    chat_log = limit(chat_log, max)
    now = datetime.now()
    ampm = now.strftime("%I:%M %p")
    t = '[' + ampm + '] '
    return f'{chat_log}{t}{username}: {question}\n{t}{botname}: {answer}\n'

def interact(bot, update, botname, username, new):
    global chat_log
    global cache
    global qcache
    print("==========START==========")
    tex = update.message.text
    text = str(tex)
    analyzer = SentimentIntensityAnalyzer()
    if new != True:
        vs = analyzer.polarity_scores(text)
        if debug == True:
            print("معنويات المدخلات:\n")
            print(vs)
        if vs['neg'] > 1:
            update.message.reply_text('هل يمكننا التحدث عن شيء آخر؟')
            return
    if new == True:
        if debug == True:
            print("Chat_LOG Cache is...")
            print(cache)
            print("Question Cache is...")
            print(qcache)
        chat_log = cache
        question = qcache
    if new != True:
        question = text
        qcache = question
        cache = chat_log
    #update.message.reply_text('Computing...')
    try:
        answer = ask(username, botname, question, chat_log)
        if debug == True:
            print("Input:\n" + question)
            print("Output:\n" + answer)
            print("====================")
        stripes = answer.encode(encoding=sys.stdout.encoding,errors='ignore')
        decoded = stripes.decode("utf-8")
        out = str(decoded)
        vs = analyzer.polarity_scores(out)
        if debug == True:
            print("معنويات الناتج:\n")
            print(vs)
        if vs['neg'] > 1:
            update.message.reply_text('لا أعتقد أنني أستطيع أن أقدم لك إجابة جيدة على هذا. استخدم /retry للحصول على مخرجات إيجابية.')
            return
        update.message.reply_text(out)
        chat_log = append_interaction_to_chat_log(username, botname, question, answer, chat_log)
        if debug == True:
            #### Print the chat log for debugging
            print('-----PRINTING CHAT LOG-----')
            print(chat_log)
            print('-----END CHAT LOG-----')
    except Exception as e:
            print(e)
            errstr = str(e)
            update.message.reply_text(errstr)


def error(bot, update):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update)


def main():
    """Start the bot."""

    updater = Updater(tgkey, use_context=False)
    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("reset", reset))
    dp.add_handler(CommandHandler("retry", retry))
    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, runn))
    # log all errors
    dp.add_error_handler(error)
    # Start the Bot
    updater.start_polling()
   
    updater.idle()


if __name__ == '__main__':
    main()
