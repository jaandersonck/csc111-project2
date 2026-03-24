"""University of Toronto course parsing script"""
import bs4
from bs4 import BeautifulSoup
from bs4.element import Tag

d: dict = {}

with open("data/courses.html") as f:
    soup = BeautifulSoup(f, "html.parser")
    s = [e for e in soup.find(class_="view-content") if isinstance(e, bs4.element.Tag)]
    for elem in s:
        title = elem.find(class_='views-field-title').find(class_='field-content')

        body: Tag | None = None
        breadth: Tag | None = None
        hours: Tag | None = None
        prereq: Tag | None = None
        exclusion: Tag | None = None
        recommended: Tag | None = None

        body_elem = elem.find(class_='views-field-body')
        if body_elem:
            body = body_elem.find(class_='field-content')

        breadth_elem = elem.find(class_='views-field-field-breadth-requirements')
        if breadth_elem:
            breadth = breadth_elem.find(class_='field-content')

        hours_elem = elem.find(class_='views-field-field-hours')
        if hours_elem:
            hours = hours_elem.find(class_='field-content')

        prereq_elem = elem.find(class_='views-field-field-prerequisite')
        if prereq_elem:
            prereq = prereq_elem.find(class_='field-content')

        exclusion_elem = elem.find(class_='views-field-field-exclusion')
        if exclusion_elem:
            exclusion = exclusion_elem.find(class_='field-content')

        recommended_elem = elem.find(class_='views-field-field-recommended')
        if recommended_elem:
            recommended = recommended_elem.find(class_='field-content')

        # title organizing
        title_parts = title.get_text().strip().split(' ')
        code = title_parts[0]
        name = " ".join(title_parts[2:])

        br_num: int | None = None
        if breadth:
            br_num = int(breadth.get_text().strip().split(' ')[-1].replace("(","").replace(")",""))

        description: str | None = None
        if body:
            description = body.get_text().strip()

        hrs: str | None = None
        if hours:
            hrs = hours.get_text().strip()

        pr: str | None = None
        if prereq:
            pr = prereq.get_text().strip()

        exc: str | None = None
        if exclusion:
            exc = exclusion.get_text().strip()

        rec: str | None = None
        if recommended:
            rec = recommended.get_text().strip()

        j = {
            'code': code,
            'name': name,
            'hours': hrs,
            'description': description,
            'prerequisites': pr,
            'exclusions': exc,
            'breadth': br_num
        }
        d[code] = j

import json
with open('data/courses.json', 'w') as f:
    json.dump(d, f)

print([d[m]['prerequisites'] for m in d])
