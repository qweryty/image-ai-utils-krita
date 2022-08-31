import os
import sys
print(

    os.path.abspath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), 'libs')
    )
)
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), 'libs')
    )
)

from .diffusion_tools import DiffusionToolsExtension, DiffusionToolsDockWidget
from .libs.dotenv import load_dotenv
from krita import DockWidgetFactory, DockWidgetFactoryBase

load_dotenv()

Krita.instance().addExtension(DiffusionToolsExtension(Krita.instance()))

DOCKER_ID = 'diffusion_tools_docker'
instance = Krita.instance()
dock_widget_factory = DockWidgetFactory(
    DOCKER_ID,
    DockWidgetFactoryBase.DockRight,
    DiffusionToolsDockWidget
)

instance.addDockWidgetFactory(dock_widget_factory)