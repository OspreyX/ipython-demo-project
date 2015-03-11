# !pip install wikitools
# !pip install bokeh

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

def page_neighborhood(page, include_original=False):
  links = page_links(page)
  in_links = dict([(link["target"], True) for link in links])
  if include_original:
    in_links[page] = True
  def reducer(sofar, title):
    new_links = page_links(title)
    keep = [link for link in new_links if in_links.get(link["target"], False)]
    return sofar + keep
  return reduce(reducer, [link["target"] for link in links], (links if include_original else []))
  
# mapping: https://github.com/python-visualization/folium

# plots: bokeh or vincent

# time series: wrobstory/bearcat, http://bl.ocks.org/wrobstory/raw/5538300/

def plot_network(title):
  links = page_network(title)
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