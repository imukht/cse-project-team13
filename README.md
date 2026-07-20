CSE 350 | Team 13

**Embark**
--
Embark is a Flask-based web application designed for dog owners, breeders, and enthusiasts to manage dog profiles and pedigree information. Users can create accounts, track bloodlines, save favorite dogs, and organize lineage records in an easy-to-use interface.

--

Team: Imran Mukthar, Toby Pepper, Artemis Olague, Adriana Patino


--------------------

**Features:**

-Create an account

-Log in/out securely

-Update settings and user preferences

--

**Dog Management:**

-Add dog profiles

-Edit dog details

-Delete dog profiles

-Upload dog photos

-Store breed, birthday, sex, traits, and registration number

--

**Pedigree:**


-Link mother and father

-Store lineage notes

-View ancestry and family (3 generations)

--

**Saved Dogs:**

-Add dogs to favorites

-Quick access list

-----------------

Run Requirements:
- Python 3.8 or higher
- Flask Installation (pip install flask)
- A supported IDE (VS Code, IntelliJ/PyCharm, etc.)
- A  web browser (Chrome, Firefox, Edge) or a built in one with an IDE.
- SQLite (bundled with Python already)

-----------------  

-**A demo account is created automatically on first run:**
   - Email: **demo@example.com**
   - Password: **DemoPass!**

   You can use this to explore the app immediately, or register your own account.

-----

**Instructions of Use**
---

1. **Make sure Python 3.8+ is installed:**
- Check with: ***python --version*** or ***py --version***
- If not installed, download it from https://www.python.org/downloads/
- **Windows users:** during installation, check the box "Add python.exe to PATH" — skipping this causes `python`/`pip` commands to fail later, even after installing correctly.

--

2. Clone the repository
   
   **OR**

   Download zip file, extract it, and open the extracted folder in an IDE

--

Steps 3-6 are completed in the IDE terminal.

--

3. Create a virtual environment with the command:
   
   ***`python -m venv .venv`** _or_ **`py -m venv .venv`***

--

4. Activate the virtual environment with the command:
   
   Windows: ***`.venv\Scripts\Activate.ps1`***
   
   Mac/Linux: ***`source .venv/bin/activate`***

--

5. Install Flask with the command:
   
   ***`pip install flask`***

--

6. Run the app witht the command:
   
   ***`python app.py`*** _or_ ***`py app.py`***

--

7. Open a browser (built-in or external), paste in and go to the following address:
    
   **http://127.0.0.1:5000**

--

8. To stop the server, go back to the terminal and press Ctrl+C (Cmd+C for Mac)

-----------------
## Project Structure (Created with Claude AI)

    cse-project-team13/
    ├── app.py
    ├── style.css
    ├── script.js
    ├── logo.png
    ├── README.md
    ├── .gitignore
    ├── static/
    │   └── uploads/
    ├── templates/
    │   ├── login.html
    │   ├── create-account.html
    │   ├── homepage.html
    │   ├── saved-dogs.html
    │   ├── pedigrees.html
    │   ├── profile.html
    │   ├── notifications.html
    │   ├── settings.html
    │   ├── confirmation.html
    │   ├── verified.html
    │   └── partials/
    └── tests/
        ├── test_auth_flow.py
        ├── test_pedigree_flow.py
        ├── test_saved_dogs_flow.py
        ├── test_dog_management_flow.py
        └── test_account_flow.py



**Tech Stack**

- **Backend:** Python, Flask
- **Database:** SQLite
- **Frontend:** HTML, CSS, vanilla JavaScript (Jinja2 templating for server-rendered pages)
- **Auth:** Password hashing, session-based login
- **Testing:** Python's built-in `unittest` framework


**Unit Test files:**
- `test_auth_flow.py` — register, login, email verification, logout
- `test_pedigree_flow.py` — linking parents, pedigree validation, ancestry tree
- `test_saved_dogs_flow.py` — saved dogs list, save/unsave toggle
- `test_dog_management_flow.py` — add, edit, and delete dog profiles
- `test_account_flow.py` — changing account email/password

