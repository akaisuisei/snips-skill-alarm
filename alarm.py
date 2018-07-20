import datetime
import json
from os.path import expanduser, isfile
import threading

class Alarm:
    def __init__(self, concierge):
        self.concierge = concierge
        self.alarms = {}
        self.filename = expanduser('~/.alarm.json')
        self.load()

    def save(self):
        to_save = [self.alarms[x].toJSON() for x in self.alarms]
        with open(self.filename, 'w') as f:
            f.write(json.dumps(to_save))

    def load(self):
        if (not isfile(self.filename)):
            return
        with open(self.filename, 'r') as f:
            data  = json.load(f)
            for x in data:
                if (x['due_time'] is not None and x['due_time'] != 'None'):
                    self.alarms[x['tag']] = Data.fromDict(x)

    def getView(self):
        items  = []
        for alarm in self.alarms.itervalues():
            items.append(alarm.getView())
        return items

    def _find_new_tag(self, tag):
        if tag in self.alarms and self.alarms[tag] is None:
            return tag
        else:
            for x in range(0, 99):
                n_tag = tag + "({})".format(x)
                if n_tag not in self.alarms:
                    return n_tag
        return ""

    def add(self, every, time, day, siteId):
        tag = self._find_new_tag("alarm")
        if tag in self.alarms:
            self.alarms[tag].activate()
        else:
            self.alarms[tag] = Data(tag, siteId, time, day, every)
        self.save()

    def remove(self, tag):
        if(len(tag)):
            tag= tag[0]
        else:
            tag = ""
        if (tag in self.alarms):
            self.alarms[tag].cancel()
        self.save()

class Data:
    day_to_int = {
        'WEE' : -2,
        'day' : -1,
        'DAY' : -1,
        'MON' : 0,
        'TUE' : 1,
        'WED' : 2,
        'THU' : 3,
        'FRI' : 4,
        'SAT' : 5,
        'SUN' : 6
    }
    def __init__(self, tag, siteId, due_time, day, every, active = True):
        self.tag = tag
        self.due_time = due_time
        self.day = day
        self.every = every
        self.siteId = siteId
        self.active = active
        self.t = None
        if self.every and self.day == "":
            self.day = "day"
        if due_time is None:
            self.due_time= datetime.datetime.now().replace(hour = 12,
                                                minute = 0,
                                                second = 0,
                                                microsecond = 0)
        if active:
            self.activate()

    # return next day at 00:00
    def _next_day(self, tmp):
        def not_today(value):
            return datetime.datetime.now().time() > value.time()
        if self.day != "":
            res = datetime.datetime.now().replace(hour = 0,
                                                minute = 0,
                                                second = 0,
                                                microsecond = 0)
            dow = res.weekday()
            day = Data.day_to_int.get(self.day[:3].upper(), None)
            if day == None:
                return None
            adding_day = 0
            if day == -2:
                if(dow  in [0,1,2,3,6]):
                    adding_day = int(not_today(tmp))
                elif (dow == 5):
                    adding_day = 2
                else:
                    adding_day = 3
            elif day != -1:
                if (day > dow):
                    adding_day = day - dow
                elif day ==  dow:
                    adding_day = int(not_today(tmp))
                else:
                    adding_day = 7 - dow + day
            else:
                adding_day = int(not_today(tmp))
            return res + datetime.timedelta(days = adding_day)
        return None
    def activate(self):
        print("activating {}".format(self.tag))
        self.cancel()
        self.active = True
        next_day = self._next_day(self.due_time)
        next_buzz = 0
        if (not self.due_time):
            return
        if (next_day):
            next_buzz = (datetime.datetime.combine(next_day.date(), self.due_time.time()) -
                        datetime.datetime.now()).total_seconds()
        else:
            next_buzz = (self.due_time -
                         datetime.datetime.now()).total_seconds()

        self.t = threading.Timer(next_buzz, self.call, self)
        self.t.start()
    def call(self):
        topic = getMqttPlayTopic(self.siteId, self.siteId)
        utils.play_wave(Concierge._client, siteId, siteId, DIR + "alarm.wav")
        self.cancel();
        if (self.every):
            activate()

    def cancel(self):
        self.active = False
        if self.t is None:
            return
        self.t.cancel()
        self.t = None

    def getView(self):
        return {
                'type': 'toggle',
                'title': self.tag,
                'subtitle': '{} {} {} {}'.format(self.day,
                                                 self.due_time,
                                                 self.every,
                                                 self.siteId),
                'value': self.active,
                'onValueChangeToOn': {
                    "intent": "snips-labs:setAlarm_EN",
                    "slots": [ { "timer_name": self.tag } ]
                },
                'onValueChangeToOff': {
                    "intent": "snips-labs:StopTimer_EN",
                    "slots": [ { "timer_name": self.tag } ]
                }
            }

    def toJSON(self):
        return {
            'tag' : self.tag,
            'due_time' : str(self.due_time),
            'day': self.day,
            'siteId': self.siteId,
            'every' : self.every,
            'active' : self.active
        }
    @staticmethod
    def fromDict(storage):
        return Data(tag = storage['tag'],
                    due_time= datetime.datetime.strptime(storage['due_time'],
                                                         "%Y-%m-%d %H:%M:%S"),
                    day = storage['day'],
                    every = storage['every'],
                    active = storage['active'],
                   siteId = storage['siteId'])
