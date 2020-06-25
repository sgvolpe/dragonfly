import datetime, functools, json, os, requests, smtplib, time

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd


from datetime import timedelta


def translate_iata(iata='EZE', what='airport'):
    cities = {'EZE': 'BUE', 'AEP': 'BUE'}
    if what == 'airport':
        try:
            return cities[iata]
        except Exception as e:
            return iata


def parse_date(raw_date):
    date_formats = ["%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y", "%Y.%m.%d", "%d.%m.%Y",
                    "%m.%d.%Y"]
    for date_format in date_formats:
        try:
            return datetime.datetime.strptime(datetime.datetime.strptime(str(raw_date), date_format).date().isoformat(),
                                              '%Y-%m-%d').date()
        except:
            pass


def add_days_to_date(raw_date: str, plus_days: int) -> str:
    return datetime.datetime.strftime(parse_date(raw_date) + timedelta(days=plus_days), '%Y-%m-%d')


def generate_date_pairs(base_date=datetime.datetime.now().date(), ap_list=[30, 60], los_list=[7, 14]):
    """Returns a list of dates based on base_date and the Advanced Purchase list provided"""

    return [[str((add_days_to_date(base_date, int(ap)))), str((add_days_to_date(base_date, int(ap) + int(los))))]
            for ap in ap_list for los in los_list]


def log(log_f_folder='LOGS', log_f_name='log.txt', to_write='START'):
    if log_f_folder not in os.listdir(os.getcwd()):
        os.makedirs(os.path.join(log_f_folder))
        log = open(os.path.join(log_f_folder, log_f_name), 'w')
        log.write('# # # LOG START # # #')
        log.close()

    log = open(os.path.join(log_f_folder, log_f_name), 'a')
    log.write(to_write + '\n')
    log.close()


def timer(func):
    """Print the runtime of the decorated function"""

    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        start_time = time.perf_counter()  # 1
        value = func(*args, **kwargs)
        end_time = time.perf_counter()  # 2
        run_time = end_time - start_time  # 3
        print(f"Finished {func.__name__!r} in {run_time:.4f} secs")
        return value

    return wrapper_timer


def function_log(func):
    """Print the runtime of the decorated function"""

    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        start_time = time.perf_counter()  # 1
        try:

            value = func(*args, **kwargs)

            end_time = time.perf_counter()  # 2
            run_time = end_time - start_time  # 3
            args_repr = [repr(a) for a in args]  # 1
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]  # 2
            signature = "|".join(args_repr + kwargs_repr)  # 3
            log(log_f_folder='LOGS', log_f_name='function_log.txt',
                to_write=f"{datetime.datetime.now()},{func.__name__!r},{run_time},{str(value)[:50]}, {signature}")
        except Exception as e:
            end_time = time.perf_counter()  # 2
            run_time = end_time - start_time  # 3
            args_repr = [repr(a) for a in args]  # 1
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]  # 2
            signature = "|".join(args_repr + kwargs_repr)  # 3
            log(log_f_folder='LOGS', log_f_name='function_log.txt',
                to_write=f"{datetime.datetime.now()},{func.__name__!r},{run_time},{str(e)}, {signature}")
            return e



        return value

    return wrapper_timer


def download_airports():
    url = 'https://raw.githubusercontent.com/datasets/airport-codes/master/data/airport-codes.csv'

    rs = requests.get(url)

    open('../Resources/ota/airports.csv', 'wb').write(rs.content)


def get_airports(text='New', limit=10):
    print (os.getcwd())

    df = pd.read_csv('static/resources/ota/airports_simple.csv') # todo: upper and title

    df['x'] = '(' + df['iata_code'] + ') ' + df['name'] + ', ' + df['municipality']
    if text != '*':
        df = df[df['x'].apply(lambda  x: x.upper()).str.contains(text.upper(), regex=False)]
    df = df.head(limit)
    data = [{'x': row['x'], 'iata': row['iata_code'] } for i, row in df.iterrows()]
    return data




def decode_city(iata: str) -> str:
    try:
        df = pd.read_csv('static/resources/ota/cities.csv') # todo: upper and title
        return df[df['IATA code'] == iata]['City name'].tolist()[0]
    except Exception as e:
        print (str(e))
        return iata


def save_cxr(cxr):
    rem = False
    if f'{cxr}.png' not in os.listdir(o_path):
        print(cxr)
        with open(f'{o_path}/{cxr}.png', 'wb') as handle:
            URL = f'https://www.toctocviajes.com/content/img/Airlines/{cxr}.png'
            print(URL)
            response = requests.get(URL, stream=True)
            response.raw.decode_content = True
            if '<!DOCTYPE html>' in response.text:
                rem = True
            else:
                print(response.text)
            if not response.ok:
                print(response)

            for block in response.iter_content(1024):
                if not block:
                    break

                    handle.write(block)

        if rem:
            os.remove(f'{o_path}/{cxr}.png')
        else:
            pass

def download_airline_icons(base_url):
    i_path = r'C:\Users\sg0216333\OneDrive - Sabre\- PrOjEcTs\river\river\static\images\ota\airline_logos_bu'
    o_path = r'C:\Users\sg0216333\OneDrive - Sabre\- PrOjEcTs\river\river\static\images\ota\airline_logos'
    def save_cxr(cxr):
        if f'{cxr}.ico' not in os.listdir(o_path):
            url = f'{base_url}/content/img/Airlines/{cxr}.png'
            print(url)
            r = requests.get(url, allow_redirects=True)
            if '<!DOCTYPE html>' in r.text:
                pass
            else:
                open(f'{o_path}/{cxr}.ico', 'wb').write(r.content)


    cxrs = [cxr.split('.')[0] for cxr in os.listdir(i_path)]

    for cxr in cxrs:
        save_cxr(cxr)

def get_credentials(what_for, creds_path=os.path.join('..', 'LOCAL', 'credentials.txt')):


    with open(creds_path) as json_file:

        json_creds = json.load(json_file, encoding='cp1252')

    json_file.close()
    return json_creds[what_for]


def send_email(email_from='sgvolpe1@gmail.com', email_to='sgvolpe1@gmail.com', email_subject="HTML Message",
               email_body="""<html><body><h1>Test Email</h1></body></html>""", attachments=[]):
    # Treat Message
    message = MIMEMultipart()
    message['From'] = email_from
    message['To'] = email_to
    message['Subject'] = email_subject
    msg1 = MIMEText(email_body, 'html')
    message.attach(msg1)

    # Treat Attachments
    for file_name in attachments:
        openfile = open(file_name, 'rb')
        mimref = MIMEBase('application', 'octet_stream')
        mimref.set_payload((openfile.read()))
        encoders.encode_base64(mimref)
        mimref.add_header('Content-Disposition', f'openfile;filename={file_name}')
        message.attach(mimref)

    # Treat Connection
    creds = get_credentials(what_for='email')
    host, port, username, password = creds['server'], creds['port'], creds['username'], creds['password']
    connection = smtplib.SMTP(host, port)
    connection.ehlo()
    connection.starttls()

    connection.login(username, password)
    connection.sendmail(email_from, email_to, message.as_string())
    connection.quit()


# send_email( attachments=['../Resources/test.txt'])

