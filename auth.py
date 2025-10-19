"""
Authentication system for SI3LN Game
Manages user registration, login, and user data
"""
import json
import os
from utils import hash_password, validate_email
from constants import USER_DATA_FILE


class AuthSystem:
    def __init__(self):
        self.users = self.load_users()
        self.current_user = None
        self.guest_mode = False
    
    def load_users(self):
        """Load users from JSON file"""
        if os.path.exists(USER_DATA_FILE):
            try:
                with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading users: {e}")
                return {}
        return {}
    
    def save_users(self):
        """Save users to JSON file"""
        try:
            with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving users: {e}")
    
    def register(self, username, password, email=""):
        """
        Register a new user
        Returns (success, message)
        """
        # Validate username
        if not username or len(username) < 3:
            return False, "Le pseudo doit contenir au moins 3 caractères"
        
        if username in self.users:
            return False, "Ce pseudo est déjà pris"
        
        # Validate password
        if not password or len(password) < 4:
            return False, "Le mot de passe doit contenir au moins 4 caractères"
        
        # Validate email (optional)
        if email and not validate_email(email):
            return False, "Email invalide"
        
        # Create user
        self.users[username] = {
            "password": hash_password(password),
            "email": email,
            "selected_character": 0,
            "high_score": 0,
            "levels_completed": {}
        }
        self.save_users()
        return True, "Compte créé avec succès!"
    
    def login(self, username, password):
        """
        Login a user
        Returns (success, message)
        """
        if username not in self.users:
            return False, "Pseudo incorrect"
        
        if self.users[username]["password"] != hash_password(password):
            return False, "Mot de passe incorrect"
        
        self.current_user = username
        self.guest_mode = False
        return True, f"Bienvenue {username}!"
    
    def login_as_guest(self, selected_character=0):
        """Login in guest mode (no score saving)"""
        self.current_user = None
        self.guest_mode = True
        self.guest_character = selected_character
        return True, "Mode invité activé"
    
    def logout(self):
        """Logout current user"""
        self.current_user = None
        self.guest_mode = False
    
    def update_user_data(self, **kwargs):
        """Update current user data"""
        if not self.current_user or self.guest_mode:
            return False
        
        for key, value in kwargs.items():
            if key in self.users[self.current_user]:
                self.users[self.current_user][key] = value
        
        self.save_users()
        return True
    
    def get_user_data(self, key=None):
        """Get current user data"""
        if self.guest_mode:
            return {
                "selected_character": getattr(self, 'guest_character', 0),
                "high_score": 0
            }
        
        if not self.current_user:
            return None
        
        if key:
            return self.users[self.current_user].get(key)
        return self.users[self.current_user]
    
    def change_password(self, old_password, new_password):
        """Change user password"""
        if not self.current_user or self.guest_mode:
            return False, "Non connecté"
        
        if self.users[self.current_user]["password"] != hash_password(old_password):
            return False, "Ancien mot de passe incorrect"
        
        if len(new_password) < 4:
            return False, "Le nouveau mot de passe doit contenir au moins 4 caractères"
        
        self.users[self.current_user]["password"] = hash_password(new_password)
        self.save_users()
        return True, "Mot de passe changé avec succès"
    
    def change_username(self, new_username):
        """Change username"""
        if not self.current_user or self.guest_mode:
            return False, "Non connecté"
        
        if len(new_username) < 3:
            return False, "Le pseudo doit contenir au moins 3 caractères"
        
        if new_username in self.users and new_username != self.current_user:
            return False, "Ce pseudo est déjà pris"
        
        # Copy user data to new username
        self.users[new_username] = self.users.pop(self.current_user)
        self.current_user = new_username
        self.save_users()
        return True, f"Pseudo changé en {new_username}"
    
    def is_username_available(self, username):
        """Check if username is available"""
        return username not in self.users
