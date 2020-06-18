import datetime, json
from django import template

from django.shortcuts import render
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


@register.simple_tag
def range(offset: int, total: int, limit: int) -> list:
    print (offset, total, limit)
    return list(range(offset, total, limit))