"""hi"""
import json
reduced = {}
with open('data/courses_final.json', 'r') as f:
    data = json.load(f)
    for code in data:
        course = data[code]
        reduced[code] = {
            "code": code,
            "prereq_tree": course['prereq_tree'],
            "exclusions": course['exclusions']
        }

with open('data/courses_final_shrunk.json', 'w') as f:
    json.dump(reduced, f)
