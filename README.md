# Krita addon for Image AI Utils

## Installation
### Manual Installation
```bash
git clone git@github.com:qweryty/image-ai-utils-krita.git
cd image-ai-utils-krita
pip install -r requirements.txt image_ai_utils/libs
cp -r image_ai_utils $PATH_TO_PYKRITA
cp image_ai_utils.desktop $PATH_TO_PYKRITA
```

## Setting up
Before you can use the plugin, you should setup server credentials first.
For that, press `Settings` button in addon panel and fill your server credentials there.

You can test the connection to server using `Test Connection` button. 
If the connection was not successful, it will show you an error message, which you can use to debug your problem.
