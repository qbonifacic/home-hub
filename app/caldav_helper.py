import os
from datetime import datetime, timedelta

import caldav

CALDAV_URL = os.environ.get('CALDAV_URL', '')
CALDAV_USERNAME = os.environ.get('CALDAV_USERNAME', 'dj.bonifacic@proton.me')
CALDAV_PASSWORD = os.environ.get('CALDAV_PASSWORD', 'ghio-hjrh-fmyw-wpgl')


def get_week_events():
    if not CALDAV_URL:
        return []
    try:
        client = caldav.DAVClient(
            url=CALDAV_URL,
            username=CALDAV_USERNAME,
            password=CALDAV_PASSWORD,
        )
        principal = client.principal()
        calendars = principal.calendars()
        start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)
        events = []
        for cal in calendars:
            results = cal.search(start=start, end=end, event=True, expand=True)
            for event in results:
                vevent = event.vobject_instance.vevent
                summary = str(vevent.summary.value) if hasattr(vevent, 'summary') else 'No title'
                dtstart = vevent.dtstart.value
                dtend = vevent.dtend.value if hasattr(vevent, 'dtend') else dtstart
                if hasattr(dtstart, 'hour'):
                    dt = dtstart
                else:
                    dt = datetime.combine(dtstart, datetime.min.time())
                events.append({
                    'summary': summary,
                    'start': dt,
                    'end': dtend,
                    'all_day': not hasattr(dtstart, 'hour'),
                    'date': dt.strftime('%Y-%m-%d'),
                    'time': dt.strftime('%H:%M') if hasattr(dtstart, 'hour') else 'All day',
                })
        events.sort(key=lambda e: e['start'])
        return events
    except Exception:
        return []
