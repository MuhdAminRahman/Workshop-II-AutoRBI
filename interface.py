

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    import fitz  
except ImportError:
    fitz = None  


class InspectorApp(tk.Tk):
    """Hub application that lets users walk through each major system flow."""

    def __init__(self) -> None:
        super().__init__()
        self.title("AutoRBI")
        self.geometry("1280x780")
        self.minsize(1100, 720)
        self.selected_role: str | None = None

        self._create_style()
        self._build_layout()
        self._build_menubar()
        self.show_role_selection()

    # UI creation
    def _create_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Card.TLabelframe", padding=12)
        style.configure("Section.TButton", padding=8)

    def _build_menubar(self) -> None:
        menubar = tk.Menu(self)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _build_layout(self) -> None:
        header = ttk.Frame(self, padding=(18, 18, 18, 6))
        header.pack(fill="x")
        ttk.Label(
            header,
            text="AutoRBI",
            font=("Segoe UI", 20, "bold"),
        ).pack(side="left")

        self.content_frame = ttk.Frame(self, padding=16)
        self.content_frame.pack(fill="both", expand=True)

        self.status_var = tk.StringVar(value="Ready.")
        status_bar = ttk.Label(
            self, textvariable=self.status_var, relief="sunken", anchor="w", padding=6
        )
        status_bar.pack(fill="x")

        self.views: dict[str, ttk.Frame] = {}
        self.current_view: ttk.Frame | None = None

    def _swap_view(self, key: str, factory) -> None:
        if self.current_view:
            self.current_view.pack_forget()
        if key not in self.views:
            self.views[key] = factory()
        self.current_view = self.views[key]
        self.current_view.pack(fill="both", expand=True)

    def show_role_selection(self) -> None:
        self.selected_role = None
        def factory() -> RoleSelectionView:
            return RoleSelectionView(self.content_frame, controller=self)

        self._swap_view("roles", factory)
        self.set_status("Select your role to begin.")

    def show_login(self, role: str) -> None:
        self.selected_role = role

        def factory() -> LoginFlowView:
            return LoginFlowView(self.content_frame, controller=self)

        self._swap_view("login", factory)
        login_view = self.views["login"]
        if isinstance(login_view, LoginFlowView):
            login_view.set_role(role)

    def show_engineer_flow(self) -> None:
        def factory() -> EngineerFlowView:
            return EngineerFlowView(self.content_frame, controller=self)

        self._swap_view("engineer", factory)
        self.set_status("Engineer module ready.")

    def show_admin_flow(self) -> None:
        def factory() -> AdminFlowView:
            return AdminFlowView(self.content_frame, controller=self)

        self._swap_view("admin", factory)
        self.set_status("Admin module ready.")

    # ------------------------------------------------------------------ #
    def show_about(self) -> None:
        messagebox.showinfo(
            "About",
            "Autorbi Flow Console\n"
            "Visual reference for Login, Engineer, and Admin processes.",
        )

    def set_status(self, message: str) -> None:
        self.status_var.set(message)
        self.update_idletasks()


class RoleSelectionView(ttk.Frame):
    """First screen where users choose their role."""

    def __init__(self, parent: ttk.Frame, controller: InspectorApp) -> None:
        super().__init__(parent, padding=20)
        self.controller = controller
        self._build()

    def _build(self) -> None:
        ttk.Label(
            self,
            text="Select your role to continue.",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w", pady=(0, 16))

        cards = ttk.Frame(self)
        cards.pack(fill="x", pady=10)

        engineer_card = ttk.LabelFrame(cards, text="Engineer", padding=15, style="Card.TLabelframe")
        engineer_card.pack(side="left", expand=True, fill="both", padx=(0, 12))
        ttk.Label(
            engineer_card,
            text="Extract GA drawings, verify data, generate PDF/PPT templates.",
            wraplength=320,
        ).pack(anchor="w")
        ttk.Button(
            engineer_card,
            text="Continue as Engineer",
            style="Section.TButton",
            command=lambda: self.controller.show_login("engineer"),
        ).pack(fill="x", pady=(14, 0))

        admin_card = ttk.LabelFrame(cards, text="Admin", padding=15, style="Card.TLabelframe")
        admin_card.pack(side="left", expand=True, fill="both", padx=(12, 0))
        ttk.Label(
            admin_card,
            text="Manage users, update accounts, and control activation states.",
            wraplength=320,
        ).pack(anchor="w")
        ttk.Button(
            admin_card,
            text="Continue as Admin",
            style="Section.TButton",
            command=lambda: self.controller.show_login("admin"),
        ).pack(fill="x", pady=(14, 0))


class LoginFlowView(ttk.Frame):
    """Login/Register view displayed after choosing a role."""

    def __init__(self, parent: ttk.Frame, controller: InspectorApp) -> None:
        super().__init__(parent, padding=20)
        self.controller = controller
        self.role = "engineer"
        self._build()

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.role_heading = ttk.Label(self, text="", font=("Segoe UI", 16, "bold"))
        self.role_heading.pack(anchor="w", pady=(0, 12))

        forms_container = ttk.Frame(self)
        forms_container.pack(fill="x", pady=10)

        login_card = ttk.LabelFrame(forms_container, text="Login", padding=15, style="Card.TLabelframe")
        login_card.pack(side="left", expand=True, fill="both", padx=(0, 10))
        self.login_username = ttk.Entry(login_card)
        self.login_password = ttk.Entry(login_card, show="*")
        ttk.Label(login_card, text="Username").pack(anchor="w")
        self.login_username.pack(fill="x", pady=(0, 8))
        ttk.Label(login_card, text="Password").pack(anchor="w")
        self.login_password.pack(fill="x", pady=(0, 8))
        ttk.Button(login_card, text="Login", command=self._attempt_login, style="Section.TButton").pack(
            fill="x", pady=(6, 0)
        )
        ttk.Button(login_card, text="Back to Role Selection", command=self.controller.show_role_selection).pack(
            fill="x", pady=(8, 0)
        )

        register_card = ttk.LabelFrame(
            forms_container, text="Register New Account", padding=15, style="Card.TLabelframe"
        )
        register_card.pack(side="left", expand=True, fill="both", padx=(10, 0))
        self.register_username = ttk.Entry(register_card)
        self.register_password = ttk.Entry(register_card, show="*")
        ttk.Label(register_card, text="New Username").pack(anchor="w")
        self.register_username.pack(fill="x", pady=(0, 8))
        ttk.Label(register_card, text="New Password").pack(anchor="w")
        self.register_password.pack(fill="x", pady=(0, 8))
        ttk.Button(register_card, text="Register", command=self._attempt_register, style="Section.TButton").pack(
            fill="x", pady=(6, 0)
        )

    def set_role(self, role: str) -> None:
        self.role = role
        role_name = "Engineer" if role == "engineer" else "Admin"
        self.role_heading.config(text=f"{role_name} Login")

    def _attempt_login(self) -> None:
        username = self.login_username.get().strip()
        password = self.login_password.get().strip()
        if not username or not password:
            self.controller.set_status("Provide both username and password.")
            return
        self.controller.set_status(f"Logged in as {username} (placeholder).")
        if self.role == "engineer":
            self.controller.show_engineer_flow()
        else:
            self.controller.show_admin_flow()

    def _attempt_register(self) -> None:
        username = self.register_username.get().strip()
        password = self.register_password.get().strip()
        if len(username) < 3 or len(password) < 4:
            self.controller.set_status("Registration failed: username/password too short.")
            return
        self.controller.set_status(f"Registration successful for {username}. You can now log in.")


class EngineerFlowView(ttk.Frame):
    """Guides engineers through the GA extraction & reporting flow."""

    def __init__(self, parent: ttk.Frame, controller: InspectorApp) -> None:
        super().__init__(parent, padding=16)
        self.controller = controller
        self._build()

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)

        ttk.Button(
            self,
            text="⬅ Back to Role Selection",
            command=self.controller.show_role_selection,
            style="Section.TButton",
        ).pack(anchor="e")

        ttk.Label(
            self,
            text="Engineer Workflow",
            font=("Segoe UI", 14, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        self.step_container = ttk.Frame(self)
        self.step_container.pack(fill="both", expand=True, pady=10)

        self.step_frames: list[ttk.Frame] = []
        self._build_step_frames()

        nav = ttk.Frame(self)
        nav.pack(fill="x", pady=(5, 0))
        self.prev_btn = ttk.Button(nav, text="⟵ Back", command=self._prev_step, state="disabled")
        self.prev_btn.pack(side="left")
        self.next_btn = ttk.Button(nav, text="Next ⟶", command=self._next_step)
        self.next_btn.pack(side="right")

        self.current_step = 0
        self._show_step(0)

    def _build_step_frames(self) -> None:
        # Step 1: choose file
        frame1 = ttk.LabelFrame(self.step_container, text="Step 1 · Choose GA Drawing", padding=15)
        ttk.Label(
            frame1, text="Select the GA drawing.", wraplength=700
        ).pack(anchor="w")
        ttk.Button(frame1, text="Browse File…", command=self._choose_file, style="Section.TButton").pack(
            anchor="w", pady=(10, 4)
        )
        self.file_path_var = tk.StringVar(value="No file selected.")
        ttk.Label(frame1, textvariable=self.file_path_var, foreground="#555").pack(anchor="w")

        preview_wrapper = ttk.Frame(frame1)
        preview_wrapper.pack(fill="both", expand=True, pady=(10, 0))
        self.preview_canvas = tk.Canvas(preview_wrapper, height=220, bg="#f5f5f5", highlightthickness=1)
        self.preview_canvas.pack(side="left", fill="both", expand=True)
        ttk.Label(
            preview_wrapper,
            text="Preview uses PDF thumbnail (first page).",
            wraplength=180,
            justify="left",
        ).pack(side="left", padx=(10, 0))
        self.step_frames.append(frame1)

        # Step 2: extract data
        frame3 = ttk.LabelFrame(self.step_container, text="Step 2 · Extract Data", padding=15)
        ttk.Label(
            frame3,
            text="Launch GA extractor to pull fields from the validated file. Results preview below.",
            wraplength=700,
        ).pack(anchor="w")
        ttk.Button(frame3, text="Extract Now", command=self._extract_data, style="Section.TButton").pack(
            anchor="w", pady=(10, 4)
        )
        self.extract_preview = tk.Text(frame3, height=8)
        self.extract_preview.pack(fill="both", expand=True)
        self.step_frames.append(frame3)

        # Step 3: review/edit
        frame4 = ttk.LabelFrame(self.step_container, text="Step 3 · Review / Edit Result", padding=15)
        ttk.Label(
            frame4,
            text="Review extracted fields. Make adjustments before committing.",
            wraplength=700,
        ).pack(anchor="w")
        self.edit_notes = tk.Text(frame4, height=6)
        self.edit_notes.insert("end", "Notes / adjustments here…")
        self.edit_notes.pack(fill="both", expand=True, pady=(6, 6))
        ttk.Button(frame4, text="Mark Reviewed", command=self._edit_result, style="Section.TButton").pack(anchor="e")
        self.step_frames.append(frame4)

        # Step 4: save to DB
        frame5 = ttk.LabelFrame(self.step_container, text="Step 4 · Save to Database", padding=15)
        ttk.Label(
            frame5,
            text="Push the verified dataset to the central Autorbi database.",
            wraplength=700,
        ).pack(anchor="w")
        ttk.Button(frame5, text="Save Record", command=self._save_results, style="Section.TButton").pack(
            anchor="w", pady=(10, 4)
        )
        self.save_var = tk.StringVar(value="Record not saved yet.")
        ttk.Label(frame5, textvariable=self.save_var, foreground="#555").pack(anchor="w")
        self.step_frames.append(frame5)

        # Step 5: generate deliverables
        frame6 = ttk.LabelFrame(self.step_container, text="Step 5 · Generate Templates", padding=15)
        ttk.Label(
            frame6,
            text="Produce client-facing deliverables based on the saved dataset.",
            wraplength=700,
        ).pack(anchor="w")
        ttk.Button(frame6, text="Fill Excel Template", command=self._fill_templates, style="Section.TButton").pack(
            anchor="w", pady=(10, 4)
        )
        ttk.Button(frame6, text="Generate PowerPoint", command=self._fill_templates, style="Section.TButton").pack(
            anchor="w", pady=4
        )
        self.output_var = tk.StringVar(value="No documents generated yet.")
        ttk.Label(frame6, textvariable=self.output_var, foreground="#555").pack(anchor="w", pady=(6, 0))
        self.step_frames.append(frame6)

    def _show_step(self, index: int) -> None:
        for frame in self.step_frames:
            frame.pack_forget()
        self.step_frames[index].pack(fill="both", expand=True)
        self.prev_btn.config(state="normal" if index > 0 else "disabled")
        next_label = "Finish" if index == len(self.step_frames) - 1 else "Next ⟶"
        self.next_btn.config(text=next_label)

    def _next_step(self) -> None:
        if self.current_step < len(self.step_frames) - 1:
            self.current_step += 1
            self._show_step(self.current_step)
        else:
            self.controller.set_status("Engineer workflow complete.")

    def _prev_step(self) -> None:
        if self.current_step > 0:
            self.current_step -= 1
            self._show_step(self.current_step)

    def _choose_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Select GA drawing",
            filetypes=[("Drawing Files", "*.pdf *.tif *.tiff"), ("All Files", "*.*")],
        )
        if not path:
            self.controller.set_status("No file selected.")
            return
        self.selected_file = path
        self.controller.set_status(f"Selected GA drawing: {path}")
        self.file_path_var.set(path)
        self._render_preview(path)

    def _render_preview(self, path: str) -> None:
        self.preview_canvas.delete("all")
        if fitz is None:
            image = None
        else:
            try:
                doc = fitz.open(path)
                pix = doc.load_page(0).get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
                img_data = pix.tobytes("ppm")
                image = tk.PhotoImage(data=img_data)
            except Exception:
                image = None

        if image:
            self.preview_canvas.image = image  # keep reference
            self.preview_canvas.create_image(
                self.preview_canvas.winfo_width() / 2,
                self.preview_canvas.winfo_height() / 2,
                image=image,
            )
        else:
            self.preview_canvas.create_text(
                10,
                10,
                anchor="nw",
                text="Preview unavailable. Install PyMuPDF for PDF thumbnails.",
            )

    def _validate_file(self) -> None:
        if not getattr(self, "selected_file", None):
            self.controller.set_status("Select a file before validation.")
            return
        self.controller.set_status("File validated (placeholder).")
        self.validation_var.set("Validation complete (placeholder).")

    def _extract_data(self) -> None:
        self.controller.set_status("Extracting data (placeholder).")
        self.extract_preview.delete("1.0", "end")
        self.extract_preview.insert("end", "Field A: Value A\nField B: Value B\nField C: Value C\n")

    def _edit_result(self) -> None:
        self.controller.set_status("Editing results (placeholder).")
        # Assume edits stored

    def _save_results(self) -> None:
        self.controller.set_status("Results saved to database (placeholder).")
        self.save_var.set("Saved to database (placeholder).")

    def _fill_templates(self) -> None:
        self.controller.set_status("Excel and PPT templates filled (placeholder).")
        self.output_var.set("Excel/PPT generated (placeholder).")


class AdminFlowView(ttk.Frame):
    """Guided admin tasks: create user, update user, activate/deactivate."""

    def __init__(self, parent: ttk.Frame, controller: InspectorApp) -> None:
        super().__init__(parent, padding=16)
        self.controller = controller
        self._build()

    def _build(self) -> None:
        ttk.Button(
            self,
            text="⬅ Back to Role Selection",
            command=self.controller.show_role_selection,
            style="Section.TButton",
        ).pack(anchor="e")
        ttk.Label(
            self,
            text="Admin Module",
            font=("Segoe UI", 14, "bold"),
        ).pack(anchor="w", pady=(0, 10))

        tab_control = ttk.Notebook(self)
        tab_control.pack(fill="both", expand=True)

        create_tab = ttk.Frame(tab_control, padding=12)
        self._build_create_tab(create_tab)
        tab_control.add(create_tab, text="Create User")

        update_tab = ttk.Frame(tab_control, padding=12)
        self._build_update_tab(update_tab)
        tab_control.add(update_tab, text="Update User")

        activate_tab = ttk.Frame(tab_control, padding=12)
        self._build_toggle_tab(activate_tab)
        tab_control.add(activate_tab, text="Activate / Deactivate")

        list_tab = ttk.Frame(tab_control, padding=12)
        self._build_list_tab(list_tab)
        tab_control.add(list_tab, text="User List")

    # create tab
    def _build_create_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Input new username and password.").pack(anchor="w")
        self.create_username = ttk.Entry(parent)
        self.create_password = ttk.Entry(parent, show="*")
        ttk.Label(parent, text="Username").pack(anchor="w", pady=(8, 0))
        self.create_username.pack(fill="x")
        ttk.Label(parent, text="Password").pack(anchor="w", pady=(8, 0))
        self.create_password.pack(fill="x")
        ttk.Button(parent, text="Validate & Save", command=self._save_user).pack(fill="x", pady=12)

    def _build_update_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Retrieve and update an existing user.").pack(anchor="w")
        self.update_username = ttk.Entry(parent)
        ttk.Label(parent, text="Username to update").pack(anchor="w", pady=(8, 0))
        self.update_username.pack(fill="x")
        ttk.Button(parent, text="Retrieve Details", command=self._retrieve_user).pack(fill="x", pady=6)
        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=8)
        ttk.Label(parent, text="New Username").pack(anchor="w")
        self.new_username = ttk.Entry(parent)
        self.new_username.pack(fill="x")
        ttk.Label(parent, text="New Password").pack(anchor="w", pady=(8, 0))
        self.new_password = ttk.Entry(parent, show="*")
        self.new_password.pack(fill="x")
        ttk.Button(parent, text="Apply Updates", command=self._apply_updates).pack(fill="x", pady=10)

    def _build_toggle_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Activate or deactivate a user.").pack(anchor="w")
        self.toggle_username = ttk.Entry(parent)
        ttk.Label(parent, text="Username").pack(anchor="w", pady=(8, 0))
        self.toggle_username.pack(fill="x")
        ttk.Button(parent, text="Activate", command=lambda: self._toggle_user(True)).pack(fill="x", pady=6)
        ttk.Button(parent, text="Deactivate", command=lambda: self._toggle_user(False)).pack(fill="x")

    def _build_list_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Retrieve User List").pack(anchor="w")
        ttk.Button(parent, text="Refresh User List", command=self._list_users).pack(fill="x", pady=6)
        self.user_listbox = tk.Text(parent, height=10)
        self.user_listbox.pack(fill="both", expand=True)

    # Admin actions
    def _save_user(self) -> None:
        username = self.create_username.get().strip()
        password = self.create_password.get().strip()
        if len(username) < 3 or len(password) < 4:
            self.controller.set_status("Invalid username or password for new user.")
            return
        self.controller.set_status(f"User '{username}' created (placeholder).")

    def _retrieve_user(self) -> None:
        username = self.update_username.get().strip()
        if not username:
            self.controller.set_status("Provide a username to retrieve.")
            return
        self.controller.set_status(f"Retrieved details for '{username}' (placeholder).")

    def _apply_updates(self) -> None:
        new_username = self.new_username.get().strip()
        new_password = self.new_password.get().strip()
        if not new_username and not new_password:
            self.controller.set_status("No updates provided.")
            return
        self.controller.set_status("User information updated (placeholder).")

    def _toggle_user(self, activate: bool) -> None:
        username = self.toggle_username.get().strip()
        if not username:
            self.controller.set_status("Provide a username to toggle.")
            return
        state = "activated" if activate else "deactivated"
        self.controller.set_status(f"User '{username}' {state} (placeholder).")

    def _list_users(self) -> None:
        self.user_listbox.delete("1.0", "end")
        sample = ["inspector_a", "engineer_b", "admin_c"]
        for name in sample:
            self.user_listbox.insert("end", f"- {name}\n")
        self.controller.set_status("User list refreshed (placeholder).")


def main() -> None:
    app = InspectorApp()
    app.mainloop()


if __name__ == "__main__":
    main()

