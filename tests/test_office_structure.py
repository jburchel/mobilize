import pytest
from flask import session
from flask_login import login_user
from app.models.user import User
from app.models.office import Office
from app.models.contact import Contact
from app.models.church import Church
from app.auth.permissions import OfficeDataFilter
from app.extensions import db

@pytest.fixture
def office1(app):
    with app.app_context():
        office = Office(
            name='Test Office 1',
            email='office1@test.com'
        )
        db.session.add(office)
        db.session.commit()
        db.session.refresh(office)
        return office

@pytest.fixture
def office2(app):
    with app.app_context():
        office = Office(
            name='Test Office 2',
            email='office2@test.com'
        )
        db.session.add(office)
        db.session.commit()
        db.session.refresh(office)
        return office

@pytest.fixture
def super_admin(app, office1):
    with app.app_context():
        user = User(
            username='superadmin',
            email='super@test.com',
            role='super_admin',
            office_id=office1.id
        )
        user.password = 'testpass'
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user

@pytest.fixture
def office_admin(app, office1):
    with app.app_context():
        user = User(
            username='officeadmin',
            email='admin@test.com',
            role='office_admin',
            office_id=office1.id
        )
        user.password = 'testpass'
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user

@pytest.fixture
def regular_user(app, office1):
    with app.app_context():
        user = User(
            username='user',
            email='user@test.com',
            role='user',
            office_id=office1.id
        )
        user.password = 'testpass'
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user

def test_office_isolation(app, client, office1, office2, super_admin, office_admin):
    """Test that offices are properly isolated."""
    with app.app_context():
        # Refresh objects in current session
        db.session.add(office1)
        db.session.add(office2)
        db.session.add(super_admin)
        db.session.add(office_admin)
        db.session.refresh(office1)
        db.session.refresh(office2)
        db.session.refresh(super_admin)
        db.session.refresh(office_admin)
        
        # Create test data in both offices
        contact1 = Contact(
            first_name='John',
            last_name='Doe',
            email='john@test.com',
            office_id=office1.id
        )
        # Office 2 contact
        contact2 = Contact(
            first_name='Jane',
            last_name='Smith',
            email='jane@test.com',
            office_id=office2.id
        )
        db.session.add_all([contact1, contact2])
        db.session.commit()
        
        # Test super admin access
        login_user(super_admin)  # Set super admin as current user
        filtered_query = OfficeDataFilter.filter_query(Contact.query, Contact)
        assert filtered_query.count() == 2  # Super admin sees all contacts
        
        # Test office admin access
        login_user(office_admin)  # Set office admin as current user
        filtered_query = OfficeDataFilter.filter_query(
            Contact.query.filter_by(office_id=office1.id),
            Contact
        )
        assert filtered_query.count() == 1  # Office admin sees only their office's contacts

def test_user_office_association(app, client, office1, regular_user):
    """Test user-office associations."""
    with app.app_context():
        # Refresh objects in current session
        db.session.add(office1)
        db.session.add(regular_user)
        db.session.refresh(office1)
        db.session.refresh(regular_user)
        
        # Test user's office association
        assert regular_user.office_id == office1.id
        
        # Test session contains office context after login
        with client:
            response = client.post('/api/auth/login', json={
                'email': regular_user.email,
                'password': 'testpass'
            })
            assert response.status_code == 200
            assert session['office_id'] == office1.id
            assert session['user_role'] == 'user'
            assert not session['office_admin']

def test_role_based_permissions(app, client, office1, super_admin, office_admin, regular_user):
    """Test role-based permissions."""
    with app.app_context():
        # Refresh objects in current session
        db.session.add(office1)
        db.session.add(super_admin)
        db.session.add(office_admin)
        db.session.add(regular_user)
        db.session.refresh(office1)
        db.session.refresh(super_admin)
        db.session.refresh(office_admin)
        db.session.refresh(regular_user)
        
        # Create test data
        contact = Contact(
            first_name='Test',
            last_name='Contact',
            email='test@test.com',
            office_id=office1.id,
            user_id=regular_user.id  # Owned by regular user
        )
        db.session.add(contact)
        db.session.commit()
        
        # Test super admin permissions
        login_user(super_admin)  # Set super admin as current user
        assert OfficeDataFilter.can_modify_record(contact)  # Super admin can modify any record
        
        # Test office admin permissions
        login_user(office_admin)  # Set office admin as current user
        assert office_admin.is_admin()  # Verify admin status
        assert OfficeDataFilter.can_access_record(contact)  # Admin can access office records
        
        # Test regular user permissions
        login_user(regular_user)  # Set regular user as current user
        assert not regular_user.is_admin()  # Verify non-admin status
        assert OfficeDataFilter.can_access_record(contact)  # User can access office records
        assert OfficeDataFilter.can_modify_record(contact)  # User can modify owned records

def test_data_visibility_rules(app, client, office1, office2, regular_user):
    """Test data visibility rules."""
    with app.app_context():
        # Refresh objects in current session
        db.session.add(office1)
        db.session.add(office2)
        db.session.add(regular_user)
        db.session.refresh(office1)
        db.session.refresh(office2)
        db.session.refresh(regular_user)
        
        # Create test data in both offices
        church1 = Church(
            name='Church 1',
            first_name='Church',
            last_name='One',
            email='church1@test.com',
            office_id=office1.id,
            owner_id=regular_user.id
        )
        church2 = Church(
            name='Church 2',
            first_name='Church',
            last_name='Two',
            email='church2@test.com',
            office_id=office2.id,
            owner_id=regular_user.id
        )
        db.session.add_all([church1, church2])
        db.session.commit()
        
        # Set regular user as current user
        login_user(regular_user)
        
        # Test visibility rules
        filtered_query = OfficeDataFilter.filter_query(Church.query, Church)
        visible_churches = filtered_query.all()
        
        # Regular user should only see churches in their office
        assert len(visible_churches) == 1
        assert visible_churches[0].name == 'Church 1' 