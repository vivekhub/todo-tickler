#!/usr/bin/env python
import re
import time
from datetime import datetime
from datetime import date
from datetime import timedelta
from calendar import monthrange
import monthdelta

# day_of_month = datetime.now().day
# week_number = (day_of_month - 1) // 7 + 1

RE_DAY_MON_YR = '[0-9]+(d|D|m|M|y|Y|w|W)'
RE_WEEKDAY = '(daily)|(first|second|third|fourth|fifth)-(sunday|monday|' + \
             'tuesday|wednesday|thursday|friday|saturday)|' + \
             '(sunday|monday|tuesday|wednesday|thursday|friday|saturday)'

MONTH_ARRAY_CACHE = {}

DAYS = {
    'monday': 1,
    'tuesday': 2,
    'wednesday': 3,
    'thursday': 4,
    'friday': 5,
    'saturday': 6,
    'sunday': 7,
}


def make_montharray(year, month):
    mac_key = (
        year,
        month,
    )
    res = MONTH_ARRAY_CACHE.get(mac_key)
    if res is None:
        res = {}
        aday = date(year=year, month=month, day=1)
        for i in range(1, monthrange(year, month)[1]):
            if aday.isoweekday() in list(res.keys()):
                res[aday.isoweekday()].append(aday)
            else:
                res[aday.isoweekday()] = [
                    aday,
                ]
            aday = date(year=year, month=month, day=1) + timedelta(i)
        # Last item got left out somehow
        res[aday.isoweekday()].append(aday)
        MONTH_ARRAY_CACHE[mac_key] = res
    return res


def make_dayofweek():
    one_five = [
        'first',
        'second',
        'third',
        'fourth',
        'fifth',
    ]
    dofw = {}
    dayofweek = 0
    for one_five in one_five:
        dayofweek += 1
        for week_day in list(DAYS.keys()):
            akey = '{0}-{1}'.format(one_five, week_day)
            dofw[akey] = (
                dayofweek,
                DAYS[week_day],
            )
    return dofw


DAYOFWEEK = None


def FindProjectsAndContexts(aline):
    ticklerwords = aline.split()
    projects = [aword for aword in ticklerwords if aword[0] == '+']
    contexts = [aword for aword in ticklerwords if aword[0] == '@']
    # Got the regexp from  http://www.regular-expressions.info/dates.html
    comp_re = re.compile(
        '^due:(19|20)\d\d[- /.](0[1-9]|1[012])[- /.](0[1-9]|[12][0-9]|3[01])$')

    duedates = [
        aword for aword in ticklerwords if comp_re.match(aword) is not None
    ]

    ActualDates = [
        datetime.strptime(adate.split(':')[1], '%Y-%m-%d')
        for adate in duedates
    ]
    # clean up duplicates and return
    return (
        set(projects),
        set(contexts),
        set(ActualDates),
    )


def RepeatDateInRange(start, delta):
    sunday = date.today() - timedelta(date.today().isoweekday() % 7)
    saturday = date.today() + timedelta((6 - date.today().isoweekday()) % 7)
    if start <= date.today():
        check = start
        while check < sunday:
            check += delta
        if (sunday <= check) and (check <= saturday):
            return check
    return None


def SingleDateInRange(start):
    sunday = date.today() - timedelta(date.today().isoweekday() % 7)
    saturday = date.today() + timedelta((6 - date.today().isoweekday()) % 7)
    return (sunday <= start) and (start <= saturday)


def CleanTaskLine(ticklerwords):
    skip_words = [
        'start:',
        'due:',
        't:',
        'repeat:',
    ]

    outwords = [
        outword for outword in ticklerwords
        if len(list(filter(outword.startswith, skip_words))) == 0
    ]
    return outwords


def MatchLineFuzzy(TodoContent, words):
    matched = False
    for atodo in TodoContent[2]:
        lineset = set(CleanTaskLine(atodo['line'].split()))
        matchlen = len(set(words).intersection(lineset))
        matched = (len(lineset) > 0 and (matchlen * 100 / len(lineset)) > 70)
        if matched:
            break
    return matched


def InsertTaskLine(todo, outwords, startdate, duedate, firsttime):
    outwords.insert(0, date.today().strftime('%Y-%m-%d'))
    outwords.append('due:{0}'.format(duedate.strftime('%Y-%m-%d')))
    outwords.append('t:{0}'.format(startdate.strftime('%Y-%m-%d')))
    outwords.append('\n')
    if firsttime:
        todo.write('\n')
    todo.write(' '.join(outwords))


def GetWeeknumber(adate):
    ma = make_montharray(adate.year, adate.month)
    count = 1
    for thedate in ma[adate.isoweekday()]:
        if adate == thedate:
            return count
        else:
            count += 1
    return 0


def PrepareWeekList(sunday, saturday):
    start = sunday
    ret = []
    while (start <= saturday):
        ret.append((
            GetWeeknumber(start),
            start.isoweekday(),
        ))
        start += timedelta(days=1)
    return ret


def ParseWeekday(weekdaytxt):
    sunday = date.today() - timedelta(date.today().isoweekday() % 7)
    if weekdaytxt in list(DAYS.keys()):
        startday = sunday + timedelta(days=DAYS[weekdaytxt])
        return (
            startday,
            startday + timedelta(days=1),
        )
    elif weekdaytxt in list(DAYOFWEEK.keys()):
        thisweek = PrepareWeekList(sunday, sunday + timedelta(days=6))
        if DAYOFWEEK[weekdaytxt] in thisweek:
            startday = sunday + timedelta(days=DAYOFWEEK[weekdaytxt][1])
            return (
                startday,
                startday + timedelta(days=1),
            )
    return None


def ParseRepeat(start, repeatxt):
    repeatxt = repeatxt.lower()
    delta_obj = repeatxt.split(':')[1]
    if delta_obj[0].isdigit():
        # This is a typical digit based thing
        delta = None
        repeat_num = int(delta_obj[0:-1])
        if delta_obj[-1] == 'm':
            delta = monthdelta.monthdelta(repeat_num)
        elif delta_obj[-1] == 'd':
            delta = timedelta(days=repeat_num)
        elif delta_obj[-1] == 'y':
            delta = monthdelta.monthdelta(repeat_num * 12)
        elif delta_obj[-1] == 'w':
            delta = timedelta(days=7)
        resp = RepeatDateInRange(start, delta)
        if resp:
            return (
                resp,
                resp,
            )
        return None
    else:
        return ParseWeekday(delta_obj)


def ProcessTicklerFile(aFile, todoFile, TodoContent):
    processed = 0
    firsttime = True
    repeat_re_txt = '^repeat:(({0})|{1})'.format(RE_DAY_MON_YR, RE_WEEKDAY)
    repeat_re = re.compile(repeat_re_txt)
    #    '^repeat:[0-9]+(d|D|m|M|y|Y)')
    start_re = re.compile('^start:(19|20)\d\d[- /.](0[1-9]|1[012])[- /.]' +
                          '(0[1-9]|[12][0-9]|3[01])$')

    with open(aFile, 'r') as infile, open(todoFile, 'a') as todo:
        for aline in infile:
            ticklerwords = aline.split()
            # get rid of the t: and due:
            outwords = CleanTaskLine(ticklerwords)
            # Check if we already have it in todo.txt
            if not MatchLineFuzzy(TodoContent, outwords):
                repeat_word = [
                    aword for aword in ticklerwords if repeat_re.match(aword)
                ]
                start_date_list = [
                    aword for aword in ticklerwords if start_re.match(aword)
                ]
                if len(start_date_list) > 0:
                    start_date_str = start_date_list[0].split(':')[1]
                    startdate = datetime.date(
                        datetime.strptime(start_date_str, '%Y-%m-%d'))
                    if len(repeat_word) > 0:
                        keydates = ParseRepeat(startdate, repeat_word[0])
                        if keydates:
                            InsertTaskLine(todo, outwords, keydates[0],
                                           keydates[1], firsttime)
                            firsttime = False
                            processed += 1
                    else:  # This is a onetime tickler
                        if SingleDateInRange(startdate):
                            InsertTaskLine(todo, outwords, startdate,
                                           startdate, firsttime)
                            firsttime = False
                            processed += 1
                        # This tickler item will never get triggered anymore
                        elif startdate < date.today():
                            print('Please remove from tickler : {0}'.format(
                                aline))

    print('Added {0} item{1} from the tickler file'.format(
        processed, 's' if processed > 1 else ''))


def LoadFile(aFile):
    lines = []
    totalprojects = set()
    totalcontexts = set()
    with open(aFile, 'r') as fhandle:
        for aline in fhandle:
            thisline = {}
            projects, contexts, duedates = FindProjectsAndContexts(aline)
            thisline['projects'] = projects
            thisline['contexts'] = contexts
            thisline['duedates'] = duedates
            thisline['line'] = aline
            thisline['closed'] = (aline[0] == 'x')
            lines.append(thisline)
            for p in projects:
                totalprojects.add(p)
            for c in contexts:
                totalcontexts.add(c)
    return (
        totalprojects,
        totalcontexts,
        lines,
    )


if __name__ == "__main__":
    DAYOFWEEK = make_dayofweek()
    TodoFile = LoadFile('todo.txt')
    ProcessTicklerFile('tickler.txt', 'todo.txt', TodoFile)
    TodoFile = LoadFile('todo.txt')
    DoneFile = LoadFile('done.txt')
    TicklerFile = LoadFile('tickler.txt')
    doneprojects = DoneFile[0]
    for item in TodoFile[2]:
        if item['closed']:
            doneprojects.update(item['projects'])
    DoneProjectsFile = LoadFile('project.done.txt')

    # Check for projects that we have to work on...
    doneprojects.difference_update(TodoFile[0])
    doneprojects.difference_update(DoneProjectsFile[0])
    doneprojects.difference_update(TicklerFile[0])

    with open('review-' + time.strftime('%Y-%m-%d') + '.txt', 'w') as f:
        for proj in doneprojects:
            f.write(proj + '\n')
