# create_admin.py
from app import app
from models import db, User
from werkzeug.security import generate_password_hash

def generate_secure_admin():
    with app.app_context():
        # 1. Define your master admin email address
        admin_email = "ramu@gmail.com"
        
        # 2. CREATE the new password hash FIRST so Python can use it below
        # Change "123456" to whatever new password string you want!
        hashed_password = generate_password_hash("123456", method='scrypt')
        
        # 3. Check if this account already exists in the database
        existing_admin = User.query.filter_by(email=admin_email).first()
        
        if existing_admin:
            # If the user exists, update their password hash and commit
            existing_admin.password_hash = hashed_password
            db.session.commit()
            print("--------------------------------------------------")
            print(f" SUCCESS: Password updated successfully for '{admin_email}'!")
            print("--------------------------------------------------")
            return
        
        # 4. If the user doesn't exist at all, create them from scratch
        master_admin = User(
            name="Master Administrator",
            email=admin_email,
            password_hash=hashed_password,
            role="admin" # Grants admin privileges
        )
        
        db.session.add(master_admin)
        db.session.commit()
        print("--------------------------------------------------")
        print("MASTER ADMIN ACCOUNT CREATED SUCCESSFULLY FROM SCRATCH!")
        print(f"Email: {admin_email}")
        print("Role: admin")
        print("--------------------------------------------------")

if __name__ == "__main__":
    generate_secure_admin()