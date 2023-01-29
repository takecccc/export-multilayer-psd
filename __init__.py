from .logging_util import log_info, log_warn, log_error
from PySide2 import QtWidgets
from PySide2.QtCore import Qt
import substance_painter.ui

if "export_dialog" in locals():
    log_info("reload module")
    import importlib
    importlib.reload(export_dialog)
else:
    from . import export_dialog

plugin_widgets = []

def export():
    log_info("export")
    main_window = substance_painter.ui.get_main_window()
    dialog = export_dialog.ExportDialog(parent=main_window)
    dialog.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
    dialog.exec_()

def start_plugin():
    log_info(f"{__file__} start")
    export_action = QtWidgets.QAction("export as multilayer psd")
    export_action.triggered.connect(export)
    substance_painter.ui.add_action(substance_painter.ui.ApplicationMenu.File, export_action)
    plugin_widgets.append(export_action)

def close_plugin():
    log_info(f"{__file__} close")
    global plugin_widgets
    for widget in plugin_widgets:
        substance_painter.ui.delete_ui_element(widget)
    plugin_widgets.clear()

if __name__ == "__main__":
    start_plugin()