# SPDX-License-Identifier: LGPL-2.1-or-later
"""WikiTips error explainer and "show me where".

When a feature turns red after a recompute (or CAM writes an error in the
Report view), a small Greek card says what went wrong and what to do.
Command names in the steps are links: a click outlines the real toolbar
button for a few seconds. Also catches two silent mistakes FreeCAD does not
report: a Part Design feature that changed nothing, and a Body that split in
two solids.

Everything here runs from a timer or a document observer; every entry point
is wrapped in try/except so that WikiTips can never break FreeCAD.
"""

import json
import os
import re

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui

import wikitips as wt

QtWidgets = wt.QtWidgets
Qt = wt.Qt

ERRORS_FILE = os.path.join(wt.CONTENT_DIR, "errors_el.json")
CARD_WIDTH = 400
TICK_MS = 700
_CMD = re.compile(r"\{([A-Za-z]+_[A-Za-z0-9_]+)\}")
_STAMP = re.compile(r"^\d\d:\d\d:\d\d\s+")

WA_MOUSE_THROUGH = wt._enum(Qt, "WA_TransparentForMouseEvents", "WidgetAttribute")
ANTIALIAS = wt._enum(QtGui.QPainter, "Antialiasing", "RenderHint")
END = wt._enum(QtGui.QTextCursor, "End", "MoveOperation")
KEEP_ANCHOR = wt._enum(QtGui.QTextCursor, "KeepAnchor", "MoveMode")

# Part Design features that must change the solid of the Body (silent "nothing happened" check)
SILENT_TYPES = re.compile(r"^PartDesign::(Pad|Pocket|Revolution|Groove|Hole|Additive|Subtractive|"
                          r"LinearPattern|PolarPattern|Mirrored|MultiTransform|Thickness|Fillet|Chamfer|Draft)")
NOT_ROOT = re.compile(r"^(PartDesign::Body|App::Part|App::Origin|App::Line|App::Plane|App::Point)$")
WORKBENCH_HINT = {
    "Sketcher_": "Το κουμπί φαίνεται μόνο μέσα σε σκαρίφημα: άνοιξέ το με διπλό κλικ.",
    "PartDesign_": "Το κουμπί είναι στον πάγκο Part Design: διάλεξέ τον από τη λίστα πάγκων.",
    "Part_": "Το κουμπί είναι στον πάγκο Part: διάλεξέ τον από τη λίστα πάγκων.",
    "CAM_": "Το κουμπί είναι στον πάγκο CAM: διάλεξέ τον από τη λίστα πάγκων.",
}


def enabled():
    return wt.is_enabled() and wt.params().GetBool("ExplainErrors", True)


# --------------------------------------------------------------------------
# rules
# --------------------------------------------------------------------------
_RULES = None


def rules():
    global _RULES
    if _RULES is None:
        try:
            with open(ERRORS_FILE, encoding="utf-8") as f:
                _RULES = json.load(f)["rules"]
            for r in _RULES:
                if r.get("re"):
                    r["_re"] = re.compile(r["re"], re.I)
        except Exception as e:  # pragma: no cover
            App.Console.PrintError("WikiTips: cannot read error help: %s\n" % e)
            _RULES = []
    return _RULES


def special(rule_id):
    for r in rules():
        if r["id"] == rule_id:
            return r
    return {"id": rule_id, "t": "", "d": "", "fix": []}


def explain(message, type_id="", src="doc"):
    """The Greek rule for one English error message (first match wins).

    Report view lines ("log") match only rules marked "src": "log", so that
    ordinary messages there never raise a card; red objects get the generic
    rule when nothing matches.
    """
    for r in rules():
        if "_re" not in r:
            continue
        if src == "log" and r.get("src") != "log":
            continue
        if r.get("type") and not re.search(r["type"], type_id):
            continue
        if r["_re"].search(message):
            return r
    return None if src == "log" else special("_generic")


def constraint_numbers(message):
    """Constraint numbers in a Sketcher solver message, e.g. '...constraints:1\n, 2\n' -> ['1', '2']."""
    if ":" not in message:
        return []
    return re.findall(r"\d+", message.split(":", 1)[1])


# --------------------------------------------------------------------------
# "show me where": outline the real toolbar button
# --------------------------------------------------------------------------
def find_button(cmd):
    """(tool button, in_dropdown) showing the command in a visible toolbar, or (None, False)."""
    mw = Gui.getMainWindow()
    for tb in mw.findChildren(QtWidgets.QToolBar):
        if not tb.isVisible():
            continue
        for btn in tb.findChildren(QtWidgets.QToolButton):
            if not btn.isVisible():
                continue
            a = btn.defaultAction()
            if a is None:
                continue
            if wt.action_name(a) == cmd or wt.command_name(a, btn) == cmd:
                return btn, False
            for menu in (btn.menu(), a.menu()):
                if menu is None:
                    continue
                for sub in menu.actions():
                    if wt.action_name(sub) == cmd:
                        return btn, True
    return None, False


class Outline(QtWidgets.QWidget):
    """A pulsing amber frame around a button; the mouse goes through it."""

    TICKS = 24   # x 120 ms

    def __init__(self, mw, rect):
        super().__init__(mw)
        self.setAttribute(WA_MOUSE_THROUGH, True)
        self.setGeometry(rect.adjusted(-6, -6, 6, 6))
        self._n = 0
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(120)
        self._timer.timeout.connect(self._tick)
        self._timer.start()
        self.show()
        self.raise_()

    def _tick(self):
        self._n += 1
        if self._n >= self.TICKS:
            self._timer.stop()
            self.hide()
            self.deleteLater()
        else:
            self.update()

    def paintEvent(self, ev):
        try:
            p = QtGui.QPainter(self)
            p.setRenderHint(ANTIALIAS, True)
            alpha = 255 if (self._n // 3) % 2 == 0 else 110
            p.setPen(QtGui.QPen(QtGui.QColor(245, 158, 11, alpha), 4))
            p.drawRoundedRect(self.rect().adjusted(3, 3, -3, -3), 7, 7)
            p.end()
        except Exception:
            pass


def show_me(cmd):
    """Outline the toolbar button of a command. Returns a Greek note for the user ('' if shown)."""
    mw = Gui.getMainWindow()
    title = (wt.commands_el().get(cmd) or {}).get("t", cmd)
    btn, in_menu = find_button(cmd)
    if btn is None:
        note = next((v for k, v in WORKBENCH_HINT.items() if cmd.startswith(k)),
                    "Το κουμπί δεν φαίνεται τώρα σε καμία γραμμή εργαλείων.")
        mw.statusBar().showMessage("WikiTips: %s · %s" % (title, note), 8000)
        return note
    if mw.isAncestorOf(btn):
        top_left = btn.mapTo(mw, QtCore.QPoint(0, 0))
    else:   # floating toolbar (own window)
        top_left = mw.mapFromGlobal(btn.mapToGlobal(QtCore.QPoint(0, 0)))
    Outline(mw, QtCore.QRect(top_left, btn.size()))
    msg = "Εδώ είναι: %s" % title + (" (στο βελάκι δίπλα στο κουμπί)" if in_menu else "")
    mw.statusBar().showMessage("WikiTips: " + msg, 6000)
    return msg if in_menu else ""


# --------------------------------------------------------------------------
# the card
# --------------------------------------------------------------------------
def steps_html(steps):
    def link(m):
        cmd = m.group(1)
        title = (wt.commands_el().get(cmd) or {}).get("t", cmd)
        return "<a href='cmd:%s' style='color:#2563EB'><b>%s</b></a>" % (cmd, title)
    return "<ol style='margin-left:-22px'>%s</ol>" % "".join("<li>%s</li>" % _CMD.sub(link, s) for s in steps)


class ErrorCard(QtWidgets.QFrame):
    """Child of the main window, bottom right over the 3D view: no window manager involved."""

    def __init__(self, mw):
        super().__init__(mw)
        self.setObjectName("WikiTipsError")
        self.setFixedWidth(CARD_WIDTH)
        self.key = None
        self.doc = None
        self._movie = None
        pal = QtWidgets.QApplication.palette()
        bg = pal.color(wt._enum(QtGui.QPalette, "Base", "ColorRole")).name()
        fg = pal.color(wt._enum(QtGui.QPalette, "Text", "ColorRole")).name()
        self.dark = QtGui.QColor(bg).lightness() < 128
        self.setStyleSheet(
            "#WikiTipsError { background:%s; color:%s; border:1px solid #F43F5E; border-left:5px solid #F43F5E;"
            " border-radius:8px; }"
            "#WikiTipsError QLabel { background:transparent; color:%s; border:none; }"
            "#wteTitle { font-size:11pt; font-weight:bold; }"
            "#wteSmall { color:gray; font-size:8pt; }"
            "#wteNote { color:#B45309; font-size:9pt; }"
            "#wteClose { border:none; background:transparent; color:gray; font-size:11pt; }"
            "#wteImage { background:white; border:1px solid #CBD5E1; }"
            % (bg, fg, fg))

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 8, 10)
        lay.setSpacing(5)
        head = QtWidgets.QHBoxLayout()
        self.title = QtWidgets.QLabel()
        self.title.setObjectName("wteTitle")
        self.title.setWordWrap(True)
        self.close_btn = QtWidgets.QToolButton()
        self.close_btn.setObjectName("wteClose")
        self.close_btn.setText("✕")
        self.close_btn.setToolTip("Κλείσιμο (δεν ξαναβγαίνει για το ίδιο λάθος)")
        self.close_btn.clicked.connect(self._closed)
        head.addWidget(self.title, 1)
        head.addWidget(self.close_btn, 0, wt._enum(Qt, "AlignTop", "AlignmentFlag"))
        lay.addLayout(head)
        self.where = self._label("wteSmall")
        self.image = QtWidgets.QLabel()
        self.image.setObjectName("wteImage")
        self.image.setAlignment(wt.ALIGN_CENTER)
        lay.addWidget(self.where)
        lay.addWidget(self.image)
        self.text = self._label(None)
        self.text.setOpenExternalLinks(False)
        self.text.linkActivated.connect(self._link)
        self.note = self._label("wteNote")
        self.orig = self._label("wteSmall")
        self.footer = self._label("wteSmall")
        for w in (self.text, self.note, self.orig, self.footer):
            lay.addWidget(w)
        self.dismissed = set()
        self._follow = QtCore.QTimer(self)
        self._follow.setInterval(500)
        self._follow.timeout.connect(self._place)
        self.hide()

    def _label(self, name):
        lbl = QtWidgets.QLabel()
        if name:
            lbl.setObjectName(name)
        lbl.setWordWrap(True)
        lbl.setTextFormat(wt.RICH)
        return lbl

    def show_problem(self, key, doc, rule, where, message, extra=""):
        self.key, self.doc = key, doc
        self._stop_movie()
        self.title.setText("⚠ " + rule["t"])
        self.where.setText(where)
        html = "<p>%s</p>" % rule["d"]
        if extra:
            html += "<p><b>%s</b></p>" % extra
        html += steps_html(rule.get("fix") or [])
        self.text.setText(html)
        self.footer.setText("WikiTips · κλικ στο μπλε όνομα: σου δείχνει το κουμπί" if "cmd:" in html else "WikiTips")
        self.note.setText("")
        msg = " ".join(message.split())
        self.orig.setText("Μήνυμα FreeCAD: %s" % msg[:200] if msg else "")
        img = rule.get("i")
        path = os.path.join(wt.CONTENT_IMG_DIR, img) if img else ""
        if path and os.path.isfile(path):
            self._movie = QtGui.QMovie(path)
            self._movie.jumpToFrame(0)
            sz = self._movie.currentImage().size()
            sz.scale(CARD_WIDTH - 30, 150, wt.KEEP_AR)
            self._movie.setScaledSize(sz)
            self.image.setMovie(self._movie)
            self._movie.start()
            self.image.show()
        else:
            self.image.hide()
        self._fit()
        self.show()
        self.raise_()
        self._follow.start()

    def _fit(self):
        inner = CARD_WIDTH - 30
        self.ensurePolished()
        for lbl in (self.where, self.text, self.note, self.orig, self.footer):
            lbl.ensurePolished()
            lbl.setFixedWidth(inner)
            h = lbl.heightForWidth(inner) if lbl.text() else 0
            lbl.setFixedHeight(max(0, h))
            lbl.setVisible(h > 0)
        tw = inner - 30
        self.title.setFixedWidth(tw)
        self.title.setFixedHeight(max(self.title.heightForWidth(tw), self.title.sizeHint().height()))
        self.layout().activate()
        self.setFixedHeight(self.layout().sizeHint().height())
        self._place()

    def _place(self):
        try:
            mw = self.parentWidget()
            area = mw.centralWidget().geometry() if mw.centralWidget() is not None else mw.rect()
            x = area.right() - self.width() - 16
            y = area.bottom() - self.height() - 16
            self.move(max(area.left(), x), max(area.top(), y))
        except Exception:
            pass

    def _link(self, href):
        try:
            if href.startswith("cmd:"):
                note = show_me(href[4:])
                self.note.setText(note)
                self._fit()
        except Exception:
            pass

    def _stop_movie(self):
        if self._movie is not None:
            self._movie.stop()
            self.image.setMovie(None)
            self._movie = None

    def _closed(self):
        if self.key is not None:
            self.dismissed.add(self.key)
        self.dismiss()

    def dismiss(self):
        self._follow.stop()
        self._stop_movie()
        self.key = self.doc = None
        self.hide()


# --------------------------------------------------------------------------
# watching documents and the Report view
# --------------------------------------------------------------------------
def _status(obj):
    try:
        st = obj.State
        if "Invalid" in st or "Error" in st:
            return obj.getStatusString() or ""
    except Exception:
        pass
    return None


def _solid_info(obj):
    try:
        sh = obj.Shape
        if sh.isNull():
            return None, 0
        return sh.Volume, len(sh.Solids)
    except Exception:
        return None, 0


class Explainer(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self.card = None
        self.pending = set()        # documents recomputed since the last check
        self.recomputed = {}        # document -> names of objects recomputed
        self.log_pos = None
        self.log_seen = {}
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(TICK_MS)
        self.timer.timeout.connect(self.tick)

    # -- document observer (called by FreeCAD) -----------------------------
    def slotRecomputedObject(self, obj):
        try:
            self.recomputed.setdefault(obj.Document.Name, set()).add(obj.Name)
        except Exception:
            pass

    def slotRecomputedDocument(self, doc):
        try:
            self.pending.add(doc.Name)
        except Exception:
            pass

    def slotDeletedDocument(self, doc):
        try:
            if self.card is not None and self.card.doc == doc.Name:
                self.card.dismiss()
        except Exception:
            pass

    # -- timer -------------------------------------------------------------
    def tick(self):
        try:
            if not enabled():
                if self.card is not None and self.card.isVisible():
                    self.card.dismiss()
                return
            self.check_log()
            # wait while a task dialog (Pad, sketch...) is open: values change while typing
            if self.pending and not Gui.Control.activeDialog():
                for name in list(self.pending):
                    self.pending.discard(name)
                    self.check_doc(name)
        except Exception:
            pass

    def ensure_card(self):
        if self.card is None:
            self.card = ErrorCard(Gui.getMainWindow())
        return self.card

    def check_doc(self, name):
        names = self.recomputed.pop(name, set())
        try:
            doc = App.getDocument(name)
        except Exception:
            return
        bad = [(o, m) for o, m in ((o, _status(o)) for o in doc.Objects) if m is not None]
        bad_names = {o.Name for o, _ in bad}
        roots = [(o, m) for o, m in bad
                 if not NOT_ROOT.match(o.TypeId) and not ({x.Name for x in o.OutListRecursive} & bad_names)]
        roots = roots or [(o, m) for o, m in bad if not NOT_ROOT.match(o.TypeId)]
        if roots:
            obj, msg = roots[0]
            rule = explain(msg, obj.TypeId)
            extra = ""
            if rule["id"] in ("conflicting", "redundant", "malformed"):
                nums = constraint_numbers(msg)
                if nums:
                    extra = "Αριθμοί περιορισμών: " + ", ".join(nums)
            if len(bad) > 1:
                extra = (extra + "<br>" if extra else "") + (
                    "Τα άλλα κόκκινα στο δέντρο συνήθως διορθώνονται μόνα τους μετά από αυτό.")
            self.show(("doc", name, obj.Name, msg), name, rule,
                      "Στο: <b>%s</b>" % obj.Label, msg, extra)
            return
        silent = self.silent_problem(doc, names)
        if silent:
            self.show(*silent)
            return
        # everything fine again: hide the card of this document, forget what was closed
        if self.card is not None:
            self.card.dismissed = {k for k in self.card.dismissed if k[1] != name}
            if self.card.doc == name:
                self.card.dismiss()

    def silent_problem(self, doc, names):
        for n in names:
            obj = doc.getObject(n)
            if obj is None or not SILENT_TYPES.match(obj.TypeId) or _status(obj) is not None:
                continue
            base = getattr(obj, "BaseFeature", None)
            vol, solids = _solid_info(obj)
            if vol is None:
                continue
            bvol, bsolids = _solid_info(base) if base is not None else (None, 0)
            if bvol is not None and abs(vol - bvol) <= 1e-6 * max(1.0, abs(bvol)):
                r = dict(special("_nochange"))
                r["d"] = r["d"] % obj.Label
                return (("nochange", doc.Name, obj.Name, round(vol, 6)), doc.Name, r,
                        "Στο: <b>%s</b>" % obj.Label, "")
            if solids > 1 and solids > bsolids:
                r = dict(special("_split"))
                r["t"] = r["t"] % solids
                r["d"] = r["d"] % obj.Label
                return (("split", doc.Name, obj.Name, solids), doc.Name, r,
                        "Στο: <b>%s</b>" % obj.Label, "")
        return None

    def check_log(self):
        mw = Gui.getMainWindow()
        rv = mw.findChild(QtWidgets.QTextEdit, "Report view") if mw is not None else None
        if rv is None:
            return
        doc = rv.document()
        n = doc.characterCount()
        if self.log_pos is None or n < self.log_pos:
            self.log_pos = n            # start: old messages are not explained
            return
        if n == self.log_pos:
            return
        cur = QtGui.QTextCursor(doc)
        cur.setPosition(max(self.log_pos - 1, n - 20000, 0))
        cur.movePosition(END, KEEP_ANCHOR)
        self.log_pos = n
        now = QtCore.QDateTime.currentMSecsSinceEpoch()
        for line in cur.selectedText().replace("\u2029", "\n").splitlines():
            line = _STAMP.sub("", line.strip())
            if not line or line.startswith("WikiTips"):
                continue
            rule = explain(line, src="log")
            if rule is None:
                continue
            if now - self.log_seen.get(line, 0) < 10000:   # the same line again and again
                continue
            self.log_seen[line] = now
            self.show(("log", "", rule["id"], line), None, rule, "Από το Report view", line)
            return

    def show(self, key, doc, rule, where, message, extra=""):
        card = self.ensure_card()
        if key in card.dismissed or (card.isVisible() and card.key == key):
            return
        card.show_problem(key, doc, rule, where, message, extra)


_EXPLAINER = None


def install():
    global _EXPLAINER
    if _EXPLAINER is not None:
        return
    _EXPLAINER = Explainer()
    App.addDocumentObserver(_EXPLAINER)
    _EXPLAINER.timer.start()
