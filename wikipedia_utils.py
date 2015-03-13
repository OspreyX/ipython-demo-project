# !pip install wikitools
# !pip install bokeh
# !pip install git+https://github.com/amueller/word_cloud
# !pip install --upgrade --no-deps git+https://github.com/wrobstory/vincent
# !pip install --upgrade git+https://github.com/apatil/folium
# !pip install --upgrade git+https://github.com/apatil/python-nvd3
# !pip install geopy

import bokeh
from bokeh import plotting
bokeh.plotting.output_notebook() # Tell bokeh to ouptut directly to the console

import nvd3
# nvd3.ipynb.initialize_javascript(use_remote=True)

import vincent
vincent.initialize_notebook()

import folium
import geopy
# folium.initialize_notebook()

from collections import OrderedDict
import wordcloud
import numpy as np
import pandas
import time

import wikitools
site = wikitools.wiki.Wiki("http://en.wikipedia.org/w/api.php") 

import IPython

def page_links(title):
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
def nearby_articles(place, radius=10000):
  location = geopy.geocoders.GoogleV3().geocode(place)
  
  map_widget = folium.Map(location=[location.latitude, location.longitude], zoom_start=17, tiles='Stamen Toner')

  params = {
            "action":"query", 
            "format":"json",
            "list": "geosearch",
            "gsradius": radius,
            "gscoord": "%s|%s" % (location.latitude, location.longitude)
           }
  request = wikitools.api.APIRequest(site, params)
  result = request.query()
  
  for page in result["query"]["geosearch"]:  
    map_widget.simple_marker([page["lat"], page["lon"]], popup=page["title"])
  fname = "map_widget_%s.html" % place
  map_widget.create_map(path="/cdn/%s" % fname)
  return IPython.display.HTML("<iframe src='%s' width=1200px height=600px>" % fname)

nearby_articles("Trondheim")

get.revision.series <- function(page) {
  response <- GET("http://en.wikipedia.org/w/api.php?", query=list(
    format="json",
    action="query",
    prop="revisions",
    titles=page,
    rvprop="timestamp|user",
    rvlimit=1000
  ))
  pages <- httr::content(response, "parsed")$query$pages
  revisions <- pages[[names(pages)[[1]]]]$revisions
  timestamp <- revisions %>% purrr::map(~ .$timestamp) %>% unlist
  ct <- as.POSIXct(timestamp, format = "%Y-%m-%d")
  ts <- xts(rep(1, length(ct)), ct)
  agg <- suppressWarnings(aggregate(as.zoo(ts), time(ts), sum))
  xts(unlist(agg), time(agg))
}

def get_revision_series(title):
  params = {
            "action":"query", 
            "format":"json",
            "prop": "revisions",
            "titles": title,
            "rvprop": "timestamp|user",
            "rvlimit": 1000
           }
  request = wikitools.api.APIRequest(site, params)
  result = request.query()
  revisions = result["query"]["pages"].values()[0]["revisions"]
  timestamp = [np.datetime64(revision["timestamp"]) for revision in revisions]
  s = pandas.DataFrame(1, index=timestamp, columns=['n']).resample('D', how='count')
  return pandas.Series(np.asarray(s), index=[i[0] for i in s._index])

def get_two_revision_series(title1, title2):
  r1, r2 = [get_revision_series(title) for title in (title1, title2)]
  common_start = np.max([r.index.min() for r in (r1, r2)])
  common_end = np.max([r.index.max() for r in (r1, r2)])
  ix = pandas.DatetimeIndex(start=common_start, end=common_end, freq='D')
  return [r.reindex(ix, fill_value=0) for r in (r1, r2)]

def compare_revisions(title1, title2):
  chart = nvd3.stackedAreaChart(name='stackedAreaChart',height=450,width=600,use_interactive_guideline=True)
  r1, r2 = get_two_revision_series(title1, title2)
  
  x = [int(time.mktime(idx.timetuple()) * 1000) for idx in r1.index]
  y = [[int(count) for count in np.asarray(np.cumsum(r))] for r in [r1, r2]]
  
  chart.add_serie(name=title1, y=y[0], x=x, x_is_date=True,  x_axis_format="%d %b %Y")
  chart.add_serie(name=title2, y=y[1], x=x, x_is_date=True,  x_axis_format="%d %b %Y")
  chart.buildhtml()
  file("/cdn/chart.html", "w").write(chart.htmlcontent)
  return IPython.display.HTML("<iframe src=chart.html width=800px height=550px>")
compare_revisions("J. K. Rowling", "George R. R. Martin")