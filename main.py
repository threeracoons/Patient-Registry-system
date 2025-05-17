import tkinter as tk
from dashboard import DashboardTab
from patients import PatientsTab

class PatientRegistryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Patient Registry")
        self.root.geometry("800x600")

        # Initialize tabs
        self.tab_control = tk.Notebook(root)
        self.dashboard_tab = DashboardTab(self.tab_control)
        self.patients_tab = PatientsTab(self.tab_control)
        self.tab_control.pack(expand=True, fill="both")

if __name__ == "__main__":
    root = tk.Tk()
    app = PatientRegistryApp(root)
    root.mainloop()