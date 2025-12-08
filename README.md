# Gabe-Forest-Plotter

Python script that builds a clean forest plot with an aligned results table. Exports high quality figures (PDF, PNG, TIFF).

## Example Output:
![alt text](https://github.com/GabrielBonassi77/Gabe-Forest-Plotter/blob/main/FigureExample.png "Example Figure 1")

## How to Use:

1. Open script in Google Colab (make sure you're signed into Google): Link (https://colab.research.google.com/drive/1bLZIyY-uqO1ydYCxyEiA2jDn9-ofaf4x?usp=sharing)
2. In Colab, go to **File → Save a copy in Drive** so you can edit.

## How to Customize:

In your copy of the notebook:

  Change the effect measure label (HR, RR, OR) by editing:
  ```python
  EFFECT_MEASURE = "HR"  # or "RR", "OR"
  ```

  Edit the EVENT_STATS list with your own outcomes and 95% CIs:
  ```EVENT_STATS = [
    ("Outcome label", midpoint, lower_CI, upper_CI),
    # add more rows here
  ```

Then run the script. You will be prompted some questions about x-axis design (left-most value, right-most value, how many ticks, etc.; if you don't know what to choose, just go with the recommended values and hit enter for each prompt).
Feel free to play around with it until you get your ideal figure. After all prompts are answered, the script will output the following:
- forestpanel.pdf
- forestpanel.png
- forestpanel.tiff

## Citations:

To obtain a list of all library versions used in the script within the Collab environment, run the citation helper code block: 
```
import sys
import pandas as pd
import matplotlib

print("Python:", sys.version)
print("pandas:", pd.__version__)
print("matplotlib:", matplotlib.__version__)
```
