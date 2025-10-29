from datetime import date


def generate_date( months_ago, new_month=0, new_day=0, new_year=0):
    # most beautiful program I have ever made
    current_day = (date.today()).day
    current_month = (date.today()).month
    current_year = (date.today()).year
    if new_month == 0:
        new_month = current_month
    if new_year == 0:
        new_year = current_year
    if new_day == 0:
        new_day = current_day
    new_date = None
    if months_ago != 0:
        if months_ago > 1:
            if new_month == 1:
                new_month = 12
                new_year -= 1
            else:
                new_month -= 1
            months_ago -= 1
            return generate_date(months_ago, new_month, new_day, new_year)
        if months_ago == 1:
            correct_date = False
            if new_month == 1:
                new_month = 12
                new_year -= 1
            else:
                new_month -= 1
            while not correct_date:
                try:
                    new_date = date(new_year, new_month, new_day)
                    correct_date = True
                except ValueError:
                    new_day -= 1
    return new_date


