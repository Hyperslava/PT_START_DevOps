import logging
import re
import os
import paramiko
import psycopg2

from telegram import Update, ParseMode, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

from pathlib import Path

token = os.getenv('TOKEN')
host = os.getenv('RM_HOST')
port = os.getenv('RM_PORT')
username = os.getenv('RM_USER')
password = os.getenv('RM_PASSWORD')
db_host = os.getenv('RM_HOST')
db_port = os.getenv('DB_PORT')
db_database = os.getenv('DB_DATABASE')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Подключение логирования
logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет, {user.full_name}!\nВведи /help, чтобы узнать о командах')


def helpCommand(update: Update, context):
    update.message.reply_text('''
Список команд:

/find_emails - поиск email-адресов в введённом тексте
/find_phone_number - поиск телефонных номеров в введённом тексте
/verify_password - проверка сложности введённого пароля

Команды для мониторинга Linux-системы:

/get_release - получить информацию о релизе
/get_uname - информация об архитектуре процессора, имени хоста системы и версии ядра
/get_uptime - время работы
/get_df - состояние файловой системы
/get_free - состояние оперативной памяти
/get_mpstat - производительность системы
/get_w - работающие в данной системе пользователи
/get_auths - последние 10 входов в систему
/get_critical - последние 5 критических событий
/get_ps - запущенные процессы
/get_ss - используемые порты
/get_apt_list - информация об установленных пакетах
/get_services - запущенные сервисы
/get_repl_data - получить логи репликации базы данных
/get_emails - получить email-адреса из базы данных
/get_phone_numbers - получить телефонные номера из базы данных
''')


def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'findPhoneNumbers'


def findEmailsCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска email-адресов: ')

    return 'findEmails'


def verifyPasswordCommand(update: Update, context):
    update.message.reply_text('Введите пароль: ')

    return 'verifyPassword'


def findEmails(update: Update, context):
    user_input = update.message.text
    emailRegex = re.compile(r'(([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+))')
    emailList = emailRegex.findall(user_input)
    if not emailList:
        update.message.reply_text('Email-адреса не найдены.')
        return
    emailsAdresses = ''
    for i in range(len(emailList)):
        emailsAdresses += f'{i+1}. {emailList[i][0]}\n'
    
    context.user_data['found_data'] = emailList
    context.user_data['data_type'] = 'email'

    update.message.reply_text(f'{emailsAdresses}\nСохранить в базу данных? (да/нет)')
    return 'saveToDatabase'


def findPhoneNumbers(update: Update, context):
    user_input = update.message.text  # Получение текста, содержащего(или нет) номера телефонов

    phoneNumRegex = re.compile(r'((\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})')

    phoneNumberList = phoneNumRegex.findall(user_input)  # Поиск номеров телефонов

    if not phoneNumberList:  # Обработка случая, когда номеров телефонов нет
        update.message.reply_text('Телефонные номера не найдены')
        return  # Завершение выполнения функции

    phoneNumbers = ''  # Создание строки, в которую будут записываться номера телефонов
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{i+1}. {phoneNumberList[i][0]}\n'  # Запись очередного номера

    context.user_data['found_data'] = phoneNumberList
    context.user_data['data_type'] = 'phone'
    update.message.reply_text(f'{phoneNumbers}\nСохранить в базу данных? (да/нет)')  # Отправка сообщения пользователю
    return 'saveToDatabase'


def saveDataToDatabase(update: Update, context):
    user_input = update.message.text.lower()
    if user_input == 'да':
        found_data = context.user_data.get('found_data', [])
        data_type = context.user_data.get('data_type', '')

        if not found_data:
            update.message.reply_text('❌ Ошибка: данные не найдены.')
            return ConversationHandler.END
        try:
            connection = psycopg2.connect(
                host=db_host,
                port=db_port,
                database=db_database,
                user=db_user,
                password=db_password,
                sslmode='disable'
            )
            cursor = connection.cursor()

            if data_type == 'phone':
                for item in found_data:
                    phone_number = item[0]
                    cursor.execute("INSERT INTO phone_numbers (phone) VALUES (%s)", (phone_number,))
            elif data_type == 'email':
                for item in found_data:
                    email = item[0]
                    cursor.execute("INSERT INTO emails (email) VALUES (%s)", (email,))
            
            connection.commit()
            update.message.reply_text('✅ Данные успешно сохранены в базу данных.')
        except Exception as e:
            update.message.reply_text(f'❌ Ошибка при сохранении данных:\n{e}')
        finally:
            if connection:
                cursor.close()
                connection.close()
    elif user_input == 'нет':
        update.message.reply_text('Данные не будут сохранены.')
    else:
        update.message.reply_text('Пожалуйста, введите "да" или "нет":')
        return 'saveToDatabase'
    return ConversationHandler.END


def verifyPassword(update: Update, context):
    user_input = update.message.text

    passwordRegex = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()]).{8,}$')

    if passwordRegex.match(user_input):
        update.message.reply_text('Пароль сложный')
    else:
        update.message.reply_text('Пароль простой')
    return ConversationHandler.END


def getDataFromDatabase(update: Update, context):
    update.message.reply_text('Подключение к базе данных...')
    command = update.message.text
    commands = {
        '/get_emails': ('SELECT * FROM emails', 'Список адресов электронной почты:'),
        '/get_phone_numbers': ('SELECT * FROM phone_numbers', 'Список телефонных номеров:')
    }
    try:
        connection = psycopg2.connect(
            host=db_host, port=db_port,
            database=db_database, user=db_user,
            password=db_password, sslmode='disable'
            )
        cur = connection.cursor()
        query = commands[command][0]
        cur.execute(query)
        query_results = cur.fetchall()
        text = commands[command][1] + '\n' + '\n'.join(['. '.join(map(str, x)) for x in query_results])
        update.message.reply_text(text)
    except Exception as e:
        update.message.reply_text(f'❌ Ошибка:\n{e}')
    finally:
        connection.close()
        cur.close()
        return ConversationHandler.END


def getTextData(update: Update, context):
    commands = {
        '/get_release': 'cat /etc/*release',
        '/get_uname': 'uname -a',
        '/get_uptime': 'uptime',
        '/get_df': 'df -h',
        '/get_free': 'free -h',
        '/get_w': 'w',
        '/get_auths': 'last -n 10',
        '/get_critical': 'journalctl -n 5 -p 2',
        '/get_ps': 'ps',
        '/get_services': 'service --status-all | grep "\[ + \]"',
    }
    command = update.message.text
    update.message.reply_text('Подключение к машине...')
    try:
        client.connect(hostname=host, username=username, password=password, port=port)
        update.message.reply_text('✅ Подключение к машине успешно. Сбор информации...')
        stdin, stdout, stderr = client.exec_command(commands[command])
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            error = stderr.read().decode()
            update.message.reply_text(f'❌ Ошибка выполнения команды:\n{error}')
            return
        data = stdout.read() + stderr.read()
        data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
        if command in ['/get_df', '/get_w', '/get_auths']:
            update.message.reply_text(f'<pre>{data}</pre>', parse_mode=ParseMode.HTML)
        elif command == '/get_critical':
            if '-- No entries --' in data:
                update.message.reply_text('Не найдено критических ошибок системы.')
        else:
            update.message.reply_text(data)
    except Exception as e:
        update.message.reply_text(f'❌ Ошибка при подключении к машине.{e}')
    finally:
        client.close()
        return ConversationHandler.END


def getFileData(update: Update, context):
    commands = {
        '/get_mpstat': ('mpstat > mpstat.txt', 'mpstat.txt', 'Информация о производительности системы'),
        '/get_ss': ('ss -tulpn > ports.txt', 'ports.txt', 'Список используемых портов'),
        '/get_repl_data': (
            f'echo {password} | sudo -S grep -i "replication" /var/log/postgresql/postgresql-*.log > repl_log.txt',
              'repl_log.txt', 'Логи репликации PostgreSQL'
              )
    }
    command = update.message.text
    update.message.reply_text('Подключение к машине...')
    try:
        client.connect(hostname=host, username=username, password=password, port=port)
        update.message.reply_text('✅ Подключение к машине успешно. Сбор информации...')
        stdin, stdout, stderr = client.exec_command(commands[command][0])
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            error = stderr.read().decode()
            update.message.reply_text(f'❌ Ошибка выполнения команды:\n{error}')
            return
        sftp = client.open_sftp()
        remote_file = local_file = commands[command][1]
        sftp.get(remote_file, local_file)

        sftp.stat(remote_file)
        file_size = sftp.stat(remote_file).st_size
        if file_size == 0:
            update.message.reply_text('Файл пустой.')
            return

        with open(local_file, 'rb') as document:
            update.message.reply_document(
                document=document,
                caption=commands[command][-1]
            )
    except Exception:
        update.message.reply_text(f'❌ Ошибка при подключении к машине.')
    finally:
        client.close()
        return ConversationHandler.END

def getAptListCommand(update: Update, context):
    update.message.reply_text('Введите имя установленного пакета, информацио о котором нужно получить, или "all", чтобы получить список всех установленных пакетов:')
    return 'getAptList'

def getAptList(update: Update, context):
    user_input = update.message.text
    update.message.reply_text('Подключение к машине...')
    try:
        client.connect(hostname=host, username=username, password=password, port=port)
        update.message.reply_text('✅ Подключение успешно. Сбор информации...')

        if user_input == 'all':
            command = 'apt list --installed > apt_list.txt'
            remote_file = local_file = 'apt_list.txt'
        else:
            command = f'apt list --installed | grep -i {user_input} > apt_list_{user_input}.txt'
            remote_file = local_file = f'apt_list_{user_input.lower()}.txt'

        stdin, stdout, stderr = client.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            error = stderr.read().decode()
            update.message.reply_text(f'❌ Ошибка выполнения команды: {error}')
            return
        sftp = client.open_sftp()
        sftp.stat(remote_file)
        file_size = sftp.stat(remote_file).st_size
        if file_size == 0:
            update.message.reply_text('Файл пустой.')
            return

        sftp.get(remote_file, local_file)
        with open(local_file, 'rb') as document:
            update.message.reply_document(
                document=document,
                caption='Список всех установленных пакетов' if user_input == 'all' else f'Список установленных пакетов {user_input}'
            )

    except IOError as e:
        update.message.reply_text(f'❌ Файл не найден на сервере: {str(e)}')
    except Exception:
        update.message.reply_text('❌ Ошибка подключения к машине.')
    finally:
        sftp.close()
        client.close()
        return ConversationHandler.END


def echo(update: Update, context):
    update.message.reply_text(update.message.text)


def main():
    updater = Updater(token, use_context=True)

    # Получение диспетчера для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчики диалога
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'findPhoneNumbers': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'saveToDatabase': [MessageHandler(Filters.text & ~Filters.command, saveDataToDatabase)]
        },
        fallbacks=[]
    )
    convHandlerFindEmails = ConversationHandler(
        entry_points=[CommandHandler('find_emails', findEmailsCommand)],
        states={
            'findEmails': [MessageHandler(Filters.text & ~Filters.command, findEmails)],
            'saveToDatabase': [MessageHandler(Filters.text & ~Filters.command, saveDataToDatabase)]
        },
        fallbacks=[]
    )
    convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifyPasswordCommand)],
        states={
            'verifyPassword': [MessageHandler(Filters.text & ~Filters.command, verifyPassword)],
        },
        fallbacks=[]
    )
    convHandlerAptList = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', getAptListCommand)],
        states={
            'getAptList': [MessageHandler(Filters.text & ~Filters.command, getAptList)],
        },
        fallbacks=[]
    )
	# Регистрация обработчиков команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(CommandHandler("get_release", getTextData))
    dp.add_handler(CommandHandler("get_uname", getTextData))
    dp.add_handler(CommandHandler("get_uptime", getTextData))
    dp.add_handler(CommandHandler("get_df", getTextData))
    dp.add_handler(CommandHandler("get_free", getTextData))
    dp.add_handler(CommandHandler("get_mpstat", getFileData))
    dp.add_handler(CommandHandler("get_w", getTextData))
    dp.add_handler(CommandHandler("get_auths", getTextData))
    dp.add_handler(CommandHandler("get_critical", getTextData))
    dp.add_handler(CommandHandler("get_ps", getTextData))
    dp.add_handler(CommandHandler("get_ss", getFileData))
    dp.add_handler(CommandHandler("get_services", getTextData))
    dp.add_handler(CommandHandler("get_repl_data", getFileData))
    dp.add_handler(CommandHandler("get_emails", getDataFromDatabase))
    dp.add_handler(CommandHandler("get_phone_numbers", getDataFromDatabase))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmails)
    dp.add_handler(convHandlerVerifyPassword)
    dp.add_handler(convHandlerAptList)
		
	# Регистрация обработчика текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
		
	# Запуск бота
    updater.start_polling()

	# Остановка бота при нажатии Ctrl+C
    updater.idle()

if __name__ == '__main__':
    main()