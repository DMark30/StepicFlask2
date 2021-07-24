import json
import os
import random
import sys

from flask import Flask, render_template, request, abort
from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, RadioField, IntegerField
from wtforms.fields.html5 import TelField
from wtforms.validators import InputRequired, DataRequired
from wtforms.widgets import HiddenInput
from dotenv import load_dotenv

with open('data_file.json', encoding="utf-8") as json_file:
    data = json.load(json_file)
time_limits = [("hour1_2", "1-2 часа в неделю"),
               ("hour3_5", "3-5 часов в неделю"),
               ("hour5_7", "5-7 часов в неделю"),
               ("hour7_10", "7-10 часов в неделю")]


class BookingForm(FlaskForm):
    choices = []
    for key, value in data["goals"].items():
        choices.append((key, value))
    clientName = StringField("Вас зовут", [InputRequired(message="Необходимо указать имя")])
    clientPhone = TelField("Ваш телефон", [InputRequired(message="Необходимо указать телефон")])
    clientWeekday = HiddenField()
    clientTime = HiddenField()
    clientTeacher = IntegerField(widget=HiddenInput())


class RequestForm(FlaskForm):
    choices = []
    for key, value in data["goals"].items():
        choices.append((key, value))
    clientGoal = RadioField("Какова цель занятий?", choices=choices, default="travel", validators=[DataRequired()])
    clientHours = RadioField("Сколько времени есть?", choices=time_limits, default="hour5_7",
                             validators=[DataRequired()])
    clientName = StringField("Вас зовут", [InputRequired(message="Необходимо указать имя")])
    clientPhone = TelField("Ваш телефон", [InputRequired(message="Необходимо указать телефон")])


app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print('".env" is missing.')
    sys.exit(1)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

week_days = {"mon": ["monday", "Понедельник"], "tue": ["tuesday", "Вторник"], "wed": ["wednesday", "Среда"],
             "thu": ["thursday", "Четверг"], "fri": ["friday", "Пятница"]}


@app.route("/")
def index_page():
    teachers_show = random.sample(data["teachers"], k=6)
    return render_template("index.html", teachers=teachers_show, goals=data["goals"])


@app.route("/all/", methods=["GET", "POST"])
def all_page():
    sort_value = ""
    if request.method == 'POST':
        sort_value = request.form.get("inlineFormCustomSelectPref")
    if sort_value == "1":
        teachers = sorted(data["teachers"], key=lambda teacher: teacher["price"], reverse=True)
    elif sort_value == "2":
        teachers = sorted(data["teachers"], key=lambda teacher: teacher["price"])
    elif sort_value == "3":
        teachers = sorted(data["teachers"], key=lambda teacher: teacher["rating"], reverse=True)
    else:
        teachers = random.sample(data["teachers"], k=len(data["teachers"]))
    return render_template("all.html", teachers=teachers, sort_value=sort_value)


@app.route("/goals/<goal>/")
def goal_page(goal):
    teachers_show = []
    for teacher in data["teachers"]:
        if goal in teacher["goals"]:
            teachers_show.append(teacher)
    return render_template("goal.html", teachers=teachers_show)


@app.route("/profiles/<int:teacher_id>/")
def profile_page(teacher_id):
    for teacher in data["teachers"]:
        if teacher["id"] == teacher_id:
            return render_template("profile.html", teacher=teacher, goals=data["goals"], week_days=week_days)
    abort(404)
    return render_template("index.html")


@app.route("/request/")
def request_page():
    form = RequestForm()
    return render_template("request.html", form=form)


@app.route("/request_done/", methods=["POST"])
def request_done_page():
    form = RequestForm()
    if form.validate_on_submit():
        with open('request.json', encoding="utf-8") as json_read_file:
            request_data = json.load(json_read_file)
        new_request = {"clientName": form.clientName.data, "clientPhone": form.clientPhone.data,
                       "clientGoal": form.clientGoal.data, "clientHours": form.clientHours.data
                       }
        request_data["requests"].append(new_request)
        with open("request.json", "w", encoding="utf-8") as json_write_file:
            json.dump(request_data, json_write_file, indent=2)
        value = form.clientHours.data
        choices = dict(form.clientHours.choices)
        label = choices[value]
        new_request["hours"] = label
        new_request["goal"] = data["goals"][form.clientGoal.data]
        return render_template("request_done.html", request=new_request)
    else:
        return render_template("request.html", form=form)


@app.route("/booking/<int:booking_id>/<day>/<time>/")
def booking_page(booking_id, day, time):
    abort = True
    form = BookingForm()
    for key, value in week_days.items():
        if value[0] == day:
            abort = False
            form.clientWeekday.data = key
            form.clientTime.label = value[1]
    if abort:
        abort(404)
    abort = True
    form.clientTime.data = time + ":00"
    form.clientTime.label = form.clientTime.label + ", " + form.clientTime.data
    form.clientTeacher.data = booking_id
    for teacher in data["teachers"]:
        if booking_id == teacher["id"]:
            abort = False
            form.clientTeacher.label = teacher["name"]
            picture = teacher["picture"]
    if abort:
        abort(404)
    return render_template("booking.html", form=form, picture=picture)


@app.route("/booking_done/", methods=["POST"])
def booking_done_page():
    form = BookingForm()
    if form.validate_on_submit():
        with open('booking.json', encoding="utf-8") as json_read_file:
            booking_data = json.load(json_read_file)
        new_booking = {"clientName": form.clientName.data, "clientPhone": form.clientPhone.data,
                       "clientWeekday": form.clientWeekday.data, "clientTime": form.clientTime.data,
                       "clientTeacher": form.clientTeacher.data
                       }
        booking_data["bookings"].append(new_booking)
        with open("booking.json", "w", encoding="utf-8") as json_write_file:
            json.dump(booking_data, json_write_file, indent=2)
        for key, value in week_days.items():
            if key == form.clientWeekday.data:
                new_booking["day"] = value[1] + ", " + form.clientTime.data
        return render_template("booking_done.html", booking=new_booking)
    else:
        return render_template("booking.html", form=form)


if __name__ == '__main__':
    app.run()
