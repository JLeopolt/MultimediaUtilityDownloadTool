# A multimedia utility downloader and converter tool which can download media sources from the Web.

import core
import core.graphics.gui as gui


def get_software_details():
    details = "Multimedia Utility Download Tool v" + core.__version__
    details += '\n' + "Copyright (c) 2023 PyroNeon Software. Licensed under GPL-3.0 License."
    return details


if __name__ == '__main__':
    gui.App().mainloop()
