# Krita addon for Image AI Utils based on Stable Diffusion
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
- Download the latest `image_ai_utils.zip`(`image_ai_utils_windows_krita510.zip` for Windows, requires Krita 5.1.0) from [releases](https://github.com/qweryty/image-ai-utils-krita/releases) page
- Follow the [official manual](https://docs.krita.org/en/user_manual/python_scripting/install_custom_python_plugin.html) to install plugin
- The first Krita restart may be slower than usual because the plugin needs to install it's dependencies
- Before you can use the plugin, you should setup server credentials first.
For that, press `Settings` button in addon panel and fill your server credentials there.
  - You can test the connection to server using `Test Connection` button
If the connection was not successful, it will show you an error message, which you can use to debug your problem.

## Usage tips
- All operations work on active layer only
- `Img2Img` and `Inpaint` operations perform badly on areas with transparency(this is considered a bug and will be fixed soon)
- `Inpaint` works by using transparency mask
- If the selected region is not a rectangle, its bounding box will be used
- If there is no selected region, the operation will work on the whole image
