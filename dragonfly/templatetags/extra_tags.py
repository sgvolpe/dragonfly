import datetime, json, os
from django import template
from django.shortcuts import render

from dragonfly import Handyman

register = template.Library()

@register.filter
def to_json(value):
    print (value[:500])
    value = value.replace("'",'"')
    return json.loads(value)


@register.filter
def type_(value):
    return type(value)\

@register.filter
def get_elem_adjusted(value, el):

    return value[int(el) - 1]

@register.simple_tag
def my_tag(a, b, schedules, *args, **kwargs):

    leg = a[b]
    for sched in leg:
        sched_id = sched['ref']
        schedules[sched_id-1]


    return render(None, 'ota/test.html', context={'test':'chau'})
    return [{'departure': flight['departure']['airport'],
             'arrival': flight['arrival']['airport'],
             'dep_time': flight['departure']['time'],
             'arr_time': flight['arrival']['time'],
             } for flight in [schedules[sched['ref']-1] for sched in a[b]]]


@register.filter(name='subtract')
def subtract(value, arg):
    return int(value) - int(arg)

@register.filter(name='friendly_date')
def friendly_date(value):
    return str(datetime.datetime.strftime(datetime.datetime.strptime(value, "%Y-%m-%d"), '%d %b'))

@register.filter(name='parse_time')
def parse_time(value: str) -> str:
    value = int(value)
    h = value // 60
    m = str(value - h*60) + 'm '
    h = str(value // 60) + 'h '
    return h + m

@register.filter(name='cointains')
def cointains(string: str, substing:str) -> bool:
    return str(substing) in str(string)\

@register.filter(name='limit')
def limit(l: list, el_count:int) -> list:
    if el_count > len(l): return l
    return l[:el_count]


@register.filter(name='marketing_text')
def marketing_text(promo) -> str:
    return 'Enjoy one of our selected promotions with discounts'

@register.filter(name='marketing_text')
def marketing_text(promo) -> str:
    return 'Enjoy one of our selected promotions with discounts'

@register.filter(name='decode_name')
def decode_name(code: str) -> str:
    try: return Handyman.decode_city(code)
    except: return code

DEBUG = True
@register.filter(name='get_image')
def get_image(code: str) -> str:
    if DEBUG:
        print (f'{code}.jpg' )
        print (os.listdir('static/images/dragonfly/cities'))
    if f'{code}.jpg' in os.listdir('static/images/dragonfly/cities'):
        return f'static/images/dragonfly/cities/{code}.jpg'

    message = f'{code}.jpg not Found'
    email_body = f'<html><body><h1> Worth Check: get_image not found </h1><h4>{message}</h4></body></html>'

    Handyman.send_email(email_to='sgvolpe1@gmail.com', email_from='', email_body=email_body,
                        email_subject=f'Worth Check: get_image {code}.jpg not Found', attachments=[])
    return f'static/images/dragonfly/cities/default.jpg'

    return 'data:image/gif;base64,R0lGODlhAQABAIAAAHd3dwAAACH5BAAAAAAALAAAAAABAAEAAAICRAEAOw=='


@register.simple_tag
def range(offset: int, total: int, limit: int) -> list:

    return list(range(offset, total, limit))