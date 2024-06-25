# ++++++++++++++++++++++++++++
# Beschreibung:
# ++++++++++++++++++++++++++++
'''
Startprogramm/Hauptprogramm:
VIFCON wird ausgeführt wenn dieses Programm gestartet wird!

Die Grundstruktur von VIFCON beruht auf Multilog und dem Model View Controller (MVC) Modell!
'''

# ++++++++++++++++++++++++++++
# Bibliotheken:
# ++++++++++++++++++++++++++++
## Algemein:
from argparse import ArgumentParser

## Eigene:
from vifcon.vifcon_controller import main
from vifcon import __version__

# ++++++++++++++++++++++++++++
# Programm:
# ++++++++++++++++++++++++++++
if __name__ == "__main__":
    # Argparser Starten und Argumente definieren:
    parser = ArgumentParser(
        prog="vifcon",
        description="Use of the VIFCON control. Control and reading of various devices on one system.",
    )
    parser.add_argument(
        "-c",
        "--config",
        help="vifcon configuration file [optional, default='./config.yml']",
        default="./config.yml",
    )
    parser.add_argument(
        "-n",
        "--neustart",
        help="vifcon restart [optional, default=False]",
        action = 'store_true'
    )
    parser.add_argument(
        "-o",
        "--out_dir",
        help="directory where to put the output [optional, default='.']",
        default=".",
    )
    parser.add_argument(
        "-t",
        "--test",
        help="test-mode [optional, default=False]",
        action = 'store_true'
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"{parser.prog} version {__version__}",
    )
    args = parser.parse_args()
    main(args.config, args.out_dir, args.test, args.neustart)

##########################################
# Verworfen:
##########################################
## Bereich für alten Code, denn man noch nicht vollkommen löschen will,
## da dieser später vieleicht wieder ergänzt wird!!
'''


'''