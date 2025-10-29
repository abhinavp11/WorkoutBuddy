import sqlite3 as sql
import abc
import statistics
from datetime import date, datetime
import errors


class DatabaseConn:
    #creates a connection to a database within a class, so you can use the same connection with all other classes
    def __init__(self,filename):
        self.db = sql.connect(filename, check_same_thread=False, detect_types=sql.PARSE_DECLTYPES )
        self.__cursor = self.db.cursor()

    def cursor(self):
        return self.db.cursor()
    #creates the cursor method which returns the cursor so that functions can be executed

class Container(abc.ABC):
    #ABSTRACT CLASS
    #for all objects that contain other objects
    def __init__(self,dbc: DatabaseConn,name, user_id):
        self._dbc = dbc
        self._cursor = self._dbc.cursor()
        self._name = name
        self._user_id = user_id
        self._next_object_id = self._get_next_object_id()

    @abc.abstractmethod
    def _create(self):
        pass
    # is run when initializing the function and sets some of the attributes of the function

    @abc.abstractmethod
    def _get_next_object_id(self):
        pass
    #gets the ID of the next object that will be contained within the container


    @abc.abstractmethod
    def get_full_contents(self):
        pass
    #returns all the objects within the container

    @abc.abstractmethod
    def get_object(self,inner_object_id):
        pass
    #gets one specific object within the container

    @abc.abstractmethod
    def get_details(self):
        pass
    #gets the details of each object in the container

    @abc.abstractmethod
    def get_id(self):
        pass
    #gets the ID of the container

    @abc.abstractmethod
    def get_view_data(self):
        pass
    #gets the data of the objects within the container in a way that it can be displayed on the web app


class InnerObject(abc.ABC):
    #ABSTRACT CLASS
    # for all objects that are inside Container objects.
    def __init__(self, dbc: DatabaseConn,id,name, user_id):
        self._dbc = dbc
        self._cursor = self._dbc.cursor()

        self._id = id
        self._name = name
        self._user_id = user_id


    @abc.abstractmethod
    def _create(self):
        pass
    # is run when initializing the function and sets some of the attributes of the function

    @property
    def id(self):
        return self._id
    #defines the ID property

    @property
    def name(self):
        return self._name
    #defines the NAME property

    @abc.abstractmethod
    def get_details(self):
        pass
    #gets the information regarding the InnerObject


class Categories:
    #class that contains each category
    #doesn't have the same use as the Container subclasses which is why is doesn't implement the Category abstract class
    def __init__(self,dbc):
        self.__dbc = dbc
        self.__cursor = self.__dbc.cursor()
        self.__categories = []
        self.__cursor.execute(f"SELECT * FROM categories")
        values = self.__cursor.fetchall()
        for element in values:
            self.__categories.append(Category(self.__dbc,element[1],element[0]))
        #selects all categories from the Category table and Category objects into the categories list
        #the information from the database is all that is needed to instantiate a Category

    def add_category(self,name,id=None):
        self.__categories.append(Category(self.__dbc,name,id))

    def get_category_names(self):
        output_list = []
        self.__cursor.execute("SELECT CategoryName FROM categories")
        for element in self.__cursor.fetchall():
            output_list.append(element[0])
        return output_list
    # returns every Category name - it is used for the Category Buttons on the website

    def get_categories(self):
        return self.__categories

    def get_category(self,name):
        for element in self.__categories:
            if element.get_name() == name:
                return element
            #gets a category by matching it by name

    def get_category_by_id(self,id):
        for element in self.__categories:
            if element.get_id() == id:
                return element

    def search_exercises(self,name):
        self.__cursor.execute(f"SELECT exercise_id FROM exercises WHERE exercise_name = '{name}'")
        return self.__cursor.fetchall()[0][0]
    #searches the database and returns the exercise ID from its name

    def get_highest_weights_display(self, user_id):
        highest_weights = []
        for element in self.__categories:
            highest_weights.append(element.get_highest_weights_display(user_id))
        return highest_weights
    # goes through every category in the category display and gets the highest weights display from each
    # highest weights display is all the highest weights structured in a way that the website can display them

    def estimate_1rmaxes(self, user_id):
        onermaxes = []
        for element in self.__categories:
            onermaxes.append(element.estimate_1rmaxes(user_id))
        return onermaxes
    # same as the get_highest_weights_display but for one rep maxes

    def get_target_weights(self, user_id):
        target_weights = []
        for element in self.__categories:
            target_weights.append(element.get_target_weights(user_id))
        return target_weights
    # same as the get_highest_weights_display but for target weights


    def update_target_weight(self, ex_id, target_weights, user_id):
        self.__cursor.execute(f'SELECT target_weight FROM target_weights WHERE exercise_id = {ex_id} and user_id = {user_id}')
        return_value = self.__cursor.fetchall()
        if len(return_value) > 0:
            #IF the exercise already has a target weight it updates the record
            self.__cursor.execute(f'UPDATE target_weights SET target_weight = {float(target_weights)} WHERE exercise_id = {ex_id} and user_id = {user_id}')
        else:
            #otherwise it just creates a new record in the target weights table
            self.__cursor.execute(f'INSERT INTO target_weights (user_id, target_weight, exercise_id) VALUES ({user_id}, {target_weights}, {ex_id})')
        self.__dbc.db.commit()


class Category(Container):
    #INHERITANCE
    def __init__(self,database_conn, name:str, category_num=None):
        super().__init__(database_conn,name, user_id=None)
        #uses the super method to execute the Container initialization method
        if category_num is None:
            self._cursor.execute(f"SELECT CategoryID FROM categories WHERE CategoryName = '{self._name}'")
            if len(self._cursor.fetchall()) == 0:
                self._id = self.get_next_category_id()
                # if no category number was supplied AND the category name is not used the system gets the next NEW category ID
            else:
                self._cursor.execute(f"SELECT CategoryID FROM categories WHERE CategoryName = '{self._name}'")
                self._id = self._cursor.fetchall()[0][0]
                # if the category already exists it just takes the ID from the database
        else:
            self._id = category_num
            # if category number is supplied it can just use that

        self.__exercises = []
        self._create()

    def _create(self):
        self._cursor.execute(f"SELECT CategoryID FROM categories WHERE CategoryID = {self._id} OR CategoryName = '{self._name}'")
        if len(self._cursor.fetchall()) == 0:
            self._cursor.execute(f"""
            INSERT INTO categories (CategoryID,CategoryName)
            VALUES ('{self._id}','{self._name}')
            """)
            self._dbc.db.commit()
            #the functionality is there to ADD a category incase the object doesn't represent a Category already
        self._cursor.execute(f"SELECT exercise_id FROM exercises WHERE category_id = '{self._id}'")
        values = self._cursor.fetchall()
        for element in values:
            self.__exercises.append(element[0])
            # adds all exercises within the Category and appends the IDS (not the actual object) to the exercise list


    def _get_next_object_id(self):
        self._cursor.execute("SELECT exercise_id FROM exercises ORDER BY exercise_id DESC")
        return self._cursor.fetchone()[0] + 1
    #gets the next NEW ID for exercises

    def get_full_contents(self):
        return self.__exercises

    def get_object(self,name):
        for element in self.__exercises:
            if element.name == name:
                return element

    def get_details(self):
        details_list = []
        for element in self.__exercises:
            self._cursor.execute(f'SELECT exercise_name FROM exercises WHERE exercise_id = {element}')
            details_list.append(self._cursor.fetchall()[0][0])
        return details_list
    #gets all the exercise names - used to create the buttons in the website

    def get_id(self):
        return self._id

    def get_view_data(self):
        details_list = []
        for element in self.__exercises:
            details_list.append(element.name)
        return details_list

    def get_name(self):
        return self._name

    def get_next_category_id(self):
        self._cursor.execute("SELECT CategoryID FROM categories ORDER BY CategoryID DESC")
        return self._cursor.fetchone()[0] + 1


    def get_highest_weight(self,ex_id, user_id):
        # gets the highest weight for a specific exercise
        self._cursor.execute(f'SELECT weight, sets, reps FROM exercise_completions WHERE exercise_id = {ex_id} and user_id = {user_id}')
        values = self._cursor.fetchall()
        highest_weight = [0,0,0]
        for element in values:
            # preforms a linear search for the highest weight in the list of data for an exercise
            if element[0] is not None and element[0] > highest_weight[0]:
                    highest_weight = element
            elif element[0] is not None and element[0] == highest_weight[0] and element[2] is not None:
                if highest_weight[2] is None:
                    highest_weight = element
                elif element[2] > highest_weight[2]:
                    highest_weight = element
        return highest_weight

    def get_highest_weights(self, user_id):
        #gets all the highest weights by iterating through every single element and executing the get_highest_weight function
        highest_weights = []
        for element in self.__exercises:
            return_val = self.get_highest_weight(element, user_id)
            highest_weights.append([element,return_val])
        return highest_weights

    def get_highest_weights_display(self, user_id):
        highest_weights = self.get_highest_weights(user_id)
        for i in range(len(highest_weights)):
            if highest_weights[i][1] == [0, 0, 0]:
                edited_value = "You have not recorded any completions of this exercise."
            else:
                edited_value = highest_weights[i][1]
                edited_value = [edited_value[0], f"{edited_value[1]}x{edited_value[2]}"]
            highest_weights[i][1] = edited_value
        return highest_weights
        # gets the highest weights DISPLAY instead - the same data represented in a way that can be displayed to the user

    def estimate_1rm(self, ex_id, user_id):
        #estimates the 1RM using the Brzycki formula
        highest_weight = self.get_highest_weight(ex_id, user_id)[0]
        reps = self.get_highest_weight(ex_id, user_id)[2]
        #starts to estimate with the highest weight recorded at first (as this is normally the most accurate)
        if reps == 0:
            reps = 1
        if highest_weight is not None:
            #now need to check if other weight and set combinations yield a different result
            self._cursor.execute(f'SELECT weight, sets, reps FROM exercise_completions WHERE exercise_id = {ex_id} and user_id = {user_id}')
            values = self._cursor.fetchall()
            lower_bound_weight = highest_weight * 0.8
            highest_bound_reps = 10
            #using this formula for more than 10 reps yields inaccurate results
            calc_list = [[highest_weight,reps]]
            for element in values:
                if element[0] is not None:
                    if element[2] is None and lower_bound_weight <= element[0] < highest_weight:
                        calc_list.append([element[0],1])
                    elif  lower_bound_weight <= element[0] < highest_weight and element[2] < highest_bound_reps:
                        calc_list.append([element[0], element[2]])
            #puts every combination of weights that MAY work in the calculation list
            calc_list = [round(element[0]/(1.0278-(0.0278 * element[1])), 2) for element in calc_list]
            # then calculates the estimated 1RM for each element in the list using the BRZYCKI FORMULA
            calc_list.sort(reverse=True)
            #sorts the list in descending order then takes the first index of the list to get the highest estimated 1RM
            return calc_list[0]
        else:
            return 0


    def estimate_1rmaxes(self, user_id):
        onermaxes = []
        for element in self.__exercises:
            return_val = self.estimate_1rm(element, user_id)
            onermaxes.append([element,return_val])
        return onermaxes
    #estimates 1RM for each exercise

    def get_target_weights(self, user_id):
        target_weights = []
        for element in self.__exercises:
            self._cursor.execute(f"SELECT target_weight FROM target_weights WHERE exercise_id = {element} and user_id = {user_id}")
            value = self._cursor.fetchall()
            if len(value) > 0:
                target_weights.append(value[0][0])
            else:
                target_weights.append(0)
        return target_weights
    #gets the target weights for every single exercise in the exercise list

class UserWorkouts(Container):
    def __init__(self, database_conn,exercise_set: Categories, user_id):
        super().__init__(database_conn, name=None, user_id=user_id)
        #calling the Container Class initializer

        self.__categories = exercise_set
        #requiures the categories so that it can retrieve exercises
        self.__workouts = []
        self._create()

    def _create(self):
        self._cursor.execute(f"SELECT workout_id, workout_name FROM workouts WHERE user_id = {self._user_id}")
        values = self._cursor.fetchall()
        for element in values:
            self.__workouts.append(Workout(element[0], element[1], self._dbc,self.__categories, self._user_id))
        #fills in the user workouts with ALL workouts from the database under the user_id specified
        #fills in list containing Workout objects (COMPOSITION)

    def _get_next_object_id(self):
        self._cursor.execute(f"SELECT workout_id FROM workouts WHERE user_id = {self._user_id} ORDER BY workout_id DESC")
        values = self._cursor.fetchall()
        if len(values) == 0:
            return 1
        return values[0][0] + 1
    #gets next available workout ID (used for adding workouts)

    def add(self, name, notes=None):
        assert len(name) < 40
        #makes sure workout name is under specified length

        workout_id = self._get_next_object_id()
        self.__workouts.append(Workout(workout_id,name,self._dbc,self.__categories, self._user_id))
        return workout_id
        #adds to the workout list, which then creates the workout too


    def delete_object(self,workout):
        workout_id = workout.id
        self._cursor.execute(f"DELETE FROM workout_exercises WHERE workout_id='{workout_id}' and user_id = {self._user_id}")
        self._dbc.db.commit()
        self._cursor.execute(f"DELETE FROM completions WHERE workout_id='{workout_id}' and user_id = {self._user_id}")
        self._dbc.db.commit()
        self._cursor.execute(f"DELETE FROM exercise_completions WHERE workout_id='{workout_id}' and user_id = {self._user_id}")
        self._dbc.db.commit()
        self._cursor.execute(f"DELETE FROM scheduled_workouts WHERE workout_id='{workout_id}' and user_id = {self._user_id}")
        self._dbc.db.commit()
        self._cursor.execute(f"DELETE FROM workouts WHERE workout_id='{workout_id}' and user_id = {self._user_id}")
        self._dbc.db.commit()
        self.__workouts.remove(workout)
        # deletes a workout and all relations to the workout

    def get_full_contents(self):
        return self.__workouts

    def get_object(self,id):
        for element in self.__workouts:
            if element.id == id:
                return element
        return None


    def get_details(self):
        details_list = []
        for element in self.__workouts:
            details_list.append(element.get_details())
        return details_list

    def get_id(self):
        return self._user_id

    def get_view_data(self):
        workout_labels = [[element.name, element.id] for element in self.__workouts]
        workout_details = []
        for element in self.__workouts:
            workout_details.append(element.get_exercise_view_data())
        #gets the name and the ID as well as the exercises that the workout has (used for displaying to the user)

        return workout_labels, workout_details

    def check_valid_workout_name(self, name):
        self._cursor.execute(f"SELECT workout_id FROM workouts WHERE workout_name = '{name}' and user_id = {self._user_id}")
        valid = self._cursor.fetchall()
        if len(valid) == 0:
            return True
        else:
            raise errors.WorkoutNameInUse
    #checks if the workout name the user has entered has already been used by the user before - if it has it raises an error

    def get_calendar_dict(self):
        self._cursor.execute(f'''SELECT workouts.workout_name, scheduled_workouts.date FROM workouts, scheduled_workouts
WHERE scheduled_workouts.user_id = {self._user_id}
AND workouts.workout_id = scheduled_workouts.workout_id
AND workouts.user_id = scheduled_workouts.user_id''')
        values = self._cursor.fetchall()
        calendar_dict = []
        for element in values:
            calendar_dict.append({
                'name': f'{element[0]}',
                'date': f'{element[1]}'
            })
        #returns a DICTIONARY for all SCHEDULED WORKOUTS
        self._cursor.execute(f'''SELECT scheduled_other_events.date FROM scheduled_other_events
WHERE scheduled_other_events.user_id = {self._user_id}''')
        values = self._cursor.fetchall()
        for element in values:
            calendar_dict.append({
                'name': 'BUSY',
                'date': f'{element[0]}'
            })
        #returns ANOTHER dictionary for all SCHEDULED BUSY DAYS
        return calendar_dict
        #the reason it has to return a calendar is that it the FullCalendar.js requires a dictionary for each event input


    def get_newest_workout(self):
        return self.__workouts[-1]
    #gets the most recently added workout object

    def get_newest_log(self, workout_id):
        self._cursor.execute(f"SELECT * FROM completions WHERE user_id = {self._user_id} and workout_id = {workout_id} ORDER BY completion_id ")
        return self._cursor.fetchall()[-1]
    #gets the data for the most recent log of any workout - used when logging a workout

    def delete_newest_log(self, workout_id):
        self._cursor.execute(f"DELETE FROM completions WHERE completion_id = {self.get_newest_log(workout_id)[0]} and user_id = {self._user_id} and workout_id = {workout_id}")
        self._dbc.db.commit()
        return True
    #used to cancel the previous log the user has entered

    def generate_reminders(self):
        reminders = Reminders(self.__categories,self.__workouts,self._dbc, self._user_id)
        reminders_list = reminders.create_all_reminders()
        return reminders_list
    #using the reminders object it creates the list of reminders for the user (to display on home screen)

    def schedule(self, schedule_date, workout_id):
        self._cursor.execute(f'''SELECT workout_id FROM scheduled_workouts WHERE user_id = {self._user_id} and date = "{schedule_date}"''')
        return_value = self._cursor.fetchall()
        if len(return_value) == 0 or workout_id not in return_value:
            #first checks to make sure the workout selected has not already been scheduled on the same day
            self._cursor.execute(f'''SELECT date FROM scheduled_other_events WHERE user_id = {self._user_id} and date = "{schedule_date}"''')
            #then checks if the same day is marked as BUSY or not
            next_return_value = self._cursor.fetchall()
            if len(next_return_value) != 0:
                self._cursor.execute(f'''DELETE FROM scheduled_other_events WHERE user_id = {self._user_id} and date = "{schedule_date}"''')
                self._dbc.db.commit()
                # if it is marked as busy, remove the entry that says it is busy
            self._cursor.execute(f'''
                            INSERT INTO scheduled_workouts (user_id, workout_id, date)
                            VALUES ({self._user_id}, {workout_id}, '{schedule_date}')
                            ''')
            #then finally schedule the workout
            self._dbc.db.commit()

    def schedule_other(self, schedule_date):
        #the exact same as the schedule function above but checks if there is already workouts scheduled instead
        self._cursor.execute(f'''SELECT date FROM scheduled_other_events WHERE user_id = {self._user_id} and date = "{schedule_date}"''')
        return_value = self._cursor.fetchall()
        if len(return_value) == 0:
            self._cursor.execute(f'''SELECT workout_id FROM scheduled_workouts WHERE user_id = {self._user_id} and date = "{schedule_date}"''')
            next_return_value = self._cursor.fetchall()
            if len(next_return_value) != 0:
                self._cursor.execute(
                    f'''DELETE FROM scheduled_workouts WHERE user_id = {self._user_id} and date = "{schedule_date}"''')
                self._dbc.db.commit()
            self._cursor.execute(f'''
                            INSERT INTO scheduled_other_events (user_id, date)
                            VALUES ({self._user_id}, '{schedule_date}')
                            ''')
            self._dbc.db.commit()

    @staticmethod
    def get_id_from_details_list(details_list,name):
        for element in details_list:
            if element[1] == name:
                return element[0]
        return None
    #static method to get the workout ID from the details list (which is the list of all workouts and their names and IDs)

class Exercise(InnerObject):
    #INHERITANCE
    def __init__(self,database_conn, id,name, cat_id, workout_id, user_id):
        super().__init__(database_conn,id,name, user_id)
        self.__category_id = cat_id
        self.__workout_id = workout_id

        self.__weight = 0.0
        self.__sets = 0
        self.__reps = 0
        self.__target_weight = 0.0

        self._create()

    def _create(self):
        self._cursor.execute(f'''SELECT current_weight, sets, reps FROM workout_exercises WHERE workout_id = {self.__workout_id} AND exercise_id = {self.id} AND user_id = {self._user_id}''')
        result = self._cursor.fetchall()[0]
        self.__weight = result[0]
        self.__sets = result[1]
        self.__reps = result[2]
        self._cursor.execute(f"SELECT target_weight FROM target_weights WHERE exercise_id = {self.id} AND user_id = {self._user_id}")
        value = self._cursor.fetchall()
        if len(value) >0:
            self.__target_weight = value[0][0]
        #fills in the values of an exercise by searching the table - much quicker than having to pass them in as parameters

    def get_details(self):
        return [self.id, self.name, self.__weight, self.__sets, self.__reps, self.__target_weight, self._user_id]

    def get_weight(self):
        return self.__weight

    def get_setsnreps(self):
        return [self.__sets,self.__reps]

    def get_cat_id(self):
        return self.__category_id

    def update_numbers(self,weight, sets, reps):
        #when the user logs the completion of an exercise this needs to be run
        #for each three parameters it checks if it has actually changed from last time, then updates the table
        if weight != self.__weight:
            self.__weight = weight
            self._cursor.execute(f'''UPDATE workout_exercises
                            SET current_weight = {self.__weight}
                            WHERE workout_id = {self.__workout_id} AND exercise_id = {self.id}
                            AND user_id = {self._user_id}''')
            self._dbc.db.commit()
        if sets != self.__sets:
            self.__sets = sets
            self._cursor.execute(f'''UPDATE workout_exercises
            SET sets = {self.__sets}
            WHERE workout_id = {self.__workout_id} AND exercise_id = {self.id}
            AND user_id = {self._user_id}''')
            self._dbc.db.commit()
        if reps != self.__reps:
            self.__reps = reps
            self._cursor.execute(f'''UPDATE workout_exercises
            SET reps = {self.__reps}
            WHERE workout_id = {self.__workout_id} AND exercise_id = {self.id}
            AND user_id = {self._user_id}''')
            self._dbc.db.commit()

    def get_current_vals(self):
        str=f"Currently: {self.__weight}kg for {self.__sets}x{self.__reps}"
        return str
    #gets current weight, sets and reps in a way that can be displayed to the user

    def get_target_weight(self):
        return self.__target_weight


class Workout(InnerObject):
    #INHERITANCE
    def __init__(self, id, name, database_conn,exercise_set: Categories, user_id):
        super().__init__(database_conn,id,name, int(user_id))
        self.__categories = exercise_set
        self.__exercises = []
        self._cursor.execute(f"SELECT workout_id FROM workouts where workout_id = {self._id} and user_id = {self._user_id}")
        self._create()
        self.__completions = self.__get_completions()


    def _create(self):
        if len(self._cursor.fetchall()) == 0:
            self._cursor.execute(f"""
            INSERT INTO workouts (workout_id,workout_name, user_id)
            VALUES ('{self._id}','{self._name}', '{self._user_id}')
            """)
            self._dbc.db.commit()
            #if the workout doesn't already exist, it enters a new one into the database
        exercises = self.__get_exercises()
        for element in exercises:
            self.__exercises.append(Exercise(self._dbc,element[0],element[1],element[2],self._id, self._user_id))
            # adds all exercise objects to the exercises list - COMPOSITION


    def __get_completions(self):
        self._cursor.execute(f"SELECT completion_id FROM completions WHERE workout_id = {self.id} and user_id = {self._user_id} ORDER BY completion_id DESC")
        value = self._cursor.fetchall()
        if len(value) == 0:
            return 0
        else:
            return value[0][0]
        #gets the number of times the workout has been completed

    def get_details(self):
        self._cursor.execute(f"SELECT * FROM workouts WHERE workout_id = {self._id} and user_id = {self._user_id}")
        return self._cursor.fetchall()[0]
        #gets the name, id and user id of each workout

    def __get_exercises(self):
        self._cursor.execute(f"""
        SELECT exercises.exercise_id, exercise_name, category_id, workout_exercises.user_id FROM workout_exercises, exercises, users, workouts
        WHERE users.user_id = workout_exercises.user_id AND workouts.user_id = users.user_id
        AND workout_exercises.exercise_id = exercises.exercise_id
        AND workout_exercises.workout_id = workouts.workout_id
        AND users.user_id = {self._user_id}
        AND workouts.workout_id = {self.id}
        """)
        return self._cursor.fetchall()
    #gets all the exercises for the specific workout

    def get_user_id(self):
        return self._user_id

    def get_exercise_names(self):
        details_list = []
        for element in self.__exercises:
            details_list.append(element.name)
        return details_list

    def get_exercise(self,ex_id):
        for element in self.__exercises:
            print(element.id)
            if element.id == ex_id:
                return element

    def get_exercise_view_data(self):
        details_list = []
        for element in self.__exercises:
            list = [element.name, element.get_weight(), element.get_setsnreps()]
            details_list.append(list)
        for i in range(len(details_list)):
            str=f"{details_list[i][0]} - {details_list[i][1]}kg - {details_list[i][2][0]}x{details_list[i][2][1]}"
            details_list[i] = str
        return details_list
    #returns all the exercises and their details in a way that can be viewed by the user


    def add_exercise(self, exercise_id, weight, sets=0, reps=0):
        self._cursor.execute(f"SELECT wk_ex_id FROM workout_exercises WHERE workout_id = {self.id} AND exercise_id = {exercise_id} and user_id = {self._user_id}")
        #checks if the workout has already got this exercise
        if len(self._cursor.fetchall()) == 0:
            #EXCEPTION HANDLING - in case the user enters an invalid input for the weight sets and reps
            try:
                self._cursor.execute(f"""
                        INSERT INTO workout_exercises (workout_id, exercise_id, current_weight, sets, reps,user_id)
                        VALUES ('{self._id}', '{exercise_id}', {weight}, {sets}, {reps}, {self._user_id})
                    """)
                self._dbc.db.commit()
                #if no error it adds the exercise
            except sql.OperationalError:
                return False
            self._cursor.execute(f"""SELECT exercise_name, category_id FROM exercises WHERE exercise_id = '{exercise_id}'""")
            values = self._cursor.fetchall()[0]
            # now adds the new exercise object to exercise list
            self.__exercises.append(Exercise(self._dbc,exercise_id, values[0], values[1], self.id, self._user_id))
            return True


    def delete_exercise_from_workout(self, exercise_id):
        self._cursor.execute(f"""
                DELETE FROM workout_exercises 
                WHERE workout_id = '{self._id}' AND exercise_id = '{exercise_id}' AND user_id = '{self._user_id}'
        """)
        self._dbc.db.commit()
        self.__exercises.remove(self.get_exercise(exercise_id))

    def add_log(self):
        self.__completions += 1
        self._cursor.execute(f"""INSERT INTO completions (completion_id, date, workout_id, user_id)
        VALUES ({self.__completions},'{date.today()}',{self.id}, {self._user_id})
        """)
        self._dbc.db.commit()
        return self.__completions
    #adds a completion of a workout being completed by inserting the record

    def add_exercise_complete(self,ex_id,completion_id,weight, sets, reps):
        self._cursor.execute(
            f'''SELECT current_weight, sets, reps FROM workout_exercises 
            WHERE workout_id = {self.id} AND exercise_id = {ex_id} AND user_id = {self._user_id}''')
        value = self._cursor.fetchall()
        #has to retrieve the current weight so that it can send it to the past exercise completions table (as this is the weight completed now)
        if len(value) > 0:
            result = value[0]
            current_weight = result[0]
            current_sets = result[1]
            current_reps = result[2]
        else:
            current_weight = 0
            current_sets = 0
            current_reps = 0
        self._cursor.execute(f"""SELECT * FROM exercise_completions 
        WHERE completion_id = {completion_id} AND workout_id = {self.id} AND exercise_id = {ex_id} AND user_id = {self._user_id}""")
        #checks if there is already a completion of this exercise within this workout and completion id
        if len(self._cursor.fetchall()) == 0:
            self._cursor.execute(f"""INSERT INTO exercise_completions (completion_id, workout_id, exercise_id, weight, sets, reps, user_id)
                    VALUES ({completion_id},{self.id}, {ex_id}, {current_weight}, {current_sets}, {current_reps}, {self._user_id})""")
            #inserts the current weights into the past exercise completions table
            self._dbc.db.commit()
        self.get_exercise(ex_id).update_numbers(weight, sets, reps)
        #uses the values the user entered to update the values for next time

    def add_many_exercises_complete(self,exercise_list):
        if exercise_list is not None:
            print(exercise_list)
            for element in exercise_list:
                self.add_exercise_complete(element[0],element[1],element[2],element[3],element[4])

    def get_recent_completions(self, record_number):
        self._cursor.execute(f"""SELECT * FROM completions WHERE workout_id = {self.id} AND user_id = {self._user_id}""")
        data = self._cursor.fetchall()
        #gets all the completions of the workout
        record_number = min(record_number,len(data))
        #if there is fewer data than the number of records specified, it will return just the whole data.
        initial_data = []
        #initial data is the details of the completion - completion id, date, etc.
        secondary_data = []
        #secondary data is the details of the exercises being completed
        if len(data) != 0:
            for i in range(0,record_number):
                initial_data.append(data[-1-i])
                completion_id = data[-1-i][0]
                self._cursor.execute(f"""SELECT exercise_id, weight, sets, reps FROM exercise_completions WHERE completion_id = {completion_id} AND workout_id = {self.id} AND user_id = {self._user_id}""")
                #gets the exercises completed under the current completion id
                secondary_data.append(self._cursor.fetchall())
            initial_data = [[element[0],element[2]] for element in initial_data]
            for i in range(len(secondary_data)):
                if len(secondary_data[i]) != 0:
                    for j in range(len(secondary_data[i])):
                        secondary_data[i][j] = self.get_exercise(secondary_data[i][j][0]).name, secondary_data[i][j][1], secondary_data[i][j][2] ,secondary_data[i][j][3]
                        #sets the secondary data to contain the exercise name, the weight sets and reps
        return initial_data,secondary_data

    def produce_current_vals(self):
        details_list = []
        for element in self.__exercises:
            details_list.append(element.get_current_vals())
        return details_list
    #gets the current weight sets and reps for the exercise.


class Reminders:
    #object that contains all the methods necessary to create the reminders
    def __init__(self, categories, workouts,dbc:DatabaseConn,user_id):

        self._dbc = dbc
        self.__cursor = self._dbc.cursor()

        self.__user_id = user_id
        self.__categories = categories
        self.__workouts = workouts

    def __generate_date(self,months_ago, new_month=0, new_day=0, new_year=0):
        # generates a date from a specified number of months ago
        # used in this object so that the completions in the past month can be found.
        current_day = (date.today()).day
        current_month = (date.today()).month
        current_year = (date.today()).year
        if new_month == 0:
            new_month = current_month
        if new_year == 0:
            new_year = current_year
        if new_day == 0:
            new_day = current_day
        #if the new values haven't been changed, they are the same as the current day
        new_date = None
        if months_ago != 0:
            if months_ago > 1:
                if new_month == 1:
                    new_month = 12
                    new_year -= 1
                else:
                    new_month -= 1
                # if months ago is more than 1, it takes a month away from the date and then runs the program again
                months_ago -= 1
                return self.__generate_date(months_ago, new_month, new_day, new_year)
                #the new values are non-zero after the program calls itself
            if months_ago == 1:
                correct_date = False
                if new_month == 1:
                    new_month = 12
                    new_year -= 1
                else:
                    new_month -= 1
                while not correct_date:
                    #this is used as sometimes the date will not exist, e.g. February 30th
                    try:
                        #EXCEPTION HANDLING
                        new_date = date(new_year, new_month, new_day)
                        correct_date = True
                    except ValueError:
                        new_day -= 1
                        #if there is a value error it just subtracts a day away, keeps doing this until no more ValueError
        return new_date

    def __update_frequency_of_workout_reminder(self):
        past_date = self.__generate_date(1)
        days_range = (date.today() - past_date).days
        #SQL FROM MANY INTERLINKED TABLES WITH AGGREGATE FUNCTION
        self.__cursor.execute(f'''SELECT COUNT(completion_id), workouts.workout_id 
FROM workouts, completions, users 
WHERE completions.workout_id = workouts.workout_id
AND workouts.user_id = users.user_id
AND date BETWEEN '{past_date}' and '{date.today()}'
AND users.user_id = {self.__user_id} and completions.user_id = {self.__user_id}
GROUP BY workouts.workout_id''')
        #this SQL query counts how many times each workout has been completed between a range of dates
        values = self.__cursor.fetchall()
        workout_ids = []
        completions = []
        for element in values:
            workout_ids.append(element[1])
            completions.append(element[0])
            #creates a parallel list with workouts and their corresponding completion numbers
        reminders = []
        for i in range(len(workout_ids)):
            string = ""
            workout_name = self.__get_object_by_id(self.__workouts,workout_ids[i]).name
            frequency = days_range/completions[i]
            #checks how often the user has completed a workout
            if 2 < frequency < 8:
                string += f"Your '{workout_name}' workout has been completed with a good frequency.\n"
            elif frequency <= 2:
                string +=f"Your '{workout_name}' workout has been completed too frequently.\n"
            elif frequency >= 8:
                string += f"Your '{workout_name}' workout has been completed with too little frequency.\n"
            #returns corresponding message back to the user
            if completions[i] > 2:
                #this section of the code checks the gaps in between each workout
                self.__cursor.execute(f'''SELECT date FROM completions 
                WHERE workout_id = {workout_ids[i]} AND 
                completions.user_id = {self.__user_id} AND
                date BETWEEN "{past_date}" and "{date.today()}"''')
                dates = self.__cursor.fetchall()
                #gets the date of each workout completion for one workout at a time
                days_between = [dates[0]]
                for j in range(1, len(dates)):
                    date_prev = datetime.strptime(days_between[j-1][0], "%Y-%m-%d")
                    date_current = datetime.strptime(dates[j][0], "%Y-%m-%d")
                    insert_value = date_current - date_prev
                    days_between[j-1] = int(insert_value.days)
                    days_between.append(dates[j])
                days_between.pop(-1)
                #this for loop goes through the list to create a list with the GAPS in between each workout
                average = round(statistics.median(days_between),2)
                #gets the average gap between each workout
                stdev = round(statistics.stdev(days_between),2)
                outliers = []
                for element in days_between:
                    if self.__is_outlier(element,stdev,average) is True:
                        outliers.append(element)
                #checks for any outliers
                large_rests = False
                for element in days_between:
                    if element > 8 and large_rests == False:
                        large_rests = True
                #also checks for any large gaps in between workouts
                if len(outliers) >= 0.2 * completions[i] or large_rests:
                    #if there are enough outliers or there is a large rest it alerts the user
                    string += f"The completions of your workout '{workout_name}' are not spread evenly across the time period."
                else:
                    string += f"The completions of your workout '{workout_name}' are spread evenly across the time period."
            reminders.append(string)
        return reminders
    #CHECKS IF FRQ. OF WORKOUT TOO LOW

    def __update_frequency_of_muscle_group_reminder(self):
        past_date = self.__generate_date(1)
        days_range = (date.today() - past_date).days
        #SQL FROM MANY INTERLINKED TABLES WITH AGGREGATE FUNCTION
        self.__cursor.execute(f'''SELECT COUNT(DISTINCT exercise_completions.completion_id), categories.CategoryID
FROM categories, completions, exercise_completions, exercises, users
WHERE exercise_completions.completion_id = completions.completion_id
AND completions.date BETWEEN '{past_date}' and '{date.today()}'
AND completions.user_id = exercise_completions.user_id
AND completions.user_id = {self.__user_id}
AND exercise_completions.exercise_id = exercises.exercise_id
AND exercises.category_id = categories.CategoryID
GROUP BY categories.CategoryID''')
        #checks the number of times an exercise of a particular muscle group has been completed between two dates
        # THE REST OF THE PROGRAM IS THE SAME AS THE __update_frequency_of_workout_reminder PROGRAM, JUST FOR MUSCLE GROUPS
        values = self.__cursor.fetchall()
        cat_ids = []
        completions = []
        for element in values:
            cat_ids.append(element[1])
            completions.append(element[0])
        reminders = []
        for i in range(len(cat_ids)):
            string = ""
            cat_name = self.__categories.get_category_by_id(cat_ids[i]).get_name()
            frequency = days_range/completions[i]
            if 2 < frequency < 6:
                string += f"You have trained the '{cat_name}' muscle group with a good frequency.\n"
            elif frequency <= 2:
                string +=f"You have trained the '{cat_name}' muscle group too frequently.\n"
            elif frequency >= 6:
                string += f"You have trained the '{cat_name}' muscle group with too little frequency.\n"
            if completions[i] > 2:
                self.__cursor.execute(f'''SELECT DISTINCT completions.date FROM completions, exercise_completions, categories, exercises, users 
WHERE completions.completion_id = exercise_completions.completion_id 
AND exercise_completions.exercise_id = exercises.exercise_id
AND exercises.category_id = categories.CategoryID AND categories.CategoryID = {cat_ids[i]}
AND completions.user_id = users.user_id
AND completions.user_id = {self.__user_id}
AND date BETWEEN "{past_date}" and "{date.today()}"''')
                #gets the date between each exercise of the particular muscle group being trained
                dates = self.__cursor.fetchall()
                days_between = [dates[0]]
                for j in range(1, len(dates)):
                    date_prev = datetime.strptime(days_between[j-1][0], "%Y-%m-%d")
                    date_current = datetime.strptime(dates[j][0], "%Y-%m-%d")
                    insert_value = date_current - date_prev
                    days_between[j-1] = int(insert_value.days)
                    days_between.append(dates[j])
                days_between.pop(-1)
                average = round(statistics.median(days_between),2)
                stdev = round(statistics.stdev(days_between),2)
                outliers = []
                for element in days_between:
                    if self.__is_outlier(element,stdev,average) is True:
                        outliers.append(element)
                large_rests = False
                for element in days_between:
                    if element > 8 and large_rests == False:
                        large_rests = True
                if len(outliers) >= 0.2 * completions[i] or large_rests:
                    string += f"The dates you worked out the '{cat_name}' are not spread evenly across the time period."
                else:
                    string += f"The dates you worked out the '{cat_name}' are spread evenly across the time period."
            reminders.append(string)
        return reminders
    #CHECKS IF FRQ. OF MUSCLE GROUP TOO LOW

    def __update_frequency_of_exercise_reminder(self):
        past_date = self.__generate_date(1)
        days_range = (date.today() - past_date).days
        self.__cursor.execute(f'''SELECT COUNT(exercise_completions.completion_id), exercises.exercise_name, exercises.exercise_id
FROM categories, completions, exercise_completions, exercises
WHERE completions.completion_id = exercise_completions.completion_id 
AND exercise_completions.exercise_id = exercises.exercise_id
AND exercises.category_id = categories.CategoryID
AND completions.user_id = {self.__user_id}
AND exercise_completions.user_id = {self.__user_id}
AND exercise_completions.workout_id = completions.workout_id 
AND date BETWEEN '{past_date}' and '{date.today()}'
GROUP BY exercises.exercise_id
        ''')
        # checks the number of times a specific exercise has been completed between two dates
        # THE REST OF THE PROGRAM IS THE SAME AS THE __update_frequency_of_workout_reminder PROGRAM, JUST FOR EXERCISES
        values = self.__cursor.fetchall()
        ex_names = []
        ex_ids = []
        completions = []
        for element in values:
            ex_names.append(element[1])
            completions.append(element[0])
            ex_ids.append(element[2])
        reminders = []
        for i in range(len(ex_names)):
            string = ""
            ex_name = ex_names[i]
            frequency = days_range/completions[i]
            if 2 < frequency < 8:
                string += f"The '{ex_name}' exercise has been completed with a good frequency.\n"
            elif frequency <= 2:
                string +=f"The '{ex_name}' exercise has been completed too frequently.\n"
            elif frequency >= 8:
                string += f"The '{ex_name}' exercise has been completed with too little frequency.\n"

            if completions[i] > 2:
                self.__cursor.execute(f''' SELECT DISTINCT completions.date
FROM categories, completions, exercise_completions, exercises
WHERE completions.completion_id = exercise_completions.completion_id 
AND completions.user_id = {self.__user_id}
AND exercise_completions.exercise_id = exercises.exercise_id
AND exercises.category_id = categories.CategoryID
AND exercise_completions.workout_id = completions.workout_id
AND exercises.exercise_id = {ex_ids[i]}
AND date BETWEEN '{past_date}' and '{date.today()}'
ORDER BY date ASC
''')
                #gets the dates of each exercise being completed
                dates = self.__cursor.fetchall()
                days_between = [dates[0]]
                for j in range(1, len(dates)):
                    date_prev = datetime.strptime(days_between[j-1][0], "%Y-%m-%d")
                    date_current = datetime.strptime(dates[j][0], "%Y-%m-%d")
                    insert_value = date_current - date_prev
                    days_between[j-1] = int(insert_value.days)
                    days_between.append(dates[j])
                days_between.pop(-1)
                print(days_between)
                average = round(statistics.median(days_between),2)
                stdev = round(statistics.stdev(days_between),2)
                outliers = []
                for element in days_between:
                    if self.__is_outlier(element,stdev,average) is True:
                        outliers.append(element)
                large_rests = False
                for element in days_between:
                    if element > 8 and large_rests == False:
                        large_rests = True
                if len(outliers) >= 0.2 * completions[i] or large_rests:
                    string += f"The completions of the exercise '{ex_name}' are not spread evenly across the time period."
                else:
                    string += f"The completions of the exercise '{ex_name}' are spread evenly across the time period."
            reminders.append(string)
        return reminders
    #CHECKS IF FRQ. OF EXERCISE TOO LOW

    def __update_target_weight_almost_reached_reminder(self):
        reminders = []
        self.__cursor.execute(f'''SELECT DISTINCT exercises.exercise_name FROM workout_exercises, target_weights, exercises
WHERE workout_exercises.exercise_id = target_weights.exercise_id AND workout_exercises.current_weight >= (0.9*target_weights.target_weight)
AND workout_exercises.current_weight < target_weights.target_weight
AND workout_exercises.exercise_id = exercises.exercise_id
AND target_weights.user_id = {self.__user_id}''')
        #SQL FROM SEVERAL INTERLINKED TABLES
        #checks if there are any exercises where the user is close to their target_weight in their completions but not currently above the target weight
        close_to_weight_exercises = self.__cursor.fetchall()
        self.__cursor.execute(f'''SELECT DISTINCT exercises.exercise_name FROM exercises, workout_exercises, target_weights
WHERE workout_exercises.current_weight > target_weights.target_weight AND 
target_weights.exercise_id = workout_exercises.exercise_id 
AND target_weights.user_id = workout_exercises.user_id 
AND workout_exercises.exercise_id = exercises.exercise_id
AND target_weights.user_id = {self.__user_id}''')
        #checks if there are any exercises where the user is ABOVE their target_weight
        above_weight_exercises = self.__cursor.fetchall()
        for element in above_weight_exercises:
            if element in close_to_weight_exercises:
                close_to_weight_exercises.remove(element)
                above_weight_exercises.remove(element)
                string = f"You hit your target weight for {element[0]} - WELL DONE!"
                reminders.append(string)
        for element in close_to_weight_exercises:
            string = f"You are very close to your target weight for {element[0]} - KEEP GOING!"
            reminders.append(string)
        for element in above_weight_exercises:
            string = f"You hit your target weight for {element[0]} - WELL DONE!"
            reminders.append(string)
        #alerts the user if they are close or above their target
        return reminders
    #CHECKS IF CLOSE TO TARGET WEIGHT

    def __update_changing_weight_reminders(self):
        self.__cursor.execute(f'''
        SELECT DISTINCT exercise_name FROM exercises,exercise_completions, users
        WHERE exercise_completions.exercise_id = exercises.exercise_id 
        AND exercise_completions.user_id = users.user_id
        AND users.user_id = {self.__user_id}''')
        #selects all the exercises that the user has completed
        ex_names = self.__cursor.fetchall()
        ex_names = [element[0] for element in ex_names]
        reminders = []
        for element in ex_names:
            plateau = False
            self.__cursor.execute(f'''SELECT weight FROM exercises,exercise_completions, users
            WHERE exercise_completions.exercise_id = exercises.exercise_id AND 
            exercise_name = '{element}' 
            AND exercise_completions.user_id = users.user_id
            AND users.user_id = {self.__user_id}''')
            #for each exercise, it selects the weights that the user has recorded
            list_of_weights = self.__cursor.fetchall()
            list_of_weights = [element[0] for element in list_of_weights]
            if len(list_of_weights) > 2:
                i = 0
                while not plateau and i < len(list_of_weights) - 2:
                    if list_of_weights[i] == list_of_weights[i+1] == list_of_weights[i+2]:
                        plateau = True
                        #checks if they have used the same weight for 3 sessions in a row - if they have it tells them they have hit a plateau
                    i += 1
            elif len(list_of_weights) == 2:
                if list_of_weights[0] == list_of_weights[1]:
                    plateau = True

            if plateau:
                reminders.append(f"You have used the same weight for '{element}' multiple sessions in a row")
        return reminders

    #CHECKS IF INCREASING/UPDATING WEIGHT TOO LITTLE

    def create_all_reminders(self):
        reminders_list = []
        reminders_list.append(['Workout Frequency alerts', self.__update_frequency_of_workout_reminder()])
        reminders_list.append(['Exercise Frequency alerts', self.__update_frequency_of_exercise_reminder()])
        reminders_list.append(['Muscle group alerts', self.__update_frequency_of_muscle_group_reminder()])
        reminders_list.append(['Target Weight alerts', self.__update_target_weight_almost_reached_reminder()])
        reminders_list.append(['Weight progress alerts', self.__update_changing_weight_reminders()])
        return reminders_list
        #creates all reminders

    @staticmethod
    def __is_outlier(x,stdev,mean):
        if mean - (stdev*2) <= x <= mean + (stdev*2):
            return False
        else:
            return True
        #checks if number entered is more than 2*stdev outside the mean - if so it is an outlier
        #STATISTICAL CALCULATION

    @staticmethod
    def __get_object_by_id(list,id):
        for element in list:
            if element.id == id:
                return element
        return None


class AllWorkouts:
    #contains every single workout on the database
    # is used just to generate the UserWorkouts object
    def __init__(self,database_conn: DatabaseConn, exercise_set: Categories):
        self.__dbc = database_conn
        self.__cursor = self.__dbc.cursor()
        self.__exercise_set = exercise_set
        self.__user_workouts = []

        self.__create()

    def __create(self):
        self.__cursor.execute('SELECT user_id FROM users')
        values = self.__cursor.fetchall()
        for element in values:
            #creates a list of UserWorkouts objects by using the user_id to instatiate them
            self.__user_workouts.append(UserWorkouts(self.__dbc,self.__exercise_set,element[0]))

    def get_all_workouts(self):
        return self.__user_workouts

    def get_all_user_workouts(self, user_id):
        for element in self.__user_workouts:
            if user_id == element.get_id():
                return element
        return None
    #returns the UserWorkouts object from the ID entered

class Completions:
    #used to monitor past completions of a workout
    def __init__(self, dbc:DatabaseConn, user_id):
        self._dbc = dbc
        self.__cursor = self._dbc.cursor()
        self.__user_id = user_id
        self.__exercises = []
        self.__completion_data = []


        self.__create()

    def __create(self):
        self.__exercises = self.get_exercises()
        for element in self.__exercises:
            self.__cursor.execute(f'''SELECT  ROW_NUMBER () OVER ( 
                            ORDER BY completions.date 
                            ) RowNum,
                            exercise_completions.weight, exercise_completions.reps
                    FROM categories, completions, exercise_completions, exercises
                    WHERE completions.completion_id = exercise_completions.completion_id 
                    AND exercise_completions.exercise_id = exercises.exercise_id
                    AND exercises.category_id = categories.CategoryID
                    AND completions.user_id = {self.__user_id}
                    AND exercises.exercise_name = '{element}'
                    AND exercise_completions.workout_id = completions.workout_id 
                    ORDER BY completions.date ASC''')
            #using the row number operator to make the data numbered - it essentially adds row numbers to each row and the
            #row number of each row depends on the order of the completion date values. This is then given the value RowNum
            value = self.__cursor.fetchall()
            value = [(element[0], element[1], element[2], self.__calculate_1rm(element[1], element[2])) for element in value]
            self.__completion_data.append(value)
            #completion data list contains sequential data of the completions and their data in the order below
            # data order : order, weight, reps, estimated 1 rep max

    def get_exercises(self):
        self.__cursor.execute(f'''SELECT DISTINCT exercises.exercise_name
                            FROM exercises, exercise_completions
                            WHERE exercise_completions.exercise_id = exercises.exercise_id
                            AND exercise_completions.user_id = {self.__user_id}''')
        values = self.__cursor.fetchall()
        values = [element[0] for element in values]
        return values
    #gets all the exercises the user has completed - used to create the labels for buttons

    @staticmethod
    def __calculate_1rm(weight, reps):
        if reps == 0:
            return weight
        if weight == 0:
            return 0
        return round(weight/(1.0278 - 0.0278*reps), 2)
    #using the BRYZKI FORMULA

    def get_graph_data_for_exercise(self, exercise_name, number_of_data_points):
        index = 0
        found = False
        while found == False and index < len(self.__exercises):
            if self.__exercises[index] == exercise_name:
                found = True
                #finds the index needed to access the completion data list as they are parallel lists
            else:
                index += 1
        data = self.__completion_data[index]
        if number_of_data_points >= len(data):
            return data
        else:
            return data[len(data) - number_of_data_points: len(data)]
            #splices the list if there is too much data
    #gets all the data needed to display it on the graph.

