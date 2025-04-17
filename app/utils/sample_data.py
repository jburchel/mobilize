"""
Sample Data Generation Utilities
Used for testing and development purposes
"""

import random
import string
from datetime import datetime, timedelta

# Lists for generating random data
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", 
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", 
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Margaret", 
    "Matthew", "Lisa", "Anthony", "Betty", "Mark", "Dorothy", "Donald", "Sandra", 
    "Steven", "Ashley", "Paul", "Kimberly", "Andrew", "Donna", "Joshua", "Emily", 
    "Kenneth", "Michelle", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", 
    "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", 
    "Thompson", "Garcia", "Martinez", "Robinson", "Clark", "Rodriguez", "Lewis", "Lee", 
    "Walker", "Hall", "Allen", "Young", "Hernandez", "King", "Wright", "Lopez", 
    "Hill", "Scott", "Green", "Adams", "Baker", "Gonzalez", "Nelson", "Carter", 
    "Mitchell", "Perez", "Roberts", "Turner", "Phillips", "Campbell", "Parker", "Evans"
]

STREET_NAMES = [
    "Main", "Church", "High", "Park", "Oak", "Pine", "Maple", "Cedar", "Elm", "Washington", 
    "Lake", "Hill", "Walnut", "Spring", "North", "South", "East", "West", "Center", "River", 
    "Chestnut", "Lincoln", "Jackson", "Cherry", "Highland", "Ridge", "Sunset", "Meadow", 
    "Jefferson", "Franklin", "Adams", "Madison", "Willow", "Dogwood", "Valley", "Fairview"
]

STREET_TYPES = ["St", "Ave", "Blvd", "Rd", "Ln", "Dr", "Way", "Pl", "Ct"]
CITIES = ["Springfield", "Georgetown", "Salem", "Fairview", "Riverside", "Madison", "Clinton", "Greenville", "Bristol", "Kingston"]
STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD"]
ZIP_CODES = [f"{random.randint(10000, 99999)}" for _ in range(50)]
EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "aol.com", "example.com", "test.org"]
PHONE_AREA_CODES = ["201", "202", "212", "213", "214", "215", "301", "302", "303", "304", "305", "310", "312", "313", "314", "315"]

def generate_sample_name():
    """Generate a random first and last name"""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    return first_name, last_name

def generate_sample_email(first_name=None, last_name=None):
    """Generate a random email address"""
    if not first_name or not last_name:
        first_name, last_name = generate_sample_name()
    
    username_parts = [
        f"{first_name.lower()}.{last_name.lower()}",
        f"{first_name.lower()}{last_name.lower()}",
        f"{first_name.lower()[0]}{last_name.lower()}",
        f"{first_name.lower()}{last_name.lower()[0]}",
        f"{last_name.lower()}.{first_name.lower()}",
    ]
    
    username = random.choice(username_parts)
    
    # Sometimes add numbers to username
    if random.random() < 0.3:
        username += str(random.randint(1, 999))
    
    domain = random.choice(EMAIL_DOMAINS)
    return f"{username}@{domain}"

def generate_sample_phone():
    """Generate a random phone number"""
    area_code = random.choice(PHONE_AREA_CODES)
    prefix = random.randint(100, 999)
    line = random.randint(1000, 9999)
    return f"({area_code}) {prefix}-{line}"

def generate_sample_address():
    """Generate a random address"""
    number = random.randint(1, 9999)
    street = random.choice(STREET_NAMES)
    street_type = random.choice(STREET_TYPES)
    city = random.choice(CITIES)
    state = random.choice(STATES)
    zip_code = random.choice(ZIP_CODES)
    
    return f"{number} {street} {street_type}, {city}, {state} {zip_code}"

def generate_sample_date(start_date=None, end_date=None):
    """Generate a random date between start_date and end_date"""
    if not start_date:
        start_date = datetime.now() - timedelta(days=365)
    if not end_date:
        end_date = datetime.now()
    
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)

def generate_sample_text(min_words=5, max_words=50):
    """Generate random text with a specified number of words"""
    words = ["lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit", 
             "sed", "do", "eiusmod", "tempor", "incididunt", "ut", "labore", "et", "dolore", 
             "magna", "aliqua", "ut", "enim", "ad", "minim", "veniam", "quis", "nostrud", 
             "exercitation", "ullamco", "laboris", "nisi", "ut", "aliquip", "ex", "ea", "commodo", 
             "consequat", "duis", "aute", "irure", "dolor", "in", "reprehenderit", "in", "voluptate", 
             "velit", "esse", "cillum", "dolore", "eu", "fugiat", "nulla", "pariatur", "excepteur", 
             "sint", "occaecat", "cupidatat", "non", "proident", "sunt", "in", "culpa", "qui", 
             "officia", "deserunt", "mollit", "anim", "id", "est", "laborum"]
    
    num_words = random.randint(min_words, max_words)
    return " ".join(random.choice(words) for _ in range(num_words))

def generate_sample_url(domain=None):
    """Generate a random URL"""
    if not domain:
        tlds = [".com", ".org", ".net", ".edu", ".gov"]
        domain = f"example{random.choice(tlds)}"
    
    paths = ["about", "contact", "services", "products", "blog", "news", "events", "faq", "support"]
    
    # Decide on URL complexity
    complexity = random.randint(0, 3)
    
    if complexity == 0:
        return f"https://www.{domain}"
    elif complexity == 1:
        return f"https://www.{domain}/{random.choice(paths)}"
    else:
        path1 = random.choice(paths)
        path2 = random.choice(paths)
        return f"https://www.{domain}/{path1}/{path2}" 