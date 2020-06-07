from io import StringIO
from os import listdir
from os.path import isfile, join, dirname
from shutil import copyfile
import panflute as pf
import yaml, sys, re, hashlib, json, os, traceback, urllib.parse

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from util import *

def md_set_edges(filename, new_edges):
    def action(elem, doc):
        if (isinstance(elem, pf.Code) or isinstance(elem, pf.CodeBlock)) and 'info' in elem.classes:
            data,old_edges = parse_config(elem.text)
            elem.text = make_config(data, new_edges)
    
    with open(filename,"rb") as f:
        doc = pf.convert_text(f.read().decode(),standalone=True)
        
    pf.run_filter(action, doc=doc)
    
    with open(filename,"wb") as f:
        f.write(pf.convert_text(doc, input_format='panflute',output_format='markdown', standalone=True).encode('utf-8'))


class md_builder:
    def __init__(self, filename, output_dir, plugins={}):
        self.OK = False
        self.ID = ''
        self.current_loc = 0
        self.node = {'edges':{'has':{}, 'is':{}}}
        self.filename = filename
        self.output_dir = output_dir
        self.plugins = plugins
        self.location_edges = {"is":{},"has":{}}
        with open(filename,"rb") as f:
            doc = pf.convert_text(f.read().decode(),standalone=True)
        doc = doc.walk(self.extract_metadata)
        self.doc = pf.convert_text(doc, input_format='panflute',output_format='html').encode('utf-8')
        self.OK = True

    def add_edge(self, direction, label, edgedata):
        if not label in self.node['edges'][direction]:
            self.node['edges'][direction][label] = []
        self.node['edges'][direction][label].append(edgedata)
        
    def extract_metadata(self, elem, doc):
        if (isinstance(elem, pf.Code) or isinstance(elem, pf.CodeBlock)):
            if 'info' in elem.classes:
                data,new_edges = parse_config(elem.text)
                if not 'name' in data:
                    sys.stderr.write("WARNING: 'name' required in info\n")
                    return []
                for x in data:
                    self.node[x] = data[x]
                edges = self.node['edges']
                self.ID = get_id(self.node['name'])
                add_edges(new_edges, edges)
                return []
            else:
                for p in self.plugins:
                    if p in elem.classes:
                        plugin = self.plugins[p]
                        if hasattr(plugin, 'get_files'):
                            plugin.get_files(elem, lambda fn: get_file(self.ID, self.filename, fn, self.output_dir))
                        if self.plugins[p] == "md":
                            inner_doc = pf.convert_text(elem.text,standalone=True)
                            inner_doc = inner_doc.walk(self.extract_metadata)
                            inner_doc = pf.convert_text(inner_doc, input_format='panflute',output_format='html')
                        else:
                            inner_doc = elem.text
                        return pf.RawBlock("""<cat-{pluginname}>{doc}</cat-{pluginname}>""".format(pluginname=p,doc=inner_doc),format="html")
        elif isinstance(elem, pf.Link) and len(elem.content) > 0 and hasattr(elem.content[0],'text') and elem.content[0].text == "loc":
            url = urllib.parse.unquote(elem.url)
            loc = self.current_loc
            self.current_loc += 1
            for e in url.split(";"):
                e = e.strip()
                print("LOC",url)
                m_has = re.match(r"^has ([^:]+):(.*)$", e)
                m_is = re.match(r"^is ([^:]+) of:(.*)$", e)
                if not m_has is None:
                    edge_name = m_has.group(1).strip()
                    target_name = m_has.group(2).strip()
                    print("#", self.current_loc, "HAS",edge_name,":",target_name)
                    self.add_edge("has",edge_name,{"target":target_name,"srcloc":self.current_loc})
                    loc = self.current_loc
                elif not m_is is None:
                    edge_name = m_is.group(1).strip()
                    target_name = m_is.group(2).strip()
                    print("#", self.current_loc, "IS",edge_name,"OF:",target_name)
                    self.add_edge("is",edge_name,{"target":target_name,"srcloc":self.current_loc})
                else:
                    print("Not a valid edge--ignoring:",url)
            return pf.RawInline("""<a name="node_loc_{}"></a>""".format(loc),format="html")
            
        elif isinstance(elem, pf.Link) or isinstance(elem, pf.Image):
            new_url = get_file(self.ID, self.filename, elem.url, self.output_dir)
            print("URL",elem.url)
            if new_url:
                elem.url = new_url
            elif elem.url[:5] == "node:":
                target = urllib.parse.unquote(elem.url[5:])
                print("LINK",target)
                return pf.RawInline("""<cat-link>{}:{}</cat-link>""".format(get_id(target),target),format="html")
            elif elem.url[:6] == "query:":
                q = urllib.parse.unquote(elem.url[6:])
                print("QUERY",q)
                return pf.RawInline("""<cat-query>{}</cat-query>""".format(q),format="html")
        elif isinstance(elem, pf.Math):
            print("MATH",elem.text)
            return pf.RawInline("""<cat-math>{}</cat-math>""".format(elem.text),format="html")

if __name__ == "__main__":
    import docopt
    args = docopt.docopt("""Usage: mdbuild.py <input_file> <output_dir>""")
    md_builder(args['<output_dir>'])
    
