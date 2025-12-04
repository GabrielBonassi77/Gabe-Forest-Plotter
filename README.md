# Gabe-Forest-Plotter

Python notebook that builds a clean forest plot with a linked results table and exports high resolution figures (PDF, PNG, TIFF).

## Use in Colab

1. Open Code in Colab: Link (https://colab.research.google.com/drive/1bLZIyY-uqO1ydYCxyEiA2jDn9-ofaf4x?usp=sharing)
2. In Colab, go to **File → Save a copy in Drive** so you can edit.

## How to customize

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

Then run all cells. The notebook will create:
- forestpanel.pdf
- forestpanel.png
- forestpanel.tiff

## Citations

To obtain a list of all library versions, run the citation helper code block: 
```
import sys
import pandas as pd
import matplotlib

print("Python:", sys.version)
print("pandas:", pd.__version__)
print("matplotlib:", matplotlib.__version__)
```
