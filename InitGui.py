# SPDX-License-Identifier: LGPL-2.1-or-later
# WikiTips: picture + explanation from the FreeCAD wiki on toolbar hover.
try:
    import wikitips
    wikitips.install()
except Exception as e:  # never break FreeCAD start-up
    import FreeCAD
    FreeCAD.Console.PrintError("WikiTips could not start: %s\n" % e)
