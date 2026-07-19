#CSE 350 | Team 13

Team members: Imran Mukthar, Toby Pepper, Artemis Olague, Adriana Patino

---

**Embark**
--
Embark is a Flask-based web application designed for dog owners, breeders, and enthusiasts to manage dog profiles and pedigree information. Users can create accounts, track bloodlines, save favorite dogs, and organize lineage records in an easy-to-use interface.

--------------------

**Features:**


**User Features:**

-Create an account

-Log in/out securely

-Reset password

-Update settings

--

**Dog Management:**

-Add dogs

-Edit dogs

-Delete dogs

-Upload dog photos

-Store breed, birthday, sex

--

**Pedigree:**


-Link mother and father

-Store lineage notes

-View ancestry

--

**Saved Dogs:**

-Favorite dogs

-Quick access list

-----------------

Run Requirements:
- Python 3.8 or higher
- Flask Installation (pip install flask)
- A supported IDE (VS Code, IntelliJ/PyCharm, etc.)
- A  web browser (Chrome, Firefox, Edge) or a built in one with an IDE.
- SQLite (bundled with Python already)

-----------------  

**Instructions of Use**


1. Clone the repository
   
   **OR**

   Download zip file, extract it, and open the extracted folder in an IDE

--

Steps 2-5 are completed in the IDE terminal.

--

2. Create a virtual environment with the command:
   
  ***python -m venv .venv** _or_ **py -m venv .venv***

--

3. Activate the virtual environment with the command:
   
   Windows: ***.venv\Scripts\Activate.ps1***
   
   Mac/Linux: ***source .venv/bin/activate***

--

4. Install Flask with the command:
   
   ***pip install flask***

--

5. Run the app witht the command:
   
   ***python app.py*** _or_ ***py app.py***

--

6. Open a browser (built-in or external), paste in and go to the following address:
    
   **http://127.0.0.1:5000**

--

7. To stop the server, go back to the terminal and press Ctrl+C (Cmd+C for Mac)

-----------------

## Project Structure (Created with Claude AI)

```
cse-project-team13/
├── app.py
├── style.css
├── script.js
├── logo.png
├── README.md
├── .gitignore
├── static/
│   └── uploads/
└── templates/
    ├── login.html
    ├── create-account.html
    ├── homepage.html
    ├── saved-dogs.html
    ├── pedigrees.html
    ├── profile.html
    ├── notifications.html
    ├── settings.html
    ├── confirmation.html
    └── verified.html
```

