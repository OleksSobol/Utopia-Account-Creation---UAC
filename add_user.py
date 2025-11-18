import json
import os
from config import hash_password

USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json')


def add_user(username, password, can_view_config=False):
    # Load existing users
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
    else:
        users = []
    # Hash the password using config.hash_password
    hashed = hash_password(password)
    # Check for duplicate username
    for user in users:
        if user['username'] == username:
            print(f"User '{username}' already exists.")
            return
    # Add new user with permission
    users.append({'username': username, 'password': hashed, 'can_view_config': can_view_config})
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)
    print(f"User '{username}' added successfully.")


def reset_password(username, new_password):
    if not os.path.exists(USERS_FILE):
        print("No users.json file found.")
        return
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    for user in users:
        if user['username'] == username:
            user['password'] = hash_password(new_password)
            with open(USERS_FILE, 'w') as f:
                json.dump(users, f, indent=2)
            print(f"Password for '{username}' has been reset.")
            return
    print(f"User '{username}' not found.")


def delete_user(username):
    if not os.path.exists(USERS_FILE):
        print("No users.json file found.")
        return
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    new_users = [user for user in users if user['username'] != username]
    if len(new_users) == len(users):
        print(f"User '{username}' not found.")
        return
    with open(USERS_FILE, 'w') as f:
        json.dump(new_users, f, indent=2)
    print(f"User '{username}' deleted.")


def show_all_users():
    if not os.path.exists(USERS_FILE):
        print("No users.json file found.")
        return
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    if not users:
        print("No users found.")
        return
    print("\nAll users:")
    for user in users:
        perm = user.get('can_view_config', False)
        print(f"- {user['username']} (can_view_config: {perm})")


if __name__ == "__main__":
    while True:
        print("\nSelect an option:")
        print("1. Add new user")
        print("2. Reset password for existing user")
        print("3. Delete user")
        print("4. Show all users")
        print("Type 'exit' to quit.")
        choice = input("Enter 1, 2, 3, 4, or 'exit': ").strip()
        if choice == "1":
            username = input("Enter new username: ").strip()
            password = input("Enter password: ").strip()
            perm_input = input("Can this user view config page? (y/n): ").strip().lower()
            can_view_config = perm_input == 'y'
            add_user(username, password, can_view_config)
        elif choice == "2":
            username = input("Enter username to reset password: ").strip()
            new_password = input("Enter new password: ").strip()
            reset_password(username, new_password)
        elif choice == "3":
            username = input("Enter username to delete: ").strip()
            delete_user(username)
        elif choice == "4":
            show_all_users()
        elif choice.lower() == "exit":
            print("Exiting.")
            break
        else:
            print("Invalid choice.")
