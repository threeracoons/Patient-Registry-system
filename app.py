import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pymongo import MongoClient
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
from bson import ObjectId
import json

# MONGOSH connection
client = MongoClient("mongodb://localhost:27017/")

db = client["hospital"]
patients_col = db["patients"]
appointments_col = db["appointments"]
audit_logs_col = db["audit_logs"]

class PatientRegistryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hospital Patient Registry")
        # window size
        self.root.geometry("1400x1000")
        
        # widget size
        self.style = ttk.Style()
        self.style.configure('TNotebook.Tab', font=('Arial', 12), padding=[10, 5])
        self.style.configure('TButton', font=('Arial', 12), padding=6) 
        self.style.configure('TEntry', font=('Arial', 12), padding=5)
        self.style.configure('TLabel', font=('Arial', 12))
        self.style.configure('Treeview', font=('Arial', 12), rowheight=30)  
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.create_patient_tab()
        self.create_search_tab()
        self.create_dashboard_tab()
        self.create_appointments_tab()
        self.create_export_tab()
        self.create_audit_logs_tab()

        self.update_dashboard()

    # patient management tabs
    def create_patient_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Patient Management")

        # I'll move the patient form left align
        form_frame = ttk.Frame(tab)
        form_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        tk.Label(form_frame, text="Name:", font=('Arial', 12)).grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.name_entry = tk.Entry(form_frame, font=('Arial', 12), width=30)
        self.name_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(form_frame, text="Age:", font=('Arial', 12)).grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.age_entry = tk.Entry(form_frame, font=('Arial', 12), width=30)
        self.age_entry.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(form_frame, text="Gender:", font=('Arial', 12)).grid(row=2, column=0, padx=10, pady=10, sticky='w')
        self.gender_entry = ttk.Combobox(form_frame, values=["Male", "Female", "Other"], font=('Arial', 12), width=28)
        self.gender_entry.grid(row=2, column=1, padx=10, pady=10)
        self.gender_entry.set("Other")

        tk.Label(form_frame, text="Insurance Provider:", font=('Arial', 12)).grid(row=3, column=0, padx=10, pady=10, sticky='w')
        self.insurance_entry = ttk.Combobox(form_frame, values=["Private", "Medicare", "Medicaid", "None"], font=('Arial', 12), width=28)
        self.insurance_entry.grid(row=3, column=1, padx=10, pady=10)
        self.insurance_entry.set("None")

        tk.Label(form_frame, text="Medical History:", font=('Arial', 12)).grid(row=4, column=0, padx=10, pady=10, sticky='nw')
        self.medical_history_entry = tk.Text(form_frame, height=6, width=30, font=('Arial', 12))
        self.medical_history_entry.grid(row=4, column=1, padx=10, pady=10)

        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=15)

        tk.Button(button_frame, text="Add Patient", command=self.add_patient, font=('Arial', 12), height=1, width=15).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Update Patient", command=self.update_patient, font=('Arial', 12), height=1, width=15).grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="Delete Patient", command=self.delete_patient, font=('Arial', 12), height=1, width=15).grid(row=0, column=2, padx=5)

        # Right side - Patient list
        list_frame = ttk.Frame(tab)
        list_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.patient_tree = ttk.Treeview(list_frame, columns=("id", "name", "age", "gender", "insurance"), show="headings", height=15)
        self.patient_tree.heading("id", text="ID")
        self.patient_tree.heading("name", text="Name")
        self.patient_tree.heading("age", text="Age")
        self.patient_tree.heading("gender", text="Gender")
        self.patient_tree.heading("insurance", text="Insurance")
        self.patient_tree.column("id", width=0, stretch=tk.NO)
        self.patient_tree.column("name", width=200)
        self.patient_tree.column("age", width=80)
        self.patient_tree.column("gender", width=100)
        self.patient_tree.column("insurance", width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.patient_tree.yview)
        scrollbar.pack(side="right", fill="y")

        self.patient_tree.configure(yscrollcommand=scrollbar.set)

        self.patient_tree.pack(fill=tk.BOTH, expand=True)
        
        self.patient_tree.bind("<ButtonRelease-1>", self.load_selected_patient)
        self.refresh_patient_list()

    def add_patient(self):
        try:
            patient_data = {
                "name": self.name_entry.get(),
                "age": int(self.age_entry.get()) if self.age_entry.get().isdigit() else 0,
                "gender": self.gender_entry.get(),
                "insurance": self.insurance_entry.get(),
                "medical_history": self.medical_history_entry.get("1.0", tk.END).strip(),
                "registration_date": datetime.now()
            }

            # error handling name part
            if not patient_data["name"]:
                raise ValueError("Name cannot be empty")
            
            result = patients_col.insert_one(patient_data)
            self.log_audit(f"Added patient: {patient_data['name']} (ID: {result.inserted_id})")
            self.refresh_patient_list()
            self.clear_form()
            messagebox.showinfo("Success", "Patient added successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add patient: {str(e)}")

    def update_patient(self):
        try:
            selected = self.patient_tree.selection()
            if not selected:
                raise ValueError("No patient selected")
            
            patient_id = self.patient_tree.item(selected)["values"][0]
            updates = {
                "name": self.name_entry.get(),
                "age": int(self.age_entry.get()) if self.age_entry.get().isdigit() else 0,
                "gender": self.gender_entry.get(),
                "insurance": self.insurance_entry.get(),
                "medical_history": self.medical_history_entry.get("1.0", tk.END).strip()
            }
            
            patients_col.update_one({"_id": ObjectId(patient_id)}, {"$set": updates})
            self.log_audit(f"Updated patient ID: {patient_id}")
            self.refresh_patient_list()
            messagebox.showinfo("Success", "Patient updated!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update patient: {str(e)}")

    def delete_patient(self):
        try:
            selected = self.patient_tree.selection()
            if not selected:
                raise ValueError("No patient selected")
            
            patient_id = self.patient_tree.item(selected)["values"][0]
            patients_col.delete_one({"_id": ObjectId(patient_id)})
            self.log_audit(f"Deleted patient ID: {patient_id}")
            self.refresh_patient_list()
            self.clear_form()
            messagebox.showinfo("Success", "Patient deleted!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete patient: {str(e)}")

    def refresh_patient_list(self):
        self.patient_tree.delete(*self.patient_tree.get_children())
        for patient in patients_col.find():
            self.patient_tree.insert("", tk.END, values=(
                str(patient["_id"]),
                patient.get("name", "N/A"),
                patient.get("age", "N/A"),
                patient.get("gender", "N/A"),
                patient.get("insurance", "N/A")
            ))

    def load_selected_patient(self, event):
        try:
            selected = self.patient_tree.selection()
            if not selected:
                return
            
            patient_id = self.patient_tree.item(selected)["values"][0]
            patient = patients_col.find_one({"_id": ObjectId(patient_id)})
            
            if not patient:
                raise ValueError("Patient not found in database")
            
            self.clear_form()
            self.name_entry.insert(0, patient.get("name", ""))
            self.age_entry.insert(0, str(patient.get("age", "")))
            self.gender_entry.set(patient.get("gender", "Other"))
            self.insurance_entry.set(patient.get("insurance", "None"))
            self.medical_history_entry.insert("1.0", patient.get("medical_history", ""))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load patient: {str(e)}")

    def clear_form(self):
        self.name_entry.delete(0, tk.END)
        self.age_entry.delete(0, tk.END)
        self.gender_entry.set("Other")
        self.insurance_entry.set("None")
        self.medical_history_entry.delete("1.0", tk.END)

    # Search bar
    def create_search_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Search Patients")

        search_frame = ttk.Frame(tab)
        search_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(search_frame, text="Search by Name:", font=('Arial', 12)).grid(row=0, column=0, padx=10, pady=10)
        self.search_name_entry = tk.Entry(search_frame, font=('Arial', 12), width=30)
        self.search_name_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Button(search_frame, text="Search", command=self.search_by_name, font=('Arial', 12), width=10).grid(row=0, column=2, padx=10, pady=10)

        tk.Label(search_frame, text="Age Range:", font=('Arial', 12)).grid(row=1, column=0, padx=10, pady=10)
        self.min_age_entry = tk.Entry(search_frame, font=('Arial', 12), width=10)
        self.min_age_entry.grid(row=1, column=1, padx=10, pady=10)
        tk.Label(search_frame, text="to", font=('Arial', 12)).grid(row=1, column=2, padx=10, pady=10)
        self.max_age_entry = tk.Entry(search_frame, font=('Arial', 12), width=10)
        self.max_age_entry.grid(row=1, column=3, padx=10, pady=10)

        tk.Button(search_frame, text="Filter Age", command=self.filter_by_age, font=('Arial', 12), width=10).grid(row=1, column=4, padx=10, pady=10)

        tk.Label(search_frame, text="From (YYYY-MM-DD):", font=('Arial', 12)).grid(row=2, column=0, padx=10, pady=10)

        self.from_date_entry = tk.Entry(search_frame, font=('Arial', 12), width=15)

        self.from_date_entry.grid(row=2, column=1, padx=10, pady=10)
        tk.Label(search_frame, text="To (YYYY-MM-DD):", font=('Arial', 12)).grid(row=2, column=2, padx=10, pady=10)
        self.to_date_entry = tk.Entry(search_frame, font=('Arial', 12), width=15)

        self.to_date_entry.grid(row=2, column=3, padx=10, pady=10)
        tk.Button(search_frame, text="Filter Date", command=self.filter_by_date, font=('Arial', 12), width=10).grid(row=2, column=4, padx=10, pady=10)

        tk.Label(search_frame, text="Insurance:", font=('Arial', 12)).grid(row=3, column=0, padx=10, pady=10)
        self.search_insurance_entry = ttk.Combobox(search_frame, values=["All", "Private", "Medicare", "Medicaid", "None"], font=('Arial', 12), width=10)
        self.search_insurance_entry.grid(row=3, column=1, padx=10, pady=10)
        self.search_insurance_entry.set("All")

        tk.Button(search_frame, text="Filter Insurance", command=self.filter_by_insurance, font=('Arial', 12), width=15).grid(row=3, column=2, columnspan=2, padx=10, pady=10)

        self.search_tree = ttk.Treeview(tab, columns=("id", "name", "age", "gender", "insurance", "reg_date"), show="headings", height=15)
        self.search_tree.heading("id", text="ID")
        self.search_tree.heading("name", text="Name")
        self.search_tree.heading("age", text="Age")
        self.search_tree.heading("gender", text="Gender")
        self.search_tree.heading("insurance", text="Insurance")
        self.search_tree.heading("reg_date", text="Registration Date")
        self.search_tree.column("id", width=0, stretch=tk.NO)
        self.search_tree.column("name", width=200)
        self.search_tree.column("age", width=80)
        self.search_tree.column("gender", width=100)
        self.search_tree.column("insurance", width=120)
        self.search_tree.column("reg_date", width=150)
        
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=self.search_tree.yview)

        scrollbar.pack(side="right", fill="y")
        self.search_tree.configure(yscrollcommand=scrollbar.set)
        self.search_tree.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

    def search_by_name(self):

        try:
            query = {"name": {"$regex": self.search_name_entry.get(), "$options": "i"}}
            self.display_search_results(patients_col.find(query))
        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {str(e)}")

    def filter_by_age(self):


        try:
            min_age = int(self.min_age_entry.get()) if self.min_age_entry.get().isdigit() else 0
            max_age = int(self.max_age_entry.get()) if self.max_age_entry.get().isdigit() else 100
            query = {"age": {"$gte": min_age, "$lte": max_age}}
            self.display_search_results(patients_col.find(query))
        except Exception as e:
            messagebox.showerror("Error", f"Age filter failed: {str(e)}")

    def filter_by_date(self):
        try:
            from_date = datetime.strptime(self.from_date_entry.get(), "%Y-%m-%d") if self.from_date_entry.get() else datetime.min
            to_date = datetime.strptime(self.to_date_entry.get(), "%Y-%m-%d") if self.to_date_entry.get() else datetime.max
            query = {"registration_date": {"$gte": from_date, "$lte": to_date}}
            self.display_search_results(patients_col.find(query))
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
        except Exception as e:
            messagebox.showerror("Error", f"Date filter failed: {str(e)}")

    def filter_by_insurance(self):

        try:
            insurance = self.search_insurance_entry.get()
            if insurance == "All":
                self.display_search_results(patients_col.find())
            else:
                query = {"insurance": insurance}
                self.display_search_results(patients_col.find(query))
        except Exception as e:
            messagebox.showerror("Error", f"Insurance filter failed: {str(e)}")

    def display_search_results(self, cursor):
        self.search_tree.delete(*self.search_tree.get_children())
        for patient in cursor:

            self.search_tree.insert("", tk.END, values=(
                str(patient["_id"]),
                patient.get("name", "N/A"),
                patient.get("age", "N/A"),
                patient.get("gender", "N/A"),
                patient.get("insurance", "N/A"),
                patient.get("registration_date", "N/A").strftime("%Y-%m-%d") if hasattr(patient.get("registration_date"), "strftime") else "N/A"
            ))

    # Dashboard
    def create_dashboard_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Dashboard")

        
        stats_frame = ttk.Frame(tab)
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(stats_frame, text="Total Patients:", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=5)
        self.total_patients_label = tk.Label(stats_frame, text="0", font=("Arial", 16, "bold"))
        self.total_patients_label.grid(row=0, column=1, padx=10, pady=5, sticky='w')
        #counts appointments today
        tk.Label(stats_frame, text="Today's Appointments:", font=("Arial", 12)).grid(row=0, column=2, padx=10, pady=5)
        self.today_appointments_label = tk.Label(stats_frame, text="0", font=("Arial", 16, "bold"))
        self.today_appointments_label.grid(row=0, column=3, padx=10, pady=5, sticky='w')

        tk.Label(stats_frame, text="Average Age:", font=("Arial", 12)).grid(row=0, column=4, padx=10, pady=5)
        self.avg_age_label = tk.Label(stats_frame, text="0", font=("Arial", 16, "bold"))
        self.avg_age_label.grid(row=0, column=5, padx=10, pady=5, sticky='w')

        # revenue board
        tk.Label(stats_frame, text="Total Revenue:", font=("Arial", 12)).grid(row=0, column=6, padx=10, pady=5)
        self.total_revenue_label = tk.Label(stats_frame, text="$0", font=("Arial", 16, "bold"))
        self.total_revenue_label.grid(row=0, column=7, padx=10, pady=5, sticky='w')

        graph_notebook = ttk.Notebook(tab)
        graph_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # creating the tabs
        gender_tab = ttk.Frame(graph_notebook)
        self.gender_fig, self.gender_ax = plt.subplots(figsize=(6, 4))
        self.gender_canvas = FigureCanvasTkAgg(self.gender_fig, master=gender_tab)
        self.gender_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        graph_notebook.add(gender_tab, text="Gender Distribution")
        age_tab = ttk.Frame(graph_notebook)
        self.age_fig, self.age_ax = plt.subplots(figsize=(6, 4))
        self.age_canvas = FigureCanvasTkAgg(self.age_fig, master=age_tab)
        self.age_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        graph_notebook.add(age_tab, text="Age Distribution")
        insurance_tab = ttk.Frame(graph_notebook)
        self.insurance_fig, self.insurance_ax = plt.subplots(figsize=(6, 4))
        self.insurance_canvas = FigureCanvasTkAgg(self.insurance_fig, master=insurance_tab)
        self.insurance_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        graph_notebook.add(insurance_tab, text="Insurance Distribution")

        appointments_tab = ttk.Frame(graph_notebook)
        self.appointments_fig, self.appointments_ax = plt.subplots(figsize=(6, 4))
        self.appointments_canvas = FigureCanvasTkAgg(self.appointments_fig, master=appointments_tab)
        self.appointments_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        graph_notebook.add(appointments_tab, text="Appointments Trend")

        registration_tab = ttk.Frame(graph_notebook)
        self.registration_fig, self.registration_ax = plt.subplots(figsize=(6, 4))
        self.registration_canvas = FigureCanvasTkAgg(self.registration_fig, master=registration_tab)
        self.registration_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        graph_notebook.add(registration_tab, text="Registration Trend")

        revenue_tab = ttk.Frame(graph_notebook)
        self.revenue_fig, self.revenue_ax = plt.subplots(figsize=(6, 4))
        self.revenue_canvas = FigureCanvasTkAgg(self.revenue_fig, master=revenue_tab)
        self.revenue_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        graph_notebook.add(revenue_tab, text="Revenue by Type")

        # To refresh the data, the ffunction afterwards will be responsible for making the updates to the dashboard
        tk.Button(tab, text="Refresh Dashboard", command=self.update_dashboard, font=('Arial', 12), height=1, width=20).pack(pady=10)

    def update_dashboard(self):
        try:
            total_patients = patients_col.count_documents({})
            self.total_patients_label.config(text=str(total_patients))
            
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today.replace(day=today.day + 1)
            today_appointments = appointments_col.count_documents({
                "date": {"$gte": today, "$lt": tomorrow}
            })
            self.today_appointments_label.config(text=str(today_appointments))
            
            pipeline = [
                {"$group": {"_id": None, "avgAge": {"$avg": "$age"}}}
            ]
            avg_age_result = list(patients_col.aggregate(pipeline))
            avg_age = avg_age_result[0]["avgAge"] if avg_age_result else 0
            self.avg_age_label.config(text=f"{avg_age:.1f} years")

            pipeline = [
                {"$match": {"status": "Completed"}},
                {"$group": {"_id": None, "total": {"$sum": "$bill_amount"}}}
            ]
            revenue_result = list(appointments_col.aggregate(pipeline))
            total_revenue = revenue_result[0]["total"] if revenue_result else 0
            self.total_revenue_label.config(text=f"${total_revenue:,.2f}")
            male = patients_col.count_documents({"gender": "Male"})
            female = patients_col.count_documents({"gender": "Female"})
            other = patients_col.count_documents({"gender": "Other"})
            
            self.gender_ax.clear()
            if male + female + other > 0:
                self.gender_ax.pie([male, female, other], 
                                 labels=["Male", "Female", "Other"], 
                                 autopct="%1.1f%%",
                                 colors=['lightblue', 'lightpink', 'lightgray'])
                self.gender_ax.set_title("Gender Distribution", fontsize=12)
            else:
                self.gender_ax.text(0.5, 0.5, "No data available", ha="center", fontsize=12)
            self.gender_canvas.draw()

            ages = [p.get('age', 0) for p in patients_col.find({}, {'age': 1})]
            self.age_ax.clear()

            if ages:
                bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
                self.age_ax.hist(ages, bins=bins, edgecolor='black', color='skyblue')
                self.age_ax.set_title("Age Distribution", fontsize=12)
                self.age_ax.set_xlabel("Age")
                self.age_ax.set_ylabel("Number of Patients")
                self.age_ax.grid(axis='y', alpha=0.5)
            else:
                self.age_ax.text(0.5, 0.5, "No data available", ha="center", fontsize=12)
            self.age_canvas.draw()

            insurance_counts = patients_col.aggregate([
                {"$group": {"_id": "$insurance", "count": {"$sum": 1}}}
            ])
            insurance_data = {item["_id"]: item["count"] for item in insurance_counts}
            
            self.insurance_ax.clear()
            if insurance_data:
                labels = list(insurance_data.keys())
                values = list(insurance_data.values())
                colors = ['gold', 'lightgreen', 'lightcoral', 'lightskyblue']
                self.insurance_ax.pie(values, labels=labels, autopct="%1.1f%%", colors=colors[:len(values)])
                self.insurance_ax.set_title("Insurance Distribution", fontsize=12)
            else:
                self.insurance_ax.text(0.5, 0.5, "No data available", ha="center", fontsize=12)
            self.insurance_canvas.draw()
            pipeline = [
                {"$group": {
                    "_id": {"year": {"$year": "$date"}, "month": {"$month": "$date"}},
                    "count": {"$sum": 1}
                }},
                {"$sort": {"_id.year": 1, "_id.month": 1}}
            ]
            appointments_data = list(appointments_col.aggregate(pipeline))
            
            self.appointments_ax.clear()
            if appointments_data:
                months = [f"{item['_id']['month']}/{item['_id']['year']}" for item in appointments_data]
                counts = [item['count'] for item in appointments_data]
                
                self.appointments_ax.bar(months, counts, color='mediumseagreen')
                self.appointments_ax.set_title("Appointments by Month", fontsize=12)
                self.appointments_ax.set_xlabel("Month/Year")
                self.appointments_ax.set_ylabel("Number of Appointments")
                self.appointments_ax.tick_params(axis='x', rotation=45)
                self.appointments_ax.grid(axis='y', alpha=0.5)
            else:
                self.appointments_ax.text(0.5, 0.5, "No data available", ha="center", fontsize=12)
            self.appointments_canvas.draw()
            pipeline = [
                {"$group": {
                    "_id": {"year": {"$year": "$registration_date"}, "month": {"$month": "$registration_date"}},
                    "count": {"$sum": 1}
                }},
                {"$sort": {"_id.year": 1, "_id.month": 1}}
            ]
            registration_data = list(patients_col.aggregate(pipeline))
            
            self.registration_ax.clear()
            if registration_data:
                months = [f"{item['_id']['month']}/{item['_id']['year']}" for item in registration_data]
                counts = [item['count'] for item in registration_data]
                
                self.registration_ax.plot(months, counts, marker='o', color='royalblue')
                self.registration_ax.set_title("Patient Registration Trend", fontsize=12)
                self.registration_ax.set_xlabel("Month/Year")
                self.registration_ax.set_ylabel("Number of Registrations")
                self.registration_ax.tick_params(axis='x', rotation=45)
                self.registration_ax.grid(alpha=0.5)
            else:
                self.registration_ax.text(0.5, 0.5, "No data available", ha="center", fontsize=12)
            self.registration_canvas.draw()

            pipeline = [
                {"$match": {"status": "Completed"}},
                {"$group": {
                    "_id": "$consultation_type",
                    "total": {"$sum": "$bill_amount"},
                    "count": {"$sum": 1}
                }},
                {"$sort": {"total": -1}}
            ]

            revenue_data = list(appointments_col.aggregate(pipeline))
            
            self.revenue_ax.clear()
            if revenue_data:
                types = [item["_id"] for item in revenue_data]
                amounts = [item["total"] for item in revenue_data]
                
                bars = self.revenue_ax.bar(types, amounts, color='teal')
                self.revenue_ax.set_title("Revenue by Consultation Type", fontsize=12)
                self.revenue_ax.set_xlabel("Consultation Type")
                self.revenue_ax.set_ylabel("Total Revenue ($)")
                self.revenue_ax.tick_params(axis='x', rotation=45)
                self.revenue_ax.grid(axis='y', alpha=0.5)
                
                # Add value labels on top of bars
                for bar in bars:
                    height = bar.get_height()
                    self.revenue_ax.text(bar.get_x() + bar.get_width()/2., height,
                                       f'${height:,.2f}',
                                       ha='center', va='bottom')
            else:
                self.revenue_ax.text(0.5, 0.5, "No revenue data available", ha="center", fontsize=12)
            self.revenue_canvas.draw()

        except Exception as e:
            messagebox.showerror("Error", f"Dashboard update failed: {str(e)}")

    def create_appointments_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Appointments")

        form_frame = ttk.Frame(tab)
        form_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        tk.Label(form_frame, text="Patient Name:", font=('Arial', 12)).grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.appointment_patient_name = ttk.Combobox(form_frame, font=('Arial', 12), width=28)
        self.appointment_patient_name.grid(row=0, column=1, padx=10, pady=10)
        self.appointment_patient_name.bind("<KeyRelease>", self.update_patient_suggestions)

        tk.Label(form_frame, text="Date (YYYY-MM-DD):", font=('Arial', 12)).grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.appointment_date = tk.Entry(form_frame, font=('Arial', 12), width=30)
        self.appointment_date.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(form_frame, text="Time (HH:MM):", font=('Arial', 12)).grid(row=2, column=0, padx=10, pady=10, sticky='w')
        self.appointment_time = tk.Entry(form_frame, font=('Arial', 12), width=30)
        self.appointment_time.grid(row=2, column=1, padx=10, pady=10)

        tk.Label(form_frame, text="Consultation Type:", font=('Arial', 12)).grid(row=3, column=0, padx=10, pady=10, sticky='w')
        self.consultation_type = ttk.Combobox(form_frame, values=[
            "General Checkup", "Follow-up", "Specialist", "Emergency", "Vaccination"
        ], font=('Arial', 12), width=28)
        self.consultation_type.grid(row=3, column=1, padx=10, pady=10)
        self.consultation_type.set("General Checkup")

        tk.Label(form_frame, text="Reason:", font=('Arial', 12)).grid(row=4, column=0, padx=10, pady=10, sticky='w')
        self.appointment_reason = tk.Text(form_frame, height=4, width=30, font=('Arial', 12))
        self.appointment_reason.grid(row=4, column=1, padx=10, pady=10)

        tk.Label(form_frame, text="Bill Amount ($):", font=('Arial', 12)).grid(row=5, column=0, padx=10, pady=10, sticky='w')
        self.bill_amount = tk.Entry(form_frame, font=('Arial', 12), width=30)
        self.bill_amount.grid(row=5, column=1, padx=10, pady=10)

        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=15)
        tk.Button(button_frame, text="Schedule", command=self.schedule_appointment, font=('Arial', 12), height=1, width=15).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Mark Completed", command=self.mark_appointment_completed, font=('Arial', 12), height=1, width=15).grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.cancel_appointment, font=('Arial', 12), height=1, width=15).grid(row=0, column=2, padx=5)
        list_frame = ttk.Frame(tab)
        list_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.appointments_tree = ttk.Treeview(list_frame, columns=(
            "id", "patient_name", "date", "time", "type", "status", "bill"
        ), show="headings", height=15)
        
        self.appointments_tree.heading("id", text="ID")
        self.appointments_tree.heading("patient_name", text="Patient")
        self.appointments_tree.heading("date", text="Date")
        self.appointments_tree.heading("time", text="Time")
        self.appointments_tree.heading("type", text="Type")
        self.appointments_tree.heading("status", text="Status")
        self.appointments_tree.heading("bill", text="Bill ($)")
        
        self.appointments_tree.column("id", width=0, stretch=tk.NO)
        self.appointments_tree.column("patient_name", width=150)
        self.appointments_tree.column("date", width=100)
        self.appointments_tree.column("time", width=80)
        self.appointments_tree.column("type", width=120)
        self.appointments_tree.column("status", width=100)
        self.appointments_tree.column("bill", width=80)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.appointments_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.appointments_tree.configure(yscrollcommand=scrollbar.set)
        self.appointments_tree.pack(fill=tk.BOTH, expand=True)
        self.appointments_tree.bind("<ButtonRelease-1>", self.load_selected_appointment)

        filter_frame = ttk.Frame(list_frame)
        filter_frame.pack(fill=tk.X, pady=5)

        tk.Label(filter_frame, text="Filter by Status:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.appointment_status_filter = ttk.Combobox(filter_frame, values=[
            "All", "Scheduled", "Completed", "Cancelled"
        ], font=('Arial', 10), width=12)
        self.appointment_status_filter.pack(side=tk.LEFT, padx=5)
        self.appointment_status_filter.set("All")
        
        tk.Button(filter_frame, text="Apply Filter", command=self.refresh_appointments, 
                 font=('Arial', 10), width=10).pack(side=tk.LEFT, padx=5)
        
        self.refresh_appointments()

    def update_patient_suggestions(self, event):
        query = self.appointment_patient_name.get()
        if len(query) >= 2:
            patients = patients_col.find(
                {"name": {"$regex": f"^{query}", "$options": "i"}},
                {"name": 1}
            ).limit(10)
            self.appointment_patient_name['values'] = [p['name'] for p in patients]

    def schedule_appointment(self):
        try:
            patient_name = self.appointment_patient_name.get()
            if not patient_name:
                raise ValueError("Patient name is required")
            
            patient = patients_col.find_one({"name": patient_name})
            if not patient:
                raise ValueError("Patient not found")
            
            appointment_date = datetime.strptime(self.appointment_date.get(), "%Y-%m-%d")
            appointment_time = self.appointment_time.get()
            
            try:
                datetime.strptime(appointment_time, "%H:%M")
            except ValueError:
                raise ValueError("Invalid time format. Use HH:MM")
            
            appointment_data = {
                "patient_id": str(patient["_id"]),
                "patient_name": patient_name,
                "date": appointment_date,
                "time": appointment_time,
                "consultation_type": self.consultation_type.get(),
                "reason": self.appointment_reason.get("1.0", tk.END).strip(),
                "bill_amount": float(self.bill_amount.get()) if self.bill_amount.get() else 0,
                "status": "Scheduled",
                "created_at": datetime.now()
            }
            
            appointments_col.insert_one(appointment_data)
            self.log_audit(f"Scheduled appointment for {patient_name}")
            self.refresh_appointments()
            self.clear_appointment_form()
            messagebox.showinfo("Success", "Appointment scheduled!")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to schedule appointment: {str(e)}")

    def mark_appointment_completed(self):
        try:
            selected = self.appointments_tree.selection()
            if not selected:
                raise ValueError("No appointment selected")
            
            appointment_id = self.appointments_tree.item(selected)["values"][0]
            appointments_col.update_one(
                {"_id": ObjectId(appointment_id)},
                {"$set": {"status": "Completed", "completed_at": datetime.now()}}
            )
            self.log_audit(f"Marked appointment as completed: {appointment_id}")
            self.refresh_appointments()
            messagebox.showinfo("Success", "Appointment marked as completed!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update appointment: {str(e)}")

    def cancel_appointment(self):
        try:
            selected = self.appointments_tree.selection()
            if not selected:
                raise ValueError("No appointment selected")
            
            appointment_id = self.appointments_tree.item(selected)["values"][0]
            appointments_col.update_one(
                {"_id": ObjectId(appointment_id)},
                {"$set": {"status": "Cancelled", "cancelled_at": datetime.now()}}
            )
            self.log_audit(f"Cancelled appointment: {appointment_id}")
            self.refresh_appointments()
            messagebox.showinfo("Success", "Appointment cancelled!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to cancel appointment: {str(e)}")

    def load_selected_appointment(self, event):
        try:
            selected = self.appointments_tree.selection()
            if not selected:
                return
            
            appointment_id = self.appointments_tree.item(selected)["values"][0]
            appointment = appointments_col.find_one({"_id": ObjectId(appointment_id)})
            
            if not appointment:
                raise ValueError("Appointment not found in database")
            
            self.clear_appointment_form()
            self.appointment_patient_name.set(appointment.get("patient_name", ""))
            self.appointment_date.insert(0, appointment.get("date", "").strftime("%Y-%m-%d") if hasattr(appointment.get("date"), "strftime") else "")
            self.appointment_time.insert(0, appointment.get("time", ""))
            self.consultation_type.set(appointment.get("consultation_type", "General Checkup"))
            self.appointment_reason.insert("1.0", appointment.get("reason", ""))
            self.bill_amount.insert(0, str(appointment.get("bill_amount", 0)))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load appointment: {str(e)}")

    def clear_appointment_form(self):
        self.appointment_patient_name.set('')
        self.appointment_date.delete(0, tk.END)
        self.appointment_time.delete(0, tk.END)
        self.consultation_type.set("General Checkup")
        self.appointment_reason.delete("1.0", tk.END)
        self.bill_amount.delete(0, tk.END)

    def refresh_appointments(self):
        self.appointments_tree.delete(*self.appointments_tree.get_children())
        
        status_filter = self.appointment_status_filter.get()
        query = {} if status_filter == "All" else {"status": status_filter}
        
        for appt in appointments_col.find(query).sort("date", 1):
            self.appointments_tree.insert("", tk.END, values=(
                str(appt["_id"]),
                appt.get("patient_name", "N/A"),
                appt.get("date", "N/A").strftime("%Y-%m-%d") if hasattr(appt.get("date"), "strftime") else "N/A",
                appt.get("time", "N/A"),
                appt.get("consultation_type", "N/A"),
                appt.get("status", "N/A"),
                f"{appt.get('bill_amount', 0):.2f}"
            ))

    def create_export_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Export Data")

        export_frame = ttk.Frame(tab)
        export_frame.pack(pady=50)

        tk.Label(export_frame, text="Export Patient Data", font=('Arial', 14)).grid(row=0, column=0, columnspan=2, pady=20)
        
        tk.Button(export_frame, text="Export to CSV", command=self.export_to_csv, 
                 font=('Arial', 12), height=2, width=20).grid(row=1, column=0, padx=20, pady=10)
        
        tk.Button(export_frame, text="Export to JSON", command=self.export_to_json, 
                 font=('Arial', 12), height=2, width=20).grid(row=1, column=1, padx=20, pady=10)
        
        tk.Label(export_frame, text="Export Appointment Data", font=('Arial', 14)).grid(row=2, column=0, columnspan=2, pady=20)
        
        tk.Button(export_frame, text="Export to CSV", command=lambda: self.export_to_csv('appointments'), 
                 font=('Arial', 12), height=2, width=20).grid(row=3, column=0, padx=20, pady=10)
        
        tk.Button(export_frame, text="Export to JSON", command=lambda: self.export_to_json('appointments'), 
                 font=('Arial', 12), height=2, width=20).grid(row=3, column=1, padx=20, pady=10)

    def export_to_csv(self, collection='patients'):
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv")],
                title=f"Export {collection} data to CSV"
            )
            if not file_path:
                return
            
            if collection == 'patients':
                data = list(patients_col.find({}, {"_id": 0}))
            else:
                data = list(appointments_col.find({}, {"_id": 0}))
            
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False)
            messagebox.showinfo("Success", f"{collection.capitalize()} data exported to CSV!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV: {str(e)}")

    def export_to_json(self, collection='patients'):
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json")],
                title=f"Export {collection} data to JSON"
            )
            if not file_path:
                return
            
            if collection == 'patients':
                data = list(patients_col.find({}, {"_id": 0}))
            else:
                data = list(appointments_col.find({}, {"_id": 0}))
            
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4, default=str)
            messagebox.showinfo("Success", f"{collection.capitalize()} data exported to JSON!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export JSON: {str(e)}")

    # History or audit of all changes ever made

    def create_audit_logs_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Audit Logs")

        self.audit_tree = ttk.Treeview(tab, columns=("timestamp", "action"), show="headings", height=25)
        self.audit_tree.heading("timestamp", text="Timestamp")
        self.audit_tree.heading("action", text="Action")
        self.audit_tree.column("timestamp", width=200)
        self.audit_tree.column("action", width=1000)
        
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=self.audit_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.audit_tree.configure(yscrollcommand=scrollbar.set)
        self.audit_tree.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        self.refresh_audit_logs()

    def log_audit(self, action):
        audit_logs_col.insert_one({
            "timestamp": datetime.now(),
            "action": action
        })
        self.refresh_audit_logs()

    def refresh_audit_logs(self):
        self.audit_tree.delete(*self.audit_tree.get_children())
        for log in audit_logs_col.find().sort("timestamp", -1).limit(100):
            self.audit_tree.insert("", tk.END, values=(
                log.get("timestamp", "N/A").strftime("%Y-%m-%d %H:%M:%S"),
                log.get("action", "N/A")
            ))
if __name__ == "__main__":
    root = tk.Tk()
    app = PatientRegistryApp(root)
    root.mainloop()