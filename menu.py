import os
import re
import subprocess

def display_menu():
    print("Choose an option:")
    print("1. Generate query ID of games")
    print("2. Create session")
    print("0. Exit")

def generate_query_id():
    # Run another Python script using subprocess
    try:
        subprocess.run(["python3", "generate_query_id.py"], check=True)
    except FileNotFoundError:
        print("Error: The file 'generate_query_id.py' was not found.")
    except KeyboardInterrupt:
        print("Process interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")

def create_session():
    # Run another Python script using subprocess
    print("Creating session...")
    try:
        subprocess.run(["python3", "generate_session_strg.py"], check=True)
    except FileNotFoundError:
        print("Error: The file 'generate_session_strg.py' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    while True:
        display_menu()
        try:
            choice = input("Enter your choice: ").strip()
            
            if choice == "1":
                # Check if the sessions folder exists
                if not os.path.exists('sessions'):
                    print("Error: 'sessions' folder not found. Please create it before proceeding.")
                    continue  # Go back to the menu
                generate_query_id()
            elif choice == "2":
                create_session()
            elif choice == "0":
                print("Exiting...")
                break
            else:
                print("Invalid choice, please select again.")
        except EOFError:
            print()
            print("No input received. Exiting the program.")
            break  # Exit the loop if no input is received
        except KeyboardInterrupt:
            print()
            print("Process interrupted by user.")
            break

if __name__ == "__main__":
    main()
