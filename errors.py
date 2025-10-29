class IncorrectUserInfo(Exception):
    message="Sorry, the username or password is incorrect. Maybe try again?"

class EmptyFields(Exception):
    message="Please enter data in all the fields"

class UsernameInvalid(Exception):
    message="Sorry buddy, that username has already been taken. Please try a different one."

class WorkoutNameInUse(Exception):
    message="Why would you make two workouts with the same name? Please try again buddy"

class OldPasswordInvalid(Exception):
    message="Sorry, but you got the old password wrong"

class InvalidInput(Exception):
    message="You have entered some invalid inputs. Please try again."

class FieldsTooLong(Exception):
    message='''The text fields you entered are too long'''