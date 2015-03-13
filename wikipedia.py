# Modern data visualization in Python
# ===================================
# 
# One of the nicest side effects of the widespread adoption of [IPython notebooks](http://ipython.org/notebook.html)
# in the Python community has been a bumper crop of rich interactive web graphics
# libraries. This project shows some of the awesome things you can do with datasets
# drawn from [Wikipedia](https://en.wikipedia.org).


# Visualizing Wikipedia Neighborhoods
# -----------------------------------
#
# Wikipedia's [public API](http://en.wikipedia.org/w/api.php) is an
# incredibly interesting data source. 
#
# We can use [bokeh](http://bokeh.pydata.org/en/latest/index.html)
# to visualize the links between pages in a beautiful and
# interactive way. Here's the [neighborhood](http://en.wikipedia.org/wiki/Neighbourhood_(graph_theory)
# of the [BDFL](http://en.wikipedia.org/wiki/Benevolent_dictator_for_life).
# Each black square represents a pair of Wikipedia pages that are linked.

from wikipedia_utils import *
page_neighborhood("Guido van Rossum")

# For a more meta experience, try `page.neighborhood("Adjacency matrix")`!


# Word clouds
# -----------
#
# [Word clouds](http://en.wikipedia.org/wiki/Tag_cloud) are a fun way to visualize the text in
# a website. In addition to more standard plots, [vincent](https://github.com/wrobstory/vincent)
# can create simple HTML word clouds. Let's see which words are most used in a Wikipedia page:

vincent_wordcloud("Honey Badger")

# Give it a try with your favorite animal.


# Mapping nearby pages
# --------------------
#
# The [folium](https://github.com/python-visualization/folium/) library generates
# beautiful interactive maps of geospatial datasets. Here's a map
# of the Wikipedia articles within 10km of a certain place, as
# geolocated by the Google geocoding API via [geopy](https://github.com/geopy/geopy). 
# Click on a marker to see the title of the corresponding Wikipedia 
# page.

nearby_articles("Trondheim")

# If you're not crazy about the black and white [map tiles](http://maps.stamen.com/#toner), 
# try `nearby_articles("Trondheim", tiles="OpenStreetMap")`!


# Comparing revision activity
# ---------------------------
#
# Now let's take a look at the cumulative revisions two different pages
# have been getting using the interactive time series library
# [python-nvd3](https://github.com/areski/python-nvd3).

compare_revisions("Mumbai", "Bangalore")

# You can click the radio buttons to change the format of the plot.

# Going further
# -------------
# 
# Try calling these functions with different arguments. If you want to see how they're
# implemented, or change the implementation, see `wikipedia_utils.py`.
# 
# There are many other awesome web visualization libraries available for Python,
# including [networkx](https://networkx.github.io/), [pygal](http://pygal.org/),
# [bearcart](https://github.io/wrobstory/bearcart), [mpld3](https://http://mpld3.github.io/),
# and [kartograph](http://kartograph.org/).
# 
# If you come up with a visualization that you think is cool, please
# share it with us! Just grab the link console link from your 
# browser's URL bar and tweet it to [@senseplatform](https://twitter.com/senseplatform).