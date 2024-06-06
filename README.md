# Sketchfab-GUI
A sketchfab application to automatically upload multiple models to sketchfab using API.
The appliaction allows us to upload multiple models simultaneously rather than uploading 1 by 1 in their website.

# Setup
Insert your api-key in line 16 to show proper categories in GUI ( To-do, need to be updated to take it differently ).
Install required dependencies and run the script or build it.
setup.py build

# User-Guide
Currently supports upload of up-to 100 models at a time before getting too many requests error from API.
1. Enter your own API-key, where you want to upload the models.
2. Select the upload mode (Singler Folder) or Multiple Folders.
2.1. Single Folder will allow the selection of 1 folder through browse, won't append new folders.
2.1. When multiple folder selected, you can keep adding folders to it through browse, appending the list.
3. Description is set in a text box.
4. Tags are set in a new-seperate line.
4.1. Tags written in a line like this: This is a new tag will save as This-is-a-new-tag
5. Category 1 is a must selection, won't work if it's not set.
5.1. Category 2 is not required but will append to the Category 1 if it is set, saving 2 categories.
6. Standard or Editorial licenses require a set price, minimum is 3.99.
7. Private checkbox will make the model private if it is checked.
8. Publish checkbox will publish the model.
9. Clicking on Reset form will reset all the inputs entered.
10. After clicking the upload button, a new status window will appear for the selected batch of uploads.
10.1. The Status window name will include how many models are uploading in total as well as folder name.
10.2. Status window will display the progress of upload, processing, patching and a summary.
10.3. Red color - means the upload failed. Orange color - means the patch failed.

Happy uploading!

# Some Pictures of the GUI

![alt text](https://github.com/KarolisJasad/Sketchfab-GUI/blob/main/Sketchfabmain.png?raw=true)
![alt text](https://github.com/KarolisJasad/Sketchfab-GUI/blob/main/SketchfabMainText.png?raw=true)
![alt text](https://github.com/KarolisJasad/Sketchfab-GUI/blob/main/SketchfabStatus.png?raw=true)
