import sqlite3
import json
import os
from venv import logger
from core.encryption.encryption import (
    load_key,
    decrypt_data,
    encrypt_data,
    get_key_path,
)
from core.config.user_config import DB_PATH

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
KEY_PATH = get_key_path()


def load_database():
    if not os.path.exists(DB_PATH):
        print(f"Database file does not exist at {DB_PATH}")
        return None
    return sqlite3.connect(DB_PATH)


def view_all_users(conn, key):
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    rows = c.fetchall()
    print(f"Total records: {len(rows)}")
    for row in rows:
        user_id, encrypted_data = row
        try:
            decrypted_data = decrypt_data(encrypted_data, key)
            user_config = json.loads(decrypted_data)
            print(f"User ID: {user_id}")
            print(
                f"Discord Username: {user_config.get('discord_username', 'Not available')}"
            )
            print(f"Config: {user_config}")
            print("---")
        except Exception as e:
            print(f"Error decrypting data for user {user_id}: {e}")


def find_user_by_discord_username(conn, key, discord_username):
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    rows = c.fetchall()
    for row in rows:
        user_id, encrypted_data = row
        try:
            decrypted_data = decrypt_data(encrypted_data, key)
            user_config = json.loads(decrypted_data)
            if user_config.get("discord_username") == discord_username:
                return user_id, user_config
        except Exception as e:
            print(f"Error decrypting data for user {user_id}: {e}")
    return None, None


def clear_twitter_credentials(conn, key, user_id):
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row:
        _, encrypted_data = row
        decrypted_data = decrypt_data(encrypted_data, key)
        user_config = json.loads(decrypted_data)
        user_config["twitter_access_key"] = ""
        user_config["twitter_access_secret"] = ""
        updated_encrypted_data = encrypt_data(json.dumps(user_config), key)
        c.execute(
            "UPDATE users SET encrypted_data = ? WHERE user_id = ?",
            (updated_encrypted_data, user_id),
        )
        conn.commit()
        print(f"Twitter credentials cleared for user {user_id}")
    else:
        print(f"User {user_id} not found in the database")


def update_twitter_credentials(conn, key, user_id, access_key, access_secret):
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row:
        _, encrypted_data = row
        decrypted_data = decrypt_data(encrypted_data, key)
        user_config = json.loads(decrypted_data)
        user_config["twitter_access_key"] = access_key
        user_config["twitter_access_secret"] = access_secret
        updated_encrypted_data = encrypt_data(json.dumps(user_config), key)
        c.execute(
            "UPDATE users SET encrypted_data = ? WHERE user_id = ?",
            (updated_encrypted_data, user_id),
        )
        conn.commit()
        print(f"Twitter credentials updated for user {user_id}")
    else:
        print(f"User {user_id} not found in the database")


def delete_user(conn, user_id):
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    if c.rowcount > 0:
        conn.commit()
        print(f"User {user_id} deleted from the database")
    else:
        print(f"User {user_id} not found in the database")


def main_menu():
    print("\nDatabase Management Menu:")
    print("1. View all users")
    print("2. Clear Twitter credentials for a user")
    print("3. Update Twitter credentials for a user")
    print("4. Delete a user")
    print("5. Exit")
    return input("Enter your choice (1-5): ")


def check_and_update_schema(conn):
    try:
        c = conn.cursor()

        # Check if the 'stack_auth_id' column exists
        c.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in c.fetchall()]

        if "stack_auth_id" not in columns:
            logger.info("Adding 'stack_auth_id' column to users table")
            c.execute("ALTER TABLE users ADD COLUMN stack_auth_id TEXT")
            conn.commit()
            logger.info("Schema update completed successfully")
    except sqlite3.Error as e:
        logger.error(f"Error updating database schema: {e}")
        raise


def main():
    key = load_key(KEY_PATH)
    print(f"Checking for database at: {os.path.abspath(DB_PATH)}")
    conn = load_database()
    if not conn:
        return

    try:
        key = load_key(KEY_PATH)
        check_and_update_schema(conn)  # Add this line
    except Exception as e:
        print(f"Error loading key or updating schema: {e}")
        return

    while True:
        choice = main_menu()
        if choice == "1":
            view_all_users(conn, key)
        elif choice == "2":
            discord_username = input("Enter Discord username (e.g., username#1234): ")
            user_id, _ = find_user_by_discord_username(conn, key, discord_username)
            if user_id:
                clear_twitter_credentials(conn, key, user_id)
            else:
                print(f"No user found with Discord username: {discord_username}")
        elif choice == "3":
            discord_username = input("Enter Discord username (e.g., username#1234): ")
            user_id, _ = find_user_by_discord_username(conn, key, discord_username)
            if user_id:
                access_key = input("Enter new Twitter access key: ")
                access_secret = input("Enter new Twitter access secret: ")
                update_twitter_credentials(
                    conn, key, user_id, access_key, access_secret
                )
            else:
                print(f"No user found with Discord username: {discord_username}")
        elif choice == "4":
            discord_username = input(
                "Enter Discord username to delete (e.g., username#1234): "
            )
            user_id, _ = find_user_by_discord_username(conn, key, discord_username)
            if user_id:
                delete_user(conn, user_id)
            else:
                print(f"No user found with Discord username: {discord_username}")
        elif choice == "5":
            break
        else:
            print("Invalid choice. Please try again.")

    conn.close()
    print("Database connection closed.")


if __name__ == "__main__":
    main()
