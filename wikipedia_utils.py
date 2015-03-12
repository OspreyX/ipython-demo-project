# !pip install wikitools
# !pip install bokeh
# !pip install --upgrade git+https://github.com/apatil/bearcart.git

from collections import OrderedDict

import numpy as np

from bokeh.plotting import *
output_notebook() # Tell bokeh to ouptut directly to the console

from bokeh.models import HoverTool, ColumnDataSource
from bokeh.sampledata.les_mis import data

from wikitools import wiki
from wikitools import api
site = wiki.Wiki("http://en.wikipedia.org/w/api.php") 

def page_links(title):
  # define the params for the query
  params = {
            "action":"query", 
            "format":"json",
            "prop": "links",
            "pllimit": 100,
            "titles": title
           }
  request = api.APIRequest(site, params)
  result = request.query()
  links = result["query"]["pages"].values()[0]["links"]
  return [{"src": title, "target": link["title"]} for link in links]

def page_neighborhood_links(page, include_original=False):
  links = page_links(page)
  in_links = dict([(link["target"], True) for link in links])
  if include_original:
    in_links[page] = True
  def reducer(sofar, title):
    new_links = page_links(title)
    keep = [link for link in new_links if in_links.get(link["target"], False)]
    return sofar + keep
  return reduce(reducer, [link["target"] for link in links], (links if include_original else []))
  
def page_neighborhood(title):
  links = page_neighborhood_links(title)
  names = list(set([link['src'] for link in links] + [link['target'] for link in links]))
  N = len(names)
  mat = np.zeros((N, N), dtype='bool')
  name_lookup = dict([(names[i], i) for i in xrange(len(names))])
  for link in links:
    src_i = name_lookup[link['src']]
    target_i = name_lookup[link['target']]
    mat[src_i, target_i] = mat[target_i, src_i] = True
  
  count = mat.flatten()
  colors = np.repeat('lightgrey', len(count))
  colors[np.where(count)] = 'black'
  
  name_mat = np.tile(names, (N,1))
  
  source = ColumnDataSource(
      data=dict(
          colors=colors,
          xname=name_mat.flatten(),
          yname=name_mat.T.flatten()
      )
  )
  
  p = figure(title="Wikipedia Neighborhood of %s" % title,
      x_axis_location="above", tools="resize,hover,save",
      x_range=list(reversed(names)), y_range=names)
  p.plot_width = 800
  p.plot_height = 800
  
  p.rect('xname', 'yname', 0.9, 0.9, source=source,
       color='colors', alpha=1.0, line_color=None)
  
  p.grid.grid_line_color = None
  p.axis.axis_line_color = None
  p.axis.major_tick_line_color = None
  p.axis.major_label_text_font_size = "5pt"
  p.axis.major_label_standoff = 0
  p.xaxis.major_label_orientation = np.pi/3
  
  hover = p.select(dict(type=HoverTool))
  hover.tooltips = OrderedDict([
      ('titles', '@yname, @xname')
  ])
  
  show(p)

# Kartograph
#!pip install git+https://github.com/kartograph/kartograph.py  
#!pip install tinycss
#yuck, bundle gdal from pypi into image. The latest version
#does not work because ubuntu's libgdal-dev is out of date.
#!CPLUS_INCLUDE_PATH=/usr/include/gdal C_INCLUDE_PATH=/usr/include/gdal pip install GDAL==1.9.0
import kartograph
  
# Folium at least works
# !pip install --upgrade git+https://github.com/apatil/folium
import folium
map_1 = folium.Map(location=[45.372, -121.6972], zoom_start=12,
                   tiles='Stamen Terrain')
map_1.simple_marker([45.3288, -121.6625], popup='Mt. Hood Meadows')
map_1.simple_marker([45.3311, -121.7113], popup='Timberline Lodge')
map_1.create_map(path='/cdn/mthood.html')
from IPython.display import HTML
HTML("<iframe src=mthood.html width=1200px height=600px>")


# bokeh time series attempt doesnt work well
import time
from numpy import cumprod, linspace, random
from bokeh.plotting import *
num_points = 300

now = time.time()
dt = 24*3600 # days in seconds
dates = linspace(now, now + num_points*dt, num_points) * 1000 # times in ms
acme = cumprod(random.lognormal(0.0, 0.04, size=num_points))
choam = cumprod(random.lognormal(0.0, 0.04, size=num_points))

TOOLS = "pan,wheel_zoom,box_zoom,reset,save,hover"
output_file("correlation.html", title="correlation.py example")

r = figure(x_axis_type = "datetime", tools=TOOLS)
r.line(dates, acme, color='#1F78B4', legend='ACME')
r.line(dates, choam, color='#FB9A99', legend='CHOAM')
r.title = "Stock Returns"
r.grid.grid_line_alpha=0.

hover = r.select(dict(type=HoverTool))

hover.tooltips = [
    # add to this
    ("value", "$y"),
]

show(r)

#c = figure(tools=TOOLS)
#c.circle(acme, choam, color='#A6CEE3', legend='close')
#c.title = "ACME / CHOAM Correlations"
#c.grid.grid_line_alpha=0.3

#show(c)  # open a browser



# nvd3: patch should make it workable, try iframing it.
# !pip install --upgrade git+https://github.com/apatil/python-nvd3
import nvd3
nvd3.ipynb.initialize_javascript(use_remote=True)
type = 'stackedAreaChart'
chart2 = nvd3.stackedAreaChart(name=type,height=450,use_interactive_guideline=True)
nb_element = 50
xdata = range(nb_element)
ydata = [i * random.randint(1, 10) for i in range(nb_element)]
ydata2 = [x * 2 for x in ydata]
ydata3 = [x * 5 for x in ydata]
chart2.add_serie(name="serie 1", y=ydata, x=xdata)
chart2.add_serie(name="serie 2", y=ydata2, x=xdata)
chart2.add_serie(name="serie 3", y=ydata3, x=xdata)
chart2.buildhtml()
chart2


# networkx: doesn't dump standalone html.
# !pip install networkx
import json
import networkx as nx
from networkx.readwrite import json_graph
G = nx.barbell_graph(6,3)
# this d3 example uses the name attribute for the mouse-hover value,
# so add a name to each node
for n in G:
    G.node[n]['name'] = n
# write json formatted data
d = json_graph.node_link_data(G) # node-link format to serialize
# write json
json.dump(d, open('/cdn/force.json','w'))
print('Wrote node-link JSON data to /cdn/force.json')
# open URL in running web browser


# time series: wrobstory/bearcat, http://bl.ocks.org/wrobstory/raw/5538300/
import bearcart
import pandas as pd
def bearcart_plot():
  import os
  os.chdir('/cdn')
  price = pd.DataFrame({'AAPL': np.cumsum(np.random.normal(size=100)), 
                        'GOOG': np.cumsum(np.random.normal(size=100))})
  
  vis = bearcart.Chart(price, plt_type='area', x_time=False, auto_resize=True)
  vis.create_chart(html_path='index.html')
  from IPython.display import HTML
  HTML("<iframe src=index.html width=640px height=380px>")

  
# pygal: works ok, but interaction/tooltips don't work
#!pip install pygal
import pygal
from pygal.style import LightStyle
stackedline_chart = pygal.StackedLine(fill=True, style=LightStyle)
stackedline_chart.title = 'Browser usage evolution (in %)'
stackedline_chart.x_labels = map(str, range(2002, 2013))
stackedline_chart.add('Firefox', [None, None, 0, 16.6,   25,   31, 36.4, 45.5, 46.3, 42.8, 37.1])
stackedline_chart.add('Chrome',  [None, None, None, None, None, None,    0,  3.9, 10.8, 23.8, 35.3])
stackedline_chart.add('IE',      [85.8, 84.6, 84.7, 74.5,   66, 58.6, 54.7, 44.8, 36.2, 26.6, 20.1])
stackedline_chart.add('Others',  [14.2, 15.4, 15.3,  8.9,    9, 10.4,  8.9,  5.8,  6.7,  6.8,  7.5])
stackedline_chart


#!pip install --upgrade --no-deps git+https://github.com/wrobstory/vincent
import vincent
import pandas as pd
import random

#Iterable
list_data = [10, 20, 30, 20, 15, 30, 45]

#Dicts of iterables
cat_1 = ['y1', 'y2', 'y3', 'y4']
index_1 = range(0, 21, 1)
multi_iter1 = {'index': index_1}
for cat in cat_1:
    multi_iter1[cat] = [random.randint(10, 100) for x in index_1]

bar = vincent.Bar(multi_iter1['y1'])
bar.axis_titles(x='Index', y='Value')
bar.to_json('vega.json')
from IPython.display import HTML
HTML("<iframe src=vega_template.html width=1200px height=600px>")