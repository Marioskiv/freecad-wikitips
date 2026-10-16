import sys, os
sys.path[:0] = [sys.argv[1], sys.argv[2]]
from PySide6 import QtWidgets, QtGui, QtCore
app = QtWidgets.QApplication([])
import FreeCADGui
mw = QtWidgets.QMainWindow(); mw.resize(1400, 900)
tb = mw.addToolBar('t')
def act(name, text, tip):
    a = QtGui.QAction(text, mw); a.setObjectName(name); a.setToolTip(tip); return a
acts = {}
for n, t in [('PartDesign_Pad', '&Pad'), ('CAM_Profile', 'Profile'), ('Part_RefineShape', 'Refine shape'),
             ('Std_ViewFitAll', 'Fit all'), ('Path_Pocket_Shape', 'Pocket Shape'), ('Unknown_X', 'x')]:
    a = act(n, t, '<p>' + t + ' tip</p>'); tb.addAction(a); acts[n] = a
# real FreeCAD dropdown structure: group QAction (no menu) + menu set on the button
subs = [act('Sketcher_CreateCircle', 'Center and rim point', 'circle tip'),
        act('Sketcher_Create3PointCircle', '3 rim points', '3p tip')]
grp = act('Sketcher_CompCreateCircle', '3 rim points', '3p tip')   # second sub currently shown
tb.addAction(grp)
btn = tb.widgetForAction(grp); m = QtWidgets.QMenu(btn); m.addActions(subs); btn.setMenu(m)
btn.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)
acts['group(3 rim points)'] = grp
FreeCADGui.MW = mw; mw.show()
import wikitips, FreeCAD
wikitips.install(); wikitips._scan()
out = sys.argv[3]
def hover(a):
    b = tb.widgetForAction(a); pos = b.rect().center()
    QtWidgets.QApplication.sendEvent(b, QtGui.QHelpEvent(QtCore.QEvent.ToolTip, pos, b.mapToGlobal(pos)))
    return wikitips._FILTER.popup
for n, a in acts.items():
    p = hover(a)
    print('%-22s visible=%s title=%r' % (n, p.isVisible(), p.title.text() if p.isVisible() else None),
          'key=', wikitips.command_name(a, tb.widgetForAction(a)), 'h=', p.height())
    if p.isVisible(): p.grab().save(os.path.join(out, n.split('(')[0] + '.png'))
    p.dismiss()
# toggle off
FreeCADGui.CMDS['WikiTips_Toggle'].Activated()
p = hover(acts['PartDesign_Pad']); print('after toggle off visible=', p.isVisible())
FreeCADGui.CMDS['WikiTips_Toggle'].Activated()
print('toolbar params:', {k: v for k, v in FreeCAD._P.store.items() if 'Toolbar' in k[0]})
