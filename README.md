# Patient-Registry-system
For this repository, I have created a Tkinter application for a patient registry system


## Project explanation
This project was based on an NPTEL course I had completed a few weeks back called Human Computer Interaction (HCI) in english, I was tasked with creating this project based on that course and chose to make a patient registry application on tkinter, a package to make a simple User interface for any application, it acts and provides a nice GUI for app development, I have also used MongoDB for the database of the application, its NoSQl applications provide a simpler Database access
The system follows a multi-tabbed interface design with separate sections for many different purposes, making it valuable for healthcare staff to navigate aspects of patient management.


## Project functions
Database Management: Connects to MongoDB using PyMongo has three collections called patients, appointments, and audit_logs all stored in a database called hospital, allowing easy CRUD work in the app

User Interface: Implements a GUI with ttk widgets, tabs for organized functionality, providing visible form boxes

Data Processing: Handles data type conversions (dates and numbers) and implements search and filtering capabilities

Data visualization: Created by Matplotlib, a common data visualiztion tool in python, the graphs are visualized via the app

Audit tracking: The changes and updates made to the application are tracked in the audit tab


## How to run
The app.py is where the app has to be run, if you're using VS code, simply use the 'run python file' button on the top right (your right) of the screen, but you will require certain packages to be able to run the application, such as:
tkinter - The standard Python interface to the Tk GUI toolkit (for building the graphical user interface)
ttk (from tkinter) - Themed widgets that provide a more modern look than standard tkinter widgets
pymongo - The official MongoDB driver for Python (for connecting to and interacting with MongoDB)
bson (specifically ObjectId) - For handling MongoDB's unique identifier format
matplotlib - Comprehensive library for creating static, animated, and interactive visualizations
pandas - Powerful data analysis and manipulation library (used for CSV export functionality)
numpy - Fundamental package for scientific computing (used by pandas and matplotlib)
datetime - For handling dates and times throughout the application
json - For JSON serialization (used in the export functionality)
filedialog - For file save dialogs in the export feature
messagebox - For displaying alerts and confirmation dialogs


## Project features
Adding patients: A patient's details such as Name, Age, Insurance provider, Medical history, Gender can be filled and added to the datatable present in the tab

Search patients: If you want to search a patient, you can use this tab and search them based on their age range, date they were added in, their Insurance provider and their Name 

Dashboard: The dashboard holds the graphs of data on various fields, at the top on it's window there are various other graphs tabs and also the number of patients registered overall and for today, the average age of all the patients, total revenue from appointments, the 6 graphs present in the dashboard are:-
- Gender distribution in a pie graph
- Age distribution in a pie graph
- Insurance distribution in a pie graph
- Bar graph of trends in appointments baased on the month
- A line stats graph based on the number of people registering by each month
- A revenue bar graph chart based on the amount of money each consultation generates
These are all the graphs that are representing the data in the dashboard

Appointments tab: As this is for a hospital, i have created a tab for any future appointments for a patient's checck up, this form requests the patient's name, when they'll come by and their reason or yours.
the part that you will fill in is the consultation type and the Reason and the amount to be paid, the appointment is then made to that date and can even be either marked as done or cancelled. All the appointment data is visible on the side just like in the add patients tab

Exporting data: this part of the application allows you to download either the CSSV or Json file of the Patient registry or the appointments data

Audit tracker: Audit logs provide the data that has been added and changed till the present time, allows the user to keep track of any and all changes


# thank you for reading
