"""
Constants for choice fields used in models.
Migrated from the old models.py file.
"""

# Church-related choices
CHURCH_PIPELINE_CHOICES = [
    ('PROMOTION', 'PROMOTION'), ('INFORMATION', 'INFORMATION'), ('INVITATION', 'INVITATION'),
    ('CONFIRMATION', 'CONFIRMATION'), ('EN42', 'EN42'), ('AUTOMATION', 'AUTOMATION')
]

PRIORITY_CHOICES = [
    ('URGENT', 'URGENT'), ('HIGH', 'HIGH'), ('MEDIUM', 'MEDIUM'), ('LOW', 'LOW')
]

ASSIGNED_TO_CHOICES = [
    ('BILL JONES', 'BILL JONES'), ('JASON MODOMO', 'JASON MODOMO'), ('KEN KATAYAMA', 'KEN KATAYAMA'),
    ('MATTHEW RULE', 'MATTHEW RULE'), ('CHIP ATKINSON', 'CHIP ATKINSON'), ('RACHEL LIVELY', 'RACHEL LIVELY'),
    ('JIM BURCHEL', 'JIM BURCHEL'), ('JILL WALKER', 'JILL WALKER'), ('KARINA RAMPIN', 'KARINA RAMPIN'),
    ('UNASSIGNED', 'UNASSIGNED')
]

SOURCE_CHOICES = [
    ('WEBFORM', 'WEBFORM'), ('INCOMING CALL', 'INCOMING CALL'), ('EMAIL', 'EMAIL'),
    ('SOCIAL MEDIA', 'SOCIAL MEDIA'), ('COLD CALL', 'COLD CALL'), ('PERSPECTIVES', 'PERSPECTIVES'),
    ('REFERAL', 'REFERAL'), ('OTHER', 'OTHER'), ('UNKNOWN', 'UNKNOWN')
]

# Person-related choices
MARITAL_STATUS_CHOICES = [
    ('single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced'),
    ('widowed', 'Widowed'), ('separated', 'Separated'), ('unknown', 'Unknown'),
    ('engaged', 'Engaged')
]

PEOPLE_PIPELINE_CHOICES = [
    ('PROMOTION', 'PROMOTION'), ('INFORMATION', 'INFORMATION'), ('INVITATION', 'INVITATION'),
    ('CONFIRMATION', 'CONFIRMATION'), ('AUTOMATION', 'AUTOMATION')
]

# Common Church Role choices for individuals within a church
CHURCH_ROLE_CHOICES = [
    ('senior_pastor', 'Senior Pastor'),
    ('associate_pastor', 'Associate Pastor'),
    ('missions_pastor', 'Missions Pastor'),
    ('elder', 'Elder'),
    ('deacon', 'Deacon'),
    ('member', 'Member'),
    ('attendee', 'Attendee'),
    ('volunteer', 'Volunteer'),
    ('staff', 'Staff'),
    ('guest', 'Guest'),
    ('other', 'Other')
]

# Task-related choices
TASK_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('in_progress', 'In Progress'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
    ('on_hold', 'On Hold')
]

TASK_PRIORITY_CHOICES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
    ('urgent', 'Urgent')
]

REMINDER_CHOICES = [
    ('15_min', '15 minutes before'),
    ('30_min', '30 minutes before'),
    ('1_hour', '1 hour before'),
    ('2_hours', '2 hours before'),
    ('1_day', '1 day before'),
    ('3_days', '3 days before'),
    ('1_week', '1 week before'),
    ('none', 'No reminder')
]

# Common choices
STATE_CHOICES = [
    ('al', 'AL'), ('ak', 'AK'), ('az', 'AZ'), ('ar', 'AR'), ('ca', 'CA'),('co', 'CO'),('ct', 'CT'),('de', 'DE'), 
    ('fl', 'FL'), ('ga', 'GA'), ('hi', 'HI'), ('id', 'ID'), ('il', 'IL'), ('in', 'IN'), ('ia', 'IA'), ('ks', 'KS'), 
    ('ky', 'KY'), ('la', 'LA'), ('me', 'ME'), ('md', 'MD'), ('ma', 'MA'), ('mi', 'MI'), ('mn', 'MN'), ('ms', 'MS'), 
    ('mo', 'MO'), ('mt', 'MT'), ('ne', 'NE'), ('nv', 'NV'), ('nh', 'NH'), ('nj', 'NJ'), ('nm', 'NM'), ('ny', 'NY'), 
    ('nc', 'NC'), ('nd', 'ND'), ('oh', 'OH'), ('ok', 'OK'), ('or', 'OR'), ('pa', 'PA'), ('ri', 'RI'), ('sc', 'SC'), 
    ('sd', 'SD'), ('tn', 'TN'), ('tx', 'TX'), ('ut', 'UT'), ('vt', 'VT'), ('va', 'VA'), ('wa', 'WA'), ('wv', 'WV'), 
    ('wi', 'WI'), ('wy', 'WY'), ('dc', 'DC')
]

# Communication type choices
COMMUNICATION_TYPE_CHOICES = [
    ('email', 'Email'),
    ('phone', 'Phone Call'),
    ('sms', 'Text Message'),
    ('meeting', 'Meeting'),
    ('letter', 'Letter'),
    ('video_conference', 'Video Conference'),
    ('in_person', 'In Person'),
    ('other', 'Other')
]

PREFERRED_CONTACT_METHODS = [
    ('email', 'Email'), ('phone', 'Phone'), ('text', 'Text'), ('facebook_messenger', 'Facebook Messenger'),
    ('whatsapp', 'Whatsapp'), ('groupme', 'Groupme'), ('signal', 'Signal'), ('other', 'Other')
]

# User system roles (different from church roles)
ROLE_CHOICES = [
    ('super_admin', 'Super Admin'),
    ('office_admin', 'Office Admin'),
    ('standard_user', 'Standard User'),
    ('limited_user', 'Limited User')
] 