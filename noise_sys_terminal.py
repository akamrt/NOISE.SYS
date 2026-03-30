import maya.cmds as cmds
import maya.api.OpenMaya as om
import math
import json
import os
import random

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

# --- PREFERENCES PATH ---
PREFS_FILE = os.path.join(cmds.internalVar(userPrefDir=True), "noise_sys_prefs.json")

def load_prefs():
    if os.path.exists(PREFS_FILE):
        try:
            with open(PREFS_FILE, 'r') as f: return json.load(f)
        except Exception: pass
    return {"presets": {}, "last_state": None}

def save_prefs(prefs):
    try:
        with open(PREFS_FILE, 'w') as f: json.dump(prefs, f, indent=2)
    except Exception as e:
        om.MGlobal.displayWarning(f"NOISE.SYS: Failed to save prefs: {str(e)}")

# --- MATH HELPERS ---
def pseudo_perlin(x):
    return (math.sin(x) + math.sin(x * 2.2 + 1.52) + math.sin(x * 4.3 + 0.3)) / 3.0

def get_noise_val(t, ntype):
    if ntype == 'SQUARE': return 1.0 if math.sin(t) >= 0 else -1.0
    if ntype == 'TRIANGLE': return (2.0 / math.pi) * math.asin(max(-1, min(1, math.sin(t))))
    if ntype == 'SAW': return 2.0 * (t / (2.0 * math.pi) - math.floor(0.5 + t / (2.0 * math.pi)))
    if ntype == 'PERLIN': return pseudo_perlin(t)
    if ntype == 'RANDOM': return random.uniform(-1.0, 1.0)
    return math.sin(t)

NOISE_TYPES = ['SINE', 'SQUARE', 'TRIANGLE', 'SAW', 'PERLIN', 'RANDOM']

# --- PIXEL ICON DATA (5 rows each) ---
ICONS = {
    'A': [[0,1,1,0],[1,0,0,1],[1,1,1,1],[1,0,0,1],[1,0,0,1]],
    'B': [[1,1,1,0],[1,0,0,1],[1,1,1,0],[1,0,0,1],[1,1,1,0]],
    'C': [[0,1,1,1],[1,0,0,0],[1,0,0,0],[1,0,0,0],[0,1,1,1]],
    'D': [[1,1,1,0],[1,0,0,1],[1,0,0,1],[1,0,0,1],[1,1,1,0]],
    'E': [[1,1,1,1],[1,0,0,0],[1,1,1,0],[1,0,0,0],[1,1,1,1]],
    'F': [[1,1,1,1],[1,0,0,0],[1,1,1,0],[1,0,0,0],[1,0,0,0]],
    'G': [[0,1,1,1,0],[1,0,0,0,0],[1,0,1,1,1],[1,0,0,0,1],[0,1,1,1,0]],
    'H': [[1,0,0,1],[1,0,0,1],[1,1,1,1],[1,0,0,1],[1,0,0,1]],
    'I': [[1,1,1],[0,1,0],[0,1,0],[0,1,0],[1,1,1]],
    'K': [[1,0,0,1],[1,0,1,0],[1,1,0,0],[1,0,1,0],[1,0,0,1]],
    'L': [[1,0,0,0],[1,0,0,0],[1,0,0,0],[1,0,0,0],[1,1,1,1]],
    'M': [[1,0,0,0,1],[1,1,0,1,1],[1,0,1,0,1],[1,0,0,0,1],[1,0,0,0,1]],
    'N': [[1,0,0,1],[1,1,0,1],[1,0,1,1],[1,0,0,1],[1,0,0,1]],
    'O': [[0,1,1,0],[1,0,0,1],[1,0,0,1],[1,0,0,1],[0,1,1,0]],
    'P': [[1,1,1,0],[1,0,0,1],[1,1,1,0],[1,0,0,0],[1,0,0,0]],
    'R': [[1,1,1,0,0],[1,0,0,1,0],[1,1,1,0,0],[1,0,1,0,0],[1,0,0,1,0]],
    'S': [[0,1,1,1],[1,0,0,0],[0,1,1,0],[0,0,0,1],[1,1,1,0]],
    'T': [[1,1,1,1,1],[0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0]],
    'U': [[1,0,0,1],[1,0,0,1],[1,0,0,1],[1,0,0,1],[0,1,1,0]],
    'X': [[1,0,0,0,1],[0,1,0,1,0],[0,0,1,0,0],[0,1,0,1,0],[1,0,0,0,1]],
    'Y': [[1,0,0,0,1],[0,1,0,1,0],[0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0]],
    'Z': [[1,1,1,1,1],[0,0,0,1,0],[0,0,1,0,0],[0,1,0,0,0],[1,1,1,1,1]],
}

# --- COLORS ---
C = {
    'bg': '#05060a', 'panel': '#0a0c12', 'cyan': '#00f3ff', 'pink': '#ff00ea',
    'orange': '#f6a226', 'red': '#ff4444', 'green': '#55ff55', 'blue': '#55aaff',
    'axis_red': '#ff5555', 'axis_green': '#55ff55', 'axis_blue': '#55aaff',
    'white': '#e0e7ff', 'border': 'rgba(0,243,255,0.15)',
}

# --- QSS (CRT Synthesizer Aesthetic) ---
QSS = """
QWidget { background-color: #05060a; color: #e0e7ff; font-family: "Consolas", "Courier New", monospace; font-size: 10px; }
QMainWindow { background-color: #05060a; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: #05060a; width: 6px; border: none; }
QScrollBar::handle:vertical { background: rgba(0,243,255,0.2); min-height: 20px; border-radius: 3px; }
QScrollBar::handle:vertical:hover { background: rgba(0,243,255,0.4); }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QPushButton {
    background-color: rgba(0,243,255,0.03); border: 1px solid rgba(0,243,255,0.2);
    color: #00f3ff; padding: 3px 6px; font-family: "Consolas"; font-size: 9px;
    text-transform: uppercase; letter-spacing: 1px;
}
QPushButton:hover { background-color: rgba(0,243,255,0.15); }
QPushButton#soloActive { background-color: rgba(246,162,38,0.2); border-color: #f6a226; color: #f6a226; }
QPushButton#muteActive { background-color: rgba(255,68,68,0.2); border-color: #ff4444; color: #ff4444; }
QPushButton#bakeBase { border-color: rgba(246,162,38,0.5); color: #f6a226; font-size: 11px; padding: 6px; }
QPushButton#bakeBase:hover { background-color: rgba(246,162,38,0.15); }
QPushButton#bakeLayer { border-color: rgba(255,0,234,0.5); color: #ff00ea; font-size: 11px; padding: 6px; }
QPushButton#bakeLayer:hover { background-color: rgba(255,0,234,0.15); }
QPushButton#revertBtn { border-color: rgba(255,68,68,0.3); color: rgba(255,68,68,0.4); font-size: 8px; border: none; }
QPushButton#revertBtn:hover { color: #ff4444; }
QPushButton#addLayer { background: transparent; border: 1px dashed rgba(0,243,255,0.15); color: rgba(0,243,255,0.3); }
QPushButton#addLayer:hover { border-color: rgba(0,243,255,0.4); color: #00f3ff; background: rgba(0,243,255,0.05); }
QPushButton#delBtn { border: 1px solid rgba(255,68,68,0.15); color: rgba(255,68,68,0.4); }
QPushButton#delBtn:hover { border-color: #ff4444; color: #ff4444; background: rgba(255,68,68,0.1); }
QPushButton#autoLiveOn { background-color: rgba(0,243,255,0.1); border-color: #00f3ff; color: #00f3ff; }
QComboBox { background-color: rgba(5,8,15,0.9); border: 1px solid rgba(0,243,255,0.15); color: #00f3ff; padding: 2px 4px; font-size: 9px; }
QComboBox::drop-down { border: none; width: 14px; }
QComboBox QAbstractItemView { background: #0a0c12; color: #00f3ff; selection-background-color: rgba(0,243,255,0.15); border: 1px solid rgba(0,243,255,0.2); }
QLineEdit { background-color: rgba(0,0,0,0.6); border: 1px solid rgba(246,162,38,0.3); color: #f6a226; padding: 2px 6px; font-size: 10px; }
QLabel { background: transparent; color: rgba(255,255,255,0.4); font-size: 9px; }
QLabel#groupLabel { color: rgba(255,255,255,0.15); letter-spacing: 3px; font-size: 9px; }
"""


# --- PIXEL DOT-MATRIX SLIDER ---
class PixelSlider(QtWidgets.QWidget):
    valueChanged = QtCore.Signal(float)

    def __init__(self, label="", color_fill="#00f3ff", color_empty="#002233", icons=None,
                 vmin=0.0, vmax=1.0, vdefault=0.0, parent=None):
        super().__init__(parent)
        self._value = vdefault
        self._min, self._max = vmin, vmax
        self._color_fill = QtGui.QColor(color_fill)
        self._color_empty = QtGui.QColor(color_empty)
        self._color_icon_dark = QtGui.QColor(0, 0, 0, 180)
        self._icons = icons or []
        self._label = label
        self._dragging = False
        self._flash_active = False
        self._flash_frames = 0
        self._flash_timer = QtCore.QTimer(self)
        self._flash_timer.setSingleShot(True)
        self._flash_timer.timeout.connect(self._start_flash)
        self.COLS, self.ROWS = 64, 13
        self.setFixedHeight(26)
        self.setMinimumWidth(100)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        # Only used during flash animation — NOT started by default
        self._anim_timer = QtCore.QTimer(self)
        self._anim_timer.timeout.connect(self._tick_flash)
        # Pre-cache icon pixel set for O(1) lookups
        self._icon_set = self._build_icon_set()

    def _build_icon_set(self):
        """Pre-compute a set of (row, col) pairs that are icon pixels."""
        result = set()
        icons = self._icons
        if len(icons) == 3:
            left_col = 2
            for i in range(2):
                icon = ICONS.get(icons[i])
                if not icon: continue
                start_r = (self.ROWS - len(icon)) // 2
                for ir, row in enumerate(icon):
                    for ic, px in enumerate(row):
                        if px == 1: result.add((start_r + ir, left_col + ic))
                left_col += len(icon[0]) + 1
            right_icon = ICONS.get(icons[2])
            if right_icon:
                right_col = self.COLS - len(right_icon[0]) - 2
                start_r = (self.ROWS - len(right_icon)) // 2
                for ir, row in enumerate(right_icon):
                    for ic, px in enumerate(row):
                        if px == 1: result.add((start_r + ir, right_col + ic))
        elif len(icons) == 2:
            left_col = self.COLS // 2 - 5
            for icon_key in icons:
                icon = ICONS.get(icon_key)
                if not icon: continue
                start_r = (self.ROWS - len(icon)) // 2
                for ir, row in enumerate(icon):
                    for ic, px in enumerate(row):
                        if px == 1: result.add((start_r + ir, left_col + ic))
                left_col += len(icon[0]) + 1
        return result

    def value(self): return self._value
    def setValue(self, v):
        self._value = max(self._min, min(self._max, v))
        self.update()

    def _start_flash(self):
        self._flash_active = True
        self._flash_frames = 0
        self._anim_timer.start(16)  # Start 60fps only during flash

    def _tick_flash(self):
        self._flash_frames += 1
        if self._flash_frames > 36:
            self._flash_active = False
            self._anim_timer.stop()  # Stop timer when flash ends
        self.update()

    def mousePressEvent(self, e):
        self._dragging = True
        self._handle_drag(e)

    def mouseMoveEvent(self, e):
        if self._dragging: self._handle_drag(e)

    def mouseReleaseEvent(self, e):
        self._dragging = False
        self._flash_timer.start(1500)

    def _handle_drag(self, e):
        pos = max(0.0, min(1.0, e.pos().x() / self.width()))
        new_val = self._min + pos * (self._max - self._min)
        if new_val != self._value:
            self._value = new_val
            self.valueChanged.emit(self._value)
            self.update()
            self._flash_timer.start(1500)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, QtGui.QColor(0, 0, 0, 150))

        cell_w = w / self.COLS
        cell_h = h / self.ROWS
        dot_r = min(cell_w, cell_h) * 0.42
        norm = (self._value - self._min) / max(0.001, self._max - self._min)
        fill_w = w * norm

        show_icons = True
        if self._flash_active:
            if (self._flash_frames // 6) % 2 == 0:
                show_icons = False

        icon_set = self._icon_set
        cf, ce, cd = self._color_fill, self._color_empty, self._color_icon_dark
        painter.setPen(QtCore.Qt.NoPen)

        for r in range(self.ROWS):
            y = r * cell_h + cell_h / 2
            for c in range(self.COLS):
                x = c * cell_w + cell_w / 2
                is_icon = show_icons and (r, c) in icon_set
                is_filled = x <= fill_w

                if is_icon:
                    painter.setBrush(cd if is_filled else cf)
                else:
                    painter.setBrush(cf if is_filled else ce)
                painter.drawEllipse(QtCore.QPointF(x, y), dot_r, dot_r)
        painter.end()


# --- VISUALIZER ---
class VisualizerWidget(QtWidgets.QWidget):
    def __init__(self, main_ui, parent=None):
        super().__init__(parent)
        self.main_ui = main_ui
        self.setFixedHeight(100)
        self.time_offset = 0.0
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(33)

    def _tick(self):
        self.time_offset += 0.05
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Background
        painter.fillRect(0, 0, w, h, QtGui.QColor(5, 6, 10))

        # Grid
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 243, 255, 12), 1))
        for i in range(0, w, 25): painter.drawLine(i, 0, i, h)
        for i in range(0, h, 25): painter.drawLine(0, i, w, i)
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 243, 255, 38), 1))
        painter.drawLine(0, h // 2, w, h // 2)

        g_amp = self.main_ui.get_global_amp()
        g_freq = self.main_ui.get_global_freq()
        solo_ch = self.main_ui.solo_channel
        solo_lyr = self.main_ui.solo_layer_id

        for ch_name, ch_widget in self.main_ui.channels.items():
            if solo_ch and solo_ch != ch_name: continue
            if ch_widget.is_muted(): continue
            axis = ch_name[-1].lower()
            color = QtGui.QColor(C['axis_red'] if axis == 'x' else C['axis_green'] if axis == 'y' else C['axis_blue'])
            pen = QtGui.QPen(color, 2)
            painter.setPen(pen)

            path = QtGui.QPainterPath()
            layers = ch_widget.get_layers_objects()
            if not layers: continue

            # Sample every 2 pixels for performance, interpolation via lineTo is smooth enough
            for x in range(0, w, 2):
                t_base = (x * 0.04) + self.time_offset
                y_sum = 0
                for lyr_w in layers:
                    lyr = lyr_w.get_data()
                    if solo_lyr and lyr_w.id != solo_lyr: continue
                    t = t_base * (lyr['freq'] * g_freq) + lyr['offset']
                    y_sum += get_noise_val(t, lyr['type']) * (lyr['amp'] * g_amp * 30.0)
                if x == 0: path.moveTo(x, h / 2 - y_sum)
                else: path.lineTo(x, h / 2 - y_sum)
            painter.drawPath(path)

        # CRT scanlines
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 40), 1))
        for i in range(0, h, 2): painter.drawLine(0, i, w, i)
        painter.end()


# --- NOISE TYPE SELECTOR ---
class NoiseTypeSelector(QtWidgets.QWidget):
    typeChanged = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(1)
        self._buttons = {}
        self._current = 'SINE'
        for t in NOISE_TYPES:
            btn = QtWidgets.QPushButton(t)
            btn.setFixedHeight(16)
            btn.setStyleSheet(self._btn_style(False))
            # Use factory to capture nt value per-iteration (avoids late-binding closure bug)
            def make_handler(nt): return lambda _: self._select(nt)
            btn.clicked.connect(make_handler(t))
            lay.addWidget(btn)
            self._buttons[t] = btn
        self._buttons['SINE'].setStyleSheet(self._btn_style(True))

    def _btn_style(self, active):
        if active:
            return "QPushButton { background: rgba(0,243,255,0.15); border: 1px solid #00f3ff; color: #00f3ff; font-size: 8px; padding: 1px 3px; }"
        return "QPushButton { background: rgba(0,243,255,0.03); border: 1px solid rgba(0,243,255,0.1); color: rgba(0,243,255,0.4); font-size: 8px; padding: 1px 3px; }"

    def _select(self, ntype):
        self._current = ntype
        for t, btn in self._buttons.items():
            btn.setStyleSheet(self._btn_style(t == ntype))
        self.typeChanged.emit(ntype)

    def currentType(self): return self._current
    def setType(self, t):
        self._current = t
        for tn, btn in self._buttons.items():
            btn.setStyleSheet(self._btn_style(tn == t))


# --- LAYER WIDGET ---
class LayerWidget(QtWidgets.QFrame):
    def __init__(self, main_ui, ch_prefix='T', ch_axis='X', parent=None):
        super().__init__(parent)
        self.main_ui = main_ui
        self.id = str(random.random())
        self.setStyleSheet("QFrame { background: rgba(5,8,15,0.8); border: 1px solid rgba(0,243,255,0.08); }")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # Header
        header = QtWidgets.QHBoxLayout()
        self.type_sel = NoiseTypeSelector()
        self.type_sel.typeChanged.connect(lambda _: self.main_ui.auto_apply_expression())
        self.solo_btn = QtWidgets.QPushButton("S")
        self.solo_btn.setFixedSize(18, 16)
        self.solo_btn.clicked.connect(self.toggle_solo)
        self.del_btn = QtWidgets.QPushButton("DEL")
        self.del_btn.setObjectName("delBtn")
        self.del_btn.setFixedSize(28, 16)
        self.del_btn.clicked.connect(self.delete_layer)
        header.addWidget(self.type_sel)
        header.addWidget(self.solo_btn)
        header.addWidget(self.del_btn)
        layout.addLayout(header)

        # Sliders
        self.amp_slider = PixelSlider("AMP", "#00f3ff", "#002233", [ch_prefix, ch_axis, 'A'], 0, 3.0, 0.1)
        self.freq_slider = PixelSlider("FRQ", "#ff00ea", "#330022", [ch_prefix, ch_axis, 'F'], 0, 20.0, 2.0)
        self.offset_slider = PixelSlider("OFS", "#f6a226", "#332200", [ch_prefix, ch_axis, 'O'], 0, 10.0, 0.0)
        for s in [self.amp_slider, self.freq_slider, self.offset_slider]:
            s.valueChanged.connect(lambda _: self.main_ui.auto_apply_expression())

        for lbl_text, slider in [("AMP", self.amp_slider), ("FRQ", self.freq_slider), ("OFS", self.offset_slider)]:
            row = QtWidgets.QHBoxLayout()
            row.setSpacing(4)
            lbl = QtWidgets.QLabel(lbl_text)
            lbl.setFixedWidth(28)
            self.val_label = QtWidgets.QLabel(f"{slider.value():.2f}")
            self.val_label.setFixedWidth(32)
            self.val_label.setStyleSheet(f"color: {slider._color_fill.name()}; font-size: 9px;")
            slider.valueChanged.connect(lambda v, vl=self.val_label: vl.setText(f"{v:.2f}"))
            row.addWidget(lbl)
            row.addWidget(self.val_label)
            row.addWidget(slider)
            layout.addLayout(row)

    def toggle_solo(self): self.main_ui.set_solo_layer(self.id)
    def update_solo_visual(self, is_solo):
        self.solo_btn.setObjectName("soloActive" if is_solo else "")
        self.solo_btn.setStyle(self.solo_btn.style())

    def delete_layer(self):
        if self.main_ui.solo_layer_id == self.id: self.main_ui.set_solo_layer(None)
        self.deleteLater()
        QtCore.QTimer.singleShot(50, self.main_ui.auto_apply_expression)

    def get_data(self):
        return {'type': self.type_sel.currentType(), 'amp': self.amp_slider.value(),
                'freq': self.freq_slider.value(), 'offset': self.offset_slider.value()}

    def set_data(self, data):
        self.type_sel.setType(data.get('type', 'SINE'))
        self.amp_slider.setValue(data.get('amp', 0.1))
        self.freq_slider.setValue(data.get('freq', 2.0))
        self.offset_slider.setValue(data.get('offset', 0.0))


# --- CHANNEL WIDGET ---
class ChannelWidget(QtWidgets.QFrame):
    def __init__(self, name, main_ui, parent=None):
        super().__init__(parent)
        self.main_ui, self.name, self.muted = main_ui, name, False
        self._prefix = 'T' if name[0] == 'T' else 'R'
        self._axis = name[1].upper()
        axis_l = self._axis.lower()
        border_color = C['axis_red'] if axis_l == 'x' else C['axis_green'] if axis_l == 'y' else C['axis_blue']
        self._border_color = border_color
        self.setStyleSheet(f"QFrame {{ background: rgba(10,12,18,0.9); border: 1px solid rgba(0,243,255,0.15); border-left: 2px solid {border_color}; }}")
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(6, 4, 6, 4)
        self.layout.setSpacing(2)

        # Header
        h_lay = QtWidgets.QHBoxLayout()
        self.status_label = QtWidgets.QLabel(f"{name}_ACTIVE")
        self.status_label.setStyleSheet(f"color: {border_color}; font-size: 10px; font-weight: bold; letter-spacing: 2px;")
        self.solo_btn = QtWidgets.QPushButton("S")
        self.solo_btn.setFixedSize(20, 18)
        self.solo_btn.clicked.connect(self.toggle_solo)
        self.mute_btn = QtWidgets.QPushButton("MUTE")
        self.mute_btn.setFixedSize(36, 18)
        self.mute_btn.clicked.connect(self.toggle_mute)
        h_lay.addWidget(self.status_label)
        h_lay.addStretch()
        h_lay.addWidget(self.solo_btn)
        h_lay.addWidget(self.mute_btn)
        self.layout.addLayout(h_lay)

        # Layers container
        self.layers_container = QtWidgets.QWidget()
        self.layers_lay = QtWidgets.QVBoxLayout(self.layers_container)
        self.layers_lay.setContentsMargins(0, 0, 0, 0)
        self.layers_lay.setSpacing(4)
        self.layout.addWidget(self.layers_container)

        # Add layer button
        self.add_btn = QtWidgets.QPushButton("+ ADD LAYER")
        self.add_btn.setObjectName("addLayer")
        self.add_btn.clicked.connect(self.add_layer)
        self.layout.addWidget(self.add_btn)

    def toggle_solo(self): self.main_ui.set_solo_channel(self.name)
    def update_solo_visual(self, is_solo):
        self.solo_btn.setObjectName("soloActive" if is_solo else "")
        self.solo_btn.setStyle(self.solo_btn.style())
        if is_solo:
            self.status_label.setText("ISOLATED")
            self.status_label.setStyleSheet("color: #f6a226; font-size: 10px; font-weight: bold; letter-spacing: 2px;")
        elif not self.muted:
            self.status_label.setText(f"{self.name}_ACTIVE")
            self.status_label.setStyleSheet(f"color: {self._border_color}; font-size: 10px; font-weight: bold; letter-spacing: 2px;")

    def add_layer(self):
        lyr = LayerWidget(self.main_ui, self._prefix, self._axis)
        self.layers_lay.addWidget(lyr)
        self.main_ui.auto_apply_expression()

    def add_layer_with_data(self, data):
        lyr = LayerWidget(self.main_ui, self._prefix, self._axis)
        lyr.set_data(data)
        self.layers_lay.addWidget(lyr)

    def clear_layers(self):
        for i in reversed(range(self.layers_lay.count())):
            w = self.layers_lay.itemAt(i).widget()
            if w: w.setParent(None); w.deleteLater()

    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
            self.mute_btn.setObjectName("muteActive")
            self.mute_btn.setText("ON")
            self.status_label.setText("INACTIVE")
            self.status_label.setStyleSheet("color: #ff4444; font-size: 10px; font-weight: bold; letter-spacing: 2px;")
            self.layers_container.hide()
            self.add_btn.hide()
            self.setStyleSheet(f"QFrame {{ background: rgba(25,8,8,0.95); border: 1px solid rgba(0,243,255,0.15); border-left: 2px solid rgba(255,68,68,0.6); }}")
        else:
            self.mute_btn.setObjectName("")
            self.mute_btn.setText("MUTE")
            self.status_label.setText(f"{self.name}_ACTIVE")
            self.status_label.setStyleSheet(f"color: {self._border_color}; font-size: 10px; font-weight: bold; letter-spacing: 2px;")
            self.layers_container.show()
            self.add_btn.show()
            self.setStyleSheet(f"QFrame {{ background: rgba(10,12,18,0.9); border: 1px solid rgba(0,243,255,0.15); border-left: 2px solid {self._border_color}; }}")
        self.mute_btn.setStyle(self.mute_btn.style())
        self.main_ui.auto_apply_expression()

    def is_muted(self): return self.muted
    def get_layers_objects(self):
        return [self.layers_lay.itemAt(i).widget() for i in range(self.layers_lay.count()) if self.layers_lay.itemAt(i).widget()]
    def get_layers(self): return [o.get_data() for o in self.get_layers_objects()]
    def get_base_value(self): return 0.0


# --- MAIN WINDOW ---
class NoiseSysWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NOISE.SYS // JITTER MATRIX")
        self.setMinimumWidth(360); self.resize(380, 850)
        self.setStyleSheet(QSS)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self._block_auto, self.solo_channel, self.solo_layer_id = True, None, None
        self.prefs = load_prefs()
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(4)

        # Header
        header = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("NOISE.SYS")
        title.setStyleSheet("color: white; font-size: 22px; font-weight: bold; letter-spacing: -1px;")
        ver = QtWidgets.QLabel("V2.5_CORE")
        ver.setStyleSheet("color: rgba(255,255,255,0.3); font-size: 8px;")
        header.addWidget(title); header.addStretch(); header.addWidget(ver)
        main_layout.addLayout(header)

        # Separator
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setStyleSheet("background: rgba(255,255,255,0.1); max-height: 1px;")
        main_layout.addWidget(sep)

        # Presets
        p_lay = QtWidgets.QHBoxLayout()
        self.preset_combo = QtWidgets.QComboBox()
        self.preset_combo.addItem("--- PRESETS ---")
        for p in self.prefs.get("presets", {}).keys(): self.preset_combo.addItem(p)
        self.preset_combo.currentIndexChanged.connect(self.load_preset)
        save_btn = QtWidgets.QPushButton("SAVE")
        del_btn = QtWidgets.QPushButton("DEL")
        del_btn.setObjectName("delBtn")
        save_btn.clicked.connect(self.save_preset)
        del_btn.clicked.connect(self.delete_preset)
        p_lay.addWidget(self.preset_combo); p_lay.addWidget(save_btn); p_lay.addWidget(del_btn)
        main_layout.addLayout(p_lay)

        # Target
        t_lay = QtWidgets.QHBoxLayout()
        t_lay.addWidget(QtWidgets.QLabel("TARGET:"))
        self.target_line = QtWidgets.QLineEdit()
        self.target_line.setReadOnly(True)
        t_btn = QtWidgets.QPushButton("<<<")
        t_btn.clicked.connect(self.load_target)
        t_lay.addWidget(self.target_line); t_lay.addWidget(t_btn)
        main_layout.addLayout(t_lay)

        # Visualizer
        self.channels = {}
        self.vis = VisualizerWidget(self)
        self.vis.setStyleSheet("border: 1px solid rgba(0,243,255,0.2);")
        main_layout.addWidget(self.vis)

        # Scroll area
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QtWidgets.QWidget()
        self.scroll_lay = QtWidgets.QVBoxLayout(scroll_content)
        self.scroll_lay.setContentsMargins(0, 4, 0, 4)
        self.scroll_lay.setSpacing(4)
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # Global mods
        g_frame = QtWidgets.QFrame()
        g_frame.setStyleSheet("QFrame { background: rgba(10,12,18,0.9); border: 1px solid rgba(0,243,255,0.15); border-left: 2px solid rgba(246,162,38,0.5); }")
        g_lay = QtWidgets.QVBoxLayout(g_frame)
        g_lay.setContentsMargins(6, 4, 6, 4)
        g_lbl = QtWidgets.QLabel("GLOBAL_MODS")
        g_lbl.setStyleSheet("letter-spacing: 2px;")
        g_lay.addWidget(g_lbl)

        self.g_amp_slider = PixelSlider("AMP", "#ff00ea", "#440033", ['G', 'A'], 0, 4.0, 1.0)
        self.g_freq_slider = PixelSlider("FRQ", "#00f3ff", "#001133", ['G', 'F'], 0, 4.0, 1.0)
        for lbl_t, sl in [("AMP", self.g_amp_slider), ("FRQ", self.g_freq_slider)]:
            row = QtWidgets.QHBoxLayout()
            lbl = QtWidgets.QLabel(lbl_t); lbl.setFixedWidth(28)
            vl = QtWidgets.QLabel(f"{sl.value():.2f}")
            vl.setFixedWidth(32)
            vl.setStyleSheet(f"color: {sl._color_fill.name()}; font-size: 9px; font-weight: bold;")
            sl.valueChanged.connect(lambda v, vlbl=vl: vlbl.setText(f"{v:.2f}"))
            sl.valueChanged.connect(lambda _: self.auto_apply_expression())
            row.addWidget(lbl); row.addWidget(vl); row.addWidget(sl)
            g_lay.addLayout(row)
        self.scroll_lay.addWidget(g_frame)

        # Channels
        translate_lbl = QtWidgets.QLabel("TRANSLATE")
        translate_lbl.setObjectName("groupLabel")
        self.scroll_lay.addWidget(translate_lbl)
        for ch in ['Tx', 'Ty', 'Tz']:
            cw = ChannelWidget(ch, self); self.channels[ch] = cw; self.scroll_lay.addWidget(cw)

        rotate_lbl = QtWidgets.QLabel("ROTATE")
        rotate_lbl.setObjectName("groupLabel")
        self.scroll_lay.addWidget(rotate_lbl)
        for ch in ['Rx', 'Ry', 'Rz']:
            cw = ChannelWidget(ch, self); self.channels[ch] = cw; self.scroll_lay.addWidget(cw)

        self.scroll_lay.addStretch()

        # Action buttons
        act_lay = QtWidgets.QVBoxLayout()
        act_lay.setSpacing(2)

        row1 = QtWidgets.QHBoxLayout()
        self.auto_btn = QtWidgets.QPushButton("[X] AUTO-LIVE")
        self.auto_btn.setObjectName("autoLiveOn")
        self.auto_btn.setCheckable(True); self.auto_btn.setChecked(True)
        self.auto_btn.clicked.connect(self.toggle_auto_live)
        self.apply_btn = QtWidgets.QPushButton("FORCE APPLY")
        self.apply_btn.clicked.connect(self.apply_expression)
        row1.addWidget(self.auto_btn); row1.addWidget(self.apply_btn)

        row2 = QtWidgets.QHBoxLayout()
        bake_base = QtWidgets.QPushButton("[ BAKE_TO_BASE ]")
        bake_base.setObjectName("bakeBase")
        bake_base.clicked.connect(self.bake_to_timeline)
        bake_layer = QtWidgets.QPushButton("[ BAKE_TO_LAYER ]")
        bake_layer.setObjectName("bakeLayer")
        bake_layer.clicked.connect(self.bake_to_anim_layer)
        row2.addWidget(bake_base); row2.addWidget(bake_layer)

        revert = QtWidgets.QPushButton("REVERT_TARGET_SYSTEM")
        revert.setObjectName("revertBtn")
        revert.clicked.connect(self.revert_target)

        act_lay.addLayout(row1); act_lay.addLayout(row2); act_lay.addWidget(revert)
        main_layout.addLayout(act_lay)

        # Init
        if self.prefs.get("last_state"): self.apply_state(self.prefs["last_state"])
        else:
            for ch in ['Tx', 'Ty', 'Tz', 'Rx', 'Ry', 'Rz']:
                self.channels[ch].add_layer()
                if ch in ['Rx', 'Ry', 'Rz']: self.channels[ch].toggle_mute()
        self.load_target(); self._block_auto = False; self.auto_apply_expression()

    # --- Helpers ---
    def get_global_amp(self): return self.g_amp_slider.value()
    def get_global_freq(self): return self.g_freq_slider.value()

    def set_solo_channel(self, ch_name):
        if self.solo_channel == ch_name: self.solo_channel = None
        else: self.solo_channel, self.solo_layer_id = ch_name, None
        for name, cw in self.channels.items():
            cw.update_solo_visual(name == self.solo_channel)
            for lyr in cw.get_layers_objects(): lyr.update_solo_visual(False)

    def set_solo_layer(self, layer_id):
        if self.solo_layer_id == layer_id: self.solo_layer_id = None
        else: self.solo_layer_id, self.solo_channel = layer_id, None
        for name, cw in self.channels.items():
            cw.update_solo_visual(False)
            for lyr in cw.get_layers_objects(): lyr.update_solo_visual(lyr.id == self.solo_layer_id)

    def get_current_state(self):
        state = {'global_amp': self.g_amp_slider.value(), 'global_freq': self.g_freq_slider.value(), 'channels': {}}
        for name, cw in self.channels.items():
            state['channels'][name] = {'muted': cw.is_muted(), 'layers': cw.get_layers()}
        return state

    def apply_state(self, state):
        if not state: return
        self._block_auto = True
        try:
            self.g_amp_slider.setValue(state.get('global_amp', 1.0))
            self.g_freq_slider.setValue(state.get('global_freq', 1.0))
            for name, data in state.get('channels', {}).items():
                if name in self.channels:
                    cw = self.channels[name]
                    if data.get('muted') != cw.is_muted(): cw.toggle_mute()
                    cw.clear_layers()
                    for lyr_data in data.get('layers', []): cw.add_layer_with_data(lyr_data)
        finally: self._block_auto = False; self.auto_apply_expression()

    def save_preset(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Save Preset", "Preset Name:")
        if ok and name:
            if "presets" not in self.prefs: self.prefs["presets"] = {}
            self.prefs["presets"][name] = self.get_current_state(); save_prefs(self.prefs)
            self.preset_combo.blockSignals(True)
            if self.preset_combo.findText(name) == -1: self.preset_combo.addItem(name)
            self.preset_combo.setCurrentText(name); self.preset_combo.blockSignals(False)

    def load_preset(self, index):
        if index <= 0: return
        name = self.preset_combo.itemText(index)
        preset_data = self.prefs.get("presets", {}).get(name)
        if preset_data: self.apply_state(preset_data)

    def delete_preset(self):
        name = self.preset_combo.currentText()
        if name in self.prefs.get("presets", {}):
            del self.prefs["presets"][name]; save_prefs(self.prefs)
            self.preset_combo.removeItem(self.preset_combo.currentIndex())
            self.preset_combo.setCurrentIndex(0)

    def closeEvent(self, event):
        target = self.target_line.text()
        if target and cmds.objExists(target): self._cleanup_live_nodes(target)
        self.prefs['last_state'] = self.get_current_state(); save_prefs(self.prefs)
        super().closeEvent(event)

    def toggle_auto_live(self):
        if self.auto_btn.isChecked():
            self.auto_btn.setText("[X] AUTO-LIVE")
            self.auto_btn.setObjectName("autoLiveOn")
            self.auto_btn.setStyle(self.auto_btn.style())
            self.apply_expression()
        else:
            self.auto_btn.setText("[ ] AUTO-LIVE")
            self.auto_btn.setObjectName("")
            self.auto_btn.setStyle(self.auto_btn.style())
            target = self.target_line.text()
            if target and cmds.objExists(target): self._cleanup_live_nodes(target)

    def auto_apply_expression(self):
        if not self._block_auto and hasattr(self, 'auto_btn') and self.auto_btn.isChecked():
            self.apply_expression()

    def load_target(self):
        sel = cmds.ls(selection=True)
        if sel: self.target_line.setText(sel[0]); self.auto_apply_expression()
        else: self.target_line.setText("")

    def map_maya_attr(self, ch_name):
        return {'Tx': 'translateX', 'Ty': 'translateY', 'Tz': 'translateZ',
                'Rx': 'rotateX', 'Ry': 'rotateY', 'Rz': 'rotateZ'}.get(ch_name)

    def _get_pma_name(self, target, ch_name): return f"{target}_noisePMA_{ch_name}"

    def _cleanup_single_channel(self, target, ch):
        pma = self._get_pma_name(target, ch)
        full_attr = f"{target}.{self.map_maya_attr(ch)}"
        if cmds.objExists(pma):
            driver = cmds.listConnections(f"{pma}.input1D[0]", s=True, d=False, plugs=True)
            static_val = cmds.getAttr(f"{pma}.input1D[0]")
            pma_out = cmds.listConnections(f"{pma}.output1D", s=False, d=True, plugs=True)
            if pma_out and full_attr in pma_out: cmds.disconnectAttr(f"{pma}.output1D", full_attr)
            try:
                if driver: cmds.connectAttr(driver[0], full_attr, force=True)
                else: cmds.setAttr(full_attr, static_val)
            except Exception as e:
                print(f"NOISE.SYS cleanup warning: could not restore {full_attr}: {e}")
            cmds.delete(pma)
        cust_attr = f"noise_{ch}"
        if cmds.attributeQuery(cust_attr, node=target, exists=True):
            cmds.setAttr(f"{target}.{cust_attr}", lock=False)
            cmds.deleteAttr(target, attribute=cust_attr)

    def _cleanup_live_nodes(self, target):
        expr_name = f"{target}_noise_sys_expr"
        if cmds.objExists(expr_name): cmds.delete(expr_name)
        for ch in ['Tx', 'Ty', 'Tz', 'Rx', 'Ry', 'Rz']:
            self._cleanup_single_channel(target, ch)

    def revert_target(self):
        target = self.target_line.text()
        if not target or not cmds.objExists(target):
            cmds.warning("NOISE.SYS: No valid target to revert."); return
        if self.auto_btn.isChecked():
            self.auto_btn.setChecked(False)
            self.auto_btn.setText("[ ] AUTO-LIVE")
            self.auto_btn.setObjectName("")
            self.auto_btn.setStyle(self.auto_btn.style())
        cmds.undoInfo(openChunk=True, chunkName="RevertNoiseSys")
        try:
            self._cleanup_live_nodes(target)
            cmds.warning(f"NOISE.SYS: System dismantled. {target} restored.")
        except Exception as e: cmds.warning(f"NOISE.SYS Revert Error: {str(e)}")
        finally: cmds.undoInfo(closeChunk=True)

    def apply_expression(self):
        target = self.target_line.text()
        if not target or not cmds.objExists(target): return
        expr_name = f"{target}_noise_sys_expr"
        expr_lines = []
        g_amp, g_freq = self.get_global_amp(), self.get_global_freq()
        active_channels, inactive_channels = [], []
        for ch_name, ch_widget in self.channels.items():
            if ch_widget.is_muted() or not ch_widget.get_layers(): inactive_channels.append(ch_name)
            else: active_channels.append(ch_name)
        if not active_channels: self._cleanup_live_nodes(target); return
        for ch_name in active_channels:
            cust_attr = f"noise_{ch_name}"
            if not cmds.attributeQuery(cust_attr, node=target, exists=True):
                cmds.addAttr(target, ln=cust_attr, at='double', k=True)
            cmds.setAttr(f"{target}.{cust_attr}", lock=False)
        for ch_name in active_channels:
            layers = self.channels[ch_name].get_layers()
            base_val = self.channels[ch_name].get_base_value()
            math_str = str(base_val)
            for lyr in layers:
                amp = lyr['amp'] * g_amp
                freq = lyr['freq'] * g_freq
                offset = lyr['offset']
                ntype = lyr['type']
                if ntype == 'SQUARE': s = f" ((sin(time * {freq} + {offset}) >= 0 ? 1.0 : -1.0) * {amp})"
                elif ntype == 'TRIANGLE': s = f" (2.0 * abs(2.0 * ((time * {freq} + {offset}) / 6.28318 - floor(0.5 + (time * {freq} + {offset}) / 6.28318)) - 0.5) * {amp})"
                elif ntype == 'SAW': s = f" (2.0 * ((time * {freq} + {offset}) / 6.28318 - floor(0.5 + (time * {freq} + {offset}) / 6.28318)) * {amp})"
                elif ntype == 'PERLIN': s = f" ((sin(time * {freq} + {offset}) + sin(2.0 * (time * {freq} + {offset})) * 0.5 + sin(4.0 * (time * {freq} + {offset})) * 0.25) * 0.44 * {amp})"
                elif ntype == 'RANDOM': s = f" (rand(-1.0, 1.0) * {amp})"
                else: s = f" (sin(time * {freq} + {offset}) * {amp})"
                math_str += f" + {s}"
            expr_lines.append(f"{target}.noise_{ch_name} = {math_str};")
        if expr_lines:
            full_expr = "\n".join(expr_lines)
            if cmds.objExists(expr_name): cmds.expression(expr_name, e=True, s=full_expr, alwaysEvaluate=True)
            else: cmds.expression(n=expr_name, s=full_expr, alwaysEvaluate=True)
        for ch_name in active_channels:
            cust_attr = f"noise_{ch_name}"
            full_attr = f"{target}.{self.map_maya_attr(ch_name)}"
            pma = self._get_pma_name(target, ch_name)
            if not cmds.objExists(pma):
                try:
                    driver = cmds.listConnections(full_attr, s=True, d=False, plugs=True)
                    val = cmds.getAttr(full_attr)
                    cmds.createNode('plusMinusAverage', n=pma)
                    cmds.setAttr(f"{pma}.operation", 1)
                    if driver: cmds.disconnectAttr(driver[0], full_attr); cmds.connectAttr(driver[0], f"{pma}.input1D[0]")
                    else: cmds.setAttr(f"{pma}.input1D[0]", val)
                    cmds.connectAttr(f"{target}.{cust_attr}", f"{pma}.input1D[1]")
                    cmds.connectAttr(f"{pma}.output1D", full_attr, force=True)
                except Exception: pass
        for ch_name in inactive_channels: self._cleanup_single_channel(target, ch_name)

    def bake_to_timeline(self): self._bake_logic(use_layer=False)
    def bake_to_anim_layer(self): self._bake_logic(use_layer=True)

    def _bake_logic(self, use_layer):
        target = self.target_line.text()
        if not target or not cmds.objExists(target):
            cmds.warning("NOISE.SYS: No valid target."); return
        if self.auto_btn.isChecked():
            self.auto_btn.setChecked(False)
            self.auto_btn.setText("[ ] AUTO-LIVE")
            self.auto_btn.setObjectName("")
            self.auto_btn.setStyle(self.auto_btn.style())
        self._cleanup_live_nodes(target)
        start = int(cmds.playbackOptions(q=True, minTime=True))
        end = int(cmds.playbackOptions(q=True, maxTime=True))
        fps = 24.0
        layer_name = f"{target}_NoiseSys_Layer"
        if use_layer and not cmds.objExists(layer_name):
            cmds.animLayer(layer_name, override=False)
        cmds.undoInfo(openChunk=True, chunkName="BakeNoiseSys")
        orig_time = cmds.currentTime(q=True)
        try:
            for f in range(start, end + 1):
                cmds.currentTime(f, edit=True)
                t_sec = f / fps
                for ch_name, ch_widget in self.channels.items():
                    if ch_widget.is_muted(): continue
                    layers = ch_widget.get_layers()
                    attr_name = self.map_maya_attr(ch_name)
                    full_attr = f"{target}.{attr_name}"
                    if not cmds.attributeQuery(attr_name, node=target, exists=True): continue
                    if use_layer and f == start:
                        cmds.animLayer(layer_name, edit=True, attribute=full_attr)
                    noise_val = ch_widget.get_base_value()
                    for lyr in layers:
                        t = t_sec * (lyr['freq'] * self.get_global_freq()) + lyr['offset']
                        noise_val += get_noise_val(t, lyr['type']) * (lyr['amp'] * self.get_global_amp())
                    if use_layer:
                        cmds.setKeyframe(target, attribute=attr_name, t=f, v=noise_val, animLayer=layer_name)
                    else:
                        base_val = cmds.getAttr(full_attr)
                        cmds.setKeyframe(target, attribute=attr_name, t=f, v=base_val + noise_val)
            cmds.currentTime(orig_time, edit=True)
        except Exception as e: cmds.warning(f"NOISE.SYS Error: {str(e)}")
        finally: cmds.undoInfo(closeChunk=True)


noise_window = None
def showUI():
    global noise_window
    if noise_window: noise_window.close()
    noise_window = NoiseSysWindow(); noise_window.show()

if __name__ == "__main__": showUI()