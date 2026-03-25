import maya.cmds as cmds
import maya.api.OpenMaya as om
import math
import json
import os
import random

# Dynamic Qt Import for Maya 2024- (PySide2) and Maya 2025+ (PySide6)
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


# --- STYLE SHEET (Marathon Terminal Aesthetic) ---
QSS = """
QWidget { background-color: #050705; color: #5cfc3a; font-family: "Courier New", Consolas, monospace; font-size: 11px; font-weight: bold; }
QScrollArea { border: none; }
QScrollBar:vertical { background: #050705; width: 8px; }
QScrollBar::handle:vertical { background: #2a6b1c; min-height: 20px; }
QPushButton { background-color: #0b120b; border: 1px solid #5cfc3a; color: #5cfc3a; padding: 4px; }
QPushButton:hover { background-color: #5cfc3a; color: #000; }
QPushButton#bakeBtn { border-color: #f6a226; color: #f6a226; font-size: 14px; padding: 6px; }
QPushButton#bakeBtn:hover { background-color: #f6a226; color: #000; }
QPushButton#applyBtn { border-color: #44aaff; color: #44aaff; font-size: 14px; padding: 6px; }
QPushButton#applyBtn:hover { background-color: #44aaff; color: #000; }
QPushButton#revertBtn { border-color: #ff4444; color: #ff4444; font-size: 11px; padding: 4px; }
QPushButton#revertBtn:hover { background-color: #ff4444; color: #000; }
QPushButton#delBtn:hover { color: #ff4444; border-color: #ff4444; }
QSlider::groove:horizontal { border: 1px solid #1a3a14; height: 4px; background: #1a3a14; }
QSlider::handle:horizontal { background: #5cfc3a; width: 8px; margin: -6px 0; }
QLineEdit, QComboBox { background-color: #000; border: 1px solid #1a3a14; color: #5cfc3a; padding: 2px; }
QComboBox::drop-down { border: none; }
QLabel { background: transparent; }
"""

# --- MATH HELPERS ---
def pseudo_perlin(x):
    return (math.sin(x) + math.sin(x * 2.2 + 1.52) + math.sin(x * 4.3 + 0.3)) / 3.0

def get_noise_val(t, ntype):
    if ntype == 'SQUARE': return 1.0 if math.sin(t) >= 0 else -1.0
    if ntype == 'TRIANGLE': return (2.0 / math.pi) * math.asin(math.sin(t))
    if ntype == 'SAW': return 2.0 * (t / (2.0 * math.pi) - math.floor(0.5 + t / (2.0 * math.pi)))
    if ntype == 'PERLIN': return pseudo_perlin(t)
    if ntype == 'RANDOM': return random.uniform(-1.0, 1.0)
    return math.sin(t) # SINE

NOISE_TYPES = ['SINE', 'SQUARE', 'TRIANGLE', 'SAW', 'PERLIN', 'RANDOM']

# --- WIDGETS ---
class VisualizerWidget(QtWidgets.QWidget):
    def __init__(self, main_ui, parent=None):
        super(VisualizerWidget, self).__init__(parent)
        self.main_ui = main_ui
        self.setFixedHeight(128)
        self.time_offset = 0.0
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(33)

    def update_frame(self):
        self.time_offset += 0.05
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = self.rect()
        w, h = rect.width(), rect.height()

        painter.fillRect(rect, QtGui.QColor("#050705"))
        painter.setPen(QtGui.QPen(QtGui.QColor("#0e180e"), 1))
        for i in range(0, w, 20): painter.drawLine(i, 0, i, h)
        for i in range(0, h, 20): painter.drawLine(0, i, w, i)
        painter.setPen(QtGui.QPen(QtGui.QColor("#1a2a14"), 1))
        painter.drawLine(0, h/2, w, h/2)

        global_amp = self.main_ui.get_global_amp()
        global_freq = self.main_ui.get_global_freq()
        
        solo_ch = self.main_ui.solo_channel
        solo_lyr_id = self.main_ui.solo_layer_id
        
        for ch_name, ch_widget in self.main_ui.channels.items():
            if solo_ch and solo_ch != ch_name: continue
            if ch_widget.is_muted(): continue
            
            color = "#ff4444" if 'x' in ch_name.lower() else "#44ff44" if 'y' in ch_name.lower() else "#44aaff"
            painter.setPen(QtGui.QPen(QtGui.QColor(color), 1.5))
            
            path = QtGui.QPainterPath()
            layers = ch_widget.get_layers_objects()
            if not layers: continue

            for x in range(w):
                t_base = (x * 0.04) + self.time_offset
                y_sum = 0
                for lyr_widget in layers:
                    lyr = lyr_widget.get_data()
                    if solo_lyr_id and lyr_widget.id != solo_lyr_id: continue
                    t = t_base * (lyr['freq'] * global_freq) + lyr['offset']
                    y_sum += get_noise_val(t, lyr['type']) * (lyr['amp'] * global_amp * 30.0)
                
                if x == 0: path.moveTo(x, (h/2) - y_sum)
                else: path.lineTo(x, (h/2) - y_sum)
            painter.drawPath(path)

        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 50), 1))
        for i in range(0, h, 2): painter.drawLine(0, i, w, i)


class LayerWidget(QtWidgets.QFrame):
    def __init__(self, main_ui, parent=None):
        super(LayerWidget, self).__init__(parent)
        self.main_ui = main_ui
        self.id = str(random.random())
        self.setStyleSheet("QFrame { background-color: #050805; border: 1px solid #1a3a14; }")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header_lay = QtWidgets.QHBoxLayout()
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.addItems(NOISE_TYPES)
        self.type_combo.currentIndexChanged.connect(lambda _: self.main_ui.auto_apply_expression())
        
        self.solo_btn = QtWidgets.QPushButton("[S]")
        self.solo_btn.setFixedSize(20, 20)
        self.solo_btn.clicked.connect(self.toggle_solo)
        
        self.del_btn = QtWidgets.QPushButton("[DEL]")
        self.del_btn.setObjectName("delBtn")
        self.del_btn.setFixedSize(30, 20)
        self.del_btn.clicked.connect(self.delete_layer)
        
        header_lay.addWidget(self.type_combo)
        header_lay.addStretch()
        header_lay.addWidget(self.solo_btn)
        header_lay.addWidget(self.del_btn)
        layout.addLayout(header_lay)

        self.amp_slider, self.amp_val = self.add_slider_row(layout, "AMP", 0, 200, 10)
        self.freq_slider, self.freq_val = self.add_slider_row(layout, "FREQ", 0, 2000, 200)
        self.offset_slider, self.offset_val = self.add_slider_row(layout, "OFFSET", 0, 1000, 0)

    def toggle_solo(self):
        self.main_ui.set_solo_layer(self.id)

    def update_solo_visual(self, is_solo):
        if is_solo: self.solo_btn.setStyleSheet("background-color: #f6a226; color: #000; border-color: #f6a226;")
        else: self.solo_btn.setStyleSheet("")

    def delete_layer(self):
        if self.main_ui.solo_layer_id == self.id: self.main_ui.set_solo_layer(None)
        self.deleteLater()
        QtCore.QTimer.singleShot(50, self.main_ui.auto_apply_expression)

    def add_slider_row(self, parent_lay, label, vmin, vmax, vdefault):
        lay, lbl, val_lbl = QtWidgets.QVBoxLayout(), QtWidgets.QLabel(label), QtWidgets.QLabel(str(vdefault/100.0))
        lay.setSpacing(0)
        top_lay = QtWidgets.QHBoxLayout()
        top_lay.addWidget(lbl); top_lay.addStretch(); top_lay.addWidget(val_lbl)
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(vmin, vmax); slider.setValue(vdefault)
        def on_change(v): val_lbl.setText(str(v/100.0)); self.main_ui.auto_apply_expression()
        slider.valueChanged.connect(on_change)
        lay.addLayout(top_lay); lay.addWidget(slider); parent_lay.addLayout(lay)
        return slider, val_lbl

    def get_data(self):
        return {'type': self.type_combo.currentText(), 'amp': self.amp_slider.value() / 100.0, 'freq': self.freq_slider.value() / 100.0, 'offset': self.offset_slider.value() / 100.0}

    def set_data(self, data):
        self.type_combo.setCurrentText(data.get('type', 'SINE'))
        self.amp_slider.setValue(int(data.get('amp', 0.1) * 100))
        self.freq_slider.setValue(int(data.get('freq', 2.0) * 100))
        self.offset_slider.setValue(int(data.get('offset', 0.0) * 100))


class ChannelWidget(QtWidgets.QFrame):
    def __init__(self, name, main_ui, parent=None):
        super(ChannelWidget, self).__init__(parent)
        self.main_ui, self.name, self.muted = main_ui, name, False
        color = "#ff4444" if 'x' in name.lower() else "#44ff44" if 'y' in name.lower() else "#44aaff"
        self.setStyleSheet(f"QFrame {{ background-color: #0b120b; border: 1px solid #1a3a14; border-left: 3px solid {color}; }}")
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(6, 6, 6, 6)
        h_lay = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel(name); title.setStyleSheet("font-size: 14px;")
        self.base_val = QtWidgets.QLineEdit("0.0"); self.base_val.setFixedWidth(40); self.base_val.textChanged.connect(lambda _: self.main_ui.auto_apply_expression())
        self.add_btn = QtWidgets.QPushButton("+LAY"); self.add_btn.setFixedSize(35, 20); self.add_btn.clicked.connect(self.add_layer)
        self.solo_btn = QtWidgets.QPushButton("[S]"); self.solo_btn.setFixedSize(20, 20); self.solo_btn.clicked.connect(self.toggle_solo)
        self.mute_btn = QtWidgets.QPushButton("MUTE"); self.mute_btn.setFixedSize(35, 20); self.mute_btn.clicked.connect(self.toggle_mute)
        h_lay.addWidget(title); h_lay.addStretch(); h_lay.addWidget(self.base_val); h_lay.addWidget(self.add_btn); h_lay.addWidget(self.solo_btn); h_lay.addWidget(self.mute_btn)
        self.layout.addLayout(h_lay); self.layers_lay = QtWidgets.QVBoxLayout(); self.layout.addLayout(self.layers_lay)

    def toggle_solo(self): self.main_ui.set_solo_channel(self.name)
    def update_solo_visual(self, is_solo):
        if is_solo: self.solo_btn.setStyleSheet("background-color: #f6a226; color: #000; border-color: #f6a226;")
        else: self.solo_btn.setStyleSheet("")
    def add_layer(self): lyr = LayerWidget(self.main_ui); self.layers_lay.addWidget(lyr); self.main_ui.auto_apply_expression()
    def add_layer_with_data(self, data): lyr = LayerWidget(self.main_ui); lyr.set_data(data); self.layers_lay.addWidget(lyr)
    def clear_layers(self):
        for i in reversed(range(self.layers_lay.count())):
            widget = self.layers_lay.itemAt(i).widget()
            if widget: widget.setParent(None); widget.deleteLater()
    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted: self.mute_btn.setStyleSheet("background-color: #440000; border-color: #ff4444;")
        else: self.mute_btn.setStyleSheet("")
        self.main_ui.auto_apply_expression()
    def is_muted(self): return self.muted
    def get_layers_objects(self):
        objs = []
        for i in range(self.layers_lay.count()):
            widget = self.layers_lay.itemAt(i).widget()
            if widget: objs.append(widget)
        return objs
    def get_layers(self): return [obj.get_data() for obj in self.get_layers_objects()]
    def get_base_value(self):
        try: return float(self.base_val.text())
        except ValueError: return 0.0


class NoiseSysWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(NoiseSysWindow, self).__init__()
        self.setWindowTitle("NOISE.SYS // JITTER MATRIX")
        self.setMinimumWidth(340); self.resize(360, 800); self.setStyleSheet(QSS); self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self._block_auto, self.solo_channel, self.solo_layer_id = True, None, None
        self.prefs = load_prefs()
        central = QtWidgets.QWidget(); self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central); main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)
        
        # Header
        preset_frame = QtWidgets.QFrame(); preset_frame.setStyleSheet("background-color: #0b120b; border-bottom: 1px solid #1a3a14;")
        p_lay = QtWidgets.QHBoxLayout(preset_frame); p_lay.setContentsMargins(8, 4, 8, 4)
        self.preset_combo = QtWidgets.QComboBox(); self.preset_combo.addItem("--- PRESETS ---")
        for p in self.prefs.get("presets", {}).keys(): self.preset_combo.addItem(p)
        self.preset_combo.currentIndexChanged.connect(self.load_preset)
        save_btn, del_preset_btn = QtWidgets.QPushButton("[ SAVE ]"), QtWidgets.QPushButton("[ DEL ]")
        save_btn.clicked.connect(self.save_preset); del_preset_btn.clicked.connect(self.delete_preset)
        p_lay.addWidget(self.preset_combo); p_lay.addWidget(save_btn); p_lay.addWidget(del_preset_btn); main_layout.addWidget(preset_frame)

        # Target
        target_frame = QtWidgets.QFrame(); target_frame.setStyleSheet("background-color: #081008; border-bottom: 1px solid #2a6b1c;")
        t_lay = QtWidgets.QHBoxLayout(target_frame); t_lay.setContentsMargins(8, 6, 8, 6)
        t_lay.addWidget(QtWidgets.QLabel("TARGET:"))
        self.target_line = QtWidgets.QLineEdit(); self.target_line.setReadOnly(True); self.target_line.setStyleSheet("background-color: #000; color: #f6a226; font-weight: bold; border: 1px solid #2a6b1c;")
        t_btn = QtWidgets.QPushButton("[ <<< ]"); t_btn.clicked.connect(self.load_target)
        t_lay.addWidget(self.target_line); t_lay.addWidget(t_btn); main_layout.addWidget(target_frame)

        # Visualizer
        self.channels = {}; self.vis = VisualizerWidget(self); main_layout.addWidget(self.vis)

        # Scroll
        scroll = QtWidgets.QScrollArea(); scroll.setWidgetResizable(True)
        scroll_content = QtWidgets.QWidget(); self.scroll_lay = QtWidgets.QVBoxLayout(scroll_content); self.scroll_lay.setContentsMargins(8, 8, 8, 8); self.scroll_lay.setSpacing(8)
        scroll.setWidget(scroll_content); main_layout.addWidget(scroll)

        # Global
        global_group = QtWidgets.QFrame(); global_group.setStyleSheet("background-color: #081008; border-left: 2px solid #f6a226;")
        g_lay = QtWidgets.QVBoxLayout(global_group); g_lay.addWidget(QtWidgets.QLabel("GLOBAL_MODS"))
        self.g_amp, self.g_amp_lbl = self.add_global_slider(g_lay, "AMP MULT", 0, 400, 100)
        self.g_freq, self.g_freq_lbl = self.add_global_slider(g_lay, "FREQ MULT", 0, 400, 100)
        self.scroll_lay.addWidget(global_group)

        for ch in ['Tx', 'Ty', 'Tz', 'Rx', 'Ry', 'Rz']:
            cw = ChannelWidget(ch, self); self.channels[ch] = cw; self.scroll_lay.addWidget(cw)

        # Actions
        action_frame = QtWidgets.QFrame(); action_frame.setStyleSheet("background-color: #0a0c0a; border-top: 1px solid #2a6b1c;")
        b_lay = QtWidgets.QVBoxLayout(action_frame)
        
        live_lay = QtWidgets.QHBoxLayout()
        self.auto_btn = QtWidgets.QPushButton("[X] AUTO-LIVE"); self.auto_btn.setCheckable(True); self.auto_btn.setChecked(True); self.auto_btn.setStyleSheet("background-color: #1a3a14; color: #5cfc3a;")
        self.auto_btn.clicked.connect(self.toggle_auto_live)
        self.apply_btn = QtWidgets.QPushButton("[ FORCE APPLY ]"); self.apply_btn.clicked.connect(self.apply_expression)
        live_lay.addWidget(self.auto_btn); live_lay.addWidget(self.apply_btn)
        
        bake_lay = QtWidgets.QHBoxLayout()
        bake_base_btn, bake_layer_btn = QtWidgets.QPushButton("[ BAKE TO BASE ]"), QtWidgets.QPushButton("[ BAKE TO LAYER ]")
        bake_base_btn.setObjectName("bakeBtn"); bake_base_btn.clicked.connect(self.bake_to_timeline)
        bake_layer_btn.setObjectName("applyBtn"); bake_layer_btn.clicked.connect(self.bake_to_anim_layer)
        bake_lay.addWidget(bake_base_btn); bake_lay.addWidget(bake_layer_btn)
        
        # New Revert Row
        revert_lay = QtWidgets.QHBoxLayout()
        self.revert_btn = QtWidgets.QPushButton("[ REVERT_TARGET_SYSTEM ]")
        self.revert_btn.setObjectName("revertBtn")
        self.revert_btn.clicked.connect(self.revert_target)
        revert_lay.addWidget(self.revert_btn)

        b_lay.addLayout(live_lay); b_lay.addLayout(bake_lay); b_lay.addLayout(revert_lay); main_layout.addWidget(action_frame)

        if self.prefs.get("last_state"): self.apply_state(self.prefs["last_state"])
        else:
            for ch in ['Tx', 'Ty', 'Tz', 'Rx', 'Ry', 'Rz']:
                self.channels[ch].add_layer()
                if ch in ['Rx', 'Ry', 'Rz']: self.channels[ch].toggle_mute()

        self.load_target(); self._block_auto = False; self.auto_apply_expression()

    # --- REVERT LOGIC ---
    def revert_target(self):
        target = self.target_line.text()
        if not target or not cmds.objExists(target):
            cmds.warning("NOISE.SYS: No valid target to revert.")
            return

        # Disable Auto-Live immediately so it doesn't try to rebuild during deletion
        if self.auto_btn.isChecked():
            self.auto_btn.setChecked(False)
            self.auto_btn.setText("[ ] AUTO-LIVE")
            self.auto_btn.setStyleSheet("")

        cmds.undoInfo(openChunk=True, chunkName="RevertNoiseSys")
        try:
            self._cleanup_live_nodes(target)
            cmds.warning(f"NOISE.SYS: System dismantled. {target} restored to initial state.")
        except Exception as e:
            cmds.warning(f"NOISE.SYS Revert Error: {str(e)}")
        finally:
            cmds.undoInfo(closeChunk=True)

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
        state = {'global_amp': self.g_amp.value(), 'global_freq': self.g_freq.value(), 'channels': {}}
        for name, cw in self.channels.items(): state['channels'][name] = {'base': cw.base_val.text(), 'muted': cw.is_muted(), 'layers': cw.get_layers()}
        return state

    def apply_state(self, state):
        if not state: return
        self._block_auto = True
        try:
            self.g_amp.setValue(state.get('global_amp', 100)); self.g_freq.setValue(state.get('global_freq', 100))
            for name, data in state.get('channels', {}).items():
                if name in self.channels:
                    cw = self.channels[name]; cw.base_val.setText(data.get('base', '0.0'))
                    if data.get('muted') != cw.is_muted(): cw.toggle_mute()
                    cw.clear_layers()
                    for lyr_data in data.get('layers', []): cw.add_layer_with_data(lyr_data)
        finally: self._block_auto = False; self.auto_apply_expression()

    def save_preset(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Save Preset", "Enter Preset Name:")
        if ok and name:
            if "presets" not in self.prefs: self.prefs["presets"] = {}
            self.prefs["presets"][name] = self.get_current_state(); save_prefs(self.prefs)
            self.preset_combo.blockSignals(True)
            if self.preset_combo.findText(name) == -1: self.preset_combo.addItem(name)
            self.preset_combo.setCurrentText(name); self.preset_combo.blockSignals(False)

    def load_preset(self, index):
        if index <= 0: return
        name = self.preset_combo.itemText(index); preset_data = self.prefs.get("presets", {}).get(name)
        if preset_data: self.apply_state(preset_data)

    def delete_preset(self):
        name = self.preset_combo.currentText()
        if name in self.prefs.get("presets", {}):
            del self.prefs["presets"][name]; save_prefs(self.prefs); self.preset_combo.removeItem(self.preset_combo.currentIndex()); self.preset_combo.setCurrentIndex(0)

    def closeEvent(self, event):
        target = self.target_line.text()
        if target and cmds.objExists(target): self._cleanup_live_nodes(target)
        self.prefs['last_state'] = self.get_current_state(); save_prefs(self.prefs); super(NoiseSysWindow, self).closeEvent(event)

    def toggle_auto_live(self):
        if self.auto_btn.isChecked(): self.auto_btn.setText("[X] AUTO-LIVE"), self.auto_btn.setStyleSheet("background-color: #1a3a14; color: #5cfc3a;"), self.apply_expression()
        else:
            self.auto_btn.setText("[ ] AUTO-LIVE"), self.auto_btn.setStyleSheet("")
            target = self.target_line.text()
            if target and cmds.objExists(target): self._cleanup_live_nodes(target)

    def auto_apply_expression(self):
        if not self._block_auto and hasattr(self, 'auto_btn') and self.auto_btn.isChecked(): self.apply_expression()

    def add_global_slider(self, parent_lay, label, vmin, vmax, vdefault):
        lay, lbl, val_lbl = QtWidgets.QHBoxLayout(), QtWidgets.QLabel(label), QtWidgets.QLabel(f"{vdefault/100.0}x")
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal); slider.setRange(vmin, vmax); slider.setValue(vdefault)
        def on_change(v): val_lbl.setText(f"{v/100.0}x"); self.auto_apply_expression()
        slider.valueChanged.connect(on_change); lay.addWidget(lbl); lay.addWidget(slider); lay.addWidget(val_lbl); parent_lay.addLayout(lay)
        return slider, val_lbl

    def get_global_amp(self): return self.g_amp.value() / 100.0
    def get_global_freq(self): return self.g_freq.value() / 100.0
    def load_target(self):
        sel = cmds.ls(selection=True)
        if sel: self.target_line.setText(sel[0]); self.auto_apply_expression()
        else: self.target_line.setText("")
    def map_maya_attr(self, ch_name):
        return {'Tx': 'translateX', 'Ty': 'translateY', 'Tz': 'translateZ', 'Rx': 'rotateX', 'Ry': 'rotateY', 'Rz': 'rotateZ'}.get(ch_name)

    def _get_pma_name(self, target, ch_name): return f"{target}_noisePMA_{ch_name}"

    def _cleanup_single_channel(self, target, ch):
        pma, full_attr = self._get_pma_name(target, ch), f"{target}.{self.map_maya_attr(ch)}"
        if cmds.objExists(pma):
            driver = cmds.listConnections(f"{pma}.input1D[0]", s=True, d=False, plugs=True)
            static_val = cmds.getAttr(f"{pma}.input1D[0]")
            pma_out = cmds.listConnections(f"{pma}.output1D", s=False, d=True, plugs=True)
            if pma_out and full_attr in pma_out: cmds.disconnectAttr(f"{pma}.output1D", full_attr)
            if driver: cmds.connectAttr(driver[0], full_attr, force=True)
            else: cmds.setAttr(full_attr, static_val)
            cmds.delete(pma)
        cust_attr = f"noise_{ch}"
        if cmds.attributeQuery(cust_attr, node=target, exists=True):
            cmds.setAttr(f"{target}.{cust_attr}", lock=False); cmds.deleteAttr(target, attribute=cust_attr)

    def _cleanup_live_nodes(self, target):
        expr_name = f"{target}_noise_sys_expr"
        if cmds.objExists(expr_name): cmds.delete(expr_name)
        for ch in ['Tx', 'Ty', 'Tz', 'Rx', 'Ry', 'Rz']: self._cleanup_single_channel(target, ch)

    def apply_expression(self):
        target = self.target_line.text()
        if not target or not cmds.objExists(target): return
        expr_name, expr_lines, g_amp, g_freq = f"{target}_noise_sys_expr", [], self.get_global_amp(), self.get_global_freq()
        active_channels, inactive_channels = [], []
        for ch_name, ch_widget in self.channels.items():
            if ch_widget.is_muted() or not ch_widget.get_layers(): inactive_channels.append(ch_name)
            else: active_channels.append(ch_name)
        if not active_channels: self._cleanup_live_nodes(target); return
        for ch_name in active_channels:
            cust_attr = f"noise_{ch_name}"
            if not cmds.attributeQuery(cust_attr, node=target, exists=True): cmds.addAttr(target, ln=cust_attr, at='double', k=True)
            cmds.setAttr(f"{target}.{cust_attr}", lock=False)
        for ch_name in active_channels:
            ch_widget, layers, base_val = self.channels[ch_name], self.channels[ch_name].get_layers(), self.channels[ch_name].get_base_value()
            math_str = str(base_val)
            for lyr in layers:
                amp, freq, offset, ntype = lyr['amp'] * g_amp, lyr['freq'] * g_freq, lyr['offset'], lyr['type']
                if ntype == 'SQUARE': lyr_str = f" ((sin(time * {freq} + {offset}) >= 0 ? 1.0 : -1.0) * {amp})"
                elif ntype == 'TRIANGLE': lyr_str = f" ((2.0 / 3.14159) * asin(sin(time * {freq} + {offset})) * {amp})"
                elif ntype == 'SAW': lyr_str = f" (2.0 * (((time * {freq} + {offset}) / (2.0 * 3.14159)) - floor(0.5 + t / (2 * 3.14159))) * {amp})" # Simplified check
                elif ntype == 'PERLIN': lyr_str = f" (noise(time * {freq} + {offset}) * {amp})"
                elif ntype == 'RANDOM': lyr_str = f" (rand(-1.0, 1.0) * {amp})"
                else: lyr_str = f" (sin(time * {freq} + {offset}) * {amp})"
                math_str += f" + {lyr_str}"
            expr_lines.append(f"{target}.noise_{ch_name} = {math_str};")
        if expr_lines:
            full_expr = "\n".join(expr_lines)
            if cmds.objExists(expr_name): cmds.expression(expr_name, e=True, s=full_expr, alwaysEvaluate=True)
            else: cmds.expression(n=expr_name, s=full_expr, alwaysEvaluate=True)
        for ch_name in active_channels:
            cust_attr, full_attr, pma = f"noise_{ch_name}", f"{target}.{self.map_maya_attr(ch_name)}", self._get_pma_name(target, ch_name)
            if not cmds.objExists(pma):
                try:
                    driver, val = cmds.listConnections(full_attr, s=True, d=False, plugs=True), cmds.getAttr(full_attr)
                    cmds.createNode('plusMinusAverage', n=pma); cmds.setAttr(f"{pma}.operation", 1)
                    if driver: cmds.disconnectAttr(driver[0], full_attr); cmds.connectAttr(driver[0], f"{pma}.input1D[0]")
                    else: cmds.setAttr(f"{pma}.input1D[0]", val)
                    cmds.connectAttr(f"{target}.{cust_attr}", f"{pma}.input1D[1]"); cmds.connectAttr(f"{pma}.output1D", full_attr, force=True)
                except Exception: pass
        for ch_name in inactive_channels: self._cleanup_single_channel(target, ch_name)

    def bake_to_timeline(self): self._bake_logic(use_layer=False)
    def bake_to_anim_layer(self): self._bake_logic(use_layer=True)

    def _bake_logic(self, use_layer):
        target = self.target_line.text()
        if not target or not cmds.objExists(target): cmds.warning("NOISE.SYS: No valid target selected."); return
        if self.auto_btn.isChecked(): self.auto_btn.setChecked(False), self.auto_btn.setText("[ ] AUTO-LIVE"), self.auto_btn.setStyleSheet("")
        self._cleanup_live_nodes(target)
        start, end, fps = int(cmds.playbackOptions(q=True, minTime=True)), int(cmds.playbackOptions(q=True, maxTime=True)), 24.0
        layer_name = f"{target}_NoiseSys_Layer"
        if use_layer and not cmds.objExists(layer_name): cmds.animLayer(layer_name, override=False)
        cmds.undoInfo(openChunk=True, chunkName="BakeNoiseSys")
        orig_time = cmds.currentTime(q=True)
        try:
            for f in range(start, end + 1):
                cmds.currentTime(f, edit=True); t_sec = f / fps
                for ch_name, ch_widget in self.channels.items():
                    if ch_widget.is_muted(): continue
                    layers, attr_name = ch_widget.get_layers(), self.map_maya_attr(ch_name)
                    full_attr = f"{target}.{attr_name}"
                    if not cmds.attributeQuery(attr_name, node=target, exists=True): continue
                    if use_layer and f == start: cmds.animLayer(layer_name, edit=True, attribute=full_attr)
                    noise_val = ch_widget.get_base_value()
                    for lyr in layers:
                        t = t_sec * (lyr['freq'] * self.get_global_freq()) + lyr['offset']
                        noise_val += get_noise_val(t, lyr['type']) * (lyr['amp'] * self.get_global_amp())
                    if use_layer: cmds.setKeyframe(target, attribute=attr_name, t=f, v=noise_val, animLayer=layer_name)
                    else:
                        base_anim_val = cmds.getAttr(full_attr); cmds.setKeyframe(target, attribute=attr_name, t=f, v=base_anim_val + noise_val)
            cmds.currentTime(orig_time, edit=True)
        except Exception as e: cmds.warning(f"NOISE.SYS Error: {str(e)}")
        finally: cmds.undoInfo(closeChunk=True)

noise_window = None
def showUI():
    global noise_window
    if noise_window: noise_window.close()
    noise_window = NoiseSysWindow(); noise_window.show()

if __name__ == "__main__": showUI()