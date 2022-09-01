import os
import sys
import subprocess

current_path = os.path.dirname(os.path.realpath(__file__))
libs_path = os.path.abspath(os.path.join(current_path, 'libs'))
# Installing dependencies
if not os.path.isdir(libs_path):
    subprocess.run([sys.executable, '-m', 'ensurepip'], check=True)
    subprocess.run(
        [
            sys.executable, '-m',
            'pip', 'install',
            '-r', os.path.abspath(os.path.join(current_path, 'requirements.txt')),
            '-t', libs_path
        ],
        check=True
    )

sys.path.append(libs_path)

from .diffusion_tools import DiffusionToolsExtension, DiffusionToolsDockWidget
from krita import DockWidgetFactory, DockWidgetFactoryBase

Krita.instance().addExtension(DiffusionToolsExtension(Krita.instance()))

DOCKER_ID = 'diffusion_tools_docker'
instance = Krita.instance()
dock_widget_factory = DockWidgetFactory(
    DOCKER_ID,
    DockWidgetFactoryBase.DockRight,
    DiffusionToolsDockWidget
)

instance.addDockWidgetFactory(dock_widget_factory)