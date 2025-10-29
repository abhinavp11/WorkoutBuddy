from flask import Blueprint, render_template, request, redirect, session
import errors
import workout_objects as obj
import account_handling as accounts

connection = obj.DatabaseConn('workoutbuddy_database.db')
auth = Blueprint('auth', __name__)
#creates the connection and the blueprint


@auth.route("/login", methods=['POST', 'GET'])
def login():
    error = None
    if 'user_id' in session:
        return redirect('/')
    if request.method == "POST":
        if 'password' and 'username' in request.form and len(request.form['username']) > 0 and len(request.form['password']) > 0:
            #makes sure that both username and password have been entered and that they have a length.
            #EXCEPTION HANDLING
            try:
                user_id = accounts.login(request.form['username'], request.form['password'],connection)
                print(user_id)
                #this function checks if the user info is correct and raises an error if not
            except errors.IncorrectUserInfo:
                error = errors.IncorrectUserInfo.message
            else:
                session['user_id'] = user_id
                return redirect('/')
        else:
            error=errors.EmptyFields.message

    return render_template('login.html', title='LOGIN', error=error)

@auth.route('/sign_up', methods=["GET","POST"])
def signup():
    error = None
    if 'user_id' in session:
        return redirect('/')
    if request.method == "POST":
        if len(request.form['username']) == 0 or len(request.form['password']) == 0:
            #checks if all fields filled out
            error=errors.EmptyFields.message
        else:
            username = request.form['username']
            #EXCEPTION HANDLING - checking if the names or passwords are too long or the name is in use
            try:
                accounts.check_if_name_in_use(username,connection)
                password = request.form['password']
                starters = False
                if 'starters' in request.form:
                    starters = True
                try:
                    accounts.create_new_account(username,password,connection)
                    user_id = accounts.login(username,password, connection)
                    if starters:
                        accounts.create_starter_workouts(connection,user_id)
                    session['user_id'] = user_id
                    return redirect('/')
                except AssertionError:
                    error = errors.FieldsTooLong.message
            except errors.UsernameInvalid:
                error=errors.UsernameInvalid.message
    return render_template('sign_up.html', title='SIGN UP', error=error)

@auth.route('/user_details', methods=['POST', 'GET'])
def user_details():
    if 'user_id' not in session:
        return redirect('/login')
    else:
        account = accounts.Account(session['user_id'],connection)
        #creates the account object if logged in
    error = None
    if request.method == "POST":
        if 'add_weight' in request.form:
            if len(request.form['add_weight']) > 0:
                account.update_weight(request.form['add_weight'])
            else:
                error = errors.EmptyFields.message
            all_data = account.get_weights(10)
            labels = [element[0] for element in all_data]
            values = [element[1] for element in all_data]
            # updates the users current and past weights tables, then updates the labels and values for the graph
        elif 'username' in request.form:
            #updating the users username
            if len(request.form['username']) > 0:
                #makes sure the new username is not blank
                #EXCEPTION HANDLING - checking if the new username has been used already
                try:
                    account.update_username(request.form['username'])
                except errors.UsernameInvalid:
                    error = errors.UsernameInvalid.message
            else:
                error = errors.EmptyFields.message
        elif 'old_password' in request.form and 'new_password' in request.form:
            #updating the users password
            if len(request.form['old_password']) > 0 and len(request.form['new_password']) >0:
                #makes sure neither the old nor new password is blank
                #EXCEPTION HANDLING - checks if the old password is wrong before changing the password
                try:
                    account.update_password(request.form['old_password'],request.form['new_password'])
                except errors.OldPasswordInvalid:
                    error = errors.OldPasswordInvalid.message
            else:
                error = errors.EmptyFields.message
    all_data = account.get_weights(10)
    labels = [element[0] for element in all_data]
    values = [element[1] for element in all_data]
    #gets the last ten data points for the users weight for the graph on the user details page
    return render_template('user_details.html', title=f"Hello {account.get_username()}", labels=labels, values=values, error=error)