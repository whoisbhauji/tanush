

from flask import Flask, flash, jsonify, redirect, render_template, request, session, Response
import datetime
import json
import requests
import re

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SECRET_KEY"] = "finna"

pincode = '600004'

"""
# https://api.telegram.org/bot1875782260:AAFb-WNmExM-Uaf6MwCYhrhgeeBTFPHULlQ/getMe
# https://api.telegram.org/bot1875782260:AAFb-WNmExM-Uaf6MwCYhrhgeeBTFPHULlQ/sendMessage?chat_id=1164516088&text="Hello vaxxer!"
# https://api.telegram.org/bot1875782260:AAFb-WNmExM-Uaf6MwCYhrhgeeBTFPHULlQ/setWebhook?url=https://49bf92ba50f9.ngrok.io
"""


def write_json(data, filename="resp.json"):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def get_slots(pin='600004', slotdate='datetime.date.today()'):

    url1 = 'https://cdn-api.co-vin.in/api'
    url2 = "/v2/appointment/sessions/public/findByPin"
    slots = []
    pinurl = 'https://api.postalpincode.in/pincode/'
    area = requests.get(pinurl+pin)

    if area.ok:
        area = area.json()
        flash('Showing slots for ')
        flash(area[0]['PostOffice'][0]['Name'])
    else:
        flash('Showing slots for ')
        flash(pin)

    for i in range(5):
        slotdate = datetime.date.today() + datetime.timedelta(days=i)
        sfdate = slotdate.strftime("%d/%m/%Y")
        q1 = '?pincode='+pin+'&date=' + sfdate

        resp = requests.get(url1+url2+q1)
        if resp.ok:
            data = json.loads(resp.text)
            for slot in data['sessions']:
                cname = slot['name']
                cap = slot['available_capacity']
                age = slot['min_age_limit']
                vax = slot['vaccine']
                #fee = slot['fee_type']
                slots.append([sfdate, cname, cap, age, vax])
        else:
            flash('Error from Covin Server')
    return slots


@app.route("/pin", methods=["POST"])
def pin():
    global pincode

    #uname = request.form.get('uname')
    #age = request.form.get('age')
    #mobile_num = request.form.get('phone')
    pincode = request.form.get('pincode')
    # pincode must have exactly 6 digits
    pattern = r'\d{6}'
    matches = re.findall(pattern, pincode)
    if matches:
        pincode = matches[0]
        print(pincode)
    else:
        flash('wrong pincode format, defaulting to mandaveli')
        pincode = '600004'
    return redirect("/")


def parse_mesg(mesg):
    chat_id = mesg['message']['chat']['id']
    txt = mesg['message']['text']

    # pincode must have 6 digits
    pattern = r'/\d{6}'
    matches = re.findall(pattern, txt)
    if matches:
        pincode = matches[0][1:]    # remove the /
    else:
        pincode = ''
    return chat_id, pincode


def send_message(chat_id, text='you got it!'):
    url = f'https://api.telegram.org/bot{tel_token}/sendMessage'
    payload = {'chat_id': chat_id, 'text': text}

    r = requests.post(url, json=payload)
    return r


def send_slots_info(chat_id, slots):
    pass


@app.route("/", methods=["GET", "POST"])
def index():
    global pincode
    # telegram bot functionality
    if request.method == "POST":
        msg = request.get_json()
        chat_id, pincode = parse_mesg(msg)
        #write_json(msg, 'tel.json')
#        with open(infofile, "a") as f:
#            f.writeline(mobile_num, age, pincode, uname)
        if pincode == '':
            send_message(
                chat_id, 'Please send command as / <6 digit pincode >')
            return Response('ok', status=200)
        else:
            slots = get_slots(pincode, datetime.date.today())
            s = 'Number of slots: '+str(len(slots))
            send_message(chat_id, s)

            if len(slots) > 0:
                s = "Date           " + "Center Name            " + " Available " + \
                    " Min_Age" + " Vaccine"
                send_message(chat_id, s)

                for slot in slots:
                    s = "| ".join(map(str, slot))
                    send_message(chat_id, s)

            return Response('ok', status=200)

    else:
        # default get the slots for my pincode for today
        slots = get_slots(pincode, datetime.date.today())
        return render_template("index.html", slots=slots)


if __name__ == '__main__':
    app.run(debug=True)
