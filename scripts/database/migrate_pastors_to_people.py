import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app import create_app
app = create_app()
from app.extensions import db
from app.models import Church, Person

def get_or_create_person(first_name, last_name, email, phone, church_id, office_id, role):
    person = None
    if email:
        person = Person.query.filter_by(email=email).first()
    if not person and first_name and last_name:
        person = Person.query.filter_by(first_name=first_name, last_name=last_name, church_id=church_id).first()
    if not person:
        person = Person(
            first_name=first_name or '',
            last_name=last_name or '',
            email=email,
            phone=phone,
            church_id=church_id,
            church_role=role,
            office_id=office_id
        )
        db.session.add(person)
        db.session.commit()
    else:
        # Update role and church if needed
        updated = False
        if not person.church_id:
            person.church_id = church_id
            updated = True
        if not person.church_role or person.church_role != role:
            person.church_role = role
            updated = True
        if not person.office_id:
            person.office_id = office_id
            updated = True
        if updated:
            db.session.commit()
    return person

def migrate():
    with app.app_context():
        churches = Church.query.all()
        for church in churches:
            # Senior Pastor
            if church.senior_pastor_name or church.senior_pastor_email or church.senior_pastor_phone:
                # Try to split name if possible
                if church.senior_pastor_name:
                    parts = church.senior_pastor_name.split(' ', 1)
                    first = parts[0]
                    last = parts[1] if len(parts) > 1 else ''
                else:
                    first = ''
                    last = ''
                person = get_or_create_person(
                    first_name=first or church.senior_pastor_first_name,
                    last_name=last or church.senior_pastor_last_name,
                    email=church.senior_pastor_email,
                    phone=church.senior_pastor_phone,
                    church_id=church.id,
                    office_id=church.office_id,
                    role='senior_pastor'
                )
                print(f"Linked Senior Pastor {person.first_name} {person.last_name} to church {church.name}")
            # Missions Pastor
            if church.missions_pastor_first_name or church.missions_pastor_last_name or church.mission_pastor_email or church.mission_pastor_phone:
                person = get_or_create_person(
                    first_name=church.missions_pastor_first_name,
                    last_name=church.missions_pastor_last_name,
                    email=church.mission_pastor_email,
                    phone=church.mission_pastor_phone,
                    church_id=church.id,
                    office_id=church.office_id,
                    role='missions_pastor'
                )
                print(f"Linked Missions Pastor {person.first_name} {person.last_name} to church {church.name}")
        db.session.commit()
        print("Migration complete.")

if __name__ == "__main__":
    migrate() 