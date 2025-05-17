from tkinter import ttk

class DashboardTab:
    def __init__(self, tab_control):
        self.tab = ttk.Frame(tab_control)
        tab_control.add(self.tab, text="Dashboard")
        self.create_widgets()

    def create_widgets(self):
        label = ttk.Label(self.tab, text="Total Patients: 120")
        label.pack()