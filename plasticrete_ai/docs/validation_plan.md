# What to cast next

Call `POST /optimize` for the plant's constraints. The response `tradeoff_points` already carry M1 means and the lower bound. `modules/batch_passport/suggest.py` ranks those points by interval width. The widest interval is the next cube to cast.

Five mixes is a pilot, not a validation of the model. The passport page records whatever the lab measures. This file does not list megapascal targets, because those numbers have to come from that response.
