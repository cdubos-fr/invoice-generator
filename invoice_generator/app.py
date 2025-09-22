"""Point d'entrée de l'application Invoice Generator (UI PyQt6).

Ce module initialise QApplication, le contrôleur et la fenêtre principale.
"""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from .controller.app_controller import AppController


def main() -> None:
    """Lancer l'application graphique."""
    app = QApplication(sys.argv)
    controller = AppController()
    controller.show()
    sys.exit(app.exec())


if __name__ == '__main__':  # pragma: no cover - point d'entrée manuel
    main()
