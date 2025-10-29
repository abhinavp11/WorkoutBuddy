from datetime import date

import errors
import workout_objects as obj
from passlib.hash import pbkdf2_sha256 as p_hash

connection = obj.DatabaseConn('workoutbuddy_database.db')
#creating the connection to the database

def login(username, passkey, dbc: obj.DatabaseConn):
    cursor = dbc.db.cursor()
    cursor.execute(f'SELECT user_passkey FROM users WHERE user_name = "{username}"')
    return_passkey = cursor.fetchall()
    if len(return_passkey) > 0:
        correct_passkey = p_hash.verify(passkey,return_passkey[0][0])
        # PASSWORD HASHING
        #using the built-in method to verify if the password entered matches the hashed password in the database
        if correct_passkey:
            cursor.execute(f'SELECT user_id FROM users WHERE user_name = "{username}"')
            return cursor.fetchall()[0][0]
            # returns the user_id so the website will recognise the user is logged in.
        else:
            raise errors.IncorrectUserInfo
    else:
        raise errors.IncorrectUserInfo

def check_if_name_in_use(username,dbc:obj.DatabaseConn):
    cursor = dbc.db.cursor()
    cursor.execute(f'SELECT user_id FROM users WHERE user_name = "{username}"')
    # selects all users_ids with the name, so it can check if a user with the name already exists
    return_value = cursor.fetchall()
    if len(return_value) == 0:
        return False
    else:
        raise errors.UsernameInvalid

def create_new_account(username, passkey, dbc: obj.DatabaseConn):
    cursor = dbc.db.cursor()
    user_id = get_next_user_id(dbc)
    #get_next_user_id gets the next unique user_id by preforming an SQL search

    assert len(username) < 40
    assert len(passkey) < 30
    # making sure the user hasn't entered an overly long username or password

    cursor.execute(f'INSERT INTO users (user_id, user_passkey, user_name,current_weight) VALUES ({int(user_id)}, "{p_hash.hash(passkey)}", "{username}",0)')
    dbc.db.commit()

def get_next_user_id(dbc: obj.DatabaseConn):
    cursor = dbc.db.cursor()
    cursor.execute(f'SELECT user_id FROM users ORDER BY user_id DESC')
    values = cursor.fetchall()
    if len(values) == 0:
        return 1
    return values[0][0] + 1
    #gets the next available user_id

def create_starter_workouts(dbc: obj.DatabaseConn, user_id):
    cursor = dbc.db.cursor()
    cursor.execute(f'''INSERT INTO workouts (workout_id, workout_name, user_id)
    VALUES (1, "Push", {user_id})''')
    dbc.db.commit()
    cursor.execute(f'''INSERT INTO workouts (workout_id, workout_name, user_id)
        VALUES (2, "Pull", {user_id})''')
    dbc.db.commit()
    cursor.execute(f'''INSERT INTO workouts (workout_id, workout_name, user_id)
        VALUES (3, "Legs", {user_id})''')
    dbc.db.commit()
    sequence = [(1, 17), (1, 23), (1, 36), (1, 26), (1, 32), (1, 27), (2, 1), (2, 2), (2, 11), (2, 12), (3, 41),
                (3, 39), (3, 40), (3, 43), (3, 42)]
    #the numbers represent the workout ids in the first index and the exercise ids in the second index of each array
    cursor.executemany(f'''INSERT INTO workout_exercises (workout_id, exercise_id, current_weight, sets, reps, user_id)
    VALUES (?, ?, 0, 0, 0, {user_id})''', sequence)
    dbc.db.commit()
    #using the execute many command it creates the 'starter workouts'

class Account:
    #creates an Account for the user - this is used when the user wants to update their details
    def __init__(self, user_id, dbc: obj.DatabaseConn):
        self.__user_id = user_id
        self.__dbc = dbc
        self.__cursor = self.__dbc.cursor()
        self.__username = None
        self.__current_weight = None

        self.__create()

    def __create(self):
        self.__cursor.execute(f'SELECT user_name, current_weight FROM users WHERE user_id = {self.__user_id}')
        values = self.__cursor.fetchall()[0]
        self.__username = values[0]
        self.__current_weight = values[1]
        # fills out the username and current weight attributes using the User ID
        # this means the only thing that needs to be entered when creating a class is the User ID

    def get_username(self):
        return self.__username


    def update_weight(self, new_weight):
        self.__cursor.execute(f'SELECT current_weight FROM users WHERE user_id = {self.__user_id}')
        if new_weight != self.__cursor.fetchall()[0][0]:
        # checks if the new weight is the same as the current weight - if it is then it will not update
            self.__current_weight = new_weight
            self.__cursor.execute(f'INSERT INTO users_weights(user_id,weight,date) VALUES ({self.__user_id},{self.__current_weight},"{date.today()}")')
            self.__dbc.db.commit()
            #places the old current weight into the users past weights table
            self.__cursor.execute(f'UPDATE users SET current_weight = {new_weight} WHERE user_id = {self.__user_id}')
            self.__dbc.db.commit()
            #sets the users current weight to the new current weight


    def get_weights(self, number_of_data_points):
        self.__cursor.execute(f'''SELECT  ROW_NUMBER () OVER (ORDER BY users_weights.date) RowNum, users_weights.weight
FROM users_weights
WHERE users_weights.user_id = {self.__user_id}''')
        # using the row number function it generates sequential numbers to the past user weights (using ORDER BY)
        data = self.__cursor.fetchall()
        if number_of_data_points >= len(data):
            return data
            #if number of data points is less than specified, it just returns the full data
        else:
            return data[len(data) - number_of_data_points: len(data)]
            # if not it splices the list to get the last few elements

    def update_username(self, new_username):
        self.__cursor.execute(f'SELECT user_id FROM users WHERE user_name = "{new_username}"')
        if len(self.__cursor.fetchall()) == 0:
            #checks if the username is the same as before, only then it updates
            self.__cursor.execute(f'UPDATE users SET user_name = "{new_username}" WHERE user_id = {self.__user_id}')
            self.__dbc.db.commit()
            self.__username = new_username
            return True
        raise errors.UsernameInvalid

    def update_password(self, old_password, new_password):
        self.__cursor.execute(f'SELECT user_passkey FROM users WHERE user_id = "{self.__user_id}"')
        return_passkey = self.__cursor.fetchall()[0][0]
        correct_passkey = p_hash.verify(old_password, return_passkey)
        # checks if the password entered before is correct, just like the login function
        if correct_passkey:
            self.__cursor.execute(f'UPDATE users SET user_passkey = "{p_hash.hash(new_password)}" WHERE user_id = {self.__user_id}')
            #updates the user passkey and by entering the new hashed password
            self.__dbc.db.commit()
            return True
        else:
            raise errors.OldPasswordInvalid