import random

def generate_random_birthdate(min_year, max_year):
    """
    generates a random birthdate between min_year and max_year (inclusive).
    returns a tuple (day, month, year) as strings.
    """
    year = random.randint(min_year, max_year)
    month = random.randint(1, 12)
    
    if month in [1, 3, 5, 7, 8, 10, 12]:
        day = random.randint(1, 31)
    elif month in [4, 6, 9, 11]:
        day = random.randint(1, 30)
    else: # february
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0): # leap year
            day = random.randint(1, 29)
        else:
            day = random.randint(1, 28)
            
    return str(day), str(month), str(year)