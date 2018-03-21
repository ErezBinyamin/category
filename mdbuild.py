"""Usage: build.py <cat_name> <input_dir> <output_dir>"""

from io import StringIO
from os import listdir
from os.path import isfile, join, dirname
from shutil import copyfile
import panflute as pf
import yaml, sys, re, hashlib, json, docopt, os, traceback
from util import *

node = {}
metadata = {}
path = ''
ID=''
args = {}

def extract_metadata(elem, doc):
    global node
    global path
    global ID
    global args
    if (isinstance(elem, pf.Code) or isinstance(elem, pf.CodeBlock)):
        if 'edges' in elem.classes:
            if not 'edges' in node: node['edges'] = {'has':{}, 'is':{}}
            for line in elem.text.split("\n"):
                m = re.match(r"^\s*has\s+([^:]*):\s*(.*)\s*$", line)
                et = 'has'
                if not m:
                    m = re.match(r"^\s*is\s+([^:]*)\s+of:\s*(.*)\s*$", line)
                    et = 'is'
                    if not m:
                        sys.stderr.write("WARNING: Line not a valid edge: {}\n".format(line))
                        continue
                en = m.group(1).strip()
                target = m.group(2).strip()
                edges = node['edges'][et]
                if not en in edges: edges[en] = []
                edges[en].append(target)
            return []
        elif 'info' in elem.classes:
            data = yaml.load(elem.text)
            if not 'name' in data:
                sys.stderr.write("WARNING: 'name' required in info\n")
                return []
            node['name'] = data['name']
            ID = get_id(node['name'])
            return []
    elif isinstance(elem, pf.Link) or isinstance(elem, pf.Image):
        if elem.url[:6] == "files/":
            files_dir = join(args['<output_dir>'],'files/'+ID)
            try:
                os.mkdir(files_dir)
            except:
                pass
            print("COPY", join(path, elem.url), files_dir+"/"+elem.url[6:])
            copyfile(join(path, elem.url), files_dir+"/"+elem.url[6:])
            elem.url = "data/files/"+ID+"/"+elem.url[6:]
    elif isinstance(elem, pf.Math):
        print("MATH",elem.text)
        return pf.Str("$"+elem.text+"$")
            

if __name__ == "__main__":
    args = docopt.docopt(__doc__)
    old_metadata = import_metadata(join(args['<output_dir>'],'metadata.json'))
    try:
        os.mkdir(join(args['<output_dir>'],'files'))
    except:
        pass
    files = [join(dirpath,f) for dirpath,dirnames,filenames in os.walk(args['<input_dir>']) for f in filenames if f[-3:] == ".md"]
    for fn in files:
        print(fn)
        node = {}
        ID = ''
        try:
            with open(fn,"rb") as f:
                doc = pf.convert_text(f.read().decode(),standalone=True)
            path = dirname(fn)
            doc = doc.walk(extract_metadata)
            if ID in metadata and metadata[ID]['name'] != node['name']:
                print("WARNING: Duplicate node ID: {} -- skipping".format(node['name']))
                continue
        except Exception as e:
            print("WARNING: Invalid input file: {} -- skipping".format(fn))
            traceback.print_exc()
            continue
        metadata[ID] = node
        with open(join(args['<output_dir>'],'{}.html'.format(ID)),"wb") as f:
            f.write(pf.convert_text(doc, input_format='panflute',output_format='html').encode('utf-8'))
    for x in metadata:
        print(x,metadata[x].get('name','NONE'))
    metadata = complete_metadata(args['<cat_name>'],metadata)
    metadata.update(old_metadata)
    with open(join(args['<output_dir>'],'metadata.json'.format(ID)),"w") as f:
        f.write(json.dumps(metadata))
