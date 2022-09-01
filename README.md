# Krita addon for Image AI Utils
## Features
- Text to image
- Image to image
- Inpainting
- Upscaling using [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN)

## Planned features
- [ ] GoBIG upscaling
- [ ] [GFPGAN](https://github.com/TencentARC/GFPGAN) face restoration
- [ ] Make texture tilable
- [ ] Quality of Life features
- [ ] Ports to other programs

## Installation
- Install server from [here](https://github.com/qweryty/image-ai-utils-server)
- Download the latest `image_ai_utils.zip` from [releases](https://github.com/qweryty/image-ai-utils-krita/releases) page
- Follow the [official manual](https://docs.krita.org/en/user_manual/python_scripting/install_custom_python_plugin.html) to install plugin
- The first Krita restart may be slower than usual because the plugin needs to install it's dependencies
- Before you can use the plugin, you should setup server credentials first.
For that, press `Settings` button in addon panel and fill your server credentials there.
  - You can test the connection to server using `Test Connection` button
If the connection was not successful, it will show you an error message, which you can use to debug your problem.
