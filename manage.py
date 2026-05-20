#!/usr/bin/env python
import os
import sys


def main() -> None:
    # Django komutlarının hangi ayar dosyasıyla çalışacağını belirler.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "qrcode_project.settings")
    from django.core.management import execute_from_command_line
    # Terminalden gelen komutları (runserver, migrate vb.) Django'ya iletir.
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()