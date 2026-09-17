import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
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

def _frame_hash(frame, offset):
    """Deterministic per-frame random in [-1, 1], so live and bake agree."""
    h = math.sin(frame * 12.9898 + offset * 78.233) * 43758.5453
    return 2.0 * (h - math.floor(h)) - 1.0

def seed_phase(seed, ch_name, layer_index):
    """Extra phase for one layer, derived from the global seed so every channel/layer gets its
    own repeatable variation. Seed 0 adds nothing (original behaviour)."""
    if not seed: return 0.0
    return random.Random(f"{seed}:{ch_name}:{layer_index}").uniform(0.0, 628.0)

def get_noise_val(t, ntype, frame=None, offset=0.0):
    """Unit wave value. t = phase (time * freq + offset). RANDOM is only reproducible
    when a frame is given (bake); the visualizer passes none and gets a preview."""
    if ntype == 'SQUARE': return 1.0 if math.sin(t) >= 0 else -1.0
    if ntype == 'TRIANGLE': return (2.0 / math.pi) * math.asin(max(-1, min(1, math.sin(t))))
    if ntype == 'SAW': return 2.0 * (t / (2.0 * math.pi) - math.floor(0.5 + t / (2.0 * math.pi)))
    if ntype == 'PERLIN': return pseudo_perlin(t)
    if ntype == 'RANDOM':
        return _frame_hash(frame, offset) if frame is not None else random.uniform(-1.0, 1.0)
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
QPushButton#targetName { background: transparent; border: none; color: #e0e7ff; text-align: left; text-transform: none; letter-spacing: 0px; }
QPushButton#targetName:hover { color: #f6a226; }
QPushButton#delBtn:hover { border-color: #ff4444; color: #ff4444; background: rgba(255,68,68,0.1); }
QPushButton#autoLiveOn { background-color: rgba(0,243,255,0.1); border-color: #00f3ff; color: #00f3ff; }
QSpinBox { background-color: rgba(0,0,0,0.6); border: 1px solid rgba(246,162,38,0.3); color: #f6a226; padding: 1px 4px; font-size: 10px; }
QSpinBox::up-button, QSpinBox::down-button { width: 12px; background: rgba(246,162,38,0.08); border: none; }
QComboBox { background-color: rgba(5,8,15,0.9); border: 1px solid rgba(0,243,255,0.15); color: #00f3ff; padding: 2px 4px; font-size: 9px; }
QComboBox::drop-down { border: none; width: 14px; }
QComboBox QAbstractItemView { background: #0a0c12; color: #00f3ff; selection-background-color: rgba(0,243,255,0.15); border: 1px solid rgba(0,243,255,0.2); }
QLineEdit { background-color: rgba(0,0,0,0.6); border: 1px solid rgba(246,162,38,0.3); color: #f6a226; padding: 2px 6px; font-size: 10px; }
QLabel { background: transparent; color: rgba(255,255,255,0.4); font-size: 9px; }
QLabel#groupLabel { color: rgba(255,255,255,0.15); letter-spacing: 3px; font-size: 9px; }
"""


# --- PIXEL DOT-MATRIX SLIDER ---
class PixelSlider(QtWidgets.QWidget):
    valueChanged = QtCore.Signal(float)  # user changed it (drives Maya)
    valueSet = QtCore.Signal(float)      # set in code (presets/state): display only

    def __init__(self, label="", color_fill="#00f3ff", color_empty="#002233", icons=None,
                 vmin=0.0, vmax=1.0, vdefault=0.0, parent=None):
        super().__init__(parent)
        self._value = vdefault
        self._min, self._max = vmin, vmax
        self._default_max = vmax
        self._drag_ratio = 0.0  # pointer position along the slider, NOT clamped (>1 = past the right edge)
        # Shift + drag at/past the right edge raises the cap steadily while held.
        self._grow_timer = QtCore.QTimer(self)
        self._grow_timer.setInterval(30)
        self._grow_timer.timeout.connect(self._tick_grow)
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
        self.valueSet.emit(self._value)
        self.update()

    def maximum(self): return self._max
    def set_value_from_user(self, v):
        """Typed-in value: raises the cap if needed (double-click the slider to reset it)."""
        v = max(self._min, float(v))
        if v > self._max: self._max = v
        if v != self._value:
            self._value = v
            self.valueChanged.emit(v)
        self.update()

    def setMaximum(self, m):
        """Cap can be raised above the built-in maximum but never set below it."""
        self._max = max(self._default_max, float(m or 0.0))
        self.setValue(self._value)

    GROW_PER_SECOND = 0.66  # fraction of the built-in maximum added per second (3.0 -> ~+2/sec)

    def _tick_grow(self):
        shift = bool(QtWidgets.QApplication.keyboardModifiers() & QtCore.Qt.ShiftModifier)
        if not (self._dragging and shift and self._drag_ratio >= 1.0): return
        self._max += self._default_max * self.GROW_PER_SECOND * self._grow_timer.interval() / 1000.0
        self._value = self._max  # handle stays pinned to the (moving) end
        self.valueChanged.emit(self._value)
        self.update()
        self._flash_timer.start(1500)

    def mouseDoubleClickEvent(self, e):
        # Double-click resets a raised cap back to the built-in maximum (value clamps to it).
        old = self._value
        self._max = self._default_max
        self.setValue(self._value)
        if self._value != old: self.valueChanged.emit(self._value)

    def _start_flash(self):
        self._flash_active = True
        self._flash_frames = 0
        self._anim_timer.start(33)  # ~30fps, only during flash

    def _tick_flash(self):
        self._flash_frames += 1
        if self._flash_frames > 18:
            self._flash_active = False
            self._anim_timer.stop()  # Stop timer when flash ends
        self.update()

    def mousePressEvent(self, e):
        self._dragging = True
        self._handle_drag(e)
        self._grow_timer.start()

    def mouseMoveEvent(self, e):
        if self._dragging: self._handle_drag(e)

    def mouseReleaseEvent(self, e):
        self._dragging = False
        self._grow_timer.stop()
        self._flash_timer.start(1500)

    def _handle_drag(self, e):
        self._drag_ratio = e.pos().x() / max(1, self.width() - 1)
        pos = max(0.0, min(1.0, self._drag_ratio))
        new_val = self._min + pos * (self._max - self._min)
        if new_val != self._value:
            self._value = new_val
            self.valueChanged.emit(self._value)
            self.update()
            self._flash_timer.start(1500)

    # Pre-rendered dot grids, shared by every slider with the same size/colours/icons.
    # Painting then costs two pixmap blits instead of 832 antialiased ellipses.
    _sprite_cache = {}

    def _sprite(self, filled, show_icons):
        w, h = self.width(), self.height()
        dpr = self.devicePixelRatioF()
        key = (w, h, dpr, self._color_fill.rgba(), self._color_empty.rgba(),
               tuple(self._icons), filled, show_icons)
        cache = PixelSlider._sprite_cache
        pm = cache.get(key)
        if pm is not None: return pm
        if len(cache) > 256: cache.clear()  # window resizes create new sizes; keep it bounded

        pm = QtGui.QPixmap(max(1, int(w * dpr)), max(1, int(h * dpr)))
        pm.setDevicePixelRatio(dpr)
        pm.fill(QtCore.Qt.transparent)
        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setPen(QtCore.Qt.NoPen)
        cell_w, cell_h = w / self.COLS, h / self.ROWS
        dot_r = min(cell_w, cell_h) * 0.42
        icon_set = self._icon_set if show_icons else ()
        cf, ce, cd = self._color_fill, self._color_empty, self._color_icon_dark
        for r in range(self.ROWS):
            y = r * cell_h + cell_h / 2
            for c in range(self.COLS):
                is_icon = (r, c) in icon_set
                if filled: p.setBrush(cd if is_icon else cf)
                else: p.setBrush(cf if is_icon else ce)
                p.drawEllipse(QtCore.QPointF(c * cell_w + cell_w / 2, y), dot_r, dot_r)
        p.end()
        cache[key] = pm
        return pm

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, QtGui.QColor(0, 0, 0, 150))

        cell_w = w / self.COLS
        norm = (self._value - self._min) / max(0.001, self._max - self._min)
        # A dot counts as filled when its centre is inside the fill width.
        fill_cols = max(0, min(self.COLS, int(math.floor(w * norm / cell_w + 0.5))))
        split_x = fill_cols * cell_w
        show_icons = not (self._flash_active and (self._flash_frames // 3) % 2 == 0)

        painter.setClipRect(QtCore.QRectF(0, 0, split_x, h))
        painter.drawPixmap(0, 0, self._sprite(True, show_icons))
        painter.setClipRect(QtCore.QRectF(split_x, 0, w - split_x, h))
        painter.drawPixmap(0, 0, self._sprite(False, show_icons))
        painter.end()


# --- TYPE-IN VALUE FOR A SLIDER ---
class ValueField(QtWidgets.QLineEdit):
    """Editable number shown beside a PixelSlider. Enter (or clicking away) applies it,
    Esc cancels. Values above the slider's cap raise the cap."""
    def __init__(self, slider, bold=False, parent=None):
        super().__init__(parent)
        self.slider = slider
        self._shown = ""
        color = slider._color_fill.name()
        weight = "font-weight: bold;" if bold else ""
        self.setFixedWidth(44)
        self.setStyleSheet(
            f"QLineEdit {{ background: transparent; border: 1px solid transparent; color: {color}; "
            f"font-size: 9px; padding: 0px 2px; {weight} }}"
            f"QLineEdit:hover {{ border-color: rgba(255,255,255,0.15); }}"
            f"QLineEdit:focus {{ border-color: {color}; background: rgba(0,0,0,0.6); }}")
        self.setToolTip("Type a value, then Enter. Above the slider's max raises its cap.")
        self._show(slider.value())
        slider.valueChanged.connect(self._on_slider)
        slider.valueSet.connect(self._on_slider)
        self.editingFinished.connect(self._commit)

    def _show(self, v):
        self._shown = f"{v:.3g}" if abs(v) >= 1000 else f"{v:.2f}"
        self.setText(self._shown)

    def _on_slider(self, v):
        if not self.hasFocus(): self._show(v)  # don't overwrite what's being typed

    def _commit(self):
        text = self.text().strip()
        if text == self._shown: return  # unchanged (e.g. focus left after Enter): keep full precision
        try: v = float(text.replace(',', '.'))
        except ValueError: self._show(self.slider.value()); return
        self.slider.set_value_from_user(v)
        self._show(self.slider.value())

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self._show(self.slider.value()); self.clearFocus(); return
        super().keyPressEvent(e)
        if e.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter): self.selectAll()

    def focusInEvent(self, e):
        super().focusInEvent(e)
        QtCore.QTimer.singleShot(0, self.selectAll)  # click in, type straight over the old value

    def focusOutEvent(self, e):
        super().focusOutEvent(e)
        if self.text().strip() != self._shown: self._commit()
        self._show(self.slider.value())


# --- VISUALIZER ---
def eval_params(params, t):
    """Sum of one channel's layers at preview time t. params = [(freq, phase, amp, type)]."""
    return sum(get_noise_val(t * f + o, ty) * a for f, o, a, ty in params)


class VisualizerWidget(QtWidgets.QWidget):
    """Scrolling wave display. The playhead (centre line) is 'now'; the 3D box shows that instant.
    Wheel = zoom time, Shift/Ctrl+wheel = zoom height, double-click = reset zoom."""
    TIME_PER_PX = 0.04  # preview time units per pixel at zoom 1
    AMP_PX = 30.0       # pixels per unit of noise at height zoom 1 (when not normalized)

    def __init__(self, main_ui, parent=None):
        super().__init__(parent)
        self.main_ui = main_ui
        self.setFixedHeight(110)
        self.setMinimumWidth(120)
        self.time_offset = 0.0
        self.time_zoom = 1.0
        self.amp_zoom = 1.0
        self.normalize = False
        self.companions = []  # widgets repainted on every animation tick (the 3D box)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._tick)
        # Animation only runs while this set is empty ("user", "playback", "scrub", "move", ...).
        self._pause_reasons = set()
        self._resume_timers = {}
        self._bg = self._scan = None  # static layers, cached per size
        self._pens = {axis: QtGui.QPen(QtGui.QColor(C['axis_' + name]), 2)
                      for axis, name in (('x', 'red'), ('y', 'green'), ('z', 'blue'))}
        self._playhead_pen = QtGui.QPen(QtGui.QColor(246, 162, 38, 90), 1, QtCore.Qt.DashLine)
        self._label_font = QtGui.QFont("Consolas", 7)
        self.setToolTip("Wheel: zoom time   Shift+Wheel: zoom height   Double-click: reset")

    # --- pausing ---
    def set_paused(self, reason, paused):
        if paused: self._pause_reasons.add(reason)
        else: self._pause_reasons.discard(reason)
        self._sync_timer()

    def pause_for(self, reason, ms):
        """Pause now, resume automatically once 'ms' passes without another call (debounced)."""
        t = self._resume_timers.get(reason)
        if t is None:
            t = QtCore.QTimer(self)
            t.setSingleShot(True)
            t.timeout.connect(lambda r=reason: self.set_paused(r, False))
            self._resume_timers[reason] = t
        if reason not in self._pause_reasons: self.set_paused(reason, True)
        t.start(ms)

    def _sync_timer(self):
        visible = self.isVisible() or any(c.isVisible() for c in self.companions)
        should_run = not self._pause_reasons and visible
        if should_run and not self.timer.isActive(): self.timer.start(33)
        elif not should_run and self.timer.isActive(): self.timer.stop()

    def showEvent(self, e): super().showEvent(e); self._sync_timer()
    def hideEvent(self, e): super().hideEvent(e); self._sync_timer()
    def resizeEvent(self, e): super().resizeEvent(e); self._bg = self._scan = None

    def _tick(self):
        self.time_offset += 0.05
        self.refresh()

    def refresh(self):
        self.update()
        for c in self.companions: c.update()

    # --- zoom ---
    def zoom_time(self, factor):
        self.time_zoom = max(0.1, min(20.0, self.time_zoom * factor)); self.refresh()

    def zoom_amp(self, factor):
        self.amp_zoom = max(0.05, min(50.0, self.amp_zoom * factor)); self.refresh()

    def set_normalize(self, on):
        self.normalize = bool(on); self.refresh()

    def reset_view(self):
        self.time_zoom = self.amp_zoom = 1.0; self.refresh()

    def wheelEvent(self, e):
        d = e.angleDelta().y() or e.angleDelta().x()  # Shift+wheel arrives as horizontal on Windows
        if not d: return
        factor = 1.25 if d > 0 else 0.8
        if e.modifiers() & (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier): self.zoom_amp(factor)
        else: self.zoom_time(factor)
        e.accept()

    def mouseDoubleClickEvent(self, e): self.reset_view()

    # --- drawing ---
    def _build_static(self, w, h):
        dpr = self.devicePixelRatioF()
        def new_pm():
            pm = QtGui.QPixmap(max(1, int(w * dpr)), max(1, int(h * dpr)))
            pm.setDevicePixelRatio(dpr)
            return pm
        self._bg = new_pm()
        self._bg.fill(QtGui.QColor(5, 6, 10))
        p = QtGui.QPainter(self._bg)
        p.setPen(QtGui.QPen(QtGui.QColor(0, 243, 255, 12), 1))
        for i in range(0, w, 25): p.drawLine(i, 0, i, h)
        for i in range(0, h, 25): p.drawLine(0, i, w, i)
        p.setPen(QtGui.QPen(QtGui.QColor(0, 243, 255, 38), 1))
        p.drawLine(0, h // 2, w, h // 2)
        p.setPen(QtGui.QPen(QtGui.QColor(0, 243, 255, 50), 1))
        p.drawRect(0, 0, w - 1, h - 1)
        p.end()
        self._scan = new_pm()
        self._scan.fill(QtCore.Qt.transparent)
        p = QtGui.QPainter(self._scan)
        p.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 40), 1))
        for i in range(0, h, 2): p.drawLine(0, i, w, i)
        p.end()

    def paintEvent(self, event):
        w, h = self.width(), self.height()
        if self._bg is None: self._build_static(w, h)
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0, 0, self._bg)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        mid, cx = h / 2.0, w / 2.0

        # Sample every channel first so NORM can fit the tallest wave to the display.
        t0, dt = self.time_offset, self.TIME_PER_PX / self.time_zoom
        xs = range(0, w, 2)
        curves = []
        for ch_name, params in self.main_ui.preview_params().items():
            ys = [eval_params(params, t0 + (x - cx) * dt) for x in xs] if params else [0.0] * len(xs)
            curves.append((ch_name, ys))
        if self.normalize:
            peak = max((abs(y) for _, ys in curves for y in ys), default=0.0)
            scale = (mid - 6.0) / peak if peak > 1e-9 else self.AMP_PX
        else:
            scale = self.AMP_PX * self.amp_zoom

        for ch_name, ys in curves:
            painter.setPen(self._pens[ch_name[-1].lower()])
            painter.drawPolyline(QtGui.QPolygonF([QtCore.QPointF(x, mid - y * scale) for x, y in zip(xs, ys)]))

        painter.setPen(self._playhead_pen)
        painter.drawLine(QtCore.QPointF(cx, 0), QtCore.QPointF(cx, h))
        painter.drawPixmap(0, 0, self._scan)

        painter.setFont(self._label_font)
        painter.setPen(QtGui.QColor(255, 255, 255, 90))
        amp_txt = "NORM" if self.normalize else f"x{self.amp_zoom:.2g}"
        status = "  PAUSED" if 'user' in self._pause_reasons else ""
        painter.drawText(4, h - 4, f"T x{self.time_zoom:.2g}  A {amp_txt}{status}")
        painter.end()


# --- 3D NOISE PYRAMID ---
class Box3DWidget(QtWidgets.QWidget):
    """Wireframe pyramid moved by the noise at the wave display's playhead, with an optional
    trail traced by its tip. Translate = scene units (x height zoom, or fitted when NORM is on);
    rotate = degrees, Maya xyz order. Drag to orbit, double-click to reset the camera."""
    AXES = ['+Y', '-Y', '+X', '-X', '+Z', '-Z']
    PIVOTS = ['BASE', 'CENTER', 'TIP']
    FADES = ['NONE', 'LINEAR', 'EASE', 'FAST']
    STYLES = ['SOLID', 'DASH', 'DOT', 'DASH-DOT', 'POINTS']
    COLORS = {'ORANGE': C['orange'], 'CYAN': C['cyan'], 'PINK': C['pink'], 'WHITE': C['white'], 'GREEN': C['green']}
    DEFAULTS = {'axis': '+Y', 'pivot': 'BASE', 'trail_on': True, 'trail_len': 30, 'trail_fade': 'LINEAR',
                'trail_width': 1.5, 'trail_taper': False, 'trail_style': 'SOLID', 'trail_color': 'ORANGE'}
    STEP = 0.05  # preview time per frame; matches VisualizerWidget._tick

    # Pyramid pointing +Y, 1 unit tall/wide, centred on its bounding box: 4 base corners + apex.
    _BASE = [(-0.5, -0.5, -0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (-0.5, -0.5, 0.5)]
    _APEX = (0.0, 0.5, 0.0)
    EDGES = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 4), (1, 4), (2, 4), (3, 4)]
    # Proper rotations taking +Y to each axis (so the pyramid is never mirrored).
    _AXIS_MAP = {'+Y': lambda x, y, z: (x, y, z),  '-Y': lambda x, y, z: (x, -y, -z),
                 '+X': lambda x, y, z: (y, -x, z), '-X': lambda x, y, z: (-y, x, z),
                 '+Z': lambda x, y, z: (x, -z, y), '-Z': lambda x, y, z: (x, z, -y)}
    _PIVOT_SHIFT = {'BASE': 0.5, 'CENTER': 0.0, 'TIP': -0.5}  # along the pointing axis

    def __init__(self, main_ui, vis, parent=None):
        super().__init__(parent)
        self.main_ui, self.vis = main_ui, vis
        self.setMinimumSize(120, 110)
        self.setFixedHeight(110)
        self.yaw, self.pitch = 35.0, 20.0
        self.zoom = 1.0
        self.pan = QtCore.QPointF(0.0, 0.0)  # screen-space offset in pixels
        self._drag_pos = None
        self._drag_mode = None  # 'orbit' | 'pan' | 'zoom'
        self.setFocusPolicy(QtCore.Qt.ClickFocus)  # so F can reset the view
        for k, v in self.DEFAULTS.items(): setattr(self, k, v)
        self._ghost_pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 40), 1, QtCore.Qt.DashLine)
        self._shape_pen = QtGui.QPen(QtGui.QColor(C['cyan']), 1.5)
        self._grid_pen = QtGui.QPen(QtGui.QColor(0, 243, 255, 22), 1)
        self._axis_pens = [QtGui.QPen(QtGui.QColor(C['axis_' + n]), 2) for n in ('red', 'green', 'blue')]
        self.setCursor(QtCore.Qt.OpenHandCursor)
        self.setToolTip("Noise applied to a pyramid at the playhead\n"
                        "Left-drag: orbit    Middle-drag or Shift+left-drag: pan\n"
                        "Wheel or right-drag: zoom    Double-click or F: reset view")

    # --- settings ---
    def settings(self): return {k: getattr(self, k) for k in self.DEFAULTS}

    def apply_settings(self, d):
        for k, default in self.DEFAULTS.items():
            v = (d or {}).get(k, default)
            setattr(self, k, type(default)(v) if not isinstance(default, bool) else bool(v))
        self.update()

    def set_option(self, key, value):
        setattr(self, key, value); self.update()

    # --- visibility drives the shared animation timer (it lives on the wave display) ---
    def showEvent(self, e): super().showEvent(e); self.vis._sync_timer()
    def hideEvent(self, e): super().hideEvent(e); self.vis._sync_timer()

    # --- camera ---
    def mousePressEvent(self, e):
        btn, shift = e.button(), bool(e.modifiers() & QtCore.Qt.ShiftModifier)
        if btn == QtCore.Qt.MiddleButton or (btn == QtCore.Qt.LeftButton and shift): self._drag_mode = 'pan'
        elif btn == QtCore.Qt.RightButton: self._drag_mode = 'zoom'
        elif btn == QtCore.Qt.LeftButton: self._drag_mode = 'orbit'
        else: return
        self._drag_pos = e.pos()
        self.setCursor(QtCore.Qt.SizeAllCursor if self._drag_mode == 'pan' else QtCore.Qt.ClosedHandCursor)

    def mouseMoveEvent(self, e):
        if self._drag_pos is None: return
        d = e.pos() - self._drag_pos
        self._drag_pos = e.pos()
        if self._drag_mode == 'pan':
            self.pan += QtCore.QPointF(d.x(), d.y())
        elif self._drag_mode == 'zoom':
            self._zoom_about(1.01 ** (d.x() - d.y()), QtCore.QPointF(self.width() / 2, self.height() / 2))
            return
        else:
            self.yaw += d.x() * 0.8
            self.pitch = max(-89.0, min(89.0, self.pitch + d.y() * 0.8))
        self.update()

    def mouseReleaseEvent(self, e):
        self._drag_pos = self._drag_mode = None; self.setCursor(QtCore.Qt.OpenHandCursor)

    def wheelEvent(self, e):
        d = e.angleDelta().y() or e.angleDelta().x()
        if not d: return
        pos = e.position() if hasattr(e, 'position') else QtCore.QPointF(e.pos())
        self._zoom_about(1.15 if d > 0 else 1 / 1.15, pos)
        e.accept()

    def _zoom_about(self, factor, anchor):
        """Zoom keeping the point under 'anchor' (widget pixels) fixed on screen."""
        new_zoom = max(0.1, min(50.0, self.zoom * factor))
        factor = new_zoom / self.zoom
        centre = QtCore.QPointF(self.width() / 2, self.height() / 2)
        self.pan = (anchor - centre) - ((anchor - centre) - self.pan) * factor
        self.zoom = new_zoom
        self.update()

    def reset_view(self):
        self.yaw, self.pitch, self.zoom = 35.0, 20.0, 1.0
        self.pan = QtCore.QPointF(0.0, 0.0)
        self.update()

    def mouseDoubleClickEvent(self, e): self.reset_view()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_F: self.reset_view()
        else: super().keyPressEvent(e)

    # --- maths ---
    @staticmethod
    def _rotate_xyz(p, rx, ry, rz):
        """Maya's default xyz rotate order: X first, then Y, then Z (angles in radians)."""
        x, y, z = p
        c, s = math.cos(rx), math.sin(rx); y, z = y * c - z * s, y * s + z * c
        c, s = math.cos(ry), math.sin(ry); x, z = x * c + z * s, -x * s + z * c
        c, s = math.cos(rz), math.sin(rz); x, y = x * c - y * s, x * s + y * c
        return x, y, z

    def _shape_points(self):
        """Pyramid corners (base x4, apex) in object space for the chosen axis and pivot.
        The pivot sits at the origin, which is what the noise rotates around."""
        shift = self._PIVOT_SHIFT.get(self.pivot, 0.0)
        to_axis = self._AXIS_MAP.get(self.axis, self._AXIS_MAP['+Y'])
        return [to_axis(x, y + shift, z) for x, y, z in self._BASE + [self._APEX]]

    def _project(self, p, w, h):
        x, y, z = p
        c, s = math.cos(math.radians(self.yaw)), math.sin(math.radians(self.yaw))
        x, z = x * c - z * s, x * s + z * c
        c, s = math.cos(math.radians(self.pitch)), math.sin(math.radians(self.pitch))
        y, z = y * c - z * s, y * s + z * c
        depth = max(0.2, z + 4.5)  # camera 4.5 units back
        f = min(w, h) * 1.6 * self.zoom
        return QtCore.QPointF(w / 2 + self.pan.x() + x * f / depth, h / 2 + self.pan.y() - y * f / depth)

    def _transform_at(self, params, t_scale, t):
        """Function mapping object-space points to world space at preview time t."""
        val = {ch: eval_params(p, t) for ch, p in params.items()}
        offset = tuple(val.get(ch, 0.0) * t_scale for ch in ('Tx', 'Ty', 'Tz'))
        rx, ry, rz = (math.radians(val.get(ch, 0.0)) for ch in ('Rx', 'Ry', 'Rz'))
        return lambda p: tuple(a + b for a, b in zip(self._rotate_xyz(p, rx, ry, rz), offset))

    def _fade(self, u):
        """Opacity for a trail point, u = 0 at the tip (now) .. 1 at the oldest point."""
        if self.trail_fade == 'LINEAR': return 1.0 - u
        if self.trail_fade == 'EASE': return 1.0 - u * u * (3.0 - 2.0 * u)  # smoothstep: holds, then drops
        if self.trail_fade == 'FAST': return (1.0 - u) ** 3
        return 1.0

    # --- drawing ---
    def _trail_look(self, u):
        """(opacity, width) at position u along the trail (0 = tip, 1 = tail), quantized so
        neighbouring segments share a look and can be drawn as one continuous stroke."""
        alpha = round(max(0.0, min(1.0, self._fade(u))) * 48) / 48.0
        width = float(self.trail_width) * (1.0 - u) if self.trail_taper else float(self.trail_width)
        return alpha, max(0.5, round(width * 4) / 4.0)

    def _draw_trail(self, painter, pts):
        """pts[0] = tip now, pts[-1] = oldest.

        Drawn as runs of connected polylines, never as separate overlapping segments: each
        segment with its own rounded end used to double up the semi-transparent colour where
        ends overlapped, so a 'solid' line came out beaded. A trail with no fade and no taper
        is now a single stroke."""
        n = len(pts)
        if n < 2: return
        base = QtGui.QColor(self.COLORS.get(self.trail_color, C['orange']))

        if self.trail_style == 'POINTS':
            painter.setPen(QtCore.Qt.NoPen)
            for i, p in enumerate(pts):
                alpha, width = self._trail_look(i / (n - 1))
                if alpha <= 0.0: break
                c = QtGui.QColor(base); c.setAlphaF(alpha)
                painter.setBrush(c)
                painter.drawEllipse(p, width, width)
            painter.setBrush(QtCore.Qt.NoBrush)
            return

        style = {'DASH': QtCore.Qt.DashLine, 'DOT': QtCore.Qt.DotLine,
                 'DASH-DOT': QtCore.Qt.DashDotLine}.get(self.trail_style, QtCore.Qt.SolidLine)
        runs = []  # [look, start_distance, [points]]
        dist = 0.0
        for i in range(n - 1):
            look = self._trail_look((i + 0.5) / (n - 1))
            if look[0] <= 0.0: break
            if not runs or runs[-1][0] != look:
                runs.append([look, dist, [pts[i]]])
            runs[-1][2].append(pts[i + 1])
            seg = pts[i + 1] - pts[i]
            dist += math.hypot(seg.x(), seg.y())

        single = len(runs) == 1
        for (alpha, width), start, points in runs:
            c = QtGui.QColor(base); c.setAlphaF(alpha)
            pen = QtGui.QPen(c, width, style)
            pen.setJoinStyle(QtCore.Qt.RoundJoin)
            # Flat ends between runs so they butt together instead of overlapping.
            pen.setCapStyle(QtCore.Qt.RoundCap if single and style == QtCore.Qt.SolidLine else QtCore.Qt.FlatCap)
            if style != QtCore.Qt.SolidLine:
                pen.setDashOffset(start / width)  # dash units are pen widths; keeps the pattern continuous
            painter.setPen(pen)
            painter.drawPolyline(QtGui.QPolygonF(points))

    def paintEvent(self, event):
        w, h = self.width(), self.height()
        painter = QtGui.QPainter(self)
        painter.fillRect(0, 0, w, h, QtGui.QColor(5, 6, 10))
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        proj = lambda p: self._project(p, w, h)

        painter.setPen(self._grid_pen)  # ground grid
        for i in range(-2, 3):
            g = i * 0.5
            painter.drawLine(proj((g, -1.0, -1.0)), proj((g, -1.0, 1.0)))
            painter.drawLine(proj((-1.0, -1.0, g)), proj((1.0, -1.0, g)))

        shape = self._shape_points()
        painter.setPen(self._ghost_pen)  # rest position
        rest = [proj(p) for p in shape]
        for a, b in self.EDGES: painter.drawLine(rest[a], rest[b])

        params = self.main_ui.preview_params()
        if self.vis.normalize:
            # Fit using the largest possible translate (sum of amps), so the scale doesn't jitter.
            peak = max((sum(abs(a) for _, _, a, _ in params.get(ch, [])) for ch in ('Tx', 'Ty', 'Tz')), default=0.0)
            t_scale = 0.6 / peak if peak > 1e-9 else 1.0
        else:
            t_scale = self.vis.amp_zoom
        t_now = self.vis.time_offset
        apex = shape[4]

        if self.trail_on and self.trail_len > 1:
            # Computed from the noise itself (not recorded), so it works while paused and orbiting.
            trail = [proj(self._transform_at(params, t_scale, t_now - k * self.STEP)(apex))
                     for k in range(int(self.trail_len))]
            self._draw_trail(painter, trail)

        place = self._transform_at(params, t_scale, t_now)
        pts = [proj(place(p)) for p in shape]
        painter.setPen(self._shape_pen)
        for a, b in self.EDGES: painter.drawLine(pts[a], pts[b])
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(self.COLORS.get(self.trail_color, C['orange'])))
        painter.drawEllipse(pts[4], 2.2, 2.2)  # tip marker
        painter.setBrush(QtCore.Qt.NoBrush)

        centre = proj(place((0.0, 0.0, 0.0)))  # pivot
        for pen, axis in zip(self._axis_pens, ((0.4, 0, 0), (0, 0.4, 0), (0, 0, 0.4))):
            painter.setPen(pen)
            painter.drawLine(centre, proj(place(axis)))

        painter.setPen(QtGui.QPen(QtGui.QColor(0, 243, 255, 50), 1))
        painter.drawRect(0, 0, w - 1, h - 1)
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
            # PySide sometimes calls clicked() with no 'checked' argument, so keep it optional.
            btn.clicked.connect(lambda checked=False, nt=t: self._select(nt))
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
            row.addWidget(lbl)
            row.addWidget(ValueField(slider))
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
                'freq': self.freq_slider.value(), 'offset': self.offset_slider.value(),
                'amp_max': self.amp_slider.maximum(), 'freq_max': self.freq_slider.maximum(),
                'offset_max': self.offset_slider.maximum()}

    def set_data(self, data):
        self.type_sel.setType(data.get('type', 'SINE'))
        # Raised caps first, otherwise a saved value above the built-in max would be clamped.
        self.amp_slider.setMaximum(data.get('amp_max', 0.0))
        self.freq_slider.setMaximum(data.get('freq_max', 0.0))
        self.offset_slider.setMaximum(data.get('offset_max', 0.0))
        self.amp_slider.setValue(data.get('amp', 0.1))
        self.freq_slider.setValue(data.get('freq', 2.0))
        self.offset_slider.setValue(data.get('offset', 0.0))


# --- TARGET ROW ---
class TargetRow(QtWidgets.QFrame):
    """One target object: name (click to select it in Maya and preview its seed), seed, reroll, remove."""
    def __init__(self, main_ui, name, seed, parent=None):
        super().__init__(parent)
        self.main_ui, self.name = main_ui, name
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(2, 1, 2, 1)
        lay.setSpacing(2)
        self.name_btn = QtWidgets.QPushButton(name)
        self.name_btn.setObjectName("targetName")
        self.name_btn.setToolTip(f"{name}\nClick: select in Maya and show its seed in the preview")
        self.name_btn.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed)
        self.name_btn.clicked.connect(lambda checked=False: self.main_ui.focus_target(self.name, select=True))
        self.seed_spin = QtWidgets.QSpinBox()
        self.seed_spin.setRange(0, 99999)
        self.seed_spin.setValue(seed)
        self.seed_spin.setFixedWidth(62)
        self.seed_spin.setToolTip("Seed for this target (0 = no seed variation)")
        self.seed_spin.valueChanged.connect(lambda _: self.main_ui.on_target_seed_changed(self.name))
        rnd = QtWidgets.QPushButton("RND")
        rnd.setFixedWidth(32)
        rnd.clicked.connect(lambda checked=False: self.seed_spin.setValue(self.main_ui.new_seed()))
        rm = QtWidgets.QPushButton("X")
        rm.setObjectName("delBtn")
        rm.setFixedWidth(18)
        rm.clicked.connect(lambda checked=False: self.main_ui.remove_target(self.name))
        lay.addWidget(self.name_btn, 1); lay.addWidget(self.seed_spin); lay.addWidget(rnd); lay.addWidget(rm)
        self.set_focused(False)

    def seed(self): return self.seed_spin.value()

    def set_focused(self, on):
        color = "rgba(246,162,38,0.6)" if on else "rgba(0,243,255,0.08)"
        self.setStyleSheet(f"TargetRow {{ background: rgba(5,8,15,0.8); border: 1px solid {color}; }}")


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
        self._live_sig = {}  # channel -> settings last written to its live curve
        self._maya_cb_ids = []
        # Slider drags fire dozens of changes a second; push to Maya once they settle.
        self._apply_timer = QtCore.QTimer(self)
        self._apply_timer.setSingleShot(True)
        self._apply_timer.setInterval(60)
        self._apply_timer.timeout.connect(self._debounced_apply)
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
        ver = QtWidgets.QLabel("V3.0_CORE")
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

        # Targets: every target shares the noise settings below; each has its own seed so
        # they don't move in sync.
        self.target_rows = {}  # name -> TargetRow, in the order they were added
        self._preview_target = None
        t_lay = QtWidgets.QHBoxLayout()
        t_lay.addWidget(QtWidgets.QLabel("TARGETS:"))
        t_lay.addStretch()
        set_btn = QtWidgets.QPushButton("<<< SET")
        set_btn.setToolTip("Replace the target list with the current Maya selection")
        set_btn.clicked.connect(lambda checked=False: self.set_targets_from_selection(replace=True))
        add_btn = QtWidgets.QPushButton("+ ADD")
        add_btn.setToolTip("Add the current Maya selection to the target list")
        add_btn.clicked.connect(lambda checked=False: self.set_targets_from_selection(replace=False))
        reroll_all = QtWidgets.QPushButton("REROLL ALL")
        reroll_all.clicked.connect(lambda checked=False: self.reroll_all_seeds())
        t_lay.addWidget(set_btn); t_lay.addWidget(add_btn); t_lay.addWidget(reroll_all)
        main_layout.addLayout(t_lay)
        # Fixed height (1-4 rows, then it scrolls). A merely-capped height let Qt squeeze this
        # list and the wave display into each other when the window ran short of space.
        self.t_scroll = t_scroll = QtWidgets.QScrollArea()
        t_scroll.setWidgetResizable(True)
        t_scroll.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        t_content = QtWidgets.QWidget()
        self.targets_lay = QtWidgets.QVBoxLayout(t_content)
        self.targets_lay.setContentsMargins(0, 0, 0, 0)
        self.targets_lay.setSpacing(2)
        self.targets_empty = QtWidgets.QLabel("Select objects in Maya, then <<< SET")
        self.targets_lay.addWidget(self.targets_empty)
        self.targets_lay.addStretch()
        t_scroll.setWidget(t_content)
        main_layout.addWidget(t_scroll)

        self._update_target_list_height()

        # Preview: controls, then waves + 3D box side by side
        self.channels = {}
        self.vis = VisualizerWidget(self)
        self.box3d = Box3DWidget(self, self.vis)
        self.vis.companions.append(self.box3d)
        v_ctl = QtWidgets.QHBoxLayout()
        v_ctl.setSpacing(2)
        self.view_combo = QtWidgets.QComboBox()
        self.view_combo.addItems(["BOTH", "WAVE", "3D"])
        self.view_combo.setToolTip("Which preview to show")
        v_ctl.addWidget(self.view_combo)
        for text, tip, fn in (("T-", "Zoom time out (wheel on the waves)", lambda: self.vis.zoom_time(0.8)),
                              ("T+", "Zoom time in (wheel on the waves)", lambda: self.vis.zoom_time(1.25)),
                              ("A-", "Shrink wave height and pyramid movement (Shift+wheel)", lambda: self.vis.zoom_amp(0.8)),
                              ("A+", "Grow wave height and pyramid movement (Shift+wheel)", lambda: self.vis.zoom_amp(1.25)),
                              ("1:1", "Reset zoom (double-click the waves)", lambda: self.vis.reset_view())):
            b = QtWidgets.QPushButton(text)
            b.setToolTip(tip)
            b.clicked.connect(lambda checked=False, f=fn: f())
            v_ctl.addWidget(b)
        v_ctl.addStretch()
        self.norm_btn = QtWidgets.QPushButton("NORM")
        self.norm_btn.setCheckable(True)
        self.norm_btn.setToolTip("Fit the waves (and the pyramid's movement) to the display")
        self.norm_btn.toggled.connect(self._toggle_normalize)
        self.pause_btn = QtWidgets.QPushButton("PAUSE")
        self.pause_btn.setCheckable(True)
        self.pause_btn.setToolTip("Freeze the preview (doesn't affect Maya)")
        self.pause_btn.toggled.connect(self._toggle_preview_pause)
        self.opts_btn = QtWidgets.QPushButton("3D OPT")
        self.opts_btn.setCheckable(True)
        self.opts_btn.setToolTip("Show pyramid and trail options")
        v_ctl.addWidget(self.norm_btn); v_ctl.addWidget(self.pause_btn); v_ctl.addWidget(self.opts_btn)
        main_layout.addLayout(v_ctl)
        v_row = QtWidgets.QHBoxLayout()
        v_row.setSpacing(4)
        v_row.addWidget(self.vis, 1)
        v_row.addWidget(self.box3d, 1)
        main_layout.addLayout(v_row)
        main_layout.addWidget(self._build_box_options())
        self.view_combo.currentTextChanged.connect(self._set_view_mode)
        self.opts_btn.toggled.connect(lambda on: self._set_view_mode(self.view_combo.currentText()))

        # Scroll area (the only part of the window that shrinks when space runs short)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(140)
        scroll_content = QtWidgets.QWidget()
        self.scroll_lay = QtWidgets.QVBoxLayout(scroll_content)
        self.scroll_lay.setContentsMargins(0, 4, 0, 4)
        self.scroll_lay.setSpacing(4)
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, 1)

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
            sl.valueChanged.connect(lambda _: self.auto_apply_expression())
            row.addWidget(lbl); row.addWidget(ValueField(sl, bold=True)); row.addWidget(sl)
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
        self.apply_btn.clicked.connect(self.force_apply)
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
        self.set_targets_from_selection(replace=True); self._block_auto = False; self.auto_apply_expression()
        self._install_maya_callbacks()
        self._restore_view_prefs()

    def _restore_view_prefs(self):
        view = self.prefs.get('view') or {}
        try: self.box3d.apply_settings(view.get('box'))
        except (TypeError, ValueError): self.box3d.apply_settings({})  # bad/old prefs: use defaults
        self._sync_box_controls()
        self.norm_btn.setChecked(bool(view.get('normalize', False)))
        self.opts_btn.setChecked(bool(view.get('options_open', True)))
        mode = view.get('mode', 'BOTH')
        self.view_combo.setCurrentText(mode if mode in ('BOTH', 'WAVE', '3D') else 'BOTH')
        self._set_view_mode(self.view_combo.currentText())

    # --- Pause the preview while Maya or the window is busy ---
    def _install_maya_callbacks(self):
        try:
            self._maya_cb_ids.append(om.MConditionMessage.addConditionCallback("playingBack", self._on_playing_back))
            self._maya_cb_ids.append(om.MEventMessage.addEventCallback("timeChanged", self._on_time_changed))
            # Live curves cover the playback range at the scene frame rate; rebuild if either changes.
            for ev in ("playbackRangeChanged", "timeUnitChanged"):
                self._maya_cb_ids.append(om.MEventMessage.addEventCallback(ev, self._on_range_changed))
        except Exception as e:
            om.MGlobal.displayWarning(f"NOISE.SYS: could not watch playback ({e}); preview won't auto-pause.")

    def _remove_maya_callbacks(self):
        for cb in self._maya_cb_ids:
            try: om.MMessage.removeCallback(cb)
            except Exception: pass
        self._maya_cb_ids = []

    def _on_playing_back(self, state, *args):
        try: self.vis.set_paused('playback', bool(state))
        except RuntimeError: self._remove_maya_callbacks()  # Qt side already destroyed

    def _on_range_changed(self, *args):
        try: self.auto_apply_expression()
        except RuntimeError: self._remove_maya_callbacks()

    def _on_time_changed(self, *args):
        # Fires every frame while scrubbing or playing; resume 300ms after the last one.
        try: self.vis.pause_for('scrub', 300)
        except RuntimeError: self._remove_maya_callbacks()

    def moveEvent(self, e):
        super().moveEvent(e)
        if hasattr(self, 'vis'): self.vis.pause_for('move', 250)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'vis'): self.vis.pause_for('move', 250)

    def changeEvent(self, e):
        super().changeEvent(e)
        if e.type() == QtCore.QEvent.WindowStateChange and hasattr(self, 'vis'):
            self.vis.set_paused('minimized', self.isMinimized())

    # --- Helpers ---
    def get_global_amp(self): return self.g_amp_slider.value()
    def get_global_freq(self): return self.g_freq_slider.value()
    # --- Targets ---
    def get_targets(self):
        """[(name, seed)] for every listed target that still exists in the scene."""
        return [(n, r.seed()) for n, r in self.target_rows.items() if cmds.objExists(n)]

    def get_seed(self):
        """Seed shown in the preview: the focused target's, else the first one's."""
        row = self.target_rows.get(self._preview_target) or next(iter(self.target_rows.values()), None)
        return row.seed() if row else 0

    def new_seed(self):
        used = {r.seed() for r in self.target_rows.values()}
        while True:
            s = random.randint(1, 99999)
            if s not in used: return s

    def set_targets_from_selection(self, replace=True):
        sel = cmds.ls(selection=True) or []
        if replace:
            for name in [n for n in self.target_rows if n not in sel]:
                self.remove_target(name)
        for name in sel:
            if name not in self.target_rows:
                row = TargetRow(self, name, self.new_seed())  # unique seed per new target
                self.targets_lay.insertWidget(self.targets_lay.count() - 1, row)  # above the stretch
                self.target_rows[name] = row
        if self._preview_target not in self.target_rows:
            self.focus_target(next(iter(self.target_rows), None))
        self.targets_empty.setVisible(not self.target_rows)
        self._update_target_list_height()
        self.auto_apply_expression()

    def _update_target_list_height(self):
        rows = list(self.target_rows.values())[:4]
        widgets = rows or [self.targets_empty]
        spacing = self.targets_lay.spacing() * (len(widgets) - 1)
        frame = self.t_scroll.frameWidth() * 2
        self.t_scroll.setFixedHeight(sum(wd.sizeHint().height() for wd in widgets) + spacing + frame + 2)

    # --- Preview ---
    def preview_params(self):
        """{channel: [(freq, phase, amp, type)]} for the wave display and 3D box: honours mute and
        solo, uses the focused target's seed. Amps are unscaled (scene units / degrees)."""
        g_amp, g_freq, seed = self.get_global_amp(), self.get_global_freq(), self.get_seed()
        out = {}
        for ch_name, cw in self.channels.items():
            if self.solo_channel and self.solo_channel != ch_name: continue
            if cw.is_muted(): continue
            layer_objs = cw.get_layers_objects()
            if not layer_objs: continue
            params = []
            for i, lyr_w in enumerate(layer_objs):  # index before solo filtering, same as live/bake
                if self.solo_layer_id and lyr_w.id != self.solo_layer_id: continue
                d = lyr_w.get_data()
                amp = d['amp'] * g_amp
                if amp == 0: continue
                params.append((d['freq'] * g_freq, d['offset'] + seed_phase(seed, ch_name, i), amp, d['type']))
            out[ch_name] = params
        return out

    def _build_box_options(self):
        """Two compact rows of pyramid/trail settings, bound straight to the 3D widget."""
        box = self.box3d
        self.box_opts = frame = QtWidgets.QFrame()
        frame.setStyleSheet("QFrame { background: rgba(10,12,18,0.9); border: 1px solid rgba(0,243,255,0.1); }")
        lay = QtWidgets.QVBoxLayout(frame)
        lay.setContentsMargins(4, 3, 4, 3)
        lay.setSpacing(2)
        self._box_controls = {}

        def label(text):
            l = QtWidgets.QLabel(text); l.setStyleSheet("border: none;"); return l

        def combo(key, items, tip):
            cb = QtWidgets.QComboBox(); cb.addItems(items); cb.setToolTip(tip)
            cb.currentTextChanged.connect(lambda v, k=key: box.set_option(k, v))
            self._box_controls[key] = cb; return cb

        def spin(key, cls, lo, hi, step, tip, suffix=""):
            sp = cls(); sp.setRange(lo, hi); sp.setSingleStep(step); sp.setToolTip(tip)
            if suffix: sp.setSuffix(suffix)
            sp.valueChanged.connect(lambda v, k=key: box.set_option(k, v))
            self._box_controls[key] = sp; return sp

        def toggle(key, text, tip):
            b = QtWidgets.QPushButton(text); b.setCheckable(True); b.setToolTip(tip)
            def on_toggled(on, k=key, btn=b):
                btn.setObjectName("autoLiveOn" if on else ""); btn.setStyle(btn.style())
                box.set_option(k, on)
            b.toggled.connect(on_toggled)
            self._box_controls[key] = b; return b

        r1 = QtWidgets.QHBoxLayout(); r1.setSpacing(3)
        r1.addWidget(label("TIP")); r1.addWidget(combo('axis', Box3DWidget.AXES, "Axis the pyramid's tip points along"))
        r1.addWidget(label("PIVOT")); r1.addWidget(combo('pivot', Box3DWidget.PIVOTS, "Point the noise rotates the pyramid around"))
        r1.addStretch()
        r1.addWidget(toggle('trail_on', "TRAIL", "Trace the tip's path"))
        r1.addWidget(combo('trail_color', list(Box3DWidget.COLORS), "Trail colour"))
        lay.addLayout(r1)

        r2 = QtWidgets.QHBoxLayout(); r2.setSpacing(3)
        r2.addWidget(label("LEN"))
        r2.addWidget(spin('trail_len', QtWidgets.QSpinBox, 2, 600, 5, "Trail length in preview frames (type a value)", "f"))
        r2.addWidget(label("FADE")); r2.addWidget(combo('trail_fade', Box3DWidget.FADES,
                                                       "NONE: solid   LINEAR: even   EASE: holds then drops   FAST: drops quickly"))
        width = spin('trail_width', QtWidgets.QDoubleSpinBox, 0.5, 8.0, 0.5, "Trail thickness (px)", "px")
        width.setDecimals(1)
        r2.addWidget(width)
        r2.addWidget(toggle('trail_taper', "TAPER", "Thin the trail towards its tail"))
        r2.addWidget(combo('trail_style', Box3DWidget.STYLES, "Line style"))
        lay.addLayout(r2)
        self._sync_box_controls()
        return frame

    def _sync_box_controls(self):
        """Push the 3D widget's current settings into the option controls (no feedback loops)."""
        for key, value in self.box3d.settings().items():
            w = self._box_controls[key]
            w.blockSignals(True)
            if isinstance(w, QtWidgets.QComboBox): w.setCurrentText(str(value))
            elif isinstance(w, QtWidgets.QPushButton):
                w.setChecked(bool(value)); w.setObjectName("autoLiveOn" if value else ""); w.setStyle(w.style())
            else: w.setValue(value)
            w.blockSignals(False)

    def _set_view_mode(self, mode):
        show_wave, show_3d = mode in ("BOTH", "WAVE"), mode in ("BOTH", "3D")
        self.vis.setVisible(show_wave)
        self.box3d.setVisible(show_3d)
        # Side by side the pyramid stays compact; on its own it takes the full width.
        self.box3d.setMaximumWidth(170 if show_wave else 16777215)
        self.box_opts.setVisible(show_3d and self.opts_btn.isChecked())
        self.opts_btn.setEnabled(show_3d)
        self.vis._sync_timer()

    def _toggle_normalize(self, on):
        self.norm_btn.setObjectName("autoLiveOn" if on else "")
        self.norm_btn.setStyle(self.norm_btn.style())
        self.vis.set_normalize(on)

    def _toggle_preview_pause(self, on):
        self.pause_btn.setText("PLAY" if on else "PAUSE")
        self.pause_btn.setObjectName("autoLiveOn" if on else "")
        self.pause_btn.setStyle(self.pause_btn.style())
        self.vis.set_paused('user', on)
        self.vis.refresh()  # redraw now so the PAUSED label appears

    def remove_target(self, name):
        row = self.target_rows.pop(name, None)
        if row is None: return
        # Don't leave a live rig on an object the tool no longer tracks.
        if cmds.objExists(name): self._cleanup_live_nodes(name)
        row.setParent(None); row.deleteLater()
        if self._preview_target == name: self.focus_target(next(iter(self.target_rows), None))
        self.targets_empty.setVisible(not self.target_rows)
        self._update_target_list_height()

    def focus_target(self, name, select=False):
        self._preview_target = name
        for n, r in self.target_rows.items(): r.set_focused(n == name)
        if select and name and cmds.objExists(name): cmds.select(name, replace=True)
        self._refresh_preview()  # preview uses the focused target's seed

    def on_target_seed_changed(self, name):
        self.focus_target(name)
        self.auto_apply_expression()

    def reroll_all_seeds(self):
        for row in self.target_rows.values():
            row.seed_spin.setValue(self.new_seed())

    def set_solo_channel(self, ch_name):
        if self.solo_channel == ch_name: self.solo_channel = None
        else: self.solo_channel, self.solo_layer_id = ch_name, None
        for name, cw in self.channels.items():
            cw.update_solo_visual(name == self.solo_channel)
            for lyr in cw.get_layers_objects(): lyr.update_solo_visual(False)
        self._refresh_preview()

    def set_solo_layer(self, layer_id):
        if self.solo_layer_id == layer_id: self.solo_layer_id = None
        else: self.solo_layer_id, self.solo_channel = layer_id, None
        for name, cw in self.channels.items():
            cw.update_solo_visual(False)
            for lyr in cw.get_layers_objects(): lyr.update_solo_visual(lyr.id == self.solo_layer_id)
        self._refresh_preview()

    def get_current_state(self):
        state = {'global_amp': self.g_amp_slider.value(), 'global_freq': self.g_freq_slider.value(),
                 'global_amp_max': self.g_amp_slider.maximum(), 'global_freq_max': self.g_freq_slider.maximum(),
                 'channels': {}}  # seeds belong to scene targets, so they aren't stored in presets
        for name, cw in self.channels.items():
            state['channels'][name] = {'muted': cw.is_muted(), 'layers': cw.get_layers()}
        return state

    def apply_state(self, state):
        if not state: return
        self._block_auto = True
        try:
            self.g_amp_slider.setMaximum(state.get('global_amp_max', 0.0))  # before value, so it isn't clamped
            self.g_freq_slider.setMaximum(state.get('global_freq_max', 0.0))
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
        self._apply_timer.stop()
        self._remove_maya_callbacks()
        self.vis.set_paused('closed', True)
        for target, _ in self.get_targets(): self._cleanup_live_nodes(target)
        self.prefs['last_state'] = self.get_current_state()
        self.prefs['view'] = {'mode': self.view_combo.currentText(), 'options_open': self.opts_btn.isChecked(),
                              'normalize': self.norm_btn.isChecked(), 'box': self.box3d.settings()}
        save_prefs(self.prefs)
        super().closeEvent(event)

    def toggle_auto_live(self):
        if self.auto_btn.isChecked():
            self.auto_btn.setText("[X] AUTO-LIVE")
            self.auto_btn.setObjectName("autoLiveOn")
            self.auto_btn.setStyle(self.auto_btn.style())
            self.force_apply()
        else:
            self.auto_btn.setText("[ ] AUTO-LIVE")
            self.auto_btn.setObjectName("")
            self.auto_btn.setStyle(self.auto_btn.style())
            for target, _ in self.get_targets(): self._cleanup_live_nodes(target)

    def _refresh_preview(self):
        # Redraw even while the preview is paused, so edits still show on the frozen waves/box.
        if hasattr(self, 'vis'): self.vis.refresh()

    def auto_apply_expression(self):
        self._refresh_preview()  # every settings change comes through here
        if not self._block_auto and hasattr(self, 'auto_btn') and self.auto_btn.isChecked():
            # Throttle, not debounce: continuous drags (or Shift-growing a cap) still update Maya
            # every 60ms, and the pending apply always reads the latest values when it fires.
            if not self._apply_timer.isActive(): self._apply_timer.start()

    def _debounced_apply(self):
        # Re-check: a bake or revert may have switched AUTO-LIVE off while this was pending.
        if self.auto_btn.isChecked(): self.apply_live()

    def force_apply(self):
        self._live_sig = {}  # rewrite every curve even if settings look unchanged
        self.apply_live()

    def map_maya_attr(self, ch_name):
        return {'Tx': 'translateX', 'Ty': 'translateY', 'Tz': 'translateZ',
                'Rx': 'rotateX', 'Ry': 'rotateY', 'Rz': 'rotateZ'}.get(ch_name)

    # Namespaced targets (e.g. "ns:SpineMain") would put our helper nodes inside a
    # reference namespace, so flatten ':' and '|' into '_' for helper node names.
    def _safe_name(self, target): return target.replace(':', '_').replace('|', '_')
    def _get_pma_name(self, target, ch_name): return f"{self._safe_name(target)}_noisePMA_{ch_name}"
    def _get_curve_name(self, target, ch_name): return f"{self._safe_name(target)}_noiseCrv_{ch_name}"
    def _get_expr_name(self, target): return f"{self._safe_name(target)}_noise_sys_expr"  # legacy

    def _is_referenced(self, node):
        try: return cmds.referenceQuery(node, isNodeReferenced=True)
        except RuntimeError: return False

    # --- Live network -------------------------------------------------------------------
    # Per channel:  noise animCurve --> PMA.input1D[1]
    #               original driver/value --> PMA.input1D[0]
    #               PMA.output1D --> target.translateX (etc.)
    # The curve holds one key per frame over the playback range. Maya evaluates animCurves
    # natively (parallel + cached playback friendly), far cheaper than a MEL expression.

    def _live_frames(self):
        start = int(math.floor(cmds.playbackOptions(q=True, minTime=True)))
        end = int(math.ceil(cmds.playbackOptions(q=True, maxTime=True)))
        return range(start, end + 1)

    def _channel_noise_values(self, ch_widget, frames, seed):
        """Per-frame noise for one channel on one target, in Maya UI units (degrees for rotate)."""
        g_amp, g_freq = self.get_global_amp(), self.get_global_freq()
        params = [(l['freq'] * g_freq, l['offset'] + seed_phase(seed, ch_widget.name, i), l['amp'] * g_amp, l['type'])
                  for i, l in enumerate(ch_widget.get_layers()) if l['amp'] * g_amp != 0.0]
        base = ch_widget.get_base_value()
        spf = self._frame_to_seconds(1)
        wave = get_noise_val
        return [base + sum(wave(f * spf * fr + o, ty, frame=f, offset=o) * a for fr, o, a, ty in params)
                for f in frames], tuple(params)

    def _write_curve(self, crv, frames, values):
        sel = om.MSelectionList(); sel.add(crv)
        fn = oma.MFnAnimCurve(sel.getDependNode(0))
        unit = om.MTime.uiUnit()
        n = len(values)
        if n and fn.numKeys == n and fn.input(0).asUnits(unit) == frames[0] \
                and fn.input(n - 1).asUnits(unit) == frames[-1]:
            for i, v in enumerate(values): fn.setValue(i, v)  # same frames: just move the keys
            return
        for i in range(fn.numKeys - 1, -1, -1): fn.remove(i)
        times, vals = om.MTimeArray(), om.MDoubleArray()
        for f, v in zip(frames, values):
            times.append(om.MTime(f, unit)); vals.append(v)
        fn.addKeys(times, vals, oma.MFnAnimCurve.kTangentLinear, oma.MFnAnimCurve.kTangentLinear)

    def _ensure_live_nodes(self, target, ch):
        """Create/repair the curve + PMA for one channel. Returns the curve name, or None."""
        full_attr = f"{target}.{self.map_maya_attr(ch)}"
        pma, crv = self._get_pma_name(target, ch), self._get_curve_name(target, ch)
        try:
            if not cmds.objExists(pma):
                if cmds.getAttr(full_attr, lock=True):
                    cmds.warning(f"NOISE.SYS: {full_attr} is locked; live noise skipped for {ch}.")
                    return None
                driver = cmds.listConnections(full_attr, s=True, d=False, plugs=True)
                val = cmds.getAttr(full_attr)
                cmds.createNode('plusMinusAverage', n=pma, skipSelect=True)
                cmds.setAttr(f"{pma}.operation", 1)
                if driver:
                    cmds.disconnectAttr(driver[0], full_attr)
                    cmds.connectAttr(driver[0], f"{pma}.input1D[0]")
                else:
                    cmds.setAttr(f"{pma}.input1D[0]", val)
                cmds.connectAttr(f"{pma}.output1D", full_attr, force=True)
            if not cmds.objExists(crv):
                cmds.createNode('animCurveTU', n=crv, skipSelect=True)
            if not cmds.isConnected(f"{crv}.output", f"{pma}.input1D[1]"):
                cmds.connectAttr(f"{crv}.output", f"{pma}.input1D[1]", force=True)
            return crv
        except Exception as e:
            cmds.warning(f"NOISE.SYS: could not build live noise on {full_attr}: {e}")
            return None

    def apply_live(self):
        for target, seed in self.get_targets():
            self._apply_live_target(target, seed)

    def _apply_live_target(self, target, seed):
        active, inactive = [], []
        for ch_name, ch_widget in self.channels.items():
            (inactive if ch_widget.is_muted() or not ch_widget.get_layers() else active).append(ch_name)
        if not active: self._cleanup_live_nodes(target); return
        frames = self._live_frames()
        dirty = []
        for ch in active:
            values, params = self._channel_noise_values(self.channels[ch], frames, seed)
            sig = (params, frames.start, frames.stop, self._frame_to_seconds(1))  # params include the seed
            crv = self._get_curve_name(target, ch)
            if self._live_sig.get((target, ch)) == sig and cmds.objExists(crv) and cmds.objExists(self._get_pma_name(target, ch)):
                continue  # unchanged; don't touch Maya
            crv = self._ensure_live_nodes(target, ch)
            if not crv: continue
            self._write_curve(crv, frames, values)
            self._live_sig[(target, ch)] = sig
            dirty.append(crv)
        for ch in inactive: self._cleanup_single_channel(target, ch)
        if dirty: cmds.dgdirty(dirty)  # API key edits: make sure the viewport picks them up

    # --- Cleanup ---------------------------------------------------------------------------
    def _delete_nodes(self, nodes):
        """Delete our helper nodes plus any unitConversion nodes Maya inserted for them."""
        nodes = [n for n in nodes if cmds.objExists(n) and not self._is_referenced(n)]
        if not nodes: return
        convs = set(cmds.listConnections(nodes, type='unitConversion') or [])
        cmds.delete(nodes)
        for c in convs:
            if cmds.objExists(c) and not self._is_referenced(c) and not cmds.listConnections(c):
                cmds.delete(c)

    def _cleanup_single_channel(self, target, ch):
        self._live_sig.pop((target, ch), None)
        full_attr = f"{target}.{self.map_maya_attr(ch)}"
        # Current name first, then the pre-namespace-fix name older versions created.
        for pma in (self._get_pma_name(target, ch), f"{target}_noisePMA_{ch}"):
            if not cmds.objExists(pma) or self._is_referenced(pma): continue
            # Look through Maya's auto-inserted unitConversion nodes (rotate channels have them
            # on both sides of the PMA), otherwise the disconnect misses and the restore fails.
            driver = cmds.listConnections(f"{pma}.input1D[0]", s=True, d=False, plugs=True, skipConversionNodes=True)
            static_val = cmds.getAttr(f"{pma}.input1D[0]")
            feeds = cmds.listConnections(full_attr, s=True, d=False, skipConversionNodes=True) or []
            if pma in feeds:
                direct = cmds.listConnections(full_attr, s=True, d=False, plugs=True) or []
                if direct: cmds.disconnectAttr(direct[0], full_attr)
            try:
                if driver: cmds.connectAttr(driver[0], full_attr, force=True)
                else: cmds.setAttr(full_attr, static_val)
            except Exception as e:
                print(f"NOISE.SYS cleanup warning: could not restore {full_attr}: {e}")
            self._delete_nodes([pma])
        self._delete_nodes([self._get_curve_name(target, ch)])
        # Driver attrs from the old expression-based versions.
        for cust_attr in (f"noise_{ch}", f"noiseSys_{ch}"):
            if not cmds.attributeQuery(cust_attr, node=target, exists=True): continue
            try:
                cmds.setAttr(f"{target}.{cust_attr}", lock=False)
                cmds.deleteAttr(target, attribute=cust_attr)
            except RuntimeError:
                pass  # attr belongs to a referenced file; can't remove it from here

    def _cleanup_live_nodes(self, target):
        self._delete_nodes([self._get_expr_name(target), f"{target}_noise_sys_expr"])  # legacy
        for ch in ['Tx', 'Ty', 'Tz', 'Rx', 'Ry', 'Rz']:
            self._cleanup_single_channel(target, ch)

    def _set_auto_live_off(self):
        self._apply_timer.stop()
        if self.auto_btn.isChecked():
            self.auto_btn.setChecked(False)
            self.auto_btn.setText("[ ] AUTO-LIVE")
            self.auto_btn.setObjectName("")
            self.auto_btn.setStyle(self.auto_btn.style())

    def revert_target(self):
        targets = [t for t, _ in self.get_targets()]
        if not targets:
            cmds.warning("NOISE.SYS: No valid target to revert."); return
        self._set_auto_live_off()
        cmds.undoInfo(openChunk=True, chunkName="RevertNoiseSys")
        try:
            for target in targets: self._cleanup_live_nodes(target)
            cmds.warning(f"NOISE.SYS: System dismantled. {len(targets)} target(s) restored.")
        except Exception as e: cmds.warning(f"NOISE.SYS Revert Error: {str(e)}")
        finally: cmds.undoInfo(closeChunk=True)

    # --- Bake ---------------------------------------------------------------------------------
    def bake_to_timeline(self): self._bake_logic(use_layer=False)
    def bake_to_anim_layer(self): self._bake_logic(use_layer=True)

    def _bake_logic(self, use_layer):
        """One click: for every target, build live from the UI (with that target's seed), bake
        exactly what it shows, and remove every live node. See _bake_target for the steps."""
        targets = self.get_targets()
        if not targets:
            cmds.warning("NOISE.SYS: No valid target."); return
        self._set_auto_live_off()
        frames = self._live_frames()
        bake_chans = [ch for ch, w in self.channels.items() if not w.is_muted() and w.get_layers()]
        if not bake_chans:
            cmds.warning("NOISE.SYS: Nothing to bake."); return

        # Lock the window and show a wait cursor: the bake blocks Maya, and any click made
        # meanwhile would otherwise run AFTER it (e.g. FORCE APPLY rebuilding the live nodes).
        self.setEnabled(False)
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        QtWidgets.QApplication.processEvents()
        # One chunk for everything, so a single undo restores the pre-bake scene.
        cmds.undoInfo(openChunk=True, chunkName="BakeNoiseSys")
        cmds.refresh(suspend=True)
        try:
            total, worst, notes = 0, 0.0, []
            for target, seed in targets:
                try:
                    n, w, t_notes = self._bake_target(target, seed, use_layer, frames, bake_chans)
                    total += n; worst = max(worst, w); notes += t_notes
                except Exception as e:
                    notes.append(f"{target}: bake failed ({e})")
                    self._cleanup_live_nodes(target)  # never leave a half-built rig behind
            for n in notes: cmds.warning(f"NOISE.SYS: {n}")
            where = "their NoiseSys layers" if use_layer else "the base animation"
            msg = (f"NOISE.SYS: Baked {total} channel(s) on {len(targets)} target(s), frames "
                   f"{frames.start}-{frames.stop - 1}, into {where}. "
                   f"Max difference from live view: {worst:.6f}. Live nodes removed.")
            if worst > 1e-3: cmds.warning(msg + " Larger than expected: check other layers or constraints on these channels.")
            else: om.MGlobal.displayInfo(msg)
        finally:
            cmds.refresh(suspend=False)
            cmds.undoInfo(closeChunk=True)
            # Swallow clicks queued during the bake while still disabled, then unlock.
            QtWidgets.QApplication.processEvents()
            QtWidgets.QApplication.restoreOverrideCursor()
            self.setEnabled(True)

    def _bake_target(self, target, seed, use_layer, frames, bake_chans):
        """Bake one target. Returns (channels baked, max difference from live, notes).

        1. If re-baking into this target's NoiseSys layer, strip these channels out of it first,
           so the previous bake's noise isn't measured as part of the "live" result.
        2. Build this target's live network from the current UI and its seed.
        3. Read the final attribute value Maya evaluates at every frame  -> 'live'.
        4. Tear the live network down (original connections/values come back).
        5. Read the original value at every frame                        -> 'orig'.
           noise = live - orig, measured from Maya itself, not recomputed.
        6. Key it in bulk, then read the result back and compare with 'live'.
        """
        layer_name = f"{self._safe_name(target)}_NoiseSys_Layer"
        if cmds.objExists(layer_name):
            in_layer = cmds.animLayer(layer_name, q=True, attribute=True) or []
            for ch in bake_chans:
                full_attr = f"{target}.{self.map_maya_attr(ch)}"
                if full_attr in in_layer:
                    cmds.animLayer(layer_name, edit=True, removeAttribute=full_attr)

        for ch in bake_chans: self._live_sig.pop((target, ch), None)
        self._apply_live_target(target, seed)

        # Pass 1: sample the live result, remembering each channel's original driver.
        chans = []
        for ch_name in bake_chans:
            pma = self._get_pma_name(target, ch_name)
            if not cmds.objExists(pma): continue  # live couldn't be built (locked etc.), already warned
            attr_name = self.map_maya_attr(ch_name)
            full_attr = f"{target}.{attr_name}"
            src = cmds.listConnections(f"{pma}.input1D[0]", s=True, d=False, skipConversionNodes=True) or []
            src_type = cmds.nodeType(src[0]) if src else ""
            kind = ('static' if not src else 'curve' if src_type.startswith('animCurve')
                    else 'layered' if src_type.startswith('animBlendNode') else 'driven')
            live = [cmds.getAttr(full_attr, time=f) for f in frames]
            chans.append({'attr': attr_name, 'full': full_attr, 'kind': kind, 'src': src, 'live': live})

        # Pass 2: remove everything live and measure the untouched animation.
        self._cleanup_live_nodes(target)
        if not chans: return 0, 0.0, []
        for c in chans:
            if use_layer or c['kind'] == 'layered':  # base bakes of other kinds key 'live' directly
                c['orig'] = [cmds.getAttr(c['full'], time=f) for f in frames]
                c['noise'] = [l - o for l, o in zip(c['live'], c['orig'])]

        # Pass 3: key.
        baked, notes = [], []
        if use_layer:
            layer_chans = [c for c in chans if c['kind'] != 'driven']
            for c in chans:
                if c['kind'] == 'driven':
                    notes.append(f"{c['full']} is driven by {c['src'][0]}; layers can't sit on it, use BAKE_TO_BASE")
            if layer_chans:
                if not cmds.objExists(layer_name): cmds.animLayer(layer_name, override=False)
                # A muted or half-weighted layer would not reproduce the live view.
                cmds.animLayer(layer_name, edit=True, mute=False, weight=1.0)
            for c in layer_chans:
                cmds.animLayer(layer_name, edit=True, attribute=c['full'])
                self._key_values(target, c['attr'], frames, c['noise'], layer_name)
                baked.append(c)
        else:
            root = cmds.animLayer(q=True, root=True) if any(c['kind'] == 'layered' for c in chans) else None
            for c in chans:
                if c['kind'] == 'layered':
                    # getAttr returns every layer blended; key the base layer's own curve instead.
                    curves = cmds.animLayer(root, q=True, findCurveForPlug=c['full']) or []
                    if not curves:
                        notes.append(f"{c['full']} has no curve on {root}; key it there first"); continue
                    base = [cmds.keyframe(curves[0], q=True, eval=True, time=(f, f))[0] for f in frames]
                    self._key_values(target, c['attr'], frames, [b + n for b, n in zip(base, c['noise'])], root)
                else:
                    if c['kind'] == 'driven':
                        # Constraint/other node: the only way to keep what live showed is to flatten it.
                        plug = cmds.listConnections(c['full'], s=True, d=False, plugs=True) or []
                        if plug: cmds.disconnectAttr(plug[0], c['full'])
                        notes.append(f"{c['full']} was driven by {c['src'][0]}; flattened to keys")
                    self._key_values(target, c['attr'], frames, c['live'], None)
                baked.append(c)

        # Pass 4: prove it. Compare the baked result with what live showed.
        worst = 0.0
        for c in baked:
            after = [cmds.getAttr(c['full'], time=f) for f in frames]
            worst = max([worst] + [abs(a - l) for a, l in zip(after, c['live'])])
        return len(baked), worst, notes

    def _key_values(self, target, attr_name, frames, values, anim_layer):
        """Write one key per frame in bulk: fill a temporary curve through the API, then
        copyKey/pasteKey it onto the channel. Paste is native and undoable, and far faster than
        a setKeyframe call per frame. Linear tangents match the live curve (no spline overshoot)."""
        full_attr = f"{target}.{attr_name}"
        attr_type = cmds.getAttr(full_attr, type=True)
        crv_type = {'doubleAngle': 'animCurveTA', 'doubleLinear': 'animCurveTL'}.get(attr_type, 'animCurveTU')
        kw = {'animLayer': anim_layer} if anim_layer else {}
        tmp = cmds.createNode(crv_type, n="noiseSys_bakeTmp#", skipSelect=True)
        try:
            sel = om.MSelectionList(); sel.add(tmp)
            fn = oma.MFnAnimCurve(sel.getDependNode(0))
            unit = om.MTime.uiUnit()
            times, vals = om.MTimeArray(), om.MDoubleArray()
            for f, v in zip(frames, values):
                times.append(om.MTime(f, unit))
                # The API stores internal units (cm / radians); the values are in UI units.
                if crv_type == 'animCurveTA': v = om.MAngle(v, om.MAngle.uiUnit()).asRadians()
                elif crv_type == 'animCurveTL': v = om.MDistance(v, om.MDistance.uiUnit()).asCentimeters()
                vals.append(v)
            fn.addKeys(times, vals, oma.MFnAnimCurve.kTangentLinear, oma.MFnAnimCurve.kTangentLinear)
            cmds.copyKey(tmp)
            cmds.pasteKey(target, attribute=attr_name, option='replace', time=(frames[0], frames[-1]), **kw)
        except Exception as e:
            print(f"NOISE.SYS: bulk paste failed on {full_attr} ({e}); keying frame by frame instead.")
            for f, v in zip(frames, values):
                cmds.setKeyframe(target, attribute=attr_name, t=f, v=v, itt='linear', ott='linear', **kw)
        finally:
            if cmds.objExists(tmp): cmds.delete(tmp)

    def _frame_to_seconds(self, f):
        return om.MTime(f, om.MTime.uiUnit()).asUnits(om.MTime.kSeconds)

# Keep the previous window when this script is re-run in the Script Editor, so it gets closed
# properly (removing its Maya callbacks and live nodes) instead of being orphaned.
noise_window = globals().get('noise_window')
def showUI():
    global noise_window
    if noise_window:
        try: noise_window.close()
        except RuntimeError: pass  # already deleted on the Qt side
    noise_window = NoiseSysWindow(); noise_window.show()

if __name__ == "__main__": showUI()