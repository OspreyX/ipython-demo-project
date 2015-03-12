# !pip install wikitools
# !pip install bokeh
# !pip install git+https://github.com/amueller/word_cloud
# !pip install --upgrade --no-deps git+https://github.com/wrobstory/vincent
# !pip install --upgrade git+https://github.com/apatil/folium
# !pip install --upgrade git+https://github.com/apatil/python-nvd3

import bokeh
from bokeh import plotting
bokeh.plotting.output_notebook() # Tell bokeh to ouptut directly to the console

import nvd3
# nvd3.ipynb.initialize_javascript(use_remote=True)

import vincent
vincent.initialize_notebook()

import folium
# folium.initialize_notebook()

from collections import OrderedDict
import wordcloud
import numpy as np

import wikitools
site = wikitools.wiki.Wiki("http://en.wikipedia.org/w/api.php") 

def page_links(title):
  # define the params for the query
#  params = {
#            "action":"query", 
#            "format":"json",
#            "prop": "links",
#            "pllimit": 100,
#            "titles": title
#           }
#  request = wikitools.api.APIRequest(site, params)
#  result = request.query()
#  links = result["query"]["pages"].values()[0]["links"]
#  return [{"src": title, "target": link["title"]} for link in links]
  links = wikitools.page.Page(site, title).getLinks()
  return [{"src": title, "target": link} for link in links]

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
  
  source = bokeh.models.ColumnDataSource(
      data=dict(
          colors=colors,
          xname=name_mat.flatten(),
          yname=name_mat.T.flatten()
      )
  )
  
  p = bokeh.plotting.figure(title="Wikipedia Neighborhood of %s" % title,
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
  
  hover = p.select(dict(type=bokeh.models.HoverTool))
  hover.tooltips = OrderedDict([
      ('titles', '@yname, @xname')
  ])
  
  bokeh.plotting.show(p)
page_neighborhood("David Blackwell")  


# Word cloud
def vincent_wordcloud(title):
  text = wikitools.page.Page(site, title).getWikiText()

  # mask may or may not work with Vincent.
  stopwords = wordcloud.STOPWORDS
  stopwords.add("ref")
  stopwords.add("cite")
  stopwords.add("date")
  stopwords.add("pp")
  
  wc = wordcloud.WordCloud(background_color='white').generate(text)
  
  words = wc.words_
  #Encodes for each word the string, font size, position, orientation and color.
  #layout = wordcloud.layout_
  
  normalize = lambda x: int(x * 90 + 10)
  word_list = {word: normalize(size) for word, size in words}
  w = vincent.Word(word_list)
  for mark in w.marks:
    mark.properties.hover = vincent.PropertySet()
    mark.properties.hover.fill = vincent.ValueRef(value='red')
    mark.properties.update = vincent.PropertySet()
    mark.properties.update.fill = vincent.ValueRef(field='data.idx', scale='color')

  return w
vincent_wordcloud("Python (programming language)")


# Folium at least works
def nearby_articles():
  map_1 = folium.Map(location=[45.372, -121.6972], zoom_start=12,
                     tiles='Stamen Terrain')
  map_1.simple_marker([45.3288, -121.6625], popup='Mt. Hood Meadows')
  map_1.simple_marker([45.3311, -121.7113], popup='Timberline Lodge')
  map_1.create_map(path='/cdn/mthood.html')
  from IPython.display import HTML
  return HTML("<iframe src=mthood.html width=1200px height=600px>")
  
  #c = figure(tools=TOOLS)
  #c.circle(acme, choam, color='#A6CEE3', legend='close')
  #c.title = "ACME / CHOAM Correlations"
  #c.grid.grid_line_alpha=0.3
  
  #show(c)  # open a browser
nearby_articles()

def stacked_ts():
  type = 'stackedAreaChart'
  chart2 = nvd3.stackedAreaChart(name=type,height=450,width=600,use_interactive_guideline=True)
  nb_element = 50
  xdata = range(nb_element)
  ydata = [i * random.randint(1, 10) for i in range(nb_element)]
  ydata2 = [x * 2 for x in ydata]
  ydata3 = [x * 5 for x in ydata]
  chart2.add_serie(name="serie 1", y=ydata, x=xdata)
  chart2.add_serie(name="serie 2", y=ydata2, x=xdata)
  chart2.add_serie(name="serie 3", y=ydata3, x=xdata)
  chart2.buildhtml()
  file("/cdn/chart.html", "w").write(chart2.htmlcontent)
  from IPython.display import HTML
  return HTML("<iframe src=chart.html width=800px height=550px>")
stacked_ts()