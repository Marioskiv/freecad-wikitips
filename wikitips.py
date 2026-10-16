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

POPUP_WIDTH = 440


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
        self.setFixedWidth(POPUP_WIDTH)
        self._owner = None
        self._movie = None
        self._max_image_h = 260

        pal = QtWidgets.QApplication.palette()
        bg = pal.color(_enum(QtGui.QPalette, "Base", "ColorRole")).name()
        fg = pal.color(_enum(QtGui.QPalette, "Text", "ColorRole")).name()
        hl = pal.color(_enum(QtGui.QPalette, "Highlight", "ColorRole")).name()
        self.setStyleSheet(
            "#WikiTipsPopup { background:%s; color:%s; border:2px solid %s; border-radius:6px; }"
            "#WikiTipsPopup QLabel { background:transparent; color:%s; }"
            "#wtTitle { font-size:12pt; font-weight:bold; }"
            "#wtSmall { color:gray; font-size:8pt; }"
            "#wtImage { background:white; border:1px solid #bbb; }" % (bg, fg, hl, fg))

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(6)

        head = QtWidgets.QHBoxLayout()
        self.icon = QtWidgets.QLabel()
        self.icon.setFixedSize(32, 32)
        self.title = QtWidgets.QLabel()
        self.title.setObjectName("wtTitle")
        self.title.setWordWrap(True)
        head.addWidget(self.icon)
        head.addWidget(self.title, 1)
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

    # -- content -----------------------------------------------------------
    def fill(self, key, entry, action):
        self._stop_movie()
        label = clean_label(action.text()) if action is not None else ""
        self.title.setText(label or entry.get("t", key))
        if action is not None and not action.icon().isNull():
            self.icon.setPixmap(action.icon().pixmap(32, 32))
            self.icon.show()
        else:
            self.icon.hide()

        meta = ["<i>%s</i>" % key]
        if entry.get("m"):
            meta.append("Μενού: " + entry["m"])
        sc = action.shortcut().toString() if action is not None else ""
        if sc:
            meta.append("Συντόμευση: <b>%s</b>" % sc)
        elif entry.get("k"):
            meta.append("Συντόμευση: " + entry["k"])
        self.meta.setText(" · ".join(meta))
        self.meta.setVisible(bool(meta))

        img = entry.get("i")
        path = os.path.join(IMG_DIR, img) if img else ""
        if img and os.path.exists(path):
            if img.lower().endswith(".gif"):
                self._movie = QtGui.QMovie(path)
                self._movie.jumpToFrame(0)
                sz = self._movie.currentImage().size()
                maxw, maxh = POPUP_WIDTH - 24, self._max_image_h
                if sz.width() > 0 and (sz.width() > maxw or sz.height() > maxh):
                    sz.scale(maxw, maxh, KEEP_AR)
                    self._movie.setScaledSize(sz)
                self.image.setMovie(self._movie)
                self._movie.start()
            else:
                pm = QtGui.QPixmap(path)
                maxw, maxh = POPUP_WIDTH - 24, self._max_image_h
                if pm.width() > maxw or pm.height() > maxh:
                    pm = pm.scaled(maxw, maxh, KEEP_AR, SMOOTH)
                self.image.setPixmap(pm)
            self.image.show()
        else:
            self.image.clear()
            self.image.hide()

        html = short_html(entry.get("d", ""))
        steps = (entry.get("u") or [])[:MAX_STEPS]
        if steps:
            html += "<p><b>Πώς χρησιμοποιείται:</b></p><ol style='margin-left:-20px'>%s</ol>" % "".join(
                "<li>%s</li>" % s for s in steps)
        self.text.setText(html)
        inner = POPUP_WIDTH - 24
        for lbl in (self.meta, self.text, self.footer):
            lbl.setFixedWidth(inner)
            lbl.setFixedHeight(lbl.heightForWidth(inner))
        self.title.setFixedHeight(self.title.heightForWidth(inner - 40))
        self.layout().activate()
        self.setFixedHeight(self.layout().sizeHint().height())

    def _stop_movie(self):
        if self._movie is not None:
            self._movie.stop()
            self.image.setMovie(None)
            self._movie = None

    # -- show / hide -------------------------------------------------------
    def show_for(self, owner, key, entry, action, gpos):
        self._owner = owner
        screen = None
        if hasattr(QtGui.QGuiApplication, "screenAt"):
            screen = QtGui.QGuiApplication.screenAt(gpos)
        if screen is None:
            screen = QtGui.QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()
        # small screens (laptops): smaller picture so the popup always fits
        self._max_image_h = 260 if geo.height() >= 900 else 170
        self.fill(key, entry, action)
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
            try:
                action = obj.defaultAction()
            except AttributeError:
                return False
            key = command_name(action, obj)
            if not key:
                return False
            _, entry = lookup(key)
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
    """Attach the filter to every toolbar button of the main window."""
    mw = Gui.getMainWindow()
    if mw is None or _FILTER is None:
        return
    for btn in mw.findChildren(QtWidgets.QToolButton):
        if not btn.property("wikitips"):
            btn.installEventFilter(_FILTER)
            btn.setProperty("wikitips", True)


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
    _SCAN_TIMER = QtCore.QTimer()
    _SCAN_TIMER.setInterval(2000)  # new toolbars appear when switching workbench
    _SCAN_TIMER.timeout.connect(_scan)
    _SCAN_TIMER.start()
    QtCore.QTimer.singleShot(500, _scan)
    App.Console.PrintLog("WikiTips: %d commands loaded\n" % len(data()))
