from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QColor, QBrush, QPen, QFont
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem
import pandas as pd
from data import DAYS, SHIFTS, COMPETENCES, DEFAULT_CANDIDATES, DEMAND, default_availability
from scheduler import HiringScheduler


def parse_shift_times(shift_name):
    mapping = {
        "Matin": (8, 14, False),
        "Garde": (14, 8, True),  
    }
    return mapping.get(shift_name, (8, 16, False))


class WeekCalendarView(QGraphicsView):

    def __init__(self, days, periods, parent=None):
        super().__init__(parent)
        self.days = days
        self.periods = periods
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.TextAntialiasing)
        self.cell_width = 110
        self.hour_height = 10.0
        self.left_margin = 50
        self.top_margin = 24
        self.staff_colors = {}
        self.setMinimumHeight(int(self.top_margin + self.hour_height * 24 + 20))
        self.setMaximumHeight(320)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.mode = "WEEKLY"
        self.personal_staff = None

    def clear_scene(self):
        self.scene.clear()

    def assign_color(self, name):
        if name in self.staff_colors:
            return self.staff_colors[name]
        h = abs(hash(name)) % 360
        color = QColor.fromHsl(h, 140, 200)
        self.staff_colors[name] = color
        return color

    def draw_grid(self):
        self.clear_scene()
        days = self.days
        cols = len(days)
        total_width = self.left_margin + cols * self.cell_width
        total_height = self.top_margin + self.hour_height * 24 + 30
        rect = QtCore.QRectF(0, 0, total_width, total_height)
        self.scene.addRect(rect, QPen(QtCore.Qt.NoPen), QBrush(QColor(250, 250, 250)))
        font = QFont("Sans", 8)
        for i, d in enumerate(days):
            x = self.left_margin + i * self.cell_width
            header = QGraphicsTextItem(f"{d}")
            header.setFont(font)
            header.setPos(x + 6, 2)
            self.scene.addItem(header)
            pen = QPen(QColor(210, 210, 210))
            self.scene.addLine(x, self.top_margin, x, self.top_margin + 24 * self.hour_height, pen)
        x_end = self.left_margin + cols * self.cell_width
        self.scene.addLine(x_end, self.top_margin, x_end, self.top_margin + 24 * self.hour_height, QPen(QColor(210, 210, 210)))
        for hour in range(0, 25, 2):
            y = self.top_margin + hour * self.hour_height
            pen = QPen(QColor(230, 230, 230))
            self.scene.addLine(self.left_margin, y, self.left_margin + cols * self.cell_width, y, pen)
            t = QGraphicsTextItem(f"{hour:02d}h")
            t.setFont(QFont("Sans", 7))
            t.setPos(2, y - 7)
            self.scene.addItem(t)
        pen = QPen(QColor(180, 180, 180))
        self.scene.addRect(self.left_margin, self.top_margin, cols * self.cell_width, 24 * self.hour_height, pen)
        self.scene.setSceneRect(0, 0, total_width + 10, total_height + 10)

    def draw_assignments(self, assignments, staff_focus=None):
        self.draw_grid()
        days = self.days
        for t, names in assignments.items():
            if "_" not in t:
                continue
            d, p = t.split("_", 1)
            if d not in days:
                continue
            if staff_focus and all(staff_focus != n for n in names):
                continue
            start_h, end_h, wraps = parse_shift_times(p)
            col_idx = days.index(d)
            x = self.left_margin + col_idx * self.cell_width + 5
            width = self.cell_width - 10
            text = ", ".join(names)
            color = self.assign_color(text)
            if not wraps:
                y = self.top_margin + start_h * self.hour_height
                height = max(12.0, (end_h - start_h) * self.hour_height)
                rect = QGraphicsRectItem(x, y, width, height)
                rect.setBrush(QBrush(color))
                rect.setPen(QPen(QColor(80, 80, 80)))
                rect.setOpacity(0.9)
                self.scene.addItem(rect)
                txt = QGraphicsTextItem(text)
                txt.setDefaultTextColor(QtCore.Qt.white)
                txt.setFont(QFont("Sans", 8))
                txt.setPos(x + 4, y + 2)
                self.scene.addItem(txt)
                rect.setToolTip(f"{text}\n{d} {p}: {int(start_h)}:00 - {int(end_h)}:00")
            else:
                y1 = self.top_margin + start_h * self.hour_height
                h1 = (24.0 - start_h) * self.hour_height
                rect1 = QGraphicsRectItem(x, y1, width, h1)
                rect1.setBrush(QBrush(color))
                rect1.setPen(QPen(QColor(80, 80, 80)))
                rect1.setOpacity(0.9)
                self.scene.addItem(rect1)
                txt1 = QGraphicsTextItem(text)
                txt1.setDefaultTextColor(QtCore.Qt.white)
                txt1.setFont(QFont("Sans", 8))
                txt1.setPos(x + 4, y1 + 2)
                self.scene.addItem(txt1)
                rect1.setToolTip(f"{text}\n{d} {p}: {int(start_h)}:00 - 24:00")
                idx = days.index(d)
                next_idx = idx + 1
                if next_idx < len(days):
                    x2 = self.left_margin + next_idx * self.cell_width + 5
                    y2 = self.top_margin
                    h2 = end_h * self.hour_height
                    rect2 = QGraphicsRectItem(x2, y2, width, h2)
                    rect2.setBrush(QBrush(color))
                    rect2.setPen(QPen(QColor(80, 80, 80)))
                    rect2.setOpacity(0.9)
                    self.scene.addItem(rect2)
                    txt2 = QGraphicsTextItem(text)
                    txt2.setDefaultTextColor(QtCore.Qt.white)
                    txt2.setFont(QFont("Sans", 8))
                    txt2.setPos(x2 + 4, y2 + 2)
                    self.scene.addItem(txt2)
                    rect2.setToolTip(f"{text}\n{days[next_idx]} {p}: 00:00 - {int(end_h)}:00")

    def set_mode(self, mode, staff_name=None):
        self.mode = mode
        self.personal_staff = staff_name

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shift Scheduling")
        self.resize(1500,850)

        self.candidates = {c["id"]:c.copy() for c in DEFAULT_CANDIDATES}
        self.avail = default_availability(DEFAULT_CANDIDATES)
        self.demand = DEMAND.copy()
        self.assign_map = {}

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)

        header = QtWidgets.QLabel("Planification des quarts")
        header.setAlignment(QtCore.Qt.AlignCenter)
        header.setStyleSheet("font-size:18px; font-weight:bold; padding:10px; background:#0f4c75; color:white;")
        main_layout.addWidget(header)

        content = QtWidgets.QGridLayout()
        content.setColumnStretch(0, 3)
        content.setColumnStretch(1, 4)
        content.setRowStretch(0, 3)
        content.setRowStretch(1, 2)
        main_layout.addLayout(content, 1)


        grp = QtWidgets.QGroupBox("Gestion des candidats")
        left_layout = QtWidgets.QVBoxLayout(grp)
        left_layout.setSpacing(6)
        content.addWidget(grp, 0, 0)

        self.list_candidates = QtWidgets.QListWidget()
        left_layout.addWidget(self.list_candidates)
        self.refresh_candidate_list_items()

    
        form = QtWidgets.QFormLayout()
        self.input_id = QtWidgets.QLineEdit()
        self.input_name = QtWidgets.QLineEdit()
        self.chk_infirmier = QtWidgets.QCheckBox("Infirmier")
        self.chk_medecin = QtWidgets.QCheckBox("Medecin")
        self.input_hire_cost = QtWidgets.QLineEdit("1200")
        form.addRow("ID:", self.input_id)
        form.addRow("Nom:", self.input_name)
        form.addRow("", self.chk_infirmier)
        form.addRow("", self.chk_medecin)
        form.addRow("Coût embauche:", self.input_hire_cost)
        left_layout.addLayout(form)
        btn_add = QtWidgets.QPushButton("Ajouter")
        btn_remove = QtWidgets.QPushButton("Supprimer")
        for b in (btn_add, btn_remove):
            b.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        btn_add.clicked.connect(self.add_candidate)
        btn_remove.clicked.connect(self.remove_candidate)
        left_layout.addWidget(btn_add)
        left_layout.addWidget(btn_remove)

      
        demand_grp = QtWidgets.QGroupBox("Exigences")
        demand_layout = QtWidgets.QVBoxLayout(demand_grp)
        self.demand_table = QtWidgets.QTableWidget(len(DAYS), 4)
        self.demand_table.setHorizontalHeaderLabels(["Matin INF","Matin MED","Garde INF","Garde MED"])
        self.demand_table.setVerticalHeaderLabels(DAYS)
        for r,d in enumerate(DAYS):
            for c,(shift,comp) in enumerate([("Matin","infirmier"),("Matin","medecin"),("Garde","infirmier"),("Garde","medecin")]):
                item = QtWidgets.QTableWidgetItem(str(self.demand[d][shift][comp]))
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.demand_table.setItem(r,c,item)
        demand_layout.addWidget(self.demand_table)
        content.addWidget(demand_grp, 1, 0)

        right_top_widget = QtWidgets.QWidget()
        right_top = QtWidgets.QVBoxLayout(right_top_widget)
        right_top.setSpacing(6)

        solve_box = QtWidgets.QHBoxLayout()
        self.solve_btn = QtWidgets.QPushButton("Résoudre")
        self.solve_btn.setStyleSheet("font-weight:bold; font-size:14px; color:white; background-color:green; padding:8px 14px;")
        self.solve_btn.clicked.connect(self.solve_and_display)
        solve_box.addWidget(self.solve_btn, 0, QtCore.Qt.AlignLeft)
        self.status_lbl = QtWidgets.QLabel("Statut: prêt")
        solve_box.addWidget(self.status_lbl, 1, QtCore.Qt.AlignLeft)
        right_top.addLayout(solve_box)

        planning_grp = QtWidgets.QGroupBox("Planification des quarts")
        planning_layout = QtWidgets.QVBoxLayout(planning_grp)

        self.plan_tabs = QtWidgets.QTabWidget()
        self.plan_tabs.setTabPosition(QtWidgets.QTabWidget.North)

        # Vue équipe
        team_widget = QtWidgets.QWidget()
        team_layout = QtWidgets.QVBoxLayout(team_widget)
        self.plan_view = WeekCalendarView(DAYS, SHIFTS)
        team_layout.addWidget(self.plan_view)
        self.plan_tabs.addTab(team_widget, "Vue équipe")

        # Vue personnelle
        personal_widget = QtWidgets.QWidget()
        personal_layout = QtWidgets.QVBoxLayout(personal_widget)
        selector_layout = QtWidgets.QHBoxLayout()
        selector_layout.addWidget(QtWidgets.QLabel("Personnel:"))
        self.personal_combo = QtWidgets.QComboBox()
        selector_layout.addWidget(self.personal_combo, 1)
        selector_layout.addStretch()
        personal_layout.addLayout(selector_layout)
        self.personal_view = WeekCalendarView(DAYS, SHIFTS)
        personal_layout.addWidget(self.personal_view)
        self.plan_tabs.addTab(personal_widget, "Vue personnelle")

        self.plan_tabs.currentChanged.connect(self.update_personal_view)
        self.personal_combo.currentTextChanged.connect(self.update_personal_view)

        planning_layout.addWidget(self.plan_tabs)

        self.table = QtWidgets.QTableWidget(len(DAYS), len(SHIFTS))
        self.table.setHorizontalHeaderLabels(SHIFTS)
        self.table.setVerticalHeaderLabels(DAYS)
        self.table.setVisible(False)
        planning_layout.addWidget(self.table)
        right_top.addWidget(planning_grp, 1)

        content.addWidget(right_top_widget, 0, 1)

        right_bottom_widget = QtWidgets.QWidget()
        right_bottom = QtWidgets.QVBoxLayout(right_bottom_widget)
        right_bottom.setSpacing(6)

        hired_grp = QtWidgets.QGroupBox("Resultats des embauches")
        hired_layout = QtWidgets.QVBoxLayout(hired_grp)
        self.hired_list = QtWidgets.QListWidget()
        hired_layout.addWidget(self.hired_list)
        self.stats_lbl = QtWidgets.QLabel("Nombre total: INF=0 | MED=0")
        self.stats_lbl.setStyleSheet("font-weight:bold; font-size:13px; color:blue;")
        hired_layout.addWidget(self.stats_lbl)
        btn_export = QtWidgets.QPushButton("Exporter CSV")
        btn_export.clicked.connect(self.export_csv)
        hired_layout.addWidget(btn_export)
        right_bottom.addWidget(hired_grp)

        log_grp = QtWidgets.QGroupBox("Diagnostic IIS")
        log_layout = QtWidgets.QVBoxLayout(log_grp)
        self.log_box = QtWidgets.QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet("background:#f7f9fb;")
        log_layout.addWidget(self.log_box)
        right_bottom.addWidget(log_grp)

        content.addWidget(right_bottom_widget, 1, 1)

        self.refresh_candidate_list()

    def append_log(self, text):
        self.log_box.append(text)

    def show_diagnostics(self, messages):
        if not messages:
            self.log_box.setPlainText("Aucun détail de diagnostic disponible.")
            return
        html = "<ul>" + "".join(f"<li>{m}</li>" for m in messages) + "</ul>"
        self.log_box.setHtml(html)

    def refresh_candidate_list_items(self):
        self.list_candidates.clear()
        for cid,c in sorted(self.candidates.items()):
            quals=[]
            if c["qual"].get("infirmier",0): quals.append("INF")
            if c["qual"].get("medecin",0): quals.append("MED")
            self.list_candidates.addItem(f"{cid} - {c['name']} ({','.join(quals)}) - cost={c['hire_cost']}")

    def refresh_candidate_list(self):
        self.refresh_candidate_list_items()
        if hasattr(self, 'personal_combo'):
            current = self.personal_combo.currentText()
            self.personal_combo.blockSignals(True)
            self.personal_combo.clear()
            for cid,c in sorted(self.candidates.items()):
                self.personal_combo.addItem(c["name"], cid)
            if self.personal_combo.count() > 0:
                if current and any(self.personal_combo.itemText(i) == current for i in range(self.personal_combo.count())):
                    self.personal_combo.setCurrentText(current)
                else:
                    self.personal_combo.setCurrentIndex(0)
            self.personal_combo.blockSignals(False)
            self.update_personal_view()

    def add_candidate(self):
        cid = self.input_id.text().strip()
        name = self.input_name.text().strip() or cid
        if not cid or cid in self.candidates:
            QtWidgets.QMessageBox.warning(self,"Erreur","ID invalide ou déjà présent")
            return
        qual = {"infirmier":int(self.chk_infirmier.isChecked()),"medecin":int(self.chk_medecin.isChecked())}
        try: hire_cost=float(self.input_hire_cost.text())
        except: hire_cost=1200
        self.candidates[cid]={"id":cid,"name":name,"qual":qual,"hire_cost":hire_cost,"shift_cost":{"Matin":80,"Garde":120}}
        self.avail[cid]={d:1 for d in DAYS}
        self.refresh_candidate_list()

    def remove_candidate(self):
        sel = self.list_candidates.currentItem()
        if sel:
            cid = sel.text().split(" - ")[0]
            if cid in self.candidates: del self.candidates[cid]
            if cid in self.avail: del self.avail[cid]
            self.refresh_candidate_list()

    def solve_and_display(self):
        for r,d in enumerate(DAYS):
            for c,(shift,comp) in enumerate([("Matin","infirmier"),("Matin","medecin"),("Garde","infirmier"),("Garde","medecin")]):
                try: val=int(self.demand_table.item(r,c).text())
                except: val=0
                self.demand[d][shift][comp]=max(0,val)

        candidates_list=[self.candidates[k] for k in sorted(self.candidates.keys())]
        scheduler = HiringScheduler(candidates=candidates_list,demand=self.demand,availability=self.avail)
        self.status_lbl.setText("Résolution en cours...")
        QtWidgets.QApplication.processEvents()
        res = scheduler.solve(time_limit=60, verbose=False)

        if not res or res.get("status") in ("infeasible","infeasible_or_unbounded"):
            iis = res.get("iis",[]) if res else []
            msgs = res.get("messages",[]) if res else []
            msg = "Modèle infaisable."
            if iis:
                msg += " Voir détails ci-dessous."
            else:
                msg += " Impossible d'identifier les contraintes actives."
            self.status_lbl.setText(msg)
            QtWidgets.QMessageBox.warning(self,"In faisable",msg)
            self.show_diagnostics(msgs if msgs else iis)
            return
        if res.get("status","") not in ("optimal","suboptimal","time_limit"):
            self.status_lbl.setText(f"Résolution interrompue (statut={res.get('status')})")
            self.append_log(self.status_lbl.text())
            return

        for r in range(len(DAYS)):
            for c in range(len(SHIFTS)):
                self.table.setItem(r,c,QtWidgets.QTableWidgetItem(""))

        for (d,s),emps in res["assigns"].items():
            r=DAYS.index(d); c=SHIFTS.index(s)
            names=[next((emp for emp in candidates_list if emp["id"]==eid),{"name":eid})["name"] for eid in emps]
            self.table.setItem(r,c,QtWidgets.QTableWidgetItem(", ".join(names)))
        self.assign_map = {f"{d}_{s}":[next((emp for emp in candidates_list if emp["id"]==eid),{"name":eid})["name"] for eid in emps]
                           for (d,s),emps in res["assigns"].items()}
        self.plan_view.draw_assignments(self.assign_map)
        self.update_personal_view()

        self.hired_list.clear()
        for eid in res["hired"]:
            emp=next((emp for emp in candidates_list if emp["id"]==eid),{"name":eid})
            self.hired_list.addItem(f"{eid} - {emp['name']} - cost {emp.get('hire_cost',0)}")

        self.stats_lbl.setText(f"Nombre total embauchés: INF={res['total_infirmiers']} | MED={res['total_medecins']}")
        self.status_lbl.setText(f"Résolution terminée — coût total={res['objective']:.1f}")
        self.append_log(f"Statut: {res.get('status')} | Coût={res.get('objective'):.1f}")

    def export_csv(self):
        rows=[]
        for d in DAYS:
            for s in SHIFTS:
                item=self.table.item(DAYS.index(d),SHIFTS.index(s))
                val=item.text() if item else ""
                rows.append({"day":d,"shift":s,"assigned":val})
        df=pd.DataFrame(rows)
        fname,_=QtWidgets.QFileDialog.getSaveFileName(self,"Enregistrer CSV","planning.csv","CSV Files (*.csv)")
        if fname: df.to_csv(fname,index=False)

    def update_personal_view(self, *args):
        if not hasattr(self, 'plan_tabs') or not hasattr(self, 'personal_combo') or not hasattr(self, 'personal_view'):
            return
        if self.plan_tabs.currentIndex() != 1:
            return
        staff_name = self.personal_combo.currentText()
        if not hasattr(self, 'assign_map') or not self.assign_map:
            self.personal_view.clear_scene()
            self.personal_view.draw_grid()
            return
        self.personal_view.draw_assignments(self.assign_map, staff_focus=staff_name)
