from datetime import date
from flask import Blueprint, render_template, request, redirect, session

import errors
import sqlite3
import workout_objects as obj

connection = obj.DatabaseConn('workoutbuddy_database.db')
#creates the connection to the database
views = Blueprint('views', __name__)
#creates the blueprint necessary for flask to run

##VARIABLES##
Categories = obj.Categories(connection)
Workouts = obj.AllWorkouts(connection,Categories)


@views.route('/',methods=['GET','POST'])
@views.route('/home', methods=['GET','POST'])
def home_page():
    Categories = obj.Categories(connection)
    Workouts = obj.AllWorkouts(connection, Categories)
    logged_in = False
    if 'user_id' not in session:
        #checking if the user is logged in or not
        return redirect('/login')
    else:
        logged_in = True
    if request.method == 'POST':
        if 'log_out' in request.form:
            session.clear()
            #if the user chooses to log out it clears all session data
            logged_in = False
            return redirect('/login')
    user_id = session['user_id']
    user_workouts = Workouts.get_all_user_workouts(user_id)
    reminders = user_workouts.generate_reminders()
    events = user_workouts.get_calendar_dict()
    #generates reminders and events to display to the user on the homescreen
    return render_template('homepage.html', title='HOME', reminders=reminders, logged_in = logged_in, events=events)


@views.route("/View_Workouts", methods=['GET', 'POST'])
def view_workouts():
    if 'user_id' not in session:
        return redirect('/login')
    else:
        user_id = session['user_id']
        Workouts = obj.AllWorkouts(connection, Categories)
        user_workouts = Workouts.get_all_user_workouts(user_id)
    workout_details = user_workouts.get_view_data()
    #gets the data required to view the workouts
    number_of_workouts = len(workout_details[0])
    column_num = 1
    if 35 >= number_of_workouts > 12:
        column_num = 2
    elif number_of_workouts >= 36:
        column_num = 3
    #decides how many columns to use when displaying the workout

    if request.method == 'POST':
        workout = user_workouts.get_object(int(list(request.form.keys())[0]))
        #using the key of the request form, which is the user ID, it can get the workout object
        user_workouts.delete_object(workout)
        workout_details = user_workouts.get_view_data()
        Workouts = obj.AllWorkouts(connection,Categories)
        #needs this line^^ to update the display
        session.pop('workout_info', None)
        session.pop('selected_workout', None)
        session.pop('workout_selected_for_completions', None)
        session.pop('workout_selected_for_schedule', None)
        #clears all session data so that it doesn't contain session data related to a non existent workout
    return render_template('view_workout_page.html',title='VIEW WORKOUTS', workout_labels=workout_details[0], workout_details=workout_details[1], column_num=column_num)


@views.route('View_Exercises',methods=['GET', 'POST'])
def view_exercises():
    error = None
    if 'user_id' not in session:
        return redirect('/login')
    else:
        user_id = session['user_id']
        user_workouts = Workouts.get_all_user_workouts(user_id)
    categories = Categories.get_category_names()
    exercises = []
    for element in Categories.get_categories():
        exercises.append(element.get_details())
    #gets all the data for the buttons on the users page
    highest_weights = Categories.get_highest_weights_display(user_id)
    one_rep_maxes = Categories.estimate_1rmaxes(user_id)
    target_weights = Categories.get_target_weights(user_id)
    #gets the view data for everything displayed to the user
    if request.method == 'POST':
        #the only POST form is when updating target weight
        exercise_chosen = list(request.form.keys())[0]
        weight_chosen = list(request.form.values())[0]
        # USING DICTIONARY FUNCTIONS to get the exercise and weight chosen
        if len(weight_chosen) > 0:
            exercise_chosen = Categories.search_exercises(exercise_chosen)
            Categories.update_target_weight(exercise_chosen,weight_chosen, user_id)
            target_weights = Categories.get_target_weights(user_id)
        else:
            error = errors.EmptyFields.message
    return render_template('view_exercises.html', title="VIEW EXERCISES", categories=categories, exercises=exercises, highest_weights = highest_weights, one_rep_maxes=one_rep_maxes, target_weights = target_weights,error= error)


@views.route('/Create_Workouts', methods=['GET', 'POST'])
def create_workouts():
    error = None
    if 'user_id' not in session:
        return redirect('/login')
    else:
        user_id = session['user_id']
        Workouts = obj.AllWorkouts(connection, Categories)
        user_workouts = Workouts.get_all_user_workouts(user_id)
    categories = Categories.get_category_names()
    exercises = []
    for element in Categories.get_categories():
        exercises.append(element.get_details())
    if 'workout_info' not in session:
        workout_info = None
    else:
        workout_info = session['workout_info']
    #workout_info variable needed to pass to website
    if request.method == 'POST':
        if 'workout_name' in request.form and request.form['workout_name'] != '':
            #checks if workout_name is not just blank as well
            #EXCEPTION HANDLING
            try:
                user_workouts.check_valid_workout_name(request.form['workout_name'])
                #if this fails it raises a Workout Name in use error
                try:
                    workout_id = user_workouts.add(str(request.form['workout_name']))
                    session['workout_info'] = user_workouts.get_object(workout_id).name
                    workout_info = session['workout_info']
                    session['workout_id'] = workout_id
                    #stores the workout_id in the session so when the user is out of this particular post request, they can still get the workout_id of the workout they are creating
                except AssertionError:
                    #shown when the workout name field is over 40 characters
                    error = errors.FieldsTooLong.message
            except errors.WorkoutNameInUse:
                error = errors.WorkoutNameInUse.message
        
        elif 'delete_exercise' in request.form:
            current_workout = user_workouts.get_object(int(session['workout_id']))
            workout_info = current_workout.name

            button_pressed = request.form['delete_exercise'][7:]
            # takes the letters after the first 7 as those characters are for the phrase 'Delete '
            exercise_chosen = Categories.search_exercises(button_pressed)
            current_workout.delete_exercise_from_workout(exercise_chosen)
            connection.db.commit()
            #removes the exercise selected from the workout

        elif 'save' in request.form:
            session.pop('workout_info', None)
            session.pop('workout_id',None)
            return redirect("/")
        #when save is pressed it clears the session so that when making a new workout, it doesn't have the ID of the old one

        elif 'workout_id' in session:
            #the only POST form is the adding of an exercise
            current_workout = user_workouts.get_object(int(session['workout_id']))
            exercise_chosen = list(request.form.keys())[0]
            values = request.form.getlist(exercise_chosen)
            #uses dictionary methods to get the exercise and exercises values from the request.form
            weight_chosen = values[0]
            sets = values[1]
            reps = values[2]
            exercise_id = Categories.search_exercises(exercise_chosen)
            valid_inputs = current_workout.add_exercise(exercise_id,weight_chosen,sets, reps)
            #has to check to make sure the user has entered NON TEXT inputs for weight and integers for sets and reps
            if not valid_inputs:
                error = errors.InvalidInput.message
                #passes this error variable through to the page which
            else:
                error = None
    workout_exercises = []
    if workout_info is not None:
        #checks if the user is currently editing a workout and if they are, it gets the workouts exercises to display to the user
        workout_exercises = user_workouts.get_object(int(session['workout_id'])).get_exercise_names()
    connection.db.commit()
    return render_template('create_workouts.html', title="CREATE WORKOUTS", workout_info=workout_info, workout_exercises=workout_exercises, categories=categories, exercises=exercises, error = error)


@views.route('Log_Workouts', methods=['GET', 'POST'])
def log_workouts():
    error = None
    if 'user_id' not in session:
        return redirect('/login')
    else:
        user_id = session['user_id']
        Workouts = obj.AllWorkouts(connection, Categories)
        user_workouts = Workouts.get_all_user_workouts(user_id)
    workout_details = user_workouts.get_details()
    # needs the name of the workouts so the selection buttons can be made
    recent_completion_data = [None,None]
    # need a variable for the completion of each workout - it matches the format of the result of the get_recent_completions method
    workout_exercises = None
    current_values=None
    if 'exercises_selected' not in session:
        exercises_selected = None
    else:
        exercises_selected = session['exercises_selected']
    # keeps track of each exercise selected by the user to log
    if 'selected_workout' not in session:
        workout_selected = None
    else:
        workout_selected = session['selected_workout']
    if 'exercise_selected_details' not in session:
        exercises_selected_details = None
    else:
        exercises_selected_details = session['exercise_selected_details']
    #keeps track of all the values of the exercises selected e.g. Weight, reps etc.
    if request.method == 'POST':
        if 'select' in request.form:
            workout_id = user_workouts.get_id_from_details_list(workout_details,request.form['select'])
            workout = user_workouts.get_object(workout_id)
            workout.add_log()
            session['selected_workout'] = workout.name
            workout_selected = session['selected_workout']
            #adds a completion of a workout when a workout is selected

        elif 'save' in request.form:
            try:
                workout_id = user_workouts.get_id_from_details_list(workout_details, workout_selected)
                workout = user_workouts.get_object(workout_id)
                workout.add_many_exercises_complete(exercises_selected_details)
                session.pop('selected_workout', None)
                session.pop('exercises_selected', None)
                session.pop('exercise_selected_details', None)
                return redirect("/")
            except sqlite3.OperationalError:
                session.pop('selected_workout', None)
                session.pop('exercises_selected', None)
                session.pop('exercise_selected_details', None)
                error = errors.InvalidInput.message
                return redirect("/")
            #adds the completion of the exercises the user has selected and then gets rid of the session data from this page

        elif 'cancel' in request.form:
            workout_id = user_workouts.get_id_from_details_list(workout_details, workout_selected)
            workout = user_workouts.delete_newest_log(workout_id)
            session.pop('selected_workout', None)
            session.pop('exercises_selected', None)
            session.pop('exercise_selected_details', None)
            return redirect("/")
            # deletes the workout completion created at the start and then removes the session data

        else:
            workout_id = user_workouts.get_id_from_details_list(workout_details, workout_selected)
            completion_id = user_workouts.get_newest_log(workout_id)[0]
            exercise_chosen = list(request.form.keys())[0]
            #gets the workout_id, completion_id and the exercise chosen id
            if 'exercises_selected' in session:
                temp = session['exercises_selected']
                temp.append(exercise_chosen)
                session['exercises_selected'] = temp
            else:
                session['exercises_selected'] = [exercise_chosen]
            #adds the exercise selected to the session data
            exercises_selected = session['exercises_selected']
            values = request.form.getlist(exercise_chosen)
            if len(values[0]) == 0:
                weight_chosen = 0
            else:
                weight_chosen = values[0]
            if len(values[1]) == 0:
                sets = 0
            else:
                sets = values[1]
            if len(values[2]) == 0:
                reps = 0
            else:
                reps = values[2]

            exercise_id = Categories.search_exercises(exercise_chosen)
            if 'exercise_selected_details' in session:
                temp = session['exercise_selected_details']
                temp.append([exercise_id, completion_id, weight_chosen, sets, reps])
                session['exercise_selected_details'] = temp
            else:
                session['exercise_selected_details'] = [[exercise_id, completion_id, weight_chosen, sets, reps]]
            #completes the exercise selected details so the exercises can be logged when SAVE is pressed
            exercises_selected_details = session['exercise_selected_details']

    if workout_selected is not None:
        workout_id = user_workouts.get_id_from_details_list(workout_details, workout_selected)
        workout = user_workouts.get_object(workout_id)
        workout_exercises = workout.get_exercise_names()
        # need to get the names so that the workout exercises can be viewed
        recent_completion_data = workout.get_recent_completions(4)
        #gets recent completion values so the user can see them while logging
        current_values = workout.produce_current_vals()
        # need to get the current values of the exercises e.g. 32kg for 5x5
    return render_template('log_workouts.html', workout_name=workout_selected, workout_exercises=workout_exercises, workout_labels=workout_details,initial_data = recent_completion_data[0],secondary_data = recent_completion_data[1], current_values=current_values, exercises_selected=exercises_selected, error = error)


@views.route('workout_completions', methods=['GET', 'POST'])
def view_workout_completions():
    # basically the same as the log workouts page but without the need to create a new log
    if 'user_id' not in session:
        return redirect('/login')
    else:
        user_id = session['user_id']
        Workouts = obj.AllWorkouts(connection, Categories)
        user_workouts = Workouts.get_all_user_workouts(user_id)
    workout_details = user_workouts.get_details()
    recent_completion_data = [None,None]
    if 'workout_selected_for_completions' not in session:
        workout_selected = None
    else:
        workout_selected = session['workout_selected_for_completions']

    if request.method == 'POST':
        if 'select' in request.form:
            workout_id = user_workouts.get_id_from_details_list(workout_details, request.form['select'])
            workout = user_workouts.get_object(workout_id)
            session['workout_selected_for_completions'] = workout.name
            workout_selected = session['workout_selected_for_completions']
        if 'exit' in request.form:
            session.pop('workout_selected_for_completions', None)
            return redirect("/")
    if workout_selected is not None:
        workout_id = user_workouts.get_id_from_details_list(workout_details, workout_selected)
        workout = user_workouts.get_object(workout_id)
        recent_completion_data = workout.get_recent_completions(8)
        # gets the 8 most recent completions of the workout the user has selected
    return render_template('view_workout_completions.html',title="View Completed Workouts", workout_name=workout_selected, workout_labels=workout_details,initial_data = recent_completion_data[0],secondary_data = recent_completion_data[1])


@views.route('barbell_calc',methods=["POST", "GET"])
def barbell_calculator():
    created_weight = None
    left_over = None
    plates_used = None
    error = None
    if request.method == "POST":
        return_value = request.form
        target_weight = return_value.get('target_weight')
        weights = return_value.getlist('weights')
        if len(target_weight) == 0 or len(weights) == 0:
            error=errors.EmptyFields.message
            #makes sure the user has entered a weight and checked which weights they have available
        else:
            weights = [float(x) for x in weights]
            target_weight = int(target_weight)
            values = calc_plates(target_weight,weights)
            #uses the calc_ploates function to calculate the plates needed to use
            created_weight = values[0]
            left_over = values[1]
            plates_used = values[2]
    return render_template('barbell_calc.html', created_weight=created_weight, left_over=left_over, plates_used=plates_used, error=error)


def calc_plates(target_weight, available_plates):
    #used to calculate the most efficient way to create the desired weight
    bar_weight = 20
    left_over = target_weight - bar_weight
    plates_used = []

    for element in available_plates:
        while left_over - (element * 2) >= 0:
            left_over -= (element * 2)
            plates_used.append(element)
    created_weight = target_weight - left_over
    return [created_weight, left_over, plates_used]


@views.route('/schedule', methods=['GET', 'POST'])
def schedule_workouts():
    error = None
    current_date = date.today()
    if 'user_id' not in session:
        return redirect('/login')
    else:
        user_id = session['user_id']
        Workouts = obj.AllWorkouts(connection, Categories)
        user_workouts = Workouts.get_all_user_workouts(user_id)
    workout_details = user_workouts.get_details()
    #once again needed for the buttons to select the workouts
    if 'workout_selected_for_schedule' not in session:
        workout_selected = None
    else:
        workout_selected = session['workout_selected_for_schedule']
    if request.method == 'POST':
        if 'select' in request.form:
            workout_id = user_workouts.get_id_from_details_list(workout_details, request.form['select'])
            workout = user_workouts.get_object(workout_id)
            session['workout_selected_for_schedule'] = workout.name
            workout_selected = session['workout_selected_for_schedule']
            #adds the workout_selected into the session data, so it can be accessed outside this post request
        elif 'schedule' in request.form and workout_selected is not None:
            #if workout selected is not None that means they are scheduling a workout
            if len(request.form['schedule']) == 0:
                #makes sure the date is not empty
                error = errors.EmptyFields.message
            else:
                workout_selected = session['workout_selected_for_schedule']
                workout_id = user_workouts.get_id_from_details_list(workout_details, workout_selected)
                user_workouts.schedule(request.form['schedule'], workout_id)
                session.pop('workout_selected_for_schedule', None)
                return redirect("/")
            #schedules the workout then returns to the calendar, so they can view their workout
        elif 'schedule' in request.form and workout_selected is None:
            #if the workout selected is none, that means they are scheduling a day they are busy
            if len(request.form['schedule']) == 0:
                error = errors.EmptyFields.message
            else:
                user_workouts.schedule_other(request.form['schedule'])
                return redirect("/")
        elif 'exit' in request.form:
            session.pop('workout_selected_for_schedule', None)
            workout_selected = None
    return render_template('schedule.html', title="Schedule Workouts", current_date =current_date, workout_labels=workout_details, workout_selected=workout_selected, error=error)


@views.route('view_data', methods=['POST', 'GET'])
def view_data():
    if 'user_id' not in session:
        return redirect('/login')
    else:
        user_id = session['user_id']
        Workouts = obj.AllWorkouts(connection, Categories)
        user_completions = obj.Completions(connection,user_id)
        #creates the completions object as it has methods which can retrieve the data needed for the graphs
    exercise_labels = user_completions.get_exercises()
    #gets the names of all the exercises that have been completed by the user
    if 'exercise_selected' not in session:
        exercise_selected = None
    else:
        exercise_selected = session['exercise_selected']
    if 'graph_type' not in session:
        graph_type = None
    else:
        graph_type = session['graph_type']
    # selected type of graph - Weights, Estimated 1RM, Reps
    if request.method == "POST":
        if 'select' in request.form:
            session['exercise_selected'] = request.form['select']
            exercise_selected = session['exercise_selected']
            #saves the exercise selected by the user into the session data
        elif 'exit' in request.form:
            session.pop('exercise_selected', None)
            exercise_selected = None
        elif 'graph_type' in request.form:
            session['graph_type'] = request.form['graph_type']
            graph_type = session['graph_type']
    if exercise_selected is None:
        title="View Data"
        labels = None
        values = None
        #enters blank values and labels for the graph as the exercise hasn't been selected yet
    else:
        title=f"View data for {exercise_selected}"
        if graph_type is None:
            labels = None
            values = None
        # enters blank values and labels for the graph as the graph type hasn't been selected yet
        else:
            all_data =  user_completions.get_graph_data_for_exercise(exercise_selected, 15)
            # this gets the last 15 data points that the user has for the particular exercise
            labels = [element[0] for element in all_data]
            if graph_type == "WEIGHT":
                values = [element[1] for element in all_data]
            elif graph_type == "REPS":
                values = [element[2] for element in all_data]
            else:
                values = [element[3] for element in all_data]
            #gets a different index dependent on WHICH graph type was selected.
    return render_template('view_data.html', title=title, exercise_labels=exercise_labels, exercise_selected=exercise_selected, graph_type=graph_type, labels=labels, values=values)