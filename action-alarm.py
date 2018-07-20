#!/usr/bin/env python2
# -*-: coding utf-8 -*-

from alarm import Alarm
from concierge_python.concierge import Concierge
from concierge_python.extract import Extract
from hermes_python.hermes import Hermes

MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))

lang = "EN"

def setAlarm(hermes, intent_message):
    every = Extract.value(intent_message.slots.recurrence, None) is not None
    day = Extract.value(intent_message.slots.weekday)
    time = Extract.timeSlot(intent_message.slots.time)
    siteId = intent_message.site_id
    hermes.alarm.add(every, time, day, siteId)

def stopTimer(hermes, intent_message):
    current_session_id = intent_message.session_id
    tag = Extract.values(intent_message.slots.tag)
    hermes.alarm.remove(tag)

if __name__ == "__main__":
    lang = Concierge.getLang()
    c = Concierge(MQTT_IP_ADDR)
    a = Alarm(c)
    with Hermes(MQTT_ADDR) as h:
        h.alarm = a
        h.subscribe_intent("snips-labs:SetAlarm_" + lang, setAlarm) \
        .subscribe_intent("snips-labs:StopTimer_" + lang, stopTimer) \
        .loop_forever()
