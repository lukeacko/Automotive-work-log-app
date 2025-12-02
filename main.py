import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import os
import csv

# --------------------------
# Firebase Setup
# --------------------------
SERVICE_ACCOUNT_PATH = "serviceAccount.json"
if not os.path.exists(SERVICE_ACCOUNT_PATH):
    raise FileNotFoundError(f"Firebase service account file not found at: {SERVICE_ACCOUNT_PATH}")

cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

# --------------------------
# Models
# --------------------------
class Vehicle:
    def __init__(self, make: str, model: str, registration: str, year: str, doc_id: str = None):
        self.make = (make or "").strip()
        self.model = (model or "").strip()
        self.registration = (registration or "").strip().upper()
        self.year = (year or "").strip()
        self.doc_id = doc_id

    @property
    def label(self) -> str:
        parts = [p for p in (self.make, self.model) if p]
        label_left = " ".join(parts) if parts else "Unknown"
        reg_part = f"({self.registration})" if self.registration else ""
        year_part = f"{self.year}" if self.year else ""
        return " ".join([label_left, reg_part, year_part]).strip()

    def __repr__(self):
        return f"<Vehicle {self.label}>"

# --------------------------
# Reusable Popups
# --------------------------
class BasePopup(tk.Toplevel):
    def __init__(self, parent, title="Popup", width=400, height=300):
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

class VehiclePopup(BasePopup):
    def __init__(self, parent, vehicle: Vehicle = None, callback=None):
        super().__init__(parent, "Edit Vehicle" if vehicle else "Add Vehicle", 360, 280)
        self.vehicle = vehicle
        self.callback = callback

        self.make_var = tk.StringVar(value=vehicle.make if vehicle else "")
        self.model_var = tk.StringVar(value=vehicle.model if vehicle else "")
        self.reg_var = tk.StringVar(value=vehicle.registration if vehicle else "")
        self.year_var = tk.StringVar(value=vehicle.year if vehicle else "")

        for text, var in [("Make", self.make_var), ("Model", self.model_var),
                          ("Registration", self.reg_var), ("Year", self.year_var)]:
            tk.Label(self, text=f"{text}:").pack(anchor="w", padx=10, pady=(5,0))
            tk.Entry(self, textvariable=var).pack(fill="x", padx=10)

        tk.Button(self, text="Save", command=self.save_vehicle).pack(pady=15)

    def save_vehicle(self):
        make = self.make_var.get().strip()
        model = self.model_var.get().strip()
        reg = self.reg_var.get().strip().upper()
        year = self.year_var.get().strip()
        if year and (not year.isdigit() or len(year) != 4):
            messagebox.showerror("Error", "Year must be 4-digit or blank")
            return

        v = Vehicle(make, model, reg, year, self.vehicle.doc_id if self.vehicle else None)
        if self.callback:
            self.callback(v)
        self.destroy()

class TechnicianPopup(BasePopup):
    def __init__(self, parent, callback=None):
        super().__init__(parent, "Add Technician", 250, 120)
        self.callback = callback
        tk.Label(self, text="Enter technician name:").pack(pady=5)
        self.name_var = tk.StringVar()
        tk.Entry(self, textvariable=self.name_var).pack(pady=5)
        tk.Button(self, text="Save", command=self.save_technician).pack(pady=5)

    def save_technician(self):
        name = self.name_var.get().strip()
        if name and self.callback:
            self.callback(name)
        self.destroy()

class JobPopup(BasePopup):
    def __init__(self, parent, vehicles, technicians, job_data=None, callback=None):
        super().__init__(parent, "Edit Job" if job_data else "Add Job", 400, 450)
        self.vehicles = vehicles
        self.technicians = technicians
        self.callback = callback
        self.job_data = job_data

        # Job Number
        tk.Label(self, text="Job Number:").pack(anchor="w", padx=10, pady=(10,0))
        self.jobnum_var = tk.StringVar(value=job_data.get("jobnum") if job_data else "")
        tk.Entry(self, textvariable=self.jobnum_var).pack(fill="x", padx=10)

        # Vehicle
        tk.Label(self, text="Vehicle:").pack(anchor="w", padx=10, pady=(10,0))
        self.vehicle_var = tk.StringVar(value=job_data.get("vehicle_label") if job_data else "")
        self.vehicle_dropdown = ttk.Combobox(self, textvariable=self.vehicle_var,
                                             values=list(self.vehicles.keys()), state="readonly")
        self.vehicle_dropdown.pack(fill="x", padx=10)

        # Technician
        tk.Label(self, text="Technician:").pack(anchor="w", padx=10, pady=(10,0))
        self.tech_var = tk.StringVar(value=job_data.get("technician") if job_data else "")
        self.tech_dropdown = ttk.Combobox(self, textvariable=self.tech_var,
                                          values=self.technicians, state="readonly")
        self.tech_dropdown.pack(fill="x", padx=10)

        # Status
        tk.Label(self, text="Status:").pack(anchor="w", padx=10, pady=(10,0))
        self.status_var = tk.StringVar(value=job_data.get("status") if job_data else "Pending")
        self.status_dropdown = ttk.Combobox(self, textvariable=self.status_var,
                                            values=["Pending","In Progress","Complete"], state="readonly")
        self.status_dropdown.pack(fill="x", padx=10)

        # Date
        tk.Label(self, text="Date:").pack(anchor="w", padx=10, pady=(10,0))
        self.date_var = tk.StringVar(value=job_data.get("date") if job_data else datetime.today().strftime("%Y-%m-%d"))
        tk.Entry(self, textvariable=self.date_var).pack(fill="x", padx=10)

        # Description
        tk.Label(self, text="Description:").pack(anchor="w", padx=10, pady=(10,0))
        self.desc_text = tk.Text(self, height=5)
        self.desc_text.pack(fill="both", padx=10, pady=5)
        if job_data:
            self.desc_text.insert("1.0", job_data.get("description",""))

        tk.Button(self, text="Save", command=self.save_job).pack(anchor="s", pady=10)


    def save_job(self):
        jobnum = self.jobnum_var.get().strip()
        vehicle_label = self.vehicle_var.get()
        technician = self.tech_var.get()
        status = self.status_var.get()
        date = self.date_var.get()
        description = self.desc_text.get("1.0","end").strip()

        if not jobnum or not vehicle_label or not technician:
            messagebox.showerror("Error","Please fill all required fields")
            return

        if self.callback:
            self.callback({
                "jobnum": jobnum,
                "vehicle_label": vehicle_label,
                "technician": technician,
                "status": status,
                "date": date,
                "description": description
            })
        
        self.destroy()


        
# --------------------------
# Main App
# --------------------------
class WorkLogApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Work Log App")
        self.root.geometry("900x400")

        self.jobnum_input = tk.StringVar(value=self.get_next_jobnum())
        self.vehicle_var = tk.StringVar()
        self.tech_var = tk.StringVar(value="Select...")
        self.status_var = tk.StringVar(value="Pending")
        self.date_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))

        self.vehicles = {}  # label -> Vehicle
        self.tech_list = []

        self.load_vehicles()
        self.load_technicians()

        self.create_input_section()
        self.create_buttons()
        self.job_logs_window = None

    # --------------------------
    # UI
    # --------------------------
    def create_input_section(self):
        frame = tk.LabelFrame(self.root, text="Job Data")
        frame.pack(padx=10, pady=10, fill="x")

        tk.Label(frame, text="Job Number:").grid(row=0,column=0,padx=5,pady=5,sticky="w")
        tk.Entry(frame,textvariable=self.jobnum_input,width=20).grid(row=0,column=1,padx=5,pady=5)

        tk.Label(frame,text="Vehicle:").grid(row=0,column=2,padx=5,pady=5,sticky="w")
        self.vehicle_dropdown = ttk.Combobox(frame,textvariable=self.vehicle_var,
                                             values=list(self.vehicles.keys()), state="readonly",width=30)
        self.vehicle_dropdown.grid(row=0,column=3,padx=5,pady=5)
        self.vehicle_dropdown.bind("<<ComboboxSelected>>", self.vehicle_dropdown_selected)

        tk.Label(frame,text="Technician:").grid(row=1,column=0,padx=5,pady=5,sticky="w")
        self.tech_dropdown = ttk.Combobox(frame,textvariable=self.tech_var,
                                          values=self.tech_list, state="readonly",width=18)
        self.tech_dropdown.grid(row=1,column=1,padx=5,pady=5)

        tk.Label(frame,text="Status:").grid(row=1,column=2,padx=5,pady=5,sticky="w")
        self.status_dropdown = ttk.Combobox(frame,textvariable=self.status_var,
                                            values=["Pending","In Progress","Complete"],state="readonly",width=18)
        self.status_dropdown.grid(row=1,column=3,padx=5,pady=5)

        tk.Label(frame,text="Date:").grid(row=2,column=0,padx=5,pady=5,sticky="w")
        tk.Entry(frame,textvariable=self.date_var,width=20).grid(row=2,column=1,padx=5,pady=5)

        tk.Label(self.root,text="Description:").pack(anchor="w",padx=12)
        self.desc_text = tk.Text(self.root,height=5)
        self.desc_text.pack(fill="x", padx=10, pady=5)

    def create_buttons(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=10)
        tk.Button(frame,text="Save Job",command=self.save_job).grid(row=0,column=0,padx=5)
        tk.Button(frame,text="Reset",command=self.reset_form).grid(row=0,column=1,padx=5)
        tk.Button(frame,text="View Job Logs",command=self.view_job_logs).grid(row=0,column=2,padx=5)
        tk.Button(frame,text="Manage Vehicles",command=self.manage_vehicles).grid(row=0,column=3,padx=5)
        tk.Button(frame,text="Manage Technicians",command=self.manage_technicians).grid(row=0,column=4,padx=5)

    # --------------------------
    # Data Load
    # --------------------------
    def load_vehicles(self):
        self.vehicles.clear()
        try:
            for doc in db.collection("vehicles").stream():
                data = doc.to_dict() or {}
                v = Vehicle(data.get("make",""),data.get("model",""),data.get("registration",""),str(data.get("year","")), doc.id)
                self.vehicles[v.label] = v
        except Exception as e:
            messagebox.showerror("Error",f"Failed to load vehicles: {e}")

    def load_technicians(self):
        self.tech_list.clear()
        try:
            for doc in db.collection("technicians").stream():
                name = doc.to_dict().get("name")
                if name:
                    self.tech_list.append(name)
        except Exception as e:
            messagebox.showerror("Error",f"Failed to load technicians: {e}")

    # --------------------------
    # Save Job
    # --------------------------
    def save_job(self):
        jobnum = self.jobnum_input.get().strip()
        vehicle_label = self.vehicle_var.get()
        technician = self.tech_var.get()
        status = self.status_var.get()
        date = self.date_var.get()
        description = self.desc_text.get("1.0","end").strip()

        if not jobnum or not vehicle_label or not technician:
            messagebox.showerror("Error","Please fill all required fields")
            return

        vehicle = self.vehicles.get(vehicle_label)
        if not vehicle:
            messagebox.showerror("Error","Vehicle not found")
            return

        try:
            db.collection("logs").add({
                "jobnum": jobnum,
                "vehicle_label": vehicle.label,
                "vehicle_id": vehicle.doc_id,
                "technician": technician,
                "status": status,
                "date": date,
                "description": description
            })
            messagebox.showinfo("Saved","Job saved successfully")
            self.jobnum_input.set(self.get_next_jobnum())
            self.reset_form()
        except Exception as e:
            messagebox.showerror("Error",f"Failed to save job: {e}")

    # --------------------------
    # Utilities
    # --------------------------
    def get_next_jobnum(self):
        try:
            last = list(db.collection("logs").order_by("jobnum",direction=firestore.Query.DESCENDING).limit(1).stream())
            if last:
                return str(int(last[0].to_dict().get("jobnum",0))+1)
            return "1"
        except:
            return "1"

    def reset_form(self):
        self.vehicle_var.set("")
        self.tech_var.set("Select...")
        self.status_var.set("Pending")
        self.date_var.set(datetime.today().strftime("%Y-%m-%d"))
        self.desc_text.delete("1.0","end")

    def vehicle_dropdown_selected(self,event=None):
        if self.vehicle_var.get()=="Add new…":
            VehiclePopup(self.root,callback=self.add_vehicle)

    def add_vehicle(self,vehicle):
        try:
            doc_ref = db.collection("vehicles").add({
                "make": vehicle.make,
                "model": vehicle.model,
                "registration": vehicle.registration,
                "year": vehicle.year,
                "label": vehicle.label,
                "created_at": datetime.now().replace(microsecond=0)
            })[0]
            vehicle.doc_id = doc_ref.id
            messagebox.showinfo("Added",f"Vehicle {vehicle.label} added")
            self.load_vehicles()
            self.vehicle_var.set(vehicle.label)
        except Exception as e:
            messagebox.showerror("Error",f"Failed to add vehicle: {e}")

    # --------------------------
    # Job Logs
    # --------------------------
    def view_job_logs(self):
        if self.job_logs_window and tk.Toplevel.winfo_exists(self.job_logs_window):
            self.job_logs_window.focus()
            return

        self.job_logs_window = tk.Toplevel(self.root)
        self.job_logs_window.title("Job Logs")
        self.job_logs_window.geometry("1000x500")

        columns = ("jobnum","vehicle_label","technician","status","date","description")
        tree = ttk.Treeview(self.job_logs_window, columns=columns,show="headings")
        for col in columns:
            tree.heading(col,text=col.replace("_"," ").title())
            tree.column(col,width=150)
        tree.pack(fill="both",expand=True,padx=10,pady=10)

        # Buttons
        btn_frame = tk.Frame(self.job_logs_window)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame,text="Edit",command=lambda:self.edit_selected_job(tree)).grid(row=0,column=0,padx=5)
        tk.Button(btn_frame,text="Delete",command=lambda:self.delete_selected_job(tree)).grid(row=0,column=1,padx=5)
        tk.Button(btn_frame,text="Export CSV",command=lambda:self.export_tree_csv(tree)).grid(row=0,column=2,padx=5)

        # Load jobs
        for row in tree.get_children():
            tree.delete(row)
        try:
            for doc in db.collection("logs").order_by("date",direction=firestore.Query.DESCENDING).stream():
                data = doc.to_dict() or {}
                tree.insert("", "end", iid=doc.id, values=(
                    data.get("jobnum",""),
                    data.get("vehicle_label",""),
                    data.get("technician",""),
                    data.get("status",""),
                    data.get("date",""),
                    data.get("description","")
                ))
        except Exception as e:
            messagebox.showerror("Error",f"Failed to load jobs: {e}")

    def edit_selected_job(self,tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Select","Select a job to edit")
            return
        doc_id = selected[0]
        doc = db.collection("logs").document(doc_id).get()
        if not doc.exists:
            messagebox.showerror("Error","Job not found")
            return
        JobPopup(self.root,vehicles=self.vehicles,technicians=self.tech_list,job_data=doc.to_dict(),
                 callback=lambda data:self.update_job(doc_id,data))

    def update_job(self,doc_id,data):
        vehicle = self.vehicles.get(data["vehicle_label"])
        if not vehicle:
            messagebox.showerror("Error","Vehicle not found")
            return
        try:
            db.collection("logs").document(doc_id).update({
                "jobnum": data["jobnum"],
                "vehicle_label": vehicle.label,
                "vehicle_id": vehicle.doc_id,
                "technician": data["technician"],
                "status": data["status"],
                "date": data["date"],
                "description": data["description"]
            })
            messagebox.showinfo("Updated","Job updated successfully")
            self.view_job_logs()
        except Exception as e:
            messagebox.showerror("Error",f"Failed to update job: {e}")

    def delete_selected_job(self,tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Select","Select a job to delete")
            return
        doc_id = selected[0]
        if messagebox.askyesno("Confirm","Delete this job?"):
            try:
                db.collection("logs").document(doc_id).delete()
                messagebox.showinfo("Deleted","Job deleted")
                self.view_job_logs()
            except Exception as e:
                messagebox.showerror("Error",f"Failed to delete job: {e}")

    def export_tree_csv(self,tree):
        if not tree.get_children():
            messagebox.showinfo("Info","No data to export")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV files","*.csv")])
        if not file_path:
            return
        with open(file_path,"w",newline="",encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([tree.heading(c)["text"] for c in tree["columns"]])
            for row in tree.get_children():
                writer.writerow(tree.item(row)["values"])
        messagebox.showinfo("Exported","Data exported to CSV")

    # --------------------------
    # Manage Vehicles
    # --------------------------
    def manage_vehicles(self):
        ManageWindow(self.root,"Vehicles",self.vehicles,self.add_vehicle,db.collection("vehicles"))

    # --------------------------
    # Manage Technicians
    # --------------------------
    def manage_technicians(self):
        def add_tech(name):
            try:
                db.collection("technicians").add({"name":name})
                messagebox.showinfo("Added",f"Technician {name} added")
                self.load_technicians()
            except Exception as e:
                messagebox.showerror("Error",f"Failed to add technician: {e}")
        ManageWindow(self.root,"Technicians", {t:t for t in self.tech_list}, add_tech, db.collection("technicians"))

# --------------------------
# Generic Manage Window
# --------------------------
class ManageWindow(tk.Toplevel):
    def __init__(self,parent,title,items,add_callback,collection_ref):
        super().__init__(parent)
        self.title(title)
        self.geometry("500x400")
        self.items = items
        self.add_callback = add_callback
        self.collection_ref = collection_ref

        self.tree = ttk.Treeview(self,columns=("Name",),show="headings")
        self.tree.heading("Name",text="Name")
        self.tree.pack(fill="both",expand=True,padx=10,pady=10)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame,text="Add",command=self.add_item).grid(row=0,column=0,padx=5)
        tk.Button(btn_frame,text="Delete",command=self.delete_item).grid(row=0,column=1,padx=5)
        self.refresh_tree()

    def refresh_tree(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for name in self.items.keys():
            self.tree.insert("", "end", iid=name, values=(name,))

    def add_item(self):
        if "Vehicles" in self.title():
            VehiclePopup(self,callback=self._callback_add)
        else:
            TechnicianPopup(self,callback=self._callback_add)

    def _callback_add(self,item):
        if isinstance(item,str):
            self.add_callback(item)
        else:
            self.add_callback(item)
        self.refresh_tree()

    def delete_item(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select","Select item to delete")
            return
        key = selected[0]
        if messagebox.askyesno("Confirm","Delete this item?"):
            try:
                # Find doc id
                doc_id = None
                for doc in self.collection_ref.stream():
                    data = doc.to_dict()
                    if data.get("label", data.get("name"))==key:
                        doc_id = doc.id
                        break
                if doc_id:
                    self.collection_ref.document(doc_id).delete()
                    messagebox.showinfo("Deleted","Item deleted")
                    self.refresh_tree()
            except Exception as e:
                messagebox.showerror("Error",f"Failed to delete: {e}")

# --------------------------
# Run App
# --------------------------
if __name__=="__main__":
    root = tk.Tk()
    app = WorkLogApp(root)
    root.mainloop()
