# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


df = pd.read_csv("20190702-154313.txt", names=["delta"])

df["rate"] = 1.0 / df["delta"]

sns.distplot(df["rate"])
