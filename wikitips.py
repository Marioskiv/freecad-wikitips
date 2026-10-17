# SPDX-License-Identifier: LGPL-2.1-or-later
"""WikiTips: show a picture and a short explanation from the FreeCAD wiki
when the mouse rests on a toolbar button.

All content is bundled in ./data (taken from the FreeCAD-documentation
repository, CC-BY 3.0), so no internet connection is needed.
"""

import json
import os
import re

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui

try:
    from PySide import QtWidgets
except ImportError:  # very old PySide shim
    QtWidgets = QtGui

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
IMG_DIR = os.path.join(DATA_DIR, "img")
CONTENT_DIR = os.path.join(HERE, "content")   # hand-written help (Greek), not generated
CONTENT_IMG_DIR = os.path.join(CONTENT_DIR, "img")
PARAM_PATH = "User parameter:BaseApp/Preferences/Mod/WikiTips"

Qt = QtCore.Qt


def _enum(owner, name, *scopes):
    """Qt5/Qt6 compatible enum lookup (Qt.ToolTip vs Qt.WindowType.ToolTip)."""
    if hasattr(owner, name):
        return getattr(owner, name)
    for scope in scopes:
        s = getattr(owner, scope, None)
        if s is not None and hasattr(s, name):
            return getattr(s, name)
    raise AttributeError(name)


EV_TOOLTIP = _enum(QtCore.QEvent, "ToolTip", "Type")
EV_LEAVE = _enum(QtCore.QEvent, "Leave", "Type")
EV_PRESS = _enum(QtCore.QEvent, "MouseButtonPress", "Type")
EV_HIDE = _enum(QtCore.QEvent, "Hide", "Type")
EV_WHEEL = _enum(QtCore.QEvent, "Wheel", "Type")
WIN_FLAGS = (_enum(Qt, "ToolTip", "WindowType")
             | _enum(Qt, "FramelessWindowHint", "WindowType"))
WA_NOACTIVATE = _enum(Qt, "WA_ShowWithoutActivating", "WidgetAttribute")
RICH = _enum(Qt, "RichText", "TextFormat")
SMOOTH = _enum(Qt, "SmoothTransformation", "TransformationMode")
KEEP_AR = _enum(Qt, "KeepAspectRatio", "AspectRatioMode")
ALIGN_CENTER = _enum(Qt, "AlignCenter", "AlignmentFlag")

POPUP_WIDTH = 440        # the smallest popup; on bigger screens it grows with the screen width
POPUP_WIDTH_MAX = 820    # (40 % of it) up to this, so our 1248 px GIFs show their detail


def params():
    return App.ParamGet(PARAM_PATH)


def is_enabled():
    return params().GetBool("Enabled", True)


# --------------------------------------------------------------------------
# data
# --------------------------------------------------------------------------
_DATA = None


def data():
    global _DATA
    if _DATA is None:
        try:
            with open(os.path.join(DATA_DIR, "commands.json"), encoding="utf-8") as f:
                _DATA = json.load(f)
        except Exception as e:  # pragma: no cover
            App.Console.PrintError("WikiTips: cannot read data: %s\n" % e)
            _DATA = {}
    return _DATA


def lookup(name):
    """Return the wiki entry for a command name, trying old/new prefixes."""
    if not name:
        return None, None
    d = data()
    candidates = [name]
    if name.startswith("CAM_"):
        candidates.append("Path_" + name[4:])
    elif name.startswith("Path_"):
        candidates.append("CAM_" + name[5:])
    if name.startswith("Std_") and name.endswith("Std"):
        candidates.append(name[:-3])
    for c in candidates:
        if c in d:
            return c, d[c]
    # new commands without a wiki page (e.g. CAM_MillFacing in 26.3): our Greek help is enough
    el = commands_el()
    for c in candidates:
        if c in el:
            return c, {"t": el[c].get("t", c)}
    return None, None


_ITALIC = re.compile(r"<i>\s*([A-Za-z][A-Za-z0-9_]*)")
_TIP_MAP = None


def _tip_map():
    """Plain tooltip/status text -> command name, for actions without a name.

    Python dropdown groups (Part_CompOffset, CAM_DrillingTools, ...) create
    their sub-actions without objectName; only their text identifies them.
    """
    global _TIP_MAP
    if _TIP_MAP is None:
        _TIP_MAP = {}
        try:
            for n in Gui.Command.listAll():
                c = Gui.Command.get(n)
                info = c.getInfo() if c is not None else {}
                for k in ("toolTip", "statusTip"):
                    t = (info.get(k) or "").strip()
                    if t:
                        _TIP_MAP.setdefault(t, n)
        except Exception:
            pass
    return _TIP_MAP


def action_name(action):
    """Command name of one QAction, or "" if it cannot be found.

    Verified in FreeCAD 26.3: C++ commands set objectName and data(); the rich
    tooltip ends with <i>CommandName</i> (or <i>Sub (Group:0)</i> for groups);
    Python group sub-actions only carry the plain tooltip/status text.
    """
    if action is None:
        return ""
    n = action.objectName()
    if n:
        return n
    d = action.data()
    if isinstance(d, str) and d:
        return d
    m = _ITALIC.findall(action.toolTip() or "")
    if m:
        return m[-1]
    for t in (action.toolTip(), action.statusTip()):
        t = (t or "").strip()
        if t and t in _tip_map():
            return _tip_map()[t]
    return ""


_FIELDS = None
_COMMANDS_EL = None


def commands_el():
    """Greek help written by hand for toolbar commands (overrides the English wiki text)."""
    global _COMMANDS_EL
    if _COMMANDS_EL is None:
        try:
            with open(os.path.join(CONTENT_DIR, "commands_el.json"), encoding="utf-8") as f:
                _COMMANDS_EL = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
        except Exception as e:  # pragma: no cover
            App.Console.PrintError("WikiTips: cannot read Greek help: %s\n" % e)
            _COMMANDS_EL = {}
    return _COMMANDS_EL


def with_greek(key, entry):
    """Wiki entry with the Greek hand-written help on top, if we have one."""
    g = commands_el().get(key)
    if not g:
        return entry
    merged = dict(entry or {})
    merged.update(g)
    merged["_el"] = True
    return merged


def _box(rows, bar, fill):
    """A rich-text box with a coloured bar on the left (Qt rich text has no border-left)."""
    cells = "".join("<tr><td width='4' bgcolor='%s'></td><td bgcolor='%s'>%s</td></tr>" % (bar, fill, r)
                    for r in rows)
    return "<table width='100%%' cellspacing='0' cellpadding='6' style='margin-top:2px'>%s</table>" % cells


def sections_html(entry, dark=False, compact=False):
    """Short on purpose: the animation shows how. One sentence, the one trap, where it helps."""
    warn_bg, warn = ("#3B2F1A", "#FBBF24") if dark else ("#FFF7E6", "#B45309")
    use_bg, use = ("#16302A", "#34D399") if dark else ("#ECFDF5", "#047857")
    html = "<p style='font-size:10pt'>%s</p>" % entry.get("d", "")
    if entry.get("selw"):
        html += _box(["⚠ %s" % entry["selw"]], "#F59E0B", warn_bg).replace("<td bgcolor='%s'>" % warn_bg,
                                                                             "<td bgcolor='%s' style='color:%s'>" % (warn_bg, warn))
    uses = entry.get("uses") or []
    if uses and not compact:
        html += _box(["<b>Χρήσιμο:</b> " + " · ".join(uses)], "#10B981", use_bg).replace(
            "<td bgcolor='%s'>" % use_bg, "<td bgcolor='%s' style='color:%s'>" % (use_bg, use))
    return html


def fields():
    """Greek help for fields of task panels, keyed by the field's Qt objectName."""
    global _FIELDS
    if _FIELDS is None:
        try:
            with open(os.path.join(CONTENT_DIR, "fields_el.json"), encoding="utf-8") as f:
                _FIELDS = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
        except Exception as e:  # pragma: no cover
            App.Console.PrintError("WikiTips: cannot read field help: %s\n" % e)
            _FIELDS = {}
    return _FIELDS


def _field_names():
    return {k.split(":")[-1] for k in fields()}


def current_op():
    """Module name of the object being edited, e.g. 'MillFacing' for Path.Op.MillFacing."""
    for name in App.listDocuments():
        try:
            vp = Gui.getDocument(name).getInEdit()
            if vp is None:
                continue
            proxy = getattr(vp.Object, "Proxy", None)
            if proxy is not None:
                return type(proxy).__module__.rsplit(".", 1)[-1]
            return vp.Object.TypeId.split("::")[-1]
        except Exception:
            continue
    return ""


def field_entry(name):
    f = fields()
    return f.get(current_op() + ":" + name) or f.get(name)


def command_name(action, button=None):
    """Find the FreeCAD command name behind a toolbar button.

    FreeCAD names every command QAction after the command (Gui::Action sets
    objectName). For dropdown groups (e.g. the Sketcher circle/arc group) the
    button shows the group action and keeps the sub-commands in the button's
    own menu; the group copies the tooltip and icon of the sub-command shown.
    """
    if action is None:
        return None
    key, entry = lookup(action.objectName() or "")
    if entry:
        return key
    # the tooltip names the command really shown, e.g. Std_Undo or
    # "Sketcher_Projection (Sketcher_CompExternal:0)"
    for n in reversed(_ITALIC.findall(action.toolTip() or "")):
        key, entry = lookup(n)
        if entry:
            return key
    menus = []
    if button is not None and button.menu() is not None:
        menus.append(button.menu())
    if action.menu() is not None:
        menus.append(action.menu())
    tip = action.toolTip()
    icon_key = action.icon().cacheKey()
    for menu in menus:
        subs = [(a, action_name(a)) for a in menu.actions() if not a.isSeparator()]
        subs = [(a, n) for a, n in subs if n]
        # 1) same tooltip as the button (= the one shown)  2) the checked one
        # 3) the same icon  4) the first one (FreeCAD's default)
        for test in (lambda a: a.toolTip() == tip,
                     lambda a: a.isCheckable() and a.isChecked(),
                     lambda a: a.icon().cacheKey() == icon_key,
                     lambda a: True):
            for sub, n in subs:
                if test(sub):
                    key, entry = lookup(n)
                    if entry:
                        return key
    return None


MAX_PARAGRAPHS = 2
MAX_TEXT = 420  # characters of visible text; longer wiki intros are cut
MAX_STEPS = 4
_PARA = re.compile(r"<p>.*?</p>", re.S)
_TAGS = re.compile(r"<[^>]+>")


def short_html(html):
    """Keep the first paragraphs of a wiki description so the popup fits a laptop screen."""
    paras = _PARA.findall(html) or ([html] if html else [])
    out, size = [], 0
    for p in paras[:MAX_PARAGRAPHS]:
        n = len(_TAGS.sub("", p))
        if out and size + n > MAX_TEXT:
            break
        out.append(p)
        size += n
    if len(out) < len(paras):
        out.append("<p style='color:gray'>…</p>")
    return "".join(out)


def clean_label(text):
    return text.replace("&&", "\0").replace("&", "").replace("\0", "&").replace("...", "").strip()


# --------------------------------------------------------------------------
# popup
# --------------------------------------------------------------------------
class TipPopup(QtWidgets.QFrame):
    def __init__(self):
        super().__init__(None, WIN_FLAGS)
        self.setAttribute(WA_NOACTIVATE, True)
        self.setObjectName("WikiTipsPopup")
        self._pw = POPUP_WIDTH
        self.setFixedWidth(self._pw)
        self._owner = None
        self._rect = None
        self._movie = None
        self._hidpi = False
        self._max_image_h = 250

        pal = QtWidgets.QApplication.palette()
        bg = pal.color(_enum(QtGui.QPalette, "Base", "ColorRole")).name()
        fg = pal.color(_enum(QtGui.QPalette, "Text", "ColorRole")).name()
        hl = pal.color(_enum(QtGui.QPalette, "Highlight", "ColorRole")).name()
        self.setStyleSheet(
            "#WikiTipsPopup { background:%s; color:%s; border:2px solid %s; border-radius:6px; }"
            "#WikiTipsPopup QLabel { background:transparent; color:%s; }"
            "#wtTitle { font-size:12pt; font-weight:bold; }"
            "#wtSmall { color:gray; font-size:8pt; }"
            "#wtImage { background:white; border:1px solid #bbb; }"
            "#wtKey { background:%s; color:%s; border:1px solid #94A3B8; border-radius:4px; padding:2px 7px; font-weight:bold; font-size:9pt; }"
            % (bg, fg, hl, fg, "#334155" if self._dark(bg) else "#E2E8F0", fg))

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(6)

        head = QtWidgets.QHBoxLayout()
        self.icon = QtWidgets.QLabel()
        self.icon.setFixedSize(32, 32)
        self.title = QtWidgets.QLabel()
        self.title.setObjectName("wtTitle")
        self.title.setWordWrap(True)
        self.key = QtWidgets.QLabel()
        self.key.setObjectName("wtKey")
        head.addWidget(self.icon)
        head.addWidget(self.title, 1)
        head.addWidget(self.key, 0, _enum(Qt, "AlignTop", "AlignmentFlag"))
        lay.addLayout(head)

        self.meta = QtWidgets.QLabel()
        self.meta.setObjectName("wtSmall")
        self.meta.setWordWrap(True)
        self.meta.setTextFormat(RICH)
        lay.addWidget(self.meta)

        self.image = QtWidgets.QLabel()
        self.image.setObjectName("wtImage")
        self.image.setAlignment(ALIGN_CENTER)
        lay.addWidget(self.image)

        self.text = QtWidgets.QLabel()
        self.text.setWordWrap(True)
        self.text.setTextFormat(RICH)
        lay.addWidget(self.text)

        self.footer = QtWidgets.QLabel()
        self.footer.setObjectName("wtSmall")
        self.footer.setWordWrap(True)
        self.footer.setText("Ολόκληρη η σελίδα: Shift+F1 και κλικ στο κουμπί · "
                            "Πηγή: FreeCAD wiki (CC-BY 3.0)")
        lay.addWidget(self.footer)

        self._watch = QtCore.QTimer(self)
        self._watch.setInterval(250)
        self._watch.timeout.connect(self._check_cursor)

    @staticmethod
    def _dark(color_name):
        return QtGui.QColor(color_name).lightness() < 128

    # -- content -----------------------------------------------------------
    def fill(self, key, entry, action, compact=False):
        self._stop_movie()
        field = action is None   # help for a field of a dialog, from content/
        el = bool(entry.get("_el"))   # hand-written Greek help for a command
        label = clean_label(action.text()) if action is not None else ""
        self.title.setText(entry["t"] if el else (label or entry.get("t", key)))
        if action is not None and not action.icon().isNull():
            self.icon.setPixmap(action.icon().pixmap(32, 32))
            self.icon.show()
        else:
            self.icon.hide()

        meta = [] if field else ["<i>%s</i>" % (label if el and label else key)]
        if field and entry.get("f"):
            meta.append("Στο Fusion 360: <b>%s</b>" % entry["f"])
        if entry.get("m"):
            meta.append("Μενού: " + entry["m"])
        self.meta.setText(" · ".join(meta))
        sc = action.shortcut().toString() if action is not None else ""
        sc = sc or entry.get("k", "")
        self.key.setText(sc.replace(", ", " ").replace(",", " "))
        self.key.setVisible(bool(sc))

        img = entry.get("i")
        path = os.path.join(CONTENT_IMG_DIR if (field or el) else IMG_DIR, img) if img else ""
        if el and img and not os.path.isfile(path):
            # Greek text without our own animation: keep the wiki picture
            path = os.path.join(IMG_DIR, img)
        self._hidpi = path.startswith(CONTENT_IMG_DIR)
        if img and os.path.exists(path):
            if img.lower().endswith(".gif"):
                # our GIFs are stored at 2x: each frame is scaled smoothly to the screen's real
                # pixels (Windows 125 %/150 % scaling included), never stretched up (blurry)
                self._movie = QtGui.QMovie(path)
                self._movie.setCacheMode(_enum(QtGui.QMovie, "CacheAll", "CacheMode"))
                self._movie.frameChanged.connect(self._show_frame)
                self._movie.jumpToFrame(0)
                self._show_frame()
                self._movie.start()
            else:
                self.image.setPixmap(self._sharp(QtGui.QPixmap(path)))
            self.image.show()
        else:
            self.image.clear()
            self.image.hide()

        if el:
            html = sections_html(entry, self._dark(QtWidgets.QApplication.palette().color(
                _enum(QtGui.QPalette, "Base", "ColorRole")).name()), compact)
        else:
            html = entry.get("d", "") if field else short_html(entry.get("d", ""))
        if entry.get("w"):
            html += "<p style='color:#c0392b'><b>⚠ </b>%s</p>" % entry["w"]
        wiki_pic = el and path.startswith(IMG_DIR)
        self.footer.setText("WikiTips · δικά μας σχέδια και κείμενα" if field else
                            "WikiTips · εικόνα: FreeCAD wiki (CC-BY 3.0) · Shift+F1 και κλικ: ολόκληρη η σελίδα"
                            if wiki_pic else
                            "WikiTips · ελέγχθηκε με το FreeCAD wiki · Shift+F1 και κλικ: ολόκληρη η σελίδα"
                            if el else
                            "Ολόκληρη η σελίδα: Shift+F1 και κλικ στο κουμπί · "
                            "Πηγή: FreeCAD wiki (CC-BY 3.0)")
        steps = [] if el else (entry.get("u") or [])[:MAX_STEPS]
        if steps:
            html += "<p><b>Πώς χρησιμοποιείται:</b></p><ol style='margin-left:-20px'>%s</ol>" % "".join(
                "<li>%s</li>" % s for s in steps)
        self.text.setText(html)
        inner = self._pw - 24
        self.ensurePolished()   # style sheet fonts (bigger title) must apply before measuring
        for lbl in (self.title, self.meta, self.text, self.footer):
            lbl.ensurePolished()
        for lbl in (self.meta, self.text, self.footer):
            lbl.setFixedWidth(inner)
            h = lbl.heightForWidth(inner) if lbl.text() else 0
            lbl.setFixedHeight(max(0, h))
            lbl.setVisible(h > 0)
        tw = inner - (40 if not self.icon.isHidden() else 0) - (
            self.key.sizeHint().width() + 6 if not self.key.isHidden() else 0)
        self.title.setFixedWidth(tw)
        self.title.setFixedHeight(max(self.title.heightForWidth(tw), self.title.sizeHint().height()))
        self.layout().activate()
        self.setFixedHeight(self.layout().sizeHint().height())

    def _stop_movie(self):
        if self._movie is not None:
            self._movie.stop()
            try:
                self._movie.frameChanged.disconnect(self._show_frame)
            except Exception:
                pass
            self._movie = None

    def _sharp(self, pm):
        """The picture at most popup width - 24 x _max_image_h on screen, drawn with the screen's
        real pixels: our 3x pictures stay sharp on 100-300 % displays."""
        if pm.isNull():
            return pm
        dpr = max(1.0, self.devicePixelRatioF() if hasattr(self, "devicePixelRatioF") else 1.0)
        w, h = pm.width(), pm.height()
        big = 1.0
        if self._hidpi and w > 416:               # ours: 2x or 3x of 416 x 250, may be shown bigger
            h, w = h * 416.0 / w, 416.0
            big = (POPUP_WIDTH_MAX - 24) / 416.0  # shown up to 796 px wide: still sharp from 1248 px
        k = min(big, (self._pw - 24) / w, self._max_image_h / h)
        size = QtCore.QSize(int(round(w * k * dpr)), int(round(h * k * dpr)))
        if size != pm.size():
            pm = pm.scaled(size, KEEP_AR, SMOOTH)
        pm.setDevicePixelRatio(dpr)
        return pm

    def _show_frame(self, *args):
        try:
            if self._movie is not None:
                self.image.setPixmap(self._sharp(self._movie.currentPixmap()))
        except Exception:
            pass

    # -- show / hide -------------------------------------------------------
    def show_for(self, owner, key, entry, action, gpos, rect=None):
        self._owner = owner
        self._rect = rect      # fields: only a screen rectangle, never the widget
        screen = None
        if hasattr(QtGui.QGuiApplication, "screenAt"):
            screen = QtGui.QGuiApplication.screenAt(gpos)
        if screen is None:
            screen = QtGui.QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()
        # the popup and its picture grow with the screen (a 536 px picture hides the detail of our
        # GIFs on a 100 % 1920 px screen); if it does not fit, first drop the examples and the tip,
        # then make the picture lower until it fits
        self._pw = max(POPUP_WIDTH, min(POPUP_WIDTH_MAX, int(geo.width() * 0.4)))
        self.setFixedWidth(self._pw)
        self._max_image_h = int((self._pw - 24) * 0.6)
        self.fill(key, entry, action)
        if self.height() > geo.height() - 30 and entry.get("_el"):
            self.fill(key, entry, action, compact=True)
        if self.height() > geo.height() - 30:
            self._max_image_h = max(170, self._max_image_h - (self.height() - geo.height() + 30))
            self.fill(key, entry, action, compact=bool(entry.get("_el")))
        x, y = gpos.x() + 16, gpos.y() + 22
        w, h = self.width(), self.height()
        if x + w > geo.right():
            x = max(geo.left(), gpos.x() - w - 8)
        if y + h > geo.bottom():
            y = max(geo.top(), gpos.y() - h - 8)
        self.move(x, y)
        self.show()
        self.raise_()
        self._watch.start()

    def dismiss(self):
        self._watch.stop()
        self._stop_movie()
        self._owner = None
        self.hide()

    def _check_cursor(self):
        if self._rect is not None:
            if not self._rect.contains(QtGui.QCursor.pos()):
                self.dismiss()
            return
        o = self._owner
        try:
            if o is None or not o.isVisible():
                self.dismiss()
                return
            local = o.mapFromGlobal(QtGui.QCursor.pos())
            if not o.rect().contains(local):
                self.dismiss()
        except RuntimeError:  # widget deleted
            self.dismiss()


# --------------------------------------------------------------------------
# event filter on tool buttons
# --------------------------------------------------------------------------
class ButtonFilter(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self.popup = TipPopup()

    def eventFilter(self, obj, ev):
        # never let an error here disturb FreeCAD's own event handling
        try:
            return self._filter(obj, ev)
        except Exception:
            return False

    def _filter(self, obj, ev):
        t = ev.type()
        if t == EV_TOOLTIP:
            if not is_enabled():
                return False
            if self.popup.isVisible() and self.popup._owner is obj:
                return True   # already showing for this button: moving the mouse must not restart it
            try:
                action = obj.defaultAction()
            except AttributeError:
                return False
            key = command_name(action, obj)
            if not key:
                return False
            _, entry = lookup(key)
            entry = with_greek(key, entry)
            gpos = ev.globalPos() if hasattr(ev, "globalPos") else QtGui.QCursor.pos()
            # a fresh popup every time keeps the size right for each entry
            self.popup.dismiss()
            self.popup.deleteLater()
            self.popup = TipPopup()
            self.popup.show_for(obj, key, entry, action, gpos)
            return True  # replace the normal tooltip
        if t in (EV_LEAVE, EV_PRESS, EV_HIDE, EV_WHEEL):
            if self.popup.isVisible() and self.popup._owner is obj:
                self.popup.dismiss()
        return False


_FILTER = None
_SCAN_TIMER = None


def _scan():
    """Attach the filter to the buttons of the main window's toolbars.

    Only toolbar buttons: they live as long as FreeCAD. Wrapping short-lived
    widgets (e.g. of task dialogs) in Python leaves stale PySide wrappers that
    crashed FreeCAD 26.3 when a CAM dialog was closed (found 2026-10-16).
    """
    mw = Gui.getMainWindow()
    if mw is None or _FILTER is None:
        return
    for tb in mw.findChildren(QtWidgets.QToolBar):
        for btn in tb.findChildren(QtWidgets.QToolButton):
            if not btn.property("wikitips"):
                btn.installEventFilter(_FILTER)
                btn.setProperty("wikitips", True)


# --------------------------------------------------------------------------
# help for fields of task dialogs (CAM operations ...)
# --------------------------------------------------------------------------
LABEL_ROLE = _enum(QtWidgets.QFormLayout, "LabelRole", "ItemRole")
FIELD_ROLE = _enum(QtWidgets.QFormLayout, "FieldRole", "ItemRole")
REST_MS = 450   # mouse must rest this long on a field (FreeCAD's own tooltip comes at ~700 ms)


def _label_field(label):
    """The field next to a label in a form/grid layout, or None."""
    parent = label.parentWidget()
    lay = parent.layout() if parent is not None else None
    if isinstance(lay, QtWidgets.QFormLayout):
        row, role = lay.getWidgetPosition(label)
        if row >= 0 and role == LABEL_ROLE:
            item = lay.itemAt(row, FIELD_ROLE)
            return item.widget() if item is not None else None
    elif isinstance(lay, QtWidgets.QGridLayout):
        i = lay.indexOf(label)
        if i >= 0:
            row, col, _, _ = lay.getItemPosition(i)
            for c in range(col + 1, lay.columnCount()):
                item = lay.itemAtPosition(row, c)
                if item is not None and item.widget() is not None:
                    return item.widget()
    return None


def field_under_cursor():
    """(field name, field widget) under the mouse, if we have help for it.

    Spin boxes: the cursor is over their inner line edit, so look at parents too.
    Labels: use the field in the same row. Nothing is kept: the widgets are only
    used inside this call.
    """
    names = _field_names()
    w = QtWidgets.QApplication.widgetAt(QtGui.QCursor.pos())
    if w is None:
        return None, None
    cand = w
    for _ in range(3):
        if cand is None:
            break
        n = cand.objectName()
        if n in names:
            return n, cand
        if n.endswith("Label") and n[:-5] in names:   # e.g. startDepthLabel
            return n[:-5], cand
        if isinstance(cand, QtWidgets.QLabel) and not n:
            f = _label_field(cand)
            if f is not None and f.objectName() in names:
                return f.objectName(), cand
        cand = cand.parentWidget()
    return None, None


class FieldWatcher(QtCore.QObject):
    """Shows help when the mouse rests on a field of an open task dialog.

    Polls the widget under the cursor instead of installing event filters on
    dialog widgets: dialogs are destroyed when closed, and Python filters or
    wrappers on them are a crash risk. The popup remembers only a screen
    rectangle, never the widget.
    """

    def __init__(self, popup_owner):
        super().__init__()
        self.owner = popup_owner          # ButtonFilter: shares its popup
        self.name = None
        self.since = QtCore.QElapsedTimer()
        self.since.start()
        self.shown = False
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(150)
        self.timer.timeout.connect(self.tick)

    def tick(self):
        try:
            self._tick()
        except Exception:
            pass

    def _tick(self):
        if not is_enabled() or not Gui.Control.activeDialog():
            self._hide()
            self.name = None
            return
        if QtWidgets.QApplication.mouseButtons() != _enum(Qt, "NoButton", "MouseButton"):
            self._hide()
            return
        name, w = field_under_cursor()
        if name != self.name:
            self._hide()
            self.name = name
            self.since.restart()
            return
        if not name or self.shown or self.since.elapsed() < REST_MS:
            return
        entry = field_entry(name)
        if not entry:
            return
        tip = (w.toolTip() or "").strip()
        if tip:
            w.setToolTip("")   # our popup replaces FreeCAD's tooltip; its text goes into the popup
            entry = dict(entry, en=tip)
        rect = QtCore.QRect(w.mapToGlobal(QtCore.QPoint(0, 0)), w.size())
        f = self.owner
        f.popup.dismiss()
        f.popup.deleteLater()
        f.popup = TipPopup()
        f.popup.show_for(None, name, entry, None, QtGui.QCursor.pos(), rect=rect)
        self.shown = True

    def _hide(self):
        if self.shown:
            self.owner.popup.dismiss()
        self.shown = False


def _ensure_toolbar():
    """Add a small global toolbar with the on/off button (only the first time)."""
    p = params()
    if p.GetBool("ToolbarCreated", False):
        return
    grp = App.ParamGet("User parameter:BaseApp/Workbench/Global/Toolbar/WikiTips")
    grp.SetString("Name", "WikiTips")
    grp.SetBool("Active", True)
    grp.SetString("WikiTips_Toggle", "wikitips")
    p.SetBool("ToolbarCreated", True)


def _ensure_tool_buttons():
    """WikiTips tools (Knurl ...) on the WikiTips toolbar, also for users who already have it."""
    grp = App.ParamGet("User parameter:BaseApp/Workbench/Global/Toolbar/WikiTips")
    for cmd in ("WikiTips_Knurl", "WikiTips_Wrap"):
        if not grp.GetString(cmd, ""):
            grp.SetString(cmd, "wikitips")


class ToggleCommand:
    def GetResources(self):
        return {
            "Pixmap": os.path.join(HERE, "Resources", "WikiTips.svg"),
            "MenuText": "WikiTips on/off",
            "ToolTip": "Ενεργοποίηση/απενεργοποίηση των εικόνων-βοήθειας από το wiki "
                       "όταν κρατάς το ποντίκι πάνω σε ένα κουμπί.",
        }

    def Activated(self):
        new = not is_enabled()
        params().SetBool("Enabled", new)
        msg = "WikiTips: ενεργό" if new else "WikiTips: ανενεργό"
        App.Console.PrintMessage(msg + "\n")
        mw = Gui.getMainWindow()
        if mw is not None:
            mw.statusBar().showMessage(msg, 3000)

    def IsActive(self):
        return True


def install():
    global _FILTER, _SCAN_TIMER
    if _FILTER is not None:
        return
    Gui.addCommand("WikiTips_Toggle", ToggleCommand())
    _ensure_toolbar()
    _FILTER = ButtonFilter()
    _FILTER.watcher = FieldWatcher(_FILTER)
    _FILTER.watcher.timer.start()
    _SCAN_TIMER = QtCore.QTimer()
    _SCAN_TIMER.setInterval(2000)  # new toolbars appear when switching workbench
    _SCAN_TIMER.timeout.connect(_scan)
    _SCAN_TIMER.start()
    QtCore.QTimer.singleShot(500, _scan)
    try:
        import wikitips_knurl    # tools: knurling on a cylinder, drawing on a cylinder
        import wikitips_wrap
        wikitips_knurl.install()
        wikitips_wrap.install()
        _ensure_tool_buttons()
    except Exception as e:
        App.Console.PrintWarning("WikiTips: tools off: %s\n" % e)
    try:
        import wikitips_errors   # Greek explanation of red features, "show me where"
        wikitips_errors.install()
    except Exception as e:
        App.Console.PrintWarning("WikiTips: error explainer off: %s\n" % e)
    App.Console.PrintLog("WikiTips: %d commands loaded\n" % len(data()))
