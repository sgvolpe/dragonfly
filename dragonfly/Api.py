import base64, functools, json, os, requests, time
try: import numpy as np
except: pass

from .Handyman import add_days_to_date, function_log, translate_iata
DEBUG = True

def bfm_log(**kwargs):
    bfm_log = open('../dragonfly/static/resources/ota/logs/bfm_log.log', 'a')
    sep = '|'
    bfm_log.write(sep.join([str(v) for v in kwargs.values()]) + '\n')
    bfm_log.close()





@function_log
def parse_response(http_response):
    # TODO: check if http is 200

    # version messages statistics scheduleDescs taxDescs taxSummaryDescs fareComponentDescs validatingCarrierDescs baggageAllowanceDescs legDescs
    try:
        response_json = json.loads(http_response.text)
        if 'groupedItineraryResponse' not in response_json: raise Exception('groupedItineraryResponse not in response')
        response = response_json['groupedItineraryResponse']
    except Exception as e:
        raise Exception(f'Could not parse json: {str(e)}')

    itineraries = {}
    if 'itineraryGroups' not in response:
        raise Exception('No Options Found')

    baggage_allowance_descriptions = response['baggageAllowanceDescs']

    for itin_group in response['itineraryGroups']:
        departure_dates = []
        arrival_dates = []
        for leg_desc in itin_group['groupDescription']['legDescriptions']:
            departure_dates.append(leg_desc['departureDate'])
            arrival_dates.append('PENDING***')

        for itin in itin_group['itineraries']:

            itinerary = {'legs': itin['legs']}
            itineraries[itin['id'] - 1] = itinerary  # to start in 0

            pricing_info = []

            for price_info in itin['pricingInformation']:
                itinerary['currency'] = price_info['fare']['totalFare']['currency']
                itinerary['total_price'] = price_info['fare']['totalFare']['totalPrice']

                for passenger_fare in price_info['fare']['passengerInfoList']:
                    rbds, cabins = [], []
                    ptc = passenger_fare['passengerInfo']['passengerType']
                    pax_count = passenger_fare['passengerInfo']['passengerNumber']
                    #pax_count = passenger_fare['passengerInfo']['passengerNumber']
                    non_ref = passenger_fare['passengerInfo']['nonRefundable']
                    bag_infos = passenger_fare['passengerInfo']['baggageInformation']

                    baggage_allowance = []
                    for bag_info in bag_infos:
                        for _ in bag_info['segments']:
                            all = baggage_allowance_descriptions[bag_info['allowance']['ref'] - 1]
                            if 'pieceCount' in all:
                                baggage_allowance.append(all['pieceCount'])
                            else:
                                baggage_allowance.append(1)

                    try:
                        for fare_component in passenger_fare['passengerInfo']['fareComponents']:
                            segs = fare_component['segments']

                            rbds += [seg['segment']['bookingCode'] for seg in segs]
                            cabins += [seg['segment']['cabinCode'] for seg in segs]
                            meals = [seg['segment']['mealCode'] if 'meals' in seg['segment'] else 'no' for seg in segs]

                    except Exception as e:
                        print(f'error: {str(e)}')

                    pricing_info.append({'ptc': ptc, 'pax_count': pax_count, 'non_ref': non_ref,
                                         'segs': segs, 'rbds': rbds, 'cabins': cabins, 'meals': meals,

                                         })


            passenger_count, seat_count = 0, 0
            for pi in pricing_info:
                passenger_count += pi['pax_count']
                if pi['ptc'] != 'INF': seat_count += pi['pax_count']

            itinerary['bags'] = baggage_allowance
            itinerary['pricing_info'] = pricing_info
            itinerary['passenger_count'] = passenger_count
            itinerary['seat_count'] = seat_count



            for pi in pricing_info:
                non_ref = pi['non_ref']

            flights = []
            flight_count = []
            for id, leg_id in enumerate(itin['legs']):
                schedules = response['legDescs'][leg_id['ref'] - 1]['schedules']
                flight_count.append(len(schedules))
                for sched_i, schedule in enumerate(schedules):
                    flight = response['scheduleDescs'][schedule['ref'] - 1]
                    flight_details = {'departure_airport': flight['departure']['airport'],
                                      'departure_time': flight['departure']['time'][:5],
                                      'arrival_airport': flight['arrival']['airport'],
                                      'arrival_time': flight['arrival']['time'][:5],
                                      'carrier': flight['carrier']['marketing'],
                                      'flight_number': flight['carrier']['marketingFlightNumber'],
                                      'rbd': pricing_info[0]['rbds'][sched_i],
                                      'cabin': pricing_info[0]['cabins'][sched_i],
                                      'departure_date': departure_dates[id],
                                      'arrival_date': 'empty',
                                      'elapsed_time': flight['elapsedTime'],


                                      }

                    if 'departureDateAdjustment' in flight:
                        flight_details['departure_date'] = add_days_to_date(flight_details['departure_date'],
                                                                            flight['departureDateAdjustment'])

                    if 'dateAdjustment' in flight['departure']:
                        flight_details['departure_date'] = add_days_to_date(flight_details['departure_date'],
                                                                            flight['departure']['dateAdjustment'])

                    flight_details['arrival_date'] = flight_details['departure_date']

                    if 'dateAdjustment' in flight['arrival']:
                        flight_details['arrival_date'] = add_days_to_date(flight_details['arrival_date'],
                                                                          flight['arrival']['dateAdjustment'])

                    flights.append(flight_details)
                    itinerary['flights'] = flights

                itinerary['itin_carriers'] = '-'.join([f['carrier'] for f in flights])
                from collections import Counter
                carrier_count = Counter(c for c in itinerary['itin_carriers'].split('-'))
                count_carrier = {v: k for k, v in carrier_count.items()}
                itinerary['main_carrier'] = count_carrier[max(count_carrier.keys())]
                itinerary['travel_time'] = sum([f['elapsed_time'] for f in flights])

                itinerary['itinerary_origin'] = translate_iata(flights[0]['departure_airport'])

                itinerary['itinerary_departure_time'] = flights[0]['departure_time'][:5]
                itinerary['itinerary_arrival_time'] = flights[-1]['arrival_time'][:5]
                itinerary['flight_count'] = flight_count

                itinerary['itinerary_destination'] = translate_iata(
                    flights[flight_count[0] - 1]['arrival_airport'])  # TODO: RT OW only

    return itineraries


@function_log
def get_token(url="https://api-crt.cert.havail.sabre.com/v2/auth/token", parameters={}, version='v1'):
    # return 'T1RLAQLS8yzTJaFHKCoZ2Qkcz/jHW+WMTRB10L3gp0il+ogZicb2F+m+AADAuqzuwwKEPV6sedn5nsR4F5GqZBu800PhKGd7CBqILfVKRyDsEGTrcMTqKoJU99t+tTPcCeMpudKwPm1GZNgXx18NkDRRUDt8zlkH8G1L9cj0cw7LLlTvaWbWN7SsjL2rvIDPxQsMTWhiNyK2B9ABqtt/AnddM01zTiz4V+WGbnr3n1sv5gANPKwMlU9xoW8sNQBInnNREKcGCrTccwhopKiEPScygsNkkSEPL/MDelkdcr4cEyvt7qNMSOxCCnYE'
    print()
    print('Getting Token')
    user = r'8h2xrynur03b7rq5'  # parameters["user"]
    group = r'DEVCENTER'  # parameters["group"]
    domain = r'EXT'  # parameters["domain"]
    password = r'5KjfNt7W'  # parameters["password"]
    encodedUserInfo = base64.b64encode(f'V1:{user}:{group}:{domain}'.encode('ascii'))
    encodedPassword = base64.b64encode(password.encode('ascii'))
    encodedSecurityInfo = str(base64.b64encode(encodedUserInfo + ":".encode('ascii') + encodedPassword))
    print(encodedSecurityInfo)
    print(f'V1:{user}:{group}:{domain}'.encode('ascii'))

    data = {'grant_type': 'client_credentials'}
    headers = {'content-type': 'application/x-www-form-urlencoded ',
               'Authorization': 'Basic VmpFNk9HZ3llSEo1Ym5WeU1ETmlOM0p4TlRwRVJWWkRSVTVVUlZJNlJWaFU6TlV0cVprNTBOMWM9',
               'Accept-Encoding': 'gzip,deflate'}
    print(headers)
    response = requests.post(url, headers=headers, data=data)
    if (response.status_code != 200):
        print("ERROR: I couldnt authenticate")
        print(response.text)

    token = json.loads(response.text)["access_token"]
    print(token)
    return token


def get_persona(passengers={'ADT': 1}):
    if ('CNN' in passengers and passengers['CNN'] > 0) | ('INF' in passengers and passengers['INF'] > 0):
        return 'FAMILY'
    else:
        return 'STANDARD'


# @log_search
@function_log
def send_bfm(origins, destinations, dates, adt, cnn=0, inf=0, options_limit=10, session_id=''):
    if DEBUG: print (f'**********SENDING BFM: {session_id}')
    sep = ','
    standard_time = '12:00:00'

    token = get_token()
    payload = open('../dragonfly/static/resources/ota/bfm_payloads/standard_rq.txt').read()
    payload = json.loads(payload)
    if origins[-1] == ',': origins = origins[:-1]
    if destinations[-1] == ',': destinations = destinations[:-1]
    if dates[-1] == ',': dates = dates[:-1]
    origins, destinations, dates = origins.split(sep), destinations.split(sep), dates.split(sep)

    if DEBUG: print(f'Doing BFM for: {origins, destinations, dates}')
    payload['OTA_AirLowFareSearchRQ']['OriginDestinationInformation'] = []
    for i, _ in enumerate(origins):
        ond = {'OriginLocation': {'LocationCode': origins[i]},
               'DestinationLocation': {'LocationCode': destinations[i]},
               'DepartureDateTime': f'{dates[i]}T{standard_time}',
               'RPH': str(i)
               }

        payload['OTA_AirLowFareSearchRQ']['OriginDestinationInformation'].append(ond)

        """payload['OTA_AirLowFareSearchRQ']['OriginDestinationInformation'][0]['OriginLocation']['LocationCode'] = origins[i]
        payload['OTA_AirLowFareSearchRQ']['OriginDestinationInformation'][0]['DestinationLocation']['LocationCode'] = destinations[i]
        payload['OTA_AirLowFareSearchRQ']['OriginDestinationInformation'][0]['DepartureDateTime'] = f'{dates[i]}T{standard_time}'"""

        if len(origins) == 1 and len(dates) == 2:  # Roundtrip
            ond = {'OriginLocation': {'LocationCode': destinations[i]},
                   'DestinationLocation': {'LocationCode': origins[i]},
                   'DepartureDateTime': f'{dates[i + 1]}T{standard_time}',
                   'RPH': "1"
                   }
            payload['OTA_AirLowFareSearchRQ']['OriginDestinationInformation'].append(ond)
            """payload['OTA_AirLowFareSearchRQ']['OriginDestinationInformation'][1]['OriginLocation']['LocationCode'] = origins[i]
            payload['OTA_AirLowFareSearchRQ']['OriginDestinationInformation'][1]['DestinationLocation']['LocationCode'] = destinations[i]
            payload['OTA_AirLowFareSearchRQ']['OriginDestinationInformation'][1]['DepartureDateTime'] = f'{dates[i+1]}T{standard_time}'"""

    # passengers = []
    codes = ['ADT', 'CNN', 'INF']
    for id, ptc in enumerate([adt, cnn, inf]):
        if ptc > 0:
            payload['OTA_AirLowFareSearchRQ']['TravelerInfoSummary']['AirTravelerAvail'][0][
                "PassengerTypeQuantity"].append({"Code": codes[id], "Quantity": ptc})

    payload = json.dumps(payload)

    url = "https://api-crt.cert.havail.sabre.com/v2/offers/shop"
    headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + token}

    response = requests.post(url, headers=headers, data=payload)

    if response.status_code != 200:
        print(response.text)
        bfm_log(origins=origins, destinations=destinations, dates=dates, options_limit=options_limit,
                status=response.status_code,
                business_error='')
        if response.status_code == 400:
            with open('static/ota/rq.txt', 'w') as rq:
                rq.write(payload)
            with open('static/ota/rs.txt', 'w') as rs:
                rs.write(response.text)
            raise Exception(f'HTTP Error on sending BFM: {response.text}')
        if response.status_code == 401:
            with open('static/ota/rq.txt', 'w') as rq:
                rq.write(payload)
            with open('static/ota/rs.txt', 'w') as rs:
                rs.write(response.text)
            raise Exception(f'HTTP Error on sending BFM: {str(response.status_code), response.text}')
            get_token()
        else:
            with open('static/ota/rq.txt', 'w') as rq:
                rq.write(payload)
            with open('static/ota/rs.txt', 'w') as rs:
                rs.write(response.text)
            raise Exception(f'HTTP Error on sending BFM: {str(response.status_code), response.text}')

    with open('static/ota/rq.txt', 'w') as rq:
        rq.write(payload)
    with open('static/ota/rs.txt', 'w') as rs:
        rs.write(response.text)

    try:
        results = parse_response(response)
        results = {k: v for k, v in results.items() if k < options_limit}
        return results

    except Exception as e:
        raise Exception(f'Error on Searching: {str(e)}')
    finally:
        bfm_log(origins=origins, destinations=destinations, dates=dates, options_limit=options_limit,
                status=response.status_code,
                business_error='')




#TODO:
@function_log
def book(session_id='') -> str:
    return np.random.choice(['success', 'price_jump', 'other'], p=[.6, .2, .1])
