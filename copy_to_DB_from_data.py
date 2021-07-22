import data
import json

DBdata = {}

DBdata["goals"] = data.goals
DBdata["teachers"] = data.teachers

with open("data_file.json", "w", encoding="utf8") as write_file:
    json.dump(DBdata, write_file, ensure_ascii=False)
