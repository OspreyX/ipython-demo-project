# Package Installation
# --------------------
# 
# These packages only need to be installed once per project.
# Once they're installed, every console launched in the project
# can use them.
# 
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

import IPython

# Wikipedia neighborhood adjacency matrix
# =======================================

def page_links(title, lang="en"):
  """
  Obtains all the links in the Wikipedia page with the given title. 
  Links are returned as a list of dicts with keys "src" and "target".
  """
  
  # Use wikitools to get the links in the page.
  site = wikitools.wiki.Wiki("http://%s.wikipedia.org/w/api.php" % lang) 
  links = wikitools.page.Page(site, title).getLinks()
  return [{"src": title, "target": link} for link in links]

def page_neighborhood_links(page, include_original=False, lang="en"):
  """
  Obtains all the links in the neighborhood of the Wikipedia page with
  the given title. If include_original is False, the open neighborhood
  is returned. Links are returned as a list of dicts with keys "src" and
  "target".
  """
  links = [link for link in page_links(page, lang) if ":" not in link["target"]]
  in_links = dict([(link["target"], True) for link in links])
  if include_original:
    in_links[page] = True
  def reducer(sofar, title):
    try:
      new_links = page_links(title)
      keep = [link for link in new_links if in_links.get(link["target"], False)]
      return sofar + keep
    except wikitools.NoPage:
      return sofar
  return reduce(reducer, [link["target"] for link in links], (links if include_original else []))
  
def page_neighborhood(title, lang="en"):
  """
  Displays the Wikipedia neighborhood of the given title as a Bokeh plot
  along the lines of http://bokeh.pydata.org/en/latest/docs/gallery/les_mis.html.
  """

  # Create the adjancency matrix as a NumPy matrix.
  links = page_neighborhood_links(title, lang=lang)
  names = list(set([link['src'] for link in links] + [link['target'] for link in links]))
  N = len(names)
  mat = np.zeros((N, N), dtype='bool')
  name_lookup = dict([(names[i], i) for i in xrange(len(names))])
  for link in links:
    src_i = name_lookup[link['src']]
    target_i = name_lookup[link['target']]
    mat[src_i, target_i] = mat[target_i, src_i] = True

  # Convert the adjacency matrix to a vector of colors. There's a 'black'
  # where there is a link, 'lightgrey' otherwise.
  count = mat.flatten()
  colors = np.repeat('lightgrey', len(count))
  colors[np.where(count)] = 'black'
  
  # Create the data object that Bokeh will use to make the plot. It contains
  # three vectors that hold the 'src' and 'target' of each pair of titles, and 
  # a color indicating whether there is a link between the two.
  name_mat = np.tile(names, (N,1))
  source = bokeh.models.ColumnDataSource(
      data=dict(
          colors=colors,
          xname=name_mat.flatten(),
          yname=name_mat.T.flatten()
      )
  )
  
  # Create the Bokeh plot object, and format it nicely.
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
  
  # Add tooltip behavior to the plot, so you see the name of each 
  # pair of pages when your mouse hovers over the corresponding tile.
  hover = p.select(dict(type=bokeh.models.HoverTool))
  hover.tooltips = OrderedDict([
      ('titles', '@yname, @xname')
  ])
  
  # Tell Bokeh to hand the plot to IPython's rich display system.
  # Note, this works because we called bokeh.plotting.output_notebook()
  # above.
  bokeh.plotting.show(p)


# Word cloud
# ==========

def vincent_wordcloud(title, lang="en"):
  """
  Displays the words in a Wikipedia page as a word cloud.
  """
  
  # Use wikitools to get the text of the page.
  site = wikitools.wiki.Wiki("http://%s.wikipedia.org/w/api.php" % lang) 
  text = wikitools.page.Page(site, title).getWikiText()

  # Add some wikipedia-specific 'stop words', which we don't want
  # in the word cloud.
  stopwords = wordcloud.STOPWORDS
  stopwords.add("ref")
  stopwords.add("cite")
  stopwords.add("date")
  stopwords.add("pp")

  # Use the wordcloud module to compute the word cloud.  
  wc = wordcloud.WordCloud(background_color='white').generate(text)
  
  # Pass the words and their respective sizes to Vincent, whic
  # passes them to Vega's word cloud renderer.
  words = wc.words_
  normalize = lambda x: int(x * 90 + 10)
  word_list = {word: normalize(size) for word, size in words}
  w = vincent.Word(word_list)
  for mark in w.marks:
    mark.properties.hover = vincent.PropertySet()
    mark.properties.hover.fill = vincent.ValueRef(value='red')
    mark.properties.update = vincent.PropertySet()
    mark.properties.update.fill = vincent.ValueRef(field='data.idx', scale='color')

  # Return the Vincent object. In environments that use the IPython
  # rich display system, it will display as an HTML word cloud.
  return w


# Mapping nearby articles
# =======================

def nearby_articles(place, radius=10000, tiles='Stamen Toner', lang="en"):
  """
  Returns a Folium widget containing up to ten of the Wikipedia
  articles within 10km of the given article, if it can be 
  geocoded.
  """
  
  # Attempt to geocode (get latitude and longitude for) the
  # central article using geopy.
  location = geopy.geocoders.GoogleV3().geocode(place)

  site = wikitools.wiki.Wiki("http://%s.wikipedia.org/w/api.php" % lang) 
  
  # Create the Folium basemap.
  map_widget = folium.Map(location=[location.latitude, location.longitude], zoom_start=14, tiles=tiles)

  # Use wikitools to get the nearby articles.
  params = {
            "action":"query", 
            "format":"json",
            "list": "geosearch",
            "gsradius": radius,
            "gscoord": "%s|%s" % (location.latitude, location.longitude)
           }
  request = wikitools.api.APIRequest(site, params)
  result = request.query()
  
  # Add markers to the map.
  for page in result["query"]["geosearch"]:  
    map_widget.simple_marker([page["lat"], page["lon"]], popup=page["title"])
    
  # Export the Folium map to a standalone HTML file in the special /cdn
  # folder.
  fname = "map_widget_%s.html" % place
  map_widget.create_map(path="/cdn/%s" % fname)
  
  # Return an IPython HTML widget containing an IFrame tag. The iframe
  # contains a relative reference (no path) to the HTML file we just
  # created, which works because the file is in the special /cdn folder.
  return IPython.display.HTML("<iframe src='%s' width=1200px height=600px>" % fname)

# Comparing revisions
# ===================

def get_revision_series(title, lang="en"):
  """
  Returns the recent revisions of the given Wikipedia page as a
  Pandas time series.
  """

  site = wikitools.wiki.Wiki("http://%s.wikipedia.org/w/api.php" % lang) 
  # Use wikitools to get the recent revisions.
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
  
  # Create a Pandas time series from the revisions.
  timestamp = [np.datetime64(revision["timestamp"]) for revision in revisions]
  s = pandas.DataFrame(1, index=timestamp, columns=['n']).resample('D', how='count')
  return pandas.Series(np.asarray(s), index=[i[0] for i in s._index])

def get_two_revision_series(title1, title2, lang="en"):
  """
  Returns the recent revisions of the two given Wikipedia pages as
  conformed Pandas time series.
  """
  
  # Get non-conformed Pandas time series containing the revisions
  # for the two pages.
  r1, r2 = [get_revision_series(title, lang) for title in (title1, title2)]
  
  # Conform them.
  common_start = np.max([r.index.min() for r in (r1, r2)])
  common_end = np.max([r.index.max() for r in (r1, r2)])
  ix = pandas.DatetimeIndex(start=common_start, end=common_end, freq='D')
  return [r.reindex(ix, fill_value=0) for r in (r1, r2)]

def compare_revisions(title1, title2, lang="en"):
  """
  Presents the recent revisions of the two given Wikipedia pages as an
  interactive NVD3 chart.
  """
  chart = nvd3.stackedAreaChart(name='stackedAreaChart',height=450,width=800,use_interactive_guideline=True, x_is_date=True, date_format="%d %b %Y")
  r1, r2 = get_two_revision_series(title1, title2, lang)
  
  x = [int(time.mktime(idx.timetuple()) * 1000) for idx in r1.index]
  y = [[int(count) for count in np.asarray(np.cumsum(r))] for r in [r1, r2]]
  
  chart.add_serie(name=title1, y=y[0], x=x)
  chart.add_serie(name=title2, y=y[1], x=x)
  chart.buildhtml()
  
  # Export the chart to a standalone HTML file in the special /cdn
  # folder.
  fname = "chart_%s_%s.html" % (title1, title2)
  file("/cdn/%s" % fname, "w").write(chart.htmlcontent)
  
  # Return an IPython HTML widget containing an IFrame tag. The iframe
  # contains a relative reference (no path) to the HTML file we just
  # created, which works because the file is in the special /cdn folder.
  return IPython.display.HTML("<iframe src='%s' width=1000px height=550px>" % fname)