"""Pytest configuration and fixtures."""

import pytest
from app import create_app
from app.extensions import db
from app.config import TestingConfig
from app.auth.models import User, UserRole
from app.companies.models import Company


@pytest.fixture
def app():
    """Create Flask application for testing."""
    app = create_app(TestingConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user."""
    response = client.post('/api/auth/login', json={
        'email': test_user.email,
        'password': 'TestPassword123!'
    })
    data = response.get_json()
    token = data.get('tokens', {}).get('access_token')
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def test_user(app):
    """Create test user."""
    with app.app_context():
        user = User(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            role=UserRole.CEO
        )
        user.set_password('TestPassword123!')
        user.is_verified = True
        user.is_active = True
        
        db.session.add(user)
        db.session.commit()
        
        return user


@pytest.fixture
def test_company(app, test_user):
    """Create test company."""
    with app.app_context():
        company = Company(
            user_id=test_user.id,
            name='Test Company',
            website_url='https://testcompany.com',
            industry='Technology',
            description='A test company'
        )
        
        db.session.add(company)
        db.session.commit()
        
        return company
